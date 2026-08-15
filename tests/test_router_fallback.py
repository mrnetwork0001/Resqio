"""Degraded-mode route planning tests (no Bedrock required)."""

from src.agents.strands_volunteer_router import fallback_route_plan
from src.core.models import (
    CrisisEvent,
    CrisisSource,
    GeoPoint,
    Match,
    ResourceOffer,
    ResourceRequest,
    ResourceType,
    Severity,
    Vulnerability,
)


def _fixture():
    offer = ResourceOffer(
        id="off_1", contact_name="Marcus", resource_type=ResourceType.GENERATOR,
        description="7500W generator", address="Springdale Rd",
        location=GeoPoint(lat=30.2795, lon=-97.6923),
    )
    request = ResourceRequest(
        id="req_1", contact_name="Amara", resource_type=ResourceType.MEDICAL,
        description="insulin refrigeration", address="42 Maple St", urgency=5,
        vulnerability=Vulnerability.MEDICAL_REFRIGERATION,
        location=GeoPoint(lat=30.2764, lon=-97.7041),
    )
    match = Match(offer_id=offer.id, request_id=request.id, rationale="generator serves refrigeration")
    hazards = [
        CrisisEvent(source=CrisisSource.NOAA, event="Excessive Heat Warning", severity=Severity.EXTREME),
        CrisisEvent(source=CrisisSource.GRID, event="Feeder Outage", severity=Severity.SEVERE),
    ]
    return match, offer, request, hazards


def test_fallback_plan_has_reply_protocol():
    match, offer, request, hazards = _fixture()
    plan = fallback_route_plan(match, offer, request, hazards)
    assert f"ACCEPT {match.id}" in plan.ping_message
    assert f"PASS {match.id}" in plan.ping_message


def test_fallback_plan_computes_distance_and_time():
    match, offer, request, hazards = _fixture()
    plan = fallback_route_plan(match, offer, request, hazards)
    assert 0.5 < plan.distance_km < 2.5
    assert plan.est_minutes >= 5  # loading buffer floor


def test_fallback_plan_carries_hazard_guidance():
    match, offer, request, hazards = _fixture()
    plan = fallback_route_plan(match, offer, request, hazards)
    assert "Excessive Heat Warning" in plan.hazards
    assert "heat" in plan.instructions.lower()
    assert "intersection" in plan.instructions.lower()  # outage → dark signals guidance


def test_fallback_plan_without_coordinates_uses_default_scale():
    match, offer, request, hazards = _fixture()
    offer.location = None
    plan = fallback_route_plan(match, offer, request, hazards)
    assert plan.distance_km == 3.0


def test_ping_mentions_addresses():
    match, offer, request, hazards = _fixture()
    plan = fallback_route_plan(match, offer, request, hazards)
    assert "Springdale Rd" in plan.ping_message
    assert "42 Maple St" in plan.ping_message

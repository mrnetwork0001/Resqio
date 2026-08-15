"""Degraded-mode logic tests for the resource matcher (no Bedrock required)."""

from src.agents.strands_resource_matcher import (
    COMPATIBILITY,
    heuristic_matches,
    heuristic_parse,
)
from src.core.models import ResourceType, Vulnerability


# ── SMS parsing ──────────────────────────────────────────────────────


def test_parse_generator_offer():
    parsed = heuristic_parse("OFFER: Generator available in Sector 4, 7500W dual fuel.")
    assert parsed.kind == "offer"
    assert parsed.resource_type == ResourceType.GENERATOR


def test_parse_insulin_request_is_life_safety():
    parsed = heuristic_parse("HELP: My father is 82, insulin needs refrigeration, power out at 42 Maple St.")
    assert parsed.kind == "request"
    assert parsed.urgency == 5
    assert parsed.vulnerability == Vulnerability.MEDICAL_REFRIGERATION
    assert parsed.address == "42 Maple St"


def test_parse_infant_request():
    parsed = heuristic_parse("HELP: family with a 3-month-old, no power, need somewhere cool. Govalle.")
    assert parsed.kind == "request"
    assert parsed.vulnerability == Vulnerability.INFANT
    assert parsed.urgency >= 4


def test_parse_accept_reply_extracts_match_id():
    parsed = heuristic_parse("ACCEPT mat_ab12cd34ef")
    assert parsed.kind == "accept"
    assert parsed.match_id == "mat_ab12cd34ef"


def test_parse_pass_reply():
    parsed = heuristic_parse("pass mat_ab12cd34ef")
    assert parsed.kind == "pass"
    assert parsed.match_id == "mat_ab12cd34ef"


def test_parse_gibberish_is_unknown():
    assert heuristic_parse("hi").kind == "unknown"


def test_request_wins_over_offer_wording():
    # Safety bias: a message with both signals is treated as a request.
    parsed = heuristic_parse("Please help, we need water, I have nothing left")
    assert parsed.kind == "request"


# ── Matching ─────────────────────────────────────────────────────────


def test_compatibility_matrix_covers_every_offer_type():
    assert set(COMPATIBILITY) == set(ResourceType)


def test_heuristic_matches_prioritize_urgent_medical(seeded_store):
    proposal = heuristic_matches(seeded_store)
    assert proposal.matches, "expected at least one match"
    first = proposal.matches[0]
    # Most urgent request (insulin, urgency 5) is matched first, and the
    # generator (serves MEDICAL refrigeration) is a valid pick for it.
    assert first.request_id == "req_insulin1"
    assert first.offer_id in {"off_generator1", "off_ice1"}
    assert 0.0 <= first.score <= 1.0


def test_heuristic_matches_never_double_book(seeded_store):
    proposal = heuristic_matches(seeded_store)
    offer_ids = [m.offer_id for m in proposal.matches]
    assert len(offer_ids) == len(set(offer_ids))


def test_unmatchable_request_reported_unmet(store):
    from src.core.models import ResourceRequest, ResourceOffer, GeoPoint

    store.add_offer(ResourceOffer(id="off_food", resource_type=ResourceType.FOOD, description="canned goods"))
    store.add_request(ResourceRequest(id="req_transport", resource_type=ResourceType.TRANSPORT,
                                      description="need evacuation ride", urgency=4))
    proposal = heuristic_matches(store)
    assert proposal.matches == []
    assert proposal.unmet_request_ids == ["req_transport"]

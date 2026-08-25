"""StrandsVolunteerRouter — Agent 3: safe transit routing + approval pings.

Given a proposed match, produces a ``RoutePlan``: distance, crisis-condition
time estimate, hazards the volunteer must know about, and the exact
WhatsApp/SMS text a captain sees. The ping always ends with
``ACCEPT <match_id>`` / ``PASS <match_id>`` reply options — the single
human-in-the-loop moment in an otherwise fully background pipeline.
"""

from __future__ import annotations

import json
import logging

from strands import Agent, tool
from strands.models import BedrockModel

from ..core.config import Settings
from ..core.geo import estimate_transit_minutes, haversine_km
from ..core.models import (
    CrisisEvent,
    Match,
    ResourceOffer,
    ResourceRequest,
    RoutePlan,
)

logger = logging.getLogger("resqio.volunteer_router")

SYSTEM_PROMPT = """You are Resqio's Volunteer Router. A supply match has been proposed and a \
volunteer captain must approve the delivery. Your job:

1. Estimate the trip (straight-line distance is available via your tool; assume ~30 km/h \
crisis-condition driving plus 5 minutes for loading).
2. List hazards along the way from the active event list — heat exposure, flooded roads, downed \
lines, dark intersections during outages. Give one concrete safety instruction per hazard.
3. Write the approval ping: under 320 characters, plain language, states WHAT to bring, WHERE \
(street address), WHY it matters (urgency/vulnerability), the distance/time estimate, and ends \
EXACTLY with: Reply ACCEPT <match_id> or PASS <match_id>

Volunteers are neighbors, not first responders. Never route anyone into an evacuation zone; if \
conditions look unsafe for amateurs, say so in the instructions."""


_HAZARD_GUIDANCE: list[tuple[tuple[str, ...], str]] = [
    (("heat",), "Extreme heat: travel with AC, carry water, limit time outdoors."),
    (("flood", "storm", "hurricane"), "Possible flooded roads: never drive through standing water."),
    (("outage", "blackout", "power"), "Traffic signals may be dark: treat every intersection as a 4-way stop."),
    (("freeze", "ice", "winter", "snow"), "Icy roads: drive slowly, keep blankets in the vehicle."),
    (("tornado",), "Tornado risk: check the warning window before departing."),
]


def _trim_words(text: str, limit: int) -> str:
    """Truncate at a word boundary — captains read this text mid-crisis."""
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0].rstrip(",;:") + "…"


def fallback_route_plan(
    match: Match,
    offer: ResourceOffer,
    request: ResourceRequest,
    hazards: list[CrisisEvent],
) -> RoutePlan:
    """Deterministic route plan used when Bedrock is unreachable."""
    if offer.location is not None and request.location is not None:
        distance_km = round(haversine_km(offer.location, request.location), 2)
    else:
        distance_km = match.distance_km or 3.0  # conservative neighborhood-scale default
    est_minutes = estimate_transit_minutes(distance_km)

    active_labels = [e.event for e in hazards if e.is_active]
    hazard_notes: list[str] = []
    for keywords, guidance in _HAZARD_GUIDANCE:
        if any(any(kw in label.lower() for kw in keywords) for label in active_labels):
            hazard_notes.append(guidance)

    pickup = offer.address or "the pickup point"
    dropoff = request.address or "the drop-off point"
    item = _trim_words(offer.description, 48) or offer.resource_type.value
    need = _trim_words(request.description, 80) or request.resource_type.value
    instructions = (
        f"Pick up {item} at {pickup}, deliver to {dropoff}. " + " ".join(hazard_notes)
    ).strip()

    ping = (
        f"🚨 Resqio: {offer.resource_type.value} needed for {need} "
        f"({request.vulnerability.value}, urgency {request.urgency}/5). "
        f"Bring {item} from {pickup} to {dropoff} "
        f"— {distance_km} km, ~{est_minutes:.0f} min. "
        f"Reply ACCEPT {match.id} or PASS {match.id}"
    )
    return RoutePlan(
        distance_km=distance_km,
        est_minutes=est_minutes,
        hazards=active_labels,
        instructions=instructions,
        ping_message=ping,
    )


class StrandsVolunteerRouter:
    """Calculates safe delivery transit routes and formats human approval pings."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def _build_agent(self, offer: ResourceOffer, request: ResourceRequest) -> Agent:
        @tool
        def compute_trip_distance() -> str:
            """Compute the straight-line distance in km between this trip's pickup and dropoff."""
            if offer.location is None or request.location is None:
                return "unknown (missing coordinates); assume a neighborhood-scale trip of ~3 km"
            return f"{round(haversine_km(offer.location, request.location), 2)} km"

        return Agent(
            name="VolunteerRouter",
            model=BedrockModel(
                model_id=self._settings.bedrock_model_id,
                region_name=self._settings.aws_region,
                temperature=0.3,
            ),
            system_prompt=SYSTEM_PROMPT,
            tools=[compute_trip_distance],
            callback_handler=None,
        )

    def plan_route(
        self,
        match: Match,
        offer: ResourceOffer,
        request: ResourceRequest,
        hazards: list[CrisisEvent],
    ) -> RoutePlan:
        """Produce the route plan + approval ping for a proposed match."""
        hazard_json = json.dumps(
            [{"event": e.event, "severity": e.severity.value, "area": e.area_desc} for e in hazards if e.is_active]
        )
        prompt = (
            f"Match id: {match.id}\n"
            f"Rationale: {match.rationale}\n"
            f"OFFER: {offer.model_dump_json(include={'resource_type', 'description', 'address', 'contact_name'})}\n"
            f"REQUEST: {request.model_dump_json(include={'resource_type', 'description', 'address', 'urgency', 'vulnerability', 'contact_name'})}\n"
            f"ACTIVE HAZARDS: {hazard_json}\n\n"
            "Plan the trip and write the approval ping."
        )
        try:
            result = self._build_agent(offer, request)(prompt, structured_output_model=RoutePlan)
            plan = result.structured_output
            # Guardrail: the ping MUST carry the reply protocol or the
            # approval loop breaks. Repair rather than fail.
            if f"ACCEPT {match.id}" not in plan.ping_message or f"PASS {match.id}" not in plan.ping_message:
                plan.ping_message = plan.ping_message.rstrip(". ") + (
                    f". Reply ACCEPT {match.id} or PASS {match.id}"
                )
            return plan
        except Exception as exc:  # noqa: BLE001 — degraded mode must still route
            logger.warning("Bedrock routing unavailable (%s); using fallback planner", exc)
            return fallback_route_plan(match, offer, request, hazards)

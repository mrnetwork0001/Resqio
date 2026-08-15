"""StrandsResourceMatcher — Agent 2: supply↔need matching with spatial reasoning.

Two responsibilities:
1. Parse raw community SMS ("Generator available in Sector 4" / "Insulin ice
   needed at 42 Maple St") into validated offers and requests.
2. During a crisis, propose offer→request matches, prioritizing urgency and
   vulnerability, using distance tools for spatial reasoning.

LLM proposals are never trusted blindly: every candidate is validated against
the live store (ids exist, entries still open) before a match is recorded.
Degraded mode falls back to a compatibility-matrix + haversine greedy match.
"""

from __future__ import annotations

import json
import logging
import re

from strands import Agent, tool
from strands.models import BedrockModel

from ..core.config import Settings
from ..core.geo import haversine_km
from ..core.models import (
    CrisisAssessment,
    GeoPoint,
    Match,
    MatchCandidate,
    MatchProposal,
    ParsedInboundMessage,
    ResourceOffer,
    ResourceRequest,
    ResourceType,
    Vulnerability,
)
from ..core.store import CommunityStore, InvalidTransition

logger = logging.getLogger("resqio.resource_matcher")

SYSTEM_PROMPT = """You are Resqio's Resource Matcher, the logistics brain of a community \
disaster response network. Neighbors text in what they can offer (generators, ice, food, water, \
medical supplies, rides, cool shelter) and what they urgently need.

Matching principles, in order:
1. Life-safety first: medical refrigeration (insulin!), infants, and elderly residents outrank \
everything else.
2. Fitness for purpose: a generator serves a refrigeration need; ice serves it temporarily; \
food does not.
3. Proximity: shorter volunteer trips are safer trips during a disaster. Use your distance tool.
4. One offer serves one request at a time — never double-book an offer.

Only propose matches you would defend to a volunteer captain in one sentence. Requests that \
nothing can serve go in unmet_request_ids so captains can escalate them."""

PARSE_SYSTEM_PROMPT = """You parse raw SMS messages sent by neighbors to Resqio, a community \
disaster logistics service. Classify each message as an offer of help, a request for help, an \
ACCEPT/PASS/DELIVERED reply from a volunteer, or unknown. Extract the resource type, urgency \
(1-5, where insulin/medical refrigeration, infants, and elderly with no power are 4-5), any \
vulnerability, and a street address if present. Messages are informal — read them like a \
neighbor would."""

# What an offered resource type can serve.
COMPATIBILITY: dict[ResourceType, set[ResourceType]] = {
    ResourceType.GENERATOR: {ResourceType.GENERATOR, ResourceType.MEDICAL, ResourceType.SHELTER},
    ResourceType.ICE: {ResourceType.ICE, ResourceType.MEDICAL, ResourceType.FOOD},
    ResourceType.FOOD: {ResourceType.FOOD},
    ResourceType.WATER: {ResourceType.WATER, ResourceType.FOOD},
    ResourceType.MEDICAL: {ResourceType.MEDICAL},
    ResourceType.SHELTER: {ResourceType.SHELTER},
    ResourceType.TRANSPORT: {ResourceType.TRANSPORT, ResourceType.SHELTER},
    ResourceType.OTHER: set(ResourceType),
}

_RESOURCE_KEYWORDS: list[tuple[ResourceType, tuple[str, ...]]] = [
    (ResourceType.GENERATOR, ("generator", "power bank", "solar panel", "inverter")),
    (ResourceType.MEDICAL, ("insulin", "medical", "medicine", "oxygen", "prescription", "refrigeration")),
    (ResourceType.ICE, ("ice", "cooler", "dry ice")),
    (ResourceType.WATER, ("water", "bottled")),
    (ResourceType.FOOD, ("food", "meal", "groceries", "formula")),
    (ResourceType.TRANSPORT, ("ride", "transport", "evacuate", "evacuation", "pickup truck")),
    (ResourceType.SHELTER, ("shelter", "cool place", "cooling center", "spare room", "a/c", "ac", "fan")),
]


def _has_keyword(keyword: str, lower_text: str) -> bool:
    # Whole-word match: "office" must not hit "ice", "notice" must not
    # hit "ice", "8 Oak Drive" must not read as transport.
    return re.search(rf"\b{re.escape(keyword)}\b", lower_text) is not None

_MATCH_ID_RE = re.compile(r"\b(mat_[a-z0-9]+)\b", re.IGNORECASE)
_ADDRESS_RE = re.compile(
    r"\b(\d{1,5}\s+[A-Za-z][A-Za-z'\.]*(?:\s+[A-Za-z][A-Za-z'\.]*)?\s+"
    r"(?:St|Street|Ave|Avenue|Rd|Road|Blvd|Boulevard|Dr|Drive|Ln|Lane|Way|Ct|Court))\b",
    re.IGNORECASE,
)


def heuristic_parse(body: str) -> ParsedInboundMessage:
    """Keyword fallback parser for inbound SMS (no LLM required)."""
    text = body.strip()
    # "OFFER: generator…" → description "generator…" (the tag is a signal, not content)
    description = re.sub(r"^\s*(offer|help|need|request)\s*[:\-]\s*", "", text, flags=re.IGNORECASE)
    lower = text.lower()

    # A captain reply must LEAD with the verb or carry a match id — a
    # neighbor writing "can you pass this along, we need water" is a
    # request, not a PASS.
    match_id = _MATCH_ID_RE.search(text)
    for kind in ("accept", "pass", "delivered"):
        if _has_keyword(kind, lower) and (match_id or lower.startswith(kind)):
            return ParsedInboundMessage(kind=kind, match_id=match_id.group(1).lower() if match_id else "")

    resource_type = ResourceType.OTHER
    for rtype, keywords in _RESOURCE_KEYWORDS:
        if any(_has_keyword(kw, lower) for kw in keywords):
            resource_type = rtype
            break

    offer_signals = ("offer", "available", "i have", "we have", "can provide", "spare", "extra", "giving away")
    request_signals = ("help", "need", "urgent", "please", "emergency", "no power", "power is out", "power out")
    is_offer = any(_has_keyword(s, lower) for s in offer_signals)
    is_request = any(_has_keyword(s, lower) for s in request_signals)
    # "HELP: ... available power" style messages hit both; request wins (safety bias).
    kind = "request" if is_request else ("offer" if is_offer else "unknown")

    urgency = 3
    vulnerability = Vulnerability.NONE
    if any(_has_keyword(w, lower) for w in ("insulin", "oxygen", "dialysis", "refrigeration")):
        urgency, vulnerability = 5, Vulnerability.MEDICAL_REFRIGERATION
    elif any(_has_keyword(w, lower) for w in ("baby", "infant", "newborn", "month-old", "month old")):
        urgency, vulnerability = 4, Vulnerability.INFANT
    elif any(_has_keyword(w, lower) for w in ("elderly", "senior", "years old", "wheelchair", "disabled")):
        urgency, vulnerability = 4, Vulnerability.ELDERLY
    if any(_has_keyword(w, lower) for w in ("urgent", "emergency", "asap", "life")):
        urgency = 5

    address = _ADDRESS_RE.search(text)
    return ParsedInboundMessage(
        kind=kind,
        resource_type=resource_type,
        description=description,
        urgency=urgency,
        vulnerability=vulnerability,
        address=address.group(1) if address else "",
    )


def _entry_distance_km(offer: ResourceOffer, request: ResourceRequest) -> float | None:
    if offer.location is None or request.location is None:
        return None
    return round(haversine_km(offer.location, request.location), 2)


def heuristic_matches(store: CommunityStore) -> MatchProposal:
    """Greedy compatibility+distance matcher (no LLM required)."""
    offers = list(store.open_offers())
    candidates: list[MatchCandidate] = []
    unmet: list[str] = []
    for request in store.open_requests():  # already urgency-sorted, most urgent first
        best: tuple[float, ResourceOffer, float | None] | None = None
        for offer in offers:
            if request.resource_type not in COMPATIBILITY[offer.resource_type]:
                continue
            score = 0.6 if offer.resource_type == request.resource_type else 0.5
            distance = _entry_distance_km(offer, request)
            if distance is not None:
                score += 0.25 if distance <= 2 else 0.15 if distance <= 5 else 0.08 if distance <= 10 else 0.0
            if request.urgency >= 5:
                score += 0.10
            if request.vulnerability != Vulnerability.NONE:
                score += 0.05
            score = min(score, 1.0)
            if best is None or score > best[0]:
                best = (score, offer, distance)
        if best is None:
            unmet.append(request.id)
            continue
        score, offer, distance = best
        offers.remove(offer)  # one offer serves one request
        dist_note = f" ~{distance} km away" if distance is not None else ""
        candidates.append(
            MatchCandidate(
                offer_id=offer.id,
                request_id=request.id,
                score=round(score, 2),
                rationale=(
                    f"{offer.resource_type.value} offer serves {request.resource_type.value} need "
                    f"(urgency {request.urgency}/5, {request.vulnerability.value}){dist_note}."
                ),
            )
        )
    return MatchProposal(matches=candidates, unmet_request_ids=unmet)


class StrandsResourceMatcher:
    """Ingests community SMS and matches supply capacity to urgent needs."""

    def __init__(self, settings: Settings, store: CommunityStore) -> None:
        self._settings = settings
        self.store = store

        @tool
        def list_open_offers() -> str:
            """List all currently open resource offers as JSON (id, type, description, address, lat/lon)."""
            return json.dumps([o.model_dump(mode="json") for o in self.store.open_offers()], indent=2)

        @tool
        def list_open_requests() -> str:
            """List open resource requests as JSON, most urgent first (id, type, urgency, vulnerability, address, lat/lon)."""
            return json.dumps([r.model_dump(mode="json") for r in self.store.open_requests()], indent=2)

        @tool
        def compute_distance_km(offer_id: str, request_id: str) -> str:
            """Compute the straight-line distance in km between an offer and a request.

            Args:
                offer_id: id of the resource offer
                request_id: id of the resource request
            """
            offer = self.store.offers.get(offer_id)
            request = self.store.requests.get(request_id)
            if offer is None or request is None:
                return "error: unknown offer or request id"
            distance = _entry_distance_km(offer, request)
            if distance is None:
                return "unknown (one side has no coordinates)"
            return f"{distance} km"

        self._tools = [list_open_offers, list_open_requests, compute_distance_km]

    def _build_model(self, temperature: float) -> BedrockModel:
        return BedrockModel(
            model_id=self._settings.bedrock_model_id,
            region_name=self._settings.aws_region,
            temperature=temperature,
        )

    # ── Inbound SMS ingestion ────────────────────────────────────────

    def parse_inbound_sms(self, body: str) -> ParsedInboundMessage:
        """Parse one raw SMS. LLM first, keyword heuristics as fallback."""
        try:
            # Fresh Agent per parse: Agent instances accumulate conversation
            # history, and each SMS is an independent classification.
            parser = Agent(
                name="SmsParser",
                model=self._build_model(temperature=0.0),
                system_prompt=PARSE_SYSTEM_PROMPT,
                callback_handler=None,
            )
            result = parser(f"Parse this SMS:\n{body!r}", structured_output_model=ParsedInboundMessage)
            return result.structured_output
        except Exception as exc:  # noqa: BLE001 — degraded mode must always parse
            logger.warning("LLM parse unavailable (%s); using keyword parser", exc)
            return heuristic_parse(body)

    def ingest_message(
        self,
        body: str,
        phone: str = "",
        contact_name: str = "neighbor",
        location: GeoPoint | None = None,
    ) -> ResourceOffer | ResourceRequest | ParsedInboundMessage:
        """Turn an inbound SMS into a stored offer/request.

        ACCEPT/PASS/DELIVERED replies and unparseable messages are returned
        as the parse result for the orchestrator to act on.
        """
        parsed = self.parse_inbound_sms(body)
        if parsed.kind == "offer":
            return self.store.add_offer(
                ResourceOffer(
                    contact_name=contact_name, phone=phone,
                    resource_type=parsed.resource_type,
                    description=parsed.description or body,
                    address=parsed.address, location=location,
                )
            )
        if parsed.kind == "request":
            return self.store.add_request(
                ResourceRequest(
                    contact_name=contact_name, phone=phone,
                    resource_type=parsed.resource_type,
                    description=parsed.description or body,
                    urgency=parsed.urgency, vulnerability=parsed.vulnerability,
                    address=parsed.address, location=location,
                )
            )
        return parsed

    # ── Matching ─────────────────────────────────────────────────────

    def propose_matches(self, assessment: CrisisAssessment) -> list[Match]:
        """Propose validated offer→request matches for the current crisis."""
        proposal = self._llm_or_heuristic_proposal(assessment)
        matches: list[Match] = []
        for candidate in proposal.matches:
            offer = self.store.offers.get(candidate.offer_id)
            request = self.store.requests.get(candidate.request_id)
            if offer is None or request is None:
                logger.warning("dropping match with unknown ids: %s -> %s", candidate.offer_id, candidate.request_id)
                continue
            if offer.status.value != "open" or request.status.value != "open":
                logger.warning("dropping match on non-open entries: %s -> %s", offer.id, request.id)
                continue
            match = Match(
                offer_id=offer.id,
                request_id=request.id,
                score=candidate.score,
                rationale=candidate.rationale,
                distance_km=_entry_distance_km(offer, request),
            )
            try:
                # record_match re-verifies OPEN under the store lock: a
                # concurrent cycle that booked the same offer first wins.
                self.store.record_match(match)
                matches.append(match)
            except (KeyError, InvalidTransition) as exc:
                logger.warning("dropping match %s -> %s: %s", offer.id, request.id, exc)
        if proposal.unmet_request_ids:
            logger.info("unmet requests needing escalation: %s", proposal.unmet_request_ids)
        return matches

    def _llm_or_heuristic_proposal(self, assessment: CrisisAssessment) -> MatchProposal:
        open_offers = self.store.open_offers()
        open_requests = self.store.open_requests()
        if not open_offers or not open_requests:
            return MatchProposal(matches=[], unmet_request_ids=[r.id for r in open_requests])
        prompt = (
            f"Crisis situation: {assessment.summary}\n"
            f"Crisis level: {assessment.crisis_level}/5. Hazards: {', '.join(assessment.active_hazards)}.\n\n"
            "Use your tools to review open offers and requests, check distances, "
            "and propose the best set of matches."
        )
        try:
            matcher = Agent(
                name="ResourceMatcher",
                model=self._build_model(temperature=0.2),
                system_prompt=SYSTEM_PROMPT,
                tools=self._tools,
                callback_handler=None,
            )
            result = matcher(prompt, structured_output_model=MatchProposal)
            return result.structured_output
        except Exception as exc:  # noqa: BLE001 — degraded mode must still match
            logger.warning("Bedrock matching unavailable (%s); using heuristic matcher", exc)
            return heuristic_matches(self.store)

"""ResqioPipeline — the silent background loop tying the three agents together.

One cycle:  poll feeds → assess crisis → (if crisis) match resources →
plan routes → ping captains for approval.  No crisis, no noise: the pipeline
produces zero outward messages unless a delivery needs a human yes/no.

The same pipeline object serves every runtime: the local daemon, the
AgentCore entrypoint, and the demo runner.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from .agents.strands_grid_monitor import StrandsGridMonitor
from .agents.strands_resource_matcher import StrandsResourceMatcher
from .agents.strands_volunteer_router import StrandsVolunteerRouter
from .core.config import Settings, get_settings
from .core.feeds import build_feeds
from .core.models import (
    ApprovalPing,
    CrisisAssessment,
    Match,
    MatchStatus,
    ParsedInboundMessage,
    ResourceOffer,
    RouteInfo,
)
from .core.store import CommunityStore
from .integrations.twilio_whatsapp_dispatcher import TwilioWhatsAppDispatcher

logger = logging.getLogger("resqio.pipeline")


@dataclass
class CycleReport:
    """What one background cycle observed and did."""

    assessment: CrisisAssessment
    new_matches: list[Match] = field(default_factory=list)
    pings: list[ApprovalPing] = field(default_factory=list)

    @property
    def surfaced_to_humans(self) -> bool:
        return bool(self.pings)

    def to_dict(self) -> dict:
        return {
            "assessment": self.assessment.model_dump(),
            "new_matches": [m.model_dump(mode="json") for m in self.new_matches],
            "pings": [p.model_dump(mode="json") for p in self.pings],
            "surfaced_to_humans": self.surfaced_to_humans,
        }


class ResqioPipeline:
    def __init__(self, settings: Settings | None = None, store: CommunityStore | None = None) -> None:
        self.settings = settings or get_settings()
        self.store = store or CommunityStore(self.settings.store_path)
        weather_feed, grid_feed = build_feeds(self.settings)
        self.monitor = StrandsGridMonitor(self.settings, weather_feed, grid_feed)
        self.matcher = StrandsResourceMatcher(self.settings, self.store)
        self.router = StrandsVolunteerRouter(self.settings)
        self.dispatcher = TwilioWhatsAppDispatcher(self.settings)

    # ── The background cycle ─────────────────────────────────────────

    def run_cycle(self) -> CycleReport:
        """One full monitor → match → route → ping pass. Never raises."""
        events = self.monitor.poll()
        assessment = self.monitor.assess(events)
        report = CycleReport(assessment=assessment)

        if not assessment.is_crisis:
            logger.info("cycle: calm (level %s) — staying silent", assessment.crisis_level)
            return report

        logger.info("cycle: CRISIS level %s — activating logistics", assessment.crisis_level)
        for match in self.matcher.propose_matches(assessment):
            offer = self.store.offers[match.offer_id]
            request = self.store.requests[match.request_id]
            plan = self.router.plan_route(match, offer, request, events)
            match.route = RouteInfo(
                distance_km=plan.distance_km,
                est_minutes=plan.est_minutes,
                hazards=plan.hazards,
                instructions=plan.instructions,
            )
            self.store.set_match_status(match.id, MatchStatus.PENDING_APPROVAL)
            report.new_matches.append(match)
            report.pings.extend(self.dispatcher.send_approval_ping(match.id, plan.ping_message))
        return report

    # ── Inbound SMS/WhatsApp (webhook or seeded demo messages) ───────

    def handle_inbound(self, body: str, phone: str = "", name: str = "neighbor", location=None) -> str:
        """Process one inbound message; returns the reply text for the sender."""
        result = self.matcher.ingest_message(body, phone=phone, contact_name=name, location=location)
        if isinstance(result, ParsedInboundMessage):
            return self._handle_reply(result)
        if isinstance(result, ResourceOffer):
            logger.info("ingested offer %s from %s", result.id, name)
            return "Resqio: got it — your offer is on the community board. We'll ping you only if a neighbor needs it."
        logger.info("ingested request %s from %s", result.id, name)
        return "Resqio: your request is logged. We're matching it against nearby offers and will confirm shortly."

    def _handle_reply(self, parsed: ParsedInboundMessage) -> str:
        match = self.store.get_match(parsed.match_id) if parsed.match_id else None
        if parsed.kind == "accept":
            if match is None:
                return "Resqio: couldn't find that match id. Reply ACCEPT <match_id> exactly as pinged."
            self.store.set_match_status(match.id, MatchStatus.APPROVED)
            logger.info("match %s APPROVED by captain", match.id)
            return f"Resqio: match {match.id} approved ✔ — reply DELIVERED {match.id} once the drop-off is done. Stay safe."
        if parsed.kind == "pass":
            if match is None:
                return "Resqio: couldn't find that match id. Reply PASS <match_id> exactly as pinged."
            self.store.set_match_status(match.id, MatchStatus.DECLINED)
            logger.info("match %s declined; both sides reopened", match.id)
            return f"Resqio: match {match.id} passed — the offer and request are back on the board for re-matching."
        if parsed.kind == "delivered":
            if match is None:
                return "Resqio: couldn't find that match id. Reply DELIVERED <match_id>."
            self.store.set_match_status(match.id, MatchStatus.DELIVERED)
            logger.info("match %s DELIVERED", match.id)
            return f"Resqio: delivery {match.id} confirmed 🎉 — thank you."
        return (
            "Resqio: I couldn't read that. Text OFFER: <what you can share + where> "
            "or HELP: <what you need + where>."
        )

    # ── Status (dashboard / AgentCore status action) ─────────────────

    def status(self) -> dict:
        return {
            "demo_mode": self.settings.demo_mode,
            "open_offers": len(self.store.open_offers()),
            "open_requests": len(self.store.open_requests()),
            "pending_matches": [m.model_dump(mode="json") for m in self.store.pending_matches()],
            "total_matches": len(self.store.matches),
            "last_events": [e.model_dump(mode="json") for e in self.monitor.last_events],
        }

"""ResqioPipeline - the silent background loop tying the three agents together.

One cycle:  poll feeds → assess crisis → (if crisis) match resources →
plan routes → ping captains for approval.  No crisis, no noise: the pipeline
produces zero outward messages unless a delivery needs a human yes/no.

The same pipeline object serves every runtime: the local daemon, the
AgentCore entrypoint, and the demo runner.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import timedelta

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
from .core.models import utcnow
from .core.store import CommunityStore, InvalidTransition
from .core.zones import ZoneRegistry
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
        self.zones = ZoneRegistry.load(self.settings)
        weather_feed, grid_feed = build_feeds(self.settings, self.zones.noaa_areas())
        self.monitor = StrandsGridMonitor(self.settings, weather_feed, grid_feed)
        self.matcher = StrandsResourceMatcher(self.settings, self.store, zones=self.zones)
        self.router = StrandsVolunteerRouter(self.settings)
        self.dispatcher = TwilioWhatsAppDispatcher(self.settings)
        self.last_report: CycleReport | None = None
        self.last_cycle_at = None

    # ── The background cycle ─────────────────────────────────────────

    def run_cycle(self) -> CycleReport:
        """One full monitor → match → route → ping pass. Never raises."""
        self._expire_stale_matches()
        self._enforce_retention()
        events = self.monitor.poll()
        assessment = self.monitor.assess(events)
        report = CycleReport(assessment=assessment)
        self.last_report = report  # same object; later ping appends show through
        self.last_cycle_at = utcnow()

        if not assessment.is_crisis:
            logger.info("cycle: calm (level %s) - staying silent", assessment.crisis_level)
            return report

        logger.info("cycle: CRISIS level %s - activating logistics", assessment.crisis_level)
        for match in self.matcher.propose_matches(assessment):
            # One bad match (routing error, dispatch error) must not stop
            # the rest of the cycle or kill the 24/7 loop.
            try:
                self._route_and_ping(match, events, report)
            except Exception:  # noqa: BLE001
                logger.exception("processing match %s failed; continuing cycle", match.id)
        return report

    def _route_and_ping(self, match: Match, events, report: CycleReport) -> None:
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
        # Ping the roster of the zone where the need is.
        captains = self.zones.captains_for(request.zone)
        report.pings.extend(self.dispatcher.send_approval_ping(match.id, plan.ping_message, captains))

    def _expire_stale_matches(self) -> None:
        """Free resources locked behind pings nobody ever answered."""
        ttl = timedelta(minutes=self.settings.match_ttl_minutes)
        now = utcnow()
        for match in self.store.awaiting_action_matches():
            if now - match.created_at > ttl:
                self.store.set_match_status(match.id, MatchStatus.EXPIRED)
                logger.info(
                    "match %s expired after %s min without approval; both sides reopened",
                    match.id, self.settings.match_ttl_minutes,
                )

    def _enforce_retention(self) -> None:
        """Keep long-running deployments bounded: prune old dead matches, cap the ping log."""
        if self.settings.match_retention_hours > 0:
            cutoff = utcnow() - timedelta(hours=self.settings.match_retention_hours)
            removed = self.store.prune_closed_matches(cutoff)
            if removed:
                logger.info("pruned %d declined/expired matches older than %sh",
                            removed, self.settings.match_retention_hours)
        limit = self.settings.ping_log_limit
        if limit > 0 and len(self.dispatcher.sent) > limit:
            del self.dispatcher.sent[:-limit]

    # ── Inbound SMS/WhatsApp (webhook or seeded demo messages) ───────

    def handle_inbound(self, body: str, phone: str = "", name: str = "neighbor", location=None) -> str:
        """Process one inbound message; returns the reply text for the sender."""
        result = self.matcher.ingest_message(body, phone=phone, contact_name=name, location=location)
        if isinstance(result, ParsedInboundMessage):
            return self._handle_reply(result)
        if isinstance(result, ResourceOffer):
            logger.info("ingested offer %s from %s", result.id, name)
            return "Resqio: got it - your offer is on the community board. We'll ping you only if a neighbor needs it."
        logger.info("ingested request %s from %s", result.id, name)
        return "Resqio: your request is logged. We're matching it against nearby offers and will confirm shortly."

    _REPLY_TARGETS = {
        "accept": MatchStatus.APPROVED,
        "pass": MatchStatus.DECLINED,
        "delivered": MatchStatus.DELIVERED,
    }

    def _handle_reply(self, parsed: ParsedInboundMessage) -> str:
        if parsed.kind not in self._REPLY_TARGETS:
            return (
                "Resqio: I couldn't read that. Text OFFER: <what you can share + where> "
                "or HELP: <what you need + where>."
            )
        match = self.store.get_match(parsed.match_id) if parsed.match_id else None
        if match is None:
            return (
                f"Resqio: couldn't find that match id. Reply {parsed.kind.upper()} <match_id> "
                "exactly as pinged."
            )
        # The state machine guards against stale replies: a second captain's
        # PASS after someone already ACCEPTed must not reopen the delivery.
        try:
            self.store.set_match_status(match.id, self._REPLY_TARGETS[parsed.kind])
        except InvalidTransition:
            logger.info("stale %s reply for match %s (already %s)", parsed.kind, match.id, match.status.value)
            return (
                f"Resqio: match {match.id} is already {match.status.value.replace('_', ' ')} "
                "- no change made."
            )
        if parsed.kind == "accept":
            logger.info("match %s APPROVED by captain", match.id)
            return f"Resqio: match {match.id} approved ✔ - reply DELIVERED {match.id} once the drop-off is done. Stay safe."
        if parsed.kind == "pass":
            logger.info("match %s declined; both sides reopened", match.id)
            return f"Resqio: match {match.id} passed - the offer and request are back on the board for re-matching."
        logger.info("match %s DELIVERED", match.id)
        return f"Resqio: delivery {match.id} confirmed 🎉 - thank you."

    # ── Status (dashboard / AgentCore status action) ─────────────────

    def status(self) -> dict:
        return {
            "demo_mode": self.settings.demo_mode,
            # Rosters are private - the unauthenticated dashboard never sees numbers.
            "zones": [z.model_dump(exclude={"captain_numbers"}) for z in self.zones.zones.values()],
            "open_offers": len(self.store.open_offers()),
            "open_requests": len(self.store.open_requests()),
            "pending_matches": [m.model_dump(mode="json") for m in self.store.pending_matches()],
            "total_matches": len(self.store.matches),
            "last_events": [e.model_dump(mode="json") for e in self.monitor.last_events],
            # Full board + latest cycle, for the dashboard.
            "assessment": self.last_report.assessment.model_dump() if self.last_report else None,
            "last_cycle_at": self.last_cycle_at.isoformat() if self.last_cycle_at else None,
            "offers": [o.model_dump(mode="json") for o in self.store.offers.values()],
            "requests": [r.model_dump(mode="json") for r in self.store.requests.values()],
            "matches": [m.model_dump(mode="json") for m in self.store.matches.values()],
            "pings": [p.model_dump(mode="json") for p in self.dispatcher.sent],
        }

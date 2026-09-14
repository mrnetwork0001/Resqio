"""StrandsGridMonitor - Agent 1: 24/7 weather & power-grid crisis detection.

The daemon polls the feeds deterministically (a scheduler's job, not an
LLM's); the Strands agent then reasons over the snapshot - correlating heat
warnings with county outage records via FIPS codes - and returns a validated
``CrisisAssessment``. If Bedrock is unreachable the monitor degrades to a
severity-threshold heuristic: a disaster tool must keep working when the
cloud is having a bad day too.
"""

from __future__ import annotations

import json
import logging

from strands import Agent, tool
from strands.models import BedrockModel

from ..core.config import Settings
from ..core.feeds import GridFeed, WeatherFeed
from ..core.models import CrisisAssessment, CrisisEvent, CrisisSource, Severity

logger = logging.getLogger("resqio.grid_monitor")

SYSTEM_PROMPT = """You are Resqio's Grid & Weather Monitor, the crisis-detection agent for a \
community disaster logistics network. You watch NOAA/NWS weather alerts and county-level power \
outage records for one service area.

Your job each cycle:
1. Judge whether current conditions warrant ACTIVATING community logistics (is_crisis).
2. Rate the situation 0-5 (crisis_level). Compounding hazards matter: an Excessive Heat Warning \
plus a 12,000-customer outage is worse than either alone, because cooling and medical \
refrigeration fail exactly when they are most needed. Correlate weather alerts and outages that \
share county FIPS codes.
3. Summarize for volunteer captains in two plain sentences - no jargon, no drama.

Be conservative: minor advisories with no outages are NOT a crisis. Life-safety combinations \
(extreme heat + outage, hard freeze + outage) are."""


def _events_to_json(events: list[CrisisEvent]) -> str:
    return json.dumps(
        [
            {
                "source": e.source.value,
                "event": e.event,
                "severity": e.severity.value,
                "headline": e.headline,
                "area": e.area_desc,
                "fips": e.fips_codes,
                "customers_out": e.customers_affected,
                "active": e.is_active,
            }
            for e in events
        ],
        indent=2,
    )


def heuristic_assessment(events: list[CrisisEvent]) -> CrisisAssessment:
    """Deterministic severity-threshold fallback used when Bedrock is unreachable."""
    active = [e for e in events if e.is_active]
    if not active:
        return CrisisAssessment(
            is_crisis=False, crisis_level=0, active_hazards=[], affected_areas=[],
            summary="No active weather alerts or grid outages. Monitoring continues.",
        )

    max_rank = max(e.severity.rank for e in active)
    customers_out = sum(e.customers_affected or 0 for e in active)
    sources = {e.source for e in active}
    weather_fips = {f for e in active if e.source == CrisisSource.NOAA for f in e.fips_codes}
    grid_fips = {f for e in active if e.source == CrisisSource.GRID for f in e.fips_codes}
    # NWS SAME codes are 6-digit (leading 0 + county FIPS); EAGLE-I uses 5-digit.
    compounding = bool({f.lstrip("0") for f in weather_fips} & {f.lstrip("0") for f in grid_fips})

    level = {4: 4, 3: 3, 2: 2, 1: 1, 0: 0}[max_rank]
    if customers_out >= 10_000:
        level = max(level, 4)
    if compounding or (len(sources) == 2 and max_rank >= Severity.SEVERE.rank):
        level = min(5, level + 1)

    is_crisis = level >= 3 or customers_out >= 500
    hazards = sorted({e.event for e in active})
    areas = sorted({e.area_desc for e in active if e.area_desc})
    summary = (
        f"{len(active)} active event(s): {', '.join(hazards)}. "
        f"{customers_out:,} customers without power."
        + (" Weather and outage zones overlap - compounding risk." if compounding else "")
    )
    return CrisisAssessment(
        is_crisis=is_crisis, crisis_level=level,
        active_hazards=hazards, affected_areas=areas, summary=summary,
    )


class StrandsGridMonitor:
    """Polls environmental feeds and flags crisis zones."""

    def __init__(self, settings: Settings, weather_feed: WeatherFeed, grid_feed: GridFeed) -> None:
        self._settings = settings
        self._weather_feed = weather_feed
        self._grid_feed = grid_feed
        self.last_events: list[CrisisEvent] = []

        @tool
        def fetch_weather_alerts() -> str:
            """Fetch the latest active NWS weather alerts for the monitored area.

            Returns a JSON list of alerts with event, severity, headline,
            area, and county FIPS codes.
            """
            return _events_to_json(self._safe_fetch_weather())

        @tool
        def fetch_grid_outages() -> str:
            """Fetch the latest county-level power outage records (EAGLE-I schema).

            Returns a JSON list with area, customers_out, and county FIPS codes.
            """
            return _events_to_json(self._safe_fetch_grid())

        self._tools = [fetch_weather_alerts, fetch_grid_outages]

    # ── Feed polling (deterministic; failure = "no change") ──────────

    def _safe_fetch_weather(self) -> list[CrisisEvent]:
        try:
            return self._weather_feed.fetch_active_alerts()
        except Exception as exc:  # noqa: BLE001 - any feed failure means "keep last picture"
            logger.warning("weather feed fetch failed (%s); keeping last known state", exc)
            return [e for e in self.last_events if e.source == CrisisSource.NOAA]

    def _safe_fetch_grid(self) -> list[CrisisEvent]:
        try:
            return self._grid_feed.fetch_outages()
        except Exception as exc:  # noqa: BLE001
            logger.warning("grid feed fetch failed (%s); keeping last known state", exc)
            return [e for e in self.last_events if e.source == CrisisSource.GRID]

    def poll(self) -> list[CrisisEvent]:
        """One polling pass over both feeds. Never raises."""
        events = self._safe_fetch_weather() + self._safe_fetch_grid()
        self.last_events = events
        return events

    # ── Reasoning ────────────────────────────────────────────────────

    def _build_agent(self) -> Agent:
        model = BedrockModel(
            model_id=self._settings.bedrock_model_id,
            region_name=self._settings.aws_region,
            temperature=0.2,
        )
        return Agent(
            name="GridMonitor",
            model=model,
            system_prompt=SYSTEM_PROMPT,
            tools=self._tools,
            callback_handler=None,
        )

    def assess(self, events: list[CrisisEvent] | None = None) -> CrisisAssessment:
        """Assess the current snapshot. LLM reasoning, heuristic on failure."""
        if events is None:
            events = self.poll()
        prompt = (
            "Current feed snapshot (you may re-query with your tools if needed):\n"
            f"{_events_to_json(events)}\n\nProduce your crisis assessment."
        )
        try:
            result = self._build_agent()(prompt, structured_output_model=CrisisAssessment)
            assessment = result.structured_output
            logger.info("LLM assessment: crisis=%s level=%s", assessment.is_crisis, assessment.crisis_level)
            return assessment
        except Exception as exc:  # noqa: BLE001 - degraded mode must always produce an answer
            logger.warning("Bedrock assessment unavailable (%s); using heuristic fallback", exc)
            return heuristic_assessment(events)

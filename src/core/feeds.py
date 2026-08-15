"""Crisis data feeds: NOAA/NWS active alerts + power grid outage sources.

`api.weather.gov` is free and unauthenticated but requires a "(app, contact)"
User-Agent. There is NO free real-time outage feed (EAGLE-I is restricted to
government/utility accounts; poweroutage.us is a paid enterprise API), so the
grid source is pluggable: `SimulatedGridFeed` emits county-level records in
the exact EAGLE-I schema (fips_code, county, state, customers_out,
run_start_time), and a real utility API can implement the same `GridFeed`
protocol later without touching the agents.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Protocol

import httpx

from .config import Settings
from .models import CrisisEvent, CrisisSource, Severity

NWS_ALERTS_URL = "https://api.weather.gov/alerts/active"


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def parse_nws_alerts(payload: dict) -> list[CrisisEvent]:
    """Convert an api.weather.gov GeoJSON alert collection into CrisisEvents.

    Deduplicates on the NWS alert id and honors Cancel messages (a Cancel
    removes the alert from the active picture rather than adding it).
    """
    events: dict[str, CrisisEvent] = {}
    cancelled: set[str] = set()
    for feature in payload.get("features", []):
        props = feature.get("properties", {}) or {}
        external_id = props.get("id") or feature.get("id") or ""
        if (props.get("messageType") or "").lower() == "cancel":
            cancelled.add(external_id)
            continue
        try:
            severity = Severity(props.get("severity") or "Unknown")
        except ValueError:
            severity = Severity.UNKNOWN
        geocode = props.get("geocode") or {}
        events[external_id or f"anon_{len(events)}"] = CrisisEvent(
            external_id=external_id,
            source=CrisisSource.NOAA,
            event=props.get("event", "Unknown Event"),
            severity=severity,
            headline=props.get("headline") or "",
            description=(props.get("description") or "")[:2000],
            area_desc=props.get("areaDesc") or "",
            fips_codes=list(geocode.get("SAME") or []),
            effective=_parse_dt(props.get("effective")),
            # `ends` is when the hazard ends; `expires` is when the message
            # expires. Prefer `ends`, fall back to `expires`.
            expires=_parse_dt(props.get("ends")) or _parse_dt(props.get("expires")),
        )
    return [evt for ext_id, evt in events.items() if ext_id not in cancelled]


class WeatherFeed(Protocol):
    def fetch_active_alerts(self) -> list[CrisisEvent]: ...


class GridFeed(Protocol):
    def fetch_outages(self) -> list[CrisisEvent]: ...


class NOAAAlertFeed:
    """Polls NWS active alerts for a state via api.weather.gov.

    A fetch failure means "no change", never "no alerts" — the daemon must
    not stand down community logistics because the API had a bad minute.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def fetch_active_alerts(self) -> list[CrisisEvent]:
        headers = {
            "User-Agent": self._settings.noaa_user_agent,
            "Accept": "application/geo+json",
        }
        # /alerts/active does NOT accept `limit` (400 if sent).
        params = {
            "area": self._settings.noaa_area,
            "status": "actual",
            "message_type": "alert,update",
        }
        with httpx.Client(timeout=20.0, headers=headers) as client:
            resp = client.get(NWS_ALERTS_URL, params=params)
            resp.raise_for_status()
            return parse_nws_alerts(resp.json())


def severity_for_customers_out(customers_out: int) -> Severity:
    if customers_out >= 10_000:
        return Severity.EXTREME
    if customers_out >= 2_500:
        return Severity.SEVERE
    if customers_out >= 500:
        return Severity.MODERATE
    return Severity.MINOR


class SimulatedGridFeed:
    """Demo grid feed reading EAGLE-I-schema county outage records.

    Fixture shape: {"outages": [{"fips_code", "county", "state",
    "customers_out", "run_start_time", ...optional "cause"}]}
    """

    def __init__(self, fixture_path: Path) -> None:
        self._fixture_path = fixture_path

    def fetch_outages(self) -> list[CrisisEvent]:
        if not self._fixture_path.exists():
            return []
        raw = json.loads(self._fixture_path.read_text())
        events: list[CrisisEvent] = []
        for outage in raw.get("outages", []):
            customers_out = int(outage.get("customers_out", 0))
            county = outage.get("county", "Unknown County")
            state = outage.get("state", "")
            area = f"{county} County, {state}".strip().rstrip(",")
            events.append(
                CrisisEvent(
                    external_id=f"eaglei:{outage.get('fips_code', '')}:{outage.get('run_start_time', '')}",
                    source=CrisisSource.GRID,
                    event=outage.get("event", "Power Outage"),
                    severity=severity_for_customers_out(customers_out),
                    headline=f"{customers_out:,} customers without power — {area}",
                    description=outage.get("cause", ""),
                    area_desc=outage.get("area_detail", area),
                    fips_codes=[outage["fips_code"]] if outage.get("fips_code") else [],
                    effective=_parse_dt(outage.get("run_start_time")),
                    customers_affected=customers_out,
                )
            )
        return events


class StaticAlertFeed:
    """Demo weather feed reading a saved api.weather.gov GeoJSON response.

    Fixtures marked ``"demo_retimestamp": true`` are re-timed to "now" on
    every read, so the demo scenario always looks live instead of expiring
    the day after the fixture was written.
    """

    def __init__(self, fixture_path: Path) -> None:
        self._fixture_path = fixture_path

    def fetch_active_alerts(self) -> list[CrisisEvent]:
        if not self._fixture_path.exists():
            return []
        raw = json.loads(self._fixture_path.read_text())
        events = parse_nws_alerts(raw)
        if raw.get("demo_retimestamp"):
            now = datetime.now(timezone.utc)
            for event in events:
                event.effective = now - timedelta(hours=1)
                event.expires = now + timedelta(hours=6)
        return events


def build_feeds(settings: Settings) -> tuple[WeatherFeed, GridFeed]:
    """Return (weather_feed, grid_feed) honoring demo mode."""
    if settings.demo_mode:
        return (
            StaticAlertFeed(settings.demo_dir / "nws_alerts.json"),
            SimulatedGridFeed(settings.demo_dir / "grid_outages.json"),
        )
    return NOAAAlertFeed(settings), SimulatedGridFeed(settings.demo_dir / "grid_outages.json")

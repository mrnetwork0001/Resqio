import json
from pathlib import Path

from src.core.feeds import (
    SimulatedGridFeed,
    StaticAlertFeed,
    parse_nws_alerts,
    severity_for_customers_out,
)
from src.core.models import CrisisSource, Severity

DEMO_DIR = Path(__file__).resolve().parents[1] / "data" / "demo"


def test_parse_demo_nws_fixture():
    events = StaticAlertFeed(DEMO_DIR / "nws_alerts.json").fetch_active_alerts()
    assert len(events) == 2
    heat = next(e for e in events if e.severity == Severity.EXTREME)
    assert heat.event == "Excessive Heat Warning"
    assert heat.source == CrisisSource.NOAA
    assert "048453" in heat.fips_codes
    assert heat.external_id.startswith("urn:oid:")


def test_parse_dedupes_on_alert_id():
    feature = {
        "properties": {
            "id": "urn:test:1", "event": "Flood Warning", "severity": "Severe",
            "messageType": "Alert", "areaDesc": "X County",
        }
    }
    events = parse_nws_alerts({"features": [feature, feature]})
    assert len(events) == 1


def test_parse_honors_cancel_messages():
    alert = {"properties": {"id": "urn:test:1", "event": "Flood Warning", "severity": "Severe"}}
    cancel = {"properties": {"id": "urn:test:1", "event": "Flood Warning", "messageType": "Cancel"}}
    assert parse_nws_alerts({"features": [alert, cancel]}) == []


def test_parse_prefers_ends_over_expires():
    feature = {
        "properties": {
            "id": "urn:test:2", "event": "Heat Advisory", "severity": "Moderate",
            "ends": "2026-08-15T20:00:00-05:00", "expires": "2026-08-15T18:00:00-05:00",
        }
    }
    (event,) = parse_nws_alerts({"features": [feature]})
    assert event.expires is not None and event.expires.hour == 20


def test_parse_unknown_severity_does_not_crash():
    (event,) = parse_nws_alerts(
        {"features": [{"properties": {"id": "u", "event": "Weirdness", "severity": "Apocalyptic"}}]}
    )
    assert event.severity == Severity.UNKNOWN


def test_simulated_grid_feed_reads_eaglei_schema():
    events = SimulatedGridFeed(DEMO_DIR / "grid_outages.json").fetch_outages()
    assert len(events) == 2
    big = max(events, key=lambda e: e.customers_affected or 0)
    assert big.customers_affected == 12400
    assert big.severity == Severity.EXTREME
    assert big.fips_codes == ["48453"]


def test_grid_severity_ladder():
    assert severity_for_customers_out(50) == Severity.MINOR
    assert severity_for_customers_out(600) == Severity.MODERATE
    assert severity_for_customers_out(3000) == Severity.SEVERE
    assert severity_for_customers_out(20000) == Severity.EXTREME


def test_missing_fixture_returns_empty(tmp_path):
    assert SimulatedGridFeed(tmp_path / "nope.json").fetch_outages() == []
    assert StaticAlertFeed(tmp_path / "nope.json").fetch_active_alerts() == []

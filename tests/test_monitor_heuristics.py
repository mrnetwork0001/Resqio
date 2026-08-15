"""Degraded-mode crisis assessment tests (no Bedrock required)."""

from datetime import datetime, timedelta, timezone

from src.agents.strands_grid_monitor import heuristic_assessment
from src.core.models import CrisisEvent, CrisisSource, Severity


def _weather(severity: Severity, fips: list[str] | None = None, **kwargs) -> CrisisEvent:
    return CrisisEvent(
        source=CrisisSource.NOAA, event=kwargs.pop("event", "Excessive Heat Warning"),
        severity=severity, area_desc="Travis County, TX", fips_codes=fips or [], **kwargs,
    )


def _outage(customers: int, fips: list[str] | None = None) -> CrisisEvent:
    return CrisisEvent(
        source=CrisisSource.GRID, event="Feeder Outage", severity=Severity.SEVERE,
        customers_affected=customers, area_desc="East Austin", fips_codes=fips or [],
    )


def test_calm_when_no_events():
    assessment = heuristic_assessment([])
    assert not assessment.is_crisis
    assert assessment.crisis_level == 0


def test_minor_advisory_alone_is_not_a_crisis():
    assessment = heuristic_assessment([_weather(Severity.MINOR, event="Heat Advisory")])
    assert not assessment.is_crisis


def test_extreme_heat_is_a_crisis():
    assessment = heuristic_assessment([_weather(Severity.EXTREME)])
    assert assessment.is_crisis
    assert assessment.crisis_level >= 4


def test_compounding_heat_plus_outage_escalates():
    heat_only = heuristic_assessment([_weather(Severity.EXTREME, fips=["048453"])])
    compounding = heuristic_assessment(
        [_weather(Severity.EXTREME, fips=["048453"]), _outage(12400, fips=["48453"])]
    )
    assert compounding.crisis_level == 5
    assert compounding.crisis_level > heat_only.crisis_level
    assert "compounding" in compounding.summary.lower()


def test_fips_overlap_handles_leading_zero_difference():
    # NWS SAME codes are 6-digit ("048453"); EAGLE-I county FIPS are 5-digit ("48453").
    assessment = heuristic_assessment(
        [_weather(Severity.SEVERE, fips=["048453"]), _outage(600, fips=["48453"])]
    )
    assert "compounding" in assessment.summary.lower()


def test_expired_events_are_ignored():
    past = datetime.now(timezone.utc) - timedelta(hours=2)
    expired = _weather(Severity.EXTREME, expires=past)
    assessment = heuristic_assessment([expired])
    assert not assessment.is_crisis


def test_outage_alone_reaches_crisis_threshold():
    assessment = heuristic_assessment([_outage(600)])
    assert assessment.is_crisis

"""End-to-end pipeline test in demo mode (no AWS, no Twilio, no network).

The agents' Bedrock calls fail fast without credentials and drop to their
deterministic fallbacks - which is exactly the degraded-mode path this
verifies. With real AWS credentials the same test exercises live reasoning.
"""

import os

import pytest

from src.core.config import Settings
from src.core.models import GeoPoint, MatchStatus
from src.core.store import CommunityStore
from src.orchestrator import ResqioPipeline


@pytest.fixture()
def pipeline(tmp_path, monkeypatch):
    # Guarantee the no-credentials degraded path regardless of the host env.
    for var in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN", "AWS_PROFILE"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("AWS_EC2_METADATA_DISABLED", "true")
    settings = Settings(store_path=tmp_path / "store.json", demo_mode=True)
    return ResqioPipeline(settings=settings, store=CommunityStore(tmp_path / "store.json"))


def _seed_community(pipeline: ResqioPipeline) -> None:
    pipeline.handle_inbound(
        "OFFER: Generator available in Sector 4, 7500W dual fuel.",
        phone="+15125550101", name="Marcus", location=GeoPoint(lat=30.2795, lon=-97.6923),
    )
    pipeline.handle_inbound(
        "HELP: insulin needs refrigeration and our power is out at 42 Maple St. Urgent.",
        phone="+15125550103", name="Amara", location=GeoPoint(lat=30.2764, lon=-97.7041),
    )


def test_full_cycle_produces_match_and_ping(pipeline):
    _seed_community(pipeline)
    report = pipeline.run_cycle()

    assert report.assessment.is_crisis, "demo fixtures must trip crisis detection"
    assert report.assessment.crisis_level == 5  # extreme heat + 12.4k outage, overlapping FIPS
    assert len(report.new_matches) == 1
    assert report.surfaced_to_humans
    match = report.new_matches[0]
    assert match.status == MatchStatus.PENDING_APPROVAL
    assert match.route is not None and match.route.distance_km > 0
    ping = report.pings[0]
    assert f"ACCEPT {match.id}" in ping.message_body
    assert ping.channel == "console"  # demo mode never touches Twilio


def test_quiet_cycle_sends_nothing(pipeline, tmp_path, monkeypatch):
    # Point demo feeds at an empty dir: no events, no crisis, zero pings.
    quiet = Settings(store_path=tmp_path / "s.json", demo_mode=True, demo_dir=tmp_path / "empty")
    quiet_pipeline = ResqioPipeline(settings=quiet, store=CommunityStore(tmp_path / "s.json"))
    report = quiet_pipeline.run_cycle()
    assert not report.assessment.is_crisis
    assert report.pings == []


def test_accept_reply_approves_match(pipeline):
    _seed_community(pipeline)
    match = pipeline.run_cycle().new_matches[0]

    reply = pipeline.handle_inbound(f"ACCEPT {match.id}", phone="+15125550999", name="Captain")
    assert "approved" in reply.lower()
    assert pipeline.store.get_match(match.id).status == MatchStatus.APPROVED

    reply = pipeline.handle_inbound(f"DELIVERED {match.id}", phone="+15125550999", name="Captain")
    assert "confirmed" in reply.lower()
    assert pipeline.store.get_match(match.id).status == MatchStatus.DELIVERED


def test_pass_reply_reopens_for_rematch(pipeline):
    _seed_community(pipeline)
    match = pipeline.run_cycle().new_matches[0]

    pipeline.handle_inbound(f"PASS {match.id}", phone="+15125550999", name="Captain")
    assert pipeline.store.get_match(match.id).status == MatchStatus.DECLINED
    # Both sides back on the board → the next cycle re-matches them.
    rematch_report = pipeline.run_cycle()
    assert len(rematch_report.new_matches) == 1


def test_unknown_match_id_is_handled(pipeline):
    reply = pipeline.handle_inbound("ACCEPT mat_doesnotexist", phone="+1", name="Captain")
    assert "couldn't find" in reply.lower()


def test_status_snapshot(pipeline):
    _seed_community(pipeline)
    status = pipeline.status()
    assert status["open_offers"] == 1
    assert status["open_requests"] == 1
    assert status["demo_mode"] is True

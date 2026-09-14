"""Retention for long-running deployments: dead matches and the ping log stay bounded."""

from datetime import timedelta

import pytest

from src.core.config import Settings
from src.core.models import ApprovalPing, Match, MatchStatus, utcnow
from src.core.store import CommunityStore
from src.orchestrator import ResqioPipeline


@pytest.fixture(autouse=True)
def _no_cloud(monkeypatch):
    # .env may hold real AWS keys; keep these tests on the offline paths.
    for var in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN", "AWS_PROFILE"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("AWS_EC2_METADATA_DISABLED", "true")


def _match_in(store: CommunityStore, offer_id: str, request_id: str, status: MatchStatus, age_hours: float) -> Match:
    match = store.record_match(Match(offer_id=offer_id, request_id=request_id))
    path = {
        MatchStatus.EXPIRED: [MatchStatus.EXPIRED],
        MatchStatus.DECLINED: [MatchStatus.DECLINED],
        MatchStatus.PENDING_APPROVAL: [MatchStatus.PENDING_APPROVAL],
        MatchStatus.DELIVERED: [MatchStatus.PENDING_APPROVAL, MatchStatus.APPROVED, MatchStatus.DELIVERED],
    }[status]
    for step in path:
        store.set_match_status(match.id, step)
    match.created_at = utcnow() - timedelta(hours=age_hours)
    return match


def test_prune_removes_only_old_dead_matches(seeded_store):
    old_expired = _match_in(seeded_store, "off_generator1", "req_insulin1", MatchStatus.EXPIRED, age_hours=10)
    old_declined = _match_in(seeded_store, "off_generator1", "req_insulin1", MatchStatus.DECLINED, age_hours=10)
    fresh_expired = _match_in(seeded_store, "off_generator1", "req_insulin1", MatchStatus.EXPIRED, age_hours=1)
    old_delivered = _match_in(seeded_store, "off_ice1", "req_infant1", MatchStatus.DELIVERED, age_hours=10)

    removed = seeded_store.prune_closed_matches(utcnow() - timedelta(hours=6))

    assert removed == 2
    assert old_expired.id not in seeded_store.matches
    assert old_declined.id not in seeded_store.matches
    assert fresh_expired.id in seeded_store.matches
    assert old_delivered.id in seeded_store.matches  # delivery history is kept


def test_prune_persists_to_disk(seeded_store):
    old = _match_in(seeded_store, "off_generator1", "req_insulin1", MatchStatus.EXPIRED, age_hours=10)
    seeded_store._save()  # persist the backdated timestamp
    seeded_store.prune_closed_matches(utcnow() - timedelta(hours=6))
    assert old.id not in CommunityStore(seeded_store._path).matches


def test_pending_matches_are_never_pruned(seeded_store):
    pending = _match_in(seeded_store, "off_generator1", "req_insulin1", MatchStatus.PENDING_APPROVAL, age_hours=48)
    assert seeded_store.prune_closed_matches(utcnow()) == 0
    assert pending.id in seeded_store.matches


def test_cycle_prunes_dead_matches_and_caps_ping_log(tmp_path, seeded_store):
    settings = Settings(store_path=tmp_path / "store.json", demo_mode=True,
                        match_retention_hours=6, ping_log_limit=2)
    pipeline = ResqioPipeline(settings=settings, store=seeded_store)
    old = _match_in(seeded_store, "off_generator1", "req_insulin1", MatchStatus.EXPIRED, age_hours=10)
    pipeline.dispatcher.sent.extend(
        ApprovalPing(match_id=f"mat_{i}", captain_phone="console", message_body="x") for i in range(5)
    )

    report = pipeline.run_cycle()

    assert old.id not in pipeline.store.matches
    # the cap applies before this cycle's pings are appended
    assert len(pipeline.dispatcher.sent) == 2 + len(report.pings)
    assert [p.match_id for p in pipeline.dispatcher.sent[:2]] == ["mat_3", "mat_4"]


def test_zero_disables_retention(tmp_path, seeded_store):
    settings = Settings(store_path=tmp_path / "store.json", demo_mode=True,
                        match_retention_hours=0, ping_log_limit=0)
    pipeline = ResqioPipeline(settings=settings, store=seeded_store)
    old = _match_in(seeded_store, "off_generator1", "req_insulin1", MatchStatus.EXPIRED, age_hours=500)
    pipeline.dispatcher.sent.extend(
        ApprovalPing(match_id=f"mat_{i}", captain_phone="console", message_body="x") for i in range(5)
    )
    pipeline.run_cycle()
    assert old.id in pipeline.store.matches
    assert len(pipeline.dispatcher.sent) >= 5

import pytest

from src.core.models import Match, MatchStatus, EntryStatus
from src.core.store import CommunityStore


def test_open_requests_sorted_by_urgency(seeded_store):
    requests = seeded_store.open_requests()
    assert [r.id for r in requests] == ["req_insulin1", "req_infant1"]


def test_record_match_marks_both_sides_matched(seeded_store):
    seeded_store.record_match(Match(offer_id="off_generator1", request_id="req_insulin1"))
    assert seeded_store.offers["off_generator1"].status == EntryStatus.MATCHED
    assert seeded_store.requests["req_insulin1"].status == EntryStatus.MATCHED
    assert "off_generator1" not in {o.id for o in seeded_store.open_offers()}


def test_record_match_rejects_unknown_ids(seeded_store):
    with pytest.raises(KeyError):
        seeded_store.record_match(Match(offer_id="off_ghost", request_id="req_insulin1"))


def test_declined_match_reopens_both_sides(seeded_store):
    match = seeded_store.record_match(Match(offer_id="off_generator1", request_id="req_insulin1"))
    seeded_store.set_match_status(match.id, MatchStatus.DECLINED)
    assert seeded_store.offers["off_generator1"].status == EntryStatus.OPEN
    assert seeded_store.requests["req_insulin1"].status == EntryStatus.OPEN


def test_delivered_match_closes_both_sides(seeded_store):
    match = seeded_store.record_match(Match(offer_id="off_generator1", request_id="req_insulin1"))
    seeded_store.set_match_status(match.id, MatchStatus.DELIVERED)
    assert seeded_store.offers["off_generator1"].status == EntryStatus.CLOSED
    assert seeded_store.requests["req_insulin1"].status == EntryStatus.CLOSED


def test_persistence_roundtrip(tmp_path, seeded_store):
    match = seeded_store.record_match(Match(offer_id="off_ice1", request_id="req_insulin1"))
    seeded_store.set_match_status(match.id, MatchStatus.PENDING_APPROVAL)

    reloaded = CommunityStore(seeded_store._path)
    assert set(reloaded.offers) == set(seeded_store.offers)
    assert reloaded.get_match(match.id).status == MatchStatus.PENDING_APPROVAL
    assert reloaded.pending_matches()[0].id == match.id


def test_set_status_on_unknown_match_raises(store):
    with pytest.raises(KeyError):
        store.set_match_status("mat_ghost", MatchStatus.APPROVED)

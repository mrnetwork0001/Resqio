"""Regression tests for the confirmed adversarial-review findings."""

from datetime import timedelta

import pytest

from src.agents.strands_resource_matcher import heuristic_parse
from src.core.models import (
    Match,
    MatchStatus,
    EntryStatus,
    ParsedInboundMessage,
    ResourceType,
    utcnow,
)
from src.core.store import CommunityStore, InvalidTransition


# ── Match state machine (PASS-after-ACCEPT double-booking) ───────────


def _pending_match(store) -> Match:
    match = store.record_match(Match(offer_id="off_generator1", request_id="req_insulin1"))
    store.set_match_status(match.id, MatchStatus.PENDING_APPROVAL)
    return match


def test_pass_after_accept_is_rejected(seeded_store):
    match = _pending_match(seeded_store)
    seeded_store.set_match_status(match.id, MatchStatus.APPROVED)
    with pytest.raises(InvalidTransition):
        seeded_store.set_match_status(match.id, MatchStatus.DECLINED)
    # The in-flight delivery is untouched.
    assert seeded_store.get_match(match.id).status == MatchStatus.APPROVED
    assert seeded_store.offers["off_generator1"].status == EntryStatus.MATCHED


def test_accept_after_delivered_is_rejected(seeded_store):
    match = _pending_match(seeded_store)
    seeded_store.set_match_status(match.id, MatchStatus.APPROVED)
    seeded_store.set_match_status(match.id, MatchStatus.DELIVERED)
    with pytest.raises(InvalidTransition):  # delayed webhook retry
        seeded_store.set_match_status(match.id, MatchStatus.APPROVED)


def test_delivered_requires_approval_first(seeded_store):
    match = _pending_match(seeded_store)
    with pytest.raises(InvalidTransition):
        seeded_store.set_match_status(match.id, MatchStatus.DELIVERED)


def test_stale_decline_does_not_touch_rebooked_entries(seeded_store):
    # match1 declined -> entries reopen -> match2 books them. A later
    # operation on match1's entries must not disturb match2's booking.
    match1 = _pending_match(seeded_store)
    seeded_store.set_match_status(match1.id, MatchStatus.DECLINED)
    match2 = _pending_match(seeded_store)
    assert seeded_store.offers["off_generator1"].status == EntryStatus.MATCHED
    assert seeded_store.get_match(match2.id).status == MatchStatus.PENDING_APPROVAL


# ── TOCTOU: record_match re-verifies OPEN under the lock ─────────────


def test_record_match_rejects_already_matched_offer(seeded_store):
    seeded_store.record_match(Match(offer_id="off_generator1", request_id="req_insulin1"))
    with pytest.raises(InvalidTransition):
        seeded_store.record_match(Match(offer_id="off_generator1", request_id="req_infant1"))


# ── Store durability ─────────────────────────────────────────────────


def test_corrupt_store_file_quarantined_not_fatal(tmp_path):
    path = tmp_path / "store.json"
    path.write_text("{not valid json!!")
    store = CommunityStore(path)
    assert store.offers == {} and store.matches == {}
    assert list(tmp_path.glob("store.json.corrupt-*")), "corrupt file should be quarantined"


def test_one_bad_record_does_not_discard_the_rest(tmp_path, seeded_store):
    import json

    raw = json.loads(seeded_store._path.read_text())
    raw["offers"].append({"id": "off_bad", "resource_type": "spaceship"})
    seeded_store._path.write_text(json.dumps(raw))
    reloaded = CommunityStore(seeded_store._path)
    assert "off_generator1" in reloaded.offers
    assert "off_bad" not in reloaded.offers


# ── Parser fixes ─────────────────────────────────────────────────────


def test_pass_mention_without_leading_verb_or_id_is_not_a_reply():
    parsed = heuristic_parse("Can you pass this along? We need water at 12 Elm St")
    assert parsed.kind == "request"
    assert parsed.resource_type == ResourceType.WATER


def test_delivered_mention_in_offer_is_not_a_reply():
    parsed = heuristic_parse("I have meals that can be delivered, plenty available")
    assert parsed.kind == "offer"


def test_office_is_not_ice():
    parsed = heuristic_parse("HELP: stuck at my office, need a ride home")
    assert parsed.resource_type == ResourceType.TRANSPORT


def test_oak_drive_address_is_not_transport():
    parsed = heuristic_parse("OFFER: spare fan at 8 Oak Court")
    assert parsed.resource_type == ResourceType.SHELTER


def test_reply_with_id_anywhere_still_works():
    parsed = heuristic_parse("yes I ACCEPT mat_ab12cd34ef thanks")
    assert parsed.kind == "accept"
    assert parsed.match_id == "mat_ab12cd34ef"


# ── LLM structured-output hardening ──────────────────────────────────


def test_llm_kind_capitalization_is_normalized():
    parsed = ParsedInboundMessage(kind="Offer")
    assert parsed.kind == "offer"


def test_llm_invalid_kind_falls_to_unknown():
    parsed = ParsedInboundMessage(kind="reply")
    assert parsed.kind == "unknown"


def test_llm_match_id_is_case_normalized():
    parsed = ParsedInboundMessage(kind="accept", match_id="  MAT_AB12CD34EF ")
    assert parsed.match_id == "mat_ab12cd34ef"


# ── Match TTL expiry ─────────────────────────────────────────────────


def test_stale_pending_match_expires_and_reopens(tmp_path, monkeypatch):
    from src.core.config import Settings
    from src.orchestrator import ResqioPipeline

    for var in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN", "AWS_PROFILE"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("AWS_EC2_METADATA_DISABLED", "true")

    settings = Settings(store_path=tmp_path / "s.json", demo_mode=True, match_ttl_minutes=45)
    pipeline = ResqioPipeline(settings=settings, store=CommunityStore(tmp_path / "s.json"))
    from src.core.models import GeoPoint

    pipeline.handle_inbound("OFFER: generator available", phone="+1", name="M",
                            location=GeoPoint(lat=30.28, lon=-97.69))
    pipeline.handle_inbound("HELP: insulin needs refrigeration at 42 Maple St urgent", phone="+2", name="A",
                            location=GeoPoint(lat=30.27, lon=-97.70))
    match = pipeline.run_cycle().new_matches[0]

    # Backdate the ping and run another cycle: the match expires, both sides
    # reopen, and the next cycle re-matches them.
    pipeline.store.matches[match.id].created_at = utcnow() - timedelta(minutes=90)
    report = pipeline.run_cycle()
    assert pipeline.store.get_match(match.id).status == MatchStatus.EXPIRED
    assert len(report.new_matches) == 1
    assert report.new_matches[0].id != match.id


# ── Stale captain replies get an informative answer ──────────────────


def test_second_captain_pass_after_accept_gets_no_change_reply(tmp_path, monkeypatch):
    from src.core.config import Settings
    from src.core.models import GeoPoint
    from src.orchestrator import ResqioPipeline

    for var in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN", "AWS_PROFILE"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("AWS_EC2_METADATA_DISABLED", "true")

    settings = Settings(store_path=tmp_path / "s.json", demo_mode=True)
    pipeline = ResqioPipeline(settings=settings, store=CommunityStore(tmp_path / "s.json"))
    pipeline.handle_inbound("OFFER: generator available", phone="+1", name="M",
                            location=GeoPoint(lat=30.28, lon=-97.69))
    pipeline.handle_inbound("HELP: insulin needs refrigeration urgent", phone="+2", name="A",
                            location=GeoPoint(lat=30.27, lon=-97.70))
    match = pipeline.run_cycle().new_matches[0]

    assert "approved" in pipeline.handle_inbound(f"ACCEPT {match.id}", name="Captain A").lower()
    reply = pipeline.handle_inbound(f"PASS {match.id}", name="Captain B")
    assert "already approved" in reply.lower()
    assert pipeline.store.get_match(match.id).status == MatchStatus.APPROVED
    # No double-booking: the offer stays with the accepted delivery.
    assert pipeline.run_cycle().new_matches == []

"""Captain phone numbers never appear in full in logs, console output, or the public /status."""

import logging

from src.core.config import Settings
from src.core.models import ApprovalPing
from src.core.store import CommunityStore
from src.integrations.twilio_whatsapp_dispatcher import TwilioWhatsAppDispatcher

CAPTAIN = "whatsapp:+2348012345678"
DIGITS = "+2348012345678"
FAKE_TWILIO = dict(
    twilio_account_sid="AC" + "0" * 32,
    twilio_auth_token="0" * 32,
    captain_numbers=(CAPTAIN,),
)


def test_masked_formats():
    m = TwilioWhatsAppDispatcher.masked
    assert m(CAPTAIN) == "whatsapp:+234…678"
    assert m("+15550000001") == "+155…001"
    assert m("console") == "console"
    assert m("") == ""
    assert m("+1234") == "***"


class _FailingTwilio:
    class messages:
        @staticmethod
        def create(**kwargs):
            # Provider errors can echo the destination number back.
            raise RuntimeError(f"The 'To' number {kwargs['to']} is not a valid WhatsApp number")


def test_failed_send_never_logs_or_prints_full_number(caplog, capsys):
    dispatcher = TwilioWhatsAppDispatcher(Settings(demo_mode=True, real_pings=True, **FAKE_TWILIO))
    dispatcher._client = _FailingTwilio()

    with caplog.at_level(logging.INFO, logger="resqio.dispatcher"):
        pings = dispatcher.send_approval_ping("mat_x", "test ping")
    printed = capsys.readouterr().out

    assert pings[0].channel == "console"  # fell back, match not stranded
    assert DIGITS not in caplog.text
    assert DIGITS not in printed
    assert "+234…678" in caplog.text
    assert "+234…678" in printed


def test_status_masks_ping_numbers_but_keeps_them_internally(tmp_path):
    from src.orchestrator import ResqioPipeline

    settings = Settings(store_path=tmp_path / "store.json", demo_mode=True)
    pipeline = ResqioPipeline(settings=settings, store=CommunityStore(tmp_path / "store.json"))
    pipeline.dispatcher.sent.append(ApprovalPing(match_id="mat_x", captain_phone=CAPTAIN, message_body="x"))

    shown = pipeline.status()["pings"][0]["captain_phone"]
    assert shown == "whatsapp:+234…678"
    assert pipeline.dispatcher.sent[0].captain_phone == CAPTAIN  # still sendable

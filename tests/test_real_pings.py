"""When the dispatcher sends real Twilio messages vs. rendering to the console."""

import os

from src.core.config import Settings
from src.integrations.twilio_whatsapp_dispatcher import TwilioWhatsAppDispatcher

FAKE_TWILIO = dict(
    twilio_account_sid="AC" + "0" * 32,
    twilio_auth_token="0" * 32,
    captain_numbers=("whatsapp:+15550000001",),
)


def test_demo_mode_stays_console_by_default():
    dispatcher = TwilioWhatsAppDispatcher(Settings(demo_mode=True, **FAKE_TWILIO))
    assert not dispatcher.live


def test_real_pings_enable_twilio_in_demo_mode():
    dispatcher = TwilioWhatsAppDispatcher(Settings(demo_mode=True, real_pings=True, **FAKE_TWILIO))
    assert dispatcher.live


def test_live_mode_uses_twilio_when_configured():
    dispatcher = TwilioWhatsAppDispatcher(Settings(demo_mode=False, **FAKE_TWILIO))
    assert dispatcher.live


def test_real_pings_without_credentials_stays_console():
    dispatcher = TwilioWhatsAppDispatcher(Settings(demo_mode=True, real_pings=True,
                                                   twilio_account_sid="", twilio_auth_token="",
                                                   captain_numbers=()))
    assert not dispatcher.live


def test_guard_strips_real_credentials_from_test_environment():
    # conftest's autouse fixture must keep a real .env from reaching tests.
    for var in ("TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "RESQIO_CAPTAIN_NUMBERS",
                "RESQIO_REAL_PINGS", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"):
        assert var not in os.environ
    assert not TwilioWhatsAppDispatcher(Settings(demo_mode=True)).live

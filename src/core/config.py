"""Environment-driven configuration for Resqio.

Everything defaults to demo-safe values so `python -m src.demo` runs with no
AWS/Twilio credentials at all; production values come from `.env`. All env
reads happen at instantiation time (default_factory), so `get_settings()`
always reflects the current environment.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default)


def _bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    # AWS / Bedrock
    aws_region: str = field(default_factory=lambda: _env("AWS_REGION", "us-east-1"))
    bedrock_model_id: str = field(
        default_factory=lambda: _env("BEDROCK_MODEL_ID", "global.anthropic.claude-sonnet-4-6")
    )

    # NOAA polling
    noaa_area: str = field(default_factory=lambda: _env("NOAA_AREA", "TX"))
    noaa_user_agent: str = field(
        default_factory=lambda: _env(
            "NOAA_USER_AGENT", "(resqio-community-disaster-agent, contact@example.com)"
        )
    )
    poll_interval_seconds: int = field(
        default_factory=lambda: int(_env("POLL_INTERVAL_SECONDS", "300"))
    )

    # Twilio
    twilio_account_sid: str = field(default_factory=lambda: _env("TWILIO_ACCOUNT_SID", ""))
    twilio_auth_token: str = field(default_factory=lambda: _env("TWILIO_AUTH_TOKEN", ""))
    twilio_whatsapp_from: str = field(
        default_factory=lambda: _env("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
    )
    twilio_sms_from: str = field(default_factory=lambda: _env("TWILIO_SMS_FROM", ""))
    captain_numbers: tuple[str, ...] = field(
        default_factory=lambda: tuple(
            n.strip() for n in _env("RESQIO_CAPTAIN_NUMBERS", "").split(",") if n.strip()
        )
    )

    # Behavior
    demo_mode: bool = field(default_factory=lambda: _bool("RESQIO_DEMO_MODE", True))
    match_ttl_minutes: int = field(
        default_factory=lambda: int(_env("RESQIO_MATCH_TTL_MINUTES", "45"))
    )
    store_path: Path = field(default_factory=lambda: PROJECT_ROOT / "data" / "store.json")
    demo_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "data" / "demo")

    @property
    def twilio_configured(self) -> bool:
        return bool(self.twilio_account_sid and self.twilio_auth_token and self.captain_numbers)


def get_settings() -> Settings:
    """Read settings fresh from the environment (cheap; call freely)."""
    return Settings()

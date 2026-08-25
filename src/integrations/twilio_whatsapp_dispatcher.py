"""Twilio WhatsApp/SMS dispatcher — Resqio's ONLY outward-facing surface.

The agent pipeline runs 100% silently; this module fires exactly one kind of
outbound message: an approval ping to volunteer captains when a delivery
match needs a human yes/no. In demo mode (or with Twilio unconfigured) pings
render to the console so the full loop is demonstrable with zero credentials.

WhatsApp notes (Twilio Content API rules):
- Free-form ``body=`` sends only work inside the 24-hour session window a
  captain opens by messaging the number (or joining the sandbox). Captains
  are onboarded by texting the sandbox join code, which opens that window.
- For business-initiated pings outside the window, set
  ``TWILIO_CONTENT_SID`` to an approved ``twilio/quick-reply`` template with
  an ``{{1}}`` body variable; we then send via content_sid with the ping text
  as the variable, and button taps arrive as ``ButtonPayload``.
"""

from __future__ import annotations

import json
import logging
import os

from ..core.config import Settings
from ..core.models import ApprovalPing

logger = logging.getLogger("resqio.dispatcher")


class TwilioWhatsAppDispatcher:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = None
        if settings.twilio_configured and not settings.demo_mode:
            from twilio.rest import Client  # imported lazily so demo mode needs no Twilio at all

            self._client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        self.sent: list[ApprovalPing] = []  # session log; the dashboard reads this

    @property
    def live(self) -> bool:
        return self._client is not None

    # ── Outbound ─────────────────────────────────────────────────────

    def send_approval_ping(
        self, match_id: str, message_body: str, captains: tuple[str, ...] | None = None
    ) -> list[ApprovalPing]:
        """Ping the given captains (a zone roster), falling back to the
        global list, then to the console. Returns the pings actually sent."""
        pings: list[ApprovalPing] = []
        captains = captains or self._settings.captain_numbers or ("console",)
        for captain in captains:
            sendable = (
                self.live
                and captain != "console"
                # An SMS captain with no SMS sender configured can't be reached.
                and (captain.startswith("whatsapp:") or bool(self._settings.twilio_sms_from))
            )
            if sendable:
                try:
                    ping = self._send_via_twilio(match_id, captain, message_body)
                except Exception as exc:  # noqa: BLE001 — one bad number must not strand the match
                    logger.error("Twilio send to %s failed (%s); falling back to console", captain, exc)
                    ping = self._send_via_console(match_id, captain, message_body)
            else:
                ping = self._send_via_console(match_id, captain, message_body)
            pings.append(ping)
            self.sent.append(ping)
        return pings

    def _send_via_twilio(self, match_id: str, captain: str, body: str) -> ApprovalPing:
        is_whatsapp = captain.startswith("whatsapp:")
        from_ = self._settings.twilio_whatsapp_from if is_whatsapp else self._settings.twilio_sms_from
        content_sid = os.environ.get("TWILIO_CONTENT_SID", "")
        kwargs: dict = {"from_": from_, "to": captain}
        if is_whatsapp and content_sid:
            # Approved quick-reply template ({{1}} = ping text) for
            # business-initiated sends outside the 24-h session window.
            kwargs["content_sid"] = content_sid
            kwargs["content_variables"] = json.dumps({"1": body})  # must be a JSON *string*
        else:
            kwargs["body"] = body
        message = self._client.messages.create(**kwargs)
        logger.info("ping sent to %s (sid=%s, status=%s)", captain, message.sid, message.status)
        return ApprovalPing(
            match_id=match_id,
            captain_phone=captain,
            message_body=body,
            channel="whatsapp" if is_whatsapp else "sms",
        )

    def _send_via_console(self, match_id: str, captain: str, body: str) -> ApprovalPing:
        print("\n" + "═" * 62)
        print("📱  VOLUNTEER CAPTAIN PING" + (f"  →  {captain}" if captain != "console" else "  (demo console)"))
        print("─" * 62)
        print(body)
        print("═" * 62)
        return ApprovalPing(match_id=match_id, captain_phone=captain, message_body=body, channel="console")

    # ── Inbound (webhook form → normalized reply) ────────────────────

    @staticmethod
    def parse_inbound_form(form: dict) -> dict:
        """Normalize a Twilio inbound webhook POST (SMS or WhatsApp).

        Quick-reply button taps arrive as ButtonPayload/ButtonText; match on
        ButtonPayload when present, else on Body.
        """
        return {
            "from": form.get("From", ""),
            "profile_name": form.get("ProfileName", ""),
            "body": form.get("Body", ""),
            "button_payload": form.get("ButtonPayload", ""),
            "latitude": form.get("Latitude"),
            "longitude": form.get("Longitude"),
        }

    @staticmethod
    def twiml_reply(text: str) -> str:
        """Build a TwiML response (must be served with Content-Type text/xml)."""
        from twilio.twiml.messaging_response import MessagingResponse

        response = MessagingResponse()
        if text:
            response.message(text)
        return str(response)

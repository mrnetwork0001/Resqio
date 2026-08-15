"""Twilio inbound webhook server (SMS + WhatsApp) — the single local live runtime.

    python -m src.integrations.webhook_server   # serves :5001 AND runs the poll loop

This process owns the community store: it ingests inbound messages on
POST /sms and runs the background monitor→match→route→ping loop on an
embedded thread (disable with RESQIO_POLL_IN_WEBHOOK=0). Do NOT run
`python -m src.daemon` against the same store file at the same time — the
JSON-snapshot store is single-writer, and two processes would silently
overwrite each other's board.

Point the Twilio number / WhatsApp Sandbox "When a message comes in" URL at
POST /sms (expose locally with `ngrok http 5001`). Validates the
X-Twilio-Signature when TWILIO_AUTH_TOKEN is set, so a random POST can't
inject offers or approve matches; behind a proxy set RESQIO_WEBHOOK_URL to
the exact public URL Twilio calls, since signatures are computed over it.
"""

from __future__ import annotations

import logging
import os
import threading
import time

import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route

from ..core.models import GeoPoint
from ..orchestrator import ResqioPipeline
from .twilio_whatsapp_dispatcher import TwilioWhatsAppDispatcher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("resqio.webhook")

pipeline = ResqioPipeline()


def _signature_valid(request: Request, form: dict) -> bool:
    token = pipeline.settings.twilio_auth_token
    if not token:
        return True  # demo mode: no token configured, nothing to validate against
    from twilio.request_validator import RequestValidator

    url = os.environ.get("RESQIO_WEBHOOK_URL", str(request.url))
    signature = request.headers.get("X-Twilio-Signature", "")
    return RequestValidator(token).validate(url, form, signature)


async def inbound_sms(request: Request) -> Response:
    form = dict((await request.form()).items())
    if not _signature_valid(request, form):
        logger.warning("rejected webhook POST with bad/missing Twilio signature")
        return Response("forbidden", status_code=403)

    normalized = TwilioWhatsAppDispatcher.parse_inbound_form(form)
    body = normalized["button_payload"] or normalized["body"]  # button taps carry the payload
    location = None
    if normalized["latitude"] and normalized["longitude"]:
        location = GeoPoint(lat=float(normalized["latitude"]), lon=float(normalized["longitude"]))

    reply = pipeline.handle_inbound(
        body=body,
        phone=normalized["from"],
        name=normalized["profile_name"] or "neighbor",
        location=location,
    )
    return Response(TwilioWhatsAppDispatcher.twiml_reply(reply), media_type="text/xml")


app = Starlette(routes=[Route("/sms", inbound_sms, methods=["POST"])])


def _poll_loop() -> None:
    interval = pipeline.settings.poll_interval_seconds
    logger.info("embedded poll loop up (every %ss)", interval)
    while True:
        try:
            report = pipeline.run_cycle()
            logger.info(
                "cycle: crisis=%s level=%d matches=%d pings=%d",
                report.assessment.is_crisis, report.assessment.crisis_level,
                len(report.new_matches), len(report.pings),
            )
        except Exception:  # noqa: BLE001 — the 24/7 loop survives any single bad cycle
            logger.exception("cycle failed; continuing")
        time.sleep(interval)


if __name__ == "__main__":
    if os.environ.get("RESQIO_POLL_IN_WEBHOOK", "1") == "1":
        threading.Thread(target=_poll_loop, daemon=True, name="resqio-poll").start()
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("RESQIO_WEBHOOK_PORT", "5001")))

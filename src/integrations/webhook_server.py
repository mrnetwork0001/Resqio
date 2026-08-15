"""Twilio inbound webhook server (SMS + WhatsApp).

    python -m src.integrations.webhook_server   # serves :5001

Point the Twilio number / WhatsApp Sandbox "When a message comes in" URL at
POST /sms (expose locally with `ngrok http 5001`). Validates the
X-Twilio-Signature when TWILIO_AUTH_TOKEN is set, so a random POST can't
inject offers or approve matches.
"""

from __future__ import annotations

import logging
import os

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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("RESQIO_WEBHOOK_PORT", "5001")))

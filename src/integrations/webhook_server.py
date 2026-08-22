"""Twilio inbound webhook + dashboard API server — the single local live runtime.

    python -m src.integrations.webhook_server   # serves :5001 AND runs the poll loop

This process owns the community store: it ingests inbound messages on
POST /sms, serves the Next.js dashboard's JSON API, and runs the background
monitor→match→route→ping loop on an embedded thread (disable with
RESQIO_POLL_IN_WEBHOOK=0). Do NOT run `python -m src.daemon` against the
same store file at the same time — the JSON-snapshot store is single-writer,
and two processes would silently overwrite each other's board.

Routes:
    POST /sms            Twilio inbound (signature-validated when a token is set)
    GET  /status         full situation snapshot for the dashboard
    POST /cycle          run one monitor→match→route→ping pass now
    POST /demo/seed      demo mode only: ingest the fixture community texts
    POST /demo/inbound   demo mode only: {"body": "...", "name": "..."} → reply
    POST /demo/reset     demo mode only: clear the board for a fresh run

Point the Twilio number / WhatsApp Sandbox "When a message comes in" URL at
POST /sms (expose locally with `ngrok http 5001`). Behind a proxy set
RESQIO_WEBHOOK_URL to the exact public URL Twilio calls, since signatures
are computed over it.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time

import uvicorn
from starlette.applications import Starlette
from starlette.concurrency import run_in_threadpool
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
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

    reply = await run_in_threadpool(
        pipeline.handle_inbound,
        body,
        normalized["from"],
        normalized["profile_name"] or "neighbor",
        location,
    )
    return Response(TwilioWhatsAppDispatcher.twiml_reply(reply), media_type="text/xml")


# ── Dashboard API ────────────────────────────────────────────────────


async def get_status(request: Request) -> JSONResponse:
    return JSONResponse(pipeline.status())


async def run_cycle_now(request: Request) -> JSONResponse:
    report = await run_in_threadpool(pipeline.run_cycle)
    return JSONResponse(report.to_dict())


def _demo_only() -> JSONResponse | None:
    if not pipeline.settings.demo_mode:
        return JSONResponse({"error": "demo endpoints are disabled outside demo mode"}, status_code=403)
    return None


async def demo_seed(request: Request) -> JSONResponse:
    if (blocked := _demo_only()) is not None:
        return blocked
    if pipeline.store.offers or pipeline.store.requests:
        return JSONResponse({"seeded": 0, "note": "board already has entries — reset first"})
    fixture = pipeline.settings.demo_dir / "community_messages.json"
    messages = json.loads(fixture.read_text())["messages"]
    seeded = []
    for msg in messages:
        location = GeoPoint(lat=msg["lat"], lon=msg["lon"]) if "lat" in msg else None
        reply = await run_in_threadpool(
            pipeline.handle_inbound, msg["body"], msg["from"], msg["name"], location
        )
        seeded.append({"from": msg["name"], "body": msg["body"], "reply": reply})
    return JSONResponse({"seeded": len(seeded), "messages": seeded})


async def demo_inbound(request: Request) -> JSONResponse:
    if (blocked := _demo_only()) is not None:
        return blocked
    try:
        data = await request.json()
    except Exception:  # noqa: BLE001
        return JSONResponse({"error": "body must be JSON"}, status_code=400)
    body = (data or {}).get("body", "").strip()
    if not body:
        return JSONResponse({"error": "missing 'body'"}, status_code=400)
    reply = await run_in_threadpool(
        pipeline.handle_inbound, body, data.get("phone", "+15125550000"), data.get("name", "dashboard")
    )
    return JSONResponse({"reply": reply})


async def demo_reset(request: Request) -> JSONResponse:
    if (blocked := _demo_only()) is not None:
        return blocked
    pipeline.store.clear()
    pipeline.dispatcher.sent.clear()
    pipeline.last_report = None
    pipeline.last_cycle_at = None
    return JSONResponse({"reset": True})


app = Starlette(
    routes=[
        Route("/sms", inbound_sms, methods=["POST"]),
        Route("/status", get_status, methods=["GET"]),
        Route("/cycle", run_cycle_now, methods=["POST"]),
        Route("/demo/seed", demo_seed, methods=["POST"]),
        Route("/demo/inbound", demo_inbound, methods=["POST"]),
        Route("/demo/reset", demo_reset, methods=["POST"]),
    ]
)
# The dashboard dev server runs on another port; the API carries no secrets.
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


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

"""End-to-end demo: the Austin heatwave scenario.

    python -m src.demo

Runs the full autonomous loop against the bundled fixtures — an Excessive
Heat Warning colliding with a 12,400-customer feeder outage in East Austin —
with community SMS traffic seeded from data/demo/community_messages.json.
Zero credentials needed: without AWS/Bedrock access the agents drop to their
deterministic degraded-mode logic; with credentials you see full LLM
reasoning. Twilio pings render to the console either way.
"""

from __future__ import annotations

import json
import logging
import tempfile
from pathlib import Path

from .core.config import get_settings
from .core.models import GeoPoint
from .core.store import CommunityStore
from .orchestrator import ResqioPipeline

logging.basicConfig(level=logging.WARNING)
# Degraded-mode fallbacks are by design, not an error condition — one
# intentional notice in the banner replaces a wall of per-call warnings.
logging.getLogger("resqio").setLevel(logging.ERROR)


def banner(text: str) -> None:
    print(f"\n\n🚨 {text}")
    print("─" * 70)


def main() -> None:
    settings = get_settings()
    # Fresh store per demo run so reruns are deterministic.
    store = CommunityStore(Path(tempfile.mkdtemp()) / "demo_store.json")
    pipeline = ResqioPipeline(settings=settings, store=store)

    print("=" * 70)
    print("  RESQIO — Autonomous Community Disaster & Crisis Logistics Agent")
    print("  Scenario: Austin heatwave + Sector 4 feeder outage")
    print("  ℹ Without AWS credentials the agents run their deterministic")
    print("    degraded mode — by design; with credentials, live Bedrock reasoning.")
    print("=" * 70)

    banner("PHASE 1 — Community members text the Resqio number")
    messages = json.loads((settings.demo_dir / "community_messages.json").read_text())["messages"]
    for msg in messages:
        location = GeoPoint(lat=msg["lat"], lon=msg["lon"]) if "lat" in msg else None
        reply = pipeline.handle_inbound(msg["body"], phone=msg["from"], name=msg["name"], location=location)
        print(f"\n  📩 {msg['name']}: {msg['body'][:80]}{'…' if len(msg['body']) > 80 else ''}")
        print(f"  ↩️  {reply}")

    banner("PHASE 2 — Background cycle: poll feeds → assess → match → route → ping")
    report = pipeline.run_cycle()
    a = report.assessment
    print(f"\n  Crisis: {a.is_crisis}   Level: {a.crisis_level}/5")
    print(f"  Hazards: {', '.join(a.active_hazards)}")
    print(f"  Situation: {a.summary}")
    print(f"\n  Matches proposed: {len(report.new_matches)}   Captain pings sent: {len(report.pings)}")
    for match in report.new_matches:
        offer = store.offers[match.offer_id]
        request = store.requests[match.request_id]
        print(f"   • {offer.resource_type.value} ({offer.contact_name}) → "
              f"{request.contact_name}: score {match.score}, {match.distance_km} km — {match.rationale}")

    if not report.new_matches:
        print("  (no matches this cycle)")
        return

    banner("PHASE 3 — A captain taps ACCEPT on WhatsApp")
    first = report.new_matches[0]
    print(f"\n  📲 Captain replies: ACCEPT {first.id}")
    print(f"  ↩️  {pipeline.handle_inbound(f'ACCEPT {first.id}', phone='+15125550999', name='Captain Reyes')}")

    banner("PHASE 4 — Delivery confirmed")
    print(f"\n  📲 Captain replies: DELIVERED {first.id}")
    print(f"  ↩️  {pipeline.handle_inbound(f'DELIVERED {first.id}', phone='+15125550999', name='Captain Reyes')}")

    status = pipeline.status()
    print(f"\n  Board: {status['open_offers']} open offers, {status['open_requests']} open requests, "
          f"{status['total_matches']} matches total.")
    print("\n✅ Full loop: silent monitoring → autonomous matching → one-tap human approval → delivery.")


if __name__ == "__main__":
    main()

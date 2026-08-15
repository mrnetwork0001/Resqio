"""Local 24/7 polling daemon — the clean-Python fallback to AgentCore.

    python -m src.daemon              # poll forever at POLL_INTERVAL_SECONDS
    python -m src.daemon --cycles 3   # bounded run (demos, smoke tests)

The store is single-writer: do NOT run this alongside the webhook server on
the same store file — the webhook server already embeds this poll loop, so
for live inbound SMS use `python -m src.integrations.webhook_server` alone.
"""

from __future__ import annotations

import argparse
import logging
import time

from .orchestrator import ResqioPipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger("resqio.daemon")


def main() -> None:
    parser = argparse.ArgumentParser(description="Resqio background polling daemon")
    parser.add_argument("--cycles", type=int, default=0, help="stop after N cycles (0 = run forever)")
    parser.add_argument("--interval", type=int, default=0, help="override poll interval in seconds")
    args = parser.parse_args()

    pipeline = ResqioPipeline()
    interval = args.interval or pipeline.settings.poll_interval_seconds
    logger.info(
        "Resqio daemon up: area=%s interval=%ss demo_mode=%s — silent until a match needs approval",
        pipeline.settings.noaa_area, interval, pipeline.settings.demo_mode,
    )

    cycle = 0
    while True:
        cycle += 1
        # A 24/7 monitor must survive any single bad cycle.
        try:
            report = pipeline.run_cycle()
            logger.info(
                "cycle %d: crisis=%s level=%d matches=%d pings=%d",
                cycle, report.assessment.is_crisis, report.assessment.crisis_level,
                len(report.new_matches), len(report.pings),
            )
        except Exception:  # noqa: BLE001
            logger.exception("cycle %d failed; continuing", cycle)
        if args.cycles and cycle >= args.cycles:
            break
        time.sleep(interval)


if __name__ == "__main__":
    main()

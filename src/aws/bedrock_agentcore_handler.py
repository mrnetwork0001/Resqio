"""Amazon Bedrock AgentCore entrypoint for Resqio.

Wraps the ResqioPipeline in a ``BedrockAgentCoreApp`` (POST /invocations,
GET /ping on :8080). Payload actions:

    {"action": "cycle"}                       one monitor→match→route→ping pass
    {"action": "daemon", "cycles": 12}        background polling loop; the session
                                              reports HealthyBusy via add_async_task
                                              so the runtime keeps it alive
    {"action": "inbound_sms", "body": "...", "from": "+1...", "name": "..."}
    {"action": "status"}

Long-running rule honored here: the entrypoint thread never blocks — daemon
work runs on a background thread tracked with add_async_task/complete_async_task
so /ping stays responsive (a blocked ping is the classic cause of 15-minute
session terminations).

Deploy (npm AgentCore CLI — the pip starter-toolkit CLI is deprecated):
    npm install -g @aws/agentcore
    agentcore create --name Resqio --framework Strands --protocol HTTP --model-provider Bedrock
    agentcore deploy
Local check: python -m src.aws.bedrock_agentcore_handler  (serves :8080)
"""

from __future__ import annotations

import logging
import threading
import time

from bedrock_agentcore.runtime import BedrockAgentCoreApp

from ..orchestrator import ResqioPipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("resqio.agentcore")

app = BedrockAgentCoreApp()
_pipeline: ResqioPipeline | None = None
_pipeline_lock = threading.Lock()


def get_pipeline() -> ResqioPipeline:
    global _pipeline
    with _pipeline_lock:
        if _pipeline is None:
            _pipeline = ResqioPipeline()
        return _pipeline


def _run_daemon(task_id: int, cycles: int, interval_seconds: int) -> None:
    pipeline = get_pipeline()
    try:
        for cycle_number in range(1, cycles + 1):
            report = pipeline.run_cycle()
            logger.info(
                "daemon cycle %d/%d: crisis=%s matches=%d pings=%d",
                cycle_number, cycles,
                report.assessment.is_crisis, len(report.new_matches), len(report.pings),
            )
            if cycle_number < cycles:
                time.sleep(interval_seconds)
    finally:
        app.complete_async_task(task_id)  # /ping returns "Healthy" again


@app.entrypoint
def invoke(payload, context):
    """Route an AgentCore invocation to the pipeline (context: RequestContext)."""
    pipeline = get_pipeline()
    action = (payload or {}).get("action", "cycle")

    if action == "cycle":
        return pipeline.run_cycle().to_dict()

    if action == "daemon":
        cycles = int(payload.get("cycles", 12))
        interval = int(payload.get("interval_seconds", pipeline.settings.poll_interval_seconds))
        task_id = app.add_async_task("resqio_polling_daemon", {"cycles": cycles, "interval": interval})
        threading.Thread(
            target=_run_daemon, args=(task_id, cycles, interval), daemon=True
        ).start()
        return {
            "status": "daemon_started",
            "cycles": cycles,
            "interval_seconds": interval,
            "note": "session reports HealthyBusy until the polling loop completes",
        }

    if action == "inbound_sms":
        reply = pipeline.handle_inbound(
            body=payload.get("body", ""),
            phone=payload.get("from", ""),
            name=payload.get("name", "neighbor"),
        )
        return {"reply": reply}

    if action == "status":
        return pipeline.status()

    return {"error": f"unknown action {action!r}", "actions": ["cycle", "daemon", "inbound_sms", "status"]}


if __name__ == "__main__":
    import os

    # AgentCore's contract is :8080; the env override is for local runs where
    # something else (an ssh tunnel, another dev server) already owns 8080.
    app.run(port=int(os.environ.get("RESQIO_AGENTCORE_PORT", "8080")))

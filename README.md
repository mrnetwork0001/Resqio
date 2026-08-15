# 🚨 Resqio — Autonomous Community Disaster & Crisis Logistics Agent

> **AWS Agents for Humans Hackathon** · Good Neighbor Agents track
> Strands Agents SDK · Amazon Bedrock AgentCore · Twilio WhatsApp/SMS · Apache 2.0

During severe weather and power outages, community emergency services are overwhelmed. Vulnerable residents — elderly neighbors who need medical refrigeration for insulin, families with infants and no power — struggle to find help, even when a neighbor two blocks away has a spare generator.

**Resqio runs 100% silently in the background.** It monitors NOAA weather alerts and county-level grid outage data 24/7, ingests plain SMS from community members ("Generator available in Sector 4", "Insulin ice needed at 42 Maple St"), autonomously matches supplies to the most urgent needs, plans safe volunteer transit routes — and surfaces to humans **only** when a delivery match needs a one-tap WhatsApp approval.

![Resqio architecture](architecture_diagram.png)

## The three Strands agents

| Agent | File | What it does |
| :--- | :--- | :--- |
| **① StrandsGridMonitor** | `src/agents/strands_grid_monitor.py` | Polls NOAA/NWS `api.weather.gov` alerts + grid outage records; correlates weather and outages on shared county FIPS codes; returns a validated `CrisisAssessment` (level 0–5). |
| **② StrandsResourceMatcher** | `src/agents/strands_resource_matcher.py` | Parses raw neighbor SMS into offers/requests; matches supply ↔ need on urgency, vulnerability, and distance (haversine `@tool`s); every LLM proposal is re-validated against the live board before it's recorded. |
| **③ StrandsVolunteerRouter** | `src/agents/strands_volunteer_router.py` | Plans crisis-condition transit with per-hazard safety guidance and writes the captain approval ping, always ending `Reply ACCEPT <id> or PASS <id>`. |

All three are built on the **Strands Agents SDK**: `Agent` + custom `@tool`s + Bedrock Claude models, with structured output validated by Pydantic (`structured_output_model=...`).

**Degraded mode, by design.** A disaster tool can't assume the cloud is reachable mid-disaster. If Bedrock is unavailable, every agent drops to a deterministic fallback (severity heuristics, a compatibility-matrix matcher, a haversine route planner) — the pipeline keeps flowing, and the same property lets the whole demo and test suite run with **zero credentials**.

## Quickstart

```bash
git clone <this-repo> && cd Resqio
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# End-to-end demo — no AWS/Twilio credentials required
python -m src.demo

# Run the test suite (49 tests, fully offline)
python -m pytest

# 24/7 local daemon (the clean-Python fallback to AgentCore)
python -m src.daemon --cycles 3 --interval 10
```

The demo plays the **Austin heatwave scenario**: an Excessive Heat Warning collides with a 12,400-customer feeder outage (overlapping FIPS ⇒ crisis level 5), four neighbors text in, the generator is matched to the insulin request 1.2 km away, and a captain approves the delivery over (console-rendered) WhatsApp.

With AWS credentials + Bedrock model access configured (`.env` from `.env.example`), the same commands use live Claude reasoning for assessment, SMS parsing, matching, and routing.

## Live mode configuration

Copy `.env.example` → `.env`:

- **Bedrock**: `AWS_REGION`, `BEDROCK_MODEL_ID` (any tool-use-capable model; inference-profile ids like `global.anthropic.claude-sonnet-4-6`).
- **NOAA**: `NOAA_AREA` (state code), `NOAA_USER_AGENT` — api.weather.gov requires a `(app, contact-email)` User-Agent. Set `RESQIO_DEMO_MODE=0` to poll live alerts.
- **Grid data**: there is **no free real-time outage feed** (EAGLE-I is restricted to government/utility accounts; poweroutage.us is a paid enterprise API), so the grid source is pluggable: `SimulatedGridFeed` ships EAGLE-I-schema county records, and any real utility API can implement the same two-method `GridFeed` protocol.
- **Twilio**: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `RESQIO_CAPTAIN_NUMBERS`. For dev, captains join the WhatsApp Sandbox (`join <code>` to +1 415 523 8886), which opens the 24-h session window for free-form pings; for production business-initiated pings, set `TWILIO_CONTENT_SID` to an approved `twilio/quick-reply` template and captains get real **[Accept] [Pass]** buttons.

The live local runtime is a **single process** — the webhook server ingests inbound SMS/WhatsApp *and* runs the polling loop on an embedded thread (the JSON store is single-writer by design; don't run `src.daemon` against the same store file simultaneously):

```bash
python -m src.integrations.webhook_server   # POST /sms on :5001 + poll loop — expose with `ngrok http 5001`
```

X-Twilio-Signature is validated on every inbound POST, so a random request can't inject offers or approve matches (behind a proxy, set `RESQIO_WEBHOOK_URL` to the exact public URL Twilio calls). Approval pings that nobody answers expire after `RESQIO_MATCH_TTL_MINUTES` (default 45) and both sides go back on the board; match lifecycle is a guarded state machine, so a second captain's stale `PASS` can never reopen a delivery someone already accepted.

## Amazon Bedrock AgentCore deployment

`src/aws/bedrock_agentcore_handler.py` wraps the pipeline in a `BedrockAgentCoreApp` (`POST /invocations`, `GET /ping`). The `daemon` action runs the polling loop on a background thread tracked with `add_async_task`, so the session reports **HealthyBusy** and the runtime keeps it alive between cycles — the entrypoint thread never blocks.

```bash
# Local runtime check (serves :8080)
python -m src.aws.bedrock_agentcore_handler
curl -X POST localhost:8080/invocations -d '{"action": "cycle"}'

# Deploy with the AgentCore CLI (npm; the pip starter-toolkit CLI is deprecated)
npm install -g @aws/agentcore
agentcore create --name Resqio --framework Strands --protocol HTTP --model-provider Bedrock
# `create` scaffolds a wrapper project — point its runtime entrypoint at
# src/aws/bedrock_agentcore_handler.py (copy src/ + requirements.txt into the
# generated app dir), then:
agentcore deploy
agentcore invoke --runtime Resqio '{"action": "daemon", "cycles": 12}'
```

(Alternative: build a `linux/arm64` image serving this app on `:8080`, push to ECR, and register it via boto3 `bedrock-agentcore-control.create_agent_runtime`.)

Payload actions: `cycle` (one pass), `daemon` (background polling), `inbound_sms`, `status`.

## Repository structure

```
Resqio/
├── LICENSE                      # Apache 2.0
├── README.md
├── architecture_diagram.png     # (source: docs/architecture_diagram.svg)
├── RESQIO_PROJECT_SPEC.md       # master blueprint
├── src/
│   ├── agents/                  # the three Strands agents
│   ├── aws/                     # Bedrock AgentCore entrypoint
│   ├── core/                    # models, feeds, store, geo, config
│   ├── integrations/            # Twilio dispatcher + inbound webhook server
│   ├── orchestrator.py          # monitor → match → route → ping pipeline
│   ├── daemon.py                # local 24/7 polling loop
│   └── demo.py                  # end-to-end Austin heatwave scenario
├── data/demo/                   # NWS + EAGLE-I-schema fixtures, seeded SMS
├── tests/                       # 49 offline tests
└── client/                      # Next.js 14 dashboard (in progress)
```

## License

[Apache 2.0](LICENSE) — built by Ifeanyichukwu Onwo for the AWS Agents for Humans Hackathon.

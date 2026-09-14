# Agents for Humans: Building Resqio, an AI Agent That Stays Silent Until Neighbors Need to Decide

*Suggested tags: strands-agents, amazon-bedrock, agentcore, generative-ai, hackathon*

When a heatwave knocks out the power grid, the fastest responders usually aren't ambulances. They're neighbors. The person with a generator in the garage, the family with a freezer full of ice, the house with a spare air-conditioned room.

The problem is never the help. It's coordination. Someone has to watch the weather alerts, read every text, work out who can help whom, and send the same dispatch messages over and over, on the worst day of the year. For the **AWS Agents for Humans Hackathon**, I built **Resqio** to take that repetitive work off a community's plate.

Resqio is an open-source AI agent for neighborhoods, food banks, shelters, and mutual-aid groups. It watches weather and power-grid feeds around the clock, turns plain text messages from neighbors into offers and requests, matches supply to the most urgent needs, and pings a volunteer captain on WhatsApp only when a real delivery needs a human yes.

## The design rule: silent until a human must decide

The hackathon brief asked for an agent that runs in the background and surfaces only when there's a real decision to make. For disaster logistics, that rule isn't a nice-to-have. A volunteer coordinating help during a blackout has no attention to spare for status updates.

So Resqio has exactly one outward action: an approval message. When there's no crisis, it sends nothing. When there is, a captain gets one WhatsApp message like this:

> Resqio: generator needed for insulin refrigeration (urgency 5/5). Bring the generator from Springdale Rd to 42 Maple St - 1.18 km, ~7 min. Reply ACCEPT or PASS

Everything before that message is the agent's job. Everything after it is a human decision.

## Three Strands agents, one background pipeline

I built Resqio with the **Strands Agents SDK**, splitting the work across three specialized agents:

1. **StrandsGridMonitor** reads NOAA/National Weather Service alerts and county-level outage records, correlates hazards that share county FIPS codes, and scores the crisis from 0 to 5. An extreme heat warning plus a 12,400-customer outage in the same county is a compounding emergency.
2. **StrandsResourceMatcher** parses informal texts ("HELP: my father is 82, insulin needs refrigeration, power is out at 42 Maple St") and pairs offers with requests by urgency, vulnerability, and distance.
3. **StrandsVolunteerRouter** plans a crisis-condition route with safety guidance for each active hazard and writes the approval message.

What made Strands a good fit was how little ceremony it needs. Each agent is a model, a system prompt, a few tools, and a structured output type. Here is the matcher, slightly simplified:

```python
matcher = Agent(
    name="ResourceMatcher",
    model=BedrockModel(model_id=settings.bedrock_model_id, temperature=0.2),
    system_prompt=SYSTEM_PROMPT,
    tools=[list_open_offers, list_open_requests, compute_distance_km],
    callback_handler=None,
)
result = matcher(prompt, structured_output_model=MatchProposal)
proposal = result.structured_output  # a validated Pydantic model
```

Tools are plain Python functions decorated with `@tool`, with the schema generated from type hints and docstrings. Structured output mattered even more: the model's answer has to validate against a Pydantic model before the pipeline trusts it. Then every proposed match is checked again against the live community board, under a lock, before anything is booked. The model proposes; the code decides what's allowed.

## Running in the background on Amazon Bedrock AgentCore

A background agent needs somewhere to live. I packaged the pipeline as an **Amazon Bedrock AgentCore Runtime** app. The interesting part was keeping a polling loop alive without blocking the runtime's health check. AgentCore's SDK handles this with async task tracking:

```python
app = BedrockAgentCoreApp()

@app.entrypoint
def invoke(payload, context):
    if payload.get("action") == "daemon":
        task_id = app.add_async_task("resqio_polling_daemon", {"cycles": cycles})
        threading.Thread(target=_run_daemon, args=(task_id, cycles, interval), daemon=True).start()
        return {"status": "daemon_started"}
```

While the task is open, the runtime's `/ping` reports **HealthyBusy**, so the session stays alive between polling cycles. When the loop finishes, `complete_async_task` flips it back to Healthy. The entrypoint returns immediately and never blocks.

## Designing for the worst day, not the demo day

A disaster tool can't assume the cloud is healthy in the middle of a disaster. So every AI step in Resqio has a deterministic fallback:

- Crisis assessment falls back to severity thresholds and county-overlap rules.
- Text parsing falls back to a keyword parser with word-boundary matching.
- Matching falls back to a compatibility matrix plus straight-line distance.
- Routing falls back to a template planner with per-hazard guidance.

If Bedrock is unreachable, the loop slows down its thinking but keeps the same protocol. This had a great side effect for a hackathon: anyone can clone the repo and run the whole scenario offline in three commands, with zero credentials, and the test suite runs in CI without any cloud access.

## Guarding the one human decision

Real crises are messy. Several captains reply to the same ping, and webhooks get retried. My first version had a nasty bug: a second captain's late PASS could reopen a delivery someone had already accepted, and the next cycle would promise the same generator to a different family.

The fix was to make the match lifecycle a guarded state machine (proposed, pending approval, approved, delivered, with declined and expired as exits). Stale replies now get a polite "already approved, no change made" instead of changing anything. Pings nobody answers expire after 45 minutes and both sides go back on the board.

I found that bug, and 19 others, by running an adversarial multi-agent code review over the codebase and fixing every confirmed finding with regression tests.

## Lessons learned

- **Plan for new-account limits.** A brand-new AWS account starts with zero Amazon Bedrock token quotas until account verification completes. Create your account and request model access early, before you need live inference.
- **Use the current Strands structured output API.** Pass `structured_output_model=` to the agent call and read `result.structured_output`.
- **The AgentCore deployment tooling has moved to the npm-based AgentCore CLI** (`@aws/agentcore`); the older Python starter toolkit CLI is superseded.
- **NOAA's api.weather.gov is free and excellent,** but it requires a descriptive User-Agent, and `/alerts/active` rejects a `limit` parameter.
- **Silence is a design constraint.** "Only surface when a human must decide" changed how I wrote messages, handled failures, and scoped the whole product.

## What's next

I'd love to pilot Resqio with a neighborhood mutual-aid network, add playbooks for winter freezes and hurricanes, and support Spanish-language texts.

Resqio is open source under Apache 2.0:

- **Code:** https://github.com/mrnetwork0001/Resqio
- **Live demo:** https://tryresqio.vercel.app
- **Demo video:** https://youtu.be/7n79CaCKzPY

The next storm isn't waiting. Fork it for your county.

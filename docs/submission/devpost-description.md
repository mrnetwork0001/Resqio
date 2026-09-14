# Resqio - Devpost submission text

**Track:** Good Neighbor Agents

## Project name

Resqio

## Elevator pitch

An AI agent that quietly coordinates neighbors during blackouts and heatwaves - matching spare generators, ice, and food to the most vulnerable, and only pinging a volunteer when a delivery needs a human yes.

## About the project

### Inspiration

When a heatwave knocks out the grid, the people at greatest risk can't wait in an emergency-line queue: an 82-year-old whose insulin is spoiling, a family with a newborn and no cooling. The help usually already exists a few blocks away - a neighbor with a generator, a freezer full of ice. What's missing is coordination, at the exact moment nobody has time to coordinate. Heat is the deadliest weather hazard in the United States, and the work of coordinating help is relentlessly repetitive: watching alerts, reading texts, figuring out who can help whom, and writing the same dispatch messages over and over.

### What it does

Resqio runs in the background and handles that work end to end:

- **Watches** NOAA/National Weather Service alerts and county-level power outage data around the clock and scores crisis severity from 0 to 5, recognizing compounding emergencies such as extreme heat plus a 12,400-customer outage in the same county.
- **Listens** to plain SMS from neighbors ("OFFER: generator available in Sector 4", "HELP: insulin needs refrigeration at 42 Maple St"). No app, no account.
- **Matches** supply to need by urgency, vulnerability, and distance - medical refrigeration, infants, and elderly residents first - never double-books an offer, and keeps volunteers inside their own service zone.
- **Asks a human** only when a real-world delivery needs a decision: one WhatsApp message to a volunteer captain with the route, the hazards, and two replies, ACCEPT or PASS. Requests nobody answers expire and are re-matched automatically.

No crisis, no messages. A situation board with an ops map lets organizers see everything at a glance, but nobody has to watch it.

### Who it's for

Neighborhood block captains, mutual-aid groups, food banks, and shelters - the small local organizations that end up coordinating help when official services are overwhelmed - and the vulnerable residents they serve.

### How we built it

- **Strands Agents SDK** powers three specialized agents: `StrandsGridMonitor` (crisis detection), `StrandsResourceMatcher` (SMS parsing and supply-to-need matching), and `StrandsVolunteerRouter` (hazard-aware routing and the approval message). Each has its own custom `@tool`s and returns validated structured output (Pydantic models via `structured_output_model`).
- **Amazon Bedrock** provides Claude as the reasoning model.
- **Amazon Bedrock AgentCore Runtime:** the pipeline is packaged as a `BedrockAgentCoreApp` whose polling daemon runs as a tracked async task, so the runtime keeps the session alive (HealthyBusy) between cycles.
- **Twilio** WhatsApp and SMS for inbound texts and approval pings, with signature-validated webhooks.
- **NOAA api.weather.gov** for live weather alerts; power outages come through a pluggable feed that uses the EAGLE-I county outage schema.
- **Next.js 14, Tailwind CSS, and Leaflet** for the landing page and the situation board with its ops map.
- Python 3.11, an 82-test offline suite, GitHub Actions CI, Apache 2.0 license.

### Challenges we ran into

- **A disaster tool can't assume the cloud is up.** Every AI step has a deterministic fallback (severity thresholds, a compatibility matrix, a distance-based route planner), so the loop keeps running if Bedrock is unreachable. The same design lets anyone run the full demo offline with zero credentials.
- **Real crises are messy.** Several captains reply to the same ping and webhooks get retried, so the match lifecycle is a guarded state machine: a stale PASS can never undo a delivery someone already accepted.
- **There is no free real-time power outage feed in the US,** so the grid source is a pluggable interface that any utility API can implement.

### Accomplishments that we're proud of

- The full loop - detection, intake, matching, routing, human approval, and delivery confirmation - works end to end.
- The codebase went through an adversarial multi-agent code review, and all 20 confirmed findings were fixed, including a double-booking race.
- Multi-county service zones with per-zone volunteer rosters, and a live NOAA integration validated against production alerts.

### What we learned

The most valuable thing an agent can do for a stressed community is stay quiet. Designing around "only surface when a human must decide" shaped every part of the system, from how approval messages are written to how failures degrade.

### What's next for Resqio

A pilot with a neighborhood mutual-aid network, playbooks for winter freezes and hurricanes, and Spanish-language SMS.

## Built with

strands-agents, amazon-bedrock, amazon-bedrock-agentcore, claude, python, twilio, whatsapp, noaa-weather-api, next.js, react, typescript, tailwindcss, leaflet, github-actions

## Links

- Code: https://github.com/mrnetwork0001/Resqio
- Live demo: https://tryresqio.vercel.app
- Demo video: ADD-YOUTUBE-URL

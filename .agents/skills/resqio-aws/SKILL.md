---
name: resqio-aws
description: Architecture, guidelines, Strands Agents SDK specs, and AWS hackathon rules for Resqio (Autonomous Community Disaster & Crisis Logistics Agent) built for the AWS Agents for Humans Hackathon.
---

# 🚨 Resqio — AWS Hackathon Skill & Execution Guide

Use this skill whenever working on, reviewing, or developing **Resqio** — the Autonomous Community Disaster & Crisis Logistics Agent for the AWS Agents for Humans Hackathon.

## 📌 Project Overview & Prize Targets
- **Target Event:** AWS Agents for Humans Hackathon (Devpost)
- **Deadline:** September 15, 2026 @ 1:00 am GMT+1
- **Prize Targets:** $10,000 Grand Prize + $5,000 Good Neighbor Track (Golden Agent)
- **Core Stack:** Strands Agents SDK (Python) + Amazon Bedrock AgentCore + Twilio WhatsApp/SMS API + Next.js 14

## 🏗️ Technical Architecture Rules

### 1. Strands Agents SDK (Mandatory Core)
- Build modular agent classes using Strands Agents SDK:
  - `StrandsGridMonitor`: Polls environmental weather & power outage feeds.
  - `StrandsResourceMatcher`: Matches emergency supply capacity with vulnerable requests using spatial & tool reasoning.
  - `StrandsVolunteerRouter`: Calculates delivery transit routes and formats human approval pings.

### 2. AWS AgentCore Deployment (Score Booster)
- Deploying on Amazon Bedrock AgentCore is optional but boosts the Technical Implementation score.
- Always ensure the app can run cleanly locally with Python as a fallback.

### 3. Background Autonomy Rule
- The agent runs 100% in the background. It must ONLY ping the volunteer/captain via WhatsApp/SMS when a delivery match requires physical confirmation.

## 🧭 Implementation Ground Rules (learned during the build)
- Strands structured output is `agent(prompt, structured_output_model=Model)` → `result.structured_output` (the `.structured_output()` method is deprecated).
- Every LLM step has a deterministic degraded-mode fallback; never remove that property — the demo and tests depend on running credential-free.
- The community store is **single-writer**: one process owns `data/store.json` (AgentCore runtime, or the webhook server with its embedded poll loop). Never run `src.daemon` and the webhook server against the same store file.
- Match lifecycle is a guarded state machine (`store.set_match_status`); stale captain replies must get an informative "no change" reply, not a mutation.
- The pip `agentcore` starter-toolkit CLI is deprecated; deployment docs must reference the npm `@aws/agentcore` CLI or boto3 `create_agent_runtime`.

## 🚨 Submission Checklist
- Public GitHub repo with Apache 2.0 or MIT License. ✅ github.com/mrnetwork0001/Resqio
- Architecture Diagram + `README.md`. ✅
- Max 5-minute video demo (human voiceover, no AI voice). ⬜ (Week 4)
- AWS Builder ID + optional builder.aws.com journey post. ⬜ (Week 4)

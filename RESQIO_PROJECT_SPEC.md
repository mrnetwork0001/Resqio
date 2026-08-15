# 🚨 RESQIO — Autonomous Community Disaster & Emergency Logistics Agent

> **AWS Agents for Humans Hackathon Master Blueprint ($40,000 Cash Pool)**  
> **Target Track:** Good Neighbor Agents ($5,000 Golden Agent Track / $10,000 Grand Prize Target)  
> **Core Stack:** Strands Agents SDK (Python) + Amazon Bedrock AgentCore + Twilio/WhatsApp API + Next.js  
> **Submission Deadline:** September 15, 2026 @ 1:00 am GMT+1  
> **License:** Apache 2.0 Open Source  
> **Author:** Ifeanyichukwu Onwo (`mrnetwork`)  

---

## 📌 Executive Summary

**Resqio** is an **Autonomous Community Disaster & Crisis Logistics Agent** built for local neighborhoods, food banks, shelters, and volunteer groups using the **Strands Agents SDK** and **Amazon Bedrock AgentCore**.

During severe weather events, power grid outages, heatwaves, or winter freezes, local community emergency services are overwhelmed. Vulnerable residents (elderly, families with infants, people needing medical refrigeration) struggle to find critical resources, while willing neighbors with generators, food surplus, or medical supplies have no easy way to coordinate.

**Resqio operates 100% autonomously in the background.** It continuously monitors NOAA weather feeds and local power grid outage APIs. When a crisis occurs, it ingests simple SMS/text messages from community members, automatically matches available supplies to nearby urgent needs using multi-agent intelligence, calculates safe volunteer transit routes, and **surfaces to local volunteer captains ONLY when a physical action or delivery confirmation requires human approval.**

---

## 🎯 Technical Moat & AWS Judging Criteria Alignment

| Judging Criteria | Implementation in Resqio | Impact Score |
| :--- | :--- | :--- |
| **Strands Agents SDK** | Multi-agent coordination (Grid & Weather Monitor Agent, Resource Matcher Agent, Volunteer Dispatch Agent). | ⭐⭐⭐⭐⭐ (5/5) |
| **AWS AgentCore Deployment** | Deployed on Amazon Bedrock AgentCore for 24/7 background weather/grid polling daemon execution. | ⭐⭐⭐⭐⭐ (5/5) |
| **Background Autonomy** | Runs silently without manual prompting. Surfaces notifications via WhatsApp/SMS ONLY when a match needs approval. | ⭐⭐⭐⭐⭐ (5/5) |
| **Good Neighbor Track Fit** | Built specifically to help communities, neighborhoods, and food banks during emergency crises. | ⭐⭐⭐⭐⭐ (5/5) |
| **Bonus Points** | Published build journey article on `builder.aws.com`. | 🏅 +10% Bonus |

---

## 🏗️ System Architecture & Workflow

```
                                  ┌──────────────────────────────┐
                                  │ NOAA Weather & Grid Outages  │
                                  └──────────────┬───────────────┘
                                                 │
                                                 │ 24/7 Background Polling
                                                 ▼
                                 ┌───────────────────────────────┐
                                 │     Resqio Strands Agent      │
                                 │   (Amazon Bedrock AgentCore)  │
                                 └───────────────┬───────────────┘
                                                 │
                   ┌─────────────────────────────┼─────────────────────────────┐
                   │                             │                             │
                   ▼                             ▼                             ▼
     [ Agent 1: Grid & Weather ]    [ Agent 2: Resource Matcher ]  [ Agent 3: Volunteer Router ]
     • Polls NOAA/Grid APIs         • Ingests SMS Capacity         • Calculates Safe Routes
     • Detects Crisis Events        • Matches Urgent Needs         • Verifies Delivery Status
                   │                             │                             │
                   └─────────────────────────────┼─────────────────────────────┘
                                                 │
                                                 │ Surfaces ONLY when human action needed
                                                 ▼
                                 ┌───────────────────────────────┐
                                 │  Volunteer WhatsApp/SMS Ping  │
                                 │  "Bring Generator to 42 Maple"│
                                 │  [ Accept Match ] [ Pass ]    │
                                 └───────────────────────────────┘
```

---

## 📋 Devpost Submission Form Fill-In Answers

### 1. PROJECT NAME
`Resqio`

### 2. ELEVATOR PITCH (1–2 Sentences)
`Resqio is an autonomous community disaster logistics agent built with Strands Agents SDK and Amazon Bedrock AgentCore that silently monitors weather/grid outages, autonomously matches local emergency supplies to vulnerable neighbors, and pings volunteers only when human action is needed.`

### 3. DETAILED PROJECT DESCRIPTION
`During severe weather events and power outages, community emergency services are overwhelmed. Vulnerable residents (such as elderly neighbors needing medical refrigeration for insulin or families requiring emergency power) struggle to find help, even when neighbors nearby have excess capacity. Resqio solves community crisis logistics by turning emergency coordination into a silent, background AI workflow. Built on the open-source Strands Agents SDK and deployed on Amazon Bedrock AgentCore, Resqio continuously monitors NOAA weather alerts and grid outage feeds. When a crisis occurs, community members send simple text messages (e.g. "Generator available in Sector 4" or "Insulin ice needed at 42 Maple St"). Resqio's multi-agent engine automatically matches resources to urgent needs based on location and safety constraints, routing volunteer deliveries and pinging block captains on WhatsApp/SMS ONLY when a delivery match needs a single-click human confirmation.`

### 4. HOW DOES IT USE STRANDS AGENTS SDK?
`Resqio utilizes the Strands Agents SDK to orchestrate three specialized agents:
1. Grid & Weather Monitor Agent: Polls environmental data feeds and flags crisis zones.
2. Resource Matcher Agent: Uses LLM tool-calling and spatial reasoning to match supply offerings (generators, ice, food) with urgent vulnerable requests.
3. Volunteer Dispatch Agent: Calculates safe delivery transit routes and formats human approval pings.`

### 5. TECH STACK
`Strands Agents SDK, Amazon Bedrock AgentCore, Python 3.11, Next.js 14, Tailwind CSS, TypeScript, Twilio SMS / WhatsApp API, Apache 2.0 License.`

---

## ⚙️ Repository Structure

```
Resqio/
├── LICENSE                     # Apache 2.0 Open Source License
├── RESQIO_PROJECT_SPEC.md      # Master Blueprint
├── CLAUDE_RESQIO.md            # Persistent Context Directive
├── architecture_diagram.png    # AWS System Architecture Diagram
├── README.md                   # Setup Instructions & Documentation
├── src/
│   ├── agents/
│   │   ├── strands_grid_monitor.py
│   │   ├── strands_resource_matcher.py
│   │   └── strands_volunteer_router.py
│   ├── aws/
│   │   └── bedrock_agentcore_handler.py
│   └── integrations/
│       └── twilio_whatsapp_dispatcher.py
└── client/                     # Next.js 14 Dashboard
```

---

## ⏱️ Technical Execution Plan (Aug 15 – Sept 15)

- **Week 1 (Aug 15 – Aug 22):** Setup Strands Agents SDK in Python & build `strands_resource_matcher.py`.
- **Week 2 (Aug 23 – Aug 30):** Integrate Amazon Bedrock AgentCore & build weather/grid monitoring daemon.
- **Week 3 (Aug 31 – Sept 7):** Build Next.js 14 Web Dashboard & Twilio WhatsApp notification handler.
- **Week 4 (Sept 8 – Sept 15):** Record 3-minute video demo, publish `builder.aws.com` journey post, and submit to Devpost.

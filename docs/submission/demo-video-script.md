# Resqio - demo video script

**Target length:** about 4:35. **Hard limit:** 5:00.
Use your own voice (no AI voice). Screen recording only; you don't need to appear on camera.

## Before you record

- [ ] Open the live site, nothing to run locally: https://tryresqio.vercel.app (landing page) and https://tryresqio.vercel.app/board (situation board)
- [ ] On the board, click **Reset** so it starts empty
- [ ] Scenes 6-7 show the approval ping in the board's **Ping log** and the **Captain console** (real WhatsApp delivery needs a paid Twilio account)
- [ ] Browser window about 1440px wide, zoom 100%, bookmarks bar hidden
- [ ] Turn on macOS Focus mode so no notifications pop up
- [ ] Open in tabs or windows: the landing page, the board, `architecture_diagram.png`, and `src/agents/strands_resource_matcher.py` in VS Code
- [ ] Record with **Cmd+Shift+5** → Record Selected Portion → **Options** → choose your microphone

Tip: record each scene as its own clip. Redoing one scene is much faster than redoing the whole video.

---

## Scene 1 - Hook (0:00-0:15)

**Screen:** Landing page hero. Let the animation play.

**Say:**
"When a heatwave knocks out the power, the fastest responders aren't ambulances. They're neighbors. This is Resqio, an AI agent that makes sure they reach the right door."

## Scene 2 - The problem (0:15-0:55)

**Screen:** Scroll slowly to the "Silent until a human must decide" section with the text-message card.

**Say:**
"Picture an 82-year-old in Austin. The power is out, the heat index is over 110, and his insulin needs to stay cold. A few blocks away, a neighbor has a generator sitting in the garage. The help exists. The coordination doesn't. Emergency lines are flooded within hours, and heat is the deadliest weather hazard in the United States. The people organizing help are stuck doing the same repetitive work by hand: checking alerts, reading texts, and figuring out who can help whom."

## Scene 3 - Who it's for (0:55-1:15)

**Screen:** Scroll to the yellow "Built for the people who show up" section.

**Say:**
"Resqio is for the people who already show up: block captains, mutual-aid groups, food banks, and shelters. Residents just send a normal text message. No app, no account."

## Scene 4 - How it works (1:15-2:00)

**Screen:** The architecture diagram.

**Say:**
"Resqio is built with the Strands Agents SDK. Three agents run in the background. The Grid Monitor watches NOAA weather alerts and power outage data and scores the crisis. The Resource Matcher reads community texts and pairs supply with need, most urgent first. The Volunteer Router plans a safe route and writes one WhatsApp message. It uses Claude on Amazon Bedrock and is packaged to run as a background agent on Amazon Bedrock AgentCore. The key idea: it stays silent. The only time a person hears from it is when a delivery needs a human yes."

## Scene 5 - Demo: texts come in (2:00-2:30)

**Screen:** The board. Click **Seed texts**, then point your cursor at the Community board panel.

**Say:**
"Let's run the Austin heatwave scenario. Four neighbors text in. Marcus offers a generator. Rosa has ice. Amara's father needs his insulin kept cold. Dan has a three-month-old and no power. Resqio has already turned those texts into structured offers and requests, and flagged the insulin request as urgency five."

## Scene 6 - Demo: the agent acts (2:30-3:00)

**Screen:** Click **Run cycle**. Point at the crisis gauge, the SITREP line, the match line on the map, the Dispatch panel, and the Ping log.

**Say:**
"Now one background cycle. An excessive heat warning overlaps a 12,400-customer power outage in the same county, so the crisis level jumps to five. The matcher pairs Marcus's generator with Amara's father, 1.2 kilometers away. The router adds heat and dark-intersection safety guidance, and sends exactly one message to the volunteer captain."

## Scene 7 - Demo: a human decides (3:00-3:35)

**Screen:** Copy the match ID from the Dispatch panel before you start talking. Type `ACCEPT mat_...` in the Captain console and click **Send**. Then type `DELIVERED mat_...` and send it. Show the match line on the map turn green.

**Say:**
"The captain accepts. That's the only decision a person had to make. When the drop-off is done, they reply delivered, and the loop closes. If they had passed instead, both sides would go straight back on the board for the next cycle, and a late reply from a second captain can't undo an accepted delivery."

## Scene 8 - Under the hood (3:35-4:10)

**Screen:** VS Code showing `src/agents/strands_resource_matcher.py`. Scroll to the `Agent(...)` block with `tools=` and the `structured_output_model=` call. Then switch to a terminal and run `python -m pytest -q` so "82 passed" is visible.

**Say:**
"Under the hood, each agent is a Strands Agent with its own tools, like a distance calculator, and every answer comes back as validated structured output before it touches the board. A disaster tool can't assume the cloud is up, so every AI step also has a deterministic fallback, and the loop keeps running even if Bedrock is unreachable. Eighty-two automated tests run offline."

**If live Bedrock is working by the time you record:** instead of the tests, show the terminal log of a live cycle and say "Here it is reasoning live on Claude through Amazon Bedrock."

## Scene 9 - Why it matters (4:10-4:35)

**Screen:** Scroll to the yellow "The next storm isn't waiting" section.

**Say:**
"Disasters don't wait for software rollouts, and neighbors don't need another app. Resqio takes the repetitive coordination off a community's plate and hands people the one decision that matters. It's open source under Apache 2.0. Fork it for your county. The next storm isn't waiting."

---

## Required pitch points (check before uploading)

- [ ] The problem → Scene 2
- [ ] Who it's for → Scene 3
- [ ] Why it matters → Scenes 2 and 9
- [ ] The working project → Scenes 5, 6, and 7
- [ ] Strands Agents SDK clearly visible → Scenes 4 and 8

## If you run long

Cut the last sentence of Scene 7 and the last sentence of Scene 8. That saves about 15 seconds.

## After recording

1. Trim the dead air at the start and end in QuickTime (**Edit → Trim**) or iMovie. Keep the video under 5:00.
2. Upload to YouTube as **Public**. Title: `Resqio - AI agent for community disaster logistics | Agents for Humans Hackathon`
3. Paste the YouTube link into Devpost and into `docs/submission/devpost-description.md`.

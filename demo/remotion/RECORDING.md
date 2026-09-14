# Recording your narration for the Resqio demo video

The video is fully built and timed to a scratch narration. You record the same 14 lines, and one command swaps your voice in and re-times every scene to your delivery. You don't need to edit anything by hand.

## Before you start

- **Use a quiet room**, and stay close to the mic. Your phone's **Voice Memos** app is fine.
- **Record one file per line.** It's fine to leave a short pause at the start and end, because silence is trimmed automatically.
- **Pronunciation:**
  - **Resqio** is **"resk-YO"**.
  - **NOAA** is **"Noah"**.
- **Pace:** calm and clear. The "scratch length" column shows how long the scratch voice took; you can be a little slower. The whole film has to stay under 4:00, and the render step warns you if it doesn't.
- If you stumble, just re-record that one line.

## The lines

| File | Read this | Scratch length | On screen |
|---|---|---|---|
| `v01` | This is Resqio. An AI agent that coordinates neighbors when the power fails. | 4.6s | Logo and tagline |
| `v02` | Austin, Texas. The heat index is over 110, and a feeder outage has cut power to twelve thousand customers. An eighty-two-year-old's insulin needs to stay cold. Emergency lines are already flooded. | 13.2s | Heat warning, outage counter, insulin text |
| `v03` | A few blocks away, a neighbor has a generator in the garage. The help exists. What's missing is someone to connect them, fast. | 7.7s | Map: generator and insulin request, 1.2 km apart |
| `v04` | Resqio is for the people who already show up: block captains, mutual-aid groups, food banks, and shelters. Residents don't install anything. They just send a text. | 10.3s | Four audience cards and a text bubble |
| `v05` | It runs in the background, around the clock. It stays silent, and only asks a human when a real delivery needs a yes. | 6.4s | Landing page animation |
| `v06` | Under the hood are three agents built with the Strands Agents SDK. A grid monitor watches NOAA weather alerts and power outages. A resource matcher turns texts into offers and needs. A volunteer router plans a safe trip and writes one approval message. | 16.7s | Watch, Match, Route, Approve pipeline |
| `v07` | Here's the live board. Four neighbors text in. A generator. Bags of ice. A father who needs his insulin kept cold. A family with a three-month-old. Resqio turns every message into structured offers and requests. | 14.5s | Board fills with offers and requests |
| `v08` | One background cycle. An extreme heat warning overlaps the outage in the same county, so the crisis level jumps to five. The generator is matched to the insulin request, one point two kilometers away. | 12.1s | Crisis 5/5, match line on the map |
| `v09` | The router adds heat and dark-intersection safety guidance, then sends exactly one message to a volunteer captain. | 6.9s | The approval message types out |
| `v10` | The captain accepts. That's the only decision a person makes. When the drop-off is done, they confirm delivery, and the loop closes. | 7.2s | Captain console: ACCEPT, then DELIVERED |
| `v11` | Every agent returns validated, structured output, and every proposal is checked against the live board before anything is booked. The model proposes. The code decides what's allowed. | 11.2s | Strands agent code |
| `v12` | A disaster tool can't assume the cloud is up. Every step has a deterministic fallback, and the whole loop is packaged to run as a background agent on Amazon Bedrock AgentCore. | 10.4s | Fallback table, AgentCore badge |
| `v13` | And when two captains reply to the same ping, a late pass can't undo a delivery someone already accepted. | 5.6s | A late PASS bounces off an approved match |
| `v14` | Resqio is open source. Fork it for your county. The next storm isn't waiting. | 4.8s | Logo, live demo URL, GitHub |

## After recording

1. **Name each file after its line**, keeping whatever format your recorder made: `v01.m4a`, `v02.m4a`, … `v14.m4a`. `.wav`, `.mp3`, `.aiff`, and `.caf` also work.
2. **Put them in** `demo/remotion/recordings/`. That folder is gitignored, so your recordings never go to GitHub.
3. From `demo/remotion/`, run:
   ```bash
   npm run vo:human   # trims, normalizes loudness, re-times every scene, prints the film length
   npm run render     # writes out/resqio-demo.mp4
   ```
4. The **"Scratch narration · not final"** tag in the corner disappears automatically once your recordings are in.

**To redo one line** (for example `v03`), re-record it, replace the file, then run `node scripts/voiceover.mjs --source human --only v03` and `npm run render`.

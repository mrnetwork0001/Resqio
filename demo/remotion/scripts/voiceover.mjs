#!/usr/bin/env node
/**
 * Per-scene narration for the Resqio demo video.
 *
 *   node scripts/voiceover.mjs --source eleven   # scratch narration from ElevenLabs (timing only)
 *   node scripts/voiceover.mjs --source human    # your recordings in recordings/<id>.{wav,m4a,mp3,aiff,caf}
 *   node scripts/voiceover.mjs --source human --only v03   # redo one scene
 *
 * Every clip is trimmed of leading/trailing silence, loudness-normalized to
 * -16 LUFS, and written to public/vo/<id>.mp3. Measured durations go to
 * src/vo-manifest.json, and the composition sizes each scene from them, so
 * swapping scratch audio for real recordings re-times the whole film with no
 * manual editing and no clipped words.
 *
 * Based on /Users/mrnetwork/Syntura/video/scripts/voiceover.mjs.
 */

import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const CACHE = join(ROOT, "vo-cache");
const RECORDINGS = join(ROOT, "recordings");
const OUT = join(ROOT, "public", "vo");
const MANIFEST = join(ROOT, "src", "vo-manifest.json");
const API = "https://api.elevenlabs.io/v1";
const PAD_SECS = 0.9;          // must match PAD_SECS in src/Resqio.tsx
const LIMIT_SECS = 238;        // keep the film under 4:00

// Load demo/remotion/.env without a dotenv dependency.
const envFile = join(ROOT, ".env");
if (existsSync(envFile)) {
  for (const line of readFileSync(envFile, "utf8").split("\n")) {
    const m = line.match(/^\s*([A-Z0-9_]+)\s*=\s*(.*?)\s*$/);
    if (m && !process.env[m[1]]) process.env[m[1]] = m[2].replace(/^["']|["']$/g, "");
  }
}

const args = process.argv.slice(2);
const opt = (n) => { const i = args.indexOf(n); return i >= 0 ? args[i + 1] : null; };
const SOURCE = opt("--source") || "eleven";
const ONLY = opt("--only");
if (!["eleven", "human"].includes(SOURCE)) throw new Error(`--source must be eleven or human, got ${SOURCE}`);

const VOICE = process.env.ELEVENLABS_VOICE || "CwhRBWXzGAHq8TQ4Fs17"; // "Roger" premade voice
const MODEL = process.env.ELEVENLABS_MODEL || "eleven_multilingual_v2";
const VOICE_SETTINGS = { stability: 0.5, similarity_boost: 0.75, style: 0.0, use_speaker_boost: true };

const ff = (a) => execFileSync("ffmpeg", ["-y", "-loglevel", "error", ...a]);
const durationOf = (f) => parseFloat(execFileSync("ffprobe", [
  "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", f,
]).toString().trim());

async function synthesise(text, dest) {
  const key = process.env.ELEVENLABS_API_KEY;
  if (!key) throw new Error("ELEVENLABS_API_KEY is not set (demo/remotion/.env).");
  const res = await fetch(`${API}/text-to-speech/${VOICE}`, {
    method: "POST",
    headers: { "xi-api-key": key, "Content-Type": "application/json" },
    body: JSON.stringify({ text, model_id: MODEL, voice_settings: VOICE_SETTINGS }),
  });
  if (!res.ok) throw new Error(`ElevenLabs ${res.status}: ${(await res.text()).slice(0, 300)}`);
  writeFileSync(dest, Buffer.from(await res.arrayBuffer()));
}

function findRecording(id) {
  for (const ext of ["wav", "m4a", "mp3", "aiff", "aif", "caf"]) {
    const f = join(RECORDINGS, `${id}.${ext}`);
    if (existsSync(f)) return f;
  }
  return null;
}

// Trim silence at both ends, then normalize loudness, mono 48 kHz mp3.
const TRIM = "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05";
const CHAIN = `${TRIM},areverse,${TRIM},areverse,loudnorm=I=-16:TP=-1.5:LRA=11`;

const { scenes } = JSON.parse(readFileSync(join(ROOT, "narration.json"), "utf8"));
mkdirSync(CACHE, { recursive: true });
mkdirSync(OUT, { recursive: true });

const previous = existsSync(MANIFEST) ? JSON.parse(readFileSync(MANIFEST, "utf8")) : { scenes: {} };
const durations = ONLY && previous.source === SOURCE ? { ...previous.scenes } : {};

if (SOURCE === "human") {
  const missing = scenes.filter((s) => (!ONLY || s.id === ONLY) && !findRecording(s.id)).map((s) => s.id);
  if (missing.length) {
    console.error(`\nMissing recordings in recordings/: ${missing.join(", ")}\nName each file after its scene id, e.g. recordings/v01.m4a\n`);
    process.exit(1);
  }
}

console.log(`\nSource: ${SOURCE}${SOURCE === "eleven" ? ` (voice ${VOICE}, ${MODEL}) - SCRATCH, for timing only` : " (your recordings)"}\n`);

for (const s of scenes) {
  if (ONLY && s.id !== ONLY) continue;
  let input;
  if (SOURCE === "eleven") {
    const text = s.say || s.text;
    const raw = join(CACHE, `${s.id}.raw.mp3`);
    const stamp = join(CACHE, `${s.id}.stamp`);
    const want = JSON.stringify({ text, voice: VOICE, model: MODEL, VOICE_SETTINGS });
    const fresh = existsSync(raw) && existsSync(stamp) && readFileSync(stamp, "utf8") === want;
    if (!fresh) { await synthesise(text, raw); writeFileSync(stamp, want); }
    input = raw;
    process.stdout.write(`  ${s.id} ${fresh ? "cached     " : "synthesised"} `);
  } else {
    input = findRecording(s.id);
    process.stdout.write(`  ${s.id} recording   `);
  }
  const dest = join(OUT, `${s.id}.mp3`);
  ff(["-i", input, "-af", CHAIN, "-ar", "48000", "-ac", "1", "-c:a", "libmp3lame", "-b:a", "192k", dest]);
  const secs = durationOf(dest);
  durations[s.id] = Math.round(secs * 100) / 100;
  const sceneSecs = Math.max(s.minSecs, secs + PAD_SECS);
  const words = s.text.split(/\s+/).length;
  console.log(`${secs.toFixed(2)}s spoken -> scene ${sceneSecs.toFixed(1)}s  (${Math.round(words / secs * 60)} wpm)`);
}

writeFileSync(MANIFEST, JSON.stringify({
  source: SOURCE, voice: SOURCE === "eleven" ? VOICE : "human", generated: new Date().toISOString(), scenes: durations,
}, null, 2) + "\n");

const total = scenes.reduce((a, s) => a + Math.max(s.minSecs, (durations[s.id] ?? 0) + PAD_SECS), 0);
console.log(`\nFilm length: ${Math.floor(total / 60)}:${String(Math.round(total % 60)).padStart(2, "0")} (${total.toFixed(1)}s)`);
if (total > LIMIT_SECS) {
  console.log(`WARNING: over ${LIMIT_SECS}s - trim narration to stay under 4:00.`);
  process.exitCode = 2;
}
console.log(`Wrote src/vo-manifest.json\n`);

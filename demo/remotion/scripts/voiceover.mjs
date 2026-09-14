#!/usr/bin/env node
/**
 * Per-scene narration for the Resqio demo video.
 *
 *   node scripts/voiceover.mjs --source eleven   # scratch narration from ElevenLabs (timing only)
 *   node scripts/voiceover.mjs --source human    # your recordings in recordings/<id>.{wav,m4a,mp3,aiff,caf}
 *   node scripts/voiceover.mjs --source human --only v03   # redo one scene
 *
 * Human recordings: run `python scripts/align_recordings.py` first. It writes
 * recordings/alignment.json with exact speech boundaries and word timings, so
 * each take is cut precisely around your words (no dead air), lightly cleaned
 * (80 Hz high-pass + gentle denoise), click-free faded, and normalized to
 * -16 LUFS. Word timings also become src/cues.json, which the scenes use to
 * reveal cards and diagrams exactly as you say the matching words. Without
 * alignment.json it falls back to threshold-based silence trimming.
 *
 * Measured durations go to src/vo-manifest.json; each scene lasts
 * max(minSecs, narration + 0.9 s), so the film re-times itself.
 *
 * Based on /Users/mrnetwork/Syntura/video/scripts/voiceover.mjs.
 */

import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { execFileSync, spawnSync } from "node:child_process";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const CACHE = join(ROOT, "vo-cache");
const RECORDINGS = join(ROOT, "recordings");
const ALIGNMENT = join(RECORDINGS, "alignment.json");
const OUT = join(ROOT, "public", "vo");
const MANIFEST = join(ROOT, "src", "vo-manifest.json");
const CUES = join(ROOT, "src", "cues.json");
const API = "https://api.elevenlabs.io/v1";
const PAD_SECS = 0.9;          // must match PAD_SECS in src/Resqio.tsx
const LIMIT_SECS = 238;        // keep the film under 4:00
const LEAD_SECS = 0.12;        // breath before your first word
const TAIL_SECS = 0.30;        // natural decay after your last word

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

const NORMALIZE = "loudnorm=I=-16:TP=-1.5:LRA=11";
const CLEAN = "highpass=f=80,afftdn=nf=-42:tn=1:nr=8";
const trim = (db) => `silenceremove=start_periods=1:start_threshold=${db}dB:start_silence=0.05`;
// Scratch TTS is near-silent between takes; threshold trimming is exact enough.
const ELEVEN_CHAIN = `${trim(-45)},areverse,${trim(-45)},areverse,${NORMALIZE}`;
// Room tone on phone recordings sits around -42 dB, so fall back to a higher threshold.
const HUMAN_FALLBACK_CHAIN = `${CLEAN},${trim(-35)},areverse,${trim(-35)},areverse,${NORMALIZE}`;

// Gentle voice compression evens out phrase-to-phrase level before loudness matching.
const COMPRESS = "acompressor=threshold=-20dB:ratio=2.5:attack=8:release=120:makeup=1";

function humanChain(align, fileSecs) {
  const start = Math.max(0, align.start - LEAD_SECS);
  const end = Math.min(fileSecs, align.end + TAIL_SECS);
  const len = end - start;
  const pre = [
    `atrim=start=${start.toFixed(3)}:end=${end.toFixed(3)}`,
    "asetpts=PTS-STARTPTS",
    CLEAN,
    COMPRESS,
    "afade=t=in:d=0.02",
    `afade=t=out:st=${Math.max(0, len - 0.08).toFixed(3)}:d=0.08`,
  ].join(",");
  return { start, pre };
}

// Two-pass loudnorm: measure, then apply the exact gain so every take lands on -16 LUFS.
function measuredNormalize(input, pre) {
  const r = spawnSync("ffmpeg", ["-hide_banner", "-nostats", "-i", input, "-af", `${pre},${NORMALIZE}:print_format=json`, "-f", "null", "-"], { encoding: "utf8" });
  const m = JSON.parse(r.stderr.slice(r.stderr.lastIndexOf("{"), r.stderr.lastIndexOf("}") + 1));
  return `${NORMALIZE}:measured_I=${m.input_i}:measured_TP=${m.input_tp}:measured_LRA=${m.input_lra}:measured_thresh=${m.input_thresh}:offset=${m.target_offset}:linear=true`;
}

const normWord = (w) => w.toLowerCase().replace(/[^a-z0-9]/g, "");

// Seconds from the start of the processed clip to each cue word, in cue order.
function cueTimes(scene, align, clipStart) {
  if (!scene.cues || !align?.words?.length) return null;
  const out = {};
  let from = 0;
  for (const [name, word] of Object.entries(scene.cues)) {
    const target = normWord(word);
    const idx = align.words.findIndex((w, i) => i >= from && normWord(w.w).startsWith(target));
    if (idx >= 0) {
      out[name] = Math.max(0, Math.round((align.words[idx].s - clipStart) * 1000) / 1000);
      from = idx;
    }
  }
  return out;
}

const { scenes } = JSON.parse(readFileSync(join(ROOT, "narration.json"), "utf8"));
mkdirSync(CACHE, { recursive: true });
mkdirSync(OUT, { recursive: true });

const previous = existsSync(MANIFEST) ? JSON.parse(readFileSync(MANIFEST, "utf8")) : { scenes: {} };
const mergePrevious = Boolean(ONLY) && previous.source === SOURCE;
const durations = mergePrevious ? { ...previous.scenes } : {};
const cues = mergePrevious && existsSync(CUES) ? JSON.parse(readFileSync(CUES, "utf8")) : {};

let alignment = null;
if (SOURCE === "human") {
  const missing = scenes.filter((s) => (!ONLY || s.id === ONLY) && !findRecording(s.id)).map((s) => s.id);
  if (missing.length) {
    console.error(`\nMissing recordings in recordings/: ${missing.join(", ")}\nName each file after its scene id, e.g. recordings/v01.m4a\n`);
    process.exit(1);
  }
  if (existsSync(ALIGNMENT)) {
    alignment = JSON.parse(readFileSync(ALIGNMENT, "utf8"));
  } else {
    console.warn("No recordings/alignment.json - run `python scripts/align_recordings.py` for word-exact trimming and cues.");
  }
}

console.log(`\nSource: ${SOURCE}${SOURCE === "eleven" ? ` (voice ${VOICE}, ${MODEL}) - SCRATCH, for timing only` : " (your recordings)"}\n`);

for (const s of scenes) {
  if (ONLY && s.id !== ONLY) continue;
  const dest = join(OUT, `${s.id}.mp3`);
  let note = "";
  if (SOURCE === "eleven") {
    const text = s.say || s.text;
    const raw = join(CACHE, `${s.id}.raw.mp3`);
    const stamp = join(CACHE, `${s.id}.stamp`);
    const want = JSON.stringify({ text, voice: VOICE, model: MODEL, VOICE_SETTINGS });
    const fresh = existsSync(raw) && existsSync(stamp) && readFileSync(stamp, "utf8") === want;
    if (!fresh) { await synthesise(text, raw); writeFileSync(stamp, want); }
    ff(["-i", raw, "-af", ELEVEN_CHAIN, "-ar", "48000", "-ac", "1", "-c:a", "libmp3lame", "-b:a", "192k", dest]);
    note = fresh ? "cached" : "synthesised";
    delete cues[s.id];
  } else {
    const input = findRecording(s.id);
    const align = alignment?.[s.id];
    if (align) {
      const { start, pre } = humanChain(align, durationOf(input));
      ff(["-i", input, "-af", `${pre},${measuredNormalize(input, pre)}`, "-ar", "48000", "-ac", "1", "-c:a", "libmp3lame", "-b:a", "192k", dest]);
      const sceneCues = cueTimes(s, align, start);
      if (sceneCues) cues[s.id] = sceneCues; else delete cues[s.id];
      note = `word-exact trim, match ${Math.round(align.match * 100)}%` + (sceneCues ? `, ${Object.keys(sceneCues).length}/${Object.keys(s.cues).length} cues` : "");
    } else {
      ff(["-i", input, "-af", HUMAN_FALLBACK_CHAIN, "-ar", "48000", "-ac", "1", "-c:a", "libmp3lame", "-b:a", "192k", dest]);
      delete cues[s.id];
      note = "threshold trim (no alignment)";
    }
  }
  const secs = durationOf(dest);
  durations[s.id] = Math.round(secs * 100) / 100;
  const sceneSecs = Math.max(s.minSecs, secs + PAD_SECS);
  const words = s.text.split(/\s+/).length;
  console.log(`  ${s.id} ${secs.toFixed(2)}s spoken -> scene ${sceneSecs.toFixed(1)}s  (${Math.round(words / secs * 60)} wpm)  ${note}`);
}

writeFileSync(MANIFEST, JSON.stringify({
  source: SOURCE, voice: SOURCE === "eleven" ? VOICE : "human", generated: new Date().toISOString(), scenes: durations,
}, null, 2) + "\n");
writeFileSync(CUES, JSON.stringify(cues, null, 2) + "\n");

const total = scenes.reduce((a, s) => a + Math.max(s.minSecs, (durations[s.id] ?? 0) + PAD_SECS), 0);
console.log(`\nFilm length: ${Math.floor(total / 60)}:${String(Math.round(total % 60)).padStart(2, "0")} (${total.toFixed(1)}s)`);
if (total > LIMIT_SECS) {
  console.log(`WARNING: over ${LIMIT_SECS}s - trim narration to stay under 4:00.`);
  process.exitCode = 2;
}
console.log(`Wrote src/vo-manifest.json and src/cues.json\n`);

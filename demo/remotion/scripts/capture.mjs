// Screen clips for the Resqio demo video, recorded headless with Playwright
// (system Google Chrome) at 1920x1080, converted to H.264 in public/clips.
//
//   node scripts/capture.mjs            # record clips that don't exist yet
//   node scripts/capture.mjs --force    # re-record everything (in order: seed -> cycle -> accept)
//
// Records the LOCAL copy of the site so the shared live board is never reset
// mid-recording. Based on /Users/mrnetwork/Triadr/demo/remotion/scripts/capture.mjs.
import { chromium } from 'playwright'
import { execSync } from 'node:child_process'
import fs from 'node:fs'
import path from 'node:path'

const BASE = process.env.CAPTURE_BASE || 'http://localhost:3003'
const API = process.env.CAPTURE_API || 'http://localhost:5001'
const FORCE = process.argv.includes('--force')
const OUT = path.resolve('public/clips')
const TMP = path.resolve('clips-tmp')
const MANIFEST = path.resolve('src/clips.json')
fs.mkdirSync(OUT, { recursive: true }); fs.mkdirSync(TMP, { recursive: true })
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

async function api(route, method = 'GET') {
  const res = await fetch(API + route, { method })
  if (!res.ok) throw new Error(`${method} ${route} -> HTTP ${res.status}`)
  return res.json()
}

async function scrollBy(page, px, { step = 8, every = 14 } = {}) {
  const n = Math.round(Math.abs(px) / step), dir = px < 0 ? -1 : 1
  for (let i = 0; i < n; i++) { await page.mouse.wheel(0, dir * step); await sleep(every) }
}

async function record(name, seconds, run) {
  const target = path.join(OUT, `${name}.mp4`)
  if (fs.existsSync(target) && !FORCE) { console.log(`${name}: present, skipping`); return }
  const browser = await chromium.launch({ channel: 'chrome', headless: true })
  const dir = path.join(TMP, name)
  fs.rmSync(dir, { recursive: true, force: true })
  const ctx = await browser.newContext({
    viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1, colorScheme: 'dark',
    recordVideo: { dir, size: { width: 1920, height: 1080 } },
  })
  const page = await ctx.newPage()
  const t0 = Date.now()
  let failed = null
  try { await run(page) } catch (e) { failed = e.message.split('\n')[0] }
  const left = seconds * 1000 - (Date.now() - t0)
  if (left > 0) await sleep(left)
  await ctx.close(); await browser.close()
  const webm = fs.readdirSync(dir).find((f) => f.endsWith('.webm'))
  execSync(`ffmpeg -y -loglevel error -i "${path.join(dir, webm)}" -r 30 -c:v libx264 -preset veryfast -crf 18 -pix_fmt yuv420p -vf scale=1920:1080 -an "${target}"`)
  const d = execSync(`ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "${target}"`).toString().trim()
  console.log(`${name}: ${Number(d).toFixed(1)}s${failed ? `  (step failed: ${failed})` : ''}`)
}

// 1. Landing page hero: the live pipeline animation loops every 14 s.
await record('landing', 16, async (page) => {
  await page.goto(`${BASE}/`, { waitUntil: 'networkidle' })
  await page.mouse.move(1910, 1070)
})

// 2. Board: start empty, then four neighbors text in.
await record('board-seed', 15, async (page) => {
  await api('/demo/reset', 'POST')
  await page.goto(`${BASE}/board`, { waitUntil: 'networkidle' })
  await page.mouse.move(1910, 1070)
  await sleep(2500)
  await page.click('button:has-text("Seed texts")')
  await sleep(4500)
  await scrollBy(page, 420); await sleep(2800)
  await scrollBy(page, -420)
})

// 3. One background cycle: crisis 5/5, match line on the map, the approval ping.
await record('board-cycle', 16, async (page) => {
  await page.goto(`${BASE}/board`, { waitUntil: 'networkidle' })
  await page.mouse.move(1910, 1070)
  await sleep(2200)
  await page.click('button:has-text("Run cycle")')
  await page.waitForSelector('text=CRISIS 5/5', { timeout: 60000 })
  await sleep(3500)
  await scrollBy(page, 560); await sleep(3500)
})

// 4. A human decides: ACCEPT, then DELIVERED; the map line turns green.
await record('board-accept', 18, async (page) => {
  await page.goto(`${BASE}/board`, { waitUntil: 'networkidle' })
  await page.mouse.move(1910, 1070)
  const status = await api('/status')
  const match = status.matches.find((m) => m.status === 'pending_approval')
  if (!match) throw new Error('no pending match - record board-cycle first')
  await sleep(1500)
  await scrollBy(page, 560); await sleep(900)
  const input = page.locator('input[placeholder^="ACCEPT"]')
  await input.click()
  await input.type(`ACCEPT ${match.id}`, { delay: 45 }); await sleep(400)
  await page.click('button:has-text("Send")'); await sleep(3200)
  await input.type(`DELIVERED ${match.id}`, { delay: 45 }); await sleep(400)
  await page.click('button:has-text("Send")'); await sleep(3000)
  await scrollBy(page, -560); await sleep(3500)
})

// Manifest of clips that exist, so the composition never crashes on a missing file.
const clips = {}
for (const f of fs.readdirSync(OUT).filter((f) => f.endsWith('.mp4'))) {
  const d = execSync(`ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "${path.join(OUT, f)}"`).toString().trim()
  clips[f.replace(/\.mp4$/, '')] = Math.round(Number(d) * 10) / 10
}
fs.writeFileSync(MANIFEST, JSON.stringify({ clips }, null, 2) + '\n')
console.log(`capture done; src/clips.json lists ${Object.keys(clips).length} clip(s)`)

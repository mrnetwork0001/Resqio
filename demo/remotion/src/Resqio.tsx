// The Resqio demo film. Scene lengths come from the narration manifest:
// each scene lasts max(minSecs, narration + PAD_SECS), so recordings of any
// pace re-time the film without clipping a word.
import React from 'react'
import { AbsoluteFill, Audio, Img, Sequence, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from 'remotion'
import narration from '../narration.json'
import voManifest from './vo-manifest.json'
import cuesManifest from './cues.json'
import { Backdrop, Body, C, Caption, Chip, Counter, Eyebrow, FONT, Footage, Headline, SceneFade, useRise } from './ui'

type SceneDef = { id: string; minSecs: number; text: string; say?: string }
type SceneProps = { dur: number; cue: (name: string, fallback: number) => number }

export const FPS = 30
const PAD_SECS = 0.9 // keep in sync with scripts/voiceover.mjs
const VO_DELAY_FRAMES = 6
const clamp = { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' } as const

const SCENES = (narration as { scenes: SceneDef[] }).scenes
const VO = voManifest as { source: string | null; scenes: Record<string, number> }
const CUES = cuesManifest as Record<string, Record<string, number>>

const Layout: React.FC<{ children: React.ReactNode; glow?: 'accent' | 'danger' | 'ok' }> = ({ children, glow }) => (
  <AbsoluteFill>
    <Backdrop glow={glow} />
    <AbsoluteFill style={{ padding: '110px 130px' }}>{children}</AbsoluteFill>
  </AbsoluteFill>
)

// v01 ─ Title
function Title() {
  const frame = useCurrentFrame()
  const { fps } = useVideoConfig()
  const s = spring({ frame, fps, config: { damping: 200 } })
  return (
    <AbsoluteFill>
      <Backdrop />
      <AbsoluteFill style={{ alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 40 }}>
        <Img src={staticFile('brand/resqio-header.png')} style={{ width: 1000, opacity: s, transform: `scale(${0.92 + 0.08 * s})` }} />
        <div style={{ ...useRise(16), fontFamily: FONT.mono, fontWeight: 600, color: C.accent, fontSize: 28, letterSpacing: '0.24em', textTransform: 'uppercase' }}>
          Autonomous community disaster logistics
        </div>
        <div style={{ ...useRise(28), fontFamily: FONT.mono, color: C.muted, fontSize: 22, letterSpacing: '0.16em', textTransform: 'uppercase' }}>
          Strands Agents SDK · Amazon Bedrock · Good Neighbor Agents
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  )
}

const StatCard: React.FC<{ delay: number; tone: string; label: string; value: React.ReactNode; sub: string; valueSize?: number }> = ({
  delay,
  tone,
  label,
  value,
  sub,
  valueSize = 64,
}) => (
  <div style={{ ...useRise(delay, 34), flex: 1, background: C.panel, border: `1px solid ${C.line}`, borderTop: `6px solid ${tone}`, padding: '30px 34px 34px' }}>
    <div style={{ fontFamily: FONT.mono, fontWeight: 600, fontSize: 20, letterSpacing: '0.2em', color: tone, textTransform: 'uppercase' }}>{label}</div>
    <div style={{ fontFamily: FONT.display, fontSize: valueSize, lineHeight: 1.02, color: C.ink, textTransform: 'uppercase', marginTop: 16 }}>{value}</div>
    <div style={{ fontFamily: FONT.sans, fontSize: 26, color: C.muted, marginTop: 14 }}>{sub}</div>
  </div>
)

// v02 ─ The problem
function Problem({ cue }: SceneProps) {
  return (
    <Layout glow="danger">
      <Eyebrow color={C.danger}>The problem · Austin, Texas</Eyebrow>
      <div style={{ marginTop: 22 }}>
        <Headline size={110}>The grid fails when</Headline>
        <Headline size={110} outline delay={8}>the heat peaks.</Headline>
      </div>
      <div style={{ display: 'flex', gap: 28, marginTop: 64 }}>
        <StatCard delay={cue('heat', 22)} tone={C.danger} label="NWS alert · extreme" value="Excessive heat warning" sub="Heat index up to 112°F" valueSize={56} />
        <StatCard delay={cue('outage', 34)} tone={C.warn} label="Grid · Travis County" value={<Counter to={12400} delay={cue('outage', 34) + 6} frames={45} />} sub="customers without power" />
        <StatCard delay={cue('insulin', 46)} tone={C.danger} label="Incoming text · urgency 5/5" value="Insulin needs to stay cold" sub="82 years old · 42 Maple St" valueSize={56} />
      </div>
      <div style={{ marginTop: 46 }}>
        <Body delay={cue('emergency', 70)} size={34} color={C.ink}>Emergency lines are already flooded.</Body>
      </div>
    </Layout>
  )
}

// v03 ─ The help exists
function HelpExists({ cue }: SceneProps) {
  const frame = useCurrentFrame()
  const { fps } = useVideoConfig()
  const pop = (d: number) => spring({ frame: frame - d, fps, config: { damping: 12, mass: 0.5 } })
  const drawAt = cue('connect', 70)
  const line = interpolate(frame, [drawAt, drawAt + 40], [0, 1], clamp)
  const req = { x: 190, y: 430 }
  const gen = { x: 610, y: 160 }
  return (
    <Layout>
      <div style={{ display: 'flex', gap: 80, alignItems: 'center', height: '100%' }}>
        <div style={{ flex: 1 }}>
          <Eyebrow>A few blocks away</Eyebrow>
          <div style={{ marginTop: 22 }}>
            <Headline size={100}>The help exists.</Headline>
            <Headline size={100} outline delay={cue('missing', 40)}>The coordination</Headline>
            <Headline size={100} outline delay={cue('missing', 40) + 6}>doesn't.</Headline>
          </div>
        </div>
        <div style={{ ...useRise(6, 30), position: 'relative', width: 800, height: 600, background: C.panel, border: `1px solid ${C.line}` }}>
          <svg width={800} height={600} style={{ position: 'absolute', inset: 0 }}>
            {Array.from({ length: 8 }).map((_, r) =>
              Array.from({ length: 11 }).map((__, c) => (
                <rect key={`${r}-${c}`} x={22 + c * 70} y={22 + r * 70} width={52} height={52} fill="#191916" />
              )),
            )}
            <line
              x1={gen.x}
              y1={gen.y}
              x2={gen.x + (req.x - gen.x) * line}
              y2={gen.y + (req.y - gen.y) * line}
              stroke={C.accent}
              strokeWidth={5}
              strokeDasharray="16 12"
              strokeDashoffset={-frame * 1.2}
            />
            <circle cx={req.x} cy={req.y} r={20 * pop(20)} fill={C.danger} />
            <circle cx={req.x} cy={req.y} r={20 + ((frame % 45) / 45) * 34} fill="none" stroke={C.danger} strokeWidth={3} opacity={pop(20) * (1 - (frame % 45) / 45)} />
            <circle cx={gen.x} cy={gen.y} r={20 * pop(cue('generator', 42))} fill={C.ok} />
          </svg>
          <div style={{ ...useRise(26, 12), position: 'absolute', left: req.x - 40, top: req.y + 36 }}>
            <Chip color={C.danger}>Insulin · urgency 5/5</Chip>
          </div>
          <div style={{ ...useRise(cue('generator', 42) + 6, 12), position: 'absolute', left: gen.x - 260, top: gen.y - 74 }}>
            <Chip color={C.ok}>Generator · 7.5 kW</Chip>
          </div>
          <div style={{ ...useRise(drawAt + 34, 12), position: 'absolute', left: 330, top: 256 }}>
            <Chip color={C.accent} filled>1.2 km</Chip>
          </div>
        </div>
      </div>
    </Layout>
  )
}

// v04 ─ Who it's for
function WhoItsFor({ cue }: SceneProps) {
  const cards = [
    ['Block captains', 'A WhatsApp group and whatever is in the garages.'],
    ['Mutual-aid groups', 'Volunteers dispatched with routes, not group-chat chaos.'],
    ['Food banks', 'Cold-chain capacity matched to homes that lost power.'],
    ['Shelters', 'Cooling, power, and transport needs, staffed.'],
  ]
  return (
    <Layout>
      <Eyebrow>Who it's for</Eyebrow>
      <div style={{ marginTop: 22 }}>
        <Headline size={104}>Built for the people</Headline>
        <Headline size={104} outline delay={8}>who show up.</Headline>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, marginTop: 56, width: 1100 }}>
        {cards.map(([title, sub], i) => (
          <div key={title} style={{ ...useRise(cue(['block', 'mutual', 'food', 'shelters'][i], 22 + i * 10), 28), background: C.panel, border: `1px solid ${C.line}`, padding: '26px 30px' }}>
            <div style={{ fontFamily: FONT.display, fontSize: 44, color: C.ink, textTransform: 'uppercase' }}>{title}</div>
            <div style={{ fontFamily: FONT.sans, fontSize: 25, color: C.muted, marginTop: 8 }}>{sub}</div>
          </div>
        ))}
      </div>
      <div style={{ ...useRise(cue('text', 78), 30), position: 'absolute', right: 130, bottom: 150, width: 520 }}>
        <div style={{ background: '#1f2c1f', color: C.ink, fontFamily: FONT.sans, fontSize: 30, lineHeight: 1.35, padding: '22px 26px', borderRadius: '22px 22px 4px 22px' }}>
          HELP: insulin needs refrigeration at 42 Maple St.
        </div>
        <div style={{ fontFamily: FONT.mono, fontSize: 22, color: C.accent, letterSpacing: '0.14em', textTransform: 'uppercase', marginTop: 18, textAlign: 'right', whiteSpace: 'nowrap' }}>
          No app. No account. Just a text.
        </div>
      </div>
    </Layout>
  )
}

// v05 ─ Silent by design (landing page)
function Landing({ dur }: SceneProps) {
  return (
    <AbsoluteFill>
      <Backdrop />
      <Footage name="landing" url="tryresqio.vercel.app" dur={dur} />
      <Caption eyebrow="Silent by design" text="Only asks a human when a delivery needs a yes." />
    </AbsoluteFill>
  )
}

// v06 ─ Three Strands agents
function Agents({ cue }: SceneProps) {
  const frame = useCurrentFrame()
  const nodes = [
    { verb: 'Watch', name: 'StrandsGridMonitor', what: 'NOAA alerts + outages → crisis 0-5', human: false },
    { verb: 'Match', name: 'StrandsResourceMatcher', what: 'Texts → offers and needs → best match', human: false },
    { verb: 'Route', name: 'StrandsVolunteerRouter', what: 'Safe trip + one approval message', human: false },
    { verb: 'Approve', name: 'Volunteer captain', what: 'One tap: accept or pass', human: true },
  ]
  return (
    <Layout>
      <Eyebrow>Built with the Strands Agents SDK</Eyebrow>
      <div style={{ marginTop: 22 }}>
        <Headline size={104}>Three agents.</Headline>
        <Headline size={104} outline delay={8}>One silent pipeline.</Headline>
      </div>
      <div style={{ display: 'flex', alignItems: 'stretch', marginTop: 80 }}>
        {nodes.map((n, i) => {
          const delay = cue(['grid', 'resource', 'volunteer', 'approval'][i], 30 + i * 60)
          const wire = interpolate(frame, [delay + 30, delay + 60], [0, 1], clamp)
          return (
            <React.Fragment key={n.verb}>
              <div
                style={{
                  ...useRise(delay, 30),
                  width: 330,
                  background: n.human ? C.accent : C.panel,
                  border: `1px solid ${n.human ? C.accent : C.line}`,
                  padding: '26px 26px 30px',
                }}
              >
                <div style={{ fontFamily: FONT.display, fontSize: 60, textTransform: 'uppercase', color: n.human ? C.ground : C.ink }}>{n.verb}</div>
                <div style={{ fontFamily: FONT.mono, fontSize: 19, fontWeight: 600, color: n.human ? C.ground : C.accent, marginTop: 8 }}>{n.name}</div>
                <div style={{ fontFamily: FONT.sans, fontSize: 24, lineHeight: 1.35, color: n.human ? C.ground : C.muted, marginTop: 14 }}>{n.what}</div>
              </div>
              {i < nodes.length - 1 ? (
                <div style={{ flex: 1, display: 'flex', alignItems: 'center' }}>
                  <div style={{ height: 4, width: `${wire * 100}%`, background: C.accent }} />
                </div>
              ) : null}
            </React.Fragment>
          )
        })}
      </div>
    </Layout>
  )
}

function BoardSeed({ dur }: SceneProps) {
  return (
    <AbsoluteFill>
      <Backdrop />
      <Footage name="board-seed" url="tryresqio.vercel.app/board" dur={dur} />
      <Caption eyebrow="Four neighbors text in" text="Every message becomes an offer or a need." />
    </AbsoluteFill>
  )
}

function BoardCycle({ dur }: SceneProps) {
  return (
    <AbsoluteFill>
      <Backdrop />
      <Footage name="board-cycle" url="tryresqio.vercel.app/board" dur={dur} />
      <Caption eyebrow="One background cycle" text="Crisis 5/5. Generator matched to insulin, 1.2 km." />
    </AbsoluteFill>
  )
}

// v09 ─ Exactly one message
function OneMessage({ dur }: SceneProps) {
  const frame = useCurrentFrame()
  const message =
    'Resqio: generator needed for insulin refrigeration (urgency 5/5). Bring the generator from Springdale Rd to 42 Maple St - 1.18 km, ~7 min. Extreme heat: carry water. Signals may be dark: treat every intersection as a 4-way stop.'
  const shown = Math.floor(interpolate(frame, [18, Math.max(30, dur * 0.62)], [0, message.length], clamp))
  const buttons = useRise(Math.round(dur * 0.66), 18)
  return (
    <Layout>
      <div style={{ display: 'flex', gap: 90, alignItems: 'center', height: '100%' }}>
        <div style={{ flex: 1 }}>
          <Eyebrow>Exactly one message</Eyebrow>
          <div style={{ marginTop: 22 }}>
            <Headline size={112}>One ping.</Headline>
            <Headline size={112} outline delay={8}>One decision.</Headline>
          </div>
          <div style={{ marginTop: 34, width: 640 }}>
            <Body delay={20}>Heat and dark-intersection guidance come built in. Nothing else ever buzzes a captain's phone.</Body>
          </div>
        </div>
        <div style={{ ...useRise(6, 34), width: 780, background: C.panel, border: `1px solid ${C.line}`, borderRadius: 18, padding: '30px 34px 34px' }}>
          <div style={{ fontFamily: FONT.mono, fontSize: 20, fontWeight: 600, letterSpacing: '0.16em', color: C.muted, textTransform: 'uppercase' }}>
            Approval ping · volunteer captain
          </div>
          <div style={{ fontFamily: FONT.sans, fontSize: 32, lineHeight: 1.45, color: C.ink, marginTop: 18, minHeight: 330 }}>
            {message.slice(0, shown)}
            <span style={{ color: C.accent, opacity: frame % 30 < 15 ? 1 : 0 }}>▍</span>
          </div>
          <div style={{ ...buttons, display: 'flex', gap: 18, marginTop: 16 }}>
            <Chip color={C.ok} filled style={{ flex: 1, textAlign: 'center' }}>Accept</Chip>
            <Chip color={C.muted} style={{ flex: 1, textAlign: 'center' }}>Pass</Chip>
          </div>
        </div>
      </div>
    </Layout>
  )
}

function BoardAccept({ dur }: SceneProps) {
  return (
    <AbsoluteFill>
      <Backdrop glow="ok" />
      <Footage name="board-accept" url="tryresqio.vercel.app/board" dur={dur} />
      <Caption eyebrow="A human decides" text="Accept. Deliver. Loop closed." />
    </AbsoluteFill>
  )
}

// v11 ─ The model proposes, the code decides
function ModelProposes() {
  const lines: Array<[string, string]> = [
    ['kw', 'matcher = Agent('],
    ['', '    model=BedrockModel(model_id=settings.bedrock_model_id),'],
    ['', '    tools=[list_open_offers, list_open_requests, compute_distance_km],'],
    ['kw', ')'],
    ['', 'result = matcher(prompt, structured_output_model=MatchProposal)'],
    ['ok', 'proposal = result.structured_output   # validated Pydantic model'],
    ['ok', 'store.record_match(match)   # re-checked under a lock before booking'],
  ]
  return (
    <Layout>
      <Eyebrow>Validated, not trusted</Eyebrow>
      <div style={{ marginTop: 22 }}>
        <Headline size={104}>The model proposes.</Headline>
        <Headline size={104} outline delay={8}>The code decides.</Headline>
      </div>
      <div style={{ ...useRise(20, 30), marginTop: 56, background: '#0d0d0c', border: `1px solid ${C.line}`, padding: '34px 40px', width: 1480 }}>
        {lines.map(([kind, text], i) => (
          <div
            key={i}
            style={{
              ...useRise(30 + i * 9, 10),
              fontFamily: FONT.mono,
              fontSize: 30,
              lineHeight: 1.7,
              whiteSpace: 'pre',
              color: kind === 'kw' ? C.accent : kind === 'ok' ? C.ok : C.ink,
            }}
          >
            {text}
          </div>
        ))}
      </div>
    </Layout>
  )
}

// v12 ─ Built for the worst day
function WorstDay({ cue }: SceneProps) {
  const rows: Array<[string, string, string]> = [
    ['Crisis assessment', 'Claude scores the situation', 'Severity thresholds + county overlap'],
    ['Reading texts', 'Claude parses informal SMS', 'Word-boundary keyword parser'],
    ['Matching', 'Claude + distance tools', 'Compatibility matrix + distance'],
    ['Routing', 'Claude writes hazard-aware plans', 'Deterministic planner'],
  ]
  return (
    <Layout>
      <Eyebrow>Built for the worst day</Eyebrow>
      <div style={{ marginTop: 22 }}>
        <Headline size={104}>Works when</Headline>
        <Headline size={104} outline delay={8}>the cloud doesn't.</Headline>
      </div>
      <div style={{ marginTop: 50, width: 1560, border: `1px solid ${C.line}` }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.3fr 1.3fr', background: C.raised, fontFamily: FONT.mono, fontSize: 20, fontWeight: 600, letterSpacing: '0.16em', textTransform: 'uppercase' }}>
          <div style={{ padding: '16px 24px', color: C.muted }}>Step</div>
          <div style={{ padding: '16px 24px', color: C.accent }}>Amazon Bedrock</div>
          <div style={{ padding: '16px 24px', color: C.ok }}>If the cloud is down</div>
        </div>
        {rows.map(([step, live, fallback], i) => (
          <div key={step} style={{ ...useRise(cue('fallback', 24) + i * 10, 16), display: 'grid', gridTemplateColumns: '1fr 1.3fr 1.3fr', borderTop: `1px solid ${C.line}`, fontFamily: FONT.sans, fontSize: 28 }}>
            <div style={{ padding: '18px 24px', color: C.ink, fontWeight: 600 }}>{step}</div>
            <div style={{ padding: '18px 24px', color: C.muted }}>{live}</div>
            <div style={{ padding: '18px 24px', color: C.ink }}>{fallback}</div>
          </div>
        ))}
      </div>
      <div style={{ ...useRise(cue('bedrock', 70), 16), display: 'flex', gap: 18, marginTop: 34 }}>
        <Chip color={C.accent}>Packaged for Amazon Bedrock AgentCore</Chip>
        <Chip color={C.muted}>Background daemon · HealthyBusy</Chip>
      </div>
    </Layout>
  )
}

// v13 ─ Guarded decisions
function Guarded({ dur, cue }: SceneProps) {
  const frame = useCurrentFrame()
  const states = ['Proposed', 'Pending', 'Approved', 'Delivered']
  const hit = cue('pass', Math.round(dur * 0.45)) + 10
  const tokenX = interpolate(frame, [hit - 24, hit, hit + 16], [420, 0, 150], clamp)
  const tokenOpacity = interpolate(frame, [hit - 30, hit - 20, hit + 30, hit + 42], [0, 1, 1, 0.35], clamp)
  const shake = frame >= hit && frame < hit + 10 ? Math.sin((frame - hit) * 2.4) * 8 : 0
  const verdict = useRise(Math.max(hit + 8, cue('undo', hit + 8)), 16)
  return (
    <Layout>
      <Eyebrow>Guarded decisions</Eyebrow>
      <div style={{ marginTop: 22 }}>
        <Headline size={104}>A late reply can't</Headline>
        <Headline size={104} outline delay={8}>undo a delivery.</Headline>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 22, marginTop: 110, position: 'relative' }}>
        {states.map((s, i) => (
          <React.Fragment key={s}>
            <div style={{ ...useRise(20 + i * 8, 20), transform: s === 'Approved' ? `translateX(${shake}px)` : undefined }}>
              <Chip color={s === 'Approved' ? C.accent : C.muted} filled={s === 'Approved'} style={{ fontSize: 30, padding: '16px 28px' }}>
                {s}
              </Chip>
            </div>
            {i < states.length - 1 ? <span style={{ fontFamily: FONT.mono, fontSize: 36, color: C.muted }}>→</span> : null}
          </React.Fragment>
        ))}
        <div style={{ position: 'absolute', left: 820, top: -110, opacity: tokenOpacity, transform: `translateX(${tokenX}px)` }}>
          <Chip color={C.danger} style={{ fontSize: 28 }}>Late PASS from captain 2</Chip>
        </div>
      </div>
      <div style={{ ...verdict, marginTop: 60, fontFamily: FONT.mono, fontSize: 30, color: C.danger }}>
        "match is already approved - no change made."
      </div>
    </Layout>
  )
}

// v14 ─ Close
function Close({ cue }: SceneProps) {
  return (
    <AbsoluteFill>
      <Backdrop />
      <AbsoluteFill style={{ alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 34 }}>
        <Img src={staticFile('brand/resqio-header.png')} style={{ ...useRise(0, 20), width: 760 }} />
        <div style={{ ...useRise(14, 24), fontFamily: FONT.display, fontSize: 96, color: C.ink, textTransform: 'uppercase' }}>
          The next storm isn't waiting.
        </div>
        <div style={{ ...useRise(cue('fork', 26), 16), fontFamily: FONT.mono, fontWeight: 600, fontSize: 40, color: C.accent }}>tryresqio.vercel.app</div>
        <div style={{ ...useRise(cue('fork', 26) + 8, 16), fontFamily: FONT.mono, fontSize: 24, color: C.muted, letterSpacing: '0.08em' }}>
          github.com/mrnetwork0001/Resqio · Open source · Apache 2.0
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  )
}

const COMPONENTS: Record<string, React.FC<SceneProps>> = {
  v01: Title,
  v02: Problem,
  v03: HelpExists,
  v04: WhoItsFor,
  v05: Landing,
  v06: Agents,
  v07: BoardSeed,
  v08: BoardCycle,
  v09: OneMessage,
  v10: BoardAccept,
  v11: ModelProposes,
  v12: WorstDay,
  v13: Guarded,
  v14: Close,
}

export const TIMELINE = (() => {
  let start = 0
  return SCENES.map((s) => {
    const frames = Math.round(Math.max(s.minSecs, (VO.scenes[s.id] ?? 0) + PAD_SECS) * FPS)
    const item = { id: s.id, start, frames }
    start += frames
    return item
  })
})()

export const RESQIO_DURATION = TIMELINE.reduce((sum, t) => sum + t.frames, 0)

// Frame (within a scene) where a spoken cue word begins, so reveals land on the words.
// Falls back to the scene's default timing when there is no cue for this voice.
const cueFor = (id: string) => (name: string, fallback: number) => {
  const secs = CUES[id]?.[name]
  return secs == null ? fallback : Math.max(0, VO_DELAY_FRAMES + Math.round(secs * FPS) - 3)
}

const ScratchTag: React.FC = () => (
  <div
    style={{
      position: 'absolute',
      top: 22,
      right: 26,
      fontFamily: FONT.mono,
      fontSize: 18,
      fontWeight: 600,
      letterSpacing: '0.14em',
      color: C.warn,
      border: `1px solid ${C.warn}`,
      padding: '6px 12px',
      background: 'rgba(10,10,10,0.8)',
      textTransform: 'uppercase',
    }}
  >
    Scratch narration · not final
  </div>
)

export const Resqio: React.FC = () => (
  <AbsoluteFill style={{ background: C.ground }}>
    {TIMELINE.map((t) => {
      const Scene = COMPONENTS[t.id]
      return (
        <Sequence key={t.id} from={t.start} durationInFrames={t.frames} name={t.id}>
          <SceneFade dur={t.frames}>{Scene ? <Scene dur={t.frames} cue={cueFor(t.id)} /> : <Backdrop />}</SceneFade>
          {VO.scenes[t.id] ? (
            <Sequence from={VO_DELAY_FRAMES}>
              <Audio src={staticFile(`vo/${t.id}.mp3`)} />
            </Sequence>
          ) : null}
        </Sequence>
      )
    })}
    {VO.source !== 'human' ? <ScratchTag /> : null}
  </AbsoluteFill>
)

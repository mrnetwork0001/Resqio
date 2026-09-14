// Resqio motion kit: brand tokens, fonts, and the building blocks every scene uses.
// Patterns adapted from the Meritr, Triadr, Bazar, and Syntura demo videos.
import React from 'react'
import {
  AbsoluteFill,
  Easing,
  OffthreadVideo,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion'
import { loadFont as loadAnton } from '@remotion/google-fonts/Anton'
import { loadFont as loadPlexSans } from '@remotion/google-fonts/IBMPlexSans'
import { loadFont as loadPlexMono } from '@remotion/google-fonts/IBMPlexMono'
import clipsManifest from './clips.json'

const anton = loadAnton('normal', { weights: ['400'], subsets: ['latin'] })
const plexSans = loadPlexSans('normal', { weights: ['400', '600'], subsets: ['latin'] })
const plexMono = loadPlexMono('normal', { weights: ['400', '600'], subsets: ['latin'] })

export const FONT = {
  display: anton.fontFamily,
  sans: plexSans.fontFamily,
  mono: plexMono.fontFamily,
}

// Same palette as the Resqio web client (client/tailwind.config.ts).
export const C = {
  ground: '#0a0a0a',
  panel: '#121211',
  raised: '#1a1a18',
  line: '#272723',
  ink: '#f1f1ec',
  muted: '#8b8b84',
  accent: '#d7ff00',
  ok: '#52c776',
  warn: '#dcae3c',
  danger: '#e5484d',
}

const clamp = { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' } as const

export function useRise(delay = 0, dist = 24): React.CSSProperties {
  const frame = useCurrentFrame()
  const { fps } = useVideoConfig()
  const p = spring({ frame: frame - delay, fps, config: { damping: 200, mass: 0.6 } })
  return { opacity: p, transform: `translateY(${(1 - p) * dist}px)` }
}

export const SceneFade: React.FC<{ dur: number; children: React.ReactNode }> = ({ dur, children }) => {
  const frame = useCurrentFrame()
  const opacity = interpolate(frame, [0, 10, dur - 10, dur], [0, 1, 1, 0], clamp)
  return <AbsoluteFill style={{ opacity }}>{children}</AbsoluteFill>
}

export const Backdrop: React.FC<{ glow?: 'accent' | 'danger' | 'ok' }> = ({ glow = 'accent' }) => {
  const frame = useCurrentFrame()
  const x = 62 + Math.sin(frame / 95) * 10
  const y = 38 + Math.cos(frame / 120) * 9
  const tint = {
    accent: 'rgba(215,255,0,0.09)',
    danger: 'rgba(229,72,77,0.14)',
    ok: 'rgba(82,199,118,0.11)',
  }[glow]
  const fadeMask = 'radial-gradient(ellipse at center, black 35%, transparent 80%)'
  return (
    <AbsoluteFill style={{ background: C.ground }}>
      <AbsoluteFill style={{ background: `radial-gradient(1000px 700px at ${x}% ${y}%, ${tint}, transparent 70%)` }} />
      <AbsoluteFill
        style={{
          backgroundImage:
            'linear-gradient(rgba(241,241,236,0.035) 1px, transparent 1px), linear-gradient(90deg, rgba(241,241,236,0.035) 1px, transparent 1px)',
          backgroundSize: '80px 80px',
          maskImage: fadeMask,
          WebkitMaskImage: fadeMask,
        }}
      />
    </AbsoluteFill>
  )
}

export const Eyebrow: React.FC<{ children: React.ReactNode; delay?: number; color?: string }> = ({
  children,
  delay = 0,
  color = C.accent,
}) => (
  <div
    style={{
      ...useRise(delay, 14),
      fontFamily: FONT.mono,
      fontWeight: 600,
      fontSize: 22,
      letterSpacing: '0.22em',
      textTransform: 'uppercase',
      color,
      display: 'flex',
      alignItems: 'center',
      gap: 14,
    }}
  >
    <span>✳</span>
    {children}
  </div>
)

export const Headline: React.FC<{ children: React.ReactNode; delay?: number; size?: number; outline?: boolean; color?: string }> = ({
  children,
  delay = 4,
  size = 104,
  outline = false,
  color = C.ink,
}) => (
  <div
    style={{
      ...useRise(delay, 30),
      fontFamily: FONT.display,
      fontSize: size,
      lineHeight: 0.95,
      letterSpacing: '0.01em',
      textTransform: 'uppercase',
      color: outline ? 'transparent' : color,
      WebkitTextStroke: outline ? `2px ${color}` : undefined,
    }}
  >
    {children}
  </div>
)

export const Body: React.FC<{ children: React.ReactNode; delay?: number; size?: number; color?: string }> = ({
  children,
  delay = 10,
  size = 32,
  color = C.muted,
}) => (
  <div style={{ ...useRise(delay, 16), fontFamily: FONT.sans, fontSize: size, lineHeight: 1.45, color }}>{children}</div>
)

export const Counter: React.FC<{ to: number; delay?: number; frames?: number }> = ({ to, delay = 0, frames = 40 }) => {
  const frame = useCurrentFrame()
  const p = interpolate(frame, [delay, delay + frames], [0, 1], { ...clamp, easing: Easing.out(Easing.cubic) })
  return <span style={{ fontVariantNumeric: 'tabular-nums' }}>{Math.round(to * p).toLocaleString('en-US')}</span>
}

export const Caption: React.FC<{ eyebrow: string; text: string; delay?: number }> = ({ eyebrow, text, delay = 18 }) => (
  <div
    style={{
      ...useRise(delay, 26),
      position: 'absolute',
      left: 64,
      bottom: 60,
      maxWidth: 1180,
      background: 'rgba(10,10,10,0.92)',
      borderLeft: `6px solid ${C.accent}`,
      padding: '22px 32px 24px',
      boxShadow: '0 20px 60px rgba(0,0,0,0.55)',
    }}
  >
    <div style={{ fontFamily: FONT.mono, fontWeight: 600, color: C.accent, fontSize: 20, letterSpacing: '0.2em', textTransform: 'uppercase' }}>
      {eyebrow}
    </div>
    <div style={{ fontFamily: FONT.display, color: C.ink, fontSize: 52, lineHeight: 1.04, textTransform: 'uppercase', marginTop: 8 }}>
      {text}
    </div>
  </div>
)

const CLIPS = (clipsManifest as { clips: Record<string, number> }).clips

// Frames of idle lead-in to skip per recorded clip (page load, map tiles).
const LEAD_IN: Record<string, number> = {
  'board-seed': 45,
  'board-cycle': 30,
  'board-accept': 60,
}

export const Footage: React.FC<{ name: string; url: string; dur: number; startFrom?: number }> = ({
  name,
  url,
  dur,
  startFrom = LEAD_IN[name] ?? 0,
}) => {
  const frame = useCurrentFrame()
  const scale = interpolate(frame, [0, dur], [1, 1.035], clamp)
  const rise = useRise(0, 30)
  const have = Boolean(CLIPS[name])
  return (
    <AbsoluteFill style={{ alignItems: 'center', paddingTop: 48 }}>
      <div
        style={{
          ...rise,
          width: 1600,
          borderRadius: 16,
          overflow: 'hidden',
          border: `1px solid ${C.line}`,
          background: C.panel,
          boxShadow: '0 40px 120px rgba(0,0,0,0.7)',
        }}
      >
        <div style={{ height: 46, display: 'flex', alignItems: 'center', gap: 10, padding: '0 20px', borderBottom: `1px solid ${C.line}` }}>
          {[C.danger, C.warn, C.ok].map((c) => (
            <span key={c} style={{ width: 12, height: 12, borderRadius: 6, background: c, opacity: 0.8 }} />
          ))}
          <span style={{ marginLeft: 18, fontFamily: FONT.mono, fontSize: 18, color: C.muted, background: C.raised, padding: '5px 16px', borderRadius: 8 }}>
            {url}
          </span>
        </div>
        <div style={{ width: 1600, height: 900, overflow: 'hidden', background: C.ground }}>
          {have ? (
            <OffthreadVideo
              src={staticFile(`clips/${name}.mp4`)}
              startFrom={startFrom}
              muted
              style={{ width: '100%', height: '100%', objectFit: 'cover', transform: `scale(${scale})`, transformOrigin: 'center top' }}
            />
          ) : (
            <AbsoluteFill style={{ alignItems: 'center', justifyContent: 'center', fontFamily: FONT.mono, color: C.warn, fontSize: 36 }}>
              RECORD CLIP: {name}
            </AbsoluteFill>
          )}
        </div>
      </div>
    </AbsoluteFill>
  )
}

export const Chip: React.FC<{ children: React.ReactNode; color?: string; filled?: boolean; style?: React.CSSProperties }> = ({
  children,
  color = C.accent,
  filled = false,
  style,
}) => (
  <span
    style={{
      fontFamily: FONT.mono,
      fontWeight: 600,
      fontSize: 22,
      letterSpacing: '0.12em',
      textTransform: 'uppercase',
      padding: '10px 18px',
      borderRadius: 999,
      border: `2px solid ${color}`,
      background: filled ? color : 'transparent',
      color: filled ? C.ground : color,
      whiteSpace: 'nowrap',
      ...style,
    }}
  >
    {children}
  </span>
)

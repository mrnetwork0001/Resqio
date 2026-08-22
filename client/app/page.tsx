import Link from "next/link";
import HeroAnimation from "@/components/HeroAnimation";
import SiteFooter from "@/components/SiteFooter";

const GITHUB = "https://github.com/mrnetwork0001/Resqio";

function Eyebrow({ children }: { children: React.ReactNode }) {
  return (
    <p className="font-mono text-[11px] font-semibold uppercase tracking-[0.18em] text-accent">
      {children}
    </p>
  );
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <h2 className="mt-2 font-display text-3xl leading-tight tracking-tight sm:text-4xl [text-wrap:balance]">
      {children}
    </h2>
  );
}

const STEPS = [
  {
    n: "1",
    title: "Watch",
    body: "Polls NOAA/NWS alerts and county-level grid outage data around the clock, correlating hazards that share county FIPS codes — extreme heat plus a feeder outage is treated as the compounding emergency it is.",
  },
  {
    n: "2",
    title: "Listen",
    body: "Neighbors text plain SMS — “Generator available in Sector 4”, “Insulin ice needed at 42 Maple St”. No app to install, no account to create, nothing to learn during a crisis.",
  },
  {
    n: "3",
    title: "Match",
    body: "When a crisis is active, supply is matched to need on urgency, vulnerability, and distance. Medical refrigeration, infants, and elderly residents outrank everything else. One offer serves one request — never double-booked.",
  },
  {
    n: "4",
    title: "Approve",
    body: "A volunteer captain gets one WhatsApp message with the route, the hazards, and two buttons. Accept dispatches the delivery; Pass puts both sides back on the board. Humans decide — the agent does everything else.",
  },
];

const AGENTS = [
  {
    name: "StrandsGridMonitor",
    role: "Crisis detection",
    body: "Reads weather and outage feeds and produces a validated 0–5 crisis assessment. Conservative by design: advisories alone stay silent; life-safety combinations activate the network.",
  },
  {
    name: "StrandsResourceMatcher",
    role: "Supply ↔ need matching",
    body: "Parses informal community texts into structured offers and requests, then proposes matches with spatial reasoning tools. Every proposal is re-validated against the live board before it's recorded.",
  },
  {
    name: "StrandsVolunteerRouter",
    role: "Safe dispatch",
    body: "Plans crisis-condition transit with per-hazard guidance — dark intersections, heat exposure, flooded roads — and writes the single approval ping a captain sees.",
  },
];

const PRINCIPLES = [
  {
    title: "Silent by default",
    body: "No crisis means zero messages. During a crisis, the only outbound traffic is an approval ping when a physical delivery needs a human yes. Nobody's phone buzzes for a status update.",
  },
  {
    title: "A human approves every action",
    body: "The agent never dispatches a volunteer on its own. Every physical action passes through a one-tap approval, and a guarded match lifecycle means a stale reply can never undo an accepted delivery.",
  },
  {
    title: "Works when the cloud doesn't",
    body: "Every AI reasoning step has a deterministic fallback. If Bedrock is unreachable mid-disaster, matching degrades gracefully instead of stopping — the pipeline keeps flowing on pure logic.",
  },
  {
    title: "Runs on a shelter laptop",
    body: "The community board is a JSON file, not a database cluster. The whole runtime is one Python process — deployable on Amazon Bedrock AgentCore, or on whatever machine the shelter has.",
  },
];

export default function Landing() {
  return (
    <div className="min-h-screen">
      {/* ── Nav ── */}
      <nav className="mx-auto flex max-w-6xl items-center gap-6 px-6 py-5">
        <span className="font-display text-2xl leading-none tracking-tight">
          RESQIO<span className="text-accent">.</span>
        </span>
        <div className="ml-auto flex items-center gap-5">
          <a
            href={GITHUB}
            className="hidden font-mono text-xs uppercase tracking-wider text-muted transition-colors hover:text-ink sm:block"
          >
            GitHub
          </a>
          <Link
            href="/board"
            className="border border-accent bg-accent/10 px-4 py-2 font-mono text-xs font-semibold uppercase tracking-wider text-accent transition-colors hover:bg-accent hover:text-ground focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent"
          >
            Launch App
          </Link>
        </div>
      </nav>

      {/* ── Hero ── */}
      <header className="mx-auto grid max-w-6xl items-center gap-12 px-6 pb-20 pt-10 lg:grid-cols-2 lg:gap-16">
        <div>
          <Eyebrow>Autonomous community disaster logistics</Eyebrow>
          <h1 className="mt-4 font-display text-4xl leading-[1.05] tracking-tight sm:text-5xl xl:text-[3.4rem] [text-wrap:balance]">
            When the power fails, neighbors are the fastest responders.
          </h1>
          <p className="mt-6 max-w-[52ch] text-lg leading-relaxed text-muted">
            Resqio is an AI agent that watches weather and grid feeds 24/7,
            matches spare generators, ice, and food to the most vulnerable
            requests texted in over plain SMS — and pings a volunteer captain
            on WhatsApp only when a delivery needs a human yes.
          </p>
          <div className="mt-8 flex flex-wrap items-center gap-4">
            <Link
              href="/board"
              className="border border-accent bg-accent px-6 py-3 font-mono text-sm font-semibold uppercase tracking-wider text-ground transition-colors hover:bg-accent/85 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
            >
              Launch App
            </Link>
            <a
              href={GITHUB}
              className="border border-line px-6 py-3 font-mono text-sm font-semibold uppercase tracking-wider text-ink transition-colors hover:border-muted focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent"
            >
              View source
            </a>
          </div>
          <p className="mt-6 font-mono text-[11px] uppercase tracking-wider text-muted/80">
            Open source · Apache 2.0 · Built on Strands Agents SDK + Amazon Bedrock AgentCore
          </p>
        </div>

        <div className="relative">
          <div className="overflow-hidden rounded-lg border border-line bg-panel shadow-[0_24px_80px_-24px_rgba(0,0,0,0.8)]">
            <div className="flex items-center gap-2 border-b border-line px-4 py-2.5">
              <span className="h-2.5 w-2.5 rounded-full bg-danger/70" />
              <span className="h-2.5 w-2.5 rounded-full bg-warn/70" />
              <span className="h-2.5 w-2.5 rounded-full bg-ok/70" />
              <span className="ml-3 font-mono text-[10px] uppercase tracking-[0.14em] text-muted">
                resqio · live watch
              </span>
              <span className="ml-auto flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-wider text-ok">
                <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-ok" />
                Autonomous
              </span>
            </div>
            <HeroAnimation />
          </div>
        </div>
      </header>

      {/* ── Problem ── */}
      <section className="border-y border-line bg-panel/60">
        <div className="mx-auto grid max-w-6xl gap-10 px-6 py-20 lg:grid-cols-[1fr_1.2fr]">
          <div>
            <Eyebrow>The problem</Eyebrow>
            <SectionTitle>The gap between 911 and a neighbor with a generator</SectionTitle>
          </div>
          <div className="flex flex-col gap-5 text-[17px] leading-relaxed text-muted lg:pt-12">
            <p>
              During severe weather and grid failures, community emergency
              services are overwhelmed within hours. The people at greatest
              risk — an 82-year-old whose insulin needs refrigeration, a family
              with a newborn and no cooling — can&apos;t wait in a call queue.
            </p>
            <p>
              Meanwhile the help usually already exists two blocks away: a
              neighbor with a 7.5&nbsp;kW generator, a chest freezer full of ice, a
              spare room with air conditioning. What&apos;s missing isn&apos;t capacity.
              It&apos;s coordination — at a moment when nobody has the bandwidth to
              coordinate anything.
            </p>
            <p className="text-ink">
              Resqio closes that gap by turning crisis coordination into a
              silent background process, run by AI agents, checked by humans.
            </p>
          </div>
        </div>
      </section>

      {/* ── How it works ── */}
      <section id="how-it-works" className="mx-auto max-w-6xl scroll-mt-8 px-6 py-20">
        <Eyebrow>How it works</Eyebrow>
        <SectionTitle>From weather feed to doorstep, autonomously</SectionTitle>
        <div className="mt-12 grid gap-px border border-line bg-line sm:grid-cols-2 lg:grid-cols-4">
          {STEPS.map((s) => (
            <div key={s.n} className="bg-ground p-6">
              <div className="font-display text-3xl text-accent">{s.n}</div>
              <h3 className="mt-3 text-lg font-semibold">{s.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted">{s.body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Agents ── */}
      <section id="agents" className="scroll-mt-8 border-y border-line bg-panel/60">
        <div className="mx-auto max-w-6xl px-6 py-20">
          <Eyebrow>Under the hood</Eyebrow>
          <SectionTitle>Three specialized agents, one silent pipeline</SectionTitle>
          <p className="mt-4 max-w-[62ch] text-muted">
            Built on the open-source Strands Agents SDK with Claude models on
            Amazon Bedrock, deployed as a background daemon on Amazon Bedrock
            AgentCore. Every agent returns validated, structured output — and
            every proposal is checked against the live community board before
            anything is dispatched.
          </p>
          <div className="mt-12 grid gap-4 lg:grid-cols-3">
            {AGENTS.map((a) => (
              <div key={a.name} className="border border-line bg-ground p-6">
                <p className="font-mono text-xs text-accent">{a.name}</p>
                <h3 className="mt-2 text-lg font-semibold">{a.role}</h3>
                <p className="mt-2 text-sm leading-relaxed text-muted">{a.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Principles ── */}
      <section id="principles" className="mx-auto max-w-6xl scroll-mt-8 px-6 py-20">
        <Eyebrow>Design principles</Eyebrow>
        <SectionTitle>Built for the worst day, not the demo day</SectionTitle>
        <div className="mt-12 grid gap-x-12 gap-y-10 sm:grid-cols-2">
          {PRINCIPLES.map((p) => (
            <div key={p.title} className="border-t-2 border-accent/70 pt-4">
              <h3 className="text-lg font-semibold">{p.title}</h3>
              <p className="mt-2 leading-relaxed text-muted">{p.body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="border-t border-line bg-panel/60">
        <div className="mx-auto flex max-w-6xl flex-col items-start gap-6 px-6 py-16 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="font-display text-2xl tracking-tight sm:text-3xl">
              See the situation board live.
            </h2>
            <p className="mt-2 max-w-[48ch] text-muted">
              Seed the Austin heatwave scenario, run a cycle, and approve a
              delivery yourself — no credentials required.
            </p>
          </div>
          <Link
            href="/board"
            className="shrink-0 border border-accent bg-accent px-6 py-3 font-mono text-sm font-semibold uppercase tracking-wider text-ground transition-colors hover:bg-accent/85 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
          >
            Launch App
          </Link>
        </div>
      </section>

      <SiteFooter />
    </div>
  );
}

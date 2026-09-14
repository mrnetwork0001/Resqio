import Link from "next/link";
import HeroAnimation from "@/components/HeroAnimation";
import Faq from "@/components/Faq";
import SiteFooter from "@/components/SiteFooter";

const GITHUB = "https://github.com/mrnetwork0001/Resqio";

function Eyebrow({ children }: { children: React.ReactNode }) {
  return (
    <p className="flex items-center gap-3 font-mono text-xs font-semibold uppercase tracking-[0.22em] text-accent">
      <span aria-hidden="true">✳</span>
      {children}
    </p>
  );
}

const PARTS = [
  {
    n: "01",
    title: "Grid & Weather Monitor",
    file: "strands_grid_monitor.py",
    body: "Polls NOAA/NWS alerts and county-level outage records around the clock, correlating hazards that share county FIPS codes. An extreme heat warning colliding with a 12,400-customer feeder outage is read as the compounding emergency it is - and scored 0–5.",
  },
  {
    n: "02",
    title: "Resource Matcher",
    file: "strands_resource_matcher.py",
    body: "Parses informal community SMS into structured offers and requests, then matches supply to need on urgency, vulnerability, and distance. Medical refrigeration, infants, and elderly residents outrank everything. Every proposal is re-validated against the live board.",
  },
  {
    n: "03",
    title: "Volunteer Router",
    file: "strands_volunteer_router.py",
    body: "Plans crisis-condition transit with per-hazard guidance - dark intersections during outages, heat exposure, flooded roads - and writes the single approval message a captain sees, always ending with two reply options.",
  },
  {
    n: "04",
    title: "WhatsApp Dispatch",
    file: "twilio_whatsapp_dispatcher.py",
    body: "The pipeline's only outward surface. One ping, two buttons - Accept dispatches the delivery, Pass puts both sides back on the board. Signature-validated inbound webhooks close the loop when the captain replies DELIVERED.",
  },
];

const STATS = [
  { n: "24/7", label: "autonomous watch on weather and grid feeds", accent: false },
  { n: "3", label: "Strands agents reasoning on Amazon Bedrock", accent: false },
  { n: "1", label: "tap on WhatsApp to dispatch help", accent: true },
  { n: "0", label: "messages sent when nothing needs a human", accent: false },
];

const FRAMES = [
  { t: 2.2, tag: "DETECT", caption: "Heat warning × feeder outage on overlapping counties - crisis level 5/5." },
  { t: 4.2, tag: "INGEST", caption: "Offers and requests arrive as plain SMS. No app, no account, no training." },
  { t: 8.8, tag: "APPROVE", caption: "One WhatsApp ping to a volunteer captain. Two buttons. A human decides." },
  { t: 11.8, tag: "DELIVER", caption: "Generator to 42 Maple St - 1.2 km, ~7 min - confirmed and closed out." },
];

const CYCLE = [
  { n: "01", word: "WATCH", body: "Feeds polled, hazards correlated, crisis scored. Feed failure means \"no change\", never \"all clear\"." },
  { n: "02", word: "LISTEN", body: "Community texts parsed into offers and urgent requests, on the board in seconds." },
  { n: "03", word: "MATCH", body: "Supply paired to need - urgency first, then vulnerability, then distance. Never double-booked." },
  { n: "04", word: "APPROVE", body: "Route planned, hazards flagged, one captain pinged. Silence otherwise." },
];

const SERVES = [
  { title: "Neighborhood blocks", body: "A block captain, a WhatsApp group, and whatever's in the garages - organized the moment the grid fails." },
  { title: "Food banks", body: "Perishables and cold-chain capacity matched to households that lose refrigeration in an outage." },
  { title: "Shelters", body: "Cooling, power, and transport needs surfaced and staffed without another spreadsheet." },
  { title: "Mutual-aid networks", body: "Volunteer capacity dispatched with routes and hazard guidance instead of group-chat chaos." },
];

const DEMO_FEATURES = [
  "The full loop, fully offline",
  "Simulated NOAA + EAGLE-I-schema feeds",
  "Console-rendered WhatsApp pings",
  "Deterministic agent fallbacks",
  "82-test suite, zero credentials",
];

const LIVE_FEATURES = [
  "Claude reasoning on Amazon Bedrock",
  "Live NOAA alert polling",
  "Real WhatsApp pings via Twilio",
  "AgentCore background daemon",
  "Signature-validated inbound webhooks",
];

export default function Landing() {
  return (
    <div className="min-h-screen overflow-x-clip">
      {/* ── Nav ── */}
      {/* Side space is 75% of what the max-w-7xl + px-6 layout gives at any
          width: 18px below 1280px, then 0.75 × ((viewport − 1280) / 2 + 24px). */}
      <nav
        className="sticky top-0 z-50 flex items-center gap-8 border-b border-line/60 bg-ground/90 py-5 backdrop-blur"
        style={{ paddingInline: "max(18px, calc(0.75 * ((100vw - 1280px) / 2 + 24px)))" }}
      >
        <span className="font-display text-2xl uppercase leading-none tracking-wide">
          Resqio<span className="text-accent">.</span>
        </span>
        <div className="ml-auto hidden items-center gap-7 font-mono text-xs uppercase tracking-wider text-muted md:flex">
          <a href="#system" className="transition-colors hover:text-ink">System</a>
          <a href="#scenario" className="transition-colors hover:text-ink">Scenario</a>
          <a href="#modes" className="transition-colors hover:text-ink">Run it</a>
          <a href="#faq" className="transition-colors hover:text-ink">FAQ</a>
        </div>
      </nav>

      {/* ── Hero ── */}
      <header className="mx-auto grid max-w-7xl items-center gap-12 px-6 pb-16 pt-12 lg:grid-cols-[1.05fr_1fr] lg:gap-16">
        <div>
          <Eyebrow>Autonomous disaster logistics - open source</Eyebrow>
          <h1 className="mt-6 font-display text-5xl uppercase leading-[0.95] tracking-wide sm:text-6xl xl:text-7xl">
            Built for neighbors,
            <br />
            <span className="text-outline">run by AI agents.</span>
          </h1>
          <p className="mt-7 max-w-[52ch] text-lg leading-relaxed text-muted">
            Resqio watches weather and grid feeds 24/7, matches spare
            generators, ice, and food to the most vulnerable requests texted in
            over plain SMS - and pings a volunteer captain on WhatsApp only
            when a delivery needs a human yes.
          </p>
          <div className="mt-9 flex flex-wrap items-center gap-4">
            <Link
              href="/board"
              className="bg-accent px-7 py-3.5 font-mono text-sm font-semibold uppercase tracking-wider text-ground transition-colors hover:bg-ink focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
            >
              Launch App
            </Link>
            <a
              href={GITHUB}
              className="border border-line px-7 py-3.5 font-mono text-sm font-semibold uppercase tracking-wider text-ink transition-colors hover:border-accent hover:text-accent focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent"
            >
              View source
            </a>
          </div>
          <p className="mt-7 font-mono text-[11px] uppercase tracking-[0.18em] text-muted/80">
            Apache 2.0 · Strands Agents SDK · Amazon Bedrock AgentCore
          </p>
        </div>

        <div className="border border-line bg-panel">
          <div className="flex items-center gap-3 border-b border-line px-4 py-2.5">
            <span className="h-2 w-2 bg-accent" aria-hidden="true" />
            <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted">
              resqio · live watch
            </span>
            <span className="ml-auto flex items-center gap-2 font-mono text-[10px] uppercase tracking-wider text-accent">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-accent" />
              Autonomous
            </span>
          </div>
          <HeroAnimation />
        </div>
      </header>

      {/* ── Watermark ── */}
      <div aria-hidden="true" className="select-none overflow-hidden">
        <div className="text-outline-faint whitespace-nowrap text-center font-display text-[21vw] uppercase leading-[0.8]">
          Resqio
        </div>
      </div>

      {/* ── 01–04 The system ── */}
      <section id="system" className="mx-auto max-w-7xl scroll-mt-8 px-6 py-24">
        <Eyebrow>The system</Eyebrow>
        <h2 className="mt-4 max-w-[16ch] font-display text-4xl uppercase leading-[0.95] tracking-wide sm:text-5xl">
          Four moving parts. <span className="text-outline">Zero busywork.</span>
        </h2>
        <div className="mt-14">
          {PARTS.map((p) => (
            <div
              key={p.n}
              className="grid gap-4 border-t border-line py-9 last:border-b sm:grid-cols-[72px_1fr] lg:grid-cols-[72px_1fr_1.2fr]"
            >
              <span className="font-display text-xl text-accent">{p.n}</span>
              <div>
                <h3 className="font-display text-2xl uppercase tracking-wide sm:text-3xl">{p.title}</h3>
                <p className="mt-2 font-mono text-xs text-muted">{p.file}</p>
              </div>
              <p className="max-w-[58ch] leading-relaxed text-muted lg:justify-self-end">{p.body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Principle + scenario quote ── */}
      <section className="border-y border-line bg-panel">
        <div className="mx-auto grid max-w-7xl gap-12 px-6 py-24 lg:grid-cols-2 lg:gap-20">
          <div>
            <Eyebrow>The principle</Eyebrow>
            <h2 className="mt-4 font-display text-4xl uppercase leading-[0.95] tracking-wide sm:text-5xl">
              Silent until a human <span className="text-outline-accent">must decide.</span>
            </h2>
            <p className="mt-7 max-w-[56ch] leading-relaxed text-muted">
              During a disaster, the last thing a community needs is another
              feed to monitor. Resqio produces no dashboards to babysit and no
              alerts to triage. It works in the background - and the only time
              a phone buzzes is when a physical delivery needs a one-tap
              approval from a volunteer captain. No crisis, no noise.
            </p>
            <p className="mt-5 max-w-[56ch] leading-relaxed text-muted">
              And because a disaster tool can&apos;t assume the cloud is healthy
              mid-disaster, every AI reasoning step degrades to deterministic
              logic if Amazon Bedrock is unreachable. The pipeline keeps
              flowing on the worst day, not just the demo day.
            </p>
          </div>
          <div className="flex flex-col justify-center gap-4">
            <figure className="border border-line bg-ground p-7">
              <figcaption className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted">
                Inbound SMS - demo scenario
              </figcaption>
              <blockquote className="mt-4 font-mono text-lg leading-relaxed text-ink">
                &ldquo;HELP: My father is 82, insulin needs refrigeration and
                our power is out at 42 Maple St. Urgent.&rdquo;
              </blockquote>
            </figure>
            <div className="bg-accent p-7 text-ground">
              <p className="font-mono text-[10px] uppercase tracking-[0.18em]">One cycle later</p>
              <p className="mt-3 font-display text-xl uppercase leading-snug tracking-wide">
                Matched to a 7.5 kW generator, 1.2 km away. One tap. Delivered.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ── Stats ── */}
      <section className="mx-auto max-w-7xl px-6 py-24">
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {STATS.map((s) => (
            <div
              key={s.label}
              className={`${s.accent ? "bg-accent text-ground" : "bg-paper text-ground"} p-7`}
            >
              <div className="font-display text-6xl leading-none">{s.n}</div>
              <p className="mt-4 font-mono text-xs uppercase leading-relaxed tracking-wider opacity-80">
                {s.label}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Scenario gallery ── */}
      <section id="scenario" className="border-y border-line bg-panel">
        <div className="mx-auto max-w-7xl scroll-mt-8 px-6 py-24">
          <Eyebrow>The loop, frame by frame</Eyebrow>
          <h2 className="mt-4 font-display text-4xl uppercase leading-[0.95] tracking-wide sm:text-5xl">
            Real crisis. <span className="text-outline">Real logistics.</span>
          </h2>
          <p className="mt-5 max-w-[62ch] leading-relaxed text-muted">
            Four moments from the Austin heatwave scenario - the same loop the
            live animation above plays end to end, and the same one you can
            drive yourself on the situation board.
          </p>
          <div className="mt-14 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {FRAMES.map((f) => (
              <figure key={f.tag} className="border border-line bg-ground">
                <HeroAnimation frozenAt={f.t} />
                <figcaption className="border-t border-line p-5">
                  <span className="font-display text-lg uppercase tracking-wide text-accent">{f.tag}</span>
                  <p className="mt-2 text-sm leading-relaxed text-muted">{f.caption}</p>
                </figcaption>
              </figure>
            ))}
          </div>
        </div>
      </section>

      {/* ── Modes ── */}
      <section id="modes" className="mx-auto max-w-7xl scroll-mt-8 px-6 py-24">
        <Eyebrow>Run it</Eyebrow>
        <h2 className="mt-4 font-display text-4xl uppercase leading-[0.95] tracking-wide sm:text-5xl">
          Two modes. <span className="text-outline">One pipeline.</span>
        </h2>
        <div className="mt-14 grid gap-4 lg:grid-cols-2">
          <div className="flex flex-col border border-line bg-panel p-8">
            <p className="font-mono text-xs uppercase tracking-[0.18em] text-muted">Demo mode</p>
            <div className="mt-4 flex items-baseline gap-3">
              <span className="font-display text-6xl leading-none">$0</span>
              <span className="font-mono text-xs uppercase tracking-wider text-muted">no credentials · any laptop</span>
            </div>
            <ul className="mt-8 flex flex-col gap-3.5">
              {DEMO_FEATURES.map((f) => (
                <li key={f} className="flex items-baseline gap-3 text-[15px] text-ink/90">
                  <span aria-hidden="true" className="font-mono text-accent">▪</span>
                  {f}
                </li>
              ))}
            </ul>
            <Link
              href="/board"
              className="mt-10 self-start border border-line px-6 py-3 font-mono text-xs font-semibold uppercase tracking-wider transition-colors hover:border-accent hover:text-accent focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent"
            >
              Launch demo board
            </Link>
          </div>
          <div className="flex flex-col bg-accent p-8 text-ground">
            <p className="font-mono text-xs uppercase tracking-[0.18em] opacity-70">Live mode</p>
            <div className="mt-4 flex items-baseline gap-3">
              <span className="font-display text-6xl leading-none">AWS</span>
              <span className="font-mono text-xs uppercase tracking-wider opacity-70">your account · your county</span>
            </div>
            <ul className="mt-8 flex flex-col gap-3.5">
              {LIVE_FEATURES.map((f) => (
                <li key={f} className="flex items-baseline gap-3 text-[15px] font-medium">
                  <span aria-hidden="true" className="font-mono">▪</span>
                  {f}
                </li>
              ))}
            </ul>
            <a
              href={`${GITHUB}#amazon-bedrock-agentcore-deployment`}
              className="mt-10 self-start bg-ground px-6 py-3 font-mono text-xs font-semibold uppercase tracking-wider text-ink transition-colors hover:bg-panel focus-visible:outline focus-visible:outline-2 focus-visible:outline-ground"
            >
              Deployment guide
            </a>
          </div>
        </div>
      </section>

      {/* ── Who it serves ── */}
      <section className="bg-accent text-ground">
        <div className="mx-auto max-w-7xl px-6 py-24">
          <p className="flex items-center gap-3 font-mono text-xs font-semibold uppercase tracking-[0.22em]">
            <span aria-hidden="true">✳</span> Who it serves
          </p>
          <h2 className="mt-4 max-w-[18ch] font-display text-4xl uppercase leading-[0.95] tracking-wide sm:text-5xl">
            Built for the people <span className="text-outline-paper">who show up.</span>
          </h2>
          <div className="mt-14 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            {SERVES.map((s) => (
              <div key={s.title} className="bg-ground p-7 text-ink">
                <h3 className="font-display text-xl uppercase tracking-wide">{s.title}</h3>
                <p className="mt-3 text-sm leading-relaxed text-muted">{s.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── The cycle ── */}
      <section className="mx-auto max-w-7xl px-6 py-24">
        <Eyebrow>One cycle</Eyebrow>
        <h2 className="mt-4 font-display text-4xl uppercase leading-[0.95] tracking-wide sm:text-5xl">
          What happens <span className="text-outline">every five minutes.</span>
        </h2>
        <div className="mt-14">
          {CYCLE.map((c) => (
            <div
              key={c.n}
              className="group grid items-baseline gap-4 border-t border-line py-8 last:border-b sm:grid-cols-[72px_1fr_1.1fr]"
            >
              <span className="font-mono text-sm text-accent">{c.n}</span>
              <h3 className="font-display text-5xl uppercase leading-none tracking-wide transition-colors group-hover:text-accent sm:text-6xl">
                {c.word}
              </h3>
              <p className="max-w-[52ch] leading-relaxed text-muted sm:justify-self-end">{c.body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── FAQ ── */}
      <section id="faq" className="border-t border-line bg-panel">
        <div className="mx-auto max-w-7xl scroll-mt-8 px-6 py-24">
          <Eyebrow>Questions</Eyebrow>
          <h2 className="mt-4 mb-12 font-display text-4xl uppercase leading-[0.95] tracking-wide sm:text-5xl">
            Asked before <span className="text-outline">the storm.</span>
          </h2>
          <Faq />
        </div>
      </section>

      {/* ── CTA band ── */}
      <section className="bg-accent text-ground">
        <div className="mx-auto flex max-w-7xl flex-col gap-10 px-6 py-24">
          <h2 className="max-w-[14ch] font-display text-5xl uppercase leading-[0.92] tracking-wide sm:text-7xl">
            The next storm isn&apos;t waiting.
          </h2>
          <div className="flex flex-wrap items-center gap-4">
            <Link
              href="/board"
              className="bg-ground px-8 py-4 font-mono text-sm font-semibold uppercase tracking-wider text-ink transition-colors hover:bg-panel focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ground"
            >
              Launch App
            </Link>
            <a
              href={GITHUB}
              className="border-2 border-ground px-8 py-4 font-mono text-sm font-semibold uppercase tracking-wider transition-colors hover:bg-ground hover:text-ink focus-visible:outline focus-visible:outline-2 focus-visible:outline-ground"
            >
              Fork it for your county
            </a>
          </div>
        </div>
      </section>

      <SiteFooter />
    </div>
  );
}

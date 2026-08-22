"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import {
  Assessment,
  CrisisEvent,
  Match,
  Offer,
  Ping,
  Request_,
  Status,
  fetchStatus,
  post,
} from "@/lib/api";

const SEVERITY_STYLE: Record<string, string> = {
  Extreme: "bg-danger/15 text-danger",
  Severe: "bg-accent/15 text-accent",
  Moderate: "bg-warn/15 text-warn",
  Minor: "bg-info/15 text-info",
  Unknown: "bg-line text-muted",
};

const MATCH_STYLE: Record<string, string> = {
  proposed: "bg-line text-muted",
  pending_approval: "bg-warn/15 text-warn",
  approved: "bg-info/15 text-info",
  delivered: "bg-ok/15 text-ok",
  declined: "bg-line text-muted",
  expired: "bg-line text-muted",
};

const ENTRY_STYLE: Record<string, string> = {
  open: "bg-ok/15 text-ok",
  matched: "bg-warn/15 text-warn",
  closed: "bg-line text-muted",
};

function Chip({ label, className }: { label: string; className: string }) {
  return (
    <span className={`rounded-full px-2.5 py-0.5 font-mono text-[11px] font-semibold uppercase tracking-wider ${className}`}>
      {label}
    </span>
  );
}

function Panel({ title, hint, children }: { title: string; hint?: string; children: React.ReactNode }) {
  return (
    <section className="flex min-w-0 flex-col gap-3 border border-line bg-panel p-4">
      <header className="flex items-baseline justify-between gap-3">
        <h2 className="font-mono text-xs font-semibold uppercase tracking-[0.14em] text-muted">{title}</h2>
        {hint ? <span className="font-mono text-[11px] text-muted/70">{hint}</span> : null}
      </header>
      {children}
    </section>
  );
}

function Empty({ children }: { children: React.ReactNode }) {
  return <p className="border border-dashed border-line px-3 py-6 text-center text-sm text-muted">{children}</p>;
}

function CrisisGauge({ assessment }: { assessment: Assessment | null }) {
  const level = assessment?.crisis_level ?? 0;
  const active = assessment?.is_crisis ?? false;
  return (
    <div className="flex items-center gap-3">
      <div className="flex gap-1" aria-label={`crisis level ${level} of 5`}>
        {[1, 2, 3, 4, 5].map((i) => (
          <span
            key={i}
            className={`h-5 w-2.5 ${i <= level ? (level >= 4 ? "bg-danger" : level === 3 ? "bg-accent" : "bg-warn") : "bg-line"}`}
          />
        ))}
      </div>
      <span className="font-display text-lg leading-none">
        {active ? `CRISIS ${level}/5` : "CALM"}
      </span>
    </div>
  );
}

export default function Board() {
  const [status, setStatus] = useState<Status | null>(null);
  const [offline, setOffline] = useState(false);
  const [busy, setBusy] = useState<string | null>(null);
  const [reply, setReply] = useState("");
  const [console_, setConsole] = useState<{ sent: string; reply: string }[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);

  const refresh = useCallback(async () => {
    try {
      setStatus(await fetchStatus());
      setOffline(false);
    } catch {
      setOffline(true);
    }
  }, []);

  useEffect(() => {
    refresh();
    const timer = setInterval(refresh, 3000);
    return () => clearInterval(timer);
  }, [refresh]);

  const act = async (label: string, path: string) => {
    setBusy(label);
    try {
      await post(path);
      await refresh();
    } catch {
      setOffline(true);
    } finally {
      setBusy(null);
    }
  };

  const sendReply = async (event: React.FormEvent) => {
    event.preventDefault();
    const body = reply.trim();
    if (!body) return;
    setReply("");
    try {
      const result = await post("/demo/inbound", { body, name: "Captain (dashboard)" });
      setConsole((log) => [{ sent: body, reply: result.reply }, ...log].slice(0, 6));
      await refresh();
    } catch {
      setOffline(true);
    }
    inputRef.current?.focus();
  };

  const offers = status?.offers ?? [];
  const requests = [...(status?.requests ?? [])].sort((a, b) => b.urgency - a.urgency);
  const matches = [...(status?.matches ?? [])].reverse();
  const pings = [...(status?.pings ?? [])].reverse();
  const events = status?.last_events ?? [];
  const boardEmpty = offers.length === 0 && requests.length === 0;

  return (
    <div className="mx-auto flex min-h-screen max-w-[1400px] flex-col gap-4 p-4 lg:p-6">
      <header className="flex flex-wrap items-center gap-x-6 gap-y-3 border border-line bg-panel px-5 py-4">
        <h1 className="font-display text-3xl leading-none tracking-tight">
          <Link
            href="/"
            aria-label="Back to the Resqio landing page"
            className="transition-colors hover:text-accent focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent"
          >
            RESQIO<span className="text-accent">.</span>
          </Link>
        </h1>
        <span className="hidden font-mono text-[11px] uppercase tracking-[0.14em] text-muted sm:block">
          Community situation board
        </span>
        <CrisisGauge assessment={status?.assessment ?? null} />
        <div className="ml-auto flex flex-wrap items-center gap-2">
          <span className="mr-2 font-mono text-[11px] text-muted">
            {offline
              ? "runtime offline — start `python -m src.integrations.webhook_server`"
              : status?.last_cycle_at
                ? `last cycle ${new Date(status.last_cycle_at).toLocaleTimeString()}`
                : "no cycle yet"}
          </span>
          {(
            [
              ["Seed texts", "/demo/seed"],
              ["Run cycle", "/cycle"],
              ["Reset", "/demo/reset"],
            ] as const
          ).map(([label, path]) => (
            <button
              key={path}
              onClick={() => act(label, path)}
              disabled={busy !== null || offline}
              className="border border-line bg-raised px-3 py-1.5 font-mono text-xs font-semibold uppercase tracking-wider text-ink transition-colors hover:border-accent hover:text-accent focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent disabled:opacity-40"
            >
              {busy === label ? "…" : label}
            </button>
          ))}
        </div>
      </header>

      {status?.assessment ? (
        <p className="border border-line bg-panel px-5 py-3 text-sm text-ink/90">
          <span className="font-semibold text-accent">SITREP&ensp;</span>
          {status.assessment.summary}
        </p>
      ) : null}

      <main className="grid flex-1 gap-4 lg:grid-cols-3">
        <Panel title="Situation" hint={`${events.length} active events`}>
          {events.length === 0 ? (
            <Empty>No active weather alerts or outages.</Empty>
          ) : (
            <ul className="flex flex-col gap-2">
              {events.map((e: CrisisEvent) => (
                <li key={e.id} className="border border-line bg-raised/60 p-3">
                  <div className="flex items-start justify-between gap-2">
                    <span className="text-sm font-semibold">{e.event}</span>
                    <Chip label={e.severity} className={SEVERITY_STYLE[e.severity] ?? SEVERITY_STYLE.Unknown} />
                  </div>
                  <p className="mt-1 text-[13px] leading-snug text-muted">{e.headline || e.area_desc}</p>
                  <div className="mt-1.5 flex gap-3 font-mono text-[11px] text-muted/80">
                    <span>{e.source === "noaa" ? "NWS" : "GRID"}</span>
                    {e.customers_affected != null && (
                      <span className="tabular-nums">{e.customers_affected.toLocaleString()} customers out</span>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Panel>

        <Panel title="Community board" hint={`${offers.length} offers · ${requests.length} requests`}>
          {boardEmpty ? (
            <Empty>
              Board is empty. Press <span className="font-mono text-accent">SEED TEXTS</span> to simulate
              inbound community SMS, then <span className="font-mono text-accent">RUN CYCLE</span>.
            </Empty>
          ) : (
            <div className="flex flex-col gap-4">
              <div>
                <h3 className="mb-2 font-mono text-[11px] uppercase tracking-wider text-ok">Offers</h3>
                <ul className="flex flex-col gap-2">
                  {offers.map((o: Offer) => (
                    <li key={o.id} className="border border-line bg-raised/60 p-3">
                      <div className="flex items-start justify-between gap-2">
                        <span className="text-sm font-semibold capitalize">{o.resource_type}</span>
                        <Chip label={o.status} className={ENTRY_STYLE[o.status] ?? ""} />
                      </div>
                      <p className="mt-1 text-[13px] leading-snug text-muted">{o.description}</p>
                      <div className="mt-1.5 font-mono text-[11px] text-muted/80">{o.contact_name}{o.address ? ` · ${o.address}` : ""}</div>
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <h3 className="mb-2 font-mono text-[11px] uppercase tracking-wider text-warn">Requests</h3>
                <ul className="flex flex-col gap-2">
                  {requests.map((r: Request_) => (
                    <li key={r.id} className="border border-line bg-raised/60 p-3">
                      <div className="flex items-start justify-between gap-2">
                        <span className="text-sm font-semibold capitalize">{r.resource_type}</span>
                        <Chip label={r.status} className={ENTRY_STYLE[r.status] ?? ""} />
                      </div>
                      <p className="mt-1 text-[13px] leading-snug text-muted">{r.description}</p>
                      <div className="mt-1.5 flex flex-wrap gap-x-3 gap-y-1 font-mono text-[11px] text-muted/80">
                        <span className={r.urgency >= 5 ? "text-danger" : r.urgency >= 4 ? "text-warn" : ""}>
                          urgency {r.urgency}/5
                        </span>
                        {r.vulnerability !== "none" && <span className="text-accent">{r.vulnerability.replace(/_/g, " ")}</span>}
                        <span>{r.contact_name}{r.address ? ` · ${r.address}` : ""}</span>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </Panel>

        <Panel title="Dispatch" hint={`${matches.length} matches · ${pings.length} pings`}>
          <div className="flex flex-col gap-4">
            {matches.length === 0 ? (
              <Empty>No matches yet — run a cycle during a crisis.</Empty>
            ) : (
              <ul className="flex flex-col gap-2">
                {matches.map((m: Match) => (
                  <li key={m.id} className="border border-line bg-raised/60 p-3">
                    <div className="flex items-start justify-between gap-2">
                      <span className="font-mono text-xs text-muted">{m.id}</span>
                      <Chip label={m.status.replace(/_/g, " ")} className={MATCH_STYLE[m.status] ?? ""} />
                    </div>
                    <p className="mt-1 text-[13px] leading-snug">{m.rationale}</p>
                    {m.route && (
                      <div className="mt-1.5 font-mono text-[11px] tabular-nums text-muted/80">
                        {m.route.distance_km} km · ~{Math.round(m.route.est_minutes)} min
                        {m.route.hazards.length > 0 && ` · hazards: ${m.route.hazards.length}`}
                      </div>
                    )}
                  </li>
                ))}
              </ul>
            )}

            <div>
              <h3 className="mb-2 font-mono text-[11px] uppercase tracking-wider text-muted">Captain console</h3>
              <form onSubmit={sendReply} className="flex gap-2">
                <input
                  ref={inputRef}
                  value={reply}
                  onChange={(e) => setReply(e.target.value)}
                  placeholder="ACCEPT mat_… / PASS mat_… / DELIVERED mat_…"
                  className="min-w-0 flex-1 border border-line bg-ground px-3 py-2 font-mono text-xs text-ink placeholder:text-muted/50 focus:border-accent focus:outline-none"
                />
                <button
                  type="submit"
                  disabled={offline || !reply.trim()}
                  className="border border-line bg-raised px-3 py-2 font-mono text-xs font-semibold uppercase tracking-wider transition-colors hover:border-accent hover:text-accent focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent disabled:opacity-40"
                >
                  Send
                </button>
              </form>
              {console_.length > 0 && (
                <ul className="mt-2 flex flex-col gap-1.5">
                  {console_.map((entry, i) => (
                    <li key={i} className="border-l-2 border-accent/60 pl-2 text-[12px] leading-snug">
                      <span className="font-mono text-muted">▸ {entry.sent}</span>
                      <br />
                      <span className="text-ink/90">{entry.reply}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            {pings.length > 0 && (
              <div>
                <h3 className="mb-2 font-mono text-[11px] uppercase tracking-wider text-muted">Ping log</h3>
                <ul className="flex flex-col gap-2">
                  {pings.slice(0, 4).map((p: Ping, i) => (
                    <li key={`${p.match_id}-${i}`} className="border border-line bg-ground p-3 text-[12px] leading-snug text-ink/90">
                      <div className="mb-1 flex justify-between font-mono text-[11px] text-muted">
                        <span>→ {p.captain_phone}</span>
                        <span>{p.channel}</span>
                      </div>
                      {p.message_body}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </Panel>
      </main>

      <footer className="flex flex-wrap gap-x-6 gap-y-1 border-t border-line pt-3 font-mono text-[11px] text-muted">
        <span>Resqio · silent background agent — this board is read-only observability plus demo controls</span>
        <span>{status?.demo_mode ? "DEMO MODE (simulated feeds, console pings)" : "LIVE MODE"}</span>
      </footer>
    </div>
  );
}

import Link from "next/link";

const GITHUB = "https://github.com/mrnetwork0001/Resqio";

const COLUMNS: { title: string; links: { label: string; href: string; external?: boolean }[] }[] = [
  {
    title: "Product",
    links: [
      { label: "Situation Board", href: "/board" },
      { label: "The System", href: "/#system" },
      { label: "The Scenario", href: "/#scenario" },
      { label: "FAQ", href: "/#faq" },
    ],
  },
  {
    title: "Platform",
    links: [
      { label: "Strands Agents SDK", href: "https://strandsagents.com", external: true },
      { label: "Amazon Bedrock AgentCore", href: "https://aws.amazon.com/bedrock/agentcore/", external: true },
      { label: "Twilio WhatsApp API", href: "https://www.twilio.com/en-us/messaging/channels/whatsapp", external: true },
      { label: "NOAA Weather API", href: "https://www.weather.gov/documentation/services-web-api", external: true },
    ],
  },
  {
    title: "Resources",
    links: [
      { label: "GitHub", href: GITHUB, external: true },
      { label: "Docs", href: `${GITHUB}#readme`, external: true },
      { label: "Architecture Diagram", href: `${GITHUB}/blob/main/architecture_diagram.png`, external: true },
      { label: "Apache 2.0 License", href: `${GITHUB}/blob/main/LICENSE`, external: true },
    ],
  },
];

function GitHubIcon() {
  return (
    <svg viewBox="0 0 16 16" width="18" height="18" fill="currentColor" aria-hidden="true">
      <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27s1.36.09 2 .27c1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8Z" />
    </svg>
  );
}

export default function SiteFooter() {
  return (
    <footer
      className="border-t border-line bg-ground"
      style={{
        backgroundImage:
          "linear-gradient(rgba(241,241,236,0.025) 1px, transparent 1px), linear-gradient(90deg, rgba(241,241,236,0.025) 1px, transparent 1px)",
        backgroundSize: "68px 68px",
      }}
    >
      <div className="mx-auto grid max-w-6xl gap-x-12 gap-y-12 px-6 py-16 lg:grid-cols-[1.5fr_1fr_1fr_1fr]">
        {/* ── Brand block ── */}
        <div>
          <div className="flex items-center gap-4">
            <span
              aria-hidden="true"
              className="relative flex h-12 w-12 items-center justify-center rounded-full border border-muted/40 font-display text-xl uppercase"
            >
              R
              <span className="absolute bottom-0.5 right-0.5 h-2 w-2 rounded-full bg-accent" />
            </span>
            <span className="h-10 w-px bg-line" aria-hidden="true" />
            <span>
              <span className="block font-display text-lg uppercase leading-tight tracking-[0.08em]">
                Resqio
              </span>
              <span className="block font-mono text-[9px] uppercase tracking-[0.32em] text-muted">
                Crisis Logistics
              </span>
            </span>
          </div>
          <p className="mt-6 max-w-[46ch] text-[15px] leading-relaxed text-muted">
            An autonomous disaster-logistics agent for neighborhoods, food
            banks, and volunteer groups. Weather and grid feeds watched 24/7,
            community SMS matched to urgent need - surfaced to a human only
            when a delivery needs a one-tap approval.
          </p>
          <div className="mt-6 flex gap-4">
            <a
              href={GITHUB}
              aria-label="Resqio on GitHub"
              className="text-muted transition-colors hover:text-ink focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent"
            >
              <GitHubIcon />
            </a>
          </div>
        </div>

        {/* ── Link columns ── */}
        {COLUMNS.map((col) => (
          <nav key={col.title} aria-label={col.title}>
            <h4 className="font-mono text-xs font-semibold uppercase tracking-[0.22em] text-accent">
              {col.title}
            </h4>
            <ul className="mt-4 flex flex-col gap-2">
              {col.links.map((link) => (
                <li key={link.label}>
                  {link.external ? (
                    <a
                      href={link.href}
                      className="font-mono text-sm text-ink/80 transition-colors hover:text-accent focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent"
                    >
                      {link.label}
                    </a>
                  ) : (
                    <Link
                      href={link.href}
                      className="font-mono text-sm text-ink/80 transition-colors hover:text-accent focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent"
                    >
                      {link.label}
                    </Link>
                  )}
                </li>
              ))}
            </ul>
          </nav>
        ))}
      </div>
    </footer>
  );
}

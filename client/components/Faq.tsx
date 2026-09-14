"use client";

const ITEMS: { q: string; a: string }[] = [
  {
    q: "Does it work without AWS credentials?",
    a: "Yes. Every agent has a deterministic degraded-mode fallback, so the full loop - detection, matching, routing, approval - runs offline with simulated feeds and console pings. That's how the demo and the 82-test suite run. Add AWS credentials and the same pipeline switches to live Claude reasoning on Amazon Bedrock.",
  },
  {
    q: "What happens if Bedrock is unreachable mid-disaster?",
    a: "The pipeline keeps flowing. A disaster tool can't assume the cloud is healthy during a disaster, so LLM failures drop each agent to pure logic: severity thresholds for crisis detection, a compatibility matrix plus haversine distance for matching, a deterministic route planner for dispatch. Slower thinking, same protocol.",
  },
  {
    q: "How do neighbors participate?",
    a: "Plain SMS. \"OFFER: generator available in Sector 4\" or \"HELP: insulin needs refrigeration at 42 Maple St.\" No app to install, no account to create, nothing to learn during a crisis. Location can come from WhatsApp location sharing or a street address in the text.",
  },
  {
    q: "Can the agent dispatch a volunteer on its own?",
    a: "Never. Every physical action passes through a one-tap human approval on WhatsApp, and the match lifecycle is a guarded state machine - a second captain's stale PASS can't reopen a delivery someone already accepted, and unanswered pings expire and free both sides for re-matching.",
  },
  {
    q: "Where does the outage data come from?",
    a: "Weather alerts are live from NOAA's api.weather.gov. For power outages there is no free real-time national feed (EAGLE-I is restricted to government accounts; poweroutage.us is a paid API), so the grid source is a pluggable protocol shipping realistic EAGLE-I-schema county records - any utility API can implement the same two methods.",
  },
  {
    q: "Is it really open source?",
    a: "Apache 2.0, the whole thing - the three Strands agents, the AgentCore runtime, the Twilio integration, the situation board, the tests, and the architecture docs. Fork it for your county.",
  },
];

export default function Faq() {
  return (
    <div className="border-t border-line">
      {ITEMS.map((item) => (
        <details key={item.q} className="group border-b border-line">
          <summary className="flex cursor-pointer list-none items-baseline gap-6 py-6 pr-2 [&::-webkit-details-marker]:hidden">
            <span
              aria-hidden="true"
              className="font-display text-xl text-accent transition-transform duration-200 group-open:rotate-45"
            >
              +
            </span>
            <span className="flex-1 font-display text-xl uppercase tracking-wide sm:text-2xl">
              {item.q}
            </span>
          </summary>
          <p className="max-w-[68ch] pb-8 pl-12 leading-relaxed text-muted">{item.a}</p>
        </details>
      ))}
    </div>
  );
}

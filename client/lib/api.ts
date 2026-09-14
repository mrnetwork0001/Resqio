// Client for the Resqio runtime's dashboard API (webhook server, :5001).

// Same-origin by default: next.config.mjs proxies API routes to the runtime.
// Set NEXT_PUBLIC_RESQIO_API to call a runtime directly instead.
export const API_BASE = process.env.NEXT_PUBLIC_RESQIO_API ?? "";

export interface Assessment {
  is_crisis: boolean;
  crisis_level: number;
  active_hazards: string[];
  affected_areas: string[];
  summary: string;
}

export interface CrisisEvent {
  id: string;
  source: "noaa" | "grid";
  event: string;
  severity: "Extreme" | "Severe" | "Moderate" | "Minor" | "Unknown";
  headline: string;
  area_desc: string;
  customers_affected: number | null;
}

export interface GeoPoint {
  lat: number;
  lon: number;
}

export interface Zone {
  key: string;
  name: string;
  noaa_area: string;
  fips_codes: string[];
  center: GeoPoint | null;
  radius_km: number;
}

export interface Offer {
  id: string;
  contact_name: string;
  resource_type: string;
  description: string;
  address: string;
  zone: string;
  location: GeoPoint | null;
  status: "open" | "matched" | "closed";
  created_at: string;
}

export interface Request_ {
  id: string;
  contact_name: string;
  resource_type: string;
  description: string;
  urgency: number;
  vulnerability: string;
  address: string;
  zone: string;
  location: GeoPoint | null;
  status: "open" | "matched" | "closed";
  created_at: string;
}

export interface RouteInfo {
  distance_km: number;
  est_minutes: number;
  hazards: string[];
  instructions: string;
}

export interface Match {
  id: string;
  offer_id: string;
  request_id: string;
  score: number;
  rationale: string;
  distance_km: number | null;
  status: string;
  route: RouteInfo | null;
  created_at: string;
}

export interface Ping {
  match_id: string;
  captain_phone: string;
  message_body: string;
  channel: string;
  sent_at: string;
}

export interface Status {
  demo_mode: boolean;
  zones: Zone[];
  assessment: Assessment | null;
  last_cycle_at: string | null;
  offers: Offer[];
  requests: Request_[];
  matches: Match[];
  pings: Ping[];
  last_events: CrisisEvent[];
}

export async function fetchStatus(): Promise<Status> {
  const res = await fetch(`${API_BASE}/status`, { cache: "no-store" });
  if (!res.ok) throw new Error(`status ${res.status}`);
  return res.json();
}

export async function post(path: string, body?: unknown): Promise<any> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error(`${path} → ${res.status}`);
  return res.json();
}

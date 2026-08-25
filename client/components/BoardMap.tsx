"use client";

// Community ops map: offers, requests, active match lines, and zone
// circles on a dark basemap. CircleMarkers only — no icon assets to
// break under bundling. Loaded with ssr:false (Leaflet needs window).

import { useEffect } from "react";
import { CircleMarker, MapContainer, Polyline, TileLayer, Tooltip, Circle, useMap } from "react-leaflet";
import { latLngBounds } from "leaflet";
import "leaflet/dist/leaflet.css";
import type { GeoPoint, Match, Offer, Request_, Zone } from "@/lib/api";

const COLORS = {
  offer: "#52c776",
  urgent: "#e5484d",
  high: "#dcae3c",
  normal: "#58a6ff",
  match: "#d7ff00",
  closed: "#8b8b84",
  zone: "#8b8b84",
};

function requestColor(r: Request_): string {
  if (r.status === "closed") return COLORS.closed;
  return r.urgency >= 5 ? COLORS.urgent : r.urgency >= 4 ? COLORS.high : COLORS.normal;
}

// MapContainer applies center/zoom only at mount; this child refits the
// view whenever the located data set actually changes.
function FitToData({ points }: { points: [number, number][] }) {
  const map = useMap();
  const signature = points.map((p) => p.join(",")).join(";");
  useEffect(() => {
    if (points.length > 0) {
      map.fitBounds(latLngBounds(points), { padding: [36, 36], maxZoom: 14 });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [signature, map]);
  return null;
}

export default function BoardMap({
  offers,
  requests,
  matches,
  zones,
}: {
  offers: Offer[];
  requests: Request_[];
  matches: Match[];
  zones: Zone[];
}) {
  const located = [...offers, ...requests].filter(
    (e): e is (Offer | Request_) & { location: GeoPoint } => e.location != null
  );
  const points = located.map((e) => [e.location.lat, e.location.lon] as [number, number]);
  const center: [number, number] = points.length
    ? [
        points.reduce((s, p) => s + p[0], 0) / points.length,
        points.reduce((s, p) => s + p[1], 0) / points.length,
      ]
    : [30.2672, -97.7431]; // Austin, TX

  const byId = new Map<string, Offer | Request_>();
  offers.forEach((o) => byId.set(o.id, o));
  requests.forEach((r) => byId.set(r.id, r));
  const activeLines = matches
    .filter((m) => ["pending_approval", "approved", "delivered"].includes(m.status))
    .map((m) => {
      const offer = byId.get(m.offer_id);
      const request = byId.get(m.request_id);
      if (!offer?.location || !request?.location) return null;
      return {
        id: m.id,
        status: m.status,
        points: [
          [offer.location.lat, offer.location.lon],
          [request.location.lat, request.location.lon],
        ] as [number, number][],
      };
    })
    .filter(Boolean) as { id: string; status: string; points: [number, number][] }[];

  return (
    <MapContainer
      center={center}
      zoom={13}
      scrollWheelZoom={false}
      style={{ height: "100%", width: "100%", background: "#0a0a0a" }}
      attributionControl={true}
    >
      <TileLayer
        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>'
      />
      <FitToData points={points} />

      {zones
        .filter((z) => z.center)
        .map((z) => (
          <Circle
            key={z.key}
            center={[z.center!.lat, z.center!.lon]}
            radius={z.radius_km * 1000}
            pathOptions={{ color: COLORS.zone, weight: 1, dashArray: "6 6", fillOpacity: 0.03 }}
          >
            <Tooltip direction="top">{z.name || z.key}</Tooltip>
          </Circle>
        ))}

      {activeLines.map((line) => (
        <Polyline
          key={line.id}
          positions={line.points}
          pathOptions={{
            color: line.status === "delivered" ? COLORS.offer : COLORS.match,
            weight: 2.5,
            dashArray: line.status === "pending_approval" ? "8 6" : undefined,
            opacity: 0.9,
          }}
        />
      ))}

      {offers
        .filter((o) => o.location)
        .map((o) => (
          <CircleMarker
            key={o.id}
            center={[o.location!.lat, o.location!.lon]}
            radius={8}
            pathOptions={{
              color: o.status === "closed" ? COLORS.closed : COLORS.offer,
              fillColor: o.status === "closed" ? COLORS.closed : COLORS.offer,
              fillOpacity: 0.85,
              weight: 2,
            }}
          >
            <Tooltip direction="top">
              <b>OFFER · {o.resource_type}</b>
              <br />
              {o.description.slice(0, 70)}
              <br />
              {o.contact_name} · {o.status}
            </Tooltip>
          </CircleMarker>
        ))}

      {requests
        .filter((r) => r.location)
        .map((r) => (
          <CircleMarker
            key={r.id}
            center={[r.location!.lat, r.location!.lon]}
            radius={8}
            pathOptions={{
              color: requestColor(r),
              fillColor: requestColor(r),
              fillOpacity: 0.85,
              weight: 2,
            }}
          >
            <Tooltip direction="top">
              <b>REQUEST · {r.resource_type} · urgency {r.urgency}/5</b>
              <br />
              {r.description.slice(0, 70)}
              <br />
              {r.contact_name} · {r.status}
            </Tooltip>
          </CircleMarker>
        ))}
    </MapContainer>
  );
}

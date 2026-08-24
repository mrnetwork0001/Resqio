"use client";

// Always-on hero motion: Resqio's actual loop played on a stylized city
// grid — alert → outage → community texts → match → approval ping →
// delivery — looping every 14 s. Pure canvas, no video asset; honors
// prefers-reduced-motion by rendering one representative still frame.

import { useEffect, useRef } from "react";

const W = 560;
const H = 470;
const LOOP = 14; // seconds

const C = {
  ground: "#0a0a0a",
  street: "#1d1d19",
  block: "#131311",
  blockLit: "#1a1a16",
  ink: "#f1f1ec",
  muted: "#8b8b84",
  accent: "#d7ff00",
  ok: "#52c776",
  warn: "#dcae3c",
  danger: "#e5484d",
  card: "#181815",
};

const OFFER = { x: 430, y: 132 };
const REQ1 = { x: 172, y: 328 };
const REQ2 = { x: 372, y: 396 };
const OUTAGE = { x: 190, y: 250 };

// phase progress: 0→1 across [start, start+dur], clamped
const at = (t: number, start: number, dur: number) =>
  Math.min(1, Math.max(0, (t - start) / dur));
const easeOut = (p: number) => 1 - Math.pow(1 - p, 3);

export default function HeroAnimation({ frozenAt }: { frozenAt?: number }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = W * dpr;
    canvas.height = H * dpr;
    ctx.scale(dpr, dpr);

    const styles = getComputedStyle(document.documentElement);
    const monoVar = styles.getPropertyValue("--font-mono").trim() || "monospace";
    const mono = (size: number, weight = 600) => `${weight} ${size}px ${monoVar}, monospace`;

    // frozenAt prop (still-frame cards) or ?t=<seconds> (screenshots) freezes
    // the loop; reduced motion pins a representative mid-loop frame.
    const frozenParam = new URLSearchParams(window.location.search).get("t");
    const frozen =
      frozenAt !== undefined
        ? frozenAt % LOOP
        : frozenParam !== null
          ? Number(frozenParam) % LOOP
          : null;
    const reduced =
      window.matchMedia("(prefers-reduced-motion: reduce)").matches || frozen !== null;
    let raf = 0;
    const started = performance.now();

    const chip = (x: number, y: number, text: string, fg: string, bg: string, size = 10) => {
      ctx.font = mono(size);
      const w = ctx.measureText(text).width + 14;
      ctx.fillStyle = bg;
      ctx.beginPath();
      ctx.roundRect(x, y, w, size + 10, 3);
      ctx.fill();
      ctx.fillStyle = fg;
      ctx.fillText(text, x + 7, y + size + 3);
      return w;
    };

    const dot = (x: number, y: number, r: number, color: string, pop: number) => {
      if (pop <= 0) return;
      const scale = easeOut(pop);
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.arc(x, y, r * scale, 0, Math.PI * 2);
      ctx.fill();
    };

    const pulse = (x: number, y: number, t: number, color: string, on: number) => {
      if (on <= 0) return;
      const p = (t * 0.9) % 1;
      ctx.strokeStyle = color;
      ctx.globalAlpha = (1 - p) * 0.55 * on;
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.arc(x, y, 8 + p * 22, 0, Math.PI * 2);
      ctx.stroke();
      ctx.globalAlpha = 1;
    };

    const draw = (now: number) => {
      const t = reduced ? (frozen ?? 7) : ((now - started) / 1000) % LOOP;
      // Scenario overlays fade out during the last 1.5 s of the loop.
      const fade = t > LOOP - 1.5 ? 1 - at(t, LOOP - 1.5, 1.5) : 1;

      // ── ground + street grid ──
      ctx.fillStyle = C.ground;
      ctx.fillRect(0, 0, W, H);
      ctx.strokeStyle = C.street;
      ctx.lineWidth = 1;
      for (let x = 20; x < W; x += 54) {
        ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke();
      }
      for (let y = 20; y < H; y += 54) {
        ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke();
      }
      // city blocks; blocks near the outage flicker once the event begins
      const outageOn = at(t, 1.5, 0.8) * fade;
      for (let x = 20; x < W - 54; x += 54) {
        for (let y = 20; y < H - 54; y += 54) {
          const cx = x + 27, cy = y + 27;
          const dist = Math.hypot(cx - OUTAGE.x, cy - OUTAGE.y);
          const inZone = dist < 110;
          let fill = C.blockLit;
          if (inZone && outageOn > 0) {
            const flicker = Math.sin(t * 7 + x * 13.7 + y * 7.3) > 0.55 ? 0.5 : 1;
            fill = flicker * (1 - outageOn) > 0.4 ? C.blockLit : C.block;
          }
          ctx.fillStyle = fill;
          ctx.fillRect(x + 5, y + 5, 44, 44);
        }
      }

      // ── outage zone glow ──
      if (outageOn > 0) {
        const g = ctx.createRadialGradient(OUTAGE.x, OUTAGE.y, 10, OUTAGE.x, OUTAGE.y, 120);
        const breathe = 0.16 + 0.06 * Math.sin(t * 2.2);
        g.addColorStop(0, `rgba(229, 72, 77, ${breathe * outageOn})`);
        g.addColorStop(1, "rgba(229, 72, 77, 0)");
        ctx.fillStyle = g;
        ctx.fillRect(0, 0, W, H);
      }

      // ── monitoring sweep (always on — the agent never sleeps) ──
      const sweep = (t * 0.55) % (Math.PI * 2);
      ctx.save();
      ctx.translate(W - 64, 64);
      ctx.strokeStyle = "rgba(143, 160, 173, 0.35)";
      ctx.beginPath(); ctx.arc(0, 0, 26, 0, Math.PI * 2); ctx.stroke();
      ctx.rotate(sweep);
      const lg = ctx.createLinearGradient(0, 0, 26, 0);
      lg.addColorStop(0, "rgba(82, 199, 118, 0.9)");
      lg.addColorStop(1, "rgba(82, 199, 118, 0)");
      ctx.strokeStyle = lg;
      ctx.lineWidth = 2;
      ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(26, 0); ctx.stroke();
      ctx.restore();
      ctx.font = mono(9);
      ctx.fillStyle = C.muted;
      ctx.textAlign = "center";
      ctx.fillText("24/7 WATCH", W - 64, 104);
      ctx.textAlign = "left";

      // ── alert chip ──
      const alertIn = easeOut(at(t, 1.5, 0.6)) * fade;
      if (alertIn > 0) {
        ctx.globalAlpha = alertIn;
        const y = 16 - (1 - alertIn) * 12;
        const w1 = chip(16, y, "EXCESSIVE HEAT WARNING", C.ink, C.card, 10);
        chip(16 + w1 + 6, y, "EXTREME", "#ffd9db", "rgba(229,72,77,0.35)", 10);
        chip(16, y + 26, "FEEDER OUTAGE — 12,400 OUT", "#ffe9c9", "rgba(220,174,60,0.22)", 10);
        ctx.globalAlpha = 1;
      }

      // ── community dots ──
      const offerPop = at(t, 2.6, 0.4) * fade;
      const req1Pop = at(t, 3.1, 0.4) * fade;
      const req2Pop = at(t, 3.6, 0.4) * fade;
      pulse(REQ1.x, REQ1.y, t, C.danger, req1Pop);
      pulse(OFFER.x, OFFER.y, t, C.ok, offerPop * 0.7);
      dot(OFFER.x, OFFER.y, 7, C.ok, offerPop);
      dot(REQ1.x, REQ1.y, 7, C.danger, req1Pop);
      dot(REQ2.x, REQ2.y, 6, C.warn, req2Pop);
      if (offerPop > 0.7) {
        ctx.globalAlpha = fade;
        chip(OFFER.x - 118, OFFER.y - 34, "GENERATOR · 7.5 kW", "#d9f2e1", "rgba(82,199,118,0.18)");
        ctx.globalAlpha = 1;
      }
      if (req1Pop > 0.7) {
        ctx.globalAlpha = fade;
        chip(REQ1.x - 24, REQ1.y + 16, "INSULIN · URGENCY 5/5", "#ffd9db", "rgba(229,72,77,0.2)");
        ctx.globalAlpha = 1;
      }
      if (req2Pop > 0.7) {
        ctx.globalAlpha = fade;
        chip(REQ2.x - 20, REQ2.y + 14, "FAMILY + INFANT", "#ffe9c9", "rgba(220,174,60,0.16)");
        ctx.globalAlpha = 1;
      }

      // ── match line ──
      const lineP = easeOut(at(t, 4.6, 1.4)) * fade;
      if (lineP > 0) {
        ctx.strokeStyle = C.accent;
        ctx.lineWidth = 2;
        ctx.setLineDash([7, 6]);
        ctx.lineDashOffset = -t * 26;
        ctx.beginPath();
        ctx.moveTo(OFFER.x, OFFER.y);
        ctx.lineTo(
          OFFER.x + (REQ1.x - OFFER.x) * lineP,
          OFFER.y + (REQ1.y - OFFER.y) * lineP
        );
        ctx.stroke();
        ctx.setLineDash([]);
      }
      if (at(t, 6.1, 0.4) > 0 && fade > 0) {
        ctx.globalAlpha = at(t, 6.1, 0.4) * fade;
        chip((OFFER.x + REQ1.x) / 2 - 52, (OFFER.y + REQ1.y) / 2 - 30, "MATCH 0.9 · 1.2 KM", "#0a0a0a", "rgba(215,255,0,0.92)");
        ctx.globalAlpha = 1;
      }

      // ── approval ping card ──
      const cardIn = easeOut(at(t, 6.6, 0.6)) * fade;
      const accepted = at(t, 8.6, 0.3);
      if (cardIn > 0) {
        const cw = 236, chh = 108;
        const cx = W - cw - 18, cy = H - chh - 18 + (1 - cardIn) * 26;
        ctx.globalAlpha = cardIn;
        ctx.fillStyle = C.card;
        ctx.strokeStyle = "rgba(143,160,173,0.25)";
        ctx.beginPath(); ctx.roundRect(cx, cy, cw, chh, 8); ctx.fill(); ctx.stroke();
        ctx.font = mono(9);
        ctx.fillStyle = C.muted;
        ctx.fillText("WHATSAPP · VOLUNTEER CAPTAIN", cx + 12, cy + 18);
        ctx.font = mono(10, 400);
        ctx.fillStyle = C.ink;
        ctx.fillText("Generator → 42 Maple St", cx + 12, cy + 38);
        ctx.fillText("1.2 km · ~7 min · heat: bring water", cx + 12, cy + 54);
        // buttons
        const by = cy + 68;
        ctx.font = mono(10);
        ctx.strokeStyle = C.ok;
        ctx.fillStyle = accepted > 0 ? C.ok : "transparent";
        ctx.beginPath(); ctx.roundRect(cx + 12, by, 100, 26, 13); ctx.fill(); ctx.stroke();
        ctx.fillStyle = accepted > 0 ? "#10251a" : C.ok;
        ctx.textAlign = "center";
        ctx.fillText(accepted > 0 ? "ACCEPTED ✓" : "ACCEPT", cx + 62, by + 17);
        ctx.strokeStyle = "rgba(143,160,173,0.5)";
        ctx.beginPath(); ctx.roundRect(cx + 124, by, 100, 26, 13); ctx.stroke();
        ctx.fillStyle = C.muted;
        ctx.fillText("PASS", cx + 174, by + 17);
        ctx.textAlign = "left";
        // tap ring on ACCEPT
        const tap = at(t, 8.45, 0.5);
        if (tap > 0 && tap < 1) {
          ctx.strokeStyle = C.ok;
          ctx.globalAlpha = (1 - tap) * cardIn;
          ctx.beginPath();
          ctx.arc(cx + 62, by + 13, 8 + tap * 20, 0, Math.PI * 2);
          ctx.stroke();
        }
        ctx.globalAlpha = 1;
      }

      // ── delivery run ──
      const runP = easeOut(at(t, 9.2, 2.2)) * fade;
      if (runP > 0 && runP < 1) {
        const px = OFFER.x + (REQ1.x - OFFER.x) * runP;
        const py = OFFER.y + (REQ1.y - OFFER.y) * runP;
        ctx.fillStyle = C.ink;
        ctx.beginPath(); ctx.arc(px, py, 5, 0, Math.PI * 2); ctx.fill();
        ctx.strokeStyle = "rgba(232,233,228,0.4)";
        ctx.beginPath(); ctx.arc(px, py, 9, 0, Math.PI * 2); ctx.stroke();
      }
      const deliveredIn = at(t, 11.5, 0.5) * fade;
      if (deliveredIn > 0) {
        ctx.globalAlpha = deliveredIn;
        pulse(REQ1.x, REQ1.y, t, C.ok, deliveredIn);
        chip(REQ1.x - 24, REQ1.y - 40, "DELIVERED ✓", "#d9f2e1", "rgba(82,199,118,0.25)");
        ctx.globalAlpha = 1;
      }

      // ── bottom status line ──
      ctx.font = mono(9);
      ctx.fillStyle = C.muted;
      const phase =
        t < 1.5 ? "MONITORING — NOAA ALERTS + GRID FEED"
        : t < 4.4 ? "CRISIS DETECTED — INGESTING COMMUNITY TEXTS"
        : t < 6.6 ? "MATCHING SUPPLY TO NEED — URGENCY × DISTANCE"
        : t < 9.2 ? "HUMAN APPROVAL — ONE TAP, NOTHING ELSE"
        : t < 12.5 ? "VOLUNTEER EN ROUTE — HAZARD-AWARE GUIDANCE"
        : "STANDING DOWN — BACK TO SILENT WATCH";
      ctx.fillText(phase, 16, H - 14);

      if (!reduced) raf = requestAnimationFrame(draw);
    };

    raf = requestAnimationFrame(draw);
    return () => cancelAnimationFrame(raf);
  }, [frozenAt]);

  return (
    <canvas
      ref={canvasRef}
      style={{ width: "100%", height: "auto", aspectRatio: `${W} / ${H}` }}
      className="block"
      role="img"
      aria-label="Animated demonstration of Resqio detecting a heatwave and power outage, matching a neighbor's generator to an insulin refrigeration request, sending a WhatsApp approval ping, and confirming delivery"
    />
  );
}

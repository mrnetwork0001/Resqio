import type { Config } from "tailwindcss";

// Resqio brand - brutalist emergency-ops: near-black ground, hi-vis safety
// yellow accent (hazard tape, emergency vests), paper cards, warm greys.
// ok/warn/danger/info stay semantic for the situation board.
const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ground: "#0a0a0a",
        panel: "#121211",
        raised: "#1a1a18",
        line: "#272723",
        ink: "#f1f1ec",
        muted: "#8b8b84",
        accent: "#d7ff00",
        paper: "#f4f4ee",
        ok: "#52c776",
        warn: "#dcae3c",
        danger: "#e5484d",
        info: "#58a6ff",
      },
      fontFamily: {
        display: ["var(--font-display)", "Arial Black", "sans-serif"],
        sans: ["var(--font-body)", "Helvetica Neue", "Arial", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
};
export default config;

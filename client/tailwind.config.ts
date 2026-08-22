import type { Config } from "tailwindcss";

// Resqio ops-board palette — dark ops-room screen, hazard-orange accent.
const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ground: "#10151c",
        panel: "#1a212b",
        raised: "#222b37",
        line: "#2b3440",
        ink: "#e8e9e4",
        muted: "#8fa0ad",
        accent: "#f0713a",
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

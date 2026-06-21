import type { Config } from "tailwindcss";

/**
 * Tailwind is build-time only. All colors map to CSS custom properties
 * defined in src/index.css (as RGB channel triples) so the light
 * institutional theme and the dark evidence mode share one token contract
 * and support opacity modifiers (e.g. bg-status-review/10).
 */
function withAlpha(varName: string) {
  return `rgb(var(${varName}) / <alpha-value>)`;
}

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: withAlpha("--bg"),
        fg: {
          DEFAULT: withAlpha("--fg"),
          muted: withAlpha("--fg-muted"),
        },
        surface: {
          1: withAlpha("--surface-1"),
          2: withAlpha("--surface-2"),
          3: withAlpha("--surface-3"),
        },
        line: withAlpha("--line"),
        status: {
          verified: withAlpha("--status-verified"),
          review: withAlpha("--status-review"),
          blocked: withAlpha("--status-blocked"),
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["'JetBrains Mono'", "ui-monospace", "monospace"],
      },
      borderRadius: {
        sm: "0.125rem",
        DEFAULT: "0.25rem",
        md: "0.375rem",
        lg: "0.5rem",
        xl: "0.75rem",
      },
      maxWidth: {
        container: "1600px",
        prose: "720px",
      },
    },
  },
  plugins: [],
} satisfies Config;

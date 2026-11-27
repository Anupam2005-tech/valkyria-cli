import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        graphite: {
          DEFAULT: "#1C1D20",
          950: "#101113",
          900: "#151619",
          800: "#1C1D20",
          700: "#26282C",
          600: "#34373C",
          500: "#4A4E55",
        },
        cloud: "#F2F4F1",
        sun: {
          DEFAULT: "#FFC929",
          glow: "rgba(255, 201, 41, 0.35)",
          soft: "rgba(255, 201, 41, 0.12)",
        },
      },
      fontFamily: {
        display: ["var(--font-display)", "system-ui", "sans-serif"],
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "SFMono-Regular", "monospace"],
        tech: ["var(--font-tech)", "sans-serif"],
      },
      borderRadius: {
        input: "12px",
        card: "20px",
        panel: "28px",
        pill: "999px",
      },
      boxShadow: {
        soft: "0 24px 60px rgba(0, 0, 0, 0.45)",
        sun: "0 0 0 1px rgba(255, 201, 41, 0.35), 0 0 28px rgba(255, 201, 41, 0.35)",
      },
    },
  },
  plugins: [],
};

export default config;


import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Fashion retail brand palette
        brand: {
          50:  "#fdf8ee",
          100: "#f9edcc",
          200: "#f2d990",
          300: "#e9c05a",
          400: "#dfa832",   // primary gold
          500: "#c78a1e",
          600: "#a56d18",
          700: "#7e5217",
          800: "#68421a",
          900: "#59381b",
        },
        surface: {
          950: "#07070e",
          900: "#0f0f1a",
          800: "#161625",
          700: "#1e1e31",
          600: "#27273e",
        },
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;

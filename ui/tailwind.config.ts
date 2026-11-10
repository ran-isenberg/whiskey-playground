import type { Config } from "tailwindcss";

// Theme tokens: restyle the whole app from here.
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bar: {
          bg: "#16100b",       // page background, dark oak
          panel: "#21180f",    // cards and bubbles
          raised: "#2c2015",   // hover / inputs
          line: "#3d2d1d",     // borders
          text: "#f3e9dc",     // primary text
          muted: "#b9a690",    // secondary text
          faint: "#8a7660",    // tertiary text
        },
        amber: {
          DEFAULT: "#d99a3d",  // accent: buttons, score bar
          soft: "#f0c27a",
          deep: "#a86b1f",
        },
        danger: "#e07a5f",
      },
      fontFamily: {
        display: ['"Fraunces"', "Georgia", "serif"],
        sans: ['"Inter"', "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
} satisfies Config;

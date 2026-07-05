/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#0B1220",
        panel: "#121B2E",
        panelBorder: "#22304A",
        accent: "#F2A93B",
        accentDim: "#8C6A2A",
        text: "#E7ECF5",
        textDim: "#8A93A6",
        low: "#3DDC84",
        medium: "#F2A93B",
        high: "#FF5C5C",
      },
      fontFamily: {
        mono: ["IBM Plex Mono", "ui-monospace", "monospace"],
        sans: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};

/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        // ~50% Naukri reference: clean light + recruitment blue, kept our identity
        brand: {
          bg: "#f3f6fb", // app canvas (light grey-blue)
          sidebar: "#ffffff", // white sidebar
          panel: "#ffffff", // white cards
          panel2: "#f7f9fc", // nested / hover
          line: "#e6ebf2",
          line2: "#dde4ee",
          ink: "#1d2330", // near-black text
          muted: "#6b7589", // secondary text
          blue: "#2370b7", // Naukri-ish primary blue
          blueDark: "#1b5a96",
          blueSoft: "#eaf2fb",
          teal: "#0aa39a", // secondary accent
        },
      },
      fontFamily: {
        sans: ['"Inter"', "ui-sans-serif", "system-ui", "sans-serif"],
      },
      boxShadow: {
        card: "0 1px 2px rgba(29,35,48,0.04), 0 6px 18px -10px rgba(29,35,48,0.12)",
        blue: "0 8px 20px -8px rgba(35,112,183,0.45)",
      },
    },
  },
  plugins: [],
};

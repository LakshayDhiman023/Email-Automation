/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        // Dropbox-inspired: electric blue on lots of white, near-black ink, hairlines
        brand: {
          bg: "#ffffff", // app canvas (pure white, Dropbox-style)
          sidebar: "#ffffff", // white sidebar
          panel: "#ffffff", // white cards
          panel2: "#f7f9fc", // nested / hover
          line: "#e8ebee", // hairline borders
          line2: "#dfe3e8",
          ink: "#1e1919", // Dropbox near-black text
          muted: "#637282", // secondary text
          blue: "#0061fe", // Dropbox electric blue
          blueDark: "#0050d4",
          blueSoft: "#eef4ff", // faint blue tint for hovers/badges
          teal: "#0aa39a", // secondary accent
        },
      },
      fontFamily: {
        sans: ['"Inter"', "ui-sans-serif", "system-ui", "sans-serif"],
      },
      boxShadow: {
        // Dropbox is flat — very subtle lift only
        card: "0 0 0 1px rgba(30,25,25,0.04), 0 1px 3px rgba(30,25,25,0.06)",
        blue: "0 6px 16px -8px rgba(0,97,254,0.45)",
      },
    },
  },
  plugins: [],
};

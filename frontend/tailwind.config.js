/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        // pulled from the BUILD/THINK/INNOVATE banner gradient
        brand: {
          sky: "#7cc4f2",
          blue: "#4a90e2",
          deep: "#2f6fd0",
          violet: "#7a6ff0",
          ink: "#1a2b4a",
        },
      },
      backgroundImage: {
        "brand-wash":
          "linear-gradient(120deg,#bfe3fb 0%,#7cc4f2 30%,#5fa8ee 55%,#7a8ff0 80%,#a99cf2 100%)",
      },
    },
  },
  plugins: [],
};

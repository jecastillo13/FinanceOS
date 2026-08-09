/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: { sans: ["Inter", "system-ui", "sans-serif"] },
      colors: { ink: "#07101f", panel: "#101b31" },
      boxShadow: { glow: "0 18px 70px rgba(71, 104, 255, .18)" },
    },
  },
  plugins: [],
};

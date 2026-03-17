/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: "#7c3aed", // violet-600
        secondary: "#3b82f6", // blue-500
        dark: {
          bg: "#0f172a", // slate-950
          surface: "#1e293b", // slate-800
          border: "#334155", // slate-700
          text: "#f1f5f9", // slate-100
        },
      },
      backgroundImage: {
        "gradient-dark": "linear-gradient(135deg, #7c3aed 0%, #3b82f6 100%)",
      },
    },
  },
  plugins: [],
}

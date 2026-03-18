/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Brand accents (modern, bright but not harsh)
        primary: "#7c3aed", // violet
        secondary: "#14b8a6", // teal
        dark: {
          // We keep the existing class names (bg-dark-*) for stability,
          // but map them to a clean light UI palette.
          bg: "#f6f7fb", // soft off-white
          surface: "#ffffff", // white cards
          border: "#e5e7eb", // gray-200
          text: "#0f172a", // slate-900
        },
      },
      backgroundImage: {
        "gradient-dark": "linear-gradient(135deg, #7c3aed 0%, #14b8a6 100%)",
      },
    },
  },
  plugins: [],
}

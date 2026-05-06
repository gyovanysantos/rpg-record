/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        // Dark Fantasy palette (from dark_fantasy.qss)
        background: "#1a1a2e",
        surface: "#16213e",
        card: "#0f3460",
        accent: "#c4a35a",
        "accent-hover": "#d4b36a",
        "text-primary": "#e0d6c8",
        "text-muted": "#8a7e6b",
        danger: "#8b0000",
        "danger-hover": "#a50000",
        success: "#2e5e3e",
        "success-hover": "#3a7a4e",
        border: "#2a2a4a",
      },
      fontFamily: {
        sans: ['"Segoe UI"', "system-ui", "sans-serif"],
        display: ['"Cinzel"', "serif"],
      },
      animation: {
        "card-flip": "cardFlip 0.6s ease-in-out",
        "fade-in": "fadeIn 0.3s ease-out",
        "slide-up": "slideUp 0.3s ease-out",
        glow: "glow 2s ease-in-out infinite alternate",
      },
      keyframes: {
        cardFlip: {
          "0%": { transform: "rotateY(0deg)" },
          "100%": { transform: "rotateY(180deg)" },
        },
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        glow: {
          "0%": { boxShadow: "0 0 5px rgba(196, 163, 90, 0.3)" },
          "100%": { boxShadow: "0 0 15px rgba(196, 163, 90, 0.6)" },
        },
      },
    },
  },
  plugins: [],
};

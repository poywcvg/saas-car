/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./apps/**/templates/**/*.html",
    "./apps/**/*.py",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: [
          "IRANYekan",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Tahoma",
          "sans-serif",
        ],
      },
      colors: {
        // رنگ اصلی برند: آبی نفتی، حسِ اعتماد و حرفه‌ای بودن
        brand: {
          50: "#eef4ff",
          100: "#d9e6ff",
          200: "#bcd3ff",
          300: "#8eb6ff",
          400: "#598eff",
          500: "#3366ff",
          600: "#1f47f5",
          700: "#1735e1",
          800: "#1a2eb6",
          900: "#1c2d8f",
          950: "#151d57",
        },
        // رنگ تأکیدی: نارنجی/کهربایی، حسِ انرژی و روغن موتور، مناسب CTA
        accent: {
          50: "#fff8eb",
          100: "#fdedc8",
          200: "#fbd88d",
          300: "#f9be52",
          400: "#f7a327",
          500: "#f1830e",
          600: "#d56309",
          700: "#b1450c",
          800: "#903610",
          900: "#762e11",
          950: "#441505",
        },
        // رنگ رشد/فروش: سبز، برای قاب‌بندی درآمد و بازگشت مشتری (روانشناسی فروش)
        growth: {
          50: "#ecfdf5",
          100: "#d1fae5",
          200: "#a7f3d0",
          500: "#10b981",
          600: "#059669",
          700: "#047857",
        },
        // رنگ‌های وضعیت برای سلامت سرویس خودرو
        ok: "#16a34a",     // سالم / تازه
        warn: "#f59e0b",   // نزدیک موعد
        danger: "#dc2626", // گذشته از موعد
        ink: {
          DEFAULT: "#0f172a",
          soft: "#334155",
          muted: "#64748b",
        },
        surface: {
          DEFAULT: "#ffffff",
          soft: "#f8fafc",
          muted: "#f1f5f9",
        },
      },
      boxShadow: {
        card: "0 1px 2px rgba(15,23,42,0.04), 0 8px 24px -12px rgba(15,23,42,0.12)",
        pop: "0 10px 40px -12px rgba(31,71,245,0.35)",
      },
      borderRadius: {
        xl: "0.9rem",
        "2xl": "1.25rem",
        "3xl": "1.75rem",
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        "fade-up": "fade-up 0.4s ease-out both",
      },
    },
  },
  plugins: [],
};

import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#172033",
        muted: "#657083",
        line: "#d9e0ea",
        panel: "#ffffff",
        canvas: "#f5f7fb",
        teal: {
          DEFAULT: "#0f766e",
          50: "#ecfdf5",
          100: "#ccfbf1",
          200: "#99f6e4",
          800: "#115e59",
          900: "#134e4a"
        },
        amber: {
          50: "#fffbeb",
          100: "#fef3c7",
          200: "#fde68a",
          900: "#78350f"
        },
        rose: {
          DEFAULT: "#be123c",
          50: "#fff1f2",
          100: "#ffe4e6",
          200: "#fecdd3",
          800: "#9f1239"
        }
      },
      boxShadow: {
        soft: "0 16px 40px rgba(17, 24, 39, 0.08)"
      }
    }
  },
  plugins: []
};

export default config;

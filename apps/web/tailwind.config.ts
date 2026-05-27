import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        field: {
          bg: "#f7f8f8",
          line: "#d8dedc",
          ink: "#18211f",
          muted: "#5e6b67",
          ok: "#14804a",
          warn: "#b7791f",
          fail: "#c92a2a",
          info: "#1c6dd0"
        },
      },
      boxShadow: {
        panel: "0 1px 2px rgba(20, 28, 25, 0.08)",
      },
    },
  },
  plugins: [],
};

export default config;

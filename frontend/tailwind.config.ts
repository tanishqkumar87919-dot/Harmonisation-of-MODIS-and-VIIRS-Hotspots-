import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        scientific: {
          modis: "#D9480F",
          "modis-light": "#FFE8CC",
          "modis-dark": "#A61E4D",
          viirs: "#0B7285",
          "viirs-light": "#E3FAFC",
          "viirs-dark": "#0C4A6E",
          matched: "#087F5B",
          "matched-light": "#E6FCF5",
          "unmatched-modis": "#E67700",
          "unmatched-modis-light": "#FFF3BF",
          "unmatched-viirs": "#1971C2",
          "unmatched-viirs-light": "#D0EBFF",
          ambiguous: "#862E9C",
          "ambiguous-light": "#F3D9FA",
          rejected: "#495057",
          "rejected-light": "#F1F3F5",
        },
        slate: {
          850: "#151e2e",
          950: "#0b0f19",
        },
      },
      fontFamily: {
        mono: [
          "ui-monospace",
          "SFMono-Regular",
          "Menlo",
          "Monaco",
          "Consolas",
          "Liberation Mono",
          "Courier New",
          "monospace",
        ],
      },
    },
  },
  plugins: [],
};

export default config;

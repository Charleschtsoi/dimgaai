/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        verdict: {
          true: "#16a34a",
          false: "#dc2626",
          uncertain: "#ca8a04",
        },
      },
    },
  },
  plugins: [],
};

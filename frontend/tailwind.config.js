/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: { ink: "#172033", cloud: "#f6f8fb", brand: "#3657d6", mint: "#dff7ef" },
    },
  },
  plugins: [],
};

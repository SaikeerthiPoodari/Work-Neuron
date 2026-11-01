/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: { ink: "#0f172a", cloud: "#f8fafc", brand: "#4f46e5", mint: "#dff7ef" },
    },
  },
  plugins: [],
};

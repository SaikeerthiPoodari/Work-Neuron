/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: { ink: "#0f172a", cloud: "#f5f9ff", brand: "#155eef", mint: "#dff7ef" },
    },
  },
  plugins: [],
};

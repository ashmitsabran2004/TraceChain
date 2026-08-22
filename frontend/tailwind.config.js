/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        slate: {
          950: '#0b0f19',
          900: '#111827',
          850: '#172033',
          800: '#1f2937',
        }
      }
    },
  },
  plugins: [],
}

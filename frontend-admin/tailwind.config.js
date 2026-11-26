/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        display: ['"Beautique Display"', 'serif'],
        sans: ['"Be Vietnam Pro"', 'sans-serif'],
      },
      colors: {
        darkbeige: {
          950: '#0F0E0C',
          900: '#141310',
          850: '#1A1916',
          800: '#2B2822',
          700: '#3D382F',
        },
        amberbrown: {
          300: '#E5A97C',
          400: '#D48B55',
          500: '#9C5B32',
          600: '#844B27',
          700: '#6B3B1E',
        },
        primary: {
          50: '#fdf8f3',
          100: '#f7ebde',
          500: '#9C5B32',
          600: '#844B27',
          700: '#6B3B1E',
        }
      }
    },
  },
  plugins: [],
}

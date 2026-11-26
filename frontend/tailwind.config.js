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
        display: ['"Beautique Display"', 'Georgia', 'serif'],
        sans: ['"Be Vietnam Pro"', 'system-ui', '-apple-system', 'sans-serif'],
      },
      colors: {
        // Tông Be Vàng Kim Cổ Điển (Champagne / Cream Beige)
        beige: {
          50: '#FDFBF7',
          100: '#FAF6EE',  // Nền trang chính Light mode
          200: '#F3EBDD',
          300: '#EFE6D5',  // Viền hairline tinh tế
          400: '#E2D3B8',
          500: '#CBB48E',
          600: '#AD9368',
        },
        // Nâu Da Bò / Nâu Gỗ Ấm (Màu nhấn CTA & Accent)
        amberbrown: {
          50: '#FBF5F1',
          100: '#F6EAE1',
          200: '#ECCEC0',
          300: '#DEAE9B',
          400: '#BE7850',
          500: '#9C5B32',  // Nút chính
          600: '#844B27',  // Hover
          700: '#6C3C1E',
        },
        // Dark mode: Xám be đen & Be than tối
        darkbeige: {
          700: '#322E26',
          750: '#26231D',
          800: '#222019',  // Viền / Card phụ
          850: '#181714',  // Card chính
          900: '#12110F',  // Surface
          950: '#0F0E0C',  // Nền trang Dark mode
        },
        // Primary alias map sang Nâu da bò ấm
        primary: {
          50: '#FBF5F1',
          100: '#F6EAE1',
          500: '#9C5B32',
          600: '#844B27',
          700: '#6C3C1E',
        }
      }
    },
  },
  plugins: [],
}

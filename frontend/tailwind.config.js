/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'polaroid-warm': {
          50: '#fffdfa',
          100: '#fef9f2',
          200: '#fbeee0',
          300: '#f7dbca',
          400: '#f2c8b1',
          500: '#e9b49a',
          600: '#d69a81',
          700: '#b57b65',
          800: '#945c4a',
          900: '#733d31',
        },
        'warm-accent': '#fdf6e3',
      },
    },
  },
  plugins: [],
}

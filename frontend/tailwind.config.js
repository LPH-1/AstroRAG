/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        space: {
          DEFAULT: '#0a0a1a',
          blue: '#1a1a3e',
          purple: '#2a1a4e',
        },
      },
    },
  },
  plugins: [],
};

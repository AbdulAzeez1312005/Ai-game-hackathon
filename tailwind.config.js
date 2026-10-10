/** @type {import('tailwindcss').Config} */
export default {
  content: ['./frontend/src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        night: '#080d18',
        panel: '#111c2e',
        board: '#174d91',
        gold: '#ffbd59',
        sky: '#66d3ff',
      },
      boxShadow: {
        panel: '0 24px 70px rgba(0, 0, 0, 0.28)',
      },
    },
  },
  plugins: [],
};

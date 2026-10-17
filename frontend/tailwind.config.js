/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        amazon: {
          dark: '#131921',
          nav: '#232F3E',
          subnav: '#37475A',
          yellow: '#FF9900',
          yellowHover: '#FA8900',
          blue: '#007185',
          link: '#0066c0',
          bg: '#EAEDED',
          border: '#D5DBDB',
          card: '#FFFFFF',
          text: '#0F1111',
          muted: '#565959',
          alert: '#B12704',
          green: '#067D62'
        },
        ge: {
          navy: '#0A192F',
          blue: '#0284C7',
          sky: '#0284C7',
          slate: '#F8FAFC',
          border: '#E2E8F0'
        }
      },
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'Arial', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      }
    },
  },
  plugins: [],
}

/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: {
          DEFAULT: '#050508',
          paper: '#0F0F16',
          subtle: '#1A1A24',
        },
        primary: {
          DEFAULT: '#FF0080',
          hover: '#D9006C',
          foreground: '#FFFFFF',
        },
        secondary: {
          DEFAULT: '#00FFCC',
          hover: '#00CCA3',
          foreground: '#000000',
        },
        accent: {
          purple: '#7000FF',
          yellow: '#FFD600',
        },
        text: {
          primary: '#FFFFFF',
          secondary: '#9CA3AF',
          muted: '#6B7280',
        },
        status: {
          online: '#22C55E',
          offline: '#6B7280',
          busy: '#EF4444',
        },
      },
      fontFamily: {
        heading: ['Outfit', 'sans-serif'],
        body: ['DM Sans', 'sans-serif'],
      },
      boxShadow: {
        neon: '0 0 20px -5px #FF0080',
        'neon-lg': '0 0 30px -5px #FF0080',
        card: '0 10px 40px -10px rgba(0,0,0,0.5)',
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};
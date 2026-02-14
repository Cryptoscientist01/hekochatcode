/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: {
          DEFAULT: '#0A0A0F',
          paper: '#12121A',
          subtle: '#1A1A28',
        },
        primary: {
          DEFAULT: '#FF0080',
          hover: '#E6006F',
          foreground: '#FFFFFF',
        },
        secondary: {
          DEFAULT: '#00D9FF',
          hover: '#00B8D9',
          foreground: '#000000',
        },
        accent: {
          purple: '#9D4EDD',
          yellow: '#FFD60A',
        },
        text: {
          primary: '#FFFFFF',
          secondary: '#A0AEC0',
          muted: '#718096',
        },
        status: {
          online: '#10B981',
          offline: '#6B7280',
          busy: '#EF4444',
        },
      },
      fontFamily: {
        heading: ['Inter', 'sans-serif'],
        body: ['Inter', 'sans-serif'],
      },
      boxShadow: {
        neon: '0 0 30px -5px rgba(255, 0, 128, 0.5)',
        'neon-lg': '0 0 40px -5px rgba(255, 0, 128, 0.6)',
        card: '0 20px 60px -15px rgba(0, 0, 0, 0.5)',
        'card-hover': '0 30px 80px -15px rgba(0, 0, 0, 0.6)',
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
      backdropBlur: {
        xs: '2px',
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};
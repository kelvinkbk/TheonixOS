/** @type {import('tailwindcss').Config} */
// Production build config — mirrors assets/js/tw-config.js (the CDN theme).
// Run `npm run build:css` to compile assets/css/tailwind.min.css.
module.exports = {
  darkMode: 'class',
  content: ['./*.html', './assets/js/*.js'],
  theme: {
    extend: {
      colors: {
        theo: {
          bg: '#070b14', bg2: '#0a0f1c', surface: '#0f1524',
          cyan: '#22d3ee', cyan2: '#00d4ff', blue: '#3b82f6',
          indigo: '#6c63ff', mint: '#00ffaa', ink: '#f3f6ff', muted: '#9aa7c7',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['"Space Grotesk"', 'Outfit', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
      boxShadow: {
        glow: '0 0 60px -10px rgba(34, 211, 238, 0.45)',
        'glow-blue': '0 0 50px -12px rgba(59, 130, 246, 0.5)',
        card: '0 20px 60px -20px rgba(0, 0, 0, 0.7)',
      },
      keyframes: {
        float: { '0%,100%': { transform: 'translateY(0)' }, '50%': { transform: 'translateY(-14px)' } },
        shimmer: { '0%': { backgroundPosition: '200% center' }, '100%': { backgroundPosition: '-200% center' } },
        'pulse-ring': { '0%': { transform: 'scale(0.8)', opacity: '0.7' }, '100%': { transform: 'scale(2.2)', opacity: '0' } },
      },
      animation: {
        float: 'float 6s ease-in-out infinite',
        shimmer: 'shimmer 6s linear infinite',
        'pulse-ring': 'pulse-ring 2.4s ease-out infinite',
      },
    },
  },
  plugins: [],
};

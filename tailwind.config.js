/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './theme/templates/**/*.html',
    './theme/static_src/**/*.js',
  ],
  theme: {
    extend: {
      colors: {
        // Aeromiles brand colors
        sky: {
          50: '#E0F7FF',
          100: '#B3EAFF',
          200: '#7DDFFF',
          300: '#4DD4FF',
          400: '#1AC9FF',
          500: '#00BFFF', // Primary sky blue
          600: '#0098CC',
          700: '#0073A0',
          800: '#004F74',
          900: '#002A48',
          dark: '#0090CC',
          light: '#E0F7FF',
          mid: '#7DDFFF',
        },
        ink: {
          50: '#F0F4F8',
          100: '#E0E9F1',
          200: '#C1D3E3',
          300: '#A2BDD5',
          400: '#83A7C7',
          500: '#6B7A95', // Secondary muted
          600: '#544E6A',
          700: '#3D223F',
          800: '#261414',
          900: '#0A1628', // Primary dark/ink
        },
        surface: '#F4F9FD',
        card: '#FFFFFF',
        border: '#E2ECF5',
        muted: '#6B7A95',
      },
      fontFamily: {
        jakarta: ['Plus Jakarta Sans', 'sans-serif'],
        mono: ['DM Mono', 'monospace'],
      },
      backdropBlur: {
        glass: '14px',
      },
    },
  },
  plugins: [],
}

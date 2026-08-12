export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: 'oklch(0.16 0.012 258)',
        surface: 'oklch(0.20 0.013 258)',
        'surface-2': 'oklch(0.245 0.015 258)',
        border: 'oklch(0.30 0.016 258)',
        'border-muted': 'oklch(0.25 0.014 258)',
        ink: 'oklch(0.93 0.004 258)',
        'ink-muted': 'oklch(0.70 0.012 258)',
        'ink-faint': 'oklch(0.60 0.012 258)',
        accent: 'oklch(0.48 0.16 255)',
        'accent-hover': 'oklch(0.53 0.16 255)',
        'accent-ink': 'oklch(0.99 0 0)',
        danger: 'oklch(0.68 0.18 25)',
        'danger-bg': 'oklch(0.24 0.05 25)',
      },
      fontSize: {
        xs: ['0.8125rem', { lineHeight: '1.4' }],
        sm: ['0.9375rem', { lineHeight: '1.5' }],
        base: ['1rem', { lineHeight: '1.6' }],
      },
      animation: {
        fadeIn: 'fadeIn 0.2s ease-out',
        slideUp: 'slideUp 0.25s cubic-bezier(0.16, 1, 0.3, 1)',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(6px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      }
    },
  },
  plugins: [],
}

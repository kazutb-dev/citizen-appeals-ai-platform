/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        // MedHubHAQ brand anchor colors (navy / teal / gold) — медицинская палитра
        brand: {
          navy: '#16355a',  // глубокий синий (доверие)
          teal: '#00b0ad',  // медицинский бирюзовый
          gold: '#fbbd48',  // акцент
        },

        // Navy palette
        background: '#0a1a2e',   // navy-950
        surface: '#0e2742',      // navy-900
        'surface-elevated': '#132e4b', // navy-800
        'surface-card': '#1b3755',     // navy-700
        border: '#2c4565',       // navy-600
        'border-light': '#35557c',     // navy-500

        // Primary: medical teal
        primary: {
          DEFAULT: '#09bab2',    // teal-400
          light: '#4fd4cd',      // teal-300
          dark: '#0d7281',       // teal-700
        },
        accent: '#09bab2',       // teal-400

        // Gold highlight
        gold: {
          DEFAULT: '#fbbd48',    // brand gold
          dark: '#d8902d',       // gold-600
          light: '#ffd089',      // gold-300
        },

        // Semantic / status (keep existing mapping)
        risk: {
          critical: '#dc2626',
          high: '#ea580c',
          medium: '#d97706',
          low: '#16a34a',
        },

        // Full navy scale for fine-grained use
        navy: {
          950: '#0a1a2e',
          900: '#0e2742',
          800: '#132e4b',
          700: '#1b3755',
          600: '#2c4565',
          500: '#35557c',
          400: '#4a6c95',
          300: '#6e8bad',
          200: '#9db3cb',
          100: '#cdd9e6',
          50:  '#eef3f8',
        },

        // Full teal scale
        teal: {
          900: '#053a40',
          800: '#0a5a63',
          700: '#0d7281',
          600: '#117886',
          500: '#0e9aa0',
          400: '#00b0ad',
          300: '#4fd4cd',
          200: '#8ce5e0',
          100: '#c2f2ef',
          50:  '#e7faf8',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
      fontSize: {
        'hero': ['clamp(3.5rem,2.2rem + 3vw,4.5rem)', { lineHeight: '1.10' }],
        '5xl':  ['clamp(2.75rem,1.9rem + 2.2vw,3.75rem)', { lineHeight: '1.15' }],
        '4xl':  ['clamp(2.25rem,1.6rem + 1.6vw,3rem)',    { lineHeight: '1.22' }],
      },
      borderRadius: {
        'sm':   '8px',
        'md':   '12px',
        'lg':   '18px',
        'xl':   '26px',
        '2xl':  '36px',
        'pill': '999px',
      },
      boxShadow: {
        xs:   '0 1px 2px rgba(14,39,66,0.06)',
        sm:   '0 2px 6px rgba(14,39,66,0.08)',
        md:   '0 8px 20px rgba(14,39,66,0.10)',
        lg:   '0 18px 40px rgba(14,39,66,0.14)',
        xl:   '0 30px 70px rgba(11,26,46,0.22)',
        glow: '0 0 24px -6px rgba(9,186,178,0.45)',
        gold: '0 14px 34px rgba(216,144,45,0.28)',
        card: '0 8px 20px rgba(14,39,66,0.10)',
        'focus-ring': '0 0 0 3px rgba(9,186,178,0.45)',
      },
      keyframes: {
        pulseDot: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.35' },
        },
        'kz-rise': {
          from: { opacity: '0', transform: 'translateY(22px)' },
          to:   { opacity: '1', transform: 'translateY(0)' },
        },
        'kz-wave': {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%':      { transform: 'translateY(-8px)' },
        },
        'kz-shimmer': {
          from: { backgroundPosition: '-150% 0' },
          to:   { backgroundPosition: '250% 0' },
        },
      },
      animation: {
        pulseDot: 'pulseDot 1.6s ease-in-out infinite',
        'kz-rise': 'kz-rise 0.42s cubic-bezier(0.16,1,0.3,1) forwards',
        'kz-wave': 'kz-wave 3s ease-in-out infinite',
        'kz-shimmer': 'kz-shimmer 2s linear infinite',
      },
      transitionTimingFunction: {
        'kz-out':    'cubic-bezier(0.16,1,0.3,1)',
        'kz-wave':   'cubic-bezier(0.65,0,0.35,1)',
        'kz-spring': 'cubic-bezier(0.34,1.56,0.64,1)',
      },
    },
  },
  plugins: [],
}

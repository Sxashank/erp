/**
 * Tailwind configuration — SMFC ERP design tokens.
 *
 * See CLAUDE.md §9 for the rationale and the full token table. The short
 * version: everything ambient in the UI goes through these tokens.
 * Per-page tweaks go through token composition, not new hexes.
 *
 * Colour palette is an NBFC-conservative set:
 *   primary   → brand blue (trust / finance)
 *   secondary → slate (neutral information)
 *   success   → emerald (paid, approved, active)
 *   warning   → amber (overdue, pending action)
 *   danger    → rose (rejected, NPA, destructive)
 *   info      → sky (informational tips)
 *   neutral   → slate 50-900 for backgrounds, borders, text
 *
 * Every colour has a full 50–900 scale so we can tune contrast without
 * reaching for ad-hoc hex codes. Do NOT introduce `bg-[#...]` in pages.
 */

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      // -----------------------------------------------------------------
      // Palette. 50 = lightest wash, 900 = darkest ink.
      // -----------------------------------------------------------------
      colors: {
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
          DEFAULT: '#2563eb',
        },
        secondary: {
          50: '#f8fafc',
          100: '#f1f5f9',
          200: '#e2e8f0',
          300: '#cbd5e1',
          400: '#94a3b8',
          500: '#64748b',
          600: '#475569',
          700: '#334155',
          800: '#1e293b',
          900: '#0f172a',
          DEFAULT: '#475569',
        },
        success: {
          50: '#ecfdf5',
          100: '#d1fae5',
          200: '#a7f3d0',
          300: '#6ee7b7',
          400: '#34d399',
          500: '#10b981',
          600: '#059669',
          700: '#047857',
          800: '#065f46',
          900: '#064e3b',
          DEFAULT: '#059669',
        },
        warning: {
          50: '#fffbeb',
          100: '#fef3c7',
          200: '#fde68a',
          300: '#fcd34d',
          400: '#fbbf24',
          500: '#f59e0b',
          600: '#d97706',
          700: '#b45309',
          800: '#92400e',
          900: '#78350f',
          DEFAULT: '#d97706',
        },
        danger: {
          50: '#fff1f2',
          100: '#ffe4e6',
          200: '#fecdd3',
          300: '#fda4af',
          400: '#fb7185',
          500: '#f43f5e',
          600: '#e11d48',
          700: '#be123c',
          800: '#9f1239',
          900: '#881337',
          DEFAULT: '#e11d48',
        },
        info: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          200: '#bae6fd',
          300: '#7dd3fc',
          400: '#38bdf8',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
          800: '#075985',
          900: '#0c4a6e',
          DEFAULT: '#0284c7',
        },
        neutral: {
          50: '#f8fafc',
          100: '#f1f5f9',
          200: '#e2e8f0',
          300: '#cbd5e1',
          400: '#94a3b8',
          500: '#64748b',
          600: '#475569',
          700: '#334155',
          800: '#1e293b',
          900: '#0f172a',
        },
        // Semantic surface tokens (used by shadcn/ui primitives).
        border: '#e2e8f0',
        input: '#e2e8f0',
        ring: '#2563eb',
        background: '#ffffff',
        foreground: '#0f172a',
        muted: {
          DEFAULT: '#f1f5f9',
          foreground: '#64748b',
        },
        card: {
          DEFAULT: '#ffffff',
          foreground: '#0f172a',
        },
        popover: {
          DEFAULT: '#ffffff',
          foreground: '#0f172a',
        },
        accent: {
          DEFAULT: '#f1f5f9',
          foreground: '#0f172a',
        },
        destructive: {
          DEFAULT: '#e11d48',
          foreground: '#ffffff',
        },
      },
      // -----------------------------------------------------------------
      // Typography scale. Larger than the default so dense financial
      // screens stay readable. Line-height tuned for table rows.
      // -----------------------------------------------------------------
      fontSize: {
        xs: ['0.75rem', { lineHeight: '1rem' }],
        sm: ['0.875rem', { lineHeight: '1.25rem' }],
        base: ['0.9375rem', { lineHeight: '1.5rem' }],
        lg: ['1.0625rem', { lineHeight: '1.625rem' }],
        xl: ['1.25rem', { lineHeight: '1.75rem' }],
        '2xl': ['1.5rem', { lineHeight: '2rem' }],
        '3xl': ['1.875rem', { lineHeight: '2.25rem' }],
      },
      fontFamily: {
        sans: [
          '"Inter"',
          'system-ui',
          '-apple-system',
          'Segoe UI',
          'Roboto',
          'sans-serif',
        ],
        mono: [
          '"JetBrains Mono"',
          'ui-monospace',
          'SFMono-Regular',
          'Menlo',
          'monospace',
        ],
      },
      // -----------------------------------------------------------------
      // Spacing — 4 px base. The numeric names map to multiples of 0.25rem.
      // -----------------------------------------------------------------
      spacing: {
        '4.5': '1.125rem',   // 18 px — half-step between 4 and 5
        '13': '3.25rem',     // 52 px — table-header height
        '15': '3.75rem',     // 60 px — compact toolbar height
        '18': '4.5rem',      // 72 px — dense row with actions
        sidebar: '16rem',     // 256 px — default sidebar width
        'sidebar-collapsed': '4rem',  // 64 px
      },
      // -----------------------------------------------------------------
      // Radii + shadows — canonical surface feel.
      // -----------------------------------------------------------------
      borderRadius: {
        sm: '0.25rem',
        DEFAULT: '0.375rem',
        md: '0.5rem',
        lg: '0.75rem',
        xl: '1rem',
        '2xl': '1.25rem',
        full: '9999px',
      },
      boxShadow: {
        sm: '0 1px 2px 0 rgb(15 23 42 / 0.05)',
        DEFAULT: '0 1px 3px 0 rgb(15 23 42 / 0.08), 0 1px 2px -1px rgb(15 23 42 / 0.08)',
        md: '0 4px 6px -1px rgb(15 23 42 / 0.08), 0 2px 4px -2px rgb(15 23 42 / 0.08)',
        lg: '0 10px 15px -3px rgb(15 23 42 / 0.08), 0 4px 6px -4px rgb(15 23 42 / 0.08)',
        focus: '0 0 0 3px rgb(37 99 235 / 0.35)',
        none: 'none',
      },
      // -----------------------------------------------------------------
      // Density anchors for dense financial tables / forms.
      // -----------------------------------------------------------------
      minHeight: {
        'row-sm': '2rem',     // 32 px
        'row-md': '2.5rem',   // 40 px — canonical row height
        'row-lg': '3rem',     // 48 px
      },
      // -----------------------------------------------------------------
      // Keyframes / transitions — mostly untouched from Tailwind defaults,
      // but add a "shake" used by form-error highlights.
      // -----------------------------------------------------------------
      keyframes: {
        shake: {
          '0%, 100%': { transform: 'translateX(0)' },
          '25%': { transform: 'translateX(-2px)' },
          '75%': { transform: 'translateX(2px)' },
        },
      },
      animation: {
        shake: 'shake 0.25s ease-in-out 2',
      },
    },
  },
  plugins: [],
};

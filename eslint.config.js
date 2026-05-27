// ESLint flat config for SMFC ERP frontend. See AGENTS.md §5.
// This config enforces the standards that a future maintainer must not
// relax without a documented decision updating AGENTS.md in the same PR.

import js from '@eslint/js';
import tseslint from 'typescript-eslint';
import reactPlugin from 'eslint-plugin-react';
import reactHooks from 'eslint-plugin-react-hooks';
import reactRefresh from 'eslint-plugin-react-refresh';
import jsxA11y from 'eslint-plugin-jsx-a11y';
import importPlugin from 'eslint-plugin-import';
import prettier from 'eslint-config-prettier';
import globals from 'globals';

export default tseslint.config(
  {
    ignores: [
      'dist/**',
      'build/**',
      'node_modules/**',
      'coverage/**',
      'playwright-report/**',
      'test-results/**',
      'backend/**',
      'refdocs/**',
    ],
  },

  js.configs.recommended,
  ...tseslint.configs.recommended,
  ...tseslint.configs.stylistic,

  {
    files: ['**/*.{ts,tsx}'],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: 'module',
      globals: {
        ...globals.browser,
        ...globals.es2022,
      },
      parserOptions: {
        ecmaFeatures: { jsx: true },
      },
    },
    settings: {
      react: { version: '18.2' },
    },
    plugins: {
      react: reactPlugin,
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
      'jsx-a11y': jsxA11y,
      import: importPlugin,
    },
    rules: {
      // React
      ...reactPlugin.configs.recommended.rules,
      ...reactPlugin.configs['jsx-runtime'].rules,
      ...reactHooks.configs.recommended.rules,
      'react/prop-types': 'off', // we use TypeScript
      'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],

      // A11y — AGENTS.md §5.11
      ...jsxA11y.configs.recommended.rules,

      // TypeScript — AGENTS.md §5.9 / CLAUDE.md Appendix C
      // `any` is banned. Use `unknown` + narrow.
      '@typescript-eslint/no-explicit-any': 'error',
      '@typescript-eslint/no-unused-vars': [
        'warn',
        { argsIgnorePattern: '^_', varsIgnorePattern: '^_', caughtErrorsIgnorePattern: '^_' },
      ],
      '@typescript-eslint/no-empty-object-type': 'warn',
      '@typescript-eslint/ban-ts-comment': [
        'error',
        {
          'ts-ignore': true, // AGENTS.md §5.9 / §12.1
          'ts-expect-error': 'allow-with-description',
          'ts-nocheck': true,
          'ts-check': false,
          minimumDescriptionLength: 10,
        },
      ],
      '@typescript-eslint/consistent-type-imports': ['error', { prefer: 'type-imports' }],

      // Console — AGENTS.md §5.12 / CLAUDE.md Appendix C: logger.* is the only
      // sanctioned outlet. No allow-list — strict.
      'no-console': 'error',

      // Money formatting — CLAUDE.md §5.8. Inline Intl.NumberFormat with INR,
      // hand-rolled formatCurrency declarations, and .toFixed(2) on rupee
      // amounts are all defects. Use <AmountDisplay /> or, in non-JSX code,
      // formatIndianCompactCurrency from @/components/common/AmountDisplay.
      'no-restricted-syntax': [
        'error',
        {
          selector:
            "NewExpression[callee.object.name='Intl'][callee.property.name='NumberFormat'] Literal[value=/INR/i]",
          message:
            "Inline Intl.NumberFormat('INR', …) is forbidden. Use <AmountDisplay /> or formatIndianCompactCurrency from @/components/common/AmountDisplay (CLAUDE.md §5.8).",
        },
        {
          selector:
            "VariableDeclarator[id.name='formatCurrency'][init.type='ArrowFunctionExpression']",
          message:
            'Per-file `const formatCurrency = …` is forbidden. Use <AmountDisplay /> (CLAUDE.md §5.8).',
        },
        {
          selector: "VariableDeclarator[id.name='formatCurrency'][init.type='FunctionExpression']",
          message:
            'Per-file `const formatCurrency = function …` is forbidden. Use <AmountDisplay /> (CLAUDE.md §5.8).',
        },
        {
          selector: "FunctionDeclaration[id.name='formatCurrency']",
          message:
            '`function formatCurrency(…)` is forbidden. Use <AmountDisplay /> (CLAUDE.md §5.8).',
        },
      ],

      // Imports
      'import/order': [
        'warn',
        {
          groups: ['builtin', 'external', 'internal', 'parent', 'sibling', 'index'],
          'newlines-between': 'always',
          alphabetize: { order: 'asc', caseInsensitive: true },
        },
      ],
      'import/no-default-export': 'off',

      // General correctness
      eqeqeq: ['error', 'always', { null: 'ignore' }],
      'no-empty': 'warn',
      'no-implicit-coercion': ['warn', { boolean: false }],
      'no-throw-literal': 'error',
      'prefer-const': 'error',
      'jsx-a11y/click-events-have-key-events': 'warn',
      'jsx-a11y/label-has-associated-control': 'warn',
      'jsx-a11y/no-autofocus': 'warn',
      'jsx-a11y/no-static-element-interactions': 'warn',
      'react/no-unescaped-entities': 'warn',
    },
  },

  // The sanctioned currency-rendering surfaces. CLAUDE.md §5.8 — these
  // files own the canonical formatter; everywhere else uses <AmountDisplay />.
  {
    files: [
      'src/lib/utils.ts',
      'src/lib/utils.test.ts',
      'src/components/common/AmountDisplay.tsx',
      'src/components/common/AmountDisplay.test.tsx',
      'src/components/lending/common/AmountInput.tsx',
      'src/components/lending/common/AmountDisplay.tsx',
    ],
    rules: {
      'no-restricted-syntax': 'off',
    },
  },

  // Test files: slightly relaxed
  {
    files: ['**/*.test.{ts,tsx}', '**/__tests__/**', 'src/test/**', 'playwright/**'],
    rules: {
      '@typescript-eslint/no-explicit-any': 'off',
    },
  },

  // Playwright fixture callbacks conventionally receive a parameter named
  // `use`; React's hook rule mistakes that for a hook call.
  {
    files: ['playwright/**'],
    rules: {
      'react-hooks/rules-of-hooks': 'off',
    },
  },

  // Node runtime configuration and utility scripts.
  {
    files: ['*.cjs', '*.mjs', 'scripts/**/*.mjs'],
    languageOptions: {
      globals: {
        ...globals.node,
      },
    },
  },

  // shadcn/ui primitives: we do not modify them; keep noise down
  {
    files: ['src/components/ui/**'],
    rules: {
      'react-refresh/only-export-components': 'off',
      '@typescript-eslint/no-empty-object-type': 'off',
      'jsx-a11y/anchor-has-content': 'off',
      'jsx-a11y/heading-has-content': 'off',
    },
  },

  prettier,
);

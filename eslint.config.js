// ESLint flat config for SMFC ERP frontend. See CLAUDE.md §5.
// This config enforces the standards that a future maintainer must not
// relax without a documented decision updating CLAUDE.md in the same PR.

import js from "@eslint/js";
import tseslint from "typescript-eslint";
import reactPlugin from "eslint-plugin-react";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import jsxA11y from "eslint-plugin-jsx-a11y";
import importPlugin from "eslint-plugin-import";
import prettier from "eslint-config-prettier";
import globals from "globals";

export default tseslint.config(
  {
    ignores: [
      "dist/**",
      "build/**",
      "node_modules/**",
      "coverage/**",
      "playwright-report/**",
      "test-results/**",
      "backend/**",
    ],
  },

  js.configs.recommended,
  ...tseslint.configs.recommended,
  ...tseslint.configs.stylistic,

  {
    files: ["**/*.{ts,tsx}"],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: "module",
      globals: {
        ...globals.browser,
        ...globals.es2022,
      },
      parserOptions: {
        ecmaFeatures: { jsx: true },
      },
    },
    settings: {
      react: { version: "18.2" },
      "import/resolver": {
        typescript: { project: "./tsconfig.json" },
      },
    },
    plugins: {
      react: reactPlugin,
      "react-hooks": reactHooks,
      "react-refresh": reactRefresh,
      "jsx-a11y": jsxA11y,
      import: importPlugin,
    },
    rules: {
      // React
      ...reactPlugin.configs.recommended.rules,
      ...reactPlugin.configs["jsx-runtime"].rules,
      ...reactHooks.configs.recommended.rules,
      "react/prop-types": "off", // we use TypeScript
      "react-refresh/only-export-components": ["warn", { allowConstantExport: true }],

      // A11y — CLAUDE.md §5.11
      ...jsxA11y.configs.recommended.rules,

      // TypeScript — CLAUDE.md §5.9
      "@typescript-eslint/no-explicit-any": "error",
      "@typescript-eslint/no-unused-vars": [
        "error",
        { argsIgnorePattern: "^_", varsIgnorePattern: "^_", caughtErrorsIgnorePattern: "^_" },
      ],
      "@typescript-eslint/ban-ts-comment": [
        "error",
        {
          "ts-ignore": true,                  // CLAUDE.md §5.9 / §12.1
          "ts-expect-error": "allow-with-description",
          "ts-nocheck": true,
          "ts-check": false,
          minimumDescriptionLength: 10,
        },
      ],
      "@typescript-eslint/consistent-type-imports": ["error", { prefer: "type-imports" }],

      // Console — CLAUDE.md §5.12: only logger.* is allowed
      "no-console": ["error", { allow: ["warn", "error", "info"] }],

      // Imports
      "import/order": [
        "warn",
        {
          groups: ["builtin", "external", "internal", "parent", "sibling", "index"],
          "newlines-between": "always",
          alphabetize: { order: "asc", caseInsensitive: true },
        },
      ],
      "import/no-default-export": "off",

      // General correctness
      eqeqeq: ["error", "always", { null: "ignore" }],
      "no-implicit-coercion": ["warn", { boolean: false }],
      "no-throw-literal": "error",
      "prefer-const": "error",
    },
  },

  // Test files: slightly relaxed
  {
    files: ["**/*.test.{ts,tsx}", "**/__tests__/**", "src/test/**", "playwright/**"],
    rules: {
      "@typescript-eslint/no-explicit-any": "off",
    },
  },

  // shadcn/ui primitives: we do not modify them; keep noise down
  {
    files: ["src/components/ui/**"],
    rules: {
      "react-refresh/only-export-components": "off",
      "@typescript-eslint/no-empty-object-type": "off",
    },
  },

  prettier,
);

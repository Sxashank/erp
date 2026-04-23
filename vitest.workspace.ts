/// <reference types="vitest" />
import { defineWorkspace } from 'vitest/config';

export default defineWorkspace([
  {
    extends: './vite.config.ts',
    test: {
      name: 'unit',
      environment: 'jsdom',
      setupFiles: ['./src/test/setup.ts'],
      include: ['src/**/*.test.{ts,tsx}'],
      exclude: ['src/**/*.int.test.{ts,tsx}'],
    },
  },
  {
    extends: './vite.config.ts',
    test: {
      name: 'integration',
      environment: 'jsdom',
      setupFiles: ['./src/test/setup.integration.ts'],
      include: ['src/**/*.int.test.{ts,tsx}'],
    },
  },
]);

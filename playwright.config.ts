/**
 * Playwright configuration for SMFC ERP E2E tests. See CLAUDE.md §10.5.
 *
 * CI invokes `pnpm test:e2e`. Locally, either run the dev server manually and
 * point PLAYWRIGHT_BASE_URL at it, or let the `webServer` block spin `pnpm
 * preview` over the built dist for a faster start.
 */

import { fileURLToPath } from 'node:url';

import { defineConfig, devices } from '@playwright/test';

const baseURL = process.env.PLAYWRIGHT_BASE_URL ?? 'http://localhost:5176';
const useBuilt = process.env.PLAYWRIGHT_USE_BUILD === '1';

// `globalSetup` connects to the E2E Postgres DB and asserts the seeded org +
// admin user are present. Only opt in for the real-user suite (run via
// `pnpm test:e2e:real`) — otherwise the smoke + visual specs don't need the
// dedicated DB.
const e2eGlobalSetup =
  process.env.PLAYWRIGHT_E2E === '1'
    ? fileURLToPath(new URL('./playwright/tests/e2e/globalSetup.ts', import.meta.url))
    : undefined;

export default defineConfig({
  testDir: './playwright/tests',
  globalSetup: e2eGlobalSetup,
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 2 : undefined,
  reporter: process.env.CI
    ? [['list'], ['html', { open: 'never' }], ['github']]
    : [['list'], ['html', { open: 'never' }]],
  outputDir: './test-results',

  use: {
    baseURL,
    trace: 'on-first-retry',
    video: 'retain-on-failure',
    screenshot: 'only-on-failure',
    actionTimeout: 15_000,
    navigationTimeout: 30_000,
  },

  // Visual regression settings — CLAUDE.md §9 / Stage 7.
  // Run `pnpm test:e2e --update-snapshots` after an intentional UI
  // change to regenerate baselines.
  expect: {
    toHaveScreenshot: {
      // Allow 0.2% diff across anti-aliasing / font rasterisation.
      maxDiffPixelRatio: 0.002,
      // Disable animations + caret for determinism.
      animations: 'disabled',
      caret: 'hide',
      scale: 'css',
    },
  },
  snapshotPathTemplate: '{testDir}/__screenshots__/{testFilePath}/{arg}{ext}',

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'], viewport: { width: 1440, height: 900 } },
    },
    {
      name: 'tablet',
      use: {
        ...devices['iPad (gen 7)'],
        viewport: { width: 768, height: 1024 },
      },
    },
  ],

  webServer: process.env.PLAYWRIGHT_EXTERNAL_SERVER
    ? undefined
    : {
        command: useBuilt ? 'pnpm build && pnpm preview --port 5176' : 'pnpm dev --port 5176',
        url: baseURL,
        reuseExistingServer: useBuilt ? false : !process.env.CI,
        timeout: 120_000,
        stdout: 'pipe',
        stderr: 'pipe',
      },
});

/**
 * Visual regression — baseline screenshots for critical screens.
 *
 * This spec is GATED by `PLAYWRIGHT_VISUAL=1` so CI runs only when the
 * baseline images are committed. The first time you run locally:
 *
 *     PLAYWRIGHT_VISUAL=1 pnpm test:e2e --update-snapshots
 *     git add playwright/tests/__screenshots__
 *
 * After that, `PLAYWRIGHT_VISUAL=1 pnpm test:e2e visual.spec.ts` will
 * diff against the baseline and fail on any unintended change.
 *
 * See CLAUDE.md §9 / Stage 7.
 */

import { expect, test } from '../fixtures/test';

declare const process: { env: { [k: string]: string | undefined } };

const VISUAL_ENABLED = process.env.PLAYWRIGHT_VISUAL === '1';

test.describe('visual regression', () => {
  test.skip(!VISUAL_ENABLED, 'Set PLAYWRIGHT_VISUAL=1 to run visual baselines.');

  test('login page — desktop 1440x900', async ({ page, consoleGate: _ }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto('/login');
    // Wait for all fonts + images to load for stable pixels.
    await page.evaluate(() => document.fonts.ready);
    await expect(page).toHaveScreenshot('login-desktop.png', { fullPage: false });
  });

  test('login page — tablet 768x1024', async ({ page, consoleGate: _ }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/login');
    await page.evaluate(() => document.fonts.ready);
    await expect(page).toHaveScreenshot('login-tablet.png', { fullPage: false });
  });
});

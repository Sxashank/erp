/**
 * Auth helper — drives the real login form through the UI so the entire auth
 * path (form → /auth/login API → Zustand store → /admin redirect) is exercised
 * end-to-end. The seeded-token shortcut on `authedPage` in `./test.ts` stays
 * available for non-auth specs that don't need to prove the login flow.
 *
 * Credentials default to the seeded SUPER_ADMIN (`krishna` /
 * `ChangeMe123!`). Override per-spec via `loginAs({ username, password })`.
 */

import { expect, type Page } from '@playwright/test';

interface LoginOpts {
  username?: string;
  password?: string;
  /** Expected post-login URL fragment. Defaults to `/admin` so tests don't
   *  break when the dashboard slug changes. */
  expectedPath?: RegExp;
}

const DEFAULT_USERNAME = process.env.UAT_ADMIN_USERNAME ?? 'krishna';
const DEFAULT_PASSWORD = process.env.UAT_ADMIN_PASSWORD ?? 'ChangeMe123!';
const DEFAULT_EXPECT = /\/admin(\/|$)/;

async function readRetryAfterSeconds(response: Awaited<ReturnType<Page['waitForResponse']>>) {
  try {
    const payload = (await response.json()) as { retry_after_seconds?: number };
    return payload.retry_after_seconds ?? 0;
  } catch {
    return 0;
  }
}

export async function loginAsAdmin(page: Page, opts: LoginOpts = {}): Promise<void> {
  await loginAs(page, opts);
}

export async function loginAs(page: Page, opts: LoginOpts = {}): Promise<void> {
  const username = opts.username ?? DEFAULT_USERNAME;
  const password = opts.password ?? DEFAULT_PASSWORD;
  const expectedPath = opts.expectedPath ?? DEFAULT_EXPECT;

  await page.goto('/login');

  for (const extraWaitMs of [0, 5_000, 10_000]) {
    if (extraWaitMs) {
      await page.waitForTimeout(extraWaitMs);
    }

    await page.getByLabel(/^username/i).fill(username);
    await page.getByLabel(/^password/i).fill(password);

    const loginResponsePromise = page.waitForResponse(
      (response) =>
        response.request().method() === 'POST' && response.url().includes('/api/v1/auth/login'),
    );

    await page.getByRole('button', { name: /^(sign in|log in|login)$/i }).click();

    const loginResponse = await loginResponsePromise;
    if (loginResponse.ok()) {
      await page.waitForURL(expectedPath, { timeout: 10_000 });
      await expect(page).toHaveURL(expectedPath);
      return;
    }

    if (loginResponse.status() === 429) {
      const retryAfterSeconds = await readRetryAfterSeconds(loginResponse);
      if (retryAfterSeconds > 0) {
        await page.waitForTimeout(retryAfterSeconds * 1000);
      }
      continue;
    }
  }

  await expect(page).toHaveURL(expectedPath);
}

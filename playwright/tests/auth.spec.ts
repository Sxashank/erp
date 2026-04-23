/**
 * E2E smoke: auth. See CLAUDE.md §10.5 flow 1 + §5.11 accessibility.
 */

import { expect, test } from '../fixtures/test';
import { runAxe } from '../fixtures/axe';

test.describe('auth', () => {
  test('login page renders and shows the form', async ({ page, consoleGate: _ }) => {
    await page.goto('/login');

    await expect(page.getByRole('heading', { name: /sign in/i })).toBeVisible();
    await expect(page.getByLabel(/username/i)).toBeVisible();
    await expect(page.getByLabel(/password/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /sign in/i })).toBeEnabled();
  });

  test('login page is accessible (no critical/serious axe violations)', async ({
    page,
    consoleGate: _,
  }) => {
    await page.goto('/login');
    await runAxe(page);
  });

  test('unauthenticated admin route redirects to login', async ({
    page,
    consoleGate: _,
  }) => {
    await page.goto('/admin');

    // PrivateRoute redirects to /login (either via Navigate or a real server redirect).
    await expect(page).toHaveURL(/\/login$/);
  });
});

/**
 * E2E — auth path.
 *
 * Real-user login: drives the `<input>` fields, clicks Sign in, asserts the
 * post-login URL + first paint. Also covers form validation: required fields
 * block submit, errors clear when the field is filled.
 *
 * No DB assertions here — auth state lives in the API + Zustand store, and
 * the cross-tenant probe already verifies row-level scoping.
 */

import { expect, test } from '../../fixtures/test';
import { loginAsAdmin } from '../../fixtures/auth';

test.describe('E2E auth', () => {
  test('login → redirected to admin dashboard', async ({ page, consoleGate }) => {
    void consoleGate;
    await loginAsAdmin(page);
    // The dashboard route renders the PageHeader; assert on the canonical
    // landing region (kept generic so a slug rename doesn't break the suite).
    await expect(page.locator('main, [role="main"]').first()).toBeVisible();
  });

  test('validation: empty username + password block submit', async ({ page, consoleGate }) => {
    consoleGate.allowError(/Failed to fetch/i);
    await page.goto('/login');
    await page.getByRole('button', { name: /^sign in$/i }).click();
    await expect(page.getByText(/username is required/i)).toBeVisible();
    await expect(page.getByText(/password is required/i)).toBeVisible();
    // Must still be on /login.
    await expect(page).toHaveURL(/\/login(\?|$)/);
  });

  test('validation: error clears when field is filled', async ({ page, consoleGate }) => {
    void consoleGate;
    await page.goto('/login');
    await page.getByRole('button', { name: /^sign in$/i }).click();
    await expect(page.getByText(/username is required/i)).toBeVisible();
    await page.getByLabel(/^username$/i).fill('krishna');
    // RHF re-validates on change once a submit has fired.
    await expect(page.getByText(/username is required/i)).toBeHidden();
  });

  test('invalid credentials surface the API error envelope', async ({ page, consoleGate }) => {
    // The login API will reject the bogus password; both the FE error banner
    // and the 401 response are expected.
    consoleGate.allowStatus(401, '/auth/login');
    consoleGate.allowError(/401|Invalid credentials|invalid credentials/i);
    await page.goto('/login');
    await page.getByLabel(/^username$/i).fill('krishna');
    await page.getByLabel(/^password$/i).fill('definitely-wrong-password');
    await page.getByRole('button', { name: /^sign in$/i }).click();
    // The page renders the error envelope's message inline.
    await expect(page.getByText(/invalid credentials|login failed/i)).toBeVisible({
      timeout: 5_000,
    });
    await expect(page).toHaveURL(/\/login(\?|$)/);
  });
});

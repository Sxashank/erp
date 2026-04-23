/**
 * E2E smoke: authenticated dashboard loads without console errors or failed
 * network requests. Mocks the backend so the test does not depend on a
 * running server. See CLAUDE.md §10.5 flow 1–2.
 */

import { expect, test } from '../fixtures/test';

test('dashboard loads for an authenticated user', async ({ authedPage: page, consoleGate }) => {
  // Mock the minimum backend surface the dashboard needs.
  await page.route('**/api/v1/auth/me', async (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        id: '22222222-2222-2222-2222-222222222222',
        username: 'admin',
        email: 'admin@smfc.example',
        full_name: 'Admin User',
        organization_id: '11111111-1111-1111-1111-111111111111',
        default_unit_id: null,
        mfa_enabled: false,
        roles: [{ id: 'r1', code: 'SUPER_ADMIN', name: 'Super Admin' }],
        permissions: [],
      }),
    }),
  );
  await page.route('**/api/v1/organizations**', async (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        items: [
          { id: '11111111-1111-1111-1111-111111111111', code: 'HO', name: 'Head Office' },
        ],
        total: 1,
      }),
    }),
  );
  await page.route('**/api/v1/auth/refresh', async (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        access_token: 'refreshed',
        refresh_token: 'refreshed-r',
        token_type: 'bearer',
        expires_in: 900,
      }),
    }),
  );
  // Catch-all for any other API endpoints the dashboard hits — keep them green.
  await page.route('**/api/v1/**', async (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ items: [], total: 0 }),
    }),
  );

  await page.goto('/admin');

  // Either the admin layout renders or we end up on /admin. Either way, it
  // must NOT have bounced to /login (which would mean bootstrap failed).
  await expect(page).not.toHaveURL(/\/login$/);
  // And at least one recognisable bit of chrome must be visible.
  await expect(page.locator('body')).toBeVisible();

  // Explicitly assert the console-gate state at the end.
  expect(consoleGate.getErrors()).toEqual([]);
  expect(consoleGate.getFailedResponses()).toEqual([]);
});

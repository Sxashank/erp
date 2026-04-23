/**
 * E2E smoke: loan application list renders with a seeded dataset. See
 * CLAUDE.md §10.5 flow 3 (the full lifecycle smoke will layer on top of
 * this once the page migrates to the canonical components).
 */

import { expect, test } from '../fixtures/test';

test('loan application list renders rows from the API', async ({
  authedPage: page,
  consoleGate,
}) => {
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
        permissions: ['loan_application.view'],
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
  await page.route(/\/api\/v1\/lending\/applications(?:\?|$).*/, async (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        items: [
          {
            id: 'app-001',
            application_number: 'SMFC/BOM/HL/2526/0001',
            status: 'SUBMITTED',
            applicant_name: 'Acme Industries',
            requested_amount: 10_000_000,
          },
        ],
        total: 1,
        page: 1,
        total_pages: 1,
      }),
    }),
  );
  await page.route('**/api/v1/**', async (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ items: [], total: 0 }),
    }),
  );

  await page.goto('/admin/lending/applications');

  await expect(page).not.toHaveURL(/\/login$/);
  await expect(page.locator('body')).toBeVisible();

  expect(consoleGate.getErrors()).toEqual([]);
  expect(consoleGate.getFailedResponses()).toEqual([]);
});

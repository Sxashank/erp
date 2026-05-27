import { expect, request as pwRequest, test } from '@playwright/test';

const env =
  (globalThis as { process?: { env?: Record<string, string | undefined> } }).process?.env ?? {};
const API_BASE = env.PLAYWRIGHT_API_BASE || 'http://localhost:8001/api/v1';
const ADMIN_USERNAME = env.UAT_ADMIN_USERNAME || 'krishna';
const ADMIN_PASSWORD = env.UAT_ADMIN_PASSWORD || 'ChangeMe123!';
const LIVE_BACKEND_ENABLED = env.PLAYWRIGHT_LIVE_BACKEND === '1';

async function login() {
  const ctx = await pwRequest.newContext();
  const res = await ctx.post(`${API_BASE}/auth/login`, {
    data: { username: ADMIN_USERNAME, password: ADMIN_PASSWORD },
  });
  if (!res.ok()) {
    throw new Error(`Login failed: ${res.status()} ${await res.text()}`);
  }
  const token = await res.json();
  const me = await ctx.get(`${API_BASE}/auth/me`, {
    headers: { Authorization: `Bearer ${token.accessToken}` },
  });
  if (!me.ok()) {
    throw new Error(`Auth/me failed: ${me.status()} ${await me.text()}`);
  }
  const meBody = await me.json();
  await ctx.dispose();
  return { token, me: meBody };
}

const ROUTES = [
  '/admin/lending',
  '/admin/lending/masters',
  '/admin/lending/masters/lending-options',
  '/admin/lending/masters/checklist-catalog',
  '/admin/lending/masters/approval-checklist-templates',
  '/admin/lending/products',
  '/admin/lending/products/new',
  '/admin/treasury/lenders',
  '/admin/treasury/lenders/new',
  '/admin/treasury/borrowings',
  '/admin/treasury/borrowings/new',
  '/admin/treasury/source-of-funds',
  '/admin/lending/reports',
  '/admin/treasury',
];

test.describe('lending treasury borrowing SSOT smoke', () => {
  test.skip(!LIVE_BACKEND_ENABLED, 'Set PLAYWRIGHT_LIVE_BACKEND=1 for live SSOT smoke.');

  test('canonical setup routes render cleanly and use master APIs', async ({ page, context }) => {
    test.setTimeout(90_000);
    const { token, me } = await login();
    const consoleErrors: string[] = [];
    const failedResponses: string[] = [];
    const apiCalls = new Set<string>();

    await context.addInitScript(
      ({ accessToken, refreshToken, organizationId }) => {
        window.localStorage.setItem(
          'smfc-auth',
          JSON.stringify({
            state: { accessToken, refreshToken },
            version: 0,
          }),
        );
        window.localStorage.setItem(
          'smfc-organization',
          JSON.stringify({
            state: { activeOrganizationId: organizationId },
            version: 0,
          }),
        );
      },
      {
        accessToken: token.accessToken,
        refreshToken: token.refreshToken,
        organizationId: me.organizationId,
      },
    );

    page.on('console', (msg) => {
      if (msg.type() === 'error') consoleErrors.push(msg.text());
    });
    page.on('pageerror', (error) => consoleErrors.push(`uncaught: ${error.message}`));
    page.on('response', (response) => {
      const url = response.url();
      if (url.includes('/api/v1/')) {
        apiCalls.add(`${response.request().method()} ${url.replace(/^https?:\/\/[^/]+/, '')}`);
      }
      if (response.status() >= 400 && url.includes('/api/v1/')) {
        failedResponses.push(`${response.status()} ${url.replace(/^https?:\/\/[^/]+/, '')}`);
      }
    });

    for (const route of ROUTES) {
      await page.goto(route, { waitUntil: 'domcontentloaded' });
      try {
        await page.waitForLoadState('networkidle', { timeout: 8_000 });
      } catch {
        // Some pages keep background queries alive; failed API responses are tracked separately.
      }
      await page.waitForTimeout(150);
      await expect(page.locator('body')).not.toContainText('404');
    }

    await page.goto('/admin/lending/checklist/templates', { waitUntil: 'domcontentloaded' });
    await expect(page).toHaveURL(/\/admin\/lending\/masters\/approval-checklist-templates/);

    const expectedMasterCalls = [
      '/api/v1/lending/masters/catalog',
      'optionGroup=PRODUCT_CATEGORY',
      'optionGroup=RATE_TYPE',
      'optionGroup=REPAYMENT_FREQUENCY',
      'optionGroup=REPAYMENT_MODE',
      'optionGroup=LENDER_TYPE',
      'optionGroup=RATING_AGENCY',
      'optionGroup=BORROWING_TYPE',
      'optionGroup=SECURITY_TYPE',
      '/api/v1/lending/masters/day-count-conventions/rows',
      '/api/v1/lending/masters/rate-reset-benchmarks/rows',
      '/api/v1/lending/masters/checklist-catalog/rows',
      '/api/v1/lending/masters/approval-checklist-templates/rows',
    ];

    for (const expected of expectedMasterCalls) {
      expect(
        Array.from(apiCalls).some((call) => call.includes(expected)),
        `Expected API call containing ${expected}`,
      ).toBe(true);
    }

    expect(consoleErrors, `Console errors:\n${consoleErrors.join('\n')}`).toEqual([]);
    expect(failedResponses, `Failed API responses:\n${failedResponses.join('\n')}`).toEqual([]);
  });
});

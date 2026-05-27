/**
 * Live-backend HRIS, payroll, and ESS smoke coverage.
 *
 * This spec uses the running FastAPI backend for admin auth and data fetches.
 * ESS is limited to public portal rendering until seeded ESS users are present.
 */

import { request as pwRequest, type APIRequestContext, type Page } from '@playwright/test';

import { expect, test as base } from '../fixtures/test';

const env =
  (globalThis as { process?: { env?: Record<string, string | undefined> } }).process?.env ?? {};
const API_BASE = env.PLAYWRIGHT_API_BASE || 'http://localhost:8001/api/v1';
const ADMIN_USERNAME = env.UAT_ADMIN_USERNAME || 'krishna';
const ADMIN_PASSWORD = env.UAT_ADMIN_PASSWORD || 'ChangeMe123!';
const LIVE_BACKEND_ENABLED = env.PLAYWRIGHT_LIVE_BACKEND === '1';

interface AdminSession {
  accessToken: string;
  refreshToken: string;
  organizationId: string;
}

interface LiveFixtures {
  authedPage: Page;
}

let cachedSession: AdminSession | null = null;

async function loginWithBackoff(ctx: APIRequestContext) {
  let lastFailure = '';
  for (const waitMs of [0, 5_000, 10_000, 30_000, 60_000]) {
    if (waitMs) {
      await new Promise((resolve) => setTimeout(resolve, waitMs));
    }

    const response = await ctx.post(`${API_BASE}/auth/login`, {
      data: { username: ADMIN_USERNAME, password: ADMIN_PASSWORD },
    });

    if (response.ok()) {
      return response.json();
    }

    const responseText = await response.text();
    lastFailure = `Admin login failed: ${response.status()} ${responseText}`;
    if (response.status() !== 429) {
      break;
    }
  }

  throw new Error(lastFailure || 'Admin login failed');
}

async function getAdminSession(): Promise<AdminSession> {
  if (cachedSession) {
    return cachedSession;
  }

  const ctx = await pwRequest.newContext();
  const auth = await loginWithBackoff(ctx);
  const accessToken = auth.accessToken ?? auth.access_token;
  const refreshToken = auth.refreshToken ?? auth.refresh_token;
  const headers = { Authorization: `Bearer ${accessToken}` };

  const meResponse = await ctx.get(`${API_BASE}/auth/me`, { headers });
  if (!meResponse.ok()) {
    throw new Error(`auth/me failed: ${meResponse.status()} ${await meResponse.text()}`);
  }
  const me = await meResponse.json();

  const orgResponse = await ctx.get(`${API_BASE}/organizations`, {
    headers,
    params: { limit: 20, include_inactive: false },
  });
  if (!orgResponse.ok()) {
    throw new Error(`organizations failed: ${orgResponse.status()} ${await orgResponse.text()}`);
  }
  const orgBody = await orgResponse.json();
  const organizations: { id?: string }[] = Array.isArray(orgBody.items) ? orgBody.items : [];
  const organization =
    organizations.find(
      (item: { id?: string }) => item.id === (me.organizationId ?? me.organization_id),
    ) ?? organizations[0];
  if (!organization?.id) {
    throw new Error('No organization available for live HRIS/payroll smoke');
  }

  cachedSession = {
    accessToken,
    refreshToken,
    organizationId: organization.id,
  };

  await ctx.dispose();
  return cachedSession;
}

const test = base.extend<LiveFixtures>({
  authedPage: async ({ page, context }, use) => {
    const session = await getAdminSession();
    await context.addInitScript((adminSession) => {
      window.localStorage.setItem(
        'smfc-auth',
        JSON.stringify({
          state: {
            accessToken: adminSession.accessToken,
            refreshToken: adminSession.refreshToken,
          },
          version: 0,
        }),
      );
      window.localStorage.setItem(
        'smfc-organization',
        JSON.stringify({
          state: {
            activeOrganizationId: adminSession.organizationId,
          },
          version: 0,
        }),
      );
    }, session);
    await use(page);
  },
});

test.describe('HRIS, payroll, and ESS live backend smoke', () => {
  test.skip(
    !LIVE_BACKEND_ENABLED,
    'Set PLAYWRIGHT_LIVE_BACKEND=1 to run live HRIS/payroll/ESS smoke.',
  );
  test.skip(
    ({ browserName }) => browserName !== 'chromium',
    'Runs only in the desktop Chromium project',
  );

  test('renders HRIS and payroll admin routes against the live backend', async ({
    authedPage: page,
  }) => {
    await page.goto('/admin/hris/employees', { waitUntil: 'domcontentloaded' });
    await expect(page).not.toHaveURL(/\/login$/);
    await expect(page.getByRole('heading', { name: 'Employees' })).toBeVisible();
    await expect(page.getByRole('button', { name: /add employee/i })).toBeVisible();

    await page.goto('/admin/payroll/batches', { waitUntil: 'domcontentloaded' });
    await expect(page).not.toHaveURL(/\/login$/);
    await expect(page.getByRole('heading', { name: 'Payroll Batches' })).toBeVisible();
    await expect(page.getByRole('button', { name: /new batch/i })).toBeVisible();
  });

  test('renders the ESS login entrypoint', async ({ page }) => {
    await page.goto('/ess/login', { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('heading', { name: /employee self service/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /send otp/i })).toBeVisible();
  });
});

/**
 * Cross-tenant leakage probe — CLAUDE.md §3.4 + Appendix C.
 *
 * Logs in as `krishna` (org A) and hits every list endpoint that was
 * touched in Wave 1 of the Convention Sweep. Asserts that NO row carrying
 * a different `organizationId` leaks back.
 *
 * Scaffolded in Wave 0; populated incrementally as Wave 1 fixes each
 * route. A failing assertion here is a critical multi-tenant defect.
 *
 * Run: `pnpm exec playwright test playwright/tests/cross-tenant-leak.spec.ts`.
 */

import { test as base, expect, request as pwRequest } from '@playwright/test';

const env =
  (globalThis as { process?: { env?: Record<string, string | undefined> } }).process?.env ?? {};
const API_BASE = env.PLAYWRIGHT_API_BASE || 'http://localhost:8001/api/v1';
const ADMIN_USERNAME = env.UAT_ADMIN_USERNAME || 'krishna';
const ADMIN_PASSWORD = env.UAT_ADMIN_PASSWORD || 'ChangeMe123!';

type AuthBundle = {
  accessToken: string;
  organizationId: string;
};

let cachedBundle: AuthBundle | null = null;

async function getAuth(): Promise<AuthBundle> {
  if (cachedBundle) return cachedBundle;
  const ctx = await pwRequest.newContext();
  // Retry login with backoff on 429 — /auth/login is rate-limited 5/min.
  let body: { access_token?: string } | null = null;
  for (const waitMs of [0, 15_000, 30_000, 30_000]) {
    if (waitMs > 0) await new Promise((r) => setTimeout(r, waitMs));
    const res = await ctx.post(`${API_BASE}/auth/login`, {
      data: { username: ADMIN_USERNAME, password: ADMIN_PASSWORD },
    });
    if (res.ok()) {
      body = await res.json();
      break;
    }
    if (res.status() !== 429) {
      await ctx.dispose();
      throw new Error(`login failed: ${res.status()} ${await res.text()}`);
    }
  }
  if (!body?.access_token) {
    await ctx.dispose();
    throw new Error('login failed: rate limit budget exhausted');
  }
  // Login payload omits organization_id; fetch from /auth/me.
  const me = await ctx.get(`${API_BASE}/auth/me`, {
    headers: { Authorization: `Bearer ${body.access_token}` },
  });
  if (!me.ok()) throw new Error(`/auth/me failed: ${me.status()} ${await me.text()}`);
  const meJson = await me.json();
  await ctx.dispose();
  cachedBundle = {
    accessToken: body.access_token,
    organizationId: meJson.organization_id ?? meJson.organizationId,
  };
  return cachedBundle;
}

const test = base.extend<{ auth: AuthBundle }>({
  // eslint-disable-next-line no-empty-pattern
  auth: async ({}, use) => {
    await use(await getAuth());
  },
});

/**
 * Routes that MUST scope to `current_user.organization_id`. Populated as
 * Wave 1 migrates each route to `get_db_with_tenant`.
 *
 * Each entry pulls a list of items and the probe verifies every item
 * carries the same `organizationId` as the caller. An item without an
 * `organizationId` field is allowed (e.g. platform-wide masters like
 * IIF schemes, fund-utilisation categories).
 */
const SCOPED_LIST_ROUTES: { path: string; label: string }[] = [
  // Lending (non-LOS).
  { path: '/lending/loan-accounts?page=1&page_size=50', label: 'loan_accounts' },
  { path: '/lending/treasury/lenders?page_size=50', label: 'lenders' },
  { path: '/lending/treasury/borrowings?page_size=50', label: 'borrowings' },
  { path: '/lending/disbursements?page=1&page_size=50', label: 'disbursements' },
  { path: '/lending/receipts?page=1&page_size=50', label: 'receipts' },
  { path: '/lending/iif/enrollments', label: 'iif_enrollments' },
  { path: '/lending/iif/claims', label: 'iif_claims' },
  // Finance.
  { path: '/vouchers?page=1&page_size=50', label: 'vouchers' },
  // AP/AR.
  { path: '/vendors?page=1&page_size=50', label: 'vendors' },
  { path: '/customers?page=1&page_size=50', label: 'customers' },
  { path: '/payments?page=1&page_size=50', label: 'payments' },
  // HRIS / payroll.
  { path: '/hris/employees?page=1&page_size=50', label: 'employees' },
  // Add more as Wave 1 closes routes.
];

test.describe('cross-tenant leak probe', () => {
  for (const route of SCOPED_LIST_ROUTES) {
    test(`${route.label}: only my org's rows`, async ({ auth }) => {
      const ctx = await pwRequest.newContext({
        extraHTTPHeaders: { Authorization: `Bearer ${auth.accessToken}` },
      });
      const res = await ctx.get(`${API_BASE}${route.path}`);
      // 404/403 are acceptable (route not enabled for this org) — only
      // gate on 200 + actual data.
      if (res.status() === 200) {
        const body = await res.json();
        const items: Array<Record<string, unknown>> = Array.isArray(body) ? body : body?.items ?? [];
        for (const item of items) {
          const orgRaw = (item as { organizationId?: string; organization_id?: string }).organizationId
            ?? (item as { organization_id?: string }).organization_id;
          if (orgRaw == null) continue; // platform-wide row
          expect.soft(orgRaw, `route ${route.label} returned a row from a different org`).toBe(
            auth.organizationId,
          );
        }
      }
      await ctx.dispose();
    });
  }
});

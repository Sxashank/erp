/**
 * E2E — admin routes smoke.
 *
 * Visits every admin list + form URL through the real UI and asserts:
 *   1. URL resolves (no 4xx page response from the dev server).
 *   2. No uncaught JS exception / pageerror on first paint.
 *   3. No non-asserted API 4xx/5xx during initial load.
 *   4. The page actually mounts (the `<main>` region is visible).
 *
 * The route list mirrors the canonical inventory (App.tsx, ~50 entities).
 * This is the broad gate that catches "the link doesn't load" — distinct
 * from the per-entity CRUD specs in `10-masters.spec.ts` (and follow-ons).
 *
 * Per-route allowlists tolerate known-pending integrations (e.g. lending/aa
 * 403s for unseeded permissions) without hiding genuine regressions on
 * unrelated pages.
 */

import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

import { chromium } from '@playwright/test';

import { expect, test as base } from '../../fixtures/test';
import { loginAsAdmin } from '../../fixtures/auth';

const BASE_URL = process.env.PLAYWRIGHT_BASE_URL ?? 'http://localhost:5176';

/**
 * Single-login fixture: instead of re-logging in for every URL (which thrashes
 * the FE Zustand store and the BE auth path 50+ times), log in ONCE per
 * worker, save the storage state to a temp file, and have every test in the
 * file start from that state. The first auth flow is already covered by
 * `01-auth.spec.ts`; this file is about route reachability, not auth.
 */
const test = base.extend<{}, { storageStatePath: string }>({
  storageStatePath: [
    async ({}, use, workerInfo) => {
      const dir = mkdtempSync(join(tmpdir(), 'e2e-routes-smoke-'));
      const path = join(dir, 'storage.json');
      const browser = await chromium.launch();
      const ctx = await browser.newContext({ baseURL: BASE_URL });
      const page = await ctx.newPage();
      await loginAsAdmin(page);
      await ctx.storageState({ path });
      await ctx.close();
      await browser.close();
      await use(path);
    },
    { scope: 'worker' },
  ],

  // Override the default `page` fixture: every test starts in a context
  // pre-loaded with the seeded admin session.
  context: async ({ browser, storageStatePath }, use) => {
    const ctx = await browser.newContext({ storageState: storageStatePath, baseURL: BASE_URL });
    await use(ctx);
    await ctx.close();
  },
});


interface RouteSpec {
  module: string;
  path: string;
  /** Per-route status allowlist — keyed by url substring. */
  allowStatus?: Array<{ status: number; urlSubstring?: string }>;
  /** Per-route console error allowlist (substring / regex). */
  allowError?: RegExp[];
}

const LIST_ROUTES: RouteSpec[] = [
  // ---- Masters
  { module: 'masters', path: '/admin/organizations' },
  { module: 'masters', path: '/admin/units' },
  { module: 'masters', path: '/admin/departments' },
  { module: 'masters', path: '/admin/designations' },

  // ---- Users & Roles
  { module: 'users', path: '/admin/users' },
  { module: 'roles', path: '/admin/roles' },

  // ---- Finance
  { module: 'finance', path: '/admin/finance/financial-years' },
  { module: 'finance', path: '/admin/finance/account-groups' },
  { module: 'finance', path: '/admin/finance/accounts' },
  { module: 'finance', path: '/admin/finance/voucher-types' },
  { module: 'finance', path: '/admin/finance/vouchers' },
  { module: 'finance', path: '/admin/finance/recurring-vouchers' },
  { module: 'finance', path: '/admin/finance/voucher-templates' },

  // ---- AP/AR
  { module: 'ap_ar', path: '/admin/ap-ar/payment-terms' },
  { module: 'ap_ar', path: '/admin/ap-ar/vendors' },
  { module: 'ap_ar', path: '/admin/ap-ar/customers' },
  { module: 'ap_ar', path: '/admin/ap-ar/purchase-bills' },
  { module: 'ap_ar', path: '/admin/ap-ar/sales-invoices' },
  { module: 'ap_ar', path: '/admin/ap-ar/payments' },

  // ---- GST
  { module: 'gst', path: '/admin/gst/rates' },
  { module: 'gst', path: '/admin/gst/registrations' },
  { module: 'gst', path: '/admin/gst/hsn-sac' },

  // ---- TDS
  { module: 'tds', path: '/admin/tds/sections' },
  { module: 'tds', path: '/admin/tds/entries' },

  // ---- HRIS
  { module: 'hris', path: '/admin/hris/employees' },
  { module: 'hris', path: '/admin/hris/shifts' },
  { module: 'hris', path: '/admin/hris/holidays' },
  { module: 'hris', path: '/admin/hris/leave-types' },
  { module: 'hris', path: '/admin/hris/leave-applications' },

  // ---- Payroll
  { module: 'payroll', path: '/admin/payroll/components' },
  { module: 'payroll', path: '/admin/payroll/structures' },
  { module: 'payroll', path: '/admin/payroll/statutory' },
  { module: 'payroll', path: '/admin/payroll/batches' },

  // ---- Fixed Assets
  { module: 'fixed_assets', path: '/admin/fixed-assets/categories' },
  { module: 'fixed_assets', path: '/admin/fixed-assets/assets' },

  // ---- Fixed Deposits
  { module: 'fixed_deposits', path: '/admin/fixed-deposits/products' },
  { module: 'fixed_deposits', path: '/admin/fixed-deposits' },

  // ---- Inventory
  { module: 'inventory', path: '/admin/inventory/categories' },
  { module: 'inventory', path: '/admin/inventory/items' },
  { module: 'inventory', path: '/admin/inventory/warehouses' },

  // ---- Treasury
  { module: 'treasury', path: '/admin/treasury/lenders' },
  { module: 'treasury', path: '/admin/treasury/borrowings' },

  // ---- Legal
  { module: 'legal', path: '/admin/legal/law-firms' },
  { module: 'legal', path: '/admin/legal/advocates' },
  { module: 'legal', path: '/admin/legal/cases' },
  { module: 'legal', path: '/admin/legal/notices' },
  { module: 'legal', path: '/admin/legal/expenses' },
];

const FORM_ROUTES: RouteSpec[] = [
  // ---- Masters
  { module: 'masters', path: '/admin/units/new' },
  { module: 'masters', path: '/admin/departments/new' },
  { module: 'masters', path: '/admin/designations/new' },

  // ---- Finance
  { module: 'finance', path: '/admin/finance/financial-years/new' },
  { module: 'finance', path: '/admin/finance/account-groups/new' },
  { module: 'finance', path: '/admin/finance/accounts/new' },
  { module: 'finance', path: '/admin/finance/voucher-types/new' },
  { module: 'finance', path: '/admin/finance/vouchers/new' },

  // ---- AP/AR
  { module: 'ap_ar', path: '/admin/ap-ar/payment-terms/new' },
  { module: 'ap_ar', path: '/admin/ap-ar/vendors/new' },
  { module: 'ap_ar', path: '/admin/ap-ar/customers/new' },

  // ---- GST
  { module: 'gst', path: '/admin/gst/rates/new' },
  { module: 'gst', path: '/admin/gst/hsn-sac/new' },

  // ---- TDS
  { module: 'tds', path: '/admin/tds/sections/new' },

  // ---- HRIS
  { module: 'hris', path: '/admin/hris/shifts/new' },
  { module: 'hris', path: '/admin/hris/holidays/new' },
  { module: 'hris', path: '/admin/hris/leave-types/new' },

  // ---- Fixed Assets
  { module: 'fixed_assets', path: '/admin/fixed-assets/categories/new' },

  // ---- Treasury
  { module: 'treasury', path: '/admin/treasury/lenders/new' },
  { module: 'treasury', path: '/admin/treasury/borrowings/new' },
];

const ALL_ROUTES: RouteSpec[] = [...LIST_ROUTES, ...FORM_ROUTES];

test.describe('E2E › admin routes smoke', () => {
  for (const spec of ALL_ROUTES) {
    test(`${spec.module}: ${spec.path}`, async ({ page, consoleGate }) => {
      // Apply per-route allowlists *before* navigating so the gate is open
      // when the initial request resolves.
      (spec.allowError ?? []).forEach((p) => consoleGate.allowError(p));
      (spec.allowStatus ?? []).forEach((a) => consoleGate.allowStatus(a.status, a.urlSubstring));

      const response = await page.goto(spec.path, { waitUntil: 'domcontentloaded' });
      // Vite serves the SPA shell — every URL returns 200 unless the dev
      // server crashed. A non-200 here is a routing infrastructure failure.
      expect(response?.status() ?? 0, `dev server returned non-200 for ${spec.path}`).toBeLessThan(400);

      // `<main>` region must mount; if the route falls back to a 404 page
      // the body still renders but no `<main>` exists in the AdminLayout
      // shell. The PrivateRoute would redirect to /login if auth broke.
      await expect(page.locator('main, [role="main"]').first()).toBeVisible({ timeout: 8_000 });
      await expect(page).toHaveURL(new RegExp(spec.path.replace(/\//g, '\\/')));
    });
  }
});

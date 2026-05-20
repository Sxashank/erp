/**
 * E2E — loan-module routes smoke.
 *
 * Companion to `03-routes-smoke.spec.ts`. Covers every lending / treasury /
 * reports / IIF / portal-admin URL that exists in `src/App.tsx` and is
 * reachable WITHOUT a pre-existing record id. Detail/edit URLs that need an
 * `:id` segment are exercised via the IIF / loan CRUD specs (10–12).
 *
 * Assertions per route (inherited from `03-routes-smoke.spec.ts`):
 *   1. Dev server returns < 400 (Vite serves the SPA shell, so this catches
 *      catastrophic dev-server failures only).
 *   2. `<main>` region mounts — proves the route resolved past `PrivateRoute`.
 *   3. URL still matches after redirects (catches stealth `/login` bounces).
 *   4. No uncaught console.error / pageerror.
 *   5. No non-asserted 4xx/5xx during initial load.
 *
 * Per-route allowlists tolerate genuinely-pending integrations (e.g. AA /
 * NACH portals that are stubbed under feature flags). Each allowlist entry
 * carries a comment naming the deferral.
 */

import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

import { chromium } from '@playwright/test';

import { expect, test as base } from '../../fixtures/test';
import { loginAsAdmin } from '../../fixtures/auth';

const BASE_URL = process.env.PLAYWRIGHT_BASE_URL ?? 'http://localhost:5176';

const test = base.extend<{}, { storageStatePath: string }>({
  storageStatePath: [
    async ({}, use, workerInfo) => {
      const dir = mkdtempSync(join(tmpdir(), 'e2e-loan-routes-'));
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

// ---------------------------------------------------------------------------
// Lending — origination + servicing + collections + workbenches.
// Detail routes that need an id (`:id`, `:batchId`, `:consentId`) are NOT in
// the smoke set — those are exercised by the CRUD specs once a real record
// exists.
const LENDING_ROUTES: RouteSpec[] = [
  // Dashboard
  { module: 'lending', path: '/admin/lending' },

  // Entities / Products / Applications / Sanctions
  { module: 'lending', path: '/admin/lending/entities' },
  { module: 'lending', path: '/admin/lending/entities/new' },
  { module: 'lending', path: '/admin/lending/products' },
  { module: 'lending', path: '/admin/lending/products/new' },
  { module: 'lending', path: '/admin/lending/applications' },
  { module: 'lending', path: '/admin/lending/applications/new' },
  { module: 'lending', path: '/admin/lending/sanctions' },
  { module: 'lending', path: '/admin/lending/sanctions/new' },

  // Loan accounts (legacy + new aliases)
  { module: 'lending', path: '/admin/lending/accounts' },
  { module: 'lending', path: '/admin/lending/loan-accounts' },

  // Disbursements (list + create variants)
  { module: 'lending', path: '/admin/lending/disbursements' },
  { module: 'lending', path: '/admin/lending/disbursements/new' },
  { module: 'lending', path: '/admin/lending/disbursements/create' },
  { module: 'lending', path: '/admin/lending/disbursements-enhanced' },
  { module: 'lending', path: '/admin/lending/disbursements/approval' },

  // Receipts (list + create variants)
  { module: 'lending', path: '/admin/lending/receipts' },
  { module: 'lending', path: '/admin/lending/receipts/new' },
  { module: 'lending', path: '/admin/lending/receipts/create' },
  { module: 'lending', path: '/admin/lending/receipts-enhanced' },
  { module: 'lending', path: '/admin/lending/receipts/bulk-upload' },

  // Collections / cockpits / NPA / risk / closure
  { module: 'lending', path: '/admin/lending/collection-cockpit' },
  { module: 'lending', path: '/admin/lending/collections' },
  { module: 'lending', path: '/admin/lending/collections/cockpit' },
  { module: 'lending', path: '/admin/lending/collections/followups' },
  { module: 'lending', path: '/admin/lending/collections/npa' },
  { module: 'lending', path: '/admin/lending/collections/ots' },
  { module: 'lending', path: '/admin/lending/collections/ots/new' },
  { module: 'lending', path: '/admin/lending/collections/legal' },
  { module: 'lending', path: '/admin/lending/collections/restructure' },
  { module: 'lending', path: '/admin/lending/collections/restructure/new' },
  { module: 'lending', path: '/admin/lending/closure-cockpit' },
  { module: 'lending', path: '/admin/lending/risk-cockpit' },
  { module: 'lending', path: '/admin/lending/repayment-matching' },
  { module: 'lending', path: '/admin/lending/npa' },
  { module: 'lending', path: '/admin/lending/npa/dashboard' },

  // Schedules + EMI tools
  { module: 'lending', path: '/admin/lending/schedules/generate' },
  { module: 'lending', path: '/admin/lending/emi-calculator' },

  // Collaterals
  { module: 'lending', path: '/admin/lending/collaterals' },
  { module: 'lending', path: '/admin/lending/collaterals/create' },

  // Checklist templates
  { module: 'lending', path: '/admin/lending/checklist/templates' },
  { module: 'lending', path: '/admin/lending/checklist/templates/new' },
];

// ---------------------------------------------------------------------------
// IIF — newly added in this iteration. Five JSONB rule fields per scheme
// (`calculation_rules`, `eligibility_rules`, `required_documents`,
// `workflow_rules`, `fund_rules`) — the form must render without errors.
const IIF_ROUTES: RouteSpec[] = [
  { module: 'iif', path: '/admin/lending/iif/schemes' },
  { module: 'iif', path: '/admin/lending/iif/schemes/new' },
  { module: 'iif', path: '/admin/lending/iif/categories' },
  { module: 'iif', path: '/admin/lending/iif/categories/new' },
  { module: 'iif', path: '/admin/lending/iif/enrollments' },
  { module: 'iif', path: '/admin/lending/iif/claims' },
];

// ---------------------------------------------------------------------------
// Lending reports — every report path exists in App.tsx; all but the
// dashboard render via `<ReportsDashboard>`, so the smoke check verifies the
// route is wired without exercising the underlying analytics endpoint.
const LENDING_REPORTS: RouteSpec[] = [
  { module: 'lending_reports', path: '/admin/lending/reports' },
  { module: 'lending_reports', path: '/admin/lending/reports/portfolio' },
  { module: 'lending_reports', path: '/admin/lending/reports/origination' },
  { module: 'lending_reports', path: '/admin/lending/reports/collections' },
  { module: 'lending_reports', path: '/admin/lending/reports/npa' },
  { module: 'lending_reports', path: '/admin/lending/reports/compliance' },
  { module: 'lending_reports', path: '/admin/lending/reports/treasury' },
  { module: 'lending_reports', path: '/admin/lending/reports/collections/cockpit' },
  { module: 'lending_reports', path: '/admin/lending/reports/risk' },

  // Portfolio sub-reports
  { module: 'lending_reports', path: '/admin/lending/reports/portfolio/aum' },
  { module: 'lending_reports', path: '/admin/lending/reports/portfolio/product-wise' },
  { module: 'lending_reports', path: '/admin/lending/reports/portfolio/branch-wise' },
  { module: 'lending_reports', path: '/admin/lending/reports/portfolio/industry' },
  { module: 'lending_reports', path: '/admin/lending/reports/portfolio/aging' },
  { module: 'lending_reports', path: '/admin/lending/reports/portfolio/concentration' },
  { module: 'lending_reports', path: '/admin/lending/reports/portfolio/yield' },

  // Origination sub-reports
  { module: 'lending_reports', path: '/admin/lending/reports/origination/pipeline' },
  { module: 'lending_reports', path: '/admin/lending/reports/origination/conversion' },
  { module: 'lending_reports', path: '/admin/lending/reports/origination/tat' },
  { module: 'lending_reports', path: '/admin/lending/reports/origination/sanctions' },

  // Collections sub-reports
  { module: 'lending_reports', path: '/admin/lending/reports/collections/receipts' },
  { module: 'lending_reports', path: '/admin/lending/reports/collections/ageing' },
  { module: 'lending_reports', path: '/admin/lending/reports/collections/demand' },
  { module: 'lending_reports', path: '/admin/lending/reports/collections/dpd' },
  { module: 'lending_reports', path: '/admin/lending/reports/collections/recovery' },
  { module: 'lending_reports', path: '/admin/lending/reports/collections/forecast' },

  // NPA sub-reports
  { module: 'lending_reports', path: '/admin/lending/reports/npa/movement' },
  { module: 'lending_reports', path: '/admin/lending/reports/npa/classification' },
  { module: 'lending_reports', path: '/admin/lending/reports/npa/provisioning' },
  { module: 'lending_reports', path: '/admin/lending/reports/npa/writeoff' },
  { module: 'lending_reports', path: '/admin/lending/reports/npa/recovery' },

  // Treasury / regulatory / compliance / ops
  { module: 'lending_reports', path: '/admin/lending/reports/treasury/alm' },
  { module: 'lending_reports', path: '/admin/lending/reports/treasury/spread' },
  { module: 'lending_reports', path: '/admin/lending/reports/treasury/borrowing' },
  { module: 'lending_reports', path: '/admin/lending/reports/treasury/borrowings' },
  { module: 'lending_reports', path: '/admin/lending/reports/treasury/alm-gap' },
  { module: 'lending_reports', path: '/admin/lending/reports/treasury/irs' },
  { module: 'lending_reports', path: '/admin/lending/reports/treasury/maturity' },
  { module: 'lending_reports', path: '/admin/lending/reports/regulatory/crilc' },
  { module: 'lending_reports', path: '/admin/lending/reports/regulatory/rbi-returns' },
  { module: 'lending_reports', path: '/admin/lending/reports/compliance/nbs7' },
  { module: 'lending_reports', path: '/admin/lending/reports/compliance/crilc' },
  { module: 'lending_reports', path: '/admin/lending/reports/compliance/alm' },
  { module: 'lending_reports', path: '/admin/lending/reports/compliance/calendar' },
  { module: 'lending_reports', path: '/admin/lending/reports/operations/tat' },
  { module: 'lending_reports', path: '/admin/lending/reports/operations/sla' },
  { module: 'lending_reports', path: '/admin/lending/reports/operations/productivity' },
];

// ---------------------------------------------------------------------------
// NACH / AA / Credit — partner integrations. The list pages must mount even
// when the vendor calls are feature-flagged off (we surface a soft empty
// state). Status allowlists below tolerate the 4xx that comes back from a
// flagged-off integration.
const INTEGRATIONS_ROUTES: RouteSpec[] = [
  {
    module: 'nach',
    path: '/admin/lending/nach/batches',
    allowStatus: [
      { status: 403, urlSubstring: '/lending/nach' },
      { status: 404, urlSubstring: '/lending/nach' },
    ],
  },
  {
    module: 'nach',
    path: '/admin/lending/nach/batches/new',
    allowStatus: [
      { status: 403, urlSubstring: '/lending/nach' },
      { status: 404, urlSubstring: '/lending/nach' },
    ],
  },
  {
    module: 'nach',
    path: '/admin/lending/nach/retry',
    allowStatus: [
      { status: 403, urlSubstring: '/lending/nach' },
      { status: 404, urlSubstring: '/lending/nach' },
    ],
  },
  {
    module: 'aa',
    path: '/admin/lending/aa/consents',
    allowStatus: [
      { status: 403, urlSubstring: '/lending/aa' },
      { status: 404, urlSubstring: '/lending/aa' },
    ],
  },
  {
    module: 'aa',
    path: '/admin/lending/aa/consents/new',
    allowStatus: [
      { status: 403, urlSubstring: '/lending/aa' },
      { status: 404, urlSubstring: '/lending/aa' },
    ],
  },
  {
    module: 'aa',
    path: '/admin/lending/aa/fetched-data',
    allowStatus: [
      { status: 403, urlSubstring: '/lending/aa' },
      { status: 404, urlSubstring: '/lending/aa' },
    ],
  },
  {
    module: 'credit',
    path: '/admin/lending/credit',
    allowStatus: [
      { status: 403, urlSubstring: '/lending/credit' },
      { status: 404, urlSubstring: '/lending/credit' },
    ],
  },
  {
    module: 'credit',
    path: '/admin/lending/credit/request',
    allowStatus: [
      { status: 403, urlSubstring: '/lending/credit' },
      { status: 404, urlSubstring: '/lending/credit' },
    ],
  },
];

// ---------------------------------------------------------------------------
// Treasury (new admin/treasury namespace — `lending/treasury/*` is just a
// redirect shim).
const TREASURY_ROUTES: RouteSpec[] = [
  { module: 'treasury', path: '/admin/treasury' },
  { module: 'treasury', path: '/admin/treasury/lenders' },
  { module: 'treasury', path: '/admin/treasury/lenders/new' },
  { module: 'treasury', path: '/admin/treasury/borrowings' },
  { module: 'treasury', path: '/admin/treasury/borrowings/new' },
  { module: 'treasury', path: '/admin/treasury/source-of-funds' },
  { module: 'treasury', path: '/admin/treasury/alm' },
  { module: 'treasury', path: '/admin/treasury/alm/gap' },
  { module: 'treasury', path: '/admin/treasury/alm/irs' },
  { module: 'treasury', path: '/admin/treasury/risk-dashboard' },
  { module: 'treasury', path: '/admin/treasury/var-report' },
  { module: 'treasury', path: '/admin/treasury/liquidity-risk' },
  { module: 'treasury', path: '/admin/treasury/counterparty-risk' },
  { module: 'treasury', path: '/admin/treasury/stress-test' },
  { module: 'treasury', path: '/admin/treasury/investments' },
  { module: 'treasury', path: '/admin/treasury/investments/new' },
  { module: 'treasury', path: '/admin/treasury/investments/maturity' },
  { module: 'treasury', path: '/admin/treasury/investments/valuation' },
];

// ---------------------------------------------------------------------------
// Portal admin (the admin's view of the borrower portal — registrations,
// portal users).
const PORTAL_ADMIN_ROUTES: RouteSpec[] = [
  { module: 'portal_admin', path: '/admin/portal/users' },
  { module: 'portal_admin', path: '/admin/portal/registrations' },
];

const ALL_ROUTES: RouteSpec[] = [
  ...LENDING_ROUTES,
  ...IIF_ROUTES,
  ...LENDING_REPORTS,
  ...INTEGRATIONS_ROUTES,
  ...TREASURY_ROUTES,
  ...PORTAL_ADMIN_ROUTES,
];

test.describe('E2E › loan-module routes smoke', () => {
  for (const spec of ALL_ROUTES) {
    test(`${spec.module}: ${spec.path}`, async ({ page, consoleGate }) => {
      (spec.allowError ?? []).forEach((p) => consoleGate.allowError(p));
      (spec.allowStatus ?? []).forEach((a) => consoleGate.allowStatus(a.status, a.urlSubstring));

      const response = await page.goto(spec.path, { waitUntil: 'domcontentloaded' });
      expect(
        response?.status() ?? 0,
        `dev server returned non-200 for ${spec.path}`,
      ).toBeLessThan(400);

      await expect(page.locator('main, [role="main"]').first()).toBeVisible({ timeout: 8_000 });
      await expect(page).toHaveURL(new RegExp(spec.path.replace(/\//g, '\\/')));
    });
  }
});

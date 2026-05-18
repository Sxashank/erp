/**
 * Accounting-module smoke test.
 *
 * Covers finance, accounting, AP/AR, GST, TDS, and financial reports from the
 * admin user's point of view. The goal is to catch broken routes, dead create
 * buttons, failed API calls, uncaught console errors, and pages that navigate
 * back to the dashboard because a route is missing.
 */

import { expect, request as pwRequest, test as base, type Page } from '@playwright/test';

const env =
  (globalThis as { process?: { env?: Record<string, string | undefined> } }).process?.env ?? {};
const API_BASE = env.PLAYWRIGHT_API_BASE || 'http://localhost:8001/api/v1';
const ADMIN_USERNAME = env.UAT_ADMIN_USERNAME || 'krishna';
const ADMIN_PASSWORD = env.UAT_ADMIN_PASSWORD || 'ChangeMe123!';
const LIVE_BACKEND_ENABLED = env.PLAYWRIGHT_LIVE_BACKEND === '1';
const ROUTE_TIMEOUT_MS = 8000;

interface AuthBundle {
  accessToken: string;
  refreshToken: string;
  user: {
    organization_id?: string;
    organizationId?: string;
    permissions?: string[];
  };
}

interface RouteSpec {
  path: string;
  label: string;
  heading?: RegExp;
}

const ROUTES: RouteSpec[] = [
  { path: 'finance/financial-years', label: 'Financial Years' },
  { path: 'finance/financial-years/new', label: 'New Financial Year' },
  { path: 'finance/account-groups', label: 'Chart of Accounts' },
  { path: 'finance/account-groups/new', label: 'New Account Group' },
  { path: 'finance/accounts', label: 'Accounts' },
  { path: 'finance/accounts/new', label: 'New Account' },
  { path: 'finance/voucher-types', label: 'Voucher Types' },
  { path: 'finance/voucher-types/new', label: 'New Voucher Type' },
  { path: 'finance/vouchers', label: 'Vouchers' },
  { path: 'finance/vouchers/new', label: 'New Voucher' },
  { path: 'finance/voucher-templates', label: 'Voucher Templates' },
  { path: 'finance/voucher-templates/new', label: 'New Voucher Template' },
  { path: 'finance/recurring-vouchers', label: 'Recurring Vouchers' },
  { path: 'finance/recurring-vouchers/new', label: 'New Recurring Voucher' },
  { path: 'finance/year-end-closing', label: 'Year-End Closing' },

  { path: 'accounting/gl-postings', label: 'GL Postings' },
  { path: 'accounting/gl-postings/new', label: 'New GL Posting' },
  { path: 'accounting/gl-postings/approval', label: 'GL Posting Approval' },
  { path: 'accounting/periods', label: 'Period Management' },
  { path: 'accounting/period-close', label: 'Period Close' },
  { path: 'accounting/approval-matrix', label: 'Approval Matrix' },
  { path: 'accounting/approval-matrix/new', label: 'New Approval Matrix' },
  { path: 'accounting/pending-approvals', label: 'Pending Approvals' },

  { path: 'ap-ar/payment-terms', label: 'Payment Terms' },
  { path: 'ap-ar/payment-terms/new', label: 'New Payment Term' },
  { path: 'ap-ar/vendors', label: 'Vendors' },
  { path: 'ap-ar/vendors/new', label: 'New Vendor' },
  { path: 'ap-ar/customers', label: 'Customers' },
  { path: 'ap-ar/customers/new', label: 'New Customer' },
  { path: 'ap-ar/purchase-bills', label: 'Purchase Bills' },
  { path: 'ap-ar/purchase-bills/new', label: 'New Purchase Bill' },
  { path: 'ap-ar/sales-invoices', label: 'Sales Invoices' },
  { path: 'ap-ar/sales-invoices/new', label: 'New Sales Invoice' },
  { path: 'ap-ar/payments', label: 'Payments & Receipts' },
  { path: 'ap-ar/payments/new', label: 'New Payment or Receipt' },
  { path: 'ap-ar/bank-reconciliation', label: 'Bank Statements' },
  { path: 'ap-ar/bank-reconciliation/import', label: 'Bank Statement Import' },
  { path: 'ap-ar/bank-reconciliation/reconcile', label: 'Bank Reconciliation' },
  { path: 'ap-ar/bank-reconciliation/brs-report', label: 'BRS Report' },
  { path: 'ap-ar/aging-reports/ap', label: 'AP Aging Report' },
  { path: 'ap-ar/aging-reports/ar', label: 'AR Aging Report' },

  { path: 'gst/rates', label: 'GST Rates' },
  { path: 'gst/registrations', label: 'GST Registrations' },
  { path: 'gst/gstn', label: 'GSTN Dashboard' },
  { path: 'gst/gstn/login', label: 'GSTN Login' },
  { path: 'gst/gstn/gstr1', label: 'GSTR-1' },
  { path: 'gst/gstn/gstr3b', label: 'GSTR-3B' },
  { path: 'gst/gstn/itc', label: 'ITC Reconciliation' },

  { path: 'tds/sections', label: 'TDS Sections' },
  { path: 'tds/returns', label: 'TDS Returns' },
  { path: 'tds/challans', label: 'TDS Challans' },
  { path: 'tds/certificates', label: 'TDS Certificates' },

  { path: 'reports', label: 'Reports Dashboard' },
  { path: 'reports/trial-balance', label: 'Trial Balance' },
  { path: 'reports/profit-loss', label: 'Profit & Loss' },
  { path: 'reports/balance-sheet', label: 'Balance Sheet' },
  { path: 'reports/account-ledger', label: 'Account Ledger' },
  { path: 'reports/cash-flow-statement', label: 'Cash Flow Statement' },
  { path: 'reports/day-book', label: 'Day Book' },
  { path: 'reports/mis', label: 'MIS Reports' },
];

const CREATE_BUTTON_FLOWS = [
  {
    from: 'finance/accounts',
    button: /new account|create account|add account/i,
    expectedPath: /\/admin\/finance\/accounts\/new$/,
  },
  {
    from: 'finance/vouchers',
    button: /new voucher|create voucher|add voucher/i,
    expectedPath: /\/admin\/finance\/vouchers\/new$/,
  },
  {
    from: 'ap-ar/vendors',
    button: /new vendor|create vendor|add vendor/i,
    expectedPath: /\/admin\/ap-ar\/vendors\/new$/,
  },
  {
    from: 'ap-ar/customers',
    button: /new customer|create customer|add customer/i,
    expectedPath: /\/admin\/ap-ar\/customers\/new$/,
  },
  {
    from: 'ap-ar/purchase-bills',
    button: /new bill|create bill|add bill|purchase bill/i,
    expectedPath: /\/admin\/ap-ar\/purchase-bills\/new$/,
  },
  {
    from: 'ap-ar/sales-invoices',
    button: /new invoice|create invoice|add invoice|sales invoice/i,
    expectedPath: /\/admin\/ap-ar\/sales-invoices\/new$/,
  },
  {
    from: 'ap-ar/bank-reconciliation',
    button: /import/i,
    expectedPath: /\/admin\/ap-ar\/bank-reconciliation\/import$/,
  },
];

let cachedBundle: AuthBundle | null = null;

async function getAuthBundle(): Promise<AuthBundle> {
  if (cachedBundle) return cachedBundle;

  let lastFailure = '';
  for (const waitMs of [0, 5_000, 10_000, 30_000, 60_000]) {
    if (waitMs) {
      await new Promise((resolve) => setTimeout(resolve, waitMs));
    }

    const ctx = await pwRequest.newContext();
    const res = await ctx.post(`${API_BASE}/auth/login`, {
      data: { username: ADMIN_USERNAME, password: ADMIN_PASSWORD },
    });
    if (res.ok()) {
      const body = await res.json();
      await ctx.dispose();

      cachedBundle = {
        accessToken: body.access_token,
        refreshToken: body.refresh_token,
        user: body.user,
      };
      return cachedBundle;
    }

    const text = await res.text();
    lastFailure = `Login failed: ${res.status()} ${text}`;
    await ctx.dispose();
    if (res.status() !== 429) {
      break;
    }

    try {
      const payload = JSON.parse(text) as { retry_after_seconds?: number };
      const retryAfterSeconds = payload.retry_after_seconds ?? 60;
      await new Promise((resolve) => setTimeout(resolve, retryAfterSeconds * 1000));
    } catch {
      // Fall back to the next scheduled wait interval.
    }
  }

  throw new Error(lastFailure || 'Login failed');
}

const test = base.extend<{ authedPage: Page; authBundle: AuthBundle }>({
  // eslint-disable-next-line no-empty-pattern
  authBundle: async ({}, use) => {
    await use(await getAuthBundle());
  },

  authedPage: async ({ page, context, authBundle }, use) => {
    const orgId = authBundle.user.organization_id ?? authBundle.user.organizationId ?? null;
    await context.addInitScript(
      (bundle) => {
        window.localStorage.setItem('smfc-auth', JSON.stringify(bundle.auth));
        window.localStorage.setItem('smfc-organization', JSON.stringify(bundle.org));
      },
      {
        auth: {
          state: {
            accessToken: authBundle.accessToken,
            refreshToken: authBundle.refreshToken,
          },
          version: 0,
        },
        org: {
          state: {
            activeOrganizationId: orgId,
          },
          version: 0,
        },
      },
    );
    await use(page);
  },
});

async function installRouteGates(page: Page) {
  const errors: string[] = [];
  const failedResponses: { status: number; url: string }[] = [];

  page.on('console', (msg) => {
    if (msg.type() !== 'error') return;
    const text = msg.text();
    if (/ResizeObserver loop/i.test(text)) return;
    errors.push(text);
  });
  page.on('pageerror', (err) => {
    errors.push(`uncaught: ${err.message}`);
  });
  page.on('response', (res) => {
    const status = res.status();
    if (status < 400) return;
    const url = res.url();
    if (/\.(ico|png|jpg|jpeg|gif|svg|map|woff2?|ttf)(\?.*)?$/.test(url)) return;
    failedResponses.push({ status, url: url.replace(/^https?:\/\/[^/]+/, '') });
  });

  return { errors, failedResponses };
}

test.describe('accounting modules smoke', () => {
  test.describe.configure({ mode: 'serial' });
  test.setTimeout(120_000);
  test.skip(!LIVE_BACKEND_ENABLED, 'Set PLAYWRIGHT_LIVE_BACKEND=1 to run the live accounting smoke suite.');

  for (const spec of ROUTES) {
    test(`/admin/${spec.path}`, async ({ authedPage: page }, testInfo) => {
      testInfo.setTimeout(45_000);
      const gate = await installRouteGates(page);

      await page.goto(`/admin/${spec.path}`, { waitUntil: 'domcontentloaded' });
      try {
        await page.waitForLoadState('networkidle', { timeout: ROUTE_TIMEOUT_MS });
      } catch {
        // Long-polling/background polling should not block route smoke.
      }
      await page.waitForTimeout(200);

      await expect(page).not.toHaveURL(/\/admin\/?$/);
      await expect(page.getByRole('heading', { name: /404|page not found/i })).toHaveCount(0);

      const errMsg = gate.errors.length ? `console errors:\n  - ${gate.errors.join('\n  - ')}\n` : '';
      const netMsg = gate.failedResponses.length
        ? `failed responses:\n${gate.failedResponses
            .map((r) => `  - ${r.status} ${r.url}`)
            .join('\n')}\n`
        : '';
      expect(errMsg + netMsg, `route /admin/${spec.path}\n${errMsg}${netMsg}`).toBe('');
    });
  }

  for (const flow of CREATE_BUTTON_FLOWS) {
    test(`create/import button from /admin/${flow.from}`, async ({ authedPage: page }) => {
      await page.goto(`/admin/${flow.from}`, { waitUntil: 'domcontentloaded' });
      try {
        await page.waitForLoadState('networkidle', { timeout: ROUTE_TIMEOUT_MS });
      } catch {
        // Background queries may remain active.
      }

      const button = page.getByRole('button', { name: flow.button }).first();
      await expect(button).toBeVisible();
      await expect(button).toBeEnabled();
      await button.click();
      await expect(page).toHaveURL(flow.expectedPath);
    });
  }
});

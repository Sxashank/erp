/**
 * Operations-modules smoke test.
 *
 * Covers the non-lending operational admin surface with a real authenticated
 * session against the live backend. The goal is to catch broken routes,
 * dead create links, missing canonical paths, uncaught console errors, and
 * unexpected API failures across masters, DMS, notifications, workflow,
 * fixed assets, inventory, compliance, and fixed deposits.
 */

import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

import { chromium, expect, test as base, type Page } from '@playwright/test';

import { loginAsAdmin } from '../fixtures/auth';

const env =
  (globalThis as { process?: { env?: Record<string, string | undefined> } }).process?.env ?? {};
const ADMIN_USERNAME = env.UAT_ADMIN_USERNAME || 'krishna';
const ADMIN_PASSWORD = env.UAT_ADMIN_PASSWORD || 'ChangeMe123!';
const LIVE_BACKEND_ENABLED = env.PLAYWRIGHT_LIVE_BACKEND === '1';
const ROUTE_TIMEOUT_MS = 8_000;

interface RouteSpec {
  path: string;
  label: string;
}

const ROUTES: RouteSpec[] = [
  { path: 'organizations', label: 'Organizations' },
  { path: 'organizations/new', label: 'New Organization' },
  { path: 'units', label: 'Units' },
  { path: 'units/new', label: 'New Unit' },
  { path: 'departments', label: 'Departments' },
  { path: 'departments/new', label: 'New Department' },
  { path: 'designations', label: 'Designations' },
  { path: 'designations/new', label: 'New Designation' },
  { path: 'users', label: 'Users' },
  { path: 'users/new', label: 'New User' },
  { path: 'roles', label: 'Roles' },
  { path: 'roles/new', label: 'New Role' },

  { path: 'notifications', label: 'Notifications' },
  { path: 'notifications/settings', label: 'Notification Settings' },
  { path: 'notifications/templates', label: 'Notification Templates' },
  { path: 'notifications/templates/create', label: 'Create Notification Template' },
  { path: 'notifications/logs', label: 'Notification Logs' },

  { path: 'dms', label: 'DMS Dashboard' },
  { path: 'dms/folders', label: 'Folder Browser' },
  { path: 'dms/upload', label: 'Document Upload' },
  { path: 'dms/search', label: 'Document Search' },
  { path: 'dms/tags', label: 'Tag Management' },

  { path: 'workflow/definitions', label: 'Workflow Definitions' },
  { path: 'workflow/definitions/new', label: 'Create Workflow' },
  { path: 'workflow/tasks', label: 'Workflow Tasks' },
  { path: 'workflow/instances', label: 'Workflow Instances' },

  { path: 'fixed-assets/categories', label: 'Asset Categories' },
  { path: 'fixed-assets/categories/new', label: 'New Asset Category' },
  { path: 'fixed-assets/assets', label: 'Asset Register' },
  { path: 'fixed-assets/assets/new', label: 'New Fixed Asset' },
  { path: 'fixed-assets/depreciation', label: 'Depreciation Runs' },
  { path: 'fixed-assets/depreciation/run', label: 'Run Depreciation' },
  { path: 'fixed-assets/verification', label: 'Physical Verification' },
  { path: 'fixed-assets/verification/new', label: 'New Verification Schedule' },
  { path: 'fixed-assets/disposal', label: 'Disposal Register' },
  { path: 'fixed-assets/reports', label: 'Fixed Asset Reports' },

  { path: 'inventory', label: 'Inventory Dashboard' },
  { path: 'inventory/categories', label: 'Item Categories' },
  { path: 'inventory/categories/new', label: 'New Item Category' },
  { path: 'inventory/items', label: 'Items' },
  { path: 'inventory/items/new', label: 'New Item' },
  { path: 'inventory/warehouses', label: 'Warehouses' },
  { path: 'inventory/warehouses/new', label: 'New Warehouse' },
  { path: 'inventory/stock-in', label: 'Stock In' },
  { path: 'inventory/stock-out', label: 'Stock Out' },
  { path: 'inventory/stock-transfer', label: 'Stock Transfer' },
  { path: 'inventory/stock-adjustment', label: 'Stock Adjustment' },
  { path: 'inventory/reports', label: 'Stock Reports' },
  { path: 'inventory/valuation', label: 'Inventory Valuation' },

  { path: 'compliance', label: 'Compliance Dashboard' },
  { path: 'compliance/items', label: 'Compliance Items' },
  { path: 'compliance/items/new', label: 'New Compliance Item' },

  { path: 'fixed-deposits/dashboard', label: 'FD Dashboard' },
  { path: 'fixed-deposits/interest', label: 'FD Interest' },
  { path: 'fixed-deposits/products', label: 'FD Products' },
  { path: 'fixed-deposits/products/new', label: 'New FD Product' },
  { path: 'fixed-deposits', label: 'Fixed Deposits' },
  { path: 'fixed-deposits/new', label: 'New Fixed Deposit' },

  { path: 'treasury', label: 'Treasury Dashboard' },
  { path: 'treasury/lenders', label: 'Treasury Lenders' },
  { path: 'treasury/lenders/new', label: 'New Treasury Lender' },
  { path: 'treasury/borrowings', label: 'Borrowings' },
  { path: 'treasury/borrowings/new', label: 'New Borrowing' },
  { path: 'treasury/source-of-funds', label: 'Source Of Funds' },
  { path: 'treasury/alm', label: 'ALM Dashboard' },
  { path: 'treasury/alm/gap', label: 'Gap Analysis' },
  { path: 'treasury/alm/irs', label: 'Interest Rate Risk' },
  { path: 'treasury/liquidity-risk', label: 'Liquidity Risk' },
  { path: 'treasury/counterparty-risk', label: 'Counterparty Risk' },
  { path: 'treasury/stress-test', label: 'Stress Test' },
  { path: 'treasury/investments', label: 'Investments' },
  { path: 'treasury/investments/new', label: 'New Investment' },
  { path: 'treasury/investments/maturity', label: 'Investment Maturity' },

  { path: 'hris', label: 'HRIS Dashboard' },
  { path: 'hris/employees', label: 'Employees' },
  { path: 'hris/employees/new', label: 'New Employee' },
  { path: 'hris/shifts', label: 'Shifts' },
  { path: 'hris/shifts/new', label: 'New Shift' },
  { path: 'hris/holidays', label: 'Holiday Calendars' },
  { path: 'hris/holidays/new', label: 'New Holiday Calendar' },
  { path: 'hris/leave-types', label: 'Leave Types' },
  { path: 'hris/leave-types/new', label: 'New Leave Type' },
  { path: 'hris/leave-applications', label: 'Leave Applications' },
  { path: 'hris/leave-applications/new', label: 'New Leave Application' },
  { path: 'hris/attendance', label: 'Attendance' },
  { path: 'hris/attendance/regularization', label: 'Attendance Regularization' },
  { path: 'hris/attendance/process', label: 'Attendance Process' },
  { path: 'hris/separation', label: 'Separation' },
  { path: 'hris/separation/new', label: 'Initiate Separation' },
  { path: 'hris/training', label: 'Training Programs' },
  { path: 'hris/training/new', label: 'New Training Program' },
  { path: 'hris/performance/cycles', label: 'Appraisal Cycles' },
  { path: 'hris/performance/goals', label: 'Goal Setting' },
  { path: 'hris/performance/self-appraisal', label: 'Self Appraisal' },
  { path: 'hris/performance/manager-review', label: 'Manager Review' },

  { path: 'payroll/components', label: 'Salary Components' },
  { path: 'payroll/components/new', label: 'New Salary Component' },
  { path: 'payroll/structures', label: 'Salary Structures' },
  { path: 'payroll/structures/new', label: 'New Salary Structure' },
  { path: 'payroll/employee-salary', label: 'Employee Salaries' },
  { path: 'payroll/statutory', label: 'Statutory Setup' },
  { path: 'payroll/statutory/new', label: 'New Statutory Setup' },
  { path: 'payroll/batches', label: 'Payroll Batches' },
  { path: 'payroll/batches/new', label: 'New Payroll Batch' },

  { path: 'procurement/rfq', label: 'RFQ' },
  { path: 'procurement/rfq/new', label: 'New RFQ' },
  { path: 'procurement/po', label: 'Purchase Orders' },
  { path: 'procurement/po/new', label: 'New Purchase Order' },
  { path: 'procurement/po/approval', label: 'PO Approval' },
  { path: 'procurement/grn', label: 'GRN' },
  { path: 'procurement/grn/new', label: 'New GRN' },

  { path: 'reports/scheduler', label: 'Report Scheduler' },
  { path: 'reports/history', label: 'Report History' },

  { path: 'kyc/ckyc/search', label: 'CKYC Search' },
  { path: 'kyc/ckyc/download', label: 'CKYC Download' },
  { path: 'kyc/ckyc/status', label: 'CKYC Status' },
  { path: 'kyc/ckyc/upload', label: 'CKYC Upload' },
  { path: 'kyc/documents', label: 'KYC Documents' },
  { path: 'kyc/documents/upload', label: 'KYC Document Upload' },
  { path: 'kyc/checklist', label: 'KYC Checklist' },
  { path: 'kyc/credit-bureau', label: 'Credit Bureau' },
  { path: 'kyc/credit-bureau/pull', label: 'Credit Bureau Pull' },
  { path: 'kyc/credit-bureau/history', label: 'Credit Score History' },

  { path: 'bi/dashboards', label: 'BI Dashboards' },
  { path: 'bi/dashboards/new', label: 'New BI Dashboard' },
  { path: 'bi/chart-definitions', label: 'Chart Definitions' },
  { path: 'bi/chart-definitions/new', label: 'New Chart Definition' },
  { path: 'bi/data-sources', label: 'Data Sources' },
  { path: 'bi/data-sources/new', label: 'New Data Source' },

  { path: 'settings/integrations', label: 'Integration Settings' },

  { path: 'legal', label: 'Legal Dashboard' },
  { path: 'legal/law-firms', label: 'Law Firms' },
  { path: 'legal/advocates', label: 'Advocates' },
  { path: 'legal/cases', label: 'Legal Cases' },
  { path: 'legal/notices', label: 'Legal Notices' },
  { path: 'legal/expenses', label: 'Legal Expenses' },
];

const CREATE_BUTTON_FLOWS = [
  {
    from: 'organizations',
    button: /new organization|add organization|create organization/i,
    expectedPath: /\/admin\/organizations\/new$/,
  },
  {
    from: 'users',
    button: /new user|add user|create user/i,
    expectedPath: /\/admin\/users\/new$/,
  },
  {
    from: 'roles',
    button: /new role|add role|create role/i,
    expectedPath: /\/admin\/roles\/new$/,
  },
  {
    from: 'notifications/templates',
    button: /create template|new template/i,
    expectedPath: /\/admin\/notifications\/templates\/create$/,
  },
  {
    from: 'workflow/definitions',
    button: /create workflow|new workflow/i,
    expectedPath: /\/admin\/workflow\/definitions\/new$/,
  },
  {
    from: 'fixed-assets/categories',
    button: /new category|add category|create category/i,
    expectedPath: /\/admin\/fixed-assets\/categories\/new$/,
  },
  {
    from: 'fixed-assets/assets',
    button: /new asset|add asset|create asset/i,
    expectedPath: /\/admin\/fixed-assets\/assets\/new$/,
  },
  {
    from: 'fixed-assets/verification',
    button: /new verification|create schedule|new schedule/i,
    expectedPath: /\/admin\/fixed-assets\/verification\/new$/,
  },
  {
    from: 'inventory/categories',
    button: /add category|new category|create category/i,
    expectedPath: /\/admin\/inventory\/categories\/new$/,
  },
  {
    from: 'inventory/items',
    button: /add item|new item|create item/i,
    expectedPath: /\/admin\/inventory\/items\/new$/,
  },
  {
    from: 'inventory/warehouses',
    button: /add warehouse|new warehouse|create warehouse/i,
    expectedPath: /\/admin\/inventory\/warehouses\/new$/,
  },
  {
    from: 'fixed-deposits/products',
    button: /add product|new product|create product/i,
    expectedPath: /\/admin\/fixed-deposits\/products\/new$/,
  },
  {
    from: 'fixed-deposits',
    button: /new fixed deposit|create fixed deposit|new deposit/i,
    expectedPath: /\/admin\/fixed-deposits\/new$/,
  },
  {
    from: 'treasury/lenders',
    button: /new lender|add lender|create lender/i,
    expectedPath: /\/admin\/treasury\/lenders\/new$/,
  },
  {
    from: 'treasury/borrowings',
    button: /new borrowing|add borrowing|create borrowing/i,
    expectedPath: /\/admin\/treasury\/borrowings\/new$/,
  },
  {
    from: 'hris/employees',
    button: /new employee|add employee|create employee/i,
    expectedPath: /\/admin\/hris\/employees\/new$/,
  },
  {
    from: 'hris/shifts',
    button: /new shift|add shift|create shift/i,
    expectedPath: /\/admin\/hris\/shifts\/new$/,
  },
  {
    from: 'hris/holidays',
    button: /new holiday|add holiday|create holiday/i,
    expectedPath: /\/admin\/hris\/holidays\/new$/,
  },
  {
    from: 'hris/leave-types',
    button: /new leave type|add leave type|create leave type/i,
    expectedPath: /\/admin\/hris\/leave-types\/new$/,
  },
  {
    from: 'hris/leave-applications',
    button: /new leave application|apply leave|create leave application/i,
    expectedPath: /\/admin\/hris\/leave-applications\/new$/,
  },
  {
    from: 'hris/separation',
    button: /new separation|initiate separation/i,
    expectedPath: /\/admin\/hris\/separation\/new$/,
  },
  {
    from: 'hris/training',
    button: /new training|add training|create training/i,
    expectedPath: /\/admin\/hris\/training\/new$/,
  },
  {
    from: 'payroll/components',
    button: /new component|add component|create component/i,
    expectedPath: /\/admin\/payroll\/components\/new$/,
  },
  {
    from: 'payroll/structures',
    button: /new structure|add structure|create structure/i,
    expectedPath: /\/admin\/payroll\/structures\/new$/,
  },
  {
    from: 'payroll/statutory',
    button: /new statutory|add statutory|create statutory/i,
    expectedPath: /\/admin\/payroll\/statutory\/new$/,
  },
  {
    from: 'payroll/batches',
    button: /new batch|add batch|create batch/i,
    expectedPath: /\/admin\/payroll\/batches\/new$/,
  },
  {
    from: 'procurement/rfq',
    button: /new rfq|create rfq|add rfq/i,
    expectedPath: /\/admin\/procurement\/rfq\/new$/,
  },
  {
    from: 'procurement/po',
    button: /new purchase order|create purchase order|new po/i,
    expectedPath: /\/admin\/procurement\/po\/new$/,
  },
  {
    from: 'procurement/grn',
    button: /new grn|create grn|add grn/i,
    expectedPath: /\/admin\/procurement\/grn\/new$/,
  },
  {
    from: 'bi/dashboards',
    button: /new dashboard|create dashboard|add dashboard/i,
    expectedPath: /\/admin\/bi\/dashboards\/new$/,
  },
  {
    from: 'bi/chart-definitions',
    button: /new chart|create chart|add chart/i,
    expectedPath: /\/admin\/bi\/chart-definitions\/new$/,
  },
  {
    from: 'bi/data-sources',
    button: /new data source|create data source|add data source/i,
    expectedPath: /\/admin\/bi\/data-sources\/new$/,
  },
];

const test = base.extend<{}, { storageStatePath: string }>({
  storageStatePath: [
    async (_args, use) => {
      const dir = mkdtempSync(join(tmpdir(), 'operations-smoke-'));
      const path = join(dir, 'storage.json');
      const browser = await chromium.launch();
      const ctx = await browser.newContext({
        baseURL: env.PLAYWRIGHT_BASE_URL || 'http://localhost:5176',
      });
      const page = await ctx.newPage();
      await loginAsAdmin(page, {
        username: ADMIN_USERNAME,
        password: ADMIN_PASSWORD,
      });
      await ctx.storageState({ path });
      await ctx.close();
      await browser.close();
      await use(path);
    },
    { scope: 'worker' },
  ],

  context: async ({ browser, storageStatePath }, use) => {
    const ctx = await browser.newContext({
      storageState: storageStatePath,
      baseURL: env.PLAYWRIGHT_BASE_URL || 'http://localhost:5176',
    });
    await use(ctx);
    await ctx.close();
  },
});

async function installRouteGates(page: Page) {
  const errors: string[] = [];
  const failedResponses: { status: number; url: string }[] = [];
  const failedRequests: { errorText: string; url: string }[] = [];

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
  page.on('requestfailed', (request) => {
    const url = request.url();
    const errorText = request.failure()?.errorText ?? 'request failed';
    if (/\.(ico|png|jpg|jpeg|gif|svg|map|woff2?|ttf)(\?.*)?$/.test(url)) return;
    failedRequests.push({
      errorText,
      url: url.replace(/^https?:\/\/[^/]+/, ''),
    });
  });

  return { errors, failedResponses, failedRequests };
}

test.describe('operations modules smoke', () => {
  test.describe.configure({ mode: 'serial' });
  test.setTimeout(120_000);
  test.skip(
    !LIVE_BACKEND_ENABLED,
    'Set PLAYWRIGHT_LIVE_BACKEND=1 to run the live operations smoke suite.',
  );

  for (const spec of ROUTES) {
    test(`/admin/${spec.path}`, async ({ page }, testInfo) => {
      testInfo.setTimeout(45_000);
      const gate = await installRouteGates(page);

      await page.goto(`/admin/${spec.path}`, { waitUntil: 'domcontentloaded' });
      try {
        await page.waitForLoadState('networkidle', { timeout: ROUTE_TIMEOUT_MS });
      } catch {
        // Background polling should not block route smoke.
      }
      await page.waitForTimeout(200);

      await expect(page.locator('#root')).toBeVisible();
      await expect(page).not.toHaveURL(/\/login$/);
      await expect(page).not.toHaveURL(/\/admin\/?$/);
      await expect(page.getByRole('heading', { name: /404|page not found/i })).toHaveCount(0);

      const errMsg = gate.errors.length
        ? `console errors:\n  - ${gate.errors.join('\n  - ')}\n`
        : '';
      const netMsg = gate.failedResponses.length
        ? `failed responses:\n${gate.failedResponses
            .map((r) => `  - ${r.status} ${r.url}`)
            .join('\n')}\n`
        : '';
      const reqMsg = gate.failedRequests.length
        ? `failed requests:\n${gate.failedRequests
            .map((r) => `  - ${r.errorText} ${r.url}`)
            .join('\n')}\n`
        : '';
      expect(
        errMsg + netMsg + reqMsg,
        `route /admin/${spec.path}\n${errMsg}${netMsg}${reqMsg}`,
      ).toBe('');
    });
  }

  for (const flow of CREATE_BUTTON_FLOWS) {
    test(`create button from /admin/${flow.from}`, async ({ page }) => {
      await page.goto(`/admin/${flow.from}`, { waitUntil: 'domcontentloaded' });
      try {
        await page.waitForLoadState('networkidle', { timeout: ROUTE_TIMEOUT_MS });
      } catch {
        // Background queries may remain active.
      }
      await expect(page).not.toHaveURL(/\/login$/);

      const button = page.getByRole('button', { name: flow.button }).first();
      await expect(button).toBeVisible();
      await expect(button).toBeEnabled();
      await button.click();
      await expect(page).toHaveURL(flow.expectedPath);
    });
  }
});

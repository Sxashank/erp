/**
 * Taxation-module smoke test.
 *
 * Covers GST and TDS routes added in the recent tax hardening slices. Uses a
 * real login against the backend API, then verifies route rendering, create
 * flows, and absence of console / network failures.
 */

import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

import { chromium, expect, test as base, type Page } from '@playwright/test';

import { loginAsAdmin } from '../fixtures/auth';

const env =
  (globalThis as { process?: { env?: Record<string, string | undefined> } }).process?.env ?? {};
const LIVE_BACKEND_ENABLED = env.PLAYWRIGHT_LIVE_BACKEND === '1';
const ROUTE_TIMEOUT_MS = 8000;

interface RouteSpec {
  path: string;
  label: string;
}

const ROUTES: RouteSpec[] = [
  { path: 'gst/rates', label: 'GST Rates' },
  { path: 'gst/rates/new', label: 'New GST Rate' },
  { path: 'gst/registrations', label: 'GST Registrations' },
  { path: 'gst/registrations/new', label: 'New GST Registration' },
  { path: 'gst/hsn-sac', label: 'HSN/SAC' },
  { path: 'gst/hsn-sac/new', label: 'New HSN/SAC' },
  { path: 'gst/gstn', label: 'GSTN Dashboard' },
  { path: 'gst/gstn/login', label: 'GSTN Login' },
  { path: 'gst/gstn/gstr1', label: 'GSTR-1 Filing' },
  { path: 'gst/gstn/gstr3b', label: 'GSTR-3B Filing' },
  { path: 'gst/gstn/itc', label: 'ITC Reconciliation' },
  { path: 'tds/sections', label: 'TDS Sections' },
  { path: 'tds/sections/new', label: 'New TDS Section' },
  { path: 'tds/entries', label: 'TDS Entries' },
  { path: 'tds/entries/new', label: 'New TDS Entry' },
  { path: 'tds/returns', label: 'TDS Returns' },
  { path: 'tds/returns/create', label: 'Create TDS Return' },
  { path: 'tds/challans', label: 'TDS Challans' },
  { path: 'tds/challans/create', label: 'Create TDS Challan' },
  { path: 'tds/certificates', label: 'TDS Certificates' },
  { path: 'tds/certificates/generate', label: 'Generate TDS Certificates' },
];

const CREATE_BUTTON_FLOWS = [
  {
    from: 'gst/registrations',
    button: /add gst registration/i,
    expectedPath: /\/admin\/gst\/registrations\/new$/,
  },
  {
    from: 'gst/hsn-sac',
    button: /add hsn\s*\/\s*sac/i,
    expectedPath: /\/admin\/gst\/hsn-sac\/new$/,
  },
  {
    from: 'tds/entries',
    button: /add tds entry/i,
    expectedPath: /\/admin\/tds\/entries\/new$/,
  },
  {
    from: 'tds/returns',
    button: /create return/i,
    expectedPath: /\/admin\/tds\/returns\/create$/,
  },
  {
    from: 'tds/challans',
    button: /create challan/i,
    expectedPath: /\/admin\/tds\/challans\/create$/,
  },
  {
    from: 'tds/certificates',
    button: /generate certificates/i,
    expectedPath: /\/admin\/tds\/certificates\/generate$/,
  },
];

const test = base.extend<{ authedPage: Page }, { storageStatePath: string }>({
  storageStatePath: [
    async ({ browserName: _browserName }, use) => {
      const dir = mkdtempSync(join(tmpdir(), 'taxation-smoke-'));
      const path = join(dir, 'storage.json');
      const browser = await chromium.launch();
      const ctx = await browser.newContext();
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
    const ctx = await browser.newContext({ storageState: storageStatePath });
    await use(ctx);
    await ctx.close();
  },
  authedPage: async ({ page }, use) => {
    await use(page);
  },
});

async function installRouteGates(page: Page) {
  const errors: string[] = [];
  const failedResponses: { status: number; url: string }[] = [];

  page.on('console', (msg) => {
    if (msg.type() !== 'error') return;
    errors.push(msg.text());
  });
  page.on('pageerror', (error) => {
    errors.push(`uncaught: ${error.message}`);
  });
  page.on('response', (response) => {
    const status = response.status();
    if (status < 400) return;
    const url = response.url();
    if (/\.(ico|png|jpg|jpeg|gif|svg|map|woff2?|ttf)(\?.*)?$/.test(url)) return;
    failedResponses.push({ status, url: url.replace(/^https?:\/\/[^/]+/, '') });
  });

  return { errors, failedResponses };
}

async function expectNotAuthLogin(page: Page) {
  await expect.poll(() => new URL(page.url()).pathname, { timeout: 5_000 }).not.toBe('/login');
}

test.describe('taxation modules smoke', () => {
  test.describe.configure({ mode: 'serial' });
  test.skip(
    !LIVE_BACKEND_ENABLED,
    'Set PLAYWRIGHT_LIVE_BACKEND=1 to run the live taxation smoke suite.',
  );

  for (const route of ROUTES) {
    test(`/admin/${route.path}`, async ({ authedPage: page }, testInfo) => {
      testInfo.setTimeout(45_000);
      const gate = await installRouteGates(page);

      await page.goto(`/admin/${route.path}`, { waitUntil: 'domcontentloaded' });
      try {
        await page.waitForLoadState('networkidle', { timeout: ROUTE_TIMEOUT_MS });
      } catch {
        // Background polling should not fail smoke coverage.
      }
      await page.waitForTimeout(200);

      await expectNotAuthLogin(page);
      await expect(page).not.toHaveURL(/\/admin\/?$/);
      await expect(page.getByRole('heading', { name: /404|page not found/i })).toHaveCount(0);

      const errMsg = gate.errors.length
        ? `console errors:\n  - ${gate.errors.join('\n  - ')}\n`
        : '';
      const netMsg = gate.failedResponses.length
        ? `failed responses:\n${gate.failedResponses
            .map((item) => `  - ${item.status} ${item.url}`)
            .join('\n')}\n`
        : '';
      expect(errMsg + netMsg, `route /admin/${route.path}\n${errMsg}${netMsg}`).toBe('');
    });
  }

  for (const flow of CREATE_BUTTON_FLOWS) {
    test(`create button from /admin/${flow.from}`, async ({ authedPage: page }) => {
      await page.goto(`/admin/${flow.from}`, { waitUntil: 'domcontentloaded' });
      try {
        await page.waitForLoadState('networkidle', { timeout: ROUTE_TIMEOUT_MS });
      } catch {
        // Background requests are allowed.
      }

      await expectNotAuthLogin(page);
      const button = page.getByRole('button', { name: flow.button }).first();
      await expect(button).toBeVisible();
      await expect(button).toBeEnabled();
      await button.click();
      await expect(page).toHaveURL(flow.expectedPath);
    });
  }
});

import { expect, request as pwRequest, test as base, type APIRequestContext, type Locator, type Page } from '@playwright/test';

const env =
  (globalThis as { process?: { env?: Record<string, string | undefined> } }).process?.env ?? {};
const API_BASE = env.PLAYWRIGHT_API_BASE || 'http://localhost:8001/api/v1';
const ADMIN_USERNAME = env.UAT_ADMIN_USERNAME || 'krishna';
const ADMIN_PASSWORD = env.UAT_ADMIN_PASSWORD || 'ChangeMe123!';
const LIVE_BACKEND_ENABLED = env.PLAYWRIGHT_LIVE_BACKEND === '1';

interface BootBundle {
  accessToken: string;
  refreshToken: string;
  organizationId: string;
  organizationName: string;
  financialYearId: string;
  financialYearName: string;
  financialYearValue: string;
  quarterFrom: string;
  quarterTo: string;
  deductionDate: string;
  assessmentYear: string;
}

interface TestFixtures {
  authedPage: Page;
  bootBundle: BootBundle;
}

interface OrganizationOption {
  id: string;
  name?: string;
  is_primary?: boolean;
  isPrimary?: boolean;
}

interface FinancialYearOption {
  id: string;
  name?: string;
  code?: string;
  start_date?: string;
  startDate?: string;
  end_date?: string;
  endDate?: string;
  is_current?: boolean;
  isCurrent?: boolean;
}

let cachedBundle: BootBundle | null = null;

function isoDate(date: Date) {
  return date.toISOString().slice(0, 10);
}

function escapeRegExp(value: string) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function getFinancialYearValue(startDate: string, endDate: string) {
  const startYear = new Date(startDate).getUTCFullYear();
  const endYear = new Date(endDate).getUTCFullYear();
  return `${startYear}-${String(endYear).slice(-2)}`;
}

function getAssessmentYear(financialYearValue: string) {
  const [startYearText] = financialYearValue.split('-');
  const startYear = Number(startYearText);
  return `${startYear + 1}-${String(startYear + 2).slice(-2)}`;
}

function getQuarterWindow(startDate: string) {
  const fromDate = new Date(startDate);
  const startYear = fromDate.getUTCFullYear();
  const startMonth = fromDate.getUTCMonth();
  const quarterFrom = isoDate(new Date(Date.UTC(startYear, startMonth, 1)));
  const quarterMid = isoDate(new Date(Date.UTC(startYear, startMonth + 1, 15)));
  const quarterTo = isoDate(new Date(Date.UTC(startYear, startMonth + 3, 0)));
  return { quarterFrom, quarterTo, quarterMid };
}

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
    lastFailure = `Login failed: ${response.status()} ${responseText}`;
    if (response.status() !== 429) {
      break;
    }

    try {
      const payload = JSON.parse(responseText) as { retry_after_seconds?: number };
      const retryAfterSeconds = payload.retry_after_seconds ?? 60;
      await new Promise((resolve) => setTimeout(resolve, retryAfterSeconds * 1000));
    } catch {
      // Fall back to the next scheduled wait interval.
    }
  }

  throw new Error(lastFailure || 'Login failed');
}

async function getBootBundle(): Promise<BootBundle> {
  if (cachedBundle) {
    return cachedBundle;
  }

  const ctx = await pwRequest.newContext();
  const auth = await loginWithBackoff(ctx);
  const headers = { Authorization: `Bearer ${auth.access_token}` };

  const organizationsResponse = await ctx.get(`${API_BASE}/organizations`, {
    params: { page_size: 10 },
    headers,
  });
  if (!organizationsResponse.ok()) {
    throw new Error(`Organizations fetch failed: ${organizationsResponse.status()} ${await organizationsResponse.text()}`);
  }
  const organizationsBody = await organizationsResponse.json();
  const organizations: OrganizationOption[] = Array.isArray(organizationsBody.items) ? organizationsBody.items : [];
  const organization = organizations.find((item) => item.is_primary || item.isPrimary) ?? organizations[0];
  if (!organization) {
    throw new Error('No organization available for Playwright tax workflows');
  }

  const financialYearsResponse = await ctx.get(`${API_BASE}/financial-years`, {
    params: { organization_id: organization.id, page_size: 20, include_inactive: false },
    headers,
  });
  if (!financialYearsResponse.ok()) {
    throw new Error(`Financial years fetch failed: ${financialYearsResponse.status()} ${await financialYearsResponse.text()}`);
  }
  const financialYearsBody = await financialYearsResponse.json();
  const financialYears: FinancialYearOption[] = Array.isArray(financialYearsBody.items) ? financialYearsBody.items : [];
  const financialYear = financialYears.find((item) => item.is_current || item.isCurrent) ?? financialYears[0];
  if (!financialYear) {
    throw new Error('No financial year available for Playwright tax workflows');
  }

  const financialYearStart = financialYear.start_date ?? financialYear.startDate;
  const financialYearEnd = financialYear.end_date ?? financialYear.endDate;
  if (!financialYearStart || !financialYearEnd) {
    throw new Error('Financial year start and end dates are required for Playwright tax workflows');
  }

  const financialYearValue = getFinancialYearValue(financialYearStart, financialYearEnd);
  const { quarterFrom, quarterTo, quarterMid } = getQuarterWindow(financialYearStart);

  const bundle: BootBundle = {
    accessToken: auth.access_token,
    refreshToken: auth.refresh_token,
    organizationId: organization.id,
    organizationName: organization.name ?? organization.id,
    financialYearId: financialYear.id,
    financialYearName: financialYear.name ?? financialYear.code ?? financialYear.id,
    financialYearValue,
    quarterFrom,
    quarterTo,
    deductionDate: quarterMid,
    assessmentYear: getAssessmentYear(financialYearValue),
  };
  cachedBundle = bundle;

  await ctx.dispose();
  return bundle;
}

const test = base.extend<TestFixtures>({
  bootBundle: async ({ browserName: _browserName }, use) => {
    await use(await getBootBundle());
  },
  authedPage: async ({ page, context, bootBundle }, use) => {
    await context.addInitScript((bundle) => {
      window.localStorage.setItem(
        'smfc-auth',
        JSON.stringify({
          state: {
            accessToken: bundle.accessToken,
            refreshToken: bundle.refreshToken,
          },
          version: 0,
        }),
      );
      window.localStorage.setItem(
        'smfc-organization',
        JSON.stringify({
          state: {
            activeOrganizationId: bundle.organizationId,
          },
          version: 0,
        }),
      );
    }, bootBundle);
    await use(page);
  },
});

async function waitForPageIdle(page: Page) {
  try {
    await page.waitForLoadState('networkidle', { timeout: 10_000 });
  } catch {
    await page.waitForTimeout(250);
  }
}

async function openSelectOption(trigger: Locator, optionText: string) {
  const page = trigger.page();
  await trigger.click();
  const listbox = page
    .getByRole('listbox')
    .filter({ has: page.locator('[role="option"]') })
    .last();
  await expect(listbox).toBeVisible();
  const option = listbox
    .getByRole('option', { name: new RegExp(escapeRegExp(optionText), 'i') })
    .first();
  await expect(option).toBeVisible();
  await option.evaluate((element) => {
    if (element instanceof HTMLElement) {
      element.scrollIntoView({ block: 'nearest' });
      element.click();
    }
  });
}

test.describe('taxation workflows', () => {
  test.describe.configure({ mode: 'serial' });
  test.skip(!LIVE_BACKEND_ENABLED, 'Set PLAYWRIGHT_LIVE_BACKEND=1 to run the live taxation workflows.');

  const suffix = Date.now().toString().slice(-6);
  const gstRateCode = `GST${suffix}`;
  const gstRateName = `GST ${suffix}`;
  const gstRegistrationName = `Tax Workflow ${suffix}`;
  const gstin = `27ABCDE${suffix.slice(0, 4)}F1Z${suffix.slice(-1)}`;
  const hsnCode = `99${suffix}`;
  const hsnDescription = `Playwright HSN ${suffix}`;
  const tdsSectionCode = `26Q-${suffix}`;
  const tdsSectionName = `Playwright TDS ${suffix}`;
  const deducteeName = `Deductee ${suffix}`;
  const deducteePan = `ABCDE${suffix.slice(0, 4)}L`;
  const deductorTan = `ABCD${suffix.slice(0, 5)}E`;
  const challanNumber = `CH${suffix}`;
  const bsrCode = `${suffix.slice(0, 6)}`;
  const filingAckNumber = `ACK${suffix}`;

  test('completes the GST manual workflow end to end', async ({ authedPage: page, bootBundle }) => {
    test.setTimeout(180_000);

    await page.goto('/admin/gst/rates/new', { waitUntil: 'domcontentloaded' });
    await page.getByLabel('Code').fill(gstRateCode);
    await page.getByLabel('Name').fill(gstRateName);
    const rateInputs = page.locator('input[type="number"]');
    await rateInputs.nth(0).fill('18');
    await rateInputs.nth(1).fill('9');
    await rateInputs.nth(2).fill('9');
    await rateInputs.nth(3).fill('18');
    await rateInputs.nth(4).fill('0');
    await Promise.all([
      page.waitForURL(/\/admin\/gst\/rates$/),
      page.getByRole('button', { name: 'Save Rate' }).click(),
    ]);
    await expect(page.getByText(gstRateCode)).toBeVisible();

    await page.goto('/admin/gst/registrations/new', { waitUntil: 'domcontentloaded' });
    await openSelectOption(page.getByRole('combobox').nth(0), bootBundle.organizationName);
    await page.getByLabel('GSTIN').fill(gstin);
    await page.getByLabel('Legal name').fill(gstRegistrationName);
    await page.getByLabel('State code').fill('27');
    await page.getByLabel('State name').fill('Maharashtra');
    await Promise.all([
      page.waitForURL(/\/admin\/gst\/registrations$/),
      page.getByRole('button', { name: 'Save Registration' }).click(),
    ]);
    await expect(page.getByText(gstin)).toBeVisible();

    await page.goto('/admin/gst/hsn-sac/new', { waitUntil: 'domcontentloaded' });
    await page.getByLabel('Code').fill(hsnCode);
    await page.getByLabel('Description').fill(hsnDescription);
    await openSelectOption(page.getByRole('combobox').nth(1), gstRateCode);
    await Promise.all([
      page.waitForURL(/\/admin\/gst\/hsn-sac$/),
      page.getByRole('button', { name: 'Save Code' }).click(),
    ]);
    await expect(page.getByText(hsnCode)).toBeVisible();

    await page.goto(`/admin/gst/gstn/login?gstin=${gstin}`, { waitUntil: 'domcontentloaded' });
    await page.getByTestId('gstn-request-otp').click();
    await expect(page.getByText('Enter OTP')).toBeVisible();
    await page.getByTestId('gstn-otp-input').fill('123456');
    await page.getByTestId('gstn-verify-otp').click();
    await expect(page.getByText('Connected Successfully')).toBeVisible();

    await page.goto(`/admin/gst/gstn/gstr1?gstin=${gstin}`, { waitUntil: 'domcontentloaded' });
    await waitForPageIdle(page);
    await page.getByTestId('gstr1-generate').click();
    await expect(page.getByText('GSTR-1 prepared successfully.')).toBeVisible();
    await page.getByTestId('gstr1-submit').click();
    await expect(page.getByText('GSTR-1 submitted successfully.')).toBeVisible();
    await page.getByTestId('gstr1-open-file-dialog').click();
    await page.getByTestId('gstr1-pan-input').fill('ABCDE1234F');
    await page.getByTestId('gstr1-otp-input').fill('123456');
    await page.getByTestId('gstr1-file').click();
    await expect(page.getByText('GSTR-1 filed successfully.')).toBeVisible();

    await page.goto(`/admin/gst/gstn/gstr3b?gstin=${gstin}`, { waitUntil: 'domcontentloaded' });
    await waitForPageIdle(page);
    await page.getByTestId('gstr3b-generate').click();
    await expect(page.getByText('GSTR-3B prepared successfully.')).toBeVisible();
    await page.getByTestId('gstr3b-submit').click();
    await expect(page.getByText('GSTR-3B submitted successfully.')).toBeVisible();
    await page.getByTestId('gstr3b-open-file-dialog').click();
    await page.getByTestId('gstr3b-pan-input').fill('ABCDE1234F');
    await page.getByTestId('gstr3b-otp-input').fill('123456');
    await page.getByTestId('gstr3b-file').click();
    await expect(page.getByText('GSTR-3B filed successfully.')).toBeVisible();

    await page.goto(`/admin/gst/gstn/itc?gstin=${gstin}`, { waitUntil: 'domcontentloaded' });
    await waitForPageIdle(page);
    await page.getByTestId('itc-fetch-gstr2b').click();
    await expect(page.getByText('GSTR-2B data fetched successfully.')).toBeVisible();
    await page.getByTestId('itc-run-reconciliation').click();
    await expect(page.getByText('Reconciliation completed successfully.')).toBeVisible();
  });

  test('completes the TDS workflow end to end', async ({ authedPage: page, bootBundle }) => {
    test.setTimeout(180_000);

    await page.goto('/admin/tds/sections/new', { waitUntil: 'domcontentloaded' });
    await page.getByLabel('Section code').fill(tdsSectionCode);
    await page.getByLabel('Section name').fill(tdsSectionName);
    await page.getByRole('combobox').first().click();
    await page.getByRole('option', { name: /26Q Non-salary/i }).click();
    await Promise.all([
      page.waitForURL(/\/admin\/tds\/sections$/),
      page.getByRole('button', { name: 'Save Section' }).click(),
    ]);
    await expect(page.getByText(tdsSectionCode)).toBeVisible();

    await page.goto('/admin/tds/entries/new', { waitUntil: 'domcontentloaded' });
    const entryComboboxes = page.getByRole('combobox');
    await openSelectOption(entryComboboxes.nth(0), bootBundle.financialYearName);
    await openSelectOption(entryComboboxes.nth(1), tdsSectionCode);
    await page.getByLabel('Deductee name').fill(deducteeName);
    await page.getByLabel('Deductee PAN').fill(deducteePan);
    await page.getByLabel('Deduction date').fill(bootBundle.deductionDate);
    await page.getByLabel('Base amount').fill('10000');
    await Promise.all([
      page.waitForURL(/\/admin\/tds\/entries$/),
      page.getByRole('button', { name: 'Save Entry' }).click(),
    ]);
    await expect(page.getByText(deducteeName)).toBeVisible();

    await page.goto('/admin/tds/challans/create', { waitUntil: 'domcontentloaded' });
    const challanComboboxes = page.getByRole('combobox');
    await openSelectOption(challanComboboxes.nth(0), bootBundle.financialYearName);
    await openSelectOption(challanComboboxes.nth(1), tdsSectionCode);
    await page.getByLabel('Assessment year').fill(bootBundle.assessmentYear);
    await page.getByLabel('Period from').fill(bootBundle.quarterFrom);
    await page.getByLabel('Period to').fill(bootBundle.quarterTo);
    await page.getByLabel('Deductor tan').fill(deductorTan);
    await page.getByLabel('Deductor name').fill(bootBundle.organizationName);
    const entryCheckbox = page.locator('label').filter({ hasText: new RegExp(deducteeName, 'i') }).locator('input[type="checkbox"]');
    await entryCheckbox.check();
    await Promise.all([
      page.waitForURL(/\/admin\/tds\/challans\/[0-9a-f-]{36}$/),
      page.getByRole('button', { name: 'Save Challan' }).click(),
    ]);
    await waitForPageIdle(page);

    const paymentCard = page.locator('div.rounded-lg.border').filter({ hasText: 'Payment Details' }).first();
    await paymentCard.locator('input').nth(0).fill(challanNumber);
    await paymentCard.locator('input').nth(1).fill(bsrCode);
    await paymentCard.locator('input').nth(3).fill(bootBundle.quarterTo);
    await paymentCard.locator('input').nth(5).fill('State Bank of India');
    await Promise.all([
      page.waitForResponse((response) =>
        response.request().method() === 'POST'
        && response.url().includes('/api/v1/tds/challans/')
        && response.url().includes('/payment')
        && response.status() === 200,
      ),
      page.getByTestId('tds-challan-save-payment').click(),
    ]);
    await waitForPageIdle(page);

    const oltasCard = page.locator('div.rounded-lg.border').filter({ hasText: 'OLTAS Verification' }).first();
    await oltasCard.locator('input').nth(0).fill(`OLTAS-${suffix}`);
    await oltasCard.locator('input').nth(1).fill('VERIFIED');
    await oltasCard.locator('input').nth(2).fill(bootBundle.quarterTo);
    await Promise.all([
      page.waitForResponse((response) =>
        response.request().method() === 'POST'
        && response.url().includes('/api/v1/tds/challans/')
        && response.url().includes('/verify-oltas')
        && response.status() === 200,
      ),
      page.getByTestId('tds-challan-save-oltas').click(),
    ]);
    await waitForPageIdle(page);

    await page.goto('/admin/tds/certificates/generate', { waitUntil: 'domcontentloaded' });
    const certificateComboboxes = page.getByRole('combobox');
    await openSelectOption(certificateComboboxes.nth(0), bootBundle.financialYearName);
    await openSelectOption(certificateComboboxes.nth(1), 'Q1');
    await waitForPageIdle(page);
    await openSelectOption(certificateComboboxes.nth(2), deducteeName);
    await page.getByTestId('tds-certificate-generate-single').click();
    await expect(page.getByText('Generated certificate summary')).toBeVisible();
    await expect(page.getByText('NOT_TRACES_ISSUED')).toBeVisible();
    const certificateDownload = page.waitForEvent('download');
    await page.getByTestId('tds-certificate-download-summary').click();
    await certificateDownload;

    await page.goto('/admin/tds/returns/create', { waitUntil: 'domcontentloaded' });
    const returnComboboxes = page.getByRole('combobox');
    await openSelectOption(returnComboboxes.nth(0), bootBundle.financialYearName);
    await openSelectOption(returnComboboxes.nth(1), '26Q Non-salary');
    await openSelectOption(returnComboboxes.nth(2), 'Q1');
    await page.getByLabel('Deductor tan').fill(deductorTan);
    await page.getByLabel('Deductor name').fill(bootBundle.organizationName);
    await page.getByLabel('Deductor pan').fill('ABCDE1234F');
    await page.getByLabel('Deductor email').fill(`tax-${suffix}@example.com`);
    await page.getByRole('button', { name: 'Save Return' }).click();
    const returnCreationOutcome = await Promise.race([
      page.waitForURL(/\/admin\/tds\/returns\/[0-9a-f-]{36}$/, { timeout: 10_000 }).then(() => 'created' as const).catch(() => null),
      page.getByText(/Return already exists for/i).waitFor({ state: 'visible', timeout: 10_000 }).then(() => 'duplicate' as const).catch(() => null),
    ]);
    if (returnCreationOutcome === 'duplicate') {
      await page.goto('/admin/tds/returns', { waitUntil: 'domcontentloaded' });
      const existingReturnRow = page.getByRole('row', { name: /26Q.*2024-25.*Q1/i }).first();
      await expect(existingReturnRow).toBeVisible();
      await existingReturnRow.click();
    } else if (returnCreationOutcome !== 'created') {
      throw new Error('TDS return creation did not navigate or surface a duplicate-return message.');
    }
    await waitForPageIdle(page);

    await page.getByRole('button', { name: 'Validate Return' }).click();
    await expect(page.getByText(/Status:\s+VALIDATED/i)).toBeVisible();
    await page.getByRole('button', { name: 'Generate File' }).click();
    await expect(page.getByRole('button', { name: /Download .*\.txt/i })).toBeVisible();
    const returnDownload = page.waitForEvent('download');
    await page.getByRole('button', { name: /Download .*\.txt/i }).click();
    await returnDownload;

    const filingCard = page.locator('div.rounded-lg.border').filter({ hasText: 'Filing Evidence' }).first();
    await filingCard.locator('input').nth(2).fill(filingAckNumber);
    await filingCard.locator('input').nth(3).fill(bootBundle.quarterTo);
    await Promise.all([
      page.waitForResponse((response) =>
        response.request().method() === 'POST'
        && response.url().includes('/api/v1/tds/returns/')
        && response.url().includes('/filing-details')
        && response.status() === 200,
      ),
      page.getByRole('button', { name: 'Save Filing Details' }).click(),
    ]);
    await waitForPageIdle(page);
    await expect(page.getByText(/Status:\s+FILED/i)).toBeVisible({ timeout: 10_000 });
  });
});

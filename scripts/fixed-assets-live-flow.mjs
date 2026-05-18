import fs from 'node:fs/promises';
import path from 'node:path';

import { chromium } from '@playwright/test';

const baseURL = process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:5176';
const apiBase = process.env.PLAYWRIGHT_API_BASE || 'http://localhost:8001/api/v1';
const adminUsername = process.env.UAT_ADMIN_USERNAME || 'krishna';
const adminPassword = process.env.UAT_ADMIN_PASSWORD || 'ChangeMe123!';
const approverUsername = process.env.UAT_APPROVER_USERNAME || '';
const approverPassword = process.env.UAT_APPROVER_PASSWORD || '';
const outputDir = path.resolve(
  process.env.FIXED_ASSETS_LIVE_FLOW_OUTPUT_DIR || path.join('test-results', 'fixed-assets-live-flow'),
);

const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
const runLabel = `UAT FA ${timestamp}`;
const uniqueCodeSuffix = timestamp.replace(/[^0-9]/g, '').slice(2, 16);
const categoryCode = `UATFA${uniqueCodeSuffix}`.slice(0, 20);
const categoryName = `${runLabel} Category`;
const assetName = `${runLabel} Laptop`;
const scheduleName = `${runLabel} Verification`;
const disposalRemarks = `${runLabel} disposal`;

const consoleErrors = [];
const failedResponses = [];

function buildCandidateDepreciationPeriods() {
  const periods = [];
  const cursor = new Date();
  cursor.setUTCDate(1);
  for (let index = 0; index < 24; index += 1) {
    const year = cursor.getUTCFullYear();
    const month = String(cursor.getUTCMonth() + 1).padStart(2, '0');
    periods.push(`${year}-${month}`);
    cursor.setUTCMonth(cursor.getUTCMonth() - 1);
  }
  return periods;
}

function isIgnorableFailure(status, url) {
  if (status < 400) return true;
  if (/\.(ico|png|jpg|jpeg|gif|svg|map)(\?.*)?$/.test(url)) return true;
  return false;
}

async function ensureDir(dir) {
  await fs.mkdir(dir, { recursive: true });
}

async function attachDiagnostics(page) {
  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      consoleErrors.push(msg.text());
    }
  });
  page.on('pageerror', (error) => {
    consoleErrors.push(`uncaught: ${error.message}`);
  });
  page.on('response', (response) => {
    const status = response.status();
    const url = response.url();
    if (!isIgnorableFailure(status, url)) {
      failedResponses.push({ status, url });
    }
  });
}

async function fieldContainer(scope, label) {
  return scope.locator('label', { hasText: label }).locator('..').first();
}

async function fillByLabel(scope, label, value) {
  const input = scope.getByLabel(label, { exact: true });
  await input.fill(String(value));
}

async function fillAmountByLabel(scope, label, value) {
  const input = scope.getByLabel(label, { exact: true });
  await input.click();
  await input.press(process.platform === 'darwin' ? 'Meta+A' : 'Control+A');
  await input.type(String(value));
}

async function selectByLabel(page, scope, label, optionText) {
  const field = await fieldContainer(scope, label);
  const nativeSelect = field.locator('select');
  if ((await nativeSelect.count()) > 0) {
    await nativeSelect.selectOption({ label: optionText });
    return;
  }
  await field.getByRole('combobox').click();
  const exactOption = page.getByRole('option', { name: optionText, exact: true });
  if ((await exactOption.count()) > 0) {
    await exactOption.first().click();
    return;
  }
  await page.getByText(optionText, { exact: true }).click();
}

async function fillDateByLabel(scope, label, isoDate) {
  const field = await fieldContainer(scope, label);
  const dateInput = field.locator('input[type="date"]').first();
  if ((await dateInput.count()) > 0) {
    await dateInput.fill(isoDate);
    return;
  }
  const followingDateInput = scope
    .locator('label', { hasText: label })
    .first()
    .locator('xpath=following::input[@type="date"][1]');
  if ((await followingDateInput.count()) > 0) {
    await followingDateInput.fill(isoDate);
    return;
  }
  await fillByLabel(scope, label, isoDate);
}

async function fillDateByIndex(scope, index, isoDate) {
  const dateInputs = scope.locator('input[type="date"], input[placeholder*="yyyy"]');
  await dateInputs.nth(index).fill(isoDate);
}

function pickMasterOption(options, matchers, usedIds = new Set()) {
  for (const matcher of matchers) {
    const found = options.find((option) => {
      if (usedIds.has(option.id)) return false;
      const haystack = `${option.code ?? ''} ${option.name ?? ''}`.toLowerCase();
      return matcher.every((term) => haystack.includes(term));
    });
    if (found) {
      usedIds.add(found.id);
      return found;
    }
  }
  return null;
}

async function resolveCategoryGlAccounts(page) {
  const browserSession = await getBrowserSession(page);
  const response = await apiGet(
    browserSession.token,
    `${apiBase}/accounts?organization_id=${browserSession.organizationId}&page=1&page_size=100`,
  );
  const options = response.items ?? [];
  const usedIds = new Set();

  const assetAccount = pickMasterOption(
    options,
    [
      ['1505', 'computers', 'laptops'],
      ['1504', 'office', 'equipment'],
      ['150', 'equipment'],
      ['150', 'asset'],
    ],
    usedIds,
  );
  const accumDepAccount = pickMasterOption(
    options,
    [
      ['1507', 'accumulated', 'depreciation'],
      ['accumulated', 'depreciation'],
    ],
    usedIds,
  );
  const depExpenseAccount = pickMasterOption(
    options,
    [
      ['5303', 'depreciation', 'equipment'],
      ['depreciation', 'equipment'],
      ['depreciation'],
    ],
    usedIds,
  );

  if (!assetAccount || !accumDepAccount || !depExpenseAccount) {
    throw new Error(
      `Unable to resolve category GL accounts from live masters: asset=${assetAccount?.name ?? 'missing'}, accum=${accumDepAccount?.name ?? 'missing'}, dep=${depExpenseAccount?.name ?? 'missing'}`,
    );
  }

  return { assetAccount, accumDepAccount, depExpenseAccount };
}

async function login(page) {
  await page.goto(`${baseURL}/login`, { waitUntil: 'domcontentloaded' });
  await fillByLabel(page, 'Username', adminUsername);
  await fillByLabel(page, 'Password', adminPassword);
  await Promise.all([
    page.waitForURL(/\/admin$/, { waitUntil: 'domcontentloaded' }),
    page.getByRole('button', { name: 'Sign in' }).click(),
  ]);
}

async function createCategory(page) {
  await page.goto(`${baseURL}/admin/fixed-assets/categories/new`);
  await page.getByText('New Asset Category', { exact: true }).waitFor();

  const form = page.locator('form').first();
  const glAccounts = await resolveCategoryGlAccounts(page);
  await fillByLabel(form, 'Category code', categoryCode);
  await fillByLabel(form, 'Category name', categoryName);
  await fillByLabel(form, 'Description', 'Live UAT category for fixed-assets operational-core verification');
  await fillByLabel(form, 'Useful life (years)', '5');
  await fillByLabel(form, 'Residual value', '5');
  await fillByLabel(form, 'SLM rate', '10');
  await fillByLabel(form, 'WDV rate', '18');
  await selectByLabel(
    page,
    form,
    'Asset account',
    `${glAccounts.assetAccount.code} · ${glAccounts.assetAccount.name}`,
  );
  await selectByLabel(
    page,
    form,
    'Accumulated depreciation',
    `${glAccounts.accumDepAccount.code} · ${glAccounts.accumDepAccount.name}`,
  );
  await selectByLabel(
    page,
    form,
    'Depreciation expense',
    `${glAccounts.depExpenseAccount.code} · ${glAccounts.depExpenseAccount.name}`,
  );

  await Promise.all([
    page.waitForURL(/\/admin\/fixed-assets\/categories$/, {
      waitUntil: 'domcontentloaded',
    }),
    page.getByRole('button', { name: 'Save category' }).click(),
  ]);
  await page.getByText('Asset category created').waitFor();
}

async function createAsset(page) {
  await page.goto(`${baseURL}/admin/fixed-assets/assets/new`);
  await page.getByText('New Fixed Asset', { exact: true }).waitFor();

  const form = page.locator('form').first();
  await fillByLabel(form, 'Asset name', assetName);
  await selectByLabel(page, form, 'Category', `${categoryCode} · ${categoryName}`);
  await fillByLabel(form, 'Description', 'Live UAT asset created through the admin UI');
  await selectByLabel(page, form, 'Location', 'HO · Head Office');
  await selectByLabel(page, form, 'Department', 'ADMIN · Administration');
  await fillDateByLabel(form, 'Acquisition date', '2024-10-10');
  await fillDateByLabel(form, 'Put-to-use date', '2024-10-20');
  await fillAmountByLabel(form, 'Acquisition cost', '120000');
  await fillAmountByLabel(form, 'Installation cost', '5000');
  await fillAmountByLabel(form, 'Other costs', '0');
  await fillAmountByLabel(form, 'Residual value', '5000');
  await fillByLabel(form, 'Invoice number', `INV-${timestamp.slice(0, 10)}`);
  await fillDateByLabel(form, 'Invoice date', '2024-10-10');
  await fillByLabel(form, 'PO number', `PO-${timestamp.slice(0, 10)}`);
  await fillByLabel(form, 'Quantity', '1');
  await fillByLabel(form, 'Make', 'Dell');
  await fillByLabel(form, 'Model', 'Latitude UAT');
  await fillByLabel(form, 'Serial number', `SN-${timestamp.slice(0, 12)}`);

  const createAssetResponsePromise = page.waitForResponse(
    (response) =>
      response.url().includes('/api/v1/fixed-assets/assets') &&
      response.request().method() === 'POST',
    { timeout: 15_000 },
  );
  await page.getByRole('button', { name: 'Save asset' }).click();
  const createAssetResponse = await createAssetResponsePromise;
  if (!createAssetResponse.ok()) {
    throw new Error(
      `Asset create failed: ${createAssetResponse.status()} ${await createAssetResponse.text()}`,
    );
  }
  const createdAsset = await createAssetResponse.json();
  const assetId = createdAsset.id ?? createdAsset.assetId;
  if (!assetId) {
    throw new Error('Asset create response did not include an asset id');
  }
  const assetUrl = `${baseURL}/admin/fixed-assets/assets/${assetId}`;
  await page.goto(assetUrl, { waitUntil: 'domcontentloaded' });
  await page.getByRole('heading', { name: assetName }).waitFor();
  return { assetId, assetUrl };
}

async function capitalizeAsset(page) {
  await Promise.all([
    page.waitForURL(/\/admin\/fixed-assets\/assets\/[0-9a-f-]+\/capitalize$/, {
      waitUntil: 'domcontentloaded',
    }),
    page.getByRole('button', { name: 'Capitalize' }).click(),
  ]);
  await page.getByRole('heading', { name: 'Capitalize Asset' }).waitFor();
  const form = page.locator('form').first();
  await fillDateByIndex(form, 0, '2024-10-20');
  await fillDateByIndex(form, 1, '2024-10-20');
  await fillDateByIndex(form, 2, '2024-10-20');
  await fillByLabel(form, 'Remarks', 'Live UAT capitalization');
  await Promise.all([
    page.waitForURL(/\/admin\/fixed-assets\/assets\/[0-9a-f-]+$/, {
      waitUntil: 'domcontentloaded',
    }),
    page.getByRole('button', { name: 'Capitalize Asset' }).click(),
  ]);
}

async function revalueAsset(page) {
  await Promise.all([
    page.waitForURL(/\/admin\/fixed-assets\/assets\/[0-9a-f-]+\/revalue$/, {
      waitUntil: 'domcontentloaded',
    }),
    page.getByRole('button', { name: 'Revalue' }).click(),
  ]);
  const form = page.locator('form').first();
  await fillDateByIndex(form, 0, '2025-03-01');
  await fillAmountByLabel(form, 'New value', '130000');
  await fillByLabel(form, 'Valuer name', 'Internal valuer');
  await fillByLabel(form, 'Report number', `VR-${timestamp.slice(0, 10)}`);
  await fillDateByIndex(form, 1, '2025-03-01');
  await fillByLabel(form, 'Valuation method', 'Market benchmark');
  await fillByLabel(form, 'Reason', 'Live UAT revaluation');
  await Promise.all([
    page.waitForURL(/\/admin\/fixed-assets\/assets\/[0-9a-f-]+$/, {
      waitUntil: 'domcontentloaded',
    }),
    page.getByRole('button', { name: 'Revalue Asset' }).click(),
  ]);
}

async function impairAsset(page) {
  await Promise.all([
    page.waitForURL(/\/admin\/fixed-assets\/assets\/[0-9a-f-]+\/impair$/, {
      waitUntil: 'domcontentloaded',
    }),
    page.getByRole('button', { name: 'Impair' }).click(),
  ]);
  const form = page.locator('form').first();
  await fillDateByIndex(form, 0, '2025-03-05');
  await fillAmountByLabel(form, 'Impairment amount', '3000');
  await fillByLabel(form, 'Reason', 'Live UAT impairment');
  await Promise.all([
    page.waitForURL(/\/admin\/fixed-assets\/assets\/[0-9a-f-]+$/, {
      waitUntil: 'domcontentloaded',
    }),
    page.getByRole('button', { name: 'Impair Asset' }).click(),
  ]);
}

async function pickDepreciationPeriod(page) {
  const browserSession = await getBrowserSession(page);
  const candidateDepreciationPeriods = buildCandidateDepreciationPeriods();
  const runs = await apiGet(
    browserSession.token,
    `${apiBase}/fixed-assets/depreciation/runs?organization_id=${browserSession.organizationId}&skip=0&limit=100`,
  );
  const existingPeriods = new Set(runs.items?.map((item) => item.depreciationPeriod) ?? []);
  const selected = candidateDepreciationPeriods.find((period) => !existingPeriods.has(period));
  if (!selected) {
    throw new Error(`No available depreciation period from ${candidateDepreciationPeriods.join(', ')}`);
  }
  return selected;
}

async function runDepreciation(page, depreciationPeriod) {
  await page.goto(`${baseURL}/admin/fixed-assets/depreciation/run`);
  const form = page.locator('form').first();
  await fillByLabel(form, 'Depreciation period', depreciationPeriod);
  await fillByLabel(form, 'Remarks', 'Live UAT depreciation run');
  const responsePromise = page.waitForResponse(
    (response) =>
      response.url().includes('/api/v1/fixed-assets/depreciation/run') &&
      response.request().method() === 'POST',
  );
  await page.getByRole('button', { name: 'Run depreciation' }).click();
  const response = await responsePromise;
  if (!response.ok()) {
    throw new Error(
      `Depreciation run request failed: ${response.status()} ${await response.text()}`,
    );
  }
  const run = await response.json();
  return run.id ?? run.runId ?? null;
}

async function findDepreciationRun(page, depreciationPeriod) {
  const browserSession = await getBrowserSession(page);
  const runs = await apiGet(
    browserSession.token,
    `${apiBase}/fixed-assets/depreciation/runs?organization_id=${browserSession.organizationId}&skip=0&limit=100`,
  );
  return (
    runs.items?.find((item) => item.depreciationPeriod === depreciationPeriod) ?? null
  );
}

async function postDepreciation(page, depreciationPeriod, runId) {
  const run =
    runId
      ? { id: runId }
      : (page.url().match(/\/admin\/fixed-assets\/depreciation\/runs\/([0-9a-f-]+)$/)?.[1]
        ? { id: page.url().match(/\/admin\/fixed-assets\/depreciation\/runs\/([0-9a-f-]+)$/)?.[1] }
        : await findDepreciationRun(page, depreciationPeriod));
  if (!run?.id) {
    throw new Error(`Unable to resolve depreciation run for period ${depreciationPeriod}`);
  }
  const browserSession = await getBrowserSession(page);
  const readRun = async () =>
    apiGet(
      browserSession.token,
      `${apiBase}/fixed-assets/depreciation/runs?organization_id=${browserSession.organizationId}&skip=0&limit=100`,
    ).then((payload) => payload.items?.find((item) => item.id === run.id) ?? null);
  const currentRun = await pollUntil(
    readRun,
    (item) => item?.status === 'COMPLETED' || item?.status === 'POSTED',
    `depreciation run ${run.id} to complete`,
  );
  if (currentRun?.status === 'POSTED') {
    return {
      mode: 'posted',
      message: 'Depreciation run already posted',
      run: currentRun,
      approvalRequestId: null,
      approvalRequestNumber: null,
      approvalStatus: null,
      finalizedByApprover: false,
    };
  }
  await page.goto(`${baseURL}/admin/fixed-assets/depreciation/runs/${run.id}`);
  await page.getByRole('heading', { name: `Depreciation Run ${depreciationPeriod}` }).waitFor();
  const postButton = page.getByRole('button', { name: 'Post / Submit' }).last();
  if ((await postButton.count()) === 0) {
    throw new Error('Depreciation run completed without a Post / Submit action');
  }
  const responsePromise = page
    .waitForResponse(
      (response) =>
        response.url().includes(`/api/v1/fixed-assets/depreciation/runs/${run.id}/submit-posting`) &&
        response.request().method() === 'POST',
      { timeout: 8_000 },
    )
    .catch(() => null);
  await postButton.scrollIntoViewIfNeeded();
  await postButton.click({ force: true });
  const response = await responsePromise;
  if (response) {
    if (!response.ok()) {
      throw new Error(
        `Depreciation post request failed: ${response.status()} ${await response.text()}`,
      );
    }
    const action = await response.json();
    if (action.mode === 'submitted_for_approval' && action.approvalRequestId) {
      const approvalSession = await approveRequestWithApprover(
        action.approvalRequestId,
        'Approved during fixed-assets live UAT',
      );
      if (approvalSession) {
        await pollUntil(
          readRun,
          (currentRun) => currentRun?.status === 'POSTED',
          `depreciation run ${run.id} to post after approval`,
        );
        return { ...action, finalizedByApprover: true };
      }
    }
    return { ...action, finalizedByApprover: false };
  }
  const action = await apiPost(
    browserSession.token,
    `${apiBase}/fixed-assets/depreciation/runs/${run.id}/submit-posting`,
  );
  if (action.mode === 'submitted_for_approval' && action.approvalRequestId) {
    const approvalSession = await approveRequestWithApprover(
      action.approvalRequestId,
      'Approved during fixed-assets live UAT',
    );
    if (approvalSession) {
      await pollUntil(
        readRun,
        (currentRun) => currentRun?.status === 'POSTED',
        `depreciation run ${run.id} to post after approval`,
      );
      return { ...action, finalizedByApprover: true };
    }
  }
  return { ...action, finalizedByApprover: false };
}

async function createVerification(page) {
  await page.goto(`${baseURL}/admin/fixed-assets/verification/new`);
  await page.getByText('New Verification Schedule', { exact: true }).waitFor();
  const form = page.locator('form').first();
  await fillByLabel(form, 'Schedule name', scheduleName);
  await fillByLabel(form, 'Financial year', '2024-25');
  await selectByLabel(page, form, 'Location', 'HO · Head Office');
  await fillDateByIndex(form, 0, '2025-03-10');
  await fillDateByIndex(form, 1, '2025-03-20');
  await fillByLabel(form, 'Remarks', 'Live UAT physical verification');
  await Promise.all([
    page.waitForURL(/\/admin\/fixed-assets\/verification\/[0-9a-f-]+$/, {
      waitUntil: 'domcontentloaded',
    }),
    page.getByRole('button', { name: 'Save schedule' }).click(),
  ]);
}

async function executeVerification(page) {
  const startResponsePromise = page.waitForResponse(
    (response) =>
      response.url().includes('/api/v1/fixed-assets/verification/schedules/') &&
      response.url().includes('/start') &&
      response.request().method() === 'POST',
    { timeout: 15_000 },
  );
  await page.getByRole('button', { name: 'Start' }).click();
  const startResponse = await startResponsePromise;
  if (!startResponse.ok()) {
    throw new Error(`Verification start failed: ${startResponse.status()} ${await startResponse.text()}`);
  }
  await page.getByRole('button', { name: 'Verify' }).first().click();

  const dialog = page.getByRole('dialog');
  await fillDateByIndex(dialog, 0, '2025-03-12');
  await selectByLabel(page, dialog, 'Result', 'Missing');
  await selectByLabel(page, dialog, 'Condition', 'Damaged');
  await fillByLabel(dialog, 'Condition notes', 'Asset intentionally marked missing to create a discrepancy in live UAT.');
  const verifyResponsePromise = page.waitForResponse(
    (response) =>
      response.url().includes('/api/v1/fixed-assets/verification/entries/') &&
      response.url().includes('/verify') &&
      response.request().method() === 'PUT',
    { timeout: 15_000 },
  );
  await page.getByRole('button', { name: 'Save verification' }).click();
  const verifyResponse = await verifyResponsePromise;
  if (!verifyResponse.ok()) {
    throw new Error(
      `Verification save failed: ${verifyResponse.status()} ${await verifyResponse.text()}`,
    );
  }
  await dialog.waitFor({ state: 'hidden', timeout: 15_000 });

  const completeResponsePromise = page.waitForResponse(
    (response) =>
      response.url().includes('/api/v1/fixed-assets/verification/schedules/') &&
      response.url().includes('/complete') &&
      response.request().method() === 'POST',
    { timeout: 15_000 },
  );
  await page.getByRole('button', { name: 'Complete' }).click();
  const completeResponse = await completeResponsePromise;
  if (!completeResponse.ok()) {
    throw new Error(
      `Verification complete failed: ${completeResponse.status()} ${await completeResponse.text()}`,
    );
  }

  const approveResponsePromise = page.waitForResponse(
    (response) =>
      response.url().includes('/api/v1/fixed-assets/verification/schedules/') &&
      response.url().includes('/approve') &&
      response.request().method() === 'POST',
    { timeout: 15_000 },
  );
  await page.getByRole('button', { name: 'Approve' }).click();
  const approveResponse = await approveResponsePromise;
  if (!approveResponse.ok()) {
    throw new Error(
      `Verification approve failed: ${approveResponse.status()} ${await approveResponse.text()}`,
    );
  }

  await page.getByRole('button', { name: 'Resolve' }).first().waitFor({ timeout: 15_000 });
  await page.getByRole('button', { name: 'Resolve' }).first().click();
  const discrepancyDialog = page.getByRole('dialog');
  await selectByLabel(page, discrepancyDialog, 'Status', 'Resolved');
  await fillByLabel(discrepancyDialog, 'Investigation notes', 'Asset location discrepancy reviewed during live UAT.');
  await fillByLabel(discrepancyDialog, 'Resolution', 'Physical verification issue resolved and documented.');
  const discrepancyResponsePromise = page.waitForResponse(
    (response) =>
      response.url().includes('/api/v1/fixed-assets/verification/discrepancies/') &&
      response.request().method() === 'PUT',
    { timeout: 15_000 },
  );
  await page.getByRole('button', { name: 'Save resolution' }).click();
  const discrepancyResponse = await discrepancyResponsePromise;
  if (!discrepancyResponse.ok()) {
    throw new Error(
      `Discrepancy update failed: ${discrepancyResponse.status()} ${await discrepancyResponse.text()}`,
    );
  }
  await discrepancyDialog.waitFor({ state: 'hidden', timeout: 15_000 });
}

async function disposeAsset(page, assetId) {
  await page.goto(`${baseURL}/admin/fixed-assets/assets`);
  await page.getByText(assetName, { exact: true }).click();
  await Promise.all([
    page.waitForURL(/\/admin\/fixed-assets\/assets\/[0-9a-f-]+\/dispose$/, {
      waitUntil: 'domcontentloaded',
    }),
    page.getByRole('button', { name: 'Dispose' }).click(),
  ]);
  const form = page.locator('form').first();
  await fillDateByIndex(form, 0, '2025-03-25');
  await selectByLabel(page, form, 'Disposal type', 'Write-off');
  await fillAmountByLabel(form, 'Disposal value', '1000');
  await fillByLabel(form, 'Remarks', disposalRemarks);
  const responsePromise = page.waitForResponse(
    (response) =>
      response.url().includes(`/api/v1/fixed-assets/disposals/${assetId}/submit`) &&
      response.request().method() === 'POST',
    { timeout: 15_000 },
  );
  await Promise.all([
    page.waitForURL(/\/admin\/fixed-assets\/assets\/[0-9a-f-]+$/, {
      waitUntil: 'domcontentloaded',
    }),
    page.getByRole('button', { name: 'Dispose Asset' }).click(),
  ]);
  const response = await responsePromise;
  if (!response.ok()) {
    throw new Error(`Disposal request failed: ${response.status()} ${await response.text()}`);
  }
  const action = await response.json();
  if (action.mode === 'submitted_for_approval' && action.approvalRequestId) {
    const approvalSession = await approveRequestWithApprover(
      action.approvalRequestId,
      'Approved during fixed-assets live UAT',
    );
    if (approvalSession) {
      await pollUntil(
        () => apiGet(approvalSession.access_token, `${apiBase}/fixed-assets/assets/${assetId}`),
        (asset) => asset?.status === 'DISPOSED',
        `asset ${assetId} to reach DISPOSED after approval`,
      );
      return { ...action, finalizedByApprover: true };
    }
  }
  return { ...action, finalizedByApprover: false };
}

async function finalizeDisposalIfNeeded(page) {
  await page.goto(`${baseURL}/admin/fixed-assets/disposal`);
  const searchInput = page.getByPlaceholder('Search by asset code, name, or request number');
  if ((await searchInput.count()) > 0) {
    await searchInput.fill(assetName);
  }
  const approveButton = page.getByRole('button', { name: 'Approve' }).first();
  if ((await approveButton.count()) > 0) {
    await approveButton.click();
    await page.getByText('Disposal approved').waitFor();
  }
}

async function verifyReports(page) {
  await page.goto(`${baseURL}/admin/fixed-assets/reports`);
  const [assetRegisterDownload] = await Promise.all([
    page.waitForEvent('download'),
    page.getByRole('button', { name: 'Export CSV' }).first().click(),
  ]);
  const assetRegisterPath = path.join(outputDir, `asset-register-${timestamp}.csv`);
  await assetRegisterDownload.saveAs(assetRegisterPath);

  const [depreciationDownload] = await Promise.all([
    page.waitForEvent('download'),
    page.getByRole('button', { name: 'Export CSV' }).nth(1).click(),
  ]);
  const depreciationPath = path.join(outputDir, `depreciation-summary-${timestamp}.csv`);
  await depreciationDownload.saveAs(depreciationPath);

  return { assetRegisterPath, depreciationPath };
}

async function apiGet(token, url) {
  const response = await fetch(url, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    throw new Error(`API GET failed: ${response.status} ${url}`);
  }
  return response.json();
}

async function apiLogin(username, password) {
  const response = await fetch(`${apiBase}/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Idempotency-Key': crypto.randomUUID(),
    },
    body: JSON.stringify({ username, password }),
  });
  if (!response.ok) {
    throw new Error(`API login failed: ${response.status} ${await response.text()}`);
  }
  return response.json();
}

async function apiPost(token, url, body) {
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
      'Idempotency-Key': crypto.randomUUID(),
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(`API POST failed: ${response.status} ${url} ${await response.text()}`);
  }
  return response.json();
}

async function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function pollUntil(fn, predicate, description, timeoutMs = 30_000, intervalMs = 1_000) {
  const startedAt = Date.now();
  while (Date.now() - startedAt < timeoutMs) {
    const value = await fn();
    if (predicate(value)) {
      return value;
    }
    await sleep(intervalMs);
  }
  throw new Error(`Timed out waiting for ${description}`);
}

async function approveRequestWithApprover(requestId, comments) {
  if (!approverUsername || !approverPassword) {
    return null;
  }
  const session = await apiLogin(approverUsername, approverPassword);
  await apiPost(
    session.access_token,
    `${apiBase}/approvals/requests/${requestId}/action`,
    {
      action: 'APPROVE',
      comments,
    },
  );
  return session;
}

async function getBrowserSession(page) {
  const storage = await page.evaluate(() => ({
    auth: globalThis.localStorage.getItem('smfc-auth'),
    organization: globalThis.localStorage.getItem('smfc-organization'),
  }));

  const authState = storage.auth ? JSON.parse(storage.auth) : null;
  const orgState = storage.organization ? JSON.parse(storage.organization) : null;
  const token = authState?.state?.accessToken ?? null;
  const organizationId = orgState?.state?.activeOrganizationId ?? null;

  if (!token || !organizationId) {
    throw new Error('Unable to resolve browser auth token or active organization');
  }

  return { token, organizationId };
}

async function queryCreatedRecords(token, organizationId, assetId, depreciationPeriod) {
  const categories = await apiGet(
    token,
    `${apiBase}/fixed-assets/categories?organization_id=${organizationId}&skip=0&limit=500`,
  );
  const asset = await apiGet(token, `${apiBase}/fixed-assets/assets/${assetId}`);
  const depreciationRuns = await apiGet(
    token,
    `${apiBase}/fixed-assets/depreciation/runs?organization_id=${organizationId}&skip=0&limit=100`,
  );
  const schedules = await apiGet(
    token,
    `${apiBase}/fixed-assets/verification/schedules?organization_id=${organizationId}&skip=0&limit=100`,
  );
  const discrepancies = await apiGet(
    token,
    `${apiBase}/fixed-assets/verification/discrepancies?organization_id=${organizationId}&skip=0&limit=100`,
  );
  const disposal = await apiGet(token, `${apiBase}/fixed-assets/disposals/${assetId}`).catch(() => null);

  return {
    category:
      categories.items?.find((item) => item.categoryName === categoryName || item.categoryCode === categoryCode) ??
      null,
    asset,
    depreciationRun:
      depreciationRuns.items?.find((item) => item.depreciationPeriod === depreciationPeriod) ?? null,
    verificationSchedule:
      schedules.items?.find((item) => item.scheduleName === scheduleName) ?? null,
    discrepancy:
      discrepancies.items?.find((item) => item.assetName === assetName) ?? null,
    disposal,
  };
}

async function main() {
  await ensureDir(outputDir);
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    acceptDownloads: true,
  });
  const page = await context.newPage();
  await attachDiagnostics(page);

  let results = {
    runLabel,
    categoryCode,
    categoryName,
    assetName,
    scheduleName,
    depreciationPeriod: null,
    assetId: null,
    depreciationAction: null,
    disposalAction: null,
    screenshots: {},
    downloads: {},
    records: {},
    consoleErrors,
    failedResponses,
    error: null,
  };

  try {
    console.log('STEP login');
    await login(page);
    console.log('STEP createCategory');
    await createCategory(page);
    results.screenshots.categories = path.join(outputDir, `categories-${timestamp}.png`);
    await page.screenshot({ path: results.screenshots.categories, fullPage: true });

    console.log('STEP createAsset');
    const { assetId } = await createAsset(page);
    results.assetId = assetId;
    results.screenshots.assetDraft = path.join(outputDir, `asset-draft-${timestamp}.png`);
    await page.screenshot({ path: results.screenshots.assetDraft, fullPage: true });

    console.log('STEP capitalizeAsset');
    await capitalizeAsset(page);
    console.log('STEP revalueAsset');
    await revalueAsset(page);
    console.log('STEP impairAsset');
    await impairAsset(page);

    console.log('STEP pickDepreciationPeriod');
    const depreciationPeriod = await pickDepreciationPeriod(page);
    results.depreciationPeriod = depreciationPeriod;
    console.log('STEP runDepreciation');
    const depreciationRunId = await runDepreciation(page, depreciationPeriod);
    console.log('STEP postDepreciation');
    results.depreciationAction = await postDepreciation(page, depreciationPeriod, depreciationRunId);
    results.screenshots.depreciationRun = path.join(outputDir, `depreciation-run-${timestamp}.png`);
    await page.screenshot({ path: results.screenshots.depreciationRun, fullPage: true });

    console.log('STEP createVerification');
    await createVerification(page);
    console.log('STEP executeVerification');
    await executeVerification(page);
    results.screenshots.verification = path.join(outputDir, `verification-${timestamp}.png`);
    await page.screenshot({ path: results.screenshots.verification, fullPage: true });

    console.log('STEP disposeAsset');
    results.disposalAction = await disposeAsset(page, assetId);
    console.log('STEP finalizeDisposalIfNeeded');
    await finalizeDisposalIfNeeded(page);
    results.screenshots.disposal = path.join(outputDir, `disposal-${timestamp}.png`);
    await page.screenshot({ path: results.screenshots.disposal, fullPage: true });

    console.log('STEP verifyReports');
    results.downloads = await verifyReports(page);
    console.log('STEP queryCreatedRecords');
    const browserSession = await getBrowserSession(page);
    results.records = await queryCreatedRecords(
      browserSession.token,
      browserSession.organizationId,
      assetId,
      depreciationPeriod,
    );

    if (consoleErrors.length > 0 || failedResponses.length > 0) {
      throw new Error('Console or network failures were recorded during the live flow.');
    }
  } catch (error) {
    results.error = error instanceof Error ? error.message : String(error);
    await ensureDir(outputDir);
    results.screenshots.failure = path.join(outputDir, `failure-${timestamp}.png`);
    await page.screenshot({ path: results.screenshots.failure, fullPage: true });
    throw error;
  } finally {
    results.consoleErrors = [...consoleErrors];
    results.failedResponses = [...failedResponses];
    await ensureDir(outputDir);
    await fs.writeFile(
      path.join(outputDir, `summary-${timestamp}.json`),
      JSON.stringify(results, null, 2),
      'utf8',
    );
    await context.close();
    await browser.close();
  }

  console.log(JSON.stringify(results, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});

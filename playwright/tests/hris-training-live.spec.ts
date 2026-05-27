import { expect, test, type APIRequestContext } from '@playwright/test';

import { loginAsAdmin } from '../fixtures/auth';

const LIVE_BACKEND_ENABLED = process.env.PLAYWRIGHT_LIVE_BACKEND === '1';
const API_BASE = process.env.PLAYWRIGHT_API_BASE || 'http://localhost:8001/api/v1';
const ADMIN_USERNAME = process.env.UAT_ADMIN_USERNAME || 'krishna';
const ADMIN_PASSWORD = process.env.UAT_ADMIN_PASSWORD || 'ChangeMe123!';

function isoDate(offsetDays: number) {
  const date = new Date();
  date.setDate(date.getDate() + offsetDays);
  return date.toISOString().split('T')[0] ?? '';
}

async function getAdminHeaders(request: APIRequestContext) {
  const loginResponse = await request.post(`${API_BASE}/auth/login`, {
    data: { username: ADMIN_USERNAME, password: ADMIN_PASSWORD },
  });
  expect(loginResponse.ok()).toBeTruthy();
  const auth = await loginResponse.json();
  const accessToken = auth.accessToken ?? auth.access_token;
  const meResponse = await request.get(`${API_BASE}/auth/me`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  expect(meResponse.ok()).toBeTruthy();
  const me = await meResponse.json();
  const organizationId = me.organizationId ?? me.organization_id;
  return {
    Authorization: `Bearer ${accessToken}`,
    'X-Organization-Id': organizationId,
  };
}

async function ensureActiveEmployee(request: APIRequestContext) {
  const headers = await getAdminHeaders(request);
  const employeeListResponse = await request.get(`${API_BASE}/hris/employees`, {
    headers,
    params: { limit: 10 },
  });
  expect(employeeListResponse.ok()).toBeTruthy();
  const employeeList = await employeeListResponse.json();
  const activeEmployee = Array.isArray(employeeList.items)
    ? employeeList.items.find((item: { employmentStatus?: string; employment_status?: string }) => {
        const status = item.employmentStatus ?? item.employment_status;
        return status === 'ACTIVE';
      })
    : null;
  if (activeEmployee) {
    return activeEmployee;
  }

  const uniqueSeed = Date.now().toString();
  const createEmployeeResponse = await request.post(`${API_BASE}/hris/employees`, {
    headers,
    data: {
      firstName: 'Training',
      lastName: `E2E${uniqueSeed.slice(-8)}`,
      gender: 'MALE',
      dateOfBirth: '1995-01-15',
      personalMobile: `9${uniqueSeed.slice(-9)}`,
      officialEmail: `training-e2e-${uniqueSeed}@example.com`,
      dateOfJoining: '2026-05-01',
      employmentType: 'PERMANENT',
    },
  });
  expect(createEmployeeResponse.ok()).toBeTruthy();
  return createEmployeeResponse.json();
}

test.describe('HRIS training live flow', () => {
  test.skip(
    !LIVE_BACKEND_ENABLED,
    'Set PLAYWRIGHT_LIVE_BACKEND=1 to run live HRIS training coverage.',
  );
  test.skip(
    ({ browserName }) => browserName !== 'chromium',
    'Runs only in the desktop Chromium project',
  );

  test('creates a training program, nominates an employee, and records feedback', async ({
    page,
    request,
  }) => {
    test.setTimeout(180_000);

    const runLabel = `E2E-TRN-${Date.now()}`;
    const startDate = isoDate(3);
    const endDate = isoDate(4);

    await ensureActiveEmployee(request);
    await loginAsAdmin(page);

    await page.goto('/admin/hris/training/new', { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('heading', { name: 'Create Training Program' })).toBeVisible();

    await page.getByLabel('Program Title').fill(`${runLabel} Manual Training`);
    await page
      .getByLabel('Description')
      .fill(`${runLabel} training flow for live admin verification and persisted HRIS data.`);
    await page.getByRole('combobox', { name: 'Category' }).click();
    await page.getByRole('option', { name: 'Technical' }).click();
    await page.getByRole('combobox', { name: 'Training Mode' }).click();
    await page.getByRole('option', { name: 'Virtual (Online)' }).click();
    await page.getByRole('combobox', { name: 'Trainer Type' }).click();
    await page.getByRole('option', { name: 'Internal' }).click();
    await page.getByLabel(/employee \/ trainer name/i).fill('SMFC Training Admin');
    await page.getByLabel('Trainer Contact').fill('training-admin@smfc.local');
    await page.getByLabel('Start Date').fill(startDate);
    await page.getByLabel('End Date').fill(endDate);
    await page.getByLabel('Duration (Hours)').fill('6');
    await page
      .getByLabel(/meeting link \/ platform/i)
      .fill('https://meet.example.com/smfc-training');
    await page
      .getByLabel('Learning Objectives')
      .fill('Live workflow validation\nManual-first HRIS training operations');
    await page.getByLabel('Pre-requisites').fill('Laptop access');
    await page.getByLabel('Maximum Participants').fill('2');
    await page.getByLabel('Cost Per Participant').fill('0');

    await page.getByRole('button', { name: 'Create Program' }).click();
    await expect(page).toHaveURL(/\/admin\/hris\/training\/[0-9a-f-]+$/i);

    const programUrl = page.url();
    const match = programUrl.match(/\/admin\/hris\/training\/([0-9a-f-]+)$/i);
    expect(match?.[1]).toBeTruthy();
    const programId = match?.[1] as string;

    await page.goto(`/admin/hris/training/${programId}/nominations`, {
      waitUntil: 'domcontentloaded',
    });
    await expect(page.getByRole('heading', { name: 'Training Nominations' })).toBeVisible();

    await page.getByRole('button', { name: 'Add Nominations' }).click();
    const dialog = page.getByRole('dialog', { name: 'Add Nominations' });
    await expect(dialog).toBeVisible();
    const firstCheckbox = dialog.getByRole('checkbox').first();
    await expect(firstCheckbox).toBeVisible();
    await firstCheckbox.check();
    await dialog.getByRole('button', { name: /Add 1 Nominations/i }).click();
    await expect(dialog).not.toBeVisible();

    const nominationsTable = page.locator('table').last();
    await expect(nominationsTable.getByRole('button', { name: 'Confirm' }).first()).toBeVisible();
    await nominationsTable.getByRole('button', { name: 'Confirm' }).first().click();
    await expect(nominationsTable.getByText('Confirmed').first()).toBeVisible();

    const markAttendedButton = nominationsTable
      .getByRole('button', { name: 'Mark Attended' })
      .first();
    await expect(markAttendedButton).toBeVisible();
    await markAttendedButton.click();
    await expect(nominationsTable.getByText('Attendance marked').first()).toBeVisible();

    await page.goto(`/admin/hris/training/${programId}/feedback`, {
      waitUntil: 'domcontentloaded',
    });
    await expect(page.getByRole('heading', { name: 'Training Feedback' })).toBeVisible();
    await page.getByRole('button', { name: 'Record Feedback' }).click();
    const feedbackDialog = page.getByRole('dialog', { name: 'Record Manual Feedback' });
    await expect(feedbackDialog).toBeVisible();
    await feedbackDialog.getByRole('combobox', { name: 'Participant' }).click();
    await page.getByRole('listbox').getByRole('option').first().click();
    await feedbackDialog.getByRole('button', { name: 'Save Feedback' }).click();
    await expect(feedbackDialog).not.toBeVisible();

    await expect(page.getByText('1/1')).toBeVisible();
    await expect(page.getByText('100% response rate')).toBeVisible();
    await expect(page.getByText('Would recommend')).toBeVisible();
  });
});

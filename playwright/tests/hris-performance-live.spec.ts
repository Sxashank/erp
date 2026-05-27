import { randomUUID } from 'node:crypto';

import type { APIRequestContext } from '@playwright/test';

import { expect, test } from '../fixtures/test';
import { loginAsAdmin } from '../fixtures/auth';
import type { DbHelper } from '../fixtures/db';

const LIVE_BACKEND_ENABLED = process.env.PLAYWRIGHT_LIVE_BACKEND === '1';
const API_BASE = process.env.PLAYWRIGHT_API_BASE || 'http://localhost:8001/api/v1';
const ADMIN_USERNAME = process.env.UAT_ADMIN_USERNAME || 'krishna';
const ADMIN_PASSWORD = process.env.UAT_ADMIN_PASSWORD || 'ChangeMe123!';

function isoDate(offsetDays: number) {
  const date = new Date();
  date.setDate(date.getDate() + offsetDays);
  return date.toISOString().split('T')[0] ?? '';
}

function uniqueMobile(seed: string) {
  const digits = seed.replace(/\D/g, '');
  return `9${digits.slice(-9).padStart(9, '0')}`;
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

async function createActiveEmployee(request: APIRequestContext, runLabel: string) {
  const headers = await getAdminHeaders(request);
  const mobile = uniqueMobile(runLabel);
  const createEmployeeResponse = await request.post(`${API_BASE}/hris/employees`, {
    headers,
    data: {
      firstName: 'Ess',
      lastName: runLabel,
      gender: 'MALE',
      dateOfBirth: '1994-04-15',
      personalMobile: mobile,
      officialEmail: `${runLabel.toLowerCase()}@example.com`,
      dateOfJoining: isoDate(-30),
      employmentType: 'PERMANENT',
    },
  });
  expect(createEmployeeResponse.ok()).toBeTruthy();
  const employee = await createEmployeeResponse.json();
  return {
    id: employee.id,
    employeeCode: employee.employeeCode ?? employee.employee_code,
    employeeName:
      employee.fullName ??
      employee.full_name ??
      [employee.firstName ?? employee.first_name, employee.lastName ?? employee.last_name]
        .filter(Boolean)
        .join(' '),
    mobile,
    officialEmail: employee.officialEmail ?? employee.official_email,
  };
}

async function ensureEssUser(
  db: DbHelper,
  employee: {
    id: string;
    mobile: string;
    officialEmail?: string;
  },
) {
  const existing = await db.query<{
    id: string;
    mobile: string;
  }>(
    `select id::text as id, mobile
     from ess_user
     where employee_id = $1
     limit 1`,
    [employee.id],
  );

  if (existing[0]) {
    await db.query(
      `update ess_user
       set mobile = $2,
           email = $3,
           status = 'ACTIVE',
           is_mobile_verified = false,
           updated_at = now()
       where id = $1`,
      [existing[0].id, employee.mobile, employee.officialEmail ?? null],
    );
    return existing[0].id;
  }

  const created = await db.query<{ id: string }>(
    `insert into ess_user (
       id,
       organization_id,
       employee_id,
       mobile,
       email,
       is_mobile_verified,
       is_email_verified,
       status,
       is_active,
       version
     ) values ($1, $2, $3, $4, $5, false, false, 'ACTIVE', true, 1)
     returning id::text as id`,
    [randomUUID(), db.orgId, employee.id, employee.mobile, employee.officialEmail ?? null],
  );

  return created[0]?.id;
}

async function readLatestOtp(db: DbHelper, mobile: string) {
  const rows = await db.query<{ otp_code: string }>(
    `select otp_code
     from ess_otp
     where mobile = $1
       and otp_type = 'LOGIN'
       and is_used = false
     order by created_at desc
     limit 1`,
    [mobile],
  );
  expect(rows[0]?.otp_code).toBeTruthy();
  return rows[0]?.otp_code as string;
}

async function appraisalStatus(db: DbHelper, cycleId: string, employeeId: string) {
  const rows = await db.query<{ status: string }>(
    `select status
     from txn_appraisal
     where appraisal_cycle_id = $1
       and employee_id = $2
     limit 1`,
    [cycleId, employeeId],
  );
  return rows[0]?.status ?? null;
}

async function cycleStatus(db: DbHelper, cycleId: string) {
  const rows = await db.query<{ status: string }>(
    `select status
     from mst_appraisal_cycle
     where id = $1
     limit 1`,
    [cycleId],
  );
  return rows[0]?.status ?? null;
}

test.describe('HRIS performance live flow', () => {
  test.skip(
    !LIVE_BACKEND_ENABLED,
    'Set PLAYWRIGHT_LIVE_BACKEND=1 to run live HRIS performance coverage.',
  );
  test.skip(
    ({ browserName }) => browserName !== 'chromium',
    'Runs only in the desktop Chromium project',
  );

  test('completes an appraisal cycle across admin HR and ESS', async ({ page, request, db }) => {
    test.setTimeout(240_000);

    const runLabel = `E2EAPR${Date.now()}`;
    const cycleName = `${runLabel} Appraisal Cycle`;
    const cycleDescription =
      `${runLabel} live HRMS performance cycle for admin, ESS self-appraisal, ` +
      `manager review, and calibration verification.`;
    const cycleStart = isoDate(-5);
    const cycleEnd = isoDate(30);
    const goalStart = isoDate(-4);
    const goalEnd = isoDate(5);
    const selfStart = isoDate(1);
    const selfEnd = isoDate(10);
    const managerStart = isoDate(11);
    const managerEnd = isoDate(18);
    const calibrationStart = isoDate(19);
    const calibrationEnd = isoDate(23);

    const employee = await createActiveEmployee(request, runLabel);
    await ensureEssUser(db, employee);

    await loginAsAdmin(page);

    await page.goto('/admin/hris/performance/cycles/new', {
      waitUntil: 'domcontentloaded',
    });
    await expect(page.getByRole('heading', { name: 'Create Appraisal Cycle' })).toBeVisible();

    await page.getByLabel('Cycle Name').fill(cycleName);
    await page.getByLabel('Description').fill(cycleDescription);
    await page.getByLabel('Cycle Start').fill(cycleStart);
    await page.getByLabel('Cycle End').fill(cycleEnd);
    await page.getByLabel('Goal Setting Start').fill(goalStart);
    await page.getByLabel('Goal Setting End').fill(goalEnd);
    await page.getByLabel('Self Appraisal Start').fill(selfStart);
    await page.getByLabel('Self Appraisal End').fill(selfEnd);
    await page.getByLabel('Manager Review Start').fill(managerStart);
    await page.getByLabel('Manager Review End').fill(managerEnd);
    await page.getByLabel('Calibration Start').fill(calibrationStart);
    await page.getByLabel('Calibration End').fill(calibrationEnd);

    await page.getByRole('checkbox').nth(2).click();

    const employeeCard = page
      .locator('label')
      .filter({ hasText: new RegExp(employee.employeeCode) })
      .first();
    await employeeCard.locator('[role="checkbox"]').click();

    await page.getByRole('button', { name: 'Create Cycle' }).click();
    await expect(page).toHaveURL(/\/admin\/hris\/performance\/cycles\/[0-9a-f-]+$/i);

    const cycleId =
      page.url().match(/\/admin\/hris\/performance\/cycles\/([0-9a-f-]+)$/i)?.[1] ?? '';
    expect(cycleId).toBeTruthy();

    await db.assertRowMatches(
      'mst_appraisal_cycle',
      { id: cycleId },
      { name: cycleName, status: 'DRAFT' },
    );
    await db.assertRowMatches(
      'txn_appraisal',
      { appraisal_cycle_id: cycleId, employee_id: employee.id },
      { status: 'NOT_STARTED' },
    );

    await page.getByRole('button', { name: 'Start Cycle' }).click();
    await expect(page.getByText('GOAL_SETTING')).toBeVisible();

    await page.getByRole('button', { name: 'Goals' }).click();
    await expect(page.getByRole('heading', { name: 'Goal Setting' })).toBeVisible();

    await page.getByRole('button', { name: 'Add Goal' }).click();
    const goalDialog = page.getByRole('dialog');
    await expect(goalDialog.getByRole('heading', { name: 'Add Goal' })).toBeVisible();
    await goalDialog.getByLabel('Goal Title').fill('Improve manual HR operations readiness');
    await goalDialog.getByLabel('Category').fill('HR OPERATIONS');
    await goalDialog.getByLabel('Weightage (%)').fill('100');
    await goalDialog.getByLabel('Start Date').fill(goalStart);
    await goalDialog.getByLabel('Due Date').fill(managerEnd);
    await goalDialog
      .getByLabel('Target Value')
      .fill('100% completion of the HRMS+ESSP live appraisal flow');
    await goalDialog
      .getByLabel('Measurement Criteria')
      .fill(
        'Goal is complete when the employee self-appraisal and manager review are both submitted.',
      );
    await goalDialog
      .getByLabel('Description')
      .fill('Track the full live employee appraisal workflow through ESS and HR admin.');
    await goalDialog.getByRole('button', { name: 'Add Goal' }).click();

    await expect(page.getByText('Improve manual HR operations readiness')).toBeVisible();
    await page.getByRole('button', { name: 'Submit Goals' }).click();
    await expect(page.getByText('SELF_APPRAISAL')).toBeVisible();

    await page.goto('/ess/login', { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('heading', { name: /employee self service/i })).toBeVisible();

    await page.getByLabel(/mobile number/i).fill(employee.mobile);
    await page.getByRole('button', { name: /send otp/i }).click();
    await expect(page.getByRole('heading', { name: /verify otp/i })).toBeVisible();

    const otp = await readLatestOtp(db, employee.mobile);
    await page.getByLabel(/one-time password/i).fill(otp);
    await page.getByRole('button', { name: /verify.*login/i }).click();

    await expect(page).toHaveURL(/\/ess\/dashboard$/);
    await expect(page.getByRole('heading', { name: /welcome,/i })).toBeVisible();

    await page.goto('/ess/assets', { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('heading', { name: 'Assigned Assets', exact: true })).toBeVisible();

    await page.goto('/ess/training', { waitUntil: 'domcontentloaded' });
    await expect(
      page.getByRole('heading', { name: 'Training & Learning', exact: true }),
    ).toBeVisible();

    await page.goto('/ess/goals', { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('heading', { name: 'Goals', exact: true })).toBeVisible();
    await expect(page.getByText(cycleName)).toBeVisible();

    await page.goto('/ess/self-appraisal', { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('heading', { name: 'Self Appraisal', exact: true })).toBeVisible();

    await page.getByRole('combobox').nth(0).click();
    await page.getByRole('option', { name: '4' }).click();
    await page.locator('input[type="number"]').first().fill('95');
    await page
      .getByText('Achievement Value')
      .locator('xpath=following::input[1]')
      .fill('HRMS+ESSP flow completed through ESS');
    await page
      .locator('textarea')
      .first()
      .fill(
        'Completed all assigned goals, validated the live ESS flow, and captured the required submission evidence.',
      );

    await page.getByRole('combobox').nth(1).click();
    await page.getByRole('option', { name: '4' }).click();
    const allTextareas = page.locator('textarea');
    await allTextareas
      .nth(1)
      .fill(
        'Employee comment: the ESS workflow is clear and usable for regular appraisal submissions.',
      );
    await allTextareas
      .nth(2)
      .fill(
        'Delivered the active appraisal packet in the live ESS portal and submitted it without manual backend intervention.',
      );
    await allTextareas
      .nth(3)
      .fill(
        'Validated the self-appraisal flow, dashboard visibility, and access to training and asset screens.',
      );
    await allTextareas
      .nth(4)
      .fill('No blockers remained after OTP-based login and the guided self-appraisal flow.');
    await allTextareas
      .nth(5)
      .fill(
        'Further practice on manager-review calibration language would strengthen future cycle submissions.',
      );

    await page.getByRole('button', { name: 'Submit Self Appraisal' }).click();
    await expect
      .poll(() => appraisalStatus(db, cycleId, employee.id), { timeout: 30_000 })
      .toBe('MANAGER_REVIEW');

    await page.goto(`/admin/hris/performance/manager-review/${cycleId}/${employee.id}`, {
      waitUntil: 'domcontentloaded',
    });
    await expect(page.getByRole('heading', { name: 'Manager Review' })).toBeVisible();

    await page
      .getByText('Manager Rating')
      .locator('xpath=following::*[@role="combobox"][1]')
      .click();
    await page.getByRole('option', { name: '4' }).click();
    await page
      .getByText('Final Goal Rating')
      .locator('xpath=following::*[@role="combobox"][1]')
      .click();
    await page.getByRole('option', { name: '4' }).click();
    await page
      .locator('textarea')
      .first()
      .fill(
        'Strong execution. The employee completed the live ESS workflow with clear commentary and acceptable evidence.',
      );

    await page
      .getByText('Competency Rating')
      .locator('xpath=following::*[@role="combobox"][1]')
      .click();
    await page.getByRole('option', { name: '4' }).click();
    const reviewTextareas = page.locator('textarea');
    await reviewTextareas
      .nth(1)
      .fill('Manager summary: met the appraisal-cycle execution standard for live HRMS readiness.');
    await reviewTextareas
      .nth(2)
      .fill('Confirmed completion of the ESS route sweep and the production-flow submission path.');
    await reviewTextareas
      .nth(3)
      .fill(
        'Needs slightly sharper narrative detail in improvement planning and calibration notes.',
      );
    await reviewTextareas
      .nth(4)
      .fill(
        'Recommended for completion with a calibrated final grade based on consistent execution.',
      );

    await page.getByRole('button', { name: 'Submit Review' }).click();
    await expect(page.getByRole('button', { name: 'Complete Calibration' })).toBeVisible();

    await page.getByText('Calibrated Rating').locator('xpath=following::input[1]').fill('4.20');
    await page.getByText('Final Grade').locator('xpath=following::input[1]').fill('A');
    await page
      .getByText('Calibration Notes')
      .locator('xpath=following::textarea[1]')
      .fill('Calibration confirmed after reviewing live admin and ESS submissions.');
    await page.getByRole('button', { name: 'Complete Calibration' }).click();
    await expect
      .poll(() => appraisalStatus(db, cycleId, employee.id), { timeout: 30_000 })
      .toBe('COMPLETED');
    await db.assertRowMatches(
      'txn_appraisal',
      { appraisal_cycle_id: cycleId, employee_id: employee.id },
      { final_grade: 'A' },
    );

    await page.goto(`/admin/hris/performance/cycles/${cycleId}`, {
      waitUntil: 'domcontentloaded',
    });
    await page.getByRole('button', { name: 'Close Cycle' }).click();
    await expect.poll(() => cycleStatus(db, cycleId), { timeout: 30_000 }).toBe('COMPLETED');
  });
});

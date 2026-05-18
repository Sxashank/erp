/**
 * HRIS, Payroll, and ESS E2E smoke coverage.
 *
 * These tests mock the API layer so route rendering, auth bootstrap, and the
 * ESS OTP login path can run without seeded live-backend data.
 */

import type { Page, Route } from '@playwright/test';

import { expect, test } from '../fixtures/test';

const ORG_ID = '11111111-1111-1111-1111-111111111111';
const EMPLOYEE_ID = '22222222-2222-2222-2222-222222222222';
const BATCH_ID = '33333333-3333-3333-3333-333333333333';

async function fulfillJson(route: Route, body: unknown) {
  await route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify(body),
  });
}

async function installAdminMocks(page: Page) {
  await page.route('**/api/v1/**', async (route) =>
    fulfillJson(route, { items: [], total: 0, skip: 0, limit: 20 }),
  );

  await page.route('**/api/v1/auth/me', async (route) =>
    fulfillJson(route, {
      id: '99999999-9999-9999-9999-999999999999',
      username: 'admin',
      email: 'admin@smfc.example',
      full_name: 'Admin User',
      organization_id: ORG_ID,
      default_unit_id: null,
      mfa_enabled: false,
      roles: [{ id: 'role-admin', code: 'SUPER_ADMIN', name: 'Super Admin' }],
      permissions: ['SUPER_ADMIN'],
    }),
  );

  await page.route('**/api/v1/organizations**', async (route) =>
    fulfillJson(route, {
      items: [{ id: ORG_ID, code: 'SMFC', name: 'SMFC Ltd' }],
      total: 1,
    }),
  );

  await page.route('**/api/v1/departments**', async (route) =>
    fulfillJson(route, {
      items: [{ id: 'dept-hr', name: 'Human Resources' }],
      total: 1,
    }),
  );

  await page.route('**/api/v1/designations**', async (route) =>
    fulfillJson(route, {
      items: [{ id: 'desig-hr-manager', title: 'HR Manager' }],
      total: 1,
    }),
  );

  await page.route('**/api/v1/hris/employees**', async (route) =>
    fulfillJson(route, {
      items: [
        {
          id: EMPLOYEE_ID,
          employee_code: 'SMFC-00024',
          first_name: 'Asha',
          last_name: 'Rao',
          full_name: 'Asha Rao',
          personal_mobile: '9876543210',
          official_email: 'asha.rao@smfc.example',
          department_name: 'Human Resources',
          designation_name: 'HR Manager',
          employment_type: 'PERMANENT',
          employment_status: 'ACTIVE',
          date_of_joining: '2026-01-01',
        },
      ],
      total: 1,
      skip: 0,
      limit: 20,
    }),
  );

  await page.route('**/api/v1/payroll/batches**', async (route) =>
    fulfillJson(route, {
      items: [
        {
          id: BATCH_ID,
          organization_id: ORG_ID,
          batch_number: 'PAY/2026/04/001',
          payroll_month: 4,
          payroll_year: 2026,
          pay_period_from: '2026-04-01',
          pay_period_to: '2026-04-30',
          status: 'APPROVED',
          total_employees: 1,
          total_gross: 125000,
          total_deductions: 18000,
          total_net: 107000,
          total_employer_statutory: 5400,
          created_at: '2026-04-30T10:00:00Z',
        },
      ],
      total: 1,
      skip: 0,
      limit: 20,
    }),
  );

  await page.route('**/api/v1/auth/refresh', async (route) =>
    fulfillJson(route, {
      access_token: 'refreshed-admin-token',
      refresh_token: 'refreshed-admin-refresh-token',
      token_type: 'bearer',
      expires_in: 900,
    }),
  );

}

async function installEssMocks(page: Page) {
  await page.route('**/api/v1/ess/**', async (route) =>
    fulfillJson(route, { items: [], total: 0 }),
  );

  await page.route('**/api/v1/ess/auth/send-otp', async (route) =>
    fulfillJson(route, {
      message: 'OTP sent',
      expires_in_seconds: 300,
    }),
  );

  await page.route('**/api/v1/ess/auth/login', async (route) =>
    fulfillJson(route, {
      access_token: 'ess-access-token',
      refresh_token: 'ess-refresh-token',
      token_type: 'bearer',
      expires_in: 900,
      user: {
        id: 'ess-user',
        employee_id: EMPLOYEE_ID,
        employee_code: 'SMFC-00024',
        employee_name: 'Asha Rao',
        mobile: '9876543210',
        email: 'asha.rao@smfc.example',
      },
    }),
  );

  await page.route('**/api/v1/ess/profile/dashboard', async (route) =>
    fulfillJson(route, {
      employee: {
        id: EMPLOYEE_ID,
        employee_code: 'SMFC-00024',
        name: 'Asha Rao',
        designation: 'HR Manager',
        department: 'Human Resources',
      },
      attendance_this_month: {
        month: 'May 2026',
        present: 12,
        absent: 0,
        leave: 1,
        work_from_home: 2,
      },
      leave_balance: [
        { code: 'CL', balance: 8 },
        { code: 'SL', balance: 10 },
        { code: 'EL', balance: 18 },
      ],
      pending_actions: {
        pending_claims: 0,
        pending_tickets: 0,
        pending_regularizations: 0,
        pending_declarations: 0,
      },
      latest_payslip: {
        id: 'payslip-1',
        period: 'April 2026',
        net: 107000,
      },
      announcements: [],
    }),
  );
}

test.describe('HRIS, payroll, and ESS smoke', () => {
  test('admin can open HRIS employees and payroll batches', async ({
    authedPage: page,
    consoleGate,
  }) => {
    await installAdminMocks(page);

    await page.goto('/admin/hris/employees');
    await expect(page.getByRole('heading', { name: 'Employees' })).toBeVisible();
    await expect(page.getByText('Asha Rao')).toBeVisible();
    await expect(page.getByRole('button', { name: /add employee/i })).toBeVisible();

    await page.goto('/admin/payroll/batches');
    await expect(page.getByRole('heading', { name: 'Payroll Batches' })).toBeVisible();
    await expect(page.getByText('PAY/2026/04/001')).toBeVisible();
    await expect(page.getByRole('button', { name: /new batch/i })).toBeVisible();

    expect(consoleGate.getErrors()).toEqual([]);
    expect(consoleGate.getFailedResponses()).toEqual([]);
  });

  test('employee can complete OTP login and land on ESS dashboard', async ({
    page,
    consoleGate,
  }) => {
    await installEssMocks(page);

    await page.goto('/ess/login');
    await expect(page.getByRole('heading', { name: /employee self service/i })).toBeVisible();

    await page.getByLabel(/mobile number/i).fill('9876543210');
    await page.getByRole('button', { name: /send otp/i }).click();
    await expect(page.getByRole('heading', { name: /verify otp/i })).toBeVisible();

    await page.getByLabel(/one-time password/i).fill('123456');
    await page.getByRole('button', { name: /verify.*login/i }).click();

    await expect(page).toHaveURL(/\/ess\/dashboard$/);
    await expect(page.getByRole('heading', { name: /welcome, asha rao/i })).toBeVisible();
    await expect(page.getByRole('main').getByRole('link', { name: 'Payslips', exact: true })).toBeVisible();

    expect(consoleGate.getErrors()).toEqual([]);
    expect(consoleGate.getFailedResponses()).toEqual([]);
  });
});

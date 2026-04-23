/**
 * MSW handlers — HTTP mocks for frontend integration tests.
 *
 * Tests exercise page → hook → axios → MSW → response. See CLAUDE.md §10.2.
 *
 * Each handler below is a representative happy path. Tests override per-case
 * using `server.use(rest.get('...', ...))` in individual test files.
 */

import { http, HttpResponse } from 'msw';

const API = 'http://localhost:8001/api/v1';

export const TEST_ORG = {
  id: '11111111-1111-1111-1111-111111111111',
  code: 'HO',
  name: 'Head Office',
};

export const TEST_USER = {
  id: '22222222-2222-2222-2222-222222222222',
  username: 'admin',
  email: 'admin@smfc.example',
  full_name: 'Admin User',
  organization_id: TEST_ORG.id,
  default_unit_id: null,
  mfa_enabled: false,
  roles: [{ id: 'r1', code: 'SUPER_ADMIN', name: 'Super Admin' }],
  permissions: [
    'voucher.post',
    'voucher.create',
    'loan_application.approve',
    'customer.view',
    'account.view',
  ],
};

export const TEST_ACCOUNTS = [
  { id: 'a1', code: '1001', name: 'Cash in Hand', account_type: 'ASSET', nature: 'DEBIT', is_active: true },
  { id: 'a2', code: '1002', name: 'Bank Account - HDFC', account_type: 'ASSET', nature: 'DEBIT', is_active: true },
  { id: 'a3', code: '3001', name: 'Interest Income', account_type: 'INCOME', nature: 'CREDIT', is_active: true },
  { id: 'a4', code: '4001', name: 'Interest Expense', account_type: 'EXPENSE', nature: 'DEBIT', is_active: true },
];

export const TEST_CUSTOMERS = [
  { id: 'c1', customer_code: 'CUST0001', customer_name: 'Acme Industries', is_active: true, customer_type: 'B2B' },
  { id: 'c2', customer_code: 'CUST0002', customer_name: 'Beta Traders', is_active: true, customer_type: 'B2B' },
];

export const TEST_PERIODS = [
  { id: 'p1', code: 'FY26-APR', name: 'Apr 2026', start_date: '2026-04-01', end_date: '2026-04-30', status: 'OPEN' },
  { id: 'p2', code: 'FY26-MAY', name: 'May 2026', start_date: '2026-05-01', end_date: '2026-05-31', status: 'OPEN' },
];

export const handlers = [
  // Auth
  http.post(`${API}/auth/login`, async () => {
    return HttpResponse.json({
      access_token: 'test-access-token',
      refresh_token: 'test-refresh-token',
      token_type: 'bearer',
      expires_in: 900,
    });
  }),
  http.post(`${API}/auth/refresh`, async () => {
    return HttpResponse.json({
      access_token: 'test-access-token-rotated',
      refresh_token: 'test-refresh-token-rotated',
      token_type: 'bearer',
      expires_in: 900,
    });
  }),
  http.post(`${API}/auth/logout`, () =>
    HttpResponse.json({ message: 'Successfully logged out' }),
  ),
  http.get(`${API}/auth/me`, () => HttpResponse.json(TEST_USER)),

  // Organizations
  http.get(`${API}/organizations`, () =>
    HttpResponse.json({ items: [TEST_ORG], total: 1, skip: 0, limit: 50 }),
  ),

  // Accounts
  http.get(`${API}/accounts`, () =>
    HttpResponse.json({ items: TEST_ACCOUNTS, total: TEST_ACCOUNTS.length }),
  ),

  // Financial years (needed by usePeriods)
  http.get(`${API}/financial-years`, () =>
    HttpResponse.json({
      items: [
        {
          id: 'fy1',
          code: 'FY26',
          name: '2026-27',
          start_date: '2026-04-01',
          end_date: '2027-03-31',
          status: 'OPEN',
          periods: TEST_PERIODS,
        },
      ],
      total: 1,
    }),
  ),

  // Customers
  http.get(`${API}/customers`, () =>
    HttpResponse.json({ items: TEST_CUSTOMERS, total: TEST_CUSTOMERS.length }),
  ),
  http.get(`${API}/customers/:id`, ({ params }) => {
    const c = TEST_CUSTOMERS.find((x) => x.id === params.id);
    if (!c) {
      return HttpResponse.json(
        { error_code: 'NOT_FOUND', message: 'Customer not found' },
        { status: 404 },
      );
    }
    return HttpResponse.json(c);
  }),

  // Vouchers (create / submit)
  http.post(`${API}/vouchers`, async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    return HttpResponse.json({
      id: 'v-new',
      voucher_number: 'VCH/2026/0001',
      ...body,
      status: 'DRAFT',
      version: 1,
    });
  }),
  http.post(`${API}/vouchers/:id/submit`, ({ params }) =>
    HttpResponse.json({ id: params.id, status: 'SUBMITTED' }),
  ),

  // Roles
  http.get(`${API}/roles`, () =>
    HttpResponse.json({
      items: [
        { id: 'r1', code: 'SUPER_ADMIN', name: 'Super Admin' },
        { id: 'r2', code: 'FINANCE_MANAGER', name: 'Finance Manager' },
      ],
      total: 2,
    }),
  ),
];

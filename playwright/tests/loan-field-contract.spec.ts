import { expect, request, test } from '@playwright/test';

const env =
  (globalThis as { process?: { env?: Record<string, string | undefined> } }).process?.env ?? {};
const API_BASE = env.PLAYWRIGHT_API_BASE || 'http://localhost:8001/api/v1';
const ADMIN_USERNAME = env.UAT_ADMIN_USERNAME || 'krishna';
const ADMIN_PASSWORD = env.UAT_ADMIN_PASSWORD || 'ChangeMe123!';
const LIVE_BACKEND_ENABLED = env.PLAYWRIGHT_LIVE_BACKEND === '1';

interface EndpointContract {
  name: string;
  path: string;
  expectedKeys: string[];
  forbiddenKeys: string[];
}

const LIST_CONTRACTS: EndpointContract[] = [
  {
    name: 'LOS entities',
    path: '/lending/entities?page=1&pageSize=5',
    expectedKeys: ['id', 'entityCode', 'legalName', 'tradeName', 'entityType', 'status'],
    forbiddenKeys: ['entity_id', 'entity_code', 'entity_type'],
  },
  {
    name: 'LOS products',
    path: '/lending/products?page=1&pageSize=5',
    expectedKeys: ['id', 'code', 'name', 'category', 'interestType'],
    forbiddenKeys: [
      'product_id',
      'product_code',
      'product_name',
      'product_category',
      'interest_type',
    ],
  },
  {
    name: 'LOS applications',
    path: '/lending/applications?page=1&pageSize=5',
    expectedKeys: ['id', 'applicationNumber', 'entityName', 'requestedAmount', 'status'],
    forbiddenKeys: ['application_id', 'application_number', 'entity_name', 'requested_amount'],
  },
  {
    name: 'LOS sanctions',
    path: '/lending/sanctions?page=1&pageSize=5',
    expectedKeys: ['id', 'sanctionNumber', 'entityName', 'sanctionedAmount', 'status'],
    forbiddenKeys: ['sanction_id', 'sanction_number', 'entity_name', 'sanctioned_amount'],
  },
  {
    name: 'LMS accounts',
    path: '/lending/loan-accounts?page=1&pageSize=5',
    expectedKeys: ['id', 'loanAccountNumber', 'entityName', 'sanctionedAmount', 'status'],
    forbiddenKeys: ['loan_account_id', 'loan_account_number', 'entity_name', 'sanctioned_amount'],
  },
  {
    name: 'Treasury lenders',
    path: '/lending/treasury/lenders?page=1&pageSize=5',
    expectedKeys: ['id', 'lenderCode', 'lenderName', 'lenderType', 'status'],
    forbiddenKeys: ['lender_id', 'lender_code', 'lender_name', 'lender_type'],
  },
  {
    name: 'Treasury borrowings',
    path: '/lending/treasury/borrowings?page=1&pageSize=5',
    expectedKeys: ['id', 'borrowingNumber', 'lenderName', 'sanctionedAmount', 'status'],
    forbiddenKeys: ['borrowing_id', 'borrowing_number', 'lender_name', 'sanctioned_amount'],
  },
];

async function adminToken() {
  const ctx = await request.newContext();
  const response = await ctx.post(`${API_BASE}/auth/login`, {
    data: { username: ADMIN_USERNAME, password: ADMIN_PASSWORD },
  });
  expect(response.ok(), await response.text()).toBeTruthy();
  const body = await response.json();
  await ctx.dispose();
  return (body.accessToken ?? body.access_token) as string;
}

function listItems(payload: unknown): Record<string, unknown>[] {
  if (Array.isArray(payload)) return payload as Record<string, unknown>[];
  const items = (payload as { items?: unknown }).items;
  expect(Array.isArray(items), `Expected paginated list with items[]`).toBeTruthy();
  return items as Record<string, unknown>[];
}

test.describe('loan API field contracts', () => {
  test.skip(
    !LIVE_BACKEND_ENABLED,
    'Set PLAYWRIGHT_LIVE_BACKEND=1 to run the live loan API contract suite.',
  );

  test('representative loan list endpoints emit one camelCase contract', async () => {
    const token = await adminToken();
    const ctx = await request.newContext({
      extraHTTPHeaders: { Authorization: `Bearer ${token}` },
    });

    for (const contract of LIST_CONTRACTS) {
      const response = await ctx.get(`${API_BASE}${contract.path}`);
      expect(
        response.ok(),
        `${contract.name}: ${response.status()} ${await response.text()}`,
      ).toBeTruthy();
      const payload = await response.json();
      const items = listItems(payload);
      expect(items.length, `${contract.name} should have seeded UAT data`).toBeGreaterThan(0);
      const sample = items[0];

      for (const key of contract.expectedKeys) {
        expect(sample, `${contract.name} missing ${key}`).toHaveProperty(key);
      }
      for (const key of contract.forbiddenKeys) {
        expect(sample, `${contract.name} leaked ${key}`).not.toHaveProperty(key);
      }
    }

    await ctx.dispose();
  });
});

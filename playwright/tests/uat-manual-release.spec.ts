import type { Buffer as NodeBuffer } from 'node:buffer';

import { expect, request as pwRequest, test, type Page } from '@playwright/test';

const env =
  (globalThis as { process?: { env?: Record<string, string | undefined> } }).process?.env ?? {};
const API_BASE = env.PLAYWRIGHT_API_BASE || 'http://localhost:8001/api/v1';
const ADMIN_USERNAME = env.UAT_ADMIN_USERNAME || 'krishna';
const ADMIN_PASSWORD = env.UAT_ADMIN_PASSWORD || 'ChangeMe123!';
const PORTAL_EMAIL = env.UAT_PORTAL_EMAIL || 'borrower.portal.uat@smfc.com';
const PORTAL_PASSWORD = env.UAT_PORTAL_PASSWORD || 'Portal@123';
const UAT_ORGANIZATION_CODE = env.UAT_ORGANIZATION_CODE || 'SMFC_UAT';
const LIVE_BACKEND_ENABLED = env.PLAYWRIGHT_LIVE_BACKEND === '1';
const nodeBuffer = (
  globalThis as typeof globalThis & {
    Buffer?: { from(value: string): NodeBuffer };
  }
).Buffer;

const ADMIN_RELEASE_ROUTES = [
  '/admin',
  '/admin/profile',
  '/admin/organizations',
  '/admin/organizations/new',
  '/admin/units',
  '/admin/units/new',
  '/admin/departments',
  '/admin/departments/new',
  '/admin/designations',
  '/admin/designations/new',
  '/admin/users',
  '/admin/users/new',
  '/admin/roles',
  '/admin/roles/new',
  '/admin/lending',
  '/admin/lending/entities',
  '/admin/lending/entities/new',
  '/admin/lending/products',
  '/admin/lending/products/new',
  '/admin/lending/applications',
  '/admin/lending/applications/new',
  '/admin/lending/sanctions',
  '/admin/lending/sanctions/new',
  '/admin/lending/accounts',
  '/admin/lending/disbursements',
  '/admin/lending/disbursements/new',
  '/admin/lending/disbursement-readiness',
  '/admin/lending/receipts',
  '/admin/lending/receipts/new',
  '/admin/lending/collection-cockpit',
  '/admin/lending/collections/cockpit',
  '/admin/lending/collections/followups',
  '/admin/lending/risk-cockpit',
  '/admin/lending/closure-cockpit',
  '/admin/lending/collections/npa',
  '/admin/lending/collections/ots',
  '/admin/lending/collections/ots/new',
  '/admin/lending/collections/legal',
  '/admin/lending/reports',
  '/admin/lending/reports/collections/cockpit',
  '/admin/lending/reports/risk',
  '/admin/lending/reports/portfolio/aum',
  '/admin/lending/reports/collections/efficiency',
  '/admin/lending/reports/npa/movement',
  '/admin/lending/checklist/templates',
  '/admin/lending/checklist/templates/new',
  '/admin/lending/iif/schemes',
  '/admin/lending/iif/schemes/new',
  '/admin/lending/iif/categories',
  '/admin/lending/iif/categories/new',
  '/admin/lending/iif/enrollments',
  '/admin/lending/iif/claims',
  '/admin/lending/npa',
  '/admin/lending/npa/dashboard',
  '/admin/lending/schedules/generate',
  '/admin/lending/receipts/create',
  '/admin/lending/disbursements/create',
  '/admin/lending/collaterals',
  '/admin/lending/collaterals/create',
  '/admin/lending/receipts-enhanced',
  '/admin/lending/receipts/bulk-upload',
  '/admin/lending/disbursements-enhanced',
  '/admin/lending/disbursements/approval',
  '/admin/lending/emi-calculator',
  '/admin/lending/treasury/lenders',
  '/admin/lending/treasury/borrowings',
  '/admin/lending/treasury/source-of-funds',
  '/admin/lending/treasury/alm',
  '/admin/lending/treasury/alm/gap-analysis',
  '/admin/lending/treasury/alm/interest-rate-risk',
  '/admin/treasury',
  '/admin/treasury/lenders',
  '/admin/treasury/lenders/new',
  '/admin/treasury/borrowings',
  '/admin/treasury/borrowings/new',
  '/admin/treasury/source-of-funds',
  '/admin/treasury/alm',
  '/admin/treasury/alm/gap',
  '/admin/treasury/alm/irs',
  '/admin/treasury/risk-dashboard',
  '/admin/treasury/investments',
  '/admin/treasury/investments/new',
  '/admin/regulatory/crar',
  '/admin/regulatory/exposure',
  '/admin/regulatory/infrastructure',
  '/admin/regulatory/returns',
  '/admin/workflow/definitions',
  '/admin/workflow/definitions/new',
  '/admin/workflow/tasks',
  '/admin/workflow/instances',
  '/admin/compliance',
  '/admin/compliance/items',
  '/admin/legal',
  '/admin/legal/law-firms',
  '/admin/legal/advocates',
  '/admin/legal/cases',
  '/admin/legal/notices',
  '/admin/legal/expenses',
  '/admin/dms',
  '/admin/dms/folders',
  '/admin/dms/upload',
  '/admin/dms/search',
  '/admin/dms/tags',
];

const ADMIN_RELEASE_DETAIL_ROUTES = [
  { path: '/admin/organizations/:organizationId/edit', resource: 'organization' },
  { path: '/admin/organizations/:organizationId/addresses', resource: 'organization' },
  { path: '/admin/organizations/:organizationId/addresses/new', resource: 'organization' },
  { path: '/admin/organizations/:organizationId/bank-accounts', resource: 'organization' },
  { path: '/admin/organizations/:organizationId/bank-accounts/new', resource: 'organization' },
  { path: '/admin/units/:unitId/edit', resource: 'unit' },
  { path: '/admin/departments/:departmentId/edit', resource: 'department' },
  { path: '/admin/designations/:designationId/edit', resource: 'designation' },
  { path: '/admin/users/:userId/edit', resource: 'user' },
  { path: '/admin/roles/:roleId/edit', resource: 'role' },
  { path: '/admin/lending/entities/:entityId', resource: 'entity' },
  { path: '/admin/lending/entities/:entityId/edit', resource: 'entity' },
  { path: '/admin/lending/products/:productId', resource: 'product' },
  { path: '/admin/lending/products/:productId/edit', resource: 'product' },
  { path: '/admin/lending/applications/:applicationId', resource: 'application' },
  { path: '/admin/lending/applications/:applicationId/edit', resource: 'application' },
  { path: '/admin/lending/sanctions/:sanctionId', resource: 'sanction' },
  { path: '/admin/lending/sanctions/:sanctionId/edit', resource: 'sanction' },
  { path: '/admin/lending/sanctions/:sanctionId/letter', resource: 'sanction' },
  { path: '/admin/lending/accounts/:loanAccountId', resource: 'loanAccount' },
  { path: '/admin/lending/iif/schemes/:iifSchemeId', resource: 'iifScheme' },
  { path: '/admin/lending/iif/categories/:iifCategoryId', resource: 'iifCategory' },
  { path: '/admin/lending/iif/claims/:iifClaimId', resource: 'iifClaim' },
  {
    path: '/admin/lending/checklist/templates/:checklistTemplateId',
    resource: 'checklistTemplate',
  },
  { path: '/admin/dms/documents/:documentId', resource: 'document' },
  { path: '/admin/dms/documents/:documentId/versions', resource: 'document' },
  { path: '/admin/treasury/lenders/:lenderId', resource: 'lender' },
  { path: '/admin/treasury/lenders/:lenderId/edit', resource: 'lender' },
  { path: '/admin/treasury/borrowings/:borrowingId', resource: 'borrowing' },
  { path: '/admin/treasury/borrowings/:borrowingId/edit', resource: 'borrowing' },
  { path: '/admin/treasury/investments/:investmentId', resource: 'investment' },
  { path: '/admin/workflow/definitions/:workflowDefinitionId', resource: 'workflowDefinition' },
  {
    path: '/admin/workflow/definitions/:workflowDefinitionId/edit',
    resource: 'workflowDefinition',
  },
] as const;

const ERP_DEFAULT_VISIBILITY_ROUTES = [
  '/admin/finance/vouchers',
  '/admin/gst/rates',
  '/admin/tds/sections',
  '/admin/ap-ar/vendors',
  '/admin/portal/users',
  '/admin/portal/registrations',
  '/admin/notifications',
  '/admin/notifications/templates',
  '/admin/lending/nach/batches',
  '/admin/lending/nach/batches/new',
  '/admin/lending/nach/retry',
  '/admin/lending/aa/consents',
  '/admin/lending/aa/consents/new',
  '/admin/lending/aa/fetched-data',
  '/admin/lending/repayment-matching',
  '/admin/lending/collections/repayment-matching',
  '/admin/settings/integrations',
];

const PORTAL_ROUTES = [
  '/portal/workbench',
  '/portal/applications',
  '/portal/applications/new',
  '/portal/reports',
  '/portal/claims',
  '/portal/dashboard',
  '/portal/loans',
  '/portal/documents',
  '/portal/payments',
  '/portal/support',
];

interface AdminSession {
  accessToken: string;
  refreshToken: string;
  user: {
    organization_id?: string | null;
    organizationId?: string | null;
  };
}

interface PortalSession {
  accessToken: string;
  refreshToken: string;
  user: unknown;
}

interface PortalApplicationListResponse {
  items: {
    id: string;
    applicationNumber: string;
    entityId: string;
  }[];
}

interface PortalApplicationDetailResponse {
  id: string;
  applicationNumber: string;
  entityId: string;
  requestedAmount: string;
  schemeStatus: string;
  documentRequirements?: {
    code: string;
    name: string;
    isMandatory: boolean;
    missing: boolean;
  }[];
}

interface PortalProductResponse {
  id: string;
  name: string;
}

interface PortalUtilizationCategoryResponse {
  id: string;
  label: string;
}

interface PortalApplicationDocumentResponse {
  id: string;
  fileName: string;
  documentCode?: string;
}

type AdminResourceKey = (typeof ADMIN_RELEASE_DETAIL_ROUTES)[number]['resource'];

type AdminResourceIds = Partial<Record<AdminResourceKey, string>>;

function uploadBuffer(contents: string): NodeBuffer {
  if (!nodeBuffer) {
    throw new Error('Node Buffer is required for Playwright multipart uploads');
  }
  return nodeBuffer.from(contents);
}

async function adminLogin(): Promise<AdminSession> {
  const ctx = await pwRequest.newContext();
  const response = await ctx.post(`${API_BASE}/auth/login`, {
    data: { username: ADMIN_USERNAME, password: ADMIN_PASSWORD },
  });
  if (!response.ok()) {
    throw new Error(`Admin login failed: ${response.status()} ${await response.text()}`);
  }
  const body = await response.json();
  await ctx.dispose();
  return {
    accessToken: body.accessToken ?? body.access_token,
    refreshToken: body.refreshToken ?? body.refresh_token,
    user: body.user ?? {},
  };
}

async function portalLogin(): Promise<PortalSession> {
  const ctx = await pwRequest.newContext();
  const response = await ctx.post(`${API_BASE}/portal/auth/login/password`, {
    data: {
      email: PORTAL_EMAIL,
      password: PORTAL_PASSWORD,
      device_info: { device_type: 'WEB', device_name: 'Manual UAT' },
    },
  });
  if (!response.ok()) {
    throw new Error(`Portal login failed: ${response.status()} ${await response.text()}`);
  }
  const body = await response.json();
  await ctx.dispose();
  return {
    accessToken: body.access_token ?? body.session_token,
    refreshToken: body.refresh_token,
    user: body.user,
  };
}

async function installAdminSession(page: Page, session: AdminSession): Promise<void> {
  const orgId = session.user.organization_id ?? session.user.organizationId ?? null;
  await page.addInitScript(
    ({ accessToken, refreshToken, activeOrganizationId }) => {
      window.localStorage.setItem(
        'smfc-auth',
        JSON.stringify({
          state: { accessToken, refreshToken },
          version: 0,
        }),
      );
      window.localStorage.setItem(
        'smfc-organization',
        JSON.stringify({
          state: { activeOrganizationId },
          version: 0,
        }),
      );
    },
    {
      accessToken: session.accessToken,
      refreshToken: session.refreshToken,
      activeOrganizationId: orgId,
    },
  );
}

async function createAdminRequestContext(session: AdminSession) {
  return pwRequest.newContext({
    extraHTTPHeaders: {
      Authorization: `Bearer ${session.accessToken}`,
    },
  });
}

function firstIdFromListResponse(body: unknown): string | undefined {
  return firstRecordFromListResponse(body)?.id;
}

function firstRecordFromListResponse(body: unknown): Record<string, string> | undefined {
  if (Array.isArray(body)) {
    const first = body[0] as Record<string, string> | undefined;
    return typeof first?.id === 'string' ? first : undefined;
  }

  if (!body || typeof body !== 'object') return undefined;

  const payload = body as Record<string, unknown>;
  const items = payload.items;
  if (Array.isArray(items)) {
    const first = items[0] as Record<string, string> | undefined;
    return typeof first?.id === 'string' ? first : undefined;
  }

  const data = payload.data;
  if (Array.isArray(data)) {
    const first = data[0] as Record<string, string> | undefined;
    return typeof first?.id === 'string' ? first : undefined;
  }

  return undefined;
}

function listRecordsFromResponse(body: unknown): Record<string, string>[] {
  if (Array.isArray(body)) return body as Record<string, string>[];
  if (!body || typeof body !== 'object') return [];
  const payload = body as Record<string, unknown>;
  if (Array.isArray(payload.items)) return payload.items as Record<string, string>[];
  if (Array.isArray(payload.data)) return payload.data as Record<string, string>[];
  return [];
}

async function discoverAdminResourceIds(session: AdminSession): Promise<AdminResourceIds> {
  const ctx = await createAdminRequestContext(session);
  const firstId = async (path: string): Promise<string | undefined> => {
    const response = await ctx.get(`${API_BASE}${path}`);
    if (!response.ok()) return undefined;
    return firstIdFromListResponse(await response.json());
  };
  const organizationResponse = await ctx.get(`${API_BASE}/organizations?page=1&pageSize=25`);
  const organizationRows = organizationResponse.ok()
    ? listRecordsFromResponse(await organizationResponse.json())
    : [];
  const organizationId =
    organizationRows.find((row) => row.code === UAT_ORGANIZATION_CODE)?.id ??
    firstRecordFromListResponse({ items: organizationRows })?.id;

  const ids: AdminResourceIds = {
    organization: organizationId,
    unit: await firstId('/units?page=1&pageSize=1'),
    department: await firstId('/departments?page=1&pageSize=1'),
    designation: await firstId('/designations?page=1&pageSize=1'),
    user: await firstId('/users?page=1&pageSize=1'),
    role: await firstId('/roles?page=1&pageSize=1'),
    entity: await firstId('/lending/entities?page=1&pageSize=1'),
    product: await firstId('/lending/products?page=1&pageSize=1'),
    application: await firstId('/lending/applications?page=1&pageSize=1'),
    sanction: await firstId('/lending/sanctions?page=1&pageSize=1'),
    loanAccount: await firstId('/lending/loan-accounts?page=1&pageSize=1'),
    iifScheme: await firstId('/lending/iif/schemes?page=1&pageSize=1'),
    iifCategory: await firstId('/lending/iif/categories?page=1&pageSize=1'),
    iifClaim: await firstId('/lending/iif/claims?page=1&pageSize=1'),
    checklistTemplate: await firstId('/lending/checklist/templates?page=1&pageSize=1'),
    document: await firstId('/dms/documents/recent?limit=1'),
    lender: await firstId('/lending/treasury/lenders?page=1&pageSize=1'),
    borrowing: await firstId('/lending/treasury/borrowings?page=1&pageSize=1'),
    investment: await firstId('/lending/treasury/investments?page=1&pageSize=1'),
    workflowDefinition: organizationId
      ? await firstId(`/workflows/definitions?page=1&pageSize=1&organization_id=${organizationId}`)
      : undefined,
  };

  await ctx.dispose();
  return ids;
}

function resolveAdminDetailRoute(
  route: (typeof ADMIN_RELEASE_DETAIL_ROUTES)[number],
  ids: AdminResourceIds,
): string {
  const id = ids[route.resource];
  if (!id) {
    throw new Error(`Seed data missing for ${route.resource}; cannot open ${route.path}`);
  }
  return route.path.replace(/:[A-Za-z0-9_]+/g, id);
}

async function installPortalSession(page: Page, session: PortalSession): Promise<void> {
  await page.addInitScript(({ accessToken, refreshToken, user }) => {
    window.localStorage.setItem('portal_access_token', accessToken);
    window.localStorage.setItem('portal_refresh_token', refreshToken);
    window.localStorage.setItem('portal_user', JSON.stringify(user));
  }, session);
}

async function createPortalRequestContext(session: PortalSession) {
  return pwRequest.newContext({
    extraHTTPHeaders: {
      Authorization: `Bearer ${session.accessToken}`,
    },
  });
}

async function assertRouteClean(page: Page, route: string): Promise<void> {
  const consoleErrors: string[] = [];
  const failedResponses: string[] = [];

  page.on('console', (message) => {
    if (message.type() !== 'error') return;
    const text = message.text();
    if (/favicon|ResizeObserver loop|The width\(0\) and height\(0\) of chart/i.test(text)) {
      return;
    }
    consoleErrors.push(text);
  });
  page.on('pageerror', (error) => {
    consoleErrors.push(`uncaught: ${error.message}`);
  });
  page.on('response', (response) => {
    const url = response.url();
    const status = response.status();
    if (status < 400) return;
    if (/\.(ico|png|jpg|jpeg|gif|svg|map|woff2?|ttf)(\?.*)?$/.test(url)) return;
    failedResponses.push(`${status} ${url.replace(/^https?:\/\/[^/]+/, '')}`);
  });
  page.on('requestfailed', (request) => {
    const url = request.url();
    const errorText = request.failure()?.errorText ?? 'unknown';
    if (/\.(ico|png|jpg|jpeg|gif|svg|map|woff2?|ttf)(\?.*)?$/.test(url)) return;
    if (/\/api\/v1\/bi\/dashboards\/landing(?:\?.*)?$/.test(url)) return;
    if (/ERR_ABORTED/i.test(errorText)) return;
    failedResponses.push(`request failed ${errorText} ${url.replace(/^https?:\/\/[^/]+/, '')}`);
  });

  await page.goto(route, { waitUntil: 'domcontentloaded' });
  try {
    await page.waitForLoadState('networkidle', { timeout: 8000 });
  } catch {
    // Long-running queries are acceptable; API failures are captured above.
  }
  await page.waitForTimeout(250);

  await expect(page.locator('#root'), `${route} app root`).toBeVisible();
  await expect(page.locator('#root'), `${route} app errors`).not.toContainText(
    /something went wrong|failed to load/i,
  );
  expect(failedResponses, `${route} API failures`).toEqual([]);
  expect(consoleErrors, `${route} console errors`).toEqual([]);
}

test.describe('manual release UAT readiness', () => {
  test.skip(
    !LIVE_BACKEND_ENABLED,
    'Set PLAYWRIGHT_LIVE_BACKEND=1 to run the live UAT release suite.',
  );

  test('admin release routes render without API or console failures', async ({ page }) => {
    test.setTimeout(180_000);
    const session = await adminLogin();
    await installAdminSession(page, session);

    for (const route of ADMIN_RELEASE_ROUTES) {
      await assertRouteClean(page, route);
    }
  });

  test('admin detail and edit routes render seeded records cleanly', async ({ page }) => {
    test.setTimeout(120_000);
    const session = await adminLogin();
    const ids = await discoverAdminResourceIds(session);
    await installAdminSession(page, session);

    for (const routeSpec of ADMIN_RELEASE_DETAIL_ROUTES) {
      await assertRouteClean(page, resolveAdminDetailRoute(routeSpec, ids));
    }
  });

  test('full ERP routes remain visible in default release mode', async ({ page }) => {
    const session = await adminLogin();
    await installAdminSession(page, session);

    for (const route of ERP_DEFAULT_VISIBILITY_ROUTES) {
      await page.goto(route, { waitUntil: 'domcontentloaded' });
      await expect(page).not.toHaveURL(/\/admin\/lending(\/)?$/);
      await expect(page).not.toHaveURL(/\/login$/);
      await expect(page.locator('#root'), `${route} app root`).toBeVisible();
    }
  });

  test('portal borrower routes render with seeded borrower access', async ({ page }) => {
    test.setTimeout(90_000);
    const session = await portalLogin();
    await installPortalSession(page, session);

    for (const route of PORTAL_ROUTES) {
      await assertRouteClean(page, route);
    }
  });

  test('portal borrower can apply, upload/download documents, view status, and download reports', async ({
    page,
  }) => {
    const session = await portalLogin();
    const ctx = await createPortalRequestContext(session);
    await installPortalSession(page, session);

    const existingApplicationsResponse = await ctx.get(
      `${API_BASE}/portal/applications?pageSize=1`,
    );
    expect(existingApplicationsResponse.ok()).toBeTruthy();
    const existingApplications =
      (await existingApplicationsResponse.json()) as PortalApplicationListResponse;
    expect(existingApplications.items.length).toBeGreaterThan(0);
    const entityId = existingApplications.items[0]!.entityId;

    const productsResponse = await ctx.get(`${API_BASE}/portal/products?entityId=${entityId}`);
    expect(productsResponse.ok()).toBeTruthy();
    const products = (await productsResponse.json()) as PortalProductResponse[];
    expect(products.length).toBeGreaterThan(0);

    const categoriesResponse = await ctx.get(`${API_BASE}/portal/utilization-categories`);
    expect(categoriesResponse.ok()).toBeTruthy();
    const categories = (await categoriesResponse.json()) as PortalUtilizationCategoryResponse[];
    expect(categories.length).toBeGreaterThan(0);

    const requestedAmount = '12500000.00';
    const createResponse = await ctx.post(`${API_BASE}/portal/applications`, {
      headers: { 'Idempotency-Key': crypto.randomUUID() },
      data: {
        entityId,
        productId: products[0]!.id,
        requestedAmount,
        tenureMonths: 36,
        purposeDescription: 'UAT borrower self-service application',
        projectName: 'UAT Port Automation Upgrade',
        projectLocation: 'Mumbai Port',
        projectCost: requestedAmount,
        shipyardName: 'UAT Shipyard',
        maritimeSegment: 'Port infrastructure',
        lenderName: 'State Bank of India',
        lenderBranch: 'Mumbai Corporate Branch',
        sanctionReference: `UAT-${Date.now()}`,
        declarationAccepted: true,
        fundUtilization: [
          {
            categoryId: categories[0]!.id,
            amount: requestedAmount,
            remarks: 'UAT self-service application flow',
          },
        ],
      },
    });
    expect(createResponse.ok(), await createResponse.text()).toBeTruthy();
    const draft = (await createResponse.json()) as PortalApplicationDetailResponse;
    expect(draft.schemeStatus).toBe('DRAFT');

    const requirements = (draft.documentRequirements ?? []).filter(
      (requirement) => requirement.isMandatory,
    );
    const uploadCodes =
      requirements.length > 0
        ? requirements.map((requirement) => requirement.code)
        : ['BORROWER_UPLOAD'];
    const uploadedDocumentIds: string[] = [];

    for (const documentCode of uploadCodes) {
      const uploadResponse = await ctx.post(
        `${API_BASE}/portal/applications/${draft.id}/documents/upload`,
        {
          headers: { 'Idempotency-Key': crypto.randomUUID() },
          multipart: {
            document_code: documentCode,
            document_name: `UAT ${documentCode}`,
            file: {
              name: `${documentCode.toLowerCase()}-uat.pdf`,
              mimeType: 'application/pdf',
              buffer: uploadBuffer('%PDF-1.4\n% UAT portal document\n%%EOF\n'),
            },
          },
        },
      );
      expect(uploadResponse.ok(), await uploadResponse.text()).toBeTruthy();
      const uploaded = (await uploadResponse.json()) as PortalApplicationDocumentResponse;
      uploadedDocumentIds.push(uploaded.id);
    }

    const documentsResponse = await ctx.get(
      `${API_BASE}/portal/applications/${draft.id}/documents`,
    );
    expect(documentsResponse.ok()).toBeTruthy();
    const documents = (await documentsResponse.json()) as PortalApplicationDocumentResponse[];
    expect(documents.length).toBeGreaterThanOrEqual(uploadedDocumentIds.length);

    const downloadResponse = await ctx.get(
      `${API_BASE}/portal/applications/${draft.id}/documents/${uploadedDocumentIds[0]}/download`,
    );
    expect(downloadResponse.ok(), await downloadResponse.text()).toBeTruthy();
    expect(downloadResponse.headers()['content-type']).toContain('application/pdf');

    const submitResponse = await ctx.post(`${API_BASE}/portal/applications/${draft.id}/submit`, {
      headers: { 'Idempotency-Key': crypto.randomUUID() },
    });
    expect(submitResponse.ok(), await submitResponse.text()).toBeTruthy();
    const submitted = (await submitResponse.json()) as PortalApplicationDetailResponse;
    expect(submitted.schemeStatus).toBe('LENDER_REVIEW');

    const reportResponse = await ctx.get(`${API_BASE}/portal/reports/summary.csv`);
    expect(reportResponse.ok(), await reportResponse.text()).toBeTruthy();
    expect(await reportResponse.text()).toContain('Applications');

    await assertRouteClean(page, `/portal/applications/${submitted.id}`);
    await expect(page.getByRole('heading', { name: submitted.applicationNumber })).toBeVisible();
    await expect(page.getByText('LENDER REVIEW', { exact: false })).toHaveCount(2);

    await page.goto('/portal/reports', { waitUntil: 'domcontentloaded' });
    await page.waitForLoadState('networkidle');
    const download = await Promise.all([
      page.waitForEvent('download'),
      page.getByRole('button', { name: 'Download CSV' }).click(),
    ]);
    expect(download[0].suggestedFilename()).toContain('scheme-portal-report');

    await ctx.dispose();
  });
});

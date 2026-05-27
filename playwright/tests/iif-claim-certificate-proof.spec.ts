import { randomUUID } from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';

import {
  expect,
  request as pwRequest,
  test,
  type APIRequestContext,
  type APIResponse,
  type Page,
} from '@playwright/test';

const API_BASE = process.env.PLAYWRIGHT_API_BASE || 'http://localhost:8001/api/v1';
const ADMIN_USERNAME = process.env.UAT_ADMIN_USERNAME || 'krishna';
const ADMIN_PASSWORD = process.env.UAT_ADMIN_PASSWORD || 'ChangeMe123!';
const PORTAL_EMAIL = process.env.UAT_PORTAL_EMAIL || 'borrower.portal.uat@smfc.com';
const PORTAL_PASSWORD = process.env.UAT_PORTAL_PASSWORD || 'Portal@123';
const CLAIM_REFERENCE = process.env.UAT_IIF_CLAIM_REFERENCE || 'UAT/IIF/2026Q1/00001';

interface AdminSession {
  accessToken: string;
  refreshToken: string;
  user: Record<string, unknown>;
}

interface PortalSession {
  accessToken: string;
  refreshToken: string;
  user: Record<string, unknown>;
}

interface ClaimRow {
  id: string;
  claimReference: string;
  status: string;
}

async function adminLogin(): Promise<AdminSession> {
  const ctx = await pwRequest.newContext();
  const response = await ctx.post(`${API_BASE}/auth/login`, {
    data: { username: ADMIN_USERNAME, password: ADMIN_PASSWORD },
  });
  expect(
    response.ok(),
    `Admin login failed: ${response.status()} ${await response.text()}`,
  ).toBeTruthy();
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
      device_info: { device_type: 'WEB', device_name: 'IIF claim proof' },
    },
  });
  expect(
    response.ok(),
    `Portal login failed: ${response.status()} ${await response.text()}`,
  ).toBeTruthy();
  const body = await response.json();
  await ctx.dispose();
  return {
    accessToken: body.access_token ?? body.session_token,
    refreshToken: body.refresh_token,
    user: body.user ?? {},
  };
}

async function adminContext(session: AdminSession): Promise<APIRequestContext> {
  return pwRequest.newContext({
    extraHTTPHeaders: { Authorization: `Bearer ${session.accessToken}` },
  });
}

async function portalContext(session: PortalSession): Promise<APIRequestContext> {
  return pwRequest.newContext({
    extraHTTPHeaders: { Authorization: `Bearer ${session.accessToken}` },
  });
}

async function installAdminSession(page: Page, session: AdminSession): Promise<void> {
  const orgId = session.user.organization_id ?? session.user.organizationId ?? null;
  await page.addInitScript(
    ({ accessToken, refreshToken, activeOrganizationId }) => {
      window.localStorage.setItem(
        'smfc-auth',
        JSON.stringify({ state: { accessToken, refreshToken }, version: 0 }),
      );
      window.localStorage.setItem(
        'smfc-organization',
        JSON.stringify({ state: { activeOrganizationId }, version: 0 }),
      );
    },
    {
      accessToken: session.accessToken,
      refreshToken: session.refreshToken,
      activeOrganizationId: orgId,
    },
  );
}

async function installPortalSession(page: Page, session: PortalSession): Promise<void> {
  await page.addInitScript(({ accessToken, refreshToken, user }) => {
    window.localStorage.setItem('portal_access_token', accessToken);
    window.localStorage.setItem('portal_refresh_token', refreshToken);
    window.localStorage.setItem('portal_user', JSON.stringify(user));
  }, session);
}

async function findClaim(ctx: APIRequestContext): Promise<ClaimRow> {
  const response = await ctx.get(`${API_BASE}/lending/iif/claims?page=1&pageSize=100`);
  expect(
    response.ok(),
    `Claim list failed: ${response.status()} ${await response.text()}`,
  ).toBeTruthy();
  const body = (await response.json()) as { items?: ClaimRow[] };
  const claim = (body.items ?? []).find((row) => row.claimReference === CLAIM_REFERENCE);
  expect(claim, `Seeded IIF claim ${CLAIM_REFERENCE} was not found`).toBeTruthy();
  return claim!;
}

async function transitionClaimToVerified(
  ctx: APIRequestContext,
  claim: ClaimRow,
): Promise<ClaimRow> {
  let current = claim;
  if (current.status === 'DRAFT') {
    const submit = await ctx.post(`${API_BASE}/lending/iif/claims/${current.id}/submit`, {
      headers: { 'Idempotency-Key': randomUUID() },
      data: {},
    });
    expect(
      submit.ok(),
      `Claim submit failed: ${submit.status()} ${await submit.text()}`,
    ).toBeTruthy();
    current = (await submit.json()) as ClaimRow;
  }
  if (current.status === 'SUBMITTED') {
    const verify = await ctx.post(`${API_BASE}/lending/iif/claims/${current.id}/verify`, {
      headers: { 'Idempotency-Key': randomUUID() },
      data: { decision: 'APPROVE' },
    });
    expect(
      verify.ok(),
      `Claim verification failed: ${verify.status()} ${await verify.text()}`,
    ).toBeTruthy();
    current = (await verify.json()) as ClaimRow;
  }
  expect(
    ['VERIFIED', 'RELEASE_IN_PROGRESS', 'RELEASED'].includes(current.status),
    `Claim must be verified/releasable for certificate generation; got ${current.status}`,
  ).toBeTruthy();
  return current;
}

async function generateCertificate(ctx: APIRequestContext, claimId: string): Promise<void> {
  const response = await ctx.post(
    `${API_BASE}/lending/iif/claims/${claimId}/certificate/generate`,
    {
      headers: { 'Idempotency-Key': randomUUID() },
      data: {},
    },
  );
  expect(
    response.ok(),
    `Certificate generation failed: ${response.status()} ${await response.text()}`,
  ).toBeTruthy();
  const body = (await response.json()) as Record<string, unknown>;
  expect(body.documentType).toBe('IIF_CLAIM_CERTIFICATE');
  expect(body.portalVisible).toBe(true);
}

async function assertPdf(responsePromise: Promise<APIResponse>): Promise<number> {
  const response = await responsePromise;
  expect(
    response.ok(),
    `PDF download failed: ${response.status()} ${await response.text()}`,
  ).toBeTruthy();
  expect(response.headers()['content-type']).toContain('application/pdf');
  const bytes = await response.body();
  expect(bytes.length).toBeGreaterThan(1000);
  expect(bytes.subarray(0, 5).toString()).toBe('%PDF-');
  return bytes.length;
}

function attachStrictPageGuards(page: Page): { errors: string[]; failures: string[] } {
  const errors: string[] = [];
  const failures: string[] = [];
  page.on('console', (message) => {
    if (message.type() !== 'error') return;
    const text = message.text();
    if (/favicon|ResizeObserver loop|The width\(0\) and height\(0\) of chart/i.test(text)) return;
    errors.push(text);
  });
  page.on('pageerror', (error) => errors.push(error.message));
  page.on('response', (response) => {
    const url = response.url();
    if (!url.includes('/api/v1/')) return;
    if (response.status() >= 400) {
      failures.push(`${response.status()} ${url}`);
    }
  });
  return { errors, failures };
}

test.describe('IIF interest subvention claim proof', () => {
  test('admin verifies certificate/report, portal downloads the same claim artifacts', async ({
    page,
  }) => {
    test.setTimeout(120_000);
    await page.setViewportSize({ width: 1920, height: 1080 });
    const proofDir = path.join(process.cwd(), 'test-results', 'iif-claim-proof');
    fs.mkdirSync(proofDir, { recursive: true });

    const guards = attachStrictPageGuards(page);
    const adminSession = await adminLogin();
    const adminApi = await adminContext(adminSession);
    const seededClaim = await findClaim(adminApi);
    const claim = await transitionClaimToVerified(adminApi, seededClaim);
    await generateCertificate(adminApi, claim.id);

    const report = await adminApi.get(`${API_BASE}/lending/iif/claims/${claim.id}/report.csv`);
    expect(
      report.ok(),
      `CSV report failed: ${report.status()} ${await report.text()}`,
    ).toBeTruthy();
    const csvText = await report.text();
    expect(csvText).toContain('Repayment record (per EMI/EPI allocation)');
    expect(csvText).toContain('Installment #,Due date,Installment status');
    expect(csvText).toContain('UAT-RCPT-001-001');
    expect(csvText).toContain('PAID');

    const adminPdfSize = await assertPdf(
      adminApi.get(`${API_BASE}/lending/iif/claims/${claim.id}/certificate.pdf`),
    );

    await installAdminSession(page, adminSession);
    await page.goto(`/admin/lending/iif/claims/${claim.id}`, { waitUntil: 'domcontentloaded' });
    await expect(
      page.getByRole('heading', {
        name: new RegExp(CLAIM_REFERENCE.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')),
      }),
    ).toBeVisible({
      timeout: 10_000,
    });
    await expect(page.getByRole('button', { name: /CSV report/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /XLSX report/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /PDF report/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /Generate SFC certificate/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /^Certificate$/i })).toBeVisible();
    const adminShot = path.join(proofDir, '01-admin-iif-claim-detail.png');
    await page.screenshot({ path: adminShot, fullPage: true });

    const portalSession = await portalLogin();
    const portalApi = await portalContext(portalSession);
    const portalPdfSize = await assertPdf(
      portalApi.get(`${API_BASE}/portal/claims/${claim.id}/certificate.pdf`),
    );
    const portalCsv = await portalApi.get(`${API_BASE}/portal/claims/${claim.id}/report.csv`);
    expect(
      portalCsv.ok(),
      `Portal CSV failed: ${portalCsv.status()} ${await portalCsv.text()}`,
    ).toBeTruthy();
    expect(await portalCsv.text()).toContain('UAT-RCPT-001-001');

    await installPortalSession(page, portalSession);
    await page.goto('/portal/claims', { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('heading', { name: /^Claims$/i })).toBeVisible({
      timeout: 10_000,
    });
    await expect(page.getByText(CLAIM_REFERENCE)).toBeVisible();
    await expect(page.getByRole('button', { name: /^CSV$/i }).first()).toBeVisible();
    await expect(page.getByRole('button', { name: /^XLSX$/i }).first()).toBeVisible();
    await expect(page.getByRole('button', { name: /^PDF$/i }).first()).toBeVisible();
    await expect(page.getByRole('button', { name: /Certificate/i }).first()).toBeVisible();
    await expect(
      page.getByRole('button', { name: /Verify|Initiate release|Mark released/i }),
    ).toHaveCount(0);
    const portalShot = path.join(proofDir, '02-portal-iif-claims.png');
    await page.screenshot({ path: portalShot, fullPage: true });

    await adminApi.dispose();
    await portalApi.dispose();

    expect(adminPdfSize).toBeGreaterThan(1000);
    expect(portalPdfSize).toBeGreaterThan(1000);
    expect(guards.failures, 'API failures during proof navigation').toEqual([]);
    expect(guards.errors, 'Console/page errors during proof navigation').toEqual([]);
  });
});

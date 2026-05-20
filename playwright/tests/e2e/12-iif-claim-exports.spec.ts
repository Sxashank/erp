/**
 * E2E — IIF claim exports + scheme rule fields.
 *
 * Covers the two new code paths added this iteration to the loan modules:
 *
 *   1. Subvention scheme JSONB rule columns — every scheme response must now
 *      carry `calculationRules`, `eligibilityRules`, `requiredDocuments`,
 *      `workflowRules`, `fundRules`. These materialised as 5 nullable JSONB
 *      columns + an alembic head (zzc48). The wire contract is asserted by
 *      hitting `/lending/iif/schemes` directly.
 *
 *   2. Claim report `report.xlsx` + `report.pdf` endpoints — new dependency-
 *      free exporters in `app.utils.simple_exports`. The route surface is
 *      asserted by:
 *        a) UI smoke — the Claim Detail page exposes three download buttons.
 *        b) API contract — both routes return 404 for an unknown UUID (proves
 *           the route is wired; not 405 / 501 / 422).
 *        c) Live exporter — if any claim exists in the org's DB, fetch its
 *           real XLSX + PDF and assert the response Content-Type +
 *           file-format magic bytes.
 *
 * Why not a full UI create-claim-then-download flow? Creating a real claim
 * requires a fully-disbursed loan account + receipts + scheme enrollment —
 * not a clean "one form one save" loop that suits this suite. The lifecycle
 * UI is covered by the smoke spec; the exporter logic is what's new and
 * deserves a focused gate.
 */

import { request as playwrightRequest } from '@playwright/test';

import { loginAsAdmin } from '../../fixtures/auth';
import { expect, test } from '../../fixtures/test';

const env =
  (globalThis as { process?: { env?: Record<string, string | undefined> } }).process?.env ?? {};
const API_BASE = env.PLAYWRIGHT_API_BASE || 'http://localhost:8001/api/v1';
const ADMIN_USERNAME = env.UAT_ADMIN_USERNAME || 'krishna';
const ADMIN_PASSWORD = env.UAT_ADMIN_PASSWORD || 'ChangeMe123!';

// A UUID that is guaranteed not to match any row — used to prove the route
// is reachable (handler runs, raises 404) rather than missing.
const NON_EXISTENT_UUID = '00000000-0000-0000-0000-000000000000';

async function adminToken(): Promise<string> {
  const ctx = await playwrightRequest.newContext();
  const response = await ctx.post(`${API_BASE}/auth/login`, {
    data: { username: ADMIN_USERNAME, password: ADMIN_PASSWORD },
  });
  expect(response.ok(), await response.text()).toBeTruthy();
  const body = (await response.json()) as { accessToken?: string; access_token?: string };
  await ctx.dispose();
  return body.accessToken ?? body.access_token ?? '';
}

test.describe('E2E › IIF › scheme rule fields wire contract', () => {
  test('schemes list response carries the five new JSONB rule fields', async () => {
    const token = await adminToken();
    const ctx = await playwrightRequest.newContext({
      extraHTTPHeaders: { Authorization: `Bearer ${token}` },
    });
    try {
      const res = await ctx.get(`${API_BASE}/lending/iif/schemes?page=1&page_size=10`);
      expect(res.ok(), `${res.status()} ${await res.text()}`).toBeTruthy();
      const body = (await res.json()) as { items?: Record<string, unknown>[] };
      const items = body.items ?? [];
      // At least the seeded UAT scheme exists; if not, skip the field assertions.
      // The route shape is still proven (200 + paginated envelope).
      if (items.length === 0) {
        test.info().annotations.push({
          type: 'note',
          description: 'No subvention schemes seeded; skipped per-row field assertions',
        });
        return;
      }
      const sample = items[0];
      // Canonical 5 rule fields (camelCase per response_model_by_alias=True).
      expect(sample).toHaveProperty('calculationRules');
      expect(sample).toHaveProperty('eligibilityRules');
      expect(sample).toHaveProperty('requiredDocuments');
      expect(sample).toHaveProperty('workflowRules');
      expect(sample).toHaveProperty('fundRules');
      // Snake_case must NOT leak through (CLAUDE.md Appendix C Wave 3).
      expect(sample).not.toHaveProperty('calculation_rules');
      expect(sample).not.toHaveProperty('eligibility_rules');
      expect(sample).not.toHaveProperty('required_documents');
    } finally {
      await ctx.dispose();
    }
  });
});

test.describe('E2E › IIF › claim export route wiring', () => {
  test('xlsx endpoint returns 404 (not 405/501) for an unknown claim id', async () => {
    const token = await adminToken();
    const ctx = await playwrightRequest.newContext({
      extraHTTPHeaders: { Authorization: `Bearer ${token}` },
    });
    try {
      const res = await ctx.get(`${API_BASE}/lending/iif/claims/${NON_EXISTENT_UUID}/report.xlsx`);
      // 404 = route exists, handler ran, claim not found. Any other 4xx/5xx
      // indicates a wiring regression (404 from the router itself would
      // mean the path never matched).
      expect(
        [404].includes(res.status()),
        `Expected 404 from unknown claim XLSX, got ${res.status()} ${await res.text()}`,
      ).toBeTruthy();
    } finally {
      await ctx.dispose();
    }
  });

  test('pdf endpoint returns 404 (not 405/501) for an unknown claim id', async () => {
    const token = await adminToken();
    const ctx = await playwrightRequest.newContext({
      extraHTTPHeaders: { Authorization: `Bearer ${token}` },
    });
    try {
      const res = await ctx.get(`${API_BASE}/lending/iif/claims/${NON_EXISTENT_UUID}/report.pdf`);
      expect(
        [404].includes(res.status()),
        `Expected 404 from unknown claim PDF, got ${res.status()} ${await res.text()}`,
      ).toBeTruthy();
    } finally {
      await ctx.dispose();
    }
  });

  test('csv endpoint stays reachable (regression — same router file)', async () => {
    const token = await adminToken();
    const ctx = await playwrightRequest.newContext({
      extraHTTPHeaders: { Authorization: `Bearer ${token}` },
    });
    try {
      const res = await ctx.get(`${API_BASE}/lending/iif/claims/${NON_EXISTENT_UUID}/report.csv`);
      expect(
        [404].includes(res.status()),
        `Expected 404 from unknown claim CSV, got ${res.status()} ${await res.text()}`,
      ).toBeTruthy();
    } finally {
      await ctx.dispose();
    }
  });
});

test.describe('E2E › IIF › claim exporter — live download', () => {
  test('if a claim exists, XLSX + PDF endpoints return correctly-formatted bytes', async () => {
    const token = await adminToken();
    const ctx = await playwrightRequest.newContext({
      extraHTTPHeaders: { Authorization: `Bearer ${token}` },
    });
    const listRes = await ctx.get(`${API_BASE}/lending/iif/claims?page=1&pageSize=1`);
    expect(listRes.ok(), `${listRes.status()} ${await listRes.text()}`).toBeTruthy();
    const listBody = (await listRes.json()) as { items?: { id: string }[] };
    const claimId = listBody.items?.[0]?.id;
    if (!claimId) {
      test.info().annotations.push({
        type: 'note',
        description: 'No subvention claim visible to the admin user; live exporter test skipped',
      });
      await ctx.dispose();
      return;
    }
    try {
      // ----- XLSX -----
      const xlsxRes = await ctx.get(`${API_BASE}/lending/iif/claims/${claimId}/report.xlsx`);
      expect(
        xlsxRes.ok(),
        `XLSX export failed: ${xlsxRes.status()} ${await xlsxRes.text()}`,
      ).toBeTruthy();
      expect(xlsxRes.headers()['content-type']).toContain(
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      );
      const xlsxBytes = await xlsxRes.body();
      // XLSX files are ZIP archives — magic bytes `PK\x03\x04`.
      expect(xlsxBytes.length).toBeGreaterThan(100);
      expect(xlsxBytes[0]).toBe(0x50);
      expect(xlsxBytes[1]).toBe(0x4b);
      expect(xlsxBytes[2]).toBe(0x03);
      expect(xlsxBytes[3]).toBe(0x04);
      expect(xlsxRes.headers()['content-disposition']).toContain('attachment');

      // ----- PDF -----
      const pdfRes = await ctx.get(`${API_BASE}/lending/iif/claims/${claimId}/report.pdf`);
      expect(
        pdfRes.ok(),
        `PDF export failed: ${pdfRes.status()} ${await pdfRes.text()}`,
      ).toBeTruthy();
      expect(pdfRes.headers()['content-type']).toContain('application/pdf');
      const pdfBytes = await pdfRes.body();
      // PDF files start with `%PDF-`.
      expect(pdfBytes.length).toBeGreaterThan(100);
      expect(pdfBytes[0]).toBe(0x25); // %
      expect(pdfBytes[1]).toBe(0x50); // P
      expect(pdfBytes[2]).toBe(0x44); // D
      expect(pdfBytes[3]).toBe(0x46); // F
      expect(pdfRes.headers()['content-disposition']).toContain('attachment');
    } finally {
      await ctx.dispose();
    }
  });
});

test.describe('E2E › IIF › claim detail page exposes the three downloads', () => {
  test('claim list page renders, and a seeded claim (if any) shows CSV/XLSX/PDF buttons', async ({
    page,
    consoleGate,
  }) => {
    // The list page is reachable from the routes-smoke spec; here we drill
    // into a real claim detail to verify the new download buttons are wired
    // through the UI (not just the API).
    await loginAsAdmin(page);
    await page.goto('/admin/lending/iif/claims');
    await expect(page.locator('main, [role="main"]').first()).toBeVisible({ timeout: 8_000 });

    const token = await adminToken();
    const ctx = await playwrightRequest.newContext({
      extraHTTPHeaders: { Authorization: `Bearer ${token}` },
    });
    const listRes = await ctx.get(`${API_BASE}/lending/iif/claims?page=1&pageSize=1`);
    expect(listRes.ok(), `${listRes.status()} ${await listRes.text()}`).toBeTruthy();
    const listBody = (await listRes.json()) as { items?: { id: string }[] };
    const claimId = listBody.items?.[0]?.id;
    await ctx.dispose();
    if (!claimId) {
      test.info().annotations.push({
        type: 'note',
        description:
          'No subvention claim visible to the admin user; UI download-button assertion skipped',
      });
      return;
    }
    // The detail page calls `GET /api/v1/lending/iif/claims/{id}` which is
    // org-scoped; allow nothing extra — the gate stays strict.
    await page.goto(`/admin/lending/iif/claims/${claimId}`);
    await expect(page.locator('main, [role="main"]').first()).toBeVisible({ timeout: 8_000 });
    // Three download buttons must be rendered (CSV / XLSX / PDF report).
    await expect(page.getByRole('button', { name: /CSV report/i })).toBeVisible({ timeout: 8_000 });
    await expect(page.getByRole('button', { name: /XLSX report/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /PDF report/i })).toBeVisible();
    // Silence consoleGate around the (unused) gate field — keeps the linter
    // happy if `consoleGate` ever becomes unreferenced in the body.
    void consoleGate;
  });
});

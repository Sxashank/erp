/**
 * E2E smoke: scheme claim release queues on portal + admin surfaces.
 *
 * Exercises the exact VERIFIED -> RELEASE_IN_PROGRESS -> RELEASED flow with
 * mocked APIs so the test stays deterministic and does not depend on a live
 * backend.
 */

import { expect, test } from '../fixtures/test';

function json(body: unknown) {
  return {
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify(body),
  };
}

test('portal claim queue supports initiate release and mark released', async ({
  page,
  consoleGate,
}) => {
  await page.addInitScript(() => {
    window.localStorage.setItem('portal_access_token', 'portal-access-token');
    window.localStorage.setItem('portal_refresh_token', 'portal-refresh-token');
    window.localStorage.setItem(
      'portal_user',
      JSON.stringify({
        id: '70000000-0000-0000-0000-000000000001',
        displayName: 'Portal Approver',
        actorRole: 'scheme_smfcl_approver',
        linkedEntities: [],
      }),
    );
  });

  const verifiedId = '70000000-0000-0000-0000-000000000101';
  const inProgressId = '70000000-0000-0000-0000-000000000102';
  const claims: any[] = [
    {
      id: verifiedId,
      enrollmentId: '70000000-0000-0000-0000-000000000201',
      loanAccountId: '70000000-0000-0000-0000-000000000301',
      loanAccountNumber: 'LN-1001',
      schemeId: '70000000-0000-0000-0000-000000000401',
      schemeCode: 'SMFCL-IIF',
      claimReference: 'IIF/2026Q1/00001',
      periodStart: '2026-04-01',
      periodEnd: '2026-06-30',
      claimFrequency: 'QUARTERLY',
      interestPaidInPeriod: '250000.00',
      applicableSubventionAmount: '75000.00',
      status: 'VERIFIED',
      submittedDate: '2026-07-01',
      verifiedDate: '2026-07-05',
      releaseInitiatedDate: null,
      releasedDate: null,
      releaseInstructionReference: null,
      releaseInstructionNotes: null,
      releaseReference: null,
      declarationSignedAt: '2026-07-01T10:00:00Z',
      documents: [],
      createdAt: '2026-07-01T10:00:00Z',
      updatedAt: '2026-07-05T10:00:00Z',
    },
    {
      id: inProgressId,
      enrollmentId: '70000000-0000-0000-0000-000000000202',
      loanAccountId: '70000000-0000-0000-0000-000000000302',
      loanAccountNumber: 'LN-1002',
      schemeId: '70000000-0000-0000-0000-000000000402',
      schemeCode: 'SMFCL-IIF',
      claimReference: 'IIF/2026Q1/00002',
      periodStart: '2026-04-01',
      periodEnd: '2026-06-30',
      claimFrequency: 'QUARTERLY',
      interestPaidInPeriod: '180000.00',
      applicableSubventionAmount: '54000.00',
      status: 'RELEASE_IN_PROGRESS',
      submittedDate: '2026-07-01',
      verifiedDate: '2026-07-05',
      releaseInitiatedDate: '2026-07-11',
      releasedDate: null,
      releaseInstructionReference: 'SMFCL/REL/2026/042',
      releaseInstructionNotes: 'Batch 4',
      releaseReference: null,
      declarationSignedAt: '2026-07-01T10:00:00Z',
      documents: [],
      createdAt: '2026-07-01T10:00:00Z',
      updatedAt: '2026-07-11T10:00:00Z',
    },
  ];

  const workbenchPayload = () => ({
    stats: {
      draft: 0,
      submitted: 0,
      verified: claims.filter((claim) => claim.status === 'VERIFIED').length,
      releaseInProgress: claims.filter((claim) => claim.status === 'RELEASE_IN_PROGRESS').length,
      released: claims.filter((claim) => claim.status === 'RELEASED').length,
      eligiblePeriods: 0,
    },
    enrollments: [],
    claims,
  });

  await page.route('**/api/v1/portal/notifications**', async (route) => route.fulfill(json([])));
  await page.route('**/api/v1/portal/claims/workbench', async (route) =>
    route.fulfill(json(workbenchPayload())),
  );
  await page.route(/\/api\/v1\/portal\/claims(?:\?|$).*/, async (route) =>
    route.fulfill(
      json({
        items: claims,
        total: claims.length,
        page: 1,
        pageSize: 100,
      }),
    ),
  );
  await page.route('**/api/v1/portal/claims/*/initiate-release', async (route) => {
    const parts = new URL(route.request().url()).pathname.split('/');
    const claimId = parts[parts.length - 2];
    const body = route.request().postDataJSON() as {
      releaseInstructionReference: string;
      releaseInstructionNotes?: string;
    };
    const claim = claims.find((item) => item.id === claimId);
    if (!claim) {
      return route.fulfill({ status: 404, body: '{}' });
    }
    claim.status = 'RELEASE_IN_PROGRESS';
    claim.releaseInitiatedDate = '2026-07-14';
    claim.releaseInstructionReference = body.releaseInstructionReference;
    claim.releaseInstructionNotes = body.releaseInstructionNotes ?? null;
    claim.updatedAt = '2026-07-14T09:00:00Z';
    return route.fulfill(json(claim));
  });
  await page.route('**/api/v1/portal/claims/*/mark-released', async (route) => {
    const parts = new URL(route.request().url()).pathname.split('/');
    const claimId = parts[parts.length - 2];
    const body = route.request().postDataJSON() as { releaseReference: string };
    const claim = claims.find((item) => item.id === claimId);
    if (!claim) {
      return route.fulfill({ status: 404, body: '{}' });
    }
    claim.status = 'RELEASED';
    claim.releasedDate = '2026-07-15';
    claim.releaseReference = body.releaseReference;
    claim.updatedAt = '2026-07-15T12:00:00Z';
    return route.fulfill(json(claim));
  });
  await page.goto('/portal/claims');

  await expect(page.getByRole('heading', { name: 'Claim Release Queue' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Initiate release' })).toHaveCount(1);
  await expect(page.getByRole('button', { name: 'Mark released' })).toHaveCount(1);

  await page.getByRole('button', { name: 'Initiate release' }).click();
  await page.getByLabel('Release instruction reference').fill('SMFCL/REL/2026/099');
  await page.getByRole('button', { name: 'Start release' }).click();

  await expect(page.getByRole('button', { name: 'Initiate release' })).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Mark released' })).toHaveCount(2);

  await page.getByRole('button', { name: 'Mark released' }).first().click();
  await page.getByLabel('Release reference').fill('SBIN20260715XYZ');
  await page.getByRole('button', { name: 'Confirm released' }).click();

  await expect(page.getByRole('button', { name: 'Mark released' })).toHaveCount(1);
  await expect(page.getByText('RELEASED', { exact: true })).toBeVisible();

  expect(consoleGate.getErrors()).toEqual([]);
  expect(consoleGate.getFailedResponses()).toEqual([]);
});

test('admin claim detail supports the two-step release lifecycle', async ({
  authedPage: page,
  consoleGate,
}) => {
  const claimId = '80000000-0000-0000-0000-000000000101';
  const claim: any = {
    id: claimId,
    organizationId: '11111111-1111-1111-1111-111111111111',
    enrollmentId: '80000000-0000-0000-0000-000000000201',
    loanAccountId: '80000000-0000-0000-0000-000000000301',
    loanAccountNumber: 'LN-2001',
    schemeId: '80000000-0000-0000-0000-000000000401',
    schemeCode: 'SMFCL-IIF',
    claimReference: 'IIF/2026Q1/00111',
    periodStart: '2026-04-01',
    periodEnd: '2026-06-30',
    claimFrequency: 'QUARTERLY',
    interestPaidInPeriod: '300000.00',
    applicableSubventionAmount: '90000.00',
    status: 'VERIFIED',
    submittedDate: '2026-07-01',
    verifiedDate: '2026-07-05',
    releaseInitiatedDate: null,
    releasedDate: null,
    rejectionReason: null,
    releaseInstructionReference: null,
    releaseInstructionNotes: null,
    releaseReference: null,
    declarationSignedBy: null,
    declarationSignedAt: '2026-07-01T09:00:00Z',
    documents: [],
    isActive: true,
    createdAt: '2026-07-01T09:00:00Z',
    updatedAt: '2026-07-05T09:00:00Z',
    version: 1,
  };

  await page.route('**/api/v1/auth/me', async (route) =>
    route.fulfill(
      json({
        id: '22222222-2222-2222-2222-222222222222',
        username: 'admin',
        email: 'admin@smfc.example',
        full_name: 'Admin User',
        organization_id: '11111111-1111-1111-1111-111111111111',
        default_unit_id: null,
        mfa_enabled: false,
        roles: [{ id: 'r1', code: 'SUPER_ADMIN', name: 'Super Admin' }],
        permissions: ['subvention.verify', 'treasury:write'],
      }),
    ),
  );
  await page.route('**/api/v1/organizations**', async (route) =>
    route.fulfill(
      json({
        items: [
          {
            id: '11111111-1111-1111-1111-111111111111',
            code: 'HO',
            name: 'Head Office',
          },
        ],
        total: 1,
      }),
    ),
  );
  await page.route('**/api/v1/auth/refresh', async (route) =>
    route.fulfill(
      json({
        access_token: 'refreshed',
        refresh_token: 'refreshed-r',
        token_type: 'bearer',
        expires_in: 900,
      }),
    ),
  );
  await page.route(`**/api/v1/lending/iif/claims/${claimId}`, async (route) =>
    route.fulfill(json(claim)),
  );
  await page.route(`**/api/v1/lending/iif/claims/${claimId}/initiate-release`, async (route) => {
    const body = route.request().postDataJSON() as {
      releaseInstructionReference: string;
      releaseInstructionNotes?: string;
    };
    claim.status = 'RELEASE_IN_PROGRESS';
    claim.releaseInitiatedDate = '2026-07-14';
    claim.releaseInstructionReference = body.releaseInstructionReference;
    claim.releaseInstructionNotes = body.releaseInstructionNotes ?? null;
    claim.updatedAt = '2026-07-14T09:00:00Z';
    return route.fulfill(json(claim));
  });
  await page.route(`**/api/v1/lending/iif/claims/${claimId}/mark-released`, async (route) => {
    const body = route.request().postDataJSON() as {
      releaseReference: string;
      releasedDate: string;
    };
    claim.status = 'RELEASED';
    claim.releasedDate = body.releasedDate;
    claim.releaseReference = body.releaseReference;
    claim.updatedAt = '2026-07-15T10:00:00Z';
    return route.fulfill(json(claim));
  });
  await page.goto(`/admin/lending/iif/claims/${claimId}`);

  await expect(page.getByRole('button', { name: 'Initiate release' })).toBeVisible();

  await page.getByRole('button', { name: 'Initiate release' }).click();
  const initiateDialog = page.getByRole('dialog', {
    name: 'Initiate release',
  });
  await initiateDialog.getByPlaceholder('e.g. SMFCL/REL/2026/041').fill('SMFCL/REL/2026/500');
  await initiateDialog.getByRole('button', { name: 'Start release' }).click();

  await expect(page.getByRole('button', { name: 'Mark released' })).toBeVisible();

  await page.getByRole('button', { name: 'Mark released' }).click();
  const releasedDialog = page.getByRole('dialog', {
    name: 'Mark claim released',
  });
  await releasedDialog.getByPlaceholder('e.g. SBIN20260512XYZ').fill('UTR-2026-500');
  await releasedDialog.locator('input[type="date"]').fill('2026-07-15');
  await releasedDialog.getByRole('button', { name: 'Confirm released' }).click();

  await expect(page.getByRole('button', { name: 'Mark released' })).toHaveCount(0);
  await expect(page.getByText('UTR-2026-500')).toBeVisible();

  expect(consoleGate.getErrors()).toEqual([]);
  expect(consoleGate.getFailedResponses()).toEqual([]);
});

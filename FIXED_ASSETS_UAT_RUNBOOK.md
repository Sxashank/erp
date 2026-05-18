# Fixed Assets UAT Runbook

This runbook is the operator contract for the fixed-assets phase-1 operational core:

- asset categories
- asset register
- capitalization
- revaluation
- impairment
- depreciation run and posting
- physical verification
- disposal and write-off
- fixed-asset report export

The flow is manual-first and runs against the real app and real backend. No mocking is allowed.

## Preconditions

- Frontend is reachable at `http://localhost:5176` or the URL passed in `PLAYWRIGHT_BASE_URL`.
- Backend is reachable at `http://localhost:8001/api/v1` or the URL passed in `PLAYWRIGHT_API_BASE`.
- The target organization already has:
  - at least one location and department
  - fixed-asset GL accounts that can be mapped to a category
  - a working admin user with fixed-assets permissions
- If approval mode is enabled for depreciation or disposal and self-approval is not allowed, provide a second approver user.

## Commands

Direct live-flow script:

```bash
pnpm exec node scripts/fixed-assets-live-flow.mjs
```

Formal Playwright acceptance test:

```bash
PLAYWRIGHT_LIVE_BACKEND=1 \
PLAYWRIGHT_EXTERNAL_SERVER=1 \
pnpm exec playwright test playwright/tests/fixed-assets-live-flow.spec.ts --project=chromium
```

The formal Playwright test runs the same live-flow script and validates the generated summary, screenshots, downloads, and final record statuses.

## Environment Variables

- `PLAYWRIGHT_BASE_URL`
  - Defaults to `http://localhost:5176`
- `PLAYWRIGHT_API_BASE`
  - Defaults to `http://localhost:8001/api/v1`
- `UAT_ADMIN_USERNAME`
  - Defaults to `krishna`
- `UAT_ADMIN_PASSWORD`
  - Defaults to `ChangeMe123!`
- `UAT_APPROVER_USERNAME`
  - Optional
  - Used only when depreciation posting or disposal is routed for approval
- `UAT_APPROVER_PASSWORD`
  - Optional
  - Used only when depreciation posting or disposal is routed for approval
- `FIXED_ASSETS_LIVE_FLOW_OUTPUT_DIR`
  - Optional
  - Overrides the default artifact location

## What the Flow Creates

Every run creates uniquely named UAT records:

- category code prefix: `UATFA`
- category name prefix: `UAT FA`
- asset name suffix: `Laptop`
- verification schedule suffix: `Verification`

The created asset is intentionally taken through the full lifecycle and ends in `DISPOSED`.

## Success Criteria

The run is successful only when all of the following are true:

- category is created with real GL mappings
- draft asset is created
- asset is capitalized
- revaluation is recorded
- impairment is recorded
- depreciation run completes and posts to GL
- physical verification schedule is created, executed, discrepancy handled, and completed
- disposal completes or is submitted and approved where approval is required
- asset register and depreciation summary exports are downloaded
- summary JSON contains:
  - `records.asset.status = DISPOSED`
  - `records.depreciationRun.status = POSTED`
  - `records.verificationSchedule.status = COMPLETED`
  - `records.disposal.status = COMPLETED`
- no browser console errors are recorded
- no unexpected failed network calls are recorded

## Artifacts

Default output directory:

```text
test-results/fixed-assets-live-flow
```

Each run writes:

- `summary-<timestamp>.json`
- `categories-<timestamp>.png`
- `asset-draft-<timestamp>.png`
- `depreciation-run-<timestamp>.png`
- `verification-<timestamp>.png`
- `disposal-<timestamp>.png`
- `asset-register-<timestamp>.csv`
- `depreciation-summary-<timestamp>.csv`

## Approval-Mode Notes

If approval is not required, the live flow posts depreciation and completes disposal immediately.

If approval is required:

- the script submits the request
- when `UAT_APPROVER_USERNAME` and `UAT_APPROVER_PASSWORD` are present, the script approves the request through the real approval API using that second user
- if approver credentials are not provided, the run will still create the pending approval request, but final status will remain pending and the run should not be treated as a full sign-off

## Cleanup and Data Hygiene

These UAT runs create auditable financial and lifecycle history. Do not purge them casually.

Use these rules:

- keep the records in non-production environments as proof of acceptance unless the team explicitly requests cleanup
- identify UAT categories by `categoryCode LIKE 'UATFA%'`
- identify UAT schedules by `scheduleName LIKE 'UAT FA % Verification'`
- identify UAT assets by `assetName LIKE 'UAT FA % Laptop'`
- if cleanup is required, do it only in a controlled non-production environment and only after confirming there is no reporting or audit dependency on the run

## Sign-Off Standard

Fixed assets is at sign-off quality for phase 1 only when:

- the direct live-flow script passes
- the Playwright acceptance test passes
- `pnpm typecheck` passes
- `pnpm build` passes
- `pnpm test` passes
- `pnpm test:integration` passes
- the generated live records are visible in the UI and match the summary JSON

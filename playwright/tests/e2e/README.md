# Real-user E2E suite

Playwright tests that behave like a real operator — drive UI form fields,
submit through the actual button, watch the success toast, then assert the
row reached the database (via a direct `pg` query) and is still there after a
page reload.

This is the **UI → API → DB → reload** loop. The existing smoke + cross-tenant
specs don't replace it; they live alongside.

## What it covers

| File | Scope |
|---|---|
| `01-auth.spec.ts` | Login form (required-field validation, error-clears-on-fix, 401 envelope, redirect to /admin). |
| `02-navigation.spec.ts` | Sidebar → list, list → form, breadcrumbs. |
| `10-masters.spec.ts` | Tier-1 master CRUD — Unit is the proof of the harness; pattern templates to Department, Designation, Account Group, Account, Voucher Type, Payment Terms, GST Rate, HSN/SAC, TDS Section. |
| `99-cleanup.spec.ts` | Idempotent teardown — deletes every E2E-prefixed row from the test org. |

Future specs land here (`20-reference.spec.ts`, `30-transactional.spec.ts`,
`40-lifecycle.spec.ts`).

## Bootstrap — one time

The suite uses a **dedicated** Postgres database `smfc_erp_e2e` (NOT the dev
`smfc_erp`). All writes are scoped to a dedicated organisation
`SMFC-E2E`. Create both with:

```bash
# Create the database (postgres superuser)
psql -U postgres -c "CREATE DATABASE smfc_erp_e2e OWNER smfc"

# Bootstrap schema + seed (uses the canonical reset_db + seed_data path,
# parameterised via env vars). Writes the org UUID to
# `playwright/.e2e-org-id`.
pnpm test:e2e:real:bootstrap
```

The bootstrap script is idempotent — re-running it does not destroy data.

If you ever need to reset the E2E DB to a known state:

```bash
psql -U postgres -c "DROP DATABASE IF EXISTS smfc_erp_e2e"
psql -U postgres -c "CREATE DATABASE smfc_erp_e2e OWNER smfc"
pnpm test:e2e:real:bootstrap
```

## Per-run

You need three processes:

```bash
# 1. Backend pointed at the E2E DB.
cd backend && source .venv/bin/activate
DATABASE_URL=postgresql+asyncpg://smfc:smfc_secret@localhost:5432/smfc_erp_e2e \
  uvicorn app.main:app --host 127.0.0.1 --port 8001 --log-level info

# 2. Frontend dev server (the Playwright `webServer` config will spin this
#    automatically, but you can pre-start it for faster iteration).
pnpm dev --port 5176

# 3. The suite itself.
pnpm test:e2e:real
```

`pnpm test:e2e:real` sets `PLAYWRIGHT_E2E=1` which activates `globalSetup.ts`
— that pre-flights the DB connection and fails loud if `SMFC-E2E` isn't
seeded.

## Selector strategy

Specs use **role-based selectors** (`getByRole`, `getByLabel`,
`button[type="submit"]`) as the primary identification mechanism. shadcn +
RHF give every form input an accessible name; every form has exactly one
`<button type="submit">`. This is the [Playwright-recommended
default](https://playwright.dev/docs/best-practices#use-user-facing-attributes).

`data-testid` is reserved for the narrow set of affordances where role + name
isn't unique (status pills in multi-status rows, ambiguous icon-only buttons,
wizard step controls). See `E2E_BOOTSTRAP_FIXES.md` § "Selector strategy
decision" for the rationale.

## Console + network gating

Every test inherits the `consoleGate` fixture (`playwright/fixtures/test.ts`).
Any uncaught `console.error`, page error, or non-asserted 4xx/5xx fails the
test. Per-test opt-out:

```ts
test('something that should 401', async ({ page, consoleGate }) => {
  consoleGate.allowStatus(401, '/auth/login');
  consoleGate.allowError(/Invalid credentials/i);
  // ...
});
```

## DB assertions

The `db` fixture opens a `pg.Client` against `DATABASE_URL_E2E` and sets
PostgreSQL RLS context to the E2E organisation. Helpers:

```ts
const row = await db.assertRowExists('mst_unit', { code }, { name, unit_type: 'BRANCH' });
await db.assertRowMatches('mst_unit', { id: row.id }, { name: 'renamed' });
```

Both throw a clear diff on mismatch (column vs expected). Identifiers are
quoted and parameter-bound — safe to pass test-supplied values.

## Adding a new entity

For each new master:
1. Find the form file (`src/pages/<domain>/<entity>/<Entity>Form.tsx`) and
   note the exact field labels (`<Label htmlFor="...">`).
2. In `10-masters.spec.ts` (or a new tier file), copy the Unit `test`
   block and adapt: change route, field labels, DB table, expected columns.
3. Add the table + code column to the `targets` array in `99-cleanup.spec.ts`.

The suite is intentionally one-spec-per-entity to keep failures localised.

## Env vars

| Var | Purpose | Default |
|---|---|---|
| `PLAYWRIGHT_BASE_URL` | Frontend URL | `http://localhost:5176` |
| `PLAYWRIGHT_API_BASE` | Backend URL | `http://localhost:8001/api/v1` |
| `DATABASE_URL_E2E` | Postgres URL for the test harness | `postgres://smfc:smfc_secret@localhost:5432/smfc_erp_e2e` |
| `UAT_ADMIN_USERNAME` | Login user | `krishna` |
| `UAT_ADMIN_PASSWORD` | Login password | `ChangeMe123!` |
| `E2E_ORG_CODE` | Test org code | `SMFC-E2E` |
| `E2E_ORG_ID` | Test org UUID; auto-read from `playwright/.e2e-org-id` if unset | — |

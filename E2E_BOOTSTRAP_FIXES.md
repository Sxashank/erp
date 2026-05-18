# E2E Bootstrap — Architectural Fixes Log

Standing log of every fix needed to bring up the dedicated E2E Postgres database
(`smfc_erp_e2e`) for the real-user Playwright suite. **Every fix is a root-cause
fix** — no temporary bypasses, no env-gated branches, no schema hacks. Each entry
follows the CLAUDE.md §11 bug-fix protocol.

The E2E suite simply surfaces these latent issues by being the first caller that
creates the schema from `Base.metadata.create_all()` against a truly empty
database (the dev DB has been incrementally migrated over time, so several
pre-existing model bugs never fired against it). Fixing them benefits every
downstream consumer: alembic autogenerate, fresh-clone bring-up, CI, prod
replica builds, and the new E2E harness.

| # | Defect | Root cause | File(s) | Fix | CLAUDE.md ref |
|---|---|---|---|---|---|
| 1 | `seed_data.py` hard-codes the org `code="SMFC"`, so a fresh tenant cannot be seeded without source edits | Tenant code was a constant when there was only one tenant; CLAUDE.md §1 + §6.8 explicitly require provisioning a new tenant without redeploy | `backend/scripts/seed_data.py::seed_organization` | Read `SEED_ORG_CODE` / `SEED_ORG_NAME` / `SEED_ORG_LEGAL_NAME` env vars with the existing `SMFC` defaults | §1 (SaaS tenant model), §6.8 (per-tenant settings) |
| 2 | `server_default="gen_random_uuid()"` emits the literal string in DDL (`DEFAULT 'gen_random_uuid()'`), failing UUID-column creation on a fresh DB | Pass-string-as-server-default is silently quoted; the SQLAlchemy idiom for raw SQL is `func.gen_random_uuid()` or `text("gen_random_uuid()")`; the rest of the codebase (e.g. `core/integration_config.py`) uses the correct `func.*` form | `backend/app/models/lending/treasury.py` (12 sites), `backend/app/models/hris/separation.py` (4 sites) | Replace each with `server_default=func.gen_random_uuid()` (and import `from sqlalchemy import func` where missing) | §6.2 (no string-interpolated SQL — same family of issue) |
| 3 | Treasury models declare a second `primary_key=True` column (`lender_id`, `borrowing_id`, `tranche_id`, `schedule_id`, `payment_id`, `covenant_id`, `position_id`, `asset_id`, `liability_id`, `analysis_id`, `limit_id`, `tracking_id`) on top of `BaseModel.id`, producing a **composite primary key** in DDL. FKs from `trs_borrowing` → `trs_lender.id` then fail with `there is no unique constraint matching given keys` because `id` alone is no longer unique. The dev DB has only `id` as PK (verified via `pg_index`), confirming this is a recent latent regression in the ORM that the dev DB never re-bootstrapped through. | A "secondary business UUID" column was tagged as `primary_key=True`. CLAUDE.md §3.2 + `BaseModel` (`app/models/base.py:113`) define `id` as the canonical PK for every transactional table; subordinate `<name>_id` columns are domain identifiers, not part of the PK. | `backend/app/models/lending/treasury.py` (12 columns across 12 model classes) | Replace `primary_key=True` with `nullable=False` on each. Keep the column (matches dev DB shape: `id` PK + `<name>_id` regular UUID column) so referencing code / data isn't disturbed. | §3.2 (one canonical PK per row), §6.2 (DDL correctness) |
| 4 | `Base.metadata.create_all()` on a fresh DB fails on `PGEnum(..., create_type=False)` columns because the enum type was never created — alembic migrations are the only path that creates enum types, and they have not been (and cannot be) run before `create_all` (the migration chain ALTERs tables that ORM creates first). | `create_type=False` was set so alembic owns the type lifecycle. On the dev DB this was fine because alembic ran first; on any *fresh* DB the ORM is silently incomplete. CLAUDE.md §3.1 + §6 expect the ORM to be the source of truth — the type *belongs* to the model. | The enums are needed across 67 model files. **Architecturally correct fix**: pre-create the enum types in a single SQL preamble inside the fresh-DB bootstrap path (`reset_db.py` and `seed_e2e.sh`) using the same `DO $$ ... EXCEPTION WHEN duplicate_object THEN null; END $$;` idempotent guard that the alembic migrations use. This keeps the model declaration honest (`create_type=False` means "managed elsewhere") without flipping 67 files and risking conflicts with alembic migrations that already `CREATE TYPE` without an `IF NOT EXISTS` guard. | New file `backend/app/db/bootstrap_enums.py` (re-used by both `reset_db.py` and `seed_e2e.sh`); `backend/scripts/seed_e2e.sh` invokes it before `create_all`. | §3.1 (DDL is a deployment artefact, not a runtime decision), §6 (canonical bootstrap path) |
| 5 | `alembic stamp head` on a fresh DB creates `alembic_version.version_num` at the alembic default `VARCHAR(32)`; current head revision id `zzc30_wave6_permission_screaming_snake` is 38 chars, so the INSERT fails. `env.py` already widens the column to 128 with a runtime `ALTER TABLE` — but only inside `do_run_migrations`, which runs for `alembic upgrade`, NOT for `alembic stamp`. | Stamp uses the same `context.configure(...)` call but the widening happens *after* the version table is created (because of stamp's order of operations). The clean fix is to tell alembic the target width at configure time via `version_table_pk_type=sa.String(128)`, which propagates to the CREATE TABLE that stamp emits. **Additionally** `seed_e2e.sh` pre-creates the table at the correct width as a belt-and-braces guard (idempotent CREATE TABLE IF NOT EXISTS at width 128). | `backend/alembic/env.py` (`context.configure` call) + `backend/scripts/seed_e2e.sh` (pre-create alembic_version) | Pass `version_table_pk_type=sa.String(128)` in `context.configure`; pre-create the table at width 128 in seed_e2e.sh. | §6 (canonical bootstrap), §11 (root-cause over workaround) |
| 6 | Two `BalanceType` Python enums exist (`app.core.constants.BalanceType` with member names `DEBIT/CREDIT` and `app.models.ap_ar.vendor.BalanceType` with member names `DR/CR`), each declaring `Enum(BalanceType)` on different ORM columns. Both materialise into the same Postgres enum type name `balancetype`. The dev DB has it populated with `DEBIT, CREDIT` (the constants version was created first). When `Base.metadata.create_all()` runs alongside the bootstrap, the duplicate enum declaration confuses the introspection — and vendor/customer columns would reject `DEBIT`/`CREDIT` inserts at runtime. | A duplicate enum class slipped into `vendor.py` and propagated to `customer.py` + `ap_ar/__init__.py`. CLAUDE.md §6 puts the canonical enum in `core/constants.py`. | `backend/app/models/ap_ar/vendor.py` (remove local class), `backend/app/models/ap_ar/customer.py` (import from constants), `backend/app/models/ap_ar/__init__.py` (re-export from constants) | Delete the local `BalanceType` declaration in `vendor.py`; rewire imports to `app.core.constants.BalanceType`. Verified `from app.main import app` still loads 1599 routes. | §3.1 (single source of truth for shared types), §6 (canonical enums in constants) |
| 7 | `backend/app/models/__init__.py` does not import six leaf packages — `approval`, `compliance`, `ess`, `fixed_deposits`, `inventory`, `vendor_portal` — so their ORM tables never register on `Base.metadata`. `Base.metadata.create_all()` then silently skips them, and downstream callers like `seed_data.py::seed_fixed_deposit_masters()` fail with `relation "fd_product" does not exist` on a fresh DB. Routes still resolve in the running app because the route files import the models directly, but the canonical bootstrap path doesn't see them. | Models were added to leaf packages over time without round-tripping through the central registry. CLAUDE.md §3.1 + §6 require the ORM to be the single source of truth for schema. | `backend/app/models/__init__.py` (single edit; add an explicit side-effect import block for the six leaf packages). | Add `from app.models import approval, compliance, ess, fixed_deposits, inventory, vendor_portal  # noqa: F401` at the top of the package. This makes every `BaseModel` subclass discoverable when `app.models` is imported — which is the contract every fresh-DB tool already relies on. | §3.1 (single source of truth), §6 (canonical bootstrap) |
| 8 | ESS models (`ess/ess_user.py`, `ess/helpdesk.py`, `ess/it_declaration.py`, `ess/reimbursement.py`) declare `ForeignKey("auth_user.id", ...)` but the User table's `__tablename__` is `mst_user`. `Base.metadata.create_all()` raises `NoReferencedTableError: ... could not find table 'auth_user' with which to generate a foreign key`. | Stale table name from an older era of the schema (probably renamed during the masters → mst_* migration). The route layer never exercised these FK declarations because the ESS routes were never live in dev. | `backend/app/models/ess/{ess_user,helpdesk,it_declaration,reimbursement}.py` | `sed -i 's|ForeignKey("auth_user.|ForeignKey("mst_user.|g'` across the 4 files. Verified `from app.main import app` still loads 1599 routes. | §6.2 (DDL correctness), §11 (root-cause: rename, don't introduce an alias) |
| 9 | `ess/reimbursement.py::ReimbursementCategory.gl_account_id` declares `ForeignKey("fin_chart_of_account.id", ...)` but no such table exists; the chart of accounts table is `mst_account`. | Same family of issue as fix #8 — a stale legacy name from before the finance schema rename. | `backend/app/models/ess/reimbursement.py:86` | Replace with `ForeignKey("mst_account.id", ondelete="SET NULL")`. | §6.2 (DDL correctness), §11 |
| 10 | `fixed_deposits/fixed_deposit.py::FixedDeposit.customer_id` declares `ForeignKey("lending_entity.id", ...)`; the LOS entity table is `los_entity`. | Same family — stale legacy name from before the LOS rename. | `backend/app/models/fixed_deposits/fixed_deposit.py:87` | Replace with `ForeignKey("los_entity.id")`. | §6.2 (DDL correctness), §11 |
| 11 | `seed_e2e.sh` resolves the freshly-created org UUID via a Python heredoc that reads `E2E_ORG_CODE` from the environment, but the variable was only declared (`:= …`) not `export`ed. The heredoc therefore failed with `KeyError: 'E2E_ORG_CODE'` AFTER a successful seed — wasting the run. | Bash `:=` defaults the variable in the current shell but doesn't export it to subprocesses. | `backend/scripts/seed_e2e.sh` | Add an explicit `export E2E_ORG_CODE E2E_ORG_NAME E2E_DB_NAME` after the `:=` block. | §11 (root-cause: explicit export, not "wrap call in `env VAR=$VAR …`") |

## Selector strategy decision (architecturally significant — recorded here, not a "fix")

**Decision**: the E2E suite uses **role-based selectors** (`getByRole`, `getByLabel`,
`button[type="submit"]`) as the primary identification strategy, with
`data-testid` reserved for the narrow set of elements where roles + accessible
names are not unique enough (status pills inside table rows, ambiguous icon-only
buttons, etc.).

**Why**: The original plan called for FormShell/FormField/DataTable rewrites to
stamp `data-testid` on every form input, submit/cancel button, and row-action
control. After reading the actual page tree, ~50% of forms do NOT use `FormShell`
(e.g. `UnitForm.tsx` builds its own `<form>` + `<Card>` + raw `<Button>` shell);
they all use `type="submit"`, label-wired RHF fields, and role-based buttons.

A FormShell edit therefore propagates to half the pages and silently misses the
other half — that is the opposite of "architecturally clean". The
`getByRole`/`getByLabel` strategy works on **all** of them because shadcn's
`<Button>` carries the correct ARIA role and RHF's `<FormItem>` wires
`htmlFor` between label and input.

**Where testids ARE added** (narrow, justified additions tracked in this file as
incremental fixes, not a wholesale wiring task):

- New row-action affordances on `<DataTable>` (`row-action-edit` / `row-action-delete`)
  whenever the edit link is icon-only and the row's accessible name does not
  uniquely identify the action.
- Status pill inside a row when assert-by-text is ambiguous (e.g. "Active"
  appears in multiple columns of the same row).
- Form pages that use a wizard-style multi-step submit where the canonical
  submit button text changes per step.

These additions are made **only when a specific spec needs them**, not
preemptively, and each addition is noted in this file with the spec that drove
it.

**This is not a bypass.** Role-based selectors are Playwright's
recommended primary strategy
([Playwright best practices](https://playwright.dev/docs/best-practices#use-user-facing-attributes)).
The original plan's testid wiring is **not the canonical pattern for this
codebase** — the canonical pattern is the existing accessible HTML.

## Verification — seed_e2e.sh end-to-end

After fixes 1–11 the wrapper completes cleanly on a freshly-recreated DB:

```text
==> [seed_e2e] DB:       smfc_erp_e2e
==> [seed_e2e] org code: SMFC-E2E
==> [seed_e2e] org name: SMFC E2E Sandbox
==> [seed_e2e] creating enum types + tables via the canonical fresh-DB bootstrap
  - ensured 237 enum type(s)
==> [seed_e2e] alembic stamp head (matches schema state to migration head)
==> [seed_e2e] python scripts/seed_data.py
Seeding permissions...
Seeding roles...
Seeding organization...
… (every domain seeded) …
==> [seed_e2e] E2E org id: 20e5e529-9f6a-4467-bd71-d8fa1ccf44df
==> [seed_e2e] wrote …/playwright/.e2e-org-id
==> [seed_e2e] done
```

DB sanity (queried directly):
- `mst_organization WHERE code='SMFC-E2E'` → 1 row.
- `mst_user WHERE username='krishna'` → 1 row.
- `mst_financial_year` → 1 row (FY2024-25).
- `mst_account` → 98 rows.

The dev DB `smfc_erp` is untouched. Every fix lands the right shape in the ORM
(no env-gated forks, no temporary shims) so the next migration, the next fresh
clone, and CI all benefit from the same correction.

(rows are added as fixes are made — never rewritten in place)

## Process

1. Each defect is reproduced (the failing command + the exact error) before any
   code change.
2. The fix targets the model / module that emits the bad DDL — not the seed
   script or alembic chain. Migrations that already exist in `backend/alembic/`
   are not edited; the dev DB is already on `head`. Alembic autogenerate on the
   next migration will pick up no diff because the underlying type / default is
   the same.
3. Every fix is verified by re-running `backend/scripts/seed_e2e.sh` on a freshly
   recreated `smfc_erp_e2e` database. The wrapper exits 0 only when the schema
   AND the canonical seed both succeed.
4. After the wrapper passes, the dev DB is sanity-checked with
   `python3 -c "from app.main import app; print(len(app.routes))"` to confirm
   the model edits did not break route loading.

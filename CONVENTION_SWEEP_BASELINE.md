# Convention Sweep Baseline (Wave 0 closing snapshot)

This file pins the **before** numbers for the Convention Sweep. Each subsequent
wave drives one or more of these counts to zero; the wave gate is "did the
relevant counter fall, and did the smoke spec stay 100% green."

LOS namespace (`backend/app/{api/v1,services,models,schemas}/lending/{entities,products,applications,sanctions}` + `src/pages/lending/los/**`) is excluded from every count below.

## Backend

| Counter | Baseline | Wave to close | Notes |
|---|---|---|---|
| `Depends(get_db)` on non-LOS authenticated routes | ~~859~~ → **0** ✓ Wave 1 closed | gated by `scripts/lint/check_db_dep.py`; wired into pre-commit |
| `RequirePermissions("<non-screaming-snake>")` strings | ~~220~~ → **0** ✓ Wave 6 closed | Wave 6 | 220 sites across 18 backend files + 48 FE sites rewritten in lockstep; 22 `Permissions.X` values flipped + 31 new constants registered; alembic `zzc30_wave6_permission_screaming_snake` re-seeds + grants to SUPER_ADMIN; gate `scripts/lint/check_permission_format.py` wired into pre-commit |
| `organization_id: UUID = Query(...)` violations (cross-tenant enumeration) | ~~94+~~ → **0** ✓ Wave 1 closed | covered by 3 parallel agents; one platform-admin endpoint (`audit-logs/verify-chain`) appropriately gated |
| Service-helper direct `session.commit()` | ~~499~~ → **0** ✓ Wave 2 (transactions) closed | replaced with `flush()` via codemod (`wave2_commit_to_flush.py`); request-scoped session in `get_db()` owns the commit/rollback boundary |
| `IdempotencyMiddleware.MUTATING_RESOURCES` allowlist | 14 → **22** ✓ Wave 2 (idempotency) closed | added lending/{collections,npa,schedules,credit,iif} + financial-years |
| Domain `audit_log` writes on top-8 financial mutations | 0 → **8** ✓ Wave 2 (audit) closed | helper `app/services/audit/__init__.py::record_financial_action`; covers VOUCHER_POST, RECEIPT_ALLOCATE, DISBURSEMENT_PROCESS, RESTRUCTURE_APPROVE, WRITE_OFF, OTS_APPROVE, PAYROLL_FINALIZE, IIF_CLAIM_RELEASE |
| Plain `BaseModel` response schemas | ~~244~~ → **0** ✓ Wave 3 closed | Wave 3 | 244 BaseModel subclasses migrated to `CamelSchema` across 21 files; 87 redundant `ConfigDict(from_attributes=True)` removed; `populate_by_name=True` keeps snake-case input backwards-compat |
| `response_model=` routes missing `response_model_by_alias=True` | ~~955~~ → **0** ✓ Wave 3 closed | Wave 3 | codemod `wave3_response_model_by_alias.py` inserted 960 flags across 110 files; 1365/1365 routes now camelCase on wire |
| `raise HTTPException(...)` in `backend/app/api/v1/**` | ~~490~~ → **0** ✓ Wave 3 closed | Wave 3 | every route now raises a typed `AppException` subclass; gated by `scripts/lint/check_http_exception.py` (wire into pre-commit at end of Wave 3) |

## Frontend

| Counter | Baseline | Wave to close | Notes |
|---|---|---|---|
| `pnpm lint --max-warnings=0` errors | ~~624 err, 911 warn~~ → **50 err, 1191 warn** | Wave 4 + 5 | Wave 4 closed: console→logger (395 sites), `:any` (136), `as any` (37 of 41; 4 approved exemptions in `.stubs-approved.md`), date→`<DateDisplay>` (114), currency→`<AmountDisplay>` (3 lines). Remaining errors are mostly unused-vars from refactors + still-needed manual fixes. |
| Raw `<Table>` vs `<DataTable>` | 252 in `src/pages` | Wave 5 (TOP-50 only) | long tail tracked in `.stubs-approved.md` |
| Pages with `useEffect + useState` server fetches | 35+ (audit estimate) | Wave 5 | manual review per file |
| Pages calling axios directly | ~~4~~ → **0** ✓ Wave 4 closed | Wave 4 | last site (`NachRetryList.tsx`) routed through `useNachBatches.useCreateNachRetryBatch` |
| Pages calling raw `fetch()` | ~~11~~ → **0** ✓ Wave 4 closed | Wave 4 | `src/pages/lending/aa/*` (ConsentDetail / FetchedData / RequestConsent / SessionDetail) routed through `useAAConsent` / `useAASession` / `useAABankAccounts` / `useAAProviders` hooks; backend allowlist now includes `lending/aa` and `lending/nach` |
| `console.*` in `src/**` | ~~395~~ → **0** ✓ Wave 4 closed | Wave 4 | codemod `wave4_console_to_logger.py`; ESLint `no-console: error` blocks regressions |
| `: any` annotations in `src/**` | ~~136~~ → **0** ✓ Wave 4 closed | Wave 4 | typed interfaces introduced; `Record<string, unknown>` for genuinely opaque payloads |
| `as any` casts in `src/**` | ~~41~~ → **4 (approved)** ✓ Wave 4 closed | Wave 4 | 4 exemptions in `.stubs-approved.md` (3 LOS frozen + 1 RHF/zodResolver edge case) |
| Inline `toLocaleDateString` in `src/pages` | ~~121~~ → **7 (approved)** ✓ Wave 4 closed | Wave 4 | 7 remaining are inside `<PageHeader subtitle>` (string prop, not ReactNode) |

## ESLint rule flips (Wave 0 — DONE)

- `@typescript-eslint/no-explicit-any` — `'warn'` → `'error'`.
- `no-console` — `['error', { allow: ['warn', 'error', 'info'] }]` → `'error'` (no allow list).

These two flips are responsible for the bulk of the 624 errors in the baseline.
They will drive down monotonically through Waves 4 + 5.

## Gates created (Wave 0 — DONE; wired into pre-commit per-wave)

- `scripts/lint/check_db_dep.py` — wired into pre-commit at the end of Wave 1.
- `scripts/lint/check_permission_format.py` — wired into pre-commit at the end of Wave 6.

## Playwright cross-tenant probe (Wave 0 — scaffolded)

`playwright/tests/cross-tenant-leak.spec.ts` runs against the live backend
and asserts no list endpoint returns rows from a different `organizationId`.
Populated incrementally as Wave 1 closes routes.

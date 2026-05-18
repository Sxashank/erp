# AGENTS.md — SMFC ERP Working Contract

> **This file is the standing contract for every change to this repository.** Any Codex session, human contributor, or agent operating on this codebase must read it first and honor it on every commit. Deviations require a ticketed decision that updates this file in the same PR. There are no exceptions.

---

## 0. How to read this file

- Sections 1–4 establish **what** we are building.
- Sections 5–10 establish **how** code is written and tested.
- Sections 11–13 establish **the rules of engagement** (bug-fix protocol, forbidden shortcuts, Definition of Done).
- Sections 14–15 are the **runbook** and **ownership**.

If a rule here conflicts with a prompt, habit, or external style guide, this file wins. If a rule here is wrong for a specific case, update this file in the same PR that deviates.

---

## 1. System purpose & quality bar

**What this is.** SMFC ERP is a **multi-tenant SaaS** serving Indian NBFCs under RBI Scale-Based Regulation. One deployment runs many NBFCs; each NBFC is one `Organization` row and its data is isolated by PostgreSQL Row-Level Security keyed on `app.current_org_id`. It covers the full NBFC back office and front office: general ledger, loan origination (LOS), loan management (LMS), collections, NPA and legal, treasury and ALM, HRIS and payroll, fixed assets, TDS, GST, bank reconciliation, fixed deposits, compliance, document management, notifications, BI, and portals for borrowers, employees, and vendors.

**Current client rollout scope — all modules, manual-first.** The client has confirmed that the application must show the full ERP module set, not only loan modules. Loan-only routing, loan-only sidebars, or feature gates that hide non-loan ERP modules are temporary development aids only and must not be the shipped default. Every module must remain usable through a **manual operational flow** first: users can create, approve, post, upload, reconcile, record, and report data manually without requiring any external bank, tax, bureau, payment, or government portal integration. Automated flows may be added later, but they must sit beside the manual flow and must not replace it until the client explicitly approves the release.

**Automation stance for this phase.** Internal automation is allowed where it needs no external integration and improves correctness or productivity, for example schedule generation, accrual calculation, ageing buckets, DPD/NPA classification, provisioning calculations, dashboard rollups, report exports, voucher generation from approved internal events, reminders, validations, and workflow routing. External integrations are release-gated future capabilities. Until released, the UI may expose configuration or status only where useful, but operational screens must continue to work manually and must clearly avoid pretending that a live external connection exists.

**SaaS mental model — load-bearing for many rules below.** Assume every architectural decision is stress-tested by "what happens when we add the 100th tenant." Specifically:

- **Tenant isolation is primary.** No query, no cache, no queue job, no log line, no exported report may cross org boundaries without an explicit admin audit trail. RLS handles the default case; service code must preserve it on every new code path.
- **Tenant-specific secrets live in DB settings, not env.** Each NBFC has its own Razorpay merchant ID, GSTN password, bureau API key, NACH corporate ID, SMS sender ID. These belong in Fernet-encrypted per-tenant settings tables (see §6.8). Platform secrets (JWT key, DB URL, our own encryption key) are the only things in env / pydantic-settings.
- **Onboarding a new tenant must not require a redeploy.** Seed data, permissions, feature-flag defaults, and integration credentials are all provisioned through the admin UI / DB, not the build pipeline.
- **Schema migrations are tenant-agnostic.** `alembic` migrations affect everyone at once — never add `if organization_id == 'acme'` branches to migration logic. Per-tenant customization lives in settings or feature flags, not schema shape.
- **Per-tenant billing / usage metering.** Every expensive resource (storage, emails, SMS, bureau pulls, GSTN calls) must be attributable to the owning organization; emit a metric or row with `organization_id` when consumed. Even if we don't charge yet, the accounting must be there.
- **Incident blast radius is "one tenant at most" by default.** If an operation would impact multiple tenants, it goes behind a platform-admin permission + maker-checker + audit log.

**Who uses it.** Operations, finance, credit, collections, legal, HR, treasury, branch staff, borrowers (self-service portal), employees (ESS), vendors (vendor portal), internal auditors, and statutory auditors and regulators on inspection. Above all of them is the **platform team** (us) — the SaaS operators who own one deployment servicing many NBFCs.

**Authoritative specs.** The source of truth for domain behavior is `refdocs/` (7 phase tech specs + HRMS design + capability/module reports). When in doubt, read the refdoc; when a refdoc conflicts with the code, fix the code.

**Quality bar.** Treat this as a core banking system. Any defect in accounting, tax, lending lifecycle, auth, audit, or data integrity is a **critical** defect. A "minor" UI bug on a critical-path screen is still a defect. "It works on my machine" and "tests pass" are not the same thing.

**Lifespan and records.** Expect 7+ years of operation. Financial records retain for 7 years; login/audit logs for 2 years minimum. Schemas, APIs, and workflows must be evolvable under audit.

---

## 2. Repository layout & tooling

### 2.1 Stacks

- **Frontend**: React 18 · TypeScript 5.4 · Vite 5 · Tailwind CSS 3 · shadcn/ui (Radix primitives) · react-hook-form 7 · zod 4 · axios 1 · react-router-dom 7 · recharts 3 · lucide-react 0.408 · react-grid-layout · jspdf · xlsx.
- **Backend**: FastAPI · SQLAlchemy 2 async · asyncpg · Alembic · Pydantic v2 · passlib[argon2] · python-jose · pyotp · structlog · APScheduler · httpx · Redis 7 · PostgreSQL 15.
- **Runtimes**: Node 20 LTS · Python 3.11 · PostgreSQL 15 · Redis 7.
- **Containers**: `docker-compose.yml` at repo root brings up `db`, `redis`, `backend`, `frontend` on `smfc_network`.

### 2.2 Package manager — **pnpm only**

Both `package-lock.json` and `pnpm-lock.yaml` exist today. **The contract is pnpm.** Delete `package-lock.json`. Run only `pnpm install`. `package.json` must declare `"packageManager": "pnpm@<version>"` and `"engines": { "node": ">=20" }`. Do not introduce `npm` or `yarn` usage in CI, scripts, or documentation.

### 2.3 Top-level layout

```
erp/
├── AGENTS.md                        # this file
├── README.md
├── CLAUDE_REVIEW_PROMPT.md          # the review charter that produced AGENTS.md
├── package.json · pnpm-lock.yaml    # frontend manifest (pnpm)
├── tsconfig.json · tsconfig.node.json
├── vite.config.ts                   # Vite + Vitest config
├── tailwind.config.cjs · postcss.config.cjs
├── playwright.config.ts             # Playwright config (to be added)
├── docker-compose.yml               # dev services
├── start.sh                         # one-shot dev bringup
├── index.html                       # Vite entry
├── src/                             # frontend (see §5)
├── backend/                         # backend (see §6)
├── refdocs/                         # domain source of truth (do not edit casually)
└── .github/workflows/               # CI (to be added)
```

### 2.4 Scripts expected on `package.json`

The following scripts are the contract. They must exist and they must work.

```
dev                # vite
build              # vite build
preview            # vite preview
lint               # eslint . --max-warnings=0
lint:fix           # eslint . --fix
typecheck          # tsc --noEmit
format             # prettier --write .
format:check       # prettier --check .
test               # vitest run (unit)
test:watch         # vitest
test:integration   # vitest run --project integration (MSW-backed)
test:coverage      # vitest run --coverage
test:e2e           # playwright test
test:e2e:ui        # playwright test --ui
test:e2e:debug     # playwright test --debug
```

Backend equivalents (run from `backend/`): `pytest`, `pytest --cov=app --cov-report=term-missing`, `ruff check .`, `ruff format .`, `black --check .`, `mypy app`, `alembic upgrade head`, `alembic revision --autogenerate -m "..."`.

---

## 3. Architecture overview

### 3.1 Request path

```
Browser
   │   (React Router + react-query)
   ▼
src/hooks/<domain>/*        ← domain hooks, the ONLY callers of axios
   │
   ▼
src/services/<domain>/*     ← axios wrappers; thin, typed, no business logic
   │   HTTPS + Bearer JWT
   ▼
FastAPI /api/v1/*           ← app/api/v1/endpoints/*; thin handlers
   │
   ▼
app/services/*              ← business rules; OWN the transaction
   │
   ▼
app/repositories/*          ← data access; SQLAlchemy only
   │
   ▼
app/models/*                ← ORM; extends BaseModel + mixins
   │
   ▼
PostgreSQL (RLS per org)      Redis (cache · queues · rate-limit)
```

### 3.2 Layering rules (backend)

- **Endpoints** do input validation (Pydantic), auth/permission checks (Depends), and one service call. They do not read repositories, do not branch on business rules, and do not manage transactions.
- **Services** own the transaction (`async with db.begin():`). Services call other services and repositories. One service method = one user-facing operation = one transaction boundary.
- **Repositories** do SQLAlchemy only. No HTTP, no business validation, no workflow.
- **Models** are ORM classes extending `BaseModel` (`app/models/base.py`) with `AuditMixin`, `SoftDeleteMixin`, `VersionedMixin` as appropriate. No method on a model triggers I/O.

Violations (e.g. an endpoint calling a repository directly, a service issuing an implicit commit, a model method calling `session.execute`) are defects.

### 3.3 Layering rules (frontend)

- **Pages** (`src/pages/<module>/*`) compose components. They never call axios; they never call `localStorage` directly for app state; they never define inline UI primitives (see §5).
- **Hooks** (`src/hooks/<domain>/*`) wrap react-query around service calls. All server state passes through a hook.
- **Services** (`src/services/<domain>/*`) are thin typed axios wrappers. No caching, no retry logic, no business rules.
- **Components** (`src/components/*`) are pure presentational or light container components. Domain components live under `src/components/<domain>/`; cross-module primitives under `src/components/common/`; raw shadcn under `src/components/ui/` (wrap, don't modify).

### 3.3.1 API naming contract — Pydantic aliases are mandatory

- **Python internals stay snake_case.** ORM models, service variables, repository filters, and Pydantic field names use normal Python `snake_case`.
- **Frontend-facing JSON is camelCase.** Any API consumed by React pages, hooks, or services must serialize responses as `camelCase` using `CamelSchema` from `backend/app/schemas/base.py` and FastAPI `response_model_by_alias=True`.
- **New request schemas are camelCase-compatible.** Frontend-facing mutation bodies should inherit `CamelSchema` so Pydantic accepts both canonical Python `snake_case` and frontend `camelCase`; new frontend services must send one documented shape, preferably `camelCase`.
- **Legacy `BaseSchema` endpoints are migration debt.** If a touched endpoint still emits or requires `snake_case` JSON for the frontend, migrate the backend schema/route contract to `CamelSchema` instead of adding client aliases.
- **Frontend types use camelCase only.** Shared TypeScript DTOs and page code must not define duplicate `snake_case`/`camelCase` fields, local mappers, or fallback aliases. The service layer consumes one documented API contract and pages consume typed service output.

### 3.4 Multi-tenancy

- Every mutable table has `organization_id` (UUID, not null, indexed).
- PostgreSQL Row-Level Security enforces tenant isolation via the session GUC `app.current_org_id`.
- Backend dependency `get_db_with_tenant` (in `app/api/deps.py`) sets the GUC before the endpoint runs and clears it after. **Every authenticated route uses `get_db_with_tenant`.** Routes that must cross tenants (super-admin endpoints) use a different dependency and are explicitly audited.
- Frontend mirrors via `OrganizationContext`: every hook reads `activeOrganizationId` from context and passes it on the wire (the backend does not trust it; the backend reads it from the JWT + RLS). No page may hard-code or omit the organization ID.

### 3.5 Environments

| Env            | Frontend URL          | Backend URL           | DB                      | Notes                          |
| -------------- | --------------------- | --------------------- | ----------------------- | ------------------------------ |
| local          | http://localhost:5176 | http://localhost:8001 | Docker postgres:15      | Set by `start.sh`              |
| docker-compose | http://localhost:3000 | http://localhost:8000 | container `db`          | `docker compose up`            |
| staging        | TBD                   | TBD                   | managed Postgres        | per-branch previews encouraged |
| production     | TBD                   | TBD                   | managed Postgres + PITR | blue/green; locked migrations  |

Frontend dev port is **5176** (set in `vite.config.ts`). Backend dev port is **8001** (set in `start.sh`). `VITE_API_URL` defaults to `http://localhost:8001/api/v1` (see `src/services/api.ts`).

---

## 4. Module inventory

For each module: frontend pages folder, backend API prefix, key models/services, external integrations, and refdoc reference. This is the canonical inventory; keep it up to date.

### 4.1 Auth · Users · Roles · Permissions

- Frontend: `src/pages/auth/`, `src/pages/users/`, `src/pages/roles/`.
- Backend: `/api/v1/auth`, `/users`, `/roles`.
- Models: `User`, `Role`, `Permission`, `user_role`, `role_permission` in `app/models/auth/`.
- Services: `app/services/auth/*`, `app/core/security.py` (JWT, MFA/TOTP, Argon2).
- Integrations: (none external); TOTP via `pyotp`.
- Spec: `refdocs/Phase1_TechSpec_Part1_Masters.md` (§Users & Roles).

### 4.2 Masters & Organization

- Frontend: `src/pages/masters/{organizations,units,departments,designations}/`.
- Backend: `/organizations`, `/units`, `/departments`, `/designations`.
- Models: `Organization`, `Unit`, `Department`, `Designation`, `FinancialYear`, `Period`, `CostCenter`.
- Spec: `refdocs/Phase1_TechSpec_Part1_Masters.md`.

### 4.3 Finance · GL · Vouchers · Periods

- Frontend: `src/pages/finance/`, `src/pages/accounting/`.
- Backend: `/financial-years`, `/account-groups`, `/accounts`, `/voucher-types`, `/vouchers`, `/gl-entries`, `/cost-centers`, `/accounting/approval-matrix`.
- Models: `Account`, `AccountGroup`, `Voucher`, `VoucherLine`, `GLEntry`, `CostCenter`, `Period`, `ApprovalMatrix`.
- Services: `app/services/finance/*` — notably `gl_posting_service.py` (balanced-entry enforcement, period lock, cost-center propagation, reversals).
- Invariants: every voucher balances (Σdebit = Σcredit); only leaf accounts receive postings; posting to HARD_CLOSED periods is rejected; reversals are contra-entries, never edits.
- Spec: `refdocs/Phase1_TechSpec_Part2_GL_Flows.md`.

### 4.4 AP / AR · Vendors · Customers · Payments · BRS

- Frontend: `src/pages/ap-ar/`.
- Backend: `/payment-terms`, `/vendors`, `/customers`, `/purchase-bills`, `/sales-invoices`, `/payments`, `/bank-reconciliation`.
- Models: `Vendor`, `Customer`, `PurchaseBill`, `SalesInvoice`, `Payment`, `PaymentTerm`, `BankStatement`, `BRSMatch`.
- Services: `app/services/ap_ar/*`, `app/services/finance/brs_service.py`.
- Integrations: bank statement feeds (SFTP/API), payment gateways (Razorpay/Paytm/CCAvenue), e-Invoice IRP, e-Waybill.
- Spec: `refdocs/Phase6_TechSpec_FA_TDS_GST_BRS_FD.md`.

### 4.5 GST

- Frontend: `src/pages/gst/`.
- Backend: `/gst/rates`, `/gst/hsn-sac`, `/gst/registrations`, `/gst/gstn`.
- Models: `GSTRate`, `HSNSAC`, `GSTRegistration`, `GSTRTxn`, `GSTRFiling`.
- Services: `app/services/gst/*` (gstn_service, registration_service). **Currently partial — see §12 forbidden shortcuts; no mock returns in production paths.**
- Integrations: GSTN portal (GSTR-1/3B/9/2B), e-Invoice IRP, e-Waybill.
- Spec: `refdocs/Phase6_*`.

### 4.6 TDS

- Frontend: `src/pages/tds/`.
- Backend: `/tds/sections`, `/tds/entries`, `/tds/challans`, `/tds/returns`, `/tds/form16a`.
- Models: `TDSSection`, `TDSEntry`, `TDSChallan`, `TDSReturn`, `Form16A`.
- Services: `app/services/tds/*`.
- Integrations: TRACES, NSDL (Form 24Q/26Q/16A).
- Spec: `refdocs/Phase6_*`.
- Rates: **never hardcoded**; read from `mst_tds_section` by effective date. PAN-absent rate = 20%.

### 4.7 Lending — LOS

- Frontend: `src/pages/lending/los/` (entities, products, applications, sanctions).
- Backend: `/api/v1/lending/entities`, `/applications`, `/products`, `/sanctions`, `/kyc`, `/aa`, `/credit`.
- Models: `Entity`, `LoanApplication`, `LoanProduct`, `TechnicalAppraisal`, `FinancialAnalysis`, `LoanSanction`, `DocChecklist`, `KYCRecord`.
- Services: `app/services/lending/{entity,application,appraisal,sanction,kyc}_service.py`.
- Integrations: CKYC, AA, CIBIL/Experian/Crif, CERSAI (charge registration at sanction acceptance).
- Spec: `refdocs/Phase2_*`.

### 4.8 Lending — LMS, Collections, NPA, Legal

- Frontend: `src/pages/lending/lms/`, `src/pages/lending/collections/`, `src/pages/legal/`.
- Backend: `/lending/loan-accounts`, `/disbursements`, `/receipts`, `/schedules`, `/collections`, `/npa`, `/ots`, `/restructure`, `/legal`.
- Models: `LoanAccount`, `Tranche`, `PrincipalSchedule`, `InterestSchedule`, `RateReset`, `Demand`, `Receipt`, `NPAClassification`, `OTS`, `Restructure`, `LegalCase`, `Writeoff`.
- Services: `app/services/lending/{loan_account,schedule,demand,receipt,npa,ots,restructure,legal}_service.py`.
- Invariants:
  - EMI = `P · r · (1+r)ⁿ / ((1+r)ⁿ − 1)`; day-count explicit (`ACT/365` default).
  - Receipt allocation priority: **penal → charges → overdue interest → current interest → overdue principal → current principal**. Do not reorder.
  - NPA buckets (DPD, per RBI): `standard (0) · sma_0 (1–30) · sma_1 (31–60) · sma_2 (61–90) · substandard (91–365) · doubtful_1 (366–730) · doubtful_2 (731–1095) · doubtful_3 (1096–1460) · loss (1461+)`. Changes require a migration note and regression tests.
  - Provisioning rates per RBI secured/unsecured table. Never hardcoded — read from a seed table (`mst_provisioning_rate`).
  - Upgrades: all overdues cleared + 3 months current performance.
- Integrations: NeSL (charge/security interest), NACH (auto-debit mandate), CRILC (monthly disbursement/repayment/NPA dump), DRT/NCLT/SARFAESI case trackers.
- Spec: `refdocs/Phase3_*`.

### 4.9 Treasury · ALM · Risk

- Frontend: `src/pages/treasury/`, `src/pages/lending/treasury/`.
- Backend: `/treasury`, `/lending/treasury/{borrowings,lenders,alm,gap-analysis,interest-rate-risk}`.
- Models: `Borrowing`, `Lender`, `ALMPosition`, `IRSAnalysis`, `Exposure`, `PortfolioRisk`.
- Services: `app/services/lending/treasury/*`.
- Invariants: liquidity gap by RBI buckets; single-borrower limit 15% of Tier-1 (infra carve-out 20%); group limit 25%; CRAR > 15%. ECL per Ind-AS 109.
- Spec: `refdocs/Phase4_*`.

### 4.10 HRIS

- Frontend: `src/pages/hris/`.
- Backend: `/api/v1/hris/*` (employees, shifts, holidays, leave-types, leave-applications, attendance, separation, training, performance).
- Models: `Employee`, `Shift`, `Holiday`, `LeaveType`, `LeaveApplication`, `AttendanceRecord`, `Separation`, `TrainingProgram`, `AppraisalCycle`.
- Spec: `refdocs/Phase5_*`, `refdocs/hrms_design.md`.

### 4.11 Payroll & Statutory

- Frontend: `src/pages/payroll/`.
- Backend: `/api/v1/payroll/*` (components, structures, employee-salary, statutory, batches, payslips).
- Models: `SalaryComponent`, `SalaryStructure`, `EmployeeSalary`, `PayrollBatch`, `Payslip`, `StatutoryFiling`.
- Services: `app/services/payroll/*`.
- Invariants:
  - PF: 12% on (Basic + DA) capped at ₹15,000; employer 3.67% + EPS 8.33% + admin 0.5%.
  - ESI: 0.75% / 3.25% (employee/employer); gross ≤ ₹21,000.
  - Professional Tax: state-wise (Maharashtra slab encoded in `mst_pt_slab`).
  - Gratuity: `(last drawn × 15 × years) / 26`, cap ₹20,00,000, eligibility ≥ 5 years.
  - TDS regime: old/new switchable; standard deduction ₹75,000 (new); 80C/80D exemptions applied only in old regime.
  - Attendance lock is **mandatory** before payroll processing. Bank-account verification required before payout. LOP days carry no statutory deduction.
- Integrations: EPFO, ESIC, state PT portal, TRACES (24Q), core banking (NEFT/RTGS salary file).
- Spec: `refdocs/Phase5_*`.

### 4.12 Fixed Assets

- Frontend: `src/pages/fixed-assets/`.
- Backend: `/fixed-assets`.
- Models: `FixedAsset`, `AssetCategory`, `Depreciation`, `Disposal`, `PhysicalVerification`, `Lease`.
- Services: `app/services/fixed_assets/{asset,depreciation,lease,approval,lifecycle}_service.py` — these are among the better-covered services in tests (`backend/tests/fixed_assets/`).
- Invariants: capitalization threshold ₹5,000; SLM and WDV supported; full-month convention if put-to-use > 15 days in the month; disposal creates GL entries and closes depreciation.
- Spec: `refdocs/Phase6_*`.

### 4.13 Fixed Deposits

- Frontend: `src/pages/fixed-deposits/`.
- Backend: `/fixed-deposits`.
- Models: `FDPlaced`, `FDCollateral`, `FDInterest`.
- Invariants: FDs placed → accrue interest daily; TDS @ 10% on interest. FDs as collateral → 25% default haircut; lien-marked with bank; released only on loan closure.
- Spec: `refdocs/Phase6_*`.

### 4.14 Inventory

- Frontend: `src/pages/inventory/`.
- Backend: `/inventory`.
- Models: `InventoryItem`, `StockTxn`, `ReorderLevel`, `StockAdjustment`.

### 4.15 Workflow · Approvals · Maker-Checker

- Frontend: `src/pages/workflow/`.
- Backend: `/workflows`, `/approvals`.
- Services: `app/services/workflow/{workflow_engine,approval_service,escalation_service,background_tasks}.py`.
- Invariant: **maker ≠ checker** on all financial, credit, HR, user-role-grant, and OTS actions. Escalation SLA and delegated authority matrix (amount bands) are table-driven.

### 4.16 DMS

- Frontend: `src/pages/dms/`.
- Backend: `/dms`.
- Models: `Document`, `DocumentVersion`, `Folder`, `AccessLog`.
- Invariants: versioned; content-type allowlist; size cap; antivirus scan hook; PUBLIC/PRIVATE/RESTRICTED access; every read is audited.

### 4.17 Notifications

- Frontend: `src/pages/notification/`.
- Backend: `/notifications`.
- Channels: email, SMS, push, in-app. Templates stored in DB; rendering is Jinja2 with PII-safe filters.
- Integrations: SMTP (`config.py` SMTP\_\*), Msg91 or equivalent for SMS (to be wired), FCM/APNS for push.

### 4.18 Compliance

- Frontend: `src/pages/compliance/`.
- Backend: `/compliance`.
- Models: `ComplianceItem`, `ComplianceInstance`, `FilingRecord`.
- Reminders at D-7 (warning) and D+3 (escalation) via APScheduler job.

### 4.19 Reports · BI

- Frontend: `src/pages/reports/`, `src/pages/bi/`.
- Backend: `/reports`, `/bi`.
- Core reports: Trial Balance, P&L, Balance Sheet, Day Book, Ledger, Cash Flow, AUM, Collection Efficiency, NPA Movement, MIS, Regulatory (NBS-1/2/3/4/7, ALM, CRILC).
- Export: PDF via `jspdf`, Excel via `xlsx`, CSV — through the `<ExportMenu>` component (§5.7).

### 4.20 Portals

- Borrower/Customer: `src/pages/portal/` → `/portal`.
- Employee Self-Service: `src/pages/ess/` → `/ess`.
- Vendor: `src/pages/vendor/` → `/vendor-portal`.
- Each portal has its own `src/screens/<portal>/` login page and its own layout. Portal auth is a separate dependency (`get_current_portal_user`) and has stricter rate limits (§8.3).

### 4.21 Audit & System

- Backend: `/audit-logs`, `/jobs`, `/webhooks`, `/integrations`.
- Middleware: `app/middleware/audit.py` captures HTTP-level audit; services emit domain audit rows for financial mutations.

---

## 5. Frontend coding standards

### 5.1 "Every UI element is a component" (non-negotiable — strict)

This is a multi-tenant ERP SaaS. Visual consistency across 354 pages × N tenants is not a nice-to-have — it's correctness. If a UI element appears in more than one place — or could — it **must** be a component under `src/components/`. Pages compose components; pages do not build UI primitives.

**Strict prohibitions (any of these in a page file is a defect):**

- Hand-rolled page header `<div>`s. Use `<PageHeader>` (§9.2).
- Hand-rolled tables (`<table>`, shadcn `<Table>` directly, or a `<div>`-based grid). Use `<DataTable>`.
- Hand-rolled filter bars (a `<div className="flex gap-4">` wrapping inputs + selects). Use `<FilterBar>`.
- Hand-rolled forms (`<form>` with a collection of `<Input>`/`<Select>` rendered directly). Wrap in `<FormShell>` with `<FormSection>` for groups, and use react-hook-form + zod via shadcn `<Form>`/`<FormField>` primitives — see §5.3.
- Inline back buttons (`<Button variant="ghost" size="icon"><ArrowLeft/></Button>`). Use `<PageHeader breadcrumbs={[...]}>` — the `PageHeader` renders the back-navigation affordance.
- Inline money (`value.toFixed(2)`, `Intl.NumberFormat(...)` in a `<span>`). Use `<AmountDisplay>`.
- Inline dates (`new Date(x).toLocaleDateString(...)` or `format(x, 'dd MMM yyyy')` in a `<span>`). Use `<DateDisplay>`.
- Inline status badges (`<Badge className="bg-green-100 text-green-800">Active</Badge>`). Use `<StatusPill>` / `<DpdBadge>` / `<KYCBadge>` / `<StageBadge>` / `<PriorityBadge>` / etc.
- Inline PII (a raw `<span>{user.pan}</span>` or `<span>{loan.aadhaar}</span>`). Use `<PANField>`, `<AadhaarField>`, `<PhoneField>` — the masked-by-default components.
- Inline "loading" spinner `<Loader2 className="animate-spin"/>` on list pages. Use `<SkeletonTable>`. On detail pages use `<Skeleton>` for individual regions. On buttons use the button's own `disabled={pending}` + inline spinner (permitted only inside a button).
- Inline "no results" text. Use `<EmptyState title subtitle>`.
- Inline error fallback. Use `<ErrorState error onRetry={refetch}>`.

**Canonical catalog** (`src/components/common/`, domain-wrapped under `src/components/<domain>/`). Anything like this must be a component and be reused — never inlined:

- Layout + shell: PageHeader, PageSection, Breadcrumbs, ActionBar, SideSheet, InlineTabs, WizardShell, FormShell, FormSection, DetailGrid, DefinitionList, KeyValueRow, FilterBar
- Data surfaces: DataTable, ColumnChooser, Pagination, SkeletonTable, LoadingRow, EmptyState, ErrorState, ExportMenu
- Money + dates + numbers: AmountDisplay, AmountInput, PercentageDisplay, PercentageInput, DateDisplay, DatePicker, DateRangePicker
- Status + identity: StatusPill, DpdBadge, RatingBadge, KYCBadge, PriorityBadge, StageBadge, PermissionGate, FeatureFlagGate
- Pickers: EntityPicker, PartyPicker, AccountPicker, CostCenterPicker, OrgPicker, UnitPicker, EmployeePicker, VendorPicker, CustomerPicker, ProductPicker
- Uploads + documents + signers: UploadDropzone, DocumentChip, SignerCard, AddressBlock, BankAccountBlock
- PII fields (masked by default): PANField, GSTINField, AadhaarField, PhoneField, EmailField, BankAccountField, IFSCField
- Interaction: ConfirmDialog, FieldError, FieldLabel, HelpText

**Rules:**

1. If you find yourself writing a styled `<div>` with more than ~10 lines of JSX, stop and make it a component.
2. If you're about to write the same 3 lines of JSX twice in a single file, stop and make it a component.
3. If a component already exists under `src/components/common/` or `src/components/<domain>/`, you **must** use it. Checking "does this exist" is the first step when starting any page change; open `src/components/` and skim before typing.
4. If a component _should_ exist but doesn't yet, build it under `src/components/common/` or `src/components/<domain>/` (not inline in the page) and wire the page to consume it. Separate PR if the component needs its own tests — AGENTS.md §10.0 still applies (unit + integration + E2E).
5. `src/components/common/*` are covered by design-token contract tests (`src/components/common/design-tokens.test.tsx`). Any component you add here must carry a test that pins its canonical class tokens so it can't drift silently.

### 5.2 Folder convention

```
src/components/
├── ui/          ← shadcn primitives. Do not modify; wrap if you need variants.
├── common/      ← cross-module atoms & molecules (PageHeader, DataTable, AmountDisplay, …)
├── lending/    ┐
├── finance/    │
├── hris/       │  ← domain components. Reusable within the domain.
├── payroll/    │
├── gst/        │
├── treasury/   │
├── portal/     │
├── ess/        │
├── vendor/     │
└── bi/         ┘
```

Domain components may depend on `common/` and `ui/`. `common/` may depend only on `ui/`. `ui/` depends only on Radix/shadcn. No upward dependencies.

### 5.3 Forms (strict)

Every form in this codebase uses react-hook-form + zod, rendered through shadcn's `<Form>`/`<FormField>`/`<FormItem>`/`<FormLabel>`/`<FormControl>`/`<FormMessage>` primitives, wrapped in `<FormShell>`.

**Required:**

- **RHF + zod via `<Form>` + `<FormField>`** — every input, every checkbox, every select. Raw `register()` outside `<FormField>` is forbidden (the `<FormField>` wrapper provides `<FormMessage>` for inline errors + a11y wiring).
- **Zod schemas live under `src/schemas/<domain>/`** — one file per form or logical group. Export `schema`, `type XxxInput = z.infer<typeof schema>`, and helpers. No schemas defined inside the page file.
- **Money fields**: `z.coerce.number().nonnegative()` or `.positive()` as appropriate. The input is `<AmountInput>`, which stores `number | null` and formats on blur.
- **Percentage fields**: `z.coerce.number().min(0).max(100)` for rates. Render with `<PercentageInput>`.
- **Date fields**: `z.string().date()` for business dates (ISO `yyyy-MM-dd`). Render with `<DatePicker>`.
- **PII fields**: `<PANField>`, `<AadhaarField>`, `<PhoneField>`, `<EmailField>`, `<GSTINField>` — these validate format AND mask display by default.
- **Required validation**: use `z.string().min(1, "Required")` + trim; for selects, `z.string().uuid()` or a `z.enum([...])`.
- **Cross-field rules**: `.superRefine((val, ctx) => {...})`. Never write ad-hoc `useEffect` validation in the component.
- **Multi-step**: `<WizardShell>` with step-scoped schemas; final submit validates the merged result. Each step's `onNext` triggers `form.trigger([...fieldNames])`.
- **Submit buttons**: `disabled={form.formState.isSubmitting}`, with a spinner inside. The `<FormShell>` renders the action bar; pages do not add their own submit row.
- **Error messages**: user-facing English, sentence case, no trailing period on labels. Inline errors via `<FormMessage>`. Page-level failures (API 4xx/5xx) go into a top-of-form `<ErrorState>` strip, not a toast.
- **No `<Input>` rendered directly in a page's form body** — every input sits inside a `<FormField>` that owns its validation, label, and error.
- **Date / money / PII inputs must not be raw `<Input>`** — use the named wrapper from §5.1's catalog.

### 5.4 Data fetching — react-query, nothing else

- `@tanstack/react-query` is the server-state layer. Every page reads/writes server state via a hook.
- Hooks live in `src/hooks/<domain>/*` and follow the naming convention `use<Noun>[s]` for queries (`useLoanApplications`, `useLoanApplication(id)`) and `use<Verb><Noun>` for mutations (`useCreateLoanApplication`, `useApproveSanction`).
- Query keys are arrays: `['loan-applications', filters]`, `['loan-application', id]`. Invalidation is explicit.
- Never call axios directly from a page. Never use `useState` to hold fetched server data.
- Cache defaults: `staleTime: 30_000`, `refetchOnWindowFocus: false`, `retry: 1`. Override per hook when needed.

### 5.5 Client state — Zustand + Context

- Server state → react-query.
- Cross-page UI state (sidebar collapse, toast queue, notification tray, global modal stack, current filters persisted in URL) → **Zustand** stores under `src/stores/`.
- Auth + organization → **Context** (`AuthContext`, `OrganizationContext`) because they are infra-level and change rarely.
- Component-local ephemeral state → `useState`. Do not pass local state through more than 2 levels of props; hoist to a store.

### 5.6 Auth & organization context (current state is a stub — §12)

`src/contexts/AuthContext.tsx` today returns a hardcoded user and `isAuthenticated: true`. **This is a known placeholder and must not ship.** The real contract:

- `AuthProvider` owns: `user`, `permissions: Set<string>`, `organizations: Organization[]`, `activeOrganizationId`, `isAuthenticated`, `login`, `logout`, `refresh`.
- Tokens are **not** read from `localStorage` inside services; axios gets them from the provider via an interceptor. On refresh-failure, `logout()` is invoked and the user is redirected to `/login`.
- `usePermission("resource.action")` is the only way to gate UI. Sidebar items, buttons, and routes all consult it.
- `OrganizationContext` (or a slice of AuthContext) owns `activeOrganizationId` and `switchOrganization(id)`, persisted in `localStorage` and synchronized across tabs via `BroadcastChannel`.

### 5.7 Loading, empty, error — mandatory for every list and detail view (strict)

Three states MUST be rendered on every page that fetches data. If any of these is missing, the page is incomplete.

| State   | Component                                                                                         | Trigger                                       |
| ------- | ------------------------------------------------------------------------------------------------- | --------------------------------------------- |
| Loading | `<SkeletonTable rows={N}>` for table pages, `<Skeleton>` variants from `common/` for detail pages | `query.isLoading && !query.data` (first load) |
| Empty   | `<EmptyState title subtitle cta?>`                                                                | `query.isSuccess && query.data.length === 0`  |
| Error   | `<ErrorState error onRetry={() => refetch()}>`                                                    | `query.isError`                               |

**Strict rules:**

1. **No `<Loader2 className="animate-spin"/>` in a page's render tree for page-level loading.** That spinner pattern is for button-internal "saving" states only. Page loading = skeleton, always.
2. **No `if (loading) return null`** — that yields a blank screen, which §5.7 defines as a defect. Return the skeleton instead.
3. **`onRetry` must call `refetch()`**, not reload the window, not navigate away, not call the API directly. The hook's refetch is the only supported path.
4. **Empty-state CTA is actionable.** If there's nothing to show, suggest the next step: "Add your first customer" → button → `/admin/ap-ar/customers/new`. A bare "No results found" is insufficient; include a CTA whenever there is one.
5. **Background refetches (stale-while-revalidate) do NOT trigger the loading state.** `query.isFetching && query.data` must keep rendering current data. Only first loads show skeleton.

A blank screen during fetch is a defect. A silent failure is a defect. "It was broken silently and the user didn't notice" is the worst possible outcome for a financial system.

### 5.8 Money, percentages, dates, IDs, PII

- Money: `<AmountDisplay value={…} currency="INR" />`. `AmountInput` stores `number | null` and formats on blur with Indian digit grouping. Never `toFixed(2)` inline; never `parseFloat` user input directly.
- Percentage: `<PercentageDisplay value={12.5} />` renders `12.50%`. Storage is the number, not the string.
- Date: store and transport ISO `yyyy-MM-dd` for business dates, ISO-8601 + TZ for timestamps. Display via `<DateDisplay />` (default format `dd MMM yyyy`, IST). Never do `new Date().toLocaleString()` in components.
- IDs: always show the business number (e.g. `SMFC/BOM/HL/2526/0001`), never the UUID. UUIDs are for URLs only.
- PII: `<PANField>`, `<AadhaarField>`, `<PhoneField>` render masked by default; full value unlocks only with `pii.view` permission and is audited server-side.

### 5.9 TypeScript — strict

`tsconfig.json` must include:

```json
"strict": true,
"noUncheckedIndexedAccess": true,
"noImplicitOverride": true,
"noFallthroughCasesInSwitch": true,
"exactOptionalPropertyTypes": true,
"allowUnreachableCode": false
```

- `any` is forbidden outside of `.d.ts` adapter files. Prefer `unknown` + narrowing.
- `@ts-ignore` is forbidden. `@ts-expect-error` requires an inline reason and a ticket reference.
- Discriminated unions for state machines (loan app stages, NPA bucket, payroll batch status). No string unions when a finite enum is authoritative in the backend — derive types from the OpenAPI schema.

### 5.10 Imports & routing

- Only `@/` alias; no `../../../..`.
- `src/App.tsx` is a 1,127-line monolith today. Split into `src/routes/<module>.tsx` modules that export `RouteObject[]`, and lazy-load with `React.lazy` at the module boundary. The root router just assembles them.
- Every top-level module uses nested routes under `AdminLayout`, `EssLayout`, `PortalLayout`, or `VendorLayout` — not a parallel router tree.

### 5.11 Accessibility

- Every input has an associated `<Label>` (shadcn `FormLabel` satisfies this).
- Focus rings preserved site-wide; never remove `outline` without a replacement.
- Modals use Radix Dialog with focus trap; escape closes; first focusable element is focused on open.
- Tables: `<th scope="col|row">`; numeric columns `text-right` + tabular numerals.
- Color contrast AA. Do not convey information with color alone (NPA red + an icon + text label).
- Keyboard: all actions reachable; tab order logical; Enter submits forms; Escape cancels.

### 5.12 Logging on the frontend

- No `console.log` in committed code. Use `src/lib/logger.ts` (`debug`, `info`, `warn`, `error`) — a no-op in production builds, styled console in dev.
- Errors from react-query are surfaced via `<ErrorState>` and `toast`; they are not swallowed silently.
- Global error boundary (`<AppErrorBoundary>`) wraps the router and reports to telemetry.

### 5.13 Performance

- Code-split at the route boundary.
- Use `useMemo`/`useCallback` only when profiling shows a win. Do not prematurely memoize.
- Lists over ~200 rows use virtualization (`@tanstack/react-virtual`).
- Images: always set dimensions; lazy-load below the fold.

---

## 6. Backend coding standards

### 6.1 Layering (again, because it matters)

- `app/api/v1/endpoints/<module>/*.py` — route handler. Uses `Depends` for auth, permissions, DB-with-tenant. Validates via Pydantic. Delegates to a service. Returns a Pydantic response model.
- `app/services/<module>/*.py` — business logic. Owns the transaction boundary. Emits audit entries. Calls repositories and other services.
- `app/repositories/<module>/*.py` — data access. Inherits from `BaseRepository[Model, CreateSchema, UpdateSchema]`. No HTTP, no workflow, no business validation.
- `app/models/<module>/*.py` — ORM classes. Inherit from `BaseModel` + `AuditMixin` + `SoftDeleteMixin` + `VersionedMixin` as appropriate. No I/O in model methods.
- `app/schemas/<module>/*.py` — Pydantic v2 request/response models, with explicit `model_config = ConfigDict(from_attributes=True)` when reading from ORM.

### 6.2 SQL & data integrity

- **No f-string interpolation into `text(...)`.** `backend/app/database.py:92` currently interpolates `organization_id` into `SET LOCAL app.current_org_id = '{organization_id}'`. This is fixed in Stage 1 by `text("SET LOCAL app.current_org_id = :org_id").bindparams(org_id=str(organization_id))`. The rule applies everywhere.
- Raw SQL is allowed only via `text()` with parameter bindings. Prefer SQLAlchemy expression language.
- **Decimals**: `NUMERIC(18, 2)` for INR amounts, `NUMERIC(12, 6)` for FX rates, `NUMERIC(9, 4)` for interest rates and percentages. Python side uses `decimal.Decimal`. `Float` is banned for money.
- **Dates**: `DATE` for business dates, `TIMESTAMPTZ` for audit timestamps. Store UTC; convert to IST at serialization.
- **Fiscal year**: April–March IST. Every transactional row stamps `financial_year_id` and `period_id`. Posting to a HARD_CLOSED period is rejected at the service layer with `ClosedPeriodError`.
- **Soft delete**: all master and transactional tables use `SoftDeleteMixin`. Hard delete is prohibited in production code paths; it is allowed only in test factories.

### 6.3 Every mutating endpoint

- `Depends(get_current_user)` — authenticated.
- `Depends(RequirePermissions("<resource>.<action>"))` — authorized. Format is `<resource>.<action>` (e.g. `voucher.post`, `loan_application.approve`, `payroll.run`). Permission strings are documented in `app/core/constants.py`.
- `Depends(get_db_with_tenant)` — RLS context set.
- Pydantic request model — no bare dicts, no `**kwargs`.
- `Idempotency-Key` header **required** for all financial mutations (voucher post, payment, disbursement, receipt, payroll batch, adjustment, reversal). Middleware stores `(key, user_id, request_hash, response_body)` for 24h and replays on collision.
- Optimistic locking: update queries filter `WHERE id = :id AND version = :version`; mismatches raise `ConcurrencyConflictError(409)`.
- Pydantic response model — no `Model.dict()` from ORM; always a typed response.
- Audit: `AuditMiddleware` logs the envelope; services emit domain rows for financial actions with before/after diff.

### 6.4 Transactions

- One service method = one transaction = one user-facing operation.
- Use `async with db.begin():`. Do not call `session.commit()` inside service helpers; the outer boundary commits.
- Exceptions roll back automatically inside `begin()`. Re-raise as a typed exception (`AppException` subclass).
- Nested savepoints allowed via `begin_nested()` when a sub-step needs to fail independently (bulk import with per-row failures).

### 6.5 Pagination

- All list endpoints accept `skip: int = 0, limit: int = 50` with `limit` capped at **200**. Reject `skip < 0`.
- Response shape: `{ "items": [...], "total": <int>, "skip": <int>, "limit": <int> }`.
- Cursor pagination is acceptable for hot endpoints; document the cursor format in the response model.

### 6.6 Background jobs

- **Time-based** (escalations, daily digests, cleanup): APScheduler, set up in `app/services/workflow/background_tasks.py`. Lifespan hooks start/stop.
- **Fan-out / heavy** (bulk NPA reclassification, payroll run, GSTR dump, CRILC export, FA bulk import, notification fan-out): **Arq + Redis** worker queue (to be introduced). Jobs are idempotent and checkpointed.
- Never run heavy work inside a request handler. If the request can take > 3 seconds, enqueue a job and return a job ID.

### 6.7 Integrations

**Current phase: no live external integrations by default.** Do not build a workflow that requires a bank feed, GSTN/e-waybill portal, TRACES/NSDL, CKYC, bureau, NACH, payment gateway, EPFO/ESIC, SMS provider, e-sign, CERSAI, NeSL, or any other third-party system to complete the user's job. The manual path is the canonical path until the client approves that integration for release. When an external integration is added, it must be optional, tenant-scoped, feature-flagged, auditable, and must fall back to the manual workflow without data loss.

**Manual and automated flows share the same domain model.** Do not create a separate "manual-only" data structure or a parallel "automated-only" workflow. Store the business event once, with source metadata such as manual entry, file import, system calculation, or external webhook. This lets the organization start manual and later automate without migration-heavy rewrites.

Each external vendor lives under `app/integrations/<vendor>/` with:

```
client.py      # httpx.AsyncClient wrapper, typed methods
auth.py        # credential loading (Fernet-decrypted from settings)
schemas.py     # Pydantic request/response models
errors.py      # typed exceptions (VendorTimeoutError, VendorAuthError, …)
retry.py       # exponential backoff, 3 attempts max
circuit.py     # circuit breaker: open after 5 consecutive failures, half-open after 60s
```

Timeouts are explicit (`connect=5, read=30`). Webhooks verify HMAC + timestamp nonce (±5 min). Credentials never appear in code or logs; they are Fernet-encrypted at rest.

### 6.8 Secrets — **platform-scoped vs tenant-scoped (non-negotiable)**

**This is a multi-tenant SaaS.** Secrets fall into exactly two categories and are stored in two different places. Mixing them is a critical defect.

**Platform secrets** — identical for every tenant; belong in env / pydantic-settings / KMS-backed runtime config:

- `JWT_SECRET_KEY`, `JWT_ALGORITHM`
- `DATABASE_URL`, `REDIS_URL`
- `ENCRYPTION_KEY` (the Fernet key we use to wrap tenant secrets)
- SMTP relay creds for _our_ outbound mail (app-level, not the tenant's)
- Third-party platform services we pay for: OTel collector, error tracker, log aggregator
- Any other value that is part of our deployment, not a client's account

**Tenant secrets** — different per organization; belong in **DB-backed settings tables**, encrypted at rest with Fernet, keyed by `organization_id`, loaded at runtime via `services/*`:

- GSTN / NSDL / TRACES portal passwords (per GSTIN / per TAN / per deductor)
- Bank API credentials (each NBFC has its own corporate banking login, NACH corporate ID, UTR beneficiary account)
- Payment-gateway keys (Razorpay/Paytm/CCAvenue merchant IDs + secret keys belong to the NBFC, not the platform)
- Bureau subscription IDs + API keys (CIBIL/Experian/CRIF — each NBFC has its own contract)
- CERSAI / NeSL / e-Sign ESP accounts
- SMS provider (Msg91) account keys when the NBFC sends on its own branded sender ID
- CKYC gateway credentials
- Any key that would be invalid or wrong if it leaked into another tenant's data plane

**Rule:**

- If a value is part of our deployment → env var / `settings.py` / pydantic-settings.
- If a value belongs to a specific client / org → Fernet-encrypted DB row, org-scoped, accessed through a service.

**Canonical mechanisms in this repo:**

- **Vendor integrations (primary)** → `IntegrationConfig` at `sys_integration_config` (model: `app/models/core/integration_config.py`). Keyed by `(organization_id, integration_type, provider)`. Credential fields land in the `config_data` JSONB column, Fernet-encrypted per-key via `IntegrationService._encrypt_config_data` (`app/services/core/integration_service.py`) using `encryption_service.encrypt_dict` from `app/core/encryption.py`. Reads require `decrypt=True` on `IntegrationService.get(...)` — default reads return the still-encrypted blob so nothing leaks to logs or generic responses. Webhook URLs + secrets live on the same row so rotation is one update.
- **Domain-specific tenant secrets** → a dedicated encrypted column on the domain table, wrapped by a service helper. Example: `gst_registration.portal_password` (Fernet-encrypted per GSTIN via `gst_registration_service.get_portal_password`). Use this pattern when a tenant secret is tightly coupled to a domain record and `IntegrationConfig` would duplicate the relation.
- **Platform secrets** → `app/config.py` Settings class, loaded via `pydantic-settings` from env. One value per deploy, identical for every NBFC.

**Why this matters specifically:**

- Putting a tenant's Razorpay key in env hard-codes the platform to one NBFC — the second tenant onboards and instantly reads the first tenant's money.
- Env vars aren't rotatable per-tenant. If one NBFC's portal password leaks, we must rotate just theirs, not everyone's.
- Tenant-scoped audit requires "who read what key when" — that's a DB read, not an env lookup.
- Rolling out a new tenant must NOT require a redeploy. New orgs provision secrets through the admin UI (or programmatically) into the tenant settings table.

Platform secrets must NEVER enter the tenant settings table; tenant secrets must NEVER enter `.env` or `settings.py`. The `Settings` class in `app/config.py` is for platform values only. Use `app/services/tenant/settings_service.py` (or a domain-specific counterpart) for anything client-owned.

- Never commit `.env`, keys, certs, DB dumps.
- Plaintext storage of any secret — platform OR tenant — is a defect.
- If you find yourself adding a new env var that reads like a client's account info (`RAZORPAY_API_KEY`, `MSG91_AUTH_KEY`, `GSTN_USERNAME_ACME`), STOP. That's a tenant-scoped secret; route it through the DB.

### 6.9 Logging

- `structlog` only; `print` is banned.
- Log context: `correlation_id`, `user_id`, `organization_id`, `route`, `method`, `status`, `duration_ms`.
- PII redaction is mandatory: PAN (`XXXXX1234X`), Aadhaar (`XXXX-XXXX-1234`), phone (`+91-XXXXX-XX123`), email (`u***@domain.com`). Apply via `app/core/logging_config.py` processors.
- Audit logs are a separate logger (`audit`). Never cross-mix with request logs.

### 6.10 Python style

- `ruff` (select `E, F, I, N, W, UP, B, SIM, TID`), `black` (line 100), `mypy --strict` on `app/`.
- `async` all the way down in request paths. No `time.sleep`; use `asyncio.sleep`. No `requests`; use `httpx`.
- `Exception` catches are forbidden unless re-raised as a typed app exception; never silence.
- Type hints everywhere; `Any` in `app/` is a lint error.

---

## 7. API & data-integrity standards

- **URL prefix**: `/api/v1`. Breaking changes require `/api/v2` alongside with a deprecation schedule published in AGENTS.md §4.
- **Error envelope**:
  ```json
  { "error_code": "STRING_CODE", "message": "Human-readable", "details": {...}, "correlation_id": "uuid" }
  ```
  No FastAPI default 500 bodies. `app/core/exceptions.py::AppException` hierarchy enforces the shape.
- **Idempotency**: financial mutations require `Idempotency-Key` header (§6.3).
- **Optimistic locking**: every transactional model has `version`; conflicts return 409 (§6.3).
- **Currency integrity**: `SUM(debit) = SUM(credit)` enforced in the service before insert; failures raise `GLPostingFailedError`.
- **Rate tables**: GST and TDS rates live in `mst_gst_rate` and `mst_tds_section`, keyed by effective date. No literal rates in code.
- **Soft delete**: §6.2.
- **Pagination contract**: §6.5.
- **Response DTOs**: never leak ORM relationships implicitly. Explicit Pydantic response model per endpoint.

### 7.1 Domain invariants (quick reference — do not regress)

| Area          | Invariant                                                                                   |
| ------------- | ------------------------------------------------------------------------------------------- |
| Vouchers      | Σ debit = Σ credit at post time; only leaf accounts post; HARD_CLOSED period rejects post.  |
| EMI           | `P·r·(1+r)ⁿ / ((1+r)ⁿ−1)` with explicit day-count; round at schedule-line persistence only. |
| Receipts      | Allocation priority: penal → charges → ovd int → cur int → ovd prin → cur prin.             |
| NPA           | Bucket thresholds per §4.8. Provisioning from `mst_provisioning_rate`.                      |
| GST           | Intra-state CGST+SGST; inter-state IGST; RCM > ₹5,000/day from unregistered.                |
| TDS           | No PAN → 20%; thresholds per section; challan due 7th of next month.                        |
| Depreciation  | SLM or WDV per category; full-month convention if > 15 days in month.                       |
| Payroll       | PF cap ₹15,000; ESI eligibility gross ≤ ₹21,000; gratuity (last·15·years)/26 cap ₹20L.      |
| FD collateral | 25% default haircut; lien-marked; released only on loan closure.                            |
| Maker-checker | Maker ≠ checker on financial / credit / HR / role-grant actions.                            |
| Fiscal year   | April–March IST; HARD_CLOSED posting rejected at service.                                   |
| Audit         | Retain 7 years (financial), 2 years (login). Append-only; integrity hash chain per day.     |

---

## 8. Security, audit & enterprise controls

### 8.1 Authentication

- JWT: access token 15 min, refresh token 7 days. Both carry `sub`, `iat`, `exp`, `type`; refresh carries `jti`.
- Refresh rotation on every refresh: issue a new refresh and revoke the old `jti`. Replay of a revoked `jti` revokes the entire chain (session hijack defense).
- Argon2 password hashing (`passlib[argon2]`). No MD5/SHA1.
- MFA (TOTP via `pyotp`) is mandatory for admin, finance, credit, and treasury roles. Enforced at login.
- Account lockout: 5 failed attempts → 30-minute lock (already in `config.py`).
- Password policy: min length 8 (raise to 12), no password reuse over last 5, 90-day rotation for admins.

### 8.2 Authorization

- Permissions format: `<resource>.<action>`. Examples: `voucher.post`, `voucher.reverse`, `loan_application.approve`, `disbursement.authorize`, `payroll.run`, `user.role.grant`, `pii.view`.
- `RequirePermissions(*perms, require_all=True)` is the only way to gate an endpoint.
- Frontend mirrors via `usePermission(perm)`. Sidebar items, action buttons, and protected routes all consult it. Hiding a button because of a permission still requires server-side enforcement — never trust the client.
- Roles are an abstraction over permissions, not a separate check.

### 8.3 Rate limiting

- `slowapi` middleware on `/auth/*`, `/portal/*`, `/vendor-portal/*`, `/ess/*`.
- Default: 5 req/sec per IP, burst 10. `/auth/login`: 5 req/min per IP + 10 req/hour per account. Hit 429 → exponential back-off.
- Admin endpoints: per-user 100 req/min default; override per endpoint where justified.

### 8.4 Maker-checker

- High-risk actions always flow through `workflow/approvals`: sanction, disbursement authorize, voucher post > ₹X, payroll finalize, OTS, rate reset, rate change, write-off, KYC approve, role grant, large refund/reversal, bank-account change, salary-structure change.
- The maker cannot be the checker (enforced at service layer).
- Delegated authority matrix in `mst_approval_matrix` is table-driven by amount band and action type.
- SLA breach triggers escalation (APScheduler every 15 min).

### 8.5 Audit

- `AuditMiddleware` (`app/middleware/audit.py`) records envelope for POST/PUT/PATCH/DELETE, redacting passwords/tokens.
- Services additionally write to `audit_log` with before/after diff for financial mutations.
- Retention: 7 years financial, 2 years login/access. Older rows move to partitioned cold tables via a nightly job (Stage 5). Daily integrity hash chain makes tampering detectable.
- PII read access (`pii.view` permission gate) is audited with the field name and record ID.

### 8.6 Webhooks

- HMAC (SHA-256) signature in `X-Signature` header; shared secret per integration, Fernet-encrypted at rest.
- Timestamp header `X-Timestamp` with ±5 min window; reject replays.
- Per-payload nonce to prevent replay within the window.
- Dedicated audit log entry on every webhook, including verification result.

### 8.7 Documents & PII

- DMS: content-type allowlist, size cap (50 MB default), AV scan (ClamAV sidecar), versioning with rollback, PUBLIC/PRIVATE/RESTRICTED access, signed-URL delivery for reads, access logs for every read.
- PII fields (PAN, Aadhaar, phone, email, DOB) are masked at the API boundary by default. Unmasked access requires `pii.view` and is audited.

### 8.8 Sessions & cookies

- Access tokens via `Authorization: Bearer` header, not cookies. CSRF is moot for JWT-bearer APIs.
- If cookies are introduced for portal login, they are `Secure; HttpOnly; SameSite=Lax`.
- Logout revokes the refresh token immediately; the access token expires in ≤ 15 min.

### 8.9 Transport & headers

- TLS only in non-dev environments. HSTS `max-age=31536000; includeSubDomains; preload`.
- `Content-Security-Policy` with explicit sources. `X-Frame-Options: DENY`. `X-Content-Type-Options: nosniff`. `Referrer-Policy: strict-origin-when-cross-origin`.
- CORS origins locked to known hosts (current dev set in `config.py`).

---

## 9. UI & design standards

### 9.1 Design tokens

The canonical token set lives in `tailwind.config.cjs`. Every visual decision goes through these tokens — pages may NOT introduce `bg-[#xxx]` or `text-[17px]` literals.

**Colour palette** — each colour has a full 50–900 scale plus a `DEFAULT` shortcut.

| Token       | 50        | 500       | 700       | DEFAULT   | Use                               |
| ----------- | --------- | --------- | --------- | --------- | --------------------------------- |
| `primary`   | `#eff6ff` | `#3b82f6` | `#1d4ed8` | `#2563eb` | Brand / focus ring / primary CTA  |
| `secondary` | `#f8fafc` | `#64748b` | `#334155` | `#475569` | Secondary actions / table borders |
| `success`   | `#ecfdf5` | `#10b981` | `#047857` | `#059669` | Paid, approved, active            |
| `warning`   | `#fffbeb` | `#f59e0b` | `#b45309` | `#d97706` | Overdue, pending action           |
| `danger`    | `#fff1f2` | `#f43f5e` | `#be123c` | `#e11d48` | Rejected, NPA, destructive        |
| `info`      | `#f0f9ff` | `#0ea5e9` | `#0369a1` | `#0284c7` | Informational tips                |
| `neutral`   | `#f8fafc` | `#64748b` | `#334155` | —         | Backgrounds, dividers, body text  |

Semantic surface tokens (also in `tailwind.config.cjs`) — these are what shadcn primitives consume:

| Token              | Value                          | Use                              |
| ------------------ | ------------------------------ | -------------------------------- |
| `background`       | `#ffffff`                      | App body                         |
| `foreground`       | `#0f172a`                      | Default text                     |
| `border` / `input` | `#e2e8f0`                      | Dividers, form controls          |
| `ring`             | `#2563eb`                      | Keyboard-focus ring              |
| `muted`            | `#f1f5f9` (bg), `#64748b` (fg) | Secondary cards, disabled state  |
| `card` / `popover` | `#ffffff` / `#0f172a`          | Surfaces                         |
| `accent`           | `#f1f5f9`                      | Hovered list items               |
| `destructive`      | `#e11d48` / `#ffffff`          | Destructive buttons, error state |

**Typography scale** — tuned for dense financial screens. Line-heights widen slightly at `lg+` so card titles breathe; table body stays tight.

| Token       | Size       | Line-height | Use                                   |
| ----------- | ---------- | ----------- | ------------------------------------- |
| `text-xs`   | 0.75 rem   | 1 rem       | Captions, breadcrumbs, status pills   |
| `text-sm`   | 0.875 rem  | 1.25 rem    | Table body, secondary text, form help |
| `text-base` | 0.9375 rem | 1.5 rem     | Form inputs, primary body             |
| `text-lg`   | 1.0625 rem | 1.625 rem   | Card titles                           |
| `text-xl`   | 1.25 rem   | 1.75 rem    | Section headers (inside cards)        |
| `text-2xl`  | 1.5 rem    | 2 rem       | Page titles (`PageHeader`)            |
| `text-3xl`  | 1.875 rem  | 2.25 rem    | Hero metrics                          |

Font families: `font-sans` = Inter → system fallback; `font-mono` = JetBrains Mono → ui-monospace. Numeric cells additionally use `tabular-nums` (locked-width digits).

**Spacing** — 4 px base. Extensions used for dense layouts:

| Token                 | Value           | Use                                               |
| --------------------- | --------------- | ------------------------------------------------- |
| `p-4.5`               | 18 px           | Half-step between `p-4` (16 px) and `p-5` (20 px) |
| `h-13`                | 52 px           | Table header row                                  |
| `h-15`                | 60 px           | Compact toolbar                                   |
| `h-18`                | 72 px           | Dense list row with actions                       |
| `w-sidebar`           | 256 px          | Default sidebar                                   |
| `w-sidebar-collapsed` | 64 px           | Collapsed sidebar                                 |
| `min-h-row-sm/md/lg`  | 32 / 40 / 48 px | Canonical table-row heights                       |

**Radii** — `rounded-sm` (4 px) for toggles; default `rounded` (6 px); `rounded-md` (8 px) for inputs; `rounded-lg` (12 px) for cards; `rounded-full` for pills and avatars only.

**Shadows** — four tiers only; do NOT invent new ones:

| Token          | Use                                          |
| -------------- | -------------------------------------------- |
| `shadow-sm`    | Tables, row hover                            |
| `shadow`       | Cards, standard surfaces                     |
| `shadow-md`    | Popovers, dropdowns                          |
| `shadow-lg`    | Modals, command palette                      |
| `shadow-focus` | Focus-visible rings (`0 0 0 3px primary/35`) |

**Density anchors** for dense financial tables:

- Numeric column = `text-right tabular-nums`.
- Row height = `min-h-row-md` (40 px) default, `min-h-row-sm` for compact tables, `min-h-row-lg` for tables with multi-line cells.
- Sticky first column via `sticky left-0 bg-background` when the table is wider than the viewport.

**Animation** — `animate-shake` is the ONLY bespoke keyframe, used for form-field error highlights.

**Do NOT**:

- Introduce `bg-[#xxxxxx]` or `text-[17px]` — extend `tailwind.config.cjs` instead.
- Use `shadow-[0_0_10px_red]`-style ad-hoc shadows.
- Hardcode hex codes in components.

Design-token drift is a regression. Contract tests live at `src/components/common/design-tokens.test.tsx` — any common component that stops emitting its canonical class names surfaces there.

### 9.2 Page structure (contract — strict)

Every page in this app is one of three shapes. No alternatives. No "we'll add the shell later."

| Shape             | Required skeleton                                                                                                                                                                            |
| ----------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **List**          | `<div className="space-y-6">` → `<PageHeader ...>` → `<FilterBar>` (if filters exist) → `<Card>` containing `<DataTable>` (with loading skeleton, empty state, error state) → `<Pagination>` |
| **Detail**        | `<div className="space-y-6">` → `<PageHeader ... breadcrumbs={[...]}>` → `<DetailGrid>` (tabs via `<InlineTabs>`) → optional action bar as `<PageHeader actions={...}>`                      |
| **Create / Edit** | `<div className="space-y-6">` → `<PageHeader ... breadcrumbs={[...]}>` → `<FormShell>` (steps via `<WizardShell>` when multi-step) → `<ActionBar>` inside `<FormShell>`                      |

**Every header must be `<PageHeader>`.** You do NOT write `<div className="flex items-center justify-between"><div><h1 ...>Title</h1><p ...>Subtitle</p></div><Button>...</Button></div>`. That shape is the one we migrated _away_ from. The canonical API:

```tsx
<PageHeader
  title="Loan Applications"
  subtitle="Manage loan applications through the origination pipeline"
  breadcrumbs={[
    { label: 'Lending', to: '/admin/lending' },
    { label: 'Applications' },
  ]}
  actions={
    <Button onClick={...}>
      <Plus className="mr-2 h-4 w-4" />
      New Application
    </Button>
  }
/>
```

**Rules:**

1. **No bare `<h1>` on a page.** If you need a title, it goes through `<PageHeader>`. If you need a secondary title inside a card, use `<CardTitle>` (shadcn primitive). Inline `<h1 className="text-2xl font-bold">` / `<h1 className="text-3xl font-bold">` / `<h1 className="text-2xl font-semibold">` is forbidden on pages — contract tests in `src/components/common/design-tokens.test.tsx` pin the `PageHeader`'s `text-2xl` token, so any drift surfaces there.
2. **Back buttons are breadcrumbs.** The old "`<Button variant="ghost" size="icon"><ArrowLeft/></Button>` + `<h1>`" pattern is dead; pass `breadcrumbs={[...]}` instead. The breadcrumb rendered in `<PageHeader>` links back automatically — no separate `<Link>` / `<Button>` for "Back."
3. **Multi-action pages put the group in `actions`.** If there's one button, it's the direct child; if there's a group, wrap it in `<div className="flex gap-2">...</div>` inside the actions slot. Do NOT render an action bar outside `<PageHeader>` at the top of a page.
4. **Action-less pages still use `<PageHeader>`.** You just omit the `actions` prop. Do not skip the component because the page has no button.
5. **Dashboards are a list-page variant.** They use `<PageHeader>` with whatever period/org selectors the page needs in the `actions` slot (see `src/pages/Dashboard.tsx`, `src/pages/lending/LendingDashboard.tsx`, `src/pages/lending/treasury/ALMDashboard.tsx`).
6. **Welcome / avatar pages (portal/ESS/vendor).** Even when the page has a personalized greeting + avatar, the title + subtitle go through `<PageHeader>`. If the layout needs an avatar panel, it sits inline next to the `<PageHeader>` — NOT in place of it.
7. **Deviations require an approved entry in `.stubs-approved.md`** with a named approver and a re-entry criterion. A TODO or comment is not enough.

This rule is enforced by §12.25 (forbidden shortcut) and by the `STAGE-7-page-sweep-*` closure entries in `.stubs-approved.md` that record every page already migrated.

### 9.3 Tables (strict)

**Every tabular data display uses `<DataTable>`.** Using shadcn's `<Table>` primitive directly, or hand-rolling a `<div>`-grid, is forbidden on pages.

**Rules:**

- **Row height**: `min-h-row-md` (40 px) default; `min-h-row-sm` (32 px) for compact tables; `min-h-row-lg` (48 px) for multi-line cells. No ad-hoc pixel heights.
- **Numeric columns**: `text-right tabular-nums` — enforced by `DataTable` column config `align: 'right'`. Currency columns use `<AmountDisplay>` inside the cell, never a raw number + `toFixed(2)`.
- **Dates in cells**: `<DateDisplay>`, never `new Date(x).toLocaleDateString()`.
- **Status in cells**: `<StatusPill>` / `<DpdBadge>` / etc., never a raw `<Badge className="bg-green-100">Active</Badge>`.
- **Headers**: sortable columns render a chevron affordance via `DataTable`; filtering is in `<FilterBar>` placed ABOVE the table card, never inline in the table.
- **Truncation**: long text uses the `truncate` Tailwind class + hover tooltip showing the full value. Silent clipping (overflow-hidden without a tooltip) is a defect.
- **Sticky first column**: mandatory for tables wider than the viewport, so the row identifier stays visible on horizontal scroll.
- **Column chooser**: `<ColumnChooser>` on every list page with ≥ 6 columns, wired through `DataTable`'s `columnVisibility` API.
- **Export**: `<ExportMenu>` (PDF/Excel/CSV) on every list page that shows business data. Wired through the hooks in `src/utils/exportUtils.ts` (now exceljs-backed per STAGE-8-003).
- **Empty/loading/error states are owned by `<DataTable>`** — don't add your own. Pass `data`, `isLoading`, `isError`, `error`, `onRetry`, and an optional `emptyCta`; the table handles the rest.
- **Row actions**: a `<DropdownMenu>` on the last column via `DataTable`'s `rowActions` prop. Destructive entries (Delete, Reverse) open a `<ConfirmDialog>`.
- **Selection**: row-level checkboxes are opt-in via `DataTable`'s `selectable` prop. Pages do not render their own checkbox column.
- **Pagination**: every list has `<Pagination>` rendered by `DataTable`'s `pagination` prop. Default page size 50, max 200 (matches backend §6.5).

### 9.4 Dense financial screens

GL posting, payroll review, receipts allocation, disbursement breakdown — these must fit 1440×900 without horizontal scroll by default. Use `<SideSheet>` for supporting detail and `<InlineTabs>` for secondary categories.

### 9.5 Mutating buttons (strict)

Every mutating button — submit, create, approve, reject, post, reverse, delete, disburse, allocate — follows this contract:

- **Loading state while pending**: `disabled={mutation.isPending}` + inline `<Loader2 className="mr-2 h-4 w-4 animate-spin"/>` appearing in place of the leading icon. Never swap the button out for text "Saving..." — the button stays clickable-looking but is disabled.
- **Double-submission guard**: `disabled` alone is not enough; the backend endpoint MUST carry an `Idempotency-Key` header (§6.3). If a mutation hits the network without one, it's a defect.
- **Success**: `toast.success(msg)` with a 3-second auto-dismiss; list invalidated via `queryClient.invalidateQueries`.
- **Failure**: `toast.error(err.message)` with a `Details` affordance. The Details popover shows `error_code`, `correlation_id`, and any `details` from the `AppException` envelope. Support engineers need these to trace production incidents.
- **Destructive actions** (`Delete`, `Reverse`, `Write-off`, `Terminate`, `Reject with penalty`, `Revoke session`): `<ConfirmDialog>` with a **typed confirmation** — the user types the entity's business number or name before the primary button activates. Applies unconditionally for write-offs, deletes, reversals > ₹1L, and any maker-checker-protected action.
- **Maker-checker actions** (`Approve`, `Reject`): separate maker and checker buttons, visible to different users per `usePermission`. Calling `ensure_maker_is_not_checker` is a backend-side invariant (§8.4); the frontend still double-checks by hiding the "Approve" button if `current_user.id === record.maker_id`.
- **Permission-gated**: wrap in `<PermissionGate permission="voucher.post" />` so users without the permission don't see a button they can't use. (Server-side enforcement is still required — clients are untrusted.)
- **Icons lead the label**: `<Plus/>`, `<Save/>`, `<Trash/>`, `<Check/>`, `<X/>` from lucide, sized `h-4 w-4`, with `mr-2`. Never render a button with only an icon for a textual action; icon-only buttons are reserved for `ghost size="icon"` row affordances (sort, column toggle).

### 9.6 Responsiveness

- Desktop-first; tested at 1920, 1440, 1280, 1024 widths.
- Portal/ESS tablet-portrait (768) supported; mobile (375) supported for ESS self-service flows only (check-in, leave request, payslip view).
- No horizontal scroll at tested widths.

### 9.7 Accessibility

- Focus visible site-wide.
- AA contrast.
- Keyboard path exists for every action.
- `axe-core` runs in Playwright; critical and serious violations fail the build.

### 9.8 Illustrations, empty states, error states

- One consistent illustration system (lucide icons sized 48 px on neutral background). No stock/marketing images.
- `<EmptyState>` has `title`, `subtitle`, optional primary CTA.
- `<ErrorState>` has a short human message and a `Retry` button that refetches.

---

## 10. Test strategy

Testing is part of the change, not a chore that follows it. Every fix ships with a test that would have caught it.

### 10.0 Full-stack parity rule (non-negotiable)

**No change ships on only one side of the stack.** Every user-facing feature, bug fix, or refactor must land with coverage on _every layer it actually touches_:

1. Backend unit (pytest) — service math / pure helpers.
2. Backend integration (pytest + testcontainers Postgres) — endpoint → service → repo → DB, with auth + permission + RLS exercised.
3. Frontend unit (Vitest + Testing Library) — hooks, schemas, branching components.
4. Frontend integration (Vitest + MSW) — the hook/page wired against a mocked backend for the happy path + one error path.
5. Playwright E2E — the real flow (backend running, DB seeded, browser driving the UI) whenever the change is reachable via a user journey.

A PR that adds a backend endpoint without the matching frontend hook + page + Playwright flow is incomplete. A PR that adds a page without the backend endpoint + integration test is incomplete. A PR that fixes a bug on one side without a regression test on both sides is incomplete. If a layer genuinely doesn't apply (e.g. an internal cron job has no UI), say so explicitly in the PR description — silence is not acceptance.

**What this rule forbids:**

- Merging a backend feature and "opening a follow-up PR" for the frontend, or vice versa.
- Shipping a page that calls a backend route which doesn't exist yet.
- Closing a stage gate when only half the stack is done.
- Counting Playwright coverage as optional — it is the only layer that proves the wires connect end-to-end.

The §10.7 evidence block and §13 Definition of Done both enforce this rule.

### 10.1 Frontend unit tests (Vitest + Testing Library + jsdom)

- Scope: `src/lib`, `src/hooks`, `src/schemas`, `src/components/common`, branching logic in `src/components/<domain>`.
- Target: ≥ 80% line coverage on the above. `src/lib` and `src/schemas` aim for 100%.
- File convention: `Component.tsx` → `Component.test.tsx` colocated.
- Config: `vite.config.ts` includes a `test` block (Vitest). Setup file `src/test/setup.ts` configures `@testing-library/jest-dom`.

### 10.2 Frontend integration tests (Vitest + MSW)

- MSW intercepts axios; tests exercise hook → component → UI interaction → assertion.
- One happy-path + one error-path test per major hook.
- Covers list → create → edit → delete for every major module (lending applications, loan accounts, vouchers, purchase bills, sales invoices, payments, payroll batches, leave applications, fixed-asset lifecycle, GST returns, TDS challans, BRS matching).

### 10.3 Backend unit tests (pytest + pytest-asyncio)

- Scope: service-layer math with zero or minimal I/O.
- **Golden-file fixtures** under `backend/tests/fixtures/<module>/*.yaml` encode the spec. Tests deserialize, call the service, compare outputs. Regression-safe.
- Target: ≥ 85% on `app/services/lending`, `app/services/finance`, `app/services/gst`, `app/services/tds`, `app/services/payroll`, `app/services/fixed_assets`.

### 10.4 Backend integration tests (pytest + testcontainers-python Postgres)

- Ephemeral Postgres per test session; alembic migrates on setup. SQLite is kept only for pure-math unit tests; it masks enum/JSONB/RLS behavior and is not acceptable for integration coverage.
- Cover every `/api/v1/*` prefix with at least: happy path, one validation failure, one permission failure.
- `factory-boy` for model factories. `conftest.py` provides `test_user`, `test_org`, `authenticated_client` fixtures.

### 10.5 E2E tests (Playwright)

- `playwright.config.ts`: chromium + one tablet viewport (768×1024); retries = 2 on CI; `trace: 'on-first-retry'`; video on failure.
- Fixtures:
  - `auth.ts` — logged-in session (seeds admin + MFA-verified state).
  - `console-gate.ts` — fails the test on uncaught `console.error`, any 4xx/5xx response not explicitly expected, or any request timeout.
- Required cross-module flows (must stay green on `main`):
  1. Auth + MFA: login → MFA → dashboard → logout → refresh-token rotation.
  2. Masters → roles → permissions → user gating.
  3. **Loan lifecycle**: entity create → KYC → application → appraisal → sanction → disbursement → EMI demand → receipt allocation → NPA trigger at DPD 91 → OTS with haircut approval → legal case open → write-off.
  4. Procurement / AP: vendor → purchase bill → TDS deduction → payment → BRS match → GL trace.
  5. AR / Sales: customer → invoice with GST split → receipt → aging → bank recon.
  6. HRIS / Payroll: employee → attendance → leave → payroll batch → payslip → PF/ESI/PT/TDS verification.
  7. Fixed assets: acquire → capitalize → depreciate month-close → impair → dispose → GL trace.
  8. GST returns: GSTR-1 draft → reconcile vs GSTR-2B → lock → file (mock portal).
  9. Borrower portal: login → statement → prepayment request → NOC request.
  10. Audit trail: fetch a 7-year-old voucher, confirm before/after diff visible, confirm `correlation_id` and `user_id` present.

### 10.6 Coverage gates

- Unit + integration: 60% minimum on touched files initially; ratchet to 80% by Stage 8 of the roadmap.
- Critical services (§4.8, §4.11, §4.3, §4.5, §4.6): **85%** floor; PRs that reduce coverage here are blocked.

### 10.7 Test evidence on every PR

Every PR description includes:

```
Frontend unit:         <pass>/<total>
Frontend integration:  <pass>/<total>
E2E:                   <pass>/<total>
Backend:               <pass>/<total>  coverage: <pct>%
Console errors:        0
Failed network reqs:   0 (non-asserted)
```

"Looks good" is not evidence.

### 10.8 Regression contract

- Every bug fix ships with a **failing-then-passing** test committed in the same PR.
- If the failing test must temporarily be `.skip`, there is a follow-up ticket and an expiry date. Expired skips fail CI.

---

## 11. Bug-fix protocol (zero-shortcut, 7 steps)

1. **Reproduce** — write a failing test (unit or integration) against `main` **before** touching source. Attach the command and output in the PR.
2. **Root-cause** — trace to origin. Do not stop at the first symptom. Capture hypothesis + disproof in the PR description. If the true cause is a shared abstraction, say so.
3. **Scope** — fix the root pattern, not just the reported instance. If three pages share the bug, fix the shared component. If the service mis-rounds, fix the service — do not patch callers.
4. **Contract first** — if the defect is caused by API shape drift, naming drift, pagination drift, or DTO mismatch, fix the canonical API/schema/service contract and generated or shared TypeScript types. Frontend-facing APIs must use the §3.3.1 Pydantic alias contract: Python fields are `snake_case`, JSON emitted to React is `camelCase` through `CamelSchema` + `response_model_by_alias=True`. Pages/components must not contain compatibility fallbacks such as `snake_case ?? camelCase`, `array ? array : data.items`, duplicated optional DTO aliases, or silent response-shape normalizers.
5. **Fix** — surgical change. No unrelated refactors unless the fix materially requires them (document why).
6. **Prove** — the test from step 1 passes; add adjacent regression tests that cover the neighborhood.
7. **Audit** — if the bug touched money, tax, lending state, permissions, or audit, add/run the affected E2E and record a §10.7 evidence block.
8. **Document** — changelog entry. If standards changed, update this AGENTS.md in the same PR.

**Defects explicitly in scope** (not "preferences"):

- Console errors or warnings on production paths.
- Failed network requests in core flows (unless explicitly expected and asserted).
- Broken layouts, clipped text, overlapping elements, non-functional filters.
- Missing loading / empty / error states.
- Mock data in shipped paths.
- `any` types, `@ts-ignore`, suppressed lint.
- Unvalidated forms (no zod, or zod without coverage).
- Missing permission checks, unaudited mutations, unparameterized SQL.
- Hard-coded organization IDs, rates, or dates.
- Unhandled promise rejections.
- Pages that bypass the shell components in §9.2.

---

## 12. Forbidden shortcuts

Under no circumstance, in any PR, may the following occur without a documented decision that updates this file in the same PR:

1. Suppressing TypeScript, ESLint, Ruff, MyPy, or test errors (`@ts-ignore`, `eslint-disable`, `# type: ignore`, `# noqa`, `xfail`, `skip` without an expiry) without a documented root-cause fix.
2. Weakening a zod schema, Pydantic constraint, DB check constraint, or permission scope to make a test pass.
3. **Leaving a stub, TODO, FIXME, `throw new Error('not implemented')`, mock return, placeholder onClick, empty service method, or "to be wired later" shim in shipped code without explicit written approval from the repo owner.** See §12.2 for the approval protocol. "Follow-up PR" is NOT approval; the approver must be named and the deferral recorded in `.stubs-approved.md`.
4. Converting a real defect into a TODO/FIXME/"future improvement" when a ≤ 1-day fix exists.
5. Adding `any`, casting through `unknown`, or using `Object`/`Record<string, any>` as an escape hatch.
6. Hard-coding organization IDs, user IDs, tax/interest/provision rates, or dates outside of seed fixtures and test factories.
7. Shipping mock data on a production page. If the API is not ready, either wire it, or feature-flag the page off AND label it `@status: incomplete` in the route module AND list it under `.stubs-approved.md`.
8. Calling `axios` directly from a page or component — always through a hook (§5.4).
9. Building inline UI primitives in a page — always via a component (§5.1).
10. Committing `.env`, credentials, portal passwords, signed certs, private keys, or DB dumps.
11. Skipping git hooks (`--no-verify`), amending already-pushed commits, or force-pushing `main`/shared branches.
12. Marking a ticket **Done** without §10.7 test evidence.
13. Interpolating untrusted values into raw SQL (`text(f"...")`); use parameter bindings.
14. Catching broad `Exception` without re-raising a typed `AppException`.
15. Introducing a second data-fetching library, a second state manager, or a second test runner.
16. Using `npm` or `yarn` in this repo.
17. Disabling RLS (`get_db_with_tenant`) for convenience on an authenticated route.
18. Posting to a HARD_CLOSED period, or bypassing maker-checker on a high-risk action.
19. Storing PII unmasked in logs, analytics, or error reports.
20. Adding a third-party dependency without a weekly-ish audit of its transitive tree (`pnpm why`, `pip-audit`).
21. Replacing a failing CI job with a fresh green one by deleting the failing test.
22. Deferring the completion of a stage gate in the roadmap without writing the deferral into `.stubs-approved.md` with an explicit named approver and a re-entry criterion.
23. Shipping a backend change without the matching frontend change (or vice versa). See §10.0 — every change must cover backend unit + integration AND frontend unit + MSW integration AND Playwright E2E for any layer it actually touches. Half-stack PRs are forbidden.
24. **Putting a tenant-owned secret (client's Razorpay key, NBFC's GSTN password, NBFC's bureau API key, per-NBFC bank corporate ID, per-tenant SMS sender credentials, etc.) in `.env` / `settings.py` / any platform config file.** This is a SaaS — tenant secrets belong in Fernet-encrypted DB settings keyed by `organization_id`, fetched at runtime through a service. Only platform secrets (our JWT key, our DB URL, our Redis URL, our encryption key) may live in env. See §6.8 and §1. A platform env var with a client's name or account in it is always wrong.
25. **Shipping a page that violates §5.1 / §5.3 / §5.7 / §9.2 / §9.3 / §9.5 strict contracts.** Specifically: any of the following in a committed page file is a defect.
    - Hand-rolled page header `<div>` (use `<PageHeader>`).
    - Inline `<h1 className="text-2xl font-bold">` or `text-3xl` page title (use `<PageHeader title=...>`).
    - Back button as a separate `<Button>` (use `<PageHeader breadcrumbs=...>`).
    - Raw `<table>` or shadcn `<Table>` directly in a page (use `<DataTable>`).
    - Raw `<form>` with `<Input>`/`<Select>` outside `<FormField>` (use `<FormShell>` + RHF + zod via shadcn `<Form>`).
    - Inline loading spinner for page-level loading (use `<SkeletonTable>` / `<Skeleton>`).
    - Inline "No results" text (use `<EmptyState>`).
    - Inline `<span>{amount.toFixed(2)}</span>` for money (use `<AmountDisplay>`).
    - Inline `<span>{new Date(x).toLocaleDateString()}</span>` (use `<DateDisplay>`).
    - Inline `<Badge className="bg-green-100 text-green-800">` for status (use `<StatusPill>` / `<DpdBadge>` / etc.).
    - Raw PAN / Aadhaar / phone / email / bank-account / IFSC values in JSX (use `<PANField>` / `<AadhaarField>` / `<PhoneField>` / etc., masked by default; unmask requires `pii.view` + audit).
    - Hex literal in Tailwind (`bg-[#1e40af]`, `text-[#475569]`) — use named tokens from `tailwind.config.cjs` §9.1.
    - Pixel literal sizing (`h-[37px]`, `w-[248px]`, `text-[17px]`) — use spacing/height/text tokens from §9.1.
    - Console.log / console.error anywhere in `src/**/*.tsx` (use `logger` from `src/lib/logger.ts`). This is enforced by ESLint `no-console`.

    These rules are pinned by design-token contract tests at `src/components/common/design-tokens.test.tsx` (which fail CI if `<PageHeader>` / `<DataTable>` / `<FormShell>` / `<EmptyState>` / `<ErrorState>` stop emitting their canonical tokens) and by the accumulated `STAGE-7-page-sweep-batch-*` closure entries in `.stubs-approved.md` that record every migrated page. An exemption requires a named approver in `.stubs-approved.md` with a re-entry criterion — same protocol as §12.2 stubs.

26. **Fixing API contract drift inside pages/components.** If a backend endpoint returns camelCase, snake_case, paginated, or non-paginated data inconsistently, the fix belongs in the backend schema, service wrapper, shared DTO, or generated type. Page-level compatibility code is forbidden, including `field_a ?? fieldA`, `id ?? entity_id`, `Array.isArray(data) ? data : data.items`, duplicated optional aliases in local interfaces, or "normalize in the component" helpers. A page consumes exactly one documented contract.

27. **Shipping loan-only ERP navigation or integration-mandatory workflows.** The product scope is the full ERP module set. Do not hide accounting, GST, TDS, AP/AR, HRIS, payroll, fixed assets, fixed deposits, compliance, BI, DMS, portals, inventory, workflow, or treasury modules merely because the current implementation focus was lending. Do not make an external integration mandatory for a business process that can be completed manually. If an integration is not released, the manual path must remain complete, tested, and visible.

### 12.2 Stub / TODO / deferral approval protocol (strict)

This project does **not** accumulate technical debt quietly. Every stub that lives in the codebase is accountable and visible.

**Before committing code that contains any of the following**, the author must have written approval from the repo owner recorded in `.stubs-approved.md` at the repo root:

- A `TODO`, `FIXME`, `XXX`, `HACK`, or `@status: incomplete` marker.
- A function that `throw`s "not implemented" or returns placeholder/mock data.
- A service stub that returns `None`/`{}`/`[]` where real logic is expected.
- A re-export shim that says "real implementation lives elsewhere / will move later".
- An empty onClick/handler (`() => {}`) on a rendered button or interactive element.
- A feature-flagged-off page that would otherwise ship incomplete.
- A deferred roadmap stage or sub-task (e.g. "Stage 2i deferred to follow-up").
- A commented-out block left in for "future reference".

**Every entry in `.stubs-approved.md`** must include:

1. A precise file path and line number (or a glob if a pattern).
2. What the stub represents and why it cannot be completed now.
3. The named approver (e.g. "Approved by: @balakrishna on 2026-04-23").
4. The **re-entry criterion** — the concrete event/ticket/stage that will unblock it.
5. An expiry date after which the stub is auto-reopened as a P1 defect.

Pull requests that add new stubs without a matching `.stubs-approved.md` entry **fail CI** (a repo lint job greps for `TODO|FIXME|XXX|HACK|not implemented` in diffed lines and cross-checks against the approved list).

Corollary: the historical list in §12.1 is not a license — it is a snapshot of what was approved when AGENTS.md first landed. Each entry there has migrated to `.stubs-approved.md` with an owner and re-entry criterion. If an item is open, it is because deferral was recorded; otherwise it has been closed.

### 12.3 Known current violations — state tracker

Snapshot of §12.1 items after each stage. "Closed" means no live instance remains in the codebase. "Open (approved)" means it lives in `.stubs-approved.md` with an owner and an unblocker.

| Violation                                                                                                     | Spec ref            | Status                 | Closed in           | Notes                                                                                                                                                                                                                                                                                                                |
| ------------------------------------------------------------------------------------------------------------- | ------------------- | ---------------------- | ------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| RLS f-string interpolation in `backend/app/database.py:92`                                                    | §6.2 / §12.13       | **Closed**             | Stage 1a            | Now `SELECT set_config('app.current_org_id', :org_id, true)` + `UUID()` validation. Regression tests in `backend/tests/common/test_rls_context.py`.                                                                                                                                                                  |
| Plaintext portal passwords in `gst_registration_service.py`                                                   | §6.8                | **Closed**             | Stage 1b            | Fernet-encrypted via existing `app.core.encryption`. Regression tests in `backend/tests/gst/test_gst_password_encryption.py`.                                                                                                                                                                                        |
| `AuthContext` stub (hardcoded admin)                                                                          | §5.6                | **Closed**             | Stage 2b            | Real login/logout/refresh wired; Zustand `authStore` + `organizationStore` + `useAuth`/`usePermission`/`useOrganization` hooks.                                                                                                                                                                                      |
| `tsconfig.json` not strict                                                                                    | §5.9                | **Closed**             | Stage 1d            | `strict: true`, `noFallthroughCasesInSwitch`, `noImplicitOverride`. All 39 cascading errors fixed.                                                                                                                                                                                                                   |
| `// TODO: Get organization_id` in `src/pages/fixed-deposits/**`                                               | §3.4                | **Closed**             | Stage 2f            | Uses `useRequiredActiveOrganizationId()`.                                                                                                                                                                                                                                                                            |
| Mock accounts/periods in `GLPostingCreate.tsx`                                                                | §12.7               | **Closed**             | Stage 2g            | Wired to `useAccounts()`/`usePeriods()` react-query hooks; uses `<PageHeader>`/`<FormShell>`; zod cross-field invariants.                                                                                                                                                                                            |
| `console.log` in `src/pages/**/*.tsx`                                                                         | §5.12               | **Closed**             | Stage 1c            | Replaced across 28 pages with `logger.debug`; ESLint `no-console` blocks regression.                                                                                                                                                                                                                                 |
| Duplicate lockfiles                                                                                           | §2.2                | **Closed**             | Stage 0             | Only `pnpm-lock.yaml` remains; `packageManager: pnpm@9.15.0` enforced.                                                                                                                                                                                                                                               |
| `console.log` stub `onClick` handlers in lending/legal/npa/nach/borrowings                                    | §12.3               | **Closed**             | Stage 3a            | Replaced with real handlers where the API exists; approved deferrals logged in `.stubs-approved.md`.                                                                                                                                                                                                                 |
| `customer_id: ''` with TODO in `FDForm.tsx`                                                                   | §5.1                | **Closed**             | Stage 3a            | `<CustomerPicker>` component built; form uses it.                                                                                                                                                                                                                                                                    |
| `src/components/common/*` re-export shims (AmountInput, DateDisplay, StatusPill, DpdBadge, PercentageDisplay) | §5.2                | **Closed**             | Stage 3a            | Implementations moved to `common/`; lending/ now re-exports for compat.                                                                                                                                                                                                                                              |
| `App.tsx` 1,127-line monolith                                                                                 | §5.10               | **Closed**             | Stage 3b            | Converted all page imports to `React.lazy` with `<Suspense>` wrapper; bundle split into ~30 chunks; initial chunk dropped from 5.2 MB to ~2 MB.                                                                                                                                                                      |
| Receipt allocation per-installment priority (AGENTS.md §4.8 violation)                                        | §4.8                | **Closed**             | Stage 4-PENDING-001 | Rewrote `LoanAccountService.allocate_receipt` to three-pass cross-installment allocation (penal → interest → principal). 7 regression tests.                                                                                                                                                                         |
| Missing closed-period guard in `gl_posting_service.post_from_source`                                          | §4.3                | **Closed**             | Stage 4-PENDING-003 | `session.get(FinancialPeriod, period_id)` + guard that raises `ClosedPeriodError` on `is_closed` or `is_locked`. 4 new tests.                                                                                                                                                                                        |
| Missing security response headers (CSP/HSTS/X-Frame-Options/nosniff/Referrer-Policy/Permissions-Policy)       | §8.9                | **Closed**             | Stage 5-001         | `SecurityHeadersMiddleware`; HSTS only on prod+https; Server header stripped; routes may override CSP. 6 tests.                                                                                                                                                                                                      |
| No rate limiting on `/auth/*`                                                                                 | §8.3                | **Closed**             | Stage 5-002         | slowapi wired; `@auth_login_limit()` 5/min, `@auth_refresh_limit()` 20/min. 429 envelope with `error_code`+`retry_after_seconds`. 5 tests.                                                                                                                                                                           |
| No HMAC webhook verification primitive                                                                        | §8.6                | **Closed (primitive)** | Stage 5-003         | `verify_webhook()` + `compute_hmac_sha256()` + `verify_timestamp()` in `app/core/webhook_signature.py`. 17 tests. Per-vendor wiring = STAGE-5-PENDING-005.                                                                                                                                                           |
| No PII masking helpers                                                                                        | §8.7                | **Closed (primitive)** | Stage 5-004         | 6 mask functions + `MaskedPIIModel` Pydantic mixin. 24 tests. Rollout to response schemas = STAGE-5-PENDING-006.                                                                                                                                                                                                     |
| No DMS upload hardening                                                                                       | §8.7                | **Closed (primitive)** | Stage 5-005         | `validate_upload()` with allowlist, ALWAYS_DENY, magic-byte mismatch detection, 50 MB cap, path-traversal-safe filenames. 23 tests. ClamAV = STAGE-5-PENDING-001.                                                                                                                                                    |
| No audit tamper-detection                                                                                     | §8.5                | **Closed (primitive)** | Stage 5-006         | `compute_day_anchor()` / `build_chain()` / `verify_chain()` — canonical row form + chain propagation. 16 tests. Persistence = STAGE-5-PENDING-002.                                                                                                                                                                   |
| No Arq worker / fan-out queue (§6.6)                                                                          | §6.6                | **Closed (scaffold)**  | Stage 6-001         | `app/workers/arq_worker.py` with 7 registered jobs, `WorkerSettings`, `enqueue()` producer wrapper with dedupe + defer. 14 tests. Worker-pool deploy = STAGE-6-PENDING-arq-worker-pool.                                                                                                                              |
| No integration base client with retry / circuit breaker                                                       | §6.7                | **Closed**             | Stage 6-002         | `app/integrations/base/client.py` — httpx + exponential-backoff retry + 3-state circuit breaker + typed errors. 18 tests. Per-vendor subclasses deferred (one STAGE-6-PENDING-\* per vendor).                                                                                                                        |
| No feature-flag gating for integrations (§6.7)                                                                | §6.7                | **Closed**             | Stage 6-003         | `app/core/feature_flags.py` — 22 flags, per-env defaults, override via `FEATURE_FLAG_<NAME>` env var, `snapshot()` for admin introspection. 17 tests.                                                                                                                                                                |
| No OpenTelemetry instrumentation                                                                              | §6                  | **Closed**             | Stage 6-004         | `app/core/telemetry.py` wires FastAPI + httpx + SQLAlchemy; exporter reads `OTEL_EXPORTER_OTLP_ENDPOINT`. No-op when unset. 9 tests. Dashboards + alerting = STAGE-6-PENDING-grafana-dashboards / -alerting-rules.                                                                                                   |
| Bare-default `tailwind.config.cjs` — no NBFC palette / typography scale / density anchors                     | §9.1                | **Closed**             | Stage 7-001         | Full palette (primary/secondary/success/warning/danger/info/neutral with 50–900 scales), semantic surface tokens, 7-step typography scale, density anchors (row heights, sidebar widths), 4-tier shadow system. Token tables documented in §9.1.                                                                     |
| No Playwright accessibility checks                                                                            | §5.11 / §10.5       | **Closed**             | Stage 7-002         | `@axe-core/playwright` fixture at `playwright/fixtures/axe.ts`. `runAxe(page)` fails the test on critical/serious violations; WCAG 2.1 AA tags by default. Login smoke now carries an axe assertion. Per-suppression must be logged in `.stubs-approved.md`.                                                         |
| No visual regression coverage                                                                                 | §9                  | **Closed (scaffold)**  | Stage 7-003         | `playwright.config.ts` visual-regression block (`maxDiffPixelRatio: 0.002`, animations disabled). Sample visual spec + `pnpm test:e2e:visual:update` command. Baseline capture across 10 critical screens = STAGE-7-PENDING-visual-baselines.                                                                        |
| No design-token contract tests for common components                                                          | §9                  | **Closed**             | Stage 7-004         | 11 contract tests at `src/components/common/design-tokens.test.tsx` — `PageHeader`/`FormShell`/`FormSection`/`EmptyState`/`ErrorState`/`DataTable` canonical classes (text-2xl, text-muted-foreground, tabular-nums, border-destructive, etc.). Future refactor cannot drift silently.                               |
| No production-readiness report                                                                                | §Appendix A Stage 8 | **Closed**             | Stage 8-001         | [`PRODUCTION_READINESS_REPORT.md`](PRODUCTION_READINESS_REPORT.md) — honest state, full evidence, risk list, go-live checklist, approval block.                                                                                                                                                                      |
| No dependency vulnerability audit in CI                                                                       | §12.20              | **Closed**             | Stage 8-002 / 8-003 | `pnpm audit --prod`: 0 critical, 0 high (down from 2 high in `xlsx`). `xlsx` removed and `exceljs` swapped in — STAGE-8-003 closure. 1 remaining moderate is `uuid` transitive via `exceljs` with no exploitable path. `pip-audit` on backend reports zero known vulnerabilities.                                    |
| `xlsx` package carrying 2 unfixable high-sev advisories (prototype pollution + ReDoS)                         | §12.20              | **Closed**             | Stage 8-003         | `src/utils/exportUtils.ts` now uses `exceljs` exclusively. Export functions became `async` — 6 call-sites use fire-and-forget `onClick` so no functional change. `pnpm build` verified; bundle swapped in the new `vendor-excel` chunk.                                                                              |
| Bundle size — initial chunk 2.0 MB raw (498 kB gzip)                                                          | §Appendix A Stage 8 | **Closed**             | Stage 8-004         | `vite.config.ts` `rollupOptions.output.manualChunks` splits vendor libs; main entry 2.0 MB → 1.0 MB raw (498 kB → 179 kB gzip). Named vendor chunks: `vendor-react`, `vendor-router`, `vendor-state`, `vendor-radix`, `vendor-forms`, `vendor-charts`, `vendor-pdf`, `vendor-excel`, `vendor-icons`, `vendor-other`. |
| No unified SMS/email/push abstraction                                                                         | §6 / §10.5          | **Closed**             | Stage 6-005         | `app/services/notification/communication_service.py` — `Channel` enum + `Recipient.target_for` + provider registry + per-channel live/mock/off feature flags + fail-closed `send`/`fanout`. 9 tests. Closes STAGE-6-PENDING-communication-service.                                                                   |
| `gstn_service.py` mock returns (5+ TODOs)                                                                     | §12.7               | **Open (approved)**    | —                   | Stage 6 scope; tracked as STAGE-6-PENDING-gstn-live (`gstn_live` feature flag).                                                                                                                                                                                                                                      |
| `kyc_service.py` CKYC/bureau stubs                                                                            | §12.7               | **Open (approved)**    | —                   | Stage 6 scope; CKYC + bureau integration. Tracked in `.stubs-approved.md`.                                                                                                                                                                                                                                           |
| ~55 other backend TODO/FIXME from exploration inventory                                                       | various             | **Open (approved)**    | —                   | Each tracked in `.stubs-approved.md` with the Stage that will close it.                                                                                                                                                                                                                                              |

---

## 13. Definition of Done (per ticket)

A ticket is Done only when **all** of the following are true:

- [ ] All acceptance criteria met.
- [ ] Full-stack parity (§10.0): backend unit + backend integration + frontend unit + MSW integration + Playwright E2E all present for every layer the change actually touches. Layers genuinely N/A must be named explicitly in the PR description.
- [ ] `pnpm lint && pnpm typecheck && pnpm format:check` clean.
- [ ] `cd backend && ruff check . && mypy app && black --check .` clean.
- [ ] No new `console.error`, no new failed network requests in the touched flow.
- [ ] Permissions enforced on every new mutation; audit rows present for financial mutations.
- [ ] Idempotency key wired on every new financial mutation endpoint.
- [ ] If a standard, runbook, or module inventory shifted, this AGENTS.md is updated in the same PR.
- [ ] Screenshot or Playwright trace attached for UI changes.
- [ ] §10.7 evidence block in the PR description.

For UI changes specifically, also:

- [ ] `<PageHeader>` / `<DataTable>` / `<FormShell>` used; no inline primitives.
- [ ] Loading / empty / error states render on cold start.
- [ ] Tested at 1440 and 1024 widths (plus 768 for portal/ESS).
- [ ] `axe` clean (no critical / serious violations).

For backend changes specifically, also:

- [ ] Transaction boundary explicit; no implicit commits.
- [ ] Optimistic locking `version` respected for mutations.
- [ ] `get_db_with_tenant` used on any authenticated route.
- [ ] No `text(f"...")`; parameter bindings only.

---

## 14. Runbook

### 14.1 Local bringup (first time)

```bash
# Prereqs: Node 20, pnpm, Python 3.11, Docker, Docker Compose.
docker compose up -d db redis
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python -m app.db.seeds.init   # seeds reference data + admin
cd ..
pnpm install
```

### 14.2 Everyday dev

```bash
# One shot:
./start.sh            # checks PG/Redis, brings up backend + frontend

# Or separately:
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --port 8001
pnpm dev              # http://localhost:5176
```

### 14.3 Tests

```bash
pnpm test                    # unit (Vitest)
pnpm test:watch
pnpm test:integration        # MSW-backed flows
pnpm test:coverage
pnpm test:e2e                # Playwright
pnpm test:e2e:ui             # Playwright UI
pnpm test:e2e -- --grep axe  # accessibility-only

cd backend
pytest -q
pytest --cov=app --cov-report=term-missing
pytest backend/tests/services/lending -q
```

### 14.4 Lint / typecheck / format

```bash
pnpm lint
pnpm typecheck
pnpm format:check

cd backend
ruff check .
ruff format .
mypy app
black --check .
```

### 14.5 Build

```bash
pnpm build
docker compose build
```

### 14.6 Migrations

```bash
cd backend
alembic revision --autogenerate -m "describe change"
# REVIEW the generated file — autogenerate misses enum + default changes
alembic upgrade head
alembic downgrade -1   # local rollback test only
```

Production migrations are applied in a separate release step with a DBA-approved plan. Never edit past migration files. Breaking migrations (column type change, not-null add) ship with a data-migration script + a feature-flagged code rollout.

### 14.7 Troubleshooting

| Symptom                                    | First thing to check                                                         |
| ------------------------------------------ | ---------------------------------------------------------------------------- |
| 401 loop in browser                        | `AuthContext` wired? `VITE_API_URL` correct? `access_token` stored?          |
| RLS empty results                          | `get_db_with_tenant` on the route? JWT `organization_id` claim present?      |
| Voucher rejected                           | Period status? Account is a leaf? Σdebit = Σcredit?                          |
| NPA not classifying                        | `run_npa_classification` job scheduled? DPD computed per `schedule_service`? |
| GSTN call returns mock                     | Feature flag off; check `services/gst/gstn_service.py` stubs (§12.1).        |
| CORS errors                                | Origin in `settings.CORS_ORIGINS`? Preflight returns 204?                    |
| Test DB out of sync                        | `alembic upgrade head` inside test fixture? testcontainers reused image?     |
| Console.error in Playwright                | Offending page name; console-gate fixture dumps the stack.                   |
| `docker compose` backend healthcheck fails | `pg_isready` on `db`? Migrations applied? Port 8000 free?                    |

---

## 15. Ownership matrix

Fill in as people and module owners stabilize. Every module has three named owners: a tech lead, a QA owner, and a compliance reviewer.

| Module                            | Tech Lead | QA Owner | Compliance Reviewer |
| --------------------------------- | --------- | -------- | ------------------- |
| Auth / Users / Roles              | TBD       | TBD      | TBD                 |
| Masters / Organization            | TBD       | TBD      | TBD                 |
| Finance · GL · Vouchers           | TBD       | TBD      | TBD                 |
| AP/AR · BRS                       | TBD       | TBD      | TBD                 |
| GST                               | TBD       | TBD      | TBD                 |
| TDS                               | TBD       | TBD      | TBD                 |
| Lending — LOS                     | TBD       | TBD      | TBD                 |
| Lending — LMS / NPA / Legal       | TBD       | TBD      | TBD                 |
| Treasury / ALM / Risk             | TBD       | TBD      | TBD                 |
| HRIS                              | TBD       | TBD      | TBD                 |
| Payroll / Statutory               | TBD       | TBD      | TBD                 |
| Fixed Assets                      | TBD       | TBD      | TBD                 |
| Fixed Deposits                    | TBD       | TBD      | TBD                 |
| Inventory                         | TBD       | TBD      | TBD                 |
| Workflow / Approvals              | TBD       | TBD      | TBD                 |
| DMS                               | TBD       | TBD      | TBD                 |
| Notifications                     | TBD       | TBD      | TBD                 |
| Compliance                        | TBD       | TBD      | TBD                 |
| Reports / BI                      | TBD       | TBD      | TBD                 |
| Portals (Borrower / ESS / Vendor) | TBD       | TBD      | TBD                 |

---

## Appendix A — Production-readiness roadmap (summary)

The full plan lives at `.Codex/plans/use-the-Codex-review-prompt-md-for-reactive-leaf.md`. Each stage has a gate; no stage is skipped.

| Stage | Focus                                                                                                                                                                                                                                            | Status                                                 | Gate                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **0** | Orientation & baseline: pick pnpm, delete `package-lock.json`, land this AGENTS.md, capture baseline test numbers, boot smoke.                                                                                                                   | ✅ **Closed**                                          | Baseline captured; AGENTS.md committed.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| **1** | Critical security & correctness: RLS f-string fix; Fernet encrypt GST portal passwords; TS `strict`; remove `console.log`; ESLint + Prettier + Husky; backend pre-commit.                                                                        | ✅ **Closed**                                          | Lint/typecheck clean; `console.log` count = 0.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| **2** | Frontend foundation: real `AuthContext` + `OrganizationContext`; react-query + interceptor; Zustand; canonical components; mock-data purge; `App.tsx` lazy-split.                                                                                | ✅ **Closed**                                          | Zero `TODO: organization_id`; zero mock data in production pages; every new page uses shell components.                                                                                                                                                                                                                                                                                                                                                                                                                              |
| **3** | Test infrastructure: Vitest + Testing Library + jsdom; MSW; Playwright; testcontainers-python; GitHub Actions CI with required checks.                                                                                                           | ✅ **Closed**                                          | `pnpm test`, `pnpm test:integration`, `pnpm test:e2e`, `pytest` all green in CI.                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| **4** | Domain correctness: golden-file fixtures for EMI, NPA buckets, provisioning, receipt allocation, GL posting (balance + closed-period guard), depreciation; idempotency middleware + table; optimistic-locking audit; receipt-allocation rewrite. | ✅ **Closed** (primitives)                             | High-criticality services tested; 8 items deferred to Stage 4.5 (TDS / GST / payroll / BRS / maker-checker golden tests; optimistic-lock column rollout).                                                                                                                                                                                                                                                                                                                                                                            |
| **5** | Security / audit hardening: rate limiting; webhook HMAC primitive; PII masking utility; DMS upload hardening; audit hash chain primitive; security-response headers.                                                                             | ✅ **Closed** (primitives)                             | Primitives landed + tested. 8 items deferred for per-vendor wiring, ClamAV sidecar, hash-chain persistence, cold-partition storage.                                                                                                                                                                                                                                                                                                                                                                                                  |
| **6** | Background jobs + integrations + observability: Arq scaffold; integration-base client (retry + circuit breaker); feature flags; OpenTelemetry (FastAPI + httpx + SQLAlchemy).                                                                    | ✅ **Closed** (scaffold)                               | Scaffold + 58 tests. 22 per-vendor integrations deferred (each with feature flag + approval in `.stubs-approved.md`).                                                                                                                                                                                                                                                                                                                                                                                                                |
| **7** | UI/UX quality pass: NBFC palette in `tailwind.config.cjs`; `@axe-core/playwright` fixture; visual-regression scaffold; design-token contract tests.                                                                                              | ✅ **Closed** (primitives)                             | Tokens + tooling landed + tested. 354-page module sweep and visual-baseline capture deferred as STAGE-7-PENDING-\*.                                                                                                                                                                                                                                                                                                                                                                                                                  |
| **8** | Final gate: full test matrix with numbers; dependency scan (`pnpm audit`, `pip-audit`); production-readiness report; tag release.                                                                                                                | ✅ **Closed** (report + audits + xlsx swap + chunking) | Report: [`PRODUCTION_READINESS_REPORT.md`](PRODUCTION_READINESS_REPORT.md). Full evidence captured. `pnpm audit --prod`: **0 critical, 0 high** after `xlsx` → `exceljs` swap (STAGE-8-003); 1 remaining moderate is `uuid` transitive via `exceljs` with no exploitable path. Backend `pip-audit` clean. Bundle chunking (STAGE-8-004) dropped the main entry from 2.0 MB → 1.0 MB raw (179 kB gzip). **Release tag (v1.0) explicitly deferred — STAGE-8-PENDING-release-tag — until the go-live checklist in report §5 is green.** |

**Running totals after Stage 8:**

- **318 backend tests** passing (316 unit + 2 testcontainers integration).
- **55 frontend unit tests** passing (Vitest).
- **9 frontend integration tests** passing (Vitest + MSW).
- **3 Playwright smokes** + 1 `runAxe` assertion on login + visual-regression scaffold.
- **Grand total: 385 code-level tests, 0 failed, 0 xfailed.**
- **Stub-lint clean (67 approved, 0 unapproved). `pip-audit` clean. `pnpm audit --prod` down to 2 high-sev (both `xlsx`, tracked).**
- **Typecheck clean (src + playwright). Build succeeds, 5.8 MB / 110 chunks, 498 kB gzip initial.**

See `PRODUCTION_READINESS_REPORT.md` for the honest state, the risk list, and the §5 go-live checklist.

---

## Appendix B — Quick-reference decision table

| Situation                                           | Rule                                                                                                                                                                   | Section       |
| --------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------- |
| I need to show money                                | `<AmountDisplay>`                                                                                                                                                      | §5.8          |
| I need to fetch server data                         | Write/use a hook in `src/hooks/<domain>/`; not axios in the page                                                                                                       | §5.4          |
| I need the current organization                     | `OrganizationContext.activeOrganizationId`                                                                                                                             | §3.4          |
| I'm adding a financial mutation endpoint            | Idempotency-Key required; permission gated; audit rows; optimistic locking                                                                                             | §6.3          |
| I'm posting a voucher                               | Service enforces Σdebit = Σcredit + period open + leaf accounts                                                                                                        | §4.3          |
| I need a new table                                  | Extend `BaseModel` + `AuditMixin` + `SoftDeleteMixin` + `VersionedMixin`; include `organization_id`                                                                    | §3.4          |
| I need to catch an error                            | Typed `AppException` subclass; never bare `except Exception`                                                                                                           | §6.10         |
| I need to add a PII field                           | Mask at API; `pii.view` permission; audit unmasked reads                                                                                                               | §8.7          |
| I need to call an external API                      | New module under `app/integrations/<vendor>/` with retry, circuit breaker, timeouts                                                                                    | §6.7          |
| An external integration is not released yet         | Keep the manual workflow complete and visible; integration stays optional, tenant-scoped, feature-flagged, and auditable.                                              | §1 / §6.7     |
| I'm changing navigation or module visibility        | Show the full ERP module set by default. Loan-only mode is a temporary development aid, not the client-facing product state.                                           | §1 / §12.27   |
| A process can be automated without external systems | Automate the internal calculation/workflow if it improves correctness, but keep the same domain model and preserve manual override/entry where operationally required. | §1 / §6.7     |
| I'm tempted to add `any`                            | Don't. Use `unknown` + narrow.                                                                                                                                         | §5.9          |
| A test is flaky                                     | Fix the flake; never `.skip` without a ticket and expiry                                                                                                               | §10.8         |
| A user reports a UI bug                             | Follow §11 seven-step loop                                                                                                                                             | §11           |
| I need a new secret (API key, password, token)      | Platform-wide (same for every NBFC) → env / pydantic-settings. Tenant-owned (NBFC-specific) → Fernet-encrypted DB setting keyed by `organization_id`, never env.       | §6.8 / §12.24 |
| I'm onboarding a new NBFC                           | No redeploy. Create an `Organization` row + seed perms / feature-flag defaults / tenant secrets via the admin UI or a migration-independent script.                    | §1            |
| I'm about to write a query that might cross tenants | Don't — unless it's an explicit super-admin endpoint with `RequirePermissions("platform.admin")`, maker-checker, and an audit row. RLS is the default.                 | §3.4 / §1     |

---

_This file is the contract. If something here is wrong, fix it in the PR that deviates. Otherwise, follow it._

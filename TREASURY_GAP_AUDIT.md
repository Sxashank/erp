# Treasury Gap Audit

## Purpose

This audit defines the current treasury baseline, the reuse boundaries we must respect, and the phase-1 manual-first scope to harden next.

This is explicitly written to avoid duplicating the hardened Part 1 foundation. Treasury must extend the existing system, not create a second one.

## Non-Duplication Rules

- Reuse the existing backend route family under `/api/v1/lending/treasury*`, `/api/v1/lending/treasury/investments*`, `/api/v1/lending/liquidity-risk*`, `/api/v1/lending/counterparty-risk*`, and `/api/v1/lending/stress-test*`.
- Reuse the existing service layer in [backend/app/services/lending/treasury_service.py](/Users/balakrishnavundavalli/working/talentfino/erp/backend/app/services/lending/treasury_service.py), [fund_deployment_service.py](/Users/balakrishnavundavalli/working/talentfino/erp/backend/app/services/lending/fund_deployment_service.py), [investment_service.py](/Users/balakrishnavundavalli/working/talentfino/erp/backend/app/services/lending/investment_service.py), [liquidity_risk_service.py](/Users/balakrishnavundavalli/working/talentfino/erp/backend/app/services/lending/liquidity_risk_service.py), [counterparty_risk_service.py](/Users/balakrishnavundavalli/working/talentfino/erp/backend/app/services/lending/counterparty_risk_service.py), and [stress_test_service.py](/Users/balakrishnavundavalli/working/talentfino/erp/backend/app/services/lending/stress_test_service.py).
- Reuse the existing masters and accounting foundation. No new lender master, no new borrowing ledger, no new approval engine, no new organization/unit/account/cost-center models.
- Reuse the existing route surfaces already mounted in [src/App.tsx](/Users/balakrishnavundavalli/working/talentfino/erp/src/App.tsx). Do not introduce a third treasury route tree.
- Reuse the current admin navigation section in [src/layouts/AdminLayout.tsx](/Users/balakrishnavundavalli/working/talentfino/erp/src/layouts/AdminLayout.tsx). Treasury is already a first-class module there.

## Current Surface

### Backend Already Exists

- Core treasury CRUD and summaries:
  - [backend/app/api/v1/lending/treasury.py](/Users/balakrishnavundavalli/working/talentfino/erp/backend/app/api/v1/lending/treasury.py)
- Treasury investments:
  - [backend/app/api/v1/lending/treasury_investments.py](/Users/balakrishnavundavalli/working/talentfino/erp/backend/app/api/v1/lending/treasury_investments.py)
- Liquidity risk:
  - [backend/app/api/v1/lending/liquidity_risk.py](/Users/balakrishnavundavalli/working/talentfino/erp/backend/app/api/v1/lending/liquidity_risk.py)
- Counterparty risk:
  - [backend/app/api/v1/lending/counterparty_risk.py](/Users/balakrishnavundavalli/working/talentfino/erp/backend/app/api/v1/lending/counterparty_risk.py)
- Stress testing:
  - [backend/app/api/v1/lending/stress_test.py](/Users/balakrishnavundavalli/working/talentfino/erp/backend/app/api/v1/lending/stress_test.py)

### Frontend Already Exists

- Operational treasury under lending pages:
  - [src/pages/lending/treasury/TreasuryDashboard.tsx](/Users/balakrishnavundavalli/working/talentfino/erp/src/pages/lending/treasury/TreasuryDashboard.tsx)
  - [src/pages/lending/treasury/lenders/LenderList.tsx](/Users/balakrishnavundavalli/working/talentfino/erp/src/pages/lending/treasury/lenders/LenderList.tsx)
  - [src/pages/lending/treasury/lenders/LenderForm.tsx](/Users/balakrishnavundavalli/working/talentfino/erp/src/pages/lending/treasury/lenders/LenderForm.tsx)
  - [src/pages/lending/treasury/borrowings/BorrowingList.tsx](/Users/balakrishnavundavalli/working/talentfino/erp/src/pages/lending/treasury/borrowings/BorrowingList.tsx)
  - [src/pages/lending/treasury/borrowings/BorrowingForm.tsx](/Users/balakrishnavundavalli/working/talentfino/erp/src/pages/lending/treasury/borrowings/BorrowingForm.tsx)
  - [src/pages/lending/treasury/borrowings/BorrowingView.tsx](/Users/balakrishnavundavalli/working/talentfino/erp/src/pages/lending/treasury/borrowings/BorrowingView.tsx)
  - [src/pages/lending/treasury/source-of-funds/SourceOfFundsWorkbench.tsx](/Users/balakrishnavundavalli/working/talentfino/erp/src/pages/lending/treasury/source-of-funds/SourceOfFundsWorkbench.tsx)
  - [src/pages/lending/treasury/alm/ALMDashboard.tsx](/Users/balakrishnavundavalli/working/talentfino/erp/src/pages/lending/treasury/alm/ALMDashboard.tsx)
  - [src/pages/lending/treasury/alm/GapAnalysis.tsx](/Users/balakrishnavundavalli/working/talentfino/erp/src/pages/lending/treasury/alm/GapAnalysis.tsx)
  - [src/pages/lending/treasury/alm/InterestRateRisk.tsx](/Users/balakrishnavundavalli/working/talentfino/erp/src/pages/lending/treasury/alm/InterestRateRisk.tsx)
- Standalone treasury analytics and investments:
  - [src/pages/treasury/InvestmentList.tsx](/Users/balakrishnavundavalli/working/talentfino/erp/src/pages/treasury/InvestmentList.tsx)
  - [src/pages/treasury/InvestmentCreate.tsx](/Users/balakrishnavundavalli/working/talentfino/erp/src/pages/treasury/InvestmentCreate.tsx)
  - [src/pages/treasury/InvestmentMaturity.tsx](/Users/balakrishnavundavalli/working/talentfino/erp/src/pages/treasury/InvestmentMaturity.tsx)
  - [src/pages/treasury/LiquidityRisk.tsx](/Users/balakrishnavundavalli/working/talentfino/erp/src/pages/treasury/LiquidityRisk.tsx)
  - [src/pages/treasury/CounterpartyRisk.tsx](/Users/balakrishnavundavalli/working/talentfino/erp/src/pages/treasury/CounterpartyRisk.tsx)
  - [src/pages/treasury/StressTest.tsx](/Users/balakrishnavundavalli/working/talentfino/erp/src/pages/treasury/StressTest.tsx)
  - [src/pages/treasury/RiskDashboard.tsx](/Users/balakrishnavundavalli/working/talentfino/erp/src/pages/treasury/RiskDashboard.tsx)
  - [src/pages/treasury/VaRReport.tsx](/Users/balakrishnavundavalli/working/talentfino/erp/src/pages/treasury/VaRReport.tsx)

### Query / Service Layer Already Exists

- Summary:
  - [src/hooks/lending/useTreasurySummary.ts](/Users/balakrishnavundavalli/working/talentfino/erp/src/hooks/lending/useTreasurySummary.ts)
- Lenders and borrowings:
  - [src/hooks/lending/useLenders.ts](/Users/balakrishnavundavalli/working/talentfino/erp/src/hooks/lending/useLenders.ts)
  - [src/hooks/lending/useBorrowings.ts](/Users/balakrishnavundavalli/working/talentfino/erp/src/hooks/lending/useBorrowings.ts)
- Investments:
  - [src/hooks/lending/useTreasuryInvestments.ts](/Users/balakrishnavundavalli/working/talentfino/erp/src/hooks/lending/useTreasuryInvestments.ts)
  - [src/services/lending/treasuryInvestmentApi.ts](/Users/balakrishnavundavalli/working/talentfino/erp/src/services/lending/treasuryInvestmentApi.ts)
- Liquidity / counterparty / stress:
  - [src/hooks/lending/useLiquidityRisk.ts](/Users/balakrishnavundavalli/working/talentfino/erp/src/hooks/lending/useLiquidityRisk.ts)
  - [src/hooks/lending/useCounterpartyRisk.ts](/Users/balakrishnavundavalli/working/talentfino/erp/src/hooks/lending/useCounterpartyRisk.ts)
  - [src/hooks/lending/useStressTest.ts](/Users/balakrishnavundavalli/working/talentfino/erp/src/hooks/lending/useStressTest.ts)
  - [src/services/lending/treasuryApi.ts](/Users/balakrishnavundavalli/working/talentfino/erp/src/services/lending/treasuryApi.ts)

## What Is Already Strong Enough To Reuse

- Treasury is already modeled as one domain, not multiple disconnected subsystems.
- Investments are already on a clean camelCase API contract with typed hooks and idempotency handling in:
  - [src/services/lending/treasuryInvestmentApi.ts](/Users/balakrishnavundavalli/working/talentfino/erp/src/services/lending/treasuryInvestmentApi.ts)
  - [backend/app/api/v1/lending/treasury_investments.py](/Users/balakrishnavundavalli/working/talentfino/erp/backend/app/api/v1/lending/treasury_investments.py)
- Liquidity, counterparty, and stress surfaces already have real backend computations and real react-query wrappers. They are not mocked dashboards.
- Borrowings, lenders, ALM, and source-of-funds are already represented in one service stack rather than split into separate micro-flows.

## Gaps And Risks

### 1. Tenant Dependency Drift In Core Treasury Endpoints

This is the biggest backend hardening issue.

Many authenticated endpoints in [backend/app/api/v1/lending/treasury.py](/Users/balakrishnavundavalli/working/talentfino/erp/backend/app/api/v1/lending/treasury.py) still use `Depends(get_db)` instead of `Depends(get_db_with_tenant)`.

That breaks the repository contract in AGENTS.md §3.4. Even where `organization_id` is passed into service methods, the route should still run under the tenant-scoped DB dependency so RLS and downstream queries stay safe by default.

This needs to be normalized before we expand treasury further.

### 2. Treasury Is Split Across Two Route Trees

The same domain is mounted under both:

- `/admin/lending/treasury/*`
- `/admin/treasury/*`

See [src/App.tsx](/Users/balakrishnavundavalli/working/talentfino/erp/src/App.tsx).

This is not a second backend, but it is a duplicated navigation surface. It increases maintenance cost and makes it easier to accidentally build parallel UX later.

The next phase should standardize which tree is canonical and keep the other as compatibility redirects if needed.

### 3. Older Treasury Forms Bypass The Hook Layer

Some older operational pages still fetch and mutate directly from the page instead of going through dedicated mutation hooks:

- [src/pages/lending/treasury/borrowings/BorrowingForm.tsx](/Users/balakrishnavundavalli/working/talentfino/erp/src/pages/lending/treasury/borrowings/BorrowingForm.tsx)
- [src/pages/lending/treasury/lenders/LenderForm.tsx](/Users/balakrishnavundavalli/working/talentfino/erp/src/pages/lending/treasury/lenders/LenderForm.tsx)

This is not a parallel system, but it is below the current frontend contract used in fixed assets and the newer treasury analytics pages.

### 4. Investments Need Operational Completion, Not Re-architecture

Investments are fairly well structured, but there is a material lifecycle gap:

- [backend/app/services/lending/investment_service.py](/Users/balakrishnavundavalli/working/talentfino/erp/backend/app/services/lending/investment_service.py) still carries a TODO for GL posting on maturity / sale.

That means the module can record holdings and maturity events, but the treasury-accounting close loop is not fully complete yet.

This should be wired into the existing accounting posting path, not solved by a standalone treasury ledger.

### 5. Risk Dashboard And VaR Are Intentionally Not Ready

These pages are explicit placeholders:

- [src/pages/treasury/RiskDashboard.tsx](/Users/balakrishnavundavalli/working/talentfino/erp/src/pages/treasury/RiskDashboard.tsx)
- [src/pages/treasury/VaRReport.tsx](/Users/balakrishnavundavalli/working/talentfino/erp/src/pages/treasury/VaRReport.tsx)

They correctly refuse to fabricate numbers. They should stay out of phase 1 unless we are willing to build the full aggregation and VaR engine.

### 6. Treasury Test Coverage Is Thin

There are currently no obvious dedicated treasury backend test folders or treasury Playwright specs in the repo search, unlike fixed assets.

That means treasury likely has lower verification depth than fixed assets today even where real functionality exists.

## Recommended Phase-1 Treasury Scope

This should be manual-first and bounded.

### In Scope

- Lenders
- Borrowings
- Tranches / drawdowns
- Borrowing payments
- Source-of-funds mapping
- Treasury dashboard
- ALM dashboard and gap analysis
- Interest-rate-risk preview
- Investment register
- Investment maturity / sale flow
- Liquidity risk
- Counterparty risk
- Stress testing

### Out Of Scope For Phase 1

- VaR engine
- Unified risk snapshot engine behind `RiskDashboard`
- Full market-risk analytics platform
- External treasury integrations
- Automated bank / depository feeds
- A new reporting subsystem separate from the current reports foundation

## Recommended Implementation Order

1. **Tenant Hardening**
   - Convert treasury authenticated routes in [backend/app/api/v1/lending/treasury.py](/Users/balakrishnavundavalli/working/talentfino/erp/backend/app/api/v1/lending/treasury.py) to `get_db_with_tenant`.

2. **Surface Consolidation**
   - Define one canonical treasury route tree.
   - Keep the alternative tree only as compatibility routing if necessary.

3. **Frontend Contract Hardening**
   - Move lender and borrowing create/edit flows onto proper mutation hooks.
   - Eliminate page-level fetch orchestration where hooks should own it.

4. **Treasury Accounting Completion**
   - Wire investment maturity / sale GL posting through the existing accounting foundation.
   - Do not create treasury-specific posting shortcuts.

5. **Verification**
   - Add backend treasury tests.
   - Add frontend integration coverage.
   - Add at least one real Playwright path:
     - create lender
     - create borrowing
     - create tranche / payment if exposed
     - map source of funds
     - create investment
     - mature or sell investment
     - open liquidity / counterparty / stress views successfully

## What Not To Do

- Do not create `src/pages/treasury-v2/*`.
- Do not create a second treasury API namespace.
- Do not create a treasury-only posting engine.
- Do not add mocked summary cards for risk or VaR.
- Do not build new masters for lenders, exposures, or funding sources outside the current treasury models.

## Recommendation

The next module should be **Treasury operational core hardening**, not HRIS or taxation.

Reason:

- It is closest to the NBFC operating model after lending.
- The backend base is already substantial.
- The missing work is mostly hardening, consolidation, and verification.
- It can be completed manual-first without external integrations.

If we start implementation, the first actual change should be:

- tenant hardening of [backend/app/api/v1/lending/treasury.py](/Users/balakrishnavundavalli/working/talentfino/erp/backend/app/api/v1/lending/treasury.py)
- followed by frontend cleanup of lender / borrowing forms onto query-hook patterns


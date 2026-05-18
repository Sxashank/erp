"""Lending API package."""

from fastapi import APIRouter

# Phase 6: Account Aggregator Integration
from app.api.v1.lending.aa import router as aa_router
from app.api.v1.lending.applications import router as applications_router

# Approval Checklist (loan-application gating)
from app.api.v1.lending.checklist import router as checklist_router
from app.api.v1.lending.closure_cockpit import router as closure_cockpit_router
from app.api.v1.lending.collaterals import router as collaterals_router
from app.api.v1.lending.collection_cockpit import router as collection_cockpit_router

# Phase 3: NPA & Collections
from app.api.v1.lending.collections import router as collections_router
from app.api.v1.lending.counterparty_risk import router as counterparty_risk_router

# Phase 7: Credit Bureau Integration
from app.api.v1.lending.credit import router as credit_router
from app.api.v1.lending.disbursement_readiness import (
    router as disbursement_readiness_router,
)
from app.api.v1.lending.disbursements import router as disbursements_router
from app.api.v1.lending.entities import router as entities_router

# IIF (Interest Incentivization Fund — Maritime Development Fund)
from app.api.v1.lending.iif import router as iif_router
from app.api.v1.lending.liquidity_risk import router as liquidity_risk_router

# Phase 2: Loan Accounting
from app.api.v1.lending.loan_accounts import router as loan_accounts_router

# Phase 5: NACH Integration
from app.api.v1.lending.nach import router as nach_router

# Phase 8: Enhanced Lending Features
from app.api.v1.lending.npa import router as npa_router
from app.api.v1.lending.products import router as products_router
from app.api.v1.lending.receipts import router as receipts_router
from app.api.v1.lending.repayment_matching import router as repayment_matching_router
from app.api.v1.lending.risk_cockpit import router as risk_cockpit_router
from app.api.v1.lending.sanctions import router as sanctions_router
from app.api.v1.lending.schedules import router as schedules_router
from app.api.v1.lending.stress_test import router as stress_test_router

# Phase 4: Treasury & ALM
from app.api.v1.lending.treasury import router as treasury_router
from app.api.v1.lending.treasury_investments import router as treasury_investments_router

router = APIRouter()

# Dashboard aggregator — composes data from the per-domain endpoints below
# so the lending dashboard makes one network round-trip instead of six.
from app.api.v1.lending.dashboard import router as dashboard_router

router.include_router(dashboard_router, prefix="/dashboard", tags=["Lending - Dashboard"])
router.include_router(
    risk_cockpit_router,
    prefix="/risk-cockpit",
    tags=["Lending - Credit Risk Cockpit"],
)
router.include_router(
    collection_cockpit_router,
    prefix="/collection-cockpit",
    tags=["Lending - Collection Cockpit"],
)
router.include_router(
    disbursement_readiness_router,
    prefix="/disbursement-readiness",
    tags=["Lending - Disbursement Readiness"],
)
router.include_router(
    closure_cockpit_router,
    prefix="/closure-cockpit",
    tags=["Lending - Closure Cockpit"],
)

# Phase 1: LOS
router.include_router(entities_router, prefix="/entities", tags=["LOS - Entities"])
router.include_router(products_router, prefix="/products", tags=["LOS - Products"])
router.include_router(applications_router, prefix="/applications", tags=["LOS - Applications"])
router.include_router(sanctions_router, prefix="/sanctions", tags=["LOS - Sanctions"])

# Phase 2: LMS
router.include_router(loan_accounts_router, prefix="/loan-accounts", tags=["LMS - Loan Accounts"])

# Phase 3: Collections & NPA
router.include_router(collections_router, prefix="/collections", tags=["COL - Collections & NPA"])

# Phase 4: Treasury & ALM
router.include_router(treasury_router, prefix="/treasury", tags=["TRS - Treasury & ALM"])
router.include_router(
    treasury_investments_router,
    prefix="/treasury/investments",
    tags=["TRS - Investment Portfolio"],
)
router.include_router(
    counterparty_risk_router,
    prefix="/counterparty-risk",
    tags=["TRS - Counterparty Risk"],
)
router.include_router(
    stress_test_router,
    prefix="/stress-test",
    tags=["TRS - Stress Testing"],
)
router.include_router(
    liquidity_risk_router,
    prefix="/liquidity-risk",
    tags=["TRS - Liquidity Risk"],
)

# Phase 5: NACH Integration
router.include_router(nach_router, tags=["INT - NACH Integration"])

# Phase 6: Account Aggregator Integration
router.include_router(aa_router, tags=["INT - Account Aggregator"])

# Phase 7: Credit Bureau Integration
router.include_router(credit_router, tags=["INT - Credit Bureau"])

# Phase 8: Enhanced Lending Features
router.include_router(npa_router, prefix="/npa", tags=["LMS - NPA Management"])
router.include_router(schedules_router, prefix="/schedules", tags=["LMS - Loan Schedules"])
router.include_router(receipts_router, prefix="/receipts", tags=["LMS - Receipts"])
router.include_router(collaterals_router, prefix="/collaterals", tags=["LMS - Collaterals"])
router.include_router(disbursements_router, prefix="/disbursements", tags=["LMS - Disbursements"])
router.include_router(
    repayment_matching_router,
    prefix="/repayment-matching",
    tags=["LMS - Repayment Matching"],
)

# IIF — Interest Incentivization Fund (Maritime Development Fund)
router.include_router(iif_router, prefix="/iif")

# Approval Checklist — per-loan gating before sanction approval
router.include_router(checklist_router, prefix="/checklist", tags=["LOS - Approval Checklist"])

"""Lending API package."""

from fastapi import APIRouter

from app.api.v1.lending.entities import router as entities_router
from app.api.v1.lending.products import router as products_router
from app.api.v1.lending.applications import router as applications_router
from app.api.v1.lending.sanctions import router as sanctions_router

# Phase 2: Loan Accounting
from app.api.v1.lending.loan_accounts import router as loan_accounts_router

# Phase 3: NPA & Collections
from app.api.v1.lending.collections import router as collections_router

# Phase 4: Treasury & ALM
from app.api.v1.lending.treasury import router as treasury_router

# Phase 5: NACH Integration
from app.api.v1.lending.nach import router as nach_router

# Phase 6: Account Aggregator Integration
from app.api.v1.lending.aa import router as aa_router

# Phase 7: Credit Bureau Integration
from app.api.v1.lending.credit import router as credit_router

# Phase 8: Enhanced Lending Features
from app.api.v1.lending.npa import router as npa_router
from app.api.v1.lending.schedules import router as schedules_router
from app.api.v1.lending.receipts import router as receipts_router
from app.api.v1.lending.collaterals import router as collaterals_router
from app.api.v1.lending.disbursements import router as disbursements_router

router = APIRouter()

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

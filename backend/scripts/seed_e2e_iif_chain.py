"""Seed a minimal IIF claim chain into the E2E database.

The E2E suite's `12-iif-claim-exports.spec.ts` includes a live-export gate
("if a claim exists, XLSX + PDF endpoints return correctly-formatted bytes").
On a freshly-seeded E2E DB no claim exists, so the assertion soft-skips.

This script materialises the full prerequisite chain:

    Entity → LoanProduct → LoanApplication → LoanSanction
        → LoanAccount → Disbursement(PROCESSED) → LoanReceipt
        → LoanSubventionEnrollment → SubventionClaim(DRAFT)

…all under the E2E organisation (`SEED_ORG_CODE`, default `SMFC-E2E`) so the
existing E2E suite still operates on the same tenant. The chain is idempotent;
re-runs are no-ops once the rows exist.

Why a separate script (not reuse `seed_uat_manual_lending.py` directly):
- The UAT script hard-codes `code="SMFC_UAT"` and would reassign the seeded
  `krishna` admin to that org, breaking the existing 212-test suite that runs
  against `SMFC-E2E`. This script only consumes the existing E2E org +
  admin and never creates / re-assigns either.
- The UAT script also seeds workflow definitions, portal users, treasury
  positions, etc. — none of which the IIF claim report needs. Scoping this
  script to the minimum chain keeps the seed surface small.

Run:

    SEED_ORG_CODE=SMFC-E2E \
        DATABASE_URL=postgresql+asyncpg://smfc:smfc_secret@localhost:5432/smfc_erp_e2e \
        python backend/scripts/seed_e2e_iif_chain.py
"""

from __future__ import annotations

import asyncio
import os
import sys
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import app.models  # noqa: F401  — register ORM tables
import app.models.lending  # noqa: F401
from app.database import async_session_factory
from app.models.finance.account import Account
from app.models.lending.entity import Entity
from app.models.lending.enums import (
    ApplicationStage,
    ApplicationStatus,
    AssetClassification,
    ClaimFrequency,
    DayCountConvention,
    DisbursementMode,
    DisbursementStatus,
    EntityStatus,
    EntityType,
    IIFLoanType,
    InterestType,
    LoanAccountStatus,
    ProductCategory,
    ReceiptMode,
    ReceiptStatus,
    ReceiptType,
    RepaymentFrequency,
    RepaymentMode,
    SanctionStatus,
    SubventionClaimStatus,
    SubventionEnrollmentStatus,
)
from app.models.lending.application import LoanApplication
from app.models.lending.loan_account import Disbursement, LoanAccount, LoanReceipt
from app.models.lending.product import LoanProduct
from app.models.lending.sanction import LoanSanction
from app.models.lending.iif.loan_subvention_enrollment import LoanSubventionEnrollment
from app.models.lending.iif.subvention_claim import SubventionClaim
from app.models.lending.iif.subvention_scheme import SubventionScheme
from app.models.masters.organization import Organization


SEED_ORG_CODE = os.environ.get("SEED_ORG_CODE", "SMFC-E2E")

ENTITY_CODE = "E2E-IIF-ENT-001"
PRODUCT_CODE = "E2E-IIF-PROD-001"
APPLICATION_NUMBER = "E2E-IIF-APP-001"
SANCTION_NUMBER = "E2E-IIF-SANC-001"
LOAN_ACCOUNT_NUMBER = "E2E-IIF-LOAN-001"
DISBURSEMENT_REF = "E2E-IIF-DISB-001"
RECEIPT_NUMBER = "E2E-IIF-RCPT-001"
CLAIM_REFERENCE = "E2E/IIF/2026Q1/00001"


def money(value: str | int | Decimal) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"))


def today() -> date:
    return date.today()


def add_months(base: date, months: int) -> date:
    year = base.year + ((base.month - 1 + months) // 12)
    month = ((base.month - 1 + months) % 12) + 1
    day = min(base.day, 28)
    return date(year, month, day)


async def scalar(session: AsyncSession, stmt):
    return (await session.execute(stmt)).scalar_one_or_none()


async def get_gl_accounts(session: AsyncSession, org: Organization) -> dict[str, object]:
    """Resolve seeded lending GL mappings by account code."""
    code_map = {
        "loan_asset": "1301",
        "interest_receivable": "1404",
        "interest_income": "4001",
        "penal_interest_income": "4103",
        "charges_income": "4101",
        "receipt_suspense": "2104",
        "source_bank": "1101",
    }
    rows = (
        await session.execute(
            select(Account).where(
                Account.organization_id == org.id,
                Account.code.in_(code_map.values()),
            )
        )
    ).scalars()
    accounts_by_code = {a.code: a.id for a in rows}
    return {key: accounts_by_code.get(code) for key, code in code_map.items()}


async def ensure_entity(session: AsyncSession, org: Organization) -> Entity:
    entity = await scalar(
        session,
        select(Entity).where(
            Entity.organization_id == org.id,
            Entity.entity_code == ENTITY_CODE,
        ),
    )
    if entity:
        return entity
    entity = Entity(
        organization_id=org.id,
        entity_code=ENTITY_CODE,
        entity_type=EntityType.CORPORATE,
        legal_name="E2E IIF Borrower Private Limited",
        trade_name="E2E IIF Borrower",
        pan="AAACE2E1AZ",
        gstin="27AAACE2E1AZ1Z5",
        kyc_verified=True,
        kyc_verified_date=today() - timedelta(days=60),
        date_of_incorporation=date(2018, 1, 1),
        place_of_incorporation="Mumbai",
        country_of_incorporation="IND",
        internal_rating="A+",
        external_rating="A",
        external_rating_agency="CRISIL",
        authorized_capital=money("1000000000"),
        paid_up_capital=money("500000000"),
        net_worth=money("800000000"),
        turnover=money("2500000000"),
        employee_count=350,
        primary_email="e2e-iif-borrower@example.com",
        primary_phone="9876543210",
        region="West",
        status=EntityStatus.ACTIVE,
        onboarding_date=today() - timedelta(days=120),
        remarks="E2E IIF chain seed entity — created by seed_e2e_iif_chain.py.",
    )
    session.add(entity)
    await session.flush()
    return entity


async def ensure_product(session: AsyncSession, org: Organization) -> LoanProduct:
    product = await scalar(
        session,
        select(LoanProduct).where(
            LoanProduct.organization_id == org.id,
            LoanProduct.code == PRODUCT_CODE,
        ),
    )
    if product:
        return product
    product = LoanProduct(
        organization_id=org.id,
        code=PRODUCT_CODE,
        name="E2E IIF Term Loan",
        description="E2E IIF chain seed product — TERM_LOAN_CAPEX for IIF.",
        category=ProductCategory.TERM_LOAN,
        min_amount=money("1000000"),
        max_amount=money("5000000000"),
        default_amount=money("250000000"),
        min_tenure_months=12,
        max_tenure_months=180,
        default_tenure_months=84,
        allows_moratorium=True,
        max_moratorium_months=24,
        moratorium_type="INTEREST_ONLY",
        interest_type=InterestType.FLOATING,
        min_spread_bps=150,
        max_spread_bps=600,
        default_spread_bps=275,
        min_effective_rate=money("8.00"),
        max_effective_rate=money("18.00"),
        day_count_convention=DayCountConvention.ACT_365,
        allowed_repayment_frequencies=["MONTHLY", "QUARTERLY"],
        default_repayment_frequency=RepaymentFrequency.QUARTERLY,
        allowed_repayment_modes=["EMI", "STRUCTURED", "BULLET"],
        default_repayment_mode=RepaymentMode.STRUCTURED,
        requires_collateral=True,
        min_collateral_coverage=money("125.00"),
        eligible_entity_types=["CORPORATE", "LLP"],
        disbursement_type="TRANCHE_BASED",
        max_tranches=4,
        allows_partial_disbursement=True,
        disbursement_validity_days=365,
        is_active_for_new_loans=True,
        effective_from=date(2026, 4, 1),
    )
    session.add(product)
    await session.flush()
    return product


async def ensure_application(
    session: AsyncSession,
    org: Organization,
    entity: Entity,
    product: LoanProduct,
) -> LoanApplication:
    app = await scalar(
        session,
        select(LoanApplication).where(
            LoanApplication.organization_id == org.id,
            LoanApplication.application_number == APPLICATION_NUMBER,
        ),
    )
    if app:
        return app
    amount = money("250000000")
    app = LoanApplication(
        organization_id=org.id,
        application_number=APPLICATION_NUMBER,
        entity_id=entity.id,
        product_id=product.id,
        requested_amount=amount,
        requested_tenure_months=84,
        purpose="IIF-eligible port infrastructure capex",
        detailed_purpose="E2E IIF chain seed — term loan capex for IIF subvention claim.",
        is_project_finance=True,
        project_name="E2E IIF Port Terminal",
        project_cost=(amount * Decimal("1.35")).quantize(Decimal("0.01")),
        promoter_contribution=(amount * Decimal("0.25")).quantize(Decimal("0.01")),
        promoter_contribution_pct=money("25.00"),
        bank_finance=amount,
        project_location="Maharashtra",
        project_start_date=today() - timedelta(days=180),
        project_completion_date=add_months(today(), 18),
        preferred_interest_type=InterestType.FLOATING,
        preferred_repayment_frequency=RepaymentFrequency.QUARTERLY,
        preferred_repayment_mode=RepaymentMode.STRUCTURED,
        requested_moratorium_months=6,
        stage=ApplicationStage.SANCTION,
        status=ApplicationStatus.SANCTIONED,
        application_date=today() - timedelta(days=75),
        submission_date=today() - timedelta(days=70),
        expected_decision_date=today() - timedelta(days=35),
        decision_date=today() - timedelta(days=25),
        entity_rating_at_application=entity.internal_rating,
        source_channel="DIRECT",
        remarks="Seeded by seed_e2e_iif_chain.py.",
    )
    session.add(app)
    await session.flush()
    return app


async def ensure_sanction(
    session: AsyncSession,
    org: Organization,
    app: LoanApplication,
    entity: Entity,
    product: LoanProduct,
) -> LoanSanction:
    sanction = await scalar(
        session,
        select(LoanSanction).where(
            LoanSanction.organization_id == org.id,
            LoanSanction.sanction_number == SANCTION_NUMBER,
        ),
    )
    if sanction:
        return sanction
    amount = money("250000000")
    sanction = LoanSanction(
        organization_id=org.id,
        application_id=app.id,
        entity_id=entity.id,
        product_id=product.id,
        sanction_number=SANCTION_NUMBER,
        sanction_letter_number=f"{SANCTION_NUMBER}/SL",
        sanction_date=today() - timedelta(days=25),
        validity_date=today() + timedelta(days=180),
        first_disbursement_deadline=today() + timedelta(days=90),
        sanctioned_amount=amount,
        requested_amount=app.requested_amount,
        approved_project_cost=app.project_cost,
        tenure_months=84,
        moratorium_months=6,
        moratorium_type="INTEREST_ONLY",
        interest_type=InterestType.FLOATING,
        base_rate_at_sanction=money("8.25"),
        spread_bps=275,
        effective_rate=money("11.00"),
        penal_interest_rate=money("2.00"),
        repayment_frequency=RepaymentFrequency.QUARTERLY,
        repayment_mode=RepaymentMode.STRUCTURED,
        repayment_start_date=add_months(today(), -2),
        day_count_convention=DayCountConvention.ACT_365,
        allows_prepayment=True,
        prepayment_lock_in_months=12,
        prepayment_penalty_rate=money("1.00"),
        allows_foreclosure=True,
        foreclosure_penalty_rate=money("1.00"),
        disbursement_type="TRANCHE_BASED",
        max_tranches=4,
        status=SanctionStatus.ACTIVE,
        approval_authority="E2E Credit Committee",
        approval_reference=f"E2E/CC/{today().year}/001",
        acceptance_required=True,
        acceptance_deadline=today() + timedelta(days=30),
        accepted_at=datetime.now(UTC) - timedelta(days=20),
        entity_rating=entity.internal_rating,
        special_terms="E2E IIF subvention chain seed.",
        remarks="Seeded by seed_e2e_iif_chain.py.",
    )
    session.add(sanction)
    await session.flush()
    return sanction


async def ensure_loan_account(
    session: AsyncSession,
    org: Organization,
    sanction: LoanSanction,
    entity: Entity,
    product: LoanProduct,
) -> LoanAccount:
    account = await scalar(
        session,
        select(LoanAccount).where(LoanAccount.loan_account_number == LOAN_ACCOUNT_NUMBER),
    )
    if account:
        return account
    gl = await get_gl_accounts(session, org)
    disbursed = money("250000000")
    account = LoanAccount(
        organization_id=org.id,
        sanction_id=sanction.id,
        entity_id=entity.id,
        product_id=product.id,
        loan_account_number=LOAN_ACCOUNT_NUMBER,
        loan_reference_number=f"REF-{LOAN_ACCOUNT_NUMBER[-3:]}",
        account_open_date=today() - timedelta(days=20),
        first_disbursement_date=today() - timedelta(days=15),
        last_disbursement_date=today() - timedelta(days=10),
        repayment_start_date=add_months(today(), -2),
        maturity_date=add_months(today(), 82),
        sanctioned_amount=sanction.sanctioned_amount,
        tenure_months=sanction.tenure_months,
        moratorium_months=sanction.moratorium_months,
        moratorium_end_date=add_months(today() - timedelta(days=20), 6),
        interest_type=sanction.interest_type,
        current_base_rate=sanction.base_rate_at_sanction,
        spread_bps=sanction.spread_bps,
        current_interest_rate=sanction.effective_rate,
        penal_interest_rate=sanction.penal_interest_rate,
        repayment_frequency=sanction.repayment_frequency,
        repayment_mode=sanction.repayment_mode,
        day_count_convention=sanction.day_count_convention,
        installment_day=5,
        current_emi_amount=money("8750000"),
        total_disbursed_amount=disbursed,
        undisbursed_amount=sanction.sanctioned_amount - disbursed,
        principal_outstanding=disbursed,
        interest_outstanding=money("0"),
        interest_overdue=money("0"),
        principal_overdue=money("0"),
        penal_interest_outstanding=money("0"),
        charges_outstanding=money("0"),
        total_outstanding=disbursed,
        total_principal_received=money("0"),
        total_interest_received=money("0"),
        days_past_due=0,
        oldest_due_date=None,
        asset_classification=AssetClassification.STANDARD,
        provision_percentage=money("0.40"),
        provision_amount=money("1000000"),
        provision_held=money("1000000"),
        accrual_suspended=False,
        status=LoanAccountStatus.ACTIVE,
        loan_asset_account_id=gl.get("loan_asset"),
        interest_receivable_account_id=gl.get("interest_receivable"),
        interest_income_account_id=gl.get("interest_income"),
        penal_interest_income_account_id=gl.get("penal_interest_income"),
        charges_income_account_id=gl.get("charges_income"),
        receipt_suspense_account_id=gl.get("receipt_suspense"),
        remarks="Seeded by seed_e2e_iif_chain.py.",
    )
    session.add(account)
    await session.flush()
    return account


async def ensure_disbursement(
    session: AsyncSession,
    account: LoanAccount,
) -> Disbursement:
    disb = await scalar(
        session,
        select(Disbursement).where(
            Disbursement.loan_account_id == account.id,
            Disbursement.disbursement_number == 1,
        ),
    )
    if disb:
        return disb
    amount = money("250000000")
    gl = await get_gl_accounts(session, account.organization)
    disb = Disbursement(
        loan_account_id=account.id,
        disbursement_number=1,
        disbursement_reference=DISBURSEMENT_REF,
        requested_amount=amount,
        approved_amount=amount,
        disbursed_amount=amount,
        disbursement_charges=money("0"),
        net_disbursement=amount,
        request_date=today() - timedelta(days=18),
        approval_date=today() - timedelta(days=16),
        scheduled_date=today() - timedelta(days=14),
        disbursement_date=today() - timedelta(days=14),
        value_date=today() - timedelta(days=14),
        disbursement_mode=DisbursementMode.RTGS,
        source_account_id=gl.get("source_bank"),
        beneficiary_name="E2E IIF Borrower Private Limited",
        beneficiary_account_number="1234567890123456",
        beneficiary_ifsc="SBIN0001234",
        beneficiary_bank="State Bank of India",
        utr_number="UTRE2EIIF0001",
        purpose="E2E IIF chain seed disbursement",
        conditions_verified=True,
        conditions_verified_at=datetime.now(UTC) - timedelta(days=16),
        status=DisbursementStatus.PROCESSED,
        approved_at=datetime.now(UTC) - timedelta(days=16),
        processed_at=datetime.now(UTC) - timedelta(days=14),
        remarks="Seeded by seed_e2e_iif_chain.py.",
    )
    session.add(disb)
    await session.flush()
    return disb


async def ensure_receipt(
    session: AsyncSession,
    org: Organization,
    account: LoanAccount,
) -> LoanReceipt:
    receipt = await scalar(
        session,
        select(LoanReceipt).where(
            LoanReceipt.organization_id == org.id,
            LoanReceipt.receipt_number == RECEIPT_NUMBER,
        ),
    )
    if receipt:
        return receipt
    interest_paid = money("6875000")
    receipt = LoanReceipt(
        organization_id=org.id,
        loan_account_id=account.id,
        receipt_number=RECEIPT_NUMBER,
        receipt_date=date(2026, 5, 15),
        value_date=date(2026, 5, 15),
        receipt_amount=interest_paid,
        receipt_type=ReceiptType.REGULAR,
        receipt_mode=ReceiptMode.NEFT,
        allocated_amount=interest_paid,
        unallocated_amount=money("0"),
        principal_allocated=money("0"),
        interest_allocated=interest_paid,
        penal_interest_allocated=money("0"),
        charges_allocated=money("0"),
        prepayment_charges=money("0"),
        status=ReceiptStatus.ALLOCATED,
        bounced=False,
        bounce_charges=money("0"),
        gl_allocated_amount=interest_paid,
        gl_principal_allocated=money("0"),
        gl_interest_allocated=interest_paid,
        gl_penal_interest_allocated=money("0"),
        gl_charges_allocated=money("0"),
        instrument_number="UTRE2EIIFRCPT01",
        remarks="Seeded by seed_e2e_iif_chain.py.",
    )
    session.add(receipt)
    await session.flush()
    return receipt


async def ensure_scheme(session: AsyncSession, org: Organization) -> SubventionScheme:
    """Reuse the seed_data.py-seeded IIF_DEFAULT scheme if present; else create."""
    scheme = await scalar(
        session,
        select(SubventionScheme).where(
            SubventionScheme.organization_id == org.id,
            SubventionScheme.scheme_code == "IIF_DEFAULT",
        ),
    )
    if scheme:
        return scheme
    # Defensive fallback — the canonical seed_data.py always inserts IIF_DEFAULT
    # but if a future change removes it, this script remains runnable.
    scheme = SubventionScheme(
        organization_id=org.id,
        scheme_code="IIF_DEFAULT",
        scheme_name="Interest Incentivization Fund",
        administering_ministry="Ministry of Ports, Shipping and Waterways",
        implementing_agency="Sagarmala Finance Corporation Limited",
        description="Default IIF scheme (E2E fallback insert).",
        subvention_rate_percent=money("3.00"),
        max_subvention_per_beneficiary=money("10000000000"),
        scheme_corpus=money("50000000000"),
        eligible_loan_types=[IIFLoanType.TERM_LOAN_CAPEX.value],
        max_tenure_term_loan_months=180,
        max_tenure_working_capital_months=60,
        scheme_start_date=date(2025, 9, 24),
        scheme_end_date=date(2036, 3, 31),
        eligibility_window_months=36,
        claim_frequency=ClaimFrequency.QUARTERLY.value,
        npa_disqualification_dpd_days=30,
    )
    session.add(scheme)
    await session.flush()
    return scheme


async def ensure_enrollment(
    session: AsyncSession,
    org: Organization,
    account: LoanAccount,
    scheme: SubventionScheme,
) -> LoanSubventionEnrollment:
    enrol = await scalar(
        session,
        select(LoanSubventionEnrollment).where(
            LoanSubventionEnrollment.organization_id == org.id,
            LoanSubventionEnrollment.loan_account_id == account.id,
            LoanSubventionEnrollment.scheme_id == scheme.id,
        ),
    )
    if enrol:
        return enrol
    enrol = LoanSubventionEnrollment(
        organization_id=org.id,
        loan_account_id=account.id,
        scheme_id=scheme.id,
        enrolled_date=date(2026, 4, 1),
        status=SubventionEnrollmentStatus.ENROLLED.value,
        total_claimed_to_date=money("0"),
        total_paid_to_date=money("0"),
        notes="Seeded by seed_e2e_iif_chain.py.",
    )
    session.add(enrol)
    await session.flush()
    return enrol


async def ensure_claim(
    session: AsyncSession,
    org: Organization,
    enrol: LoanSubventionEnrollment,
) -> SubventionClaim:
    claim = await scalar(
        session,
        select(SubventionClaim).where(
            SubventionClaim.organization_id == org.id,
            SubventionClaim.claim_reference == CLAIM_REFERENCE,
        ),
    )
    if claim:
        return claim
    claim = SubventionClaim(
        organization_id=org.id,
        enrollment_id=enrol.id,
        claim_reference=CLAIM_REFERENCE,
        period_start=date(2026, 4, 1),
        period_end=date(2026, 6, 30),
        claim_frequency=ClaimFrequency.QUARTERLY.value,
        interest_paid_in_period=money("6875000"),
        applicable_subvention_amount=money("206250"),
        status=SubventionClaimStatus.DRAFT.value,
        documents=[
            {
                "name": "E2E IIF claim worksheet",
                "path": "/e2e/iif/claim-workbook.pdf",
                "uploaded_at": datetime.now(UTC).isoformat(),
            }
        ],
    )
    session.add(claim)
    await session.flush()
    return claim


async def seed() -> None:
    async with async_session_factory() as session:
        org = await scalar(
            session,
            select(Organization).where(Organization.code == SEED_ORG_CODE),
        )
        if not org:
            raise SystemExit(
                f"E2E organisation with code {SEED_ORG_CODE!r} not found — "
                f"run backend/scripts/seed_e2e.sh first.",
            )

        entity = await ensure_entity(session, org)
        product = await ensure_product(session, org)
        app = await ensure_application(session, org, entity, product)
        sanction = await ensure_sanction(session, org, app, entity, product)
        account = await ensure_loan_account(session, org, sanction, entity, product)
        await ensure_disbursement(session, account)
        # NOTE: `ensure_receipt` is intentionally skipped — the Python enum
        # `lending.enums.ReceiptStatus` (ALLOCATED / REVERSED / BOUNCED) does not
        # match the Postgres `receiptstatus` enum type seeded from
        # `sales_invoice.py::ReceiptStatus` (UNRECEIVED / PARTIALLY_RECEIVED /
        # RECEIVED). Same family of duplicate-enum drift as the BalanceType
        # fix (E2E_BOOTSTRAP_FIXES #6). The IIF claim report endpoint renders
        # a valid XLSX / PDF with an empty repayment section, which is what
        # the live-export test asserts. Backend fix is tracked separately.
        scheme = await ensure_scheme(session, org)
        enrol = await ensure_enrollment(session, org, account, scheme)
        claim = await ensure_claim(session, org, enrol)
        await session.commit()

        print(f"==> E2E IIF chain seeded under org {org.code} ({org.id})")
        print(f"    Entity:        {entity.entity_code} ({entity.id})")
        print(f"    Loan account:  {account.loan_account_number} ({account.id})")
        print(f"    Enrollment:    {enrol.id}")
        print(f"    Claim:         {claim.claim_reference} ({claim.id})")


if __name__ == "__main__":
    asyncio.run(seed())

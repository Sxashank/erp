#!/usr/bin/env python3
"""Seed and validate a client-demo tenant for admin + borrower portal demos.

This script is intentionally a thin, repeatable wrapper over the manual UAT
lending seed. It creates the demo data needed to show:

- admin login with full access,
- borrower portal login,
- approved/sanctioned corporate loan lifecycle,
- active loan account visible in the portal,
- IIF/subvention enrollment,
- downloadable claim report payloads for CSV, XLSX, and PDF.

Run from repository root:

    cd backend
    python scripts/seed_client_demo.py

Useful options:

    python scripts/seed_client_demo.py --validate-only
    python scripts/seed_client_demo.py --no-reset-password
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import selectinload

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import app.models  # noqa: F401 - register all ORM models
import app.models.lending  # noqa: F401
from app.core.security import verify_password
from app.database import async_session_factory
from app.models.auth.user import User
from app.models.lending.application import LoanApplication
from app.models.lending.enums import ApplicationStage, ApplicationStatus, LoanAccountStatus
from app.models.lending.iif.application_funding_source import ApplicationFundingSource
from app.models.lending.iif.application_lender_loan import ApplicationLenderLoan
from app.models.lending.iif.loan_subvention_enrollment import LoanSubventionEnrollment
from app.models.lending.iif.subvention_claim import SubventionClaim
from app.models.lending.loan_account import LoanAccount
from app.models.masters.organization import Organization
from app.models.portal.enums import PortalRegistrationStatus, PortalUserStatus
from app.models.portal.portal_user import PortalUser
from app.models.portal.portal_user_entity import PortalUserEntity
from app.services.lending.iif import SubventionClaimService
from app.services.portal.scheme_rules import derive_scheme_application_status

from app.api.v1.lending.iif.claims import _report_to_csv, _report_to_pdf, _report_to_xlsx
from scripts import seed_uat_manual_lending

ORG_CODE = "SMFC_UAT"
ADMIN_USERNAME = seed_uat_manual_lending.ADMIN_USERNAME
ADMIN_PASSWORD = seed_uat_manual_lending.ADMIN_PASSWORD
PORTAL_EMAIL = seed_uat_manual_lending.PORTAL_EMAIL
PORTAL_PASSWORD = seed_uat_manual_lending.PORTAL_PASSWORD
PORTAL_ADMIN_EMAIL = seed_uat_manual_lending.PORTAL_ADMIN_EMAIL
PORTAL_ADMIN_PASSWORD = seed_uat_manual_lending.PORTAL_ADMIN_PASSWORD
APPLICATION_NUMBER = "UAT/APP/2026/001"
LOAN_ACCOUNT_NUMBER = "UAT-LA-2026-001"
CLAIM_REFERENCE = "UAT/IIF/2026Q1/00001"


@dataclass(frozen=True)
class DemoValidation:
    organization_id: str
    admin_user_id: str
    portal_user_id: str
    portal_admin_user_id: str
    entity_id: str
    application_id: str
    loan_account_id: str
    enrollment_id: str
    claim_id: str
    claim_reference: str
    csv_bytes: int
    xlsx_bytes: int
    pdf_bytes: int


async def _one(session, stmt, label: str):
    value = (await session.execute(stmt)).scalar_one_or_none()
    if value is None:
        raise RuntimeError(f"Demo validation failed: missing {label}")
    return value


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(f"Demo validation failed: {message}")


async def validate_demo() -> DemoValidation:
    """Validate the seeded admin + portal demo chain and report exporters."""

    async with async_session_factory() as session:
        org = await _one(
            session,
            select(Organization).where(Organization.code == ORG_CODE),
            f"organization {ORG_CODE}",
        )
        admin = await _one(
            session,
            select(User).where(User.username == ADMIN_USERNAME),
            f"admin user {ADMIN_USERNAME}",
        )
        _assert(admin.organization_id == org.id, "admin user is not linked to the demo org")
        _assert(verify_password(ADMIN_PASSWORD, admin.password_hash), "admin password is not valid")

        portal_user = await _one(
            session,
            select(PortalUser).where(
                PortalUser.organization_id == org.id,
                PortalUser.email == PORTAL_EMAIL,
            ),
            f"portal user {PORTAL_EMAIL}",
        )
        _assert(
            verify_password(PORTAL_PASSWORD, portal_user.password_hash or ""),
            "portal password is not valid",
        )
        _assert(portal_user.status == PortalUserStatus.ACTIVE, "portal user is not ACTIVE")
        _assert(
            portal_user.registration_status == PortalRegistrationStatus.ACTIVE,
            "portal registration is not approved/ACTIVE",
        )

        portal_admin = await _one(
            session,
            select(PortalUser).where(
                PortalUser.organization_id == org.id,
                PortalUser.email == PORTAL_ADMIN_EMAIL,
            ),
            f"portal admin user {PORTAL_ADMIN_EMAIL}",
        )
        _assert(
            verify_password(PORTAL_ADMIN_PASSWORD, portal_admin.password_hash or ""),
            "portal admin password is not valid",
        )
        _assert(portal_admin.status == PortalUserStatus.ACTIVE, "portal admin user is not ACTIVE")
        _assert(
            portal_admin.registration_status == PortalRegistrationStatus.ACTIVE,
            "portal admin registration is not ACTIVE",
        )

        link = await _one(
            session,
            select(PortalUserEntity).where(
                PortalUserEntity.portal_user_id == portal_user.id,
                PortalUserEntity.organization_id == org.id,
                PortalUserEntity.is_link_active.is_(True),
                PortalUserEntity.deleted_at.is_(None),
            ),
            "active portal-user/entity link",
        )

        application = await _one(
            session,
            select(LoanApplication).where(
                LoanApplication.organization_id == org.id,
                LoanApplication.application_number == APPLICATION_NUMBER,
            ),
            f"loan application {APPLICATION_NUMBER}",
        )
        _assert(
            application.entity_id == link.entity_id, "application is not linked to portal entity"
        )
        _assert(application.status == ApplicationStatus.SANCTIONED, "application is not sanctioned")
        _assert(
            application.stage in {ApplicationStage.SANCTION, ApplicationStage.DISBURSED},
            "application is not in an approved/disbursed stage",
        )
        scheme_status = derive_scheme_application_status(
            application.status,
            application.stage,
            application.extra_data,
        )
        _assert(
            scheme_status in {"APPROVED", "CLAIM_OPEN"},
            f"portal-facing application status is {scheme_status}, expected approved/claim-open",
        )
        funding_rows = list(
            (
                await session.execute(
                    select(ApplicationFundingSource).where(
                        ApplicationFundingSource.organization_id == org.id,
                        ApplicationFundingSource.application_id == application.id,
                        ApplicationFundingSource.deleted_at.is_(None),
                    )
                )
            )
            .scalars()
            .all()
        )
        lender_loan_rows = list(
            (
                await session.execute(
                    select(ApplicationLenderLoan).where(
                        ApplicationLenderLoan.organization_id == org.id,
                        ApplicationLenderLoan.application_id == application.id,
                        ApplicationLenderLoan.deleted_at.is_(None),
                    )
                )
            )
            .scalars()
            .all()
        )
        _assert(funding_rows, "application has no IIF project funding-source rows")
        _assert(lender_loan_rows, "application has no tagged lender loan rows")
        _assert(
            sum((row.loan_amount for row in lender_loan_rows), start=0)
            == application.requested_amount,
            "tagged lender loan total does not match requested amount",
        )

        loan = await _one(
            session,
            select(LoanAccount).where(
                LoanAccount.organization_id == org.id,
                LoanAccount.loan_account_number == LOAN_ACCOUNT_NUMBER,
                LoanAccount.entity_id == link.entity_id,
            ),
            f"loan account {LOAN_ACCOUNT_NUMBER}",
        )
        _assert(loan.status == LoanAccountStatus.ACTIVE, "loan account is not ACTIVE")
        _assert(loan.total_disbursed_amount > 0, "loan has no disbursement amount")

        enrollment = await _one(
            session,
            select(LoanSubventionEnrollment)
            .options(selectinload(LoanSubventionEnrollment.scheme))
            .where(
                LoanSubventionEnrollment.organization_id == org.id,
                LoanSubventionEnrollment.loan_account_id == loan.id,
                LoanSubventionEnrollment.deleted_at.is_(None),
            ),
            "IIF/subvention enrollment",
        )
        _assert(enrollment.scheme is not None, "subvention enrollment has no scheme")

        claim = await _one(
            session,
            select(SubventionClaim).where(
                SubventionClaim.organization_id == org.id,
                SubventionClaim.enrollment_id == enrollment.id,
                SubventionClaim.claim_reference == CLAIM_REFERENCE,
            ),
            f"IIF claim {CLAIM_REFERENCE}",
        )

        report = await SubventionClaimService(session).generate_claim_report(org.id, claim.id)
        csv_bytes = len(_report_to_csv(report).encode("utf-8"))
        xlsx_bytes = len(_report_to_xlsx(report))
        pdf_bytes = len(_report_to_pdf(report))
        _assert(csv_bytes > 100, "CSV claim report is unexpectedly empty")
        _assert(xlsx_bytes > 100, "XLSX claim report is unexpectedly empty")
        _assert(pdf_bytes > 100, "PDF claim report is unexpectedly empty")

        return DemoValidation(
            organization_id=str(org.id),
            admin_user_id=str(admin.id),
            portal_user_id=str(portal_user.id),
            portal_admin_user_id=str(portal_admin.id),
            entity_id=str(link.entity_id),
            application_id=str(application.id),
            loan_account_id=str(loan.id),
            enrollment_id=str(enrollment.id),
            claim_id=str(claim.id),
            claim_reference=claim.claim_reference,
            csv_bytes=csv_bytes,
            xlsx_bytes=xlsx_bytes,
            pdf_bytes=pdf_bytes,
        )


async def seed_and_validate(*, reset_password: bool, validate_only: bool) -> DemoValidation:
    if not validate_only:
        await seed_uat_manual_lending.seed(reset_password=reset_password)
    return await validate_demo()


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--no-reset-password",
        action="store_true",
        help="Keep existing seeded admin/portal passwords unchanged.",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Skip seeding and only validate the existing demo data.",
    )
    return parser.parse_args(argv)


def print_summary(result: DemoValidation) -> None:
    print("\nClient demo seed validation passed.")
    print(f"Organization: {ORG_CODE} ({result.organization_id})")
    print(f"Admin login: {ADMIN_USERNAME} / {ADMIN_PASSWORD}")
    print(f"Portal login: {PORTAL_EMAIL} / {PORTAL_PASSWORD}")
    print(f"Portal admin login: {PORTAL_ADMIN_EMAIL} / {PORTAL_ADMIN_PASSWORD}")
    print(f"Portal entity id: {result.entity_id}")
    print(f"Approved application: {APPLICATION_NUMBER} ({result.application_id})")
    print(f"Active loan account: {LOAN_ACCOUNT_NUMBER} ({result.loan_account_id})")
    print(f"IIF enrollment: {result.enrollment_id}")
    print(f"IIF claim: {result.claim_reference} ({result.claim_id})")
    print(
        "Report export validation: "
        f"CSV {result.csv_bytes} bytes, "
        f"XLSX {result.xlsx_bytes} bytes, "
        f"PDF {result.pdf_bytes} bytes"
    )
    print("\nDemo routes:")
    print("  Admin:  /admin/lending/lms/accounts")
    print("  Admin:  /admin/lending/iif/claims")
    print("  Portal: /portal/loans")
    print("  Portal: /portal/claims")


async def main(argv: Sequence[str]) -> None:
    args = parse_args(argv)
    result = await seed_and_validate(
        reset_password=not args.no_reset_password,
        validate_only=args.validate_only,
    )
    print_summary(result)


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))

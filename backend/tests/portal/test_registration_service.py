from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lending.entity import Entity
from app.models.lending.enums import DayCountConvention, EntityType
from app.models.lending.loan_account import LoanAccount
from app.models.portal.enums import PortalRegistrationStatus
from app.models.portal.portal_user import PortalOTP, PortalUser
from app.models.portal.portal_user_entity import PortalUserEntity
from app.schemas.portal.registration import RegisterRequest
from app.services.notification.communication_service import Channel, DispatchResult, DispatchStatus
from app.services.portal.registration_service import PortalRegistrationService


@pytest.fixture
async def borrower_entity(
    session: AsyncSession,
    test_organization,
) -> Entity:
    entity = Entity(
        id=uuid4(),
        organization_id=test_organization.id,
        entity_code="ENT/2026/00001",
        entity_type=EntityType.CORPORATE,
        legal_name="Acme Maritime Limited",
        trade_name="Acme Maritime",
        pan="ABCDE1234F",
        gstin="27ABCDE1234F1Z5",
        cin="L12345MH2020PLC123456",
        primary_email="ops@acmemaritime.example",
        primary_phone="+919876543210",
    )
    session.add(entity)
    await session.commit()
    await session.refresh(entity)
    return entity


@pytest.fixture
async def borrower_loan(
    session: AsyncSession,
    test_organization,
    borrower_entity: Entity,
) -> LoanAccount:
    loan = LoanAccount(
        id=uuid4(),
        organization_id=test_organization.id,
        sanction_id=uuid4(),
        entity_id=borrower_entity.id,
        product_id=uuid4(),
        loan_account_number="SMFC/LA/2026/00001",
        account_open_date=date(2026, 4, 1),
        sanctioned_amount=Decimal("2500000.00"),
        tenure_months=24,
        interest_type="FIXED",
        current_interest_rate=Decimal("11.50"),
        repayment_frequency="MONTHLY",
        repayment_mode="EMI",
        day_count_convention=DayCountConvention.ACT_365,
        installment_day=5,
        undisbursed_amount=Decimal("0.00"),
    )
    session.add(loan)
    await session.commit()
    await session.refresh(loan)
    return loan


@pytest.fixture(autouse=True)
def mocked_sms(monkeypatch):
    async def _send(**_kwargs):
        return DispatchResult(
            channel=Channel.SMS,
            status=DispatchStatus.MOCKED,
            provider_message_id="test-otp",
        )

    monkeypatch.setattr("app.services.portal.auth_service.communication_service.send", _send)


async def _latest_otp(session: AsyncSession, mobile: str) -> PortalOTP:
    stmt = (
        select(PortalOTP)
        .where(PortalOTP.mobile == mobile)
        .order_by(PortalOTP.generated_at.desc())
        .limit(1)
    )
    otp = (await session.execute(stmt)).scalar_one()
    return otp


@pytest.mark.asyncio
async def test_existing_loan_registration_auto_approves_and_links_entity(
    session: AsyncSession,
    borrower_entity: Entity,
    borrower_loan: LoanAccount,
) -> None:
    service = PortalRegistrationService(session)
    payload = RegisterRequest(
        loan_account_number=borrower_loan.loan_account_number,
        sanctioned_amount=borrower_loan.sanctioned_amount,
        authorized_signatory_name="Operations Desk",
        mobile="+919876543210",
        email="ops@acmemaritime.example",
    )

    response = await service.register(payload)
    otp = await _latest_otp(session, payload.mobile)
    verify = await service.verify_otp(response.registration_reference, otp.otp_code)

    assert verify.registration_status == "ACTIVE"
    assert verify.auto_approved is True
    assert verify.linked_entity_ids == [borrower_entity.id]

    portal_user = (
        await session.execute(
            select(PortalUser).where(
                PortalUser.registration_reference == response.registration_reference
            )
        )
    ).scalar_one()
    assert portal_user.registration_status == PortalRegistrationStatus.ACTIVE
    assert portal_user.organization_id == borrower_entity.organization_id

    link = (
        await session.execute(
            select(PortalUserEntity).where(PortalUserEntity.portal_user_id == portal_user.id)
        )
    ).scalar_one()
    assert link.entity_id == borrower_entity.id


@pytest.mark.asyncio
async def test_existing_loan_registration_with_wrong_amount_stays_pending(
    session: AsyncSession,
    borrower_loan: LoanAccount,
) -> None:
    service = PortalRegistrationService(session)
    payload = RegisterRequest(
        loan_account_number=borrower_loan.loan_account_number,
        sanctioned_amount=Decimal("2499999.99"),
        authorized_signatory_name="Operations Desk",
        mobile="+919876543210",
        email="ops@acmemaritime.example",
    )

    response = await service.register(payload)
    otp = await _latest_otp(session, payload.mobile)
    verify = await service.verify_otp(response.registration_reference, otp.otp_code)

    assert verify.registration_status == "PENDING_APPROVAL"
    assert verify.auto_approved is False
    assert verify.linked_entity_ids == []


@pytest.mark.asyncio
async def test_same_mobile_can_hold_distinct_pending_registrations_when_loan_differs(
    session: AsyncSession,
    borrower_loan: LoanAccount,
) -> None:
    service = PortalRegistrationService(session)

    first = await service.register(
        RegisterRequest(
            loan_account_number=borrower_loan.loan_account_number,
            sanctioned_amount=borrower_loan.sanctioned_amount,
            authorized_signatory_name="Operations Desk",
            mobile="+919876543210",
            email="ops@acmemaritime.example",
        )
    )
    second = await service.register(
        RegisterRequest(
            loan_account_number="SMFC/LA/2026/99999",
            sanctioned_amount=Decimal("1500000.00"),
            authorized_signatory_name="Operations Desk",
            mobile="+919876543210",
            email="ops@acmemaritime.example",
        )
    )

    refs = (
        await session.execute(
            select(PortalUser.registration_reference).where(
                PortalUser.mobile == "+919876543210",
                PortalUser.deleted_at.is_(None),
            )
        )
    ).scalars().all()

    assert first.registration_reference != second.registration_reference
    assert len(refs) == 2

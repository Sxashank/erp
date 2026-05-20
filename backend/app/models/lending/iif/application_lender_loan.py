"""Per-lender loan details for scheme loan tagging applications."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Date, DateTime, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class ApplicationLenderLoan(BaseModel):
    """One lender loan facility tagged to an IIF application."""

    __tablename__ = "los_application_lender_loan"
    __table_args__ = (
        Index("ix_los_application_lender_loan_org", "organization_id"),
        Index("ix_los_application_lender_loan_app", "application_id"),
        Index("ix_los_application_lender_loan_status", "lender_validation_status"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
    )
    application_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("los_loan_application.id", ondelete="CASCADE"),
        nullable=False,
    )

    loan_type: Mapped[str] = mapped_column(String(80), nullable=False)
    loan_amount: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    lender_name: Mapped[str] = mapped_column(String(200), nullable=False)
    lender_category: Mapped[str | None] = mapped_column(String(80), nullable=True)
    lender_contact: Mapped[str | None] = mapped_column(String(50), nullable=True)
    lender_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    lender_address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    lender_state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    lender_district: Mapped[str | None] = mapped_column(String(100), nullable=True)
    lender_pincode: Mapped[str | None] = mapped_column(String(20), nullable=True)

    sanction_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    sanction_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    interest_rate_percent: Mapped[Decimal | None] = mapped_column(Numeric(9, 4), nullable=True)
    emi_periodicity: Mapped[str | None] = mapped_column(String(30), nullable=True)
    interest_debiting_periodicity: Mapped[str | None] = mapped_column(String(30), nullable=True)
    loan_account_number: Mapped[str | None] = mapped_column(String(80), nullable=True)
    ifsc_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    security_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    disbursement_call_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    emi_amount: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    emi_due_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    lender_validation_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="PENDING",
    )
    lender_validation_remarks: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    lender_validated_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("portal_user.id", ondelete="SET NULL"),
        nullable=True,
    )
    lender_validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

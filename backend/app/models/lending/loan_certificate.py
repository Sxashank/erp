"""LoanCertificate — every certificate issued to a borrower.

Each row links a DMS document to the loan (or application) that produced
it, captures issuance metadata, and (for KFS) the borrower ack timestamp.
Each issuance emits a `CERTIFICATE_ISSUED` lifecycle event.
"""

from __future__ import annotations

from datetime import date as date_type, datetime
from enum import Enum as PyEnum
from typing import Optional
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class CertificateType(str, PyEnum):
    KFS = "KFS"
    SANCTION_LETTER = "SANCTION_LETTER"
    WELCOME_LETTER = "WELCOME_LETTER"
    INTEREST_CERT = "INTEREST_CERT"
    PROVISIONAL_INTEREST_CERT = "PROVISIONAL_INTEREST_CERT"
    PRINCIPAL_PAID_CERT = "PRINCIPAL_PAID_CERT"
    STATEMENT_OF_ACCOUNT = "STATEMENT_OF_ACCOUNT"
    NDC = "NDC"
    FORECLOSURE_LETTER = "FORECLOSURE_LETTER"
    BALANCE_CONFIRMATION = "BALANCE_CONFIRMATION"
    CHARGE_RELEASE_LETTER = "CHARGE_RELEASE_LETTER"
    ANNUAL_LOAN_STATEMENT = "ANNUAL_LOAN_STATEMENT"
    RATE_REVISION_INTIMATION = "RATE_REVISION_INTIMATION"
    DEMAND_NOTICE = "DEMAND_NOTICE"
    SARFAESI_13_2_NOTICE = "SARFAESI_13_2_NOTICE"
    OTS_LETTER = "OTS_LETTER"
    RESTRUCTURE_ADDENDUM = "RESTRUCTURE_ADDENDUM"
    WILFUL_DEFAULTER_NOTICE = "WILFUL_DEFAULTER_NOTICE"


class LoanCertificate(BaseModel):
    __tablename__ = "txn_loan_certificate"
    __table_args__ = (
        Index("ix_txn_loan_certificate_loan", "loan_account_id"),
        Index("ix_txn_loan_certificate_application", "application_id"),
        Index("ix_txn_loan_certificate_type", "certificate_type"),
        Index("ix_txn_loan_certificate_issued_at", "issued_at"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
    )

    # One of loan_account_id or application_id will be set; KFS is
    # typically application-only (before LoanAccount exists), interest
    # cert etc. are loan-only.
    loan_account_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lms_loan_account.id", ondelete="SET NULL"),
        nullable=True,
    )
    application_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("los_loan_application.id", ondelete="SET NULL"),
        nullable=True,
    )
    sanction_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("los_loan_sanction.id", ondelete="SET NULL"),
        nullable=True,
    )

    certificate_type: Mapped[CertificateType] = mapped_column(
        SAEnum(CertificateType, name="loan_certificate_type"),
        nullable=False,
    )
    certificate_number: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
        comment="Human-readable id, e.g. SMFC/CERT/KFS/2526/0001",
    )

    dms_document_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("dms_document.id", ondelete="SET NULL"),
        nullable=True,
        comment="DMS row where the PDF lives.",
    )
    file_path: Mapped[Optional[str]] = mapped_column(String(1000))
    file_size: Mapped[Optional[int]] = mapped_column()

    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    issued_by_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
    )
    issued_to_portal_user_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("portal_user.id", ondelete="SET NULL"),
    )

    # For period-bounded certs (interest cert, statement)
    period_from: Mapped[Optional[date_type]] = mapped_column(Date)
    period_to: Mapped[Optional[date_type]] = mapped_column(Date)
    financial_year: Mapped[Optional[str]] = mapped_column(String(10))

    # KFS ack tracking — borrower must acknowledge before acceptance
    requires_acknowledgement: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_acknowledged: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    acknowledged_by_portal_user_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("portal_user.id", ondelete="SET NULL"),
    )

    template_code: Mapped[Optional[str]] = mapped_column(String(60))
    template_version: Mapped[Optional[int]] = mapped_column()

    remarks: Mapped[Optional[str]] = mapped_column(Text)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<LoanCertificate {self.certificate_type.value} " f"{self.certificate_number}>"

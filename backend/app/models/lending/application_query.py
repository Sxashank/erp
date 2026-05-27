"""LosApplicationQuery — formal model for the lender ↔ borrower bounce.

Today the platform has `ApplicationStatus.ADDITIONAL_INFO_REQUIRED` defined
but no service path to it and no borrower-facing surface. This table is the
formal mechanism: lender raises a query (with required_attachments + SLA),
borrower responds via portal (text + attachments), lender resolves (or
re-queries with a new row).

Every state transition on this table emits a `LoanLifecycleEvent` so the
unified timeline shows the whole back-and-forth.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional
from uuid import UUID

from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class ApplicationQueryStatus(str, PyEnum):
    RAISED = "RAISED"  # lender created; borrower has not yet responded
    RESPONDED = "RESPONDED"  # borrower replied; awaiting lender review
    RE_REVIEW = "RE_REVIEW"  # lender re-reviewing (alias of RESPONDED post-look)
    RESOLVED = "RESOLVED"  # lender accepted the response; query closed
    LAPSED = "LAPSED"  # SLA expired without borrower response


class ApplicationQueryRaisedReason(str, PyEnum):
    """Optional bucket for raising. Adding a new reason is just a string in
    payload — this enum captures common cases only for filtering."""

    MISSING_DOCUMENT = "MISSING_DOCUMENT"
    DOCUMENT_CLARIFICATION = "DOCUMENT_CLARIFICATION"
    FINANCIAL_QUERY = "FINANCIAL_QUERY"
    KYC_QUERY = "KYC_QUERY"
    CREDIT_QUERY = "CREDIT_QUERY"
    LEGAL_QUERY = "LEGAL_QUERY"
    SECURITY_QUERY = "SECURITY_QUERY"
    OTHER = "OTHER"


class LosApplicationQuery(BaseModel):
    """One row per query raised on a loan application."""

    __tablename__ = "los_application_query"
    __table_args__ = (
        Index("ix_los_application_query_app_status", "application_id", "status"),
        Index("ix_los_application_query_sla_due", "sla_due_at"),
        Index("ix_los_application_query_org", "organization_id"),
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
    query_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Sequential per application — Q1, Q2, etc. UI-friendly.",
    )

    # Raised side
    raised_by_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="RESTRICT"),
        nullable=False,
    )
    raised_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    raised_reason_code: Mapped[ApplicationQueryRaisedReason] = mapped_column(
        SAEnum(ApplicationQueryRaisedReason, name="application_query_reason"),
        nullable=False,
        default=ApplicationQueryRaisedReason.OTHER,
    )
    query_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    required_attachments: Mapped[list[str]] = mapped_column(
        ARRAY(String(80)),
        nullable=False,
        default=list,
        comment="Document codes (from mst_checklist_item_catalog) the lender requires uploaded.",
    )
    sla_due_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Response side
    status: Mapped[ApplicationQueryStatus] = mapped_column(
        SAEnum(ApplicationQueryStatus, name="application_query_status"),
        nullable=False,
        default=ApplicationQueryStatus.RAISED,
    )
    responded_by_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("portal_user.id", ondelete="SET NULL"),
        nullable=True,
        comment="Portal user (borrower entity) who replied.",
    )
    responded_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    response_text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    response_attachments: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        comment="Array of {dms_document_id, file_name} uploaded by borrower.",
    )

    # Resolution side
    resolved_by_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    resolution_remark: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<LosApplicationQuery app={self.application_id} "
            f"Q{self.query_number} {self.status.value}>"
        )

"""IIF scheme fund ledger.

Records manual-first fund movements under a subvention scheme: Government
allocation, claim release, service charge, incidental expense and carry-forward.
No external bank integration is implied; references are manually entered.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class SubventionFundTransaction(BaseModel):
    """One manually recorded IIF fund movement."""

    __tablename__ = "txn_subvention_fund_transaction"
    __table_args__ = (
        Index("ix_txn_sft_org", "organization_id"),
        Index("ix_txn_sft_scheme", "scheme_id"),
        Index("ix_txn_sft_claim", "claim_id"),
        Index("ix_txn_sft_date", "transaction_date"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
    )
    scheme_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_subvention_scheme.id", ondelete="RESTRICT"),
        nullable=False,
    )
    claim_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("txn_subvention_claim.id", ondelete="SET NULL"),
        nullable=True,
    )

    transaction_type: Mapped[str] = mapped_column(String(40), nullable=False)
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    reference_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

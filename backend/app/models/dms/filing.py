"""DMS filing rules for generated and uploaded business documents."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class DocumentFilingRule(BaseModel):
    """Governed path rule for where documents should be filed in DMS."""

    __tablename__ = "dms_filing_rule"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "module",
            "document_type",
            "entity_type",
            name="uq_dms_filing_rule_scope",
        ),
        Index("ix_dms_filing_rule_lookup", "organization_id", "module", "document_type"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    module: Mapped[str] = mapped_column(String(50), nullable=False)
    document_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    path_template: Mapped[str] = mapped_column(String(2000), nullable=False)
    access_level: Mapped[str] = mapped_column(String(50), nullable=False, default="organization")
    retention_policy: Mapped[str | None] = mapped_column(String(100))
    portal_visible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    default_tags: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    description: Mapped[str | None] = mapped_column(Text)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

"""DMS Tag models."""

from typing import Optional
from uuid import UUID

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class DMSTag(BaseModel):
    """Tags for document categorization."""

    __tablename__ = "dms_tag"

    # Organization scope
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Tag information
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="URL-friendly version of name",
    )
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Display settings
    color: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, comment="Hex color code")
    icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Category grouping
    category: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Group tags by category",
    )

    # Usage count
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    organization = relationship("Organization", lazy="selectin")
    document_tags = relationship("DMSDocumentTag", back_populates="tag", lazy="dynamic")


class DMSDocumentTag(BaseModel):
    """Many-to-many relationship between documents and tags."""

    __tablename__ = "dms_document_tag"

    # Document reference
    document_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("dms_document.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Tag reference
    tag_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("dms_tag.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    document = relationship("DMSDocument", back_populates="tags")
    tag = relationship("DMSTag", back_populates="document_tags")

"""Designation master model."""

from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.core.constants import EntityStatus

if TYPE_CHECKING:
    from app.models.masters.department import Department


class Designation(BaseModel):
    """Designation master - job titles and levels."""

    __tablename__ = "mst_designation"

    # Basic info
    code: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    short_name: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Department (optional - designation can be org-wide)
    department_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_department.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Level & Hierarchy
    level: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )
    reporting_to_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_designation.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Approval Limits
    approval_limit: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2),
        nullable=True,
    )  # Maximum amount this designation can approve

    # Requirements
    min_experience_years: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    min_qualification: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
    )

    # Job details
    job_description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    responsibilities: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        default=EntityStatus.ACTIVE.value,
        nullable=False,
        index=True,
    )

    # Relationships
    department: Mapped[Optional["Department"]] = relationship(
        "Department",
        back_populates="designations",
    )
    reporting_to: Mapped[Optional["Designation"]] = relationship(
        "Designation",
        remote_side="Designation.id",
        back_populates="reports",
    )
    reports: Mapped[list["Designation"]] = relationship(
        "Designation",
        back_populates="reporting_to",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Designation(code={self.code}, name={self.name})>"

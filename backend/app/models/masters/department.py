"""Department master model."""

from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.core.constants import EntityStatus

if TYPE_CHECKING:
    from app.models.masters.organization import Organization
    from app.models.masters.designation import Designation
    from app.models.auth.user import User


class Department(BaseModel):
    """Department master - organizational cost centers."""

    __tablename__ = "mst_department"

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

    # Organization
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Hierarchy
    parent_dept_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_department.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    level: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )
    path: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        index=True,
    )

    # Cost Center
    cost_center_code: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )

    # Department Head (FK to User)
    head_user_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Contact (legacy - kept for backward compatibility)
    head_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(20),
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
    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="departments",
    )
    parent_dept: Mapped[Optional["Department"]] = relationship(
        "Department",
        remote_side="Department.id",
        back_populates="child_depts",
    )
    child_depts: Mapped[List["Department"]] = relationship(
        "Department",
        back_populates="parent_dept",
        lazy="selectin",
    )
    designations: Mapped[List["Designation"]] = relationship(
        "Designation",
        back_populates="department",
        lazy="selectin",
    )
    head_user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[head_user_id],
    )

    def __repr__(self) -> str:
        return f"<Department(code={self.code}, name={self.name})>"

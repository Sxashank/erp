"""Cost Center model for expense tracking and allocation."""

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from sqlalchemy import Date, Numeric, String, Text, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.masters.organization import Organization


class CostCenter(BaseModel):
    """
    Cost Center for expense tracking and allocation.

    Supports hierarchical structure for nested cost centers.
    """

    __tablename__ = "mst_cost_center"

    # Organization
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Cost center identification
    code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="Unique code within organization",
    )
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Hierarchy
    parent_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_cost_center.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Parent cost center for hierarchy",
    )
    level: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
        comment="Hierarchy level (0 = root)",
    )
    path: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Full path for hierarchy queries (e.g., '/root/dept/subdept')",
    )

    # Classification
    category: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Category: DEPARTMENT, PROJECT, BRANCH, PRODUCT_LINE, etc.",
    )
    cost_type: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Type: DIRECT, INDIRECT, OVERHEAD",
    )

    # Budget control
    has_budget: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether budget tracking is enabled",
    )
    annual_budget: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Annual budget amount",
    )
    budget_variance_threshold: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("10.00"),
        comment="Variance percentage to trigger alerts",
    )

    # Allocation settings
    is_allocatable: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Can expenses be allocated to this cost center",
    )
    allocation_basis: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Basis for cost allocation: DIRECT, HEADCOUNT, AREA, REVENUE, etc.",
    )
    allocation_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("100.00"),
        comment="Default allocation percentage",
    )

    # Responsible person
    manager_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        comment="Manager responsible for this cost center",
    )
    manager_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
    )

    # Validity period
    effective_from: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        default=date.today,
    )
    effective_to: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="End date (null = currently active)",
    )

    # GL account mapping
    default_expense_account_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        comment="Default expense account for this cost center",
    )

    # External reference
    external_code: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="External system reference code",
    )

    # Additional data
    extra_data: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        lazy="selectin",
    )
    parent: Mapped[Optional["CostCenter"]] = relationship(
        "CostCenter",
        remote_side="CostCenter.id",
        lazy="selectin",
    )
    children: Mapped[List["CostCenter"]] = relationship(
        "CostCenter",
        back_populates="parent",
        lazy="selectin",
    )

    @property
    def is_leaf(self) -> bool:
        """Check if this is a leaf node (no children)."""
        return len(self.children) == 0 if self.children else True

    @property
    def full_path(self) -> str:
        """Get full hierarchical path."""
        if self.path:
            return self.path
        return f"/{self.code}"

    def __repr__(self) -> str:
        return f"<CostCenter(code={self.code}, name={self.name})>"

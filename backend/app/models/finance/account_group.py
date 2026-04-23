"""Account Group model for Chart of Accounts hierarchy."""

from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Integer, String, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.core.constants import AccountNature

if TYPE_CHECKING:
    from app.models.masters.organization import Organization
    from app.models.finance.account import Account


class AccountGroup(BaseModel):
    """Account Group for Chart of Accounts structure."""

    __tablename__ = "mst_account_group"

    code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Group code e.g. ASSETS, CURRENT_ASSETS",
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Group name e.g. Current Assets",
    )
    nature: Mapped[AccountNature] = mapped_column(
        SQLEnum(AccountNature),
        nullable=False,
        comment="Account nature - ASSETS, LIABILITIES, INCOME, EXPENSES, EQUITY",
    )
    parent_group_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_account_group.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Parent account group for hierarchy",
    )
    level: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Hierarchy level (0 for root)",
    )
    path: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Materialized path for hierarchy e.g. /uuid1/uuid2/",
    )
    sequence: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Display order within parent",
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    is_system: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="System-defined group (cannot be deleted)",
    )
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="account_groups",
        lazy="selectin",
    )
    parent_group: Mapped[Optional["AccountGroup"]] = relationship(
        "AccountGroup",
        remote_side="AccountGroup.id",
        back_populates="child_groups",
        lazy="selectin",
    )
    child_groups: Mapped[List["AccountGroup"]] = relationship(
        "AccountGroup",
        back_populates="parent_group",
        lazy="selectin",
    )
    accounts: Mapped[List["Account"]] = relationship(
        "Account",
        back_populates="account_group",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<AccountGroup(code={self.code}, name={self.name})>"

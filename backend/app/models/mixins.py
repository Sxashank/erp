"""Additional model mixins for common functionality."""

from typing import Optional
from uuid import UUID

from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, declared_attr


class CodeNameMixin:
    """Mixin for entities with code and name fields."""

    @declared_attr
    def code(cls) -> Mapped[str]:
        return mapped_column(
            String(50),
            unique=True,
            nullable=False,
            index=True,
        )

    @declared_attr
    def name(cls) -> Mapped[str]:
        return mapped_column(
            String(200),
            nullable=False,
        )

    @declared_attr
    def description(cls) -> Mapped[Optional[str]]:
        return mapped_column(
            Text,
            nullable=True,
        )


class HierarchyMixin:
    """Mixin for hierarchical entities (with parent-child relationships)."""

    # Note: The actual parent_id foreign key should be defined in the child class
    # pointing to the same table

    @declared_attr
    def level(cls) -> Mapped[int]:
        return mapped_column(
            default=1,
            nullable=False,
        )

    @declared_attr
    def path(cls) -> Mapped[Optional[str]]:
        """Materialized path for efficient tree queries (e.g., '/1/2/3/')."""
        return mapped_column(
            String(500),
            nullable=True,
            index=True,
        )


class AddressMixin:
    """Mixin for address fields."""

    @declared_attr
    def address_line1(cls) -> Mapped[Optional[str]]:
        return mapped_column(String(255), nullable=True)

    @declared_attr
    def address_line2(cls) -> Mapped[Optional[str]]:
        return mapped_column(String(255), nullable=True)

    @declared_attr
    def city(cls) -> Mapped[Optional[str]]:
        return mapped_column(String(100), nullable=True)

    @declared_attr
    def district(cls) -> Mapped[Optional[str]]:
        return mapped_column(String(100), nullable=True)

    @declared_attr
    def state_code(cls) -> Mapped[Optional[str]]:
        return mapped_column(String(2), nullable=True)

    @declared_attr
    def pincode(cls) -> Mapped[Optional[str]]:
        return mapped_column(String(10), nullable=True)

    @declared_attr
    def country(cls) -> Mapped[str]:
        return mapped_column(String(50), default="India", nullable=False)


class ContactMixin:
    """Mixin for contact information fields."""

    @declared_attr
    def phone(cls) -> Mapped[Optional[str]]:
        return mapped_column(String(20), nullable=True)

    @declared_attr
    def mobile(cls) -> Mapped[Optional[str]]:
        return mapped_column(String(20), nullable=True)

    @declared_attr
    def email(cls) -> Mapped[Optional[str]]:
        return mapped_column(String(255), nullable=True)

    @declared_attr
    def website(cls) -> Mapped[Optional[str]]:
        return mapped_column(String(255), nullable=True)

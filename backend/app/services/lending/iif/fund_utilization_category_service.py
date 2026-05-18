"""Fund-utilization category master service.

CRUD over ``mst_fund_utilization_category``. Same tenant-scoping rule
as the scheme service — platform rows (``organization_id IS NULL``)
are read-only; tenant overrides live on their own org row.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
)
from app.models.auth.user import User
from app.models.lending.iif.fund_utilization_category import (
    FundUtilizationCategory,
)
from app.schemas.lending.iif import (
    FundUtilizationCategoryCreate,
    FundUtilizationCategoryUpdate,
)


class FundUtilizationCategoryService:
    """Service for fund-utilization category CRUD."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # =========================================================================
    # Create
    # =========================================================================

    async def create(
        self,
        data: FundUtilizationCategoryCreate,
        current_user: User,
    ) -> FundUtilizationCategory:
        if current_user.organization_id is None:
            raise BadRequestException(
                "Current user has no organization context",
                error_code="MISSING_ORG_CONTEXT",
            )

        # Per-org uniqueness on (scheme_id, code) for active rows.
        existing = await self.session.execute(
            select(FundUtilizationCategory).where(
                FundUtilizationCategory.organization_id == current_user.organization_id,
                FundUtilizationCategory.scheme_id == data.scheme_id,
                FundUtilizationCategory.code == data.code,
                FundUtilizationCategory.deleted_at.is_(None),
            )
        )
        if existing.scalar_one_or_none() is not None:
            raise ConflictException(
                f"Category with code '{data.code}' already exists for this scheme",
                error_code="CATEGORY_CODE_EXISTS",
            )

        cat = FundUtilizationCategory(
            organization_id=current_user.organization_id,
            scheme_id=data.scheme_id,
            code=data.code,
            label=data.label,
            description=data.description,
            sort_order=data.sort_order,
            created_by=current_user.id,
        )
        self.session.add(cat)
        await self.session.flush()
        await self.session.refresh(cat)
        return cat

    # =========================================================================
    # Read
    # =========================================================================

    async def list_categories(
        self,
        organization_id: UUID,
        scheme_id: UUID | None = None,
        include_inactive: bool = False,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[FundUtilizationCategory], int]:
        """List platform + tenant categories. Optionally filter by scheme."""
        where = [
            or_(
                FundUtilizationCategory.organization_id.is_(None),
                FundUtilizationCategory.organization_id == organization_id,
            ),
            FundUtilizationCategory.deleted_at.is_(None),
        ]
        if scheme_id is not None:
            where.append(FundUtilizationCategory.scheme_id == scheme_id)
        if not include_inactive:
            where.append(FundUtilizationCategory.is_active.is_(True))

        count_stmt = select(func.count()).select_from(FundUtilizationCategory).where(*where)
        total = (await self.session.execute(count_stmt)).scalar_one()

        stmt = (
            select(FundUtilizationCategory)
            .where(*where)
            .order_by(
                FundUtilizationCategory.sort_order.asc(),
                FundUtilizationCategory.label.asc(),
            )
            .offset(skip)
            .limit(limit)
        )
        rows = (await self.session.execute(stmt)).scalars().all()
        return list(rows), int(total)

    async def get(self, organization_id: UUID, category_id: UUID) -> FundUtilizationCategory:
        cat = await self.session.get(FundUtilizationCategory, category_id)
        if not cat or cat.deleted_at is not None:
            raise NotFoundException("Category not found", error_code="CATEGORY_NOT_FOUND")
        if cat.organization_id is not None and cat.organization_id != organization_id:
            raise NotFoundException("Category not found", error_code="CATEGORY_NOT_FOUND")
        return cat

    # =========================================================================
    # Update / Delete
    # =========================================================================

    async def update(
        self,
        organization_id: UUID,
        category_id: UUID,
        data: FundUtilizationCategoryUpdate,
        current_user: User,
    ) -> FundUtilizationCategory:
        cat = await self.get(organization_id, category_id)
        if cat.organization_id is None:
            raise BadRequestException(
                "Platform-default categories are read-only",
                error_code="READONLY_PLATFORM_CATEGORY",
            )
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(cat, field, value)
        cat.updated_by = current_user.id
        cat.version = (cat.version or 1) + 1
        await self.session.flush()
        await self.session.refresh(cat)
        return cat

    async def soft_delete(
        self,
        organization_id: UUID,
        category_id: UUID,
        current_user: User,
    ) -> None:
        cat = await self.get(organization_id, category_id)
        if cat.organization_id is None:
            raise BadRequestException(
                "Platform-default categories cannot be deleted",
                error_code="READONLY_PLATFORM_CATEGORY",
            )
        cat.soft_delete(deleted_by=current_user.id)
        await self.session.flush()

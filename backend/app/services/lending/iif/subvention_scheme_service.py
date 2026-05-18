"""Subvention scheme master service.

CRUD over ``mst_subvention_scheme``. The tenant scoping rule:

- Reads return platform-wide rows (``organization_id IS NULL``) AND the
  caller's tenant-owned rows, so a tenant can see the IIF default plus
  any custom overrides they've defined.
- Writes can only target the caller's own tenant — never the
  NULL/platform row. Platform-level seeding is done in alembic.
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
from app.models.lending.iif.subvention_scheme import SubventionScheme
from app.schemas.lending.iif import (
    SubventionSchemeCreate,
    SubventionSchemeUpdate,
)


class SubventionSchemeService:
    """Service for subvention scheme CRUD."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # =========================================================================
    # Create
    # =========================================================================

    async def create(
        self,
        data: SubventionSchemeCreate,
        current_user: User,
    ) -> SubventionScheme:
        """Create a tenant-owned scheme override."""
        if current_user.organization_id is None:
            raise BadRequestException(
                "Current user has no organization context",
                error_code="MISSING_ORG_CONTEXT",
            )

        if data.scheme_end_date < data.scheme_start_date:
            raise BadRequestException(
                "scheme_end_date must be on or after scheme_start_date",
                error_code="INVALID_SCHEME_DATES",
            )

        # Per-org uniqueness on scheme_code (matches the DB unique index).
        existing = await self.session.execute(
            select(SubventionScheme).where(
                SubventionScheme.organization_id == current_user.organization_id,
                SubventionScheme.scheme_code == data.scheme_code,
                SubventionScheme.deleted_at.is_(None),
            )
        )
        if existing.scalar_one_or_none() is not None:
            raise ConflictException(
                f"Scheme with code '{data.scheme_code}' already exists",
                error_code="SCHEME_CODE_EXISTS",
            )

        scheme = SubventionScheme(
            organization_id=current_user.organization_id,
            scheme_code=data.scheme_code,
            scheme_name=data.scheme_name,
            administering_ministry=data.administering_ministry,
            implementing_agency=data.implementing_agency,
            subvention_rate_percent=data.subvention_rate_percent,
            max_subvention_per_beneficiary=data.max_subvention_per_beneficiary,
            scheme_corpus=data.scheme_corpus,
            eligible_loan_types=list(data.eligible_loan_types),
            max_tenure_term_loan_months=data.max_tenure_term_loan_months,
            max_tenure_working_capital_months=data.max_tenure_working_capital_months,
            scheme_start_date=data.scheme_start_date,
            scheme_end_date=data.scheme_end_date,
            eligibility_window_months=data.eligibility_window_months,
            claim_frequency=data.claim_frequency,
            npa_disqualification_dpd_days=data.npa_disqualification_dpd_days,
            description=data.description,
            created_by=current_user.id,
        )
        self.session.add(scheme)
        await self.session.flush()
        await self.session.refresh(scheme)
        return scheme

    # =========================================================================
    # Read
    # =========================================================================

    async def list_schemes(
        self,
        organization_id: UUID,
        include_inactive: bool = False,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[SubventionScheme], int]:
        """List platform + tenant-owned schemes visible to the caller.

        Returns (items, total_count).
        """
        where = [
            or_(
                SubventionScheme.organization_id.is_(None),
                SubventionScheme.organization_id == organization_id,
            ),
            SubventionScheme.deleted_at.is_(None),
        ]
        if not include_inactive:
            where.append(SubventionScheme.is_active.is_(True))

        count_stmt = select(func.count()).select_from(SubventionScheme).where(*where)
        total = (await self.session.execute(count_stmt)).scalar_one()

        stmt = (
            select(SubventionScheme)
            .where(*where)
            .order_by(SubventionScheme.scheme_code.asc())
            .offset(skip)
            .limit(limit)
        )
        rows = (await self.session.execute(stmt)).scalars().all()
        return list(rows), int(total)

    async def get(self, organization_id: UUID, scheme_id: UUID) -> SubventionScheme:
        """Get a single scheme (platform-default OR caller-owned)."""
        scheme = await self.session.get(SubventionScheme, scheme_id)
        if not scheme or scheme.deleted_at is not None:
            raise NotFoundException("Scheme not found", error_code="SCHEME_NOT_FOUND")
        if scheme.organization_id is not None and scheme.organization_id != organization_id:
            # Tenant boundary — pretend it doesn't exist.
            raise NotFoundException("Scheme not found", error_code="SCHEME_NOT_FOUND")
        return scheme

    async def get_by_code(self, organization_id: UUID, scheme_code: str) -> SubventionScheme | None:
        """Fetch by code, preferring tenant override over platform default."""
        stmt = (
            select(SubventionScheme)
            .where(
                SubventionScheme.scheme_code == scheme_code,
                SubventionScheme.deleted_at.is_(None),
                or_(
                    SubventionScheme.organization_id.is_(None),
                    SubventionScheme.organization_id == organization_id,
                ),
            )
            # Prefer tenant-owned over NULL via ordering.
            .order_by(SubventionScheme.organization_id.is_(None).asc())
            .limit(1)
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    # =========================================================================
    # Update / Delete
    # =========================================================================

    async def update(
        self,
        organization_id: UUID,
        scheme_id: UUID,
        data: SubventionSchemeUpdate,
        current_user: User,
    ) -> SubventionScheme:
        """Update a tenant-owned scheme (platform rows are read-only)."""
        scheme = await self.get(organization_id, scheme_id)

        if scheme.organization_id is None:
            raise BadRequestException(
                "Platform-default schemes are read-only; create a tenant override",
                error_code="READONLY_PLATFORM_SCHEME",
            )

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(scheme, field, value)

        if (
            data.scheme_start_date is not None or data.scheme_end_date is not None
        ) and scheme.scheme_end_date < scheme.scheme_start_date:
            raise BadRequestException(
                "scheme_end_date must be on or after scheme_start_date",
                error_code="INVALID_SCHEME_DATES",
            )

        scheme.updated_by = current_user.id
        scheme.version = (scheme.version or 1) + 1
        await self.session.flush()
        await self.session.refresh(scheme)
        return scheme

    async def soft_delete(
        self,
        organization_id: UUID,
        scheme_id: UUID,
        current_user: User,
    ) -> None:
        """Soft-delete a tenant-owned scheme."""
        scheme = await self.get(organization_id, scheme_id)
        if scheme.organization_id is None:
            raise BadRequestException(
                "Platform-default schemes cannot be deleted",
                error_code="READONLY_PLATFORM_SCHEME",
            )
        scheme.soft_delete(deleted_by=current_user.id)
        await self.session.flush()

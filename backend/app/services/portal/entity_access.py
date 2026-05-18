"""Borrower-portal entity-access guard.

Every borrower-portal endpoint reads or writes data scoped to one (or
many) ``los_entity`` rows. The browser only ever speaks its session
token; the BE intersects "what does the URL/body claim?" with "what
does ``mst_portal_user_entity`` say this user owns?". Anything outside
the intersection raises 404 — never 403 — so we never leak the
existence of records across tenants (CLAUDE.md §3.4, §8.7).
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.models.lending.application import LoanApplication
from app.models.lending.loan_account import LoanAccount
from app.models.portal.portal_user import PortalUser
from app.models.portal.portal_user_entity import PortalUserEntity


async def get_accessible_entity_ids(
    portal_user: PortalUser,
    db: AsyncSession,
) -> set[UUID]:
    """Return the set of ``los_entity.id`` values this portal user can act on."""
    stmt = select(PortalUserEntity.entity_id).where(
        PortalUserEntity.portal_user_id == portal_user.id,
        PortalUserEntity.is_link_active.is_(True),
        PortalUserEntity.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    return {row[0] for row in result.all()}


async def assert_entity_access(
    portal_user: PortalUser,
    entity_id: UUID,
    db: AsyncSession,
) -> None:
    """Raise NotFound if ``entity_id`` is not accessible to ``portal_user``."""
    accessible = await get_accessible_entity_ids(portal_user, db)
    if entity_id not in accessible:
        raise NotFoundException(
            "Entity not found",
            error_code="ENTITY_NOT_FOUND",
        )


async def assert_loan_access(
    portal_user: PortalUser,
    loan_account_id: UUID,
    db: AsyncSession,
) -> LoanAccount:
    """Resolve a loan account and verify the borrower owns its entity.

    Returns the loaded :class:`LoanAccount` for downstream use so callers
    don't repeat the lookup. Raises :class:`NotFoundException` on any miss.
    """
    accessible = await get_accessible_entity_ids(portal_user, db)
    if not accessible:
        raise NotFoundException(
            "Loan account not found",
            error_code="LOAN_ACCOUNT_NOT_FOUND",
        )
    stmt = select(LoanAccount).where(
        LoanAccount.id == loan_account_id,
        LoanAccount.entity_id.in_(accessible),
        LoanAccount.deleted_at.is_(None),
    )
    loan = (await db.execute(stmt)).scalar_one_or_none()
    if loan is None:
        raise NotFoundException(
            "Loan account not found",
            error_code="LOAN_ACCOUNT_NOT_FOUND",
        )
    return loan


async def assert_application_access(
    portal_user: PortalUser,
    application_id: UUID,
    db: AsyncSession,
) -> LoanApplication:
    """Resolve a loan application and verify the borrower owns its entity.

    Returns the loaded :class:`LoanApplication` for downstream use.
    Raises :class:`NotFoundException` on any miss.
    """
    accessible = await get_accessible_entity_ids(portal_user, db)
    if not accessible:
        raise NotFoundException(
            "Application not found",
            error_code="APPLICATION_NOT_FOUND",
        )
    stmt = select(LoanApplication).where(
        LoanApplication.id == application_id,
        LoanApplication.entity_id.in_(accessible),
        LoanApplication.deleted_at.is_(None),
    )
    application = (await db.execute(stmt)).scalar_one_or_none()
    if application is None:
        raise NotFoundException(
            "Application not found",
            error_code="APPLICATION_NOT_FOUND",
        )
    return application

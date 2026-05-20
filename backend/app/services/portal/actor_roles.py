"""Helpers for integrated scheme-portal actor roles."""

from __future__ import annotations

from app.models.portal.enums import PortalActorRole
from app.models.portal.portal_user import PortalUser

REVIEW_PORTAL_ROLES: frozenset[str] = frozenset(
    {
        PortalActorRole.SCHEME_LENDER.value,
        PortalActorRole.SCHEME_SMFCL_REVIEWER.value,
        PortalActorRole.SCHEME_SMFCL_APPROVER.value,
        PortalActorRole.SCHEME_MINISTRY_VIEWER.value,
        PortalActorRole.SCHEME_ADMIN.value,
    }
)

CLAIM_VERIFY_ROLES: frozenset[str] = frozenset(
    {
        PortalActorRole.SCHEME_SMFCL_REVIEWER.value,
        PortalActorRole.SCHEME_ADMIN.value,
    }
)

CLAIM_RELEASE_ROLES: frozenset[str] = frozenset(
    {
        PortalActorRole.SCHEME_SMFCL_APPROVER.value,
        PortalActorRole.SCHEME_ADMIN.value,
    }
)

CLAIM_SUBMITTER_ROLES: frozenset[str] = frozenset(
    {
        PortalActorRole.SCHEME_BORROWER.value,
        PortalActorRole.SCHEME_LENDER.value,
        PortalActorRole.SCHEME_ADMIN.value,
    }
)

APPLICATION_LENDER_ROLES: frozenset[str] = frozenset(
    {
        PortalActorRole.SCHEME_LENDER.value,
        PortalActorRole.SCHEME_ADMIN.value,
    }
)

APPLICATION_SMFCL_REVIEW_ROLES: frozenset[str] = frozenset(
    {
        PortalActorRole.SCHEME_SMFCL_REVIEWER.value,
        PortalActorRole.SCHEME_SMFCL_APPROVER.value,
        PortalActorRole.SCHEME_ADMIN.value,
    }
)

APPLICATION_APPROVER_ROLES: frozenset[str] = frozenset(
    {
        PortalActorRole.SCHEME_SMFCL_APPROVER.value,
        PortalActorRole.SCHEME_ADMIN.value,
    }
)


def portal_actor_role(user: PortalUser) -> str:
    raw = getattr(user, "actor_role", None)
    if hasattr(raw, "value"):
        return str(raw.value)
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    return PortalActorRole.SCHEME_BORROWER.value


def is_borrower_role(user: PortalUser) -> bool:
    return portal_actor_role(user) == PortalActorRole.SCHEME_BORROWER.value

"""Borrower-portal registration service.

Manages the borrower-side onboarding flow, distinct from the legacy
customer-portal login. The lifecycle is:

1. ``register(...)`` — caller submits either CIN/GSTIN/LLPIN/PAN or an
   existing loan-account number + sanctioned amount, plus
   authorised-signatory + mobile + email. The service either reuses the
   same in-flight PENDING_APPROVAL row (idempotent retries) or inserts a
   fresh ``PortalUser`` row with
   ``registration_status='PENDING_APPROVAL'`` and a new
   ``registration_reference`` (``REG/{YYYY}/{NNNNNN}``). An OTP row is
   issued via the existing ``PortalAuthService`` plumbing.

2. ``verify_otp(reference, otp)`` — checks the OTP. On success, runs the
   **auto-approval** heuristic:

      * exact loan-account-number + sanctioned-amount match, or
      * exactly one matching ``los_entity`` on CIN/GSTIN/PAN/LLPIN
      * AND a contact with the same mobile + email on that entity

   If the heuristic matches, the service inserts a
   ``mst_portal_user_entity`` link and flips the user to ACTIVE. The
   approver is the system (``approved_by=NULL``). Otherwise the user
   stays PENDING_APPROVAL.

3. ``get_status(reference, mobile)`` — unauthenticated lookup. Returns
   the current state with masked mobile + (if rejected) the reason.

4. ``admin_list / admin_get / admin_approve / admin_reject`` — admin
   review flow. ``approve`` validates every supplied entity belongs to
   the current admin's organisation (CLAUDE.md §3.4).
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from datetime import UTC, datetime
from hashlib import sha256
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import (
    BadRequestException,
    NotFoundException,
)
from app.models.lending.entity import Entity, EntityContact
from app.models.lending.enums import EntityType
from app.models.lending.loan_account import LoanAccount
from app.models.masters.organization import Organization
from app.models.portal.enums import (
    OTPPurpose,
    PortalActorRole,
    PortalRegistrationStatus,
)
from app.models.portal.portal_user import PortalOTP, PortalUser
from app.models.portal.portal_user_entity import PortalUserEntity
from app.schemas.portal.registration import (
    AdminRegistrationDetail,
    AdminRegistrationListItem,
    AdminRegistrationListResponse,
    EntitySuggestion,
    RegisterRequest,
    RegisterResponse,
    RegisterVerifyOtpResponse,
    RegistrationStatusResponse,
)
from app.services.portal.auth_service import PortalAuthService

_REGISTRATION_REFERENCE_RE = re.compile(r"^REG/\d{4}/\d{6}$")


def _hash_otp(otp: str) -> str:
    """Match :class:`PortalAuthService._hash_otp`."""
    return sha256(otp.encode()).hexdigest()


def _mask_mobile(mobile: str) -> str:
    """Display-mask helper. ``+919XXXXXX1234`` → ``+91-XXXXX-X1234``."""
    digits = re.sub(r"\D", "", mobile)
    if len(digits) >= 4:
        return f"+91-XXXXX-X{digits[-4:]}"
    return "+91-XXXXX-XXXX"


def _normalize(value: str | None) -> str | None:
    """Trim + upper for case-insensitive identifier matches."""
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned.upper() if cleaned else None


class PortalRegistrationService:
    """Borrower-side registration lifecycle."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # =====================================================================
    # Borrower-facing
    # =====================================================================

    async def register(
        self,
        payload: RegisterRequest,
    ) -> RegisterResponse:
        """Create or reuse a PENDING_APPROVAL portal user and issue an OTP."""
        # Resolve the intake organization. The borrower has no org yet;
        # the admin's approve action enforces tenant-scope at link time.
        intake_org_id = await self._intake_organization_id()

        normalized_mobile = payload.mobile.strip()

        # Reuse only the same in-flight registration. Matching on mobile
        # alone is too weak because one authorised signatory can represent
        # multiple borrowers.
        user = await self._find_pending_user(intake_org_id, payload)

        if user is None:
            user = PortalUser(
                organization_id=intake_org_id,
                customer_id=None,
                mobile=normalized_mobile,
                email=payload.email,
                mobile_verified=False,
                actor_role=PortalActorRole.SCHEME_BORROWER,
                registration_status=PortalRegistrationStatus.PENDING_APPROVAL,
                registration_requested_pan=_normalize(payload.pan),
                registration_requested_cin=_normalize(payload.cin),
                registration_requested_gstin=_normalize(payload.gstin),
                registration_requested_llpin=_normalize(payload.llpin),
                registration_requested_loan_account_number=_normalize(payload.loan_account_number),
                registration_requested_sanctioned_amount=payload.sanctioned_amount,
                registration_authorized_signatory_name=(payload.authorized_signatory_name.strip()),
                registered_at=datetime.now(UTC),
                registration_reference=await self._next_registration_reference(),
            )
            self.db.add(user)
            await self.db.flush()
        else:
            # Update the self-asserted IDs / signatory in case the user
            # corrects a typo on a retry.
            user.email = payload.email
            user.registration_requested_pan = _normalize(payload.pan)
            user.registration_requested_cin = _normalize(payload.cin)
            user.registration_requested_gstin = _normalize(payload.gstin)
            user.registration_requested_llpin = _normalize(payload.llpin)
            user.registration_requested_loan_account_number = _normalize(
                payload.loan_account_number
            )
            user.registration_requested_sanctioned_amount = payload.sanctioned_amount
            user.registration_authorized_signatory_name = payload.authorized_signatory_name.strip()

        otp_result = await PortalAuthService(self.db).send_otp(
            organization_id=intake_org_id,
            mobile=normalized_mobile,
            purpose=OTPPurpose.REGISTRATION,
            reference_type="REGISTRATION",
            reference_id=user.id,
        )
        if not otp_result.get("success"):
            raise BadRequestException(
                otp_result.get("error") or "Unable to send registration OTP",
                error_code=otp_result.get("error_code", "REGISTRATION_OTP_FAILED"),
            )

        return RegisterResponse(
            registration_reference=user.registration_reference or "",
            status="OTP_SENT",
            masked_mobile=_mask_mobile(normalized_mobile),
        )

    async def verify_otp(
        self,
        registration_reference: str,
        otp_code: str,
    ) -> RegisterVerifyOtpResponse:
        """Verify OTP and optionally auto-approve.

        Returns the new user state. Idempotent for already-verified
        ACTIVE users (won't re-link entities).
        """
        if not _REGISTRATION_REFERENCE_RE.match(registration_reference):
            raise BadRequestException(
                "registrationReference is malformed",
                error_code="REGISTRATION_REFERENCE_INVALID",
            )

        user = await self._get_user_by_reference(registration_reference)
        if user is None:
            raise NotFoundException(
                "Registration not found",
                error_code="REGISTRATION_NOT_FOUND",
            )

        if user.registration_status == PortalRegistrationStatus.REJECTED:
            raise BadRequestException(
                "Registration was rejected",
                error_code="REGISTRATION_REJECTED",
            )

        if user.registration_status == PortalRegistrationStatus.ACTIVE:
            linked = await self._linked_entity_ids(user.id)
            return RegisterVerifyOtpResponse(
                registration_reference=registration_reference,
                portal_user_id=user.id,
                registration_status="ACTIVE",
                auto_approved=False,
                linked_entity_ids=linked,
            )

        otp_stmt = (
            select(PortalOTP)
            .where(
                PortalOTP.organization_id == user.organization_id,
                PortalOTP.mobile == user.mobile,
                PortalOTP.purpose == OTPPurpose.REGISTRATION,
                PortalOTP.is_used.is_(False),
                PortalOTP.expires_at > datetime.utcnow(),
            )
            .order_by(PortalOTP.generated_at.desc())
            .limit(1)
        )
        otp = (await self.db.execute(otp_stmt)).scalar_one_or_none()
        if otp is None:
            raise BadRequestException(
                "OTP expired or not found",
                error_code="OTP_EXPIRED",
            )
        if otp.attempts >= otp.max_attempts:
            raise BadRequestException(
                "Maximum OTP attempts exceeded",
                error_code="OTP_ATTEMPTS_EXCEEDED",
            )

        otp.attempts += 1
        if _hash_otp(otp_code) != otp.otp_hash:
            raise BadRequestException(
                "Invalid OTP",
                error_code="OTP_INVALID",
            )

        otp.is_used = True
        otp.verified_at = datetime.utcnow()
        user.mobile_verified = True
        user.mobile_verified_at = datetime.utcnow()

        auto_approved, linked_entity_ids = await self._try_auto_approve(user)
        if auto_approved:
            return RegisterVerifyOtpResponse(
                registration_reference=registration_reference,
                portal_user_id=user.id,
                registration_status="ACTIVE",
                auto_approved=True,
                linked_entity_ids=linked_entity_ids,
            )

        return RegisterVerifyOtpResponse(
            registration_reference=registration_reference,
            portal_user_id=user.id,
            registration_status="PENDING_APPROVAL",
            auto_approved=False,
            linked_entity_ids=[],
        )

    async def get_status(
        self,
        registration_reference: str,
        mobile: str,
    ) -> RegistrationStatusResponse:
        """Public status lookup. Returns 404 on mobile+reference mismatch."""
        if not _REGISTRATION_REFERENCE_RE.match(registration_reference):
            raise NotFoundException(
                "Registration not found",
                error_code="REGISTRATION_NOT_FOUND",
            )

        normalized_mobile = mobile.strip()
        user = await self._get_user_by_reference(registration_reference)
        if user is None or user.mobile != normalized_mobile:
            raise NotFoundException(
                "Registration not found",
                error_code="REGISTRATION_NOT_FOUND",
            )

        return RegistrationStatusResponse(
            registration_reference=registration_reference,
            registration_status=user.registration_status,
            masked_mobile=_mask_mobile(user.mobile),
            rejection_reason=user.rejection_reason,
            approved_at=user.approved_at,
        )

    # =====================================================================
    # Admin-facing
    # =====================================================================

    async def admin_list(
        self,
        status: PortalRegistrationStatus | None,
        page: int,
        page_size: int,
    ) -> AdminRegistrationListResponse:
        """Platform-wide list (tenant-scope is enforced at approve-time)."""
        page = max(1, page)
        page_size = max(1, min(page_size, 200))

        stmt = select(PortalUser).where(PortalUser.deleted_at.is_(None))
        if status is not None:
            stmt = stmt.where(PortalUser.registration_status == status)
        # Borrower-portal rows only — exclude legacy customer-portal rows
        # that have no registration_reference. The migration set every
        # legacy row to ACTIVE with NULL reference, so we filter those out
        # of the admin queue.
        stmt = stmt.where(PortalUser.registration_reference.is_not(None))
        stmt = stmt.order_by(PortalUser.registered_at.desc().nullslast())

        total_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.db.execute(total_stmt)).scalar_one()

        rows = list(
            (await self.db.execute(stmt.offset((page - 1) * page_size).limit(page_size)))
            .scalars()
            .all()
        )

        items: list[AdminRegistrationListItem] = [self._to_admin_list_item(u) for u in rows]
        return AdminRegistrationListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )

    async def admin_get(
        self,
        portal_user_id: UUID,
        current_user_org_id: UUID,
    ) -> AdminRegistrationDetail:
        """Detail view with same-org entity suggestions + current links."""
        user = await self._get_user_by_id(portal_user_id)
        if user is None or user.registration_reference is None:
            raise NotFoundException(
                "Registration not found",
                error_code="REGISTRATION_NOT_FOUND",
            )

        suggestions = await self._find_entity_matches(
            user,
            organization_id=current_user_org_id,
        )
        linked = await self._linked_entity_ids(user.id)

        base = self._to_admin_list_item(user)
        return AdminRegistrationDetail(
            **base.model_dump(by_alias=False),
            suggested_entities=suggestions,
            linked_entity_ids=linked,
        )

    async def admin_approve(
        self,
        portal_user_id: UUID,
        entity_ids: Sequence[UUID],
        current_user_id: UUID,
        current_user_org_id: UUID,
    ) -> AdminRegistrationDetail:
        """Link the user to the given entities and flip status to ACTIVE.

        Validates every ``entity_id`` belongs to the admin's
        organization (cross-tenant probe is rejected with 400).
        """
        if not entity_ids:
            raise BadRequestException(
                "At least one entityId is required",
                error_code="ENTITY_IDS_REQUIRED",
            )

        user = await self._get_user_by_id(portal_user_id)
        if user is None or user.registration_reference is None:
            raise NotFoundException(
                "Registration not found",
                error_code="REGISTRATION_NOT_FOUND",
            )
        if user.registration_status == PortalRegistrationStatus.REJECTED:
            raise BadRequestException(
                "Cannot approve a rejected registration",
                error_code="REGISTRATION_REJECTED",
            )

        # Cross-tenant guard: every entity must belong to the admin's org.
        ent_stmt = select(Entity).where(
            Entity.id.in_(list(entity_ids)),
            Entity.deleted_at.is_(None),
        )
        entities = list((await self.db.execute(ent_stmt)).scalars().all())
        if len(entities) != len(set(entity_ids)):
            raise BadRequestException(
                "One or more entityIds were not found",
                error_code="ENTITY_NOT_FOUND",
            )
        for ent in entities:
            if ent.organization_id != current_user_org_id:
                raise BadRequestException(
                    "Entity belongs to another organization",
                    error_code="ENTITY_CROSS_TENANT",
                )
            if ent.entity_type == EntityType.INDIVIDUAL:
                raise BadRequestException(
                    "Scheme borrower registrations can only be linked to institutional entities",
                    error_code="SCHEME_ENTITY_TYPE_INVALID",
                )

        # Insert links (skip duplicates of existing live links).
        existing_links = await self._linked_entity_ids(user.id)
        for ent in entities:
            if ent.id in existing_links:
                continue
            link = PortalUserEntity(
                portal_user_id=user.id,
                entity_id=ent.id,
                organization_id=ent.organization_id,
                granted_at=datetime.now(UTC),
                granted_by=current_user_id,
                is_link_active=True,
                created_by=current_user_id,
            )
            self.db.add(link)

        # Stamp the user as approved. Move the user into the org of the
        # FIRST linked entity so any tenant-scoped queries on the
        # portal_user row resolve correctly. (RLS is enforced on the
        # link table for borrower-portal data access — see
        # ``services/portal/entity_access.py``.)
        user.registration_status = PortalRegistrationStatus.ACTIVE
        user.approved_at = datetime.now(UTC)
        user.approved_by = current_user_id
        user.organization_id = entities[0].organization_id
        user.rejection_reason = None

        await self.db.flush()

        return await self.admin_get(portal_user_id, current_user_org_id)

    async def admin_reject(
        self,
        portal_user_id: UUID,
        reason: str,
        current_user_id: UUID,
        current_user_org_id: UUID,
    ) -> AdminRegistrationDetail:
        """Reject a registration with a reason."""
        user = await self._get_user_by_id(portal_user_id)
        if user is None or user.registration_reference is None:
            raise NotFoundException(
                "Registration not found",
                error_code="REGISTRATION_NOT_FOUND",
            )
        if user.registration_status == PortalRegistrationStatus.ACTIVE:
            raise BadRequestException(
                "Cannot reject an already-active registration",
                error_code="REGISTRATION_ALREADY_ACTIVE",
            )

        user.registration_status = PortalRegistrationStatus.REJECTED
        user.rejection_reason = reason.strip()
        user.approved_by = current_user_id
        user.approved_at = datetime.now(UTC)
        await self.db.flush()

        return await self.admin_get(portal_user_id, current_user_org_id)

    # =====================================================================
    # Internals
    # =====================================================================

    async def _intake_organization_id(self) -> UUID:
        """Return the platform's registration-intake organization.

        The intake organization must be explicit in multi-tenant mode.
        For single-tenant demos/dev a sole active organization is accepted.
        """
        configured = getattr(settings, "PORTAL_DEFAULT_ORGANIZATION_ID", None)
        if configured:
            org = (
                await self.db.execute(
                    select(Organization.id).where(
                        Organization.id == configured,
                        Organization.deleted_at.is_(None),
                    )
                )
            ).scalar_one_or_none()
            if org is None:
                raise BadRequestException(
                    "Configured portal intake organization was not found",
                    error_code="INVALID_INTAKE_ORG",
                )
            return org

        org_ids = list(
            (
                await self.db.execute(
                    select(Organization.id)
                    .where(Organization.deleted_at.is_(None))
                    .order_by(Organization.created_at.asc())
                )
            )
            .scalars()
            .all()
        )
        if len(org_ids) == 1:
            return org_ids[0]
        if not org_ids:
            raise BadRequestException(
                "No organization configured to receive registrations",
                error_code="NO_INTAKE_ORG",
            )
        raise BadRequestException(
            "Multiple organizations exist. Set PORTAL_DEFAULT_ORGANIZATION_ID "
            "for scheme-portal registration intake.",
            error_code="AMBIGUOUS_INTAKE_ORG",
        )

    async def _next_registration_reference(self) -> str:
        """Generate ``REG/{YYYY}/{NNNNNN}`` — monotonic-ish per year.

        We compute the sequence by counting existing references for the
        current year (``deleted_at`` agnostic to avoid collisions on
        soft-deletes). Collisions trigger a unique-constraint retry by
        the caller's transaction layer.
        """
        year = datetime.now(UTC).year
        prefix = f"REG/{year}/"
        count_stmt = select(func.count(PortalUser.id)).where(
            PortalUser.registration_reference.like(f"{prefix}%")
        )
        existing = (await self.db.execute(count_stmt)).scalar_one()
        return f"{prefix}{existing + 1:06d}"

    async def _find_pending_user(
        self,
        organization_id: UUID,
        payload: RegisterRequest,
    ) -> PortalUser | None:
        normalized_mobile = payload.mobile.strip()
        stmt = (
            select(PortalUser)
            .where(
                PortalUser.organization_id == organization_id,
                PortalUser.mobile == normalized_mobile,
                PortalUser.registration_status == PortalRegistrationStatus.PENDING_APPROVAL,
                PortalUser.deleted_at.is_(None),
            )
            .order_by(PortalUser.created_at.desc())
        )
        candidates = list((await self.db.execute(stmt)).scalars().all())
        for candidate in candidates:
            if self._pending_request_matches(candidate, payload):
                return candidate
        return None

    async def _get_user_by_reference(self, registration_reference: str) -> PortalUser | None:
        stmt = select(PortalUser).where(
            PortalUser.registration_reference == registration_reference,
            PortalUser.deleted_at.is_(None),
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def _get_user_by_id(self, user_id: UUID) -> PortalUser | None:
        stmt = select(PortalUser).where(
            PortalUser.id == user_id,
            PortalUser.deleted_at.is_(None),
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def _linked_entity_ids(self, portal_user_id: UUID) -> list[UUID]:
        stmt = select(PortalUserEntity.entity_id).where(
            PortalUserEntity.portal_user_id == portal_user_id,
            PortalUserEntity.is_link_active.is_(True),
            PortalUserEntity.deleted_at.is_(None),
        )
        return [row[0] for row in (await self.db.execute(stmt)).all()]

    def _pending_request_matches(
        self,
        user: PortalUser,
        payload: RegisterRequest,
    ) -> bool:
        return (
            user.email == payload.email
            and user.registration_requested_pan == _normalize(payload.pan)
            and user.registration_requested_cin == _normalize(payload.cin)
            and user.registration_requested_gstin == _normalize(payload.gstin)
            and user.registration_requested_llpin == _normalize(payload.llpin)
            and user.registration_requested_loan_account_number
            == _normalize(payload.loan_account_number)
            and user.registration_requested_sanctioned_amount == payload.sanctioned_amount
            and (user.registration_authorized_signatory_name or "").strip()
            == payload.authorized_signatory_name.strip()
        )

    async def _contact_matches_entity(
        self,
        entity: Entity,
        user: PortalUser,
    ) -> bool:
        normalized_mobile = re.sub(r"\D", "", user.mobile)
        target_email = (user.email or "").strip().lower()
        if not normalized_mobile or not target_email:
            return False

        primary_phone = re.sub(r"\D", "", entity.primary_phone or "")
        primary_email = (entity.primary_email or "").strip().lower()
        if primary_phone.endswith(normalized_mobile[-10:]) and primary_email == target_email:
            return True

        contact_stmt = select(EntityContact).where(
            EntityContact.entity_id == entity.id,
            EntityContact.deleted_at.is_(None),
        )
        contacts = list((await self.db.execute(contact_stmt)).scalars().all())
        return any(
            (c.mobile and re.sub(r"\D", "", c.mobile).endswith(normalized_mobile[-10:]))
            and ((c.email or "").strip().lower() == target_email)
            for c in contacts
        )

    async def _activate_user_for_entity(
        self,
        user: PortalUser,
        entity: Entity,
        granted_by: UUID | None,
    ) -> None:
        existing_links = await self._linked_entity_ids(user.id)
        if entity.id not in existing_links:
            self.db.add(
                PortalUserEntity(
                    portal_user_id=user.id,
                    entity_id=entity.id,
                    organization_id=entity.organization_id,
                    granted_at=datetime.now(UTC),
                    granted_by=granted_by,
                    is_link_active=True,
                )
            )

        user.registration_status = PortalRegistrationStatus.ACTIVE
        user.approved_at = datetime.now(UTC)
        user.approved_by = granted_by
        user.organization_id = entity.organization_id
        user.rejection_reason = None
        await self.db.flush()

    async def _find_existing_loan_entity(self, user: PortalUser) -> Entity | None:
        loan_account_number = _normalize(user.registration_requested_loan_account_number)
        sanctioned_amount = user.registration_requested_sanctioned_amount
        if not loan_account_number or sanctioned_amount is None:
            return None

        stmt = (
            select(Entity)
            .join(LoanAccount, LoanAccount.entity_id == Entity.id)
            .where(
                LoanAccount.deleted_at.is_(None),
                func.upper(LoanAccount.loan_account_number) == loan_account_number,
                LoanAccount.sanctioned_amount == sanctioned_amount,
                Entity.deleted_at.is_(None),
                Entity.entity_type != EntityType.INDIVIDUAL,
            )
            .limit(1)
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def _try_auto_approve(
        self,
        user: PortalUser,
    ) -> tuple[bool, list[UUID]]:
        """Auto-approve when exactly one entity matches AND contact OK.

        Returns ``(auto_approved, linked_entity_ids)``. On auto-approval
        the user's ``organization_id`` is rebound to the matched entity's
        org, the link row is inserted, and status is flipped to ACTIVE.
        """
        loan_entity = await self._find_existing_loan_entity(user)
        if loan_entity is not None and await self._contact_matches_entity(loan_entity, user):
            await self._activate_user_for_entity(user, loan_entity, granted_by=None)
            return True, [loan_entity.id]

        candidates = await self._find_entity_matches(user, organization_id=None)
        if len(candidates) != 1:
            return False, []

        candidate = candidates[0]
        ent_stmt = select(Entity).where(Entity.id == candidate.entity_id)
        entity = (await self.db.execute(ent_stmt)).scalar_one_or_none()
        if entity is None or not await self._contact_matches_entity(entity, user):
            return False, []

        await self._activate_user_for_entity(user, entity, granted_by=None)
        return True, [entity.id]

    async def _find_entity_matches(
        self,
        user: PortalUser,
        organization_id: UUID | None,
    ) -> list[EntitySuggestion]:
        """Find candidate ``los_entity`` rows on identifier match.

        ``organization_id`` scopes the search to one tenant (admin
        review). Pass ``None`` to search platform-wide (auto-approve).
        Ordered by match strength: CIN > GSTIN > PAN > LLPIN > FUZZY.
        """
        out: list[EntitySuggestion] = []
        seen: set[UUID] = set()

        if (
            user.registration_requested_loan_account_number
            and user.registration_requested_sanctioned_amount is not None
        ):
            loan_stmt = (
                select(Entity, LoanAccount)
                .join(LoanAccount, LoanAccount.entity_id == Entity.id)
                .where(
                    Entity.deleted_at.is_(None),
                    Entity.entity_type != EntityType.INDIVIDUAL,
                    LoanAccount.deleted_at.is_(None),
                    func.upper(LoanAccount.loan_account_number)
                    == user.registration_requested_loan_account_number,
                    LoanAccount.sanctioned_amount
                    == user.registration_requested_sanctioned_amount,
                )
            )
            if organization_id is not None:
                loan_stmt = loan_stmt.where(Entity.organization_id == organization_id)
            for ent, loan in (await self.db.execute(loan_stmt)).all():
                if ent.id in seen:
                    continue
                out.append(_entity_to_suggestion(ent, "EXACT_LOAN_ACCOUNT", loan))
                seen.add(ent.id)

        async def _query(
            *,
            field_value: str,
            field_attr,
        ) -> list[Entity]:
            stmt = select(Entity).where(
                Entity.deleted_at.is_(None),
                Entity.entity_type != EntityType.INDIVIDUAL,
                func.upper(field_attr) == field_value.upper(),
            )
            if organization_id is not None:
                stmt = stmt.where(Entity.organization_id == organization_id)
            return list((await self.db.execute(stmt)).scalars().all())

        if user.registration_requested_cin:
            for ent in await _query(
                field_value=user.registration_requested_cin,
                field_attr=Entity.cin,
            ):
                if ent.id in seen:
                    continue
                out.append(_entity_to_suggestion(ent, "EXACT_CIN"))
                seen.add(ent.id)

        if user.registration_requested_gstin:
            for ent in await _query(
                field_value=user.registration_requested_gstin,
                field_attr=Entity.gstin,
            ):
                if ent.id in seen:
                    continue
                out.append(_entity_to_suggestion(ent, "EXACT_GSTIN"))
                seen.add(ent.id)

        if user.registration_requested_pan:
            for ent in await _query(
                field_value=user.registration_requested_pan,
                field_attr=Entity.pan,
            ):
                if ent.id in seen:
                    continue
                out.append(_entity_to_suggestion(ent, "EXACT_PAN"))
                seen.add(ent.id)

        if user.registration_requested_llpin:
            for ent in await _query(
                field_value=user.registration_requested_llpin,
                field_attr=Entity.llpin,
            ):
                if ent.id in seen:
                    continue
                out.append(_entity_to_suggestion(ent, "EXACT_LLPIN"))
                seen.add(ent.id)

        return out

    def _to_admin_list_item(self, user: PortalUser) -> AdminRegistrationListItem:
        return AdminRegistrationListItem(
            portal_user_id=user.id,
            registration_reference=user.registration_reference or "",
            registration_status=user.registration_status,
            requested_cin=user.registration_requested_cin,
            requested_gstin=user.registration_requested_gstin,
            requested_llpin=user.registration_requested_llpin,
            requested_pan=user.registration_requested_pan,
            requested_loan_account_number=user.registration_requested_loan_account_number,
            requested_sanctioned_amount=user.registration_requested_sanctioned_amount,
            authorized_signatory_name=(user.registration_authorized_signatory_name or ""),
            mobile=user.mobile,
            email=user.email or "",
            registered_at=user.registered_at or user.created_at,
            approved_at=user.approved_at,
            rejection_reason=user.rejection_reason,
        )


def _entity_to_suggestion(
    entity: Entity,
    strength: str,
    loan: LoanAccount | None = None,
) -> EntitySuggestion:
    return EntitySuggestion(
        entity_id=entity.id,
        legal_name=entity.legal_name,
        cin=entity.cin,
        gstin=entity.gstin,
        pan=entity.pan,
        llpin=entity.llpin,
        loan_account_number=loan.loan_account_number if loan is not None else None,
        sanctioned_amount=loan.sanctioned_amount if loan is not None else None,
        match_strength=strength,  # type: ignore[arg-type]
    )

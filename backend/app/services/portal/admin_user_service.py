"""Tenant-scoped admin service for integrated scheme-portal users."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import BadRequestException, NotFoundException
from app.models.lending.entity import Entity, EntityContact
from app.models.lending.enums import ContactType, EntityType
from app.models.portal.enums import (
    PortalActorRole,
    PortalRegistrationStatus,
    PortalUserStatus,
)
from app.models.portal.portal_user import PortalUser
from app.models.portal.portal_user_entity import PortalUserEntity
from app.schemas.portal.admin_user import (
    AdminPortalInviteResponse,
    AdminPortalUserCreateRequest,
    AdminPortalUserDetail,
    AdminPortalUserEntityLink,
    AdminPortalUserListItem,
    AdminPortalUserListResponse,
    AdminPortalUserUpdateRequest,
)
from app.services.portal.auth_service import PortalAuthService


class PortalAdminUserService:
    """Manage scheme-portal users within one tenant."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_users(
        self,
        *,
        organization_id: UUID,
        actor_role: str | None = None,
        status: str | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> AdminPortalUserListResponse:
        page = max(1, page)
        page_size = max(1, min(page_size, 200))

        stmt = (
            select(PortalUser)
            .options(selectinload(PortalUser.entities).selectinload(PortalUserEntity.entity))
            .where(
                PortalUser.organization_id == organization_id,
                PortalUser.deleted_at.is_(None),
            )
            .order_by(PortalUser.created_at.desc())
        )
        if actor_role:
            stmt = stmt.where(PortalUser.actor_role == actor_role)
        if status:
            stmt = stmt.where(PortalUser.status == status)
        if search:
            pattern = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    PortalUser.mobile.ilike(pattern),
                    PortalUser.email.ilike(pattern),
                    PortalUser.registration_authorized_signatory_name.ilike(pattern),
                )
            )

        rows = list((await self.db.execute(stmt)).scalars().all())
        total = len(rows)
        rows = rows[(page - 1) * page_size : (page - 1) * page_size + page_size]
        return AdminPortalUserListResponse(
            items=[self._to_list_item(user) for user in rows],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_user(
        self,
        *,
        organization_id: UUID,
        portal_user_id: UUID,
    ) -> AdminPortalUserDetail:
        user = await self._get_user(organization_id, portal_user_id)
        return self._to_detail(user)

    async def create_user(
        self,
        *,
        organization_id: UUID,
        current_user_id: UUID,
        payload: AdminPortalUserCreateRequest,
    ) -> AdminPortalUserDetail:
        actor_role = self._parse_actor_role(payload.actor_role)
        status = self._parse_status(payload.status)
        existing = (
            await self.db.execute(
                select(PortalUser).where(
                    PortalUser.organization_id == organization_id,
                    PortalUser.mobile == payload.mobile.strip(),
                    PortalUser.deleted_at.is_(None),
                )
            )
        ).scalar_one_or_none()
        if existing is not None:
            raise BadRequestException(
                "A portal user already exists for this mobile number",
                error_code="PORTAL_USER_EXISTS",
            )

        entity_ids = payload.linked_entity_ids or []
        entities = await self._validate_entities(
            organization_id,
            entity_ids,
            actor_role=actor_role,
        )
        registration_status = self._derive_registration_status(actor_role, entities)

        user = PortalUser(
            organization_id=organization_id,
            customer_id=None,
            mobile=payload.mobile.strip(),
            email=(payload.email or "").strip() or None,
            registration_authorized_signatory_name=payload.display_name.strip(),
            preferred_language=payload.preferred_language,
            status=status,
            actor_role=actor_role,
            registration_status=registration_status,
            registered_at=datetime.now(UTC),
            approved_at=(
                datetime.now(UTC)
                if registration_status == PortalRegistrationStatus.ACTIVE
                else None
            ),
            approved_by=(
                current_user_id if registration_status == PortalRegistrationStatus.ACTIVE else None
            ),
            created_by=current_user_id,
        )
        self.db.add(user)
        await self.db.flush()

        await self._sync_entity_links(
            organization_id=organization_id,
            portal_user=user,
            entity_ids=entity_ids,
            current_user_id=current_user_id,
        )
        await self._sync_entity_contacts_for_portal_user(
            portal_user=user,
            entities=entities,
            current_user_id=current_user_id,
        )
        await self.db.flush()
        await self.db.refresh(user)
        user = await self._get_user(organization_id, user.id)
        return self._to_detail(user)

    async def update_user(
        self,
        *,
        organization_id: UUID,
        current_user_id: UUID,
        portal_user_id: UUID,
        payload: AdminPortalUserUpdateRequest,
    ) -> AdminPortalUserDetail:
        user = await self._get_user(organization_id, portal_user_id)

        actor_role = (
            self._parse_actor_role(payload.actor_role)
            if payload.actor_role is not None
            else self._parse_actor_role(
                user.actor_role.value if hasattr(user.actor_role, "value") else str(user.actor_role)
            )
        )
        if payload.email is not None:
            user.email = payload.email.strip() or None
        if payload.display_name is not None:
            user.registration_authorized_signatory_name = payload.display_name.strip()
        if payload.preferred_language is not None:
            user.preferred_language = payload.preferred_language
        if payload.status is not None:
            user.status = self._parse_status(payload.status)
        user.actor_role = actor_role

        entity_ids = (
            payload.linked_entity_ids
            if payload.linked_entity_ids is not None
            else [
                link.entity_id
                for link in user.entities
                if link.deleted_at is None and link.is_link_active
            ]
        )
        entities = await self._validate_entities(
            organization_id,
            entity_ids,
            actor_role=actor_role,
        )
        user.registration_status = self._derive_registration_status(actor_role, entities)
        if user.registration_status == PortalRegistrationStatus.ACTIVE:
            user.approved_at = user.approved_at or datetime.now(UTC)
            user.approved_by = user.approved_by or current_user_id
        else:
            user.approved_at = None
            user.approved_by = None

        if payload.linked_entity_ids is not None:
            await self._sync_entity_links(
                organization_id=organization_id,
                portal_user=user,
                entity_ids=entity_ids,
                current_user_id=current_user_id,
            )
        await self._sync_entity_contacts_for_portal_user(
            portal_user=user,
            entities=entities,
            current_user_id=current_user_id,
        )
        user.updated_by = current_user_id
        await self.db.flush()
        user = await self._get_user(organization_id, portal_user_id)
        return self._to_detail(user)

    async def issue_invite(
        self,
        *,
        organization_id: UUID,
        current_user_id: UUID,
        portal_user_id: UUID,
    ) -> AdminPortalInviteResponse:
        user = await self._get_user(organization_id, portal_user_id)
        invite = await PortalAuthService(self.db).issue_activation_invite(
            user=user,
            invited_by=current_user_id,
        )
        await self.db.flush()
        return AdminPortalInviteResponse(
            portal_user_id=user.id,
            email=invite["email"],
            invite_expires_at=invite["invite_expires_at"],
            activation_token=invite["activation_token"],
            activation_url=invite["activation_url"],
        )

    async def _get_user(
        self,
        organization_id: UUID,
        portal_user_id: UUID,
    ) -> PortalUser:
        stmt = (
            select(PortalUser)
            .options(selectinload(PortalUser.entities).selectinload(PortalUserEntity.entity))
            .where(
                PortalUser.id == portal_user_id,
                PortalUser.organization_id == organization_id,
                PortalUser.deleted_at.is_(None),
            )
        )
        user = (await self.db.execute(stmt)).scalar_one_or_none()
        if user is None:
            raise NotFoundException(
                "Portal user not found",
                error_code="PORTAL_USER_NOT_FOUND",
            )
        return user

    async def _validate_entities(
        self,
        organization_id: UUID,
        entity_ids: list[UUID],
        *,
        actor_role: PortalActorRole | None = None,
    ) -> list[Entity]:
        if not entity_ids:
            return []
        stmt = select(Entity).where(
            Entity.id.in_(entity_ids),
            Entity.organization_id == organization_id,
            Entity.deleted_at.is_(None),
        )
        entities = list((await self.db.execute(stmt)).scalars().all())
        if len(entities) != len(set(entity_ids)):
            raise BadRequestException(
                "One or more entity links are invalid for this tenant",
                error_code="ENTITY_CROSS_TENANT",
            )
        if actor_role == PortalActorRole.SCHEME_BORROWER:
            invalid = [
                entity.legal_name
                for entity in entities
                if entity.entity_type == EntityType.INDIVIDUAL
            ]
            if invalid:
                raise BadRequestException(
                    "Borrower portal users can only be linked to institutional entities",
                    error_code="SCHEME_ENTITY_TYPE_INVALID",
                )
        return entities

    async def _sync_entity_links(
        self,
        *,
        organization_id: UUID,
        portal_user: PortalUser,
        entity_ids: list[UUID],
        current_user_id: UUID,
    ) -> None:
        desired = set(entity_ids)
        existing_by_entity = {
            link.entity_id: link for link in portal_user.entities if link.deleted_at is None
        }
        for entity_id, link in existing_by_entity.items():
            if entity_id not in desired:
                link.is_link_active = False
                link.updated_by = current_user_id
        for entity_id in desired:
            existing = existing_by_entity.get(entity_id)
            if existing is not None:
                existing.is_link_active = True
                existing.updated_by = current_user_id
                continue
            self.db.add(
                PortalUserEntity(
                    organization_id=organization_id,
                    portal_user_id=portal_user.id,
                    entity_id=entity_id,
                    granted_at=datetime.now(UTC),
                    granted_by=current_user_id,
                    is_link_active=True,
                    created_by=current_user_id,
                )
            )

    async def _sync_entity_contacts_for_portal_user(
        self,
        *,
        portal_user: PortalUser,
        entities: list[Entity],
        current_user_id: UUID,
    ) -> None:
        actor_role = self._parse_actor_role(
            portal_user.actor_role.value
            if hasattr(portal_user.actor_role, "value")
            else str(portal_user.actor_role)
        )
        if actor_role != PortalActorRole.SCHEME_BORROWER:
            return

        first_name, last_name = self._split_contact_name(
            portal_user.registration_authorized_signatory_name,
            portal_user.email or portal_user.mobile,
        )
        registration_status = (
            portal_user.registration_status.value
            if hasattr(portal_user.registration_status, "value")
            else str(portal_user.registration_status)
        )
        is_kyc_verified = registration_status == PortalRegistrationStatus.ACTIVE.value
        for entity in entities:
            identity_filters = []
            if portal_user.email:
                identity_filters.append(EntityContact.email == portal_user.email)
            if portal_user.mobile:
                identity_filters.append(EntityContact.mobile == portal_user.mobile)

            stmt = select(EntityContact).where(
                EntityContact.entity_id == entity.id,
                EntityContact.deleted_at.is_(None),
            )
            if identity_filters:
                stmt = stmt.where(or_(*identity_filters))
            else:
                stmt = stmt.where(
                    EntityContact.first_name == first_name,
                    EntityContact.last_name == last_name,
                )

            contact = (await self.db.execute(stmt)).scalar_one_or_none()
            if contact is None:
                self.db.add(
                    EntityContact(
                        entity_id=entity.id,
                        contact_type=ContactType.AUTHORIZED_SIGNATORY,
                        first_name=first_name,
                        last_name=last_name,
                        designation="Authorized Signatory",
                        email=portal_user.email,
                        mobile=portal_user.mobile,
                        is_primary=True,
                        is_authorized_signatory=True,
                        kyc_verified=is_kyc_verified,
                        created_by=current_user_id,
                    )
                )
                continue

            contact.first_name = first_name
            contact.last_name = last_name
            contact.email = portal_user.email
            contact.mobile = portal_user.mobile
            contact.contact_type = ContactType.AUTHORIZED_SIGNATORY
            contact.designation = contact.designation or "Authorized Signatory"
            contact.is_primary = True
            contact.is_authorized_signatory = True
            contact.kyc_verified = is_kyc_verified
            contact.is_active = True
            contact.updated_by = current_user_id

    def _split_contact_name(
        self,
        name: str | None,
        fallback: str,
    ) -> tuple[str, str]:
        raw = (name or fallback).strip() or "Portal User"
        parts = raw.split()
        if len(parts) == 1:
            return parts[0], "-"
        return parts[0], " ".join(parts[1:])

    def _derive_registration_status(
        self,
        actor_role: PortalActorRole,
        entities: list[Entity],
    ) -> PortalRegistrationStatus:
        if actor_role != PortalActorRole.SCHEME_BORROWER:
            return PortalRegistrationStatus.ACTIVE
        return (
            PortalRegistrationStatus.ACTIVE
            if entities
            else PortalRegistrationStatus.PENDING_APPROVAL
        )

    def _parse_actor_role(self, raw: str) -> PortalActorRole:
        try:
            return PortalActorRole(raw)
        except ValueError as exc:
            raise BadRequestException(
                "Invalid portal actor role",
                error_code="INVALID_PORTAL_ACTOR_ROLE",
            ) from exc

    def _parse_status(self, raw: str) -> PortalUserStatus:
        try:
            return PortalUserStatus(raw)
        except ValueError as exc:
            raise BadRequestException(
                "Invalid portal user status",
                error_code="INVALID_PORTAL_USER_STATUS",
            ) from exc

    def _to_list_item(self, user: PortalUser) -> AdminPortalUserListItem:
        links = [
            AdminPortalUserEntityLink(
                entity_id=link.entity_id,
                legal_name=link.entity.legal_name,
            )
            for link in user.entities
            if link.deleted_at is None and link.is_link_active and link.entity is not None
        ]
        actor_role = (
            user.actor_role.value if hasattr(user.actor_role, "value") else str(user.actor_role)
        )
        status = user.status.value if hasattr(user.status, "value") else str(user.status)
        registration_status = (
            user.registration_status.value
            if hasattr(user.registration_status, "value")
            else str(user.registration_status)
        )
        return AdminPortalUserListItem(
            portal_user_id=user.id,
            mobile=user.mobile,
            email=user.email,
            display_name=user.registration_authorized_signatory_name,
            actor_role=actor_role,
            registration_status=registration_status,
            status=status,
            linked_entity_ids=[link.entity_id for link in links],
            linked_entities=links,
            last_login_at=user.last_login_at,
            created_at=user.created_at,
        )

    def _to_detail(self, user: PortalUser) -> AdminPortalUserDetail:
        base = self._to_list_item(user)
        return AdminPortalUserDetail(
            **base.model_dump(),
            preferred_language=user.preferred_language,
            approved_at=user.approved_at,
            approved_by=user.approved_by,
            mobile_verified=user.mobile_verified,
            email_verified=user.email_verified,
            is_2fa_enabled=user.is_2fa_enabled,
            password_login_enabled=bool(user.password_hash),
            invite_pending=bool(user.invite_token_hash and user.invite_token_expires_at),
            invited_at=user.invited_at,
            invite_expires_at=user.invite_token_expires_at,
            activated_at=user.activated_at,
        )

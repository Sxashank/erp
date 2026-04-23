"""Account Group service."""

from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ConflictException, BadRequestException
from app.models.finance.account_group import AccountGroup
from app.repositories.finance.account_group_repo import AccountGroupRepository
from app.repositories.masters.organization_repo import OrganizationRepository
from app.schemas.finance.account_group import AccountGroupCreate, AccountGroupUpdate


class AccountGroupService:
    """Service for account group management."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = AccountGroupRepository(session)
        self.org_repo = OrganizationRepository(session)

    async def create(
        self,
        data: AccountGroupCreate,
        created_by: Optional[UUID] = None,
    ) -> AccountGroup:
        """Create a new account group."""
        # Check if code exists in organization
        if await self.repo.code_exists(data.code, data.organization_id):
            raise ConflictException(f"Account group code '{data.code}' already exists")

        # Verify organization exists
        org = await self.org_repo.get(data.organization_id)
        if not org:
            raise NotFoundException("Organization not found")

        # Verify parent group if provided
        level = 0
        path = None
        if data.parent_group_id:
            parent = await self.repo.get(data.parent_group_id)
            if not parent:
                raise NotFoundException("Parent account group not found")
            if parent.organization_id != data.organization_id:
                raise BadRequestException(
                    "Parent account group must belong to the same organization"
                )
            # Inherit nature from parent
            if parent.nature != data.nature:
                raise BadRequestException(
                    f"Account group nature must match parent nature ({parent.nature.value})"
                )
            level = parent.level + 1
            path = f"{parent.path or ''}/{parent.id}"

        group_data = data.model_dump()
        group_data["created_by"] = created_by
        group_data["level"] = level
        group_data["path"] = path

        return await self.repo.create(group_data)

    async def update(
        self,
        id: UUID,
        data: AccountGroupUpdate,
        updated_by: Optional[UUID] = None,
    ) -> AccountGroup:
        """Update an account group."""
        group = await self.repo.get(id)
        if not group:
            raise NotFoundException("Account group not found")

        if group.is_system:
            raise BadRequestException("Cannot update system-defined account group")

        # Check code uniqueness if being updated
        if data.code and data.code != group.code:
            if await self.repo.code_exists(data.code, group.organization_id, exclude_id=id):
                raise ConflictException(f"Account group code '{data.code}' already exists")

        # Handle parent change
        if data.parent_group_id is not None:
            if data.parent_group_id == id:
                raise BadRequestException("Account group cannot be its own parent")

            parent = await self.repo.get(data.parent_group_id)
            if parent:
                if parent.organization_id != group.organization_id:
                    raise BadRequestException(
                        "Parent account group must belong to the same organization"
                    )
                # Check for circular reference
                if parent.path and str(id) in parent.path:
                    raise BadRequestException("Cannot set a child group as parent")

        update_data = data.model_dump(exclude_unset=True)
        update_data["updated_by"] = updated_by

        group = await self.repo.update(group, update_data)

        # Update hierarchy if parent changed
        if data.parent_group_id is not None:
            await self.repo.update_hierarchy(group)

        return group

    async def get(self, id: UUID) -> AccountGroup:
        """Get account group by ID."""
        group = await self.repo.get_with_children(id)
        if not group:
            raise NotFoundException("Account group not found")
        return group

    async def get_all(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
    ) -> Tuple[List[AccountGroup], int]:
        """Get all account groups for an organization."""
        groups = await self.repo.get_by_organization(organization_id, include_inactive)
        # Enrich with account counts
        for group in groups:
            group.account_count = await self.repo.get_account_count(group.id)
        total = len(groups)
        return groups[skip:skip + limit], total

    async def get_tree(self, organization_id: UUID) -> List[dict]:
        """Get account group hierarchy tree."""
        groups = await self.repo.get_by_organization(organization_id, include_inactive=False)

        # Build a lookup map by id
        group_map = {}
        for group in groups:
            account_count = await self.repo.get_account_count(group.id)
            group_map[group.id] = {
                "id": group.id,
                "code": group.code,
                "name": group.name,
                "nature": group.nature.value,
                "level": group.level,
                "sequence": group.sequence,
                "is_system": group.is_system,
                "account_count": account_count,
                "parent_group_id": group.parent_group_id,
                "children": [],
            }

        # Build the tree
        root_groups = []
        for group_id, group_data in group_map.items():
            parent_id = group_data.pop("parent_group_id")
            if parent_id is None:
                root_groups.append(group_data)
            elif parent_id in group_map:
                group_map[parent_id]["children"].append(group_data)

        # Sort by sequence
        def sort_tree(nodes):
            nodes.sort(key=lambda x: (x["sequence"], x["code"]))
            for node in nodes:
                sort_tree(node["children"])

        sort_tree(root_groups)
        return root_groups

    async def get_children(self, id: UUID) -> List[AccountGroup]:
        """Get child account groups."""
        return await self.repo.get_children(id)

    async def delete(
        self,
        id: UUID,
        deleted_by: Optional[UUID] = None,
    ) -> AccountGroup:
        """Soft delete an account group."""
        group = await self.repo.get(id)
        if not group:
            raise NotFoundException("Account group not found")

        if group.is_system:
            raise BadRequestException("Cannot delete system-defined account group")

        # Check if has children
        if await self.repo.has_children(id):
            raise BadRequestException("Cannot delete account group with child groups")

        # Check if has accounts
        if await self.repo.has_accounts(id):
            raise BadRequestException("Cannot delete account group with accounts")

        return await self.repo.soft_delete(id, deleted_by)

"""Folder management service."""

import logging
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dms import (
    DMSFolder,
    DMSFolderAccess,
    DocumentAccessLevel,
)

logger = logging.getLogger(__name__)


class FolderService:
    """Service for managing folders."""

    def __init__(self, db: AsyncSession):
        """Initialize folder service."""
        self.db = db

    async def create_folder(
        self,
        organization_id: UUID,
        name: str,
        parent_id: Optional[UUID] = None,
        description: Optional[str] = None,
        folder_type: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[UUID] = None,
        access_level: DocumentAccessLevel = DocumentAccessLevel.ORGANIZATION,
        color: Optional[str] = None,
        icon: Optional[str] = None,
        created_by: Optional[UUID] = None,
    ) -> DMSFolder:
        """
        Create a new folder.

        Args:
            organization_id: Organization ID
            name: Folder name
            parent_id: Parent folder ID (for nested folders)
            description: Folder description
            folder_type: Type of folder
            entity_type: Linked entity type
            entity_id: Linked entity ID
            access_level: Access level
            color: Display color
            icon: Display icon
            created_by: User creating the folder

        Returns:
            Created folder
        """
        # Determine path and level
        if parent_id:
            parent = await self.get_folder(parent_id)
            if parent:
                path = f"{parent.path}/{name}"
                level = parent.level + 1
            else:
                path = f"/{name}"
                level = 0
        else:
            path = f"/{name}"
            level = 0

        folder = DMSFolder(
            organization_id=organization_id,
            parent_id=parent_id,
            name=name,
            description=description,
            path=path,
            level=level,
            folder_type=folder_type,
            entity_type=entity_type,
            entity_id=entity_id,
            access_level=access_level.value if isinstance(access_level, DocumentAccessLevel) else access_level,
            color=color,
            icon=icon,
            created_by=created_by,
        )

        self.db.add(folder)
        await self.db.commit()
        await self.db.refresh(folder)

        return folder

    async def get_folder(self, folder_id: UUID) -> Optional[DMSFolder]:
        """Get folder by ID."""
        result = await self.db.execute(
            select(DMSFolder).where(
                DMSFolder.id == folder_id,
                DMSFolder.is_active == True,
            )
        )
        return result.scalar_one_or_none()

    async def list_folders(
        self,
        organization_id: UUID,
        parent_id: Optional[UUID] = None,
        folder_type: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[UUID] = None,
    ) -> List[DMSFolder]:
        """List folders with filters."""
        conditions = [
            DMSFolder.organization_id == organization_id,
            DMSFolder.is_active == True,
        ]

        if parent_id:
            conditions.append(DMSFolder.parent_id == parent_id)
        else:
            conditions.append(DMSFolder.parent_id.is_(None))

        if folder_type:
            conditions.append(DMSFolder.folder_type == folder_type)
        if entity_type:
            conditions.append(DMSFolder.entity_type == entity_type)
        if entity_id:
            conditions.append(DMSFolder.entity_id == entity_id)

        result = await self.db.execute(
            select(DMSFolder)
            .where(and_(*conditions))
            .order_by(DMSFolder.sort_order, DMSFolder.name)
        )
        return list(result.scalars().all())

    async def get_folder_tree(
        self,
        organization_id: UUID,
        root_folder_id: Optional[UUID] = None,
        max_depth: int = 10,
    ) -> List[dict]:
        """
        Get folder tree structure.

        Returns:
            List of folder dictionaries with nested children
        """
        # Get root folders or children of specified folder
        conditions = [
            DMSFolder.organization_id == organization_id,
            DMSFolder.is_active == True,
        ]

        if root_folder_id:
            conditions.append(DMSFolder.parent_id == root_folder_id)
        else:
            conditions.append(DMSFolder.parent_id.is_(None))

        result = await self.db.execute(
            select(DMSFolder)
            .where(and_(*conditions))
            .order_by(DMSFolder.sort_order, DMSFolder.name)
        )
        folders = list(result.scalars().all())

        # Build tree recursively
        tree = []
        for folder in folders:
            node = await self._build_tree_node(folder, max_depth, 1)
            tree.append(node)

        return tree

    async def _build_tree_node(
        self,
        folder: DMSFolder,
        max_depth: int,
        current_depth: int,
    ) -> dict:
        """Build a tree node with children."""
        node = {
            "id": str(folder.id),
            "name": folder.name,
            "path": folder.path,
            "level": folder.level,
            "folder_type": folder.folder_type,
            "color": folder.color,
            "icon": folder.icon,
            "document_count": folder.document_count,
            "children": [],
        }

        if current_depth < max_depth:
            result = await self.db.execute(
                select(DMSFolder).where(
                    DMSFolder.parent_id == folder.id,
                    DMSFolder.is_active == True,
                ).order_by(DMSFolder.sort_order, DMSFolder.name)
            )
            children = list(result.scalars().all())

            for child in children:
                child_node = await self._build_tree_node(child, max_depth, current_depth + 1)
                node["children"].append(child_node)

        return node

    async def update_folder(
        self,
        folder_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        color: Optional[str] = None,
        icon: Optional[str] = None,
        access_level: Optional[DocumentAccessLevel] = None,
        updated_by: Optional[UUID] = None,
    ) -> Optional[DMSFolder]:
        """Update folder metadata."""
        folder = await self.get_folder(folder_id)
        if not folder:
            return None

        old_name = folder.name

        if name is not None:
            folder.name = name
            # Update path if name changed
            if name != old_name:
                await self._update_folder_path(folder)
        if description is not None:
            folder.description = description
        if color is not None:
            folder.color = color
        if icon is not None:
            folder.icon = icon
        if access_level is not None:
            folder.access_level = access_level.value if isinstance(access_level, DocumentAccessLevel) else access_level

        folder.updated_by = updated_by

        await self.db.commit()
        await self.db.refresh(folder)

        return folder

    async def _update_folder_path(self, folder: DMSFolder) -> None:
        """Update folder path and all children paths."""
        if folder.parent_id:
            parent = await self.get_folder(folder.parent_id)
            if parent:
                folder.path = f"{parent.path}/{folder.name}"
        else:
            folder.path = f"/{folder.name}"

        # Update children paths recursively
        result = await self.db.execute(
            select(DMSFolder).where(DMSFolder.parent_id == folder.id)
        )
        children = list(result.scalars().all())
        for child in children:
            child.path = f"{folder.path}/{child.name}"
            await self._update_folder_path(child)

    async def move_folder(
        self,
        folder_id: UUID,
        new_parent_id: Optional[UUID],
        updated_by: Optional[UUID] = None,
    ) -> Optional[DMSFolder]:
        """Move folder to a new parent."""
        folder = await self.get_folder(folder_id)
        if not folder:
            return None

        # Can't move to self or descendant
        if new_parent_id:
            if new_parent_id == folder_id:
                return None
            # Check if new parent is a descendant
            if folder.path and new_parent_id:
                new_parent = await self.get_folder(new_parent_id)
                if new_parent and new_parent.path.startswith(folder.path):
                    return None

        folder.parent_id = new_parent_id
        folder.updated_by = updated_by

        # Update paths
        await self._update_folder_path(folder)

        await self.db.commit()
        await self.db.refresh(folder)

        return folder

    async def delete_folder(
        self,
        folder_id: UUID,
        deleted_by: Optional[UUID] = None,
        recursive: bool = False,
    ) -> bool:
        """
        Delete folder.

        Args:
            folder_id: Folder ID
            deleted_by: User deleting the folder
            recursive: If True, delete all children as well

        Returns:
            True if deleted
        """
        folder = await self.get_folder(folder_id)
        if not folder:
            return False

        if recursive:
            # Delete all children recursively
            await self._delete_children(folder_id, deleted_by)

        # Soft delete folder
        folder.soft_delete(deleted_by)
        await self.db.commit()

        return True

    async def _delete_children(
        self,
        folder_id: UUID,
        deleted_by: Optional[UUID],
    ) -> None:
        """Recursively delete all children of a folder."""
        result = await self.db.execute(
            select(DMSFolder).where(DMSFolder.parent_id == folder_id)
        )
        children = list(result.scalars().all())

        for child in children:
            await self._delete_children(child.id, deleted_by)
            child.soft_delete(deleted_by)

    async def update_document_count(
        self,
        folder_id: UUID,
        delta: int,
    ) -> None:
        """Update document count for a folder."""
        folder = await self.get_folder(folder_id)
        if folder:
            folder.document_count = max(0, folder.document_count + delta)
            await self.db.commit()

    async def grant_access(
        self,
        folder_id: UUID,
        user_id: Optional[UUID] = None,
        role_id: Optional[UUID] = None,
        department_id: Optional[UUID] = None,
        can_view: bool = True,
        can_upload: bool = False,
        can_create_subfolder: bool = False,
        can_edit: bool = False,
        can_delete: bool = False,
        expires_at: Optional[str] = None,
        granted_by: Optional[UUID] = None,
    ) -> DMSFolderAccess:
        """Grant access to a folder."""
        access = DMSFolderAccess(
            folder_id=folder_id,
            user_id=user_id,
            role_id=role_id,
            department_id=department_id,
            can_view=can_view,
            can_upload=can_upload,
            can_create_subfolder=can_create_subfolder,
            can_edit=can_edit,
            can_delete=can_delete,
            expires_at=expires_at,
            created_by=granted_by,
        )
        self.db.add(access)
        await self.db.commit()
        await self.db.refresh(access)
        return access

    async def revoke_access(
        self,
        folder_id: UUID,
        user_id: Optional[UUID] = None,
        role_id: Optional[UUID] = None,
    ) -> bool:
        """Revoke access to a folder."""
        conditions = [DMSFolderAccess.folder_id == folder_id]
        if user_id:
            conditions.append(DMSFolderAccess.user_id == user_id)
        if role_id:
            conditions.append(DMSFolderAccess.role_id == role_id)

        result = await self.db.execute(
            select(DMSFolderAccess).where(and_(*conditions))
        )
        access = result.scalar_one_or_none()

        if access:
            await self.db.delete(access)
            await self.db.commit()
            return True
        return False

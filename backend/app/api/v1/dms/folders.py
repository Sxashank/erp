"""DMS Folders API endpoints."""

import logging
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user, get_db_with_tenant
from app.models.auth.user import User
from app.models.dms import DocumentAccessLevel
from app.services.dms import FolderService
from app.schemas.dms.folder import (
    FolderCreate,
    FolderUpdate,
    FolderResponse,
    FolderTreeResponse,
    FolderMoveRequest,
    FolderAccessCreate,
    FolderAccessResponse,
    FolderListResponse,
)
from app.core.exceptions import BadRequestException, NotFoundException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/folders", tags=["DMS Folders"])


@router.post("", response_model=FolderResponse, response_model_by_alias=True, status_code=status.HTTP_201_CREATED)
async def create_folder(
    data: FolderCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Create a new folder."""
    service = FolderService(db)

    # Parse access level
    try:
        access_level_enum = DocumentAccessLevel(data.access_level)
    except ValueError:
        access_level_enum = DocumentAccessLevel.ORGANIZATION

    folder = await service.create_folder(
        organization_id=current_user.organization_id,
        name=data.name,
        parent_id=data.parent_id,
        description=data.description,
        folder_type=data.folder_type,
        entity_type=data.entity_type,
        entity_id=data.entity_id,
        access_level=access_level_enum,
        color=data.color,
        icon=data.icon,
        created_by=current_user.id,
    )

    return folder


@router.get("", response_model=List[FolderResponse], response_model_by_alias=True)
async def list_folders(
    parent_id: Optional[UUID] = Query(None),
    folder_type: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """List folders with filters."""
    service = FolderService(db)
    folders = await service.list_folders(
        organization_id=current_user.organization_id,
        parent_id=parent_id,
        folder_type=folder_type,
        entity_type=entity_type,
        entity_id=entity_id,
    )
    return folders


@router.get("/tree", response_model=List[FolderTreeResponse], response_model_by_alias=True)
async def get_folder_tree(
    root_folder_id: Optional[UUID] = Query(None),
    max_depth: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Get folder tree structure."""
    service = FolderService(db)
    tree = await service.get_folder_tree(
        organization_id=current_user.organization_id,
        root_folder_id=root_folder_id,
        max_depth=max_depth,
    )
    return tree


@router.get("/{folder_id}", response_model=FolderResponse, response_model_by_alias=True)
async def get_folder(
    folder_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Get a specific folder."""
    service = FolderService(db)
    folder = await service.get_folder(folder_id)
    if not folder:
        raise NotFoundException(detail="Folder not found", error_code="FOLDER_NOT_FOUND")
    return folder


@router.patch("/{folder_id}", response_model=FolderResponse, response_model_by_alias=True)
async def update_folder(
    folder_id: UUID,
    data: FolderUpdate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Update folder metadata."""
    service = FolderService(db)

    # Parse access level if provided
    access_level_enum = None
    if data.access_level:
        try:
            access_level_enum = DocumentAccessLevel(data.access_level)
        except ValueError:
            pass

    folder = await service.update_folder(
        folder_id=folder_id,
        name=data.name,
        description=data.description,
        color=data.color,
        icon=data.icon,
        access_level=access_level_enum,
        updated_by=current_user.id,
    )
    if not folder:
        raise NotFoundException(detail="Folder not found", error_code="FOLDER_NOT_FOUND")
    return folder


@router.post("/{folder_id}/move", response_model=FolderResponse, response_model_by_alias=True)
async def move_folder(
    folder_id: UUID,
    data: FolderMoveRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Move folder to a new parent."""
    service = FolderService(db)
    folder = await service.move_folder(
        folder_id=folder_id,
        new_parent_id=data.new_parent_id,
        updated_by=current_user.id,
    )
    if not folder:
        raise BadRequestException(
            detail="Cannot move folder to specified location",
            error_code="CANNOT_MOVE_FOLDER_TO_SPECIFIED_LOCATION",
        )
    return folder


@router.delete("/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_folder(
    folder_id: UUID,
    recursive: bool = Query(False),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Delete a folder."""
    service = FolderService(db)
    success = await service.delete_folder(
        folder_id=folder_id,
        deleted_by=current_user.id,
        recursive=recursive,
    )
    if not success:
        raise NotFoundException(detail="Folder not found", error_code="FOLDER_NOT_FOUND")


@router.post("/{folder_id}/access", response_model=FolderAccessResponse, response_model_by_alias=True, status_code=status.HTTP_201_CREATED)
async def grant_folder_access(
    folder_id: UUID,
    data: FolderAccessCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Grant access to a folder."""
    service = FolderService(db)
    access = await service.grant_access(
        folder_id=folder_id,
        user_id=data.user_id,
        role_id=data.role_id,
        department_id=data.department_id,
        can_view=data.can_view,
        can_upload=data.can_upload,
        can_create_subfolder=data.can_create_subfolder,
        can_edit=data.can_edit,
        can_delete=data.can_delete,
        expires_at=data.expires_at.isoformat() if data.expires_at else None,
        granted_by=current_user.id,
    )
    return access


@router.delete("/{folder_id}/access", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_folder_access(
    folder_id: UUID,
    user_id: Optional[UUID] = Query(None),
    role_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Revoke access from a folder."""
    service = FolderService(db)
    success = await service.revoke_access(
        folder_id=folder_id,
        user_id=user_id,
        role_id=role_id,
    )
    if not success:
        raise NotFoundException(detail="Access record not found", error_code="ACCESS_RECORD_NOT_FOUND")


@router.get("/{folder_id}/documents")
async def get_folder_documents(
    folder_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Get documents in a folder."""
    from app.services.dms import DocumentService

    service = DocumentService(db)
    documents, total = await service.list_documents(
        organization_id=current_user.organization_id,
        folder_id=folder_id,
        skip=skip,
        limit=limit,
    )
    return {
        "items": documents,
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/{folder_id}/children", response_model=List[FolderResponse], response_model_by_alias=True)
async def get_folder_children(
    folder_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Get child folders of a folder."""
    service = FolderService(db)
    folders = await service.list_folders(
        organization_id=current_user.organization_id,
        parent_id=folder_id,
    )
    return folders

"""DMS Documents API endpoints."""

import logging
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.auth.user import User
from app.models.dms import DocumentStatus, DocumentAccessLevel
from app.services.dms import DocumentService, SearchService
from app.schemas.dms.document import (
    DocumentCreate,
    DocumentUpdate,
    DocumentResponse,
    DocumentListResponse,
    DocumentVersionResponse,
    DocumentHistoryResponse,
    DocumentDownloadResponse,
    DocumentStatsResponse,
    NewVersionCreate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["DMS Documents"])


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    folder_id: Optional[UUID] = Form(None),
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    document_type: Optional[str] = Form(None),
    document_subtype: Optional[str] = Form(None),
    entity_type: Optional[str] = Form(None),
    entity_id: Optional[UUID] = Form(None),
    access_level: str = Form("organization"),
    keywords: Optional[str] = Form(None),  # Comma-separated
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a new document."""
    try:
        service = DocumentService(db)

        # Parse keywords
        keyword_list = None
        if keywords:
            keyword_list = [k.strip() for k in keywords.split(",") if k.strip()]

        # Parse access level
        try:
            access_level_enum = DocumentAccessLevel(access_level)
        except ValueError:
            access_level_enum = DocumentAccessLevel.ORGANIZATION

        document = await service.upload_document(
            organization_id=current_user.organization_id,
            file=file.file,
            file_name=file.filename,
            file_size=file.size or 0,
            mime_type=file.content_type or "application/octet-stream",
            folder_id=folder_id,
            name=name,
            description=description,
            document_type=document_type,
            document_subtype=document_subtype,
            entity_type=entity_type,
            entity_id=entity_id,
            access_level=access_level_enum,
            keywords=keyword_list,
            created_by=current_user.id,
        )

        return document
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload document",
        )


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    folder_id: Optional[UUID] = Query(None),
    document_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[UUID] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List documents with filters."""
    service = DocumentService(db)

    # Parse status
    status_enum = None
    if status:
        try:
            status_enum = DocumentStatus(status)
        except ValueError:
            pass

    documents, total = await service.list_documents(
        organization_id=current_user.organization_id,
        folder_id=folder_id,
        document_type=document_type,
        status=status_enum,
        entity_type=entity_type,
        entity_id=entity_id,
        search=search,
        skip=skip,
        limit=limit,
    )

    return DocumentListResponse(
        items=documents,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/search", response_model=DocumentListResponse)
async def search_documents(
    query: Optional[str] = Query(None),
    folder_id: Optional[UUID] = Query(None),
    document_type: Optional[str] = Query(None),
    document_subtype: Optional[str] = Query(None),
    mime_type: Optional[str] = Query(None),
    tags: Optional[str] = Query(None),  # Comma-separated
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[UUID] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    include_archived: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Search documents with various filters."""
    service = SearchService(db)

    # Parse tags
    tag_list = None
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]

    documents, total = await service.search_documents(
        organization_id=current_user.organization_id,
        query=query,
        folder_id=folder_id,
        document_type=document_type,
        document_subtype=document_subtype,
        mime_type=mime_type,
        tags=tag_list,
        entity_type=entity_type,
        entity_id=entity_id,
        date_from=date_from,
        date_to=date_to,
        include_archived=include_archived,
        skip=skip,
        limit=limit,
    )

    return DocumentListResponse(
        items=documents,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/recent")
async def get_recent_documents(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get recently accessed documents."""
    service = SearchService(db)
    documents = await service.get_recent_documents(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        limit=limit,
    )
    return documents


@router.get("/stats", response_model=DocumentStatsResponse)
async def get_document_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get document statistics."""
    service = SearchService(db)
    stats = await service.get_document_stats(
        organization_id=current_user.organization_id,
    )
    return stats


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific document."""
    service = DocumentService(db)
    document = await service.get_document(
        document_id=document_id,
        user_id=current_user.id,
    )
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    return document


@router.patch("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: UUID,
    data: DocumentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update document metadata."""
    service = DocumentService(db)

    # Parse access level if provided
    access_level_enum = None
    if data.access_level:
        try:
            access_level_enum = DocumentAccessLevel(data.access_level)
        except ValueError:
            pass

    document = await service.update_document(
        document_id=document_id,
        name=data.name,
        description=data.description,
        folder_id=data.folder_id,
        document_type=data.document_type,
        document_subtype=data.document_subtype,
        access_level=access_level_enum,
        keywords=data.keywords,
        expiry_date=data.expiry_date,
        updated_by=current_user.id,
    )
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    hard_delete: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a document."""
    service = DocumentService(db)
    success = await service.delete_document(
        document_id=document_id,
        deleted_by=current_user.id,
        hard_delete=hard_delete,
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )


@router.get("/{document_id}/download")
async def download_document(
    document_id: UUID,
    version: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download a document file."""
    service = DocumentService(db)
    result = await service.download_document(
        document_id=document_id,
        user_id=current_user.id,
        version=version,
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    storage_path, file_name, mime_type = result

    # Get full file path
    import os
    full_path = os.path.join(service.upload_path, storage_path)

    if not os.path.exists(full_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on storage",
        )

    return FileResponse(
        path=full_path,
        filename=file_name,
        media_type=mime_type,
    )


@router.post("/{document_id}/versions", response_model=DocumentVersionResponse)
async def upload_new_version(
    document_id: UUID,
    file: UploadFile = File(...),
    change_notes: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a new version of a document."""
    service = DocumentService(db)
    version = await service.upload_new_version(
        document_id=document_id,
        file=file.file,
        file_name=file.filename,
        file_size=file.size or 0,
        mime_type=file.content_type or "application/octet-stream",
        change_notes=change_notes,
        uploaded_by=current_user.id,
    )
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    return version


@router.get("/{document_id}/versions")
async def get_document_versions(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all versions of a document."""
    from sqlalchemy import select
    from app.models.dms import DMSDocumentVersion

    result = await db.execute(
        select(DMSDocumentVersion)
        .where(DMSDocumentVersion.document_id == document_id)
        .order_by(DMSDocumentVersion.version_number.desc())
    )
    versions = list(result.scalars().all())
    return versions


@router.get("/{document_id}/history")
async def get_document_history(
    document_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get document activity history."""
    from sqlalchemy import select
    from app.models.dms import DMSDocumentHistory

    result = await db.execute(
        select(DMSDocumentHistory)
        .where(DMSDocumentHistory.document_id == document_id)
        .order_by(DMSDocumentHistory.performed_at.desc())
        .offset(skip)
        .limit(limit)
    )
    history = list(result.scalars().all())
    return history


@router.post("/{document_id}/tags/{tag_id}", status_code=status.HTTP_201_CREATED)
async def add_tag_to_document(
    document_id: UUID,
    tag_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a tag to a document."""
    service = DocumentService(db)
    success = await service.add_tag(
        document_id=document_id,
        tag_id=tag_id,
        created_by=current_user.id,
    )
    return {"success": success}


@router.delete("/{document_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_tag_from_document(
    document_id: UUID,
    tag_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove a tag from a document."""
    service = DocumentService(db)
    await service.remove_tag(
        document_id=document_id,
        tag_id=tag_id,
    )

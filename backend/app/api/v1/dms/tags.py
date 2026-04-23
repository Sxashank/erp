"""DMS Tags API endpoints."""

import logging
import re
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.auth.user import User
from app.models.dms import DMSTag, DMSDocumentTag
from app.schemas.dms.tag import (
    TagCreate,
    TagUpdate,
    TagResponse,
    TagListResponse,
    TagDocumentsRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tags", tags=["DMS Tags"])


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text


@router.post("", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(
    data: TagCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new tag."""
    # Check for duplicate name
    result = await db.execute(
        select(DMSTag).where(
            DMSTag.organization_id == current_user.organization_id,
            DMSTag.name == data.name,
            DMSTag.is_active == True,
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tag with this name already exists",
        )

    tag = DMSTag(
        organization_id=current_user.organization_id,
        name=data.name,
        slug=slugify(data.name),
        description=data.description,
        color=data.color,
        icon=data.icon,
        category=data.category,
        created_by=current_user.id,
    )

    db.add(tag)
    await db.commit()
    await db.refresh(tag)

    return tag


@router.get("", response_model=TagListResponse)
async def list_tags(
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List tags with filters."""
    conditions = [
        DMSTag.organization_id == current_user.organization_id,
        DMSTag.is_active == True,
    ]

    if category:
        conditions.append(DMSTag.category == category)
    if search:
        conditions.append(DMSTag.name.ilike(f"%{search}%"))

    # Count
    count_result = await db.execute(
        select(func.count()).select_from(DMSTag).where(and_(*conditions))
    )
    total = count_result.scalar()

    # Data
    result = await db.execute(
        select(DMSTag)
        .where(and_(*conditions))
        .order_by(DMSTag.usage_count.desc(), DMSTag.name)
        .offset(skip)
        .limit(limit)
    )
    tags = list(result.scalars().all())

    return TagListResponse(items=tags, total=total)


@router.get("/categories")
async def list_tag_categories(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get list of tag categories."""
    result = await db.execute(
        select(DMSTag.category)
        .where(
            DMSTag.organization_id == current_user.organization_id,
            DMSTag.is_active == True,
            DMSTag.category.isnot(None),
        )
        .distinct()
        .order_by(DMSTag.category)
    )
    categories = [row[0] for row in result.all()]
    return categories


@router.get("/{tag_id}", response_model=TagResponse)
async def get_tag(
    tag_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific tag."""
    result = await db.execute(
        select(DMSTag).where(
            DMSTag.id == tag_id,
            DMSTag.is_active == True,
        )
    )
    tag = result.scalar_one_or_none()
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found",
        )
    return tag


@router.patch("/{tag_id}", response_model=TagResponse)
async def update_tag(
    tag_id: UUID,
    data: TagUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a tag."""
    result = await db.execute(
        select(DMSTag).where(
            DMSTag.id == tag_id,
            DMSTag.is_active == True,
        )
    )
    tag = result.scalar_one_or_none()
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found",
        )

    if data.name is not None:
        # Check for duplicate name
        dup_result = await db.execute(
            select(DMSTag).where(
                DMSTag.organization_id == current_user.organization_id,
                DMSTag.name == data.name,
                DMSTag.id != tag_id,
                DMSTag.is_active == True,
            )
        )
        if dup_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tag with this name already exists",
            )
        tag.name = data.name
        tag.slug = slugify(data.name)

    if data.description is not None:
        tag.description = data.description
    if data.color is not None:
        tag.color = data.color
    if data.icon is not None:
        tag.icon = data.icon
    if data.category is not None:
        tag.category = data.category

    tag.updated_by = current_user.id

    await db.commit()
    await db.refresh(tag)

    return tag


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a tag."""
    result = await db.execute(
        select(DMSTag).where(
            DMSTag.id == tag_id,
            DMSTag.is_active == True,
        )
    )
    tag = result.scalar_one_or_none()
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found",
        )

    # Soft delete
    tag.soft_delete(current_user.id)
    await db.commit()


@router.get("/{tag_id}/documents")
async def get_tag_documents(
    tag_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get documents with a specific tag."""
    from app.models.dms import DMSDocument

    # Get document IDs with this tag
    doc_ids_result = await db.execute(
        select(DMSDocumentTag.document_id).where(
            DMSDocumentTag.tag_id == tag_id
        )
    )
    doc_ids = [row[0] for row in doc_ids_result.all()]

    if not doc_ids:
        return {"items": [], "total": 0, "skip": skip, "limit": limit}

    # Count
    count_result = await db.execute(
        select(func.count()).select_from(DMSDocument).where(
            DMSDocument.id.in_(doc_ids),
            DMSDocument.organization_id == current_user.organization_id,
            DMSDocument.is_active == True,
        )
    )
    total = count_result.scalar()

    # Data
    result = await db.execute(
        select(DMSDocument)
        .where(
            DMSDocument.id.in_(doc_ids),
            DMSDocument.organization_id == current_user.organization_id,
            DMSDocument.is_active == True,
        )
        .order_by(DMSDocument.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    documents = list(result.scalars().all())

    return {
        "items": documents,
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.post("/bulk-tag")
async def bulk_tag_documents(
    data: TagDocumentsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add multiple tags to multiple documents."""
    added = 0

    for doc_id in data.document_ids:
        for tag_id in data.tag_ids:
            # Check if already tagged
            result = await db.execute(
                select(DMSDocumentTag).where(
                    DMSDocumentTag.document_id == doc_id,
                    DMSDocumentTag.tag_id == tag_id,
                )
            )
            if not result.scalar_one_or_none():
                doc_tag = DMSDocumentTag(
                    document_id=doc_id,
                    tag_id=tag_id,
                    created_by=current_user.id,
                )
                db.add(doc_tag)
                added += 1

                # Update tag usage count
                tag_result = await db.execute(
                    select(DMSTag).where(DMSTag.id == tag_id)
                )
                tag = tag_result.scalar_one_or_none()
                if tag:
                    tag.usage_count += 1

    await db.commit()

    return {"added": added}

"""DMS search service."""

import logging
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dms import (
    DMSDocument,
    DMSFolder,
    DMSTag,
    DMSDocumentTag,
    DocumentStatus,
)

logger = logging.getLogger(__name__)


class SearchService:
    """Service for searching documents and folders."""

    def __init__(self, db: AsyncSession):
        """Initialize search service."""
        self.db = db

    async def search_documents(
        self,
        organization_id: UUID,
        query: Optional[str] = None,
        folder_id: Optional[UUID] = None,
        document_type: Optional[str] = None,
        document_subtype: Optional[str] = None,
        mime_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[UUID] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        include_archived: bool = False,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[List[DMSDocument], int]:
        """
        Search documents with various filters.

        Args:
            organization_id: Organization ID
            query: Full-text search query
            folder_id: Filter by folder
            document_type: Filter by document type
            document_subtype: Filter by document subtype
            mime_type: Filter by MIME type
            tags: Filter by tag names
            entity_type: Filter by linked entity type
            entity_id: Filter by linked entity ID
            date_from: Filter by created date from
            date_to: Filter by created date to
            include_archived: Include archived documents
            skip: Pagination offset
            limit: Page size

        Returns:
            Tuple of (documents list, total count)
        """
        conditions = [
            DMSDocument.organization_id == organization_id,
            DMSDocument.is_active == True,
        ]

        # Status filter
        if include_archived:
            conditions.append(
                or_(
                    DMSDocument.status == DocumentStatus.ACTIVE,
                    DMSDocument.status == DocumentStatus.ARCHIVED,
                )
            )
        else:
            conditions.append(DMSDocument.status == DocumentStatus.ACTIVE)

        # Full-text search
        if query:
            search_conditions = [
                DMSDocument.name.ilike(f"%{query}%"),
                DMSDocument.description.ilike(f"%{query}%"),
                DMSDocument.file_name.ilike(f"%{query}%"),
            ]
            # Also search in OCR text if available
            search_conditions.append(DMSDocument.ocr_text.ilike(f"%{query}%"))
            # Search in keywords array
            search_conditions.append(func.array_to_string(DMSDocument.keywords, ' ').ilike(f"%{query}%"))
            conditions.append(or_(*search_conditions))

        # Folder filter
        if folder_id:
            conditions.append(DMSDocument.folder_id == folder_id)

        # Type filters
        if document_type:
            conditions.append(DMSDocument.document_type == document_type)
        if document_subtype:
            conditions.append(DMSDocument.document_subtype == document_subtype)
        if mime_type:
            conditions.append(DMSDocument.mime_type.ilike(f"%{mime_type}%"))

        # Entity filters
        if entity_type:
            conditions.append(DMSDocument.entity_type == entity_type)
        if entity_id:
            conditions.append(DMSDocument.entity_id == entity_id)

        # Date filters
        if date_from:
            conditions.append(DMSDocument.created_at >= date_from)
        if date_to:
            conditions.append(DMSDocument.created_at <= date_to)

        # Base query
        base_query = select(DMSDocument).where(and_(*conditions))

        # Tag filter (requires join)
        if tags:
            tag_result = await self.db.execute(
                select(DMSTag.id).where(
                    DMSTag.organization_id == organization_id,
                    DMSTag.name.in_(tags),
                )
            )
            tag_ids = [row[0] for row in tag_result.all()]

            if tag_ids:
                doc_ids_with_tags = await self.db.execute(
                    select(DMSDocumentTag.document_id)
                    .where(DMSDocumentTag.tag_id.in_(tag_ids))
                    .distinct()
                )
                doc_ids = [row[0] for row in doc_ids_with_tags.all()]
                conditions.append(DMSDocument.id.in_(doc_ids))
                base_query = select(DMSDocument).where(and_(*conditions))

        # Count query
        count_result = await self.db.execute(
            select(func.count()).select_from(DMSDocument).where(and_(*conditions))
        )
        total = count_result.scalar()

        # Data query with pagination
        result = await self.db.execute(
            base_query
            .order_by(DMSDocument.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        documents = list(result.scalars().all())

        return documents, total

    async def search_by_content(
        self,
        organization_id: UUID,
        query: str,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[List[DMSDocument], int]:
        """
        Search documents by OCR/extracted content.

        Args:
            organization_id: Organization ID
            query: Search query
            skip: Pagination offset
            limit: Page size

        Returns:
            Tuple of (documents list, total count)
        """
        conditions = [
            DMSDocument.organization_id == organization_id,
            DMSDocument.is_active == True,
            DMSDocument.status == DocumentStatus.ACTIVE,
            DMSDocument.is_ocr_processed == True,
            DMSDocument.ocr_text.ilike(f"%{query}%"),
        ]

        # Count
        count_result = await self.db.execute(
            select(func.count()).select_from(DMSDocument).where(and_(*conditions))
        )
        total = count_result.scalar()

        # Data
        result = await self.db.execute(
            select(DMSDocument)
            .where(and_(*conditions))
            .order_by(DMSDocument.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        documents = list(result.scalars().all())

        return documents, total

    async def get_recent_documents(
        self,
        organization_id: UUID,
        user_id: UUID,
        limit: int = 10,
    ) -> List[DMSDocument]:
        """Get recently accessed documents for a user."""
        result = await self.db.execute(
            select(DMSDocument).where(
                DMSDocument.organization_id == organization_id,
                DMSDocument.is_active == True,
                DMSDocument.status == DocumentStatus.ACTIVE,
            ).order_by(DMSDocument.last_accessed_at.desc().nullslast())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_document_stats(
        self,
        organization_id: UUID,
    ) -> dict:
        """Get document statistics for an organization."""
        # Total documents
        total_result = await self.db.execute(
            select(func.count()).select_from(DMSDocument).where(
                DMSDocument.organization_id == organization_id,
                DMSDocument.is_active == True,
            )
        )
        total_documents = total_result.scalar()

        # Total size
        size_result = await self.db.execute(
            select(func.sum(DMSDocument.file_size)).where(
                DMSDocument.organization_id == organization_id,
                DMSDocument.is_active == True,
            )
        )
        total_size = size_result.scalar() or 0

        # By type
        type_result = await self.db.execute(
            select(
                DMSDocument.document_type,
                func.count(),
            ).where(
                DMSDocument.organization_id == organization_id,
                DMSDocument.is_active == True,
            ).group_by(DMSDocument.document_type)
        )
        by_type = {row[0] or "other": row[1] for row in type_result.all()}

        # By status
        status_result = await self.db.execute(
            select(
                DMSDocument.status,
                func.count(),
            ).where(
                DMSDocument.organization_id == organization_id,
                DMSDocument.is_active == True,
            ).group_by(DMSDocument.status)
        )
        by_status = {row[0].value: row[1] for row in status_result.all()}

        # By extension
        ext_result = await self.db.execute(
            select(
                DMSDocument.file_extension,
                func.count(),
            ).where(
                DMSDocument.organization_id == organization_id,
                DMSDocument.is_active == True,
            ).group_by(DMSDocument.file_extension)
            .order_by(func.count().desc())
            .limit(10)
        )
        by_extension = {row[0]: row[1] for row in ext_result.all()}

        # Total folders
        folder_result = await self.db.execute(
            select(func.count()).select_from(DMSFolder).where(
                DMSFolder.organization_id == organization_id,
                DMSFolder.is_active == True,
            )
        )
        total_folders = folder_result.scalar()

        return {
            "total_documents": total_documents,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "total_folders": total_folders,
            "by_type": by_type,
            "by_status": by_status,
            "by_extension": by_extension,
        }

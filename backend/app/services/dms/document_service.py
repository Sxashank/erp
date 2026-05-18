"""Document management service."""

import hashlib
import logging
import os
from datetime import UTC, datetime
from typing import BinaryIO
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.dms import (
    DMSDocument,
    DMSDocumentHistory,
    DMSDocumentTag,
    DMSDocumentVersion,
    DocumentAccessLevel,
    DocumentStatus,
)

logger = logging.getLogger(__name__)


class DocumentService:
    """Service for managing documents."""

    def __init__(self, db: AsyncSession):
        """Initialize document service."""
        self.db = db
        self.upload_path = getattr(settings, "UPLOAD_PATH", "uploads")

    async def upload_document(
        self,
        organization_id: UUID,
        file: BinaryIO,
        file_name: str,
        file_size: int,
        mime_type: str,
        folder_id: UUID | None = None,
        name: str | None = None,
        description: str | None = None,
        document_type: str | None = None,
        document_subtype: str | None = None,
        entity_type: str | None = None,
        entity_id: UUID | None = None,
        access_level: DocumentAccessLevel = DocumentAccessLevel.ORGANIZATION,
        keywords: list[str] | None = None,
        expiry_date: datetime | None = None,
        created_by: UUID | None = None,
        auto_commit: bool = True,
    ) -> DMSDocument:
        """
        Upload a new document.

        Args:
            organization_id: Organization ID
            file: File content
            file_name: Original file name
            file_size: File size in bytes
            mime_type: MIME type
            folder_id: Optional folder ID
            name: Document name (defaults to file name)
            description: Document description
            document_type: Document type category
            document_subtype: Document subtype
            entity_type: Linked entity type
            entity_id: Linked entity ID
            access_level: Access level
            keywords: Search keywords
            expiry_date: Document expiry date
            created_by: User uploading the document

        Returns:
            Created document
        """
        # Generate document code
        code = await self._generate_code(organization_id)

        # Get file extension
        file_extension = os.path.splitext(file_name)[1].lower().lstrip(".")

        # Generate storage path
        storage_path = self._generate_storage_path(organization_id, code, file_extension)

        # AV scan before persistence. Done here (rather than inside _save_file)
        # so we never write infected content to disk, even transiently. The
        # `clamav_scan` feature flag selects the backend; when OFF (production
        # default until the sidecar is deployed) this is a no-op.
        # See CLAUDE.md §8.7 and app/core/av_scan.py.
        from app.core.av_scan import enforce_scan

        body = file.read()
        enforce_scan(body)
        from io import BytesIO

        file = BytesIO(body)

        # Save file to storage
        checksum = await self._save_file(file, storage_path)

        # Create document record
        document = DMSDocument(
            organization_id=organization_id,
            folder_id=folder_id,
            code=code,
            name=name or file_name,
            description=description,
            file_name=file_name,
            file_extension=file_extension,
            mime_type=mime_type,
            file_size=file_size,
            storage_path=storage_path,
            storage_provider="local",
            checksum=checksum,
            document_type=document_type,
            document_subtype=document_subtype,
            status=DocumentStatus.ACTIVE,
            access_level=access_level,
            current_version=1,
            entity_type=entity_type,
            entity_id=entity_id,
            keywords=keywords,
            expiry_date=expiry_date,
            created_by=created_by,
        )

        self.db.add(document)
        await self.db.flush()

        # Create initial version
        version = DMSDocumentVersion(
            document_id=document.id,
            version_number=1,
            file_name=file_name,
            file_size=file_size,
            mime_type=mime_type,
            storage_path=storage_path,
            checksum=checksum,
            is_current=True,
            created_by=created_by,
        )
        self.db.add(version)

        # Log history
        await self._log_history(
            document.id,
            "created",
            created_by,
            {"file_name": file_name, "file_size": file_size},
        )

        if auto_commit:
            await self.db.flush()
        else:
            await self.db.flush()
        await self.db.refresh(document)

        return document

    async def get_document(
        self,
        document_id: UUID,
        user_id: UUID | None = None,
    ) -> DMSDocument | None:
        """Get document by ID."""
        result = await self.db.execute(
            select(DMSDocument).where(
                DMSDocument.id == document_id,
                DMSDocument.is_active == True,
            )
        )
        document = result.scalar_one_or_none()

        if document and user_id:
            # Log view
            await self._log_history(document_id, "viewed", user_id)
            document.view_count = (document.view_count or 0) + 1
            document.last_accessed_at = datetime.now(UTC)
            await self.db.flush()
            await self.db.refresh(document)

        return document

    async def list_documents(
        self,
        organization_id: UUID,
        folder_id: UUID | None = None,
        document_type: str | None = None,
        status: DocumentStatus | None = None,
        entity_type: str | None = None,
        entity_id: UUID | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[DMSDocument], int]:
        """
        List documents with filters.

        Returns:
            Tuple of (documents list, total count)
        """
        conditions = [
            DMSDocument.organization_id == organization_id,
            DMSDocument.is_active == True,
        ]

        if folder_id:
            conditions.append(DMSDocument.folder_id == folder_id)
        if document_type:
            conditions.append(DMSDocument.document_type == document_type)
        if status:
            conditions.append(DMSDocument.status == status)
        if entity_type:
            conditions.append(DMSDocument.entity_type == entity_type)
        if entity_id:
            conditions.append(DMSDocument.entity_id == entity_id)
        if search:
            conditions.append(
                (DMSDocument.name.ilike(f"%{search}%"))
                | (DMSDocument.description.ilike(f"%{search}%"))
                | (DMSDocument.file_name.ilike(f"%{search}%"))
            )

        # Count query
        count_result = await self.db.execute(
            select(func.count()).select_from(DMSDocument).where(and_(*conditions))
        )
        total = count_result.scalar()

        # Data query
        result = await self.db.execute(
            select(DMSDocument)
            .where(and_(*conditions))
            .order_by(DMSDocument.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        documents = list(result.scalars().all())

        return documents, total

    async def update_document(
        self,
        document_id: UUID,
        name: str | None = None,
        description: str | None = None,
        folder_id: UUID | None = None,
        document_type: str | None = None,
        document_subtype: str | None = None,
        access_level: DocumentAccessLevel | None = None,
        keywords: list[str] | None = None,
        expiry_date: datetime | None = None,
        updated_by: UUID | None = None,
    ) -> DMSDocument | None:
        """Update document metadata."""
        document = await self.get_document(document_id)
        if not document:
            return None

        if name is not None:
            document.name = name
        if description is not None:
            document.description = description
        if folder_id is not None:
            document.folder_id = folder_id
        if document_type is not None:
            document.document_type = document_type
        if document_subtype is not None:
            document.document_subtype = document_subtype
        if access_level is not None:
            document.access_level = access_level
        if keywords is not None:
            document.keywords = keywords
        if expiry_date is not None:
            document.expiry_date = expiry_date

        document.updated_by = updated_by

        await self._log_history(document_id, "updated", updated_by)
        await self.db.flush()
        await self.db.refresh(document)

        return document

    async def upload_new_version(
        self,
        document_id: UUID,
        file: BinaryIO,
        file_name: str,
        file_size: int,
        mime_type: str,
        change_notes: str | None = None,
        uploaded_by: UUID | None = None,
    ) -> DMSDocumentVersion | None:
        """Upload a new version of a document."""
        document = await self.get_document(document_id)
        if not document:
            return None

        # Generate storage path for new version
        new_version_number = document.current_version + 1
        file_extension = os.path.splitext(file_name)[1].lower().lstrip(".")
        storage_path = self._generate_storage_path(
            document.organization_id,
            f"{document.code}_v{new_version_number}",
            file_extension,
        )

        # AV scan before persistence — see comment in upload_document.
        from app.core.av_scan import enforce_scan

        body = file.read()
        enforce_scan(body)
        from io import BytesIO

        file = BytesIO(body)

        # Save file
        checksum = await self._save_file(file, storage_path)

        # Mark old versions as not current
        await self.db.execute(
            select(DMSDocumentVersion).where(DMSDocumentVersion.document_id == document_id)
        )
        # Update is_current on existing versions
        from sqlalchemy import update

        await self.db.execute(
            update(DMSDocumentVersion)
            .where(DMSDocumentVersion.document_id == document_id)
            .values(is_current=False)
        )

        # Create new version record
        version = DMSDocumentVersion(
            document_id=document_id,
            version_number=new_version_number,
            change_notes=change_notes,
            file_name=file_name,
            file_size=file_size,
            mime_type=mime_type,
            storage_path=storage_path,
            checksum=checksum,
            is_current=True,
            created_by=uploaded_by,
        )
        self.db.add(version)

        # Update document
        document.current_version = new_version_number
        document.file_name = file_name
        document.file_size = file_size
        document.mime_type = mime_type
        document.storage_path = storage_path
        document.checksum = checksum
        document.updated_by = uploaded_by

        await self._log_history(
            document_id,
            "new_version",
            uploaded_by,
            {"version": new_version_number, "change_notes": change_notes},
        )

        await self.db.flush()
        await self.db.refresh(version)

        return version

    async def delete_document(
        self,
        document_id: UUID,
        deleted_by: UUID | None = None,
        hard_delete: bool = False,
    ) -> bool:
        """Delete a document (soft or hard delete)."""
        document = await self.get_document(document_id)
        if not document:
            return False

        if hard_delete:
            # Delete file from storage
            await self._delete_file(document.storage_path)
            # Delete all versions
            for version in await document.versions.all():
                await self._delete_file(version.storage_path)
            # Hard delete from database
            await self.db.delete(document)
        else:
            # Soft delete
            document.status = DocumentStatus.DELETED
            document.soft_delete(deleted_by)
            await self._log_history(document_id, "deleted", deleted_by)

        await self.db.flush()
        return True

    async def download_document(
        self,
        document_id: UUID,
        user_id: UUID | None = None,
        version: int | None = None,
    ) -> tuple[str, str, str] | None:
        """
        Get document file path for download.

        Returns:
            Tuple of (storage_path, file_name, mime_type) or None
        """
        document = await self.get_document(document_id)
        if not document:
            return None

        storage_path = document.storage_path
        file_name = document.file_name
        mime_type = document.mime_type

        # If specific version requested
        if version and version != document.current_version:
            result = await self.db.execute(
                select(DMSDocumentVersion).where(
                    DMSDocumentVersion.document_id == document_id,
                    DMSDocumentVersion.version_number == version,
                )
            )
            ver = result.scalar_one_or_none()
            if ver:
                storage_path = ver.storage_path
                file_name = ver.file_name
                mime_type = ver.mime_type

        # Update download count and log
        document.download_count += 1
        await self._log_history(document_id, "downloaded", user_id, {"version": version})
        await self.db.flush()

        return storage_path, file_name, mime_type

    async def add_tag(
        self,
        document_id: UUID,
        tag_id: UUID,
        created_by: UUID | None = None,
    ) -> bool:
        """Add a tag to a document."""
        # Check if tag already exists
        result = await self.db.execute(
            select(DMSDocumentTag).where(
                DMSDocumentTag.document_id == document_id,
                DMSDocumentTag.tag_id == tag_id,
            )
        )
        if result.scalar_one_or_none():
            return True  # Already tagged

        tag = DMSDocumentTag(
            document_id=document_id,
            tag_id=tag_id,
            created_by=created_by,
        )
        self.db.add(tag)
        await self.db.flush()
        return True

    async def remove_tag(
        self,
        document_id: UUID,
        tag_id: UUID,
    ) -> bool:
        """Remove a tag from a document."""
        result = await self.db.execute(
            select(DMSDocumentTag).where(
                DMSDocumentTag.document_id == document_id,
                DMSDocumentTag.tag_id == tag_id,
            )
        )
        tag = result.scalar_one_or_none()
        if tag:
            await self.db.delete(tag)
            await self.db.flush()
            return True
        return False

    async def _generate_code(self, organization_id: UUID) -> str:
        """Generate unique document code."""
        # Get count for today
        today = datetime.now(UTC).strftime("%Y%m%d")
        result = await self.db.execute(
            select(func.count())
            .select_from(DMSDocument)
            .where(
                DMSDocument.organization_id == organization_id,
                DMSDocument.code.like(f"DOC-{today}%"),
            )
        )
        count = result.scalar() or 0
        return f"DOC-{today}-{(count + 1):04d}"

    def _generate_storage_path(
        self,
        organization_id: UUID,
        code: str,
        extension: str,
    ) -> str:
        """Generate storage path for document."""
        date_path = datetime.now(UTC).strftime("%Y/%m/%d")
        return f"{str(organization_id)}/{date_path}/{code}.{extension}"

    async def _save_file(self, file: BinaryIO, storage_path: str) -> str:
        """Save file to storage and return checksum."""
        full_path = os.path.join(self.upload_path, storage_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        # Calculate checksum while writing
        hasher = hashlib.sha256()
        with open(full_path, "wb") as f:
            while chunk := file.read(8192):
                hasher.update(chunk)
                f.write(chunk)

        return hasher.hexdigest()

    async def _delete_file(self, storage_path: str) -> None:
        """Delete file from storage."""
        full_path = os.path.join(self.upload_path, storage_path)
        if os.path.exists(full_path):
            os.remove(full_path)

    async def _log_history(
        self,
        document_id: UUID,
        action: str,
        user_id: UUID | None = None,
        details: dict | None = None,
    ) -> None:
        """Log document action to history."""
        history = DMSDocumentHistory(
            document_id=document_id,
            action=action,
            action_details=details,
            performed_by=user_id,
        )
        self.db.add(history)

"""DMS schemas module."""

from app.schemas.dms.document import (
    DocumentCreate,
    DocumentUpdate,
    DocumentResponse,
    DocumentListResponse,
    DocumentVersionResponse,
    DocumentHistoryResponse,
    DocumentDownloadResponse,
    DocumentStatsResponse,
)
from app.schemas.dms.folder import (
    FolderCreate,
    FolderUpdate,
    FolderResponse,
    FolderTreeResponse,
    FolderAccessCreate,
    FolderAccessResponse,
)
from app.schemas.dms.tag import (
    TagCreate,
    TagUpdate,
    TagResponse,
    DocumentTagResponse,
)

__all__ = [
    # Document schemas
    "DocumentCreate",
    "DocumentUpdate",
    "DocumentResponse",
    "DocumentListResponse",
    "DocumentVersionResponse",
    "DocumentHistoryResponse",
    "DocumentDownloadResponse",
    "DocumentStatsResponse",
    # Folder schemas
    "FolderCreate",
    "FolderUpdate",
    "FolderResponse",
    "FolderTreeResponse",
    "FolderAccessCreate",
    "FolderAccessResponse",
    # Tag schemas
    "TagCreate",
    "TagUpdate",
    "TagResponse",
    "DocumentTagResponse",
]

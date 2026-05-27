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
from app.schemas.dms.filing import (
    EntityVaultResponse,
    FilingRuleCreate,
    FilingRuleResponse,
    ResolveFolderRequest,
    ResolveFolderResponse,
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
    "FilingRuleCreate",
    "FilingRuleResponse",
    "ResolveFolderRequest",
    "ResolveFolderResponse",
    "EntityVaultResponse",
    # Tag schemas
    "TagCreate",
    "TagUpdate",
    "TagResponse",
    "DocumentTagResponse",
]

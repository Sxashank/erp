"""Document Management System models."""

from app.models.dms.document import (
    DocumentStatus,
    DocumentAccessLevel,
    DMSDocument,
    DMSDocumentVersion,
    DMSDocumentAccess,
    DMSDocumentHistory,
)

from app.models.dms.folder import (
    DMSFolder,
    DMSFolderAccess,
)

from app.models.dms.filing import DocumentFilingRule

from app.models.dms.tag import (
    DMSTag,
    DMSDocumentTag,
)

__all__ = [
    # Enums
    "DocumentStatus",
    "DocumentAccessLevel",
    # Document Models
    "DMSDocument",
    "DMSDocumentVersion",
    "DMSDocumentAccess",
    "DMSDocumentHistory",
    # Folder Models
    "DMSFolder",
    "DMSFolderAccess",
    "DocumentFilingRule",
    # Tag Models
    "DMSTag",
    "DMSDocumentTag",
]

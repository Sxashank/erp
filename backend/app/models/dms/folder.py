"""DMS Folder models."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.dms.document import DocumentAccessLevel


class DMSFolder(BaseModel):
    """Folder in the DMS for organizing documents."""

    __tablename__ = "dms_folder"

    # Organization scope
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Parent folder (for nested structure)
    parent_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("dms_folder.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Folder identification
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Path for quick hierarchical queries
    path: Mapped[str] = mapped_column(
        String(2000),
        nullable=False,
        comment="Full path like /root/subfolder/folder",
    )
    level: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Depth level in hierarchy (0 = root)",
    )

    # Folder type
    folder_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="system, user, shared, entity",
    )

    # Entity reference (link folder to business entity)
    entity_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    entity_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)

    # Access control
    access_level: Mapped[DocumentAccessLevel] = mapped_column(
        String(50),
        default=DocumentAccessLevel.ORGANIZATION.value,
        nullable=False,
    )
    inherit_access: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Inherit access from parent folder",
    )

    # Display settings
    color: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, comment="Hex color code")
    icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, comment="Icon identifier")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Statistics
    document_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_size: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment="Total size in bytes")

    # Metadata
    folder_metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Relationships
    organization = relationship("Organization", lazy="selectin")
    parent = relationship("DMSFolder", remote_side="DMSFolder.id", lazy="selectin")
    children = relationship("DMSFolder", back_populates="parent", lazy="dynamic")
    documents = relationship("DMSDocument", back_populates="folder", lazy="dynamic")
    access_list = relationship("DMSFolderAccess", back_populates="folder", lazy="dynamic")


class DMSFolderAccess(BaseModel):
    """Folder access control list entry."""

    __tablename__ = "dms_folder_access"

    # Folder reference
    folder_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("dms_folder.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Access grantee (user or role)
    user_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="CASCADE"),
        nullable=True,
    )
    role_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_role.id", ondelete="CASCADE"),
        nullable=True,
    )
    department_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_department.id", ondelete="CASCADE"),
        nullable=True,
    )

    # Permissions
    can_view: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    can_upload: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    can_create_subfolder: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    can_edit: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    can_delete: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Access expiry
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    folder = relationship("DMSFolder", back_populates="access_list")
    user = relationship("User", foreign_keys=[user_id], lazy="selectin")
    role = relationship("Role", foreign_keys=[role_id], lazy="selectin")

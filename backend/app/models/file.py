"""Context file and file version models."""
from typing import Any

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.mixins import BaseMixin, WorkspaceMixin


class ContextFile(Base, BaseMixin, WorkspaceMixin):
    """Context file model."""

    __tablename__ = "context_files"

    workspace_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id"),
        nullable=False,
        index=True,
    )
    category = Column(
        String,
        nullable=False,
    )  # draft, reference, upload, memory, todo, system
    name = Column(String, nullable=False)
    path = Column(String, nullable=False)
    mime_type = Column(String, nullable=False)
    size = Column(Integer, nullable=False)
    checksum = Column(String, nullable=False)

    # References
    related_pages = Column(ARRAY(String), default=[], nullable=False)

    # Relationships
    workspace = relationship("Workspace", back_populates="context_files")
    versions = relationship(
        "FileVersion",
        back_populates="file",
        cascade="all, delete-orphan",
    )
    upload_asset = relationship(
        "UploadAsset",
        back_populates="context_file",
        uselist=False,
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<ContextFile {self.name}>"


class FileVersion(Base, BaseMixin):
    """File version model."""

    __tablename__ = "file_versions"

    file_id = Column(
        UUID(as_uuid=True),
        ForeignKey("context_files.id"),
        nullable=False,
        index=True,
    )
    snapshot_path = Column(String, nullable=False)
    created_by = Column(String, nullable=False)  # Agent ID or user ID
    diff_summary = Column(Text, nullable=True)

    # Relationships
    file = relationship("ContextFile", back_populates="versions")

    def __repr__(self) -> str:
        """String representation."""
        return f"<FileVersion {self.id} of {self.file_id}>"

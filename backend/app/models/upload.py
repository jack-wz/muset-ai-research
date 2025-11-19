"""Upload asset model for file processing."""
from sqlalchemy import Column, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.mixins import BaseMixin


class UploadAsset(Base, BaseMixin):
    """Upload asset model for tracking file uploads and processing."""

    __tablename__ = "upload_assets"

    # Workspace relationship
    workspace_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Workspace ID",
    )

    # Uploader relationship
    uploader_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="User who uploaded the file",
    )

    # File reference (ContextFile ID)
    file_id = Column(
        UUID(as_uuid=True),
        ForeignKey("context_files.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to ContextFile",
    )

    # Original file information
    original_name = Column(
        String,
        nullable=False,
        comment="Original filename",
    )

    # File type
    file_type = Column(
        String,
        nullable=False,
        index=True,
        comment="File type: document, image, audio, video, spreadsheet, presentation",
    )

    # Processing status
    status = Column(
        String,
        default="processing",
        nullable=False,
        index=True,
        comment="Processing status: processing, ready, failed",
    )

    # Processing metadata
    processing_metadata = Column(
        JSONB,
        nullable=True,
        default={},
        comment="Processing metadata including extracted text, thumbnails, OCR status",
    )

    # Error information (if failed)
    error_message = Column(
        Text,
        nullable=True,
        comment="Error message if processing failed",
    )

    # Processing details
    mime_type = Column(
        String,
        nullable=True,
        comment="MIME type of the file",
    )

    # File size in bytes
    file_size = Column(
        String,
        nullable=True,
        comment="File size in bytes",
    )

    # Relationships
    workspace = relationship("Workspace", back_populates="upload_assets")
    uploader = relationship("User", back_populates="uploads")
    context_file = relationship("ContextFile", back_populates="upload_asset")

    def __repr__(self) -> str:
        """String representation."""
        return f"<UploadAsset {self.original_name} ({self.status})>"

    def is_processing(self) -> bool:
        """Check if asset is currently being processed."""
        return self.status == "processing"

    def is_ready(self) -> bool:
        """Check if asset is ready for use."""
        return self.status == "ready"

    def is_failed(self) -> bool:
        """Check if asset processing failed."""
        return self.status == "failed"

    def get_extracted_text_file_id(self) -> str | None:
        """Get extracted text file ID from processing metadata."""
        if self.processing_metadata:
            return self.processing_metadata.get("extractedTextFileId")
        return None

    def get_thumbnail_file_id(self) -> str | None:
        """Get thumbnail file ID from processing metadata."""
        if self.processing_metadata:
            return self.processing_metadata.get("thumbnailFileId")
        return None

    def get_ocr_status(self) -> str | None:
        """Get OCR status from processing metadata."""
        if self.processing_metadata:
            return self.processing_metadata.get("ocrStatus")
        return None

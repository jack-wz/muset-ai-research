"""File system manager for DeepAgent."""
import asyncio
import hashlib
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiofiles
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import FileNotFoundError, PermissionDeniedError
from app.models.file import ContextFile, FileVersion


@dataclass
class Edit:
    """Represents a single edit operation on a file."""

    start_line: int  # 1-based line number
    end_line: int  # 1-based line number (inclusive)
    new_content: str  # New content to replace the lines


class FileSystemManager:
    """Manages file operations for DeepAgent with version control."""

    # Context size threshold in characters (e.g., 10KB)
    CONTEXT_THRESHOLD = 10000

    def __init__(
        self,
        workspace_id: str,
        base_path: str,
        session: AsyncSession,
    ):
        """
        Initialize file system manager.

        Args:
            workspace_id: Workspace identifier
            base_path: Base directory for file storage
            session: Database session
        """
        self.workspace_id = workspace_id
        self.base_path = Path(base_path)
        self.session = session

        # Create workspace directory
        self.workspace_dir = self.base_path / workspace_id
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

    async def write_file(
        self,
        path: str,
        content: str,
        category: str = "draft",
        agent_id: Optional[str] = None,
    ) -> ContextFile:
        """
        Write content to a file and create version.

        Args:
            path: Relative path to the file
            content: File content
            category: File category (draft, reference, upload, memory, todo, system)
            agent_id: ID of the agent creating the file

        Returns:
            ContextFile instance

        Raises:
            PermissionDeniedError: If path is invalid or access denied
        """
        # Validate path
        if not self._is_valid_path(path):
            raise PermissionDeniedError(f"Invalid path: {path}")

        # Create full path
        full_path = self.workspace_dir / path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # Write content
        async with aiofiles.open(full_path, "w", encoding="utf-8") as f:
            await f.write(content)

        # Calculate checksum
        checksum = self._calculate_checksum(content)

        # Get file info
        file_stat = full_path.stat()

        # Check if file exists in database
        existing_file = await self._get_file_by_path(path)

        if existing_file:
            # Update existing file
            existing_file.checksum = checksum
            existing_file.size = file_stat.st_size
            existing_file.updated_at = datetime.utcnow()

            # Create new version
            await self._create_version(
                file_id=str(existing_file.id),
                content=content,
                agent_id=agent_id or "system",
            )

            await self.session.commit()
            await self.session.refresh(existing_file)
            return existing_file
        else:
            # Create new file record
            file_record = ContextFile(
                workspace_id=self.workspace_id,
                category=category,
                name=Path(path).name,
                path=path,
                mime_type=self._get_mime_type(path),
                size=file_stat.st_size,
                checksum=checksum,
                related_pages=[],
            )

            self.session.add(file_record)
            await self.session.flush()

            # Create initial version
            await self._create_version(
                file_id=str(file_record.id),
                content=content,
                agent_id=agent_id or "system",
            )

            await self.session.commit()
            await self.session.refresh(file_record)
            return file_record

    async def read_file(self, path: str) -> str:
        """
        Read content from a file.

        Args:
            path: Relative path to the file

        Returns:
            File content

        Raises:
            FileNotFoundError: If file doesn't exist
            PermissionDeniedError: If access denied
        """
        # Validate path
        if not self._is_valid_path(path):
            raise PermissionDeniedError(f"Invalid path: {path}")

        # Create full path
        full_path = self.workspace_dir / path

        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        # Read content
        async with aiofiles.open(full_path, "r", encoding="utf-8") as f:
            content = await f.read()

        return content

    async def edit_file(
        self,
        path: str,
        old_content: str,
        new_content: str,
        agent_id: Optional[str] = None,
    ) -> ContextFile:
        """
        Edit a file by replacing old content with new content.

        Args:
            path: Relative path to the file
            old_content: Content to be replaced
            new_content: New content
            agent_id: ID of the agent making the edit

        Returns:
            Updated ContextFile instance

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If old_content not found in file
        """
        # Read current content
        current_content = await self.read_file(path)

        # Replace content
        if old_content not in current_content:
            raise ValueError(f"Content to replace not found in file: {path}")

        updated_content = current_content.replace(old_content, new_content, 1)

        # Write updated content
        return await self.write_file(path, updated_content, agent_id=agent_id)

    async def edit_file_lines(
        self,
        path: str,
        edits: List[Edit],
        agent_id: Optional[str] = None,
    ) -> ContextFile:
        """
        Edit a file by applying multiple line-based edits.

        Args:
            path: Relative path to the file
            edits: List of Edit objects specifying line ranges and new content
            agent_id: ID of the agent making the edit

        Returns:
            Updated ContextFile instance

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If edit ranges are invalid or overlapping

        Example:
            >>> edits = [
            ...     Edit(start_line=5, end_line=7, new_content="New lines 5-7"),
            ...     Edit(start_line=10, end_line=10, new_content="Replace line 10"),
            ... ]
            >>> await manager.edit_file_lines("test.txt", edits)
        """
        # Read current content
        current_content = await self.read_file(path)
        lines = current_content.split("\n")

        # Validate and sort edits by line number (descending) to apply from bottom to top
        sorted_edits = sorted(edits, key=lambda e: e.start_line, reverse=True)

        # Validate edits
        for i, edit in enumerate(sorted_edits):
            if edit.start_line < 1 or edit.end_line < edit.start_line:
                raise ValueError(
                    f"Invalid edit range: lines {edit.start_line}-{edit.end_line}"
                )

            if edit.end_line > len(lines):
                raise ValueError(
                    f"Edit range {edit.start_line}-{edit.end_line} exceeds file length {len(lines)}"
                )

            # Check for overlapping edits
            if i > 0:
                prev_edit = sorted_edits[i - 1]
                if edit.end_line >= prev_edit.start_line:
                    raise ValueError(
                        f"Overlapping edits: {edit.start_line}-{edit.end_line} and "
                        f"{prev_edit.start_line}-{prev_edit.end_line}"
                    )

        # Apply edits from bottom to top to maintain line numbers
        for edit in sorted_edits:
            # Convert to 0-based indexing
            start_idx = edit.start_line - 1
            end_idx = edit.end_line  # end_line is inclusive, so we don't subtract 1

            # Split new content into lines
            new_lines = edit.new_content.split("\n") if edit.new_content else []

            # Replace the range
            lines[start_idx:end_idx] = new_lines

        # Join lines back together
        updated_content = "\n".join(lines)

        # Write updated content
        return await self.write_file(path, updated_content, agent_id=agent_id)

    async def ls(self, directory: str = "", pattern: Optional[str] = None) -> List[str]:
        """
        List files in a directory.

        Args:
            directory: Directory path relative to workspace
            pattern: Optional glob pattern

        Returns:
            List of file paths

        Raises:
            PermissionDeniedError: If access denied
        """
        # Validate path
        if directory and not self._is_valid_path(directory):
            raise PermissionDeniedError(f"Invalid path: {directory}")

        target_dir = self.workspace_dir / directory

        if not target_dir.exists():
            return []

        files = []
        if pattern:
            files = [str(p.relative_to(self.workspace_dir)) for p in target_dir.glob(pattern)]
        else:
            files = [
                str(p.relative_to(self.workspace_dir))
                for p in target_dir.rglob("*")
                if p.is_file()
            ]

        return sorted(files)

    async def grep(self, pattern: str, directory: str = "") -> List[Dict[str, Any]]:
        """
        Search for pattern in files.

        Args:
            pattern: Search pattern
            directory: Directory to search in

        Returns:
            List of matches with file path, line number, and content

        Raises:
            PermissionDeniedError: If access denied
        """
        # Validate path
        if directory and not self._is_valid_path(directory):
            raise PermissionDeniedError(f"Invalid path: {directory}")

        target_dir = self.workspace_dir / directory

        if not target_dir.exists():
            return []

        matches = []
        for file_path in target_dir.rglob("*"):
            if file_path.is_file():
                try:
                    async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                        content = await f.read()
                        lines = content.split("\n")
                        for i, line in enumerate(lines, 1):
                            if pattern.lower() in line.lower():
                                matches.append(
                                    {
                                        "file": str(file_path.relative_to(self.workspace_dir)),
                                        "line": i,
                                        "content": line.strip(),
                                    }
                                )
                except Exception:
                    # Skip files that can't be read
                    continue

        return matches

    async def get_file_versions(self, path: str) -> List[FileVersion]:
        """
        Get all versions of a file.

        Args:
            path: Relative path to the file

        Returns:
            List of FileVersion instances
        """
        file_record = await self._get_file_by_path(path)
        if not file_record:
            raise FileNotFoundError(f"File not found: {path}")

        return file_record.versions

    async def should_externalize_content(self, content: str) -> bool:
        """
        Check if content should be externalized to a file.

        Args:
            content: Content to check

        Returns:
            True if content exceeds threshold, False otherwise
        """
        return len(content) > self.CONTEXT_THRESHOLD

    async def _get_file_by_path(self, path: str) -> Optional[ContextFile]:
        """Get file record by path."""
        from sqlalchemy import select

        result = await self.session.execute(
            select(ContextFile).where(
                ContextFile.workspace_id == self.workspace_id, ContextFile.path == path
            )
        )
        return result.scalar_one_or_none()

    async def _create_version(self, file_id: str, content: str, agent_id: str) -> FileVersion:
        """Create a new file version."""
        # Create snapshot file
        snapshot_path = self.workspace_dir / ".versions" / f"{file_id}_{datetime.utcnow().timestamp()}.txt"
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(snapshot_path, "w", encoding="utf-8") as f:
            await f.write(content)

        # Create version record
        version = FileVersion(
            file_id=file_id,
            snapshot_path=str(snapshot_path.relative_to(self.base_path)),
            created_by=agent_id,
        )

        self.session.add(version)
        return version

    def _is_valid_path(self, path: str) -> bool:
        """Check if path is valid and safe."""
        # Prevent directory traversal attacks
        try:
            resolved = (self.workspace_dir / path).resolve()
            return resolved.is_relative_to(self.workspace_dir)
        except (ValueError, OSError):
            return False

    def _calculate_checksum(self, content: str) -> str:
        """Calculate SHA-256 checksum of content."""
        return hashlib.sha256(content.encode()).hexdigest()

    def _get_mime_type(self, path: str) -> str:
        """Get MIME type from file extension."""
        extension = Path(path).suffix.lower()
        mime_types = {
            ".txt": "text/plain",
            ".md": "text/markdown",
            ".py": "text/x-python",
            ".json": "application/json",
            ".yaml": "application/x-yaml",
            ".yml": "application/x-yaml",
        }
        return mime_types.get(extension, "application/octet-stream")

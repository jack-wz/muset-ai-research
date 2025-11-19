"""Search service for global full-text search using PostgreSQL FTS."""
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import ChatMessage, ChatSession
from app.models.file import ContextFile
from app.models.page import Page
from app.models.search import SearchHistory, SearchIndex


class SearchService:
    """
    Service for managing global search functionality.

    Provides full-text search across pages, chat messages, and files
    using PostgreSQL's built-in FTS capabilities.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize search service.

        Args:
            session: Database session
        """
        self.session = session

    async def index_page(self, page: Page) -> SearchIndex:
        """
        Index a page for searching.

        Args:
            page: Page to index

        Returns:
            Created or updated SearchIndex instance
        """
        # Extract searchable content from TipTap JSON
        content_text = self._extract_tiptap_text(page.tiptap_content)

        # Create or update search index
        existing = await self._get_existing_index("page", page.id)

        if existing:
            # Update existing index
            existing.title = page.title
            existing.description = page.summary
            existing.content = content_text
            existing.search_metadata = {
                "tags": page.tags,
                "status": page.status,
                "word_count": page.word_count,
            }
            existing.url = f"/pages/{page.id}"
            # Update search vector
            existing.search_vector = await self._generate_search_vector(
                page.title, content_text
            )
            return existing
        else:
            # Create new index
            search_index = SearchIndex(
                workspace_id=page.workspace_id,
                content_type="page",
                content_id=page.id,
                title=page.title,
                description=page.summary,
                content=content_text,
                search_metadata={
                    "tags": page.tags,
                    "status": page.status,
                    "word_count": page.word_count,
                },
                url=f"/pages/{page.id}",
                search_vector=await self._generate_search_vector(
                    page.title, content_text
                ),
            )
            self.session.add(search_index)
            return search_index

    async def index_chat_message(
        self, message: ChatMessage, session: ChatSession
    ) -> SearchIndex:
        """
        Index a chat message for searching.

        Args:
            message: ChatMessage to index
            session: ChatSession the message belongs to

        Returns:
            Created or updated SearchIndex instance
        """
        # Create title from session and message role
        title = f"{session.title} - {message.role}"

        # Create or update search index
        existing = await self._get_existing_index("chat_message", message.id)

        if existing:
            # Update existing index
            existing.title = title
            existing.content = message.content
            existing.search_metadata = {
                "session_id": str(session.id),
                "session_title": session.title,
                "role": message.role,
                "mode": session.mode,
            }
            existing.url = f"/chat/{session.id}?message={message.id}"
            # Update search vector
            existing.search_vector = await self._generate_search_vector(
                title, message.content
            )
            return existing
        else:
            # Create new index
            search_index = SearchIndex(
                workspace_id=session.workspace_id,
                content_type="chat_message",
                content_id=message.id,
                title=title,
                description=f"Message in {session.title}",
                content=message.content,
                search_metadata={
                    "session_id": str(session.id),
                    "session_title": session.title,
                    "role": message.role,
                    "mode": session.mode,
                },
                url=f"/chat/{session.id}?message={message.id}",
                search_vector=await self._generate_search_vector(
                    title, message.content
                ),
            )
            self.session.add(search_index)
            return search_index

    async def index_file(self, file: ContextFile) -> SearchIndex:
        """
        Index a file for searching.

        Args:
            file: ContextFile to index

        Returns:
            Created or updated SearchIndex instance
        """
        # Create or update search index
        existing = await self._get_existing_index("file", file.id)

        if existing:
            # Update existing index
            existing.title = file.name
            existing.content = file.path  # Store file path as content
            existing.search_metadata = {
                "category": file.category,
                "mime_type": file.mime_type,
                "size": file.size,
            }
            existing.url = f"/files/{file.id}"
            # Update search vector
            existing.search_vector = await self._generate_search_vector(
                file.name, file.path
            )
            return existing
        else:
            # Create new index
            search_index = SearchIndex(
                workspace_id=file.workspace_id,
                content_type="file",
                content_id=file.id,
                title=file.name,
                description=f"{file.category} file",
                content=file.path,
                search_metadata={
                    "category": file.category,
                    "mime_type": file.mime_type,
                    "size": file.size,
                },
                url=f"/files/{file.id}",
                search_vector=await self._generate_search_vector(
                    file.name, file.path
                ),
            )
            self.session.add(search_index)
            return search_index

    async def search(
        self,
        workspace_id: UUID,
        query: str,
        content_types: Optional[List[str]] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Perform full-text search.

        Args:
            workspace_id: Workspace to search in
            query: Search query string
            content_types: Optional filter by content types
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            Dictionary with search results and metadata
        """
        # Build base query
        stmt = select(SearchIndex).where(SearchIndex.workspace_id == workspace_id)

        # Filter by content types if specified
        if content_types:
            stmt = stmt.where(SearchIndex.content_type.in_(content_types))

        # Generate search query
        search_query = self._generate_tsquery(query)

        # Apply full-text search filter
        stmt = stmt.where(
            SearchIndex.search_vector.op("@@")(func.to_tsquery("english", search_query))
        )

        # Order by relevance (ts_rank)
        stmt = stmt.order_by(
            func.ts_rank(
                SearchIndex.search_vector, func.to_tsquery("english", search_query)
            ).desc()
        )

        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_count = await self.session.scalar(count_stmt)

        # Apply pagination
        stmt = stmt.limit(limit).offset(offset)

        # Execute query
        result = await self.session.execute(stmt)
        results = result.scalars().all()

        return {
            "results": [self._format_result(r) for r in results],
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "query": query,
        }

    async def save_search_history(
        self,
        user_id: UUID,
        workspace_id: UUID,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        results_count: int = 0,
        clicked_result_id: Optional[UUID] = None,
    ) -> SearchHistory:
        """
        Save user search history.

        Args:
            user_id: User ID
            workspace_id: Workspace ID
            query: Search query
            filters: Search filters applied
            results_count: Number of results returned
            clicked_result_id: ID of result clicked (if any)

        Returns:
            Created SearchHistory instance
        """
        history = SearchHistory(
            user_id=user_id,
            workspace_id=workspace_id,
            query=query,
            filters=filters or {},
            results_count={"total": results_count},
            clicked_result_id=clicked_result_id,
        )
        self.session.add(history)
        return history

    async def get_search_history(
        self, user_id: UUID, workspace_id: UUID, limit: int = 10
    ) -> List[SearchHistory]:
        """
        Get user search history.

        Args:
            user_id: User ID
            workspace_id: Workspace ID
            limit: Maximum number of history entries

        Returns:
            List of SearchHistory instances
        """
        stmt = (
            select(SearchHistory)
            .where(
                and_(
                    SearchHistory.user_id == user_id,
                    SearchHistory.workspace_id == workspace_id,
                )
            )
            .order_by(SearchHistory.created_at.desc())
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete_index(self, content_type: str, content_id: UUID) -> bool:
        """
        Delete a search index entry.

        Args:
            content_type: Type of content
            content_id: ID of content

        Returns:
            True if deleted, False if not found
        """
        existing = await self._get_existing_index(content_type, content_id)
        if existing:
            await self.session.delete(existing)
            return True
        return False

    # Private helper methods

    async def _get_existing_index(
        self, content_type: str, content_id: UUID
    ) -> Optional[SearchIndex]:
        """Get existing search index for content."""
        stmt = select(SearchIndex).where(
            and_(
                SearchIndex.content_type == content_type,
                SearchIndex.content_id == content_id,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def _generate_search_vector(self, title: str, content: str) -> Any:
        """
        Generate PostgreSQL TSVector for search.

        Args:
            title: Title text (weighted higher)
            content: Content text

        Returns:
            TSVector expression
        """
        # Use text() to create raw SQL expression for TSVector
        # Weight 'A' for title (highest), 'B' for content
        return func.to_tsvector(
            "english",
            func.concat(
                func.coalesce(title, ""),
                " ",
                func.coalesce(content, ""),
            ),
        )

    def _generate_tsquery(self, query: str) -> str:
        """
        Generate PostgreSQL TSQuery from user query.

        Args:
            query: User search query

        Returns:
            TSQuery string
        """
        # Split query into words and join with '&' (AND operator)
        # This creates a more flexible search
        words = query.strip().split()
        if not words:
            return ""

        # Join words with OR operator for more flexible matching
        # Use :* suffix for prefix matching
        return " | ".join([f"{word}:*" for word in words])

    def _extract_tiptap_text(self, tiptap_content: Dict[str, Any]) -> str:
        """
        Extract plain text from TipTap JSON content.

        Args:
            tiptap_content: TipTap JSON document

        Returns:
            Plain text content
        """
        if not tiptap_content:
            return ""

        text_parts = []

        def extract_text(node: Dict[str, Any]) -> None:
            """Recursively extract text from TipTap nodes."""
            if node.get("type") == "text":
                text_parts.append(node.get("text", ""))
            elif "content" in node:
                for child in node["content"]:
                    extract_text(child)

        extract_text(tiptap_content)
        return " ".join(text_parts)

    def _format_result(self, index: SearchIndex) -> Dict[str, Any]:
        """Format search result for API response."""
        return {
            "id": str(index.id),
            "content_type": index.content_type,
            "content_id": str(index.content_id),
            "title": index.title,
            "description": index.description,
            "metadata": index.search_metadata,
            "url": index.url,
            "created_at": index.created_at.isoformat(),
            "updated_at": index.updated_at.isoformat(),
        }

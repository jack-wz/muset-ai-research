"""Memory manager for DeepAgent."""
from typing import Any, Dict, List, Optional

from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pinecone import Pinecone, ServerlessSpec
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.memory import Memory


class MemoryManager:
    """Manages long-term memory for DeepAgent with vector search."""

    def __init__(
        self,
        session: AsyncSession,
        llm: BaseChatModel,
        embeddings: Embeddings,
        pinecone_api_key: Optional[str] = None,
        pinecone_index: Optional[str] = None,
    ):
        """
        Initialize memory manager.

        Args:
            session: Database session
            llm: Language model for analysis
            embeddings: Embedding model
            pinecone_api_key: Optional Pinecone API key
            pinecone_index: Optional Pinecone index name
        """
        self.session = session
        self.llm = llm
        self.embeddings = embeddings
        self.pinecone_api_key = pinecone_api_key
        self.pinecone_index = pinecone_index

        # Initialize Pinecone if credentials provided
        self.pc = None
        self.index = None
        if pinecone_api_key and pinecone_index:
            self.pc = Pinecone(api_key=pinecone_api_key)
            # Check if index exists
            if pinecone_index not in self.pc.list_indexes().names():
                # Create index
                self.pc.create_index(
                    name=pinecone_index,
                    dimension=1536,  # OpenAI embedding dimension
                    metric="cosine",
                    spec=ServerlessSpec(cloud="aws", region="us-east-1"),
                )
            self.index = self.pc.Index(pinecone_index)

    async def store_style_profile(
        self,
        workspace_id: str,
        samples: List[str],
        title: str = "Writing Style Profile",
        tags: Optional[List[str]] = None,
    ) -> Memory:
        """
        Analyze writing samples and store style profile.

        Args:
            workspace_id: Workspace ID
            samples: List of writing samples
            title: Profile title
            tags: Optional tags

        Returns:
            Created Memory instance
        """
        # Analyze style with LLM
        system_prompt = """Analyze the provided writing samples and extract the writing style profile.

Identify:
1. Tone descriptors (e.g., formal, casual, technical, friendly)
2. Pacing (fast, moderate, slow)
3. Average sentence length and complexity
4. Dos and Don'ts based on the samples

Return a JSON object with:
{
  "toneDescriptors": ["descriptor1", "descriptor2"],
  "pacing": "moderate",
  "sentenceLength": "medium",
  "complexity": "moderate",
  "dos": ["Do this", "Do that"],
  "donts": ["Don't do this", "Don't do that"]
}"""

        user_prompt = "Writing samples:\n\n" + "\n\n---\n\n".join(samples)

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        response = await self.llm.ainvoke(messages)

        # Parse response
        import json

        try:
            style_data = json.loads(response.content)
        except json.JSONDecodeError:
            style_data = {"error": "Could not parse style analysis"}

        # Add samples to payload
        payload = {
            "samples": samples,
            **style_data,
        }

        # Create memory
        memory = Memory(
            workspace_id=workspace_id,
            type="style",
            title=title,
            payload=payload,
            tags=tags or [],
            importance_score=0.8,
        )

        self.session.add(memory)
        await self.session.flush()

        # Store embedding
        if self.index:
            combined_text = f"{title} " + " ".join(samples)
            embedding = await self.embeddings.aembed_query(combined_text)
            memory.embedding_id = str(memory.id)
            self.index.upsert(
                vectors=[
                    {
                        "id": str(memory.id),
                        "values": embedding,
                        "metadata": {
                            "workspace_id": workspace_id,
                            "type": "style",
                            "title": title,
                        },
                    }
                ]
            )

        await self.session.commit()
        await self.session.refresh(memory)

        return memory

    async def store_glossary_term(
        self,
        workspace_id: str,
        term: str,
        definition: str,
        usage_examples: Optional[List[str]] = None,
        locale: str = "en",
        tags: Optional[List[str]] = None,
    ) -> Memory:
        """
        Store a glossary term.

        Args:
            workspace_id: Workspace ID
            term: Term to define
            definition: Term definition
            usage_examples: Optional usage examples
            locale: Language locale
            tags: Optional tags

        Returns:
            Created Memory instance
        """
        payload = {
            "term": term,
            "definition": definition,
            "usageExamples": usage_examples or [],
            "locale": locale,
        }

        memory = Memory(
            workspace_id=workspace_id,
            type="glossary",
            title=term,
            payload=payload,
            tags=tags or [],
            importance_score=0.7,
        )

        self.session.add(memory)
        await self.session.flush()

        # Store embedding
        if self.index:
            combined_text = f"{term} {definition}"
            embedding = await self.embeddings.aembed_query(combined_text)
            memory.embedding_id = str(memory.id)
            self.index.upsert(
                vectors=[
                    {
                        "id": str(memory.id),
                        "values": embedding,
                        "metadata": {
                            "workspace_id": workspace_id,
                            "type": "glossary",
                            "term": term,
                        },
                    }
                ]
            )

        await self.session.commit()
        await self.session.refresh(memory)

        return memory

    async def load_memories(
        self,
        workspace_id: str,
        query: str,
        memory_type: Optional[str] = None,
        top_k: int = 5,
    ) -> List[Memory]:
        """
        Load relevant memories using semantic search.

        Args:
            workspace_id: Workspace ID
            query: Search query
            memory_type: Optional memory type filter
            top_k: Number of results to return

        Returns:
            List of Memory instances
        """
        # If Pinecone is available, use vector search
        if self.index:
            query_embedding = await self.embeddings.aembed_query(query)

            # Build filter
            filter_dict = {"workspace_id": workspace_id}
            if memory_type:
                filter_dict["type"] = memory_type

            # Search
            results = self.index.query(
                vector=query_embedding,
                filter=filter_dict,
                top_k=top_k,
                include_metadata=True,
            )

            # Load memories from database
            memory_ids = [match.id for match in results.matches]
            db_result = await self.session.execute(
                select(Memory).where(Memory.embedding_id.in_(memory_ids))
            )
            memories = list(db_result.scalars().all())

            # Sort by score
            memory_map = {str(m.id): m for m in memories}
            sorted_memories = [
                memory_map[match.id] for match in results.matches if match.id in memory_map
            ]

            return sorted_memories
        else:
            # Fallback to database query
            query_stmt = select(Memory).where(Memory.workspace_id == workspace_id)

            if memory_type:
                query_stmt = query_stmt.where(Memory.type == memory_type)

            query_stmt = query_stmt.order_by(Memory.importance_score.desc()).limit(top_k)

            result = await self.session.execute(query_stmt)
            return list(result.scalars().all())

    async def store_knowledge(
        self,
        workspace_id: str,
        topic: str,
        summary: str,
        citations: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
    ) -> Memory:
        """
        Store knowledge/research.

        Args:
            workspace_id: Workspace ID
            topic: Topic title
            summary: Summary of knowledge
            citations: Optional citations
            tags: Optional tags

        Returns:
            Created Memory instance
        """
        payload = {
            "topic": topic,
            "summary": summary,
            "citations": citations or [],
        }

        memory = Memory(
            workspace_id=workspace_id,
            type="knowledge",
            title=topic,
            payload=payload,
            tags=tags or [],
            importance_score=0.6,
        )

        self.session.add(memory)
        await self.session.flush()

        # Store embedding
        if self.index:
            combined_text = f"{topic} {summary}"
            embedding = await self.embeddings.aembed_query(combined_text)
            memory.embedding_id = str(memory.id)
            self.index.upsert(
                vectors=[
                    {
                        "id": str(memory.id),
                        "values": embedding,
                        "metadata": {
                            "workspace_id": workspace_id,
                            "type": "knowledge",
                            "topic": topic,
                        },
                    }
                ]
            )

        await self.session.commit()
        await self.session.refresh(memory)

        return memory

    async def store_preference(
        self,
        workspace_id: str,
        key: str,
        value: Any,
        context: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Memory:
        """
        Store a user preference.

        Args:
            workspace_id: Workspace ID
            key: Preference key
            value: Preference value
            context: Optional context
            tags: Optional tags

        Returns:
            Created Memory instance
        """
        payload = {
            "key": key,
            "value": value,
            "context": context,
        }

        memory = Memory(
            workspace_id=workspace_id,
            type="preference",
            title=key,
            payload=payload,
            tags=tags or [],
            importance_score=0.5,
        )

        self.session.add(memory)
        await self.session.commit()
        await self.session.refresh(memory)

        return memory

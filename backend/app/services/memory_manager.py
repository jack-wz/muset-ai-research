"""Memory manager for DeepAgent."""
from typing import Any, Dict, List, Optional
import os
import logging
import json
import uuid

from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pinecone import Pinecone, ServerlessSpec
import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.config import Configure, Property, DataType
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.memory import Memory

logger = logging.getLogger(__name__)

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
        
        # Vector DB configuration
        self.vector_db_type = os.getenv("VECTOR_DB_TYPE", "weaviate")
        self.weaviate_url = os.getenv("WEAVIATE_URL", "http://weaviate:8080")
        self.collection_name = "MusetMemory"

        # Initialize Vector DB
        self.pc = None
        self.index = None
        self.weaviate_client = None
        
        self._init_vector_db()

    def _init_vector_db(self):
        """Initialize the configured vector database."""
        try:
            if self.vector_db_type == "pinecone" and self.pinecone_api_key and self.pinecone_index:
                logger.info("Initializing Pinecone vector database...")
                self.pc = Pinecone(api_key=self.pinecone_api_key)
                # Check if index exists
                if self.pinecone_index not in self.pc.list_indexes().names():
                    # Create index
                    self.pc.create_index(
                        name=self.pinecone_index,
                        dimension=1536,  # OpenAI embedding dimension
                        metric="cosine",
                        spec=ServerlessSpec(cloud="aws", region="us-east-1"),
                    )
                self.index = self.pc.Index(self.pinecone_index)
                logger.info("Pinecone initialized successfully.")
                
            elif self.vector_db_type == "weaviate":
                logger.info(f"Initializing Weaviate at {self.weaviate_url}...")
                
                # Parse URL
                url_parts = self.weaviate_url.split("://")
                scheme = url_parts[0]
                host_port = url_parts[1]
                
                # Connect to Weaviate
                self.weaviate_client = weaviate.connect_to_custom(
                    http_host=host_port.split(":")[0],
                    http_port=int(host_port.split(":")[1]) if ":" in host_port else 8080,
                    http_secure=scheme == "https",
                    grpc_host=host_port.split(":")[0],
                    grpc_port=50051,
                    grpc_secure=False,
                )
                
                # Check if collection exists, if not create it
                if not self.weaviate_client.collections.exists(self.collection_name):
                    self.weaviate_client.collections.create(
                        name=self.collection_name,
                        vectorizer_config=Configure.Vectorizer.none(), # We provide embeddings manually
                        properties=[
                            Property(name="memory_id", data_type=DataType.TEXT),
                            Property(name="text", data_type=DataType.TEXT),
                            Property(name="workspace_id", data_type=DataType.TEXT),
                            Property(name="type", data_type=DataType.TEXT),
                            Property(name="title", data_type=DataType.TEXT),
                            Property(name="metadata_json", data_type=DataType.TEXT),
                        ]
                    )
                    
                logger.info("Weaviate initialized successfully.")
                
        except Exception as e:
            logger.error(f"Failed to initialize vector database: {str(e)}")
            # Fallback to no vector DB (will use SQL only)

    async def _upsert_vector(self, id: str, text: str, metadata: Dict[str, Any]):
        """Upsert vector to the active vector database."""
        try:
            embedding = await self.embeddings.aembed_query(text)
            
            if self.index:  # Pinecone
                self.index.upsert(
                    vectors=[
                        {
                            "id": id,
                            "values": embedding,
                            "metadata": metadata,
                        }
                    ]
                )
            elif self.weaviate_client:  # Weaviate
                collection = self.weaviate_client.collections.get(self.collection_name)
                
                # Prepare properties
                properties = {
                    "memory_id": id,
                    "text": text,
                    "workspace_id": metadata.get("workspace_id", ""),
                    "type": metadata.get("type", ""),
                    "title": metadata.get("title", ""),
                    "metadata_json": json.dumps(metadata),
                }
                
                # Weaviate uses UUIDs for object IDs
                # We can generate a deterministic UUID from our ID if needed, 
                # or let Weaviate generate one and store our ID as a property.
                # Here we use a deterministic UUID based on our ID to allow updates.
                obj_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, id)
                
                # Upsert (Weaviate doesn't have a direct upsert, but insert with same UUID overwrites)
                collection.data.insert(
                    properties=properties,
                    vector=embedding,
                    uuid=obj_uuid
                )
                
        except Exception as e:
            logger.error(f"Failed to upsert vector: {str(e)}")

    async def _query_vectors(self, query: str, filter: Dict[str, Any], top_k: int) -> List[str]:
        """Query vectors and return list of IDs."""
        ids = []
        try:
            query_embedding = await self.embeddings.aembed_query(query)
            
            if self.index:  # Pinecone
                results = self.index.query(
                    vector=query_embedding,
                    filter=filter,
                    top_k=top_k,
                    include_metadata=True,
                )
                ids = [match.id for match in results.matches]
                
            elif self.weaviate_client:  # Weaviate
                collection = self.weaviate_client.collections.get(self.collection_name)
                
                # Build filter
                from weaviate.classes.query import Filter
                
                w_filter = None
                if "workspace_id" in filter:
                    w_filter = Filter.by_property("workspace_id").equal(filter["workspace_id"])
                    
                if "type" in filter:
                    type_filter = Filter.by_property("type").equal(filter["type"])
                    if w_filter:
                        w_filter = w_filter & type_filter
                    else:
                        w_filter = type_filter
                
                # Search
                results = collection.query.near_vector(
                    near_vector=query_embedding,
                    limit=top_k,
                    filters=w_filter,
                    return_properties=["memory_id"]
                )
                
                ids = [obj.properties["memory_id"] for obj in results.objects]
                
        except Exception as e:
            logger.error(f"Failed to query vectors: {str(e)}")
            
        return ids

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

        # Store vector
        combined_text = f"{title} " + " ".join(samples)
        memory.embedding_id = str(memory.id)
        
        metadata = {
            "id": str(memory.id), # Store ID in metadata for easier retrieval
            "workspace_id": workspace_id,
            "type": "style",
            "title": title,
        }
        
        await self._upsert_vector(str(memory.id), combined_text, metadata)

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

        # Store vector
        combined_text = f"{term} {definition}"
        memory.embedding_id = str(memory.id)
        
        metadata = {
            "id": str(memory.id),
            "workspace_id": workspace_id,
            "type": "glossary",
            "term": term,
        }
        
        await self._upsert_vector(str(memory.id), combined_text, metadata)

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
        # Try vector search first
        if self.index or self.weaviate_client:
            # Build filter
            filter_dict = {"workspace_id": workspace_id}
            if memory_type:
                filter_dict["type"] = memory_type

            # Search
            memory_ids = await self._query_vectors(query, filter_dict, top_k)

            if memory_ids:
                # Load memories from database
                db_result = await self.session.execute(
                    select(Memory).where(Memory.embedding_id.in_(memory_ids))
                )
                memories = list(db_result.scalars().all())

                # Sort by original search order (if possible)
                # This is a simple approximation
                memory_map = {str(m.id): m for m in memories}
                sorted_memories = [
                    memory_map[mid] for mid in memory_ids if mid in memory_map
                ]
                
                return sorted_memories

        # Fallback to database query if no vector DB or no results
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

        # Store vector
        combined_text = f"{topic} {summary}"
        memory.embedding_id = str(memory.id)
        
        metadata = {
            "id": str(memory.id),
            "workspace_id": workspace_id,
            "type": "knowledge",
            "topic": topic,
        }
        
        await self._upsert_vector(str(memory.id), combined_text, metadata)

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

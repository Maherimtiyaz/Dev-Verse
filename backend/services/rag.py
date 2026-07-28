"""
RAG Service for DevVerse AI

Handles:
- Document ingestion
- Embedding generation
- Vector storage (Qdrant)
- Semantic search
- Context retrieval
"""

import asyncio
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from langchain_openai import OpenAIEmbeddings
from pydantic import BaseModel, Field

from backend.core.config import settings


@dataclass
class DocumentChunk:
    """A chunk of document content."""
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None


class RAGQueryResult(BaseModel):
    """Result from RAG query."""
    content: str
    score: float
    source: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class QdrantVectorStore:
    """
    Qdrant vector database client.
    
    In production, this would use the actual Qdrant client.
    For now, provides mock functionality.
    """
    
    def __init__(
        self,
        url: Optional[str] = None,
        api_key: Optional[str] = None,
        collection_name: str = "devverse_documents",
    ):
        self.url = url or settings.QDRANT_URL
        self.api_key = api_key or settings.QDRANT_API_KEY
        self.collection_name = collection_name
        self._initialized = False
        # In production:
        # from qdrant_client import QdrantClient
        # self.client = QdrantClient(url=self.url, api_key=self.api_key)
    
    async def initialize(self) -> bool:
        """Initialize the vector store connection."""
        try:
            # In production: check/create collection
            # if not self.client.collection_exists(self.collection_name):
            #     self.client.create_collection(...)
            self._initialized = True
            return True
        except Exception as e:
            print(f"Failed to initialize Qdrant: {e}")
            return False
    
    async def upsert(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        payloads: List[Dict[str, Any]],
    ) -> bool:
        """Upsert documents into the vector store."""
        if not self._initialized:
            await self.initialize()
        
        try:
            # In production:
            # self.client.upsert(
            #     collection_name=self.collection_name,
            #     points=[...],
            # )
            return True
        except Exception as e:
            print(f"Failed to upsert: {e}")
            return False
    
    async def search(
        self,
        query_embedding: List[float],
        limit: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[RAGQueryResult]:
        """Search for similar documents."""
        if not self._initialized:
            await self.initialize()
        
        try:
            # In production:
            # results = self.client.search(
            #     collection_name=self.collection_name,
            #     query_vector=query_embedding,
            #     limit=limit,
            #     query_filter=filter_dict,
            # )
            
            # Mock results for now
            return [
                RAGQueryResult(
                    content="Mock document content for testing",
                    score=0.95,
                    source="mock_source",
                    metadata={"type": "documentation"}
                )
            ]
        except Exception as e:
            print(f"Search failed: {e}")
            return []
    
    async def delete(self, ids: List[str]) -> bool:
        """Delete documents by ID."""
        try:
            # In production: self.client.delete(...)
            return True
        except Exception as e:
            print(f"Delete failed: {e}")
            return False


class RAGService:
    """
    Main RAG service orchestrating document processing and retrieval.
    
    Features:
    - Document chunking
    - Embedding generation
    - Vector storage
    - Semantic search with filtering
    - Context assembly for LLM prompts
    """
    
    def __init__(self):
        self.vector_store = QdrantVectorStore()
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=settings.OPENAI_API_KEY,
        )
        self.chunk_size = 500
        self.chunk_overlap = 50
    
    def _chunk_document(
        self, 
        content: str, 
        metadata: Dict[str, Any]
    ) -> List[DocumentChunk]:
        """Split document into overlapping chunks."""
        chunks = []
        words = content.split()
        
        for i in range(0, len(words), self.chunk_size - self.chunk_overlap):
            chunk_words = words[i:i + self.chunk_size]
            chunk_content = " ".join(chunk_words)
            
            chunks.append(DocumentChunk(
                content=chunk_content,
                metadata={
                    **metadata,
                    "chunk_index": len(chunks),
                    "total_chunks": (len(words) // (self.chunk_size - self.chunk_overlap)) + 1,
                }
            ))
        
        return chunks
    
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for text."""
        try:
            embedding = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.embeddings.embed_query(text)
            )
            return embedding
        except Exception as e:
            print(f"Embedding failed: {e}")
            return [0.0] * 384  # Return zero vector on failure
    
    async def ingest_document(
        self,
        doc_id: str,
        content: str,
        metadata: Dict[str, Any],
    ) -> bool:
        """
        Ingest a document into the RAG system.
        
        Steps:
        1. Chunk the document
        2. Generate embeddings for each chunk
        3. Store in vector database
        """
        # Chunk document
        chunks = self._chunk_document(content, metadata)
        
        if not chunks:
            return False
        
        # Generate embeddings
        embeddings = []
        payloads = []
        
        for chunk in chunks:
            embedding = await self.embed_text(chunk.content)
            embeddings.append(embedding)
            
            payload = {
                "doc_id": doc_id,
                "content": chunk.content,
                "chunk_index": chunk.metadata["chunk_index"],
                **metadata
            }
            payloads.append(payload)
        
        # Store in vector DB
        ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
        success = await self.vector_store.upsert(ids, embeddings, payloads)
        
        return success
    
    async def search_documents(
        self,
        query: str,
        limit: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[RAGQueryResult]:
        """
        Search for relevant documents.
        
        Steps:
        1. Generate query embedding
        2. Search vector database
        3. Return ranked results
        """
        # Generate query embedding
        query_embedding = await self.embed_text(query)
        
        # Search
        results = await self.vector_store.search(
            query_embedding=query_embedding,
            limit=limit,
            filter_dict=filters,
        )
        
        return results
    
    async def get_context_for_query(
        self,
        query: str,
        max_tokens: int = 2000,
        filters: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Retrieve contextual information for an LLM query.
        
        Assembles relevant document chunks into a context string.
        """
        results = await self.search_documents(query, limit=10, filters=filters)
        
        context_parts = []
        total_tokens = 0
        
        for result in results:
            # Simple token estimation (1 token ≈ 4 chars)
            estimated_tokens = len(result.content) // 4
            
            if total_tokens + estimated_tokens > max_tokens:
                break
            
            context_parts.append(f"[Source: {result.source}]\n{result.content}")
            total_tokens += estimated_tokens
        
        return "\n\n---\n\n".join(context_parts)
    
    async def ingest_github_readme(
        self,
        repo_owner: str,
        repo_name: str,
        readme_content: str,
    ) -> bool:
        """Ingest a GitHub README into the RAG system."""
        metadata = {
            "type": "github_readme",
            "repo_owner": repo_owner,
            "repo_name": repo_name,
            "source_url": f"https://github.com/{repo_owner}/{repo_name}",
        }
        
        doc_id = f"github_{repo_owner}_{repo_name}"
        return await self.ingest_document(doc_id, readme_content, metadata)
    
    async def ingest_codebase_docs(
        self,
        project_id: str,
        docs: List[Dict[str, str]],
    ) -> int:
        """
        Ingest multiple documentation files.
        
        Args:
            project_id: Unique project identifier
            docs: List of {path, content} dicts
        
        Returns:
            Number of successfully ingested documents
        """
        success_count = 0
        
        for doc in docs:
            metadata = {
                "type": "codebase_doc",
                "project_id": project_id,
                "file_path": doc.get("path", "unknown"),
            }
            
            success = await self.ingest_document(
                doc_id=f"{project_id}_{doc.get('path', 'unknown')}",
                content=doc.get("content", ""),
                metadata=metadata,
            )
            
            if success:
                success_count += 1
        
        return success_count


# Singleton instance
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """Get or create the RAG service singleton."""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service

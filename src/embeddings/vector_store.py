"""
Vector store module for managing resume embeddings and semantic search.
Uses ChromaDB for persistent storage and LangChain's OpenAI embeddings.
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

import chromadb
from langchain.schema import Document
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

from src.core.config import settings

logger = logging.getLogger(__name__)

# Global vector store instance (singleton pattern)
_vector_store = None


class ResumeVectorStore:
    """
    Manages resume embeddings and semantic search using ChromaDB.
    """

    def __init__(
        self,
        persist_dir: Optional[str] = None,
        collection_name: str = "resumes",
        embedding_model: Optional[str] = None
    ):
        """
        Initialize the ResumeVectorStore.

        Args:
            persist_dir: Directory for ChromaDB persistence (default from config)
            collection_name: Name of the ChromaDB collection
            embedding_model: Embedding model name (default from config)
        """
        self.persist_dir = persist_dir or settings.CHROMA_PERSIST_DIR
        self.collection_name = collection_name
        self.embedding_model = embedding_model or settings.OPENAI_EMBEDDING_MODEL

        # Create persist directory if it doesn't exist
        Path(self.persist_dir).mkdir(parents=True, exist_ok=True)

        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(
            model=self.embedding_model,
            api_key=settings.OPENAI_API_KEY
        )

        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(path=self.persist_dir)

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

        # Initialize LangChain Chroma wrapper
        self.vector_store = Chroma(
            client=self.client,
            collection_name=collection_name,
            embedding_function=self.embeddings
        )

        logger.info(
            f"ResumeVectorStore initialized with collection '{collection_name}' "
            f"at {self.persist_dir} using model {self.embedding_model}"
        )

    def ingest_documents(
        self,
        documents: List[Document],
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        Ingest documents into the vector store, avoiding duplicates.

        Converts any list metadata values to comma-separated strings before ingestion
        to ensure compatibility with ChromaDB metadata storage.

        Args:
            documents: List of LangChain Document objects
            batch_size: Batch size for processing documents

        Returns:
            Dictionary with ingestion results

        Raises:
            ValueError: If documents list is empty or invalid
        """
        if not isinstance(documents, list) or not documents:
            raise ValueError("documents must be a non-empty list")

        # Get existing document IDs to avoid duplicates
        existing_docs = self.collection.get()
        existing_ids = set(existing_docs.get("ids", []))

        # Filter out duplicates
        new_documents = []
        duplicate_count = 0

        for doc in documents:
            doc_id = doc.metadata.get("chunk_id")
            if not doc_id:
                # Generate ID from metadata if not present
                resume_id = doc.metadata.get("resume_id", "unknown")
                chunk_idx = doc.metadata.get("chunk_index", 0)
                doc_id = f"{resume_id}_chunk_{chunk_idx}"

            if doc_id in existing_ids:
                duplicate_count += 1
                logger.debug(f"Skipping duplicate document: {doc_id}")
            else:
                # Add chunk_id to metadata
                doc.metadata["chunk_id"] = doc_id
                new_documents.append(doc)

        if not new_documents:
            logger.warning(f"No new documents to ingest. All {duplicate_count} documents are duplicates.")
            return {
                "ingested": 0,
                "duplicates": duplicate_count,
                "total_in_store": len(existing_ids)
            }

        # Ingest documents in batches
        total_ingested = 0
        errors = []

        for i in range(0, len(new_documents), batch_size):
            batch = new_documents[i:i + batch_size]
            try:
                # Convert list metadata values to comma-separated strings
                # ChromaDB requires metadata values to be strings, not lists
                for doc in batch:
                    doc.metadata = self._normalize_metadata(doc.metadata)

                ids = self.vector_store.add_documents(batch)
                total_ingested += len(ids)
                logger.info(f"Ingested batch of {len(ids)} documents")
            except Exception as e:
                error_msg = f"Error ingesting batch {i//batch_size}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)

        logger.info(
            f"Successfully ingested {total_ingested} new documents. "
            f"Skipped {duplicate_count} duplicates."
        )

        return {
            "ingested": total_ingested,
            "duplicates": duplicate_count,
            "total_in_store": len(existing_ids) + total_ingested,
            "errors": errors
        }

    def _normalize_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert any list metadata values to comma-separated strings.

        ChromaDB has limitations on metadata types. Lists need to be converted
        to comma-separated strings for compatibility.

        Example:
            Input:  {"top_skills": ["Python", "SQL"], "experience_level": "senior"}
            Output: {"top_skills": "Python, SQL", "experience_level": "senior"}

        Args:
            metadata: Dictionary of metadata from a Document

        Returns:
            Dictionary with list values converted to comma-separated strings

        """
        try:
            normalized = {}

            for key, value in metadata.items():
                if isinstance(value, list):
                    # Convert list to comma-separated string
                    # Handle list of strings
                    str_values = [str(v) for v in value]
                    normalized[key] = ", ".join(str_values)
                    logger.debug(
                        f"Converted list metadata '{key}': {value} → '{normalized[key]}'"
                    )
                else:
                    # Keep non-list values as-is
                    normalized[key] = value

            return normalized

        except Exception as e:
            logger.error(f"Error normalizing metadata: {str(e)}")
            # Return original metadata if normalization fails
            return metadata

    def semantic_search(
        self,
        query: str,
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[Document, float]]:
        """
        Perform semantic similarity search using ChromaDB's native query method.

        Uses ChromaDB's native query() instead of LangChain wrapper for better reliability.
        Converts cosine distance to similarity score (1 - distance).

        Args:
            query: Search query string
            top_k: Number of results to return (default from config)
            filters: Dictionary of metadata filters (e.g., experience_level, role_category)

        Returns:
            List of (Document, similarity_score) tuples sorted by score (descending)

        Raises:
            ValueError: If query is empty
        """
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query must be a non-empty string")

        top_k = top_k or settings.TOP_K

        try:
            logger.info(f"Performing semantic search with query: '{query[:100]}...'")

            # Get query embedding using OpenAI embeddings
            logger.debug("Generating query embedding...")
            query_embedding = self.embeddings.embed_query(query)
            logger.debug(f"Query embedding generated (dimension: {len(query_embedding)})")

            # Use ChromaDB's native query method instead of LangChain wrapper
            # This is more reliable and gives us access to raw distance scores
            logger.info(f"Querying ChromaDB collection for top {top_k} results...")
            chroma_results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )

            num_results = len(chroma_results["documents"][0]) if chroma_results["documents"] else 0
            logger.info(
                f"ChromaDB query returned: {num_results} results from {top_k} requested"
            )

            if not chroma_results["documents"] or not chroma_results["documents"][0]:
                logger.warning(f"No results returned from ChromaDB query")
                return []

            # Convert ChromaDB results to List[Tuple[Document, float]] format
            results = []
            documents = chroma_results["documents"][0]
            metadatas = chroma_results["metadatas"][0]
            distances = chroma_results["distances"][0]

            logger.debug(f"Processing {len(documents)} results...")

            for idx, (document_text, metadata, distance) in enumerate(
                zip(documents, metadatas, distances)
            ):
                # Convert cosine distance to similarity score (0-1)
                # distance is cosine distance, similarity = 1 - distance
                similarity_score = 1 - distance

                # Create LangChain Document object
                doc = Document(
                    page_content=document_text,
                    metadata=metadata or {}
                )

                results.append((doc, similarity_score))

            # Filter results if filters provided
            if filters:
                logger.info(f"Applying metadata filters: {filters}")
                results = self._filter_results(results, filters, top_k)

            logger.info(
                f"Semantic search completed: returned {len(results)} results. "
                f"Score range: [{min([s for _, s in results]):.4f}, {max([s for _, s in results]):.4f}]"
            )

            return results

        except Exception as e:
            logger.error(f"Error performing semantic search: {str(e)}", exc_info=True)
            return []

    def _filter_results(
        self,
        results: List[Tuple[Document, float]],
        filters: Dict[str, Any],
        top_k: int
    ) -> List[Tuple[Document, float]]:
        """
        Filter search results based on metadata filters.

        Args:
            results: List of (Document, score) tuples from semantic search
            filters: Metadata filters to apply
            top_k: Number of results to return after filtering

        Returns:
            Filtered list of (Document, score) tuples
        """
        logger.debug(f"Filtering {len(results)} results with filters: {filters}")

        filtered_results = []

        for doc, score in results:
            metadata = doc.metadata
            match = True

            for filter_key, filter_value in filters.items():
                if filter_key not in metadata:
                    match = False
                    break

                # Handle different filter types
                if isinstance(filter_value, list):
                    if metadata[filter_key] not in filter_value:
                        match = False
                        break
                elif isinstance(filter_value, dict):
                    # Handle range filters (e.g., {"min": 5, "max": 10})
                    if "min" in filter_value and metadata[filter_key] < filter_value["min"]:
                        match = False
                        break
                    if "max" in filter_value and metadata[filter_key] > filter_value["max"]:
                        match = False
                        break
                else:
                    if metadata[filter_key] != filter_value:
                        match = False
                        break

            if match:
                filtered_results.append((doc, score))
                if len(filtered_results) >= top_k:
                    break

        logger.info(
            f"After filtering: {len(filtered_results)} results from {len(results)} candidates "
            f"(filters: {filters})"
        )
        return filtered_results

    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store collection.

        Returns:
            Dictionary with collection statistics
        """
        try:
            collection_data = self.collection.get()
            documents = collection_data.get("documents", [])
            metadatas = collection_data.get("metadatas", [])

            total_documents = len(documents)

            # Analyze metadata
            resumes_by_id = {}
            categories = {}
            experience_levels = {}
            role_categories = {}

            for metadata in metadatas:
                resume_id = metadata.get("resume_id", "unknown")
                category = metadata.get("category", "Uncategorized")
                exp_level = metadata.get("experience_level", "unknown")
                role = metadata.get("role_category", "unknown")

                resumes_by_id[resume_id] = resumes_by_id.get(resume_id, 0) + 1
                categories[category] = categories.get(category, 0) + 1
                experience_levels[exp_level] = experience_levels.get(exp_level, 0) + 1
                role_categories[role] = role_categories.get(role, 0) + 1

            stats = {
                "total_documents": total_documents,
                "total_resumes": len(resumes_by_id),
                "avg_chunks_per_resume": total_documents / len(resumes_by_id) if resumes_by_id else 0,
                "resumes_by_id": resumes_by_id,
                "categories": categories,
                "experience_levels": experience_levels,
                "role_categories": role_categories,
                "collection_name": self.collection_name,
                "persist_dir": self.persist_dir
            }

            logger.info(f"Collection stats: {total_documents} documents from {len(resumes_by_id)} resumes")
            return stats

        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            return {
                "total_documents": 0,
                "error": str(e)
            }

    def delete_resume(self, resume_id: str) -> int:
        """
        Delete all chunks for a specific resume.

        Args:
            resume_id: The resume ID to delete

        Returns:
            Number of documents deleted
        """
        try:
            # Get all documents for this resume
            results = self.collection.get(
                where={"resume_id": {"$eq": resume_id}}
            )
            doc_ids = results.get("ids", [])

            if doc_ids:
                self.collection.delete(ids=doc_ids)
                logger.info(f"Deleted {len(doc_ids)} chunks for resume {resume_id}")
                return len(doc_ids)
            else:
                logger.warning(f"No documents found for resume {resume_id}")
                return 0

        except Exception as e:
            logger.error(f"Error deleting resume {resume_id}: {str(e)}")
            return 0

    def clear_collection(self) -> bool:
        """
        Clear all documents from the collection.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete the existing collection
            self.client.delete_collection(name=self.collection_name)
            # Recreate it
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            # Reinitialize the Chroma wrapper
            self.vector_store = Chroma(
                client=self.client,
                collection_name=self.collection_name,
                embedding_function=self.embeddings
            )
            logger.info(f"Successfully cleared collection {self.collection_name}")
            return True
        except Exception as e:
            logger.error(f"Error clearing collection: {str(e)}")
            return False


def init_vector_store(
    persist_dir: Optional[str] = None,
    collection_name: str = "resumes",
    embedding_model: Optional[str] = None
) -> ResumeVectorStore:
    """
    Initialize or load a persistent ChromaDB vector store.

    Args:
        persist_dir: Directory for ChromaDB persistence (default from config)
        collection_name: Name of the collection (default: "resumes")
        embedding_model: Embedding model name (default from config)

    Returns:
        ResumeVectorStore instance
    """
    global _vector_store

    if _vector_store is None:
        _vector_store = ResumeVectorStore(
            persist_dir=persist_dir,
            collection_name=collection_name,
            embedding_model=embedding_model
        )

    return _vector_store


def get_vector_store() -> Optional[ResumeVectorStore]:
    """Get the current vector store instance."""
    return _vector_store


def ingest_resumes(
    documents: List[Document],
    vector_store: Optional[ResumeVectorStore] = None
) -> Dict[str, Any]:
    """
    Convenience function to ingest documents into the vector store.

    Args:
        documents: List of LangChain Document objects
        vector_store: Vector store instance (default: global instance)

    Returns:
        Ingestion results dictionary
    """
    if vector_store is None:
        vector_store = get_vector_store()
        if vector_store is None:
            raise RuntimeError("Vector store not initialized. Call init_vector_store() first.")

    return vector_store.ingest_documents(documents)


def semantic_search(
    query: str,
    top_k: Optional[int] = None,
    filters: Optional[Dict[str, Any]] = None,
    vector_store: Optional[ResumeVectorStore] = None
) -> List[Tuple[Document, float]]:
    """
    Convenience function for semantic search.

    Args:
        query: Search query string
        top_k: Number of results to return
        filters: Metadata filters
        vector_store: Vector store instance (default: global instance)

    Returns:
        List of (Document, similarity_score) tuples
    """
    if vector_store is None:
        vector_store = get_vector_store()
        if vector_store is None:
            raise RuntimeError("Vector store not initialized. Call init_vector_store() first.")

    return vector_store.semantic_search(query, top_k, filters)


def get_collection_stats(
    vector_store: Optional[ResumeVectorStore] = None
) -> Dict[str, Any]:
    """
    Convenience function to get collection statistics.

    Args:
        vector_store: Vector store instance (default: global instance)

    Returns:
        Collection statistics dictionary
    """
    if vector_store is None:
        vector_store = get_vector_store()
        if vector_store is None:
            raise RuntimeError("Vector store not initialized. Call init_vector_store() first.")

    return vector_store.get_collection_stats()

"""
Document chunking module for splitting resume text into overlapping chunks.
"""
import logging
from typing import List, Dict, Any, Optional
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

from src.core.config import settings

logger = logging.getLogger(__name__)


class ResumeChunker:
    """
    Handles splitting resume text into overlapping chunks with metadata.
    Uses LangChain's RecursiveCharacterTextSplitter for intelligent chunking.
    """

    def __init__(
        self,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        separators: Optional[List[str]] = None
    ):
        """
        Initialize the ResumeChunker.

        Args:
            chunk_size: Size of each chunk in characters (default from config)
            chunk_overlap: Overlap between chunks in characters (default from config)
            separators: Custom separators for splitting (default: LangChain defaults)
        """
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP

        # Custom separators optimized for resume documents
        # Splits at sentence, section, and word boundaries
        self.separators = separators or [
            "\n\n",  # Paragraph breaks
            "\n",    # Line breaks
            ". ",    # Sentence breaks
            " ",     # Word breaks
            ""       # Character breaks
        ]

        # Initialize the text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=self.separators,
            length_function=len,
            is_separator_regex=False
        )

        logger.info(
            f"ResumeChunker initialized with chunk_size={self.chunk_size}, "
            f"chunk_overlap={self.chunk_overlap}"
        )

    def chunk_resume(
        self,
        resume_text: str,
        resume_id: str,
        category: str = "Uncategorized",
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Split resume text into overlapping chunks with metadata.

        Args:
            resume_text: The full resume text to chunk
            resume_id: Unique identifier for the resume
            category: Category/classification of the resume
            metadata: Additional metadata to attach to each chunk

        Returns:
            List of LangChain Document objects with page_content and metadata

        Raises:
            ValueError: If resume_text is empty or invalid
        """
        if not isinstance(resume_text, str) or not resume_text.strip():
            raise ValueError("resume_text must be a non-empty string")

        if not isinstance(resume_id, str) or not resume_id.strip():
            raise ValueError("resume_id must be a non-empty string")

        # Prepare base metadata for all chunks
        base_metadata = {
            "resume_id": resume_id,
            "category": category,
        }

        # Merge with additional metadata if provided
        if metadata:
            if not isinstance(metadata, dict):
                raise ValueError("metadata must be a dictionary")
            base_metadata.update(metadata)

        try:
            # Split the text into chunks
            text_chunks = self.text_splitter.split_text(resume_text)

            if not text_chunks:
                logger.warning(f"No chunks created for resume {resume_id}")
                return []

            # Create Document objects with metadata
            documents = []
            for chunk_index, chunk_text in enumerate(text_chunks):
                # Create metadata for this chunk
                chunk_metadata = base_metadata.copy()
                chunk_metadata["chunk_index"] = chunk_index
                chunk_metadata["chunk_count"] = len(text_chunks)
                chunk_metadata["chunk_length"] = len(chunk_text)
                chunk_metadata["chunk_words"] = len(chunk_text.split())

                # Create Document object
                document = Document(
                    page_content=chunk_text,
                    metadata=chunk_metadata
                )

                documents.append(document)

            logger.info(
                f"Created {len(documents)} chunks for resume {resume_id} "
                f"(category: {category})"
            )

            return documents

        except Exception as e:
            logger.error(f"Error chunking resume {resume_id}: {str(e)}")
            raise

    def chunk_resumes_batch(
        self,
        resumes: List[Dict[str, str]],
        metadata_field: Optional[str] = None
    ) -> List[Document]:
        """
        Chunk multiple resumes and return combined list of documents.

        Args:
            resumes: List of resume dicts with keys: id, resume_text, category
            metadata_field: Optional additional field name to include as metadata

        Returns:
            Combined list of LangChain Document objects from all resumes

        Raises:
            ValueError: If resumes list is invalid or empty
        """
        if not isinstance(resumes, list) or not resumes:
            raise ValueError("resumes must be a non-empty list")

        all_documents = []
        failed_count = 0

        for idx, resume in enumerate(resumes):
            try:
                if not isinstance(resume, dict):
                    logger.warning(f"Skipping item {idx}: not a dictionary")
                    failed_count += 1
                    continue

                resume_id = resume.get("id")
                resume_text = resume.get("resume_text")
                category = resume.get("category", "Uncategorized")

                if not resume_id or not resume_text:
                    logger.warning(
                        f"Skipping resume at index {idx}: "
                        f"missing id or resume_text"
                    )
                    failed_count += 1
                    continue

                # Prepare additional metadata
                extra_metadata = None
                if metadata_field and metadata_field in resume:
                    extra_metadata = {metadata_field: resume[metadata_field]}

                # Chunk this resume
                documents = self.chunk_resume(
                    resume_text=resume_text,
                    resume_id=resume_id,
                    category=category,
                    metadata=extra_metadata
                )

                all_documents.extend(documents)

            except Exception as e:
                logger.error(f"Error processing resume at index {idx}: {str(e)}")
                failed_count += 1
                continue

        logger.info(
            f"Successfully chunked {len(resumes) - failed_count}/{len(resumes)} resumes. "
            f"Total chunks created: {len(all_documents)}"
        )

        if failed_count > 0:
            logger.warning(f"Failed to process {failed_count} resumes")

        return all_documents

    def get_chunking_stats(self, documents: List[Document]) -> Dict[str, Any]:
        """
        Calculate statistics about the chunked documents.

        Args:
            documents: List of LangChain Document objects

        Returns:
            Dictionary with chunking statistics
        """
        if not documents:
            return {
                "total_chunks": 0,
                "total_characters": 0,
                "total_words": 0,
                "avg_chunk_size": 0,
                "resumes": {}
            }

        total_chars = 0
        total_words = 0
        resumes_stats = {}

        for doc in documents:
            content = doc.page_content
            metadata = doc.metadata or {}

            total_chars += len(content)
            total_words += len(content.split())

            resume_id = metadata.get("resume_id", "unknown")
            if resume_id not in resumes_stats:
                resumes_stats[resume_id] = {
                    "chunks": 0,
                    "total_size": 0,
                    "category": metadata.get("category", "Uncategorized")
                }

            resumes_stats[resume_id]["chunks"] += 1
            resumes_stats[resume_id]["total_size"] += len(content)

        stats = {
            "total_chunks": len(documents),
            "total_characters": total_chars,
            "total_words": total_words,
            "avg_chunk_size": total_chars / len(documents) if documents else 0,
            "avg_chunk_words": total_words / len(documents) if documents else 0,
            "resumes": resumes_stats,
            "unique_resumes": len(resumes_stats)
        }

        return stats


def chunk_resume_text(
    resume_text: str,
    resume_id: str,
    category: str = "Uncategorized",
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None
) -> List[Document]:
    """
    Convenience function to chunk a single resume text.

    Args:
        resume_text: The resume text to chunk
        resume_id: Unique identifier for the resume
        category: Category/classification of the resume
        chunk_size: Optional custom chunk size
        chunk_overlap: Optional custom chunk overlap

    Returns:
        List of LangChain Document objects
    """
    chunker = ResumeChunker(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    return chunker.chunk_resume(resume_text, resume_id, category)


def chunk_resumes_batch(
    resumes: List[Dict[str, str]],
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None
) -> List[Document]:
    """
    Convenience function to chunk multiple resumes.

    Args:
        resumes: List of resume dicts with keys: id, resume_text, category
        chunk_size: Optional custom chunk size
        chunk_overlap: Optional custom chunk overlap

    Returns:
        Combined list of LangChain Document objects from all resumes
    """
    chunker = ResumeChunker(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    return chunker.chunk_resumes_batch(resumes)

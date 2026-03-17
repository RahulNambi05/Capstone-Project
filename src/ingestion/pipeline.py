"""
End-to-end ingestion pipeline for resume data.
Orchestrates loading, validation, metadata extraction, chunking, and vector storage.
"""
import logging
from typing import Dict, List, Any
from datetime import datetime

from src.ingestion.resume_loader import load_resumes_from_csv, validate_resume
from src.ingestion.metadata_extractor import MetadataExtractor
from src.ingestion.chunker import ResumeChunker
from src.embeddings.vector_store import init_vector_store, ResumeVectorStore
from langchain.schema import Document

logger = logging.getLogger(__name__)


class ResumePipeline:
    """
    End-to-end pipeline for resume ingestion and vector storage.
    """

    def __init__(
        self,
        vector_store: ResumeVectorStore = None,
        extract_metadata: bool = True,
        skip_invalid: bool = True
    ):
        """
        Initialize the ResumePipeline.

        Args:
            vector_store: ResumeVectorStore instance (creates default if None)
            extract_metadata: Whether to extract metadata using LLM (default: True)
            skip_invalid: Whether to skip invalid resumes (default: True)
        """
        self.vector_store = vector_store or init_vector_store()
        self.extract_metadata_flag = extract_metadata
        self.skip_invalid = skip_invalid

        # Initialize components
        self.chunker = ResumeChunker()
        self.metadata_extractor = MetadataExtractor() if extract_metadata else None

        logger.info(
            f"ResumePipeline initialized with metadata_extraction={extract_metadata}, "
            f"skip_invalid={skip_invalid}"
        )

    def run(
        self,
        csv_path: str,
        progress_interval: int = 50,
        resume_id_column: str = "ID",
        resume_text_column: str = "Resume_str",
        category_column: str = "Category"
    ) -> Dict[str, Any]:
        """
        Run the complete resume ingestion pipeline.

        Args:
            csv_path: Path to the CSV file with resumes
            progress_interval: Print progress every N resumes (default: 50)
            resume_id_column: Name of ID column (default: "ID")
            resume_text_column: Name of resume text column (default: "Resume_str")
            category_column: Name of category column (default: "Category")

        Returns:
            Dictionary with pipeline summary:
            {
                "total_processed": int,
                "total_failed": int,
                "total_chunks": int,
                "execution_time": float (seconds),
                "timestamp": str,
                "details": {
                    "validation_failures": int,
                    "metadata_extraction_failures": int,
                    "chunking_failures": int,
                    "ingestion_failures": int,
                    "resumes_per_category": dict,
                    "chunks_per_resume": float
                }
            }
        """
        start_time = datetime.now()

        logger.info(f"Starting resume ingestion pipeline with CSV: {csv_path}")
        print(f"\n{'=' * 70}")
        print(f"Resume Ingestion Pipeline")
        print(f"{'=' * 70}\n")

        # Track statistics
        total_processed = 0
        total_failed = 0
        total_chunks_ingested = 0
        validation_failures = 0
        metadata_failures = 0
        chunking_failures = 0
        ingestion_failures = 0
        resumes_by_category = {}

        try:
            # Step 1: Load resumes from CSV
            print(f"[Step 1/5] Loading resumes from CSV...")
            resumes = load_resumes_from_csv(
                file_path=csv_path,
                id_column=resume_id_column,
                resume_column=resume_text_column,
                category_column=category_column,
                validate=False,  # Will validate individually
                skip_invalid=False
            )

            if not resumes:
                logger.error("No resumes loaded from CSV")
                return self._create_summary(
                    0, 0, 0, 0, 0, 0, 0, 0, {}, start_time
                )

            print(f"✓ Loaded {len(resumes)} resumes from CSV\n")

            # Step 2: Process each resume
            print(f"[Step 2/5] Processing resumes...")
            print(f"{'Progress':<20} | {'Category':<20} | {'Status':<30}\n")

            for idx, resume in enumerate(resumes, 1):
                try:
                    resume_id = resume.get("id")
                    category = resume.get("category", "Uncategorized")
                    resume_text = resume.get("resume_text", "")

                    # Track category
                    resumes_by_category[category] = resumes_by_category.get(category, 0) + 1

                    # Step 2a: Validate resume
                    if not validate_resume(resume_text):
                        logger.warning(f"Resume {resume_id} failed validation")
                        validation_failures += 1
                        total_failed += 1
                        if self.skip_invalid:
                            self._print_progress(idx, len(resumes), category, "Skipped (validation)")
                            continue
                        else:
                            logger.debug(f"Processing invalid resume {resume_id} anyway")

                    # Step 2b: Extract metadata
                    metadata = {"category": category}
                    if self.extract_metadata_flag:
                        try:
                            extracted = self.metadata_extractor.extract_metadata(resume_text)
                            metadata.update(extracted)
                        except Exception as e:
                            logger.error(f"Failed to extract metadata for {resume_id}: {str(e)}")
                            metadata_failures += 1
                            total_failed += 1
                            if self.skip_invalid:
                                self._print_progress(idx, len(resumes), category, "Skipped (metadata)")
                                continue

                    # Step 2c: Chunk resume
                    try:
                        chunks = self.chunker.chunk_resume(
                            resume_text=resume_text,
                            resume_id=resume_id,
                            category=category,
                            metadata=metadata
                        )
                    except Exception as e:
                        logger.error(f"Failed to chunk resume {resume_id}: {str(e)}")
                        chunking_failures += 1
                        total_failed += 1
                        if self.skip_invalid:
                            self._print_progress(idx, len(resumes), category, "Skipped (chunking)")
                            continue

                    # Step 2d: Ingest chunks into vector store
                    try:
                        result = self.vector_store.ingest_documents(chunks)
                        total_chunks_ingested += result["ingested"]
                    except Exception as e:
                        logger.error(f"Failed to ingest chunks for {resume_id}: {str(e)}")
                        ingestion_failures += 1
                        total_failed += 1
                        if self.skip_invalid:
                            self._print_progress(idx, len(resumes), category, "Skipped (ingestion)")
                            continue

                    total_processed += 1
                    chunk_count = len(chunks)

                    # Print progress
                    if idx % progress_interval == 0 or idx == len(resumes):
                        self._print_progress(
                            idx, len(resumes), category,
                            f"✓ {chunk_count} chunks ingested"
                        )

                except Exception as e:
                    logger.error(f"Error processing resume at index {idx}: {str(e)}")
                    total_failed += 1
                    self._print_progress(idx, len(resumes), category, "Failed (unexpected)")
                    continue

            # Execution summary
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            # Get final vector store stats
            vector_stats = self.vector_store.get_collection_stats()

            summary = self._create_summary(
                total_processed,
                total_failed,
                total_chunks_ingested,
                validation_failures,
                metadata_failures,
                chunking_failures,
                ingestion_failures,
                total_chunks_ingested / total_processed if total_processed > 0 else 0,
                resumes_by_category,
                start_time
            )

            # Print final summary
            self._print_summary(summary, vector_stats)

            return summary

        except Exception as e:
            logger.error(f"Fatal error in ingestion pipeline: {str(e)}")
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            print(f"\n❌ Pipeline failed with error: {str(e)}")
            return {
                "total_processed": total_processed,
                "total_failed": total_failed,
                "total_chunks": total_chunks_ingested,
                "execution_time": execution_time,
                "timestamp": start_time.isoformat(),
                "error": str(e)
            }

    def _print_progress(
        self,
        current: int,
        total: int,
        category: str,
        status: str
    ) -> None:
        """Print progress information."""
        progress_pct = (current / total) * 100 if total > 0 else 0
        progress_bar = f"{current}/{total} ({progress_pct:.1f}%)"
        print(f"{progress_bar:<20} | {category:<20} | {status:<30}")

    def _create_summary(
        self,
        processed: int,
        failed: int,
        chunks: int,
        val_fail: int,
        meta_fail: int,
        chunk_fail: int,
        ingest_fail: int,
        chunks_per_resume: float,
        categories: Dict[str, int],
        start_time: datetime
    ) -> Dict[str, Any]:
        """Create pipeline summary dictionary."""
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()

        return {
            "total_processed": processed,
            "total_failed": failed,
            "total_chunks": chunks,
            "execution_time": execution_time,
            "timestamp": start_time.isoformat(),
            "details": {
                "validation_failures": val_fail,
                "metadata_extraction_failures": meta_fail,
                "chunking_failures": chunk_fail,
                "ingestion_failures": ingest_fail,
                "resumes_per_category": categories,
                "chunks_per_resume": round(chunks_per_resume, 2)
            }
        }

    def _print_summary(
        self,
        summary: Dict[str, Any],
        vector_stats: Dict[str, Any]
    ) -> None:
        """Print pipeline execution summary."""
        details = summary.get("details", {})

        print(f"\n{'=' * 70}")
        print(f"Pipeline Execution Summary")
        print(f"{'=' * 70}\n")

        print(f"Execution Results:")
        print(f"  Total processed: {summary['total_processed']}")
        print(f"  Total failed: {summary['total_failed']}")
        print(f"  Total chunks created: {summary['total_chunks']}")
        print(f"  Execution time: {summary['execution_time']:.2f} seconds")

        if details.get('resumes_per_category'):
            print(f"\nResumes by category:")
            for category, count in details['resumes_per_category'].items():
                print(f"  {category}: {count}")

        print(f"\nFailure Breakdown:")
        print(f"  Validation failures: {details.get('validation_failures', 0)}")
        print(f"  Metadata extraction failures: {details.get('metadata_extraction_failures', 0)}")
        print(f"  Chunking failures: {details.get('chunking_failures', 0)}")
        print(f"  Ingestion failures: {details.get('ingestion_failures', 0)}")

        print(f"\nMetrics:")
        print(f"  Average chunks per resume: {details.get('chunks_per_resume', 0)}")
        print(f"  Total documents in vector store: {vector_stats.get('total_documents', 0)}")
        print(f"  Total resumes in vector store: {vector_stats.get('total_resumes', 0)}")

        if vector_stats.get('role_categories'):
            print(f"\nRole categories in vector store:")
            for role, count in vector_stats['role_categories'].items():
                print(f"  {role}: {count} chunks")

        print(f"\n{'=' * 70}\n")


def run_ingestion_pipeline(
    csv_path: str,
    progress_interval: int = 50,
    extract_metadata: bool = True,
    skip_invalid: bool = True
) -> Dict[str, Any]:
    """
    Convenience function to run the complete ingestion pipeline.

    Args:
        csv_path: Path to the CSV file with resumes
        progress_interval: Print progress every N resumes (default: 50)
        extract_metadata: Whether to extract metadata using LLM (default: True)
        skip_invalid: Whether to skip invalid resumes (default: True)

    Returns:
        Pipeline summary dictionary with:
        - total_processed: int
        - total_failed: int
        - total_chunks: int
        - execution_time: float
        - timestamp: str
        - details: dict with breakdown
    """
    pipeline = ResumePipeline(
        extract_metadata=extract_metadata,
        skip_invalid=skip_invalid
    )

    return pipeline.run(csv_path, progress_interval=progress_interval)

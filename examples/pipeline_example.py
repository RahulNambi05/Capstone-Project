"""
Example usage of the resume ingestion pipeline.
Demonstrates end-to-end resume loading, processing, and vector storage.
"""
import logging
from pathlib import Path
from src.ingestion.pipeline import ResumePipeline, run_ingestion_pipeline
from src.embeddings.vector_store import get_vector_store, get_collection_stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def example_basic_pipeline():
    """Example 1: Run pipeline with default settings."""
    print("\n" + "=" * 70)
    print("Example 1: Basic Pipeline Execution")
    print("=" * 70)

    csv_path = "data/resumes/resume_dataset.csv"

    # Check if file exists
    if not Path(csv_path).exists():
        print(f"\nNote: CSV file not found at {csv_path}")
        print("This example requires a resume dataset CSV file.")
        print("\nExpected CSV columns:")
        print("  - ID: Unique resume identifier")
        print("  - Resume_str: Full resume text")
        print("  - Category: Resume category/classification")
        return

    try:
        # Run pipeline with default settings
        summary = run_ingestion_pipeline(
            csv_path=csv_path,
            progress_interval=50,
            extract_metadata=True,
            skip_invalid=True
        )

        print("\nPipeline completed successfully!")
        print(f"Summary: {summary}")

    except Exception as e:
        print(f"Error running pipeline: {e}")


def example_custom_pipeline():
    """Example 2: Run pipeline with custom settings."""
    print("\n" + "=" * 70)
    print("Example 2: Custom Pipeline Configuration")
    print("=" * 70)

    csv_path = "data/resumes/resume_dataset.csv"

    if not Path(csv_path).exists():
        print(f"\nCSV file not found at {csv_path}")
        return

    try:
        # Create pipeline with custom settings
        pipeline = ResumePipeline(
            extract_metadata=True,  # Use LLM to extract metadata
            skip_invalid=True       # Skip validation failures
        )

        # Run with custom progress interval
        summary = pipeline.run(
            csv_path=csv_path,
            progress_interval=25,  # Print progress every 25 resumes
            resume_id_column="ID",
            resume_text_column="Resume_str",
            category_column="Category"
        )

        print(f"\nPipeline Results:")
        print(f"  Processed: {summary['total_processed']}")
        print(f"  Failed: {summary['total_failed']}")
        print(f"  Total chunks: {summary['total_chunks']}")
        print(f"  Time: {summary['execution_time']:.2f}s")

    except Exception as e:
        print(f"Error: {e}")


def example_skip_metadata():
    """Example 3: Run pipeline without metadata extraction (faster)."""
    print("\n" + "=" * 70)
    print("Example 3: Pipeline Without Metadata Extraction")
    print("=" * 70)

    csv_path = "data/resumes/resume_dataset.csv"

    if not Path(csv_path).exists():
        print(f"\nCSV file not found at {csv_path}")
        return

    try:
        # Run pipeline without LLM metadata extraction (faster)
        summary = run_ingestion_pipeline(
            csv_path=csv_path,
            extract_metadata=False,  # Skip LLM metadata extraction
            skip_invalid=True
        )

        print(f"\nResults (without metadata extraction):")
        print(f"  Processed: {summary['total_processed']}")
        print(f"  Chunks created: {summary['total_chunks']}")
        print(f"  Execution time: {summary['execution_time']:.2f}s")

    except Exception as e:
        print(f"Error: {e}")


def example_pipeline_with_analysis():
    """Example 4: Pipeline with post-processing analysis."""
    print("\n" + "=" * 70)
    print("Example 4: Pipeline with Vector Store Analysis")
    print("=" * 70)

    csv_path = "data/resumes/resume_dataset.csv"

    if not Path(csv_path).exists():
        print(f"\nCSV file not found at {csv_path}")
        return

    try:
        # Clear previous data if needed (optional)
        # vector_store = get_vector_store()
        # if vector_store:
        #     vector_store.clear_collection()

        # Run pipeline
        print("Running ingestion pipeline...")
        summary = run_ingestion_pipeline(
            csv_path=csv_path,
            progress_interval=50,
            extract_metadata=True
        )

        # Analyze vector store
        print("\nAnalyzing vector store contents...")
        vector_store = get_vector_store()
        if vector_store:
            stats = get_collection_stats(vector_store)

            print(f"\nVector Store Analysis:")
            print(f"  Total documents: {stats.get('total_documents', 0)}")
            print(f"  Unique resumes: {stats.get('total_resumes', 0)}")
            print(f"  Avg chunks/resume: {stats.get('avg_chunks_per_resume', 0):.2f}")

            if stats.get('experience_levels'):
                print(f"\n  Experience Level Distribution:")
                for level, count in stats['experience_levels'].items():
                    pct = (count / stats.get('total_documents', 1)) * 100
                    print(f"    {level}: {count} ({pct:.1f}%)")

            if stats.get('role_categories'):
                print(f"\n  Role Category Distribution:")
                for role, count in stats['role_categories'].items():
                    pct = (count / stats.get('total_documents', 1)) * 100
                    print(f"    {role}: {count} ({pct:.1f}%)")

    except Exception as e:
        print(f"Error: {e}")


def example_mock_pipeline():
    """Example 5: Mock pipeline with sample data (no CSV required)."""
    print("\n" + "=" * 70)
    print("Example 5: Mock Pipeline with Sample Data")
    print("=" * 70)

    # Create temporary sample data
    import tempfile
    import csv

    temp_csv = None
    try:
        # Create temporary CSV with sample data
        with tempfile.NamedTemporaryFile(
            mode='w',
            delete=False,
            suffix='.csv',
            newline=''
        ) as f:
            temp_csv = f.name
            writer = csv.DictWriter(f, fieldnames=['ID', 'Resume_str', 'Category'])
            writer.writeheader()

            # Sample resumes
            sample_resumes = [
                {
                    'ID': 'sample_001',
                    'Resume_str': 'Senior Python backend developer with 7 years of experience '
                                 'building FastAPI and Django applications. Strong expertise in '
                                 'PostgreSQL, Docker, and AWS Kubernetes. Led teams of 5 engineers. '
                                 'Expert in REST APIs, microservices, CI/CD pipelines.',
                    'Category': 'Backend Engineer'
                },
                {
                    'ID': 'sample_002',
                    'Resume_str': 'Frontend developer with 4 years in React and TypeScript. '
                                 'Skilled in responsive design, state management with Redux, '
                                 'and CSS-in-JS. Knowledge of web performance optimization '
                                 'and accessibility standards.',
                    'Category': 'Frontend Engineer'
                },
                {
                    'ID': 'sample_003',
                    'Resume_str': 'Data scientist with 5 years of ML experience. Expertise in '
                                 'TensorFlow, PyTorch, and NLP. Built recommendation systems '
                                 'and computer vision models. Proficient in Python, SQL, '
                                 'and Apache Spark for big data processing.',
                    'Category': 'Data Science'
                }
            ]

            for resume in sample_resumes:
                writer.writerow(resume)

        print(f"Created temporary CSV with {len(sample_resumes)} sample resumes")

        # Run pipeline on sample data
        print("\nRunning pipeline on sample data...")
        summary = run_ingestion_pipeline(
            csv_path=temp_csv,
            progress_interval=1,  # Print progress for each resume
            extract_metadata=False  # Skip metadata extraction for speed
        )

        print(f"\nSample Pipeline Results:")
        print(f"  Processed: {summary['total_processed']}")
        print(f"  Failed: {summary['total_failed']}")
        print(f"  Chunks: {summary['total_chunks']}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Cleanup
        if temp_csv and Path(temp_csv).exists():
            Path(temp_csv).unlink()
            print(f"\nTemporary CSV cleaned up")


def example_error_handling():
    """Example 6: Pipeline error handling and resilience."""
    print("\n" + "=" * 70)
    print("Example 6: Error Handling and Resilience")
    print("=" * 70)

    print("\nPipeline features error handling for:")
    print("  • Missing or invalid CSV files")
    print("  • Empty or short resumes (validation failure)")
    print("  • Missing skill keywords (validation failure)")
    print("  • LLM metadata extraction failures")
    print("  • Document chunking failures")
    print("  • Vector store ingestion failures")

    print("\nWhen skip_invalid=True:")
    print("  • Invalid resumes are logged and skipped")
    print("  • Pipeline continues processing remaining resumes")
    print("  • Summary includes failure counts per category")

    print("\nWhen skip_invalid=False:")
    print("  • Invalid resumes are still processed")
    print("  • Logged with warnings but included in output")

    print("\nFailure tracking:")
    print("  • Total failed count")
    print("  • Validation failures")
    print("  • Metadata extraction failures")
    print("  • Chunking failures")
    print("  • Ingestion failures")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("Resume Ingestion Pipeline Examples")
    print("=" * 70)

    print("\nNote: Examples that use actual CSV files require a resume dataset.")
    print("Download from: https://www.kaggle.com/datasets/snehaanbhawal/resume-dataset")
    print("Place the CSV in: data/resumes/resume_dataset.csv\n")

    try:
        # Run examples
        # Uncomment to run with actual CSV file:
        # example_basic_pipeline()
        # example_custom_pipeline()
        # example_skip_metadata()
        # example_pipeline_with_analysis()

        # This example works without a CSV file (creates sample data)
        example_mock_pipeline()

        # Information examples (don't require CSV)
        example_error_handling()

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\nError: {e}")

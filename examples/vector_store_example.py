"""
Example usage of the vector store module.
Demonstrates ChromaDB integration, document ingestion, and semantic search.
"""
import logging
from langchain.schema import Document
from src.embeddings.vector_store import (
    init_vector_store,
    get_vector_store,
    ingest_resumes,
    semantic_search,
    get_collection_stats,
    ResumeVectorStore
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def example_init_vector_store():
    """Example 1: Initialize the vector store."""
    print("\n" + "=" * 70)
    print("Example 1: Initialize Vector Store")
    print("=" * 70)

    try:
        # Initialize vector store
        vector_store = init_vector_store()

        print(f"\nVector store initialized successfully!")
        print(f"  Collection: {vector_store.collection_name}")
        print(f"  Persist dir: {vector_store.persist_dir}")
        print(f"  Embedding model: {vector_store.embedding_model}")

    except Exception as e:
        print(f"Error: {e}")


def example_ingest_documents():
    """Example 2: Ingest documents into the vector store."""
    print("\n" + "=" * 70)
    print("Example 2: Ingest Documents")
    print("=" * 70)

    try:
        vector_store = init_vector_store()

        # Create sample documents
        documents = [
            Document(
                page_content="Senior Python developer with 7 years of experience building "
                            "web applications using Django and FastAPI.",
                metadata={
                    "resume_id": "resume_001",
                    "category": "Software Engineering",
                    "chunk_index": 0,
                    "experience_level": "senior",
                    "role_category": "backend"
                }
            ),
            Document(
                page_content="Strong expertise in cloud platforms including AWS, GCP, and Azure. "
                            "Experienced with containerization technologies Docker and Kubernetes.",
                metadata={
                    "resume_id": "resume_001",
                    "category": "Software Engineering",
                    "chunk_index": 1,
                    "experience_level": "senior",
                    "role_category": "backend"
                }
            ),
            Document(
                page_content="Frontend developer with 4 years of experience. Proficient in React, "
                            "Vue.js, and modern JavaScript. Strong CSS and UI/UX knowledge.",
                metadata={
                    "resume_id": "resume_002",
                    "category": "Web Development",
                    "chunk_index": 0,
                    "experience_level": "mid",
                    "role_category": "frontend"
                }
            ),
            Document(
                page_content="Data scientist with 5 years of experience in machine learning and "
                            "deep learning. Expertise in TensorFlow, PyTorch, and scikit-learn.",
                metadata={
                    "resume_id": "resume_003",
                    "category": "Data Science",
                    "chunk_index": 0,
                    "experience_level": "senior",
                    "role_category": "data_science"
                }
            ),
        ]

        print(f"\nIngesting {len(documents)} documents...")
        results = ingest_resumes(documents, vector_store)

        print(f"\nIngestion Results:")
        print(f"  Ingested: {results['ingested']}")
        print(f"  Duplicates skipped: {results['duplicates']}")
        print(f"  Total in store: {results['total_in_store']}")
        if results.get('errors'):
            print(f"  Errors: {results['errors']}")

    except Exception as e:
        print(f"Error: {e}")


def example_semantic_search():
    """Example 3: Perform semantic search."""
    print("\n" + "=" * 70)
    print("Example 3: Semantic Search")
    print("=" * 70)

    try:
        vector_store = init_vector_store()

        # Example search queries
        queries = [
            "Python backend developer",
            "React frontend skills",
            "machine learning experience",
            "cloud platform expertise",
        ]

        for query in queries:
            print(f"\nQuery: '{query}'")
            results = semantic_search(query, top_k=2, vector_store=vector_store)

            if results:
                for i, (doc, score) in enumerate(results, 1):
                    print(f"  Result {i} (score: {score:.4f}):")
                    print(f"    Resume: {doc.metadata.get('resume_id')}")
                    print(f"    Role: {doc.metadata.get('role_category')}")
                    print(f"    Content: {doc.page_content[:80]}...")
            else:
                print(f"  No results found")

    except Exception as e:
        print(f"Error: {e}")


def example_search_with_filters():
    """Example 4: Semantic search with metadata filters."""
    print("\n" + "=" * 70)
    print("Example 4: Semantic Search with Filters")
    print("=" * 70)

    try:
        vector_store = init_vector_store()

        # Search for senior-level backend developers
        filters = {
            "experience_level": "senior",
            "role_category": "backend"
        }

        print(f"\nSearching for: 'Python developer' with filters {filters}")
        results = semantic_search(
            "Python developer",
            top_k=5,
            filters=filters,
            vector_store=vector_store
        )

        print(f"Found {len(results)} matching results:")
        for i, (doc, score) in enumerate(results, 1):
            print(f"  {i}. {doc.metadata.get('resume_id')} - {doc.metadata.get('role_category')}")
            print(f"     Score: {score:.4f}, Level: {doc.metadata.get('experience_level')}")

        # Search for mid-level or senior frontend developers
        filters_list = {
            "experience_level": ["mid", "senior"],
            "role_category": "frontend"
        }

        print(f"\nSearching for: 'React developer' with experience level in ['mid', 'senior']")
        results = semantic_search(
            "React developer",
            top_k=5,
            filters=filters_list,
            vector_store=vector_store
        )

        print(f"Found {len(results)} matching results:")
        for i, (doc, score) in enumerate(results, 1):
            print(f"  {i}. {doc.metadata.get('resume_id')} - {doc.metadata.get('role_category')}")

    except Exception as e:
        print(f"Error: {e}")


def example_collection_stats():
    """Example 5: Get collection statistics."""
    print("\n" + "=" * 70)
    print("Example 5: Collection Statistics")
    print("=" * 70)

    try:
        vector_store = init_vector_store()

        stats = get_collection_stats(vector_store)

        print(f"\nCollection Statistics:")
        print(f"  Total documents: {stats.get('total_documents', 0)}")
        print(f"  Total resumes: {stats.get('total_resumes', 0)}")
        print(f"  Avg chunks per resume: {stats.get('avg_chunks_per_resume', 0):.2f}")

        if stats.get('categories'):
            print(f"\n  Categories:")
            for category, count in stats['categories'].items():
                print(f"    {category}: {count}")

        if stats.get('role_categories'):
            print(f"\n  Role Categories:")
            for role, count in stats['role_categories'].items():
                print(f"    {role}: {count}")

        if stats.get('experience_levels'):
            print(f"\n  Experience Levels:")
            for level, count in stats['experience_levels'].items():
                print(f"    {level}: {count}")

        if stats.get('resumes_by_id'):
            print(f"\n  Resumes:")
            for resume_id, chunk_count in stats['resumes_by_id'].items():
                print(f"    {resume_id}: {chunk_count} chunks")

    except Exception as e:
        print(f"Error: {e}")


def example_delete_resume():
    """Example 6: Delete a resume from the vector store."""
    print("\n" + "=" * 70)
    print("Example 6: Delete Resume")
    print("=" * 70)

    try:
        vector_store = init_vector_store()

        # Show stats before deletion
        stats_before = get_collection_stats(vector_store)
        print(f"\nBefore deletion: {stats_before.get('total_documents', 0)} documents")

        # Delete a specific resume
        resume_id = "resume_001"
        print(f"\nDeleting {resume_id}...")
        deleted_count = vector_store.delete_resume(resume_id)
        print(f"Deleted {deleted_count} documents")

        # Show stats after deletion
        stats_after = get_collection_stats(vector_store)
        print(f"After deletion: {stats_after.get('total_documents', 0)} documents")

    except Exception as e:
        print(f"Error: {e}")


def example_class_usage():
    """Example 7: Using ResumeVectorStore class directly."""
    print("\n" + "=" * 70)
    print("Example 7: Direct Class Usage")
    print("=" * 70)

    try:
        # Create a separate instance (not using singleton)
        vector_store = ResumeVectorStore(
            collection_name="resumes_test",
            embedding_model="text-embedding-3-small"
        )

        # Create a test document
        doc = Document(
            page_content="Test document with AI and machine learning skills",
            metadata={
                "resume_id": "test_001",
                "category": "Test",
                "chunk_index": 0,
                "experience_level": "mid",
                "role_category": "data_science"
            }
        )

        # Ingest
        print(f"\nIngesting test document...")
        results = vector_store.ingest_documents([doc])
        print(f"Ingestion results: {results}")

        # Search
        print(f"\nSearching for 'machine learning'...")
        search_results = vector_store.semantic_search("machine learning", top_k=1)
        if search_results:
            doc, score = search_results[0]
            print(f"Found: {doc.metadata.get('resume_id')} with score {score:.4f}")

        # Stats
        stats = vector_store.get_collection_stats()
        print(f"Collection has {stats.get('total_documents', 0)} documents")

    except Exception as e:
        print(f"Error: {e}")


def example_range_filters():
    """Example 8: Search with range filters."""
    print("\n" + "=" * 70)
    print("Example 8: Range Filters")
    print("=" * 70)

    try:
        vector_store = init_vector_store()

        # Filter for developers with 5-10 years of experience
        # (Assuming this metadata is available in chunks)
        filters = {
            "chunk_words": {"min": 10, "max": 100}  # Filter by chunk size
        }

        print(f"\nSearching with range filter (10-100 words per chunk)...")
        results = semantic_search(
            "Python developer",
            top_k=3,
            filters=filters,
            vector_store=vector_store
        )

        print(f"Found {len(results)} results within the word range")
        for i, (doc, score) in enumerate(results, 1):
            words = len(doc.page_content.split())
            print(f"  {i}. {words} words, Score: {score:.4f}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("Vector Store Examples")
    print("=" * 70)
    print("\nNote: These examples require OPENAI_API_KEY to be set in .env file")
    print("Running these examples will make API calls and may incur costs.\n")

    try:
        # Run examples
        example_init_vector_store()
        example_ingest_documents()
        example_collection_stats()
        example_semantic_search()
        example_search_with_filters()

        # Uncomment to run additional examples:
        # example_delete_resume()
        # example_class_usage()
        # example_range_filters()

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\nError: {e}")
        print("\nMake sure:")
        print("  1. OPENAI_API_KEY is set in your .env file")
        print("  2. ChromaDB is properly installed")
        print("  3. You have valid OpenAI API credits")

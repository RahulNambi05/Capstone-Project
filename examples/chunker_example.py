"""
Example usage of the document chunker module.
"""
import logging
from src.ingestion.chunker import ResumeChunker, chunk_resume_text, chunk_resumes_batch
from src.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


# Example 1: Chunk a single resume
def example_chunk_single_resume():
    """Example of chunking a single resume."""
    print("\n" + "=" * 70)
    print("Example 1: Chunk Single Resume")
    print("=" * 70)

    resume_text = """
    JOHN DOE
    Senior Software Engineer | Python | Django | FastAPI | AWS

    PROFESSIONAL SUMMARY
    Experienced software engineer with 7 years of professional experience building
    scalable web applications and microservices. Strong expertise in Python backend
    development, cloud infrastructure, and team leadership.

    TECHNICAL SKILLS
    Programming Languages: Python, Java, JavaScript, TypeScript
    Backend Frameworks: Django, FastAPI, Spring Boot, Express.js
    Databases: PostgreSQL, MongoDB, Redis, Elasticsearch
    Cloud Platforms: AWS (EC2, S3, Lambda, SQS), Google Cloud
    DevOps: Docker, Kubernetes, Jenkins, GitHub Actions, Terraform
    Other Tools: Git, Linux, Agile/Scrum, Jira, Confluence

    PROFESSIONAL EXPERIENCE

    Senior Backend Engineer | TechCorp Inc. | Jan 2021 - Present
    - Led development of microservices architecture using FastAPI and Docker
    - Implemented CI/CD pipelines using GitHub Actions and Kubernetes
    - Optimized database queries reducing API response time by 40%
    - Mentored team of 3 junior developers

    Full Stack Developer | StartupXYZ | Jun 2018 - Dec 2020
    - Developed full-stack web applications using Django and React
    - Implemented authentication and authorization systems
    - Deployed applications on AWS using EC2 and RDS
    - Improved code quality through comprehensive unit testing

    EDUCATION
    Bachelor of Science in Computer Science
    University Name | Graduated: 2018

    CERTIFICATIONS
    AWS Certified Solutions Architect - Associate
    Python Professional Certification
    """

    # Using convenience function
    documents = chunk_resume_text(
        resume_text=resume_text,
        resume_id="resume_001",
        category="Senior Engineer"
    )

    print(f"\nCreated {len(documents)} chunks")
    for i, doc in enumerate(documents):
        print(f"\nChunk {i}:")
        print(f"  Metadata: {doc.metadata}")
        print(f"  Length: {len(doc.page_content)} chars, {len(doc.page_content.split())} words")
        print(f"  Content preview: {doc.page_content[:100]}...")


# Example 2: Using ResumeChunker class directly
def example_chunker_class():
    """Example of using the ResumeChunker class directly."""
    print("\n" + "=" * 70)
    print("Example 2: Using ResumeChunker Class")
    print("=" * 70)

    # Initialize chunker with custom settings
    chunker = ResumeChunker(
        chunk_size=500,
        chunk_overlap=50
    )

    sample_resume = """
    JANE SMITH
    Senior Data Scientist | Machine Learning | Python | TensorFlow

    SUMMARY
    Passionate data scientist with 6 years building machine learning models and
    data pipelines. Expert in deep learning, NLP, and computer vision.

    SKILLS
    Machine Learning: TensorFlow, PyTorch, scikit-learn, XGBoost
    Languages: Python, SQL, R
    Data Processing: Pandas, NumPy, Spark
    Cloud: AWS, Google Cloud Platform
    NLP: NLTK, spaCy, Transformers, BERT
    Computer Vision: OpenCV, YOLOv5

    EXPERIENCE
    Senior ML Engineer | DataCorp | 2021 - Present
    Built end-to-end ML pipelines using TensorFlow and Spark
    Deployed deep learning models to production on AWS Lambda
    Reduced inference time by 60% through model optimization

    DATA SCIENTIST | Analytics Inc | 2018 - 2021
    Developed NLP models for sentiment analysis and text classification
    Created computer vision pipeline for image recognition
    """

    # Chunk with additional metadata
    documents = chunker.chunk_resume(
        resume_text=sample_resume,
        resume_id="resume_002",
        category="Data Science",
        metadata={"experience_years": 6, "location": "San Francisco"}
    )

    print(f"\nTotal chunks created: {len(documents)}")
    print(f"Chunk size: {chunker.chunk_size}, Overlap: {chunker.chunk_overlap}")

    # Print first chunk with full metadata
    if documents:
        first_doc = documents[0]
        print(f"\nFirst chunk metadata:")
        for key, value in first_doc.metadata.items():
            print(f"  {key}: {value}")


# Example 3: Batch processing multiple resumes
def example_batch_chunking():
    """Example of chunking multiple resumes in batch."""
    print("\n" + "=" * 70)
    print("Example 3: Batch Chunking Multiple Resumes")
    print("=" * 70)

    resumes = [
        {
            "id": "resume_003",
            "resume_text": """
            BACKEND ENGINEER
            Skills: Python Python Python Django FastAPI FastAPI FastAPI
            PostgreSQL PostgreSQL PostgreSQL Docker Docker Docker
            AWS AWS AWS Kubernetes Kubernetes Kubernetes
            JSON JSON REST REST API API Microservices Microservices
            Git Git GitHub GitHub Linux Linux Jenkins Jenkins CI/CD CI/CD
            Agile Agile Scrum Scrum JIRA JIRA 5 years backend development
            """ * 3,  # Repeat to ensure enough content
            "category": "Backend",
            "location": "New York"
        },
        {
            "id": "resume_004",
            "resume_text": """
            FRONTEND ENGINEER
            JavaScript JavaScript JavaScript TypeScript TypeScript React React
            Vue Angular CSS CSS HTML HTML Webpack Webpack npm npm yarn yarn
            Redux Redux Context Context State management Performance optimization
            Web accessibility responsive design UX principles UI design patterns
            3 years frontend development with modern frameworks
            """ * 3,
            "category": "Frontend",
            "location": "Boston"
        },
        {
            "id": "resume_005",
            "resume_text": """
            DEVOPS ENGINEER
            Docker Docker Docker Kubernetes Kubernetes CI/CD CI/CD Jenkins Jenkins
            Terraform Terraform IaC Infrastructure as Code AWS AWS Azure Azure
            Deployment automation monitoring logging Prometheus Grafana ELK stack
            Security compliance networking load balancing auto-scaling 4 years
            """ * 3,
            "category": "DevOps",
            "location": "Seattle"
        }
    ]

    # Batch chunk all resumes
    all_documents = chunk_resumes_batch(resumes)

    print(f"\nTotal resumes: {len(resumes)}")
    print(f"Total chunks created: {len(all_documents)}")

    # Group by resume
    by_resume = {}
    for doc in all_documents:
        resume_id = doc.metadata["resume_id"]
        if resume_id not in by_resume:
            by_resume[resume_id] = []
        by_resume[resume_id].append(doc)

    print("\nChunks per resume:")
    for resume_id, docs in by_resume.items():
        total_chars = sum(len(doc.page_content) for doc in docs)
        print(f"  {resume_id}: {len(docs)} chunks, {total_chars} total characters")


# Example 4: Get chunking statistics
def example_chunking_stats():
    """Example of calculating chunking statistics."""
    print("\n" + "=" * 70)
    print("Example 4: Chunking Statistics")
    print("=" * 70)

    chunker = ResumeChunker()

    sample_resumes = [
        {
            "id": "resume_006",
            "resume_text": "Python Django FastAPI Docker AWS " * 50,  # ~250 words
            "category": "Backend"
        },
        {
            "id": "resume_007",
            "resume_text": "React JavaScript TypeScript CSS HTML " * 50,  # ~250 words
            "category": "Frontend"
        }
    ]

    documents = chunker.chunk_resumes_batch(sample_resumes)
    stats = chunker.get_chunking_stats(documents)

    print(f"\nChunking Statistics:")
    print(f"  Total chunks: {stats['total_chunks']}")
    print(f"  Total characters: {stats['total_characters']}")
    print(f"  Total words: {stats['total_words']}")
    print(f"  Average chunk size: {stats['avg_chunk_size']:.2f} characters")
    print(f"  Average chunk words: {stats['avg_chunk_words']:.2f} words")
    print(f"  Unique resumes: {stats['unique_resumes']}")

    print(f"\nPer-resume statistics:")
    for resume_id, resume_stats in stats['resumes'].items():
        print(f"  {resume_id}:")
        print(f"    Chunks: {resume_stats['chunks']}")
        print(f"    Category: {resume_stats['category']}")
        print(f"    Total size: {resume_stats['total_size']} characters")


# Example 5: Display current configuration
def example_show_config():
    """Display current chunking configuration."""
    print("\n" + "=" * 70)
    print("Example 5: Current Configuration")
    print("=" * 70)

    print(f"\nChunking Configuration from settings:")
    print(f"  CHUNK_SIZE: {settings.CHUNK_SIZE}")
    print(f"  CHUNK_OVERLAP: {settings.CHUNK_OVERLAP}")
    print(f"  TOP_K: {settings.TOP_K}")
    print(f"  OPENAI_LLM_MODEL: {settings.OPENAI_LLM_MODEL}")
    print(f"  OPENAI_EMBEDDING_MODEL: {settings.OPENAI_EMBEDDING_MODEL}")
    print(f"  CHROMA_PERSIST_DIR: {settings.CHROMA_PERSIST_DIR}")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("Document Chunker Examples")
    print("=" * 70)

    # Run all examples
    example_show_config()
    example_chunk_single_resume()
    example_chunker_class()
    example_batch_chunking()
    example_chunking_stats()

    print("\n" + "=" * 70)
    print("All examples completed!")
    print("=" * 70)

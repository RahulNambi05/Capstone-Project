"""
Example usage of the candidate retriever module.
Demonstrates finding matching resumes for parsed job descriptions.
"""
import logging
from src.retrieval.job_parser import parse_job_description, ParsedJobDescription
from src.retrieval.candidate_retriever import retrieve_candidates, CandidateRetriever

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


# Sample job descriptions
BACKEND_JOB = """
Senior Backend Engineer - Python

Company: TechCorp
Location: San Francisco, CA

We're looking for an experienced Senior Backend Engineer to join our platform team.

Requirements:
- 7+ years of professional software development experience
- Expert-level proficiency in Python
- Strong experience with Django or FastAPI web frameworks
- Expertise in PostgreSQL and relational databases
- Experience with Docker and Kubernetes
- Strong understanding of REST APIs and microservices architecture
- AWS cloud platform experience
- Excellent problem-solving and communication skills

Preferred Qualifications:
- Experience with GraphQL
- Kubernetes certification
- Experience with event-driven architectures (Kafka, RabbitMQ)
- Contributions to open-source projects
"""

FRONTEND_JOB = """
Frontend Developer - React

Company: WebDesign Inc
Location: Remote

We're seeking a talented Frontend Developer with strong React skills.

Required:
- 3+ years of front-end development experience
- Proficiency in React (16.8+)
- Strong JavaScript/TypeScript knowledge
- CSS and responsive design expertise
- HTML5 fundamentals
- Experience with modern build tools (Webpack, Vite)
- Git version control

Nice to Have:
- Next.js experience
- Testing frameworks (Jest, React Testing Library)
- State management (Redux, Zustand)
- CSS-in-JS libraries
"""

DATA_SCIENCE_JOB = """
Data Scientist - Machine Learning

Company: AI Innovations
Location: New York, NY

Join our AI team as a Data Scientist to develop ML solutions.

Required Skills:
- Master's degree in Computer Science, Statistics, or related field
- 4+ years of experience in machine learning
- Python expertise (NumPy, Pandas, Scikit-learn)
- Deep learning frameworks: TensorFlow or PyTorch
- SQL and database experience
- Statistical analysis and hypothesis testing
- Cloud platforms (AWS preferred)

Preferred Skills:
- NLP experience (NLTK, spaCy, Transformers)
- Computer vision (OpenCV, YOLOv5)
- Apache Spark for big data processing
- Model deployment and MLOps (MLflow, Airflow)
"""


def example_single_job_retrieval():
    """Example 1: Retrieve candidates for a single job."""
    print("\n" + "=" * 70)
    print("Example 1: Single Job Candidate Retrieval")
    print("=" * 70)

    print("\nParsing backend job description...")
    try:
        # Parse the job description
        parsed_jd = parse_job_description(BACKEND_JOB)

        print(f"\nJob Summary: {parsed_jd.job_summary}")
        print(f"Level: {parsed_jd.experience_level}")
        print(f"Role: {parsed_jd.role_category}")
        print(f"Required Skills: {', '.join(parsed_jd.required_skills[:5])}...")

        # Retrieve candidates
        print(f"\nRetrieving matching candidates...")
        candidates = retrieve_candidates(parsed_jd, top_k=5)

        print(f"\nFound {len(candidates)} matching candidates:\n")

        for i, candidate in enumerate(candidates, 1):
            print(f"{i}. Resume {candidate['resume_id']}")
            print(f"   Score: {candidate['score']:.4f}")
            print(f"   Category: {candidate['category']}")
            print(f"   Experience Level: {candidate['metadata']['experience_level']}")
            print(f"   Matched Skills: {', '.join(candidate['matched_skills'][:3])}...")
            print()

    except Exception as e:
        print(f"Note: This example requires vector store to be populated.")
        print(f"Run the ingestion pipeline first: python -m examples.pipeline_example")
        logger.error(f"Error: {e}")


def example_multiple_jobs():
    """Example 2: Retrieve candidates for multiple jobs."""
    print("\n" + "=" * 70)
    print("Example 2: Multiple Job Openings")
    print("=" * 70)

    jobs = [
        {"description": BACKEND_JOB, "name": "Backend Engineer"},
        {"description": FRONTEND_JOB, "name": "Frontend Developer"},
        {"description": DATA_SCIENCE_JOB, "name": "Data Scientist"},
    ]

    print(f"\nParsing {len(jobs)} job descriptions...\n")

    try:
        retriever = CandidateRetriever()
        parsed_jobs = []

        for job in jobs:
            parsed = parse_job_description(job["description"])
            parsed_jobs.append(parsed)
            print(f"✓ {job['name']}: {parsed.experience_level} {parsed.role_category}")

        # Retrieve candidates for all jobs
        print(f"\nRetrieving candidates for all jobs...")
        all_results = retriever.retrieve_for_multiple_jobs(parsed_jobs, top_k_per_job=3)

        # Display results
        for job_key, job_results in all_results.items():
            print(f"\n{job_results['role_category'].upper()}")
            print(f"  Level: {job_results['experience_level']}")
            print(f"  Candidates: {job_results['candidate_count']}")

            for candidate in job_results['candidates'][:2]:
                print(f"    • {candidate['resume_id']}: {candidate['score']:.4f}")

    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"Note: This example requires the ingestion pipeline to be run first.")


def example_skill_matching():
    """Example 3: Detailed skill matching analysis."""
    print("\n" + "=" * 70)
    print("Example 3: Skill Matching Analysis")
    print("=" * 70)

    print("\nAnalyzing skill matches for backend position...\n")

    try:
        # Parse job
        parsed_jd = parse_job_description(BACKEND_JOB)

        print(f"Job: {parsed_jd.job_summary}")
        print(f"\nRequired Skills ({len(parsed_jd.required_skills)}):")
        for skill in parsed_jd.required_skills[:10]:
            print(f"  • {skill}")

        # Retrieve candidates
        candidates = retrieve_candidates(parsed_jd, top_k=5)

        if candidates:
            print(f"\nTop Candidate Analysis:\n")
            top_candidate = candidates[0]

            print(f"Candidate: {top_candidate['resume_id']}")
            print(f"Match Score: {top_candidate['score']:.4f}")
            print(f"Category: {top_candidate['metadata']['role_category']}")
            print(f"Experience: {top_candidate['metadata']['experience_years']} years")
            print(f"\nMatched Required Skills:")
            for skill in top_candidate['matched_skills']:
                print(f"  ✓ {skill}")

            # Calculate skill coverage
            total_required = len(parsed_jd.required_skills)
            matched_count = len(top_candidate['matched_skills'])
            coverage = (matched_count / total_required * 100) if total_required > 0 else 0
            print(f"\nSkill Coverage: {matched_count}/{total_required} ({coverage:.1f}%)")
        else:
            print("\nNo candidates found in vector store.")

    except Exception as e:
        logger.error(f"Error: {e}")


def example_experience_filtering():
    """Example 4: Filter candidates by experience level."""
    print("\n" + "=" * 70)
    print("Example 4: Experience Level Filtering")
    print("=" * 70)

    print("\nComparing senior vs mid-level candidates...\n")

    try:
        # Parse job
        parsed_jd = parse_job_description(BACKEND_JOB)

        # Retrieve without filters
        print(f"Retrieving candidates WITHOUT experience filter...\n")
        candidates_unfiltered = retrieve_candidates(
            parsed_jd,
            top_k=10,
            apply_filters=False
        )

        # Count by level
        level_counts = {}
        for candidate in candidates_unfiltered:
            level = candidate['metadata']['experience_level']
            level_counts[level] = level_counts.get(level, 0) + 1

        print(f"Experience Level Distribution:")
        for level, count in level_counts.items():
            print(f"  {level}: {count} candidates")

        # Show top candidates by level
        print(f"\nTop Candidates by Level:")
        for level in ['senior', 'mid', 'entry']:
            level_candidates = [c for c in candidates_unfiltered
                              if c['metadata']['experience_level'] == level]
            if level_candidates:
                top = level_candidates[0]
                print(f"  {level}: {top['resume_id']} (score: {top['score']:.4f})")

    except Exception as e:
        logger.error(f"Error: {e}")


def example_role_category_matching():
    """Example 5: Match candidates by role category."""
    print("\n" + "=" * 70)
    print("Example 5: Role Category Matching")
    print("=" * 70)

    print("\nAnalyzing role category matches...\n")

    try:
        jobs = [
            {"desc": BACKEND_JOB, "name": "Backend"},
            {"desc": FRONTEND_JOB, "name": "Frontend"},
            {"desc": DATA_SCIENCE_JOB, "name": "Data Science"},
        ]

        for job in jobs:
            parsed_jd = parse_job_description(job["desc"])
            candidates = retrieve_candidates(parsed_jd, top_k=3)

            print(f"{job['name'].upper()} ({parsed_jd.role_category})")

            if candidates:
                for candidate in candidates[:2]:
                    match_role = candidate['metadata']['role_category']
                    score = candidate['score']
                    print(f"  • {candidate['resume_id']}: {match_role} ({score:.4f})")
            else:
                print(f"  • No candidates found")
            print()

    except Exception as e:
        logger.error(f"Error: {e}")


def example_deduplication():
    """Example 6: Understand deduplication process."""
    print("\n" + "=" * 70)
    print("Example 6: Deduplication Explanation")
    print("=" * 70)

    print("\nDeduplication Process:\n")

    print("The retriever works with chunks (segments) of resume text.")
    print("Multiple chunks may come from the same resume.\n")

    print("Without Deduplication:")
    print("  • Returns best-matching chunks")
    print("  • May include multiple chunks from same resume")
    print("  • Useful for detailed analysis\n")

    print("With Deduplication (Default):")
    print("  • Returns best chunk per resume")
    print("  • Shows one candidate per resume")
    print("  • Better for candidate ranking\n")

    print("Example:")
    print("  Before: Resume_A (chunk 0, score 0.92)")
    print("          Resume_A (chunk 1, score 0.87)")
    print("          Resume_B (chunk 0, score 0.85)")
    print("                    ↓")
    print("  After:  Resume_A (chunk 0, score 0.92)  ← Highest score kept")
    print("          Resume_B (chunk 0, score 0.85)")

    try:
        parsed_jd = parse_job_description(BACKEND_JOB)

        print("\nRetrieving WITH deduplication:")
        candidates_dedup = retrieve_candidates(parsed_jd, top_k=5, deduplicate=True)
        print(f"  Result: {len(candidates_dedup)} unique resumes")

        print("\nRetrieving WITHOUT deduplication:")
        candidates_no_dedup = retrieve_candidates(parsed_jd, top_k=5, deduplicate=False)
        print(f"  Result: {len(candidates_no_dedup)} chunks")

    except Exception as e:
        logger.error(f"Error: {e}")


def example_ranking_analysis():
    """Example 7: Analyze ranking and scores."""
    print("\n" + "=" * 70)
    print("Example 7: Ranking and Score Analysis")
    print("=" * 70)

    print("\nRanking candidates by match score...\n")

    try:
        parsed_jd = parse_job_description(BACKEND_JOB)
        candidates = retrieve_candidates(parsed_jd, top_k=10)

        if candidates:
            print(f"{'Rank':<6} {'Resume ID':<15} {'Score':<8} {'Level':<10} {'Matched':<8}")
            print(f"{'-' * 60}")

            for i, candidate in enumerate(candidates, 1):
                resume_id = candidate['resume_id'][:12]
                score = candidate['score']
                level = candidate['metadata']['experience_level']
                matched = len(candidate['matched_skills'])

                print(f"{i:<6} {resume_id:<15} {score:<8.4f} {level:<10} {matched:<8}")
        else:
            print("No candidates found in vector store.")
            print("Run the ingestion pipeline to populate the vector store.")

    except Exception as e:
        logger.error(f"Error: {e}")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("Candidate Retriever Examples")
    print("=" * 70)
    print("\nNote: These examples require the vector store to be populated.")
    print("Run the ingestion pipeline first:\n")
    print("  python -m examples.pipeline_example\n")

    try:
        # Run examples
        example_deduplication()
        example_skill_matching()
        example_experience_filtering()
        example_role_category_matching()

        # Uncomment to run additional examples (require populated vector store):
        # example_single_job_retrieval()
        # example_multiple_jobs()
        # example_ranking_analysis()

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\nError: {e}")
        print("\nNote: Some examples require the vector store to be populated.")
        print("Run the ingestion pipeline first to load resume data.")

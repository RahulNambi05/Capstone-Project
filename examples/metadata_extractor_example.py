"""
Example usage of the metadata extractor module.
Demonstrates extracting structured metadata from resumes using LLM.
"""
import logging
from src.ingestion.metadata_extractor import (
    MetadataExtractor,
    extract_metadata,
    extract_batch_metadata
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


# Sample resumes for testing
SAMPLE_RESUME_1 = """
JOHN DOE
Senior Backend Engineer | Python | Django | FastAPI | AWS

PROFESSIONAL SUMMARY
Experienced software engineer with 7 years of professional experience building
scalable web applications and microservices. Strong expertise in Python backend
development, cloud infrastructure on AWS, and distributed systems design.

TECHNICAL SKILLS
Programming Languages: Python, Java, JavaScript
Backend Frameworks: Django, FastAPI, Spring Boot, Express.js
Databases: PostgreSQL, MongoDB, Redis, Elasticsearch
Cloud Platforms: AWS (EC2, S3, Lambda, RDS)
DevOps: Docker, Kubernetes, Jenkins, GitHub Actions
Architecture: Microservices, REST APIs, Event-driven design
Other: Git, Linux, CI/CD, Agile/Scrum

PROFESSIONAL EXPERIENCE

Senior Backend Engineer | TechCorp Inc. | Jan 2021 - Present
- Led development of microservices architecture using FastAPI and Docker
- Designed and implemented distributed systems handling 1M+ requests/day
- Mentored team of 5 junior engineers
- Achieved 99.9% uptime SLA for production services

Full Stack Developer | StartupXYZ | Jun 2018 - Dec 2020
- Developed web applications using Django and React
- Implemented PostgreSQL database schemas and optimizations
- Deployed applications on AWS using EC2, RDS, and S3

Junior Developer | WebAgency | Jun 2017 - May 2018
- Built client websites using Python and JavaScript

EDUCATION
B.S. Computer Science, State University, 2017

CERTIFICATIONS
AWS Certified Solutions Architect - Associate (2022)
Python Professional Certification (2021)
"""

SAMPLE_RESUME_2 = """
JANE SMITH
Data Scientist | Machine Learning | Python | TensorFlow

SUMMARY
Passionate data scientist with 4 years building machine learning models and
data pipelines. Expert in deep learning, NLP, and computer vision applications.
Proven track record of delivering ML solutions for real-world problems.

TECHNICAL SKILLS
Machine Learning: TensorFlow, PyTorch, scikit-learn, XGBoost, Keras
Languages: Python, SQL, R
Data Processing: Pandas, NumPy, Spark, Dask
NLP: NLTK, spaCy, Transformers, BERT, GPT
Computer Vision: OpenCV, YOLOv5, Detectron2
Cloud: AWS SageMaker, Google Cloud ML
Tools: Jupyter, MLflow, Weights & Biases, Git

EXPERIENCE
Senior Data Scientist | DataCorp | 2022 - Present
- Built end-to-end ML pipelines using TensorFlow and Spark
- Deployed deep learning models to production on AWS Lambda
- Lead team of 2 data scientists on NLP projects

Data Scientist | Analytics Inc | 2020 - 2022
- Developed computer vision models for object detection achieving 95% accuracy
- Created recommendation engine using collaborative filtering
- Built real-time NLP sentiment analysis system

Junior Data Scientist | Analytics Inc | 2020 - 2021
- Analyzed datasets and created visualizations
- Assisted in model development and evaluation

EDUCATION
M.S. Data Science, Tech University, 2020
B.S. Physics, Tech University, 2018

CERTIFICATIONS
Google Cloud Professional Data Engineer (2023)
Deep Learning Specialization (2021)
"""

SAMPLE_RESUME_3 = """
ALEX JOHNSON
Full Stack Developer | React | Node.js | Full Stack Development

SUMMARY
Detail-oriented developer with 3 years building modern web applications.
Expertise in React frontend development and Node.js backend systems.

SKILLS
Frontend: React, Vue, JavaScript, TypeScript, CSS, HTML, Webpack
Backend: Node.js, Express, REST APIs, GraphQL
Databases: MongoDB, Firebase, PostgreSQL
Tools & Platforms: Git, Docker, AWS, Heroku, Netlify
Methodologies: Agile, TDD, Git workflows

WORK EXPERIENCE
Full Stack Developer | WebSolutions | 2022 - Present
- Developed responsive React web applications
- Built Express.js REST APIs and microservices
- Implemented real-time features using WebSockets

Junior Frontend Developer | DesignStudio | 2021 - 2022
- Created interactive React components
- Improved performance reducing load time by 40%

EDUCATION
B.S. Computer Science, State College, 2021

CERTIFICATIONS
React Advanced Patterns (2022)
"""

SAMPLE_RESUME_4 = """
SARAH WILLIAMS
DevOps Engineer | Kubernetes | CI/CD | Infrastructure As Code

SUMMARY
Infrastructure enthusiast with 6 years designing and maintaining cloud platforms.
Expertise in Kubernetes, infrastructure automation, and DevOps best practices.

TECHNICAL SKILLS
Container Orchestration: Kubernetes, Docker Compose
CI/CD: Jenkins, GitLab CI, GitHub Actions, CircleCI
Infrastructure as Code: Terraform, Ansible, CloudFormation
Cloud Platforms: AWS, Azure, Google Cloud
Monitoring: Prometheus, Grafana, ELK Stack, Datadog
Languages: Python, Bash, Go
Practices: GitOps, Infrastructure as Code, Security

PROFESSIONAL EXPERIENCE
Senior DevOps Engineer | CloudSys | 2020 - Present
- Managed Kubernetes clusters supporting 100+ microservices
- Implemented CI/CD pipelines reducing deployment time by 70%
- Leads infrastructure automation initiatives

DevOps Engineer | HostingCo | 2018 - 2020
- Set up Docker and Kubernetes environments
- Implemented monitoring and logging infrastructure

Junior DevOps Engineer | HostingCo | 2017 - 2018
- Assisted with infrastructure management
- Maintained production servers

EDUCATION
B.S. Information Systems, University, 2017

CERTIFICATIONS
Certified Kubernetes Administrator (CKA) (2021)
AWS Solutions Architect - Professional (2020)
"""


def example_single_extraction():
    """Example 1: Extract metadata from a single resume."""
    print("\n" + "=" * 70)
    print("Example 1: Single Resume Metadata Extraction")
    print("=" * 70)

    print("\nExtracting metadata from Senior Backend Engineer resume...")

    try:
        metadata = extract_metadata(SAMPLE_RESUME_1)

        print("\nExtracted Metadata:")
        print(f"  Experience Years: {metadata['experience_years']}")
        print(f"  Experience Level: {metadata['experience_level']}")
        print(f"  Education: {metadata['education']}")
        print(f"  Role Category: {metadata['role_category']}")
        print(f"  Top Skills ({len(metadata['top_skills'])} total):")
        for skill in metadata['top_skills']:
            print(f"    - {skill}")

    except Exception as e:
        print(f"Error: {e}")


def example_multiple_extractions():
    """Example 2: Extract metadata from multiple resumes."""
    print("\n" + "=" * 70)
    print("Example 2: Multiple Resume Metadata Extraction")
    print("=" * 70)

    resumes = [
        {"id": "resume_1", "resume_text": SAMPLE_RESUME_1},
        {"id": "resume_2", "resume_text": SAMPLE_RESUME_2},
        {"id": "resume_3", "resume_text": SAMPLE_RESUME_3},
        {"id": "resume_4", "resume_text": SAMPLE_RESUME_4},
    ]

    print(f"\nExtracting metadata from {len(resumes)} resumes...")

    try:
        metadata_list = extract_batch_metadata(resumes)

        print(f"\nSuccessfully extracted metadata from {len(metadata_list)} resumes:\n")

        for metadata in metadata_list:
            resume_id = metadata.get("id", "unknown")
            print(f"Resume: {resume_id}")
            print(f"  Experience: {metadata['experience_years']} years ({metadata['experience_level']})")
            print(f"  Education: {metadata['education']}")
            print(f"  Role: {metadata['role_category']}")
            print(f"  Skills: {', '.join(metadata['top_skills'][:5])}...")
            print()

    except Exception as e:
        print(f"Error: {e}")


def example_class_usage():
    """Example 3: Using MetadataExtractor class directly."""
    print("\n" + "=" * 70)
    print("Example 3: Using MetadataExtractor Class")
    print("=" * 70)

    # Create an extractor instance
    extractor = MetadataExtractor(temperature=0.1)

    print("\nExtracting metadata with custom configuration...")

    try:
        metadata = extractor.extract_metadata(SAMPLE_RESUME_2)

        print("\nData Scientist Resume Metadata:")
        print(f"  Experience: {metadata['experience_years']} years")
        print(f"  Level: {metadata['experience_level']}")
        print(f"  Education: {metadata['education']}")
        print(f"  Primary Role: {metadata['role_category']}")
        print(f"\n  Technical Skills:")
        for skill in metadata['top_skills']:
            print(f"    ✓ {skill}")

    except Exception as e:
        print(f"Error: {e}")


def example_compare_categories():
    """Example 4: Compare role categories across multiple resumes."""
    print("\n" + "=" * 70)
    print("Example 4: Compare Role Categories")
    print("=" * 70)

    resumes = [
        {"id": "backend", "resume_text": SAMPLE_RESUME_1},
        {"id": "data_science", "resume_text": SAMPLE_RESUME_2},
        {"id": "full_stack", "resume_text": SAMPLE_RESUME_3},
        {"id": "devops", "resume_text": SAMPLE_RESUME_4},
    ]

    print(f"\nAnalyzing {len(resumes)} different role profiles...\n")

    try:
        metadata_list = extract_batch_metadata(resumes)

        role_summary = {}
        for metadata in metadata_list:
            role = metadata['role_category']
            if role not in role_summary:
                role_summary[role] = []
            role_summary[role].append(metadata)

        for role, records in role_summary.items():
            print(f"{role.upper()}")
            for record in records:
                print(f"  Experience: {record['experience_years']} years ({record['experience_level']})")
                print(f"  Top Skills: {', '.join(record['top_skills'][:3])}")
            print()

    except Exception as e:
        print(f"Error: {e}")


def example_experience_analysis():
    """Example 5: Analyze experience levels across resumes."""
    print("\n" + "=" * 70)
    print("Example 5: Experience Level Analysis")
    print("=" * 70)

    resumes = [
        {"name": "Senior Backend Engineer", "resume_text": SAMPLE_RESUME_1},
        {"name": "Data Scientist", "resume_text": SAMPLE_RESUME_2},
        {"name": "Full Stack Dev", "resume_text": SAMPLE_RESUME_3},
        {"name": "DevOps Engineer", "resume_text": SAMPLE_RESUME_4},
    ]

    print(f"\nAnalyzing experience levels...\n")

    try:
        metadata_list = extract_batch_metadata(resumes)

        # Group by experience level
        levels = {}
        for i, metadata in enumerate(metadata_list):
            name = resumes[i]["name"]
            level = metadata['experience_level']
            years = metadata['experience_years']

            if level not in levels:
                levels[level] = []

            levels[level].append({
                "name": name,
                "years": years,
                "education": metadata['education']
            })

        # Display results
        level_names = {"entry": "Entry Level", "mid": "Mid Level",
                      "senior": "Senior", "lead": "Lead/Principal"}

        for level in ["entry", "mid", "senior", "lead"]:
            if level in levels:
                print(f"{level_names.get(level, level).upper()}")
                for person in levels[level]:
                    print(f"  {person['name']}: {person['years']} years, {person['education']}")
                print()

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("Metadata Extractor Examples")
    print("=" * 70)
    print("\nNote: These examples require OPENAI_API_KEY to be set in .env file")
    print("Running examples will make API calls and may incur costs.")

    # Uncomment the examples you want to run
    # (Requires valid OpenAI API key)

    try:
        example_single_extraction()
        example_class_usage()
        # Uncomment to run batch examples (may take longer):
        # example_multiple_extractions()
        # example_compare_categories()
        # example_experience_analysis()

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\nError: {e}")
        print("\nMake sure:")
        print("  1. OPENAI_API_KEY is set in your .env file")
        print("  2. You have valid OpenAI API credits")
        print("  3. Your internet connection is working")

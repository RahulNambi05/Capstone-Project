"""
Example usage of the job description parser module.
Demonstrates parsing job postings to extract structured information.
"""
import logging
from src.retrieval.job_parser import (
    parse_job_description,
    parse_job_descriptions_batch,
    JobDescriptionParser,
    ParsedJobDescription
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


# Sample job descriptions
SAMPLE_JOB_1 = """
Senior Backend Engineer - Python

Company: TechCorp
Location: San Francisco, CA

About the Role:
We're looking for an experienced Senior Backend Engineer to join our platform team.
You'll be responsible for designing and building scalable microservices that handle
millions of requests per day.

Requirements:
- 7+ years of professional software development experience
- Expert-level proficiency in Python
- Strong experience with Django or FastAPI web frameworks
- Expertise in PostgreSQL and relational databases
- Experience with Docker and container orchestration (Kubernetes preferred)
- Strong understanding of REST APIs and microservices architecture
- Experience with CI/CD pipelines and DevOps practices
- AWS cloud platform experience
- Excellent problem-solving and communication skills

Preferred Qualifications:
- Experience with GraphQL
- Kubernetes certification
- Experience with event-driven architectures (Kafka, RabbitMQ)
- Contributions to open-source projects
- Experience with machine learning pipelines

Responsibilities:
- Design and implement high-performance backend services
- Mentor junior engineers
- Lead architectural discussions
- Optimize database queries and system performance
"""

SAMPLE_JOB_2 = """
Frontend Developer - React

Company: WebDesign Inc
Location: Remote

Job Overview:
We're seeking a talented Frontend Developer with strong React skills to build
modern, responsive user interfaces for our SaaS platform.

Required:
- 3+ years of front-end development experience
- Proficiency in React (16.8+)
- Strong JavaScript/TypeScript knowledge
- CSS and responsive design expertise
- HTML5 fundamentals
- Experience with modern build tools (Webpack, Vite)
- Git version control
- Understanding of web performance optimization

Nice to Have:
- Next.js experience
- Testing frameworks (Jest, React Testing Library)
- State management (Redux, Zustand)
- CSS-in-JS libraries (styled-components, emotion)
- UI/UX design knowledge
- Accessibility (WCAG) compliance experience

Key Responsibilities:
- Develop interactive web components
- Collaborate with designers and backend engineers
- Implement unit tests
- Optimize bundle size and load times
- Participate in code reviews
"""

SAMPLE_JOB_3 = """
Data Scientist - Machine Learning

Company: AI Innovations
Location: New York, NY

Position Summary:
Join our AI team as a Data Scientist to develop machine learning solutions
that drive business impact. You'll work on NLP, computer vision, and
recommendation systems.

Required Skills:
- Master's degree in Computer Science, Statistics, or related field
- 4+ years of experience in machine learning
- Python expertise (NumPy, Pandas, Scikit-learn)
- Deep learning frameworks: TensorFlow or PyTorch
- SQL and database experience
- Statistical analysis and hypothesis testing
- Experience with cloud platforms (AWS preferred)
- Strong communication skills

Preferred Skills:
- NLP experience (NLTK, spaCy, Transformers)
- Computer vision (OpenCV, YOLOv5)
- Apache Spark for big data processing
- Model deployment and MLOps (MLflow, Airflow)
- Kaggle competition experience
- Published research papers
- Docker and containerization

Duties:
- Design and implement ML models
- Prepare and analyze large datasets
- Build data pipelines
- Deploy models to production
- Present findings to stakeholders
"""

SAMPLE_JOB_4 = """
Entry-Level Backend Engineer

Company: StartupXYZ
Location: Boston, MA

About Us:
We're a venture-backed startup building developer tools. We're looking for
passionate junior engineers to grow with our team.

About the Role:
- Recent graduate or 0-2 years of experience
- Work with Python and JavaScript
- Build RESTful APIs
- Learn and grow rapidly
- Mentor from senior engineers

Must Have:
- Computer Science degree or bootcamp graduation
- Knowledge of Python, JavaScript, or similar language
- Basic understanding of databases
- Familiarity with Git
- Problem-solving ability

Nice to Have:
- Internship experience
- Portfolio or GitHub projects
- Understanding of web fundamentals
- Basic DevOps knowledge

Responsibilities:
- Write clean, maintainable code
- Participate in sprint planning
- Assist with DevOps tasks
- Contribute to documentation
"""

SAMPLE_JOB_5 = """
DevOps Engineer - Infrastructure

Company: CloudSystems
Location: Seattle, WA

Description:
We need a DevOps engineer to manage our cloud infrastructure and
improve our deployment pipelines.

Requirements:
- 5+ years in DevOps or infrastructure engineering
- Kubernetes administration and orchestration
- Docker containerization
- CI/CD pipeline experience (Jenkins, GitLab CI, GitHub Actions)
- AWS or Azure cloud platform knowledge
- Infrastructure as Code (Terraform, CloudFormation)
- Linux system administration
- Monitoring and logging tools (Prometheus, ELK, Datadog)
- Ansible or Chef configuration management

Preferred:
- CKA (Certified Kubernetes Administrator) certification
- Terraform expertise
- GitOps experience
- Helm chart creation
- Istio service mesh knowledge
- On-call rotation experience

Duties:
- Maintain production Kubernetes clusters
- Automate infrastructure provisioning
- Monitor system performance
- Optimize cloud costs
- Implement disaster recovery
"""


def example_single_parse():
    """Example 1: Parse a single job description."""
    print("\n" + "=" * 70)
    print("Example 1: Parse Single Job Description")
    print("=" * 70)

    print("\nParsing Senior Backend Engineer job description...")

    try:
        parsed = parse_job_description(SAMPLE_JOB_1)

        print("\nParsed Job Description:")
        print(f"  Summary: {parsed.job_summary}")
        print(f"  Experience Level: {parsed.experience_level}")
        print(f"  Role Category: {parsed.role_category}")
        print(f"\n  Required Skills ({len(parsed.required_skills)}):")
        for skill in parsed.required_skills:
            print(f"    • {skill}")
        print(f"\n  Preferred Skills ({len(parsed.preferred_skills)}):")
        for skill in parsed.preferred_skills:
            print(f"    • {skill}")

    except Exception as e:
        print(f"Error: {e}")


def example_batch_parse():
    """Example 2: Parse multiple job descriptions."""
    print("\n" + "=" * 70)
    print("Example 2: Batch Parse Job Descriptions")
    print("=" * 70)

    jobs = [
        {"description": SAMPLE_JOB_1, "id": "job_001", "title": "Senior Backend Engineer"},
        {"description": SAMPLE_JOB_2, "id": "job_002", "title": "Frontend Developer"},
        {"description": SAMPLE_JOB_3, "id": "job_003", "title": "Data Scientist"},
    ]

    print(f"\nParsing {len(jobs)} job descriptions...\n")

    try:
        parsed_jobs = parse_job_descriptions_batch(jobs)

        for i, parsed in enumerate(parsed_jobs):
            job_info = jobs[i]
            print(f"Job: {job_info['title']}")
            print(f"  Summary: {parsed.job_summary}")
            print(f"  Level: {parsed.experience_level} | Role: {parsed.role_category}")
            print(f"  Required: {', '.join(parsed.required_skills[:3])}...")
            print()

    except Exception as e:
        print(f"Error: {e}")


def example_class_usage():
    """Example 3: Using JobDescriptionParser class directly."""
    print("\n" + "=" * 70)
    print("Example 3: Direct Class Usage")
    print("=" * 70)

    # Create a parser instance
    parser = JobDescriptionParser(temperature=0.1)

    print("\nParsing Frontend Developer job description...\n")

    try:
        parsed = parser.parse(SAMPLE_JOB_2)

        print("Frontend Role Analysis:")
        print(f"  Job Summary: {parsed.job_summary}")
        print(f"  Experience Level: {parsed.experience_level}")
        print(f"  Role Category: {parsed.role_category}")
        print(f"\n  Core Required Technologies:")
        for skill in parsed.required_skills[:5]:
            print(f"    ✓ {skill}")
        print(f"\n  Additional Assets:")
        for skill in parsed.preferred_skills[:5]:
            print(f"    ◇ {skill}")

    except Exception as e:
        print(f"Error: {e}")


def example_compare_jobs():
    """Example 4: Compare multiple job postings."""
    print("\n" + "=" * 70)
    print("Example 4: Job Comparison Analysis")
    print("=" * 70)

    jobs = [
        {"description": SAMPLE_JOB_1, "title": "Senior Backend Engineer"},
        {"description": SAMPLE_JOB_4, "title": "Entry-Level Backend Engineer"},
    ]

    print(f"\nAnalyzing different seniority levels for backend roles...\n")

    try:
        for job_info in jobs:
            parsed = parse_job_description(job_info["description"])

            print(f"{job_info['title'].upper()}")
            print(f"  Experience Level: {parsed.experience_level}")
            print(f"  Required Skills: {len(parsed.required_skills)}")
            print(f"  Preferred Skills: {len(parsed.preferred_skills)}")
            print(f"  Total Skills: {len(parsed.required_skills) + len(parsed.preferred_skills)}")
            print()

    except Exception as e:
        print(f"Error: {e}")


def example_skill_analysis():
    """Example 5: Analyze skill requirements across jobs."""
    print("\n" + "=" * 70)
    print("Example 5: Skill Requirements Analysis")
    print("=" * 70)

    jobs = [
        {"description": SAMPLE_JOB_1, "title": "Backend"},
        {"description": SAMPLE_JOB_2, "title": "Frontend"},
        {"description": SAMPLE_JOB_3, "title": "Data Science"},
        {"description": SAMPLE_JOB_5, "title": "DevOps"},
    ]

    print(f"\nAnalyzing skill requirements across {len(jobs)} roles...\n")

    try:
        all_required_skills = {}
        role_categories = {}

        for job_info in jobs:
            parsed = parse_job_description(job_info["description"])
            role_categories[job_info['title']] = parsed.role_category

            # Collect required skills
            for skill in parsed.required_skills:
                if skill not in all_required_skills:
                    all_required_skills[skill] = []
                all_required_skills[skill].append(job_info['title'])

        print("Role Categories Found:")
        for role_type, category in role_categories.items():
            print(f"  {role_type}: {category}")

        print(f"\nMost Commonly Required Skills:")
        sorted_skills = sorted(all_required_skills.items(),
                             key=lambda x: len(x[1]), reverse=True)

        for skill, roles in sorted_skills[:10]:
            print(f"  {skill}: {', '.join(roles)}")

    except Exception as e:
        print(f"Error: {e}")


def example_parsed_model():
    """Example 6: Working with ParsedJobDescription model."""
    print("\n" + "=" * 70)
    print("Example 6: ParsedJobDescription Model")
    print("=" * 70)

    print("\nParsing job description and working with Pydantic model...\n")

    try:
        parsed = parse_job_description(SAMPLE_JOB_3)

        # Access as dictionary
        print("As Dictionary:")
        print(f"  {parsed.model_dump()}\n")

        # Access as JSON
        print("As JSON:")
        print(f"  {parsed.model_dump_json(indent=2)}\n")

        # Access individual fields
        print("Individual Fields:")
        print(f"  Required Skills Count: {len(parsed.required_skills)}")
        print(f"  Preferred Skills Count: {len(parsed.preferred_skills)}")
        print(f"  Experience Level: {parsed.experience_level}")
        print(f"  Role Category: {parsed.role_category}")

    except Exception as e:
        print(f"Error: {e}")


def example_experience_distribution():
    """Example 7: Experience level distribution."""
    print("\n" + "=" * 70)
    print("Example 7: Experience Level Distribution")
    print("=" * 70)

    jobs = [
        {"description": SAMPLE_JOB_1, "title": "Senior Backend Engineer"},
        {"description": SAMPLE_JOB_2, "title": "Frontend Developer"},
        {"description": SAMPLE_JOB_3, "title": "Data Scientist"},
        {"description": SAMPLE_JOB_4, "title": "Entry-Level Backend Engineer"},
        {"description": SAMPLE_JOB_5, "title": "DevOps Engineer"},
    ]

    print(f"\nAnalyzing experience levels across {len(jobs)} job postings...\n")

    try:
        level_distribution = {}

        for job_info in jobs:
            parsed = parse_job_description(job_info["description"])
            level = parsed.experience_level

            if level not in level_distribution:
                level_distribution[level] = []
            level_distribution[level].append(job_info['title'])

        # Display distribution
        level_names = {
            "entry": "Entry Level (0-2 years)",
            "mid": "Mid Level (2-5 years)",
            "senior": "Senior (5-10 years)",
            "lead": "Lead/Principal (10+ years)"
        }

        for level in ["entry", "mid", "senior", "lead"]:
            if level in level_distribution:
                jobs_at_level = level_distribution[level]
                print(f"{level_names[level]}:")
                for job_title in jobs_at_level:
                    print(f"  • {job_title}")
                print()

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("Job Description Parser Examples")
    print("=" * 70)
    print("\nNote: These examples require OPENAI_API_KEY to be set in .env file")
    print("Running these examples will make API calls and may incur costs.\n")

    try:
        # Run examples
        example_single_parse()
        example_class_usage()
        # Uncomment to run batch examples (may take longer):
        # example_batch_parse()
        # example_compare_jobs()
        # example_skill_analysis()
        # example_parsed_model()
        # example_experience_distribution()

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\nError: {e}")
        print("\nMake sure:")
        print("  1. OPENAI_API_KEY is set in your .env file")
        print("  2. You have valid OpenAI API credits")
        print("  3. Your internet connection is working")

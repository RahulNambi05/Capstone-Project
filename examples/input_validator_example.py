"""
Example usage of the input validator module.
Demonstrates validation of job descriptions and resume uploads.
"""
import logging
from src.guardrails.input_validator import (
    validate_job_description,
    validate_resume_upload,
    InputValidator
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


# Sample inputs
VALID_JOB_DESCRIPTION = """
Senior Backend Engineer - New York

We are looking for an experienced Senior Backend Engineer to join our platform team.
You will be responsible for designing and building scalable microservices that
handle millions of requests per day.

Requirements:
- 7+ years of professional software development experience
- Expert-level proficiency in Python
- Strong experience with Django or FastAPI web frameworks
- Expertise in PostgreSQL and relational databases
- Experience with Docker and Kubernetes container orchestration
- Strong understanding of REST APIs and microservices architecture
- AWS cloud platform experience
- Excellent problem-solving and communication skills

Preferred Qualifications:
- GraphQL experience
- Experience with event-driven architectures (Kafka, RabbitMQ)
- Kubernetes certification
- Contributions to open-source projects

This is a great opportunity to work with cutting-edge technologies and grow your career.
"""

SHORT_JOB_DESCRIPTION = "Need developer."

GIBBERISH_JOB_DESCRIPTION = """
xyz abc qwe rty uop hjk lmn vbn mnb cxz qaz wsx edc rfv tgy uhi olk p;l kmo ijn
xyz abc qwe rty uop hjk lmn vbn mnb cxz qaz wsx edc rfv tgy uhi olk p;l kmo ijn
xyz abc qwe rty uop hjk lmn vbn mnb cxz qaz wsx edc rfv tgy uhi olk p;l kmo ijn
"""

SKILLLESS_JOB = """
We are looking for someone to join our team. This is a great opportunity.
You will work on interesting projects and grow your career. We offer competitive
compensation and benefits. Please send your resume if you are interested.
We look forward to hearing from you soon. Contact us today for more information.
"""

VALID_RESUME = """
JOHN DOE
john.doe@example.com | (555) 123-4567 | LinkedIn: /in/johndoe

PROFESSIONAL SUMMARY
Experienced Backend Engineer with 7 years of expertise in Python development and
cloud infrastructure. Strong background in building scalable microservices and
leading engineering teams.

TECHNICAL SKILLS
Programming Languages: Python, JavaScript, Java
Backend Frameworks: Django, FastAPI, Spring Boot
Databases: PostgreSQL, MongoDB, Redis
Cloud Platforms: AWS (EC2, S3, Lambda, RDS), Google Cloud
DevOps: Docker, Kubernetes, Jenkins, GitHub Actions
Other: Git, Linux, REST APIs, Microservices

PROFESSIONAL EXPERIENCE

Senior Backend Engineer | TechCorp Inc. | January 2021 - Present
- Led development of microservices architecture using FastAPI and Docker
- Designed and implemented distributed systems handling 1M+ requests/day
- Mentored team of 5 junior engineers
- Achieved 99.9% uptime SLA for production services

Full Stack Developer | StartupXYZ | June 2018 - December 2020
- Developed web applications using Django and React
- Implemented PostgreSQL database schemas and optimizations
- Deployed applications on AWS using EC2, RDS, and S3

EDUCATION
B.S. Computer Science
State University | Graduated: 2017

CERTIFICATIONS
AWS Certified Solutions Architect - Associate (2022)
Python Professional Certification (2021)
"""

SHORT_RESUME = "I am a developer with some experience."

RESUME_NO_SECTIONS = """
I have worked at various companies over the years. I know Python and JavaScript.
I live in New York and enjoy programming. I am looking for new opportunities.
My email is test@example.com. Contact me if interested.
"""


def example_valid_job_description():
    """Example 1: Validate a well-formed job description."""
    print("\n" + "=" * 70)
    print("Example 1: Valid Job Description")
    print("=" * 70)

    result = validate_job_description(VALID_JOB_DESCRIPTION)

    print(f"\nInput: Senior Backend Engineer job description")
    print(f"Valid: {result.is_valid}")
    print(f"Reason: {result.reason}")

    if result.details:
        print(f"\nDetails:")
        print(f"  Word Count: {result.details.get('word_count', 0)}")
        print(f"  Has Skills: {result.details.get('contains_skills', False)}")
        print(f"  Has Roles: {result.details.get('contains_roles', False)}")
        print(f"  Entropy: {result.details.get('entropy_score', 0):.4f}")
        print(f"  Skills Found: {result.details.get('skill_keywords_found', [])[:5]}...")

    if result.warnings:
        print(f"\nWarnings:")
        for warning in result.warnings:
            print(f"  ⚠ {warning}")


def example_invalid_job_descriptions():
    """Example 2: Validate invalid job descriptions."""
    print("\n" + "=" * 70)
    print("Example 2: Invalid Job Descriptions")
    print("=" * 70)

    test_cases = [
        ("Too Short", SHORT_JOB_DESCRIPTION),
        ("Gibberish", GIBBERISH_JOB_DESCRIPTION),
        ("No Skills/Roles", SKILLLESS_JOB),
    ]

    for name, text in test_cases:
        result = validate_job_description(text)

        print(f"\nTest: {name}")
        print(f"  Valid: {result.is_valid}")
        print(f"  Reason: {result.reason}")


def example_valid_resume():
    """Example 3: Validate a well-formed resume."""
    print("\n" + "=" * 70)
    print("Example 3: Valid Resume")
    print("=" * 70)

    result = validate_resume_upload(VALID_RESUME)

    print(f"\nInput: John Doe resume")
    print(f"Valid: {result.is_valid}")
    print(f"Reason: {result.reason}")

    if result.details:
        print(f"\nDetails:")
        print(f"  Word Count: {result.details.get('word_count', 0)}")
        print(f"  Sections Found:")
        sections = result.details.get('found_sections', {})
        for section, found in sections.items():
            status = "✓" if found else "✗"
            print(f"    {status} {section.capitalize()}")
        print(f"  Has Email: {result.details.get('has_email', False)}")
        print(f"  Has Phone: {result.details.get('has_phone', False)}")
        print(f"  Has Name Section: {result.details.get('has_name_section', False)}")
        print(f"  Entropy: {result.details.get('entropy_score', 0):.4f}")

    if result.warnings:
        print(f"\nWarnings:")
        for warning in result.warnings:
            print(f"  ⚠ {warning}")


def example_invalid_resumes():
    """Example 4: Validate invalid resumes."""
    print("\n" + "=" * 70)
    print("Example 4: Invalid Resumes")
    print("=" * 70)

    test_cases = [
        ("Too Short", SHORT_RESUME),
        ("Missing Sections", RESUME_NO_SECTIONS),
    ]

    for name, text in test_cases:
        result = validate_resume_upload(text)

        print(f"\nTest: {name}")
        print(f"  Valid: {result.is_valid}")
        print(f"  Reason: {result.reason}")

        if result.details:
            print(f"  Word Count: {result.details.get('word_count', 0)}")
            sections = result.details.get('found_sections', {})
            found_count = sum(1 for found in sections.values() if found)
            print(f"  Sections Found: {found_count}/4")


def example_batch_validation():
    """Example 5: Validate multiple inputs."""
    print("\n" + "=" * 70)
    print("Example 5: Batch Validation")
    print("=" * 70)

    jobs = [
        ("Job 1", VALID_JOB_DESCRIPTION),
        ("Job 2", SHORT_JOB_DESCRIPTION),
        ("Job 3", SKILLLESS_JOB),
    ]

    resumes = [
        ("Resume 1", VALID_RESUME),
        ("Resume 2", SHORT_RESUME),
        ("Resume 3", RESUME_NO_SECTIONS),
    ]

    print("\nJob Description Validation:")
    print(f"{'Job':<12} {'Valid':<8} {'Word Count':<12} {'Skills':<8}")
    print(f"{'-' * 50}")

    for name, text in jobs:
        result = validate_job_description(text)
        details = result.details
        print(
            f"{name:<12} {str(result.is_valid):<8} "
            f"{details.get('word_count', 0):<12} "
            f"{details.get('contains_skills', False):<8}"
        )

    print("\n\nResume Validation:")
    print(f"{'Resume':<12} {'Valid':<8} {'Word Count':<12} {'Sections':<10}")
    print(f"{'-' * 50}")

    for name, text in resumes:
        result = validate_resume_upload(text)
        details = result.details
        sections = details.get('found_sections', {})
        section_count = sum(1 for found in sections.values() if found)
        print(
            f"{name:<12} {str(result.is_valid):<8} "
            f"{details.get('word_count', 0):<12} {section_count:<10}"
        )


def example_edge_cases():
    """Example 6: Test edge cases."""
    print("\n" + "=" * 70)
    print("Example 6: Edge Cases")
    print("=" * 70)

    edge_cases = [
        ("Empty String", ""),
        ("Only Whitespace", "   \n\n  \t  "),
        ("Single Word", "Developer"),
        ("Numbers Only", "123 456 789 012"),
    ]

    print("\nJob Description Edge Cases:")
    for name, text in edge_cases:
        result = validate_job_description(text)
        print(f"  {name}: {'Valid' if result.is_valid else 'Invalid'}")

    print("\nResume Upload Edge Cases:")
    for name, text in edge_cases:
        result = validate_resume_upload(text)
        print(f"  {name}: {'Valid' if result.is_valid else 'Invalid'}")


def example_class_usage():
    """Example 7: Using InputValidator class directly."""
    print("\n" + "=" * 70)
    print("Example 7: Direct Class Usage")
    print("=" * 70)

    validator = InputValidator()

    # Custom validation with details
    jd_result = validator.validate_job_description(VALID_JOB_DESCRIPTION)
    resume_result = validator.validate_resume_upload(VALID_RESUME)

    print("\nJob Description Validation:")
    print(f"  Status: {jd_result.is_valid}")
    print(f"  Skills: {len(jd_result.details.get('skill_keywords_found', []))} found")
    print(f"  Entropy: {jd_result.details.get('entropy_score', 0):.4f}")

    print("\nResume Validation:")
    print(f"  Status: {resume_result.is_valid}")
    sections = resume_result.details.get('found_sections', {})
    sections_found = [s for s, found in sections.items() if found]
    print(f"  Sections: {', '.join(sections_found)}")
    print(f"  Entropy: {resume_result.details.get('entropy_score', 0):.4f}")


def example_validation_rules():
    """Example 8: Explain validation rules."""
    print("\n" + "=" * 70)
    print("Example 8: Validation Rules")
    print("=" * 70)

    print("\nJOB DESCRIPTION VALIDATION RULES:")
    print("  1. Must contain at least 20 words")
    print("  2. Must contain at least one skill or role keyword")
    print("  3. Must not appear to be gibberish (entropy > 2.5)")
    print("  4. Warning: If < 30% unique words (indicates repetition)")

    print("\nRESUME VALIDATION RULES:")
    print("  1. Must contain at least 100 words")
    print("  2. Must contain at least 2 of: experience, education, skills, summary")
    print("  3. Must not appear to be gibberish (entropy > 2.5)")
    print("  4. Warning: Should contain email or phone")
    print("  5. Warning: Should have name/header section")
    print("  6. Warning: If < 20% unique words (indicates poor formatting)")

    print("\nKEYWORD EXAMPLES:")
    print("  Skills: Python, Java, Docker, Kubernetes, AWS, React, etc.")
    print("  Roles: Engineer, Developer, Lead, Architect, Manager, etc.")
    print("  Sections: Experience, Education, Skills, Summary, etc.")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("Input Validator Examples")
    print("=" * 70)

    try:
        # Run examples
        example_valid_job_description()
        example_invalid_job_descriptions()
        example_valid_resume()
        example_invalid_resumes()
        example_batch_validation()
        example_edge_cases()
        example_class_usage()
        example_validation_rules()

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\nError: {e}")

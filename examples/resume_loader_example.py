"""
Example usage of the resume loader module.
"""
from src.ingestion.resume_loader import (
    load_resumes_from_csv,
    load_resumes_from_list,
    validate_resume,
    get_resume_stats,
    clean_text
)
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Example 1: Load from CSV file
def example_load_from_csv():
    """Example of loading resumes from a CSV file."""
    try:
        resumes = load_resumes_from_csv(
            file_path="data/resumes/resume_dataset.csv",
            id_column="ID",
            resume_column="Resume_str",
            category_column="Category",
            validate=True,
            skip_invalid=True
        )

        print(f"\nLoaded {len(resumes)} resumes")
        if resumes:
            print(f"First resume: {resumes[0]}")

    except FileNotFoundError as e:
        print(f"Error: {e}")


# Example 2: Load from list of dictionaries
def example_load_from_list():
    """Example of loading resumes from a list of dictionaries."""
    resume_list = [
        {
            "id": "resume_001",
            "resume_text": "Experienced Python developer with 5 years in Django and FastAPI. "
                          "Strong in SQL, PostgreSQL, Docker containers, and AWS deployment. "
                          "Proficient in React frontend development and RESTful API design. "
                          "Leadership experience managing teams of 3-5 engineers.",
            "category": "Software Engineering"
        },
        {
            "id": "resume_002",
            "resume_text": "Senior Data Scientist specializing in machine learning and deep learning. "
                          "Expert in TensorFlow, PyTorch, scikit-learn, and Pandas. "
                          "Experience with cloud platforms AWS and Google Cloud. "
                          "Proven track record in NLP and computer vision projects.",
            "category": "Data Science"
        },
        {
            "id": "resume_003",
            "resume_text": "Recent graduate",  # Invalid - too short
            "category": "Entry-Level"
        }
    ]

    resumes = load_resumes_from_list(
        resume_list=resume_list,
        validate=True,
        skip_invalid=True
    )

    print(f"\nProcessed {len(resumes)} resumes from list")
    for resume in resumes:
        print(f"  - {resume['id']}: {resume['category']}")


# Example 3: Validate individual resumes
def example_validate_resume():
    """Example of validating individual resumes."""
    valid_resume = (
        "Experienced software engineer with 7 years in Python, Java, and JavaScript. "
        "Strong expertise in Django, React, and microservices architecture. "
        "Worked extensively with Docker, Kubernetes, and AWS services. "
        "Led teams in agile environments and mentored junior developers."
    )

    invalid_resume = "Brief resume text"

    print(f"\nValidate long resume: {validate_resume(valid_resume)}")
    print(f"Validate short resume: {validate_resume(invalid_resume)}")


# Example 4: Get resume statistics
def example_resume_stats():
    """Example of calculating resume statistics."""
    sample_resumes = [
        {
            "id": "1",
            "resume_text": "Python Java JavaScript React Docker Kubernetes AWS MongoDB SQL",
            "category": "Backend"
        },
        {
            "id": "2",
            "resume_text": "JavaScript React Vue Angular CSS HTML Webpack npm yarn",
            "category": "Frontend"
        },
        {
            "id": "3",
            "resume_text": "Python Machine Learning TensorFlow PyTorch Pandas NumPy Scikit-learn",
            "category": "Data Science"
        }
    ]

    stats = get_resume_stats(sample_resumes)
    print(f"\nResume Statistics:")
    print(f"  Total resumes: {stats['total_resumes']}")
    print(f"  Average words: {stats['avg_words']:.2f}")
    print(f"  Average characters: {stats['avg_characters']:.2f}")
    print(f"  Categories: {stats['categories']}")


# Example 5: Clean text
def example_clean_text():
    """Example of text cleaning."""
    messy_text = "  Python!!!   Developer   with   5+ years  @#$%  experience   "
    cleaned = clean_text(messy_text)
    print(f"\nOriginal: '{messy_text}'")
    print(f"Cleaned: '{cleaned}'")


if __name__ == "__main__":
    print("=" * 60)
    print("Resume Loader Examples")
    print("=" * 60)

    # Uncomment examples to run them
    # example_load_from_csv()  # Requires actual CSV file
    example_load_from_list()
    example_validate_resume()
    example_resume_stats()
    example_clean_text()

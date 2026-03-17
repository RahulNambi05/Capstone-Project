"""
Resume loader module for ingesting and processing resume data from CSV files.
"""
import pandas as pd
import re
import logging
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Common skill keywords for validation
SKILL_KEYWORDS = {
    # Programming Languages
    "python", "java", "javascript", "typescript", "csharp", "c#", "c++", "ruby",
    "php", "swift", "kotlin", "go", "rust", "r", "matlab",

    # Web Technologies
    "html", "css", "react", "angular", "vue", "nodejs", "node.js", "django",
    "flask", "fastapi", "express", "spring", "asp.net", "rails", "laravel",

    # Data & Databases
    "sql", "mysql", "postgresql", "mongodb", "cassandra", "redis", "elasticsearch",
    "spark", "hadoop", "hive", "pandas", "numpy", "sqlite", "oracle", "dynamodb",

    # Cloud & DevOps
    "aws", "azure", "gcp", "google cloud", "docker", "kubernetes", "k8s",
    "jenkins", "gitlab", "github", "terraform", "ansible", "ci/cd", "devops",

    # Data Science & ML
    "machine learning", "deep learning", "tensorflow", "pytorch", "scikit-learn",
    "sklearn", "nlp", "computer vision", "keras", "xgboost", "analytics",

    # Other Technologies
    "api", "rest", "graphql", "grpc", "microservices", "git", "linux", "unix",
    "windows", "macos", "agile", "scrum", "jira", "confluence", "slack",

    # Frameworks & Tools
    "jupyter", "conda", "pip", "npm", "yarn", "webpack", "gradle", "maven",
    "jboss", "tomcat", "nginx", "apache", "rabbitmq", "kafka", "aws lambda"
}

# Minimum word count for valid resume
MIN_RESUME_WORDS = 50


def clean_text(text: str) -> str:
    """
    Clean and normalize resume text.

    Args:
        text: Raw text to clean

    Returns:
        Cleaned and normalized text
    """
    if not isinstance(text, str):
        return ""

    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)

    # Remove special characters but keep basic punctuation and alphanumeric
    text = re.sub(r'[^\w\s\-\.\,\(\)\/\@\:\;\']', '', text)

    # Remove leading/trailing whitespace
    text = text.strip()

    return text


def validate_resume(text: str) -> bool:
    """
    Validate if resume text meets minimum quality standards.

    A valid resume must:
    - Contain at least MIN_RESUME_WORDS words
    - Contain at least one recognizable skill keyword

    Args:
        text: Resume text to validate

    Returns:
        True if resume is valid, False otherwise
    """
    if not isinstance(text, str):
        return False

    # Check minimum word count
    words = text.split()
    if len(words) < MIN_RESUME_WORDS:
        logger.debug(f"Resume validation failed: insufficient words ({len(words)} < {MIN_RESUME_WORDS})")
        return False

    # Check for recognizable skill keywords
    text_lower = text.lower()
    has_skills = any(skill in text_lower for skill in SKILL_KEYWORDS)

    if not has_skills:
        logger.debug("Resume validation failed: no recognizable skill keywords found")
        return False

    return True


def load_resumes_from_csv(
    file_path: str,
    id_column: str = "ID",
    resume_column: str = "Resume_str",
    category_column: str = "Category",
    validate: bool = True,
    skip_invalid: bool = False
) -> List[Dict[str, str]]:
    """
    Load and process resumes from a CSV file.

    Args:
        file_path: Path to the CSV file
        id_column: Name of the ID column (default: "ID")
        resume_column: Name of the resume text column (default: "Resume_str")
        category_column: Name of the category column (default: "Category")
        validate: Whether to validate resumes (default: True)
        skip_invalid: Whether to skip invalid resumes (default: False)

    Returns:
        List of processed resume dictionaries with keys: id, resume_text, category

    Raises:
        FileNotFoundError: If the CSV file does not exist
        ValueError: If required columns are missing
    """
    file_path = Path(file_path)

    # Check if file exists
    if not file_path.exists():
        raise FileNotFoundError(f"CSV file not found: {file_path}")

    try:
        logger.info(f"Loading resumes from {file_path}")
        df = pd.read_csv(file_path)
    except Exception as e:
        raise ValueError(f"Error reading CSV file: {str(e)}")

    # Check if required columns exist
    required_columns = {id_column, resume_column, category_column}
    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}. "
            f"Found columns: {list(df.columns)}"
        )

    processed_resumes = []
    skipped_count = 0

    for idx, row in df.iterrows():
        try:
            # Extract values
            resume_id = str(row[id_column]).strip()
            resume_text = str(row[resume_column]) if pd.notna(row[resume_column]) else ""
            category = str(row[category_column]).strip() if pd.notna(row[category_column]) else "Uncategorized"

            # Handle missing or empty resume text
            if not resume_text or not resume_text.strip():
                logger.warning(f"Skipping row {idx}: empty resume text for ID {resume_id}")
                skipped_count += 1
                continue

            # Clean resume text
            cleaned_text = clean_text(resume_text)

            # Validate resume if requested
            if validate and not validate_resume(cleaned_text):
                if skip_invalid:
                    logger.warning(f"Skipping row {idx}: resume validation failed for ID {resume_id}")
                    skipped_count += 1
                    continue
                else:
                    logger.warning(f"Resume validation failed for ID {resume_id}, but processing anyway")

            # Add to processed list
            processed_resumes.append({
                "id": resume_id,
                "resume_text": cleaned_text,
                "category": category
            })

        except Exception as e:
            logger.error(f"Error processing row {idx}: {str(e)}")
            skipped_count += 1
            continue

    logger.info(
        f"Successfully loaded {len(processed_resumes)} resumes. "
        f"Skipped {skipped_count} invalid/missing entries."
    )

    return processed_resumes


def load_resumes_from_list(
    resume_list: List[Dict[str, str]],
    validate: bool = True,
    skip_invalid: bool = False
) -> List[Dict[str, str]]:
    """
    Process a list of resume dictionaries.

    Args:
        resume_list: List of dicts with 'id', 'resume_text', 'category' keys
        validate: Whether to validate resumes (default: True)
        skip_invalid: Whether to skip invalid resumes (default: False)

    Returns:
        List of processed resume dictionaries

    Raises:
        ValueError: If input list is empty or has invalid structure
    """
    if not resume_list:
        raise ValueError("Resume list is empty")

    if not isinstance(resume_list, list):
        raise ValueError("Input must be a list of dictionaries")

    processed_resumes = []
    skipped_count = 0

    for idx, resume in enumerate(resume_list):
        try:
            if not isinstance(resume, dict):
                logger.warning(f"Skipping item {idx}: not a dictionary")
                skipped_count += 1
                continue

            resume_id = resume.get("id", f"resume_{idx}")
            resume_text = resume.get("resume_text", "")
            category = resume.get("category", "Uncategorized")

            if not resume_text or not resume_text.strip():
                logger.warning(f"Skipping item {idx}: empty resume text for ID {resume_id}")
                skipped_count += 1
                continue

            # Clean resume text
            cleaned_text = clean_text(resume_text)

            # Validate resume if requested
            if validate and not validate_resume(cleaned_text):
                if skip_invalid:
                    logger.warning(f"Skipping item {idx}: resume validation failed for ID {resume_id}")
                    skipped_count += 1
                    continue

            processed_resumes.append({
                "id": resume_id,
                "resume_text": cleaned_text,
                "category": category
            })

        except Exception as e:
            logger.error(f"Error processing item {idx}: {str(e)}")
            skipped_count += 1
            continue

    logger.info(
        f"Successfully processed {len(processed_resumes)} resumes. "
        f"Skipped {skipped_count} invalid/missing entries."
    )

    return processed_resumes


def get_resume_stats(resumes: List[Dict[str, str]]) -> Dict[str, any]:
    """
    Calculate statistics about a list of resumes.

    Args:
        resumes: List of processed resume dictionaries

    Returns:
        Dictionary with resume statistics
    """
    if not resumes:
        return {
            "total_resumes": 0,
            "avg_words": 0,
            "avg_characters": 0,
            "categories": {}
        }

    total_words = 0
    total_chars = 0
    categories = {}

    for resume in resumes:
        text = resume.get("resume_text", "")
        category = resume.get("category", "Uncategorized")

        total_words += len(text.split())
        total_chars += len(text)
        categories[category] = categories.get(category, 0) + 1

    return {
        "total_resumes": len(resumes),
        "avg_words": total_words / len(resumes) if resumes else 0,
        "avg_characters": total_chars / len(resumes) if resumes else 0,
        "categories": categories,
        "category_distribution": {
            cat: count / len(resumes) * 100
            for cat, count in categories.items()
        }
    }

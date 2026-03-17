"""
Input validation module providing guardrails for job descriptions and resume uploads.
Includes validation for content quality, format, and basic sanity checks.
"""
import logging
import re
from typing import List, Dict, Any, Optional
from collections import Counter
import math
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

def detect_bias(job_description: str) -> Dict[str, Any]:
    """
    Detect potentially biased language in a job description.

    Returns a dict:
    {
      "has_bias": True/False,
      "bias_types": ["age_bias", "gender_bias"],
      "flagged_words": ["young", "he"],
      "suggestion": "Consider using inclusive language"
    }
    """
    if not isinstance(job_description, str) or not job_description.strip():
        return {
            "has_bias": False,
            "bias_types": [],
            "flagged_words": [],
            "suggestion": "Consider using inclusive language",
        }

    text = job_description.lower()

    age_bias_keywords = [
        "young",
        "recent graduate",
        "digital native",
        "energetic",
        "aged between",
        "under 30",
        "fresh",
    ]
    gender_bias_keywords = [
        "he",
        "she",
        "manpower",
        "salesman",
        "stewardess",
        "mankind",
        "chairman",
    ]
    cultural_language_bias_keywords = [
        "native english speaker",
        "mother tongue english",
        "locally born",
        "local candidate only",
    ]

    flagged: List[str] = []
    bias_types: List[str] = []

    def _match_phrases(phrases: List[str]) -> List[str]:
        hits: List[str] = []
        for phrase in phrases:
            if phrase in text:
                hits.append(phrase)
        return hits

    age_hits = _match_phrases(age_bias_keywords)
    gender_hits = _match_phrases(gender_bias_keywords)
    cultural_hits = _match_phrases(cultural_language_bias_keywords)

    if age_hits:
        bias_types.append("age_bias")
        flagged.extend(age_hits)
    if gender_hits:
        bias_types.append("gender_bias")
        flagged.extend(gender_hits)
    if cultural_hits:
        bias_types.append("cultural_language_bias")
        flagged.extend(cultural_hits)

    # Reduce duplicates while preserving order
    seen = set()
    flagged_unique: List[str] = []
    for w in flagged:
        if w not in seen:
            flagged_unique.append(w)
            seen.add(w)

    return {
        "has_bias": bool(bias_types),
        "bias_types": bias_types,
        "flagged_words": flagged_unique,
        "suggestion": "Consider using inclusive language",
    }


class ValidationResult(BaseModel):
    """
    Result of input validation.
    """
    is_valid: bool = Field(
        ...,
        description="Whether the input passed validation"
    )
    reason: str = Field(
        ...,
        description="Human-readable reason if invalid, or success message"
    )
    details: Dict[str, Any] = Field(
        default_factory=dict,
        description="Detailed validation information"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Non-blocking warnings about the input"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "is_valid": True,
                "reason": "Job description passed all validation checks",
                "details": {
                    "word_count": 150,
                    "has_skills": True,
                    "entropy_score": 4.2,
                    "contains_keywords": ["python", "engineer"]
                },
                "warnings": []
            }
        }


# Skill and role keywords for validation
SKILL_KEYWORDS = {
    "python", "java", "javascript", "typescript", "csharp", "c#", "c++", "ruby",
    "php", "swift", "kotlin", "go", "rust", "r", "matlab", "scala",
    "html", "css", "react", "angular", "vue", "nodejs", "node.js", "django",
    "flask", "fastapi", "express", "spring", "asp.net", "rails", "laravel",
    "sql", "mysql", "postgresql", "mongodb", "cassandra", "redis", "elasticsearch",
    "spark", "hadoop", "hive", "pandas", "numpy", "tensorflow", "pytorch",
    "aws", "azure", "gcp", "google cloud", "docker", "kubernetes", "k8s",
    "jenkins", "gitlab", "github", "terraform", "ansible", "ci/cd",
    "machine learning", "deep learning", "nlp", "computer vision", "api",
    "rest", "graphql", "grpc", "microservices", "git", "linux", "unix",
    "agile", "scrum", "jira", "git", "kafka", "rabbitmq"
}

ROLE_KEYWORDS = {
    "engineer", "developer", "lead", "senior", "junior", "architect",
    "analyst", "manager", "director", "scientist", "specialist",
    "intern", "coordinator", "administrator", "consultant",
    "backend", "frontend", "full stack", "fullstack", "devops",
    "data scientist", "machine learning", "qa", "quality assurance",
    "product owner", "product manager", "solutions architect"
}

RESUME_SECTION_KEYWORDS = {
    "experience": {"experience", "work history", "previous roles", "employment"},
    "education": {"education", "degree", "university", "college", "school", "graduated"},
    "skills": {"skills", "technical", "competencies", "expertise", "proficiencies"},
    "summary": {"summary", "objective", "profile", "about", "overview"}
}

# Minimum requirements
MIN_JOB_DESCRIPTION_WORDS = 20
MIN_RESUME_WORDS = 100
MIN_ENTROPY_THRESHOLD = 2.5  # For gibberish detection

JOB_DESCRIPTION_REQUIRED_KEYWORDS = {
    "experience",
    "skills",
    "looking",
    "candidate",
    "developer",
    "manager",
    "engineer",
    "analyst",
    "team",
    "work",
    "require",
    "knowledge",
    "ability",
    "position",
    "role",
    "job",
    "hire",
    "professional",
    "expert",
    "background",
    "qualified",
    "python",
    "java",
    "sql",
    "data",
    "software",
    "technical",
    "business",
    "senior",
    "junior",
    "lead",
    "strong",
    "build",
    "design",
    "develop",
    "manage",
    "support",
    "implement",
    "analyze",
    "communicate",
    "collaborate",
    "responsible",
    "proficient",
}

INVALID_JOB_DESCRIPTION_REASON = (
    "Invalid job description: please provide a real job description with role requirements"
)


class InputValidator:
    """
    Validates job descriptions and resume uploads against quality and format standards.
    """

    def __init__(self):
        """Initialize the InputValidator."""
        logger.info("InputValidator initialized")

    def validate_job_description(self, text: str) -> ValidationResult:
        """
        Validate a job description for quality and format.

        Args:
            text: The job description text to validate

        Returns:
            ValidationResult with validation status and details
        """
        if not isinstance(text, str):
            return ValidationResult(
                is_valid=False,
                reason="Job description must be a text string",
                details={"error": "invalid_type"}
            )

        if not text.strip():
            return ValidationResult(
                is_valid=False,
                reason="Job description cannot be empty",
                details={"error": "empty_text"}
            )

        details: Dict[str, Any] = {}
        warnings: List[str] = []

        text_lower = text.lower()
        words = re.findall(r"[a-z]+", text_lower)
        word_count = len(words)
        details["word_count"] = word_count

        # Keyword check (lenient; used together with word-count check)
        word_set = set(words)
        job_keywords_found = sorted(word_set.intersection(JOB_DESCRIPTION_REQUIRED_KEYWORDS))
        details["job_keywords_found"] = job_keywords_found
        details["job_keywords_count"] = len(job_keywords_found)

        # Only reject if BOTH: too short AND no keywords found
        if word_count < MIN_JOB_DESCRIPTION_WORDS and len(job_keywords_found) < 1:
            return ValidationResult(
                is_valid=False,
                reason=INVALID_JOB_DESCRIPTION_REASON,
                details={
                    "word_count": word_count,
                    "job_keywords_found": job_keywords_found,
                    "job_keywords_count": len(job_keywords_found),
                    "failed_check": "min_word_count_and_keywords",
                },
            )

        # Additional signals (non-blocking)
        found_skills: List[str] = []
        found_roles: List[str] = []

        for skill in SKILL_KEYWORDS:
            if skill in text_lower:
                found_skills.append(skill)

        for role in ROLE_KEYWORDS:
            if role in text_lower:
                found_roles.append(role)

        details["contains_skills"] = len(found_skills) > 0
        details["skill_keywords_found"] = found_skills[:10]  # Top 10
        details["contains_roles"] = len(found_roles) > 0
        details["role_keywords_found"] = found_roles[:10]  # Top 10

        entropy_score = self._calculate_entropy(text)
        details["entropy_score"] = round(entropy_score, 4)

        # Reasonable content (warning only)
        if len(set(words)) < len(words) * 0.3:  # Less than 30% unique words
            warnings.append(
                "Job description has many repeated words, which may indicate poor quality"
            )

        reason = "Job description passed all validation checks"
        is_valid = True

        logger.info(
            f"Job description validation: "
            f"is_valid={is_valid}, word_count={word_count}, "
            f"skills={len(found_skills)}, roles={len(found_roles)}"
        )

        return ValidationResult(
            is_valid=is_valid,
            reason=reason,
            details=details,
            warnings=warnings
        )

    def validate_resume_upload(self, text: str) -> ValidationResult:
        """
        Validate a resume upload for quality and format.

        Args:
            text: The resume text to validate

        Returns:
            ValidationResult with validation status and details
        """
        if not isinstance(text, str):
            return ValidationResult(
                is_valid=False,
                reason="Resume must be a text string",
                details={"error": "invalid_type"}
            )

        if not text.strip():
            return ValidationResult(
                is_valid=False,
                reason="Resume cannot be empty",
                details={"error": "empty_text"}
            )

        details: Dict[str, Any] = {}
        warnings: List[str] = []
        reasons: List[str] = []

        # Check 1: Minimum word count
        words = text.split()
        word_count = len(words)
        details["word_count"] = word_count

        if word_count < MIN_RESUME_WORDS:
            reasons.append(
                f"Resume must contain at least {MIN_RESUME_WORDS} words "
                f"(found {word_count})"
            )

        # Check 2: Contains required sections
        text_lower = text.lower()
        found_sections = {}

        for section_name, keywords in RESUME_SECTION_KEYWORDS.items():
            found = False
            for keyword in keywords:
                if keyword in text_lower:
                    found = True
                    break
            found_sections[section_name] = found

        details["found_sections"] = found_sections

        # At least 2 of the 4 sections should be present
        section_count = sum(1 for found in found_sections.values() if found)
        details["section_count"] = section_count

        if section_count < 2:
            reasons.append(
                "Resume must contain at least 2 of these sections: "
                "experience, education, skills, or summary"
            )

        # Check 3: Quality indicators
        has_email = self._has_email(text)
        has_phone = self._has_phone(text)
        details["has_email"] = has_email
        details["has_phone"] = has_phone

        if not has_email and not has_phone:
            warnings.append(
                "Resume should contain contact information "
                "(email or phone number)"
            )

        # Check 4: Entropy check
        entropy_score = self._calculate_entropy(text)
        details["entropy_score"] = round(entropy_score, 4)

        if entropy_score < MIN_ENTROPY_THRESHOLD:
            reasons.append(
                f"Resume appears to be gibberish or low quality "
                f"(entropy: {entropy_score:.2f})"
            )

        # Check 5: Check for name section (heuristic)
        has_name_section = self._has_name_section(text)
        details["has_name_section"] = has_name_section

        if not has_name_section:
            warnings.append(
                "Resume should include a name or header section"
            )

        # Check 6: Reasonable uniqueness
        if len(set(words)) < len(words) * 0.2:  # Less than 20% unique words
            warnings.append(
                "Resume has many repeated words, which may indicate poor formatting"
            )

        # Build final result
        if reasons:
            reason = " AND ".join(reasons)
            is_valid = False
        else:
            reason = "Resume passed all validation checks"
            is_valid = True

        logger.info(
            f"Resume validation: is_valid={is_valid}, word_count={word_count}, "
            f"sections_found={section_count}"
        )

        return ValidationResult(
            is_valid=is_valid,
            reason=reason,
            details=details,
            warnings=warnings
        )

    def _calculate_entropy(self, text: str) -> float:
        """
        Calculate Shannon entropy of text to detect gibberish.
        Higher entropy = more diverse characters = less likely gibberish.

        Args:
            text: Text to analyze

        Returns:
            Entropy score
        """
        if not text:
            return 0.0

        # Count character frequencies
        char_counts = Counter(text.lower())
        text_length = len(text)

        # Calculate Shannon entropy
        entropy = 0.0
        for count in char_counts.values():
            probability = count / text_length
            if probability > 0:
                entropy -= probability * math.log2(probability)

        return entropy

    def _has_email(self, text: str) -> bool:
        """Check if text contains an email address."""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return bool(re.search(email_pattern, text))

    def _has_phone(self, text: str) -> bool:
        """Check if text contains a phone number."""
        phone_patterns = [
            r'\+?1?\s*\(?[0-9]{3}\)?[.\s-]?[0-9]{3}[.\s-]?[0-9]{4}',
            r'[0-9]{3}[.\s-]?[0-9]{3}[.\s-]?[0-9]{4}',
            r'\+[0-9]{1,3}\s?[0-9]{1,14}'
        ]
        for pattern in phone_patterns:
            if re.search(pattern, text):
                return True
        return False

    def _has_name_section(self, text: str) -> bool:
        """
        Heuristic check for name/header section.
        Checks if there are capitalized words at the beginning.
        """
        lines = text.split('\n')
        if not lines:
            return False

        first_line = lines[0].strip()
        # Check if first line has capitalized words (typical for name/header)
        words = first_line.split()
        if not words:
            return False

        # Count capitalized words
        capitalized = sum(1 for word in words if word[0].isupper() if word)
        return capitalized >= 1


# Convenience functions for direct use
def validate_job_description(text: str) -> ValidationResult:
    """
    Convenience function to validate a job description.

    Args:
        text: Job description text to validate

    Returns:
        ValidationResult with validation status
    """
    validator = InputValidator()
    return validator.validate_job_description(text)


def validate_resume_upload(text: str) -> ValidationResult:
    """
    Convenience function to validate a resume upload.

    Args:
        text: Resume text to validate

    Returns:
        ValidationResult with validation status
    """
    validator = InputValidator()
    return validator.validate_resume_upload(text)

"""
Metadata extraction module for extracting structured information from resume text.
Uses LLM to intelligently extract experience, skills, education, and role information.
"""
import json
import logging
from typing import Dict, List, Any, Optional
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

from src.core.config import settings

logger = logging.getLogger(__name__)


# Define valid metadata values
VALID_EXPERIENCE_LEVELS = {"entry", "mid", "senior", "lead"}
VALID_EDUCATION_LEVELS = {"high_school", "bachelors", "masters", "phd", "unknown"}
VALID_ROLE_CATEGORIES = {
    "backend", "frontend", "full_stack", "data_science", "devops",
    "cloud_engineer", "ml_engineer", "qa_engineer", "product_manager",
    "solutions_architect", "security_engineer", "other"
}

# Default metadata when extraction fails
DEFAULT_METADATA = {
    "experience_years": 0,
    "experience_level": "entry",
    "education": "unknown",
    "top_skills": [],
    "role_category": "other"
}


class MetadataExtractor:
    """
    Extracts structured metadata from resume text using an LLM.
    """

    def __init__(self, model_name: Optional[str] = None, temperature: float = 0.1):
        """
        Initialize the MetadataExtractor.

        Args:
            model_name: LLM model to use (default from config)
            temperature: Temperature for LLM (lower = more deterministic)
        """
        self.model_name = model_name or settings.OPENAI_LLM_MODEL
        self.temperature = temperature

        # Initialize the LLM
        self.llm = ChatOpenAI(
            model_name=self.model_name,
            temperature=temperature,
            api_key=settings.OPENAI_API_KEY
        )

        logger.info(f"MetadataExtractor initialized with model: {self.model_name}")

    def extract_metadata(self, resume_text: str) -> Dict[str, Any]:
        """
        Extract structured metadata from resume text.

        Args:
            resume_text: The resume text to analyze

        Returns:
            Dictionary with keys:
            - experience_years: int (estimated total years)
            - experience_level: str (entry|mid|senior|lead)
            - education: str (high_school|bachelors|masters|phd|unknown)
            - top_skills: list of up to 10 skills
            - role_category: str (backend|frontend|full_stack|data_science|devops|...)
        """
        if not isinstance(resume_text, str) or not resume_text.strip():
            logger.warning("Empty or invalid resume text provided")
            return DEFAULT_METADATA.copy()

        try:
            # Create the extraction prompt
            prompt = self._create_extraction_prompt(resume_text)

            # Call the LLM
            response = self.llm.invoke([
                SystemMessage(content=self._get_system_prompt()),
                HumanMessage(content=prompt)
            ])

            # Parse and validate the response
            metadata = self._parse_response(response.content)

            logger.info(f"Successfully extracted metadata from resume")
            return metadata

        except Exception as e:
            logger.error(f"Error extracting metadata: {str(e)}")
            return DEFAULT_METADATA.copy()

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the LLM."""
        return """You are an expert resume analyzer with deep knowledge of job markets,
technology stacks, and career progression. Your task is to extract structured metadata
from resumes in JSON format. Always respond with valid JSON only, no additional text.

Be accurate and conservative in your estimates. If information is unclear, use the most
reasonable default value from the allowed options."""

    def _create_extraction_prompt(self, resume_text: str) -> str:
        """
        Create the extraction prompt for the LLM.

        Args:
            resume_text: The resume text to analyze

        Returns:
            Formatted prompt string
        """
        prompt = f"""Analyze the following resume and extract structured metadata in JSON format.

RESUME TEXT:
{resume_text}

Extract and return ONLY a valid JSON object (no other text) with the following structure:
{{
    "experience_years": <integer, estimated total years of professional experience>,
    "experience_level": <one of: "entry" (0-2 years), "mid" (2-5 years), "senior" (5-10 years), "lead" (10+ years)>,
    "education": <highest degree: "high_school", "bachelors", "masters", "phd", or "unknown">,
    "top_skills": <list of up to 10 most relevant technical skills as strings>,
    "role_category": <primary role category: "backend", "frontend", "full_stack", "data_science", "devops", "cloud_engineer", "ml_engineer", "qa_engineer", "product_manager", "solutions_architect", "security_engineer", or "other">
}}

Guidelines:
- experience_years: Count total years mentioned or infer from job history. Minimum 0.
- experience_level: Map experience_years to the appropriate level.
- education: Extract the highest degree explicitly mentioned or infer from context.
- top_skills: Identify the most frequently mentioned or important technical skills. Include programming languages, frameworks, tools, and technologies.
- role_category: Determine the primary technical role from job titles and skills. If multiple categories apply, choose the primary one.

Ensure all values are valid according to the schema above. Return ONLY the JSON object."""

        return prompt

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse and validate the LLM response.

        Args:
            response_text: Raw response from the LLM

        Returns:
            Validated metadata dictionary
        """
        try:
            # Try to extract JSON from the response
            # Handle case where LLM might include extra text
            json_str = response_text.strip()

            # If response contains markdown code blocks, extract JSON
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()

            # Parse JSON
            metadata = json.loads(json_str)

            # Validate and clean the metadata
            validated = self._validate_metadata(metadata)

            return validated

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {str(e)}")
            logger.debug(f"Response was: {response_text}")
            return DEFAULT_METADATA.copy()
        except Exception as e:
            logger.error(f"Error parsing response: {str(e)}")
            return DEFAULT_METADATA.copy()

    def _validate_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and clean extracted metadata.

        Args:
            metadata: Raw metadata dictionary from LLM

        Returns:
            Validated metadata dictionary
        """
        validated = DEFAULT_METADATA.copy()

        try:
            # Validate experience_years
            if "experience_years" in metadata:
                years = int(metadata.get("experience_years", 0))
                validated["experience_years"] = max(0, min(years, 100))  # Clamp 0-100

            # Validate experience_level
            if "experience_level" in metadata:
                level = str(metadata.get("experience_level", "entry")).lower().strip()
                if level in VALID_EXPERIENCE_LEVELS:
                    validated["experience_level"] = level
                else:
                    # Infer from years if level is invalid
                    years = validated["experience_years"]
                    if years <= 2:
                        validated["experience_level"] = "entry"
                    elif years <= 5:
                        validated["experience_level"] = "mid"
                    elif years <= 10:
                        validated["experience_level"] = "senior"
                    else:
                        validated["experience_level"] = "lead"

            # Validate education
            if "education" in metadata:
                edu = str(metadata.get("education", "unknown")).lower().strip()
                if edu in VALID_EDUCATION_LEVELS:
                    validated["education"] = edu
                else:
                    validated["education"] = "unknown"

            # Validate top_skills
            if "top_skills" in metadata:
                skills = metadata.get("top_skills", [])
                if isinstance(skills, list):
                    # Take up to 10 skills, clean them
                    validated["top_skills"] = [
                        str(skill).strip()
                        for skill in skills[:10]
                        if isinstance(skill, str) and skill.strip()
                    ]
                else:
                    validated["top_skills"] = []

            # Validate role_category
            if "role_category" in metadata:
                role = str(metadata.get("role_category", "other")).lower().strip()
                if role in VALID_ROLE_CATEGORIES:
                    validated["role_category"] = role
                else:
                    # Try to match if similar
                    role_clean = role.replace("_", " ").replace(" ", "_")
                    if role_clean in VALID_ROLE_CATEGORIES:
                        validated["role_category"] = role_clean
                    else:
                        validated["role_category"] = "other"

            logger.debug(f"Metadata validated: {validated}")
            return validated

        except Exception as e:
            logger.error(f"Error validating metadata: {str(e)}")
            return DEFAULT_METADATA.copy()

    def extract_batch(
        self,
        resumes: List[Dict[str, str]],
        resume_text_key: str = "resume_text"
    ) -> List[Dict[str, Any]]:
        """
        Extract metadata from multiple resumes.

        Args:
            resumes: List of resume dictionaries
            resume_text_key: Key in each dict containing the resume text

        Returns:
            List of metadata dictionaries
        """
        metadata_list = []
        failed_count = 0

        for idx, resume in enumerate(resumes):
            try:
                if not isinstance(resume, dict):
                    logger.warning(f"Skipping item {idx}: not a dictionary")
                    failed_count += 1
                    continue

                resume_text = resume.get(resume_text_key, "")
                if not resume_text:
                    logger.warning(f"Skipping item {idx}: no resume text found")
                    failed_count += 1
                    continue

                # Extract metadata for this resume
                metadata = self.extract_metadata(resume_text)

                # Add the original ID if available
                if "id" in resume:
                    metadata["id"] = resume["id"]

                metadata_list.append(metadata)

            except Exception as e:
                logger.error(f"Error processing resume at index {idx}: {str(e)}")
                failed_count += 1
                continue

        logger.info(
            f"Extracted metadata from {len(metadata_list)}/{len(resumes)} resumes. "
            f"Failed: {failed_count}"
        )

        return metadata_list


# Convenience function for single resume extraction
def extract_metadata(resume_text: str, model_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to extract metadata from a single resume.

    Args:
        resume_text: The resume text to analyze
        model_name: Optional custom model name

    Returns:
        Metadata dictionary
    """
    extractor = MetadataExtractor(model_name=model_name)
    return extractor.extract_metadata(resume_text)


def extract_batch_metadata(
    resumes: List[Dict[str, str]],
    model_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Convenience function to extract metadata from multiple resumes.

    Args:
        resumes: List of resume dictionaries with 'resume_text' key
        model_name: Optional custom model name

    Returns:
        List of metadata dictionaries
    """
    extractor = MetadataExtractor(model_name=model_name)
    return extractor.extract_batch(resumes)

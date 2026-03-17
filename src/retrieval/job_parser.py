"""
Job description parsing module for extracting structured information from job postings.
Uses LLM to intelligently extract skills, experience level, role category, and summary.
"""
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from functools import lru_cache
import re
from pydantic import BaseModel, Field, validator
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

from src.core.config import settings

logger = logging.getLogger(__name__)


# Pydantic model for parsed job descriptions
class ParsedJobDescription(BaseModel):
    """
    Structured representation of a parsed job description.
    """
    required_skills: List[str] = Field(
        ...,
        description="List of required technical skills"
    )
    preferred_skills: List[str] = Field(
        default_factory=list,
        description="List of preferred/nice-to-have skills"
    )
    experience_level: str = Field(
        ...,
        description="Required experience level: entry|mid|senior|lead"
    )
    role_category: str = Field(
        ...,
        description="Primary role category (e.g., backend, frontend, data_science)"
    )
    job_summary: str = Field(
        ...,
        description="One sentence summary of the job"
    )

    @validator("experience_level")
    def validate_experience_level(cls, v):
        """Validate experience level is one of the allowed values."""
        valid_levels = {"entry", "mid", "senior", "lead"}
        if v.lower() not in valid_levels:
            raise ValueError(f"experience_level must be one of {valid_levels}")
        return v.lower()

    @validator("required_skills", "preferred_skills", pre=True)
    def validate_skills(cls, v):
        """Ensure skills are clean strings."""
        if not isinstance(v, list):
            return []
        return [str(skill).strip() for skill in v if isinstance(skill, str) and skill.strip()]

    @validator("job_summary")
    def validate_summary(cls, v):
        """Validate job summary is not empty."""
        if not isinstance(v, str) or not v.strip():
            raise ValueError("job_summary must be a non-empty string")
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "required_skills": ["Python", "Django", "PostgreSQL", "Docker"],
                "preferred_skills": ["Kubernetes", "AWS", "GraphQL"],
                "experience_level": "senior",
                "role_category": "backend",
                "job_summary": "Senior backend engineer to build scalable microservices using Python and cloud technologies."
            }
        }


# Default parsed job description when extraction fails
DEFAULT_PARSED_JOB = ParsedJobDescription(
    required_skills=["Not extracted"],
    preferred_skills=[],
    experience_level="mid",
    role_category="other",
    job_summary="Job description could not be processed."
)


class JobDescriptionParser:
    """
    Parses job descriptions using an LLM to extract structured information.
    """

    def __init__(self, model_name: Optional[str] = None, temperature: float = 0.1):
        """
        Initialize the JobDescriptionParser.

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

        logger.info(f"JobDescriptionParser initialized with model: {self.model_name}")

    def parse(self, jd_text: str) -> ParsedJobDescription:
        """
        Parse a job description and extract structured information.

        Args:
            jd_text: The job description text to parse

        Returns:
            ParsedJobDescription model with extracted information
        """
        if not isinstance(jd_text, str) or not jd_text.strip():
            logger.warning("Empty or invalid job description text provided")
            return DEFAULT_PARSED_JOB

        try:
            # Create the parsing prompt
            prompt = self._create_parsing_prompt(jd_text)

            # Call the LLM
            response = self.llm.invoke([
                SystemMessage(content=self._get_system_prompt()),
                HumanMessage(content=prompt)
            ])

            # Parse and validate the response
            parsed = self._parse_response(response.content)
            parsed.required_skills = _expand_skills(
                text=jd_text,
                extracted_skills=parsed.required_skills,
                role_category=parsed.role_category,
            )

            logger.info("Successfully parsed job description")
            return parsed

        except Exception as e:
            logger.error(f"Error parsing job description: {str(e)}")
            return DEFAULT_PARSED_JOB

    def parse_with_token_usage(self, jd_text: str) -> Tuple[ParsedJobDescription, Dict[str, int]]:
        """
        Parse a job description and return token usage if available.

        Returns:
            (ParsedJobDescription, token_usage_dict)
        token_usage_dict shape (when available):
            {"prompt_tokens": int, "completion_tokens": int, "total_tokens": int}
        """
        if not isinstance(jd_text, str) or not jd_text.strip():
            return DEFAULT_PARSED_JOB, {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

        try:
            prompt = self._create_parsing_prompt(jd_text)

            response = self.llm.invoke([
                SystemMessage(content=self._get_system_prompt()),
                HumanMessage(content=prompt)
            ])

            parsed = self._parse_response(response.content)
            parsed.required_skills = _expand_skills(
                text=jd_text,
                extracted_skills=parsed.required_skills,
                role_category=parsed.role_category,
            )
            token_usage = self._extract_token_usage(response)

            logger.info("Successfully parsed job description")
            return parsed, token_usage

        except Exception as e:
            logger.error(f"Error parsing job description: {str(e)}")
            return DEFAULT_PARSED_JOB, {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    def _extract_token_usage(self, response: Any) -> Dict[str, int]:
        """
        Best-effort extraction of token usage from a LangChain response.
        """
        usage: Dict[str, Any] = {}

        try:
            # Common LangChain places for token usage metadata
            if hasattr(response, "response_metadata") and isinstance(response.response_metadata, dict):
                md = response.response_metadata
                usage = md.get("token_usage") or md.get("usage") or {}
            elif hasattr(response, "usage_metadata") and isinstance(response.usage_metadata, dict):
                usage = response.usage_metadata
            elif hasattr(response, "additional_kwargs") and isinstance(response.additional_kwargs, dict):
                usage = response.additional_kwargs.get("token_usage") or response.additional_kwargs.get("usage") or {}
        except Exception:
            usage = {}

        def _to_int(v: Any) -> int:
            try:
                return int(v)
            except Exception:
                return 0

        prompt_tokens = _to_int(usage.get("prompt_tokens"))
        completion_tokens = _to_int(usage.get("completion_tokens"))
        total_tokens = _to_int(usage.get("total_tokens")) or (prompt_tokens + completion_tokens)

        return {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
        }

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the LLM."""
        return """You are an expert recruiter and technical hiring specialist with deep knowledge
of job markets, technical roles, and skill requirements. Your task is to parse job descriptions
and extract structured information in JSON format. Always respond with valid JSON only, no additional text.

Be thorough and accurate. Extract all explicitly mentioned skills and requirements.
For preferred skills, identify nice-to-have technologies mentioned.
Infer experience level from job requirements and responsibilities.
Determine the primary role category based on the job description."""

    def _create_parsing_prompt(self, jd_text: str) -> str:
        """
        Create the parsing prompt for the LLM.

        Args:
            jd_text: The job description text to parse

        Returns:
            Formatted prompt string
        """
        jd_compact = jd_text.strip()
        if len(jd_compact) > 2000:
            jd_compact = jd_compact[:2000].rstrip() + "\n\n[TRUNCATED]"

        prompt = f"""Parse the following job description and extract structured information in JSON format.

JOB DESCRIPTION:
{jd_compact}

Extract and return ONLY a valid JSON object (no other text) with the following structure:
{{
    "required_skills": <list of required technical skills as strings>,
    "preferred_skills": <list of preferred/nice-to-have skills as strings>,
    "experience_level": <one of: "entry" (0-2 yrs), "mid" (2-5 yrs), "senior" (5-10 yrs), "lead" (10+ yrs)>,
    "role_category": <primary role category: "backend", "frontend", "full_stack", "data_science", "devops", "cloud_engineer", "ml_engineer", "qa_engineer", "product_manager", "solutions_architect", "security_engineer", or "other">,
    "job_summary": <one sentence summary of the job>
}}

Guidelines:
- required_skills: Extract ALL explicitly required technical skills, frameworks, languages, and tools. Be comprehensive.
- preferred_skills: Extract skills that are optional, nice-to-have, or mentioned as desirable.
- experience_level: Infer from years mentioned, seniority level, and responsibilities. Default to "mid" if unclear.
- role_category: Choose the primary technical role. If multiple categories apply, choose the most prominent one.
- job_summary: Create a concise one-sentence summary that captures the essence of the role.

Ensure all values are valid according to the schema above. Return ONLY the JSON object."""

        return prompt

    def _parse_response(self, response_text: str) -> ParsedJobDescription:
        """
        Parse and validate the LLM response.

        Args:
            response_text: Raw response from the LLM

        Returns:
            ParsedJobDescription model instance
        """
        try:
            # Try to extract JSON from the response
            json_str = response_text.strip()

            # If response contains markdown code blocks, extract JSON
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()

            # Parse JSON
            data = json.loads(json_str)

            # Validate and create Pydantic model
            parsed = ParsedJobDescription(**data)

            logger.debug(f"Successfully parsed job description")
            return parsed

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {str(e)}")
            logger.debug(f"Response was: {response_text}")
            return DEFAULT_PARSED_JOB
        except ValueError as e:
            logger.error(f"Validation error: {str(e)}")
            return DEFAULT_PARSED_JOB
        except Exception as e:
            logger.error(f"Error parsing response: {str(e)}")
            return DEFAULT_PARSED_JOB

    def parse_batch(
        self,
        job_descriptions: List[Dict[str, str]],
        jd_text_key: str = "description"
    ) -> List[ParsedJobDescription]:
        """
        Parse multiple job descriptions.

        Args:
            job_descriptions: List of job description dictionaries
            jd_text_key: Key in each dict containing the job description text

        Returns:
            List of ParsedJobDescription instances
        """
        parsed_list = []
        failed_count = 0

        for idx, job in enumerate(job_descriptions):
            try:
                if not isinstance(job, dict):
                    logger.warning(f"Skipping item {idx}: not a dictionary")
                    failed_count += 1
                    continue

                jd_text = job.get(jd_text_key, "")
                if not jd_text:
                    logger.warning(f"Skipping item {idx}: no job description text found")
                    failed_count += 1
                    continue

                # Parse this job description
                parsed = self.parse(jd_text)
                parsed_list.append(parsed)

            except Exception as e:
                logger.error(f"Error processing job at index {idx}: {str(e)}")
                failed_count += 1
                continue

        logger.info(
            f"Parsed {len(parsed_list)}/{len(job_descriptions)} job descriptions. "
            f"Failed: {failed_count}"
        )

        return parsed_list


# ============================================================================
# Fast (non-LLM) parser
# ============================================================================

_SKILL_EXPANSION_MAP: Dict[str, List[str]] = {
    # High-level concepts -> related skill keywords.
    # Keep values short and generic so they work across datasets.
    "backend": ["api", "rest", "server", "database", "microservices"],
    "frontend": ["ui", "ux", "react", "html", "css"],
    "data analysis": ["python", "pandas", "numpy", "sql"],
    "devops": ["docker", "kubernetes", "ci/cd", "cloud"],
    "hr": ["recruitment", "employee relations", "performance management", "hr policy", "hris", "payroll", "onboarding", "compensation", "benefits"],
}

_SKILL_EXPANSION_TRIGGERS: Dict[str, List[str]] = {
    # If any of these words/phrases are present, we expand the concept into related skills.
    # Keep triggers broad but reasonably specific to avoid false positives.
    "backend": [
        "backend", "back-end", "back end",
        "api", "apis", "rest", "microservice", "microservices",
        "server", "database", "databases", "backend systems",
    ],
    "frontend": [
        "frontend", "front-end", "front end",
        "user experience", "ux", "ui", "user interface", "interfaces", "interface",
        "web application", "web applications", "web app", "web apps",
        "usability", "accessibility", "responsive", "interaction", "interactions",
        "design system", "design systems",
    ],
    "data analysis": [
        "data analysis", "analyze data", "analytics", "dashboards",
        "insights", "data-driven", "data driven",
    ],
    "devops": [
        "devops", "dev ops",
        "deployment", "deployments", "release", "releases",
        "infrastructure", "ci/cd", "pipeline", "pipelines", "monitoring",
        "containers", "containerization", "docker", "kubernetes", "cloud",
    ],
    "hr": [
        "hr", "human resources", "people operations", "people ops",
        "recruitment", "recruiting", "talent acquisition", "hiring", "hire",
        "employee relations", "employee engagement", "performance management",
        "onboarding", "offboarding", "payroll", "compensation", "benefits",
        "hr policy", "hris",
    ],
}

_SKILL_PHRASES: List[str] = [
    # Languages
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "golang", "ruby", "php", "scala", "r",
    # Data/DB
    "sql", "postgresql", "mysql", "sqlite", "mongodb", "redis", "elasticsearch", "snowflake", "bigquery",
    # Web/frameworks
    "django", "flask", "fastapi", "spring", "node", "nodejs", "express", "react", "angular", "vue",
    # DevOps/cloud
    "docker", "kubernetes", "aws", "gcp", "azure", "terraform", "ci/cd", "jenkins", "github actions",
    # Data science / ML
    "machine learning", "deep learning", "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy",
    "data analysis", "statistical modeling", "nlp", "computer vision",
    # Other common tools
    "git", "linux", "rest", "rest api", "microservices", "grpc",
    # Non-tech / business / HR / operations
    "recruitment", "talent acquisition", "onboarding", "employee relations", "performance management",
    "compensation", "benefits", "payroll", "hr policy", "hris", "training", "coaching",
    "stakeholder management", "project management", "program management", "process improvement",
    "operations", "customer service", "client management", "sales", "account management",
    "marketing", "content", "social media", "seo", "campaigns", "digital media",
    "public relations", "media relations", "press release",
    "budgeting", "forecasting", "financial reporting", "accounting", "excel", "reconciliation", "audit", "tax",
    "banking", "loan processing", "underwriting", "kyc", "aml", "credit analysis", "financial products",
    "curriculum development", "classroom management", "lesson planning", "student assessment",
    "lead generation", "crm", "target achievement", "quota", "pipeline",
    "autocad", "site supervision", "construction planning",
    "compliance",
    "communication", "collaboration", "leadership", "problem solving", "time management",
    # Healthcare / clinical
    "patient care", "clinical", "treatment planning", "care coordination", "medical procedures",
    "hospital management", "hipaa", "healthcare compliance",
    # Fitness / wellness
    "fitness", "personal trainer", "strength training", "nutrition",
    # Agriculture
    "agriculture", "farming", "crop", "livestock",
    # Automotive
    "automotive", "vehicle maintenance", "engine diagnostics",
    # Aviation
    "aviation", "flight operations", "aircraft maintenance",
]

# Dataset category coverage:
# Return one of these canonical, API-safe role_category values (underscored):
# - hr, designer, information_technology, teacher, advocate, business_development,
#   healthcare, fitness, agriculture, bpo, sales, consultant, digital_media,
#   automobile, chef, finance, apparel, engineering, accountant, construction,
#   public_relations, banking, arts, aviation, other
_CATEGORY_PRIORITY: List[str] = [
    "information_technology",
    "healthcare",
    "finance",
    "banking",
    "accountant",
    "engineering",
    "construction",
    "hr",
    "teacher",
    "sales",
    "business_development",
    "consultant",
    "designer",
    "digital_media",
    "public_relations",
    "automobile",
    "chef",
    "apparel",
    "fitness",
    "agriculture",
    "bpo",
    "advocate",
    "arts",
    "aviation",
]

_DATASET_CATEGORY_RULES: Dict[str, Dict[str, List[str]]] = {
    "hr": {
        "strong": [
            r"\bhuman resources\b",
            r"\bhris\b",
            r"\bpayroll\b",
            r"\bonboarding\b",
            r"\bemployee relations\b",
            r"\bperformance management\b",
            r"\bcompensation\b",
            r"\bbenefits\b",
            r"\btalent acquisition\b",
        ],
        "weak": [
            r"\brecruitment\b",
            r"\brecruiting\b",
            r"\bhiring\b",
            r"\bpeople ops\b|\bpeople operations\b",
            r"\bhr\b",
            r"\bpolic(y|ies)\b",
        ],
    },
    "designer": {
        "strong": [
            r"\bux\b",
            r"\bui\b",
            r"\bproduct designer\b",
            r"\bgraphic designer\b",
            r"\bfigma\b",
            r"\bphotoshop\b",
            r"\billustrator\b",
        ],
        "weak": [
            r"\bwireframe(s)?\b",
            r"\bprototype(s)?\b",
            r"\bdesign system(s)?\b",
            r"\btypography\b",
            r"\bbranding\b",
        ],
    },
    "information_technology": {
        "strong": [
            r"\bsoftware\b",
            r"\bdeveloper\b",
            r"\bfull[\s-]?stack\b",
            r"\bbackend\b|\bback[\s-]?end\b",
            r"\bfrontend\b|\bfront[\s-]?end\b",
            r"\bapi(s)?\b",
            r"\brest\b",
            r"\bmicroservice(s)?\b",
            r"\bdocker\b",
            r"\bkubernetes\b",
            r"\bpython\b",
            r"\bjava\b",
            r"\bjavascript\b|\btypescript\b",
            r"\breact\b",
            r"\bmachine learning\b|\bdata scientist\b|\btensorflow\b|\bpytorch\b",
        ],
        "weak": [
            r"\bengineer\b",
            r"\bdatabase(s)?\b",
            r"\bserver(s)?\b",
            r"\bsql\b",
            r"\bcloud\b|\baws\b|\bazure\b|\bgcp\b",
            r"\bdevops\b|\bci/cd\b|\bpipeline(s)?\b",
        ],
    },
    "teacher": {
        "strong": [
            r"\bteacher\b",
            r"\bclassroom\b",
            r"\bcurriculum\b",
            r"\blesson plan(s)?\b",
            r"\bstudent assessment\b|\bassessment\b",
        ],
        "weak": [
            r"\beducation\b",
            r"\bschool\b",
            r"\binstruction\b|\binstructional\b",
            r"\blearning\b",
        ],
    },
    "advocate": {
        "strong": [
            r"\badvocate\b",
            r"\blitigation\b",
            r"\bcourt\b",
            r"\bcontracts?\b",
            r"\blegal\b",
        ],
        "weak": [
            r"\bcase management\b",
            r"\bclient advocacy\b",
            r"\bparalegal\b",
        ],
    },
    "business_development": {
        "strong": [
            r"\bbusiness development\b",
            r"\bstrategic partnership(s)?\b",
            r"\bpartnership(s)?\b",
        ],
        "weak": [
            r"\bgrowth\b",
            r"\bmarket expansion\b",
            r"\baccount management\b",
        ],
    },
    "healthcare": {
        "strong": [
            r"\bpatient care\b",
            r"\bclinical\b",
            r"\bhospital\b",
            r"\bhipaa\b",
            r"\bmedical\b",
            r"\bnurse\b|\bnursing\b",
            r"\bphysician\b|\bdoctor\b",
            r"\btreatment\b|\btreatment planning\b",
        ],
        "weak": [
            r"\bclinic(al)?\b",
            r"\bcare coordination\b",
            r"\bmedical procedures?\b",
            r"\behr\b|\bemr\b",
            r"\bhealthcare\b|\bhealth care\b",
        ],
    },
    "fitness": {
        "strong": [
            r"\bfitness\b",
            r"\bpersonal trainer\b",
            r"\bworkout\b",
            r"\bgym\b",
            r"\bstrength training\b",
            r"\bnutrition\b",
        ],
        "weak": [
            r"\bwellness\b",
            r"\bcoaching\b",
        ],
    },
    "agriculture": {
        "strong": [
            r"\bagriculture\b",
            r"\bfarm(ing)?\b",
            r"\bcrop(s)?\b",
            r"\blivestock\b",
            r"\bhorticulture\b",
        ],
        "weak": [
            r"\birrigation\b",
            r"\bagronomy\b",
        ],
    },
    "bpo": {
        "strong": [
            r"\bbpo\b",
            r"\bcall center\b",
            r"\bprocess outsourcing\b",
        ],
        "weak": [
            r"\bcustomer support\b",
            r"\bback office\b",
            r"\bvoice process\b",
        ],
    },
    "sales": {
        "strong": [
            r"\bsales\b",
            r"\blead generation\b",
            r"\bcrm\b",
            r"\bquota\b|\btarget(s)?\b",
            r"\bclosing\b",
        ],
        "weak": [
            r"\bclient relationship(s)?\b",
            r"\bnegotiation\b",
            r"\bpipeline\b",
        ],
    },
    "consultant": {
        "strong": [
            r"\bconsultant\b",
            r"\bconsulting\b",
            r"\badvisory\b",
        ],
        "weak": [
            r"\bstrategy\b",
            r"\bstakeholder(s)?\b",
            r"\banalysis\b",
        ],
    },
    "digital_media": {
        "strong": [
            r"\bdigital media\b",
            r"\bsocial media\b",
            r"\bcontent\b",
            r"\bseo\b|\bsem\b",
            r"\bcampaign(s)?\b",
        ],
        "weak": [
            r"\bmarketing\b",
            r"\bengagement\b",
        ],
    },
    "automobile": {
        "strong": [
            r"\bautomobile\b|\bautomotive\b",
            r"\bvehicle(s)?\b",
            r"\bmechanic\b",
            r"\bengine diagnostics?\b",
        ],
        "weak": [
            r"\bmaintenance\b",
            r"\bservice advisor\b",
        ],
    },
    "chef": {
        "strong": [
            r"\bchef\b",
            r"\bkitchen\b",
            r"\bculinary\b",
            r"\bmenu planning\b|\bmenu\b",
            r"\bfood safety\b",
        ],
        "weak": [
            r"\bcooking\b",
            r"\brestaurant\b",
        ],
    },
    "finance": {
        "strong": [
            r"\bfinancial reporting\b",
            r"\bbudget(ing)?\b",
            r"\bforecast(ing)?\b",
            r"\bp&l\b|\bprofit and loss\b",
            r"\bvariance\b",
            r"\bgaap\b|\bifrs\b",
            r"\bfinancial analyst\b",
        ],
        "weak": [
            r"\bexcel\b",
            r"\bfinancial analysis\b|\banalysis\b",
            r"\breconciliation(s)?\b",
            r"\baccounting\b",
        ],
    },
    "apparel": {
        "strong": [
            r"\bapparel\b",
            r"\bgarment(s)?\b",
            r"\bfashion\b",
            r"\btextile(s)?\b",
            r"\bmerchandising\b",
        ],
        "weak": [
            r"\bfabric(s)?\b",
            r"\bpattern(s)?\b",
            r"\bretail\b",
        ],
    },
    "engineering": {
        "strong": [
            r"\bcivil engineer\b",
            r"\bmechanical engineer\b",
            r"\belectrical engineer\b",
            r"\bautocad\b",
            r"\bsite supervision\b",
            r"\bconstruction planning\b",
        ],
        "weak": [
            r"\bengineering\b",
            r"\bengineering drawings?\b|\bdrawings?\b",
        ],
    },
    "accountant": {
        "strong": [
            r"\baccountant\b",
            r"\baccounts payable\b|\bap\b",
            r"\baccounts receivable\b|\bar\b",
            r"\bbookkeeping\b",
            r"\bjournal entries?\b|\bjournal entry\b",
            r"\btax\b",
        ],
        "weak": [
            r"\bledger\b",
            r"\breconciliation(s)?\b",
            r"\baudit\b",
        ],
    },
    "construction": {
        "strong": [
            r"\bconstruction\b",
            r"\bsite supervision\b",
            r"\bcontractor(s)?\b",
            r"\bproject site\b|\bsite\b",
            r"\bconstruction safety\b|\bsafety\b",
        ],
        "weak": [
            r"\bforeman\b",
            r"\bbuilding\b",
        ],
    },
    "public_relations": {
        "strong": [
            r"\bpublic relations\b",
            r"\bmedia relations\b",
            r"\bpress release(s)?\b",
        ],
        "weak": [
            r"\bcommunications?\b",
            r"\bbrand reputation\b",
        ],
    },
    "banking": {
        "strong": [
            r"\bbanking\b|\bbanker\b",
            r"\bloan processing\b|\bloans?\b",
            r"\bunderwriting\b",
            r"\bkyc\b|\baml\b",
            r"\bteller\b|\bbranch\b",
            r"\bcredit analysis\b|\bcredit\b",
        ],
        "weak": [
            r"\bfinancial products?\b",
            r"\bdeposits?\b",
            r"\bcompliance\b",
            r"\bcustomer service\b",
        ],
    },
    "arts": {
        "strong": [
            r"\barts?\b",
            r"\bartist\b",
            r"\billustration\b",
            r"\bpainting\b",
            r"\bmusic\b",
            r"\btheatre\b|\btheater\b",
        ],
        "weak": [
            r"\bcreative\b",
        ],
    },
    "aviation": {
        "strong": [
            r"\baviation\b",
            r"\baircraft\b",
            r"\bflight operations\b",
            r"\bairline\b",
            r"\baircraft maintenance\b|\bmaintenance\b",
        ],
        "weak": [
            r"\bsafety compliance\b|\bcompliance\b",
        ],
    },
}

_DATASET_CATEGORY_REGEX: Dict[str, Dict[str, List[re.Pattern]]] = {
    cat: {
        "strong": [re.compile(p, re.IGNORECASE) for p in rules.get("strong", [])],
        "weak": [re.compile(p, re.IGNORECASE) for p in rules.get("weak", [])],
    }
    for cat, rules in _DATASET_CATEGORY_RULES.items()
}


def _expand_skills(text: str, extracted_skills: List[str], role_category: str = "") -> List[str]:
    """
    Expand high-level concepts in a job description into related skills.

    This improves semantic understanding when the job description uses broad terms
    (e.g., "backend") without listing specific technologies.

    - Detect high-level terms in the job text (case-insensitive)
    - Optionally use inferred role_category as an additional signal
    - Merge expanded skills + extracted skills
    - Avoid duplicates (case-insensitive), preserve order
    """
    text_lower = (text or "").lower()
    role_key = (role_category or "").strip().lower()

    out: List[str] = []
    seen: set[str] = set()

    def _push(skill: str) -> None:
        s = str(skill).strip()
        if not s:
            return
        key = s.lower()
        if key in seen:
            return
        out.append(s)
        seen.add(key)

    # Keep existing extraction as the primary signal.
    for s in (extracted_skills or []):
        _push(s)

    def _has_trigger(concept: str) -> bool:
        triggers = _SKILL_EXPANSION_TRIGGERS.get(concept, [])
        for t in triggers:
            tt = t.strip().lower()
            if not tt:
                continue

            # Short tokens like "ui"/"ux" should match as whole words.
            if len(tt) <= 2 and tt.isalnum():
                if re.search(rf"\b{re.escape(tt)}\b", text_lower):
                    return True
                continue

            if tt in text_lower:
                return True
        return False

    for concept, expansions in _SKILL_EXPANSION_MAP.items():
        if concept in text_lower or concept == role_key or _has_trigger(concept):
            for e in expansions:
                _push(e)

    return out


def _infer_experience_level(text_lower: str) -> str:
    if any(k in text_lower for k in ["intern", "entry level", "entry-level", "junior", "0-2 years", "0 to 2 years"]):
        return "entry"
    if any(k in text_lower for k in ["lead", "team lead", "tech lead", "10+ years", "10 years"]):
        return "lead"
    if any(k in text_lower for k in ["senior", "5+ years", "7+ years", "8+ years", "staff", "principal"]):
        return "senior"
    return "mid"


def _infer_role_category(text_lower: str) -> str:
    """
    Infer a dataset-aligned role category from free-form job description text.

    Goals:
    - Cover the 24 dataset categories with conservative rules
    - Prefer precision over forced classification (avoid false positives)
    - Keep "other" as a safe fallback when signals are ambiguous
    """
    text = (text_lower or "").strip()
    if not text:
        return "other"

    # Score each category using strong/weak keyword hits.
    scored: List[Tuple[int, int, str]] = []
    for cat, rules in _DATASET_CATEGORY_REGEX.items():
        strong_hits = sum(1 for rx in rules.get("strong", []) if rx.search(text))
        weak_hits = sum(1 for rx in rules.get("weak", []) if rx.search(text))
        score = (strong_hits * 2) + weak_hits
        if score > 0:
            scored.append((score, strong_hits, cat))

    if not scored:
        return "other"

    # Sort by score desc, then strong hits desc, then category priority.
    priority_rank = {c: i for i, c in enumerate(_CATEGORY_PRIORITY)}
    scored.sort(key=lambda t: (-t[0], -t[1], priority_rank.get(t[2], 10_000)))

    best_score, best_strong, best_cat = scored[0]
    second_score = scored[1][0] if len(scored) > 1 else -1

    # Require at least one strong signal OR multiple weak signals.
    # This prevents accidental classification from generic words like "analysis".
    if best_score < 2:
        return "other"

    # If ambiguity is high (tie or near-tie), fall back to "other" for safety.
    if second_score == best_score:
        return "other"
    if (best_score - second_score) == 1 and best_score < 4:
        return "other"

    return best_cat


def _extract_skills(text: str) -> List[str]:
    """
    Extract a conservative set of skills by matching common phrases.

    This is intentionally lightweight to keep /match fast even when OpenAI
    calls are disabled.
    """
    if not text:
        return []

    text_lower = text.lower()
    normalized = re.sub(r"[^a-z0-9+#/\\s]", " ", text_lower)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    padded = f" {normalized} "

    found: List[str] = []
    for phrase in _SKILL_PHRASES:
        p = phrase.lower().strip()
        if not p:
            continue

        token = f" {p} "
        if token in padded:
            found.append(phrase)
            continue

        if " " in p and p in normalized:
            found.append(phrase)
            continue

        if len(p) <= 2:
            if re.search(rf"\b{re.escape(p)}\b", normalized):
                found.append(phrase)

    deduped: List[str] = []
    seen = set()
    for s in found:
        key = s.lower()
        if key not in seen:
            deduped.append(s)
            seen.add(key)

    return deduped[:25]


_STOPWORDS = {
    "the", "and", "for", "with", "from", "that", "this", "will", "are", "you", "your", "our", "their",
    "have", "has", "had", "were", "was", "been", "being", "a", "an", "to", "of", "in", "on", "at", "as",
    "by", "or", "it", "is", "we", "they", "he", "she", "them", "us", "i", "my", "me", "role", "job",
    "candidate", "looking", "seeking", "position", "responsibilities", "requirements", "required",
    "preferred", "nice", "skills", "experience", "years", "work", "team", "strong", "ability", "knowledge",
}


def _extract_keywords_fallback(text: str) -> List[str]:
    """
    Last-resort keyword extraction to avoid returning placeholder skills like "Not extracted".

    This is intentionally simple (no external deps) and works for non-tech roles too.
    """
    if not text:
        return []

    normalized = re.sub(r"[^a-z0-9\s]", " ", text.lower())
    tokens = [t for t in normalized.split() if len(t) >= 4 and t not in _STOPWORDS]
    if not tokens:
        return []

    # Frequency-based top terms.
    freq: Dict[str, int] = {}
    for t in tokens:
        freq[t] = freq.get(t, 0) + 1

    # Prefer more specific words: (count desc, length desc)
    ranked = sorted(freq.items(), key=lambda kv: (kv[1], len(kv[0])), reverse=True)
    top = [w for w, _ in ranked[:12]]

    # De-dupe while preserving order.
    out: List[str] = []
    seen = set()
    for w in top:
        if w not in seen:
            out.append(w)
            seen.add(w)
    return out


@lru_cache(maxsize=256)
def _parse_job_description_fast_cached(jd_text: str) -> Dict[str, Any]:
    text = (jd_text or "").strip()
    text_lower = text.lower()

    summary = ""
    for line in text.splitlines():
        if line.strip():
            summary = line.strip()
            break
    if not summary:
        summary = (text[:160] + "...") if len(text) > 160 else text
    if len(summary) > 180:
        summary = summary[:180].rstrip() + "..."

    skills = _extract_skills(text)
    if not skills:
        skills = _extract_keywords_fallback(text)
    exp = _infer_experience_level(text_lower)
    role = _infer_role_category(text_lower)

    # Expand high-level concepts (e.g., "backend") into related skills.
    skills = _expand_skills(text=text, extracted_skills=skills, role_category=role)

    return {
        "required_skills": skills or ["general"],
        "preferred_skills": [],
        "experience_level": exp,
        "role_category": role,
        "job_summary": summary or "Job description could not be processed.",
    }


def parse_job_description_fast(jd_text: str) -> Tuple[ParsedJobDescription, Dict[str, int]]:
    """
    Fast, non-LLM job parser for low-latency matching.

    Returns a ParsedJobDescription plus a token_usage dict with zeros.
    """
    if not isinstance(jd_text, str) or not jd_text.strip():
        return DEFAULT_PARSED_JOB, {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    data = _parse_job_description_fast_cached(jd_text)
    try:
        return ParsedJobDescription(**data), {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    except Exception:
        return DEFAULT_PARSED_JOB, {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}


def parse_job_description(
    jd_text: str,
    model_name: Optional[str] = None
) -> Tuple[ParsedJobDescription, Dict[str, int]]:
    """
    Convenience function to parse a single job description.

    Args:
        jd_text: The job description text to parse
        model_name: Optional custom model name

    Returns:
        (ParsedJobDescription, token_usage_dict)
    """
    parser = JobDescriptionParser(model_name=model_name)
    return parser.parse_with_token_usage(jd_text)


def parse_job_descriptions_batch(
    job_descriptions: List[Dict[str, str]],
    model_name: Optional[str] = None
) -> List[ParsedJobDescription]:
    """
    Convenience function to parse multiple job descriptions.

    Args:
        job_descriptions: List of job description dicts with description text
        model_name: Optional custom model name

    Returns:
        List of ParsedJobDescription instances
    """
    parser = JobDescriptionParser(model_name=model_name)
    return parser.parse_batch(job_descriptions)

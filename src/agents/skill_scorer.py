"""
Skill scoring module for computing semantic skill overlap between candidates and jobs.
Uses sentence-transformers for semantic similarity matching with configurable thresholds.
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from pydantic import BaseModel, Field, validator
from sentence_transformers import SentenceTransformer, util

logger = logging.getLogger(__name__)

# Global SkillScorer instance to avoid repeatedly initializing SentenceTransformer
_global_skill_scorer: Optional["SkillScorer"] = None


class SkillScoreResult(BaseModel):
    """
    Result of skill overlap scoring between candidate and job requirements.
    """
    overall_score: float = Field(
        ...,
        ge=0,
        le=100,
        description="Overall weighted score (0-100): 70% required + 30% preferred"
    )
    required_match_pct: float = Field(
        ...,
        ge=0,
        le=100,
        description="Percentage of required skills matched"
    )
    preferred_match_pct: float = Field(
        ...,
        ge=0,
        le=100,
        description="Percentage of preferred skills matched"
    )
    matched_skills: List[str] = Field(
        default_factory=list,
        description="List of matched skills"
    )
    missing_required_skills: List[str] = Field(
        default_factory=list,
        description="Required skills not found in candidate skills"
    )
    missing_preferred_skills: List[str] = Field(
        default_factory=list,
        description="Preferred skills not found in candidate skills"
    )
    matched_required_count: int = Field(
        ...,
        description="Number of required skills matched"
    )
    total_required_count: int = Field(
        ...,
        description="Total required skills"
    )
    matched_preferred_count: int = Field(
        ...,
        description="Number of preferred skills matched"
    )
    total_preferred_count: int = Field(
        ...,
        description="Total preferred skills"
    )
    match_details: Dict[str, Any] = Field(
        default_factory=dict,
        description="Detailed matching information per skill"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "overall_score": 82.5,
                "required_match_pct": 85.0,
                "preferred_match_pct": 75.0,
                "matched_skills": ["Python", "Django", "PostgreSQL", "Docker"],
                "missing_required_skills": ["Kubernetes"],
                "missing_preferred_skills": ["GraphQL"],
                "matched_required_count": 5,
                "total_required_count": 6,
                "matched_preferred_count": 3,
                "total_preferred_count": 4
            }
        }


class SkillScorer:
    """
    Computes semantic skill overlap between candidate and job requirements.
    Uses sentence-transformers for intelligent skill matching.
    """

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        similarity_threshold: float = 0.75,
        **_: Any,
    ):
        """
        Initialize the SkillScorer.

        Args:
            model_name: Sentence-transformers model name (default: all-MiniLM-L6-v2)
            similarity_threshold: Cosine similarity threshold for matching (default: 0.75)
        """
        self.model_name = model_name
        self.similarity_threshold = similarity_threshold

        try:
            # Load the sentence transformer model once per SkillScorer instance
            self.model = SentenceTransformer(model_name)
            logger.info(
                f"SkillScorer initialized with model '{model_name}' "
                f"and threshold {similarity_threshold}"
            )
        except Exception as e:
            logger.error(f"Error loading sentence-transformer model: {str(e)}")
            raise

    def compute_skill_overlap_score(
        self,
        candidate_skills: List[str],
        required_skills: List[str],
        preferred_skills: Optional[List[str]] = None,
        required_weight: float = 0.7,
        preferred_weight: float = 0.3
    ) -> SkillScoreResult:
        """
        Compute semantic skill overlap score between candidate and job requirements.

        Args:
            candidate_skills: List of skills the candidate possesses
            required_skills: List of required job skills
            preferred_skills: List of preferred job skills (default: empty list)
            required_weight: Weight for required skills in overall score (default: 0.7)
            preferred_weight: Weight for preferred skills in overall score (default: 0.3)

        Returns:
            SkillScoreResult with detailed scoring breakdown

        Raises:
            ValueError: If inputs are invalid
        """
        # Validate inputs
        if not isinstance(candidate_skills, list) or not candidate_skills:
            raise ValueError("candidate_skills must be a non-empty list")

        if not isinstance(required_skills, list) or not required_skills:
            raise ValueError("required_skills must be a non-empty list")

        if preferred_skills is None:
            preferred_skills = []
        elif not isinstance(preferred_skills, list):
            raise ValueError("preferred_skills must be a list or None")

        # Verify weights sum to 1.0
        if not np.isclose(required_weight + preferred_weight, 1.0):
            raise ValueError(f"Weights must sum to 1.0 (got {required_weight + preferred_weight})")

        try:
            # Clean and normalize inputs
            candidate_skills = self._normalize_skills(candidate_skills)
            required_skills = self._normalize_skills(required_skills)
            preferred_skills = self._normalize_skills(preferred_skills)

            logger.debug(
                f"Computing skill overlap: {len(candidate_skills)} candidate skills "
                f"vs {len(required_skills)} required + {len(preferred_skills)} preferred"
            )

            # Match required skills
            required_matches, required_missing, required_details = self._match_skills(
                candidate_skills,
                required_skills
            )

            # Match preferred skills
            preferred_matches, preferred_missing, preferred_details = self._match_skills(
                candidate_skills,
                preferred_skills
            )

            # Calculate percentages
            required_match_pct = (
                (len(required_matches) / len(required_skills) * 100)
                if required_skills else 0
            )
            preferred_match_pct = (
                (len(preferred_matches) / len(preferred_skills) * 100)
                if preferred_skills else 0
            )

            # Calculate overall score
            overall_score = (
                (required_match_pct * required_weight) +
                (preferred_match_pct * preferred_weight)
            )

            # Combine matched skills
            all_matched = list(set(required_matches + preferred_matches))

            # Create result
            result = SkillScoreResult(
                overall_score=round(overall_score, 2),
                required_match_pct=round(required_match_pct, 2),
                preferred_match_pct=round(preferred_match_pct, 2),
                matched_skills=sorted(all_matched),
                missing_required_skills=sorted(required_missing),
                missing_preferred_skills=sorted(preferred_missing),
                matched_required_count=len(required_matches),
                total_required_count=len(required_skills),
                matched_preferred_count=len(preferred_matches),
                total_preferred_count=len(preferred_skills),
                match_details={
                    "required": required_details,
                    "preferred": preferred_details
                }
            )

            logger.info(
                f"Skill overlap computed: {result.overall_score}% "
                f"({result.required_match_pct}% required, "
                f"{result.preferred_match_pct}% preferred)"
            )

            return result

        except Exception as e:
            logger.error(f"Error computing skill overlap: {str(e)}")
            raise

    def _normalize_skills(self, skills: List[str]) -> List[str]:
        """
        Normalize skill list by cleaning and removing duplicates.

        Args:
            skills: List of skills to normalize

        Returns:
            Cleaned, deduplicated list of skills
        """
        normalized = []
        seen = set()

        for skill in skills:
            if isinstance(skill, str):
                cleaned = skill.strip().lower()
                if cleaned and cleaned not in seen:
                    normalized.append(cleaned)
                    seen.add(cleaned)

        return normalized

    def _match_skills(
        self,
        candidate_skills: List[str],
        job_skills: List[str]
    ) -> Tuple[List[str], List[str], Dict[str, Any]]:
        """
        Match candidate skills against job skills using semantic similarity.

        Args:
            candidate_skills: Candidate's skills (normalized)
            job_skills: Job's required/preferred skills (normalized)

        Returns:
            Tuple of (matched_skills, missing_skills, match_details)
        """
        if not job_skills:
            return [], [], {}

        matched = []
        missing = []
        details = {}

        # Encode all skills once
        candidate_embeddings = self.model.encode(candidate_skills, convert_to_tensor=True)
        job_embeddings = self.model.encode(job_skills, convert_to_tensor=True)

        # For each job skill, find best match in candidate skills
        for i, job_skill in enumerate(job_skills):
            job_embedding = job_embeddings[i]

            # Compute cosine similarity with all candidate skills
            similarities = util.cos_sim(job_embedding, candidate_embeddings)[0]

            # Find best match
            best_match_idx = similarities.argmax().item()
            best_similarity = similarities[best_match_idx].item()

            details[job_skill] = {
                "similarity": round(best_similarity, 4),
                "matched_candidate_skill": candidate_skills[best_match_idx] if best_similarity > 0 else None,
                "threshold": self.similarity_threshold,
                "is_match": best_similarity >= self.similarity_threshold
            }

            if best_similarity >= self.similarity_threshold:
                matched.append(job_skill)
            else:
                missing.append(job_skill)

            logger.debug(
                f"Job skill '{job_skill}' → "
                f"'{candidate_skills[best_match_idx]}' "
                f"(similarity: {best_similarity:.4f}, "
                f"match: {best_similarity >= self.similarity_threshold})"
            )

        return matched, missing, details

    def score_batch(
        self,
        candidates: List[Dict[str, Any]],
        required_skills: List[str],
        preferred_skills: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Score multiple candidates against the same job requirements.

        Args:
            candidates: List of candidate dicts with 'skills' key
            required_skills: Required job skills
            preferred_skills: Preferred job skills

        Returns:
            List of candidates with added score information
        """
        scored_candidates = []
        failed_count = 0

        for idx, candidate in enumerate(candidates):
            try:
                if not isinstance(candidate, dict):
                    logger.warning(f"Skipping item {idx}: not a dictionary")
                    failed_count += 1
                    continue

                candidate_skills = candidate.get("skills", [])
                if not candidate_skills:
                    logger.warning(f"Skipping candidate {idx}: no skills found")
                    failed_count += 1
                    continue

                # Compute score
                score_result = self.compute_skill_overlap_score(
                    candidate_skills=candidate_skills,
                    required_skills=required_skills,
                    preferred_skills=preferred_skills
                )

                # Add score to candidate
                scored = candidate.copy()
                scored["skill_score"] = score_result.model_dump()

                scored_candidates.append(scored)

            except Exception as e:
                logger.error(f"Error scoring candidate at index {idx}: {str(e)}")
                failed_count += 1
                continue

        logger.info(
            f"Scored {len(scored_candidates)}/{len(candidates)} candidates. "
            f"Failed: {failed_count}"
        )

        return scored_candidates


def compute_skill_overlap_score(
    candidate_skills: List[str],
    required_skills: List[str],
    preferred_skills: Optional[List[str]] = None,
    similarity_threshold: float = 0.75,
    model_name: str = "all-MiniLM-L6-v2"
) -> SkillScoreResult:
    """
    Convenience function to compute skill overlap score.

    Args:
        candidate_skills: Candidate's skills
        required_skills: Required job skills
        preferred_skills: Preferred job skills
        similarity_threshold: Cosine similarity threshold (default: 0.75)
        model_name: Sentence-transformer model (default: all-MiniLM-L6-v2)

    Returns:
        SkillScoreResult with scoring breakdown
    """
    global _global_skill_scorer
    if (
        _global_skill_scorer is None
        or _global_skill_scorer.model_name != model_name
        or _global_skill_scorer.similarity_threshold != similarity_threshold
    ):
        _global_skill_scorer = SkillScorer(
            model_name=model_name,
            similarity_threshold=similarity_threshold,
        )

    return _global_skill_scorer.compute_skill_overlap_score(
        candidate_skills=candidate_skills,
        required_skills=required_skills,
        preferred_skills=preferred_skills
    )

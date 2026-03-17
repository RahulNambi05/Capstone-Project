"""
Ranking agent module for scoring and ranking candidates against job descriptions.
Combines semantic similarity with skill overlap scoring for comprehensive ranking.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.agents.skill_scorer import compute_skill_overlap_score

logger = logging.getLogger(__name__)


class RankingResult:
    """Result of ranking a single candidate."""

    def __init__(
        self,
        resume_id: str,
        semantic_score: float,
        skill_score: float,
        final_score: float,
        matched_skills: List[str],
        missing_skills: List[str],
        explanation: str,
        metadata: Dict[str, Any],
        rank: int = 0,
    ):
        """Initialize ranking result."""
        self.resume_id = resume_id
        self.semantic_score = round(semantic_score, 2)
        self.skill_score = round(skill_score, 2)
        self.final_score = round(final_score, 2)
        self.matched_skills = matched_skills
        self.missing_skills = missing_skills
        self.explanation = explanation
        self.metadata = metadata
        self.rank = rank

    def to_dict(self) -> Dict[str, Any]:
        """Convert ranking result to dictionary."""
        return {
            "rank": self.rank,
            "resume_id": self.resume_id,
            "final_score": self.final_score,
            "semantic_score": self.semantic_score,
            "skill_score": self.skill_score,
            "matched_skills": self.matched_skills,
            "missing_skills": self.missing_skills,
            "explanation": self.explanation,
            "metadata": self.metadata,
        }


def rank_candidates(
    candidates: List[Dict[str, Any]],
    parsed_jd: Dict[str, Any],
    semantic_weight: float = 0.4,
    skill_weight: float = 0.6,
) -> List[Dict[str, Any]]:
    """
    Rank candidates based on semantic similarity and skill overlap.

    Combines semantic similarity score from vector store retrieval (default 40%)
    with skill overlap score from semantic skill matching (default 60%).

    Args:
        candidates: List of candidate dicts from vector store retrieval.
                   Expected fields: resume_id, score (semantic), metadata, matched_skills
        parsed_jd: Parsed job description with required_skills, preferred_skills
        semantic_weight: Weight for semantic similarity score (default: 0.4 = 40%)
        skill_weight: Weight for skill overlap score (default: 0.6 = 60%)

    Returns:
        List of candidates ranked by final_score (descending) with fields:
        - rank: Position in rankings (1-based)
        - resume_id: Unique resume identifier
        - final_score: Weighted combination score (0-100)
        - semantic_score: Semantic similarity (0-100)
        - skill_score: Skill overlap percentage (0-100)
        - matched_skills: Skills that match job requirements
        - missing_skills: Required skills candidate is missing
        - explanation: Human-readable explanation of score
        - metadata: Candidate metadata (experience_level, role_category, education, etc.)

    Example:
        >>> candidates = [
        ...     {
        ...         "resume_id": "res_001",
        ...         "score": 0.85,  # semantic similarity 0-1
        ...         "metadata": {"top_skills": ["Python", "Django"], ...},
        ...         "matched_skills": ["Python"]
        ...     }
        ... ]
        >>> parsed_jd = {
        ...     "required_skills": ["Python", "PostgreSQL"],
        ...     "preferred_skills": ["Docker"]
        ... }
        >>> ranked = rank_candidates(candidates, parsed_jd)
        >>> print(ranked[0]["final_score"])  # Best candidate's score
    """
    try:
        if not candidates:
            logger.warning("No candidates provided for ranking")
            return []

        if not parsed_jd:
            logger.warning("No parsed job description provided for ranking")
            return []

        # Validate weights sum to 1.0
        total_weight = semantic_weight + skill_weight
        if abs(total_weight - 1.0) > 0.01:
            logger.warning(
                f"Weights do not sum to 1.0 (sum: {total_weight}). "
                f"Normalizing weights."
            )
            semantic_weight = semantic_weight / total_weight
            skill_weight = skill_weight / total_weight

        ranked_results = []

        # Extract job requirements
        required_skills = parsed_jd.get("required_skills", [])
        preferred_skills = parsed_jd.get("preferred_skills", [])

        logger.info(
            f"Ranking {len(candidates)} candidates with weights: "
            f"semantic={semantic_weight:.1%}, skill={skill_weight:.1%}"
        )

        # Score each candidate
        for candidate in candidates:
            try:
                resume_id = candidate.get("resume_id", "unknown")

                # Extract semantic score from vector store (0-1)
                semantic_similarity = candidate.get("score", 0.5)
                # Normalize to 0-100
                semantic_score = semantic_similarity * 100

                # Get candidate skills from metadata
                candidate_skills = (
                    candidate.get("metadata", {}).get("top_skills", [])
                )

                # Compute skill overlap score
                skill_score_result = compute_skill_overlap_score(
                    candidate_skills=candidate_skills,
                    required_skills=required_skills,
                    preferred_skills=preferred_skills,
                )

                skill_score = skill_score_result.overall_score

                # Calculate weighted final score
                # semantic_weight=0.4 (40%), skill_weight=0.6 (60%)
                final_score = (
                    semantic_score * semantic_weight
                ) + (skill_score * skill_weight)

                # Build explanation
                explanation = _build_explanation(
                    resume_id=resume_id,
                    semantic_score=semantic_score,
                    skill_score=skill_score,
                    final_score=final_score,
                    skill_score_result=skill_score_result,
                    semantic_weight=semantic_weight,
                    skill_weight=skill_weight,
                )

                # Create ranking result
                result = RankingResult(
                    resume_id=resume_id,
                    semantic_score=semantic_score,
                    skill_score=skill_score,
                    final_score=final_score,
                    matched_skills=skill_score_result.matched_skills[:10],
                    missing_skills=skill_score_result.missing_required_skills,
                    explanation=explanation,
                    metadata=candidate.get("metadata", {}),
                )

                ranked_results.append(result)

            except Exception as e:
                logger.error(
                    f"Error ranking candidate {candidate.get('resume_id', 'unknown')}: {str(e)}",
                    exc_info=True,
                )
                # Continue with next candidate on error
                continue

        # Sort by final_score descending (highest first)
        ranked_results.sort(key=lambda x: x.final_score, reverse=True)

        # Assign ranks (1-based)
        for rank, result in enumerate(ranked_results, 1):
            result.rank = rank

        # Convert to dictionaries
        ranked_candidates = [result.to_dict() for result in ranked_results]

        logger.info(
            f"Ranking completed: {len(ranked_candidates)} candidates ranked. "
            f"Top score: {ranked_candidates[0]['final_score'] if ranked_candidates else 'N/A'}"
        )

        return ranked_candidates

    except Exception as e:
        logger.error(f"Fatal error in rank_candidates: {str(e)}", exc_info=True)
        raise


def _build_explanation(
    resume_id: str,
    semantic_score: float,
    skill_score: float,
    final_score: float,
    skill_score_result: Any,
    semantic_weight: float = 0.4,
    skill_weight: float = 0.6,
) -> str:
    """
    Build human-readable explanation for candidate ranking.

    Args:
        resume_id: Resume identifier for logging
        semantic_score: Semantic similarity score (0-100)
        skill_score: Skill overlap score (0-100)
        final_score: Final weighted score (0-100)
        skill_score_result: SkillScoreResult object with detailed skill matching
        semantic_weight: Weight of semantic score in final calculation
        skill_weight: Weight of skill score in final calculation

    Returns:
        Human-readable explanation string
    """
    try:
        explanation_parts = []

        # Semantic match summary
        if semantic_score >= 85:
            semantic_desc = "Excellent semantic match"
        elif semantic_score >= 70:
            semantic_desc = "Strong semantic match"
        elif semantic_score >= 55:
            semantic_desc = "Moderate semantic match"
        else:
            semantic_desc = "Weak semantic match"

        explanation_parts.append(
            f"{semantic_desc} ({semantic_score:.1f}/100, {semantic_weight:.0%} weight)"
        )

        # Skill match summary
        required_pct = skill_score_result.required_match_pct
        preferred_pct = skill_score_result.preferred_match_pct

        if required_pct >= 80:
            skill_desc = "Strong skill coverage"
        elif required_pct >= 60:
            skill_desc = "Moderate skill coverage"
        elif required_pct >= 40:
            skill_desc = "Partial skill coverage"
        else:
            skill_desc = "Limited skill coverage"

        explanation_parts.append(
            f"{skill_desc} ({required_pct:.0f}% required, {preferred_pct:.0f}% preferred, {skill_weight:.0%} weight)"
        )

        # Matched skills
        if skill_score_result.matched_skills:
            matched = ", ".join(skill_score_result.matched_skills[:3])
            if len(skill_score_result.matched_skills) > 3:
                matched += f" +{len(skill_score_result.matched_skills) - 3} more"
            explanation_parts.append(f"Matched: {matched}")

        # Missing skills (only if significant)
        if skill_score_result.missing_required_skills and required_pct < 100:
            missing = ", ".join(skill_score_result.missing_required_skills[:2])
            if len(skill_score_result.missing_required_skills) > 2:
                missing += f" +{len(skill_score_result.missing_required_skills) - 2} more"
            explanation_parts.append(f"Missing: {missing}")

        # Final score assessment
        if final_score >= 85:
            final_desc = "Excellent fit"
        elif final_score >= 75:
            final_desc = "Very good fit"
        elif final_score >= 65:
            final_desc = "Good fit"
        elif final_score >= 50:
            final_desc = "Acceptable fit"
        else:
            final_desc = "Weak fit"

        explanation_parts.append(f"Overall: {final_desc} ({final_score:.1f}/100)")

        return ". ".join(explanation_parts)

    except Exception as e:
        logger.error(f"Error building explanation for {resume_id}: {str(e)}")
        return f"Final score: {final_score:.1f}/100"


def sort_candidates_by_criteria(
    candidates: List[Dict[str, Any]],
    sort_by: str = "final_score",
    ascending: bool = False,
) -> List[Dict[str, Any]]:
    """
    Sort candidates by specified criteria.

    Args:
        candidates: List of ranked candidate dictionaries
        sort_by: Field to sort by (final_score, skill_score, semantic_score, matched_skills_count)
        ascending: If True, sort ascending; if False (default), sort descending

    Returns:
        Sorted list of candidates
    """
    try:
        if not candidates:
            return []

        valid_sort_fields = [
            "final_score",
            "semantic_score",
            "skill_score",
        ]

        if sort_by not in valid_sort_fields:
            logger.warning(f"Invalid sort field {sort_by}, using final_score")
            sort_by = "final_score"

        sorted_candidates = sorted(
            candidates,
            key=lambda x: x.get(sort_by, 0),
            ascending=ascending,
        )

        # Re-rank sorted results
        for rank, candidate in enumerate(sorted_candidates, 1):
            candidate["rank"] = rank

        return sorted_candidates

    except Exception as e:
        logger.error(f"Error sorting candidates: {str(e)}", exc_info=True)
        return candidates


def get_ranking_statistics(candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate statistics about ranked candidates.

    Args:
        candidates: List of ranked candidate dictionaries

    Returns:
        Dictionary with ranking statistics
    """
    try:
        if not candidates:
            return {
                "total_candidates": 0,
                "avg_final_score": 0.0,
                "avg_semantic_score": 0.0,
                "avg_skill_score": 0.0,
                "top_score": 0.0,
                "bottom_score": 0.0,
                "median_score": 0.0,
            }

        final_scores = [c.get("final_score", 0) for c in candidates]
        semantic_scores = [c.get("semantic_score", 0) for c in candidates]
        skill_scores = [c.get("skill_score", 0) for c in candidates]

        sorted_final = sorted(final_scores)
        median_idx = len(sorted_final) // 2
        median_score = (
            sorted_final[median_idx]
            if len(sorted_final) % 2 == 1
            else (sorted_final[median_idx - 1] + sorted_final[median_idx]) / 2
        )

        return {
            "total_candidates": len(candidates),
            "avg_final_score": round(sum(final_scores) / len(final_scores), 2),
            "avg_semantic_score": round(sum(semantic_scores) / len(semantic_scores), 2),
            "avg_skill_score": round(sum(skill_scores) / len(skill_scores), 2),
            "top_score": round(max(final_scores), 2),
            "bottom_score": round(min(final_scores), 2),
            "median_score": round(median_score, 2),
        }

    except Exception as e:
        logger.error(f"Error calculating ranking statistics: {str(e)}", exc_info=True)
        return {}

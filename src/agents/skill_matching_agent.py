from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from src.agents.skill_scorer import SkillScorer, SkillScoreResult


@dataclass(frozen=True)
class SkillMatchingResult:
    """
    Result of skill evaluation for a candidate against a parsed job description.

    Notes:
    - `score` maps to the existing `SkillScorer.overall_score` (0-100).
    - `top_skills_raw`, `candidate_skills`, and `resume_text_preview` are included to
      preserve existing debug logging expectations in the matching service.
    """

    score: float
    explanation: str
    skill_score: SkillScoreResult
    candidate_skills: List[str]
    top_skills_raw: Any
    resume_text_preview: str


class SkillMatchingAgent:
    """
    Agent responsible for extracting candidate skills and computing the existing
    semantic skill overlap score.

    This keeps the logic aligned with the current implementation:
    1) Try `top_skills` metadata
    2) If empty, extract skills directly from resume text using required skills
       containment checks (case-insensitive)
    3) Ensure `candidate_skills` is never empty for the scorer
    """

    def __init__(self, skill_scorer: SkillScorer):
        self._skill_scorer = skill_scorer

    def evaluate(
        self,
        candidate: Dict[str, Any],
        parsed_job: Any,
        resume_text_fallback: str = "",
    ) -> SkillMatchingResult:
        resume_id = candidate.get("resume_id", "unknown")

        candidate_skills: List[str] = []
        top_skills_raw: Any = candidate.get("metadata", {}).get("top_skills", "")

        if isinstance(top_skills_raw, str) and top_skills_raw:
            candidate_skills = [s.strip() for s in top_skills_raw.split(",") if s.strip()]
        elif isinstance(top_skills_raw, list):
            candidate_skills = [str(s).strip() for s in top_skills_raw if str(s).strip()]

        if not candidate_skills:
            resume_text = ((candidate.get("resume_text", "") or "") or (resume_text_fallback or "")).lower()
            candidate_skills = [
                skill
                for skill in (getattr(parsed_job, "required_skills", None) or [])
                if isinstance(skill, str) and skill.lower() in resume_text
            ]

        if not candidate_skills:
            candidate_skills = ["unknown"]

        # Compute the existing overlap score (unchanged)
        skill_score = self._skill_scorer.compute_skill_overlap_score(
            candidate_skills=candidate_skills,
            required_skills=getattr(parsed_job, "required_skills", None) or [],
            preferred_skills=getattr(parsed_job, "preferred_skills", None) or [],
        )

        explanation = (
            f"Skills: {skill_score.required_match_pct:.0f}% required, "
            f"{skill_score.preferred_match_pct:.0f}% preferred."
        )

        return SkillMatchingResult(
            score=float(skill_score.overall_score),
            explanation=explanation,
            skill_score=skill_score,
            candidate_skills=candidate_skills,
            top_skills_raw=top_skills_raw,
            resume_text_preview=str(candidate.get("resume_text", "") or "")[:100],
        )

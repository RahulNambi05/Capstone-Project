from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

import zlib

from src.agents.culture_fit_agent import CultureFitAgent, CultureFitResult
from src.agents.experience_evaluation_agent import ExperienceEvaluationAgent, ExperienceEvaluationResult
from src.agents.skill_matching_agent import SkillMatchingAgent, SkillMatchingResult
from src.agents.technical_evaluation_agent import TechnicalEvaluationAgent, TechnicalEvaluationResult
from src.agents.skill_scorer import SkillScorer


@dataclass(frozen=True)
class PipelineEvaluation:
    """
    Combined evaluation from all agents for one candidate.

    This structure is designed so the matching service can produce the same API
    response fields as before:
    - final_score
    - semantic_score
    - skill_score
    - matched_skills / missing_skills
    - skill_coverage
    - explanation
    """

    final_score: float
    semantic_score: float
    skill_score: float
    skill_coverage: float
    matched_skills: list[str]
    missing_skills: list[str]
    explanation: str

    # Agent outputs (kept for debugging/extension; not required in API response)
    technical: TechnicalEvaluationResult
    skill: SkillMatchingResult
    experience: ExperienceEvaluationResult
    culture: CultureFitResult


class AgentPipeline:
    """
    Orchestrator that sequentially calls all agents and combines their outputs.

    Scoring behavior is kept consistent with the existing implementation:
    - technical_score = semantic score (0-100) from vector store similarity
    - skill_score = semantic skill overlap score (0-100)
    - raw_score = 50% technical + 50% skill
    - final_score = 40 + (raw_score * 0.6) capped at 100

    Experience and culture fit agents are included for architecture completeness,
    but are assigned 0.0 weight by default to avoid changing scoring behavior.
    """

    def __init__(self, skill_scorer: SkillScorer):
        self.technical_agent = TechnicalEvaluationAgent()
        self.skill_agent = SkillMatchingAgent(skill_scorer=skill_scorer)
        self.experience_agent = ExperienceEvaluationAgent()
        self.culture_fit_agent = CultureFitAgent()

        self.weights = {
            "technical": 0.5,
            "skill": 0.5,
            "experience": 0.0,
            "culture": 0.0,
        }

    def evaluate_candidate(
        self,
        candidate: Dict[str, Any],
        parsed_job: Any,
        resume_text_fallback: str = "",
    ) -> PipelineEvaluation:
        def _pretty_skill(s: str) -> str:
            raw = str(s or "").strip()
            if not raw:
                return ""
            key = raw.lower()
            acronyms = {
                "api": "API",
                "rest": "REST",
                "sql": "SQL",
                "ux": "UX",
                "ui": "UI",
                "hris": "HRIS",
                "ci/cd": "CI/CD",
                "aws": "AWS",
                "gcp": "GCP",
                "hipaa": "HIPAA",
            }
            if key in acronyms:
                return acronyms[key]

            words = raw.split()
            pretty_words: list[str] = []
            for w in words:
                wk = w.lower()
                pretty_words.append(acronyms.get(wk, w.capitalize() if w.islower() else w))
            return " ".join(pretty_words)

        technical = self.technical_agent.evaluate(candidate)
        skill = self.skill_agent.evaluate(candidate=candidate, parsed_job=parsed_job, resume_text_fallback=resume_text_fallback)
        experience = self.experience_agent.evaluate(candidate=candidate, parsed_job=parsed_job)
        culture = self.culture_fit_agent.evaluate(candidate=candidate, parsed_job=parsed_job)

        raw_score = (
            (technical.score * self.weights["technical"]) +
            (skill.score * self.weights["skill"]) +
            (experience.score * self.weights["experience"]) +
            (culture.score * self.weights["culture"])
        )

        final_score = 40 + (raw_score * 0.6)
        final_score = min(final_score, 100.0)

        # Human-friendly explanation (no raw percentages/scores).
        matched = [_pretty_skill(s) for s in (skill.skill_score.matched_skills or []) if _pretty_skill(s)]
        missing_required = [_pretty_skill(s) for s in (skill.skill_score.missing_required_skills or []) if _pretty_skill(s)]

        strengths_txt = ", ".join(matched[:3]) if matched else ""
        gaps_txt = ", ".join(missing_required[:3]) if missing_required else ""

        resume_id = str(candidate.get("resume_id") or "unknown")
        opener_variants = [
            "This candidate aligns well with the role's core needs.",
            "Overall, this profile shows a solid fit for the role's priorities.",
            "At a glance, the candidate demonstrates relevant alignment for this position.",
            "The candidate shows meaningful overlap with the role's requirements.",
        ]
        opener = opener_variants[zlib.crc32(resume_id.encode("utf-8")) % len(opener_variants)]

        sentences: list[str] = [opener]
        if strengths_txt:
            sentences.append(
                f"The strongest signals are in {strengths_txt}, which map directly to key responsibilities."
            )
        else:
            sentences.append(
                "Their transferable experience is apparent, though specific skill signals are limited in the available text."
            )

        # Use experience/role as context (avoid repeating exact same phrasing across candidates).
        exp_level = str(candidate.get("metadata", {}).get("experience_level", "") or "").strip().lower()
        role_cat = str(candidate.get("metadata", {}).get("role_category", "") or "").strip().lower()
        if exp_level or role_cat:
            label = " ".join([p for p in [exp_level, role_cat] if p]) or "this role"
            sentences.append(f"Their background suggests they can operate effectively in a {label} context.")

        if gaps_txt:
            sentences.append(
                f"However, there is limited evidence of {gaps_txt}, so this is worth validating in screening."
            )
        else:
            sentences.append("No major gaps stand out from the skill signals provided.")

        # Keep to 3-4 sentences.
        explanation = " ".join(sentences[:4]).strip()

        # Add concise strengths/gaps bullets (frontend should render newlines with pre-line).
        strengths_bullets = matched[:3] if matched else []
        gaps_bullets = missing_required[:3] if missing_required else []
        if strengths_bullets or gaps_bullets:
            explanation += "\n\nStrengths:\n"
            explanation += "\n".join([f"- {s}" for s in strengths_bullets]) if strengths_bullets else "- Not enough signal"
            explanation += "\n\nGaps:\n"
            explanation += "\n".join([f"- {g}" for g in gaps_bullets]) if gaps_bullets else "- None highlighted"

        return PipelineEvaluation(
            final_score=round(final_score, 2),
            semantic_score=round(technical.score, 2),
            skill_score=round(float(skill.skill_score.overall_score), 2),
            skill_coverage=round(float(skill.skill_score.required_match_pct), 2),
            matched_skills=skill.skill_score.matched_skills[:10],
            missing_skills=skill.skill_score.missing_required_skills,
            explanation=explanation.strip(),
            technical=technical,
            skill=skill,
            experience=experience,
            culture=culture,
        )

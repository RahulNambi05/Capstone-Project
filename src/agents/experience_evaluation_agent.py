from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class ExperienceEvaluationResult:
    """
    Experience evaluation result.

    This agent is included for multi-agent architecture completeness. To maintain
    backward-compatible scoring behavior, the orchestrator can assign this agent
    a 0.0 weight so it does not affect final_score.
    """

    score: float
    explanation: str


class ExperienceEvaluationAgent:
    """Agent that evaluates experience level alignment (non-blocking)."""

    def evaluate(self, candidate: Dict[str, Any], parsed_job: Any) -> ExperienceEvaluationResult:
        desired = str(getattr(parsed_job, "experience_level", "") or "").strip().lower() or "unknown"
        actual = str(candidate.get("metadata", {}).get("experience_level", "") or "").strip().lower() or "unknown"

        if desired == "unknown" or actual == "unknown":
            return ExperienceEvaluationResult(score=50.0, explanation="Experience level not available.")

        if desired == actual:
            return ExperienceEvaluationResult(score=100.0, explanation=f"Experience level matches ({actual}).")

        # Conservative: partial alignment
        return ExperienceEvaluationResult(score=60.0, explanation=f"Experience level differs (job={desired}, candidate={actual}).")


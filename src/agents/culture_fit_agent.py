from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class CultureFitResult:
    """
    Culture fit evaluation result.

    This is a placeholder agent for the multi-agent architecture. The current
    pipeline does not include a culture-fit model, so the default implementation
    returns a neutral score and explanation. The orchestrator can assign this
    agent a 0.0 weight to preserve existing final_score behavior.
    """

    score: float
    explanation: str


class CultureFitAgent:
    """Agent that returns a neutral culture-fit evaluation (non-blocking)."""

    def evaluate(self, candidate: Dict[str, Any], parsed_job: Any) -> CultureFitResult:
        return CultureFitResult(score=50.0, explanation="Culture fit not evaluated in current pipeline.")


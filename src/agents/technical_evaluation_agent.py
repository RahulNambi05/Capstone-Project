from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class TechnicalEvaluationResult:
    """
    Technical evaluation result derived from the existing semantic similarity score.

    `retrieve_candidates()` provides `candidate["score"]` as a similarity value in [0, 1]
    (Chroma cosine distance is converted to similarity via `1 - distance`).

    We convert similarity to a 0-100 score:
      semantic_score_normalized = similarity * 100
    """

    score: float
    explanation: str


class TechnicalEvaluationAgent:
    """Agent that produces the existing semantic/technical score and explanation."""

    def evaluate(self, candidate: Dict[str, Any]) -> TechnicalEvaluationResult:
        similarity = candidate.get("score", 0.5)
        try:
            similarity_f = float(similarity)
        except Exception:
            similarity_f = 0.5

        # Clamp defensively in case an upstream component returns values outside [0, 1]
        if similarity_f < 0:
            similarity_f = 0.0
        elif similarity_f > 1:
            similarity_f = 1.0

        semantic_score_normalized = round(similarity_f * 100, 2)
        explanation = f"Semantic match score {semantic_score_normalized:.1f}%."
        return TechnicalEvaluationResult(score=float(semantic_score_normalized), explanation=explanation)

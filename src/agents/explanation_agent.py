from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from langchain.schema import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src.core.config import settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ExplanationInputs:
    resume_id: str
    experience_level: str
    role_category: str
    matched_skills: List[str]
    missing_skills: List[str]


class ExplanationAgent:
    """
    Generates natural, recruiter-style explanations using OpenAI.

    - Uses model: gpt-4o-mini
    - Output: 3-4 sentences, recruiter-friendly, strengths + gaps, no raw scores/percentages
    - Fallback: returns a clearly-marked template string only on real failure
    """

    def __init__(
        self,
        temperature: float = 0.4,
        max_tokens: int = 220,
        model_name: str = "gpt-4o-mini",
    ) -> None:
        # Keep temperature within requested band.
        t = float(temperature)
        if t < 0.3:
            t = 0.3
        if t > 0.5:
            t = 0.5

        api_key_loaded = bool(getattr(settings, "OPENAI_API_KEY", "") or "")
        logger.info("ExplanationAgent init: api_key_loaded=%s", api_key_loaded)

        self.model_name = model_name
        self.temperature = t
        self.max_tokens = int(max_tokens)

        # Initialize client (if key is missing, we still init will likely fail; we'll fallback with logs)
        self._llm = ChatOpenAI(
            model_name=self.model_name,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            api_key=settings.OPENAI_API_KEY,
        )

    def _fallback_template(self, candidate_data: Dict[str, Any]) -> str:
        """
        Fallback explanation for debugging. Clearly different from LLM output.
        """
        experience_level = str(candidate_data.get("experience_level") or "unknown")
        role_category = str(candidate_data.get("role_category") or "unknown")
        matched = candidate_data.get("matched_skills") or []
        missing = candidate_data.get("missing_skills") or []

        matched_txt = ", ".join([str(s) for s in matched[:3] if str(s).strip()])
        missing_txt = ", ".join([str(s) for s in missing[:3] if str(s).strip()])

        out = f"[FALLBACK] {experience_level} {role_category} candidate"
        if matched_txt:
            out += f" shows evidence of: {matched_txt}."
        if missing_txt:
            out += f" Limited evidence of: {missing_txt}."
        return out

    def _build_prompt_single(self, inputs: ExplanationInputs) -> str:
        matched = ", ".join(inputs.matched_skills[:8]) if inputs.matched_skills else "N/A"
        missing = ", ".join(inputs.missing_skills[:8]) if inputs.missing_skills else "N/A"

        return (
            "You are a senior recruiter writing a short evaluation note for a hiring manager.\n"
            "Write exactly 3-4 sentences in natural, professional language.\n"
            "Do NOT mention raw scores, percentages, numeric ratings, or \"coverage\".\n"
            "Do NOT use headings, bullet points, or a fixed template; vary phrasing naturally.\n"
            "Use evidence-based wording:\n"
            "- Strengths: cite a few matched skills as concrete examples.\n"
            "- Gaps: cite 1-2 missing skills as \"limited evidence of\" or \"would benefit from exposure to\".\n\n"
            f"Candidate seniority: {inputs.experience_level}\n"
            f"Candidate role category: {inputs.role_category}\n"
            f"Matched skills: {matched}\n"
            f"Missing skills: {missing}\n"
        )

    def generate_explanation(self, candidate_data: Dict[str, Any], job_data: Dict[str, Any]) -> str:
        """
        Generate an explanation for one candidate. Always returns a string.
        """
        try:
            inputs = ExplanationInputs(
                resume_id=str(candidate_data.get("resume_id") or "unknown"),
                experience_level=str(candidate_data.get("experience_level") or "unknown"),
                role_category=str(candidate_data.get("role_category") or "unknown"),
                matched_skills=list(candidate_data.get("matched_skills") or []),
                missing_skills=list(candidate_data.get("missing_skills") or []),
            )

            prompt = self._build_prompt_single(inputs)
            logger.info("ExplanationAgent: calling LLM (single) resume_id=%s", inputs.resume_id)
            response = self._llm.invoke(
                [
                    SystemMessage(content="You are a senior recruiter. Output only the explanation text."),
                    HumanMessage(content=prompt),
                ]
            )
            text = (getattr(response, "content", "") or "").strip()
            logger.info("ExplanationAgent: LLM response (single) resume_id=%s text=%r", inputs.resume_id, text)
            return text if text else self._fallback_template(candidate_data)
        except Exception as e:
            logger.exception("ExplanationAgent: LLM failed (single); using fallback. error=%r", e)
            return self._fallback_template(candidate_data)

    def _build_prompt_batch(self, items: List[Dict[str, Any]]) -> str:
        return (
            "You are a senior recruiter writing short evaluation notes for a hiring manager.\n"
            "For each candidate, write exactly 3-4 sentences in natural, professional language.\n"
            "Do NOT mention raw scores, percentages, numeric ratings, or \"coverage\".\n"
            "Avoid repetition and do not follow a fixed template; vary phrasing naturally across candidates.\n"
            "Mention strengths using a few matched skills, then mention 1-2 gaps using "
            "\"limited evidence of\" or \"would benefit from exposure to\".\n\n"
            "Return ONLY valid JSON (no markdown). Format:\n"
            "{\n"
            '  "explanations": [\n'
            '    {"resume_id": "...", "explanation": "..."},\n'
            "    ...\n"
            "  ]\n"
            "}\n\n"
            f"Candidates JSON:\n{json.dumps(items, ensure_ascii=True)}\n"
        )

    def generate_explanations_batch(
        self,
        candidates: List[Dict[str, Any]],
        job_data: Dict[str, Any],
    ) -> Dict[str, str]:
        """
        Generate explanations for multiple candidates in a single LLM call.
        Returns mapping resume_id -> explanation. On failure, returns {}.
        """
        if not candidates:
            return {}

        items: List[Dict[str, Any]] = []
        for c in candidates[:25]:
            items.append(
                {
                    "resume_id": c.get("resume_id"),
                    "experience_level": c.get("experience_level"),
                    "role_category": c.get("role_category"),
                    "matched_skills": (c.get("matched_skills") or [])[:8],
                    "missing_skills": (c.get("missing_skills") or [])[:8],
                }
            )

        prompt = self._build_prompt_batch(items)
        try:
            logger.info("ExplanationAgent: calling LLM (batch) count=%d", len(items))
            response = self._llm.invoke(
                [
                    SystemMessage(content="You are a senior recruiter. Output JSON only."),
                    HumanMessage(content=prompt),
                ]
            )
            content = (getattr(response, "content", "") or "").strip()
            logger.info("ExplanationAgent: LLM response (batch) text=%r", content)

            # Strip markdown fences if present (defensive)
            if "```json" in content:
                content = content.split("```json", 1)[1].split("```", 1)[0].strip()
            elif "```" in content:
                content = content.split("```", 1)[1].split("```", 1)[0].strip()

            parsed = json.loads(content)
            explanations = parsed.get("explanations") if isinstance(parsed, dict) else None
            if not isinstance(explanations, list):
                return {}

            out: Dict[str, str] = {}
            for item in explanations:
                if not isinstance(item, dict):
                    continue
                rid = str(item.get("resume_id") or "").strip()
                exp = str(item.get("explanation") or "").strip()
                if rid and exp:
                    out[rid] = exp
            return out
        except Exception as e:
            logger.exception("ExplanationAgent: LLM failed (batch); skipping. error=%r", e)
            return {}


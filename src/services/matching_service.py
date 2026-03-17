"""
Standalone matching microservice for the Resume Matching System.
Handles candidate retrieval, scoring, and ranking independently.
Can be started on port 8001 for parallel processing.

Used in the recommended architecture:
  - `gateway.py` (API Gateway, port 8000) forwards requests to this service
  - Scoring is orchestrated by `src/services/agent_pipeline.py`
"""
import logging
import json
import re
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
import uvicorn
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

from src.core.config import settings
from src.retrieval.job_parser import parse_job_description, parse_job_description_fast
from src.retrieval.candidate_retriever import retrieve_candidates
from src.agents.skill_scorer import SkillScorer
from src.services.agent_pipeline import AgentPipeline
from src.agents.explanation_agent import ExplanationAgent
from src.embeddings.vector_store import init_vector_store, get_vector_store
from src.guardrails.input_validator import validate_job_description, detect_bias

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global vector store instance
_vector_store_instance = None
_vector_store_total_documents: int = 0

# Global skill scorer instance (SentenceTransformer)
_skill_scorer = None

# Global LLM for soft skills assessment
_soft_skills_llm = None

# Global agent pipeline orchestrator
_agent_pipeline = None

# Global explanation agent (LLM-based)
_explanation_agent = None

# Cached stats response (avoid expensive stats calls per request)
_stats_cache: Dict[str, Any] = {"ts": None, "data": None}


async def assess_soft_skills(resume_text: str, job_description: str) -> Dict[str, Any]:
    """
    Uses GPT-4o-mini to evaluate soft skills for a candidate vs a job.
    Returns ONLY a dict with:
      - communication_score: int 0-100
      - leadership_score: int 0-100
      - teamwork_score: int 0-100
      - problem_solving_score: int 0-100
      - overall_soft_skill_score: int 0-100
      - summary: str
    """
    global _soft_skills_llm

    if _soft_skills_llm is None:
        if not getattr(settings, "OPENAI_API_KEY", None):
            logger.error("Soft skills assessment disabled: OPENAI_API_KEY is missing/empty")
            return {
                "communication_score": 0,
                "leadership_score": 0,
                "teamwork_score": 0,
                "problem_solving_score": 0,
                "overall_soft_skill_score": 0,
                "summary": "Soft skills assessment unavailable (missing OPENAI_API_KEY).",
            }

        try:
            _soft_skills_llm = ChatOpenAI(
                model_name="gpt-4o-mini",
                temperature=0.1,
                max_tokens=150,
                api_key=settings.OPENAI_API_KEY,
            )
            logger.info("Soft skills LLM initialized (model=gpt-4o-mini, max_tokens=150)")
        except Exception as e:
            logger.exception(f"Failed to initialize soft skills LLM: {e!r}")
            return {
                "communication_score": 0,
                "leadership_score": 0,
                "teamwork_score": 0,
                "problem_solving_score": 0,
                "overall_soft_skill_score": 0,
                "summary": "Soft skills assessment unavailable (LLM init failed).",
            }

    resume_excerpt = (resume_text or "")[:200]
    job_excerpt = (job_description or "")[:100]

    prompt = (
        "Rate soft skills 0-100. Return JSON with keys: communication_score, leadership_score, "
        "teamwork_score, problem_solving_score, overall_soft_skill_score, summary.\n"
        f"Resume: {resume_excerpt}\n"
        f"Job: {job_excerpt}\n"
    )

    try:
        if not resume_excerpt.strip():
            logger.warning("Soft skills assessment: resume_text excerpt is empty (resume_text missing?)")

        try:
            response = await _soft_skills_llm.ainvoke([
                SystemMessage(content="You are an expert recruiter. Output JSON only."),
                HumanMessage(content=prompt),
            ])
        except Exception as e:
            logger.exception(f"Soft skills LLM call failed: {e!r}")
            return {
                "communication_score": 0,
                "leadership_score": 0,
                "teamwork_score": 0,
                "problem_solving_score": 0,
                "overall_soft_skill_score": 0,
                "summary": "Soft skills assessment unavailable (LLM call failed).",
            }

        content = (getattr(response, "content", "") or "").strip()

        # Strip markdown fences if present
        if "```json" in content:
            content = content.split("```json", 1)[1].split("```", 1)[0].strip()
        elif "```" in content:
            content = content.split("```", 1)[1].split("```", 1)[0].strip()

        try:
            data = json.loads(content)
        except Exception as e:
            logger.error(
                "Soft skills JSON parse failed. "
                f"error={e!r} content_preview={content[:400]!r}"
            )
            return {
                "communication_score": 0,
                "leadership_score": 0,
                "teamwork_score": 0,
                "problem_solving_score": 0,
                "overall_soft_skill_score": 0,
                "summary": "Soft skills assessment unavailable (invalid JSON response).",
            }

        def _clamp_int(v: Any) -> int:
            try:
                iv = int(round(float(v)))
            except Exception:
                iv = 0
            return max(0, min(iv, 100))

        return {
            "communication_score": _clamp_int(data.get("communication_score", 0)),
            "leadership_score": _clamp_int(data.get("leadership_score", 0)),
            "teamwork_score": _clamp_int(data.get("teamwork_score", 0)),
            "problem_solving_score": _clamp_int(data.get("problem_solving_score", 0)),
            "overall_soft_skill_score": _clamp_int(data.get("overall_soft_skill_score", 0)),
            "summary": str(data.get("summary", "")).strip()[:300],
        }
    except Exception as e:
        logger.exception(f"Soft skills assessment failed: {e!r}")
        return {
            "communication_score": 0,
            "leadership_score": 0,
            "teamwork_score": 0,
            "problem_solving_score": 0,
            "overall_soft_skill_score": 0,
            "summary": "Soft skills assessment unavailable.",
        }

# ============================================================================
# Request/Response Models
# ============================================================================

class MatchRequest(BaseModel):
    """Request model for job matching endpoint."""
    job_description: str = Field(
        ...,
        description="Complete job description text",
        min_length=50,
        max_length=10000
    )
    top_k: int = Field(
        default=10,
        description="Number of candidates to return",
        ge=1,
        le=100
    )


class SkillMatch(BaseModel):
    """Skill match information for a candidate."""
    name: str
    match_type: str  # "required" or "preferred"
    matched: bool


class CandidateMatch(BaseModel):
    """Single candidate match result."""
    rank: int
    resume_id: str
    final_score: float = Field(..., ge=0, le=100)
    semantic_score: float = Field(..., ge=0, le=100)
    skill_score: float = Field(..., ge=0, le=100)
    skill_coverage: float = Field(..., ge=0, le=100)
    matched_skills: List[str]
    missing_skills: List[str]
    explanation: str
    experience_level: str
    role_category: str
    soft_skills_assessment: Optional[Dict[str, Any]] = None


class MatchResponse(BaseModel):
    """Response model for job matching endpoint."""
    status: str
    query_summary: str
    parsed_job: Dict[str, Any]
    bias_check: Dict[str, Any]
    token_usage: Dict[str, Any]
    candidates: List[CandidateMatch]
    total_found: int
    execution_time: float
    performance: Dict[str, Any]
    message: str


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    service: str
    timestamp: str
    vector_store_ready: bool
    total_documents: int = 0


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="Resume Matching Microservice",
    description="Standalone service for candidate matching and scoring",
    version="1.0.0"
)


# ============================================================================
# Startup Event
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize vector store on service startup."""
    global _vector_store_instance, _skill_scorer, _vector_store_total_documents, _agent_pipeline, _explanation_agent
    try:
        logger.info("=" * 70)
        logger.info("Matching Microservice - Starting")
        logger.info("=" * 70)

        logger.info("Initializing skill scorer...")
        _skill_scorer = SkillScorer()
        logger.info("✓ Skill scorer initialized!")
        _agent_pipeline = AgentPipeline(skill_scorer=_skill_scorer)
        logger.info("✓ Agent pipeline initialized!")

        enable_llm_explanations = os.getenv("ENABLE_LLM_EXPLANATIONS", "0") == "1"
        if enable_llm_explanations:
            _explanation_agent = ExplanationAgent(temperature=0.4)
            logger.info("✓ Explanation agent initialized!")
        else:
            _explanation_agent = None

        logger.info("Initializing vector store...")
        init_vector_store()
        _vector_store_instance = get_vector_store()

        if _vector_store_instance:
            logger.info("✓ Vector store initialized!")
            stats = _vector_store_instance.get_collection_stats()
            total_docs = stats.get('total_documents', 0)
            total_resumes = stats.get('total_resumes', 0)
            _vector_store_total_documents = int(total_docs or 0)
            logger.info(f"✓ Vector store ready with {total_docs} documents from {total_resumes} resumes")
        else:
            logger.warning("✗ Vector store initialization returned None")

        logger.info("=" * 70)
        logger.info("Matching Microservice - Ready")
        logger.info("=" * 70)

    except Exception as e:
        logger.error(f"Failed to initialize vector store: {str(e)}", exc_info=True)


# ============================================================================
# Endpoints
# ============================================================================

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns service status and vector store readiness.
    """
    try:
        vs = get_vector_store()
        vector_store_ready = vs is not None
        total_documents = _vector_store_total_documents if vector_store_ready else 0

        return HealthResponse(
            status="healthy",
            service="matching",
            timestamp=datetime.utcnow().isoformat(),
            vector_store_ready=vector_store_ready,
            total_documents=total_documents
        )
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return HealthResponse(
            status="degraded",
            service="matching",
            timestamp=datetime.utcnow().isoformat(),
            vector_store_ready=False,
            total_documents=0
        )


@app.get("/stats", tags=["Analytics"])
async def get_statistics():
    """
    Get statistics about the vector store and indexed candidates.

    Returns statistics including total resumes, chunks, and distributions
    by category, experience level, and role.

    Returns:
    - Vector store statistics in formatted response

    Raises:
    - 500: Vector store error
    """
    try:
        logger.info("Fetching statistics...")
        global _stats_cache
        now = datetime.utcnow()
        if _stats_cache["ts"] and _stats_cache["data"]:
            age_s = (now - _stats_cache["ts"]).total_seconds()
            if age_s < 30:
                return _stats_cache["data"]

        vs = get_vector_store()

        if not vs:
            logger.error("Vector store not initialized")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Vector store not initialized"
            )

        # Get raw stats from vector store
        raw_stats = vs.get_collection_stats()
        logger.info(f"Raw stats retrieved: {list(raw_stats.keys())}")

        # Extract and format the response
        total_resumes = raw_stats.get('total_resumes', 0)
        total_chunks = raw_stats.get('total_documents', 0)

        # Get category distributions
        categories_raw = raw_stats.get('categories_by_count', [])
        categories = []
        if categories_raw:
            total_count = sum(cat.get('count', 0) for cat in categories_raw)
            for cat in categories_raw:
                count = cat.get('count', 0)
                percentage = (count / total_count * 100) if total_count > 0 else 0
                categories.append({
                    "name": cat.get('name', 'unknown'),
                    "count": count,
                    "percentage": round(percentage, 1)
                })

        # Get experience level distributions
        experience_levels_raw = raw_stats.get('experience_levels_by_count', [])
        experience_levels = []
        if experience_levels_raw:
            total_count = sum(exp.get('count', 0) for exp in experience_levels_raw)
            for exp in experience_levels_raw:
                count = exp.get('count', 0)
                percentage = (count / total_count * 100) if total_count > 0 else 0
                experience_levels.append({
                    "name": exp.get('name', 'unknown'),
                    "count": count,
                    "percentage": round(percentage, 1)
                })

        # Get role category distributions
        role_categories_raw = raw_stats.get('role_categories_by_count', [])
        role_categories = []
        if role_categories_raw:
            total_count = sum(role.get('count', 0) for role in role_categories_raw)
            for role in role_categories_raw:
                count = role.get('count', 0)
                percentage = (count / total_count * 100) if total_count > 0 else 0
                role_categories.append({
                    "name": role.get('name', 'unknown'),
                    "count": count,
                    "percentage": round(percentage, 1)
                })

        response = {
            "status": "success",
            "total_resumes": total_resumes,
            "total_chunks": total_chunks,
            "categories": categories,
            "experience_levels": experience_levels,
            "role_categories": role_categories,
            "timestamp": datetime.utcnow().isoformat()
        }

        logger.info(f"Statistics: {total_resumes} resumes, {total_chunks} chunks")
        _stats_cache = {"ts": now, "data": response}
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Statistics error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving statistics: {str(e)}"
        )


@app.post("/match", response_model=MatchResponse, tags=["Matching"])
async def match_candidates(request: MatchRequest) -> MatchResponse:
    """
    Match job description with candidate resumes.

    Validates job description, retrieves matching candidates from vector store,
    scores them with semantic skill matching, and ranks results.

    Parameters:
    - **job_description**: Complete job description text
    - **top_k**: Number of candidates to return (default: 10, max: 100)

    Returns:
    - Parsed job details and ranked candidates with explanations

    Raises:
    - 400: Invalid job description
    - 500: Processing error
    """
    start_time = datetime.utcnow()

    try:
        logger.info(f"Processing match request (top_k={request.top_k})")

        # Step 0: Validate skill scorer (initialized at startup)
        if _skill_scorer is None:
            logger.error("Skill scorer not initialized")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Skill scorer not initialized. Service not ready."
            )
        if _agent_pipeline is None:
            logger.error("Agent pipeline not initialized")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Agent pipeline not initialized. Service not ready."
            )

        # Step 1: Validate vector store
        vs = get_vector_store()
        if not vs:
            logger.error("Vector store not initialized")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Vector store not initialized. Service not ready."
            )

        # Avoid expensive stats calls on every request; rely on startup initialization.
        global _vector_store_total_documents
        if _vector_store_total_documents == 0:
            try:
                stats = vs.get_collection_stats()
                _vector_store_total_documents = int(stats.get('total_documents', 0) or 0)
            except Exception:
                _vector_store_total_documents = 0

        if _vector_store_total_documents == 0:
            logger.error("Vector store is empty")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Vector store is empty. Please ingest resumes first."
            )

        # Step 2: Validate job description
        logger.info("Validating job description...")
        validation = validate_job_description(request.job_description)

        if not validation.is_valid:
            logger.warning(f"Job validation failed: {validation.reason}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid job description: {validation.reason}"
            )

        # Step 2b: Bias check (non-blocking)
        bias_check = detect_bias(request.job_description)

        # Step 3: Parse job description
        # Default to fast parsing for low-latency matching. Enable LLM parsing by setting:
        #   ENABLE_LLM_JOB_PARSER=1
        logger.info("Parsing job description...")
        enable_llm_parser = os.getenv("ENABLE_LLM_JOB_PARSER", "0") == "1"
        if enable_llm_parser:
            parsed_job, jd_token_usage = parse_job_description(request.job_description)
        else:
            parsed_job, jd_token_usage = parse_job_description_fast(request.job_description)
        logger.info(f"Parsed job - Role: {parsed_job.role_category}, Level: {parsed_job.experience_level}")
        logger.info(f"Required skills: {parsed_job.required_skills[:5]}...")

        # Token usage + estimated cost (USD)
        prompt_tokens = int(jd_token_usage.get("prompt_tokens", 0) or 0)
        completion_tokens = int(jd_token_usage.get("completion_tokens", 0) or 0)
        total_tokens = int(jd_token_usage.get("total_tokens", prompt_tokens + completion_tokens) or 0)

        # Best-effort: estimate embedding tokens ~ prompt tokens (query embedding)
        embedding_tokens = prompt_tokens

        # If using the fast parser, token usage is 0 and cost should be 0.
        cost_input = (prompt_tokens / 1000.0) * 0.00015
        cost_output = (completion_tokens / 1000.0) * 0.0006
        cost_embeddings = (embedding_tokens / 1000.0) * 0.00002
        estimated_cost_usd = round(cost_input + cost_output + cost_embeddings, 8) if total_tokens else 0.0

        token_usage = {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "estimated_cost_usd": estimated_cost_usd,
        }

        # Step 4: Retrieve candidates
        logger.info(f"Retrieving candidates (top_k={request.top_k})...")
        candidates = retrieve_candidates(
            parsed_jd=parsed_job,
            top_k=request.top_k,
            apply_filters=False,
            deduplicate=True
        )

        logger.info(f"Retrieved {len(candidates)} candidates")

        # Step 5: Score candidates with skill matching
        logger.info(f"Scoring {len(candidates)} candidates...")
        scored_candidates = []
        resume_text_by_id: Dict[str, str] = {
            c.get("resume_id", "unknown"): (c.get("resume_text", "") or "")
            for c in candidates
            if isinstance(c, dict)
        }

        for rank, candidate in enumerate(candidates, 1):
            try:
                resume_id = candidate.get("resume_id", "unknown")
                eval_result = _agent_pipeline.evaluate_candidate(
                    candidate=candidate,
                    parsed_job=parsed_job,
                    resume_text_fallback=resume_text_by_id.get(resume_id, ""),
                )

                top_skills_raw = eval_result.skill.top_skills_raw
                candidate_skills = eval_result.skill.candidate_skills

                if os.getenv("DEBUG_SKILL_LOGS", "0") == "1":
                    logger.info(f"Candidate {candidate.get('resume_id')} - top_skills_raw: {top_skills_raw}")
                    logger.info(f"Candidate {candidate.get('resume_id')} - candidate_skills: {candidate_skills}")
                    logger.info(
                        f"Candidate {candidate.get('resume_id')} - resume_text preview: "
                        f"{candidate.get('resume_text', '')[:100]}"
                    )
                else:
                    logger.debug(f"Candidate {candidate.get('resume_id')} - top_skills_raw: {top_skills_raw}")
                    logger.debug(f"Candidate {candidate.get('resume_id')} - candidate_skills: {candidate_skills}")

                scored_candidates.append(
                    CandidateMatch(
                        rank=rank,
                        resume_id=resume_id,
                        final_score=eval_result.final_score,
                        semantic_score=eval_result.semantic_score,
                        skill_score=eval_result.skill_score,
                        experience_level=candidate.get("metadata", {}).get("experience_level", "unknown"),
                        role_category=candidate.get("metadata", {}).get("role_category", "unknown"),
                        matched_skills=[
                            (s.upper() if str(s).strip().lower() in {"api", "sql", "ux", "ui", "hris", "aws", "gcp"} else str(s).strip().title())
                            for s in (eval_result.matched_skills or [])
                            if str(s).strip()
                        ],
                        missing_skills=[
                            (s.upper() if str(s).strip().lower() in {"api", "sql", "ux", "ui", "hris", "aws", "gcp"} else str(s).strip().title())
                            for s in (eval_result.missing_skills or [])
                            if str(s).strip()
                        ],
                        skill_coverage=eval_result.skill_coverage,
                        explanation=eval_result.explanation
                    )
                )

            except Exception as e:
                logger.error(f"Error scoring candidate {candidate.get('resume_id')}: {str(e)}")
                continue

        # Sort by final score
        scored_candidates.sort(key=lambda x: x.final_score, reverse=True)

        # Update ranks after sorting
        for i, candidate in enumerate(scored_candidates, 1):
            candidate.rank = i

        # Step 5b: LLM-based explanation generation (optional; can add latency)
        # Enable with: ENABLE_LLM_EXPLANATIONS=1
        # Keep under a time budget to preserve overall latency targets.
        enable_llm_explanations = os.getenv("ENABLE_LLM_EXPLANATIONS", "0") == "1"
        elapsed_so_far = (datetime.utcnow() - start_time).total_seconds()
        if enable_llm_explanations and _explanation_agent is not None and elapsed_so_far < 2.5 and scored_candidates:
            try:
                # Only generate for TOP 1 by default to keep latency low.
                candidates_payload = [
                    {
                        "resume_id": c.resume_id,
                        "experience_level": c.experience_level,
                        "role_category": c.role_category,
                        "semantic_score": c.semantic_score,
                        "skill_score": c.skill_score,
                        "skill_coverage": c.skill_coverage,
                        "matched_skills": c.matched_skills,
                        "missing_skills": c.missing_skills,
                    }
                    for c in scored_candidates[:1]
                ]

                llm_explanations = _explanation_agent.generate_explanations_batch(
                    candidates=candidates_payload,
                    job_data={},
                )
                if llm_explanations:
                    for c in scored_candidates[:1]:
                        base = llm_explanations.get(c.resume_id) or c.explanation
                        strengths = [s for s in (c.matched_skills or []) if str(s).strip()][:3]
                        gaps = [s for s in (c.missing_skills or []) if str(s).strip()][:3]
                        if strengths or gaps:
                            base += "\n\nStrengths:\n"
                            base += "\n".join([f"- {s}" for s in strengths]) if strengths else "- Not enough signal"
                            base += "\n\nGaps:\n"
                            base += "\n".join([f"- {g}" for g in gaps]) if gaps else "- None highlighted"
                        c.explanation = base
                else:
                    # Per-candidate fallback (still safe; uses template if OpenAI fails)
                    for c in scored_candidates[:1]:
                        c.explanation = _explanation_agent.generate_explanation(
                            candidate_data={
                                "resume_id": c.resume_id,
                                "experience_level": c.experience_level,
                                "role_category": c.role_category,
                                "semantic_score": c.semantic_score,
                                "skill_score": c.skill_score,
                                "skill_coverage": c.skill_coverage,
                                "matched_skills": c.matched_skills,
                                "missing_skills": c.missing_skills,
                            },
                            job_data={},
                        )
            except Exception as e:
                logger.warning(f"Explanation generation skipped due to error: {e!r}")

        # Step 6: Soft skills assessment (optional; can be expensive)
        # Enabled only when:
        #   ENABLE_SOFT_SKILLS=1
        # And only if we are still within a time budget to keep end-to-end latency low.
        enable_soft_skills = os.getenv("ENABLE_SOFT_SKILLS", "0") == "1"
        elapsed_so_far = (datetime.utcnow() - start_time).total_seconds()
        if enable_soft_skills and elapsed_so_far < 3.5 and len(scored_candidates) > 0:
            cm = scored_candidates[0]
            resume_text = resume_text_by_id.get(cm.resume_id, "")
            if not (resume_text or "").strip():
                logger.warning(f"Soft skills assessment: missing resume_text for resume_id={cm.resume_id}")
            cm.soft_skills_assessment = await assess_soft_skills(
                resume_text=resume_text,
                job_description=request.job_description,
            )

        execution_time = (datetime.utcnow() - start_time).total_seconds()
        candidates_per_second = (
            round(len(scored_candidates) / execution_time, 2) if execution_time > 0 else 0.0
        )
        performance = {
            "candidates_per_second": candidates_per_second,
            "total_candidates": len(scored_candidates),
            "execution_time_seconds": round(execution_time, 2),
        }

        logger.info(f"Matching completed in {execution_time:.2f}s - {len(scored_candidates)} candidates")

        return MatchResponse(
            status="success",
            query_summary=parsed_job.job_summary,
            parsed_job={
                "experience_level": parsed_job.experience_level,
                "role_category": parsed_job.role_category,
                "required_skills": parsed_job.required_skills,
                "preferred_skills": parsed_job.preferred_skills
            },
            bias_check=bias_check,
            token_usage=token_usage,
            candidates=scored_candidates,
            total_found=len(scored_candidates),
            execution_time=execution_time,
            performance=performance,
            message=f"Successfully found and ranked {len(scored_candidates)} candidates"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Matching error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Job matching error: {str(e)}"
        )


@app.get("/", tags=["Root"])
async def root():
    """API root endpoint with documentation links."""
    return {
        "message": "Resume Matching Microservice",
        "version": "1.0.0",
        "service": "matching",
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": "/openapi.json",
        "endpoints": {
            "health": "GET /health",
            "match": "POST /match"
        }
    }


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser(
        description="Resume Matching Microservice",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run on default port 8001
  python -m src.services.matching_service

  # Run on custom port
  python -m src.services.matching_service --port 8002

  # Run with hot reload (development)
  python -m src.services.matching_service --reload
        """
    )

    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host to bind the service to (default: 127.0.0.1)"
    )

    parser.add_argument(
        "--port",
        type=int,
        default=8001,
        help="Port to bind the service to (default: 8001)"
    )

    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload on code changes (development mode)"
    )

    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of worker processes (default: 1)"
    )

    args = parser.parse_args()

    # Validate port range
    if not (1 <= args.port <= 65535):
        logger.error(f"Invalid port number: {args.port}. Must be between 1 and 65535.")
        sys.exit(1)

    logger.info(f"Starting Matching Microservice on {args.host}:{args.port}")
    logger.info(f"Documentation available at http://{args.host}:{args.port}/docs")

    uvicorn.run(
        "src.services.matching_service:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=1 if args.reload else args.workers,
        log_level="info"
    )

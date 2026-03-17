"""
Legacy/alternative backend run mode (monolith).

Primary recommended backend mode for this repo is:
  - `gateway.py` (API Gateway, port 8000) forwarding to
  - `src/services/matching_service.py` (Matching Service, port 8001)

This module remains as a single-process FastAPI app for convenience, but it is a
separate code path from the matching microservice.
"""
import logging
import os
import zlib
from datetime import datetime

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.ingestion.pipeline import run_ingestion_pipeline
from src.retrieval.job_parser import parse_job_description, parse_job_description_fast
from src.retrieval.candidate_retriever import retrieve_candidates
from src.agents.skill_scorer import compute_skill_overlap_score
from src.guardrails.input_validator import validate_job_description
from src.embeddings.vector_store import get_collection_stats, init_vector_store, get_vector_store
from src.api.schemas import (
    IngestRequest,
    IngestResponse,
    MatchRequest,
    MatchFilters,
    MatchResponse,
    CandidateResult,
    StatsResponse,
    HealthResponse,
    CategoryStat,
    ErrorResponse,
)

logger = logging.getLogger(__name__)

# Global vector store instance
_vector_store_instance = None
_stats_cache = {"ts": None, "data": None}

# Initialize FastAPI app
app = FastAPI(
    title="Resume Matching System API",
    description="AI-powered resume matching system with semantic search and skill scoring",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Startup Event
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize vector store on server startup and store globally."""
    global _vector_store_instance
    try:
        logger.info("Initializing vector store...")
        init_vector_store()
        _vector_store_instance = get_vector_store()
        if _vector_store_instance:
            logger.info("Vector store initialized and stored globally!")
            stats = _vector_store_instance.get_collection_stats()
            logger.info(
                f"Vector store ready with {stats.get('total_documents', 0)} documents "
                f"from {stats.get('total_resumes', 0)} resumes"
            )
        else:
            logger.warning("Vector store initialization returned None")
    except Exception as e:
        logger.error(f"Failed to initialize vector store: {str(e)}", exc_info=True)


# ============================================================================
# Endpoints
# ============================================================================

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns basic health status and API version.
    """
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.utcnow().isoformat()
    )


@app.post("/api/v1/ingest", response_model=IngestResponse, tags=["Ingestion"])
async def ingest_resumes(request: IngestRequest) -> IngestResponse:
    """
    Trigger resume ingestion pipeline.

    Loads resumes from CSV, validates, extracts metadata, chunks, and indexes them.

    Parameters:
    - **csv_path**: Path to CSV file with columns (ID, Resume_str, Category)

    Returns:
    - Ingestion status and statistics

    Raises:
    - 400: Invalid CSV path
    - 500: Processing error
    """
    try:
        logger.info(f"Starting ingestion pipeline for: {request.csv_path}")

        # Run ingestion pipeline
        summary = run_ingestion_pipeline(
            csv_path=request.csv_path,
            progress_interval=50,
            extract_metadata=True,
            skip_invalid=True
        )

        logger.info(f"Ingestion completed: {summary['total_processed']} processed")

        return IngestResponse(
            status="success",
            total_processed=summary.get("total_processed", 0),
            total_failed=summary.get("total_failed", 0),
            total_chunks=summary.get("total_chunks", 0),
            execution_time=summary.get("execution_time", 0),
            timestamp=summary.get("timestamp", datetime.utcnow().isoformat()),
            message=f"Successfully ingested {summary.get('total_processed', 0)} resumes "
                   f"into {summary.get('total_chunks', 0)} chunks"
        )

    except FileNotFoundError as e:
        logger.error(f"File not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"CSV file not found: {request.csv_path}"
        )
    except Exception as e:
        logger.error(f"Ingestion error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion pipeline error: {str(e)}"
        )


@app.post("/api/v1/match", response_model=MatchResponse, tags=["Matching"])
async def match_job_candidates(request: MatchRequest) -> MatchResponse:
    """
    Match job description with candidate resumes.

    Validates job description, parses it, finds matching candidates from vector store,
    scores them with semantic skill matching, and ranks results.

    Parameters:
    - **job_description**: Complete job description text
    - **top_k**: Number of candidates to return (default: 10, max: 100)
    - **filters**: Optional metadata filters (experience_level, role_category)

    Returns:
    - Parsed job details and ranked candidates with explanations

    Raises:
    - 400: Invalid job description
    - 500: Processing error
    """
    start_time = datetime.utcnow()

    try:
        # Ensure vector store is initialized (startup should do this, but keep a safe fallback)
        global _vector_store_instance
        if _vector_store_instance is None:
            logger.info("Vector store not initialized yet; initializing...")
            init_vector_store()
            _vector_store_instance = get_vector_store()

        # Fast sanity check (avoid per-request expensive stats calls)
        if get_vector_store() is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Vector store is not initialized. Please restart the API and/or ingest resumes.",
            )

        # Step 1: Validate job description
        logger.info("Validating job description...")
        validation = validate_job_description(request.job_description)

        if not validation.is_valid:
            logger.warning(f"Job validation failed: {validation.reason}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid job description: {validation.reason}"
        )

        # Step 2: Parse job description
        logger.info("Parsing job description...")
        enable_llm_parser = os.getenv("ENABLE_LLM_JOB_PARSER", "0") == "1"
        if enable_llm_parser:
            parsed_job, _jd_token_usage = parse_job_description(request.job_description)
        else:
            parsed_job, _jd_token_usage = parse_job_description_fast(request.job_description)
        logger.info(f"Parsed job - Role: {parsed_job.role_category}, Level: {parsed_job.experience_level}")
        logger.info(f"Required skills: {parsed_job.required_skills[:5]}...")
        logger.info(f"Preferred skills: {parsed_job.preferred_skills}")

        # Step 3: Retrieve candidates
        logger.info(f"Retrieving candidates (top_k={request.top_k})...")
        filters = {}
        if request.filters:
            if request.filters.experience_level:
                filters["experience_level"] = request.filters.experience_level
            if request.filters.role_category:
                filters["role_category"] = request.filters.role_category

        candidates = retrieve_candidates(
            parsed_jd=parsed_job,
            top_k=request.top_k,
            apply_filters=bool(filters),
            deduplicate=True
        )

        logger.info(f"retrieve_candidates returned {len(candidates)} candidates")

        # Step 4: Score candidates with skill matching
        logger.info(f"Scoring {len(candidates)} candidates...")
        scored_candidates = []

        for rank, candidate in enumerate(candidates, 1):
            try:
                # Get candidate skills from metadata - convert comma-separated string to list
                top_skills_raw = candidate.get("metadata", {}).get("top_skills", "")
                if isinstance(top_skills_raw, str) and top_skills_raw:
                    candidate_skills = [s.strip() for s in top_skills_raw.split(",")]
                elif isinstance(top_skills_raw, list):
                    candidate_skills = top_skills_raw
                else:
                    candidate_skills = []

                # Fallback: extract from resume text directly (helps non-tech resumes with missing metadata)
                if not candidate_skills:
                    resume_text = (candidate.get("resume_text", "") or "").lower()
                    candidate_skills = [
                        skill for skill in parsed_job.required_skills
                        if isinstance(skill, str) and skill.strip() and (skill.lower() in resume_text)
                    ]

                # Compute skill overlap score
                skill_score = compute_skill_overlap_score(
                    candidate_skills=candidate_skills,
                    required_skills=parsed_job.required_skills,
                    preferred_skills=parsed_job.preferred_skills
                )

                # Calculate overall score (70% semantic + 30% skill)
                semantic_score = candidate.get("score", 0.5)
                try:
                    semantic_score_f = float(semantic_score)
                except Exception:
                    semantic_score_f = 0.5
                if semantic_score_f < 0:
                    semantic_score_f = 0.0
                elif semantic_score_f > 1:
                    semantic_score_f = 1.0
                # Normalize semantic score to 0-100
                semantic_score_normalized = semantic_score_f * 100
                overall_score = (semantic_score_normalized * 0.7) + (skill_score.overall_score * 0.3)

                # Build human-friendly explanation (no raw percentages/scores).
                matched = [str(s).strip() for s in (skill_score.matched_skills or []) if str(s).strip()]
                missing_required = [
                    str(s).strip()
                    for s in (skill_score.missing_required_skills or [])
                    if str(s).strip()
                ]

                strengths_txt = ", ".join(matched[:3]) if matched else ""
                gaps_txt = ", ".join(missing_required[:3]) if missing_required else ""

                resume_id = str(candidate.get("resume_id") or "unknown")
                opener_variants = [
                    "This profile shows good alignment with the role's priorities.",
                    "Overall, the candidate appears to be a reasonable fit for the core requirements.",
                    "At a high level, this candidate demonstrates relevant overlap for the position.",
                    "The candidate's background aligns with several of the role's key needs.",
                ]
                opener = opener_variants[zlib.crc32(resume_id.encode("utf-8")) % len(opener_variants)]

                sentences: list[str] = [opener]
                if strengths_txt:
                    sentences.append(f"Strengths are most evident in {strengths_txt}, which map to day-to-day responsibilities.")
                else:
                    sentences.append("Transferable experience is likely present, though specific skill signals are limited in the available text.")

                exp_level = str(candidate.get("metadata", {}).get("experience_level", "") or "").strip().lower()
                role_cat = str(candidate.get("metadata", {}).get("role_category", "") or "").strip().lower()
                if exp_level or role_cat:
                    label = " ".join([p for p in [exp_level, role_cat] if p]) or "this role"
                    sentences.append(f"The overall profile suggests they can operate effectively in a {label} context.")

                if gaps_txt:
                    sentences.append(f"Areas to validate in screening include {gaps_txt}, where evidence is less clear.")
                else:
                    sentences.append("No major gaps stand out from the signals provided.")

                explanation = " ".join(sentences[:4]).strip()

                # Add concise strengths/gaps bullets (frontend should render newlines with pre-line).
                strengths_bullets = matched[:3] if matched else []
                gaps_bullets = missing_required[:3] if missing_required else []

                if strengths_bullets or gaps_bullets:
                    explanation += "\n\nStrengths:\n"
                    if strengths_bullets:
                        explanation += "\n".join([f"- {s}" for s in strengths_bullets])
                    else:
                        explanation += "- Not enough signal"

                    explanation += "\n\nGaps:\n"
                    if gaps_bullets:
                        explanation += "\n".join([f"- {g}" for g in gaps_bullets])
                    else:
                        explanation += "- None highlighted"

                scored_candidates.append(
                    CandidateResult(
                        rank=rank,
                        resume_id=candidate.get("resume_id", "unknown"),
                        final_score=round(overall_score, 2),
                        semantic_score=round(semantic_score_normalized, 2),
                        skill_score=round(skill_score.overall_score, 2),
                        experience_level=candidate.get("metadata", {}).get("experience_level", "unknown"),
                        role_category=candidate.get("metadata", {}).get("role_category", "unknown"),
                        education=candidate.get("metadata", {}).get("education", "unknown"),
                        matched_skills=skill_score.matched_skills[:10],
                        missing_skills=skill_score.missing_required_skills,
                        skill_coverage=round(skill_score.required_match_pct, 2),
                        explanation=explanation.strip()
                    )
                )

            except Exception as e:
                logger.error(f"Error scoring candidate {candidate.get('resume_id')}: {str(e)}")
                continue

        # Sort by overall score
        scored_candidates.sort(key=lambda x: x.final_score, reverse=True)

        # Update ranks after sorting
        for i, candidate in enumerate(scored_candidates, 1):
            candidate.rank = i

        execution_time = (datetime.utcnow() - start_time).total_seconds()
        candidates_per_second = (
            round(len(scored_candidates) / execution_time, 2) if execution_time > 0 else 0.0
        )
        performance = {
            "candidates_per_second": candidates_per_second,
            "total_candidates": len(scored_candidates),
            "execution_time_seconds": round(execution_time, 2),
        }

        logger.info(f"Matching completed in {execution_time:.2f}s")

        return MatchResponse(
            status="success",
            query_summary=parsed_job.job_summary,
            parsed_job={
                "experience_level": parsed_job.experience_level,
                "role_category": parsed_job.role_category,
                "required_skills": parsed_job.required_skills,
                "preferred_skills": parsed_job.preferred_skills
            },
            candidates=scored_candidates,
            total_found=len(scored_candidates),
            execution_time=execution_time,
            performance=performance,
            message=f"Successfully found and ranked {len(scored_candidates)} candidates"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Matching error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Job matching error: {str(e)}"
        )


@app.get("/api/v1/stats", response_model=StatsResponse, tags=["Analytics"])
async def get_statistics() -> StatsResponse:
    """
    Get vector store statistics and analytics.

    Returns:
    - Total resumes indexed
    - Distribution by category, experience level, role category

    Raises:
    - 500: If vector store is not initialized
    """
    try:
        logger.info("Fetching vector store statistics...")

        global _stats_cache, _vector_store_instance
        now = datetime.utcnow()
        if _stats_cache["ts"] and _stats_cache["data"]:
            age_s = (now - _stats_cache["ts"]).total_seconds()
            if age_s < 30:
                return _stats_cache["data"]

        if _vector_store_instance is None:
            init_vector_store()
            _vector_store_instance = get_vector_store()

        vector_store = _vector_store_instance
        if vector_store is None:
            raise RuntimeError("Vector store is not initialized")

        # Get statistics
        stats = vector_store.get_collection_stats()

        if not stats or stats.get("total_documents", 0) == 0:
            return StatsResponse(
                status="success",
                total_resumes=0,
                total_chunks=0,
                categories=[],
                experience_levels=[],
                role_categories=[],
                timestamp=datetime.utcnow().isoformat()
            )

        # Process category stats
        total_docs = stats.get("total_documents", 1)

        categories = [
            CategoryStat(
                name=name,
                count=count,
                percentage=round((count / total_docs) * 100, 2)
            )
            for name, count in stats.get("categories", {}).items()
        ]

        experience_levels = [
            CategoryStat(
                name=name,
                count=count,
                percentage=round((count / total_docs) * 100, 2)
            )
            for name, count in stats.get("experience_levels", {}).items()
        ]

        role_categories = [
            CategoryStat(
                name=name,
                count=count,
                percentage=round((count / total_docs) * 100, 2)
            )
            for name, count in stats.get("role_categories", {}).items()
        ]

        logger.info(f"Retrieved stats: {stats.get('total_resumes')} resumes, "
                   f"{total_docs} chunks")

        response = StatsResponse(
            status="success",
            total_resumes=stats.get("total_resumes", 0),
            total_chunks=total_docs,
            categories=categories,
            experience_levels=experience_levels,
            role_categories=role_categories,
            timestamp=datetime.utcnow().isoformat()
        )
        _stats_cache = {"ts": now, "data": response}
        return response

    except Exception as e:
        logger.error(f"Error fetching statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Statistics retrieval error: {str(e)}"
        )


# ============================================================================
# Root endpoints
# ============================================================================

@app.get("/", tags=["Root"])
async def root():
    """API root endpoint with documentation links."""
    return {
        "message": "Resume Matching System API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": "/openapi.json",
        "endpoints": {
            "health": "GET /health",
            "ingest": "POST /api/v1/ingest",
            "match": "POST /api/v1/match",
            "stats": "GET /api/v1/stats"
        }
    }


@app.get("/api/v1", tags=["Root"])
async def api_root():
    """API v1 root endpoint."""
    return {
        "version": "1.0.0",
        "endpoints": {
            "ingest": "POST /api/v1/ingest - Trigger resume ingestion pipeline",
            "match": "POST /api/v1/match - Match job with candidates",
            "stats": "GET /api/v1/stats - Get vector store statistics"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )

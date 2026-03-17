"""
Pydantic schemas for Resume Matching System API.
Contains all request and response models for REST endpoints.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, validator


# ============================================================================
# Ingestion Endpoint Models
# ============================================================================

class IngestRequest(BaseModel):
    """Request model for resume ingestion endpoint."""
    csv_path: str = Field(..., description="Path to CSV file with resumes (columns: ID, Resume_str, Category)")

    class Config:
        json_schema_extra = {
            "example": {
                "csv_path": "data/resumes/resume_dataset.csv"
            }
        }


class IngestResponse(BaseModel):
    """Response model for resume ingestion endpoint."""
    status: str = Field(..., description="Status of ingestion operation (success/error)")
    total_processed: int = Field(..., description="Number of resumes successfully processed")
    total_failed: int = Field(..., description="Number of resumes that failed processing")
    total_chunks: int = Field(..., description="Total document chunks created from resumes")
    execution_time: float = Field(..., description="Execution time in seconds")
    timestamp: str = Field(..., description="ISO format timestamp of operation")
    message: str = Field(..., description="Human-readable status message")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "total_processed": 100,
                "total_failed": 5,
                "total_chunks": 450,
                "execution_time": 125.34,
                "timestamp": "2024-03-15T10:30:00Z",
                "message": "Successfully ingested 100 resumes"
            }
        }


# ============================================================================
# Job Matching Endpoint Models
# ============================================================================

class MatchFilters(BaseModel):
    """Optional metadata filters for job matching."""
    experience_level: Optional[str] = Field(
        None,
        description="Filter by experience level: entry, mid, senior, lead"
    )
    role_category: Optional[str] = Field(
        None,
        description="Filter by role category: backend, frontend, data_science, etc."
    )

    class Config:
        json_schema_extra = {
            "example": {
                "experience_level": "senior",
                "role_category": "backend"
            }
        }


class MatchRequest(BaseModel):
    """Request model for job candidate matching endpoint."""
    job_description: str = Field(..., description="Full job description text to match against candidates")
    top_k: int = Field(
        10,
        ge=1,
        le=100,
        description="Number of top candidates to return (1-100)"
    )
    filters: Optional[MatchFilters] = Field(
        None,
        description="Optional metadata filters to narrow candidate pool"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "job_description": "We are looking for a senior Python backend engineer with 8+ years...",
                "top_k": 10,
                "filters": {
                    "experience_level": "senior",
                    "role_category": "backend"
                }
            }
        }


class CandidateResult(BaseModel):
    """Single candidate match result with comprehensive scoring."""
    rank: int = Field(..., description="Ranking position in results (1-based)")
    resume_id: str = Field(..., description="Unique identifier for the resume")
    final_score: float = Field(
        ...,
        ge=0,
        le=100,
        description="Final weighted score combining semantic and skill matching (0-100)"
    )
    semantic_score: float = Field(
        ...,
        ge=0,
        le=100,
        description="Semantic similarity score between job and resume (0-100)"
    )
    skill_score: float = Field(
        ...,
        ge=0,
        le=100,
        description="Skill overlap and match score (0-100)"
    )
    experience_level: str = Field(
        ...,
        description="Candidate experience level: entry, mid, senior, or lead"
    )
    role_category: str = Field(
        ...,
        description="Candidate role category: backend, frontend, data_science, etc."
    )
    education: str = Field(
        ...,
        description="Highest education level: high_school, bachelors, masters, phd, or unknown"
    )
    matched_skills: List[str] = Field(
        ...,
        description="List of skills matched between job and candidate resume"
    )
    missing_skills: List[str] = Field(
        ...,
        description="List of required skills missing from candidate resume"
    )
    skill_coverage: float = Field(
        ...,
        ge=0,
        le=100,
        description="Percentage of required skills that match candidate skills"
    )
    explanation: str = Field(
        ...,
        description="Brief human-readable explanation of the match"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "rank": 1,
                "resume_id": "resume_001",
                "final_score": 88.75,
                "semantic_score": 92.0,
                "skill_score": 85.5,
                "experience_level": "senior",
                "role_category": "backend",
                "education": "bachelors",
                "matched_skills": ["Python", "Django", "PostgreSQL", "Docker"],
                "missing_skills": ["Kubernetes"],
                "skill_coverage": 85.0,
                "explanation": "Excellent semantic match with 85% required skills coverage. Missing Kubernetes certification."
            }
        }


class MatchResponse(BaseModel):
    """Response model for job candidate matching endpoint."""
    status: str = Field(..., description="Status of matching operation (success/error)")
    query_summary: str = Field(..., description="One-sentence summary of the parsed job description")
    parsed_job: Dict[str, Any] = Field(
        ...,
        description="Parsed job details including required/preferred skills and experience level"
    )
    candidates: List[CandidateResult] = Field(..., description="Ranked candidate matches")
    total_found: int = Field(..., description="Total number of matching candidates found")
    execution_time: float = Field(..., description="Total execution time in seconds")
    performance: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Performance metrics such as candidates per second",
    )
    message: str = Field(..., description="Human-readable status message")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "query_summary": "Senior backend engineer with Python and PostgreSQL experience",
                "parsed_job": {
                    "experience_level": "senior",
                    "role_category": "backend",
                    "required_skills": ["Python", "PostgreSQL", "Docker"],
                    "preferred_skills": ["Kubernetes", "AWS"]
                },
                "candidates": [],
                "total_found": 5,
                "execution_time": 2.34,
                "message": "Successfully found and ranked 5 candidates"
            }
        }


# ============================================================================
# Statistics Endpoint Models
# ============================================================================

class CategoryStat(BaseModel):
    """Statistics for a single category or attribute."""
    name: str = Field(..., description="Category or attribute name")
    count: int = Field(..., description="Number of items in this category")
    percentage: float = Field(..., description="Percentage of total items")


class StatsResponse(BaseModel):
    """Response model for vector store statistics endpoint."""
    status: str = Field(..., description="Status of the statistics query (success/error)")
    total_resumes: int = Field(..., description="Total number of unique resumes indexed")
    total_chunks: int = Field(..., description="Total number of document chunks in vector store")
    categories: List[CategoryStat] = Field(..., description="Breakdown by resume category")
    experience_levels: List[CategoryStat] = Field(..., description="Distribution of experience levels")
    role_categories: List[CategoryStat] = Field(..., description="Distribution of role categories")
    timestamp: str = Field(..., description="ISO format timestamp of query")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "total_resumes": 100,
                "total_chunks": 450,
                "categories": [
                    {"name": "Backend", "count": 40, "percentage": 40.0},
                    {"name": "Frontend", "count": 30, "percentage": 30.0}
                ],
                "experience_levels": [
                    {"name": "senior", "count": 35, "percentage": 35.0}
                ],
                "role_categories": [
                    {"name": "backend", "count": 40, "percentage": 40.0}
                ],
                "timestamp": "2024-03-15T10:30:00Z"
            }
        }


# ============================================================================
# Health Check Endpoint Models
# ============================================================================

class HealthResponse(BaseModel):
    """Response model for health check endpoint."""
    status: str = Field(..., description="Health status: healthy or unhealthy")
    version: str = Field(..., description="API version")
    timestamp: str = Field(..., description="ISO format response timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": "2024-03-15T10:30:00Z"
            }
        }


# ============================================================================
# Error Response Models
# ============================================================================

class ErrorResponse(BaseModel):
    """Response model for error responses across all endpoints."""
    status: str = Field(..., description="Error status (always 'error')")
    error_code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional additional error context or debugging information"
    )
    timestamp: str = Field(..., description="ISO format timestamp of error")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "error",
                "error_code": "INVALID_JOB_DESCRIPTION",
                "message": "Job description must contain at least 20 words",
                "details": {
                    "word_count": 15,
                    "minimum_required": 20
                },
                "timestamp": "2024-03-15T10:30:00Z"
            }
        }

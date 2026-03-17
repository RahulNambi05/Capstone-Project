"""
Pydantic models and schemas for the Resume Matching System.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ResumeData(BaseModel):
    """Resume data model."""
    id: Optional[str] = None
    content: str = Field(..., description="Full resume text content")
    file_name: str = Field(..., description="Original resume file name")
    extracted_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "content": "John Doe...",
                "file_name": "john_doe_resume.pdf"
            }
        }


class JobDescription(BaseModel):
    """Job description model."""
    id: Optional[str] = None
    title: str = Field(..., description="Job title")
    content: str = Field(..., description="Full job description text")
    company: Optional[str] = Field(None, description="Company name")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Senior Python Developer",
                "content": "We are looking for...",
                "company": "Tech Company"
            }
        }


class MatchResult(BaseModel):
    """Match result between resume and job description."""
    resume_id: str
    job_id: str
    score: float = Field(..., ge=0, le=1, description="Match score between 0 and 1")
    summary: str = Field(..., description="Summary of the match")
    matching_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    match_percentage: float = Field(..., ge=0, le=100)

    class Config:
        json_schema_extra = {
            "example": {
                "resume_id": "resume_1",
                "job_id": "job_1",
                "score": 0.85,
                "summary": "Strong match with key skills...",
                "matching_skills": ["Python", "FastAPI"],
                "missing_skills": ["Kubernetes"],
                "match_percentage": 85.0
            }
        }


class UploadResponse(BaseModel):
    """Response model for file uploads."""
    file_name: str
    document_id: str
    message: str

    class Config:
        json_schema_extra = {
            "example": {
                "file_name": "resume.pdf",
                "document_id": "doc_123",
                "message": "File uploaded successfully"
            }
        }

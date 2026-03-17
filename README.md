<!--
Professional README for the Resume Intelligence & Candidate Matching System.
Goal: copy/paste-friendly, minimal unicode (avoid Windows console encoding issues).
-->

# Resume Intelligence & Candidate Matching System

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-4-646CFF?logo=vite&logoColor=white)](https://vitejs.dev/)
[![ChromaDB](https://img.shields.io/badge/Vector%20Store-ChromaDB-FF6B6B)](https://www.trychroma.com/)

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Tech Stack](#tech-stack)
4. [Setup & Installation](#setup--installation)
5. [Data Ingestion](#data-ingestion)
6. [Start Services](#start-services)
7. [Start Frontend](#start-frontend)
8. [API Endpoints](#api-endpoints)
9. [Example Queries](#example-queries)
10. [Features](#features)
11. [Project Structure](#project-structure)
12. [Dataset Info](#dataset-info)
13. [Known Limitations](#known-limitations)

## Overview

This project is an AI-powered system for resume intelligence and candidate matching. It ingests resumes into a local vector store, parses job descriptions into structured requirements, retrieves semantically relevant candidates, and returns ranked results with skill coverage and explanations.

Core capabilities:
- Semantic candidate retrieval using embeddings and vector similarity search
- LLM-assisted job parsing (required skills, preferred skills, experience level, role category)
- Skill overlap scoring using a SentenceTransformer model
- FastAPI gateway + matching microservice architecture
- React frontend for matching, results review, and analytics

## Architecture

Text-based diagram:

```
                           +----------------------+
                           |  React Frontend      |
                           |  http://localhost:5173
                           +----------+-----------+
                                      |
                                      | REST (JSON)
                                      v
                           +----------------------+
                           |  API Gateway (8000)  |
                           |  gateway.py (FastAPI)|
                           +----------+-----------+
                                      |
                                      | forwards /api/v1/* to service
                                      v
                           +----------------------+
                           | Matching Service     |
                           | src/services/...     |
                           | http://localhost:8001
                           +----+------------+----+
                                |            |
                                |            +-------------------+
                                |                                |
                                v                                v
                     +-------------------+             +-------------------+
                     | Vector Store      |             | OpenAI API        |
                     | ChromaDB (persist)|             | - JD parsing      |
                     | ./data/chroma_db  |             | - soft skills     |
                     +-------------------+             +-------------------+
                                |
                                v
                     +-------------------+
                     | Resume Dataset    |
                     | CSV ingestion     |
                     +-------------------+
```

## Code Map

- Recommended backend mode: `gateway.py` (port 8000) + `src/services/matching_service.py` (port 8001)
- Legacy/alternative: monolith API in `src/api/main.py` (started by `main.py`)
- Full module map: see `docs/CODEMAP.md`

## Tech Stack

| Layer | Technology | Notes |
|------:|------------|------|
| Frontend | React + Vite | Match flow, results UI, analytics dashboard |
| API Gateway | FastAPI + httpx | Single entry point on port 8000 |
| Matching Service | FastAPI | Matching pipeline, scoring, health, stats |
| Vector Store | ChromaDB | Persistent embeddings store in `./data/chroma_db` |
| LLM integration | `langchain-openai` | Job parsing and optional assessments |
| Skill scoring | `sentence-transformers` | Semantic skill overlap scoring |
| Data processing | Pandas | CSV ingestion and preprocessing |

## Setup & Installation

### Clone repo

```bash
git clone <your-repo-url>
cd "AI RPOJECT"
```

### Create virtual environment

Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Install backend dependencies

```bash
pip install -r requirements.txt
```

### Configure environment

Copy the example env file:
```bash
copy .env.example .env
```

Add your OpenAI key:
```env
OPENAI_API_KEY=sk-...
```

Note: the backend loads config from `src/core/config.py` and requires `OPENAI_API_KEY` to be set.

## Data Ingestion

### Download Kaggle dataset

Download a resume dataset CSV from Kaggle (commonly named something like `Resume.csv`) and place it in the repository under:

```text
data/resumes.csv
```

Expected CSV columns (default pipeline settings):
- `ID` (unique resume identifier)
- `Resume_str` (full resume text)
- `Category` (label/category)

If your dataset uses different column names, you can customize them when calling the pipeline.

### Run ingestion command

Recommended: run the ingestion pipeline directly (fast mode without per-resume metadata LLM calls):

```bash
python -c "from src.ingestion.pipeline import run_ingestion_pipeline; import json; print(json.dumps(run_ingestion_pipeline(csv_path='data/resumes.csv', extract_metadata=False, skip_invalid=True), indent=2))"
```

Notes:
- `extract_metadata=False` is significantly faster and avoids per-resume LLM calls.
- Setting `extract_metadata=True` enables richer metadata extraction, but is slower and uses the OpenAI API for each resume.

### Expected output

You should see a JSON summary similar to:

```json
{
  "total_processed": 1000,
  "total_failed": 0,
  "total_chunks": 38000,
  "execution_time": 123.45,
  "timestamp": "2026-03-17T12:34:56.789Z",
  "details": { "chunks_per_resume": 38 }
}
```

After ingestion, ChromaDB persistence files will appear under:
```text
data/chroma_db/
```

## Start Services

### Windows scripts

Start gateway + matching service:
```powershell
.\start_services.bat
```

Start everything (gateway + matching + frontend):
```powershell
.\start_all_services.bat
```

### Individual commands (separate terminals)

Terminal 1 - Matching Service (port 8001):
```bash
python -m uvicorn src.services.matching_service:app --port 8001
```

Terminal 2 - API Gateway (port 8000):
```bash
python -m uvicorn gateway:app --port 8000
```

Useful URLs:
- Frontend: `http://localhost:5173`
- Gateway docs: `http://localhost:8000/docs`
- Matching service docs: `http://localhost:8001/docs`
- Health: `http://localhost:8000/health`

### Performance knobs (optional)

To keep matching fast by default, the matching service supports toggles:

- `ENABLE_LLM_JOB_PARSER=1` to use LLM job parsing (slower; default is fast parser)
- `ENABLE_LLM_EXPLANATIONS=1` to generate LLM explanations (time-budgeted; default off)
- `ENABLE_SOFT_SKILLS=1` to run soft skills assessment (time-budgeted; default off)

## Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on `http://localhost:5173` (Vite default).

## API Endpoints

All frontend traffic should go through the gateway at `http://localhost:8000`.

| Method | Path | Description |
|:------:|------|-------------|
| POST | `/api/v1/match` | Match a job description to top candidates |
| GET | `/api/v1/stats` | Retrieve vector store statistics |
| GET | `/health` | Gateway health and downstream service status |

### POST `/api/v1/match`

Request:
```bash
curl -X POST http://localhost:8000/api/v1/match \
  -H "Content-Type: application/json" \
  -d '{
    "job_description": "We are looking for a senior backend developer with strong experience in Python, REST APIs, Docker, and PostgreSQL. The candidate should have experience building scalable microservices and cloud deployment.",
    "top_k": 10
  }'
```

Response (trimmed example):
```json
{
  "status": "success",
  "query_summary": "Senior backend engineer with Python and PostgreSQL experience",
  "parsed_job": {
    "experience_level": "senior",
    "role_category": "backend",
    "required_skills": ["python", "postgresql", "docker"],
    "preferred_skills": []
  },
  "bias_check": { "has_bias": false, "bias_types": [] },
  "token_usage": { "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0 },
  "candidates": [
    {
      "rank": 1,
      "resume_id": "resume_001",
      "final_score": 88.75,
      "semantic_score": 92.0,
      "skill_score": 85.5,
      "skill_coverage": 85.0,
      "matched_skills": ["python", "docker"],
      "missing_skills": ["kubernetes"],
      "experience_level": "senior",
      "role_category": "backend",
      "explanation": "Semantic match score 92.0%. Skills: 85% required, 0% preferred. Missing: kubernetes."
    }
  ],
  "total_found": 10,
  "execution_time": 2.34,
  "performance": {
    "candidates_per_second": 4.27,
    "total_candidates": 10,
    "execution_time_seconds": 2.34
  },
  "message": "Successfully found and ranked 10 candidates"
}
```

### GET `/api/v1/stats`

```bash
curl http://localhost:8000/api/v1/stats
```

Returns stats such as total resumes, total chunks, and distributions by category/role/level.

### GET `/health`

```bash
curl http://localhost:8000/health
```

Example response:
```json
{
  "status": "healthy",
  "gateway": "api_gateway",
  "timestamp": "2026-03-17T12:34:56.789Z",
  "services": {
    "matching": {
      "status": "healthy",
      "url": "http://localhost:8001",
      "service": "matching",
      "vector_store_ready": true,
      "total_documents": 38063
    }
  }
}
```

## Example Queries

Use these as quick inputs for `/api/v1/match`:

1) HR Manager
```text
We are looking for an experienced HR manager with strong skills in recruitment, employee relations, performance management, and HR policy development. The candidate should have experience with HRIS systems, payroll processing, onboarding, and compensation and benefits administration.
```

2) Data Scientist
```text
We need a data scientist with experience in machine learning, Python, TensorFlow, and data analysis. Strong skills in statistical modeling, pandas, numpy, and experience working with large datasets and data visualization is required.
```

3) Backend Developer
```text
We are looking for a senior backend developer with strong experience in Python, REST APIs, Docker, and PostgreSQL. The candidate should have experience building scalable microservices and cloud deployment.
```

## Features

- Resume ingestion from CSV into ChromaDB (persistent local store)
- Semantic retrieval of candidates via vector similarity search
- Job description parsing into structured requirements (skills, level, role)
- Skill overlap scoring and ranked candidate results
- Explanations per candidate (human-readable)
- Health endpoint with service readiness and document counts
- Analytics dashboard for dataset distributions and local performance metrics

## Project Structure

```
.
├── data/
│   ├── resumes.csv
│   └── chroma_db/
├── examples/
├── frontend/
│   ├── package.json
│   └── src/
│       ├── pages/
│       │   ├── Match.jsx
│       │   ├── Results.jsx
│       │   └── Analytics.jsx
│       └── utils/api.js
├── src/
│   ├── agents/                 # Skill scoring
│   ├── api/                    # Optional monolith API app (includes /api/v1/ingest)
│   ├── core/                   # Configuration and settings
│   ├── embeddings/             # Vector store access
│   ├── guardrails/             # Input validation and guardrails
│   ├── ingestion/              # Resume ingestion pipeline
│   ├── retrieval/              # JD parsing and candidate retrieval
│   └── services/               # Matching microservice
├── gateway.py                  # API gateway (port 8000)
├── main.py                     # Monolith server entry (optional)
├── requirements.txt
├── start_services.bat
├── start_all_services.bat
└── README.md
```

## Dataset Info

This project is designed to work with resume datasets commonly published on Kaggle.

Typical format:
- A CSV file with resume text and an optional category label
- The ingestion pipeline chunks resumes and stores chunks as documents in ChromaDB
- Matching searches across chunks and deduplicates results to unique resumes

Recommended location:
```text
data/resumes.csv
```

## Known Limitations

- Requires `OPENAI_API_KEY` for components that use the OpenAI API (job parsing and optional assessments).
- First request can be slower due to warm-up (model loading / vector store initialization).
- Local persistence can be large depending on dataset size (disk usage).
- No authentication/authorization is included (not production-hardened).
- Soft skills and bias checks are heuristic model outputs and should not be used as automated hiring decisions without governance and human review.

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
8. [Configuration](#configuration)
9. [API Endpoints](#api-endpoints)
10. [Example Queries](#example-queries)
11. [Features](#features)
12. [Project Structure](#project-structure)
13. [Dataset Info](#dataset-info)
14. [Known Limitations](#known-limitations)

## Overview

This project is an AI-powered system for resume intelligence and candidate matching. It ingests resumes into a local vector store, parses job descriptions into structured requirements, retrieves semantically relevant candidates, and returns ranked results with:
- skill coverage
- recruiter-style explanations (with Strengths/Gaps bullets)
- performance metrics per request (execution time and candidates/sec)

Core capabilities:
- Basic RAG candidate retrieval using embeddings + vector similarity search (ChromaDB)
- Fast job parsing by default (non-LLM) with implicit skill expansion:
  - UX/UI wording -> frontend skill set
  - HR wording -> HR skill set
  - High-level terms like backend/devops/data analysis -> related skills
- Optional LLM features (time-budgeted, disabled by default for performance)
- Multi-agent scoring pipeline (technical similarity + semantic skill overlap; experience/culture agents included as placeholders)
- Input guardrails for job descriptions + resume validation during ingestion
- Bias detection guardrails (basic) + analytics tracking
- React frontend for match flow, results review, and analytics (including last-50 search trends stored locally)

## Architecture

Text-based diagram:

```text
                   +------------------------------+
                   | Frontend (React + Vite)      |
                   | http://localhost:5173        |
                   +--------------+---------------+
                                  |
                                  | REST (JSON)
                                  v
                   +------------------------------+
                   | API Gateway (FastAPI)        |
                   | gateway.py                   |
                   | http://localhost:8000        |
                   +--------------+---------------+
                                  |
                                  | forwards /api/v1/* to service
                                  v
                   +------------------------------+
                   | Matching Service (FastAPI)   |
                   | src/services/matching_service.py
                   | http://localhost:8001        |
                   +-----------+------------------+
                               |
                               | semantic_search
                               v
                   +------------------------------+
                   | ChromaDB Vector Store        |
                   | ./data/chroma_db             |
                   +------------------------------+

Ingestion (one-time / batch):
  data/resumes.csv -> src/ingestion/* -> embeddings -> ./data/chroma_db
```

Editable diagram for exporting (PNG/SVG): `docs/architecture.drawio`

Notes:
- Recommended runtime is microservices: Gateway (8000) -> Matching Service (8001).
- This repository is organized around microservices (gateway + matching service).

Code map: `docs/CODEMAP.md`
Getting started: `docs/GETTING_STARTED.md`

## Tech Stack

| Layer | Technology | Notes |
|------:|------------|------|
| Frontend | React + Vite | Match UI, results UI, analytics dashboard |
| API Gateway | FastAPI + httpx | Single entry point on port 8000 |
| Matching Service | FastAPI | Retrieval + scoring + explanations + stats + health |
| Vector Store | ChromaDB | Persistent store in `./data/chroma_db` |
| Embeddings | OpenAI embeddings | Used for semantic retrieval |
| Job parsing | Fast parser + optional LLM | Fast by default; LLM optional |
| Skill scoring | sentence-transformers | Semantic skill overlap scoring |

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

Windows:
```powershell
copy .env.example .env
```

macOS/Linux:
```bash
cp .env.example .env
```

Add your key:
```env
OPENAI_API_KEY=sk-...
```

## Data Ingestion

### Dataset

Place your resume dataset CSV here:

```text
data/resumes.csv
```

### Run ingestion

Recommended (fast mode without per-resume metadata LLM calls):

```bash
python -c "from src.ingestion.pipeline import run_ingestion_pipeline; import json; print(json.dumps(run_ingestion_pipeline(csv_path='data/resumes.csv', extract_metadata=False, skip_invalid=True), indent=2))"
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

## Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on `http://localhost:5173` (Vite default).

## Configuration

The system is designed to be fast by default. Optional LLM-based features are behind env flags.

### Performance toggles (matching service)

- `ENABLE_LLM_JOB_PARSER=1`
  - Uses LLM job parsing (slower). Default is fast parsing.
- `ENABLE_LLM_EXPLANATIONS=1`
  - Generates LLM explanations for top results (time-budgeted). Default off.
- `ENABLE_SOFT_SKILLS=1`
  - Runs soft skills assessment (time-budgeted). Default off.

### Client-side analytics storage (frontend)

The frontend stores basic trend metrics in the browser:
- `rms_query_history` (last 50 successful searches)
- `rms_queries_processed`
- `rms_bias_stats`
- `softSkillsData` (raw soft skill assessments)

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
      "matched_skills": ["Python", "Docker"],
      "missing_skills": ["Kubernetes"],
      "experience_level": "senior",
      "role_category": "backend",
      "explanation": "This profile shows good alignment with the role's priorities. Strengths are most evident in Python and Docker, which map to day-to-day responsibilities. The overall profile suggests they can operate effectively in a senior backend context. Areas to validate in screening include Kubernetes, where evidence is less clear.\\n\\nStrengths:\\n- Python\\n- Docker\\n\\nGaps:\\n- Kubernetes"
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

### GET `/health`

```bash
curl http://localhost:8000/health
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

4) Implicit HR
```text
We need someone who manages employee-related processes, supports workplace policies, handles hiring activities, and ensures smooth organizational operations.
```

## Features

- Resume ingestion from CSV into ChromaDB (persistent local store)
- Semantic retrieval of candidates via vector similarity search
- Job description parsing into structured requirements (skills, level, role)
  - Fast parser by default for low latency (`parse_job_description_fast`)
  - Optional LLM parser (`ENABLE_LLM_JOB_PARSER=1`)
  - Implicit skill expansion (UX/UI wording -> frontend skills; HR wording -> HR skills; plus backend/devops/data analysis)
- Multi-agent evaluation pipeline for scoring (technical + skills; experience/culture agents included as placeholders)
- Semantic skill matching (sentence-transformers) and ranked candidate results
- Recruiter-style explanations
  - Human-readable narrative + Strengths/Gaps bullets
  - Optional LLM explanations (time-budgeted; `ENABLE_LLM_EXPLANATIONS=1`)
- Input guardrails and validation
  - Job description validation to reject gibberish/invalid inputs
  - Resume validation during ingestion
- Bias detection guardrails (basic) with tracking for analytics
- Performance metrics returned per query (`performance` field)
- Analytics dashboard
  - Dataset distributions from `/api/v1/stats`
  - Health and readiness from `/health` via gateway
  - Local metrics (queries processed, bias stats, soft skills averages)
  - Skill demand and search trends (last 50 searches stored locally)

## Project Structure

```text
.
|-- data/
|   |-- resumes.csv
|   `-- chroma_db/
|-- docs/
|   |-- CODEMAP.md
|   `-- architecture.drawio
|-- frontend/
|   |-- README.md
|   |-- package.json
|   `-- src/
|       |-- pages/
|       |   |-- Match.jsx
|       |   |-- Results.jsx
|       |   `-- Analytics.jsx
|       `-- utils/api.js
|-- src/
|   |-- agents/
|   |-- core/
|   |-- embeddings/
|   |-- guardrails/
|   |-- ingestion/
|   |-- retrieval/
|   `-- services/
|-- gateway.py
|-- requirements.txt
|-- start_services.bat
|-- start_all_services.bat
`-- README.md
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

- Requires `OPENAI_API_KEY` for components that use the OpenAI API (optional LLM parsing, optional LLM explanations, optional soft skills).
- First request can be slower due to warm-up (model loading / vector store initialization).
- Local persistence can be large depending on dataset size (disk usage).
- No authentication/authorization is included (not production-hardened).
- Soft skills and bias checks are heuristic model outputs and should not be used as automated hiring decisions without governance and human review.
- Metadata filtering (experience/role/education) is intentionally not enforced during retrieval by default to avoid false negatives when dataset metadata is incomplete.

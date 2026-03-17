# Code Map (Where to Look for What)

This repository supports two backend run modes:

1) **Microservice mode (recommended)**: API Gateway (port 8000) + Matching Service (port 8001)
2) **Monolith mode (legacy/dev convenience)**: single FastAPI app with endpoints under `src/api/`

If you're using the React frontend, you are typically using **microservice mode** via the gateway at `http://localhost:8000`.

---

## Top-level entry points

- `gateway.py`
  - API Gateway (FastAPI)
  - Frontend should call this on `http://localhost:8000`
  - Proxies `/api/v1/*` requests to the matching service

- `src/services/matching_service.py`
  - Matching microservice (FastAPI) on `http://localhost:8001`
  - Implements `/api/v1/match`, `/api/v1/stats`, `/health`
  - Uses the agent pipeline to score candidates

- `src/api/main.py`
  - **Legacy** monolith FastAPI app (single process API mode)
  - Contains its own `/api/v1/match` implementation (similar responsibilities, separate code path)

- `main.py`
  - Convenience runner that starts the monolith (`src/api/main.py`)
  - Use `start_services.bat` / `start_all_services.bat` for microservice mode

---

## Backend directories

- `src/agents/`
  - Modular “agents” that compute a score + explanation for one aspect of matching
  - Examples:
    - `technical_evaluation_agent.py`: semantic/technical evaluation from vector similarity
    - `skill_matching_agent.py`: skill overlap scoring + matched/missing skills
    - `experience_evaluation_agent.py`: experience alignment (currently neutral/0 weight)
    - `culture_fit_agent.py`: placeholder (currently neutral/0 weight)
    - `explanation_agent.py`: optional LLM explanations (time-budgeted)
  - `skill_scorer.py`: SentenceTransformer-based overlap scorer (expensive; loaded once)

- `src/services/`
  - Service layer / orchestration
  - `agent_pipeline.py`: sequentially calls agents and combines results into the final fields used by the API response
  - `matching_service.py`: HTTP API surface for the matching microservice

- `src/retrieval/`
  - Turns a job description into a query and retrieves candidates from the vector store
  - `job_parser.py`: job description parsing (LLM parser + fast parser)
  - `candidate_retriever.py`: Chroma-based semantic retrieval + deduplication

- `src/embeddings/`
  - Vector store integration (Chroma + OpenAI embeddings)
  - `vector_store.py`: initialization, ingestion helpers, semantic search

- `src/guardrails/`
  - Input validation / guardrails
  - `input_validator.py`: rejects invalid job descriptions early

- `src/ingestion/`
  - Resume ingestion pipeline (CSV → chunks → embeddings → Chroma persistence)

- `src/core/`
  - Central configuration (env vars, defaults) and shared settings

---

## Frontend

- `frontend/src/pages/Match.jsx`
  - Sends job description to `/api/v1/match` (via gateway)

- `frontend/src/pages/Results.jsx`
  - Renders candidate cards including `candidate.explanation`

- `frontend/src/pages/Analytics.jsx`
  - Calls `/api/v1/stats` and `/health` (via gateway) and renders dashboard metrics


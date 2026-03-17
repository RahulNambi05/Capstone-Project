## Resume Intelligence & Candidate Matching System

This repository is a local, AI-assisted resume retrieval and candidate matching system.

At a high level it:
- Ingests a resume dataset into a persistent ChromaDB vector store
- Parses a job description (fast parser by default; optional LLM parsing)
- Retrieves top candidates via semantic similarity search
- Scores candidates using an agent pipeline (semantic + skills) and returns ranked results
- Produces recruiter-style explanations plus Strengths/Gaps bullets for each candidate

### Recommended run mode (microservices)

- API Gateway: `gateway.py` on `http://localhost:8000`
- Matching Service: `src/services/matching_service.py` on `http://localhost:8001`
- Frontend: `frontend/` (Vite dev server on `http://localhost:5173`)

Start backend:
```powershell
.\start_services.bat
```

Start frontend:
```bash
cd frontend
npm install
npm run dev
```

### Key endpoints (via gateway)

- `POST /api/v1/match`
- `GET /api/v1/stats`
- `GET /health`

### Performance toggles (optional)

The matching service supports environment toggles to control latency:
- `ENABLE_LLM_JOB_PARSER=1` (slower; default is fast parser)
- `ENABLE_LLM_EXPLANATIONS=1` (time-budgeted; default off)
- `ENABLE_SOFT_SKILLS=1` (time-budgeted; default off)

# Getting Started

This guide is the single place to learn how to run the project in **microservice mode** (recommended).

## Prerequisites

- Python 3.10+
- Node.js 18+ (for the frontend)
- `OPENAI_API_KEY` in your environment (required for embeddings; some LLM features are optional)

## Install (Backend)

```bash
pip install -r requirements.txt
```

Create `.env`:

Windows:
```powershell
copy .env.example .env
```

macOS/Linux:
```bash
cp .env.example .env
```

Set:
```env
OPENAI_API_KEY=sk-...
```

## Ingest Data

Place your resume CSV at:

```text
data/resumes.csv
```

Run ingestion (fast mode):

```bash
python -c "from src.ingestion.pipeline import run_ingestion_pipeline; import json; print(json.dumps(run_ingestion_pipeline(csv_path='data/resumes.csv', extract_metadata=False, skip_invalid=True), indent=2))"
```

ChromaDB persistence is written to:

```text
data/chroma_db/
```

## Run (Microservices)

### Windows (recommended scripts)

Start gateway + matching service:
```powershell
.\start_services.bat
```

Start backend + frontend:
```powershell
.\start_all_services.bat
```

### Manual (two terminals)

Terminal 1 - Matching Service (port 8001):
```bash
python -m uvicorn src.services.matching_service:app --port 8001
```

Terminal 2 - API Gateway (port 8000):
```bash
python -m uvicorn gateway:app --port 8000
```

## Run (Frontend)

```bash
cd frontend
npm install
npm run dev
```

Vite default URL: `http://localhost:5173`

## Key URLs

- Frontend: `http://localhost:5173`
- Gateway health: `http://localhost:8000/health`
- Gateway docs: `http://localhost:8000/docs`

## Performance toggles (optional)

The system is designed to be fast by default. Optional LLM-based features are behind env flags:

- `ENABLE_LLM_JOB_PARSER=1` (slower; default is fast parsing)
- `ENABLE_LLM_EXPLANATIONS=1` (time-budgeted; default off)
- `ENABLE_SOFT_SKILLS=1` (time-budgeted; default off)

## Scoring architecture (high level)

The matching service uses an agent pipeline (`src/services/agent_pipeline.py`) that combines:
- Technical similarity (vector similarity score)
- Semantic skill overlap (sentence-transformers)
- Experience/culture-fit agents (currently placeholders; 0 weight by default)

## Troubleshooting

- Getting 0 candidates:
  - Ensure you ingested data (Chroma has documents)
  - Try a longer job description (guardrails require a real description)
- Slow first request:
  - First request may include warm-up costs (model/vector init); subsequent requests are faster


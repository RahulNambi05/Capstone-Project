# Resume Intelligence & Candidate Matching - Quick Start

## Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

## Running the API

### Option 1 (Recommended): Microservices (Gateway + Matching)

Windows (PowerShell):
```powershell
.\start_services.bat
```

- Gateway: `http://localhost:8000`
- Matching Service: `http://localhost:8001`
- Docs: `http://localhost:8000/docs`

### Option 2: Start services manually (two terminals)

Terminal 1 - Matching Service (port 8001):
```bash
python -m uvicorn src.services.matching_service:app --port 8001
```

Terminal 2 - API Gateway (port 8000):
```bash
python -m uvicorn gateway:app --port 8000
```

### Option 3: Monolith (Legacy / Single process)
```bash
python main.py
```
- URL: `http://127.0.0.1:8000`
- Docs: `http://127.0.0.1:8000/docs`

### Option 4: Monolith development with auto-reload
```bash
python main.py --reload
```

### Option 5: Monolith production-like mode
```bash
python main.py --host 0.0.0.0 --port 8000 --workers 4
```

### Option 6: Monolith custom port
```bash
python main.py --port 8080
```

## Startup Output

You'll see logs like:
```
======================================================================
Resume Matching System API - Starting
======================================================================

API Configuration:
  Host: 127.0.0.1
  Port: 8000
  Reload: True
  Debug: False

LLM & Embedding Models:
  LLM Model: gpt-4o-mini
  Embedding Model: text-embedding-3-small

Document Processing:
  Chunk Size: 500
  Chunk Overlap: 50
  Top K Candidates: 10

Vector Store:
  Persist Directory: ./chroma_db
  Collection Name: resumes

OpenAI API Key: Configured

API Documentation:
  Swagger UI: http://127.0.0.1:8000/docs
  ReDoc: http://127.0.0.1:8000/redoc
  OpenAPI Schema: http://127.0.0.1:8000/openapi.json
======================================================================
API is ready to accept requests!
======================================================================
```

## API Operations

### 1. Health Check
```bash
curl http://localhost:8000/health
```

### 2. Ingest Resumes
```bash
curl -X POST http://localhost:8000/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "csv_path": "data/resumes.csv"
  }'
```

### 3. Match Job with Candidates
```bash
curl -X POST http://localhost:8000/api/v1/match \
  -H "Content-Type: application/json" \
  -d '{
    "job_description": "Senior Python backend engineer with 8+ years experience...",
    "top_k": 10,
    "filters": {
      "experience_level": "senior",
      "role_category": "backend"
    }
  }'
```

### 4. Get Statistics
```bash
curl http://localhost:8000/api/v1/stats
```

## Interactive API Testing

Open Swagger UI in your browser:
```
http://127.0.0.1:8000/docs
```

- Test all endpoints interactively
- See request/response schemas
- Try different parameters

## CLI Arguments Reference

| Argument | Default | Description |
|----------|---------|-------------|
| `--host` | 127.0.0.1 | Network interface to bind to |
| `--port` | 8000 | Port number (1-65535) |
| `--reload` | False | Enable auto-reload for development |
| `--workers` | 1 | Number of worker processes |

## Common Issues

**Port already in use:**
```bash
python main.py --port 8080
```

**OpenAI API key not found:**
```bash
# Set environment variable
export OPENAI_API_KEY=sk-...
# Or update .env file
```

**Module not found:**
```bash
pip install -r requirements.txt
```

## Next Steps

1. Start services: `.\start_services.bat`
2. Open Swagger UI: `http://localhost:8000/docs`
3. Ingest resumes: POST to `/api/v1/ingest`
4. Test matching: POST to `/api/v1/match`
5. View statistics: GET to `/api/v1/stats`

## For More Details

See `RUNNING_THE_API.md` for comprehensive documentation on all CLI options, configurations, and troubleshooting.

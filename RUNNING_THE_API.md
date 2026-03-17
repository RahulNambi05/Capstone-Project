"""
Resume Matching System - Running the API Server

This document explains how to run the Resume Matching System API server
using the main.py entry point with various CLI options.
"""

## Quick Start

### Default Configuration (Localhost Only)
```bash
python main.py
```

Server will run on `http://127.0.0.1:8000` (accessible only from your machine)

Output:
```
======================================================================
Resume Matching System API - Starting
======================================================================

API Configuration:
  Host: 127.0.0.1
  Port: 8000
  Reload: False
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

OpenAI API Key: ✓ Configured

API Documentation:
  Swagger UI: http://127.0.0.1:8000/docs
  ReDoc: http://127.0.0.1:8000/redoc
  OpenAPI Schema: http://127.0.0.1:8000/openapi.json
======================================================================
API is ready to accept requests!
======================================================================
```

---

## CLI Arguments

### --host
Bind the server to a specific network interface.

**Default:** `127.0.0.1` (localhost only)

Examples:
```bash
# Access from anywhere on network (DEVELOPMENT ONLY!)
python main.py --host 0.0.0.0

# Access from a specific network interface
python main.py --host 192.168.1.100

# Run on localhost but explicit
python main.py --host 127.0.0.1
```

### --port
Bind the server to a specific port.

**Default:** `8000`

Examples:
```bash
# Run on port 8080
python main.py --port 8080

# Run on port 5000
python main.py --port 5000

# Valid range: 1-65535
```

### --reload
Enable auto-reload on code changes (development mode).

**Important:** Disables multi-worker mode for compatibility with hot-reload.

```bash
# Enable auto-reload for development
python main.py --reload

# Disable workers when using reload (automatic)
python main.py --reload --workers 4  # Workers will be set to 1
```

### --workers (Production)
Number of worker processes for concurrent request handling.

**Default:** `1`
**Note:** Automatically set to 1 if `--reload` is enabled.

Examples:
```bash
# Single worker (default)
python main.py

# Multiple workers for production
python main.py --workers 4

# Combine with host binding for production
python main.py --host 0.0.0.0 --port 8000 --workers 4
```

---

## Common Usage Scenarios

### 1. Local Development
```bash
python main.py --reload
```

- Auto-reloads on file changes
- Accessible at http://127.0.0.1:8000
- Logs detailed error information

---

### 2. Testing on Local Network
```bash
python main.py --host 0.0.0.0 --port 8000
```

- Accessible from other machines on network
- Access via: `http://<your-machine-ip>:8000`
- Single worker

---

### 3. Production Deployment
```bash
python main.py --host 0.0.0.0 --port 8000 --workers 4
```

- Multi-worker configuration
- Production-ready performance
- Accessible from network

---

### 4. Custom Port (Behind Proxy)
```bash
python main.py --port 5000
```

- Useful if port 8000 is already in use
- Accessible at http://127.0.0.1:5000

---

### 5. Development with Custom Configuration
```bash
python main.py --host 0.0.0.0 --port 8080 --reload
```

- Custom port with auto-reload
- Accessible from network during development

---

## API Endpoints

After starting the server, the following endpoints are available:

### Health Check
```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-03-15T10:30:00Z"
}
```

---

### Resume Ingestion
```bash
curl -X POST http://localhost:8000/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "csv_path": "data/resumes/resume_dataset.csv"
  }'
```

---

### Job Candidate Matching
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

---

### Vector Store Statistics
```bash
curl http://localhost:8000/api/v1/stats
```

---

## API Documentation

Once the server is running, access interactive documentation:

### Swagger UI (Recommended)
- **URL:** http://127.0.0.1:8000/docs
- Interactive API testing
- Request/response examples
- Schema validation

### ReDoc
- **URL:** http://127.0.0.1:8000/redoc
- Alternative documentation format
- Beautiful, read-only API reference

### OpenAPI Schema (JSON)
- **URL:** http://127.0.0.1:8000/openapi.json
- Raw OpenAPI specification

---

## Configuration

The server loads configuration from `.env` file. Required variables:

```env
# OpenAI Configuration
OPENAI_API_KEY=sk-...

# Vector Store
CHROMA_PERSIST_DIR=./chroma_db

# Logging
DEBUG=false
```

### Configuration via `src/core/config.py`

The following settings are logged at startup:

| Setting | Default | Description |
|---------|---------|-------------|
| LLM_MODEL | gpt-4o-mini | OpenAI model for metadata extraction |
| EMBEDDING_MODEL | text-embedding-3-small | Embedding model for semantic search |
| CHUNK_SIZE | 500 | Resume text chunk size (characters) |
| CHUNK_OVERLAP | 50 | Overlap between chunks (characters) |
| TOP_K | 10 | Default number of candidates to retrieve |

---

## Troubleshooting

### "Address already in use"
```bash
# Use a different port
python main.py --port 8080

# Or find and kill the process using the port
lsof -i :8000  # List processes on port 8000
```

### "Permission denied"
```bash
# If port < 1024, requires sudo
sudo python main.py --port 80

# Or use a higher port
python main.py --port 8000
```

### "Module not found"
```bash
# Install dependencies
pip install -r requirements.txt

# Ensure .env is configured
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### "OpenAI API Key not configured"
```bash
# Set environment variable
export OPENAI_API_KEY=sk-...

# Or edit .env file
echo "OPENAI_API_KEY=sk-..." >> .env
```

### Slow startup
```bash
# Vector store initialization can take time on first run with many resumes
# This is normal behavior - it only happens once

# Pre-index resumes if many in database
python main.py  # First run initializes vector store
```

---

## Monitoring & Logging

### Log Levels

The server logs at INFO level by default. For detailed debugging:

Edit `main.py` and change:
```python
logging.basicConfig(level=logging.DEBUG)
```

### Key Log Messages

```
[INFO] API is ready to accept requests!
       Server started successfully

[ERROR] Invalid port number: X
        Port must be 1-65535

[ERROR] Fatal error: ...
        Server failed to start - check configuration and logs
```

---

## Performance Tips

### Development
```bash
python main.py --reload
```
- Single worker with auto-reload
- Best for iterative development

### Local Testing
```bash
python main.py --host 0.0.0.0
```
- Test from multiple machines
- Debug network issues

### Production (Docker)
```bash
# In Dockerfile
CMD ["python", "main.py", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### Multiple Concurrent Requests
```bash
# Use more workers
python main.py --workers 4
# or 2x-4x number of CPU cores for optimal performance
```

---

## Next Steps

1. Start the API server:
   ```bash
   python main.py
   ```

2. Open Swagger UI:
   ```
   http://127.0.0.1:8000/docs
   ```

3. Ingest resumes:
   - POST to `/api/v1/ingest` with CSV path

4. Test matching:
   - POST to `/api/v1/match` with job description

5. Review results:
   - Check logs and API responses for quality

---

## Support

For issues or questions:
1. Check logs: Look for [ERROR] messages
2. Review configuration: Verify .env file
3. Test endpoints: Use curl or Swagger UI
4. Check OpenAI API: Ensure API key is valid

# Resume Matching System - Setup Guide

Complete guide for setting up and running the Resume Matching System.

## System Overview

The system consists of three main components:

1. **Matching Microservice** (Port 8001)
   - Handles job matching and candidate retrieval
   - Manages vector store and semantic search
   - Computes skill scores

2. **API Gateway** (Port 8000)
   - Central entry point for all requests
   - Routes to appropriate microservices
   - Handles health checks and service monitoring

3. **React Frontend** (Port 3000)
   - User interface for job search and results
   - Analytics dashboard
   - Real-time service monitoring

## Quick Start - Windows

### Step 1: Prepare Environment
```bash
# Navigate to project directory
cd "C:\Users\Administrator\Desktop\AI RPOJECT"
```

### Step 2: Install Backend Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Install Frontend Dependencies
```bash
cd frontend
npm install
cd ..
```

### Step 4: Start All Services
```bash
# Double-click this file to start everything
start_all_services.bat
```

Or start individually in separate terminal windows:

**Terminal 1:**
```bash
python -m uvicorn src.services.matching_service:app --port 8001
```

**Terminal 2:**
```bash
python -m uvicorn gateway:app --port 8000
```

**Terminal 3:**
```bash
cd frontend
npm run dev
```

### Step 5: Access the Application
- Frontend: http://localhost:3000
- API Gateway: http://localhost:8000/docs
- Matching Service: http://localhost:8001/docs

## Configuration

### Environment Variables
Create a `.env` file in the root directory:

```env
OPENAI_API_KEY=your-api-key-here
OPENAI_LLM_MODEL=gpt-3.5-turbo
OPENAI_EMBEDDING_MODEL=text-embedding-ada-002
API_HOST=127.0.0.1
API_PORT=8000
DEBUG=True
CHUNK_SIZE=500
CHUNK_OVERLAP=50
TOP_K=10
```

### Frontend Configuration
Edit `frontend/src/utils/api.js`:
```javascript
const API_BASE_URL = 'http://localhost:8000'  // Change if backend is on different host
```

## Testing the System

### Test 1: Check Service Health
```bash
curl http://localhost:8000/health
```

### Test 2: Submit a Job Matching Request
```bash
curl -X POST http://localhost:8000/api/v1/match \
  -H "Content-Type: application/json" \
  -d '{
    "job_description": "Senior Python developer with 5+ years experience in Django and FastAPI. Must have experience with PostgreSQL, Redis, and Docker. Strong communication skills required.",
    "top_k": 10
  }'
```

### Test 3: Get System Statistics
```bash
curl http://localhost:8000/api/v1/stats
```

## Troubleshooting

### Issue: "Port already in use"
Solution: Change the port number or kill the process using the port
```bash
# Windows - Find process on port 8000
netstat -ano | findstr :8000
# Kill process
taskkill /PID <PID> /F
```

### Issue: "Vector store is empty"
Solution: Ensure resumes have been ingested using the ingestion pipeline

### Issue: "OpenAI API error"
Solution: Verify API key is correct and has sufficient credits

### Issue: Frontend can't connect to backend
Solution: 
1. Check if gateway is running on port 8000
2. Check browser console for CORS errors
3. Verify API_BASE_URL in `frontend/src/utils/api.js`

### Issue: "Module not found" error
Solution: Install dependencies
```bash
pip install -r requirements.txt
cd frontend && npm install
```

## Project Structure Details

### Backend Files
```
src/
├── api/main.py              # Main FastAPI app
├── services/
│   └── matching_service.py  # Matching microservice
├── retrieval/
│   ├── candidate_retriever.py
│   └── job_parser.py
├── embeddings/
│   └── vector_store.py      # ChromaDB interface
├── agents/
│   └── skill_scorer.py      # Skill matching logic
└── core/
    └── config.py            # Configuration

gateway.py                  # API Gateway
main.py                    # Backend entry point (if running without gateway)
```

### Frontend Files
```
frontend/
├── src/
│   ├── components/Navigation.jsx
│   ├── pages/
│   │   ├── Home.jsx
│   │   ├── Match.jsx
│   │   ├── Results.jsx
│   │   └── Analytics.jsx
│   ├── context/ResultsContext.jsx
│   ├── utils/api.js
│   ├── App.jsx
│   ├── index.jsx
│   └── index.css
├── public/index.html
└── package.json
```

## Key Components Explained

### Vector Store
Manages resume embeddings using ChromaDB:
- Stores: 38,000+ resume chunks
- Search: Semantic similarity using OpenAI embeddings
- Path: `./data/chroma_db/`

### Job Parser
Extracts from job descriptions:
- Required skills
- Preferred skills
- Experience level
- Role category

### Skill Scorer
Computes skill matching:
- Required skills match %
- Preferred skills match %
- Missing skills
- Overall skill score

### Candidate Retriever
Finds matching candidates:
- Pure semantic search (no metadata filtering)
- Retrieves top_k * 3 for deduplication
- Deduplicates by resume_id
- Returns top_k final candidates

## Performance Benchmarks

- **Semantic Search**: < 1 second
- **Skill Scoring**: ~50ms per candidate
- **Total Match Time**: 2-3 seconds for 100 candidates
- **Memory Usage**: ~2GB for embedding model + 1GB for vector store

## Common Commands

### Start Services
```bash
# All services
start_all_services.bat

# Individual services
start_services.bat              # Gateway + Matching Service
start_frontend.bat              # Frontend only
```

### Development
```bash
# Frontend hot reload
cd frontend && npm run dev

# Backend with auto-reload
python -m uvicorn gateway:app --reload
```

### Build
```bash
# Frontend production build
cd frontend && npm run build
```

### Testing
```bash
# Test backend
pytest tests/

# Test frontend
cd frontend && npm run test
```

## Next Steps

1. **Add More Resumes**: Use ingestion pipeline to add more candidate resumes
2. **Customize Scoring**: Adjust weights in `src/agents/skill_scorer.py`
3. **Deploy**: Use Docker for containerized deployment
4. **Monitor**: Set up logging and monitoring for production use

## Support

For issues or questions:
1. Check logs in terminal window
2. Review API documentation at `/docs`
3. Check browser console (F12) for frontend errors
4. Review code comments for implementation details

---

Happy matching! 🎯

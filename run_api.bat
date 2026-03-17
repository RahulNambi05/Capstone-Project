@echo off
REM Quick start script for Resume Matching System API (Windows)

echo Starting API server in development mode...
python main.py --reload

REM Alternative: Production-like mode with multiple workers
REM python main.py --host 0.0.0.0 --port 8000 --workers 4

REM Alternative: Custom port for testing
REM python main.py --port 8080

pause

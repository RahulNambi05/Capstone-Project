@echo off
REM Resume Matching System - Service Starter
REM Starts the matching microservice and API gateway in separate terminal windows

echo.
echo ========================================================================
echo Resume Matching System - Starting Services
echo ========================================================================
echo.

REM Start Matching Microservice on port 8001
echo [1/2] Starting Matching Microservice on port 8001...
start "Resume Matching Microservice" cmd /k python -m uvicorn src.services.matching_service:app --port 8001

REM Wait 5 seconds for matching service to initialize
echo [Waiting 5 seconds for service initialization...]
timeout /t 5 /nobreak

REM Start API Gateway on port 8000
echo [2/2] Starting API Gateway on port 8000...
start "Resume Matching API Gateway" cmd /k python -m uvicorn gateway:app --port 8000

echo.
echo ========================================================================
echo Startup Complete!
echo ========================================================================
echo.
echo Services started:
echo   - API Gateway:      http://localhost:8000
echo   - Matching Service: http://localhost:8001
echo.
echo Documentation:
echo   - Gateway Docs:     http://localhost:8000/docs
echo   - Service Docs:     http://localhost:8001/docs
echo.
echo ========================================================================
echo.

timeout /t 3

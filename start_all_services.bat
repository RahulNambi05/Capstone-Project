@echo off
REM Resume Matching System - Complete Startup Script
REM Starts all services: Matching Service, API Gateway, and React Frontend

echo.
echo ========================================================================
echo Resume Matching System - Complete Startup
echo ========================================================================
echo.

REM Start Matching Microservice on port 8001
echo [1/3] Starting Matching Microservice on port 8001...
start "Resume Matching Microservice" cmd /k python -m uvicorn src.services.matching_service:app --port 8001

REM Wait 5 seconds for matching service to initialize
echo [Waiting 5 seconds for service initialization...]
timeout /t 5 /nobreak

REM Start API Gateway on port 8000
echo [2/3] Starting API Gateway on port 8000...
start "Resume Matching API Gateway" cmd /k python -m uvicorn gateway:app --port 8000

REM Wait 3 seconds for gateway to initialize
echo [Waiting 3 seconds for gateway initialization...]
timeout /t 3 /nobreak

REM Start Frontend on Vite default port 5173
echo [3/3] Starting React Frontend (Vite) on port 5173...
start "Resume Matching Frontend" cmd /k cd frontend && npm install && npm run dev

echo.
echo ========================================================================
echo Startup Complete!
echo ========================================================================
echo.
echo Services started:
echo   - React Frontend:    http://localhost:5173
echo   - API Gateway:       http://localhost:8000
echo   - Matching Service:  http://localhost:8001
echo.
echo Documentation:
echo   - Frontend:          http://localhost:5173/
echo   - Gateway Docs:      http://localhost:8000/docs
echo   - Service Docs:      http://localhost:8001/docs
echo.
echo ========================================================================
echo.

timeout /t 3

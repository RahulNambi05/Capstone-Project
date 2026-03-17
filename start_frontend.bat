@echo off
REM Resume Matching System - Frontend Starter

echo.
echo ========================================================================
echo Resume Matching System - Starting Frontend
echo ========================================================================
echo.

REM Check if node_modules exists
if not exist "frontend\node_modules" (
    echo [1/3] Installing dependencies...
    cd frontend
    call npm install
    cd ..
) else (
    echo [1/3] Dependencies already installed
)

echo [2/3] Starting development server...
cd frontend
call npm run dev

echo.
echo ========================================================================
echo Frontend started! Open http://localhost:3000 in your browser
echo ========================================================================
echo.

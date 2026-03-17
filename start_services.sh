#!/bin/bash
# Resume Matching System - Service Starter
# Starts the matching microservice and API gateway in separate terminal windows/tabs

echo ""
echo "========================================================================"
echo "Resume Matching System - Starting Services"
echo "========================================================================"
echo ""

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    echo "[1/2] Starting Matching Microservice on port 8001 (macOS)..."
    open -a Terminal <<EOF
cd "$(pwd)" && python -m src.services.matching_service:app --port 8001
EOF

    echo "[Waiting 5 seconds for service initialization...]"
    sleep 5

    echo "[2/2] Starting API Gateway on port 8000 (macOS)..."
    open -a Terminal <<EOF
cd "$(pwd)" && python -m uvicorn gateway:app --port 8000
EOF

elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    echo "[1/2] Starting Matching Microservice on port 8001 (Linux)..."
    gnome-terminal -- bash -c "cd \"$(pwd)\" && python -m src.services.matching_service:app --port 8001; read -p 'Press enter to exit...'" &

    echo "[Waiting 5 seconds for service initialization...]"
    sleep 5

    echo "[2/2] Starting API Gateway on port 8000 (Linux)..."
    gnome-terminal -- bash -c "cd \"$(pwd)\" && python -m uvicorn gateway:app --port 8000; read -p 'Press enter to exit...'" &

else
    # Windows (Git Bash / Cygwin)
    echo "[1/2] Starting Matching Microservice on port 8001 (Windows)..."
    python -m src.services.matching_service:app --port 8001 &

    echo "[Waiting 5 seconds for service initialization...]"
    sleep 5

    echo "[2/2] Starting API Gateway on port 8000 (Windows)..."
    python -m uvicorn gateway:app --port 8000 &
fi

echo ""
echo "========================================================================"
echo "Startup Complete!"
echo "========================================================================"
echo ""
echo "Services started:"
echo "  - API Gateway:      http://localhost:8000"
echo "  - Matching Service: http://localhost:8001"
echo ""
echo "Documentation:"
echo "  - Gateway Docs:     http://localhost:8000/docs"
echo "  - Service Docs:     http://localhost:8001/docs"
echo ""
echo "========================================================================"
echo ""

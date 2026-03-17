#!/bin/bash
# Quick start scripts for Resume Matching System API

# Development mode with auto-reload
echo "Starting API server in development mode..."
python main.py --reload

# Alternative: Production-like mode with multiple workers
# python main.py --host 0.0.0.0 --port 8000 --workers 4

# Alternative: Custom port for testing
# python main.py --port 8080

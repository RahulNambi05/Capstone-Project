"""
API Gateway for Resume Matching System.
Routes requests to appropriate microservices and handles service health checks.
Runs on port 8000 as the main entry point.
"""
import logging
import httpx
from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# Configuration
# ============================================================================

MATCHING_SERVICE_URL = "http://localhost:8001"
SERVICE_TIMEOUT = 120  # seconds
_matching_health_cache: Dict[str, Any] = {"ts": None, "data": None}

# ============================================================================
# Request/Response Models
# ============================================================================

class MatchRequest(BaseModel):
    """Request model for job matching."""
    job_description: str
    top_k: int = 10


class HealthResponse(BaseModel):
    """Health check response from gateway."""
    status: str
    gateway: str
    timestamp: str
    services: Dict[str, Any]


class ErrorResponse(BaseModel):
    """Error response model."""
    status: str
    message: str
    timestamp: str


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="Resume Matching System - API Gateway",
    description="Central gateway routing requests to Resume Matching microservices",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Health Check Functions
# ============================================================================

async def check_matching_service_health() -> Dict[str, Any]:
    """
    Check if the matching microservice is healthy.

    Returns:
        Dictionary with service status information
    """
    try:
        global _matching_health_cache
        now = datetime.utcnow()
        if _matching_health_cache["ts"] and _matching_health_cache["data"]:
            age_s = (now - _matching_health_cache["ts"]).total_seconds()
            if age_s < 5:
                return _matching_health_cache["data"]

        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
            response = await client.get(
                f"{MATCHING_SERVICE_URL}/health",
                timeout=10.0
            )
            if response.status_code == 200:
                data = response.json()
                payload = {
                    "status": "healthy",
                    "url": MATCHING_SERVICE_URL,
                    "service": "matching",
                    "total_documents": data.get("total_documents", 0),
                    "vector_store_ready": data.get("vector_store_ready", False)
                }
                _matching_health_cache = {"ts": now, "data": payload}
                return payload
            else:
                return {
                    "status": "degraded",
                    "url": MATCHING_SERVICE_URL,
                    "service": "matching",
                    "error": f"HTTP {response.status_code}"
                }
    except Exception as e:
        logger.warning(f"Matching service health check failed: {str(e)}")
        return {
            "status": "unavailable",
            "url": MATCHING_SERVICE_URL,
            "service": "matching",
            "error": str(e)
        }


# ============================================================================
# Endpoints
# ============================================================================

@app.get("/", tags=["Root"])
async def root():
    """Gateway root endpoint with documentation links."""
    return {
        "message": "Resume Matching System - API Gateway",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": "/openapi.json",
        "services": {
            "matching": f"{MATCHING_SERVICE_URL}",
        },
        "endpoints": {
            "health": "GET /health",
            "match": "POST /api/v1/match",
            "stats": "GET /api/v1/stats"
        }
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check() -> HealthResponse:
    """
    Gateway health check endpoint.

    Checks the health of all downstream microservices and returns
    aggregated status information.

    Returns:
        Health status of gateway and all services
    """
    try:
        matching_status = await check_matching_service_health()

        # Determine overall gateway status
        all_healthy = matching_status.get("status") == "healthy"
        gateway_status = "healthy" if all_healthy else "degraded"

        return HealthResponse(
            status=gateway_status,
            gateway="api_gateway",
            timestamp=datetime.utcnow().isoformat(),
            services={
                "matching": matching_status
            }
        )
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return HealthResponse(
            status="degraded",
            gateway="api_gateway",
            timestamp=datetime.utcnow().isoformat(),
            services={
                "matching": {
                    "status": "unavailable",
                    "error": str(e)
                }
            }
        )


@app.post("/api/v1/match", tags=["Matching"])
async def match_job_candidates(request: MatchRequest):
    """
    Forward job matching request to matching microservice.

    This endpoint receives job matching requests and forwards them
    to the matching microservice running on port 8001.

    Parameters:
    - **job_description**: Complete job description text
    - **top_k**: Number of candidates to return (default: 10, max: 100)

    Returns:
    - Ranked candidates from matching service

    Raises:
    - 503: Matching service unavailable
    - 504: Matching service timeout
    """
    try:
        logger.info(f"Forwarding match request to {MATCHING_SERVICE_URL}/match")

        # Check if matching service is available
        matching_health = await check_matching_service_health()
        if matching_health.get("status") != "healthy":
            logger.error(f"Matching service is not healthy: {matching_health}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Matching service is currently unavailable. Please try again later."
            )

        # Forward request to matching service
        async with httpx.AsyncClient(timeout=httpx.Timeout(SERVICE_TIMEOUT)) as client:
            response = await client.post(
                f"{MATCHING_SERVICE_URL}/match",
                json=request.dict(),
                timeout=SERVICE_TIMEOUT
            )

        # Check response status
        if response.status_code == 200:
            logger.info(f"Match request successful: {response.json().get('total_found', 0)} candidates found")
            return response.json()
        else:
            logger.error(f"Matching service error: {response.status_code} - {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Matching service error: {response.text}"
            )

    except httpx.TimeoutException:
        logger.error("Matching service request timed out")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Matching service request timed out. Please try again with a smaller dataset."
        )
    except httpx.ConnectError:
        logger.error(f"Cannot connect to matching service at {MATCHING_SERVICE_URL}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Cannot connect to matching service. Is it running on {MATCHING_SERVICE_URL}?"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Gateway error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gateway error: {str(e)}"
        )


@app.get("/api/v1/stats", tags=["Analytics"])
async def get_statistics():
    """
    Forward statistics request to matching microservice.

    Returns statistics about the vector store and indexed candidates.

    Returns:
    - Vector store statistics from matching service

    Raises:
    - 503: Matching service unavailable
    """
    try:
        logger.info(f"Forwarding stats request to {MATCHING_SERVICE_URL}/stats")

        async with httpx.AsyncClient(timeout=httpx.Timeout(SERVICE_TIMEOUT)) as client:
            response = await client.get(
                f"{MATCHING_SERVICE_URL}/stats",
                timeout=SERVICE_TIMEOUT
            )

        if response.status_code == 200:
            logger.info("Stats request successful")
            return response.json()
        else:
            logger.error(f"Stats service error: {response.status_code} - {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Stats service error: {response.text}"
            )

    except httpx.ConnectError:
        logger.error(f"Cannot connect to matching service at {MATCHING_SERVICE_URL}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Matching service unavailable at {MATCHING_SERVICE_URL}"
        )
    except httpx.TimeoutException:
        logger.error("Stats request timed out")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Stats request timed out"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Gateway error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gateway error: {str(e)}"
        )


# ============================================================================
# Service Info Endpoint
# ============================================================================

@app.get("/services", tags=["Gateway"])
async def get_services_status():
    """
    Get status of all registered services.

    Returns:
    - Status information for all microservices
    """
    try:
        matching_status = await check_matching_service_health()

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "matching": matching_status
            },
            "gateway": {
                "status": "healthy",
                "port": 8000,
                "version": "1.0.0"
            }
        }
    except Exception as e:
        logger.error(f"Error getting services status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving services status: {str(e)}"
        )


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser(
        description="Resume Matching System - API Gateway",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run on default port 8000
  python gateway.py

  # Run on custom port
  python gateway.py --port 9000

  # Run with hot reload (development)
  python gateway.py --reload

  # Run on specific host/port
  python gateway.py --host 0.0.0.0 --port 8000
        """
    )

    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host to bind the gateway to (default: 127.0.0.1)"
    )

    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind the gateway to (default: 8000)"
    )

    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload on code changes (development mode)"
    )

    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of worker processes (default: 1)"
    )

    args = parser.parse_args()

    # Validate port range
    if not (1 <= args.port <= 65535):
        logger.error(f"Invalid port number: {args.port}. Must be between 1 and 65535.")
        sys.exit(1)

    logger.info("=" * 70)
    logger.info("Resume Matching System - API Gateway")
    logger.info("=" * 70)
    logger.info(f"Starting gateway on {args.host}:{args.port}")
    logger.info(f"Routing to matching service: {MATCHING_SERVICE_URL}")
    logger.info(f"Documentation available at http://{args.host}:{args.port}/docs")
    logger.info("=" * 70)

    uvicorn.run(
        "gateway:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=1 if args.reload else args.workers,
        log_level="info"
    )

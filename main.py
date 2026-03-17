"""
Main entry point for Resume Matching System API.
Launches the FastAPI application with configurable host and port.
Accepts CLI arguments: --host, --port, --reload
"""
import argparse
import logging
import sys
from pathlib import Path

import uvicorn

from src.core.config import settings
from src.api.main import app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def log_startup_info(host: str, port: int, reload: bool) -> None:
    """Log API startup information including configuration."""
    logger.info("=" * 70)
    logger.info("Resume Matching System API - Starting")
    logger.info("=" * 70)

    logger.info(f"\nAPI Configuration:")
    logger.info(f"  Host: {host}")
    logger.info(f"  Port: {port}")
    logger.info(f"  Reload: {reload}")
    logger.info(f"  Debug: {settings.DEBUG}")

    logger.info(f"\nLLM & Embedding Models:")
    logger.info(f"  LLM Model: {settings.OPENAI_LLM_MODEL}")
    logger.info(f"  Embedding Model: {settings.OPENAI_EMBEDDING_MODEL}")

    logger.info(f"\nDocument Processing:")
    logger.info(f"  Chunk Size: {settings.CHUNK_SIZE}")
    logger.info(f"  Chunk Overlap: {settings.CHUNK_OVERLAP}")
    logger.info(f"  Top K Candidates: {settings.TOP_K}")

    logger.info(f"\nVector Store:")
    logger.info(f"  Persist Directory: {settings.CHROMA_PERSIST_DIR}")
    logger.info(f"  Collection Name: resumes")

    logger.info(f"\nOpenAI API Key: {'✓ Configured' if settings.OPENAI_API_KEY else '✗ Not configured'}")
    logger.info(f"\nAPI Documentation:")
    logger.info(f"  Swagger UI: http://{host}:{port}/docs")
    logger.info(f"  ReDoc: http://{host}:{port}/redoc")
    logger.info(f"  OpenAPI Schema: http://{host}:{port}/openapi.json")

    logger.info("=" * 70)
    logger.info("API is ready to accept requests!")
    logger.info("=" * 70 + "\n")


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Resume Matching System API Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default settings (localhost:8000)
  python main.py

  # Run on different host/port
  python main.py --host 0.0.0.0 --port 8080

  # Run with hot reload for development
  python main.py --reload

  # Run on specific interface (accessible from network)
  python main.py --host 0.0.0.0 --port 8000 --reload
        """
    )

    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host to bind the server to (default: 127.0.0.1)"
    )

    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind the server to (default: 8000)"
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

    return parser.parse_args()


def main() -> None:
    """Main entry point for the API server."""
    try:
        # Parse arguments
        args = parse_arguments()

        # Validate port range
        if not (1 <= args.port <= 65535):
            logger.error(f"Invalid port number: {args.port}. Must be between 1 and 65535.")
            sys.exit(1)

        # Log startup information
        log_startup_info(host=args.host, port=args.port, reload=args.reload)

        # Run the server
        uvicorn.run(
            "src.api.main:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            workers=1 if args.reload else args.workers,  # Disable workers when reload is enabled
            log_level="info"
        )

    except KeyboardInterrupt:
        logger.info("\n\nServer interrupted by user.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

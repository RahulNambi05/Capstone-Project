"""
Configuration settings for the Resume Matching System.
"""
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os
from pydantic import field_validator

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings."""

    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_LLM_MODEL: str = os.getenv("OPENAI_LLM_MODEL", "gpt-4o-mini")
    OPENAI_EMBEDDING_MODEL: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

    # ChromaDB Configuration
    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma_db")

    # Document Processing Configuration
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "500"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "50"))

    # Vector Search Configuration
    TOP_K: int = int(os.getenv("TOP_K", "10"))

    # Application Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    DEBUG: bool = False

    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    class Config:
        env_file = ".env"
        case_sensitive = True

    @field_validator("DEBUG", mode="before")
    def _parse_debug(cls, v):
        """
        Accept common non-boolean environment values (e.g., DEBUG=release) without crashing.
        """
        if isinstance(v, bool):
            return v
        if v is None:
            return False
        s = str(v).strip().lower()
        if s in {"1", "true", "yes", "y", "on", "debug"}:
            return True
        if s in {"0", "false", "no", "n", "off", "release", "prod", "production"}:
            return False
        # Default safe value
        return False

    def validate_openai_key(self) -> bool:
        """Validate that OpenAI API key is configured."""
        if not self.OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY is not set. Please configure it in .env file or as an environment variable."
            )
        return True

    def __init__(self, **data):
        """Initialize settings and validate required values."""
        super().__init__(**data)
        # Validate on initialization
        if not self.OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY is not set. Please configure it in .env file or as an environment variable."
            )


# Create settings instance
settings = Settings()

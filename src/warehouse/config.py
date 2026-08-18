"""Database configuration and connection management."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)


class DatabaseConfig:
    """PostgreSQL connection configuration."""
    
    HOST = os.getenv("POSTGRES_HOST", "localhost")
    PORT = int(os.getenv("POSTGRES_PORT", 5432))
    DB = os.getenv("POSTGRES_DB", "f1_warehouse")
    USER = os.getenv("POSTGRES_USER", "postgres")
    PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres_password")
    
    @classmethod
    def get_connection_string(cls) -> str:
        """Return psycopg2 connection string."""
        return f"postgresql://{cls.USER}:{cls.PASSWORD}@{cls.HOST}:{cls.PORT}/{cls.DB}"
    
    @classmethod
    def get_sqlalchemy_uri(cls) -> str:
        """Return SQLAlchemy connection URI."""
        return f"postgresql+psycopg2://{cls.USER}:{cls.PASSWORD}@{cls.HOST}:{cls.PORT}/{cls.DB}"
    
    @classmethod
    def validate(cls) -> bool:
        """Check if all required config is set."""
        required = [cls.HOST, cls.PORT, cls.DB, cls.USER, cls.PASSWORD]
        return all(required)


class AppConfig:
    """Application-level configuration."""
    
    ENV = os.getenv("ENV", "development")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # Data paths
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    DATA_DIR = PROJECT_ROOT / "data"
    RAW_DIR = DATA_DIR / "raw"
    BRONZE_DIR = DATA_DIR / "bronze"
    KAGGLE_DIR = DATA_DIR / "kaggle"

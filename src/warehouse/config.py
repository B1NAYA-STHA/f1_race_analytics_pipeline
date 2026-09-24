"""Database configuration and connection management."""

import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import URL

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
    SSLMODE = os.getenv("POSTGRES_SSLMODE", "prefer")
    
    @classmethod
    def get_connection_string(cls) -> str:
        """Return psycopg2 connection string."""
        return URL.create(
            drivername="postgresql",
            username=cls.USER,
            password=cls.PASSWORD,
            host=cls.HOST,
            port=cls.PORT,
            database=cls.DB,
            query={"sslmode": cls.SSLMODE},
        ).render_as_string(hide_password=False)
    
    @classmethod
    def get_sqlalchemy_uri(cls) -> str:
        """Return SQLAlchemy connection URI."""
        return URL.create(
            drivername="postgresql+psycopg2",
            username=cls.USER,
            password=cls.PASSWORD,
            host=cls.HOST,
            port=cls.PORT,
            database=cls.DB,
            query={"sslmode": cls.SSLMODE},
        ).render_as_string(hide_password=False)
    
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

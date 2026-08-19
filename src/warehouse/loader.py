"""Load bronze CSV files into PostgreSQL warehouse."""

import sys
import logging
from pathlib import Path
from typing import List, Literal

import pandas as pd
from sqlalchemy import create_engine, text, inspect

from config import DatabaseConfig, AppConfig
from postgres_schema import BRONZE_SCHEMA, get_all_bronze_create_statements


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class BronzeLoader:
    """Load normalized bronze CSVs into PostgreSQL."""

    def __init__(self):
        if not DatabaseConfig.validate():
            raise ValueError("Database configuration is incomplete")

        self.engine = create_engine(DatabaseConfig.get_sqlalchemy_uri())
        self.bronze_dir = AppConfig.BRONZE_DIR

        logger.info(
            f"Connected to database: {DatabaseConfig.DB} at {DatabaseConfig.HOST}:{DatabaseConfig.PORT}"
        )

    def create_schema(self) -> bool:
        """Create database schemas (bronze, silver, marts)."""
        try:
            with self.engine.connect() as conn:
                conn.execute(text(get_all_bronze_create_statements()))
                conn.commit()
            logger.info("✓ Schemas created successfully")
            return True
        except Exception as e:
            logger.error(f"✗ Failed to create schemas: {e}")
            return False

    def get_bronze_tables(self) -> List[str]:
        """Get list of bronze CSV files to load."""
        if not self.bronze_dir.exists():
            logger.error(f"Bronze directory not found: {self.bronze_dir}")
            return []

        csv_files = sorted(self.bronze_dir.glob("*.csv"))
        tables = [f.stem for f in csv_files]
        logger.info(f"Found {len(tables)} bronze tables: {tables}")
        return tables

    def load_table(
        self, table_name: str, if_exists: Literal["fail", "replace", "append"] = "replace"
    ) -> bool:
        """Load a single CSV table into PostgreSQL.

        Args:
            table_name: Name of the table (without .csv extension)
            if_exists: How to handle existing table: 'replace', 'append', 'fail'

        Returns:
            True if successful, False otherwise
        """
        csv_path = self.bronze_dir / f"{table_name}.csv"

        if not csv_path.exists():
            logger.warning(f"CSV file not found: {csv_path}")
            return False

        try:
            # Read CSV with proper type inference
            df = pd.read_csv(csv_path, dtype=str)  # Keep as text to match bronze schema

            # Log before loading
            row_count = len(df)
            logger.info(f"Loading {table_name}: {row_count} rows")

            # Load to database
            df.to_sql(
                name=table_name,
                con=self.engine,
                schema=BRONZE_SCHEMA,
                if_exists=if_exists,
                index=False,
            )

            logger.info(f"✓ Loaded {table_name}: {row_count} rows")
            return True

        except Exception as e:
            logger.error(f"✗ Failed to load {table_name}: {e}")
            return False

    def load_all_tables(self, if_exists: Literal["fail", "replace", "append"] = "replace") -> dict:
        """Load all bronze tables into PostgreSQL.

        Args:
            if_exists: How to handle existing tables: 'replace', 'append', 'fail'

        Returns:
            Dictionary with table names and success status
        """
        tables = self.get_bronze_tables()
        results = {}

        for table_name in tables:
            success = self.load_table(table_name, if_exists=if_exists)
            results[table_name] = success

        # Summary
        successful = sum(1 for s in results.values() if s)
        total = len(results)
        logger.info(f"\n{'=' * 60}")
        logger.info(f"Load complete: {successful}/{total} tables loaded successfully")
        logger.info(f"{'=' * 60}\n")

        return results

    def validate_load(self) -> bool:
        """Validate that all tables were loaded correctly."""
        try:
            inspector = inspect(self.engine)
            schema_tables = inspector.get_table_names(schema=BRONZE_SCHEMA)

            expected_tables = [
                "seasons",
                "status",
                "circuits",
                "drivers",
                "constructors",
                "races",
                "results",
                "qualifying",
                "sprint_results",
                "lap_times",
                "pit_stops",
                "driver_standings",
                "constructor_standings",
            ]

            missing = set(expected_tables) - set(schema_tables)

            if missing:
                logger.error(f"Missing tables: {missing}")
                return False

            # Check row counts
            with self.engine.connect() as conn:
                for table in expected_tables:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {BRONZE_SCHEMA}.{table}"))
                    row_count = result.scalar()
                    logger.info(f"{table}: {row_count} rows")

            logger.info("✓ Validation passed: All tables loaded")
            return True

        except Exception as e:
            logger.error(f"✗ Validation failed: {e}")
            return False

    def close(self):
        """Close database connection."""
        self.engine.dispose()
        logger.info("Database connection closed")


def main():
    """Main entry point."""
    loader = BronzeLoader()

    try:
        # Step 1: Create schemas
        if not loader.create_schema():
            return 1

        # Step 2: Load all tables
        results = loader.load_all_tables(if_exists="replace")

        # Step 3: Validate
        if not loader.validate_load():
            return 1

        logger.info("✓ Bronze data successfully loaded to PostgreSQL")
        return 0

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        return 1

    finally:
        loader.close()


if __name__ == "__main__":
    sys.exit(main())

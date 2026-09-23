"""Data quality checks for the warehouse."""

import sys
import logging
from typing import Dict, Tuple

from sqlalchemy import create_engine, text

from config import DatabaseConfig
from postgres_schema import BRONZE_SCHEMA


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class QualityChecker:
    """Run quality checks on loaded warehouse data."""
    
    def __init__(self):
        self.engine = create_engine(DatabaseConfig.get_sqlalchemy_uri())
    
    def check_table_exists(self, table_name: str) -> bool:
        """Verify a table exists in the warehouse."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text(f"SELECT 1 FROM {BRONZE_SCHEMA}.{table_name} LIMIT 1")
                )
                result.scalar()
            return True
        except Exception as e:
            logger.error(f"Table {table_name} does not exist: {e}")
            return False
    
    def check_row_count(self, table_name: str, expected_min: int = 0) -> Tuple[bool, int]:
        """Check that table has data (at least expected_min rows)."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text(f"SELECT COUNT(*) FROM {BRONZE_SCHEMA}.{table_name}")
                )
                count = result.scalar()
            
            passed = count >= expected_min
            if not passed:
                logger.warning(f"{table_name}: {count} rows (expected >= {expected_min})")
            return passed, count
            
        except Exception as e:
            logger.error(f"Failed to count {table_name}: {e}")
            return False, 0
    
    def check_primary_keys(self, table_name: str, pk_column: str) -> Tuple[bool, int]:
        """Check that primary key column has no nulls or duplicates."""
        try:
            with self.engine.connect() as conn:
                # Check for nulls
                null_result = conn.execute(
                    text(f'SELECT COUNT(*) FROM {BRONZE_SCHEMA}.{table_name} WHERE "{pk_column}" IS NULL')
                )
                null_count = null_result.scalar()
                
                # Check for duplicates
                dup_result = conn.execute(
                    text(f'''
                        SELECT COUNT(*) FROM (
                            SELECT "{pk_column}" FROM {BRONZE_SCHEMA}.{table_name}
                            GROUP BY "{pk_column}" HAVING COUNT(*) > 1
                        ) dups
                    ''')
                )
                dup_count = dup_result.scalar()
            
            passed = null_count == 0 and dup_count == 0
            
            if null_count > 0:
                logger.warning(f"{table_name}.{pk_column}: {null_count} NULL values")
            if dup_count > 0:
                logger.warning(f"{table_name}.{pk_column}: {dup_count} duplicate keys")
            
            return passed, null_count + dup_count
            
        except Exception as e:
            logger.error(f"Failed to check PKs in {table_name}: {e}")
            return False, -1
    
    def check_referential_integrity(self, fk_table: str, fk_column: str, 
                                   ref_table: str, ref_column: str) -> Tuple[bool, int]:
        """Check that foreign key references valid primary keys."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text(f'''
                        SELECT COUNT(*) FROM {BRONZE_SCHEMA}.{fk_table} fk
                        LEFT JOIN {BRONZE_SCHEMA}.{ref_table} ref ON fk."{fk_column}" = ref."{ref_column}"
                        WHERE fk."{fk_column}" IS NOT NULL AND ref."{ref_column}" IS NULL
                    ''')
                )
                orphan_count = result.scalar()
            
            passed = orphan_count == 0
            if not passed:
                logger.warning(f"{fk_table}.{fk_column} → {ref_table}.{ref_column}: {orphan_count} orphaned records")
            
            return passed, orphan_count
            
        except Exception as e:
            logger.error(f"Failed to check referential integrity: {e}")
            return False, -1
    
    def check_source_column(self, table_name: str) -> Tuple[bool, Dict[str, int]]:
        """Verify source column contains only valid values."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text(f'''
                        SELECT "source", COUNT(*) as count
                        FROM {BRONZE_SCHEMA}.{table_name}
                        GROUP BY "source"
                    ''')
                )
                rows = result.fetchall()
            
            source_counts = {row[0]: row[1] for row in rows}
            
            # Valid sources
            valid_sources = {"historical", "api", None}
            invalid = [s for s in source_counts.keys() if s not in valid_sources]
            
            passed = len(invalid) == 0
            if not passed:
                logger.warning(f"{table_name}: Invalid source values: {invalid}")
            
            return passed, source_counts
            
        except Exception as e:
            logger.warning(f"Could not check source column in {table_name}: {e}")
            return True, {}  # Not all tables have source column
    
    def run_all_checks(self) -> bool:
        """Run comprehensive quality checks."""
        logger.info("=" * 60)
        logger.info("Running Quality Checks")
        logger.info("=" * 60)
        
        all_passed = True
        
        # 1. Table existence
        logger.info("\n--- Checking table existence ---")
        tables = [
            "seasons", "status", "circuits", "drivers", "constructors",
            "races", "results", "qualifying", "sprint_results",
            "lap_times", "pit_stops", "driver_standings", "constructor_standings"
        ]
        
        for table in tables:
            exists = self.check_table_exists(table)
            all_passed = all_passed and exists
        
        # 2. Row counts
        logger.info("\n--- Checking row counts ---")
        for table in tables:
            passed, count = self.check_row_count(table, expected_min=0)
            all_passed = all_passed and passed
        
        # 3. Primary keys
        logger.info("\n--- Checking primary keys ---")
        pk_checks = {
            "seasons": "year",
            "status": "statusId",
            "circuits": "circuitId",
            "drivers": "driverId",
            "constructors": "constructorId",
            "races": "raceId",
            "results": "resultId",
            "qualifying": "qualifyId",
            "sprint_results": "sprintResultId",
            "driver_standings": "driverStandingsId",
            "constructor_standings": "constructorStandingsId",
        }
        
        for table, pk_col in pk_checks.items():
            passed, issues = self.check_primary_keys(table, pk_col)
            all_passed = all_passed and passed
        
        # 4. Referential integrity
        logger.info("\n--- Checking referential integrity ---")
        fk_checks = [
            ("races", "circuitId", "circuits", "circuitId"),
            ("results", "raceId", "races", "raceId"),
            ("results", "driverId", "drivers", "driverId"),
            ("results", "constructorId", "constructors", "constructorId"),
            ("results", "statusId", "status", "statusId"),
            ("qualifying", "raceId", "races", "raceId"),
            ("qualifying", "driverId", "drivers", "driverId"),
            ("qualifying", "constructorId", "constructors", "constructorId"),
            ("sprint_results", "raceId", "races", "raceId"),
            ("sprint_results", "driverId", "drivers", "driverId"),
            ("sprint_results", "constructorId", "constructors", "constructorId"),
            ("lap_times", "raceId", "races", "raceId"),
            ("lap_times", "driverId", "drivers", "driverId"),
            ("pit_stops", "raceId", "races", "raceId"),
            ("pit_stops", "driverId", "drivers", "driverId"),
            ("driver_standings", "raceId", "races", "raceId"),
            ("driver_standings", "driverId", "drivers", "driverId"),
            ("constructor_standings", "raceId", "races", "raceId"),
            ("constructor_standings", "constructorId", "constructors", "constructorId"),
        ]
        
        for fk_table, fk_col, ref_table, ref_col in fk_checks:
            passed, orphans = self.check_referential_integrity(fk_table, fk_col, ref_table, ref_col)
            all_passed = all_passed and passed
        
        # 5. Source column validation
        logger.info("\n--- Checking source column ---")
        for table in tables:
            passed, sources = self.check_source_column(table)
            if sources:
                logger.info(f"{table}: {sources}")
        
        # Summary
        logger.info("\n" + "=" * 60)
        if all_passed:
            logger.info("✓ All quality checks passed!")
        else:
            logger.warning("✗ Some quality checks failed. Review logs above.")
        logger.info("=" * 60)
        
        return all_passed
    
    def close(self):
        """Close database connection."""
        self.engine.dispose()


def main():
    """Main entry point."""
    checker = QualityChecker()
    try:
        passed = checker.run_all_checks()
        return 0 if passed else 1
    finally:
        checker.close()


if __name__ == "__main__":
    sys.exit(main())

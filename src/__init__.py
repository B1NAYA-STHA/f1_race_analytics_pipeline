"""F1 Analytics Pipeline - Data ingestion, normalization, and warehouse loading.

Pipeline stages:
- ingest: Download F1 data from Ergast and Jolpica APIs
- normalize: Merge and normalize raw data into bronze CSVs
- warehouse: Load bronze data into PostgreSQL and validate
"""

import logging

import pandas as pd
from sqlalchemy import create_engine, text, MetaData, Table as SATable
from sqlalchemy.dialects.postgresql import insert as pg_insert

from aqi_config.settings import Settings
from src.transform.quality.data_validator import DataValidator

logger = logging.getLogger(__name__)

BATCH_SIZE = 5000


class PostgresLoader:
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.engine = None
        logger.info("PostgresLoader initialized")

    def _get_engine(self):
        if self.engine is None:
            try:
                self.engine = create_engine(
                    self.db_url, pool_size=5, max_overflow=10, pool_pre_ping=True
                )
                with self.engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                logger.info("Database connection established")
            except Exception as e:
                logger.error(f"Failed to connect to database: {e}")
                raise
        return self.engine

    def _ensure_tables(self, schema: str):
        engine = self._get_engine()
        sql = Settings.SCHEMA_SQL_PATH.read_text().format(schema=schema)
        with engine.begin() as conn:
            for statement in sql.split(";"):
                statement = statement.strip()
                if statement:
                    conn.execute(text(statement))
        logger.info("Tables ensured in schema '%s'", schema)

    def _insert_with_conflict(
        self,
        df: pd.DataFrame,
        table_name: str,
        schema: str,
    ) -> int:
        engine = self._get_engine()
        table = SATable(
            table_name,
            MetaData(schema=schema),
            autoload_with=engine,
        )
        rows = df.to_dict(orient="records")
        if not rows:
            return 0

        total_inserted = 0
        chunk_count = (len(rows) + BATCH_SIZE - 1) // BATCH_SIZE

        for chunk_idx, chunk_start in enumerate(range(0, len(rows), BATCH_SIZE)):
            chunk = rows[chunk_start : chunk_start + BATCH_SIZE]
            stmt = pg_insert(table).values(chunk)
            stmt = stmt.on_conflict_do_nothing()

            with engine.begin() as connection:
                result = connection.execute(stmt)
                total_inserted += result.rowcount

            if chunk_count > 1:
                logger.info(
                    "[Load] %s: lot %d/%d termine (%d lignes)",
                    table_name,
                    chunk_idx + 1,
                    chunk_count,
                    len(chunk),
                )

        return total_inserted

    def save_star_schema(
        self,
        dim_city: pd.DataFrame,
        dim_date: pd.DataFrame,
        fact_aqi: pd.DataFrame,
        schema: str,
    ):
        logger.info("Saving star schema to PostgreSQL")
        engine = self._get_engine()
        with engine.begin() as conn:
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
        self._ensure_tables(schema)

        tables = {
            "dim_city": dim_city,
            "dim_date": dim_date,
            "fact_aqi": fact_aqi,
        }

        total = 0
        for table_name in ("dim_city", "dim_date", "fact_aqi"):
            df = tables[table_name]
            if df.empty:
                continue
            DataValidator.validate(df, table_name)
            inserted = self._insert_with_conflict(df, table_name, schema)
            total += inserted
            logger.info(
                "[Load] %s: %d rows inserted (skipped if existing)",
                table_name,
                inserted,
            )

        logger.info(
            "[Load] Star schema saved: %d total rows in %s",
            total,
            schema,
        )

import logging

import pandas as pd
from sqlalchemy import create_engine, text, MetaData, Table as SATable
from sqlalchemy.dialects.postgresql import insert as pg_insert

from src.transform.quality.data_validator import DataValidator

logger = logging.getLogger(__name__)

BATCH_SIZE = 5000

CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS {schema}.dim_city (
    city_key    INTEGER PRIMARY KEY,
    city_name   VARCHAR(100) NOT NULL,
    country     VARCHAR(100),
    latitude    DOUBLE PRECISION,
    longitude   DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS {schema}.dim_date (
    date_key    INTEGER PRIMARY KEY,
    full_date   DATE NOT NULL,
    hour        INTEGER NOT NULL,
    day_of_week VARCHAR(10),
    is_weekend  BOOLEAN,
    month       INTEGER,
    year        INTEGER
);

CREATE TABLE IF NOT EXISTS {schema}.fact_aqi (
    fact_id     SERIAL PRIMARY KEY,
    city_key    INTEGER NOT NULL,
    date_key    INTEGER NOT NULL,
    aqi         INTEGER,
    co          DOUBLE PRECISION,
    no          DOUBLE PRECISION,
    no2         DOUBLE PRECISION,
    o3          DOUBLE PRECISION,
    so2         DOUBLE PRECISION,
    pm2_5       DOUBLE PRECISION,
    pm10        DOUBLE PRECISION,
    nh3         DOUBLE PRECISION
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_fact_aqi_city_date
    ON {schema}.fact_aqi (city_key, date_key);
"""

UNIQUE_INDEXES = {
    "dim_city":  [["city_key"]],
    "dim_date":  [["date_key"]],
    "fact_aqi":  [["city_key", "date_key"]],
}


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
        with engine.begin() as conn:
            for statement in CREATE_TABLES_SQL.format(schema=schema).split(";"):
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

    def _create_fk_if_not_exists(
        self,
        conn,
        schema: str,
        child: str,
        child_col: str,
        parent: str,
        parent_col: str,
    ):
        fk_name = f"fk_{child}_{child_col}"
        sql = text(f"""
            DO $$ BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.table_constraints
                    WHERE constraint_name = '{fk_name}' AND table_schema = '{schema}'
                ) THEN
                    ALTER TABLE {schema}.{child}
                    ADD CONSTRAINT {fk_name}
                    FOREIGN KEY ({child_col}) REFERENCES {schema}.{parent} ({parent_col});
                END IF;
            END $$;
        """)
        conn.execute(sql)

    def _ensure_foreign_keys(self, schema: str):
        engine = self._get_engine()
        with engine.connect() as conn:
            self._create_fk_if_not_exists(
                conn, schema, "fact_aqi", "city_key", "dim_city", "city_key"
            )
            self._create_fk_if_not_exists(
                conn, schema, "fact_aqi", "date_key", "dim_date", "date_key"
            )
            conn.commit()
        logger.info("Foreign keys ensured in schema '%s'", schema)

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

        self._ensure_foreign_keys(schema)

        logger.info(
            "[Load] Star schema saved: %d total rows in %s",
            total,
            schema,
        )

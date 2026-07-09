import logging
import pandas as pd
from sqlalchemy import create_engine, text

from src.transform.quality.data_validator import DataValidator

logger = logging.getLogger(__name__)


class PostgresLoader:

    def __init__(self, db_url):
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
                logger.error(f"Failed to connect to database: {str(e)}")
                raise
        return self.engine

    def _delete_all(self, table_name, schema):
        full = f"{schema}.{table_name}" if schema else table_name
        with self._get_engine().connect() as conn:
            conn.execute(text(f"DELETE FROM {full}"))
            conn.commit()
        logger.debug(f"Cleared existing rows from {full}")

    def _ensure_unique_constraint(self, conn, schema, table, column):
        constraint_name = f"uq_{table}_{column}"
        sql = text(f"""
            DO $$ BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.table_constraints
                    WHERE constraint_name = '{constraint_name}' AND table_schema = '{schema}'
                ) THEN
                    ALTER TABLE {schema}.{table}
                    ADD CONSTRAINT {constraint_name} UNIQUE ({column});
                END IF;
            END $$;
        """)
        conn.execute(sql)

    def _create_fk_if_not_exists(self, conn, schema, child, child_col, parent, parent_col):
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

    def save(self, df, table_name, schema, chunksize=1000):
        full_table_name = f"{schema}.{table_name}" if schema else table_name
        logger.info(f"Saving {len(df)} records to {full_table_name}")

        DataValidator.validate(df, table_name)

        try:
            engine = self._get_engine()

            df.to_sql(
                name=table_name,
                con=engine,
                schema=schema,
                if_exists="append",
                index=False,
                chunksize=chunksize,
                method="multi",
            )
            logger.info(f"Successfully saved to {full_table_name}")
        except Exception as e:
            logger.error(f"Error saving to PostgreSQL {full_table_name}: {str(e)}")
            raise

    def save_star_schema(self, dim_date, dim_city, fact_aqi, fact_aqi_today, schema):
        logger.info("Saving star schema tables to PostgreSQL")

        engine = self._get_engine()
        with engine.connect() as conn:
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
            conn.commit()

        tables = {
            "dim_date": dim_date,
            "dim_city": dim_city,
            "fact_aqi": fact_aqi,
            "fact_aqi_today": fact_aqi_today,
        }

        for table_name, df in tables.items():
            if df.empty:
                logger.warning(f"Skipping empty table: {table_name}")
                continue
            self._delete_all(table_name, schema)
            self.save(df=df, table_name=table_name, schema=schema)

        engine = self._get_engine()
        with engine.connect() as conn:
            self._ensure_unique_constraint(conn, schema, "dim_city", "city_key")
            self._ensure_unique_constraint(conn, schema, "dim_date", "date_key")
            self._create_fk_if_not_exists(conn, schema, "fact_aqi", "city_key", "dim_city", "city_key")
            self._create_fk_if_not_exists(conn, schema, "fact_aqi", "date_key", "dim_date", "date_key")
            self._create_fk_if_not_exists(conn, schema, "fact_aqi_today", "city_key", "dim_city", "city_key")
            self._create_fk_if_not_exists(conn, schema, "fact_aqi_today", "date_key", "dim_date", "date_key")
            conn.commit()

        logger.info("Star schema tables saved to PostgreSQL successfully")

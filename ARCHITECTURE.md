# Architecture

This document describes the technical stack and the reasoning behind each major design decision in the Air Quality ETL pipeline.

## 1. Stack and Justification

| Layer | Choice | Justification |
|---|---|---|
| Language | Python 3.14 | Mature data-engineering ecosystem (pandas, requests, SQLAlchemy) and a shared skillset across the team. |
| Dependency management | uv, `pyproject.toml`, `uv.lock` | Fast, deterministic installs so every developer and the Airflow container run identical dependency versions. |
| Extraction | `requests` with exponential-backoff retry | Handles the OpenWeather free-tier rate limit without pulling in a heavier HTTP framework. |
| Transformation | pandas | Star-schema joins, deduplication, and type coercion are simplest to express as DataFrame operations at this data volume (~155,000 rows). |
| Orchestration | Apache Airflow, two DAGs | Native cron-style scheduling, per-task retries, and a UI that provides unattended run history. Separate DAGs for backfill (`@once`) and hourly (`@hourly`) feeds. |
| Raw and clean storage | CSV files on disk | Raw data remains untouched and clean data can be rebuilt from raw; flat files make both easy to audit. |
| Data warehouse | PostgreSQL | Free, relational, enforces foreign-key integrity between `fact_aqi` and its dimensions, and integrates directly via SQLAlchemy. |
| Testing | pytest | Low-friction and standard; each developer owns the tests for their own extract, transform, or load module. |
| CI | GitHub Actions (uv + pytest) | Runs on every push and PR against main/preprod/prod. |

## 2. Data Flow

The pipeline runs in four stages, coordinated by two Airflow DAGs:

1. **Validate** — confirm required environment variables are present.
2. **Extract** — pull data per city from the OpenWeather API. The hourly DAG (`air_quality_pipeline`) runs every hour; the backfill DAG (`backfill`) runs once. The backfill writes per-city, per-month CSVs; the hourly feed writes per-city, per-hour CSVs — all to `data/raw/`.
3. **Clean & Rebuild** — all files in `data/raw/` are read, deduplicated, sorted, and rewritten as a single combined CSV at `data/clean/hourly_aqi_combined.csv`.
4. **Load** — the clean dataset is split into `dim_city`, `dim_date`, and `fact_aqi` and upserted into PostgreSQL.

```
OpenWeather API  -->  data/raw/{backfill,hourly}/*.csv
                              |
                              v
                 data/clean/hourly_aqi_combined.csv
                              |
                              v
                 data/star_schema/{dim_city,dim_date,fact_aqi}.csv
                              |
                              v
                 PostgreSQL (air_quality)
```

Task order in the hourly DAG: `validate_settings >> extract_hourly >> rebuild_clean >> load_to_warehouse`.

Task order in the backfill DAG: `validate_settings >> extract_backfill >> rebuild_clean >> load_to_warehouse`.

## 3. Key Design Decisions

**Raw data is immutable.** Every extraction run writes a new, uniquely named file; nothing downstream modifies these files. This preserves an audit trail and makes the pipeline replayable from any point.

**Clean data is rebuilt on every run, never appended.** `rebuild_clean` reads all of `data/raw/` each time and regenerates the combined CSV from scratch. A bug in the cleaning logic can be fixed and replayed without re-calling the API.

**Dimensions hold no measures; the fact table holds no descriptions.** `dim_city` and `dim_date` are pure lookup tables. `fact_aqi` holds only foreign keys and the eight AQI/pollutant values. This keeps the model normalized and avoids duplicating descriptive data across ~155,000 rows.

**Backfill and hourly feeds share a single fact table.** Both write into `fact_aqi`, deduplicated on `(city_key, date_key)` via a unique index, rather than maintaining separate historical and live tables. This simplifies downstream queries to one source of truth.

**Loading uses ON CONFLICT DO NOTHING (upsert), not delete-then-append.** The `PostgresLoader` batches rows in groups of 5,000 and inserts with PostgreSQL's `pg_insert.on_conflict_do_nothing()`. This keeps loading idempotent and safe to re-run.

**Cities are processed sequentially.** The current implementation iterates over cities one at a time in both extraction and loading, avoiding rate-limit contention on the free-tier API key.

## 4. Known Gaps

- OpenWeather's Air Pollution API has no forecast endpoint, so the pipeline has no forecast zone.
- Historical data is limited to one year back by the API itself.
- Free-tier rate limits mean a full 12-month backfill across all six cities must be chunked into month-sized requests.
- `DataValidator` logs out-of-range values but does not reject them.
- Raw CSVs accumulate indefinitely with no retention policy.
- `dim_date` is fully rebuilt each run rather than incrementally updated.

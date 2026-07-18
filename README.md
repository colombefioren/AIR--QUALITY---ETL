<div align="center">

# Air Quality ETL

<img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white">
<img src="https://img.shields.io/badge/Apache_Airflow-017CEE?style=for-the-badge&logo=apacheairflow&logoColor=white">
<img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white">
<img src="https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white">
<img src="https://img.shields.io/badge/OpenWeather-EB6E4B?style=for-the-badge&logo=openweathermap&logoColor=white">
<img src="https://img.shields.io/badge/uv-DE5FE9?style=for-the-badge&logo=uv&logoColor=white">
<img src="https://img.shields.io/badge/pytest-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white">

</div>

Collects **AQI + 8 pollutant metrics** for six Madagascar cities via the OpenWeather Air Pollution API, cleans and validates the data, and loads it into **PostgreSQL**, orchestrated with **Apache Airflow** DAGs.

| Feed | Purpose | Cadence |
|---|---|---|
| Backfill | Historical AQI, 3-12 months back | Run once |
| Hourly | Live AQI collection | Every hour |

---

## Pipeline

```
  OpenWeather API
        │
        ▼
  Extract ──────────────────► data/raw/{backfill,hourly}/*.csv
        │
        ▼
  Clean & Validate ─────────► data/clean/hourly_aqi_combined.csv
        │
        ▼
  Build Star Schema ────────► data/star_schema/{dim_city,dim_date,fact_aqi}.csv
        │
        ▼
  Load to PostgreSQL ───────► air_quality database
```

The hourly DAG (`air_quality_pipeline`) runs on schedule. The backfill DAG (`backfill`) runs once via the Airflow UI.

---

## Cities

| City | Latitude | Longitude |
|---|---|---|
| Antananarivo | -18.8792 | 47.5079 |
| Toamasina | -18.1443 | 49.3958 |
| Mahajanga | -15.7167 | 46.3167 |
| Fianarantsoa | -21.4333 | 47.0833 |
| Toliara | -23.3500 | 43.6667 |
| Antsiranana | -12.2667 | 49.2833 |

All cities are in Madagascar. 6 cities x 12 months x hourly ~155,520 rows.

---

## Star Schema

### `dim_city`

| Column | Type | Description |
|---|---|---|
| `city_key` | `INTEGER PK` | Surrogate key |
| `city_name` | `VARCHAR(100)` | City name |
| `country` | `VARCHAR(100)` | Country |
| `latitude` | `DOUBLE PRECISION` | Latitude |
| `longitude` | `DOUBLE PRECISION` | Longitude |

### `dim_date`

| Column | Type | Description |
|---|---|---|
| `date_key` | `INTEGER PK` | Format YYYYMMDDHH |
| `full_date` | `DATE` | Calendar date |
| `hour` | `INTEGER` | 0-23 |
| `day_of_week` | `VARCHAR(10)` | Monday-Sunday |
| `is_weekend` | `BOOLEAN` | True if Sat or Sun |
| `month` | `INTEGER` | 1-12 |
| `year` | `INTEGER` | Year |

### `fact_aqi`

Unique index on `(city_key, date_key)` prevents duplicate hourly entries per city.

| Column | Type | Unit | Description |
|---|---|---|---|
| `fact_id` | `SERIAL PK` | -- | Auto-increment |
| `city_key` | `INTEGER FK` | -- | References dim_city |
| `date_key` | `INTEGER FK` | -- | References dim_date |
| `aqi` | `INTEGER` | -- | 1 (Good) to 5 (Very Poor) |
| `co` | `DOUBLE PRECISION` | ug/m3 | Carbon monoxide |
| `no` | `DOUBLE PRECISION` | ug/m3 | Nitrogen monoxide |
| `no2` | `DOUBLE PRECISION` | ug/m3 | Nitrogen dioxide |
| `o3` | `DOUBLE PRECISION` | ug/m3 | Ozone |
| `so2` | `DOUBLE PRECISION` | ug/m3 | Sulfur dioxide |
| `pm2_5` | `DOUBLE PRECISION` | ug/m3 | Fine PM (<2.5um) |
| `pm10` | `DOUBLE PRECISION` | ug/m3 | Coarse PM (<10um) |
| `nh3` | `DOUBLE PRECISION` | ug/m3 | Ammonia |

---

## Clean Data Columns

Intermediate file `data/clean/hourly_aqi_combined.csv`:

`city_name`, `latitude`, `longitude`, `datetime`, `date`, `hour`, `aqi`, `co`, `no`, `no2`, `o3`, `so2`, `pm2_5`, `pm10`, `nh3`

Validated ranges:

| Column | Range |
|---|---|
| `aqi` | 1 - 5 |
| `co` | 0 - 50,000 |
| `no` | 0 - 2,000 |
| `no2` | 0 - 2,000 |
| `o3` | 0 - 500 |
| `so2` | 0 - 2,000 |
| `pm2_5` | 0 - 500 |
| `pm10` | 0 - 500 |
| `nh3` | 0 - 500 |

---

## Period Covered

Data starts from the first backfill run. `dim_date` dynamically indexes every unique hour present in the clean dataset.

---

## Known Gaps

- `DataValidator` logs out-of-range values but does **not reject** them.
- Backfill DAG (`schedule="@once"`) must be triggered manually.
- `dim_date` is **rebuilt from scratch** each run, not incrementally updated.
- `sql/schema.sql` is a reference copy -- table creation is inline in `PostgresLoader`.
- Raw CSVs accumulate with **no retention policy**.
- Cities are processed **sequentially** (no parallelisation).

---

## Configuration

Create `.env` at the project root:

```env
OPENWEATHER_API_KEY=your_api_key_here
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=air_quality
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password_here
POSTGRES_SCHEMA=public
```

Set `DATABASE_URL` to override individual Postgres variables.

---

## Project Structure

```
air-quality-etl/
├── aqi_config/                  settings, logging
├── dags/                        Airflow DAGs
│   ├── air_quality_dag.py       Hourly pipeline (@hourly)
│   ├── backfill_dag.py          Historical load (@once)
│   └── tasks.py                 Shared callables
├── src/
│   ├── cities.py                City definitions
│   ├── extract/
│   │   └── aqi_extractor.py     API calls with retry logic
│   ├── load/
│   │   ├── csv.py               Raw CSV writer
│   │   └── postgres.py          Postgres upsert loader
│   └── transform/
│       ├── quality/             Validator, cleaner, auditor
│       └── transformer/         AQI and date dimension builders
├── sql/schema.sql               DDL reference
├── data/
│   ├── raw/{hourly,backfill}    Per-city, per-month CSVs
│   ├── clean/                   Combined, deduplicated CSV
│   └── star_schema/             dim_city, dim_date, fact_aqi CSVs
├── tests/                       pytest suite
├── main.py                      Manual local runner
├── pyproject.toml
└── .env.example
```

---

## Running

### Via Airflow (production)

The hourly DAG runs automatically. Trigger the backfill DAG once from the Airflow UI (DAGs > backfill > Trigger DAG).

### Locally (manual test)

```bash
uv sync
cp .env.example .env    # fill in credentials
python main.py          # runs one hourly cycle
```

### Tests

```bash
uv run pytest tests/ -v
```

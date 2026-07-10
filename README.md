# Air Quality ETL Pipeline

Extracts air quality data from Visual Crossing API, transforms into a star schema, and loads to CSV files and PostgreSQL.

## Setup

1. Clone the repo
2. Create a `.env` file with:
   ```
    VISUAL_CROSSING_API_KEY=your_key
    POSTGRES_HOST=localhost  # optional, defaults to localhost
    POSTGRES_PORT=5432
   POSTGRES_DB=air_quality
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=postgres
   ```
3. Install dependencies: `uv sync`
4. Run: `python main.py`

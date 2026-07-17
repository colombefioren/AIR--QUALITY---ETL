CREATE TABLE IF NOT EXISTS {schema}.dim_region (
    region_id   INTEGER PRIMARY KEY,
    region_name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS {schema}.dim_city (
    city_key    INTEGER PRIMARY KEY,
    city_name   VARCHAR(100) NOT NULL UNIQUE,
    country     VARCHAR(100),
    latitude    DOUBLE PRECISION,
    longitude   DOUBLE PRECISION,
    region_id   INTEGER REFERENCES {schema}.dim_region(region_id)
);

CREATE TABLE IF NOT EXISTS {schema}.dim_pollutant_category (
    category_id   INTEGER PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS {schema}.dim_pollutant (
    pollutant_id   INTEGER PRIMARY KEY,
    code           VARCHAR(20) NOT NULL UNIQUE,
    name           VARCHAR(100) NOT NULL,
    unit           VARCHAR(50),
    category_id    INTEGER REFERENCES {schema}.dim_pollutant_category(category_id),
    who_threshold  DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS {schema}.dim_date (
    date_key    INTEGER PRIMARY KEY,
    full_date   DATE NOT NULL,
    hour        INTEGER NOT NULL,
    day_of_week VARCHAR(10),
    is_weekend  BOOLEAN,
    month       INTEGER,
    year        INTEGER,
    season      VARCHAR(10)
);

CREATE TABLE IF NOT EXISTS {schema}.fact_air_quality (
    fact_id      SERIAL PRIMARY KEY,
    city_key     INTEGER NOT NULL REFERENCES {schema}.dim_city(city_key),
    date_key     INTEGER NOT NULL REFERENCES {schema}.dim_date(date_key),
    pollutant_id INTEGER NOT NULL REFERENCES {schema}.dim_pollutant(pollutant_id),
    value        DOUBLE PRECISION,
    aqi          INTEGER,
    UNIQUE (city_key, date_key, pollutant_id)
);

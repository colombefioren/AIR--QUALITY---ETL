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
    nh3         DOUBLE PRECISION,
    FOREIGN KEY (city_key) REFERENCES {schema}.dim_city (city_key),
    FOREIGN KEY (date_key) REFERENCES {schema}.dim_date (date_key)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_fact_aqi_city_date
    ON {schema}.fact_aqi (city_key, date_key);

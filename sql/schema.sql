CREATE SCHEMA IF NOT EXISTS air_quality;

CREATE TABLE IF NOT EXISTS air_quality.dim_city (
    city_key   INTEGER PRIMARY KEY,
    city_name  VARCHAR(100) NOT NULL,
    region     VARCHAR(100),
    latitude   DOUBLE PRECISION,
    longitude  DOUBLE PRECISION,
    population INTEGER
);

CREATE TABLE IF NOT EXISTS air_quality.dim_date (
    date_key     INTEGER PRIMARY KEY,
    full_date    DATE NOT NULL,
    year         INTEGER NOT NULL,
    month        INTEGER NOT NULL,
    day          INTEGER NOT NULL,
    day_of_week  INTEGER NOT NULL,
    quarter      INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS air_quality.fact_aqi (
    aqi_key   SERIAL PRIMARY KEY,
    city_key  INTEGER NOT NULL REFERENCES air_quality.dim_city(city_key),
    date_key  INTEGER NOT NULL REFERENCES air_quality.dim_date(date_key),
    aqius     INTEGER,
    aqieur    INTEGER,
    pm1       DOUBLE PRECISION,
    pm2p5     DOUBLE PRECISION,
    pm10      DOUBLE PRECISION,
    o3        DOUBLE PRECISION,
    no2       DOUBLE PRECISION,
    so2       DOUBLE PRECISION,
    co        DOUBLE PRECISION,
    UNIQUE (city_key, date_key)
);

CREATE TABLE IF NOT EXISTS air_quality.fact_aqi_today (
    aqi_today_key  SERIAL PRIMARY KEY,
    city_key       INTEGER NOT NULL REFERENCES air_quality.dim_city(city_key),
    date_key       INTEGER NOT NULL REFERENCES air_quality.dim_date(date_key),
    hour           INTEGER NOT NULL,
    aqius          INTEGER,
    aqieur         INTEGER,
    pm1            DOUBLE PRECISION,
    pm2p5          DOUBLE PRECISION,
    pm10           DOUBLE PRECISION,
    o3             DOUBLE PRECISION,
    no2            DOUBLE PRECISION,
    so2            DOUBLE PRECISION,
    co             DOUBLE PRECISION,
    UNIQUE (city_key, date_key, hour)
);

CREATE INDEX IF NOT EXISTS idx_fact_aqi_city ON air_quality.fact_aqi(city_key);
CREATE INDEX IF NOT EXISTS idx_fact_aqi_date ON air_quality.fact_aqi(date_key);
CREATE INDEX IF NOT EXISTS idx_fact_aqi_today_city ON air_quality.fact_aqi_today(city_key);
CREATE INDEX IF NOT EXISTS idx_fact_aqi_today_date ON air_quality.fact_aqi_today(date_key);

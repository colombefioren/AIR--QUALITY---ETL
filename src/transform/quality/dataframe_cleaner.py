import numpy as np
import pandas as pd


class DataFrameCleaner:

    AQI_POLLUTANT_COLS = ["co", "no", "no2", "o3", "so2", "pm2_5", "pm10", "nh3"]
    AQI_META_COLS = ["aqi", "city_name", "city_id", "datetime", "dt"]

    @staticmethod
    def normalize_empty_strings(df):
        return df.replace(r"^\s*$", np.nan, regex=True)

    @staticmethod
    def remove_duplicates(df, subset=None):
        return df.drop_duplicates(subset=subset)

    @staticmethod
    def fill_numeric_nulls(df, columns):
        for column in columns:
            if column in df.columns:
                df[column] = df[column].fillna(0)
        return df

    @staticmethod
    def fill_categorical_nulls(df, fill_value="unknown"):
        for col in df.select_dtypes(include=["object"]).columns:
            df[col] = df[col].fillna(fill_value)
        return df

    @staticmethod
    def drop_all_null_columns(df):
        return df.dropna(axis=1, how="all")

    @staticmethod
    def dropna_rows(df, subset=None, how="any"):
        return df.dropna(subset=subset, how=how)

    @staticmethod
    def clean_air_quality_data(df):
        if df.empty:
            return df

        df = DataFrameCleaner.normalize_empty_strings(df)
        df = DataFrameCleaner.remove_duplicates(df)

        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if numeric_cols:
            df = DataFrameCleaner.fill_numeric_nulls(df, numeric_cols)

        df = DataFrameCleaner.fill_categorical_nulls(df)

        return df

    @staticmethod
    def clean_aqi_data(df):
        if df.empty:
            return df

        df = DataFrameCleaner.normalize_empty_strings(df)
        df = DataFrameCleaner.remove_duplicates(df, subset=["datetime", "city_name"])

        pollutant_cols = [c for c in DataFrameCleaner.AQI_POLLUTANT_COLS if c in df.columns]
        if pollutant_cols:
            df = DataFrameCleaner.fill_numeric_nulls(df, pollutant_cols)

        if "city_name" in df.columns:
            df = DataFrameCleaner.fill_categorical_nulls(df)

        return df

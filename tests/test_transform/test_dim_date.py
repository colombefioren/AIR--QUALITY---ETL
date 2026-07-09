import pytest
import pandas as pd
from src.transform.transformer.dim_date import DimDate


class TestDimDate:
    def test_create_returns_dataframe(self):
        df = DimDate.create()
        assert isinstance(df, pd.DataFrame)

    def test_create_has_expected_columns(self):
        df = DimDate.create()
        expected = {"date_key", "full_date", "year", "month", "day", "day_of_week", "quarter"}
        assert expected.issubset(set(df.columns))

    def test_create_covers_at_least_one_year(self):
        df = DimDate.create()
        years = df["year"].unique()
        assert len(years) >= 1

    def test_date_key_format(self):
        df = DimDate.create()
        sample = df["date_key"].iloc[0]
        assert isinstance(sample, int)
        assert len(str(sample)) == 8

    def test_date_key_is_ascending(self):
        df = DimDate.create()
        assert df["date_key"].is_monotonic_increasing

    def test_no_duplicate_dates(self):
        df = DimDate.create()
        assert df["date_key"].is_unique

    def test_quarter_values(self):
        df = DimDate.create()
        assert df["quarter"].isin([1, 2, 3, 4]).all()

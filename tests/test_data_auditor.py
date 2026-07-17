import logging
import pandas as pd
import pytest

from src.transform.quality.data_auditor import DataAuditor


@pytest.fixture
def auditor():
    return DataAuditor()


def test_audit_basic_info(auditor):
    df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    result = auditor.audit_dataframe(df, "Test")
    assert result["basic_info"]["row_count"] == 2
    assert result["basic_info"]["column_count"] == 2


def test_audit_nulls_found(auditor, caplog):
    caplog.set_level(logging.WARNING)
    df = pd.DataFrame({"a": [1, None, 3]})
    auditor.audit_dataframe(df, "Test")
    assert "Columns with null values" in caplog.text
    assert "nulls" in caplog.text


def test_audit_no_nulls(auditor, caplog):
    caplog.set_level(logging.INFO)
    df = pd.DataFrame({"a": [1, 2, 3]})
    auditor.audit_dataframe(df, "Test")
    assert "No null values found" in caplog.text


def test_audit_duplicates_found(auditor, caplog):
    caplog.set_level(logging.WARNING)
    df = pd.DataFrame({"a": [1, 1, 2], "b": [3, 3, 4]})
    auditor.audit_dataframe(df, "Test")
    assert "duplicate rows" in caplog.text


def test_audit_no_duplicates(auditor, caplog):
    caplog.set_level(logging.INFO)
    df = pd.DataFrame({"a": [1, 2, 3]})
    auditor.audit_dataframe(df, "Test")
    assert "No duplicate rows found" in caplog.text


def test_audit_numeric_stats(auditor):
    df = pd.DataFrame({"val": [1.0, 2.0, 3.0, 0.0, -1.0]})
    result = auditor.audit_dataframe(df, "Test")
    stats = result["numeric_statistics"]["val"]
    assert stats["min"] == -1.0
    assert stats["max"] == 3.0
    assert stats["zeros_count"] == 1
    assert stats["negative_count"] == 1


def test_audit_no_numeric(auditor):
    df = pd.DataFrame({"cat": ["x", "y", "z"]})
    result = auditor.audit_dataframe(df, "Test")
    assert result["numeric_statistics"] == {}


def test_audit_categorical(auditor):
    df = pd.DataFrame({"cat": ["a", "b", "a", "c", "b", "a"]})
    result = auditor.audit_dataframe(df, "Test")
    cat = result["categorical_analysis"]["cat"]
    assert cat["unique_count"] == 3
    assert cat["top_values"]["a"] == 3


def test_audit_data_types(auditor):
    df = pd.DataFrame({"num": [1, 2], "txt": ["x", "y"]})
    result = auditor.audit_dataframe(df, "Test")
    dtypes = result["data_types"]
    assert dtypes["num"]["dtype"] == "int64"
    assert dtypes["txt"]["dtype"] == "str"


def test_audit_empty_dataframe(auditor, caplog):
    caplog.set_level(logging.INFO)
    df = pd.DataFrame()
    result = auditor.audit_dataframe(df, "Empty")
    assert result["basic_info"]["row_count"] == 0


def test_audit_aqi_insights_present(auditor, caplog):
    caplog.set_level(logging.INFO)
    df = pd.DataFrame({
        "aqi": [1, 2, 3, 4, 5, 1],
        "pm2_5": [10.0, 20.0, 30.0, 40.0, 50.0, 15.0],
        "co": [100.0, 200.0, 300.0, 400.0, 500.0, 150.0],
    })
    result = auditor.audit_dataframe(df, "AQI Data")
    assert "aqi_insights" in result
    assert "aqi_distribution" in result["aqi_insights"]
    assert result["aqi_insights"]["aqi_distribution"][1] == 2
    assert "pm2_5" in result["aqi_insights"]
    assert "co" in result["aqi_insights"]


def test_audit_aqi_no_aqi_column(auditor):
    df = pd.DataFrame({"temp": [1, 2, 3]})
    result = auditor.audit_dataframe(df, "No AQI")
    assert "aqi_insights" not in result

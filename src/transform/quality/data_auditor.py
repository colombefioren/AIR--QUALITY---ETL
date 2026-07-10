import logging
import pandas as pd
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)


class DataAuditor:

    def __init__(self):
        logger.debug("DataAuditor initialized")

    def audit_dataframe(self, df, df_name="DataFrame"):
        logger.info(f"--- Audit: {df_name} ---")

        audit_results = {
            "name": df_name,
            "timestamp": datetime.now().isoformat(),
            "basic_info": self._audit_basic_info(df),
            "null_analysis": self._audit_nulls(df),
            "duplicate_analysis": self._audit_duplicates(df),
            "data_types": self._audit_data_types(df),
            "numeric_statistics": self._audit_numeric_stats(df),
            "categorical_analysis": self._audit_categorical(df),
        }

        self._log_audit_results(audit_results)
        return audit_results

    def _audit_basic_info(self, df):
        info = {
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": list(df.columns),
        }

        logger.info(f"Shape: {df.shape}")
        return info

    def _audit_nulls(self, df):
        null_counts = df.isnull().sum()
        null_percentages = (null_counts / len(df)) * 100

        null_info = pd.DataFrame({
            "column": null_counts.index,
            "null_count": null_counts.values,
            "null_percentage": null_percentages.values,
        })

        columns_with_nulls = null_info[null_info["null_count"] > 0]

        if not columns_with_nulls.empty:
            logger.warning("Columns with null values:")
            for _, row in columns_with_nulls.iterrows():
                logger.warning(
                    f"  {row['column']}: {row['null_count']} nulls "
                    f"({row['null_percentage']:.2f}%)"
                )
        else:
            logger.info("No null values found")

        return {
            "total_nulls": int(null_counts.sum()),
            "columns_with_nulls": columns_with_nulls.to_dict("records"),
        }

    def _audit_duplicates(self, df):
        duplicate_mask = df.duplicated()
        duplicate_count = duplicate_mask.sum()

        if duplicate_count > 0:
            logger.warning(
                f"Found {duplicate_count} duplicate rows "
                f"({(duplicate_count/len(df))*100:.2f}%)"
            )
        else:
            logger.info("No duplicate rows found")

        return {
            "duplicate_count": int(duplicate_count),
            "duplicate_percentage": ((duplicate_count / len(df)) * 100) if len(df) > 0 else 0.0,
        }

    def _audit_data_types(self, df):
        type_info = {}

        for column in df.columns:
            dtype = str(df[column].dtype)
            unique_count = df[column].nunique()
            type_info[column] = {"dtype": dtype, "unique_values": unique_count}
            logger.debug(f"  {column}: {dtype} ({unique_count} unique values)")

        return type_info

    def _audit_numeric_stats(self, df):
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        if len(numeric_cols) == 0:
            logger.info("No numeric columns found")
            return {}

        stats = {}

        for col in numeric_cols:
            col_stats = {
                "min": float(df[col].min()) if not df[col].isnull().all() else None,
                "max": float(df[col].max()) if not df[col].isnull().all() else None,
                "mean": float(df[col].mean()) if not df[col].isnull().all() else None,
                "std": float(df[col].std()) if not df[col].isnull().all() else None,
                "zeros_count": int((df[col] == 0).sum()),
                "negative_count": int((df[col] < 0).sum()),
            }
            stats[col] = col_stats

            def fmt(v): return f"{v:.2f}" if v is not None else "N/A"
            logger.debug(
                f"  {col}: mean={fmt(col_stats['mean'])}, "
                f"min={fmt(col_stats['min'])}, max={fmt(col_stats['max'])}"
            )

        return stats

    def _audit_categorical(self, df):
        categorical_cols = df.select_dtypes(include=["object", "str"]).columns

        if len(categorical_cols) == 0:
            return {}

        cat_analysis = {}

        for col in categorical_cols:
            value_counts = df[col].value_counts().head(10)
            cat_analysis[col] = {
                "unique_count": int(df[col].nunique()),
                "top_values": value_counts.to_dict(),
            }
            logger.debug(f"  {col}: {len(value_counts)} unique values")
            for val, count in value_counts.items():
                logger.debug(f"    {val}: {count}")

        return cat_analysis

    def _log_audit_results(self, audit_results):
        logger.info(f"Rows: {audit_results['basic_info']['row_count']} | "
                    f"Cols: {audit_results['basic_info']['column_count']} | "
                    f"Nulls: {audit_results['null_analysis']['total_nulls']} | "
                    f"Duplicates: {audit_results['duplicate_analysis']['duplicate_count']}")



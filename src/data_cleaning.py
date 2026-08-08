"""
data_cleaning.py
================
Pandas-based data cleaning and transformation module for the Audit Analytics
Dashboard project.

Responsibilities:
- Load raw transaction and vendor approval limit data
- Standardise data types (dates, times, currencies)
- Handle missing / null values
- Normalise string fields (vendor names, currency codes)
- Derive features required by downstream audit checks
- Produce a data quality summary
"""

from __future__ import annotations

import pandas as pd
import numpy as np
from pathlib import Path

# Business hours used for the out-of-hours audit check
BUSINESS_START_HOUR = 9  # 09:00
BUSINESS_END_HOUR = 18   # 18:00
BUSINESS_DAYS = [0, 1, 2, 3, 4]  # Monday - Friday


def load_transactions(path: str | Path) -> pd.DataFrame:
    """Load raw transaction data from CSV."""
    df = pd.read_csv(path)
    required = [
        "transaction_id", "transaction_date", "transaction_time",
        "vendor_id", "vendor_name", "amount", "currency",
        "invoice_number", "payment_method", "status",
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    return df


def load_vendor_limits(path: str | Path) -> pd.DataFrame:
    """Load vendor approval limit reference data from CSV."""
    df = pd.read_csv(path)
    required = ["vendor_id", "vendor_name", "currency", "approval_limit"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    return df


def _normalise_strings(df: pd.DataFrame) -> pd.DataFrame:
    """Strip whitespace and standardise string casing."""
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].astype(str).str.strip()
    return df


def _parse_dates_times(df: pd.DataFrame) -> pd.DataFrame:
    """Convert date and time columns to datetime/datetime.time types."""
    df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce")
    df["transaction_time"] = pd.to_datetime(
        df["transaction_time"], format="%H:%M:%S", errors="coerce"
    ).dt.time
    return df


def _parse_numeric(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce amount to numeric and handle currency."""
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df["currency"] = df["currency"].str.upper()
    return df


def _flag_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """Derive a data-quality indicator for key fields."""
    df["is_missing_invoice"] = (
        df["invoice_number"].isna()
        | df["invoice_number"].astype(str).str.strip().isin(["", "nan", "None"])
    )
    df["is_missing_amount"] = df["amount"].isna()
    df["is_missing_date"] = df["transaction_date"].isna()
    return df


def _derive_features(df: pd.DataFrame) -> pd.DataFrame:
    """Derive features needed by the audit checks."""
    # Hour of day (0-23) for out-of-hours detection
    df["hour_of_day"] = df["transaction_time"].apply(
        lambda t: t.hour if pd.notna(t) else np.nan
    )
    # Day of week: 0=Monday ... 6=Sunday
    df["day_of_week"] = df["transaction_date"].dt.dayofweek
    # Combined datetime for sorting / duplicate detection windows
    df["combined_datetime"] = pd.to_datetime(
        df["transaction_date"].astype(str) + " " + df["transaction_time"].astype(str),
        errors="coerce",
    )
    return df


def clean_transactions(raw_path: str | Path) -> pd.DataFrame:
    """
    Full cleaning pipeline for transaction data.

    Returns a cleaned DataFrame with derived columns and a subset of
    diagnostic columns retained for the audit checks.
    """
    df = load_transactions(raw_path)
    df = _normalise_strings(df)
    df = _parse_dates_times(df)
    df = _parse_numeric(df)
    df = _flag_missing_values(df)
    df = _derive_features(df)
    return df


def produce_data_quality_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Produce a simple data-quality summary table counting missing values
    per critical field.
    """
    fields = ["invoice_number", "amount", "transaction_date", "transaction_time"]
    rows = []
    total = len(df)
    for field in fields:
        missing = df[field].isna().sum()
        rows.append(
            {
                "field": field,
                "total_records": total,
                "missing_count": int(missing),
                "missing_pct": round(missing / total * 100, 2) if total else 0.0,
            }
        )
    return pd.DataFrame(rows)


def merge_with_vendor_limits(
    transactions: pd.DataFrame, vendor_limits: pd.DataFrame
) -> pd.DataFrame:
    """Left-join transactions to vendor approval limits on vendor_id."""
    return transactions.merge(
        vendor_limits[["vendor_id", "approval_limit"]],
        on="vendor_id",
        how="left",
        suffixes=("", "_vendor"),
    )

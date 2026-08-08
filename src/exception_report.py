"""
exception_report.py
====================
Consolidates flagged records from all audit checks into a single master
exception register, assigns severity levels, and generates summary outputs
suitable for import into Power BI and for reporting.
"""

from __future__ import annotations

import pandas as pd
from pathlib import Path

# Base columns that describe a transaction
BASE_COLUMNS = [
    "transaction_id",
    "transaction_date",
    "transaction_time",
    "vendor_id",
    "vendor_name",
    "amount",
    "currency",
    "invoice_number",
    "payment_method",
    "status",
]

# Severity mapping per exception type
SEVERITY_MAP = {
    "Duplicate Payment": "High",
    "Missing Invoice Number": "Medium",
    "Exceeds Approval Limit": "High",
    "Out-of-Hours Transaction": "Low",
}


def assign_severity(result: pd.DataFrame) -> pd.DataFrame:
    """Attach a severity level to each exception record."""
    result = result.copy()
    result["severity"] = result["exception_type"].map(SEVERITY_MAP).fillna("Medium")
    return result


def build_master_exception_register(
    check_results: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """
    Combine per-check exception DataFrames into one master register.

    Includes a unique exception_id and the list of checks that flagged it.
    """
    frames = []
    for check_name, df in check_results.items():
        if df is None or df.empty:
            continue
        frame = df.copy()
        frame["detected_by"] = check_name
        frames.append(frame)

    if not frames:
        return pd.DataFrame(columns=BASE_COLUMNS + ["exception_id", "exception_type", "reason", "severity", "detected_by"])

    master = pd.concat(frames, ignore_index=True, sort=False)
    master = assign_severity(master)

    # Preserve descriptive column order
    cols = BASE_COLUMNS + ["exception_type", "reason", "severity", "detected_by"]
    master = master[[c for c in cols if c in master.columns]]

    # Unique exception id
    master.insert(0, "exception_id", range(1, len(master) + 1))
    return master


def summarise_by_type(master: pd.DataFrame) -> pd.DataFrame:
    """Aggregate exception counts by exception type and severity."""
    if master.empty:
        return pd.DataFrame(columns=["exception_type", "count", "severity"])
    return (
        master.groupby(["exception_type", "severity"], dropna=False)
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
    )


def summarise_by_vendor(master: pd.DataFrame) -> pd.DataFrame:
    """Aggregate exception counts by vendor."""
    if master.empty:
        return pd.DataFrame(columns=["vendor_id", "vendor_name", "count"])
    return (
        master.groupby(["vendor_id", "vendor_name"], dropna=False)
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
    )


def export_exception_register(master: pd.DataFrame, out_dir: str | Path) -> Path:
    """Save the master exception register to CSV."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "exceptions_master.csv"
    master.to_csv(path, index=False)
    return path


def export_summaries(
    by_type: pd.DataFrame,
    by_vendor: pd.DataFrame,
    data_quality: pd.DataFrame,
    out_dir: str | Path,
):
    """Export summary tables to CSV for Power BI consumption."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    by_type.to_csv(out_dir / "summary_by_type.csv", index=False)
    by_vendor.to_csv(out_dir / "summary_by_vendor.csv", index=False)
    data_quality.to_csv(out_dir / "data_quality_summary.csv", index=False)
    return out_dir

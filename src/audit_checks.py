"""
audit_checks.py
===============
Core analytical checks engine for the Audit Analytics Dashboard.

Implements four automated exception-detection checks:
1. Duplicate payments
2. Missing invoice numbers
3. Transactions outside business hours
4. Payments exceeding vendor approval limits

Each check returns a DataFrame of flagged records with a reason column,
designed to be merged into a master exception register.
"""

from __future__ import annotations

import pandas as pd
import numpy as np

from data_cleaning import BUSINESS_DAYS, BUSINESS_START_HOUR, BUSINESS_END_HOUR

# Columns common to every exception record
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


def _base_view(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with only the base descriptive columns."""
    return df[BASE_COLUMNS].copy()


def check_duplicate_payments(
    df: pd.DataFrame,
    dup_window_days: int = 7,
) -> pd.DataFrame:
    """
    Flag records that look like duplicate payments.

    A duplicate is defined as records sharing the same vendor, amount,
    currency and invoice number within a rolling date window.
    """
    work = _base_view(df)
    work["transaction_date"] = pd.to_datetime(df["transaction_date"])

    # Normalise invoice number for grouping (NaN -> 'NO_INVOICE')
    work["_inv_key"] = work["invoice_number"].fillna("NO_INVOICE").str.strip()

    # Group key: vendor + amount + currency + invoice
    group_key = ["vendor_id", "amount", "currency", "_inv_key"]

    # Sort by date to compute windows
    work = work.sort_values("transaction_date").reset_index(drop=True)

    flagged_idx: list[int] = []
    for _, group in work.groupby(group_key, dropna=False):
        if len(group) < 2:
            continue
        # Sort dates within the group and compute day-gap between consecutive rows
        g = group.sort_values("transaction_date")
        day_gap = g["transaction_date"].diff().dt.days
        # A new cluster starts where the gap exceeds the window
        new_cluster = day_gap.fillna(0).gt(dup_window_days)
        cluster_id = new_cluster.cumsum()
        g = g.assign(_cluster=cluster_id)
        for _, cg in g.groupby("_cluster"):
            if len(cg) >= 2:
                flagged_idx.extend(cg.index.tolist())

    result = work.loc[work.index.isin(flagged_idx)].copy()
    result["exception_type"] = "Duplicate Payment"
    result["reason"] = (
        "Multiple payments with identical vendor, amount, currency and invoice "
        f"within {dup_window_days} days"
    )
    return result.drop(columns=["_inv_key"])


def check_missing_invoice_numbers(df: pd.DataFrame) -> pd.DataFrame:
    """Flag records with missing or blank invoice numbers."""
    work = _base_view(df)
    work["is_missing_invoice"] = df["is_missing_invoice"]
    flagged = work[work["is_missing_invoice"]].copy()
    flagged["exception_type"] = "Missing Invoice Number"
    flagged["reason"] = "Invoice number is missing or blank"
    return flagged.drop(columns=["is_missing_invoice"])


def check_out_of_hours_transactions(
    df: pd.DataFrame,
    start_hour: int = BUSINESS_START_HOUR,
    end_hour: int = BUSINESS_END_HOUR,
    business_days: list[int] | None = None,
) -> pd.DataFrame:
    """
    Flag transactions outside business hours (default 09:00-18:00 Mon-Fri).
    """
    business_days = business_days if business_days is not None else BUSINESS_DAYS
    work = _base_view(df)
    work["hour_of_day"] = df["hour_of_day"]
    work["day_of_week"] = df["day_of_week"]

    is_outside_hours = (
        work["hour_of_day"].isna()
        | (work["hour_of_day"] < start_hour)
        | (work["hour_of_day"] >= end_hour)
    )
    is_weekend = ~work["day_of_week"].isin(business_days)

    flagged = work[is_outside_hours | is_weekend].copy()
    flagged["exception_type"] = "Out-of-Hours Transaction"
    flagged["reason"] = flagged.apply(
        lambda r: (
            "Transaction on a non-business day"
            if not r["day_of_week"] in business_days
            else f"Transaction outside business hours ({start_hour:02d}:00-{end_hour:02d}:00)"
        ),
        axis=1,
    )
    return flagged.drop(columns=["hour_of_day", "day_of_week"])


def check_exceeding_approval_limits(df: pd.DataFrame) -> pd.DataFrame:
    """
    Flag payments whose amount exceeds the vendor's configured approval limit.

    Requires the merged 'approval_limit' column (see data_cleaning.merge_with_vendor_limits).
    """
    if "approval_limit" not in df.columns:
        raise ValueError(
            "approval_limit column missing. Merge vendor limits first "
            "using data_cleaning.merge_with_vendor_limits()."
        )
    work = _base_view(df)
    work["approval_limit"] = df["approval_limit"]

    has_limit = work["approval_limit"].notna()
    exceeds = work["amount"] > work["approval_limit"]

    flagged = work[has_limit & exceeds].copy()
    flagged["exception_type"] = "Exceeds Approval Limit"
    flagged["reason"] = flagged.apply(
        lambda r: (
            f"Payment amount {r['amount']:,.2f} exceeds approval limit "
            f"{r['approval_limit']:,.2f}"
        ),
        axis=1,
    )
    return flagged.drop(columns=["approval_limit"])


def run_all_checks(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """
    Run all four audit checks against a cleaned (and vendor-merged)
    transaction DataFrame.

    Returns a dictionary keyed by check name.
    """
    return {
        "duplicate_payments": check_duplicate_payments(df),
        "missing_invoice_numbers": check_missing_invoice_numbers(df),
        "out_of_hours": check_out_of_hours_transactions(df),
        "exceeds_approval_limit": check_exceeding_approval_limits(df),
    }

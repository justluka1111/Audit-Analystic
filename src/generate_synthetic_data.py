"""
generate_synthetic_data.py
==========================
Generates a large synthetic financial transaction dataset for the Audit
Analytics Dashboard project.

Why synthetic?
--------------
This portfolio project does not use real corporate financial data. The
dataset is generated programmatically to be realistic in structure while
deliberately seeding known anomalies (duplicate payments, missing invoice
numbers, out-of-hours transactions, and approval-limit breaches) so the
audit checks can be validated.

Output schema matches `data/raw_transactions.csv` so the same pipeline can
be re-run at scale (e.g. 100,000 rows).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DEFAULT_N_TRANSACTIONS = 100_000
BUSINESS_START_HOUR = 9
BUSINESS_END_HOUR = 18

# Vendor base data (mirrors data/vendor_approval_limits.csv)
VENDORS = [
    {"vendor_id": "V001", "vendor_name": "Acme Supplies Ltd", "approval_limit": 5000},
    {"vendor_id": "V002", "vendor_name": "Globex Corporation", "approval_limit": 10000},
    {"vendor_id": "V003", "vendor_name": "Initech Solutions", "approval_limit": 7500},
    {"vendor_id": "V004", "vendor_name": "Umbrella Services", "approval_limit": 2500},
    {"vendor_id": "V005", "vendor_name": "Hooli Enterprises", "approval_limit": 15000},
    {"vendor_id": "V006", "vendor_name": "Stark Industries", "approval_limit": 20000},
    {"vendor_id": "V007", "vendor_name": "Wayne Enterprises", "approval_limit": 12000},
    {"vendor_id": "V008", "vendor_name": "Cyberdyne Systems", "approval_limit": 8000},
    {"vendor_id": "V009", "vendor_name": "Tyrell Corporation", "approval_limit": 6000},
    {"vendor_id": "V010", "vendor_name": "Skynet Logistics", "approval_limit": 3000},
]

PAYMENT_METHODS = ["BACS", "Cheque", "Card", "Bank Transfer", "Direct Debit"]
STATUSES = ["posted", "pending", "posted", "posted", "posted"]  # mostly posted


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _random_vendors(rng: np.random.Generator, n: int) -> pd.DataFrame:
    """Randomly assign vendors to transactions."""
    idx = rng.integers(0, len(VENDORS), size=n)
    return pd.DataFrame([VENDORS[i] for i in idx])


def _random_amounts(rng: np.random.Generator, n: int) -> np.ndarray:
    """Log-normal amounts typical of invoice values (mean ~3-4k)."""
    amounts = np.round(
        rng.lognormal(mean=7.8, sigma=0.9, size=n), 2
    )
    return np.clip(amounts, 50.0, 95000.0)


def _random_business_datetime(rng: np.random.Generator, n: int):
    """
    Generate business-hours datetimes (Mon-Fri 09:00-18:00) over a 12-month
window ending 'today'.
    """
    end = pd.Timestamp("2024-12-31")
    start = pd.Timestamp("2024-01-01")
    total_days = (end - start).days

    dates = []
    while len(dates) < n:
        # Pick a random day offset
        day_delta = rng.integers(0, total_days, size=n)
        base = start + pd.to_timedelta(day_delta, unit="D")
        # Keep only Mon-Fri (weekday < 5)
        weekday = base.weekday
        mask = weekday < 5
        base = base[mask]
        # Random hour, minute, second within business hours
        hour = rng.integers(BUSINESS_START_HOUR, BUSINESS_END_HOUR, size=len(base))
        minute = rng.integers(0, 60, size=len(base))
        second = rng.integers(0, 60, size=len(base))
        timepart = pd.to_timedelta(hour, unit="h") + pd.to_timedelta(minute, unit="m") + pd.to_timedelta(second, unit="s")
        dt = pd.DatetimeIndex(base).normalize() + timepart
        dates.extend(dt)
        if len(dates) >= n:
            dates = dates[:n]
    return dates


def _generate_invoices(rng: np.random.Generator, n: int) -> list[str]:
    """Generate invoice numbers; ~2.5% left blank to seed missing-invoice anomaly."""
    invoices = [f"INV-2024-{i:06d}" for i in range(1, n + 1)]
    # Randomly blank a small percentage
    blank_mask = rng.random(n) < 0.025
    for i, is_blank in enumerate(blank_mask):
        if is_blank:
            invoices[i] = ""
    return invoices


def generate_synthetic_transactions(
    n: int = DEFAULT_N_TRANSACTIONS,
    seed: int = 42,
    anomaly_rate: float = 0.03,
) -> pd.DataFrame:
    """
    Generate `n` synthetic transactions with seeded anomalies.

    Anomalies are seeded such that the four audit checks will each find
    records. The remainder are clean, in-business-hours transactions.
    """
    rng = np.random.default_rng(seed)

    vendors = _random_vendors(rng, n)
    amounts = _random_amounts(rng, n)
    invoices = _generate_invoices(rng, n)
    methods = rng.choice(PAYMENT_METHODS, size=n)
    statuses = rng.choice(STATUSES, size=n)

# Business datetimes (then we'll corrupt some afterwards for anomalies)
    dts = _random_business_datetime(rng, n)
    dates = pd.Series(pd.to_datetime([d.date() for d in dts])).dt.normalize()
    times = pd.Series(pd.to_datetime([str(d.time()) for d in dts], format="%H:%M:%S")).dt.time

    df = pd.DataFrame({
        "transaction_id": [f"T{i:06d}" for i in range(1, n + 1)],
        "transaction_date": dates,
        "transaction_time": times,
        "vendor_id": vendors["vendor_id"],
        "vendor_name": vendors["vendor_name"],
        "amount": amounts,
        "currency": "GBP",
        "invoice_number": invoices,
        "payment_method": methods,
        "status": statuses,
    })

    # ------------------------------------------------------------------
    # Seed anomalies: modify a subset of rows
    # ------------------------------------------------------------------
    n_dup = int(n * anomaly_rate * 0.25)
    n_missing = int(n * anomaly_rate * 0.20)
    n_ooh = int(n * anomaly_rate * 0.25)
    n_over = int(n * anomaly_rate * 0.30)

    # 1) Duplicate payments: duplicate a small set of rows
    dup_indices = rng.choice(n, size=n_dup, replace=False)
    dup_rows = df.iloc[dup_indices].copy()
    dup_rows["transaction_id"] = [f"T{i:06d}" for i in range(n + 1, n + n_dup + 1)]
    df = pd.concat([df, dup_rows], ignore_index=True).sort_values("transaction_id").reset_index(drop=True)

    # 2) Missing invoice numbers
    missing_idx = rng.choice(len(df), size=n_missing, replace=False)
    df.loc[missing_idx, "invoice_number"] = ""

    # 3) Out-of-hours: push time to evening or weekend
    ooh_idx = rng.choice(len(df), size=n_ooh, replace=False)
    for i in ooh_idx:
        if rng.random() < 0.5:
            # weekend
            d = df.at[i, "transaction_date"]
            while d.weekday() < 5:
                d = d + pd.Timedelta(days=1)
            df.at[i, "transaction_date"] = d
        else:
            # late evening
            df.at[i, "transaction_time"] = pd.to_datetime("22:35:00").time()

    # 4) Exceeds approval limit: bump amount above vendor limit
    over_idx = rng.choice(len(df), size=n_over, replace=False)
    for i in over_idx:
        vid = df.at[i, "vendor_id"]
        limit = next(v["approval_limit"] for v in VENDORS if v["vendor_id"] == vid)
        df.at[i, "amount"] = round(limit * rng.uniform(1.05, 2.0), 2)

    return df


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Generate synthetic transaction data.")
    parser.add_argument("--n", type=int, default=DEFAULT_N_TRANSACTIONS,
                        help=f"Number of transactions (default {DEFAULT_N_TRANSACTIONS:,})")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--out", type=str, default=None, help="Output path")
    args = parser.parse_args()

    out_path = Path(args.out) if args.out else Path(__file__).resolve().parent.parent / "data" / "synthetic_transactions.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Generating {args.n:,} synthetic transactions...")
    df = generate_synthetic_transactions(n=args.n, seed=args.seed)
    df.to_csv(out_path, index=False)
    print(f"Saved to: {out_path}")
    print(f"Rows: {len(df):,}")


if __name__ == "__main__":
    main()

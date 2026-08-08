"""
run_analysis.py
===============
Main orchestrator for the Audit Analytics Dashboard pipeline.

Runs the full ETL + audit-check flow:
1. Load and clean transaction data
2. Load vendor approval limits and merge
3. Run all four audit checks
4. Build the master exception register
5. Export outputs (CSV) for Power BI
6. Print a console summary
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running as a script from the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
# Allow imports of sibling modules in src/
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import pandas as pd  # noqa: E402

from data_cleaning import (  # noqa: E402
    clean_transactions,
    load_vendor_limits,
    merge_with_vendor_limits,
    produce_data_quality_summary,
)
from audit_checks import run_all_checks  # noqa: E402
from exception_report import (  # noqa: E402
    build_master_exception_register,
    summarise_by_type,
    summarise_by_vendor,
    export_exception_register,
    export_summaries,
)


def main() -> None:
    data_dir = PROJECT_ROOT / "data"
    output_dir = PROJECT_ROOT / "output"

    print("=" * 60)
    print("AUDIT ANALYTICS DASHBOARD - ANALYSIS PIPELINE")
    print("=" * 60)

    # 1. Load + clean
    raw_path = data_dir / "raw_transactions.csv"
    print(f"\n[1/5] Loading & cleaning transactions: {raw_path.name}")
    transactions = clean_transactions(raw_path)
    print(f"      Loaded {len(transactions)} transactions")

    # 2. Vendor limits
    limits_path = data_dir / "vendor_approval_limits.csv"
    print(f"[2/5] Loading vendor approval limits: {limits_path.name}")
    vendor_limits = load_vendor_limits(limits_path)
    merged = merge_with_vendor_limits(transactions, vendor_limits)
    print(f"      Loaded {len(vendor_limits)} vendors")

    # 3. Run audit checks
    print("[3/5] Running four audit checks...")
    check_results = run_all_checks(merged)
    for name, frame in check_results.items():
        print(f"      {name:<28}: {len(frame)} exception(s)")

    # 4. Master register + summaries
    print("[4/5] Building master exception register")
    master = build_master_exception_register(check_results)
    by_type = summarise_by_type(master)
    by_vendor = summarise_by_vendor(master)
    data_quality = produce_data_quality_summary(transactions)

    # 5. Export
    print(f"[5/5] Exporting outputs to: {output_dir}")
    export_exception_register(master, output_dir)
    export_summaries(by_type, by_vendor, data_quality, output_dir)
    print("      -> exceptions_master.csv")
    print("      -> summary_by_type.csv")
    print("      -> summary_by_vendor.csv")
    print("      -> data_quality_summary.csv")

    # Console summary
    print("\n" + "=" * 60)
    print("EXCEPTION SUMMARY BY TYPE")
    print("=" * 60)
    if by_type.empty:
        print("No exceptions detected.")
    else:
        print(by_type.to_string(index=False))

    print("\n" + "=" * 60)
    print("DATA QUALITY SUMMARY")
    print("=" * 60)
    print(data_quality.to_string(index=False))

    print("\nPipeline complete. Use outputs in Power BI.")


if __name__ == "__main__":
    main()

# Audit Analytics Dashboard — Portfolio Project

> **Python | SQL | Pandas | Power BI**

A data analytics dashboard designed to identify potential anomalies, policy
breaches and unusual transaction patterns within business datasets. The project
implements automated analytical checks for **duplicate payments**, **missing
invoice numbers**, **transactions outside business hours** and **payments
exceeding approval limits**.

---

## Overview

This portfolio project demonstrates a complete end-to-end audit-analytics
workflow:

1. **Ingest** raw transaction data (CSV) and vendor reference data.
2. **Clean & transform** with Pandas (dates, times, currency, nulls, string
   normalisation).
3. **Run automated audit checks** to flag exceptions.
4. **Consolidate** flagged records into a master exception register with severity.
5. **Export** CSV outputs for Power BI visualisation.
6. **Validate** with SQL data-quality checks and exception-detection queries.

The solution helps business users identify exceptions more efficiently and
supports evidence-based decision-making through structured data validation and
exception-based reporting.

---

## Project Structure

```
Audit Analystic/
├── data/
│   ├── raw_transactions.csv          # Sample transaction data (with seeded anomalies)
│   └── vendor_approval_limits.csv    # Vendor approval limit reference data
├── sql/
│   ├── create_tables.sql             # Staging schema (SQL Server / Azure SQL)
│   ├── data_validation.sql           # Data-quality & integrity checks
│   └── audit_exceptions.sql          # SQL versions of the four audit checks
├── src/
│   ├── data_cleaning.py              # Pandas cleaning & transformation
│   ├── audit_checks.py               # Four analytical checks engine
│   ├── exception_report.py           # Master register + summary exporters
│   └── run_analysis.py               # Main orchestrator pipeline
├── output/                           # Generated after running the pipeline
│   ├── exceptions_master.csv
│   ├── summary_by_type.csv
│   ├── summary_by_vendor.csv
│   └── data_quality_summary.csv
├── powerbi/
│   └── audit_dashboard_notes.md      # Power BI setup, data model & DAX
├── requirements.txt
└── README.md
```

---

## The Four Audit Checks

| #   | Check                         | Definition                                                      | Severity |
| --- | ----------------------------- | --------------------------------------------------------------- | -------- |
| 1   | **Duplicate Payments**        | Same vendor + amount + currency + invoice within a 7-day window | High     |
| 2   | **Missing Invoice Numbers**   | Invoice number is NULL or blank                                 | Medium   |
| 3   | **Out-of-Hours Transactions** | Outside 09:00–18:00 Mon–Fri (incl. weekends)                    | Low      |
| 4   | **Exceeds Approval Limit**    | Payment amount > vendor's configured approval limit             | High     |

---

## Getting Started

### Prerequisites

- Python 3.9+
- `pip`

### Installation

```bash
# From the project root
pip install -r requirements.txt
```

### Run the Analysis Pipeline

```bash
python src/run_analysis.py
```

This will:

- Load and clean the sample data
- Run all four audit checks
- Print an exception summary to the console
- Write CSV outputs to the `output/` folder

### Example Console Output

```
AUDIT ANALYTICS DASHBOARD - ANALYSIS PIPELINE
[1/5] Loading & cleaning transactions: raw_transactions.csv
      Loaded 30 transactions
[2/5] Loading vendor approval limits: vendor_approval_limits.csv
      Loaded 10 vendors
[3/5] Running four audit checks...
      duplicate_payments          : N exception(s)
      missing_invoice_numbers     : N exception(s)
      out_of_hours                : N exception(s)
      exceeds_approval_limit      : N exception(s)
...
```

---

## SQL Usage

The SQL scripts target **SQL Server / Azure SQL** but can be adapted to other
dialects.

```sql
-- 1. Create staging tables
:r sql/create_tables.sql

-- 2. Run data-quality validation (returns failure counts)
:r sql/data_validation.sql

-- 3. Run exception-detection queries (returns flagged records)
:r sql/audit_exceptions.sql
```

---

## Power BI Dashboard

Follow **`powerbi/audit_dashboard_notes.md`** for:

- Connecting to the CSV outputs or SQL stage
- Building the star-schema data model
- Creating DAX measures (Total Exceptions, High Severity %, etc.)
- Suggested visualisations (KPI cards, bar/donut/line charts, slicers)
- Refresh & automation guidance

---

## Extension Ideas

- Add more audit checks (e.g., split VAT amounts, late invoice capture, vendor
  name mismatches).
- Connect to a real database (Postgres/MySQL) via SQLAlchemy.
- Add a risk-scoring model weighting severity × frequency × amount.
- Automate refresh with a scheduler (e.g., cron / Task Scheduler + Power BI
  Service gateway).

---

## Files Reference

| File                      | Purpose                                             |
| ------------------------- | --------------------------------------------------- |
| `src/data_cleaning.py`    | Standardise types, handle nulls, derive features    |
| `src/audit_checks.py`     | Modular implementations of the four checks          |
| `src/exception_report.py` | Merge flags, assign severity, export summaries      |
| `src/run_analysis.py`     | End-to-end pipeline entry point                     |
| `sql/*.sql`               | Staging DDL, validation and exception SQL           |
| `data/*.csv`              | Sample datasets with intentionally seeded anomalies |

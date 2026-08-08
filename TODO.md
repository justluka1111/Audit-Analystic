# Audit Analytics Dashboard — Project TODO

## Implementation Steps

- [x] 1. Create `requirements.txt` with dependencies
- [x] 2. Create sample raw transaction data (`data/raw_transactions.csv`)
- [x] 3. Create vendor approval limits reference data (`data/vendor_approval_limits.csv`)
- [x] 4. Build `src/data_cleaning.py` — Pandas cleaning & transformation
- [x] 5. Build `src/audit_checks.py` — 4 core analytical checks engine
- [x] 6. Build `src/exception_report.py` — exception report generator
- [x] 7. Build `src/run_analysis.py` — main orchestrator pipeline
- [x] 8. Create SQL scripts (schema, validation, audit exceptions)
- [x] 9. Create Power BI setup & DAX documentation
- [x] 10. Create README.md with project overview & usage
- [x] 11. Run the analysis pipeline to verify output

## Audit Checks Implemented

- [x] Duplicate payments detection
- [x] Missing invoice numbers detection
- [x] Out-of-hours transactions detection
- [x] Payments exceeding approval limits detection

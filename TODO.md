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
- [x] 12. Add `src/generate_synthetic_data.py` for scalable synthetic dataset (100k rows)
- [x] 13. Update `.gitignore` for generated outputs

## Audit Checks Implemented

- [x] Duplicate payments detection
- [x] Missing invoice numbers detection
- [x] Out-of-hours transactions detection
- [x] Payments exceeding approval limits detection

## Verification Results (sample dataset, 30 rows)

- Duplicate payments: 8
- Missing invoice numbers: 3
- Out-of-hours transactions: 9
- Exceeds approval limits: 14

## Verification Results (synthetic dataset, 100,750 rows)

- Duplicate payments: 1,444
- Missing invoice numbers: 2,987
- Out-of-hours transactions: 750
- Exceeds approval limits: 16,870

-- ============================================================================
-- data_validation.sql
-- Audit Analytics Dashboard - data validation queries
-- Runs structured data-quality and referential-integrity checks against the
-- staging tables. Each query returns a row per validation failure.
-- ============================================================================

-- 1) Orphaned transactions (vendor_id not present in vendors reference)
SELECT
    'Orphaned_Vendor' AS validation_check,
    COUNT(*)          AS failure_count
FROM dbo.staging_transactions t
LEFT JOIN dbo.vendors v ON t.vendor_id = v.vendor_id
WHERE v.vendor_id IS NULL;

-- 2) Missing invoice numbers
SELECT
    'Missing_Invoice' AS validation_check,
    COUNT(*)          AS failure_count
FROM dbo.staging_transactions
WHERE invoice_number IS NULL OR LTRIM(RTRIM(invoice_number)) = '';

-- 3) NULL or non-positive amounts
SELECT
    'Invalid_Amount' AS validation_check,
    COUNT(*)         AS failure_count
FROM dbo.staging_transactions
WHERE amount IS NULL OR amount <= 0;

-- 4) Invalid transaction dates (NULL or out of an acceptable range)
SELECT
    'Invalid_Date' AS validation_check,
    COUNT(*)       AS failure_count
FROM dbo.staging_transactions
WHERE transaction_date IS NULL OR transaction_date < '2020-01-01';

-- 5) Currency mismatch between transaction and vendor reference
SELECT
    'Currency_Mismatch' AS validation_check,
    COUNT(*)            AS failure_count
FROM dbo.staging_transactions t
INNER JOIN dbo.vendors v ON t.vendor_id = v.vendor_id
WHERE t.currency <> v.currency;

-- ============================================================================
-- audit_exceptions.sql
-- Audit Analytics Dashboard - exception detection queries (SQL)
-- Mirrors the four analytical checks implemented in Python, expressed in SQL
-- for validation and for use in a SQL-based reporting pipeline.
-- ============================================================================

-- ============================================================================
-- 1) Duplicate Payments
--    Same vendor + amount + currency + invoice within a 7-day window
-- ============================================================================
SELECT
    t.transaction_id,
    t.transaction_date,
    t.vendor_id,
    t.vendor_name,
    t.amount,
    t.currency,
    t.invoice_number,
    'Duplicate Payment' AS exception_type
FROM dbo.staging_transactions t
WHERE EXISTS (
    SELECT 1
    FROM dbo.staging_transactions d
    WHERE d.vendor_id       = t.vendor_id
      AND d.amount          = t.amount
      AND d.currency        = t.currency
      AND ISNULL(d.invoice_number, '') = ISNULL(t.invoice_number, '')
      AND d.transaction_id  <> t.transaction_id
      AND ABS(DATEDIFF(DAY, d.transaction_date, t.transaction_date)) <= 7
)
ORDER BY t.vendor_id, t.transaction_date;

-- ============================================================================
-- 2) Missing Invoice Numbers
-- ============================================================================
SELECT
    transaction_id,
    transaction_date,
    vendor_id,
    vendor_name,
    amount,
    currency,
    invoice_number,
    'Missing Invoice Number' AS exception_type
FROM dbo.staging_transactions
WHERE invoice_number IS NULL OR LTRIM(RTRIM(invoice_number)) = ''
ORDER BY transaction_date;

-- ============================================================================
-- 3) Out-of-Hours Transactions
--    Outside 09:00-18:00 Monday-Friday
-- ============================================================================
SELECT
    transaction_id,
    transaction_date,
    transaction_time,
    vendor_id,
    vendor_name,
    amount,
    currency,
    invoice_number,
    'Out-of-Hours Transaction' AS exception_type,
    CASE
        WHEN DATEPART(WEEKDAY, transaction_date) IN (1, 7) THEN 'Weekend'
        ELSE 'Outside business hours'
    END AS reason
FROM dbo.staging_transactions
WHERE DATEPART(WEEKDAY, transaction_date) IN (1, 7)           -- Sat/Sun
   OR transaction_time < '09:00:00'
   OR transaction_time >= '18:00:00'
ORDER BY transaction_date;

-- ============================================================================
-- 4) Payments Exceeding Approval Limits
-- ============================================================================
SELECT
    t.transaction_id,
    t.transaction_date,
    t.vendor_id,
    t.vendor_name,
    t.amount,
    t.currency,
    t.invoice_number,
    'Exceeds Approval Limit' AS exception_type,
    v.approval_limit,
    t.amount - v.approval_limit AS excess_amount
FROM dbo.staging_transactions t
INNER JOIN dbo.vendors v ON t.vendor_id = v.vendor_id
WHERE t.amount > v.approval_limit
ORDER BY excess_amount DESC;

-- ============================================================================
-- 5) Consolidated Exception Register (UNION of all four checks)
-- ============================================================================
SELECT
    'Duplicate Payment'                      AS exception_type,
    COUNT(*)                                 AS exception_count
FROM dbo.staging_transactions t
WHERE EXISTS (
    SELECT 1 FROM dbo.staging_transactions d
    WHERE d.vendor_id = t.vendor_id AND d.amount = t.amount
      AND d.currency = t.currency
      AND ISNULL(d.invoice_number,'') = ISNULL(t.invoice_number,'')
      AND d.transaction_id <> t.transaction_id
      AND ABS(DATEDIFF(DAY, d.transaction_date, t.transaction_date)) <= 7
)
UNION ALL SELECT 'Missing Invoice Number', COUNT(*)
    FROM dbo.staging_transactions
    WHERE invoice_number IS NULL OR LTRIM(RTRIM(invoice_number)) = ''
UNION ALL SELECT 'Out-of-Hours Transaction', COUNT(*)
    FROM dbo.staging_transactions
    WHERE DATEPART(WEEKDAY, transaction_date) IN (1,7)
       OR transaction_time < '09:00:00' OR transaction_time >= '18:00:00'
UNION ALL SELECT 'Exceeds Approval Limit', COUNT(*)
    FROM dbo.staging_transactions t
    INNER JOIN dbo.vendors v ON t.vendor_id = v.vendor_id
    WHERE t.amount > v.approval_limit;

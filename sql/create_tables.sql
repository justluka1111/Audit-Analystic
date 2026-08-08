-- ============================================================================
-- create_tables.sql
-- Audit Analytics Dashboard - Staging schema for SQL Server / Azure SQL
-- Creates staging tables to hold raw transaction and vendor reference data,
-- enforcing basic data-integrity constraints.
-- ============================================================================

-- Vendor reference table (approval limits)
IF OBJECT_ID('dbo.vendors', 'U') IS NOT NULL DROP TABLE dbo.vendors;
CREATE TABLE dbo.vendors (
    vendor_id       VARCHAR(20)   NOT NULL PRIMARY KEY,
    vendor_name     NVARCHAR(255) NOT NULL,
    currency        CHAR(3)       NOT NULL,
    approval_limit  DECIMAL(18,2) NOT NULL
);

-- Staging transactions table
IF OBJECT_ID('dbo.staging_transactions', 'U') IS NOT NULL DROP TABLE dbo.staging_transactions;
CREATE TABLE dbo.staging_transactions (
    transaction_id   INT           NOT NULL PRIMARY KEY,
    transaction_date DATE          NOT NULL,
    transaction_time TIME(0)       NOT NULL,
    vendor_id        VARCHAR(20)   NOT NULL,
    vendor_name      NVARCHAR(255) NULL,
    amount           DECIMAL(18,2) NOT NULL,
    currency         CHAR(3)       NOT NULL,
    invoice_number   NVARCHAR(50)  NULL,
    payment_method   NVARCHAR(50)  NULL,
    status           NVARCHAR(20)  NULL,
    CONSTRAINT FK_staging_vendor
        FOREIGN KEY (vendor_id) REFERENCES dbo.vendors(vendor_id)
);

-- Optional: index to support duplicate-detection and date-range queries
CREATE INDEX IX_staging_vendor_date
    ON dbo.staging_transactions (vendor_id, transaction_date);

-- =====================================================================================
-- Create the three warehouse layers (run inside database olist_commerce360)
-- Olist Commerce360 | DL3004 Phase 2 | owner: Member 1 (Kashish Fatima)
-- Idempotent: safe to re-run.
-- =====================================================================================

CREATE SCHEMA IF NOT EXISTS project_staging;
COMMENT ON SCHEMA project_staging IS
    'Landing (stg_*, raw TEXT copies of the CSVs), cleaned (cln_*) tables and ETL metadata.';

CREATE SCHEMA IF NOT EXISTS project_dw;
COMMENT ON SCHEMA project_dw IS
    'Star schema: 6 conformed dimensions and 4 fact tables (Phase 1 design).';

CREATE SCHEMA IF NOT EXISTS project_reporting;
COMMENT ON SCHEMA project_reporting IS
    'Reporting views and OLAP queries for Power BI (Phase 3).';

-- =====================================================================================
-- Create the project database
-- Olist Commerce360 | DL3004 Phase 2 | owner: Member 1 (Kashish Fatima)
-- Run while connected to the default 'postgres' database (CREATE DATABASE cannot run
-- inside a transaction). 03_ETL/run_pipeline.py runs this only if the database is missing,
-- so re-running the pipeline never drops existing data in other databases.
-- =====================================================================================

CREATE DATABASE olist_commerce360
    WITH ENCODING 'UTF8'
         TEMPLATE template0;

COMMENT ON DATABASE olist_commerce360 IS
    'Olist Commerce360 - DL3004 data warehouse (schemas project_staging, project_dw, project_reporting).';

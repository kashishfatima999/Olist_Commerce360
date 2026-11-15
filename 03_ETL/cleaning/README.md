# 03_ETL/cleaning (owner: M2, Khadija Faiz)

This folder turns the raw `project_staging.stg_*` tables into typed, cleaned `project_staging.cln_*` tables. The agreed table and column contract is in `01_Project_Documentation/phase2/README.md` §3. The rules are TR-01 to TR-15 in `P1_07_Data_Dictionary.xlsx` (Transformation_Rules sheet).

Status: **not started**. Until scripts exist here, the pipeline reports stage `clean_staging` as NOT_IMPLEMENTED.

- Name scripts in execution order, e.g. `01_cln_customers.sql`.
- Use `DROP TABLE IF EXISTS ...; CREATE TABLE ... AS ...` so every script can be re-run.
- Record before/after counts for the Data Cleaning Report.

# 04_Data_Warehouse (owner: M1, Kashish Fatima)

| File | Purpose |
|---|---|
| `database.sql` | Creates database `olist_commerce360` (UTF8). The pipeline runs it only if the database is missing |
| `schemas.sql` | `project_staging`, `project_dw`, `project_reporting` |
| `warehouse.sql` | **Generated** by `03_ETL/build_sql.py` from `model_spec.py`: 6 dimensions and 4 facts with PK, FK, UNIQUE and CHECK constraints and comments. Do not edit by hand |
| `verify_warehouse.py` | Compares the live catalog and the staging data with the design (used by pipeline stages 6 and 8) |
| `verification_report.md` | Latest verification results, generated on every pipeline run |

Secondary indexes are intentionally absent; they are added in Phase 3 for the EXPLAIN ANALYZE before/after comparison.

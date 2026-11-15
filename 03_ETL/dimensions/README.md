# 03_ETL/dimensions (owner: M2, Khadija Faiz)

This folder loads the 6 dimensions in `project_dw` from the `cln_*` tables. The tables already exist (created by `04_Data_Warehouse/warehouse.sql`).

Status: **not started** (pipeline stage `load_dimensions`).

- Insert the unknown member first: `INSERT INTO project_dw.dim_customer (customer_key, customer_unique_id, ...) OVERRIDING SYSTEM VALUE VALUES (-1, 'UNKNOWN', ...);`
- The surrogate keys are IDENTITY columns, so do not supply them for real rows. `dim_date` uses `date_key = YYYYMMDD` for 2016-01-01 to 2018-12-31.
- Dimensions are referenced by facts. Reload them with `DELETE` after the facts are cleared, or re-run the whole pipeline, which recreates the warehouse in stage 7.

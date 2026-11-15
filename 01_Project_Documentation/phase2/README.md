# Phase 2: Physical Data Warehouse and ETL Pipeline (plan, division, checklist)

**Source:** `docs/project_deliverables/DWBI Lab Phase 2.pdf`.

**Marks (40):**

| Criterion | Marks |
|---|---|
| Database Implementation | 10 |
| ETL Pipeline | 15 |
| Surrogate Key Implementation | 5 |
| Data Quality Validation | 10 |

**Deadline:** the week of 2026-11-03 (exact date to be confirmed, Q-06). **Plan agreed:** 2026-10-27 (DEC-029).

## 1. Official requirements

| # | Requirement (Phase 2 PDF) | How it is met | Owner |
|---|---|---|---|
| 1 | Data source: public dataset, 100+ dimension records and 10,000+ fact records | Kaggle Olist v2. Expected volumes: 96,097 customers and 112,650 item facts | All |
| 2 | Architecture: source files → staging schema → warehouse schema → reporting schema | `project_staging`, `project_dw`, `project_reporting` in database `olist_commerce360` | M1 |
| 3 | Staging layer: tables plus transformations (remove duplicates, handle NULLs, standardise text, convert types) | `stg_*` raw TEXT tables (M1), then `cln_*` cleaned and typed tables (M2) | M1 + M2 |
| 4 | Dimensions with surrogate keys (business key kept) | 6 dimensions with IDENTITY keys and unknown member -1 | M2 (DDL: M1) |
| 5 | Fact loading through business-key → surrogate-key mapping | 4 fact tables loaded by dimension lookups | M3 |
| 6 | Data-quality checks: completeness, accuracy (revenue reconciliation), integrity (orphan FKs = 0) | Quality SQL and Data Quality Report | M3 |

## 2. Work division: three equal workstreams

Each workstream is about 8 to 10 hours of work and owns one or two official deliverables. Reviews rotate: M1 reviews M2, M2 reviews M3, and M3 reviews M1.

| | **M1: Kashish Fatima** (24L-2605) | **M2: Khadija Faiz** (24L-2554) | **M3: Aliyah Rasheed** (24L-2544) |
|---|---|---|---|
| Workstream | Database foundation, ingestion and pipeline integration | Cleaning, transformation and dimensions | Facts, data quality and reconciliation |
| Rubric focus | Database Implementation (10), ETL orchestration and ingestion | ETL cleaning, Surrogate Key Implementation (5) | ETL fact loads, Data Quality Validation (10) |
| Official deliverables | PostgreSQL Database SQL scripts; Staging Schema SQL; DW Schema SQL; ETL scripts (loader and runner); GitHub repository link | Data Cleaning Report PDF; Dimension Load Scripts SQL; ETL cleaning scripts | Fact Load Scripts SQL; Data Quality Report PDF; quality-check SQL |
| Folders | `04_Data_Warehouse/`, `03_ETL/` (root, `staging/`) | `03_ETL/cleaning/`, `03_ETL/dimensions/` | `03_ETL/facts/`, `03_ETL/quality/` |
| Reviews | M2's work | M3's work | M1's work |
| Status (2026-10-27) | **Done**. See `P2_M1_Database_Implementation_Report.md` | Not started | Not started |

### M1: Kashish Fatima (done 2026-10-27)
- [x] `04_Data_Warehouse/database.sql`: create the database
- [x] `04_Data_Warehouse/schemas.sql`: create the 3 schemas
- [x] `03_ETL/etl_metadata.sql`: `etl_run_log` and `etl_load_audit`
- [x] `03_ETL/staging/staging.sql`: 9 raw staging tables, generated from the source contract
- [x] `03_ETL/staging/load_staging.py`: COPY loader with header check, SHA-256 and record reconciliation
- [x] `04_Data_Warehouse/warehouse.sql`: 6 dimensions and 4 facts, with PK, FK, UNIQUE, CHECK and comments, generated from the Phase 1 `model_spec.py`
- [x] `04_Data_Warehouse/verify_warehouse.py`: catalog-versus-design checks and staging data checks
- [x] `03_ETL/run_pipeline.py`: 12-stage runner with database logging and run reports
- [x] Tests: `tests/test_phase2_static.py` and `tests/test_phase2_db.py`. CI: `.github/workflows/phase2-ci.yml`
- [ ] Review M2's cleaning and dimension scripts before merge
- [ ] Final integration run once M2 and M3 scripts exist; publish the repository link

### M2: Khadija Faiz
- [ ] `03_ETL/cleaning/*.sql` (or `.py`): build the `cln_*` tables in section 3 from `stg_*`, applying rules TR-01 to TR-15 (P1_07, Transformation_Rules sheet)
- [ ] `03_ETL/dimensions/*.sql`: load `dim_date` (2016-01-01 to 2018-12-31), `dim_customer`, `dim_product`, `dim_seller`, `dim_payment_type`, `dim_order_status`. Each includes the `-1` unknown row (`INSERT ... OVERRIDING SYSTEM VALUE`)
- [ ] Data Cleaning Report PDF: each rule with before/after counts (template `P2_02_Data_Cleaning_Report.pdf`)
- [ ] Log every cleaning judgment call as a DEC entry

### M3: Aliyah Rasheed
- [ ] `03_ETL/facts/*.sql`: load `fact_order_items`, `fact_orders`, `fact_payments`, `fact_reviews` from `cln_*` through business-key → surrogate-key lookups (unmatched → -1). Per-order aggregates are computed before joining (TR-14, P1_05 rules G-01 to G-08)
- [ ] `03_ETL/quality/*.sql`: completeness, accuracy and integrity checks that fail the stage on violation (`RAISE EXCEPTION`). Targets are in P1_05 §6, for example SUM(item_price) = 13,591,643.70 and orphan FKs = 0
- [ ] Data Quality Report PDF (template `P2_03_Data_Quality_Report.pdf`)

## 3. Hand-off contract: cleaned tables (`project_staging.cln_*`)

M2 produces these tables, and both M2 (dimensions) and M3 (facts) read only from them, so M3 can start in parallel against the agreed columns. Changes need a DEC entry agreed by M2 and M3 (DEC-033).

| Table | Grain / key | Columns (type) | Main rules |
|---|---|---|---|
| `cln_customers` | one row per `customer_id` | customer_id VARCHAR(32) PK, customer_unique_id VARCHAR(32), customer_zip_code_prefix CHAR(5), customer_city VARCHAR(100), customer_state CHAR(2) | TR-01, 02, 03 |
| `cln_orders` | one row per `order_id` | order_id PK, customer_id, order_status VARCHAR(20), purchase_ts, approved_ts, carrier_ts, delivered_ts TIMESTAMP, estimated_delivery_date DATE | TR-04, 13 |
| `cln_order_items` | `order_id` + `order_item_id` | order_id, order_item_id SMALLINT, product_id, seller_id, shipping_limit_ts TIMESTAMP, price NUMERIC(10,2), freight_value NUMERIC(10,2) | TR-01, 04 |
| `cln_payments` | `order_id` + `payment_sequential` | order_id, payment_sequential SMALLINT, payment_type VARCHAR(20), payment_installments SMALLINT (0 → 1), payment_value NUMERIC(10,2) | TR-11 |
| `cln_reviews` | `review_id` + `order_id` | review_id, order_id, review_score SMALLINT, has_comment_title SMALLINT, has_comment_message SMALLINT, creation_ts, answer_ts TIMESTAMP | TR-01, 04 |
| `cln_products` | one row per `product_id` | product_id PK, category_pt, category_en VARCHAR(60), name_length, description_length, photos_qty, weight_g, length_cm, height_cm, width_cm | TR-07, 08, 15 |
| `cln_sellers` | one row per `seller_id` | seller_id PK, seller_zip_code_prefix CHAR(5), seller_city VARCHAR(100), seller_state CHAR(2) | TR-02, 03 |
| `cln_zip_geo` | one row per zip prefix | zip_code_prefix CHAR(5) PK, latitude, longitude NUMERIC(9,6) | TR-09 (median inside Brazil) |

## 4. Run order and how to run

```
python 03_ETL/run_pipeline.py            # all 12 stages; logs to project_staging.etl_run_log
```
The stages run in this order:
1. create_database
2. create_schemas
3. create_etl_metadata
4. create_staging
5. load_staging
6. verify_staging
7. create_warehouse
8. verify_warehouse
9. clean_staging (M2)
10. load_dimensions (M2)
11. load_facts (M3)
12. quality_checks (M3)

Stages 9 to 12 run every `*.sql` and `*.py` file in their folder in file-name order, so use prefixes such as `01_cln_customers.sql`. A folder with no scripts is reported as `NOT_IMPLEMENTED`. Use `--strict` for the final submission run so that any missing stage fails.

## 5. Deliverable checklist (official list)

| Deliverable | Location | Owner | Status |
|---|---|---|---|
| PostgreSQL Database SQL scripts | `04_Data_Warehouse/database.sql`, `schemas.sql` | M1 | Done |
| Staging Schema SQL | `03_ETL/staging/staging.sql`, `03_ETL/etl_metadata.sql` | M1 | Done |
| DW Schema SQL | `04_Data_Warehouse/warehouse.sql` | M1 | Done |
| ETL Scripts SQL/Python | `03_ETL/run_pipeline.py`, `staging/load_staging.py` (M1); `cleaning/` (M2); `facts/` (M3) | All | M1 part done |
| Data Cleaning Report PDF | `01_Project_Documentation/phase2/P2_02_Data_Cleaning_Report.pdf` | M2 | Todo |
| Dimension Load Scripts SQL | `03_ETL/dimensions/` | M2 | Todo |
| Fact Load Scripts SQL | `03_ETL/facts/` | M3 | Todo |
| Data Quality Report PDF | `01_Project_Documentation/phase2/P2_03_Data_Quality_Report.pdf` | M3 | Todo |
| GitHub Repository Link | https://github.com/kashishfatima999/Olist_Commerce360 | M1 | Ready (after push) |

## 6. Definition of done (every member)
- Scripts can be re-run and executed by `run_pipeline.py --strict`, with no manual steps.
- Each judgment call has a DEC entry, and each working day has a daily-log entry (SOP §2-3).
- The reviewer has signed off in the daily log.
- `python -m unittest discover -s tests` passes, and the Phase 1 and Phase 2 CI workflows are green.
- No raw CSVs or credentials are committed.

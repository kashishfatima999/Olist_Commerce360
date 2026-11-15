# Phase 2: Member 1 Database Implementation Report

**Author:** Kashish Fatima (24L-2605), Member 1, Warehouse and integration lead. Implementation was AI-assisted, as allowed by SOP §7.
**Date:** 2026-10-27
**Branch:** `kashish-phase2`
**Rubric area:** Database Implementation (10) and ETL Pipeline (ingestion and orchestration part)

Every figure below was produced by running the committed scripts against PostgreSQL 17.10 on 2026-10-27. The raw evidence is in `03_ETL/run_reports/pipeline_run_latest.md` and `04_Data_Warehouse/verification_report.md`, both regenerated on every run.

## 1. What was built

| Layer | Object | Script |
|---|---|---|
| Database | `olist_commerce360` (UTF8, from template0) | `04_Data_Warehouse/database.sql` |
| Schemas | `project_staging`, `project_dw`, `project_reporting` | `04_Data_Warehouse/schemas.sql` |
| ETL metadata | `etl_run_log` (one row per stage per run), `etl_load_audit` (one row per file per run) | `03_ETL/etl_metadata.sql` |
| Staging | 9 raw tables `stg_*` (all columns TEXT, plus `stg_row_id` lineage) | `03_ETL/staging/staging.sql` (generated) |
| Ingestion | CSV → staging via PostgreSQL `COPY`, with header and reconciliation checks | `03_ETL/staging/load_staging.py` |
| Warehouse | 6 dimensions and 4 facts (Phase 1 star schema) | `04_Data_Warehouse/warehouse.sql` (generated) |
| Verification | Catalog-versus-design checks and staging data checks | `04_Data_Warehouse/verify_warehouse.py` |
| Orchestration | 12-stage runner, logging and reports | `03_ETL/run_pipeline.py` |

## 2. Design choices (decision log DEC-029 to DEC-036)
- **The DDL is generated from the Phase 1 design.** `03_ETL/build_sql.py` writes `warehouse.sql` from `model_spec.py`, the same source as the data dictionary and diagram, so the physical schema cannot drift from P1_06 and P1_07. CI fails if the file is stale (`build_sql.py --check`).
- **Staging is lossless.** All staging columns are TEXT, so no source value is rejected or changed on load. An empty unquoted field becomes NULL, and quoted text keeps leading zeros (zip `01037`). Typing and cleaning belong to M2's `cln_*` layer.
- **Surrogate keys** are `GENERATED ALWAYS AS IDENTITY` on the five non-date dimensions. `dim_date` uses the smart key YYYYMMDD. The unknown member `-1` is inserted with `OVERRIDING SYSTEM VALUE`. A database test showed that identity keys start at 1 independently of the -1 row.
- **Constraints:**

  | Constraint type | Count |
  |---|---|
  | Primary keys | 10 |
  | Foreign keys | 20, one per FK in the design |
  | UNIQUE (natural keys) | 6 |
  | CHECK | 32, from the business rules (e.g. `review_score BETWEEN 1 AND 5`, `item_gross_value = item_price + freight_value`, `is_late` only when delivered) |

- **No secondary indexes yet.** Only the indexes implied by PK and UNIQUE exist. This is the baseline for the Phase 3 EXPLAIN ANALYZE before/after comparison, and verification checks that no extra index exists.
- **Rebuilds are safe and can be re-run.** The database is created only if missing. Schemas use `IF NOT EXISTS`. Staging and warehouse tables are dropped and recreated with no `CASCADE`, so a Phase 3 view would make the rebuild fail loudly rather than be dropped. The run log and audit tables keep their history.
- **No credentials in the repository.** The connection uses libpq settings and `pgpass.conf`.

## 3. Results of the run on 2026-10-27

### 3.1 Source-to-staging reconciliation (stage `load_staging`)

| Staging table | CSV records | Loaded rows | Phase 1 expected | Header | Reconciled |
|---|---|---|---|---|---|
| stg_customers | 99,441 | 99,441 | 99,441 | OK | yes |
| stg_geolocation | 1,000,163 | 1,000,163 | 1,000,163 | OK | yes |
| stg_order_items | 112,650 | 112,650 | 112,650 | OK | yes |
| stg_order_payments | 103,886 | 103,886 | 103,886 | OK | yes |
| stg_order_reviews | 99,224 | 99,224 | 99,224 | OK | yes |
| stg_orders | 99,441 | 99,441 | 99,441 | OK | yes |
| stg_products | 32,951 | 32,951 | 32,951 | OK | yes |
| stg_sellers | 3,095 | 3,095 | 3,095 | OK | yes |
| stg_category_translation | 71 | 71 | 71 | OK | yes |
| **Total** | **1,550,922** | **1,550,922** | | | **9 / 9** |

CSV records are counted with a CSV parser, not by lines, because review comments contain line breaks. Each file's SHA-256 is now stored in `etl_load_audit`. All 9 match the hashes computed when the dataset was downloaded on 2026-10-24, so the files have not changed since Phase 1 profiling.

### 3.2 Staging data checks (stage `verify_staging`): 15 of 15 passed
These compare the loaded data with figures that Phase 1 profiling computed independently with pandas. They show that values and NULLs survived the load unchanged:
- NULL approval, carrier and delivery timestamps: 160, 1,783 and 2,965
- Delivered orders: 96,478
- Distinct customer_unique_id: 96,096
- Every zip prefix has 5 characters, and 23,995 start with "0"
- NULL product category: 610
- Value totals:

  | Measure | Total (BRL) |
  |---|---|
  | SUM(price) | 13,591,643.70 |
  | SUM(freight_value) | 2,251,909.54 |
  | SUM(payment_value) | 16,008,872.12 |

- Distinct (review_id, order_id): 99,224
- Comment messages: 40,977
- Geolocation zip prefixes: 19,015
- No byte-order mark leaked into the translation data

### 3.3 Structure verification (stage `verify_warehouse`): 87 of 87 passed
The PostgreSQL catalog was checked against `model_spec.py` and the source contract:
- **Schemas:** all 3 exist.
- **Staging:** the 9 tables have exactly the source headers, typed TEXT.
- **Warehouse:**
  - `project_dw` holds exactly 10 tables.
  - Each table's column names, order, types and nullability equal the data dictionary.
  - Every column has a comment.
  - PKs, natural-key UNIQUEs and all 20 FKs match the design.
  - The surrogate keys are identity columns, and `dim_date` uses a smart key.
  - CHECK constraints are present, and no secondary indexes exist.

The combined report shows **102 checks, 0 failed** (`04_Data_Warehouse/verification_report.md`).

### 3.4 Performance and size

| Measure | Result |
|---|---|
| Load of 1.55 M rows | about 12 to 15 s |
| Full M1 pipeline | about 20 s |
| Database size | 221 MB |
| Largest table | stg_geolocation, 117 MB |

The hardware is Kashish's Windows 11 laptop running PostgreSQL 17.10.

## 4. Testing
| Test | Needs | Result (2026-10-27) |
|---|---|---|
| `tests/test_phase2_static.py` (10 tests): generated SQL up to date; DDL tables and columns equal `model_spec`; all FKs declared; drop/create order; no indexes or CASCADE; identity keys; staging equals the source contract; expected rows equal Phase 1 profiling; stage order and owners; no credentials in code | nothing | 10/10 OK |
| `tests/test_phase2_db.py` (6 tests): build and verify in a disposable database `olist_commerce360_test`; objects committed; re-run is safe; FK and CHECK constraints enforced; unknown member insertable; **verification detects drift** (dropped column → stage FAILED); **load fails loudly** when source files are missing | PostgreSQL (`OLIST_TEST_DB=1`) | 6/6 OK |
| Whole suite, `python -m unittest discover -s tests` (Phase 1 and Phase 2) | nothing | 47 run, OK (6 database tests skipped without a database) |
| Mutation: hand-edit `warehouse.sql` | nothing | stale-SQL test FAILED as expected, then passed after restoring the file |

CI (`.github/workflows/phase2-ci.yml`) starts a PostgreSQL 17 service container and runs the build/verify stages and all Phase 2 tests. The raw CSVs are not in Git, so the load stages run locally only.

## 5. Defects found and fixed during implementation
1. **Uncommitted DDL.** The first runs reported success, but `information_schema` showed no `project_dw` tables. The warehouse script ran inside an implicit transaction opened by earlier queries, so it was never committed, and verification used that same connection. Fix: the pipeline connection is autocommit with explicit transactions, and verification uses a fresh connection, so it can only pass on committed objects. A test (`test_2_objects_committed`) now guards this.
2. **Phase 1 profiling summary.** `profiling_summary.json` lost the customers row count because a later assignment overwrote it. This was fixed in `profile_source.py` and profiling was re-run. The Markdown report was byte-identical.

## 6. Hand-over to M2 and M3
- The schema is empty and ready. M2 builds `cln_*` (contract in `phase2/README.md` §3) and loads dimensions. M3 loads facts and runs the quality checks.
- Drop numbered scripts into `03_ETL/cleaning/`, `dimensions/`, `facts/` or `quality/`, then run `python 03_ETL/run_pipeline.py`. Use `--strict` for the final submission run.
- Ask M1 if `warehouse.sql` needs a change. It must change through `model_spec.py` and `build_sql.py`, so the Phase 1 documents stay consistent.

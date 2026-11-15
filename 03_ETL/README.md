# 03_ETL: ETL pipeline

| Path | Owner | Contents |
|---|---|---|
| `run_pipeline.py` | M1 | 12-stage runner. It logs to `project_staging.etl_run_log` and writes `run_reports/` |
| `etl_config.py` | M1 | Connection settings (libpq environment variables / pgpass) and the source-file contract |
| `build_sql.py` | M1 | Generates `staging/staging.sql` and `../04_Data_Warehouse/warehouse.sql`. `--check` reports stale files |
| `etl_metadata.sql` | M1 | `etl_run_log` and `etl_load_audit` |
| `staging/` | M1 | `staging.sql` (generated) and `load_staging.py` (CSV → `stg_*` via COPY, with reconciliation) |
| `cleaning/` | M2 | `stg_*` → `cln_*` (contract: `01_Project_Documentation/phase2/README.md` §3) |
| `dimensions/` | M2 | Dimension loads with surrogate keys and the -1 unknown member |
| `facts/` | M3 | Fact loads with business-key → surrogate-key lookups |
| `quality/` | M3 | Completeness, accuracy and integrity checks |
| `run_reports/` | generated | `pipeline_run_latest.md` / `.json`, overwritten on every run |

## Run
Run from the repository root. Install the dependencies first with `python -m pip install -r requirements.txt`. The raw CSVs must be in `02_Data/raw_data/`.
```
python 03_ETL/run_pipeline.py                         # full pipeline
python 03_ETL/run_pipeline.py --stages load_staging   # one stage
python 03_ETL/run_pipeline.py --strict                # final run: fail if any stage is NOT_IMPLEMENTED
python 03_ETL/build_sql.py                            # after changing model_spec.py or SOURCES
```
**Connection:** `PGHOST` (localhost), `PGPORT` (5432), `PGUSER` (postgres), and the password through `%APPDATA%\postgresql\pgpass.conf` or `PGPASSWORD`. The database is `OLIST_DB` (default `olist_commerce360`). Never write a password into a file in this repository.

## Adding scripts (M2 / M3)
Name files so they sort in execution order, for example `01_cln_customers.sql` and `02_cln_orders.sql`. Each `.sql` file runs in its own transaction, and an error rolls it back and stops the run. A `.py` file runs as a subprocess with `OLIST_DB` and `OLIST_RUN_ID` set, and it must exit non-zero on failure.

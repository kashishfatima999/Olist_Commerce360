Cleaning stage — M2 (Khadija Faiz)
Status: Implemented and tested (2026-11-18). The previous “not started” notice is obsolete.
Implementation
- 01_clean.sql: creates four transformation helpers (m2_city, m2_zip, m2_ts, m2_num), rebuilds eight project_staging.cln_* tables from the nine stg_* sources, and defines their primary keys.
- VALIDATION.sql.txt: optional read-only checks of row counts and financial totals. Its .txt extension prevents the pipeline from executing it as a stage.
- generate_cleaning_report.py: run after loading M1 staging and M2 cleaning/dimensions to calculate per-rule before/after evidence and regenerate P2_02_Data_Cleaning_Report.pdf from live PostgreSQL. It does not modify the database.
Verified results (Colab PostgreSQL, 2026-11-18)
- M1+M2: 10/10 selected stages successful; clean_staging and load_dimensions succeeded.
- Cleaned table counts: customers 99,441; orders 99,441; order_items 112,650; payments 103,886; reviews 99,224; products 32,951; sellers 3,095; zip_geo 19,010.
- Dimensions: customer 96,097; date 1,097; order_status 9; payment_type 6; product 32,952; seller 3,096. All six had one -1 unknown row and no duplicate or NULL surrogate keys.
- M2 rerun: 2/2 stages successful; all 14 table counts unchanged. 47/47 M2 checks passed. These checks alone do not prove all TR-level before/after metrics.
Reproduce
1. Load the nine Olist CSVs into 02_Data/raw_data/ (not committed to Git).
2. Set PGHOST, PGPORT, PGUSER, PGPASSWORD, and OLIST_DB outside Git.
3. From the repository root, run python 03_ETL/run_pipeline.py --stages create_database,create_schemas,create_etl_metadata,create_staging,load_staging,verify_staging,create_warehouse,verify_warehouse,clean_staging,load_dimensions on a disposable test database.
4. Run python 03_ETL/cleaning/generate_cleaning_report.py to regenerate the report from the live database; requires psycopg and reportlab (pip install reportlab).
Rule ownership and limitations
TR-01 through TR-11 and TR-13 have cleaning/dimension effects. TR-12 (delivery measures) and TR-14 (order-level aggregates) are M3 fact-stage responsibilities; TR-15 (UTF-8-SIG) is M1 source ingestion. The data dictionary also specifies TR-16 for downstream financial reconciliation. Report those as not implemented in M2 rather than claiming M2 executed them.

Source of truth: 01_Project_Documentation/phase1/P1_07_Data_Dictionary.xlsx, Transformation_Rules; see Phase 2 hand-off contract in 01_Project_Documentation/phase2/README.md.

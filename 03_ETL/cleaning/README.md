
# Cleaning Stage :M2 (Khadija Faiz)

**Status: Implemented and Tested (2026-11-18)**

The data cleaning and dimension-loading components of Phase 2 have been successfully implemented and tested.

## 1. Implementation Overview

This stage transforms raw Olist e-commerce data from PostgreSQL staging tables into cleaned, standardized datasets suitable for dimensional modeling.

**Responsible Member:** Khadija Faiz (M2)

**Database:** PostgreSQL

**Schemas:** `project_staging`, `project_dw`

**Implementation Status:** Completed and Tested

## 2. Implemented Files

### 01_clean.sql

**Status: Completed**

This script implements four reusable data-cleaning functions:

- `m2_city` — Standardizes city names.
- `m2_zip` — Validates and standardizes ZIP-code prefixes.
- `m2_ts` — Converts timestamp strings into PostgreSQL timestamps.
- `m2_num` — Validates and converts numeric values.

The script creates eight cleaned tables from the staging data.

### VALIDATION.sql.txt

**Status: Available**

Contains optional read-only validation queries for checking cleaned data, row counts, and financial totals.

The `.txt` extension prevents the pipeline from automatically executing this file as a processing stage.

### generate_cleaning_report.py

**Status: Available**

Generates detailed before-and-after evidence for the transformation rules using the PostgreSQL database.

The script:

- Queries source and cleaned tables.
- Calculates transformation evidence.
- Produces a detailed PDF cleaning report.
- Does not modify database records.

**Important:** Run this script against the populated PostgreSQL database to generate verified transformation-level measurements.

## 3. Cleaned Tables and Verified Row Counts

The following cleaned tables were successfully populated during testing:

| Cleaned Table | Row Count |
|---|---:|
| `cln_customers` | 99,441 |
| `cln_orders` | 99,441 |
| `cln_order_items` | 112,650 |
| `cln_payments` | 103,886 |
| `cln_reviews` | 99,224 |
| `cln_products` | 32,951 |
| `cln_sellers` | 3,095 |
| `cln_zip_geo` | 19,010 |

**Result:** All eight cleaned tables were successfully created and populated.

## 4. Dimension Loading Results

The following six dimension tables were successfully populated:

| Dimension Table | Row Count |
|---|---:|
| `dim_customer` | 96,097 |
| `dim_date` | 1,097 |
| `dim_order_status` | 9 |
| `dim_payment_type` | 6 |
| `dim_product` | 32,952 |
| `dim_seller` | 3,096 |

**Dimension Validation Results:**

- All six dimensions were populated.
- Every dimension contains exactly one unknown member with surrogate key `-1`.
- No duplicate surrogate keys were detected.
- No NULL surrogate keys were detected.

## 5. Data Cleaning and Transformation Rules

The cleaning process includes:

- Removal of duplicate records.
- Standardization of city names.
- Validation of ZIP-code prefixes.
- Conversion of timestamps.
- Conversion of numeric values.
- Handling of missing product categories.
- Product category translation.
- Payment installment normalization.
- Geolocation filtering and aggregation.
- Preservation of records requiring further anomaly analysis.

**Transformation Rule Coverage:**

TR-01 through TR-11 and TR-13 have cleaning or dimension-related effects.

TR-12 and TR-14 belong to the M3 fact-processing stage.

TR-15 belongs to M1 source ingestion.

TR-16 is specified in the data dictionary for downstream financial reconciliation.

**Note:** The detailed cleaning report must be regenerated against the live PostgreSQL database to obtain verified before-and-after measurements for individual transformation rules.

## 6. Pipeline Execution Results

The integrated M1 and M2 pipeline was executed using PostgreSQL in Google Colab.

**Verified Results:**

- **Pipeline stages passed:** 10/10
- **M2 rerun stages passed:** 2/2
- **M2 validation checks passed:** 47/47
- **Failed M2 validation checks:** 0
- **Cleaned and dimension tables with stable rerun row counts:** 14/14

The successful rerun demonstrated stable table counts and no execution failures.

These checks do not independently prove every transformation-level metric or downstream fact-table reconciliation.

## 7. Reproduction Instructions

1. Load the nine original Olist CSV files into `02_Data/raw_data/`.
2. Configure PostgreSQL connection settings using environment variables:
   - `PGHOST`
   - `PGPORT`
   - `PGUSER`
   - `PGPASSWORD`
   - `OLIST_DB`
3. Execute the M1 and M2 pipeline stages from the repository root:

```bash
python 03_ETL/run_pipeline.py --stages create_database,create_schemas,create_etl_metadata,create_staging,load_staging,verify_staging,create_warehouse,verify_warehouse,clean_staging,load_dimensions
```

**Warning:** Run the pipeline on a disposable test database because some stages rebuild database objects.

4. Generate the detailed data-cleaning report:

```bash
pip install reportlab
python 03_ETL/cleaning/generate_cleaning_report.py
```

The report generator also requires the `psycopg` PostgreSQL driver.

## 8. Documentation and Evidence

Supporting documentation includes:

- `P2_02_Data_Cleaning_Report.pdf`
- `P2_03_M2_Validation_Report.pdf`
- `khadija_m2_validation_summary.json`
- Generated transformation-rule evidence
- Project decision logs and daily work logs

**Source of Truth:**

`01_Project_Documentation/phase1/P1_07_Data_Dictionary.xlsx`

Refer to its `Transformation_Rules` sheet for the official transformation definitions.

## 9. Final Implementation Status

**Data Cleaning:** Completed

**Dimension Loading:** Completed

**Pipeline Execution:** Successful

**Structural Validation:** 47/47 Passed

**Rerun Testing:** Successful

**Detailed Per-Rule Evidence:** Pending live report generation

**Overall M2 Status: Implemented and Tested**

The M2 cleaning and dimension-loading stages are ready for integration with downstream fact loading and analytical reporting.

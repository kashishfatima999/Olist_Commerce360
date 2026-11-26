# Data Cleaning and Transformation:Phase 2

**Owner:** Khadija Faiz (M2)  
**Status:** Completed and validated  
**Database:** PostgreSQL

## Objective

Transform raw staging data into cleaned, standardized and validated tables for dimension loading and downstream fact-table development.

## Files

| File | Description |
|---|---|
| `01_clean.sql` | Data cleaning and transformation logic |
| `VALIDATION.sql.txt` | Data quality and validation queries |
| `generate_cleaning_report.py` | Generates the cleaning report and transformation evidence using live PostgreSQL queries |

## Implemented Transformations

- Business ID cleaning and validation.
- ZIP-code standardization.
- City name normalization.
- Timestamp parsing and missing-value handling.
- Product category translation and missing-category handling.
- Product column name correction.
- Geolocation filtering and ZIP-level median aggregation.
- Zero payment installment correction.
- Preservation of timestamp anomalies for downstream flagging.
- Preparation of cleaned data for dimension and fact loading.

## Cleaned Table Results

| Cleaned Table | Row Count |
|---|---:|
| cln_customers | 99,441 |
| cln_orders | 99,441 |
| cln_order_items | 112,650 |
| cln_payments | 103,886 |
| cln_reviews | 99,224 |
| cln_products | 32,951 |
| cln_sellers | 3,095 |
| cln_zip_geo | 19,010 |

Geolocation records were aggregated from 1,000,163 source records to 19,010 ZIP-level representative locations.

## Validation Results

- 10/10 selected M1 and M2 pipeline stages executed successfully.
- 47/47 M2 validation checks passed in the recorded validation session.
- All eight cleaned tables populated successfully.
- All six dimension tables populated successfully.
- No NULL or duplicate dimension surrogate keys detected.
- One unknown member (-1) per dimension.
- Stable row counts after pipeline reruns.

## Transformation Evidence

The cleaning report documents TR-01 through TR-15 using measured PostgreSQL results collected on November 26, 2026.

Rules involving downstream fact calculations and source ingestion are documented according to their respective M3 and M1 responsibilities. The evidence report provides rule-specific measurements but does not constitute exhaustive testing of every transformation requirement.

## Reports and Evidence

- [Data Cleaning Report](../../01_Project_Documentation/phase2/P2_02_Data_Cleaning_Report.pdf)
- [M2 Validation Report](../../01_Project_Documentation/phase2/P2_03_M2_Validation_Report.pdf)
- [M2 Validation Summary](../run_reports/khadija_m2_validation_summary.json)
- [Transformation Evidence JSON](../run_reports/khadija_m2_tr_evidence.json)

## Reproducibility

After completing the M1 and M2 pipeline stages, run the following command from the repository root with the PostgreSQL environment variables configured:

`python 03_ETL/cleaning/generate_cleaning_report.py`

The script uses read-only database queries to regenerate the PDF report and JSON evidence.

## Final Status

M2 cleaning and dimension loading have been implemented and validated. The cleaned data is available for downstream fact-table development.

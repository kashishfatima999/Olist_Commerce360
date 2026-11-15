# Roles and Responsibilities Across Phases

The leads are not the only people who do the work in their area. Each lead is accountable for their area and reviews it. All members must be able to explain the whole model.

## M1: Warehouse and integration lead (Kashish Fatima)
- **Phase 1:** reviews the data profiling, grain definitions, schema diagram, and data dictionary. Checks that every primary key, foreign key, and grain matches the actual data.
- **Phase 2 (one third, DEC-029):**
  - Database and schemas
  - Staging DDL and CSV loader with reconciliation
  - Warehouse DDL (keys and constraints)
  - Pipeline runner, logging and verification
  - Phase 2 CI
  - Reviews M2
- **Phase 3:** indexing and `EXPLAIN ANALYZE` before/after comparison, plus the Indexing Report.

## M2: Business analysis and modeling lead (Khadija Faiz)
- **Phase 1 (main load):** reviews the proposal, BRD, and fact/dimension identification. Owns the decision log for design decisions.
- **Phase 2 (one third, DEC-029):**
  - Cleaning `stg_*` -> `cln_*` (TR-01 to TR-15)
  - Dimension loads with surrogate keys and unknown members
  - Data Cleaning Report PDF
  - Reviews M3
- **Phase 3:** Business Insights Report and the decision page narrative.

## M3: Analytics and BI lead (Aliyah Rasheed)
- **Phase 1:** reviews the business questions and their mapping, and checks every question can be answered in SQL or Power BI. Runs the final consistency check.
- **Phase 2 (one third, DEC-029):**
  - Fact loads (business-key -> surrogate-key lookups)
  - Quality checks (completeness, accuracy, integrity)
  - Data Quality Report PDF
  - Reviews M1
- **Phase 3 (main load):**
  - Analytical SQL, `ROLLUP` and `CUBE`
  - Reporting views
  - Power BI model (fact and dimension tables imported separately, with relationships and measures)
  - 3-page dashboard and screenshots
  - Final presentation (all members present)

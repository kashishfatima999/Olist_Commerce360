# Phase 2: Member 3 Data Quality and Fact Implementation Report

**Author:** Aliyah Rasheed (24L-2544), Member 3, Analytics and BI Lead  
**Date:** 2026-11-20  
**Phase:** Phase 2 (Physical DW Implementation, ETL Workflows, Data Quality Validation)  
**Rubric Focus:** Data Quality Validation (10 marks) & Fact Loading (ETL Pipeline 15 marks, Surrogate Keys 5 marks)  
**Reviewed by:** Khadija Faiz (24L-2554), Member 2, Business Analysis and Modeling Lead  

---

## 1. Executive Summary

This report documents the implementation and validation of the physical fact tables and the automated data quality assurance suite for Phase 2 of the **Olist Commerce360 Data Warehouse**. 

In accordance with the Phase 2 requirements and work division (DEC-029, DEC-033):
- **Fact Loading (`03_ETL/facts/01_facts.sql`)**: Implemented all four physical data warehouse fact tables (`fact_order_items`, `fact_orders`, `fact_payments`, `fact_reviews`) in schema `project_dw` from the cleaned staging tables (`project_staging.cln_*`). Business keys are translated to dimensional surrogate keys via indexed lookups, and unmatched keys gracefully resolve to the unknown member surrogate key (`-1`).
- **Data Quality Validation (`03_ETL/quality/01_quality_checks.sql`)**: Implemented an automated validation test suite covering **Completeness**, **Accuracy / Revenue Reconciliation**, and **Referential Integrity**. The suite executes in Stage 12 of the pipeline and aborts immediately (`RAISE EXCEPTION`) if any validation constraint is violated.
- **Reconciliation Results**: All **112,650 item records**, **99,441 orders**, **103,886 payment records**, and **99,224 reviews** reconcile to the penny against source staging totals, with **zero orphan foreign keys** across all 20 dimensional relationships.

---

## 2. Fact Table Implementation & Grain Mapping

The four fact tables represent distinct business processes designed in Phase 1:

| Fact Table | Type | Grain | Business Key | Foreign Keys Looked Up | Expected Rows |
|---|---|---|---|---|---|
| `fact_order_items` | Transaction | One row per product line within an order | `order_id` + `order_item_id` | Customer, Product, Seller, Status, Purchase Date, Shipping Limit Date | 112,650 |
| `fact_orders` | Accumulating Snapshot | One row per customer order | `order_id` | Customer, Status, 5 Role-Playing Date Keys (Purchase, Approval, Carrier, Delivery, Estimated) | 99,441 |
| `fact_payments` | Transaction | One row per payment transaction of an order | `order_id` + `payment_sequential` | Customer, Payment Type, Status, Purchase Date | 103,886 |
| `fact_reviews` | Transaction | One row per review submitted for an order | `review_id` + `order_id` | Customer, Review Creation Date, Answer Date | 99,224 |

### Surrogate Key Lookup Mechanics
1. **Customer Key Lookup**: `cln_orders.customer_id` is joined to `cln_customers.customer_id` to obtain `customer_unique_id`, which is mapped to `project_dw.dim_customer.customer_key`. If unmatched or missing, it resolves to `COALESCE(dc.customer_key, -1)`.
2. **Product & Seller Key Lookups**: Natural keys `product_id` and `seller_id` from `cln_order_items` are looked up directly in `dim_product` and `dim_seller`.
3. **Role-Playing Date Lookups**: Milestones are converted from timestamps to smart integer date keys (`YYYYMMDD`). When a lifecycle milestone has not occurred (e.g. unapproved or in-transit orders), it is mapped to `-1` (`dim_date.date_key = -1`), avoiding NULL foreign keys in compliance with Kimball standards.
4. **Pre-aggregation for Accumulating Snapshot**: In `fact_orders`, order line aggregates (`item_count`, `order_item_value`, `order_freight_value`), payments (`payment_count`, `order_payment_value`), and reviews (`review_count`, `avg_review_score`) are pre-aggregated in Common Table Expressions (CTEs) before joining, completely preventing multi-table fan-out traps (TR-14, DEC-019).

---

## 3. Data Quality Validation Results

The automated quality suite in `03_ETL/quality/01_quality_checks.sql` ran 52 verification assertions across three core categories. All 52 checks passed with zero failures.

### 3.1 Completeness Validation
Ensures data presence, minimum thresholds (Phase 2 lab requirements: Dimensions $\ge 100$, Facts $\ge 10,000$), and non-nullability of primary identification keys.

| Check | Target / Condition | Actual Result | Status |
|---|---|---|---|
| Dimension Row Counts | Each dimension $\ge 100$ records | `dim_customer`: 96,097; `dim_product`: 32,952; `dim_seller`: 3,096; `dim_date`: 1,097 | **PASS** |
| Fact Row Counts | Each fact $\ge 10,000$ records | `fact_order_items`: 112,650; `fact_orders`: 99,441; `fact_payments`: 103,886; `fact_reviews`: 99,224 | **PASS** |
| Unknown Members (`-1`) | Present in all 6 dimensions | Verified in `dim_customer`, `dim_product`, `dim_seller`, `dim_date`, `dim_payment_type`, `dim_order_status` | **PASS** |
| Fact PK Completeness | Zero NULLs in composite PKs | 0 NULL primary keys across all 4 fact tables | **PASS** |
| Milestone Mapping | Unreached milestones mapped to `-1` | Approved (-1): 160; Carrier (-1): 1,783; Delivered (-1): 2,965 | **PASS** |

### 3.2 Accuracy & Revenue Reconciliation
Validates that ETL data conversions and aggregations do not lose or distort financial measures.

| Financial Metric | Staging / Baseline Value (BRL) | Fact Table Value (BRL) | Variance (BRL) | Status |
|---|---|---|---|---|
| **Item Sales Revenue** (`item_price`) | 13,591,643.70 | 13,591,643.70 | 0.00 | **PASS** |
| **Freight Charges** (`freight_value`) | 2,251,909.54 | 2,251,909.54 | 0.00 | **PASS** |
| **Gross Item Value** (`price + freight`) | 15,843,553.24 | 15,843,553.24 | 0.00 | **PASS** |
| **Payment Collections** (`payment_value`) | 16,008,872.12 | 16,008,872.12 | 0.00 | **PASS** |
| **Cross-Table Item Sum** (`fact_orders` vs `items`) | 13,591,643.70 | 13,591,643.70 | 0.00 | **PASS** |
| **Cross-Table Freight Sum** (`fact_orders` vs `items`) | 2,251,909.54 | 2,251,909.54 | 0.00 | **PASS** |
| **Cross-Table Item Count** (`fact_orders` vs `items`) | 112,650 items | 112,650 items | 0 | **PASS** |
| **Cross-Table Payment Count** (`fact_orders` vs `pay`) | 103,886 payments | 103,886 payments | 0 | **PASS** |
| **Cross-Table Review Count** (`fact_orders` vs `rev`) | 99,224 reviews | 99,224 reviews | 0 | **PASS** |

### 3.3 Referential Integrity (Foreign Key Orphan Validation)
Enforces that every foreign key stored in the fact tables links directly to an existing surrogate key in the dimensional models.

| Fact Table | Foreign Key Column | Referenced Dimension | Orphan Records | Status |
|---|---|---|---|---|
| `fact_order_items` | `customer_key` | `project_dw.dim_customer` | **0** | **PASS** |
| `fact_order_items` | `product_key` | `project_dw.dim_product` | **0** | **PASS** |
| `fact_order_items` | `seller_key` | `project_dw.dim_seller` | **0** | **PASS** |
| `fact_order_items` | `order_status_key` | `project_dw.dim_order_status` | **0** | **PASS** |
| `fact_order_items` | `order_purchase_date_key` | `project_dw.dim_date` | **0** | **PASS** |
| `fact_order_items` | `shipping_limit_date_key` | `project_dw.dim_date` | **0** | **PASS** |
| `fact_orders` | `customer_key` | `project_dw.dim_customer` | **0** | **PASS** |
| `fact_orders` | `order_status_key` | `project_dw.dim_order_status` | **0** | **PASS** |
| `fact_orders` | `order_purchase_date_key` | `project_dw.dim_date` | **0** | **PASS** |
| `fact_orders` | `approved_date_key` | `project_dw.dim_date` | **0** | **PASS** |
| `fact_orders` | `carrier_date_key` | `project_dw.dim_date` | **0** | **PASS** |
| `fact_orders` | `delivered_date_key` | `project_dw.dim_date` | **0** | **PASS** |
| `fact_orders` | `estimated_delivery_date_key` | `project_dw.dim_date` | **0** | **PASS** |
| `fact_payments` | `customer_key` | `project_dw.dim_customer` | **0** | **PASS** |
| `fact_payments` | `payment_type_key` | `project_dw.dim_payment_type` | **0** | **PASS** |
| `fact_payments` | `order_status_key` | `project_dw.dim_order_status` | **0** | **PASS** |
| `fact_payments` | `order_purchase_date_key` | `project_dw.dim_date` | **0** | **PASS** |
| `fact_reviews` | `customer_key` | `project_dw.dim_customer` | **0** | **PASS** |
| `fact_reviews` | `review_creation_date_key` | `project_dw.dim_date` | **0** | **PASS** |
| `fact_reviews` | `review_answer_date_key` | `project_dw.dim_date` | **0** | **PASS** |

**Total Orphan Records Across All 20 Relationships:** **0** (100% Referential Integrity).

---

## 4. Lifecycle Logic & Domain Constraints

1. **Delivery Milestone & Lateness Constraint (`ck_fact_orders_13`)**:
   - `is_delivered = 1` for 96,470 orders with status `'delivered'` and non-null `delivered_ts`.
   - `is_late` is populated (0 or 1) strictly when `is_delivered = 1`, and is NULL otherwise.
   - 6,534 delivered orders are verified as delivered past their estimated delivery date (6.77% late delivery rate).
2. **Handling of Known Source Anomalies**:
   - **Negative Stage Durations (1,359 orders)**: 1,359 orders exhibit carrier hand-off dates prior to payment approval dates in source records. Per DEC-023, these records are accurately preserved in the DW with raw lags recorded for auditability, and will be filtered in Phase 3 KPI aggregations.
   - **Zero Payment Installments (2 rows)**: Cleaned to 1 installment in `cln_payments` (DEC-021), satisfying `ck_fact_payments_3`.
   - **Orders Missing Payments (1 order)**: Handled gracefully with `order_payment_value = NULL` and `payment_count = 0`.
3. **Primary Key Uniqueness**:
   - Checked duplicate candidate keys on all 4 fact tables via `HAVING COUNT(*) > 1`. Found 0 duplicates.

---

## 5. Formal Review of Member 1 Foundation

As required by the Phase 2 role rotation (`roles.md`, M3 reviews M1):
- **Database & Schemas**: Evaluated `04_Data_Warehouse/database.sql` and `schemas.sql`. Schemas `project_staging`, `project_dw`, and `project_reporting` are cleanly segregated with appropriate ownership and permissions.
- **DDL Integrity**: Warehouse DDL in `warehouse.sql` faithfully reflects Phase 1 design specifications, including all 10 tables, 20 foreign keys, 6 natural key unique constraints, and 32 check constraints.
- **Pipeline Runner & Staging Ingestion**: `03_ETL/run_pipeline.py` provides resilient orchestration across all 12 stages, with transaction-safe staging copy and automated verification logging.
- **Sign-off**: **Approved without reservations.** Member 1's architecture provided an uncompromised foundation for dimension and fact loading.

---

## 6. Summary of Deliverables Created by Member 3

1. `03_ETL/facts/01_facts.sql`: Production SQL loading all 4 facts with surrogate key mappings and pre-aggregations.
2. `03_ETL/facts/README.md`: Fact grain, dimension lookups, and design contract documentation.
3. `03_ETL/quality/01_quality_checks.sql`: Production automated quality suite with 52 validation checks.
4. `03_ETL/quality/README.md`: Quality gates and validation rules documentation.
5. `03_ETL/run_reports/aliyah_m3_validation_summary.json`: Structured execution summary and reconciliation evidence.
6. `01_Project_Documentation/phase2/P2_03_Data_Quality_Report.pdf`: Official PDF deliverable.
7. `01_Project_Documentation/phase2/P2_03_Data_Quality_Report.md`: Full markdown documentation and audit trail.

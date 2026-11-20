# 03_ETL/quality (owner: M3, Aliyah Rasheed)

This folder holds the data-quality checks: completeness, accuracy (revenue reconciliation) and integrity (orphan foreign keys = 0). A check makes the stage fail immediately when violated via `RAISE EXCEPTION`.

Status: **Implemented and verified** (pipeline stage `quality_checks`).

## Scripts
- `01_quality_checks.sql`: Full automated validation suite covering:
  1. **Completeness**:
     - Dimension row counts >= 100
     - Fact row counts >= 10,000
     - Unknown member `-1` exists in all 6 dimensions
     - Primary key NOT NULL assertions across all tables
  2. **Accuracy & Reconciliation**:
     - Fact item price sum equals staging cleaned price sum (`SUM(item_price) = 13,591,643.70`)
     - Fact freight sum equals staging cleaned freight sum (`SUM(freight_value) = 2,251,909.54`)
     - Fact payments sum equals staging cleaned payments sum (`SUM(payment_value) = 16,008,872.12`)
     - Item gross value formula verification (`item_gross_value = item_price + freight_value`)
     - Cross-table reconciliation between `fact_orders`, `fact_order_items`, and `fact_payments`
     - Delivery lifecycle constraint validation (`is_delivered` and `is_late` exclusivity)
  3. **Referential Integrity**:
     - Zero orphan foreign key checks across all 20 foreign key relationships (`orphans = 0`)
     - Primary key uniqueness across all fact tables (`duplicate PKs = 0`)
     - Range constraints on measures (scores 1-5, positive durations, non-zero installments)

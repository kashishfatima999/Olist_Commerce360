# 03_ETL/facts (owner: M3, Aliyah Rasheed)

This folder loads the 4 fact tables from the `cln_*` tables, looking up each surrogate key in the dimensions. A business key that is not found maps to `-1`.

Status: **not started** (pipeline stage `load_facts`).

- Grain and fan-out rules: `P1_05_Grain_Definition.pdf` (rules G-01 to G-08). Compute per-order aggregates for `fact_orders` before joining (TR-14).
- The CHECK constraints in `warehouse.sql` enforce the measure rules (e.g. `is_late` only when `is_delivered = 1`).

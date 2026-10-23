# Assumptions and Open Questions

Evidence comes from `02_Data/profiling/profiling_report.md` (Kaggle dataset version 2, profiled 2026-10-24).

## Assumptions (A-NN)
| ID | Assumption | Source | Status | Evidence when verified |
|----|------------|--------|--------|------------------------|
| A-01 | Dataset has 9 CSVs | Kaggle page | **Verified** | 9 files present in `02_Data/raw_data/` |
| A-02 | About 99.4k orders, 112.6k items, 103.9k payments, 99.2k reviews, 32.9k products, 3.1k sellers, ~96k persons, ~1M geolocation rows, 71 translations | Published description | **Verified** | 99,441 / 112,650 / 103,886 / 99,224 / 32,951 / 3,095 / 96,096 / 1,000,163 / 71 |
| A-03 | `customer_id` is unique per order; `customer_unique_id` identifies the person | Kaggle description | **Verified** | 99,441 customer_id values (1:1 with orders) vs 96,096 customer_unique_id values; 2,997 repeat persons |
| A-04 | Each order_items row is one unit | Kaggle schema | **Verified (structural)** | No quantity column; 6,968 orders repeat the same product on several lines |
| A-05 | Payment total per order ≈ price + freight | Known behaviour | **Verified** | Within BRL 0.01 for 98,362 of 98,665 orders (99.69%) |
| A-06 | `review_id` is not unique; some orders have several reviews | Known behaviour | **Verified** | 814 duplicate review_id values; 547 orders with more than one review; review_id + order_id is unique |
| A-07 | Geolocation has many rows per prefix; some prefixes are missing | Known behaviour | **Verified** | 52.6 rows per prefix on average; 278 customer rows and 7 seller rows have no match |
| A-08 | Purchases span Sep 2016 to Oct 2018, with sparse months at the ends | Known behaviour | **Verified** | 2016-09-04 to 2018-10-17; see DEC-017 |
| A-09 | Some products have no category; some categories lack a translation | Known behaviour | **Verified** | 610 products with no category; 2 untranslated categories |
| A-10 | 8 order_status values | Known behaviour | **Verified** | delivered 96,478; shipped 1,107; canceled 625; unavailable 609; invoiced 314; processing 301; created 5; approved 2 |
| A-11 | Some delivered orders have a NULL delivery date | Known behaviour | **Verified** | 8 such orders |
| A-12 | `payment_type` includes `not_defined` | Known behaviour | **Verified** | 3 rows, all with value 0 |
| A-13 | The Olist licence is CC BY-NC-SA 4.0 | Kaggle page | Unverified: check on the Kaggle page before submission | |
| A-14 | Monetary values are in BRL | Dataset description | Assumed | |

## Open questions (Q-NN)
| ID | Question | Who decides | Status |
|----|----------|-------------|--------|
| Q-01 | Third member's name; Kashish's role (M1 or M3); student IDs | Team | **Open**: placeholders are used in all PDFs |
| Q-02 | One combined PDF or separate files? | Team / instructor | Resolved by DEC-024: separate files (confirm with instructor if unsure) |
| Q-03 | Should revenue exclude canceled/unavailable orders? | M2 + M3 | Resolved by DEC-016 |
| Q-04 | Should sparse edge months be excluded from trends? | M2 | Resolved by DEC-017 |
| Q-05 | Is a cover template mandated (IDs, section)? | Team | **Open**: placeholder cover used (DEC-024) |

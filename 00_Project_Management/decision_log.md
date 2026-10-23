# Decision Log (Judgment Calls)

Status values: **Proposed**, Accepted, Rejected, Superseded. Process and format rules are in `SOP.md` §3.

DEC-005 to DEC-014 were proposed on 2026-10-24 before the dataset was available. The same day they were **re-checked against the downloaded CSVs** (`02_Data/profiling/profiling_report.md`) and resolved as recorded under each entry. The single source of truth for the final model is `01_Project_Documentation/phase1/build/model_spec.py`.

---

### DEC-001: Repository folder structure
- **Date:** 2026-10-24 | **Proposed by:** Claude (for Kashish) | **Status:** Accepted (directed by Kashish)
- **Context:** The course overview PDF suggests a repository layout (`01_Project_Documentation` … `06_Dashboard`). The team also wants a dedicated folder for logs, SOPs, and work division.
- **Decision:** Adopt the course-suggested numbered folders and add `00_Project_Management/`. The official PDFs stay unchanged in `docs/project_deliverables/`.
- **Rationale:** Matching the structure the marker expects makes the repository easier to grade.
- **Approved by:** Kashish, 2026-10-24 (instruction in session)

### DEC-002: AI assistant never commits; personal branches
- **Date:** 2026-10-24 | **Proposed by:** Kashish | **Status:** Accepted
- **Decision:** Claude edits files only, on branch `kashish-phase1`. Kashish makes all commits and pushes.
- **Approved by:** Kashish, 2026-10-24

### DEC-003: Local `CLAUDE.md` is git-ignored
- **Date:** 2026-10-24 | **Proposed by:** Kashish | **Status:** Accepted
- **Decision:** `CLAUDE.md` holds the assistant's working context. It is listed in `.gitignore` and is never pushed.
- **Approved by:** Kashish, 2026-10-24

### DEC-004: Raw Kaggle data is not committed
- **Date:** 2026-10-24 | **Proposed by:** Claude | **Status:** Accepted (by Claude under Kashish's delegated approval, 2026-10-24; team confirms at walk-through P1-12)
- **Context:** The raw files total roughly 120 MB uncompressed, and the dataset licence (shown on Kaggle as CC BY-NC-SA 4.0; verify on the page) requires attribution.
- **Options:** A) Commit the CSVs. B) Ignore `02_Data/raw_data/` and document the download steps.
- **Decision:** B.
- **Rationale:** This keeps the repository small, avoids redistributing the data, and remains reproducible through `02_Data/README.md`.
- **Resolution:** Verified. The 9 CSVs total 126 MB and `git status` does not list them.

---

## Dimensional design (preliminary, pending data verification)

### DEC-005: Use a star schema, not a snowflake
- **Status:** Accepted (by Claude under Kashish's delegated approval, 2026-10-24; team confirms at walk-through P1-12)
- **Context:** The hierarchies are shallow: Region > State > City for geography, and Category > Product for products. The category translation table is a 1:1 lookup. Power BI works best with star schemas.
- **Options:** A) Star with denormalised dimensions. B) Snowflake, splitting out `dim_category` and `dim_geography`.
- **Decision:** A. Fold the category translation into `dim_product`. Store geography attributes directly in `dim_customer` and `dim_seller`.
- **Rationale:** Fewer joins, simpler filtering in Power BI, and no real storage saving from normalising these small attribute sets.
- **Consequences:** `dim_location` and `dim_category` are not separate tables. The geolocation CSV is used only to derive optional latitude and longitude per zip prefix.
- **Resolution:** Accepted. The only multi-level hierarchies are geography (Region > State > City > Zip) and Category > Product, and the translation table has 71 rows. Geolocation (1,000,163 rows, 261,831 duplicates, outliers) is used only to derive median coordinates per zip prefix.

### DEC-006: Four fact tables, one per business process
- **Status:** Accepted (by Claude under Kashish's delegated approval, 2026-10-24; team confirms at walk-through P1-12)
- **Decision:**
  - `fact_order_items`: transaction fact. Grain: one row per product line in an order (`order_id` + `order_item_id`).
  - `fact_orders`: accumulating snapshot. Grain: one row per order (`order_id`).
  - `fact_payments`: transaction fact. Grain: one row per payment record of an order (`order_id` + `payment_sequential`).
  - `fact_reviews`: transaction fact. Grain: one row per review submitted for an order (`review_id` + `order_id`).
- **Rationale:** Orders, items, payments, and reviews have different cardinalities per order. Storing them in one table would multiply amounts. Separate facts linked by conformed dimensions prevent this.
- **Rejected alternative:** A single flattened sales table. Joining items to payments repeats `payment_value` once per item, and repeats `price` once per payment.
- **Resolution:** Accepted. All four grains are verified unique (0 duplicate keys). Per order, there are up to 21 items, 29 payments and 3 reviews. A naive items x payments join gives 117,601 rows and inflates SUM(payment_value) by BRL 4,299,262.59. Each fact answers at least one business question: order_items BQ-01/02/04/13; orders BQ-01/03/07/08/09/11/12; payments BQ-05/06; reviews BQ-10.

### DEC-007: Customer natural key is `customer_unique_id`, not `customer_id`
- **Status:** Accepted (by Claude under Kashish's delegated approval, 2026-10-24; team confirms at walk-through P1-12)
- **Context:** In the Olist data, `customer_id` is issued once per order. `customer_unique_id` identifies the person.
- **Decision:** `dim_customer` has one row per `customer_unique_id`. The staging layer maps `customer_id` to `customer_unique_id` to find `customer_key`.
- **Rationale:** Repeat-purchase and lifetime-value questions are impossible to answer if each order produces a new customer.
- **Consequence:** The customer address is taken from the customer's most recent order (SCD Type 1). Address changes are not tracked.
- **Resolution:** Accepted. There are 99,441 customer_id values but 96,096 customer_unique_id values, and 2,997 persons are repeat buyers. Only 250 persons have more than one zip prefix (39 more than one state), so SCD Type 1 is adequate.

### DEC-008: Reject `dim_review` and `dim_location` as separate dimensions
- **Status:** Accepted (by Claude under Kashish's delegated approval, 2026-10-24; team confirms at walk-through P1-12)
- **Rationale:** Review text is free-form Portuguese with near 1:1 cardinality to reviews, so it does not work as a dimension. It is kept out of the warehouse, and only a `has_comment` flag is stored. Location is folded into the customer and seller dimensions (DEC-005).
- **Resolution:** Accepted. Comment messages are present on 41.3% of reviews and titles on 11.7%; both are free text. They are replaced by `has_comment_title` and `has_comment_message` flags in fact_reviews.

### DEC-009: Small dimensions `dim_payment_type` and `dim_order_status` are kept
- **Status:** Accepted (by Claude under Kashish's delegated approval, 2026-10-24; team confirms at walk-through P1-12)
- **Rationale:** They provide clean slicers and descriptive groupings, such as `status_group` = Completed / In progress / Cancelled. These attributes do not exist in the source data.
- **Resolution:** Accepted. Verified values: 8 statuses and 5 payment types (including `not_defined`, 3 rows). status_group: Delivered = delivered; Cancelled = canceled, unavailable; In progress = created, approved, invoiced, processing, shipped.

### DEC-010: Role-playing `dim_date`
- **Status:** Accepted (by Claude under Kashish's delegated approval, 2026-10-24; team confirms at walk-through P1-12)
- **Decision:** One `dim_date` table with key format `YYYYMMDD`. `fact_orders` references it five times: purchase, approved, delivered to carrier, delivered to customer, and estimated delivery. A missing date uses key `-1` ("Not yet occurred / Unknown").
- **Note:** Time of day is lost in `date_key`. If needed, `purchase_hour` is stored as a degenerate attribute in `fact_orders`.
- **Resolution:** Accepted with a refinement. The dim_date range is 2016-01-01 to 2018-12-31, which covers the latest estimated delivery date (2018-11-12). Roles: fact_orders 5, fact_order_items 2 (purchase, shipping limit), fact_payments 1 (purchase; the source has no payment date), fact_reviews 2 (creation, answer). `purchase_hour` is kept as a degenerate attribute.

### DEC-011: Measure definitions (no interchangeable use)
- **Status:** Accepted (by Claude under Kashish's delegated approval, 2026-10-24; team confirms at walk-through P1-12)
- **Definitions:**
  - Item sales revenue = `SUM(fact_order_items.item_price)`
  - Freight revenue = `SUM(freight_value)`
  - Gross order value = item price + freight
  - Amount paid = `SUM(fact_payments.payment_value)`. This is not called "sales revenue", because it can include voucher splits and differ slightly from item price + freight.
  - Order count = `COUNT(DISTINCT order_id)`, or row count of `fact_orders`
  - Units sold = row count of `fact_order_items`, because each row is one unit
- **Open:** Whether canceled and unavailable orders are excluded from revenue KPIs (see Q-03).
- **Resolution:** Accepted. Source totals: SUM(price) = 13,591,643.70, SUM(freight) = 2,251,909.54, SUM(payment_value) = 16,008,872.12. Payment equals price + freight within BRL 0.01 for 99.69% of orders, which confirms the measures differ and must stay separate. Q-03 is resolved by DEC-016.

### DEC-012: Delivery performance measures live in `fact_orders`
- **Status:** Accepted (by Claude under Kashish's delegated approval, 2026-10-24; team confirms at walk-through P1-12)
- **Decision:** `fact_orders` stores pre-computed lag measures:
  - `days_purchase_to_approval`
  - `days_approval_to_carrier`
  - `days_carrier_to_customer`
  - `days_purchase_to_delivery`
  - `delivery_delay_days` = actual delivery date − estimated delivery date
  - `is_late` flag
  - `is_delivered` flag

  Lags are NULL when the stage has not occurred.
- **Resolution:** Accepted with a refinement. `is_late` = delivered date (date part) > estimated date. The estimated date never has a time component. `is_delivered` = status 'delivered' AND a delivery date exists (96,470 orders). Flags are stored as SMALLINT 0/1 so they are additive. `days_promised` was added. 1,359 orders with carrier date < approval date are flagged, not deleted (DEC-023).

### DEC-013: Review score is carried onto `fact_orders` for the delivery-versus-review question
- **Status:** Accepted (by Claude under Kashish's delegated approval, 2026-10-24; team confirms at walk-through P1-12)
- **Context:** Joining `fact_reviews` directly to `fact_orders` is a fact-to-fact join, which the supervisor advised against. Some orders have more than one review.
- **Options:** A) Drill across through `order_id` in SQL. B) Store `avg_review_score` and `review_count` on `fact_orders` during ETL.
- **Decision:** B. `fact_reviews` remains the detailed fact for review-level analysis.
- **Rationale:** This allows a safe order-level analysis of lateness against score with no join risk in Power BI.
- **Resolution:** Accepted. 547 orders have more than one review, and in 202 of them the scores differ, so `avg_review_score` is the mean, with `review_count`. 768 orders have no review (NULL score).

### DEC-014: Unknown-member rows in each dimension
- **Status:** Accepted (by Claude under Kashish's delegated approval, 2026-10-24; team confirms at walk-through P1-12)
- **Decision:** Every dimension has a row with surrogate key `-1` ("Unknown"). Fact rows with a missing or unmatched business key point to it, so foreign keys are never NULL. Example: products with no category get category "unknown".
- **Resolution:** Accepted. Real cases: 610 products with no category, 2 untranslated categories, 1 order with no payment, and NULL milestone dates (date key -1).

### DEC-015: Phase 1 production approach
- **Status:** Accepted (by Claude under Kashish's delegated approval, 2026-10-24; team confirms at walk-through P1-12)
- **Decision:** Claude drafts all seven Phase 1 deliverables. Each member reviews the part matching their role, so all three can defend the model (see `work_division/task_board.md`).
- **Rationale:** The deadline is 2026-10-25. Splitting writing work three ways would cost more time in integration and consistency checks than it saves.
- **Resolution:** Accepted (Kashish approved the plan on 2026-10-24). All 7 deliverables were generated from one specification; review tasks are assigned in `work_division/task_board.md`.

---

## Decisions added during Phase 1 completion (2026-10-24)

### DEC-016: Revenue KPIs exclude the Cancelled status group (resolves Q-03)
- **Date:** 2026-10-24 | **Proposed by:** Claude | **Status:** Accepted (by Claude under Kashish's delegated approval, 2026-10-24; team confirms at walk-through P1-12)
- **Context:** Cancelled and unavailable orders hold 549 item lines worth BRL 97,242.96 (0.7% of item value).
- **Decision:** Fact tables keep all rows. Revenue KPIs filter `status_group <> 'Cancelled'` through dim_order_status, and the cancellation rate is reported separately (BQ-07).
- **Rationale:** No rows are deleted, so reconciliation with the source stays exact, and the KPI definitions are explicit.

### DEC-017: Trend window January 2017 to August 2018 (resolves Q-04)
- **Status:** Accepted (by Claude under Kashish's delegated approval, 2026-10-24; team confirms at walk-through P1-12)
- **Context:** Orders per month: 2016-09: 4, 2016-10: 324, 2016-11: 0, 2016-12: 1, 2018-09: 16, 2018-10: 4. Every other month has 800 to 7,544 orders.
- **Decision:** All rows are loaded. Month-over-month growth and trend charts use Jan 2017 to Aug 2018 only.

### DEC-018: Derived geography attributes (state name, IBGE macro-region)
- **Status:** Accepted (by Claude under Kashish's delegated approval, 2026-10-24; team confirms at walk-through P1-12)
- **Decision:** dim_customer and dim_seller get `*_state_name` and `*_region` from a fixed 27-state lookup (Lookup_Values sheet).
- **Rationale:** Supports the Region > State > City hierarchy and ROLLUP in Phase 3. The values are not in the source but are official and deterministic.

### DEC-019: Coordinates are the median per zip prefix inside Brazil's bounding box
- **Status:** Accepted (by Claude under Kashish's delegated approval, 2026-10-24; team confirms at walk-through P1-12)
- **Context:** Geolocation has 1,000,163 rows for 19,015 prefixes, and some coordinates lie outside Brazil (lat up to 45, lng up to 121). 278 customer rows and 7 seller rows have prefixes not found in geolocation.
- **Decision:** Keep lat -34..6 and lng -74..-34, then take the median per prefix. Missing prefixes get NULL coordinates. The coordinates are optional map attributes, not keys.

### DEC-020: Category gaps
- **Status:** Accepted (by Claude under Kashish's delegated approval, 2026-10-24; team confirms at walk-through P1-12)
- **Decision:** A NULL category becomes `sem_categoria` / `uncategorized`. The two untranslated names are mapped manually: `pc_gamer` -> `pc_gamer`, and `portateis_cozinha_e_preparadores_de_alimentos` -> `portable_kitchen_food_preparers`.

### DEC-021: payment_installments = 0 is treated as 1
- **Status:** Accepted (by Claude under Kashish's delegated approval, 2026-10-24; team confirms at walk-through P1-12)
- **Context:** 2 rows have 0 instalments, while valid values are 1 to 24.
- **Decision:** Map 0 to 1 in staging and record the change in the Phase 2 data-cleaning report.

### DEC-022: Customer order sequence on fact_orders
- **Status:** Accepted (by Claude under Kashish's delegated approval, 2026-10-24; team confirms at walk-through P1-12)
- **Decision:** `customer_order_number` is ROW_NUMBER over customer_unique_id ordered by purchase timestamp, and `is_repeat_purchase` = customer_order_number > 1. Together they answer BQ-12 without a fact-to-fact join.

### DEC-023: Out-of-sequence timestamps are flagged, not deleted
- **Status:** Accepted (by Claude under Kashish's delegated approval, 2026-10-24; team confirms at walk-through P1-12)
- **Context:** 1,359 orders have carrier date < approval date, and 23 have delivered date < carrier date.
- **Decision:** Keep the rows and compute the lags as-is. The Phase 2 data-quality report lists them, and stage averages exclude negative lags (TR-13).

### DEC-024: Phase 1 document format and administrative placeholders (resolves Q-02, Q-05)
- **Status:** Accepted (by Claude under Kashish's delegated approval, 2026-10-24; team confirms at walk-through P1-12)
- **Decision:** The course lists seven deliverables, so they are produced as seven separate files, P1_01 to P1_07. Student names, IDs, section and instructor are shown as `[placeholders]`. Khadija is shown only as the *proposed* Member 2 and the team must fill in the rest before submission. All files are generated from `build/model_spec.py` so they stay consistent.

---

## Phase 1 finalisation and CI (2026-10-24, session 3)

### DEC-025: GitHub Actions CI with content-based rebuild check
- **Date:** 2026-10-24 | **Proposed by:** Claude | **Status:** Accepted (task requested by Kashish)
- **Context:** The deliverables are generated files. CI must prove they are valid and up to date without the raw Olist CSVs, which are git-ignored.
- **Decision:**
  - `.github/workflows/phase1-ci.yml` runs on push, pull_request and workflow_dispatch, on Ubuntu 24.04 with Python 3.12.
  - It installs the pinned `requirements.txt` (reportlab, openpyxl, pymupdf).
  - It runs `validate_phase1.py` and then `python -m unittest discover -s tests`. The tests use the standard library only, so there is no pytest dependency.
- **Rebuild check:** `tests/test_rebuild.py` rebuilds into a temporary folder and compares page text, workbook cell values, DBML text and image sizes with the committed files. It compares content, not bytes, because CI uses the font Carlito instead of Calibri.
  - Carlito has the same character widths as Calibri, so line breaks match. Local test with Carlito forced: identical page text.
  - Builds are byte-identical on one machine: reportlab invariant mode, plus fixed xlsx metadata and zip timestamps.
- **Evidence the test works:** changing one description in `model_spec.py` without rebuilding made 3 rebuild tests fail. Restoring the file made them pass again.

### DEC-026: Team details on covers
- **Status:** Accepted (details supplied by Kashish on 2026-10-24)
- **Decision:** The covers list each member's name and roll number, plus Section BDS5A and Instructor Esha Tur Razia Babar:
  - Kashish Fatima, 24L-2605
  - Khadija Faiz, 24L-2554
  - Aliyah Rasheed, 24L-2544

  The details are stored once in `build/doc_common.py` (`TEAM`, `SECTION`, `INSTRUCTOR`).
- **Notes:**
  - The task brief gave "24L-2544" for both Khadija and Aliya. Kashish's own message gave distinct numbers, and those were used. Tests now fail on duplicate or malformed roll numbers.
  - Spellings follow Kashish's message: "Aliyah Rasheed" (the brief had "Aliya Rashid"). "Khadija Faiz" keeps the established spelling "Khadija" (the message typed "kadija"). Members should confirm spellings.
  - Role leads (M1/M3) are not yet assigned, so the covers list members without roles.

### DEC-027: `is_late` and `delivery_delay_days` are defined only when `is_delivered = 1`
- **Status:** Accepted
- **Context:** 6 orders not in status `delivered` still have a delivery timestamp. The previous wording, "NULL if not delivered", was ambiguous for these orders.
- **Decision:** Both measures are NULL whenever `is_delivered = 0`. The data dictionary rule was updated and the artifacts rebuilt.

### DEC-028: Generated PDFs, PNGs and XLSX files are marked `binary` in `.gitattributes`
- **Status:** Accepted
- **Context:** `* text=auto` made git treat the ASCII-only `P1_06_Star_Schema.pdf` as text ("LF will be replaced by CRLF"). A Windows checkout would then rewrite its line endings, which breaks the PDF's xref byte offsets. A CRLF copy was tested and pymupdf reported it as repaired.
- **Decision:** Add `*.pdf binary`, `*.png binary` and `*.xlsx binary`. `tests/test_deliverables.py` now fails if any committed PDF needs repair when opened.

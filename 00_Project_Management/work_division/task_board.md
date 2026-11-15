# Task Board

**Roles:**
- **M1:** Warehouse & integration lead
- **M2:** Business analysis & modeling lead
- **M3:** Analytics & BI lead

**Team:** Kashish Fatima (24L-2605), Khadija Faiz (24L-2554), Aliyah Rasheed (24L-2544).

**Role leads (DEC-029):** M1 = Kashish Fatima, M2 = Khadija Faiz, M3 = Aliyah Rasheed.

Status values: Todo, In progress, Review, Done.

## Phase 1 (due 2026-10-25)

All seven deliverables were drafted from one model specification (DEC-015, DEC-024), so their names and keys match. Each member now has a **focused review** of the documents in their area. Every member must be able to explain the whole model.

| ID | Task | Drafter | Owner (reviewer) | Est. | Depends on | Deliverable | Status |
|----|------|---------|------------------|------|-----------|-------------|--------|
| P1-01 | Download the Kaggle dataset into `02_Data/raw_data/` | Claude (kagglehub) | Kashish | 10 min | — | 9 CSVs present locally | Done |
| P1-02 | Read-only data profiling | Claude | M1 | 30 min | P1-01 | `02_Data/profiling/profiling_report.md` | Done; review pending |
| P1-03 | Resolve design decisions DEC-004 to DEC-015 (+ DEC-016 to DEC-024) | Claude | M2 | 20 min | P1-02 | `decision_log.md` | Done; team confirmation at P1-12 |
| P1-04 | Project Proposal | Claude | M2 | — | P1-03 | `P1_01_Project_Proposal.pdf` | Review |
| P1-05 | Business Requirements Document | Claude | M2 | — | P1-03 | `P1_02_Business_Requirements.pdf` | Review |
| P1-06 | Business Questions (13) | Claude | M3 | — | P1-03 | `P1_03_Business_Questions.pdf` | Review |
| P1-07 | Fact & Dimension Identification | Claude | M2 | — | P1-03 | `P1_04_Fact_Dimension_Identification.pdf` | Review |
| P1-08 | Grain Definition Document | Claude | M1 | — | P1-03 | `P1_05_Grain_Definition.pdf` | Review |
| P1-09 | Star schema diagram | Claude | M1 | — | P1-07 | `P1_06_Star_Schema.pdf/.png/.dbml` | Review |
| P1-10 | Data Dictionary | Claude | M1 | — | P1-07 | `P1_07_Data_Dictionary.xlsx` | Review |
| P1-11 | Automated consistency validation (269 checks) | Claude | M3 | — | P1-04 to P1-10 | `build/validation_report.md` | Done (0 failures) |
| P1-12 | Team walk-through: each member explains the model in 5 minutes | All | All | 30 min | P1-11 | Daily log note | Todo |
| P1-13 | Fill in names, IDs and section in `build/doc_common.py`; rebuild | Claude | Kashish | — | — | Rebuilt PDFs and xlsx | Done |
| P1-14 | GitHub Actions CI (validation + unit, structure and rebuild tests) | Claude | M3 | — | P1-13 | `.github/workflows/phase1-ci.yml`, `tests/` | Done locally; remote run pending push |
| P1-15 | Commit, push, open PR, confirm CI is green, merge, submit | Kashish | Kashish | 15 min | P1-14 | PR to `main` + submission | Todo |

## Phase 1 review assignments (about 45 minutes each)

| Reviewer | Scope | What to check |
|----------|-------|---------------|
| **M2** (Business analysis & modeling) | P1_01, P1_02, P1_04 | Business problem and objectives are clear. Every stakeholder need maps to a BR-xx requirement. KPI definitions make sense. Fact and dimension choices and rejected candidates are justified. You can explain why star was chosen over snowflake. |
| **M3** (Analytics & BI) | P1_03, plus the Business_Questions and Measures sheets of P1_07 | Each BQ can be answered with the listed fact, measures and dimensions. Filters and limitations are honest. You could sketch the Power BI visual for each BQ. No question implies causation. |
| **M1** (Warehouse & integration) | P1_05, P1_06, P1_07 (Columns, Relationships, Transformation_Rules), profiling report | Grain statements match the uniqueness keys. Data types are sensible for PostgreSQL. FKs and the unknown-member rule are correct. The diagram matches the dictionary. Reconciliation targets are correct. |

Record review comments in the daily log. To change the model, edit `build/model_spec.py` and rebuild (see `01_Project_Documentation/phase1/build/README.md`). Do not edit the generated PDFs or the xlsx directly.

## Phase 2 (due week of 2026-11-03, Q-06)

Plan, contract and checklist: `01_Project_Documentation/phase2/README.md`. Reviews rotate (M1 -> M2 -> M3 -> M1).

| ID | Task | Owner | Reviewer | Est. | Depends on | Deliverable | Status |
|----|------|-------|----------|------|-----------|-------------|--------|
| P2-01 | Phase 2 plan, division, hand-off contract | M1 (Claude for Kashish) | All | 1 h | - | `phase2/README.md` | Done 2026-10-27 |
| P2-02 | Database and schemas SQL | M1 | M3 | 1 h | P2-01 | `04_Data_Warehouse/database.sql`, `schemas.sql` | Done 2026-10-27 |
| P2-03 | Staging DDL + CSV loader with reconciliation | M1 | M3 | 2 h | P2-02 | `03_ETL/staging/` | Done 2026-10-27 (9/9 files reconciled) |
| P2-04 | Warehouse DDL generated from model_spec | M1 | M3 | 2 h | P2-02 | `04_Data_Warehouse/warehouse.sql` | Done 2026-10-27 (87/87 structure checks) |
| P2-05 | Pipeline runner, run log, reports | M1 | M3 | 2 h | P2-03 | `03_ETL/run_pipeline.py` | Done 2026-10-27 |
| P2-06 | Phase 2 tests and CI (PostgreSQL service) | M1 | M3 | 1.5 h | P2-04 | `tests/test_phase2_*.py`, `.github/workflows/phase2-ci.yml` | Done locally; remote CI pending push |
| P2-07 | M1 implementation report | M1 | M3 | 0.5 h | P2-05 | `phase2/P2_M1_Database_Implementation_Report.md` | Done 2026-10-27 |
| P2-08 | Cleaning scripts `stg_*` -> `cln_*` (TR-01 to TR-15) | M2 | M1 | 4 h | P2-03 | `03_ETL/cleaning/` | Todo |
| P2-09 | Dimension loads with surrogate keys and -1 members | M2 | M1 | 3 h | P2-08 | `03_ETL/dimensions/` | Todo |
| P2-10 | Data Cleaning Report PDF | M2 | M1 | 2 h | P2-08 | `phase2/P2_02_Data_Cleaning_Report.pdf` | Todo |
| P2-11 | Fact loads (BK -> SK lookups, per-order aggregates) | M3 | M2 | 4 h | P2-09, contract DEC-033 | `03_ETL/facts/` | Todo |
| P2-12 | Quality checks (completeness, accuracy, integrity) | M3 | M2 | 3 h | P2-11 | `03_ETL/quality/` | Todo |
| P2-13 | Data Quality Report PDF | M3 | M2 | 2 h | P2-12 | `phase2/P2_03_Data_Quality_Report.pdf` | Todo |
| P2-14 | Accept or revise Proposed DEC-031 to DEC-035 | M2, M3 | - | 0.5 h | - | `decision_log.md` | Todo |
| P2-15 | Final integration run `run_pipeline.py --strict`, then commit, push, PR, green CI | M1 (Kashish) | All | 1 h | P2-08 to P2-13 | PR to `main`, repository link | Todo |

## Phase 3 (planning only, not started)
See `roles.md`. Do not start before the Phase 2 submission.

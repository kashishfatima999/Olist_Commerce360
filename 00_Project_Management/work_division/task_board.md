# Task Board

**Roles:**
- **M1:** Warehouse & integration lead
- **M2:** Business analysis & modeling lead (suggested: Khadija)
- **M3:** Analytics & BI lead

**Team:** Kashish Fatima (24L-2605), Khadija Faiz (24L-2554), Aliyah Rasheed (24L-2544).

Khadija is the proposed M2. The team still needs to assign M1 and M3 between Kashish and Aliyah (Q-01).

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

## Phase 2 / Phase 3 (planning only, not started)
See `roles.md`. Do not start before the Phase 1 submission.

# Phase 1 Deliverables and Final Checklist

Source of requirements: `docs/project_deliverables/DWBI Lab Phase 1.pdf`.

| Rubric criterion | Marks |
|---|---|
| Business Understanding | 5 |
| Requirement Analysis | 5 |
| Fact/Dimension Identification | 10 |
| Schema Design | 10 |
| **Total** | **30** |

All files are generated from `build/model_spec.py` (see `build/README.md`). Automated validation is in `build/validation_report.md`: 252 checks, 0 failures, as of 2026-10-24.

## 1. Deliverables

| # | Official deliverable | File | Pages / sheets | Rubric area |
|---|---|---|---|---|
| 1 | Project Proposal PDF | `P1_01_Project_Proposal.pdf` | 4 pages | Business Understanding |
| 2 | Business Requirements Document PDF | `P1_02_Business_Requirements.pdf` | 5 pages | Requirement Analysis |
| 3 | 10 Business Questions PDF | `P1_03_Business_Questions.pdf` | 5 pages, 13 questions | Requirement Analysis |
| 4 | Fact & Dimension Identification PDF | `P1_04_Fact_Dimension_Identification.pdf` | 8 pages | Fact/Dimension Identification |
| 5 | Grain Definition Document PDF | `P1_05_Grain_Definition.pdf` | 4 pages | Fact/Dimension Identification |
| 6 | Star/Snowflake Schema Diagram PNG/PDF | `P1_06_Star_Schema.pdf` (page 1 physical, page 2 conceptual and bus matrix), `P1_06_Star_Schema.png`, `P1_06_Conceptual_Model.png`, `P1_06_Star_Schema.dbml` (dbdiagram.io source) | 2 pages, A2 | Schema Design |
| 7 | Data Dictionary Excel | `P1_07_Data_Dictionary.xlsx` | 11 sheets, 109 columns described | Schema Design |

## 2. Requirement checklist

| Requirement (Phase 1 PDF) | Where | Validation | Remaining limitation |
|---|---|---|---|
| Business problem / domain | P1_01 §1-2 | Manual review | — |
| Business processes identified | P1_02 §3, P1_04 §2 | Validator: 4 processes map to 4 facts | — |
| Minimum 10 analytical questions | P1_03 (13 questions) | Validator: each question maps to an existing fact, measure, dimension and BR | Findings are deferred to Phase 3, by design |
| Grain statements | P1_05 §2 (verbatim), P1_06, P1_07 Tables | Validator: identical in the PDF, diagram and xlsx; uniqueness verified in source data | — |
| Fact table types chosen | P1_04 §2, §4 | Manual review | No periodic snapshot or factless fact; the data does not support them (documented in P1_04 §3) |
| Dimensions and hierarchies | P1_04 §6, P1_07 Hierarchies | Validator: every dimension has a PK and NK and is used by a fact | — |
| Natural and surrogate keys | P1_04 §9, P1_07 Columns | Validator: FK types match PK types; no nullable FKs | — |
| Star or snowflake schema with justification | P1_04 §11, P1_06 | Manual review | — |
| Conceptual model | P1_06 page 2, P1_04 Figure 1 | Visual check | — |
| Logical model | P1_04 §10 | Validator: all tables present | — |
| Physical model (PK, FK, attributes, measures, grain) | P1_06 page 1, P1_07 | Validator: every dictionary column appears in the diagram | Physical DDL is Phase 2 work |
| Data Dictionary Excel | P1_07 | Validator: required sheets present; columns, types and roles identical to the model | — |
| Documents consistent with each other | All | Validator: table names, grains, relationships and DBML refs | — |
| No unsupported claims (profit, inventory, promotions, results) | P1_01 §4, P1_03 §5 | Validator: forbidden-phrase scan; manual review | — |

## 3. Before submission (manual)
- [ ] Replace the cover placeholders (names, student IDs, section, instructor) in `build/doc_common.py` → `TEAM_ROWS`, then rebuild.
- [ ] Each member completes the focused review in `00_Project_Management/work_division/task_board.md`.
- [ ] Confirm the dataset licence wording on the Kaggle page (A-13).
- [ ] Confirm with the instructor whether a single combined PDF is preferred (DEC-024).
- [ ] Open every file once on the submitting computer.

# Olist Commerce360

[![Phase 1 CI](https://github.com/kashishfatima999/Olist_Commerce360/actions/workflows/phase1-ci.yml/badge.svg)](https://github.com/kashishfatima999/Olist_Commerce360/actions/workflows/phase1-ci.yml)
[![Phase 2 CI](https://github.com/kashishfatima999/Olist_Commerce360/actions/workflows/phase2-ci.yml/badge.svg)](https://github.com/kashishfatima999/Olist_Commerce360/actions/workflows/phase2-ci.yml)

**An End-to-End E-Commerce Data Warehouse and Business Intelligence Platform.** This is the project for DL3004 Data Warehousing and Business Intelligence, Section BDS5A. The instructor is Esha Tur Razia Babar.

| Team member | Roll number | Role |
|---|---|---|
| Kashish Fatima | 24L-2605 | M1: Warehouse and integration lead |
| Khadija Faiz | 24L-2554 | M2: Business analysis and modelling lead |
| Aliyah Rasheed | 24L-2544 | M3: Analytics and BI lead |

The project builds a dimensional data warehouse in PostgreSQL and a Power BI dashboard on the public Brazilian E-Commerce Dataset by Olist (Kaggle `olistbr/brazilian-ecommerce`). The data covers about 99k orders placed between 2016 and 2018.

## Status
| Phase | Weight | Status |
|---|---|---|
| 1. Business analysis & dimensional design | 30% | Deliverables complete in `01_Project_Documentation/phase1/` and validated by CI |
| 2. Physical data warehouse & ETL | 40% | In progress. M1 part done (database, staging, warehouse DDL, pipeline); M2 and M3 to do. See `01_Project_Documentation/phase2/README.md` |
| 3. OLAP, optimisation & BI dashboard | 30% | Not started |

## Repository layout
| Path | Contents |
|---|---|
| `00_Project_Management/` | SOP, decision log, daily logs, assumptions/questions, task board |
| `01_Project_Documentation/phase1/` | Phase 1 deliverables P1_01 to P1_07 and the `build/` scripts that generate them |
| `01_Project_Documentation/phase2/` | Phase 2 plan and work division, hand-off contract, reports |
| `03_ETL/` | ETL pipeline: runner, staging loader, cleaning, dimension, fact and quality scripts |
| `04_Data_Warehouse/` | Database, schema and warehouse DDL, plus structure verification |
| `02_Data/` | Dataset download instructions and profiling. Raw CSVs are git-ignored |
| `docs/project_deliverables/` | Official course instructions |
| `tests/` | Unit, structure and rebuild-consistency tests |
| `.github/workflows/` | CI: `phase1-ci.yml` (documents) and `phase2-ci.yml` (schema build on a PostgreSQL 17 service). Both run on every push, every pull request and on manual dispatch |

## Build and test (Phase 1)
```
python -m pip install -r requirements.txt
cd 01_Project_Documentation/phase1/build
python build_data_dictionary.py
python build_schema_diagram.py
python build_documents.py
python validate_phase1.py
cd ../../..
python -m unittest discover -s tests -v
```
## Run the ETL pipeline (Phase 2)
Requirements:
- PostgreSQL 17 running locally.
- A password in `%APPDATA%\postgresql\pgpass.conf` (never in the repository).
- The raw CSVs in `02_Data/raw_data/`.

```
python 03_ETL/run_pipeline.py            # creates olist_commerce360, loads staging, builds and verifies the warehouse
```
Results are written to `03_ETL/run_reports/pipeline_run_latest.md` and `04_Data_Warehouse/verification_report.md`.

CI does not need the raw dataset. Profiling (`02_Data/profiling/profile_source.py`) runs locally after downloading the CSVs (see `02_Data/README.md`).

## Data licence
Data: Olist, published on Kaggle under the licence stated on the dataset page. The raw files are not redistributed in this repository.

# Olist Commerce360

[![Phase 1 CI](https://github.com/kashishfatima999/Olist_Commerce360/actions/workflows/phase1-ci.yml/badge.svg)](https://github.com/kashishfatima999/Olist_Commerce360/actions/workflows/phase1-ci.yml)

**An End-to-End E-Commerce Data Warehouse and Business Intelligence Platform.** This is the project for DL3004 Data Warehousing and Business Intelligence, Section BDS5A. The instructor is Esha Tur Razia Babar.

| Team member | Roll number |
|---|---|
| Kashish Fatima | 24L-2605 |
| Khadija Faiz | 24L-2554 |
| Aliyah Rasheed | 24L-2544 |

The project builds a dimensional data warehouse in PostgreSQL and a Power BI dashboard on the public Brazilian E-Commerce Dataset by Olist (Kaggle `olistbr/brazilian-ecommerce`). The data covers about 99k orders placed between 2016 and 2018.

## Status
| Phase | Weight | Status |
|---|---|---|
| 1. Business analysis & dimensional design | 30% | Deliverables complete in `01_Project_Documentation/phase1/` and validated by CI |
| 2. Physical data warehouse & ETL | 40% | Not started |
| 3. OLAP, optimisation & BI dashboard | 30% | Not started |

## Repository layout
| Path | Contents |
|---|---|
| `00_Project_Management/` | SOP, decision log, daily logs, assumptions/questions, task board |
| `01_Project_Documentation/phase1/` | Phase 1 deliverables P1_01 to P1_07 and the `build/` scripts that generate them |
| `02_Data/` | Dataset download instructions and profiling. Raw CSVs are git-ignored |
| `docs/project_deliverables/` | Official course instructions |
| `tests/` | Unit, structure and rebuild-consistency tests |
| `.github/workflows/phase1-ci.yml` | CI. It runs on every push, every pull request and on manual dispatch |

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
CI does not need the raw dataset. Profiling (`02_Data/profiling/profile_source.py`) runs locally after downloading the CSVs (see `02_Data/README.md`).

## Data licence
Data: Olist, published on Kaggle under the licence stated on the dataset page. The raw files are not redistributed in this repository.

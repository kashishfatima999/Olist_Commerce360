# Phase 1 build scripts

All Phase 1 deliverables are generated from one specification, `model_spec.py`. This keeps table names, columns, keys, grains and measures identical across the PDFs, the diagram and the Excel file.

| Script | Output |
|--------|--------|
| `model_spec.py` | Tables, columns, grains, KPIs, requirements, business questions |
| `build_data_dictionary.py` | `../P1_07_Data_Dictionary.xlsx` |
| `build_schema_diagram.py` | `../P1_06_Star_Schema.pdf`, `.png`, `.dbml`, and `../P1_06_Conceptual_Model.png` |
| `build_documents.py` | `../P1_01` to `../P1_05` PDFs. It embeds the conceptual PNG, so run the diagram script first |
| `validate_phase1.py` | `validation_report.md`, which checks that files open, layouts fit, and the documents match each other and the model |

## Rebuild
Run these commands from this folder:
```
python build_data_dictionary.py
python build_schema_diagram.py
python build_documents.py
python validate_phase1.py
```
Requirements: Python 3.10+, `reportlab`, `openpyxl`, `pymupdf`. The scripts use Calibri from `C:/Windows/Fonts` when it is available and fall back to Helvetica otherwise.

## Before submission
Replace the placeholders in `TEAM_ROWS` in `doc_common.py` (names, student IDs, section, instructor), then rebuild. To change the model, edit `model_spec.py` and log the change in `00_Project_Management/decision_log.md`. Never edit generated files by hand.

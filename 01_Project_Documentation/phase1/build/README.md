# Phase 1 build scripts

All Phase 1 deliverables are generated from one specification, `model_spec.py`. Team details come from `doc_common.py` (`TEAM`, `SECTION`, `INSTRUCTOR`). This keeps table names, columns, keys, grains, measures and cover details identical across the PDFs, the diagram and the Excel file.

| Script | Output |
|--------|--------|
| `model_spec.py` | Tables, columns, grains, KPIs, requirements, business questions |
| `doc_common.py` | PDF styles, team and cover details, font selection |
| `build_data_dictionary.py` | `../P1_07_Data_Dictionary.xlsx` |
| `build_schema_diagram.py` | `../P1_06_Star_Schema.pdf`, `.png`, `.dbml`, and `../P1_06_Conceptual_Model.png` |
| `build_documents.py` | `../P1_01` to `../P1_05` PDFs. It embeds the conceptual PNG, so run the diagram script first |
| `validate_phase1.py` | `validation_report.md`. It checks that files open and fit their pages, that the documents agree with each other and with the model, and that team details are complete (269 checks) |

## Rebuild
Run these from this folder, with dependencies from the repository root `requirements.txt`:
```
python build_data_dictionary.py
python build_schema_diagram.py
python build_documents.py
python validate_phase1.py
```
Then, from the repository root, run `python -m unittest discover -s tests -v`.

## Reproducibility
- Builds are byte-identical on the same machine. PDFs use reportlab's invariant mode, and the xlsx has fixed metadata and zip timestamps.
- **Fonts:** Windows uses Calibri. Linux CI uses Carlito, which has the same character widths as Calibri (package `fonts-crosextra-carlito`), so line breaks and page text are identical. To reproduce the CI font on Windows, set `PHASE1_FONT=Carlito` and `CARLITO_DIR=<folder with the Carlito TTFs>`.
- `PHASE1_OUTDIR=<folder>` writes all outputs to another folder. `tests/test_rebuild.py` uses this to rebuild into a temporary folder and compare the results with the committed files. CI fails if the committed artifacts are stale.

## Changing the model
Edit `model_spec.py` (or `doc_common.py` for team details), log the decision in `00_Project_Management/decision_log.md`, rebuild, and commit the regenerated files with the source change. Never edit generated files by hand.

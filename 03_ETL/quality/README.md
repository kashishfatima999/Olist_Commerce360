# 03_ETL/quality (owner: M3, Aliyah Rasheed)

This folder holds the data-quality checks: completeness, accuracy (revenue reconciliation) and integrity (orphan foreign keys = 0). A check must make the stage fail when it is violated, for example with `DO $$ BEGIN IF ... THEN RAISE EXCEPTION '...'; END IF; END $$;`.

Status: **not started** (pipeline stage `quality_checks`).

Reconciliation targets: `P1_05_Grain_Definition.pdf` §6 and `01_Project_Documentation/phase2/P2_M1_Database_Implementation_Report.md` §3.

"""Rebuild every Phase 1 artifact into a temporary folder and compare with the committed files.

Fails when someone edits model_spec.py / doc_common.py (or a build script) without rebuilding and
committing the outputs. Comparison is on content (PDF text per page, workbook cell values, DBML text,
image size) rather than bytes, because the CI font (Carlito) differs from Windows (Calibri) while being
metric-compatible, so layout and text are identical.
"""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import pymupdf

from phase1_helpers import BUILD, BUILD_SCRIPTS, PHASE1, pdf_pages_text, run_script, xlsx_values

PDFS = ["P1_01_Project_Proposal.pdf", "P1_02_Business_Requirements.pdf", "P1_03_Business_Questions.pdf",
        "P1_04_Fact_Dimension_Identification.pdf", "P1_05_Grain_Definition.pdf", "P1_06_Star_Schema.pdf"]


class TestRebuild(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls._tmp.name)
        env = dict(os.environ, PHASE1_OUTDIR=str(cls.out))
        cls.logs = {s: run_script(s, env) for s in BUILD_SCRIPTS}
        cls.validate = subprocess.run([sys.executable, str(BUILD / "validate_phase1.py")], cwd=BUILD, env=env,
                                      capture_output=True, text=True)

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_build_scripts_succeed(self):
        for s, r in self.logs.items():
            self.assertEqual(r.returncode, 0, f"{s}\n{r.stdout}\n{r.stderr}")

    def test_rebuilt_copy_passes_validation(self):
        self.assertEqual(self.validate.returncode, 0, self.validate.stdout + self.validate.stderr)

    def test_pdfs_match_committed(self):
        for f in PDFS:
            with self.subTest(f=f):
                new, old = pdf_pages_text(self.out / f), pdf_pages_text(PHASE1 / f)
                self.assertEqual(len(new), len(old), f"{f}: page count changed - rebuild and commit")
                for i, (a, b) in enumerate(zip(new, old), 1):
                    self.assertEqual(a, b, f"{f} page {i} differs from the committed file - rebuild and commit")

    def test_workbook_matches_committed(self):
        self.assertEqual(xlsx_values(self.out / "P1_07_Data_Dictionary.xlsx"),
                         xlsx_values(PHASE1 / "P1_07_Data_Dictionary.xlsx"))

    def test_dbml_matches_committed(self):
        self.assertEqual((self.out / "P1_06_Star_Schema.dbml").read_text(encoding="utf-8"),
                         (PHASE1 / "P1_06_Star_Schema.dbml").read_text(encoding="utf-8"))

    def test_png_sizes_match_committed(self):
        for f in ("P1_06_Star_Schema.png", "P1_06_Conceptual_Model.png"):
            a, b = pymupdf.Pixmap(str(self.out / f)), pymupdf.Pixmap(str(PHASE1 / f))
            self.assertEqual((a.width, a.height), (b.width, b.height), f)


if __name__ == "__main__":
    unittest.main()

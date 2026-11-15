"""Phase 2 (M1) static tests - no database or raw data needed."""
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "03_ETL"))
sys.path.insert(0, str(ROOT / "01_Project_Documentation" / "phase1" / "build"))
import etl_config as cfg  # noqa: E402
import model_spec as m  # noqa: E402

WAREHOUSE = (ROOT / "04_Data_Warehouse" / "warehouse.sql").read_text(encoding="utf-8")
STAGING = (ROOT / "03_ETL" / "staging" / "staging.sql").read_text(encoding="utf-8")


def create_blocks(sql, schema):
    """{table: [column names]} parsed from CREATE TABLE statements."""
    out = {}
    for name, body in re.findall(rf"CREATE TABLE {schema}\.(\w+) \((.*?)\n\);", sql, re.S):
        out[name] = [ln.split()[0] for ln in body.strip().splitlines() if not ln.strip().startswith("CONSTRAINT")]
    return out


class TestGeneratedSql(unittest.TestCase):
    def test_generated_sql_is_up_to_date(self):
        r = subprocess.run([sys.executable, str(ROOT / "03_ETL" / "build_sql.py"), "--check"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_warehouse_tables_and_columns_match_model(self):
        got = create_blocks(WAREHOUSE, "project_dw")
        want = {t["name"]: [c[0] for c in t["columns"]] for t in m.TABLES}
        self.assertEqual(got, want)

    def test_every_foreign_key_declared(self):
        for fact, fk, dim, pk, _ in m.relationships():
            self.assertIn(f"FOREIGN KEY ({fk}) REFERENCES project_dw.{dim} ({pk})", WAREHOUSE, f"{fact}.{fk}")

    def test_dimensions_created_before_facts_and_dropped_after(self):
        creates = [n for n in re.findall(r"CREATE TABLE project_dw\.(\w+)", WAREHOUSE)]
        self.assertTrue(all(n.startswith("dim_") for n in creates[:6]) and all(n.startswith("fact_") for n in creates[6:]))
        drops = re.findall(r"DROP TABLE IF EXISTS project_dw\.(\w+)", WAREHOUSE)
        self.assertTrue(all(n.startswith("fact_") for n in drops[:4]))

    def test_no_secondary_indexes_or_cascade(self):
        self.assertNotRegex(WAREHOUSE, r"(?i)CREATE\s+(UNIQUE\s+)?INDEX")  # Phase 3 before/after baseline
        code = "\n".join(ln for ln in WAREHOUSE.splitlines() if not ln.lstrip().startswith("--"))
        self.assertNotIn("CASCADE", code.upper())

    def test_surrogate_keys_are_identity(self):
        for t in m.DIMS:
            pk = next(c[0] for c in t["columns"] if c[2] == "PK")
            identity = re.search(rf"\n    {pk} \w+ GENERATED ALWAYS AS IDENTITY NOT NULL", WAREHOUSE)
            if t["name"] == "dim_date":
                self.assertIsNone(identity)
            else:
                self.assertIsNotNone(identity, t["name"])

    def test_staging_tables_match_source_contract(self):
        got = create_blocks(STAGING, "project_staging")
        want = {table: ["stg_row_id"] + cols for _f, table, _e, cols in cfg.SOURCES}
        self.assertEqual(got, want)
        self.assertEqual(len(re.findall(r"(?m)^    \w+ TEXT,?$", STAGING)), sum(len(c) for *_x, c in cfg.SOURCES))

    def test_expected_rows_match_phase1_profiling(self):
        prof = json.loads((ROOT / "02_Data" / "profiling" / "profiling_summary.json").read_text(encoding="utf-8"))
        key = {"olist_customers_dataset.csv": "customers", "olist_geolocation_dataset.csv": "geolocation",
               "olist_order_items_dataset.csv": "order_items", "olist_order_payments_dataset.csv": "payments",
               "olist_order_reviews_dataset.csv": "reviews", "olist_orders_dataset.csv": "orders",
               "olist_products_dataset.csv": "products", "olist_sellers_dataset.csv": "sellers",
               "product_category_name_translation.csv": "category_translation"}
        for file, _t, expected, _c in cfg.SOURCES:
            self.assertEqual(prof[key[file]]["rows"], expected, file)


class TestPipelineDefinition(unittest.TestCase):
    def test_stage_order_and_owners(self):
        text = (ROOT / "03_ETL" / "run_pipeline.py").read_text(encoding="utf-8")
        names = re.findall(r'\("(\w+)", "(M[123])", st_', text)
        self.assertEqual([n for n, _ in names][:8], ["create_database", "create_schemas", "create_etl_metadata",
                                                     "create_staging", "load_staging", "verify_staging",
                                                     "create_warehouse", "verify_warehouse"])
        self.assertEqual(dict(names)["clean_staging"], "M2")
        self.assertEqual(dict(names)["load_dimensions"], "M2")
        self.assertEqual(dict(names)["load_facts"], "M3")
        self.assertEqual(dict(names)["quality_checks"], "M3")

    def test_no_credentials_in_code(self):
        for p in list((ROOT / "03_ETL").rglob("*.py")) + list((ROOT / "03_ETL").rglob("*.sql")) + \
                list((ROOT / "04_Data_Warehouse").rglob("*.*")):
            text = p.read_text(encoding="utf-8", errors="ignore")
            self.assertNotRegex(text, r"(?i)password\s*=\s*['\"][^'\"]+['\"]", str(p))
        self.assertNotIn("password", cfg.conninfo().lower())


if __name__ == "__main__":
    unittest.main()

"""Phase 2 (M1) database integration tests.

Skipped unless OLIST_TEST_DB=1. They build a disposable database (OLIST_TEST_DB_NAME, default
olist_commerce360_test), never the project database, and drop it afterwards.
CI runs them against a PostgreSQL 17 service container; locally they use pgpass.conf.
"""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "03_ETL"))
PIPELINE = ROOT / "03_ETL" / "run_pipeline.py"
TEST_DB = os.environ.get("OLIST_TEST_DB_NAME", "olist_commerce360_test")
SCHEMA_STAGES = "create_database,create_schemas,create_etl_metadata,create_staging,create_warehouse,verify_warehouse"


def pipeline(stages, **env):
    e = dict(os.environ, OLIST_DB=TEST_DB, **env)
    return subprocess.run([sys.executable, str(PIPELINE), "--stages", stages, "--no-report"],
                          cwd=ROOT, env=e, capture_output=True, text=True)


@unittest.skipUnless(os.environ.get("OLIST_TEST_DB") == "1", "set OLIST_TEST_DB=1 to run database tests")
class TestPipelineOnDatabase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import psycopg
        import etl_config as cfg
        assert TEST_DB.endswith(("_test", "_ci")) and TEST_DB != cfg.DB_NAME, "refusing to use a non-test database"
        cls.psycopg, cls.cfg = psycopg, cfg
        cls._drop()
        cls.build = pipeline(SCHEMA_STAGES)

    @classmethod
    def tearDownClass(cls):
        cls._drop()

    @classmethod
    def _drop(cls):
        with cls.psycopg.connect(cls.cfg.conninfo("postgres"), autocommit=True) as c:
            c.execute(f'DROP DATABASE IF EXISTS "{TEST_DB}" WITH (FORCE)')

    def connect(self):
        return self.psycopg.connect(self.cfg.conninfo(TEST_DB), autocommit=True)

    def test_1_schema_build_and_verification_pass(self):
        self.assertEqual(self.build.returncode, 0, self.build.stdout + self.build.stderr)
        self.assertIn("structure checks passed", self.build.stdout)

    def test_2_objects_committed(self):
        with self.connect() as c:
            n = dict(c.execute("SELECT table_schema, count(*) FROM information_schema.tables "
                               "WHERE table_schema LIKE 'project_%' GROUP BY 1").fetchall())
            logged = c.execute("SELECT count(*) FROM project_staging.etl_run_log WHERE status = 'SUCCESS'").fetchone()[0]
        self.assertEqual(n.get("project_dw"), 10)
        self.assertEqual(n.get("project_staging"), 11)  # 9 stg_ + etl_run_log + etl_load_audit
        self.assertGreaterEqual(logged, 6)

    def test_3_rerun_is_idempotent(self):
        r = pipeline(SCHEMA_STAGES)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("already exists (kept)", r.stdout)

    def test_4_constraints_enforced(self):
        with self.connect() as c:
            with self.assertRaises(self.psycopg.errors.ForeignKeyViolation):
                c.execute("INSERT INTO project_dw.fact_reviews VALUES ('r', 'o', 999, 20180101, 20180101, 5, 1, 0, 0)")
            with self.assertRaises(self.psycopg.errors.CheckViolation):
                c.execute("INSERT INTO project_dw.dim_order_status (order_status_code, order_status_name, status_group, "
                          "is_final_status) VALUES ('x', 'X', 'Bogus', true)")
            c.execute("INSERT INTO project_dw.dim_customer (customer_key, customer_unique_id) OVERRIDING SYSTEM VALUE "
                      "VALUES (-1, 'UNKNOWN')")  # unknown member must be insertable (DEC-014)
            key = c.execute("INSERT INTO project_dw.dim_customer (customer_unique_id, customer_state) "
                            "VALUES ('abc', 'SP') RETURNING customer_key").fetchone()[0]
            self.assertEqual(key, 1)  # identity surrogate key starts at 1, independent of the -1 member
            c.execute("DELETE FROM project_dw.dim_customer")

    def test_5_verification_detects_drift(self):
        with self.connect() as c:
            c.execute("ALTER TABLE project_dw.fact_orders DROP COLUMN is_late")
        r = pipeline("verify_warehouse")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("FAILED", r.stdout)
        self.assertEqual(pipeline("create_warehouse,verify_warehouse").returncode, 0)  # rebuild repairs it

    def test_6_load_fails_loudly_without_source_files(self):
        with tempfile.TemporaryDirectory() as empty:
            r = pipeline("load_staging", OLIST_RAW_DIR=empty)
        self.assertEqual(r.returncode, 1)
        self.assertIn("missing", r.stdout)


if __name__ == "__main__":
    unittest.main()

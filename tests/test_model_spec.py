"""Unit tests for the single source of truth: build/model_spec.py and team details."""
import re
import unittest

import phase1_helpers  # noqa: F401  (adds build/ to sys.path)
import doc_common
import model_spec as m

ROLES = {"PK", "NK", "FK", "DD", "M", "A"}
ADDITIVITY = {"Additive", "Semi-additive", "Non-additive"}


class TestTables(unittest.TestCase):
    def test_expected_tables(self):
        self.assertEqual({t["name"] for t in m.FACTS},
                         {"fact_order_items", "fact_orders", "fact_payments", "fact_reviews"})
        self.assertEqual({t["name"] for t in m.DIMS},
                         {"dim_date", "dim_customer", "dim_product", "dim_seller", "dim_payment_type", "dim_order_status"})

    def test_column_tuples_well_formed(self):
        for t in m.TABLES:
            for c in t["columns"]:
                self.assertEqual(len(c), 10, f"{t['name']}.{c[0]}")
                self.assertIn(c[2], ROLES, f"{t['name']}.{c[0]}")
                self.assertTrue(c[1] and c[4] and c[5] and c[6], f"{t['name']}.{c[0]} has empty type/description/source/rule")
                if c[2] == "M":
                    self.assertIn(c[8], ADDITIVITY, f"{t['name']}.{c[0]}")
                else:
                    self.assertEqual(c[8], "", f"{t['name']}.{c[0]} additivity on non-measure")

    def test_dimension_keys(self):
        for t in m.DIMS:
            pks = [c for c in t["columns"] if c[2] == "PK"]
            nks = [c for c in t["columns"] if c[2] == "NK"]
            self.assertEqual(len(pks), 1, t["name"])
            self.assertEqual(len(nks), 1, t["name"])
            self.assertFalse(pks[0][3], f"{t['name']} PK must be NOT NULL")
            self.assertIn("-1", t["grain"], f"{t['name']} grain must mention the unknown member")

    def test_fact_grains_and_keys(self):
        grains = [t["grain"] for t in m.FACTS]
        self.assertEqual(len(grains), len(set(grains)))
        for t in m.FACTS:
            self.assertTrue(t["grain"].startswith("One row per"), t["name"])
            self.assertTrue(any(c[2] == "PK" for c in t["columns"]), t["name"])
            self.assertTrue(any(c[2] == "M" for c in t["columns"]), t["name"])

    def test_foreign_keys_reference_dimension_primary_keys(self):
        for fact, fk, dim, pk, _ in m.relationships():
            self.assertEqual(m.TABLE[dim]["kind"], "dimension", f"{fact}.{fk}")
            self.assertEqual(m.col(dim, pk)[2], "PK", f"{fact}.{fk} -> {dim}.{pk}")
            self.assertEqual(m.col(fact, fk)[1], m.col(dim, pk)[1], f"{fact}.{fk} type mismatch")
            self.assertFalse(m.col(fact, fk)[3], f"{fact}.{fk} must be NOT NULL (unknown member -1)")

    def test_no_fact_to_fact_or_snowflake_relationships(self):
        for fact, fk, dim, _pk, _ in m.relationships():
            self.assertTrue(fact.startswith("fact_") and dim.startswith("dim_"))
        for t in m.DIMS:
            self.assertFalse(any(c[2] == "FK" for c in t["columns"]), f"{t['name']} has an FK (snowflake)")


class TestBusinessDefinitions(unittest.TestCase):
    def test_sales_freight_payment_kept_distinct(self):
        meas = {x[0]: x for x in m.MEASURES}
        self.assertIn("item_price", meas["Item sales revenue"][3])
        self.assertEqual(meas["Item sales revenue"][2], "fact_order_items")
        self.assertEqual(meas["Amount paid"][2], "fact_payments")
        self.assertNotIn("payment_value", meas["Item sales revenue"][3])
        self.assertIn("freight_value", meas["Freight revenue"][3])

    def test_revenue_excludes_cancelled(self):
        for name in ("Item sales revenue", "Freight revenue", "Gross merchandise value (GMV)"):
            self.assertIn("status_group <> 'Cancelled'", next(x[3] for x in m.MEASURES if x[0] == name))
        groups = {code: grp for code, _n, grp, _f in m.ORDER_STATUS}
        self.assertEqual(groups["canceled"], "Cancelled")
        self.assertEqual(groups["unavailable"], "Cancelled")
        self.assertEqual(groups["delivered"], "Delivered")

    def test_customer_business_key(self):
        self.assertEqual(m.TABLE["dim_customer"]["natural_key"], "customer_unique_id")
        self.assertEqual(m.col("dim_customer", "customer_unique_id")[2], "NK")

    def test_separate_item_and_payment_facts(self):
        items = {c[0] for c in m.TABLE["fact_order_items"]["columns"]}
        pays = {c[0] for c in m.TABLE["fact_payments"]["columns"]}
        self.assertNotIn("payment_value", items)
        self.assertNotIn("item_price", pays)

    def test_trend_window_documented(self):
        bq01 = next(q for q in m.QUESTIONS if q[0] == "BQ-01")
        self.assertIn("Jan 2017 - Aug 2018", bq01[6])

    def test_questions_map_to_model(self):
        self.assertGreaterEqual(len(m.QUESTIONS), 10)
        ids = [q[0] for q in m.QUESTIONS]
        self.assertEqual(len(ids), len(set(ids)))
        kpis = {x[0]: x[2] for x in m.MEASURES}
        reqs = {r[0] for r in m.REQUIREMENTS}
        for q in m.QUESTIONS:
            self.assertIn(q[8], reqs, q[0])
            cols = {c[0] for f in q[5] for c in m.TABLE[f]["columns"]}
            for meas in q[3]:
                self.assertTrue(meas in kpis or meas in cols, f"{q[0]}: unknown measure {meas}")
            for d in q[4]:
                dim = d.split(" ")[0]
                self.assertTrue(any(dim in m.bus_matrix()[f] for f in q[5]), f"{q[0]}: {dim} not joined to {q[5]}")

    def test_unsupported_analyses_out_of_scope(self):
        scope = " ".join(x[0] for x in m.OUT_OF_SCOPE).lower()
        for term in ("profit", "inventory", "promotion"):
            self.assertIn(term, scope)
        kpi_names = " ".join(x[0] for x in m.MEASURES).lower()
        for term in ("profit", "margin", "stock", "inventory"):
            self.assertNotIn(term, kpi_names)


class TestTeamDetails(unittest.TestCase):
    def test_team_complete_and_unique(self):
        self.assertEqual(len(doc_common.TEAM), 3)
        names = [n for n, _ in doc_common.TEAM]
        rolls = [r for _, r in doc_common.TEAM]
        self.assertEqual(len(set(names)), 3)
        self.assertEqual(len(set(rolls)), 3, "duplicate roll numbers")
        for r in rolls:
            self.assertRegex(r, r"^\d{2}L-\d{4}$")
        self.assertTrue(doc_common.SECTION and doc_common.INSTRUCTOR)

    def test_no_placeholders_in_cover(self):
        for k, v in doc_common.TEAM_ROWS:
            self.assertNotRegex(v, re.compile(r"\[[^\]]*\]"), k)


if __name__ == "__main__":
    unittest.main()

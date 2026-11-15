"""Verify the physical database against the design (Phase 2, owner: M1).

verify_structure(): reads the PostgreSQL catalog and compares project_staging / project_dw with
    etl_config.SOURCES and the Phase 1 model_spec (tables, column order, types, nullability,
    identity surrogate keys, primary/unique/foreign keys, comments, no extra indexes).
verify_staging_data(): compares the loaded staging data with figures verified independently in
    Phase 1 profiling (pandas), proving that the TEXT landing preserved values and NULLs.
Each function returns a list of (check, passed, detail).
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "03_ETL"))
sys.path.insert(0, str(ROOT / "01_Project_Documentation" / "phase1" / "build"))
import etl_config as cfg  # noqa: E402
import model_spec as m  # noqa: E402

TYPE_MAP = {"INTEGER": "integer", "SMALLINT": "smallint", "BIGINT": "bigint", "DATE": "date",
            "BOOLEAN": "boolean", "TEXT": "text"}


def pg_format(spec_type):
    t = spec_type.upper().replace(" ", "")
    if t in TYPE_MAP:
        return TYPE_MAP[t]
    mt = re.fullmatch(r"(VARCHAR|CHAR|NUMERIC)\(([\d,]+)\)", t)
    base = {"VARCHAR": "character varying", "CHAR": "character", "NUMERIC": "numeric"}[mt.group(1)]
    return f"{base}({mt.group(2)})"


def _columns(cur, schema):
    rows = cur.execute("""
        SELECT c.relname, a.attnum, a.attname, format_type(a.atttypid, a.atttypmod), a.attnotnull,
               a.attidentity, col_description(c.oid, a.attnum)
        FROM pg_attribute a JOIN pg_class c ON c.oid = a.attrelid JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = %s AND c.relkind = 'r' AND a.attnum > 0 AND NOT a.attisdropped
        ORDER BY c.relname, a.attnum""", (schema,)).fetchall()
    out = {}
    for rel, _num, name, typ, notnull, ident, comment in rows:
        out.setdefault(rel, []).append((name, typ, notnull, ident, comment))
    return out


def _constraints(cur, schema):
    rows = cur.execute("""
        SELECT c.relname, k.contype, k.conname,
               ARRAY(SELECT a.attname FROM unnest(k.conkey) WITH ORDINALITY u(n, o)
                     JOIN pg_attribute a ON a.attrelid = k.conrelid AND a.attnum = u.n ORDER BY u.o),
               f.relname,
               ARRAY(SELECT a.attname FROM unnest(k.confkey) WITH ORDINALITY u(n, o)
                     JOIN pg_attribute a ON a.attrelid = k.confrelid AND a.attnum = u.n ORDER BY u.o)
        FROM pg_constraint k JOIN pg_class c ON c.oid = k.conrelid JOIN pg_namespace n ON n.oid = c.relnamespace
        LEFT JOIN pg_class f ON f.oid = k.confrelid
        WHERE n.nspname = %s""", (schema,)).fetchall()
    return rows


def verify_structure(conn):
    res = []

    def check(name, ok, detail=""):
        res.append((name, bool(ok), detail))

    with conn.cursor() as cur:
        schemas = {r[0] for r in cur.execute("SELECT nspname FROM pg_namespace").fetchall()}
        for s in cfg.SCHEMAS:
            check(f"schema {s} exists", s in schemas)

        # staging
        stg = _columns(cur, "project_staging")
        for _file, table, _exp, cols in cfg.SOURCES:
            got = stg.get(table)
            check(f"staging {table}: exists", got is not None)
            if got:
                names = [c[0] for c in got]
                check(f"staging {table}: columns match source header", names == ["stg_row_id"] + cols,
                      f"{len(names) - 1} source columns")
                check(f"staging {table}: source columns are TEXT", all(c[1] == "text" for c in got[1:]))
        for t in ("etl_run_log", "etl_load_audit"):
            check(f"metadata {t}: exists", t in stg)

        # warehouse
        dw = _columns(cur, "project_dw")
        spec_tables = {t["name"] for t in m.TABLES}
        check("project_dw contains exactly the 10 designed tables", set(dw) == spec_tables,
              f"extra={sorted(set(dw) - spec_tables)} missing={sorted(spec_tables - set(dw))}")
        cons = _constraints(cur, "project_dw")
        for t in m.TABLES:
            name = t["name"]
            got = dw.get(name)
            if not got:
                continue
            want = [(c[0], pg_format(c[1]), not c[3]) for c in t["columns"]]
            have = [(c[0], c[1], c[2]) for c in got]
            check(f"{name}: columns, order, types, nullability match data dictionary", have == want,
                  "" if have == want else f"first diff: {next((a, b) for a, b in zip(have, want) if a != b) if len(have) == len(want) else (len(have), len(want))}")
            check(f"{name}: every column has a comment", all(c[4] for c in got))
            pk_spec = [c[0] for c in t["columns"] if c[2] == "PK"]
            pk_db = [r[3] for r in cons if r[0] == name and r[1] == "p"]
            check(f"{name}: primary key {pk_spec}", pk_db == [pk_spec], str(pk_db))
            if t["kind"] == "dimension":
                ident = {c[0]: c[3] for c in got}
                pk = pk_spec[0]
                if name == "dim_date":
                    check(f"{name}: smart key (no identity)", ident[pk] == "")
                else:
                    check(f"{name}: surrogate key {pk} is GENERATED ALWAYS AS IDENTITY", ident[pk] == "a")
                nk = [c[0] for c in t["columns"] if c[2] == "NK"]
                uq = [r[3] for r in cons if r[0] == name and r[1] == "u"]
                check(f"{name}: natural key {nk} is UNIQUE", [nk] == uq, str(uq))
            fk_spec = sorted((c[0], c[9].split(".")[0], c[9].split(".")[1]) for c in t["columns"] if c[2] == "FK")
            fk_db = sorted((r[3][0], r[4], r[5][0]) for r in cons if r[0] == name and r[1] == "f")
            check(f"{name}: foreign keys match design ({len(fk_spec)})", fk_spec == fk_db,
                  "" if fk_spec == fk_db else f"db={fk_db}")
        n_checks = sum(1 for r in cons if r[1] == "c")
        check("project_dw: CHECK constraints present", n_checks > 0, f"{n_checks} CHECK constraints")
        extra_idx = cur.execute("""
            SELECT count(*) FROM pg_index i JOIN pg_class c ON c.oid = i.indrelid
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'project_dw'
              AND NOT EXISTS (SELECT 1 FROM pg_constraint k WHERE k.conindid = i.indexrelid)""").fetchone()[0]
        check("project_dw: no secondary indexes yet (Phase 3 before/after baseline)", extra_idx == 0, f"{extra_idx}")
    return res


# Figures verified independently in Phase 1 profiling (pandas) - 02_Data/profiling/profiling_report.md
STAGING_EXPECTATIONS = [
    ("orders: NULL order_approved_at", "SELECT count(*) FROM project_staging.stg_orders WHERE order_approved_at IS NULL", 160),
    ("orders: NULL order_delivered_carrier_date", "SELECT count(*) FROM project_staging.stg_orders WHERE order_delivered_carrier_date IS NULL", 1783),
    ("orders: NULL order_delivered_customer_date", "SELECT count(*) FROM project_staging.stg_orders WHERE order_delivered_customer_date IS NULL", 2965),
    ("orders: delivered status", "SELECT count(*) FROM project_staging.stg_orders WHERE order_status = 'delivered'", 96478),
    ("customers: distinct customer_unique_id", "SELECT count(DISTINCT customer_unique_id) FROM project_staging.stg_customers", 96096),
    ("customers: zip prefixes keep leading zero (5 chars)", "SELECT count(*) FROM project_staging.stg_customers WHERE length(customer_zip_code_prefix) <> 5", 0),
    ("customers: zip prefixes starting with 0", "SELECT count(*) FROM project_staging.stg_customers WHERE customer_zip_code_prefix LIKE '0%'", 23995),
    ("products: NULL category", "SELECT count(*) FROM project_staging.stg_products WHERE product_category_name IS NULL", 610),
    ("order_items: SUM(price)", "SELECT sum(price::numeric) FROM project_staging.stg_order_items", "13591643.70"),
    ("order_items: SUM(freight_value)", "SELECT sum(freight_value::numeric) FROM project_staging.stg_order_items", "2251909.54"),
    ("payments: SUM(payment_value)", "SELECT sum(payment_value::numeric) FROM project_staging.stg_order_payments", "16008872.12"),
    ("reviews: distinct (review_id, order_id)", "SELECT count(*) FROM (SELECT DISTINCT review_id, order_id FROM project_staging.stg_order_reviews) s", 99224),
    ("reviews: comment messages present", "SELECT count(*) FROM project_staging.stg_order_reviews WHERE review_comment_message IS NOT NULL", 40977),
    ("geolocation: distinct zip prefixes", "SELECT count(DISTINCT geolocation_zip_code_prefix) FROM project_staging.stg_geolocation", 19015),
    ("translation: BOM not in data", "SELECT count(*) FROM project_staging.stg_category_translation WHERE product_category_name LIKE E'\\uFEFF%'", 0),
]


def verify_staging_data(conn):
    res = []
    with conn.cursor() as cur:
        for name, sql, expected in STAGING_EXPECTATIONS:
            got = cur.execute(sql).fetchone()[0]
            ok = str(got) == str(expected)
            res.append((f"staging data: {name}", ok, f"got {got}, expected {expected}"))
    return res


if __name__ == "__main__":
    import psycopg
    with psycopg.connect(cfg.conninfo()) as c:
        out = verify_structure(c) + verify_staging_data(c)
    for n, ok, d in out:
        print("PASS" if ok else "FAIL", n, d)
    print(f"{len(out)} checks, {sum(not r[1] for r in out)} failed")
    sys.exit(1 if any(not r[1] for r in out) else 0)

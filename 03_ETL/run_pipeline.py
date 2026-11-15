"""Olist Commerce360 ETL pipeline runner (Phase 2, owner: M1 - Kashish Fatima).

Runs every stage in order, logs each stage to project_staging.etl_run_log, and writes
03_ETL/run_reports/pipeline_run_latest.md (+ .json) and 04_Data_Warehouse/verification_report.md.

Stages owned by M1 are implemented here. Stages owned by M2/M3 run every *.sql (in one
transaction per file) and *.py (as a subprocess) found in their folder, in file-name order.
A folder with no scripts is reported as NOT_IMPLEMENTED - never as a success.

Usage (from the repository root):
    python 03_ETL/run_pipeline.py                      # full run
    python 03_ETL/run_pipeline.py --stages create_database,create_schemas,create_warehouse
    python 03_ETL/run_pipeline.py --strict             # also fail if any stage is NOT_IMPLEMENTED
Connection: libpq environment variables / pgpass.conf (see etl_config.py). No passwords in code.
"""
import argparse
import json
import os
import platform
import re
import subprocess
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

ETL = Path(__file__).resolve().parent
sys.path.insert(0, str(ETL))
sys.path.insert(0, str(ETL / "staging"))
sys.path.insert(0, str(ETL.parent / "04_Data_Warehouse"))

import psycopg  # noqa: E402

import etl_config as cfg  # noqa: E402
import load_staging  # noqa: E402
import verify_warehouse  # noqa: E402


class NotImplementedStage(Exception):
    pass


def run_sql_file(conn, path):
    """Execute a SQL file in one explicit transaction (committed on success, rolled back on error).
    The pipeline connection is autocommit, so conn.transaction() is a real BEGIN/COMMIT, never a savepoint."""
    sql = Path(path).read_text(encoding="utf-8")
    with conn.transaction(), conn.cursor() as cur:
        cur.execute(sql)


# ------------------------------------------------------------------ M1 stages
def st_create_database(ctx):
    with psycopg.connect(cfg.conninfo("postgres"), autocommit=True) as c:
        exists = c.execute("SELECT 1 FROM pg_database WHERE datname = %s", (cfg.DB_NAME,)).fetchone()
        if exists:
            return None, f"database {cfg.DB_NAME} already exists (kept)"
        sql = (cfg.DW_DIR / "database.sql").read_text(encoding="utf-8")
        sql = re.sub(r"--[^\n]*", "", sql).replace("olist_commerce360", cfg.DB_NAME)
        for stmt in [s.strip() for s in sql.split(";") if s.strip()]:
            c.execute(stmt)
        return None, f"database {cfg.DB_NAME} created"


def st_sql(path):
    def run(ctx):
        run_sql_file(ctx["conn"], path)
        return None, f"executed {Path(path).relative_to(cfg.ROOT).as_posix()}"
    return run


def st_load_staging(ctx):
    total, results = load_staging.load_all(ctx["conn"], ctx["run_id"])
    ctx["staging_audit"] = results
    return total, f"{len(results)} files loaded and reconciled"


def _verification(ctx, checks, label):
    ctx.setdefault("verification", []).extend(checks)
    failed = [c for c in checks if not c[1]]
    if failed:
        raise RuntimeError(f"{len(failed)} {label} checks failed: " + "; ".join(f"{n} ({d})" for n, _, d in failed[:5]))
    return len(checks), f"{len(checks)} {label} checks passed"


def st_verify_staging(ctx):
    # a fresh connection only sees committed data, so verification proves the load was committed
    with psycopg.connect(cfg.conninfo(), autocommit=True) as vc:
        return _verification(ctx, verify_warehouse.verify_staging_data(vc), "staging data")


def st_verify_warehouse(ctx):
    with psycopg.connect(cfg.conninfo(), autocommit=True) as vc:
        return _verification(ctx, verify_warehouse.verify_structure(vc), "structure")


# ------------------------------------------------------------------ M2 / M3 folder stages
def st_folder(folder):
    def run(ctx):
        scripts = sorted(p for p in (ETL / folder).glob("*") if p.suffix in (".sql", ".py"))
        if not scripts:
            raise NotImplementedStage(f"no *.sql / *.py scripts in 03_ETL/{folder}/ yet")
        for p in scripts:
            if p.suffix == ".sql":
                run_sql_file(ctx["conn"], p)
            else:
                r = subprocess.run([sys.executable, str(p)], cwd=cfg.ROOT, capture_output=True, text=True,
                                   env=dict(os.environ, OLIST_DB=cfg.DB_NAME, OLIST_RUN_ID=ctx["run_id"]))
                if r.returncode != 0:
                    raise RuntimeError(f"{p.name} exited {r.returncode}: {(r.stderr or r.stdout)[-800:]}")
        return None, "ran " + ", ".join(p.name for p in scripts)
    return run


STAGES = [  # (name, owner, function)
    ("create_database", "M1", st_create_database),
    ("create_schemas", "M1", st_sql(cfg.DW_DIR / "schemas.sql")),
    ("create_etl_metadata", "M1", st_sql(ETL / "etl_metadata.sql")),
    ("create_staging", "M1", st_sql(ETL / "staging" / "staging.sql")),
    ("load_staging", "M1", st_load_staging),
    ("verify_staging", "M1", st_verify_staging),
    ("create_warehouse", "M1", st_sql(cfg.DW_DIR / "warehouse.sql")),
    ("verify_warehouse", "M1", st_verify_warehouse),
    ("clean_staging", "M2", st_folder("cleaning")),
    ("load_dimensions", "M2", st_folder("dimensions")),
    ("load_facts", "M3", st_folder("facts")),
    ("quality_checks", "M3", st_folder("quality")),
]
STAGE_NAMES = [s[0] for s in STAGES]


def log_rows(conn, rows):
    with conn.cursor() as cur:
        cur.executemany(
            "INSERT INTO project_staging.etl_run_log (run_id, stage_order, stage_name, stage_owner, status, "
            "rows_affected, started_at, finished_at, message) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            [(r["run_id"], r["order"], r["stage"], r["owner"], r["status"], r["rows"], r["started"], r["finished"],
              r["message"][:4000]) for r in rows])


def write_reports(ctx, results):
    cfg.RUN_REPORT_DIR.mkdir(exist_ok=True)
    meta = ctx["meta"]
    js = {"run_id": ctx["run_id"], **meta,
          "stages": [{k: (v.isoformat() if isinstance(v, datetime) else v) for k, v in r.items()} for r in results],
          "staging_audit": ctx.get("staging_audit", []),
          "verification": [{"check": n, "passed": ok, "detail": d} for n, ok, d in ctx.get("verification", [])]}
    (cfg.RUN_REPORT_DIR / "pipeline_run_latest.json").write_text(json.dumps(js, indent=2), encoding="utf-8")
    L = [f"# Pipeline run report - {ctx['run_id']}", "",
         "Generated by `03_ETL/run_pipeline.py`. Do not edit by hand; re-run the pipeline instead.", "",
         f"- Database: `{cfg.DB_NAME}` on {meta['server']}", f"- Python {meta['python']} | psycopg {meta['psycopg']} | {meta['platform']}",
         f"- Started {meta['started']} | total {meta['total_seconds']:.1f} s | stages requested: {meta['stages_requested']}", "",
         "## Stages", "", "| # | Stage | Owner | Status | Rows | Seconds | Message |", "|---|---|---|---|---|---|---|"]
    for r in results:
        rows = f"{r['rows']:,}" if isinstance(r["rows"], int) else ""
        L.append(f"| {r['order']} | {r['stage']} | {r['owner']} | {r['status']} | {rows} | {r['seconds']:.2f} | "
                 f"{r['message'].replace('|', '/')[:300]} |")
    if ctx.get("staging_audit"):
        L += ["", "## Source-to-staging reconciliation", "",
              "| Source file | Staging table | CSV records | Loaded rows | Expected (Phase 1) | Header | Reconciled | SHA-256 (first 16) |",
              "|---|---|---|---|---|---|---|---|"]
        for a in ctx["staging_audit"]:
            L.append(f"| {a['file']} | project_staging.{a['table']} | {a['csv_records']:,} | {a['loaded_rows']:,} | "
                     f"{a['expected_rows']:,} | {'OK' if a['header_ok'] else 'MISMATCH'} | {'yes' if a['reconciled'] else 'NO'} | "
                     f"`{a['sha256'][:16]}` |")
    (cfg.RUN_REPORT_DIR / "pipeline_run_latest.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    ver = ctx.get("verification", [])
    if ver:
        V = ["# Database verification report", "",
             f"Generated by `03_ETL/run_pipeline.py` (run `{ctx['run_id']}`) using `04_Data_Warehouse/verify_warehouse.py`.", "",
             f"Checks: {len(ver)}, passed: {sum(1 for v in ver if v[1])}, failed: {sum(1 for v in ver if not v[1])}.", "",
             "| Check | Result | Detail |", "|---|---|---|"]
        V += [f"| {n} | {'PASS' if ok else 'FAIL'} | {str(d).replace('|', '/')} |" for n, ok, d in ver]
        (cfg.DW_DIR / "verification_report.md").write_text("\n".join(V) + "\n", encoding="utf-8")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stages", help="comma-separated subset of: " + ",".join(STAGE_NAMES))
    ap.add_argument("--strict", action="store_true", help="exit 1 if any stage is NOT_IMPLEMENTED")
    ap.add_argument("--no-report", action="store_true", help="do not write run_reports / verification_report")
    a = ap.parse_args(argv)
    wanted = a.stages.split(",") if a.stages else STAGE_NAMES
    unknown = set(wanted) - set(STAGE_NAMES)
    if unknown:
        ap.error(f"unknown stage(s): {sorted(unknown)}")

    run_id = datetime.now().strftime("run-%Y%m%dT%H%M%S")
    t0 = time.perf_counter()
    ctx = {"run_id": run_id}
    results, exit_code = [], 0
    for order, (name, owner, fn) in enumerate(STAGES, 1):
        if name not in wanted:
            continue
        if name != "create_database" and "conn" not in ctx:
            ctx["conn"] = psycopg.connect(cfg.conninfo(), autocommit=True)
        started, s0 = datetime.now(timezone.utc), time.perf_counter()
        try:
            rows, msg = fn(ctx)
            status = "SUCCESS"
        except NotImplementedStage as e:
            rows, msg, status = None, f"{e} (owner {owner})", "NOT_IMPLEMENTED"
        except Exception as e:  # noqa: BLE001 - every failure is logged and stops the run
            rows, msg, status = None, f"{type(e).__name__}: {e}", "FAILED"
            traceback.print_exc()
        rec = {"run_id": run_id, "order": order, "stage": name, "owner": owner, "status": status, "rows": rows,
               "started": started, "finished": datetime.now(timezone.utc), "seconds": time.perf_counter() - s0,
               "message": msg}
        results.append(rec)
        print(f"[{status:15s}] {order:2d} {name:20s} {owner}  {rec['seconds']:7.2f}s  {msg}")
        if status == "FAILED":
            exit_code = 1
            break
        if status == "NOT_IMPLEMENTED" and a.strict:
            exit_code = 1

    # write the stage log once the metadata table exists (it may have been created during this run)
    try:
        with psycopg.connect(cfg.conninfo(), autocommit=True) as lc:
            if lc.execute("SELECT to_regclass('project_staging.etl_run_log')").fetchone()[0]:
                log_rows(lc, results)
            server = lc.execute("SHOW server_version").fetchone()[0]
    except psycopg.OperationalError:
        server = "unavailable"
    if "conn" in ctx:
        ctx["conn"].close()
    ctx["meta"] = {"server": f"PostgreSQL {server}", "python": platform.python_version(),
                   "psycopg": psycopg.__version__, "platform": platform.platform(terse=True),
                   "started": results[0]["started"].isoformat(timespec="seconds") if results else "",
                   "total_seconds": time.perf_counter() - t0, "stages_requested": ",".join(wanted)}
    if not a.no_report:
        write_reports(ctx, results)
    done = {r["status"] for r in results}
    print(f"\nRun {run_id}: " + ", ".join(f"{s}={sum(r['status'] == s for r in results)}" for s in sorted(done)))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())

"""Load the 9 Olist CSV files into project_staging.stg_* (Phase 2, owner: M1).

For every source file:
  1. verify the header against the contract in etl_config.SOURCES (dataset version check);
  2. compute SHA-256 and count CSV records with the csv module (review comments contain line breaks,
     so physical lines are not records);
  3. TRUNCATE and COPY the file into its staging table (all TEXT, empty unquoted field -> NULL);
  4. record the reconciliation in project_staging.etl_load_audit.
The stage fails if any file is missing, has a different header, or does not reconcile.

Run standalone:  python 03_ETL/staging/load_staging.py   (or through 03_ETL/run_pipeline.py)
"""
import csv
import hashlib
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import etl_config as cfg  # noqa: E402

CHUNK = 1 << 20


def file_facts(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(CHUNK), b""):
            h.update(block)
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header = next(reader)
        records = sum(1 for _ in reader)
    return h.hexdigest(), path.stat().st_size, header, records


def copy_file(cur, path, table, cols):
    sql = f"COPY project_staging.{table} ({', '.join(cols)}) FROM STDIN WITH (FORMAT csv, ENCODING 'UTF8')"
    with open(path, "rb") as f:
        f.readline()  # skip header line (headers contain no embedded line breaks)
        with cur.copy(sql) as cp:
            for block in iter(lambda: f.read(CHUNK), b""):
                cp.write(block)


def load_all(conn, run_id):
    """Returns (total_rows, results). Raises RuntimeError if anything fails to reconcile."""
    results, problems = [], []
    for file, table, expected, cols in cfg.SOURCES:
        path = cfg.RAW_DIR / file
        if not path.exists():
            problems.append(f"{file}: missing in {cfg.RAW_DIR} (see 02_Data/README.md)")
            continue
        sha, size, header, records = file_facts(path)
        header_ok = header == cols
        loaded = 0
        with conn.transaction(), conn.cursor() as cur:  # one committed transaction per file
            if header_ok:
                cur.execute(f"TRUNCATE project_staging.{table} RESTART IDENTITY")
                copy_file(cur, path, table, cols)
                loaded = cur.execute(f"SELECT count(*) FROM project_staging.{table}").fetchone()[0]
            cur.execute(
                "INSERT INTO project_staging.etl_load_audit (run_id, source_file, staging_table, file_bytes, "
                "file_sha256, header_ok, csv_records, loaded_rows, expected_rows) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (run_id, file, table, size, sha, header_ok, records, loaded, expected))
        ok = header_ok and records == loaded == expected
        results.append({"file": file, "table": table, "bytes": size, "sha256": sha, "header_ok": header_ok,
                        "csv_records": records, "loaded_rows": loaded, "expected_rows": expected, "reconciled": ok})
        if not header_ok:
            problems.append(f"{file}: header {header} does not match contract {cols}")
        elif not ok:
            problems.append(f"{file}: csv={records:,} loaded={loaded:,} expected={expected:,}")
    if problems:
        raise RuntimeError("; ".join(problems))
    return sum(r["loaded_rows"] for r in results), results


if __name__ == "__main__":
    import psycopg
    rid = "manual-" + datetime.now().strftime("%Y%m%dT%H%M%S")
    with psycopg.connect(cfg.conninfo(), autocommit=True) as c:
        total, res = load_all(c, rid)
    for r in res:
        print(f"{r['table']:28s} {r['loaded_rows']:>10,}  reconciled={r['reconciled']}")
    print(f"total {total:,} rows")

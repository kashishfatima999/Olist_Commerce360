-- =====================================================================================
-- ETL metadata tables (schema project_staging)
-- Olist Commerce360 | DL3004 Phase 2 | owner: Member 1 (Kashish Fatima)
-- Kept across runs (CREATE IF NOT EXISTS) so the run history is preserved.
-- =====================================================================================

CREATE TABLE IF NOT EXISTS project_staging.etl_run_log (
    log_id        BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id        TEXT        NOT NULL,
    stage_order   SMALLINT    NOT NULL,
    stage_name    TEXT        NOT NULL,
    stage_owner   TEXT        NOT NULL,
    status        TEXT        NOT NULL CHECK (status IN ('SUCCESS', 'FAILED', 'NOT_IMPLEMENTED')),
    rows_affected BIGINT,
    started_at    TIMESTAMPTZ NOT NULL,
    finished_at   TIMESTAMPTZ NOT NULL,
    duration_s    NUMERIC(10,3) GENERATED ALWAYS AS (EXTRACT(EPOCH FROM finished_at - started_at)) STORED,
    message       TEXT
);
COMMENT ON TABLE project_staging.etl_run_log IS 'One row per pipeline stage per run (03_ETL/run_pipeline.py).';

CREATE TABLE IF NOT EXISTS project_staging.etl_load_audit (
    audit_id      BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id        TEXT        NOT NULL,
    source_file   TEXT        NOT NULL,
    staging_table TEXT        NOT NULL,
    file_bytes    BIGINT      NOT NULL,
    file_sha256   CHAR(64)    NOT NULL,
    header_ok     BOOLEAN     NOT NULL,
    csv_records   BIGINT      NOT NULL,
    loaded_rows   BIGINT      NOT NULL,
    expected_rows BIGINT      NOT NULL,
    reconciled    BOOLEAN GENERATED ALWAYS AS (header_ok AND csv_records = loaded_rows AND loaded_rows = expected_rows) STORED,
    loaded_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE project_staging.etl_load_audit IS
    'Source-to-staging reconciliation: one row per CSV per run (checksum, record counts).';

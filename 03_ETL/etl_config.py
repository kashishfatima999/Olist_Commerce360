"""Shared configuration for the Olist Commerce360 ETL pipeline (Phase 2, owner: M1).

Connection settings come from standard libpq environment variables, so no credentials are
stored in the repository:
    PGHOST (default localhost), PGPORT (5432), PGUSER (postgres), PGPASSWORD or pgpass.conf,
    OLIST_DB (default olist_commerce360), OLIST_RAW_DIR (default 02_Data/raw_data).
"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ETL_DIR = ROOT / "03_ETL"
DW_DIR = ROOT / "04_Data_Warehouse"
RAW_DIR = Path(os.environ.get("OLIST_RAW_DIR", ROOT / "02_Data" / "raw_data"))
RUN_REPORT_DIR = ETL_DIR / "run_reports"

DB_NAME = os.environ.get("OLIST_DB", "olist_commerce360")
SCHEMAS = ("project_staging", "project_dw", "project_reporting")


def conninfo(dbname=None):
    """libpq connection string; password is resolved by libpq (PGPASSWORD or pgpass.conf)."""
    return " ".join([
        f"host={os.environ.get('PGHOST', 'localhost')}",
        f"port={os.environ.get('PGPORT', '5432')}",
        f"user={os.environ.get('PGUSER', 'postgres')}",
        f"dbname={dbname or DB_NAME}",
        "application_name=olist_commerce360_etl",
    ])


# Source contract: CSV file -> staging table -> exact header (Kaggle olistbr/brazilian-ecommerce v2).
# Expected rows were verified in Phase 1 profiling (02_Data/profiling/profiling_report.md).
SOURCES = [
    ("olist_customers_dataset.csv", "stg_customers", 99441,
     ["customer_id", "customer_unique_id", "customer_zip_code_prefix", "customer_city", "customer_state"]),
    ("olist_geolocation_dataset.csv", "stg_geolocation", 1000163,
     ["geolocation_zip_code_prefix", "geolocation_lat", "geolocation_lng", "geolocation_city", "geolocation_state"]),
    ("olist_order_items_dataset.csv", "stg_order_items", 112650,
     ["order_id", "order_item_id", "product_id", "seller_id", "shipping_limit_date", "price", "freight_value"]),
    ("olist_order_payments_dataset.csv", "stg_order_payments", 103886,
     ["order_id", "payment_sequential", "payment_type", "payment_installments", "payment_value"]),
    ("olist_order_reviews_dataset.csv", "stg_order_reviews", 99224,
     ["review_id", "order_id", "review_score", "review_comment_title", "review_comment_message",
      "review_creation_date", "review_answer_timestamp"]),
    ("olist_orders_dataset.csv", "stg_orders", 99441,
     ["order_id", "customer_id", "order_status", "order_purchase_timestamp", "order_approved_at",
      "order_delivered_carrier_date", "order_delivered_customer_date", "order_estimated_delivery_date"]),
    ("olist_products_dataset.csv", "stg_products", 32951,
     ["product_id", "product_category_name", "product_name_lenght", "product_description_lenght",
      "product_photos_qty", "product_weight_g", "product_length_cm", "product_height_cm", "product_width_cm"]),
    ("olist_sellers_dataset.csv", "stg_sellers", 3095,
     ["seller_id", "seller_zip_code_prefix", "seller_city", "seller_state"]),
    ("product_category_name_translation.csv", "stg_category_translation", 71,
     ["product_category_name", "product_category_name_english"]),
]

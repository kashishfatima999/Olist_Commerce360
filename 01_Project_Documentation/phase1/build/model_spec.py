"""Single source of truth for the Olist Commerce360 Phase 1 dimensional model.

The data dictionary, the schema diagram, the DBML file and the tables inside the
Phase 1 PDFs are all generated from this module so that names, keys, grains and
measures stay identical across deliverables.

Column tuple fields:
    name, pg_type, role, nullable, description, source, rule, example, additivity, references
role: PK, NK (natural/business key), FK, DD (degenerate dimension), M (measure), A (attribute)
additivity (measures only): Additive, Semi-additive, Non-additive
"""

PROJECT = "Olist Commerce360"
SUBTITLE = "An End-to-End E-Commerce Data Warehouse and Business Intelligence Platform"
COURSE = "DL3004 - Data Warehousing and Business Intelligence"
SCHEMA = "project_dw"

# Brazilian states -> (state name, macro-region). IBGE official regions.
STATES = {
    "AC": ("Acre", "North"), "AP": ("Amapa", "North"), "AM": ("Amazonas", "North"),
    "PA": ("Para", "North"), "RO": ("Rondonia", "North"), "RR": ("Roraima", "North"),
    "TO": ("Tocantins", "North"),
    "AL": ("Alagoas", "Northeast"), "BA": ("Bahia", "Northeast"), "CE": ("Ceara", "Northeast"),
    "MA": ("Maranhao", "Northeast"), "PB": ("Paraiba", "Northeast"), "PE": ("Pernambuco", "Northeast"),
    "PI": ("Piaui", "Northeast"), "RN": ("Rio Grande do Norte", "Northeast"), "SE": ("Sergipe", "Northeast"),
    "DF": ("Distrito Federal", "Central-West"), "GO": ("Goias", "Central-West"),
    "MT": ("Mato Grosso", "Central-West"), "MS": ("Mato Grosso do Sul", "Central-West"),
    "ES": ("Espirito Santo", "Southeast"), "MG": ("Minas Gerais", "Southeast"),
    "RJ": ("Rio de Janeiro", "Southeast"), "SP": ("Sao Paulo", "Southeast"),
    "PR": ("Parana", "South"), "RS": ("Rio Grande do Sul", "South"), "SC": ("Santa Catarina", "South"),
}

ORDER_STATUS = [  # code, display name, status_group, is_final_status
    ("created", "Created", "In progress", False),
    ("approved", "Approved", "In progress", False),
    ("invoiced", "Invoiced", "In progress", False),
    ("processing", "Processing", "In progress", False),
    ("shipped", "Shipped", "In progress", False),
    ("delivered", "Delivered", "Delivered", True),
    ("canceled", "Canceled", "Cancelled", True),
    ("unavailable", "Unavailable", "Cancelled", True),
]

PAYMENT_TYPES = [  # code, display name, method group
    ("credit_card", "Credit card", "Card"),
    ("debit_card", "Debit card", "Card"),
    ("boleto", "Boleto (bank slip)", "Bank slip"),
    ("voucher", "Voucher", "Voucher"),
    ("not_defined", "Not defined", "Unknown"),
]

C = lambda *a: a  # noqa: E731  (readability helper for column tuples)

TABLES = [
    # ------------------------------------------------------------------ dimensions
    {
        "name": "dim_date", "kind": "dimension", "type": "Conformed, role-playing date dimension",
        "grain": "One row per calendar day from 2016-01-01 to 2018-12-31, plus one 'Unknown / not occurred' row (date_key = -1).",
        "natural_key": "full_date", "surrogate_key": "date_key (smart key YYYYMMDD)",
        "source": "Generated in ETL (calendar); not a source file.",
        "scd": "Static", "est_rows": "1,096 + 1 unknown",
        "hierarchies": ["Year > Quarter > Month > Date", "Year > Week of year > Date"],
        "columns": [
            C("date_key", "INTEGER", "PK", False, "Surrogate key in YYYYMMDD form; -1 = unknown / not yet occurred.", "Generated", "TO_CHAR(full_date,'YYYYMMDD')::INT", "20171124", "", ""),
            C("full_date", "DATE", "NK", True, "Calendar date (NULL only on the unknown row).", "Generated", "Calendar series", "2017-11-24", "", ""),
            C("day_of_month", "SMALLINT", "A", True, "Day number within month (1-31).", "Generated", "EXTRACT(DAY)", "24", "", ""),
            C("day_of_week_num", "SMALLINT", "A", True, "ISO day of week (1 = Monday ... 7 = Sunday).", "Generated", "EXTRACT(ISODOW)", "5", "", ""),
            C("day_of_week_name", "VARCHAR(10)", "A", True, "Day name.", "Generated", "TO_CHAR(full_date,'FMDay')", "Friday", "", ""),
            C("is_weekend", "BOOLEAN", "A", True, "TRUE for Saturday and Sunday.", "Generated", "ISODOW IN (6,7)", "FALSE", "", ""),
            C("week_of_year", "SMALLINT", "A", True, "ISO week number.", "Generated", "EXTRACT(WEEK)", "47", "", ""),
            C("month_num", "SMALLINT", "A", True, "Month number (1-12).", "Generated", "EXTRACT(MONTH)", "11", "", ""),
            C("month_name", "VARCHAR(10)", "A", True, "Month name.", "Generated", "TO_CHAR(full_date,'FMMonth')", "November", "", ""),
            C("year_month", "CHAR(7)", "A", True, "Year and month label used for monthly trends.", "Generated", "TO_CHAR(full_date,'YYYY-MM')", "2017-11", "", ""),
            C("quarter_num", "SMALLINT", "A", True, "Quarter number (1-4).", "Generated", "EXTRACT(QUARTER)", "4", "", ""),
            C("year_quarter", "CHAR(7)", "A", True, "Year and quarter label.", "Generated", "YYYY || '-Q' || quarter", "2017-Q4", "", ""),
            C("year", "SMALLINT", "A", True, "Calendar year.", "Generated", "EXTRACT(YEAR)", "2017", "", ""),
        ],
    },
    {
        "name": "dim_customer", "kind": "dimension", "type": "Conformed dimension (SCD Type 1)",
        "grain": "One row per real customer (customer_unique_id), plus one 'Unknown' row (customer_key = -1).",
        "natural_key": "customer_unique_id", "surrogate_key": "customer_key",
        "source": "olist_customers_dataset.csv (+ olist_geolocation_dataset.csv for coordinates, olist_orders_dataset.csv for first purchase date)",
        "scd": "Type 1 - location taken from the customer's most recent order", "est_rows": "96,096 + 1 unknown",
        "hierarchies": ["Region > State > City > Zip code prefix"],
        "columns": [
            C("customer_key", "INTEGER", "PK", False, "Warehouse surrogate key (identity); -1 = unknown.", "Generated", "GENERATED ALWAYS AS IDENTITY", "1001", "", ""),
            C("customer_unique_id", "VARCHAR(32)", "NK", False, "Olist identifier of the person. Business key; unique in this table.", "customers.customer_unique_id", "Trim; one row per distinct value", "861eff4711a542e4b93843c6dd7febb0", "", ""),
            C("customer_zip_code_prefix", "CHAR(5)", "A", True, "First five digits of the customer's postcode.", "customers.customer_zip_code_prefix", "Read as text; left-pad to 5 digits (leading zeros are lost if read as integer)", "09790", "", ""),
            C("customer_city", "VARCHAR(100)", "A", True, "Customer city.", "customers.customer_city", "Trim; title case; remove accents consistently", "Sao Bernardo Do Campo", "", ""),
            C("customer_state", "CHAR(2)", "A", True, "Brazilian state code (UF).", "customers.customer_state", "Upper case", "SP", "", ""),
            C("customer_state_name", "VARCHAR(30)", "A", True, "Full state name.", "Derived", "Lookup from state code", "Sao Paulo", "", ""),
            C("customer_region", "VARCHAR(15)", "A", True, "IBGE macro-region (North, Northeast, Central-West, Southeast, South).", "Derived", "Lookup from state code", "Southeast", "", ""),
            C("customer_latitude", "NUMERIC(9,6)", "A", True, "Approximate latitude of the zip prefix.", "geolocation.geolocation_lat", "Median per zip prefix after removing points outside Brazil; NULL if prefix not found", "-23.727299", "", ""),
            C("customer_longitude", "NUMERIC(9,6)", "A", True, "Approximate longitude of the zip prefix.", "geolocation.geolocation_lng", "As latitude", "-46.542631", "", ""),
            C("first_purchase_date", "DATE", "A", True, "Date of the customer's first order in the dataset.", "orders.order_purchase_timestamp", "MIN over all orders of the person", "2017-05-16", "", ""),
        ],
    },
    {
        "name": "dim_product", "kind": "dimension", "type": "Dimension (SCD Type 1)",
        "grain": "One row per product (product_id), plus one 'Unknown' row (product_key = -1).",
        "natural_key": "product_id", "surrogate_key": "product_key",
        "source": "olist_products_dataset.csv + product_category_name_translation.csv",
        "scd": "Type 1", "est_rows": "32,951 + 1 unknown",
        "hierarchies": ["Product category > Product"],
        "columns": [
            C("product_key", "INTEGER", "PK", False, "Warehouse surrogate key (identity); -1 = unknown.", "Generated", "GENERATED ALWAYS AS IDENTITY", "2001", "", ""),
            C("product_id", "VARCHAR(32)", "NK", False, "Olist product identifier. Business key.", "products.product_id", "Trim", "1e9e8ef04dbcff4541ed26657ea517e5", "", ""),
            C("product_category_name_pt", "VARCHAR(60)", "A", False, "Category name in Portuguese.", "products.product_category_name", "NULL -> 'sem_categoria'", "perfumaria", "", ""),
            C("product_category_name_en", "VARCHAR(60)", "A", False, "Category name in English (used in reports).", "category_translation.product_category_name_english", "Join on Portuguese name; NULL category -> 'uncategorized'; 2 untranslated names mapped manually (DEC-020)", "perfumery", "", ""),
            C("product_name_length", "SMALLINT", "A", True, "Number of characters in the product name.", "products.product_name_lenght", "Rename (source misspelling); cast", "40", "", ""),
            C("product_description_length", "INTEGER", "A", True, "Number of characters in the product description.", "products.product_description_lenght", "Rename (source misspelling); cast", "287", "", ""),
            C("product_photos_qty", "SMALLINT", "A", True, "Number of published product photos.", "products.product_photos_qty", "Cast", "1", "", ""),
            C("product_weight_g", "INTEGER", "A", True, "Product weight in grams.", "products.product_weight_g", "Cast", "225", "", ""),
            C("product_length_cm", "SMALLINT", "A", True, "Package length in cm.", "products.product_length_cm", "Cast", "16", "", ""),
            C("product_height_cm", "SMALLINT", "A", True, "Package height in cm.", "products.product_height_cm", "Cast", "10", "", ""),
            C("product_width_cm", "SMALLINT", "A", True, "Package width in cm.", "products.product_width_cm", "Cast", "14", "", ""),
            C("product_volume_cm3", "INTEGER", "A", True, "Package volume.", "Derived", "length x height x width", "2240", "", ""),
            C("weight_band", "VARCHAR(20)", "A", False, "Weight class for freight analysis.", "Derived", "<0.5 kg / 0.5-2 kg / 2-10 kg / >10 kg / Unknown", "<0.5 kg", "", ""),
        ],
    },
    {
        "name": "dim_seller", "kind": "dimension", "type": "Dimension (SCD Type 1)",
        "grain": "One row per seller (seller_id), plus one 'Unknown' row (seller_key = -1).",
        "natural_key": "seller_id", "surrogate_key": "seller_key",
        "source": "olist_sellers_dataset.csv (+ olist_geolocation_dataset.csv for coordinates)",
        "scd": "Type 1", "est_rows": "3,095 + 1 unknown",
        "hierarchies": ["Region > State > City > Zip code prefix"],
        "columns": [
            C("seller_key", "INTEGER", "PK", False, "Warehouse surrogate key (identity); -1 = unknown.", "Generated", "GENERATED ALWAYS AS IDENTITY", "3001", "", ""),
            C("seller_id", "VARCHAR(32)", "NK", False, "Olist seller identifier. Business key.", "sellers.seller_id", "Trim", "3442f8959a84dea7ee197c632cb2df15", "", ""),
            C("seller_zip_code_prefix", "CHAR(5)", "A", True, "First five digits of the seller's postcode.", "sellers.seller_zip_code_prefix", "Read as text; left-pad to 5 digits", "13023", "", ""),
            C("seller_city", "VARCHAR(100)", "A", True, "Seller city.", "sellers.seller_city", "Trim; title case; remove accents consistently", "Campinas", "", ""),
            C("seller_state", "CHAR(2)", "A", True, "Brazilian state code (UF).", "sellers.seller_state", "Upper case", "SP", "", ""),
            C("seller_state_name", "VARCHAR(30)", "A", True, "Full state name.", "Derived", "Lookup from state code", "Sao Paulo", "", ""),
            C("seller_region", "VARCHAR(15)", "A", True, "IBGE macro-region.", "Derived", "Lookup from state code", "Southeast", "", ""),
            C("seller_latitude", "NUMERIC(9,6)", "A", True, "Approximate latitude of the zip prefix.", "geolocation.geolocation_lat", "Median per zip prefix inside Brazil; NULL if not found", "-22.894561", "", ""),
            C("seller_longitude", "NUMERIC(9,6)", "A", True, "Approximate longitude of the zip prefix.", "geolocation.geolocation_lng", "As latitude", "-47.062380", "", ""),
        ],
    },
    {
        "name": "dim_payment_type", "kind": "dimension", "type": "Small descriptive dimension",
        "grain": "One row per payment method code, plus one 'Unknown' row (payment_type_key = -1).",
        "natural_key": "payment_type_code", "surrogate_key": "payment_type_key",
        "source": "Distinct order_payments.payment_type + manual descriptions",
        "scd": "Type 1", "est_rows": "5 + 1 unknown",
        "hierarchies": ["Payment method group > Payment type"],
        "columns": [
            C("payment_type_key", "SMALLINT", "PK", False, "Surrogate key; -1 = unknown.", "Generated", "Sequence", "1", "", ""),
            C("payment_type_code", "VARCHAR(20)", "NK", False, "Source payment method code.", "payments.payment_type", "Lower case, trim", "credit_card", "", ""),
            C("payment_type_name", "VARCHAR(30)", "A", False, "Readable payment method name.", "Derived", "Manual mapping", "Credit card", "", ""),
            C("payment_method_group", "VARCHAR(15)", "A", False, "Grouping: Card, Bank slip, Voucher, Unknown.", "Derived", "Manual mapping", "Card", "", ""),
        ],
    },
    {
        "name": "dim_order_status", "kind": "dimension", "type": "Small descriptive dimension",
        "grain": "One row per order status code, plus one 'Unknown' row (order_status_key = -1).",
        "natural_key": "order_status_code", "surrogate_key": "order_status_key",
        "source": "Distinct orders.order_status + manual grouping",
        "scd": "Type 1", "est_rows": "8 + 1 unknown",
        "hierarchies": ["Status group > Order status"],
        "columns": [
            C("order_status_key", "SMALLINT", "PK", False, "Surrogate key; -1 = unknown.", "Generated", "Sequence", "6", "", ""),
            C("order_status_code", "VARCHAR(20)", "NK", False, "Source order status.", "orders.order_status", "Lower case, trim", "delivered", "", ""),
            C("order_status_name", "VARCHAR(20)", "A", False, "Readable status name.", "Derived", "Initial capital", "Delivered", "", ""),
            C("status_group", "VARCHAR(15)", "A", False, "Delivered / In progress / Cancelled (canceled + unavailable).", "Derived", "Manual mapping (DEC-009)", "Delivered", "", ""),
            C("is_final_status", "BOOLEAN", "A", False, "TRUE when the order can no longer change (delivered, canceled, unavailable).", "Derived", "Manual mapping", "TRUE", "", ""),
        ],
    },
    # ------------------------------------------------------------------ facts
    {
        "name": "fact_order_items", "kind": "fact", "type": "Transaction fact",
        "process": "Sales (order line items)",
        "grain": "One row per product line within a customer order (order_id + order_item_id). Each row is one unit of one product sold by one seller.",
        "natural_key": "order_id + order_item_id", "surrogate_key": "None (composite degenerate key)",
        "source": "olist_order_items_dataset.csv joined to olist_orders_dataset.csv and olist_customers_dataset.csv for keys",
        "scd": "", "est_rows": "112,650",
        "columns": [
            C("order_id", "VARCHAR(32)", "PK", False, "Order identifier (degenerate dimension). Part of PK.", "order_items.order_id", "Trim", "00010242fe8c5a6d1ba2dd792cb16214", "", ""),
            C("order_item_id", "SMALLINT", "PK", False, "Line sequence within the order (1..21). Part of PK.", "order_items.order_item_id", "Cast", "1", "", ""),
            C("order_purchase_date_key", "INTEGER", "FK", False, "Date the order was placed.", "orders.order_purchase_timestamp", "Date part -> YYYYMMDD", "20170913", "", "dim_date.date_key"),
            C("shipping_limit_date_key", "INTEGER", "FK", False, "Seller's deadline to hand the item to the carrier.", "order_items.shipping_limit_date", "Date part -> YYYYMMDD", "20170919", "", "dim_date.date_key"),
            C("customer_key", "INTEGER", "FK", False, "Customer who placed the order.", "orders.customer_id -> customers.customer_unique_id", "Lookup customer_unique_id in dim_customer; -1 if not found", "1001", "", "dim_customer.customer_key"),
            C("product_key", "INTEGER", "FK", False, "Product sold.", "order_items.product_id", "Lookup in dim_product; -1 if not found", "2001", "", "dim_product.product_key"),
            C("seller_key", "INTEGER", "FK", False, "Seller who sold the item.", "order_items.seller_id", "Lookup in dim_seller; -1 if not found", "3001", "", "dim_seller.seller_key"),
            C("order_status_key", "SMALLINT", "FK", False, "Current status of the parent order (used to exclude cancelled sales).", "orders.order_status", "Lookup in dim_order_status", "6", "", "dim_order_status.order_status_key"),
            C("item_price", "NUMERIC(10,2)", "M", False, "Selling price of the item (BRL), excluding freight.", "order_items.price", "Cast; must be > 0", "58.90", "Additive", ""),
            C("freight_value", "NUMERIC(10,2)", "M", False, "Freight charged for this item (BRL).", "order_items.freight_value", "Cast; must be >= 0", "13.29", "Additive", ""),
            C("item_gross_value", "NUMERIC(10,2)", "M", False, "item_price + freight_value.", "Derived", "Sum of the two measures", "72.19", "Additive", ""),
            C("item_quantity", "SMALLINT", "M", False, "Units on this row (always 1 in source; repeated rows mean quantity > 1).", "Derived", "Constant 1", "1", "Additive", ""),
        ],
    },
    {
        "name": "fact_orders", "kind": "fact", "type": "Accumulating snapshot fact",
        "process": "Order fulfilment lifecycle",
        "grain": "One row per customer order (order_id), updated as the order passes purchase, approval, carrier hand-off and delivery milestones.",
        "natural_key": "order_id", "surrogate_key": "None (degenerate key order_id)",
        "source": "olist_orders_dataset.csv + aggregates of order_items, order_payments and order_reviews per order",
        "scd": "", "est_rows": "99,441",
        "columns": [
            C("order_id", "VARCHAR(32)", "PK", False, "Order identifier (degenerate dimension).", "orders.order_id", "Trim", "e481f51cbdc54678b7cc49136f2d6af7", "", ""),
            C("customer_key", "INTEGER", "FK", False, "Customer who placed the order.", "orders.customer_id -> customers.customer_unique_id", "Lookup in dim_customer", "1001", "", "dim_customer.customer_key"),
            C("order_status_key", "SMALLINT", "FK", False, "Current order status.", "orders.order_status", "Lookup in dim_order_status", "6", "", "dim_order_status.order_status_key"),
            C("order_purchase_date_key", "INTEGER", "FK", False, "Order placed (role: purchase date).", "orders.order_purchase_timestamp", "Date part -> YYYYMMDD", "20171002", "", "dim_date.date_key"),
            C("approved_date_key", "INTEGER", "FK", False, "Payment approved (role: approval date); -1 if not yet.", "orders.order_approved_at", "Date part; NULL -> -1", "20171002", "", "dim_date.date_key"),
            C("carrier_date_key", "INTEGER", "FK", False, "Handed to carrier (role: carrier date); -1 if not yet.", "orders.order_delivered_carrier_date", "Date part; NULL -> -1", "20171004", "", "dim_date.date_key"),
            C("delivered_date_key", "INTEGER", "FK", False, "Delivered to customer (role: delivery date); -1 if not yet.", "orders.order_delivered_customer_date", "Date part; NULL -> -1", "20171010", "", "dim_date.date_key"),
            C("estimated_delivery_date_key", "INTEGER", "FK", False, "Delivery date promised at purchase (role: estimated date).", "orders.order_estimated_delivery_date", "Date part -> YYYYMMDD", "20171018", "", "dim_date.date_key"),
            C("purchase_hour", "SMALLINT", "DD", False, "Hour of day the order was placed (0-23).", "orders.order_purchase_timestamp", "EXTRACT(HOUR)", "10", "", ""),
            C("item_count", "SMALLINT", "M", False, "Number of item rows in the order (0 for orders without items).", "order_items", "COUNT per order_id", "1", "Additive", ""),
            C("order_item_value", "NUMERIC(12,2)", "M", False, "Sum of item_price for the order.", "order_items.price", "SUM per order_id; 0 if no items", "29.99", "Additive", ""),
            C("order_freight_value", "NUMERIC(12,2)", "M", False, "Sum of freight_value for the order.", "order_items.freight_value", "SUM per order_id; 0 if no items", "8.72", "Additive", ""),
            C("order_payment_value", "NUMERIC(12,2)", "M", True, "Total amount paid for the order (all payment records).", "order_payments.payment_value", "SUM per order_id; NULL if no payment record", "38.71", "Additive", ""),
            C("payment_count", "SMALLINT", "M", False, "Number of payment records for the order.", "order_payments", "COUNT per order_id", "3", "Additive", ""),
            C("days_purchase_to_approval", "NUMERIC(7,2)", "M", True, "Elapsed days from purchase to payment approval.", "orders timestamps", "(approved - purchase) in days; NULL if not approved", "0.01", "Non-additive", ""),
            C("days_approval_to_carrier", "NUMERIC(7,2)", "M", True, "Elapsed days from approval to carrier hand-off (seller handling).", "orders timestamps", "(carrier - approved) in days; NULL if missing", "2.37", "Non-additive", ""),
            C("days_carrier_to_customer", "NUMERIC(7,2)", "M", True, "Elapsed days in transit.", "orders timestamps", "(delivered - carrier) in days; NULL if missing", "6.06", "Non-additive", ""),
            C("days_purchase_to_delivery", "NUMERIC(7,2)", "M", True, "Total elapsed days from purchase to delivery.", "orders timestamps", "(delivered - purchase) in days; NULL if not delivered", "8.44", "Non-additive", ""),
            C("days_promised", "NUMERIC(7,2)", "M", False, "Promised lead time: purchase to estimated delivery.", "orders timestamps", "(estimated - purchase) in days", "15.54", "Non-additive", ""),
            C("delivery_delay_days", "INTEGER", "M", True, "Delivered date minus estimated date in whole days (negative = early).", "orders dates", "delivered::date - estimated::date; NULL if not delivered", "-8", "Non-additive", ""),
            C("is_delivered", "SMALLINT", "M", False, "1 if status = delivered and a delivery date exists, else 0.", "Derived", "Flag", "1", "Additive", ""),
            C("is_late", "SMALLINT", "M", True, "1 if delivered after the estimated date, 0 if on time; NULL if not delivered.", "Derived", "delivery_delay_days > 0", "0", "Additive", ""),
            C("customer_order_number", "SMALLINT", "M", False, "Sequence of this order among the customer's orders (1 = first purchase).", "Derived", "ROW_NUMBER() over customer_unique_id ordered by purchase timestamp", "1", "Non-additive", ""),
            C("is_repeat_purchase", "SMALLINT", "M", False, "1 if customer_order_number > 1.", "Derived", "Flag", "0", "Additive", ""),
            C("review_count", "SMALLINT", "M", False, "Number of reviews received for the order.", "order_reviews", "COUNT per order_id", "1", "Additive", ""),
            C("avg_review_score", "NUMERIC(3,2)", "M", True, "Mean review score of the order (1-5); NULL if no review.", "order_reviews.review_score", "AVG per order_id", "4.00", "Non-additive", ""),
        ],
    },
    {
        "name": "fact_payments", "kind": "fact", "type": "Transaction fact",
        "process": "Payment transactions",
        "grain": "One row per payment record of an order (order_id + payment_sequential). An order paid with a card and two vouchers has three rows.",
        "natural_key": "order_id + payment_sequential", "surrogate_key": "None (composite degenerate key)",
        "source": "olist_order_payments_dataset.csv joined to olist_orders_dataset.csv for customer, status and date",
        "scd": "", "est_rows": "103,886",
        "columns": [
            C("order_id", "VARCHAR(32)", "PK", False, "Order identifier (degenerate dimension). Part of PK.", "payments.order_id", "Trim", "b81ef226f3fe1789b1e8b2acac839d17", "", ""),
            C("payment_sequential", "SMALLINT", "PK", False, "Sequence of the payment within the order (1..29). Part of PK.", "payments.payment_sequential", "Cast", "1", "", ""),
            C("order_purchase_date_key", "INTEGER", "FK", False, "Date the order was placed (no separate payment date exists in source).", "orders.order_purchase_timestamp", "Date part -> YYYYMMDD", "20180425", "", "dim_date.date_key"),
            C("customer_key", "INTEGER", "FK", False, "Customer who paid.", "orders.customer_id -> customers.customer_unique_id", "Lookup in dim_customer", "1001", "", "dim_customer.customer_key"),
            C("payment_type_key", "SMALLINT", "FK", False, "Payment method.", "payments.payment_type", "Lookup in dim_payment_type", "1", "", "dim_payment_type.payment_type_key"),
            C("order_status_key", "SMALLINT", "FK", False, "Current status of the parent order.", "orders.order_status", "Lookup in dim_order_status", "6", "", "dim_order_status.order_status_key"),
            C("payment_value", "NUMERIC(10,2)", "M", False, "Amount paid in this payment record (BRL). Not the same as item sales revenue.", "payments.payment_value", "Cast; must be >= 0", "99.33", "Additive", ""),
            C("payment_installments", "SMALLINT", "M", False, "Number of instalments chosen (0 in 2 source rows, treated as 1).", "payments.payment_installments", "Cast; 0 -> 1 (DEC-021)", "8", "Non-additive", ""),
        ],
    },
    {
        "name": "fact_reviews", "kind": "fact", "type": "Transaction fact",
        "process": "Customer reviews (satisfaction)",
        "grain": "One row per review submitted for an order (review_id + order_id). The same review_id can cover more than one order, and an order can receive more than one review.",
        "natural_key": "review_id + order_id", "surrogate_key": "None (composite degenerate key)",
        "source": "olist_order_reviews_dataset.csv joined to olist_orders_dataset.csv for customer",
        "scd": "", "est_rows": "99,224",
        "columns": [
            C("review_id", "VARCHAR(32)", "PK", False, "Review identifier (degenerate). Part of PK.", "reviews.review_id", "Trim", "7bc2406110b926393aa56f80a40eba40", "", ""),
            C("order_id", "VARCHAR(32)", "PK", False, "Reviewed order (degenerate). Part of PK.", "reviews.order_id", "Trim", "73fc7af87114b39712e6da79b0a377eb", "", ""),
            C("customer_key", "INTEGER", "FK", False, "Customer who wrote the review.", "orders.customer_id -> customers.customer_unique_id", "Lookup in dim_customer", "1001", "", "dim_customer.customer_key"),
            C("review_creation_date_key", "INTEGER", "FK", False, "Date the satisfaction survey was sent (role: review date).", "reviews.review_creation_date", "Date part -> YYYYMMDD", "20180118", "", "dim_date.date_key"),
            C("review_answer_date_key", "INTEGER", "FK", False, "Date the customer answered (role: answer date).", "reviews.review_answer_timestamp", "Date part -> YYYYMMDD", "20180118", "", "dim_date.date_key"),
            C("review_score", "SMALLINT", "M", False, "Satisfaction score 1 (worst) to 5 (best).", "reviews.review_score", "Cast; check 1-5", "4", "Non-additive", ""),
            C("response_hours", "NUMERIC(8,2)", "M", False, "Hours between survey creation and customer answer.", "reviews timestamps", "(answer - creation) in hours", "21.78", "Non-additive", ""),
            C("has_comment_title", "SMALLINT", "M", False, "1 if the customer wrote a comment title.", "reviews.review_comment_title", "NOT NULL and not blank -> 1", "0", "Additive", ""),
            C("has_comment_message", "SMALLINT", "M", False, "1 if the customer wrote a comment message.", "reviews.review_comment_message", "NOT NULL and not blank -> 1", "0", "Additive", ""),
        ],
    },
]

TABLE = {t["name"]: t for t in TABLES}
DIMS = [t for t in TABLES if t["kind"] == "dimension"]
FACTS = [t for t in TABLES if t["kind"] == "fact"]


def col(table, name):
    for c in TABLE[table]["columns"]:
        if c[0] == name:
            return c
    raise KeyError(f"{table}.{name}")


def relationships():
    """(fact, fk_column, dimension, dim_pk, role) for every FK."""
    out = []
    for t in FACTS:
        for c in t["columns"]:
            if c[2] == "FK":
                dim, pk = c[9].split(".")
                out.append((t["name"], c[0], dim, pk, c[4]))
    return out


def bus_matrix():
    m = {}
    for fact, fk, dim, _pk, _role in relationships():
        m.setdefault(fact, {}).setdefault(dim, []).append(fk)
    return m


# ------------------------------------------------------------------ measures (business definitions)
MEASURES = [
    # name, definition, fact, expression, additivity, note
    ("Item sales revenue", "Value of goods sold, excluding freight.", "fact_order_items",
     "SUM(item_price) WHERE status_group <> 'Cancelled'", "Additive", "Primary revenue KPI (DEC-016)."),
    ("Freight revenue", "Freight charged to customers.", "fact_order_items",
     "SUM(freight_value) WHERE status_group <> 'Cancelled'", "Additive", "Reported separately from item sales."),
    ("Gross merchandise value (GMV)", "Item price plus freight.", "fact_order_items",
     "SUM(item_gross_value) WHERE status_group <> 'Cancelled'", "Additive", ""),
    ("Units sold", "Number of items sold.", "fact_order_items", "SUM(item_quantity)", "Additive", "Equals row count."),
    ("Order count", "Number of distinct orders.", "fact_orders", "COUNT(*) on fact_orders", "Additive",
     "On fact_order_items use COUNT(DISTINCT order_id)."),
    ("Average order value (AOV)", "Item value per non-cancelled order.", "fact_orders",
     "SUM(order_item_value) / COUNT(*) WHERE status_group <> 'Cancelled' AND item_count > 0", "Non-additive (ratio)", ""),
    ("Amount paid", "Money received from customers across all payment methods.", "fact_payments",
     "SUM(payment_value)", "Additive", "Differs from GMV in 0.31% of orders (vouchers, rounding). Never labelled 'sales revenue'."),
    ("Payment count", "Number of payment records.", "fact_payments", "COUNT(*) on fact_payments", "Additive",
     "An order can have several payment records."),
    ("Average instalments", "Mean instalments per payment record.", "fact_payments",
     "AVG(payment_installments)", "Non-additive", ""),
    ("Cancellation rate", "Share of orders cancelled or unavailable.", "fact_orders",
     "COUNT(status_group = 'Cancelled') / COUNT(*)", "Non-additive (ratio)", ""),
    ("On-time delivery rate", "Share of delivered orders that arrived on or before the estimated date.", "fact_orders",
     "1 - SUM(is_late) / SUM(is_delivered)", "Non-additive (ratio)", "Only delivered orders with a delivery date."),
    ("Average delivery days", "Mean days from purchase to delivery.", "fact_orders",
     "AVG(days_purchase_to_delivery)", "Non-additive", ""),
    ("Average delivery delay", "Mean days delivered after (+) or before (-) the estimate.", "fact_orders",
     "AVG(delivery_delay_days)", "Non-additive", ""),
    ("Repeat customer rate", "Share of customers with more than one order.", "fact_orders",
     "COUNT(DISTINCT customer_key WHERE is_repeat_purchase = 1) / COUNT(DISTINCT customer_key)", "Non-additive (ratio)", ""),
    ("Average review score", "Mean satisfaction score.", "fact_reviews",
     "AVG(review_score)", "Non-additive", "Order-level version: AVG(fact_orders.avg_review_score)."),
    ("Low-score share", "Share of reviews scoring 1 or 2.", "fact_reviews",
     "COUNT(review_score <= 2) / COUNT(*)", "Non-additive (ratio)", ""),
    ("Freight-to-price ratio", "Freight as a share of item price.", "fact_order_items",
     "SUM(freight_value) / SUM(item_price)", "Non-additive (ratio)", ""),
]

# ------------------------------------------------------------------ business requirements / questions
REQUIREMENTS = [
    # id, requirement, stakeholder, process/fact
    ("BR-01", "Track sales revenue, units and orders over time (month, quarter, year) with growth rates.", "Executive management", "Sales"),
    ("BR-02", "Analyse sales by product category and product.", "Category managers", "Sales"),
    ("BR-03", "Analyse sales and seller base by geography (region, state, city) for both customers and sellers.", "Executive management, Marketplace operations", "Sales, Order fulfilment"),
    ("BR-04", "Measure seller contribution and concentration of revenue.", "Marketplace / seller relations", "Sales"),
    ("BR-05", "Report payment method mix, amounts paid and instalment behaviour.", "Finance", "Payments"),
    ("BR-06", "Monitor order status distribution and cancellations.", "Operations", "Order fulfilment"),
    ("BR-07", "Measure delivery performance: lead times per fulfilment stage and delivery against the promised date.", "Logistics / operations", "Order fulfilment"),
    ("BR-08", "Monitor customer satisfaction through review scores and comments.", "Customer experience", "Reviews"),
    ("BR-09", "Relate delivery performance to customer satisfaction at order level.", "Customer experience, Logistics", "Order fulfilment, Reviews"),
    ("BR-10", "Identify new versus repeat customers and their contribution to sales.", "Marketing / CRM", "Order fulfilment, Sales"),
    ("BR-11", "Compare freight cost relative to item price across categories and regions.", "Logistics, Category managers", "Sales"),
    ("BR-12", "All figures must reconcile to the source files (row counts and value totals) and use one agreed definition per KPI.", "BI / data team", "All"),
]

QUESTIONS = [
    # id, question, purpose, measures, dimensions, fact, filters, limitation, BR
    ("BQ-01", "What are monthly item sales revenue and order counts, and what is the month-over-month growth?",
     "Track overall business trend and seasonality (BR-01).",
     ["Item sales revenue", "Order count"], ["dim_date (year > quarter > month)"], ["fact_order_items", "fact_orders"],
     "Purchase date; Jan 2017 - Aug 2018 for trends; exclude Cancelled status group.",
     "Sep-Dec 2016 and Sep-Oct 2018 contain very few orders and are excluded from growth rates.", "BR-01"),
    ("BQ-02", "Which product categories generate the highest item sales revenue and units, and what share of the total does each represent?",
     "Prioritise categories for assortment and marketing (BR-02).",
     ["Item sales revenue", "Units sold"], ["dim_product (category > product)", "dim_date"], ["fact_order_items"],
     "Exclude Cancelled status group.", "610 products have no category ('uncategorized').", "BR-02"),
    ("BQ-03", "Which customer regions and states generate the most revenue and orders, and which have the lowest average order value?",
     "Identify strong and weak markets (BR-03).",
     ["Item sales revenue", "Order count", "Average order value (AOV)"], ["dim_customer (region > state > city)"], ["fact_orders"],
     "Exclude Cancelled status group.", "Customer location is the most recent known address (SCD Type 1).", "BR-03"),
    ("BQ-04", "How concentrated is revenue among sellers (share of the top 10% of sellers), and in which states are the top sellers located?",
     "Assess dependence on a small seller base (BR-04).",
     ["Item sales revenue", "Units sold"], ["dim_seller (region > state)", "dim_date"], ["fact_order_items"],
     "Exclude Cancelled status group.", "No seller cost data: revenue only, not seller profit.", "BR-04"),
    ("BQ-05", "What is the payment method mix by number of payments and by amount paid, and how does it change over time?",
     "Understand customer payment preferences (BR-05).",
     ["Amount paid", "Payment count"], ["dim_payment_type", "dim_date"], ["fact_payments"],
     "Purchase date; all statuses.", "No separate payment date in source; order purchase date is used.", "BR-05"),
    ("BQ-06", "How does the average credit-card payment value change with the number of instalments chosen?",
     "Understand instalment behaviour for high-value purchases (BR-05).",
     ["Amount paid", "Average instalments"], ["dim_payment_type"], ["fact_payments"],
     "payment_type_code = 'credit_card'.", "Instalment interest is not identified in the data.", "BR-05"),
    ("BQ-07", "What share of orders end in each status, and how does the cancellation rate change by month?",
     "Monitor operational failures (BR-06).",
     ["Order count", "Cancellation rate"], ["dim_order_status (group > status)", "dim_date"], ["fact_orders"],
     "Purchase date.", "Status is the final snapshot of the dataset; status history is not available.", "BR-06"),
    ("BQ-08", "What is the on-time delivery rate and the average delivery time by customer state and by month?",
     "Find regions and periods with poor logistics performance (BR-07).",
     ["On-time delivery rate", "Average delivery days", "Average delivery delay"], ["dim_customer (state)", "dim_date (purchase or delivery role)"], ["fact_orders"],
     "is_delivered = 1.", "8 delivered orders lack a delivery date and are excluded.", "BR-07"),
    ("BQ-09", "Which fulfilment stage (approval, seller handling, carrier transit) contributes most to total delivery time, and does this differ by customer region?",
     "Target the right part of the process for improvement (BR-07).",
     ["days_purchase_to_approval", "days_approval_to_carrier", "days_carrier_to_customer"], ["dim_date", "dim_customer (region)"], ["fact_orders"],
     "is_delivered = 1.", "1,359 orders have a carrier date earlier than the approval date; these negative stage durations are flagged in Phase 2 data-quality checks and excluded from stage averages.", "BR-07"),
    ("BQ-10", "What is the distribution of review scores, and how does the average score and low-score share change by month?",
     "Monitor customer satisfaction (BR-08).",
     ["Average review score", "Low-score share"], ["dim_date (review creation role)"], ["fact_reviews"],
     "Review creation date.", "Comment text is not analysed (Portuguese free text); only presence of a comment.", "BR-08"),
    ("BQ-11", "Do orders delivered late receive lower average review scores than orders delivered on time?",
     "Quantify the association between delivery and satisfaction (BR-09).",
     ["avg_review_score", "is_late", "On-time delivery rate"], ["dim_customer", "dim_date"], ["fact_orders"],
     "is_delivered = 1 AND review_count > 0.", "Shows association, not causation.", "BR-09"),
    ("BQ-12", "What share of customers made more than one purchase, and how much revenue comes from repeat orders?",
     "Measure customer retention (BR-10).",
     ["Repeat customer rate", "Item sales revenue"], ["dim_customer"], ["fact_orders"],
     "Exclude Cancelled status group for revenue.", "Only about 3% of customers are repeat buyers; no demographic data exists.", "BR-10"),
    ("BQ-13", "How large is freight relative to item price by product category, weight band and customer region?",
     "Identify where shipping cost may discourage purchases (BR-11).",
     ["Freight-to-price ratio", "Freight revenue"], ["dim_product (category, weight band)", "dim_customer (region)"], ["fact_order_items"],
     "Exclude Cancelled status group.", "Freight charged to customer; actual carrier cost is not available.", "BR-11"),
]

OUT_OF_SCOPE = [
    ("Profit / margin by product or seller", "No cost of goods, commission or carrier cost columns.",
     "Revenue, freight-to-price ratio, AOV."),
    ("Inventory movement / stock snapshots", "No stock level or warehouse data.",
     "Units sold and demand trend by category."),
    ("Promotion / campaign effectiveness", "No promotion, coupon campaign or marketing channel data.",
     "Voucher usage share in payments (descriptive only)."),
    ("Customer demographics (age, gender, income)", "Not in source.",
     "Behavioural segmentation: region, order frequency, spend."),
    ("Product-level or seller-level review analysis", "Reviews are given per order, not per item; 1.3% of orders have several sellers.",
     "Order-level review analysis; seller view limited to single-seller orders if required later."),
    ("Order status history", "Only the final status is provided.",
     "Milestone timestamps in fact_orders."),
]

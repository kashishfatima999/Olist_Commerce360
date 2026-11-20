-- =============================================================================
-- Member 3: Aliyah Rasheed (24L-2544) | Analytics and BI Lead
-- Phase 2 ETL Pipeline Stage 11: load_facts
-- Description: Loads the four physical data warehouse fact tables from cleaned
--              staging tables (project_staging.cln_*) using Business Key -> 
--              Surrogate Key lookups against dimensions (project_dw.dim_*).
--              Unmatched business keys map to the unknown member -1.
--              Idempotent and rebuildable.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. fact_order_items (Transaction Fact)
-- Grain: One row per product line within an order (order_id + order_item_id).
-- Lookups:
--   - customer_key: cln_orders.customer_id -> cln_customers.customer_unique_id -> dim_customer.customer_key
--   - product_key: cln_order_items.product_id -> dim_product.product_key
--   - seller_key: cln_order_items.seller_id -> dim_seller.seller_key
--   - order_status_key: cln_orders.order_status -> dim_order_status.order_status_key
--   - order_purchase_date_key: cln_orders.purchase_ts -> dim_date.date_key
--   - shipping_limit_date_key: cln_order_items.shipping_limit_ts -> dim_date.date_key
-- -----------------------------------------------------------------------------
DELETE FROM project_dw.fact_order_items;

INSERT INTO project_dw.fact_order_items (
    order_id,
    order_item_id,
    order_purchase_date_key,
    shipping_limit_date_key,
    customer_key,
    product_key,
    seller_key,
    order_status_key,
    item_price,
    freight_value,
    item_gross_value,
    item_quantity
)
SELECT
    oi.order_id,
    oi.order_item_id,
    COALESCE(dpurch.date_key, -1) AS order_purchase_date_key,
    COALESCE(dship.date_key, -1) AS shipping_limit_date_key,
    COALESCE(dc.customer_key, -1) AS customer_key,
    COALESCE(dp.product_key, -1) AS product_key,
    COALESCE(ds.seller_key, -1) AS seller_key,
    COALESCE(dos.order_status_key, -1) AS order_status_key,
    oi.price AS item_price,
    oi.freight_value AS freight_value,
    (oi.price + oi.freight_value)::numeric(10,2) AS item_gross_value,
    1::smallint AS item_quantity
FROM project_staging.cln_order_items oi
LEFT JOIN project_staging.cln_orders o ON o.order_id = oi.order_id
LEFT JOIN project_staging.cln_customers c ON c.customer_id = o.customer_id
LEFT JOIN project_dw.dim_customer dc ON dc.customer_unique_id = c.customer_unique_id
LEFT JOIN project_dw.dim_product dp ON dp.product_id = oi.product_id
LEFT JOIN project_dw.dim_seller ds ON ds.seller_id = oi.seller_id
LEFT JOIN project_dw.dim_order_status dos ON dos.order_status_code = o.order_status
LEFT JOIN project_dw.dim_date dpurch ON dpurch.date_key = to_char(o.purchase_ts, 'YYYYMMDD')::integer
LEFT JOIN project_dw.dim_date dship ON dship.date_key = to_char(oi.shipping_limit_ts, 'YYYYMMDD')::integer;

-- -----------------------------------------------------------------------------
-- 2. fact_orders (Accumulating Snapshot Fact)
-- Grain: One row per customer order (order_id), updated across the fulfilment lifecycle.
-- Pre-aggregations:
--   - item_agg: item_count, order_item_value, order_freight_value from cln_order_items
--   - payment_agg: payment_count, order_payment_value from cln_payments
--   - review_agg: review_count, avg_review_score from cln_reviews
--   - cust_orders: customer_order_number (window ROW_NUMBER) for repeat purchase detection
-- -----------------------------------------------------------------------------
DELETE FROM project_dw.fact_orders;

WITH item_agg AS (
    SELECT
        order_id,
        COUNT(*)::smallint AS item_count,
        COALESCE(SUM(price), 0)::numeric(12,2) AS order_item_value,
        COALESCE(SUM(freight_value), 0)::numeric(12,2) AS order_freight_value
    FROM project_staging.cln_order_items
    GROUP BY order_id
),
payment_agg AS (
    SELECT
        order_id,
        COUNT(*)::smallint AS payment_count,
        SUM(payment_value)::numeric(12,2) AS order_payment_value
    FROM project_staging.cln_payments
    GROUP BY order_id
),
review_agg AS (
    SELECT
        order_id,
        COUNT(*)::smallint AS review_count,
        ROUND(AVG(review_score), 2)::numeric(3,2) AS avg_review_score
    FROM project_staging.cln_reviews
    GROUP BY order_id
),
cust_orders AS (
    SELECT
        o.order_id,
        ROW_NUMBER() OVER (
            PARTITION BY COALESCE(c.customer_unique_id, o.customer_id)
            ORDER BY o.purchase_ts, o.order_id
        )::smallint AS customer_order_number
    FROM project_staging.cln_orders o
    LEFT JOIN project_staging.cln_customers c ON c.customer_id = o.customer_id
)
INSERT INTO project_dw.fact_orders (
    order_id,
    customer_key,
    order_status_key,
    order_purchase_date_key,
    approved_date_key,
    carrier_date_key,
    delivered_date_key,
    estimated_delivery_date_key,
    purchase_hour,
    item_count,
    order_item_value,
    order_freight_value,
    order_payment_value,
    payment_count,
    days_purchase_to_approval,
    days_approval_to_carrier,
    days_carrier_to_customer,
    days_purchase_to_delivery,
    days_promised,
    delivery_delay_days,
    is_delivered,
    is_late,
    customer_order_number,
    is_repeat_purchase,
    review_count,
    avg_review_score
)
SELECT
    o.order_id,
    COALESCE(dc.customer_key, -1) AS customer_key,
    COALESCE(dos.order_status_key, -1) AS order_status_key,
    COALESCE(dpurch.date_key, -1) AS order_purchase_date_key,
    COALESCE(dapp.date_key, -1) AS approved_date_key,
    COALESCE(dcarr.date_key, -1) AS carrier_date_key,
    COALESCE(ddeliv.date_key, -1) AS delivered_date_key,
    COALESCE(dest.date_key, -1) AS estimated_delivery_date_key,
    COALESCE(EXTRACT(HOUR FROM o.purchase_ts)::smallint, 0::smallint) AS purchase_hour,
    COALESCE(ia.item_count, 0::smallint) AS item_count,
    COALESCE(ia.order_item_value, 0.00)::numeric(12,2) AS order_item_value,
    COALESCE(ia.order_freight_value, 0.00)::numeric(12,2) AS order_freight_value,
    pa.order_payment_value AS order_payment_value,
    COALESCE(pa.payment_count, 0::smallint) AS payment_count,
    CASE WHEN o.approved_ts IS NOT NULL THEN
        ROUND(EXTRACT(EPOCH FROM (o.approved_ts - o.purchase_ts)) / 86400.0, 2)::numeric(7,2)
    ELSE NULL END AS days_purchase_to_approval,
    CASE WHEN o.carrier_ts IS NOT NULL AND o.approved_ts IS NOT NULL THEN
        ROUND(EXTRACT(EPOCH FROM (o.carrier_ts - o.approved_ts)) / 86400.0, 2)::numeric(7,2)
    ELSE NULL END AS days_approval_to_carrier,
    CASE WHEN o.delivered_ts IS NOT NULL AND o.carrier_ts IS NOT NULL THEN
        ROUND(EXTRACT(EPOCH FROM (o.delivered_ts - o.carrier_ts)) / 86400.0, 2)::numeric(7,2)
    ELSE NULL END AS days_carrier_to_customer,
    CASE WHEN o.delivered_ts IS NOT NULL THEN
        ROUND(EXTRACT(EPOCH FROM (o.delivered_ts - o.purchase_ts)) / 86400.0, 2)::numeric(7,2)
    ELSE NULL END AS days_purchase_to_delivery,
    ROUND(EXTRACT(EPOCH FROM (o.estimated_delivery_date::timestamp - o.purchase_ts)) / 86400.0, 2)::numeric(7,2) AS days_promised,
    CASE WHEN (o.order_status = 'delivered' AND o.delivered_ts IS NOT NULL) THEN
        (o.delivered_ts::date - o.estimated_delivery_date)::integer
    ELSE NULL END AS delivery_delay_days,
    CASE WHEN (o.order_status = 'delivered' AND o.delivered_ts IS NOT NULL) THEN
        1::smallint
    ELSE 0::smallint END AS is_delivered,
    CASE WHEN (o.order_status = 'delivered' AND o.delivered_ts IS NOT NULL) THEN
        CASE WHEN (o.delivered_ts::date - o.estimated_delivery_date) > 0 THEN 1::smallint ELSE 0::smallint END
    ELSE NULL END AS is_late,
    COALESCE(co.customer_order_number, 1::smallint) AS customer_order_number,
    CASE WHEN COALESCE(co.customer_order_number, 1::smallint) > 1 THEN 1::smallint ELSE 0::smallint END AS is_repeat_purchase,
    COALESCE(ra.review_count, 0::smallint) AS review_count,
    ra.avg_review_score AS avg_review_score
FROM project_staging.cln_orders o
LEFT JOIN project_staging.cln_customers c ON c.customer_id = o.customer_id
LEFT JOIN project_dw.dim_customer dc ON dc.customer_unique_id = c.customer_unique_id
LEFT JOIN project_dw.dim_order_status dos ON dos.order_status_code = o.order_status
LEFT JOIN project_dw.dim_date dpurch ON dpurch.date_key = to_char(o.purchase_ts, 'YYYYMMDD')::integer
LEFT JOIN project_dw.dim_date dapp ON dapp.date_key = to_char(o.approved_ts, 'YYYYMMDD')::integer
LEFT JOIN project_dw.dim_date dcarr ON dcarr.date_key = to_char(o.carrier_ts, 'YYYYMMDD')::integer
LEFT JOIN project_dw.dim_date ddeliv ON ddeliv.date_key = to_char(o.delivered_ts, 'YYYYMMDD')::integer
LEFT JOIN project_dw.dim_date dest ON dest.date_key = to_char(o.estimated_delivery_date, 'YYYYMMDD')::integer
LEFT JOIN item_agg ia ON ia.order_id = o.order_id
LEFT JOIN payment_agg pa ON pa.order_id = o.order_id
LEFT JOIN review_agg ra ON ra.order_id = o.order_id
LEFT JOIN cust_orders co ON co.order_id = o.order_id;

-- -----------------------------------------------------------------------------
-- 3. fact_payments (Transaction Fact)
-- Grain: One row per payment record of an order (order_id + payment_sequential).
-- Lookups:
--   - customer_key: cln_orders -> cln_customers -> dim_customer.customer_key
--   - payment_type_key: cln_payments.payment_type -> dim_payment_type.payment_type_key
--   - order_status_key: cln_orders.order_status -> dim_order_status.order_status_key
--   - order_purchase_date_key: cln_orders.purchase_ts -> dim_date.date_key
-- -----------------------------------------------------------------------------
DELETE FROM project_dw.fact_payments;

INSERT INTO project_dw.fact_payments (
    order_id,
    payment_sequential,
    order_purchase_date_key,
    customer_key,
    payment_type_key,
    order_status_key,
    payment_value,
    payment_installments
)
SELECT
    p.order_id,
    p.payment_sequential,
    COALESCE(dpurch.date_key, -1) AS order_purchase_date_key,
    COALESCE(dc.customer_key, -1) AS customer_key,
    COALESCE(dpt.payment_type_key, -1) AS payment_type_key,
    COALESCE(dos.order_status_key, -1) AS order_status_key,
    p.payment_value,
    p.payment_installments
FROM project_staging.cln_payments p
LEFT JOIN project_staging.cln_orders o ON o.order_id = p.order_id
LEFT JOIN project_staging.cln_customers c ON c.customer_id = o.customer_id
LEFT JOIN project_dw.dim_customer dc ON dc.customer_unique_id = c.customer_unique_id
LEFT JOIN project_dw.dim_payment_type dpt ON dpt.payment_type_code = p.payment_type
LEFT JOIN project_dw.dim_order_status dos ON dos.order_status_code = o.order_status
LEFT JOIN project_dw.dim_date dpurch ON dpurch.date_key = to_char(o.purchase_ts, 'YYYYMMDD')::integer;

-- -----------------------------------------------------------------------------
-- 4. fact_reviews (Transaction Fact)
-- Grain: One row per review submitted for an order (review_id + order_id).
-- Lookups:
--   - customer_key: cln_orders -> cln_customers -> dim_customer.customer_key
--   - review_creation_date_key: cln_reviews.creation_ts -> dim_date.date_key
--   - review_answer_date_key: cln_reviews.answer_ts -> dim_date.date_key
-- -----------------------------------------------------------------------------
DELETE FROM project_dw.fact_reviews;

INSERT INTO project_dw.fact_reviews (
    review_id,
    order_id,
    customer_key,
    review_creation_date_key,
    review_answer_date_key,
    review_score,
    response_hours,
    has_comment_title,
    has_comment_message
)
SELECT
    r.review_id,
    r.order_id,
    COALESCE(dc.customer_key, -1) AS customer_key,
    COALESCE(dcreat.date_key, -1) AS review_creation_date_key,
    COALESCE(dans.date_key, -1) AS review_answer_date_key,
    r.review_score,
    GREATEST(0, ROUND(EXTRACT(EPOCH FROM (r.answer_ts - r.creation_ts)) / 3600.0, 2))::numeric(8,2) AS response_hours,
    r.has_comment_title,
    r.has_comment_message
FROM project_staging.cln_reviews r
LEFT JOIN project_staging.cln_orders o ON o.order_id = r.order_id
LEFT JOIN project_staging.cln_customers c ON c.customer_id = o.customer_id
LEFT JOIN project_dw.dim_customer dc ON dc.customer_unique_id = c.customer_unique_id
LEFT JOIN project_dw.dim_date dcreat ON dcreat.date_key = to_char(r.creation_ts, 'YYYYMMDD')::integer
LEFT JOIN project_dw.dim_date dans ON dans.date_key = to_char(r.answer_ts, 'YYYYMMDD')::integer;

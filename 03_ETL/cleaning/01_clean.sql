-- M2 Khadija | PostgreSQL 14+ | rebuildable after M1 staging load

CREATE EXTENSION IF NOT EXISTS unaccent;
CREATE OR REPLACE FUNCTION project_staging.m2_city(t TEXT) RETURNS VARCHAR(100)
LANGUAGE sql STABLE AS $$ SELECT NULLIF(initcap(lower(unaccent(btrim(t)))), '')::varchar(100) $$;
CREATE OR REPLACE FUNCTION project_staging.m2_zip(t TEXT) RETURNS CHAR(5)
LANGUAGE sql IMMUTABLE AS $$ SELECT CASE WHEN btrim(t) ~ '^[0-9]{1,5}$' THEN lpad(btrim(t),5,'0')::char(5) ELSE NULL END $$;
CREATE OR REPLACE FUNCTION project_staging.m2_ts(t TEXT) RETURNS TIMESTAMP
LANGUAGE sql STABLE AS $$ SELECT CASE WHEN btrim(coalesce(t,'')) ~ '^\d{4}-\d{2}-\d{2}( \d{2}:\d{2}:\d{2})?$' THEN btrim(t)::timestamp ELSE NULL END $$;
CREATE OR REPLACE FUNCTION project_staging.m2_num(t TEXT) RETURNS NUMERIC
LANGUAGE sql IMMUTABLE AS $$ SELECT CASE WHEN btrim(coalesce(t,'')) ~ '^[+-]?[0-9]+(\.[0-9]+)?$' THEN btrim(t)::numeric ELSE NULL END $$;

DROP TABLE IF EXISTS project_staging.cln_customers;
CREATE TABLE project_staging.cln_customers AS
SELECT DISTINCT ON (btrim(customer_id)) btrim(customer_id)::varchar(32) customer_id,
 btrim(customer_unique_id)::varchar(32) customer_unique_id,
 project_staging.m2_zip(customer_zip_code_prefix) customer_zip_code_prefix,
 project_staging.m2_city(customer_city) customer_city, upper(btrim(customer_state))::char(2) customer_state
FROM project_staging.stg_customers WHERE nullif(btrim(customer_id),'') IS NOT NULL
ORDER BY btrim(customer_id),stg_row_id DESC;
ALTER TABLE project_staging.cln_customers ADD PRIMARY KEY(customer_id);

DROP TABLE IF EXISTS project_staging.cln_orders;
CREATE TABLE project_staging.cln_orders AS
SELECT DISTINCT ON (btrim(order_id)) btrim(order_id)::varchar(32) order_id, btrim(customer_id)::varchar(32) customer_id,
 lower(btrim(order_status))::varchar(20) order_status,
 project_staging.m2_ts(order_purchase_timestamp) purchase_ts,
 project_staging.m2_ts(order_approved_at) approved_ts,
 project_staging.m2_ts(order_delivered_carrier_date) carrier_ts,
 project_staging.m2_ts(order_delivered_customer_date) delivered_ts,
 project_staging.m2_ts(order_estimated_delivery_date)::date estimated_delivery_date
FROM project_staging.stg_orders WHERE nullif(btrim(order_id),'') IS NOT NULL
ORDER BY btrim(order_id),stg_row_id DESC;
ALTER TABLE project_staging.cln_orders ADD PRIMARY KEY(order_id);
-- TR-13: sequence anomalies remain in cln_orders; never silently drop orders.

DROP TABLE IF EXISTS project_staging.cln_order_items;
CREATE TABLE project_staging.cln_order_items AS
SELECT DISTINCT ON (btrim(order_id),project_staging.m2_num(order_item_id))
 btrim(order_id)::varchar(32) order_id, project_staging.m2_num(order_item_id)::smallint order_item_id,
 btrim(product_id)::varchar(32) product_id,btrim(seller_id)::varchar(32) seller_id,
 project_staging.m2_ts(shipping_limit_date) shipping_limit_ts,
 project_staging.m2_num(price)::numeric(10,2) price,
 project_staging.m2_num(freight_value)::numeric(10,2) freight_value
FROM project_staging.stg_order_items
WHERE nullif(btrim(order_id),'') IS NOT NULL AND project_staging.m2_num(order_item_id) BETWEEN 1 AND 32767
ORDER BY btrim(order_id),project_staging.m2_num(order_item_id),stg_row_id DESC;
ALTER TABLE project_staging.cln_order_items ADD PRIMARY KEY(order_id,order_item_id);

DROP TABLE IF EXISTS project_staging.cln_payments;
CREATE TABLE project_staging.cln_payments AS
SELECT DISTINCT ON (btrim(order_id),project_staging.m2_num(payment_sequential))
 btrim(order_id)::varchar(32) order_id,project_staging.m2_num(payment_sequential)::smallint payment_sequential,
 lower(btrim(payment_type))::varchar(20) payment_type,
 (CASE WHEN project_staging.m2_num(payment_installments)=0 THEN 1 ELSE project_staging.m2_num(payment_installments) END)::smallint payment_installments,
 project_staging.m2_num(payment_value)::numeric(10,2) payment_value
FROM project_staging.stg_order_payments
WHERE nullif(btrim(order_id),'') IS NOT NULL AND project_staging.m2_num(payment_sequential) BETWEEN 1 AND 32767
ORDER BY btrim(order_id),project_staging.m2_num(payment_sequential),stg_row_id DESC;
ALTER TABLE project_staging.cln_payments ADD PRIMARY KEY(order_id,payment_sequential);

DROP TABLE IF EXISTS project_staging.cln_reviews;
CREATE TABLE project_staging.cln_reviews AS
SELECT DISTINCT ON (btrim(review_id),btrim(order_id)) btrim(review_id)::varchar(32) review_id,
 btrim(order_id)::varchar(32) order_id,project_staging.m2_num(review_score)::smallint review_score,
 CASE WHEN nullif(btrim(review_comment_title),'') IS NULL THEN 0 ELSE 1 END::smallint has_comment_title,
 CASE WHEN nullif(btrim(review_comment_message),'') IS NULL THEN 0 ELSE 1 END::smallint has_comment_message,
 project_staging.m2_ts(review_creation_date) creation_ts,project_staging.m2_ts(review_answer_timestamp) answer_ts
FROM project_staging.stg_order_reviews
WHERE nullif(btrim(review_id),'') IS NOT NULL AND nullif(btrim(order_id),'') IS NOT NULL
ORDER BY btrim(review_id),btrim(order_id),stg_row_id DESC;
ALTER TABLE project_staging.cln_reviews ADD PRIMARY KEY(review_id,order_id);

DROP TABLE IF EXISTS project_staging.cln_products;
CREATE TABLE project_staging.cln_products AS
WITH tr AS (SELECT DISTINCT ON (btrim(product_category_name)) btrim(product_category_name) pt,
 btrim(product_category_name_english) en FROM project_staging.stg_category_translation
 WHERE nullif(btrim(product_category_name),'') IS NOT NULL ORDER BY btrim(product_category_name),stg_row_id DESC)
SELECT DISTINCT ON (btrim(p.product_id)) btrim(p.product_id)::varchar(32) product_id,
 coalesce(nullif(btrim(p.product_category_name),''),'sem_categoria')::varchar(60) category_pt,
 (CASE WHEN p.product_category_name IS NULL OR btrim(p.product_category_name)='' THEN 'uncategorized'
 WHEN btrim(p.product_category_name)='pc_gamer' THEN 'pc_gamer'
 WHEN btrim(p.product_category_name)='portateis_cozinha_e_preparadores_de_alimentos' THEN 'portable_kitchen_food_preparers'
 ELSE coalesce(nullif(tr.en,''),btrim(p.product_category_name)) END)::varchar(60) category_en,
 project_staging.m2_num(p.product_name_lenght)::smallint name_length,
 project_staging.m2_num(p.product_description_lenght)::integer description_length,
 project_staging.m2_num(p.product_photos_qty)::smallint photos_qty,
 project_staging.m2_num(p.product_weight_g)::integer weight_g,
 project_staging.m2_num(p.product_length_cm)::smallint length_cm,
 project_staging.m2_num(p.product_height_cm)::smallint height_cm,
 project_staging.m2_num(p.product_width_cm)::smallint width_cm
FROM project_staging.stg_products p LEFT JOIN tr ON tr.pt=btrim(p.product_category_name)
WHERE nullif(btrim(p.product_id),'') IS NOT NULL ORDER BY btrim(p.product_id),p.stg_row_id DESC;
ALTER TABLE project_staging.cln_products ADD PRIMARY KEY(product_id);

DROP TABLE IF EXISTS project_staging.cln_sellers;
CREATE TABLE project_staging.cln_sellers AS
SELECT DISTINCT ON (btrim(seller_id)) btrim(seller_id)::varchar(32) seller_id,
 project_staging.m2_zip(seller_zip_code_prefix) seller_zip_code_prefix,
 project_staging.m2_city(seller_city) seller_city,upper(btrim(seller_state))::char(2) seller_state
FROM project_staging.stg_sellers WHERE nullif(btrim(seller_id),'') IS NOT NULL
ORDER BY btrim(seller_id),stg_row_id DESC;
ALTER TABLE project_staging.cln_sellers ADD PRIMARY KEY(seller_id);

DROP TABLE IF EXISTS project_staging.cln_zip_geo;
CREATE TABLE project_staging.cln_zip_geo AS
SELECT project_staging.m2_zip(geolocation_zip_code_prefix) zip_code_prefix,
 percentile_cont(0.5) WITHIN GROUP (ORDER BY project_staging.m2_num(geolocation_lat))::numeric(9,6) latitude,
 percentile_cont(0.5) WITHIN GROUP (ORDER BY project_staging.m2_num(geolocation_lng))::numeric(9,6) longitude
FROM project_staging.stg_geolocation
WHERE project_staging.m2_zip(geolocation_zip_code_prefix) IS NOT NULL
 AND project_staging.m2_num(geolocation_lat) BETWEEN -34 AND 6
 AND project_staging.m2_num(geolocation_lng) BETWEEN -74 AND -34
GROUP BY project_staging.m2_zip(geolocation_zip_code_prefix);
ALTER TABLE project_staging.cln_zip_geo ADD PRIMARY KEY(zip_code_prefix);

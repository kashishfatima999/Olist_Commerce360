-- M2 Khadija | PostgreSQL 14+ | rebuildable after M1 staging load

-- Dimensions are rebuilt only after M1's create_warehouse stage; do not run while facts exist.
INSERT INTO project_dw.dim_date(date_key) VALUES(-1) ON CONFLICT DO NOTHING;
INSERT INTO project_dw.dim_date(date_key,full_date,day_of_month,day_of_week_num,day_of_week_name,is_weekend,week_of_year,month_num,month_name,year_month,quarter_num,year_quarter,year)
SELECT to_char(day,'YYYYMMDD')::integer,day::date,extract(day from day)::smallint,
 extract(isodow from day)::smallint,to_char(day,'FMDay'),extract(isodow from day) IN (6,7),
 extract(week from day)::smallint,extract(month from day)::smallint,to_char(day,'FMMonth'),
 to_char(day,'YYYY-MM')::char(7),extract(quarter from day)::smallint,
 (to_char(day,'YYYY')||'-Q'||extract(quarter from day)::integer)::char(7),extract(year from day)::smallint
FROM generate_series('2016-01-01'::date,'2018-12-31'::date,interval '1 day') AS day
ON CONFLICT(date_key) DO NOTHING;

DROP TABLE IF EXISTS pg_temp.m2_states;
CREATE TEMP TABLE m2_states(code CHAR(2),state_name VARCHAR(30),region VARCHAR(15)) ON COMMIT PRESERVE ROWS;
INSERT INTO m2_states VALUES ('AC','Acre','North'),
('AP','Amapa','North'),
('AM','Amazonas','North'),
('PA','Para','North'),
('RO','Rondonia','North'),
('RR','Roraima','North'),
('TO','Tocantins','North'),
('AL','Alagoas','Northeast'),
('BA','Bahia','Northeast'),
('CE','Ceara','Northeast'),
('MA','Maranhao','Northeast'),
('PB','Paraiba','Northeast'),
('PE','Pernambuco','Northeast'),
('PI','Piaui','Northeast'),
('RN','Rio Grande do Norte','Northeast'),
('SE','Sergipe','Northeast'),
('DF','Distrito Federal','Central-West'),
('GO','Goias','Central-West'),
('MT','Mato Grosso','Central-West'),
('MS','Mato Grosso do Sul','Central-West'),
('ES','Espirito Santo','Southeast'),
('MG','Minas Gerais','Southeast'),
('RJ','Rio de Janeiro','Southeast'),
('SP','Sao Paulo','Southeast'),
('PR','Parana','South'),
('RS','Rio Grande do Sul','South'),
('SC','Santa Catarina','South');

INSERT INTO project_dw.dim_customer(customer_key,customer_unique_id,customer_city,customer_state)
OVERRIDING SYSTEM VALUE VALUES(-1,'UNKNOWN','Unknown','??') ON CONFLICT DO NOTHING;
WITH latest AS (
 SELECT DISTINCT ON (c.customer_unique_id) c.customer_unique_id,c.customer_zip_code_prefix,c.customer_city,c.customer_state,
 o.purchase_ts::date first_or_last_date
 FROM project_staging.cln_customers c LEFT JOIN project_staging.cln_orders o ON o.customer_id=c.customer_id
 WHERE nullif(c.customer_unique_id,'') IS NOT NULL
 ORDER BY c.customer_unique_id,o.purchase_ts DESC NULLS LAST,c.customer_id DESC
), firsts AS (
 SELECT c.customer_unique_id,min(o.purchase_ts::date) first_purchase_date
 FROM project_staging.cln_customers c LEFT JOIN project_staging.cln_orders o ON o.customer_id=c.customer_id
 GROUP BY c.customer_unique_id
)
INSERT INTO project_dw.dim_customer(customer_unique_id,customer_zip_code_prefix,customer_city,customer_state,customer_state_name,customer_region,customer_latitude,customer_longitude,first_purchase_date)
SELECT l.customer_unique_id,l.customer_zip_code_prefix,l.customer_city,coalesce(l.customer_state,'??'),s.state_name,s.region,g.latitude,g.longitude,f.first_purchase_date
FROM latest l LEFT JOIN firsts f ON f.customer_unique_id=l.customer_unique_id
LEFT JOIN m2_states s ON s.code=l.customer_state
LEFT JOIN project_staging.cln_zip_geo g ON g.zip_code_prefix=l.customer_zip_code_prefix
ON CONFLICT(customer_unique_id) DO UPDATE SET
 customer_zip_code_prefix=excluded.customer_zip_code_prefix,customer_city=excluded.customer_city,
 customer_state=excluded.customer_state,customer_state_name=excluded.customer_state_name,
 customer_region=excluded.customer_region,customer_latitude=excluded.customer_latitude,
 customer_longitude=excluded.customer_longitude,first_purchase_date=excluded.first_purchase_date;

INSERT INTO project_dw.dim_seller(seller_key,seller_id,seller_city,seller_state)
OVERRIDING SYSTEM VALUE VALUES(-1,'UNKNOWN','Unknown','??') ON CONFLICT DO NOTHING;
INSERT INTO project_dw.dim_seller(seller_id,seller_zip_code_prefix,seller_city,seller_state,seller_state_name,seller_region,seller_latitude,seller_longitude)
SELECT s.seller_id,s.seller_zip_code_prefix,s.seller_city,coalesce(s.seller_state,'??'),st.state_name,st.region,g.latitude,g.longitude
FROM project_staging.cln_sellers s LEFT JOIN m2_states st ON st.code=s.seller_state
LEFT JOIN project_staging.cln_zip_geo g ON g.zip_code_prefix=s.seller_zip_code_prefix
ON CONFLICT(seller_id) DO UPDATE SET seller_zip_code_prefix=excluded.seller_zip_code_prefix,
 seller_city=excluded.seller_city,seller_state=excluded.seller_state,seller_state_name=excluded.seller_state_name,
 seller_region=excluded.seller_region,seller_latitude=excluded.seller_latitude,seller_longitude=excluded.seller_longitude;

INSERT INTO project_dw.dim_product(product_key,product_id,product_category_name_pt,product_category_name_en,weight_band)
OVERRIDING SYSTEM VALUE VALUES(-1,'UNKNOWN','sem_categoria','uncategorized','Unknown') ON CONFLICT DO NOTHING;
INSERT INTO project_dw.dim_product(product_id,product_category_name_pt,product_category_name_en,product_name_length,
 product_description_length,product_photos_qty,product_weight_g,product_length_cm,product_height_cm,product_width_cm,product_volume_cm3,weight_band)
SELECT product_id,category_pt,category_en,name_length,description_length,photos_qty,weight_g,length_cm,height_cm,width_cm,
 (length_cm::bigint*height_cm*width_cm)::integer,
 CASE WHEN weight_g IS NULL THEN 'Unknown' WHEN weight_g<500 THEN '<0.5 kg'
 WHEN weight_g<2000 THEN '0.5-2 kg' WHEN weight_g<10000 THEN '2-10 kg' ELSE '>10 kg' END
FROM project_staging.cln_products
ON CONFLICT(product_id) DO UPDATE SET product_category_name_pt=excluded.product_category_name_pt,
 product_category_name_en=excluded.product_category_name_en,product_name_length=excluded.product_name_length,
 product_description_length=excluded.product_description_length,product_photos_qty=excluded.product_photos_qty,
 product_weight_g=excluded.product_weight_g,product_length_cm=excluded.product_length_cm,
 product_height_cm=excluded.product_height_cm,product_width_cm=excluded.product_width_cm,
 product_volume_cm3=excluded.product_volume_cm3,weight_band=excluded.weight_band;

INSERT INTO project_dw.dim_payment_type(payment_type_key,payment_type_code,payment_type_name,payment_method_group)
OVERRIDING SYSTEM VALUE VALUES(-1,'UNKNOWN','Unknown','Unknown') ON CONFLICT DO NOTHING;
INSERT INTO project_dw.dim_payment_type(payment_type_code,payment_type_name,payment_method_group)
SELECT DISTINCT p.payment_type,
 CASE p.payment_type WHEN 'credit_card' THEN 'Credit card' WHEN 'debit_card' THEN 'Debit card'
 WHEN 'boleto' THEN 'Boleto (bank slip)' WHEN 'voucher' THEN 'Voucher' WHEN 'not_defined' THEN 'Not defined'
 ELSE 'Unknown' END,
 CASE p.payment_type WHEN 'credit_card' THEN 'Card' WHEN 'debit_card' THEN 'Card'
 WHEN 'boleto' THEN 'Bank slip' WHEN 'voucher' THEN 'Voucher' ELSE 'Unknown' END
FROM project_staging.cln_payments p WHERE nullif(p.payment_type,'') IS NOT NULL
ON CONFLICT(payment_type_code) DO UPDATE SET payment_type_name=excluded.payment_type_name,payment_method_group=excluded.payment_method_group;

INSERT INTO project_dw.dim_order_status(order_status_key,order_status_code,order_status_name,status_group,is_final_status)
OVERRIDING SYSTEM VALUE VALUES(-1,'UNKNOWN','Unknown','Unknown',false) ON CONFLICT DO NOTHING;
INSERT INTO project_dw.dim_order_status(order_status_code,order_status_name,status_group,is_final_status)
SELECT DISTINCT o.order_status,initcap(o.order_status),
 CASE WHEN o.order_status='delivered' THEN 'Delivered'
 WHEN o.order_status IN ('canceled','unavailable') THEN 'Cancelled' ELSE 'In progress' END,
 o.order_status IN ('delivered','canceled','unavailable')
FROM project_staging.cln_orders o WHERE nullif(o.order_status,'') IS NOT NULL
ON CONFLICT(order_status_code) DO UPDATE SET order_status_name=excluded.order_status_name,
 status_group=excluded.status_group,is_final_status=excluded.is_final_status;

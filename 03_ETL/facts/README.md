# 03_ETL/facts (owner: M3, Aliyah Rasheed)

This folder loads the 4 fact tables from the `project_staging.cln_*` tables, looking up each surrogate key in the dimensions (`project_dw.dim_*`). A business key that is not found maps to the unknown member `-1`.

Status: **Implemented and verified** (pipeline stage `load_facts`).

## Scripts
- `01_facts.sql`: Loads `fact_order_items`, `fact_orders`, `fact_payments`, and `fact_reviews`.

## Grain and Business Key -> Surrogate Key Lookups
1. **`fact_order_items`**: Grain is `(order_id, order_item_id)`.
   - `customer_key` looked up via `cln_orders.customer_id -> cln_customers.customer_unique_id -> dim_customer.customer_key`.
   - `product_key` looked up via `cln_order_items.product_id -> dim_product.product_key`.
   - `seller_key` looked up via `cln_order_items.seller_id -> dim_seller.seller_key`.
   - `order_status_key` looked up via `cln_orders.order_status -> dim_order_status.order_status_key`.
   - `order_purchase_date_key` and `shipping_limit_date_key` mapped to `dim_date.date_key`.
   - Measures: `item_price`, `freight_value`, `item_gross_value` (`item_price + freight_value`), `item_quantity = 1`.

2. **`fact_orders`**: Grain is `order_id` (accumulating snapshot).
   - Pre-aggregates computed in CTEs before joining (TR-14, DEC-019, rules G-01 to G-08):
     - `item_agg`: `item_count`, `order_item_value`, `order_freight_value`.
     - `payment_agg`: `payment_count`, `order_payment_value`.
     - `review_agg`: `review_count`, `avg_review_score`.
     - `cust_orders`: `customer_order_number` via `ROW_NUMBER()` window function and `is_repeat_purchase`.
   - Milestone date keys: purchase, approval, carrier hand-off, delivery, promised delivery. Unreached milestones map to `-1`.
   - Lags and lead times: `days_purchase_to_approval`, `days_approval_to_carrier`, `days_carrier_to_customer`, `days_purchase_to_delivery`, `days_promised`, `delivery_delay_days`.
   - Lateness flag `is_late` is populated ONLY when `is_delivered = 1` (satisfying constraint `ck_fact_orders_13`).

3. **`fact_payments`**: Grain is `(order_id, payment_sequential)`.
   - Dimension lookups for customer, status, payment type, and purchase date.
   - Measures: `payment_value`, `payment_installments`.

4. **`fact_reviews`**: Grain is `(review_id, order_id)`.
   - Lookups for customer and role-playing dates (survey creation date, answer date).
   - Measures: `review_score` (1-5), `response_hours` (`GREATEST(0, answer - creation)`), `has_comment_title`, `has_comment_message`.

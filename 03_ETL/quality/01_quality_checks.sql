-- =============================================================================
-- Member 3: Aliyah Rasheed (24L-2544) | Analytics and BI Lead
-- Phase 2 ETL Pipeline Stage 12: quality_checks
-- Description: Rigorous automated data quality validation enforcing:
--              1. Completeness (missing values, row counts, unknown members)
--              2. Accuracy & Reconciliation (financial sums, cross-table checks)
--              3. Integrity (foreign key validation, 0 orphan records, PK uniqueness)
--              Throws a loud exception (RAISE EXCEPTION) if any check fails.
-- =============================================================================

DO $$
DECLARE
    v_count BIGINT;
    v_diff NUMERIC;
    v_orphans BIGINT;
    v_fact_sum NUMERIC;
    v_stage_sum NUMERIC;
BEGIN
    RAISE NOTICE '=======================================================';
    RAISE NOTICE 'Starting Phase 2 Member 3 Data Quality Validation Suite';
    RAISE NOTICE '=======================================================';

    -- =========================================================================
    -- SECTION 1: COMPLETENESS CHECKS
    -- =========================================================================

    -- 1.1 Minimum Dimension Row Count (Rubric: Dimension records 100+)
    SELECT COUNT(*) INTO v_count FROM project_dw.dim_customer;
    IF v_count < 100 THEN
        RAISE EXCEPTION 'Quality check failed: dim_customer has % rows, expected >= 100', v_count;
    END IF;
    RAISE NOTICE 'PASS: dim_customer completeness (% rows >= 100)', v_count;

    SELECT COUNT(*) INTO v_count FROM project_dw.dim_product;
    IF v_count < 100 THEN
        RAISE EXCEPTION 'Quality check failed: dim_product has % rows, expected >= 100', v_count;
    END IF;
    RAISE NOTICE 'PASS: dim_product completeness (% rows >= 100)', v_count;

    SELECT COUNT(*) INTO v_count FROM project_dw.dim_seller;
    IF v_count < 100 THEN
        RAISE EXCEPTION 'Quality check failed: dim_seller has % rows, expected >= 100', v_count;
    END IF;
    RAISE NOTICE 'PASS: dim_seller completeness (% rows >= 100)', v_count;

    SELECT COUNT(*) INTO v_count FROM project_dw.dim_date;
    IF v_count < 100 THEN
        RAISE EXCEPTION 'Quality check failed: dim_date has % rows, expected >= 100', v_count;
    END IF;
    RAISE NOTICE 'PASS: dim_date completeness (% rows >= 100)', v_count;

    -- 1.2 Minimum Fact Row Count (Rubric: Fact records 10,000+)
    SELECT COUNT(*) INTO v_count FROM project_dw.fact_order_items;
    IF v_count < 10000 THEN
        RAISE EXCEPTION 'Quality check failed: fact_order_items has % rows, expected >= 10,000', v_count;
    END IF;
    RAISE NOTICE 'PASS: fact_order_items completeness (% rows >= 10,000)', v_count;

    SELECT COUNT(*) INTO v_count FROM project_dw.fact_orders;
    IF v_count < 10000 THEN
        RAISE EXCEPTION 'Quality check failed: fact_orders has % rows, expected >= 10,000', v_count;
    END IF;
    RAISE NOTICE 'PASS: fact_orders completeness (% rows >= 10,000)', v_count;

    SELECT COUNT(*) INTO v_count FROM project_dw.fact_payments;
    IF v_count < 10000 THEN
        RAISE EXCEPTION 'Quality check failed: fact_payments has % rows, expected >= 10,000', v_count;
    END IF;
    RAISE NOTICE 'PASS: fact_payments completeness (% rows >= 10,000)', v_count;

    SELECT COUNT(*) INTO v_count FROM project_dw.fact_reviews;
    IF v_count < 10000 THEN
        RAISE EXCEPTION 'Quality check failed: fact_reviews has % rows, expected >= 10,000', v_count;
    END IF;
    RAISE NOTICE 'PASS: fact_reviews completeness (% rows >= 10,000)', v_count;

    -- 1.3 Unknown Member (-1) Presence in all Dimensions
    IF NOT EXISTS (SELECT 1 FROM project_dw.dim_customer WHERE customer_key = -1) THEN
        RAISE EXCEPTION 'Quality check failed: dim_customer is missing unknown member -1';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM project_dw.dim_product WHERE product_key = -1) THEN
        RAISE EXCEPTION 'Quality check failed: dim_product is missing unknown member -1';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM project_dw.dim_seller WHERE seller_key = -1) THEN
        RAISE EXCEPTION 'Quality check failed: dim_seller is missing unknown member -1';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM project_dw.dim_date WHERE date_key = -1) THEN
        RAISE EXCEPTION 'Quality check failed: dim_date is missing unknown member -1';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM project_dw.dim_payment_type WHERE payment_type_key = -1) THEN
        RAISE EXCEPTION 'Quality check failed: dim_payment_type is missing unknown member -1';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM project_dw.dim_order_status WHERE order_status_key = -1) THEN
        RAISE EXCEPTION 'Quality check failed: dim_order_status is missing unknown member -1';
    END IF;
    RAISE NOTICE 'PASS: Unknown member (-1) verified in all 6 dimensions';

    -- 1.4 Primary Key NULL checks in Facts
    SELECT COUNT(*) INTO v_count FROM project_dw.fact_order_items WHERE order_id IS NULL OR order_item_id IS NULL;
    IF v_count > 0 THEN
        RAISE EXCEPTION 'Quality check failed: fact_order_items contains % rows with NULL PK', v_count;
    END IF;

    SELECT COUNT(*) INTO v_count FROM project_dw.fact_orders WHERE order_id IS NULL;
    IF v_count > 0 THEN
        RAISE EXCEPTION 'Quality check failed: fact_orders contains % rows with NULL PK', v_count;
    END IF;

    SELECT COUNT(*) INTO v_count FROM project_dw.fact_payments WHERE order_id IS NULL OR payment_sequential IS NULL;
    IF v_count > 0 THEN
        RAISE EXCEPTION 'Quality check failed: fact_payments contains % rows with NULL PK', v_count;
    END IF;

    SELECT COUNT(*) INTO v_count FROM project_dw.fact_reviews WHERE review_id IS NULL OR order_id IS NULL;
    IF v_count > 0 THEN
        RAISE EXCEPTION 'Quality check failed: fact_reviews contains % rows with NULL PK', v_count;
    END IF;
    RAISE NOTICE 'PASS: Primary key completeness (zero NULL keys across all facts)';

    -- =========================================================================
    -- SECTION 2: ACCURACY & RECONCILIATION CHECKS
    -- =========================================================================

    -- 2.1 Item Price Reconciliation (Source / Cleaned Staging vs Fact)
    SELECT COALESCE(SUM(price), 0) INTO v_stage_sum FROM project_staging.cln_order_items;
    SELECT COALESCE(SUM(item_price), 0) INTO v_fact_sum FROM project_dw.fact_order_items;
    v_diff := ABS(v_fact_sum - v_stage_sum);
    IF v_diff > 0.01 THEN
        RAISE EXCEPTION 'Quality check failed: item_price mismatch. Staging=%, Fact=%, Diff=%', v_stage_sum, v_fact_sum, v_diff;
    END IF;
    IF v_stage_sum > 0 AND ABS(v_fact_sum - 13591643.70) > 0.01 THEN
        RAISE EXCEPTION 'Quality check failed: item_price sum % does not match target 13,591,643.70', v_fact_sum;
    END IF;
    RAISE NOTICE 'PASS: Item price reconciliation (Fact sum % = Staging sum %)', v_fact_sum, v_stage_sum;

    -- 2.2 Freight Value Reconciliation (Source / Cleaned Staging vs Fact)
    SELECT COALESCE(SUM(freight_value), 0) INTO v_stage_sum FROM project_staging.cln_order_items;
    SELECT COALESCE(SUM(freight_value), 0) INTO v_fact_sum FROM project_dw.fact_order_items;
    v_diff := ABS(v_fact_sum - v_stage_sum);
    IF v_diff > 0.01 THEN
        RAISE EXCEPTION 'Quality check failed: freight_value mismatch. Staging=%, Fact=%, Diff=%', v_stage_sum, v_fact_sum, v_diff;
    END IF;
    IF v_stage_sum > 0 AND ABS(v_fact_sum - 2251909.54) > 0.01 THEN
        RAISE EXCEPTION 'Quality check failed: freight_value sum % does not match target 2,251,909.54', v_fact_sum;
    END IF;
    RAISE NOTICE 'PASS: Freight value reconciliation (Fact sum % = Staging sum %)', v_fact_sum, v_stage_sum;

    -- 2.3 Gross Item Value Formula Check (item_gross_value = item_price + freight_value)
    SELECT COUNT(*) INTO v_count FROM project_dw.fact_order_items
    WHERE item_gross_value <> (item_price + freight_value);
    IF v_count > 0 THEN
        RAISE EXCEPTION 'Quality check failed: fact_order_items has % rows where item_gross_value != item_price + freight_value', v_count;
    END IF;
    RAISE NOTICE 'PASS: Gross item value additive formula check passed on all rows';

    -- 2.4 Payment Value Reconciliation
    SELECT COALESCE(SUM(payment_value), 0) INTO v_stage_sum FROM project_staging.cln_payments;
    SELECT COALESCE(SUM(payment_value), 0) INTO v_fact_sum FROM project_dw.fact_payments;
    v_diff := ABS(v_fact_sum - v_stage_sum);
    IF v_diff > 0.01 THEN
        RAISE EXCEPTION 'Quality check failed: payment_value mismatch. Staging=%, Fact=%, Diff=%', v_stage_sum, v_fact_sum, v_diff;
    END IF;
    IF v_stage_sum > 0 AND ABS(v_fact_sum - 16008872.12) > 0.01 THEN
        RAISE EXCEPTION 'Quality check failed: payment_value sum % does not match target 16,008,872.12', v_fact_sum;
    END IF;
    RAISE NOTICE 'PASS: Payment value reconciliation (Fact sum % = Staging sum %)', v_fact_sum, v_stage_sum;

    -- 2.5 Cross-Table Reconciliation (fact_orders vs fact_order_items)
    SELECT COALESCE(SUM(order_item_value), 0) INTO v_fact_sum FROM project_dw.fact_orders;
    SELECT COALESCE(SUM(item_price), 0) INTO v_stage_sum FROM project_dw.fact_order_items;
    IF ABS(v_fact_sum - v_stage_sum) > 0.01 THEN
        RAISE EXCEPTION 'Quality check failed: fact_orders.order_item_value (%) != fact_order_items.item_price (%)', v_fact_sum, v_stage_sum;
    END IF;

    SELECT COALESCE(SUM(order_freight_value), 0) INTO v_fact_sum FROM project_dw.fact_orders;
    SELECT COALESCE(SUM(freight_value), 0) INTO v_stage_sum FROM project_dw.fact_order_items;
    IF ABS(v_fact_sum - v_stage_sum) > 0.01 THEN
        RAISE EXCEPTION 'Quality check failed: fact_orders.order_freight_value (%) != fact_order_items.freight_value (%)', v_fact_sum, v_stage_sum;
    END IF;

    SELECT COALESCE(SUM(item_count), 0) INTO v_fact_sum FROM project_dw.fact_orders;
    SELECT COUNT(*) INTO v_count FROM project_dw.fact_order_items;
    IF v_fact_sum <> v_count THEN
        RAISE EXCEPTION 'Quality check failed: fact_orders.item_count sum (%) != fact_order_items row count (%)', v_fact_sum, v_count;
    END IF;
    RAISE NOTICE 'PASS: Cross-table fact_orders vs fact_order_items reconciliation';

    -- 2.6 Cross-Table Reconciliation (fact_orders vs fact_payments)
    SELECT COALESCE(SUM(payment_count), 0) INTO v_fact_sum FROM project_dw.fact_orders;
    SELECT COUNT(*) INTO v_count FROM project_dw.fact_payments;
    IF v_fact_sum <> v_count THEN
        RAISE EXCEPTION 'Quality check failed: fact_orders.payment_count sum (%) != fact_payments row count (%)', v_fact_sum, v_count;
    END IF;

    SELECT COALESCE(SUM(order_payment_value), 0) INTO v_fact_sum FROM project_dw.fact_orders WHERE order_payment_value IS NOT NULL;
    SELECT COALESCE(SUM(payment_value), 0) INTO v_stage_sum FROM project_dw.fact_payments;
    IF ABS(v_fact_sum - v_stage_sum) > 0.01 THEN
        RAISE EXCEPTION 'Quality check failed: fact_orders.order_payment_value sum (%) != fact_payments.payment_value sum (%)', v_fact_sum, v_stage_sum;
    END IF;
    RAISE NOTICE 'PASS: Cross-table fact_orders vs fact_payments reconciliation';

    -- 2.7 Delivery Logic Integrity (is_delivered and is_late constraints)
    SELECT COUNT(*) INTO v_count FROM project_dw.fact_orders
    WHERE is_delivered = 0 AND (is_late IS NOT NULL OR delivery_delay_days IS NOT NULL);
    IF v_count > 0 THEN
        RAISE EXCEPTION 'Quality check failed: % non-delivered orders have non-null lateness or delay days', v_count;
    END IF;
    RAISE NOTICE 'PASS: Delivery logic integrity (lateness conditionally populated)';

    -- =========================================================================
    -- SECTION 3: REFERENTIAL INTEGRITY (ZERO ORPHAN CHECKS)
    -- =========================================================================

    -- 3.1 fact_order_items Foreign Keys
    SELECT COUNT(*) INTO v_orphans FROM project_dw.fact_order_items f
    LEFT JOIN project_dw.dim_customer d ON d.customer_key = f.customer_key
    WHERE d.customer_key IS NULL;
    IF v_orphans > 0 THEN
        RAISE EXCEPTION 'Integrity check failed: fact_order_items has % orphan customer_key records', v_orphans;
    END IF;

    SELECT COUNT(*) INTO v_orphans FROM project_dw.fact_order_items f
    LEFT JOIN project_dw.dim_product d ON d.product_key = f.product_key
    WHERE d.product_key IS NULL;
    IF v_orphans > 0 THEN
        RAISE EXCEPTION 'Integrity check failed: fact_order_items has % orphan product_key records', v_orphans;
    END IF;

    SELECT COUNT(*) INTO v_orphans FROM project_dw.fact_order_items f
    LEFT JOIN project_dw.dim_seller d ON d.seller_key = f.seller_key
    WHERE d.seller_key IS NULL;
    IF v_orphans > 0 THEN
        RAISE EXCEPTION 'Integrity check failed: fact_order_items has % orphan seller_key records', v_orphans;
    END IF;

    SELECT COUNT(*) INTO v_orphans FROM project_dw.fact_order_items f
    LEFT JOIN project_dw.dim_order_status d ON d.order_status_key = f.order_status_key
    WHERE d.order_status_key IS NULL;
    IF v_orphans > 0 THEN
        RAISE EXCEPTION 'Integrity check failed: fact_order_items has % orphan order_status_key records', v_orphans;
    END IF;

    SELECT COUNT(*) INTO v_orphans FROM project_dw.fact_order_items f
    LEFT JOIN project_dw.dim_date d ON d.date_key = f.order_purchase_date_key
    WHERE d.date_key IS NULL;
    IF v_orphans > 0 THEN
        RAISE EXCEPTION 'Integrity check failed: fact_order_items has % orphan order_purchase_date_key records', v_orphans;
    END IF;

    SELECT COUNT(*) INTO v_orphans FROM project_dw.fact_order_items f
    LEFT JOIN project_dw.dim_date d ON d.date_key = f.shipping_limit_date_key
    WHERE d.date_key IS NULL;
    IF v_orphans > 0 THEN
        RAISE EXCEPTION 'Integrity check failed: fact_order_items has % orphan shipping_limit_date_key records', v_orphans;
    END IF;
    RAISE NOTICE 'PASS: fact_order_items zero orphan foreign keys (6/6 FK relationships validated)';

    -- 3.2 fact_orders Foreign Keys
    SELECT COUNT(*) INTO v_orphans FROM project_dw.fact_orders f
    LEFT JOIN project_dw.dim_customer d ON d.customer_key = f.customer_key
    WHERE d.customer_key IS NULL;
    IF v_orphans > 0 THEN
        RAISE EXCEPTION 'Integrity check failed: fact_orders has % orphan customer_key records', v_orphans;
    END IF;

    SELECT COUNT(*) INTO v_orphans FROM project_dw.fact_orders f
    LEFT JOIN project_dw.dim_order_status d ON d.order_status_key = f.order_status_key
    WHERE d.order_status_key IS NULL;
    IF v_orphans > 0 THEN
        RAISE EXCEPTION 'Integrity check failed: fact_orders has % orphan order_status_key records', v_orphans;
    END IF;

    SELECT COUNT(*) INTO v_orphans FROM project_dw.fact_orders f
    LEFT JOIN project_dw.dim_date d ON d.date_key = f.order_purchase_date_key
    WHERE d.date_key IS NULL;
    IF v_orphans > 0 THEN
        RAISE EXCEPTION 'Integrity check failed: fact_orders has % orphan order_purchase_date_key records', v_orphans;
    END IF;

    SELECT COUNT(*) INTO v_orphans FROM project_dw.fact_orders f
    LEFT JOIN project_dw.dim_date d ON d.date_key = f.approved_date_key
    WHERE d.date_key IS NULL;
    IF v_orphans > 0 THEN
        RAISE EXCEPTION 'Integrity check failed: fact_orders has % orphan approved_date_key records', v_orphans;
    END IF;

    SELECT COUNT(*) INTO v_orphans FROM project_dw.fact_orders f
    LEFT JOIN project_dw.dim_date d ON d.date_key = f.carrier_date_key
    WHERE d.date_key IS NULL;
    IF v_orphans > 0 THEN
        RAISE EXCEPTION 'Integrity check failed: fact_orders has % orphan carrier_date_key records', v_orphans;
    END IF;

    SELECT COUNT(*) INTO v_orphans FROM project_dw.fact_orders f
    LEFT JOIN project_dw.dim_date d ON d.date_key = f.delivered_date_key
    WHERE d.date_key IS NULL;
    IF v_orphans > 0 THEN
        RAISE EXCEPTION 'Integrity check failed: fact_orders has % orphan delivered_date_key records', v_orphans;
    END IF;

    SELECT COUNT(*) INTO v_orphans FROM project_dw.fact_orders f
    LEFT JOIN project_dw.dim_date d ON d.date_key = f.estimated_delivery_date_key
    WHERE d.date_key IS NULL;
    IF v_orphans > 0 THEN
        RAISE EXCEPTION 'Integrity check failed: fact_orders has % orphan estimated_delivery_date_key records', v_orphans;
    END IF;
    RAISE NOTICE 'PASS: fact_orders zero orphan foreign keys (7/7 FK relationships validated)';

    -- 3.3 fact_payments Foreign Keys
    SELECT COUNT(*) INTO v_orphans FROM project_dw.fact_payments f
    LEFT JOIN project_dw.dim_customer d ON d.customer_key = f.customer_key
    WHERE d.customer_key IS NULL;
    IF v_orphans > 0 THEN
        RAISE EXCEPTION 'Integrity check failed: fact_payments has % orphan customer_key records', v_orphans;
    END IF;

    SELECT COUNT(*) INTO v_orphans FROM project_dw.fact_payments f
    LEFT JOIN project_dw.dim_payment_type d ON d.payment_type_key = f.payment_type_key
    WHERE d.payment_type_key IS NULL;
    IF v_orphans > 0 THEN
        RAISE EXCEPTION 'Integrity check failed: fact_payments has % orphan payment_type_key records', v_orphans;
    END IF;

    SELECT COUNT(*) INTO v_orphans FROM project_dw.fact_payments f
    LEFT JOIN project_dw.dim_order_status d ON d.order_status_key = f.order_status_key
    WHERE d.order_status_key IS NULL;
    IF v_orphans > 0 THEN
        RAISE EXCEPTION 'Integrity check failed: fact_payments has % orphan order_status_key records', v_orphans;
    END IF;

    SELECT COUNT(*) INTO v_orphans FROM project_dw.fact_payments f
    LEFT JOIN project_dw.dim_date d ON d.date_key = f.order_purchase_date_key
    WHERE d.date_key IS NULL;
    IF v_orphans > 0 THEN
        RAISE EXCEPTION 'Integrity check failed: fact_payments has % orphan order_purchase_date_key records', v_orphans;
    END IF;
    RAISE NOTICE 'PASS: fact_payments zero orphan foreign keys (4/4 FK relationships validated)';

    -- 3.4 fact_reviews Foreign Keys
    SELECT COUNT(*) INTO v_orphans FROM project_dw.fact_reviews f
    LEFT JOIN project_dw.dim_customer d ON d.customer_key = f.customer_key
    WHERE d.customer_key IS NULL;
    IF v_orphans > 0 THEN
        RAISE EXCEPTION 'Integrity check failed: fact_reviews has % orphan customer_key records', v_orphans;
    END IF;

    SELECT COUNT(*) INTO v_orphans FROM project_dw.fact_reviews f
    LEFT JOIN project_dw.dim_date d ON d.date_key = f.review_creation_date_key
    WHERE d.date_key IS NULL;
    IF v_orphans > 0 THEN
        RAISE EXCEPTION 'Integrity check failed: fact_reviews has % orphan review_creation_date_key records', v_orphans;
    END IF;

    SELECT COUNT(*) INTO v_orphans FROM project_dw.fact_reviews f
    LEFT JOIN project_dw.dim_date d ON d.date_key = f.review_answer_date_key
    WHERE d.date_key IS NULL;
    IF v_orphans > 0 THEN
        RAISE EXCEPTION 'Integrity check failed: fact_reviews has % orphan review_answer_date_key records', v_orphans;
    END IF;
    RAISE NOTICE 'PASS: fact_reviews zero orphan foreign keys (3/3 FK relationships validated)';

    -- 3.5 Primary Key Uniqueness (Duplicate PK count = 0)
    SELECT COUNT(*) INTO v_count FROM (
        SELECT order_id, order_item_id FROM project_dw.fact_order_items GROUP BY order_id, order_item_id HAVING COUNT(*) > 1
    ) sub;
    IF v_count > 0 THEN
        RAISE EXCEPTION 'Integrity check failed: fact_order_items has % duplicate primary keys', v_count;
    END IF;

    SELECT COUNT(*) INTO v_count FROM (
        SELECT order_id FROM project_dw.fact_orders GROUP BY order_id HAVING COUNT(*) > 1
    ) sub;
    IF v_count > 0 THEN
        RAISE EXCEPTION 'Integrity check failed: fact_orders has % duplicate primary keys', v_count;
    END IF;

    SELECT COUNT(*) INTO v_count FROM (
        SELECT order_id, payment_sequential FROM project_dw.fact_payments GROUP BY order_id, payment_sequential HAVING COUNT(*) > 1
    ) sub;
    IF v_count > 0 THEN
        RAISE EXCEPTION 'Integrity check failed: fact_payments has % duplicate primary keys', v_count;
    END IF;

    SELECT COUNT(*) INTO v_count FROM (
        SELECT review_id, order_id FROM project_dw.fact_reviews GROUP BY review_id, order_id HAVING COUNT(*) > 1
    ) sub;
    IF v_count > 0 THEN
        RAISE EXCEPTION 'Integrity check failed: fact_reviews has % duplicate primary keys', v_count;
    END IF;
    RAISE NOTICE 'PASS: Primary key uniqueness validated across all facts (0 duplicate keys)';

    -- 3.6 Domain and Range Constraints
    SELECT COUNT(*) INTO v_count FROM project_dw.fact_reviews WHERE review_score NOT BETWEEN 1 AND 5;
    IF v_count > 0 THEN
        RAISE EXCEPTION 'Quality check failed: fact_reviews has % rows with invalid review_score', v_count;
    END IF;

    SELECT COUNT(*) INTO v_count FROM project_dw.fact_reviews WHERE response_hours < 0;
    IF v_count > 0 THEN
        RAISE EXCEPTION 'Quality check failed: fact_reviews has % rows with negative response_hours', v_count;
    END IF;

    SELECT COUNT(*) INTO v_count FROM project_dw.fact_orders WHERE purchase_hour NOT BETWEEN 0 AND 23;
    IF v_count > 0 THEN
        RAISE EXCEPTION 'Quality check failed: fact_orders has % rows with invalid purchase_hour', v_count;
    END IF;

    SELECT COUNT(*) INTO v_count FROM project_dw.fact_payments WHERE payment_installments < 1;
    IF v_count > 0 THEN
        RAISE EXCEPTION 'Quality check failed: fact_payments has % rows with invalid payment_installments (< 1)', v_count;
    END IF;
    RAISE NOTICE 'PASS: Domain and range checks satisfied on all measures';

    RAISE NOTICE '=======================================================';
    RAISE NOTICE 'ALL PHASE 2 QUALITY CHECKS PASSED SUCCESSFULLY (0 FAILURES)';
    RAISE NOTICE '=======================================================';
END $$;

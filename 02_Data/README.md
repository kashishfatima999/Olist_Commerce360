# 02_Data

| Folder | Contents | In git? |
|--------|----------|---------|
| `raw_data/` | Original Kaggle CSVs, never edited | No (git-ignored) |
| `profiling/` | Read-only profiling outputs (Phase 1) | Yes |
| `cleaned_data/` | Outputs of the cleaning scripts (Phase 2) | Decide in Phase 2 based on size |

## Source
**Brazilian E-Commerce Public Dataset by Olist**: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
The Kaggle page lists the licence as CC BY-NC-SA 4.0. Confirm this on the page and credit Olist in all reports.

## How to download

**Option A: browser**
1. Sign in to Kaggle.
2. Open the URL above and click **Download**. You get a zip file of about 45 MB.
3. Extract the 9 CSV files directly into `02_Data/raw_data/`, with no subfolder.

**Option B: Kaggle CLI**
1. Run `pip install kaggle`.
2. On Kaggle, go to Settings → API → Create New Token, and save the file as `%USERPROFILE%\.kaggle\kaggle.json`. Never put this token in the repository.
3. Run:
   ```
   kaggle datasets download -d olistbr/brazilian-ecommerce -p 02_Data/raw_data --unzip
   ```

## Expected files
- olist_customers_dataset.csv
- olist_geolocation_dataset.csv
- olist_order_items_dataset.csv
- olist_order_payments_dataset.csv
- olist_order_reviews_dataset.csv
- olist_orders_dataset.csv
- olist_products_dataset.csv
- olist_sellers_dataset.csv
- product_category_name_translation.csv

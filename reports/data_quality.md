# Data Quality Report

## What is clean data?

Clean data is **analysis-ready**: correct grain, no unintended duplicate entities, nulls understood and handled, types consistent, and metrics aligned with business definitions (e.g. revenue = price + freight).

## Table inventory

| File | Rows | Notes |
|---|---:|---|
| orders | 99,441 | lifecycle timestamps + status |
| order_items | 112,650 | product, seller, price, freight |
| order_payments | 103,886 | type, installments, value |
| order_reviews | 99,224 | score 1–5 + comments |
| customers | 99,441 | city, state, zip |
| sellers | 3,095 | city, state, zip |
| products | 32,951 | category, dimensions, weight |
| geolocation | 1,000,163 | zip → lat/lng |
| category_translation | 71 | PT → EN category names |

## Duplicate entities

| Entity / key | Duplicates | Action in pipeline |
|---|---:|---|
| orders.`order_id` | 0 | none |
| order_items.(order_id, order_item_id) | 0 | none |
| order_payments.(order_id, payment_sequential) | 0 | none |
| customers.`customer_id` | 0 | none |
| customers.`customer_unique_id` (repeat buyers) | 3345 | expected — not removed |
| sellers.`seller_id` | 0 | none |
| products.`product_id` | 0 | none |
| reviews.`review_id` | 814 | **de-duplicate** in `build_star_schema.py` |
| reviews.`order_id` (multi-review orders) | 551 | keep latest review per order |
| geolocation full-row | 261831 | **de-duplicate** in `build_star_schema.py` |

After geo dedupe: **738,332** rows remain (from 1,000,163).

After review_id dedupe: **98,410** rows remain (from 99,224).

## Nulls worth noting

### orders

| Column | Nulls | % |
|---|---:|---:|
| `order_approved_at` | 160 | 0.2% |
| `order_delivered_carrier_date` | 1,783 | 1.8% |
| `order_delivered_customer_date` | 2,965 | 3.0% |

### order_reviews

| Column | Nulls | % |
|---|---:|---:|
| `review_comment_title` | 87,656 | 88.3% |
| `review_comment_message` | 58,247 | 58.7% |

### products

| Column | Nulls | % |
|---|---:|---:|
| `product_category_name` | 610 | 1.9% |

## Verdict

Transactional tables are largely clean. **Yes — we de-duplicate** `geolocation` (full-row) and `order_reviews` (`review_id`, then one review per order) before building the star schema.

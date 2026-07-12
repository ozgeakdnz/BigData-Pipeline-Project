"""
Data quality checks for Olist CSVs — supports PDF STUDY (clean / duplicates).

Usage:
  python3 processing/data_quality.py

Writes reports/data_quality.md
"""

from pathlib import Path

import pandas as pd

RAW = Path("data/raw")
OUT = Path("reports/data_quality.md")


def main() -> None:
    orders = pd.read_csv(RAW / "olist_orders_dataset.csv")
    items = pd.read_csv(RAW / "olist_order_items_dataset.csv")
    payments = pd.read_csv(RAW / "olist_order_payments_dataset.csv")
    reviews = pd.read_csv(RAW / "olist_order_reviews_dataset.csv")
    customers = pd.read_csv(RAW / "olist_customers_dataset.csv")
    sellers = pd.read_csv(RAW / "olist_sellers_dataset.csv")
    products = pd.read_csv(RAW / "olist_products_dataset.csv")
    geo = pd.read_csv(RAW / "olist_geolocation_dataset.csv")
    cat = pd.read_csv(RAW / "product_category_name_translation.csv")

    geo_dups = int(geo.duplicated().sum())
    review_id_dups = int(reviews["review_id"].duplicated().sum())
    order_multi_reviews = int(reviews["order_id"].duplicated().sum())

    lines = [
        "# Data Quality Report",
        "",
        "## What is clean data?",
        "",
        "Clean data is **analysis-ready**: correct grain, no unintended duplicate "
        "entities, nulls understood and handled, types consistent, and metrics "
        "aligned with business definitions (e.g. revenue = price + freight).",
        "",
        "## Table inventory",
        "",
        "| File | Rows | Notes |",
        "|---|---:|---|",
        f"| orders | {len(orders):,} | lifecycle timestamps + status |",
        f"| order_items | {len(items):,} | product, seller, price, freight |",
        f"| order_payments | {len(payments):,} | type, installments, value |",
        f"| order_reviews | {len(reviews):,} | score 1–5 + comments |",
        f"| customers | {len(customers):,} | city, state, zip |",
        f"| sellers | {len(sellers):,} | city, state, zip |",
        f"| products | {len(products):,} | category, dimensions, weight |",
        f"| geolocation | {len(geo):,} | zip → lat/lng |",
        f"| category_translation | {len(cat):,} | PT → EN category names |",
        "",
        "## Duplicate entities",
        "",
        "| Entity / key | Duplicates | Action in pipeline |",
        "|---|---:|---|",
        f"| orders.`order_id` | {int(orders['order_id'].duplicated().sum())} | none |",
        f"| order_items.(order_id, order_item_id) | {int(items.duplicated(['order_id','order_item_id']).sum())} | none |",
        f"| order_payments.(order_id, payment_sequential) | {int(payments.duplicated(['order_id','payment_sequential']).sum())} | none |",
        f"| customers.`customer_id` | {int(customers['customer_id'].duplicated().sum())} | none |",
        f"| customers.`customer_unique_id` (repeat buyers) | {int(customers['customer_unique_id'].duplicated().sum())} | expected — not removed |",
        f"| sellers.`seller_id` | {int(sellers['seller_id'].duplicated().sum())} | none |",
        f"| products.`product_id` | {int(products['product_id'].duplicated().sum())} | none |",
        f"| reviews.`review_id` | {review_id_dups} | **de-duplicate** in `build_star_schema.py` |",
        f"| reviews.`order_id` (multi-review orders) | {order_multi_reviews} | keep latest review per order |",
        f"| geolocation full-row | {geo_dups} | **de-duplicate** in `build_star_schema.py` |",
        "",
        f"After geo dedupe: **{len(geo) - geo_dups:,}** rows remain "
        f"(from {len(geo):,}).",
        "",
        f"After review_id dedupe: **{len(reviews) - review_id_dups:,}** rows remain "
        f"(from {len(reviews):,}).",
        "",
        "## Nulls worth noting",
        "",
    ]

    for name, df, cols in [
        ("orders", orders, ["order_approved_at", "order_delivered_carrier_date", "order_delivered_customer_date"]),
        ("order_reviews", reviews, ["review_comment_title", "review_comment_message"]),
        ("products", products, ["product_category_name"]),
    ]:
        lines.append(f"### {name}")
        lines.append("")
        lines.append("| Column | Nulls | % |")
        lines.append("|---|---:|---:|")
        for c in cols:
            n = int(df[c].isna().sum())
            lines.append(f"| `{c}` | {n:,} | {100 * n / len(df):.1f}% |")
        lines.append("")

    lines += [
        "## Verdict",
        "",
        "Transactional tables are largely clean. **Yes — we de-duplicate** "
        "`geolocation` (full-row) and `order_reviews` (`review_id`, then one "
        "review per order) before building the star schema.",
        "",
    ]

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"✅ Wrote {OUT}")


if __name__ == "__main__":
    main()

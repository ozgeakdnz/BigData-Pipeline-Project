"""
Answer PDF business questions from local CSVs (same grain as star schema).

Usage:
  python3 processing/business_questions.py

Writes:
  reports/business_answers.md
"""

from pathlib import Path

import pandas as pd

RAW = Path("data/raw")
OUT = Path("reports/business_answers.md")


def load() -> dict[str, pd.DataFrame]:
    orders = pd.read_csv(
        RAW / "olist_orders_dataset.csv",
        parse_dates=[
            "order_purchase_timestamp",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ],
    )
    items = pd.read_csv(RAW / "olist_order_items_dataset.csv")
    payments = pd.read_csv(RAW / "olist_order_payments_dataset.csv")
    reviews = pd.read_csv(RAW / "olist_order_reviews_dataset.csv")
    customers = pd.read_csv(RAW / "olist_customers_dataset.csv")
    sellers = pd.read_csv(RAW / "olist_sellers_dataset.csv")
    products = pd.read_csv(RAW / "olist_products_dataset.csv")
    cat = pd.read_csv(RAW / "product_category_name_translation.csv")
    geo = pd.read_csv(RAW / "olist_geolocation_dataset.csv")

    # Clean (same rules as Spark star job)
    geo = geo.drop_duplicates()
    reviews = reviews.drop_duplicates(subset=["review_id"])
    reviews = (
        reviews.sort_values("review_answer_timestamp")
        .drop_duplicates(subset=["order_id"], keep="last")
    )

    products = products.merge(cat, on="product_category_name", how="left")
    orders["purchase_date"] = orders["order_purchase_timestamp"].dt.date
    orders["purchase_month"] = orders["order_purchase_timestamp"].dt.to_period("M").astype(str)
    orders["delivery_days"] = (
        orders["order_delivered_customer_date"] - orders["order_purchase_timestamp"]
    ).dt.total_seconds() / 86400

    fact_sales = items.merge(
        orders[["order_id", "customer_id", "purchase_month", "purchase_date"]],
        on="order_id",
        how="inner",
    )
    fact_sales["revenue"] = fact_sales["price"] + fact_sales["freight_value"]

    return {
        "orders": orders,
        "fact_sales": fact_sales,
        "payments": payments.merge(
            orders[["order_id", "purchase_month"]], on="order_id", how="inner"
        ),
        "reviews": reviews,
        "customers": customers,
        "sellers": sellers,
        "products": products,
    }


def main() -> None:
    d = load()
    lines: list[str] = [
        "# Business Question Answers",
        "",
        "Computed from cleaned Olist CSVs using the same grain as the star schema "
        "(`fact_sales`, `fact_orders`, `fact_payments`, `fact_reviews` + dimensions).",
        "",
    ]

    # 1. Monthly revenue
    monthly = (
        d["fact_sales"]
        .groupby("purchase_month", as_index=False)["revenue"]
        .sum()
        .sort_values("purchase_month")
    )
    lines += [
        "## 1. Monthly revenue",
        "",
        "Fact: `fact_sales` · Dim: `dim_date` (month)",
        "",
        f"| Month | Revenue (BRL) |",
        f"|---|---:|",
    ]
    for _, r in monthly.iterrows():
        lines.append(f"| {r['purchase_month']} | {r['revenue']:,.2f} |")
    lines += ["", f"**Total revenue:** {monthly['revenue'].sum():,.2f} BRL", ""]

    # 2. Revenue by product category
    sales_cat = d["fact_sales"].merge(
        d["products"][["product_id", "product_category_name_english"]],
        on="product_id",
        how="left",
    )
    by_cat = (
        sales_cat.groupby("product_category_name_english", as_index=False)["revenue"]
        .sum()
        .sort_values("revenue", ascending=False)
        .head(10)
    )
    lines += [
        "## 2. Revenue by product category (Top 10)",
        "",
        "Fact: `fact_sales` · Dim: `dim_product`",
        "",
        "| Category (EN) | Revenue (BRL) |",
        "|---|---:|",
    ]
    for _, r in by_cat.iterrows():
        v = r["product_category_name_english"]
        cat_name = "(missing)" if pd.isna(v) or v == "" else v
        lines.append(f"| {cat_name} | {r['revenue']:,.2f} |")
    lines.append("")

    # 3. Top-performing sellers
    by_seller = (
        d["fact_sales"]
        .groupby("seller_id", as_index=False)["revenue"]
        .sum()
        .sort_values("revenue", ascending=False)
        .head(10)
        .merge(d["sellers"], on="seller_id", how="left")
    )
    lines += [
        "## 3. Top-performing sellers (Top 10 by revenue)",
        "",
        "Fact: `fact_sales` · Dim: `dim_seller`",
        "",
        "| Seller ID | City | State | Revenue (BRL) |",
        "|---|---|---|---:|",
    ]
    for _, r in by_seller.iterrows():
        lines.append(
            f"| `{r['seller_id'][:8]}…` | {r['seller_city']} | {r['seller_state']} | {r['revenue']:,.2f} |"
        )
    lines.append("")

    # 4. Sales by customer state
    sales_state = d["fact_sales"].merge(
        d["customers"][["customer_id", "customer_state"]], on="customer_id", how="left"
    )
    by_state = (
        sales_state.groupby("customer_state", as_index=False)["revenue"]
        .sum()
        .sort_values("revenue", ascending=False)
    )
    lines += [
        "## 4. Sales by customer state",
        "",
        "Fact: `fact_sales` · Dim: `dim_customer`",
        "",
        "| State | Revenue (BRL) |",
        "|---|---:|",
    ]
    for _, r in by_state.iterrows():
        lines.append(f"| {r['customer_state']} | {r['revenue']:,.2f} |")
    lines.append("")

    # 5. Average delivery time by state
    delivered = d["orders"][
        (d["orders"]["order_status"] == "delivered")
        & d["orders"]["delivery_days"].notna()
    ].merge(
        d["customers"][["customer_id", "customer_state"]], on="customer_id", how="left"
    )
    deliv_state = (
        delivered.groupby("customer_state", as_index=False)["delivery_days"]
        .mean()
        .sort_values("delivery_days")
    )
    lines += [
        "## 5. Average delivery time by state (delivered orders)",
        "",
        "Fact: `fact_orders` · Dim: `dim_customer`",
        "",
        "| State | Avg delivery days |",
        "|---|---:|",
    ]
    for _, r in deliv_state.iterrows():
        lines.append(f"| {r['customer_state']} | {r['delivery_days']:.2f} |")
    lines.append("")

    # 6. Payment method trends
    pay = (
        d["payments"]
        .groupby(["purchase_month", "payment_type"], as_index=False)["payment_value"]
        .sum()
        .sort_values(["purchase_month", "payment_type"])
    )
    pay_tot = (
        d["payments"]
        .groupby("payment_type", as_index=False)["payment_value"]
        .sum()
        .sort_values("payment_value", ascending=False)
    )
    lines += [
        "## 6. Payment method trends",
        "",
        "Fact: `fact_payments` · Dim: `dim_date` + payment_type",
        "",
        "### Total by payment type",
        "",
        "| Payment type | Total value (BRL) |",
        "|---|---:|",
    ]
    for _, r in pay_tot.iterrows():
        lines.append(f"| {r['payment_type']} | {r['payment_value']:,.2f} |")
    lines += [
        "",
        "### Monthly × payment type (sample of recent months)",
        "",
        "| Month | Payment type | Value (BRL) |",
        "|---|---|---:|",
    ]
    recent = sorted(pay["purchase_month"].unique())[-6:]
    sample = pay[pay["purchase_month"].isin(recent)]
    for _, r in sample.iterrows():
        lines.append(
            f"| {r['purchase_month']} | {r['payment_type']} | {r['payment_value']:,.2f} |"
        )
    lines.append("")

    # 7. Average review score by category
    # Map review → order items → product category (order-level review applies to all items)
    rev_items = d["reviews"].merge(
        d["fact_sales"][["order_id", "product_id"]], on="order_id", how="inner"
    ).merge(
        d["products"][["product_id", "product_category_name_english"]],
        on="product_id",
        how="left",
    )
    rev_cat = (
        rev_items.groupby("product_category_name_english", as_index=False)["review_score"]
        .mean()
        .sort_values("review_score", ascending=False)
        .head(15)
    )
    lines += [
        "## 7. Average review score by category (Top 15)",
        "",
        "Fact: `fact_reviews` · Dim: `dim_product` (via order_items)",
        "",
        "| Category (EN) | Avg review score |",
        "|---|---:|",
    ]
    for _, r in rev_cat.iterrows():
        v = r["product_category_name_english"]
        cat_name = "(missing)" if pd.isna(v) or v == "" else v
        lines.append(f"| {cat_name} | {r['review_score']:.2f} |")
    lines.append("")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"✅ Wrote {OUT}")


if __name__ == "__main__":
    main()

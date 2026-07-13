"""
ELT transform: read raw Parquet from HDFS, clean, build star schema.

Usage (inside spark-master):
  spark-submit --master spark://spark-master:7077 \\
    --conf spark.hadoop.fs.defaultFS=hdfs://namenode:9000 \\
    /app/processing/build_star_schema.py

Environment:
  HDFS_RAW   — raw parquet base (default: hdfs://namenode:9000/olist)
  HDFS_STAR  — star schema base (default: hdfs://namenode:9000/olist/star)
"""

import os

from pyspark.sql import SparkSession, Window
from pyspark.sql import functions as F

HDFS_RAW = os.environ.get("HDFS_RAW", "hdfs://namenode:9000/olist")
HDFS_STAR = os.environ.get("HDFS_STAR", "hdfs://namenode:9000/olist/star")


def create_spark() -> SparkSession:
    return (
        SparkSession.builder.appName("Olist Star Schema")
        .config("spark.hadoop.fs.defaultFS", "hdfs://namenode:9000")
        .getOrCreate()
    )


def read_raw(spark: SparkSession, name: str):
    return spark.read.parquet(f"{HDFS_RAW}/{name}")


def write_star(df, name: str) -> None:
    path = f"{HDFS_STAR}/{name}"
    print(f"  WRITE {name} → {path}")
    df.write.mode("overwrite").parquet(path)


def build(spark: SparkSession) -> None:
    print(f"RAW : {HDFS_RAW}")
    print(f"STAR: {HDFS_STAR}\n")

    orders = read_raw(spark, "orders")
    items = read_raw(spark, "order_items")
    payments = read_raw(spark, "order_payments")
    reviews = read_raw(spark, "order_reviews")
    customers = read_raw(spark, "customers")
    sellers = read_raw(spark, "sellers")
    products = read_raw(spark, "products")
    geo = read_raw(spark, "geolocation")
    cat = read_raw(spark, "category_translation")

    # --- Clean ---
    geo_before = geo.count()
    geo = geo.dropDuplicates()
    print(f"  CLEAN geolocation: {geo_before:,} → {geo.count():,} (drop full-row dups)")

    reviews_before = reviews.count()
    reviews = reviews.dropDuplicates(["review_id"])
    print(f"  CLEAN order_reviews: {reviews_before:,} → {reviews.count():,} (drop dup review_id)")

    # --- Dimensions ---
    dim_customer = customers.select(
        "customer_id",
        "customer_unique_id",
        "customer_zip_code_prefix",
        "customer_city",
        "customer_state",
    )
    write_star(dim_customer, "dim_customer")

    dim_seller = sellers.select(
        "seller_id",
        "seller_zip_code_prefix",
        "seller_city",
        "seller_state",
    )
    write_star(dim_seller, "dim_seller")

    dim_product = (
        products.join(cat, on="product_category_name", how="left")
        .select(
            "product_id",
            "product_category_name",
            "product_category_name_english",
            "product_weight_g",
            "product_length_cm",
            "product_height_cm",
            "product_width_cm",
        )
    )
    write_star(dim_product, "dim_product")

    purchase_dates = (
        orders.select(F.to_date("order_purchase_timestamp").alias("date"))
        .where(F.col("date").isNotNull())
        .distinct()
    )
    dim_date = purchase_dates.select(
        F.date_format("date", "yyyyMMdd").cast("int").alias("date_key"),
        F.col("date"),
        F.year("date").alias("year"),
        F.month("date").alias("month"),
        F.date_format("date", "MMMM").alias("month_name"),
        F.quarter("date").alias("quarter"),
    )
    write_star(dim_date, "dim_date")

    write_star(geo, "dim_geolocation")

    # --- Facts ---
    orders_enriched = orders.withColumn(
        "purchase_date", F.to_date("order_purchase_timestamp")
    ).withColumn(
        "date_key", F.date_format("purchase_date", "yyyyMMdd").cast("int")
    ).withColumn(
        "delivery_days",
        F.when(
            F.col("order_delivered_customer_date").isNotNull()
            & F.col("order_purchase_timestamp").isNotNull(),
            F.round(
                (
                    F.unix_timestamp("order_delivered_customer_date")
                    - F.unix_timestamp("order_purchase_timestamp")
                )
                / 86400.0,
                2,
            ),
        ),
    )

    fact_orders = orders_enriched.select(
        "order_id",
        "customer_id",
        "order_status",
        "date_key",
        "purchase_date",
        "order_purchase_timestamp",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
        "delivery_days",
    )
    write_star(fact_orders, "fact_orders")

    fact_sales = (
        items.join(
            orders_enriched.select("order_id", "customer_id", "date_key", "purchase_date"),
            on="order_id",
            how="inner",
        ).select(
            "order_id",
            "order_item_id",
            "product_id",
            "seller_id",
            "customer_id",
            "date_key",
            "purchase_date",
            F.col("price").cast("double").alias("price"),
            F.col("freight_value").cast("double").alias("freight_value"),
            (F.col("price").cast("double") + F.col("freight_value").cast("double")).alias(
                "revenue"
            ),
        )
    )
    write_star(fact_sales, "fact_sales")

    fact_payments = (
        payments.join(
            orders_enriched.select("order_id", "date_key", "purchase_date"),
            on="order_id",
            how="inner",
        ).select(
            "order_id",
            "payment_sequential",
            "date_key",
            "purchase_date",
            "payment_type",
            F.col("payment_installments").cast("int").alias("payment_installments"),
            F.col("payment_value").cast("double").alias("payment_value"),
        )
    )
    write_star(fact_payments, "fact_payments")

    # one review per order for category-level joins (keep latest answer)
    w = Window.partitionBy("order_id").orderBy(F.col("review_answer_timestamp").desc_nulls_last())
    reviews_order = (
        reviews.withColumn("rn", F.row_number().over(w))
        .where(F.col("rn") == 1)
        .drop("rn")
    )
    fact_reviews = (
        reviews_order.join(
            orders_enriched.select("order_id", "date_key", "purchase_date"),
            on="order_id",
            how="left",
        ).select(
            "review_id",
            "order_id",
            "date_key",
            "purchase_date",
            F.col("review_score").cast("int").alias("review_score"),
            "review_creation_date",
        )
    )
    write_star(fact_reviews, "fact_reviews")

    print("\n✅ Star schema written to HDFS.")


if __name__ == "__main__":
    spark = create_spark()
    try:
        build(spark)
    finally:
        spark.stop()

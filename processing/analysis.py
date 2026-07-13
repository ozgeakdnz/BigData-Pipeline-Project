"""
Phase 1 — Ingest: Read Olist CSV files and write Parquet to HDFS.

Usage (inside Docker network, e.g. spark-master container):
  spark-submit --master spark://spark-master:7077 processing/analysis.py

Environment variables:
  CSV_DIR       — local CSV directory (default: data/raw)
  HDFS_OUTPUT   — HDFS base path   (default: hdfs://namenode:9000/olist)
"""

import os
import sys
from pathlib import Path

from pyspark.sql import SparkSession

CSV_DIR = os.environ.get("CSV_DIR", "data/raw")
HDFS_OUTPUT = os.environ.get("HDFS_OUTPUT", "hdfs://namenode:9000/olist")

TABLES = {
    "olist_customers_dataset.csv": "customers",
    "olist_geolocation_dataset.csv": "geolocation",
    "olist_order_items_dataset.csv": "order_items",
    "olist_order_payments_dataset.csv": "order_payments",
    "olist_order_reviews_dataset.csv": "order_reviews",
    "olist_orders_dataset.csv": "orders",
    "olist_products_dataset.csv": "products",
    "olist_sellers_dataset.csv": "sellers",
    "product_category_name_translation.csv": "category_translation",
}


def create_spark() -> SparkSession:
    return (
        SparkSession.builder.appName("Olist CSV to Parquet")
        .config("spark.hadoop.fs.defaultFS", "hdfs://namenode:9000")
        .getOrCreate()
    )


def convert_all(spark: SparkSession) -> None:
    csv_dir = Path(CSV_DIR)
    if not csv_dir.exists():
        print(f"ERROR: CSV directory not found: {csv_dir.absolute()}")
        sys.exit(1)

    print(f"CSV source : {csv_dir.absolute()}")
    print(f"HDFS target: {HDFS_OUTPUT}\n")

    for csv_name, table_name in TABLES.items():
        csv_path = csv_dir / csv_name
        if not csv_path.exists():
            print(f"  SKIP  {csv_name} — file not found")
            continue

        hdfs_path = f"{HDFS_OUTPUT}/{table_name}"
        local_path = f"file://{csv_path.resolve()}"
        print(f"  READ  {csv_name}")
        df = (
            spark.read.option("header", True)
            .option("inferSchema", True)
            .csv(local_path)
        )

        print(f"  WRITE {table_name} → {hdfs_path}")
        df.write.mode("overwrite").parquet(hdfs_path)

    print("\n✅ All tables converted to Parquet on HDFS.")


if __name__ == "__main__":
    spark = create_spark()
    try:
        convert_all(spark)
    finally:
        spark.stop()

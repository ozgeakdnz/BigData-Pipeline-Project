"""
Register Olist Parquet datasets as Hive tables for Superset visualization.

Registers:
  - raw tables under database `olist`
  - star schema tables under database `olist_star`

Superset URI (raw):  hive://spark-thriftserver:10000/olist
Superset URI (star): hive://spark-thriftserver:10000/olist_star

Usage:
  python visualization/register_tables.py
"""

import os
import subprocess
import sys

HDFS_OUTPUT = os.environ.get("HDFS_OUTPUT", "hdfs://namenode:9000/olist")
HDFS_STAR = os.environ.get("HDFS_STAR", "hdfs://namenode:9000/olist/star")

RAW_TABLES = [
    "customers",
    "geolocation",
    "order_items",
    "order_payments",
    "order_reviews",
    "orders",
    "products",
    "sellers",
    "category_translation",
]

STAR_TABLES = [
    "dim_customer",
    "dim_seller",
    "dim_product",
    "dim_date",
    "dim_geolocation",
    "fact_orders",
    "fact_sales",
    "fact_payments",
    "fact_reviews",
]


def build_sql() -> str:
    statements = [
        "CREATE DATABASE IF NOT EXISTS olist;",
        "USE olist;",
    ]
    for table in RAW_TABLES:
        location = f"{HDFS_OUTPUT}/{table}"
        statements.append(f"DROP TABLE IF EXISTS {table};")
        statements.append(f"CREATE TABLE {table} USING PARQUET LOCATION '{location}';")

    statements += [
        "CREATE DATABASE IF NOT EXISTS olist_star;",
        "USE olist_star;",
    ]
    for table in STAR_TABLES:
        location = f"{HDFS_STAR}/{table}"
        statements.append(f"DROP TABLE IF EXISTS {table};")
        statements.append(f"CREATE TABLE {table} USING PARQUET LOCATION '{location}';")

    statements.append("SHOW TABLES IN olist;")
    statements.append("SHOW TABLES IN olist_star;")
    return "\n".join(statements)


def register_via_beeline() -> None:
    sql = build_sql()
    local_sql = "visualization/register_tables.sql"

    with open(local_sql, "w") as f:
        f.write(sql)

    cmd = [
        "docker",
        "exec",
        "spark-thriftserver",
        "/spark/bin/beeline",
        "-u",
        "jdbc:hive2://localhost:10000",
        "-f",
        "/app/visualization/register_tables.sql",
    ]
    print("Registering tables via beeline...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        sys.exit(result.returncode)

    print(f"\n✅ Raw tables registered in 'olist' ({len(RAW_TABLES)}).")
    print(f"✅ Star tables registered in 'olist_star' ({len(STAR_TABLES)}).")
    print("   Superset URI: hive://spark-thriftserver:10000/olist_star")


if __name__ == "__main__":
    register_via_beeline()

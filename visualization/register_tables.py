"""
Register Olist Parquet datasets as Hive tables for Superset visualization.

Connects to the running Spark ThriftServer and creates external tables
pointing to HDFS Parquet files.

Superset connection URI: hive://spark-thriftserver:10000/olist

Usage (from host, ThriftServer must be running):
  python visualization/register_tables.py

Or via beeline inside Docker:
  docker exec spark-thriftserver /spark/bin/beeline -u 'jdbc:hive2://localhost:10000' -f /app/visualization/register_tables.sql
"""

import os
import subprocess
import sys

HDFS_OUTPUT = os.environ.get("HDFS_OUTPUT", "hdfs://namenode:9000/olist")
DATABASE = "olist"

TABLES = [
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


def build_sql() -> str:
    statements = [f"CREATE DATABASE IF NOT EXISTS {DATABASE};", f"USE {DATABASE};"]
    for table in TABLES:
        location = f"{HDFS_OUTPUT}/{table}"
        statements.append(f"DROP TABLE IF EXISTS {table};")
        statements.append(
            f"CREATE TABLE {table} USING PARQUET LOCATION '{location}';"
        )
    statements.append("SHOW TABLES;")
    return "\n".join(statements)


def register_via_beeline() -> None:
    """Register tables using beeline inside the spark-thriftserver container."""
    sql = build_sql()
    sql_file = "/tmp/register_tables.sql"
    local_sql = "visualization/register_tables.sql"

    with open(local_sql, "w") as f:
        f.write(sql)

    cmd = [
        "docker", "exec", "spark-thriftserver",
        "/spark/bin/beeline",
        "-u", "jdbc:hive2://localhost:10000",
        "-f", "/app/visualization/register_tables.sql",
    ]
    print("Registering tables via beeline...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        sys.exit(result.returncode)

    print(f"\n✅ {len(TABLES)} tables registered in '{DATABASE}' database.")
    print("   Superset URI: hive://localhost:10000/olist")


if __name__ == "__main__":
    register_via_beeline()

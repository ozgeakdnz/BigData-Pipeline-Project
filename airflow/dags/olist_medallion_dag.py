"""
Phase 3 — Olist Medallion pipeline orchestrated by Airflow.

Flow:
  download_dataset → spark_ingest (bronze load) → register_raw_hive
  → dbt_run (bronze/silver/gold) → dbt_test

UI: http://localhost:8089  (admin / admin)
"""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    "owner": "olist",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
    "execution_timeout": timedelta(minutes=45),
}

PROJECT = "/opt/airflow/project"
DBT_DIR = "/opt/airflow/dbt"

with DAG(
    dag_id="olist_medallion_pipeline",
    description="Ingest Olist CSVs to HDFS, then dbt Bronze→Silver→Gold star schema",
    default_args=default_args,
    start_date=datetime(2026, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    tags=["olist", "phase3", "medallion", "dbt"],
    max_active_runs=1,
) as dag:

    # Boundary: host/project scripts — lightweight, no Spark cluster needed
    download_dataset = BashOperator(
        task_id="download_dataset",
        bash_command=(
            f"cd {PROJECT} && python3 scripts/download_dataset.py "
            "|| echo 'Download skipped or already present'"
        ),
        pool="default_pool",
        cwd=PROJECT,
    )

    # Boundary: Spark cluster — CSV → Parquet on HDFS (bronze landing via Spark)
    # Resources: uses spark-master + worker (4g/2 cores from compose)
    spark_ingest = BashOperator(
        task_id="spark_ingest_bronze",
        bash_command=(
            "docker exec -e CSV_DIR=/app/data/raw spark-master "
            "/spark/bin/spark-submit "
            "--master spark://spark-master:7077 "
            "--conf spark.hadoop.fs.defaultFS=hdfs://namenode:9000 "
            "--conf spark.executor.memory=2g "
            "--conf spark.driver.memory=1g "
            "/app/processing/analysis.py"
        ),
        execution_timeout=timedelta(minutes=30),
    )

    # Boundary: Hive metastore registration for dbt sources
    register_raw_hive = BashOperator(
        task_id="register_raw_hive_tables",
        bash_command=f"cd {PROJECT} && python3 visualization/register_tables.py",
        execution_timeout=timedelta(minutes=10),
    )

    # Boundary: dbt transform layer — Silver clean + Gold star (Medallion)
    dbt_run = BashOperator(
        task_id="dbt_run_medallion",
        bash_command=(
            f"cd {DBT_DIR} && dbt run --profiles-dir {DBT_DIR} "
            f"--project-dir {DBT_DIR}"
        ),
        execution_timeout=timedelta(minutes=40),
        env={
            "DBT_PROFILES_DIR": DBT_DIR,
        },
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=(
            f"cd {DBT_DIR} && dbt test --profiles-dir {DBT_DIR} --project-dir {DBT_DIR}"
        ),
        execution_timeout=timedelta(minutes=15),
        env={
            "DBT_PROFILES_DIR": DBT_DIR,
        },
    )

    download_dataset >> spark_ingest >> register_raw_hive >> dbt_run >> dbt_test

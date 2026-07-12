#!/bin/bash
# Start Phase 3 stack (HDFS + Spark + Airflow) and print next steps.
set -e
cd "$(dirname "$0")/.."

bash scripts/setup_network.sh

echo "=== HDFS ==="
docker compose -f docker/docker-compose-hdfs.yml up -d
sleep 10

echo "=== Spark ==="
docker compose -f docker/docker-compose-spark.yml up -d
sleep 20

echo "=== Airflow (build may take a few minutes) ==="
docker compose -f docker/docker-compose-airflow.yml up -d --build

echo ""
echo "✅ Phase 3 stack starting"
echo "   Airflow : http://localhost:8089  (admin / admin)"
echo "   Trigger DAG: olist_medallion_pipeline"
echo "   Docs    : reports/PHASE3.md"
echo ""
echo "Optional — run dbt only (after ingest + thriftserver up):"
echo "  docker exec -e DBT_SPARK_HOST=spark-thriftserver airflow-scheduler \\"
echo "    bash -c 'cd /opt/airflow/dbt && dbt run --profiles-dir /opt/airflow/dbt'"

#!/bin/bash
# Run the full Phase 1 + Phase 2 pipeline end-to-end.
set -e

cd "$(dirname "$0")/.."

echo "=== Step 1: Download dataset ==="
python3 scripts/download_dataset.py

echo ""
echo "=== Step 2: Start Docker infrastructure ==="
bash scripts/setup_network.sh
docker compose -f docker/docker-compose-hdfs.yml up -d
sleep 15
docker compose -f docker/docker-compose-spark.yml up -d
sleep 20

echo ""
echo "=== Step 3: CSV → Parquet (Spark) ==="
docker exec -e CSV_DIR=/app/data/raw spark-master /spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --conf spark.hadoop.fs.defaultFS=hdfs://namenode:9000 \
  /app/processing/analysis.py

echo ""
echo "=== Step 4: Clean + star schema (Spark ELT) ==="
docker exec spark-master /spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --conf spark.hadoop.fs.defaultFS=hdfs://namenode:9000 \
  /app/processing/build_star_schema.py

echo ""
echo "=== Step 5: Register Hive tables (raw + star) ==="
python3 visualization/register_tables.py

echo ""
echo "=== Step 6: Data quality + business questions ==="
python3 processing/data_quality.py
python3 processing/business_questions.py

echo ""
echo "=== Step 7: Start Superset ==="
docker compose -f docker/docker-compose-superset.yml up -d --build

echo ""
echo "✅ Pipeline complete!"
echo "   HDFS UI  : http://localhost:9870"
echo "   Spark UI : http://localhost:8080"
echo "   Superset : http://localhost:8088  (admin / admin)"
echo "   DB URI   : hive://spark-thriftserver:10000/olist_star"
echo "   Answers  : reports/business_answers.md"
echo "   Quality  : reports/data_quality.md"
echo "   SQL      : sql/business_questions.sql"

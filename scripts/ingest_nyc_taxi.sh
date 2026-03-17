#!/bin/bash

set -e  # stop on error

YEAR=${1:-2019}
BASE_URL="https://d37ci6vzurychx.cloudfront.net/trip-data"
STAGING_DIR=~/nyc-data-download-staging/$YEAR
HDFS_DIR=/data/nyc-taxi/raw/$YEAR

echo "======================================="
echo "NYC Taxi Data Pipeline - Year: $YEAR"
echo "======================================="

# 1️⃣ Create staging directory
echo "[1/8] Creating staging directory..."
mkdir -p $STAGING_DIR
cd $STAGING_DIR

# 2️⃣ Download all months
echo "[2/8] Downloading data..."
for i in {01..12}; do
  FILE="yellow_tripdata_${YEAR}-${i}.parquet"
  echo "Downloading $FILE"
  wget -q --show-progress "$BASE_URL/$FILE"
done

# 3️⃣ Verify files
echo "[3/8] Verifying file sizes..."
du -sh *.parquet | sort -h

# 4️⃣ Remove bad files (corrupted ~4K)
echo "[4/8] Removing corrupted files (<100KB)..."
find . -name "*.parquet" -size -100k -print -delete

# 5️⃣ Create HDFS directory
echo "[5/8] Creating HDFS directory..."
hdfs dfs -mkdir -p $HDFS_DIR

# 6️⃣ Upload to HDFS
echo "[6/8] Uploading to HDFS..."
hdfs dfs -put -f *.parquet $HDFS_DIR/

# 7️⃣ Verify in HDFS
echo "[7/8] Verifying HDFS upload..."
hdfs dfs -ls $HDFS_DIR
hdfs dfs -du -h $HDFS_DIR

# 8️⃣ Spark sanity check (optional)
echo "[8/8] Spark sanity check..."
spark-shell <<EOF
val df = spark.read.parquet("$HDFS_DIR")
println("Record count: " + df.count())
df.printSchema()
EOF

echo "======================================="
echo "Pipeline completed successfully!"
echo "======================================="
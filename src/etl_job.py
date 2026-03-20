from pyspark.sql import SparkSession
from pyspark.sql.functions import col, hour, unix_timestamp
from pyspark.sql.types import DoubleType, LongType, StructType, StructField, TimestampType
from functools import reduce
from pyspark.sql import DataFrame
import config
import argparse

def run_etl(data_size_gb=10):
    print("Starting ETL Job...")
    
    # 1. Initialize Spark Session with assignment configurations
    # We remove the hardcoded spark.cores.max so that it can be dynamically set
    # during the benchmark tests via `spark-submit --total-executor-cores X`
    spark = SparkSession.builder \
        .master(config.SPARK_MASTER_URL) \
        .appName(config.ETL_APP_NAME) \
        .getOrCreate()
    
    try:
        # We use mergeSchema=true so Spark dynamically handles the INT32 vs INT64 
        # physical differences across the years without crashing the Parquet reader.

        raw_data_path = f"{config.RAW_DATA_PATH}/*.parquet"
        print(f"Reading raw data from: {raw_data_path}")
        
        # 2. Read all Parquet files with schema merging to handle type inconsistencies
        #  Two columns have different physical types across the yearly Parquet files:
        #   - PULocationID: INT32 in older files, INT64 in newer files.
        #   - airport_fee: INT in some files, DOUBLE in others.
        # Both mergeSchema=true and explicit schema fail because Spark reads every file's
        # metadata first and tries to merge them into one schema before reading any data.
        # It refuses to merge INT and DOUBLE even if we never asked for that column.
        #
        # Fix: read each file individually so there is nothing to merge, immediately
        # cast and select only the 5 columns we need, then unionAll everything together.
        # Since Spark is lazily evaluated, no data moves until the final .write() is called.

        sc = spark.sparkContext
        fs = sc._jvm.org.apache.hadoop.fs.FileSystem.get(sc._jsc.hadoopConfiguration())
        Path = sc._jvm.org.apache.hadoop.fs.Path
        statuses = fs.globStatus(Path(raw_data_path))
        if not statuses:
            raise Exception(f"No parquet files found in {config.RAW_DATA_PATH}")
        target_bytes = data_size_gb * (1024 ** 3)
        current_bytes = 0
        file_paths = []

        for s in statuses:
            if current_bytes < target_bytes:
                file_paths.append(s.getPath().toString())
                current_bytes += s.getLen()
            else:
                break

        print(f"Found files. Selected {len(file_paths)} files to match approx {data_size_gb}GB limit. Reading iteratively...")
        dfs = []
        for file_path in file_paths:
            df = spark.read.parquet(file_path)
            dfs.append(df.select(
                col("tpep_pickup_datetime"),
                col("tpep_dropoff_datetime"),
                col("PULocationID").cast(LongType()),
                col("fare_amount").cast(DoubleType()),
                col("trip_distance").cast(DoubleType())
            ))
        raw_df = reduce(DataFrame.unionAll, dfs)

        # 3. Clean and Transform Data
        print("Cleaning and selecting required columns...")
        # We cast types for consistency and filter invalid records immediately
        cleaned_df = raw_df \
            .withColumn("PULocationID", col("PULocationID").cast(LongType())) \
            .withColumn("fare_amount", col("fare_amount").cast(DoubleType())) \
            .withColumn("trip_distance", col("trip_distance").cast(DoubleType()))
    
        # Apply filters based on project plan
        cleaned_filtered_df = cleaned_df.filter(
            (col("fare_amount") > 0) &
            (col("trip_distance") > 0) &
            (col("PULocationID").isNotNull()) &
            (col("tpep_pickup_datetime").isNotNull()) &
            (col("tpep_dropoff_datetime").isNotNull())
        )
        # Trip duration and pickup_hour
        transformed_df = cleaned_filtered_df \
            .withColumn("pickup_hour", hour(col("tpep_pickup_datetime"))) \
            .withColumn("duration_minutes", 
                        (unix_timestamp(col("tpep_dropoff_datetime")) - unix_timestamp(col("tpep_pickup_datetime"))) / 60) \
            .filter(col("duration_minutes") > 0)
        
        # AGGRESSIVE PRUNING FOR STORAGE CONSTRAINTS
        # We keep ONLY the 4 columns needed for analysis_job.py. 
        final_transformed_df = transformed_df.select(
            "PULocationID",
            "fare_amount",
            "pickup_hour",
            "duration_minutes"
        )
        print("Data cleaning and transformation complete. Saving cleaned data to HDFS...")

        # 4. Save the cleaned and transformed data back to HDFS in Parquet format
        # We use 'overwrite' mode so running this script multiple times 
        # completely replaces the previous run's directory instead of failing or duplicating.
        final_transformed_df.write.mode("overwrite").parquet(config.CLEANED_DATA_PATH)
        
        print(f"ETL Job completed successfully.")

    except Exception as e:
        print(f"Error during ETL Job: {e}")
    finally:
        spark.stop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_size_gb", type=int, default=10, help="Target data size in GB")
    args = parser.parse_args()

    run_etl(data_size_gb=args.data_size_gb)
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, hour, unix_timestamp
from pyspark.sql.types import DoubleType, StructType, StructField, TimestampType, IntegerType
import config

def run_etl():
    print("Starting ETL Job...")
    
    # 1. Initialize Spark Session with assignment configurations
    # We remove the hardcoded spark.cores.max so that it can be dynamically set
    # during the benchmark tests via `spark-submit --total-executor-cores X`
    spark = SparkSession.builder \
        .master(config.SPARK_MASTER_URL) \
        .appName(config.ETL_APP_NAME) \
        .config("spark.sql.parquet.enableVectorizedReader", "false") \
        .getOrCreate()
    
    try:
        # Solution 2: Explicit "Narrow" Schema. 
        # We completely omit 'airport_fee' and other irrelevant columns to bypass schema merging conflicts.
        schema = StructType([
            StructField("tpep_pickup_datetime", TimestampType(), True),
            StructField("tpep_dropoff_datetime", TimestampType(), True),
            StructField("trip_distance", DoubleType(), True),
            StructField("PULocationID", IntegerType(), True), 
            StructField("fare_amount", DoubleType(), True)
        ])

        raw_data_path = f"{config.RAW_DATA_PATH}/*.parquet"
        print(f"Reading raw data from: {raw_data_path}")
        
        # Read with the explicit schema instead of mergeSchema=true
        raw_df = spark.read.schema(schema).parquet(raw_data_path)

        # 3. Clean and Transform Data
        print("Cleaning and selecting required columns...")
        # We cast types for consistency and filter invalid records immediately
        cleaned_df = raw_df \
            .withColumn("PULocationID", col("PULocationID").cast(IntegerType())) \
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
    run_etl()
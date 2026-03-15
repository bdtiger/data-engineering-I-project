import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, avg, round
import config

def run_analysis():
    print("Starting Analysis Job...")
    
    # 1. Initialize Spark Session with assignment configurations
    # We remove the hardcoded spark.cores.max so that it can be dynamically set
    # during the benchmark tests via `spark-submit --total-executor-cores X`
    spark = SparkSession.builder \
        .master(config.SPARK_MASTER_URL) \
        .appName(config.ANALYSIS_APP_NAME) \
        .config("spark.sql.parquet.enableVectorizedReader", "false") \
        .getOrCreate()
        
    try:
        # 2. Load the perfectly cleaned data
        print(f"Loading cleaned data from: {config.CLEANED_DATA_PATH}")
        # HDFS treats the directory as the dataset, easily loading all 'part-' files
        df = spark.read.parquet(config.CLEANED_DATA_PATH)
        
        # 3. Aggregate data EXACTLY as defined in project_plan.md
        # Compute average trip duration and average fare amount grouped by pickup zone and hour
        print("Performing aggregations...")
        analysis_df = df.groupBy("PULocationID", "pickup_hour") \
            .agg(
                round(avg("duration_minutes"), 2).alias("avg_trip_duration"),
                round(avg("fare_amount"), 2).alias("avg_fare_amount")
            )
            
        print("Aggregation complete. Loading Zone Lookup CSV...")
        
        # 4. Load the zone lookup mapping to get English names instead of IDs
        lookup_df = spark.read.option("header", "true") \
            .option("inferSchema", "true") \
            .csv(config.ZONE_LOOKUP_PATH)
            
        # 5. Join final output
        final_df = analysis_df.join(lookup_df, analysis_df.PULocationID == lookup_df.LocationID, "left")
        
        # Select final clean column names and order them
        final_result = final_df.select(
            col("Zone").alias("pickup_zone"), 
            "pickup_hour",
            "avg_trip_duration",
            "avg_fare_amount"
        ).orderBy("pickup_zone", "pickup_hour")
        
        # 6. Save final output
        # coalesce(1) ensures the output is exactly ONE single CSV file 
        # which is perfect here since the final aggregate table is very tiny.
        print(f"Saving final results to HDFS: {config.FINAL_RESULT_PATH}")
        final_result.coalesce(1).write \
            .mode("overwrite") \
            .option("header", "true") \
            .csv(config.FINAL_RESULT_PATH)
            
        print("Analysis Job complete! Results are ready for report insertion.")
        
    except Exception as e:
        print(f"Error during Analysis process: {e}")
        sys.exit(1)
    finally:
        spark.stop()

if __name__ == "__main__":
    run_analysis()

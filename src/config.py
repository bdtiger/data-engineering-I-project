# src/config.py
# Centralized configuration and HDFS paths for the NYC Taxi Analysis

# HDFS Master URI base
HDFS_URL = "hdfs://group-32-master:9000"

# Input/Output Paths
RAW_DATA_PATH     = f"{HDFS_URL}/data/nyc-taxi"
CLEANED_DATA_PATH = f"{HDFS_URL}/data/nyc-taxi-cleaned/"
ZONE_LOOKUP_PATH  = f"{HDFS_URL}/data/taxi_zone_lookup.csv"
FINAL_RESULT_PATH = f"{HDFS_URL}/data/results/"

# App Names
ETL_APP_NAME      = "NYCTaxi_ETL_Job"
ANALYSIS_APP_NAME = "NYCTaxi_Analysis_Job"

# Spark Cluster Config
SPARK_MASTER_URL  = "spark://group-32-master:7077"

#! /bin/bash
# scripts/run_benchmark.sh
# Runs all scaling experiments and records runtimes to results/timings.csv

MASTER_SPARK_URL="spark://group-32-master:7077"
ETL_JOB="$HOME/data-engineering-I-project/src/etl_job.py"
ANALYSIS_JOB="$HOME/data-engineering-I-project/src/analysis_job.py"
RESULTS_DIR="$HOME/data-engineering-I-project/results"
RESULTS_FILE="$RESULTS_DIR/timings.csv"

# Ensure results directory exists
mkdir -p $RESULTS_DIR
# Write CSV header
echo "experiment,workers,cores_per_executor,data_gb,runtime_seconds" > $RESULTS_FILE

run_experiment() {
    local label=$1
    local workers=$2
    local cores=$3
    local data_gb=$4

    echo "==============================="
    echo "Running: $label | workers=$workers | cores=$cores | data=${data_gb}GB"
    echo "==============================="

    START=$(date +%s)

    spark-submit \
        --master $MASTER_SPARK_URL \
        --total-executor-cores $(( workers * cores )) \
        --executor-cores $cores \
        $ETL_JOB

    spark-submit \
        --master $MASTER_SPARK_URL \
        --total-executor-cores $(( workers * cores )) \
        --executor-cores $cores \
        $ANALYSIS_JOB

    END=$(date +%s)
    RUNTIME=$(( END - START ))

    echo "$label,$workers,$cores,$data_gb,$RUNTIME" >> $RESULTS_FILE
    echo ">>> $label finished in ${RUNTIME}s"
}

# H = Horizontal scaling (changing number of workers)
# V = Vertical scaling (changing cores per worker, workers stay fixed)
# W = Weak scaling (data grows as workers grow)
# Strong scaling (fixed 5 GB, vary workers)
# 1. H-1, 1 worker, 2 cores, 5 GB 
run_experiment "H-1" 1 2 5
run_experiment "H-2" 2 2 5
run_experiment "H-3" 3 2 5
run_experiment "V-1" 3 1 5

echo "All experiments completed. Runtimes recorded in $RESULTS_FILE"
cat $RESULTS_FILE
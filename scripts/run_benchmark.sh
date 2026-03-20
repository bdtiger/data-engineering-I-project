#! /bin/bash
# scripts/run_benchmark.sh
# Runs all scaling experiments and records runtimes to results/timings.csv

# ==========================================
# 1. BASH ENVIRONMENT & STRICT MODE
# ==========================================
set -euo pipefail

MASTER_SPARK_URL="spark://group-32-master:7077"

# ==========================================
# 2. PATH RESOLUTION & CONFIGURATION
# ==========================================
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ETL_JOB="$PROJECT_ROOT/src/etl_job.py"
ANALYSIS_JOB="$PROJECT_ROOT/src/analysis_job.py"
RESULTS_DIR="$PROJECT_ROOT/results"
RESULTS_FILE="$RESULTS_DIR/timings.csv"

# ==========================================
# 3. GLOBAL LOGGING & CSV SETUP
# ==========================================
# Ensure results directory and log directory exist
mkdir -p "$RESULTS_DIR/logs"
# Write CSV header for separated ETL and Analysis runtimes
echo "experiment,workers,cores_per_executor,data_gb,etl_runtime_seconds,analysis_runtime_seconds,total_runtime_seconds" > "$RESULTS_FILE"

# Initialize the master matrix log to track experiment triggers
MAIN_LOG="$RESULTS_DIR/logs/benchmark_run_matrix.log"
echo "--- Benchmark Session Matrix Log: $(date) ---" >> "$MAIN_LOG"

# ==========================================
# 4. PRE-FLIGHT VALIDATION CHECKS
# Ensure Spark & scripts are available
# ==========================================
if ! command -v spark-submit &> /dev/null; then
    echo "ERROR: spark-submit could not be found. Please ensure it is installed and in your PATH." | tee -a "$MAIN_LOG"
    exit 1
fi
if [ ! -f "$ETL_JOB" ]; then
    echo "ERROR: ETL job script not found at $ETL_JOB" | tee -a "$MAIN_LOG"
    exit 1
fi
if [ ! -f "$ANALYSIS_JOB" ]; then
    echo "ERROR: Analysis job script not found at $ANALYSIS_JOB" | tee -a "$MAIN_LOG"
    exit 1
fi

run_experiment() {
    local label=$1
    local workers=$2
    local cores=$3
    local data_gb=$4

    echo "==============================="
    echo "Running: $label | workers=$workers | cores=$cores | data=${data_gb}GB"
    echo "==============================="
    
    # ------------------------------------------
    # Drop OS caches to guarantee a true Cold Start
    # Note: Requires passwordless sudo privileges
    # ------------------------------------------
    # echo ">>> Clearing OS Page Caches for cold start..."
    # sudo sh -c 'sync; echo 3 > /proc/sys/vm/drop_caches'
    
    # Record execution context into master matrix log
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Started $label: workers=$workers, cores=$cores, data=${data_gb}GB" >> "$MAIN_LOG"

    local etl_log="$RESULTS_DIR/logs/${label}_etl.log"
    echo ">>> Starting ETL Job... (logs: $etl_log)"
    START_ETL=$(date +%s)

    spark-submit \
        --master $MASTER_SPARK_URL \
        --total-executor-cores $(( workers * cores )) \
        --executor-cores $cores \
        $ETL_JOB --data_size_gb "$data_gb" > "$etl_log" 2>&1
        
    END_ETL=$(date +%s)
    ETL_RUNTIME=$(( END_ETL - START_ETL ))

    local analysis_log="$RESULTS_DIR/logs/${label}_analysis.log"
    echo ">>> Starting Analysis Job... (logs: $analysis_log)"
    START_ANALYSIS=$(date +%s)

    spark-submit \
        --master $MASTER_SPARK_URL \
        --total-executor-cores $(( workers * cores )) \
        --executor-cores $cores \
        $ANALYSIS_JOB > "$analysis_log" 2>&1

    END_ANALYSIS=$(date +%s)
    ANALYSIS_RUNTIME=$(( END_ANALYSIS - START_ANALYSIS ))
    
    TOTAL_RUNTIME=$(( ETL_RUNTIME + ANALYSIS_RUNTIME ))

    echo "$label,$workers,$cores,$data_gb,$ETL_RUNTIME,$ANALYSIS_RUNTIME,$TOTAL_RUNTIME" >> $RESULTS_FILE
    echo ">>> $label finished in ${TOTAL_RUNTIME}s (ETL: ${ETL_RUNTIME}s, Analysis: ${ANALYSIS_RUNTIME}s)"
}

# H = Horizontal scaling (changing number of workers)
# V = Vertical scaling (changing cores per worker, workers stay fixed)
# W = Weak scaling (data grows as workers grow)
# Strong scaling (fixed 5 GB, vary workers)
# 1. H-1, 1 worker, 2 cores, 5 GB 
# 2. H-2, 2 workers, 2 cores, 5 GB
# 3. H-3, 3 workers, 2 cores, 5 GB
# 4. W-1, 1 worker, 2 cores, 5 GB (Same as H-1)
# 5. W-2, 2 workers, 2 cores, 10 GB
# 6. V-1, 3 workers, 1 core, 5 GB
# 7. V-2, 3 workers, 2 cores, 5 GB (Same as H-3)
# 8. V-3, 3 workers, 1 cores, 10 GB
# 8. V-4, 3 workers, 2 cores, 10 GB

run_experiment "H-1" 1 2 5
run_experiment "H-2" 2 2 5
run_experiment "H-3" 3 2 5
run_experiment "W-1" 1 2 5
run_experiment "W-2" 2 2 10
run_experiment "V-1" 3 1 5
run_experiment "V-2" 3 2 5
run_experiment "V-3" 3 1 10
run_experiment "V-4" 3 2 10

echo "All experiments completed. Runtimes recorded in $RESULTS_FILE"
cat $RESULTS_FILE


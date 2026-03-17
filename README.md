# Scalable Data Engineering Solution

> **Course:** Data Engineering I (1TD169) — Uppsala University, VT 2026
> **Department:** Information Technology

---

## Group 32

### Team Members

| Name | Role |
|------|------|
| Abdur Rehman Khalid | Data Engineer |
| Arnab Kumar Ghosh | Infrastructure Engineer and Core Logic Developer |
| Dip Chowdhury | Test & QA Engineer |
| Muhammad Umair | TBA |
| Pradip Kumar Das | TBA |
| Zihao Yang | TBA |

---

## Project Overview

This project demonstrates a scalable data processing pipeline using Apache Spark on a Hadoop/HDFS cluster deployed on OpenStack SSC. We process the **NYC Taxi Trips** dataset and conduct systematic scalability experiments (horizontal strong/weak scaling and vertical scaling) to evaluate performance and identify bottlenecks.

**Dataset:** NYC Taxi Trips
**Source:** https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page
**Format:** Parquet (columnar, no format conversion required)
**Target size:** 10–20 GB (several months of trip records)

**Analysis Objective:**
Filter invalid records and compute the **average trip duration and average fare amount grouped by pickup zone and hour of day**, writing results to HDFS as Parquet/CSV.

---

## Repository Structure

```
project-repo/
├── README.md                  # This file — setup & architecture overview
├── requirements.txt           # Python dependencies
├── data/                      # Sample data only (large files are in .gitignore)
├── docs/
│   ├── PROJECT_PLAN.md        # Detailed project plan & task tracking
│   └── cluster-setup-guide.md # Step-by-step cluster installation guide
├── infrastructure/            # Scripts to provision VMs on OpenStack SSC
├── src/
│   ├── config.py              # Configuration (HDFS paths, Spark settings, constants)
│   ├── etl_job.py             # Data cleaning and ingestion logic
│   └── analysis_job.py        # Main Spark aggregation logic
├── scripts/
│   ├── deploy.sh              # Deploy code to cluster Master node
│   └── run_benchmark.sh       # Run all scaling experiments (H-1/2/3, W-1/2/3, V-1/2)
├── notebooks/                 # Jupyter notebooks for data exploration
└── project-report/
    ├── report.tex             # LaTeX report source
    └── references.bib         # BibTeX references
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [docs/PROJECT_PLAN.md](docs/PROJECT_PLAN.md) | Full project plan — phases, grading targets, experiment design, submission checklist |
| [docs/cluster-setup-guide.md](docs/cluster-setup-guide.md) | Step-by-step guide for provisioning and configuring the Hadoop + Spark cluster on OpenStack SSC |

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    OpenStack SSC Cluster                 │
│                                                         │
│  ┌──────────────┐   ┌───────────┐   ┌───────────┐      │
│  │   Master     │   │  Worker 1 │   │  Worker 2 │      │
│  │  (NameNode)  │──▶│ (DataNode)│   │ (DataNode)│      │
│  │  (Spark      │   │ (Spark    │   │ (Spark    │      │
│  │   Driver)    │   │  Executor)│   │  Executor)│      │
│  │              │   └───────────┘   └───────────┘      │
│  │  Floating IP │                                       │
│  └──────────────┘   ┌───────────┐                       │
│                     │  Worker 3 │                       │
│                     │ (DataNode)│                       │
│                     │ (Spark    │                       │
│                     │  Executor)│                       │
│                     └───────────┘                       │
└─────────────────────────────────────────────────────────┘

Cluster Config:
  • VMs:         4× ssc.medium (2 vCPU, 4 GB RAM)
  • Storage:     100 GB total volume
  • HDFS:        Replication factor = 2
  • Floating IP: 1 (Master only; Workers use internal IPs)
```

**Data Pipeline:**
```
TLC Website (Parquet)
       │
       ▼  wget → Master node
   HDFS /data/nyc-taxi/          (raw Parquet)
       │
       ▼  etl_job.py
   HDFS /data/nyc-taxi-clean/    (filtered + derived columns)
       │
       ▼  analysis_job.py
   HDFS /data/results/           (avg fare & duration by zone/hour)
```

---

## Prerequisites

- Python 3.10+
- Java 8 or 11 (OpenJDK)
- Apache Hadoop 3.x
- Apache Spark 3.5+
- SSH access to OpenStack SSC cluster

---

## Setup

### 1. Clone the repository

```bash
git clone <repo-url>
cd data-engineering-I-project
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Deploy code to cluster

```bash
bash scripts/deploy.sh <master-ip>
```

---

## Data Download

On the **Master node**, download NYC Taxi Parquet files from the TLC website:

```bash
# Example: download Yellow Taxi trip records for several months
wget https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2023-01.parquet
wget https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2023-02.parquet
# ... repeat for enough months to reach ~10–20 GB

# Upload to HDFS
hdfs dfs -mkdir -p /data/nyc-taxi
hdfs dfs -put yellow_tripdata_*.parquet /data/nyc-taxi/

# Verify
hdfs dfs -ls /data/nyc-taxi/
```

---

## Running the Pipeline

### ETL Job

Reads raw Parquet from HDFS, filters invalid records, derives `trip_duration_seconds` and `pickup_hour`, and writes cleaned data back to HDFS.

```bash
spark-submit \
  --master yarn \
  src/etl_job.py
```

### Analysis Job

Reads cleaned Parquet, groups by pickup zone and hour, computes average trip duration and average fare, and writes results to HDFS.

```bash
spark-submit \
  --master yarn \
  src/analysis_job.py
```

---

## Scalability Experiments

All scaling experiments are automated via `run_benchmark.sh`:

```bash
bash scripts/run_benchmark.sh
```

### Experiment Matrix

| ID | Type | Config | Data |
|----|------|--------|------|
| H-1 | Strong (Horizontal) | 1 Worker | ~10 GB |
| H-2 | Strong (Horizontal) | 2 Workers | ~10 GB |
| H-3 | Strong (Horizontal) | 3 Workers | ~10 GB |
| W-1 | Weak (Horizontal) | 1 Worker | ~5 GB |
| W-2 | Weak (Horizontal) | 2 Workers | ~10 GB |
| W-3 | Weak (Horizontal) | 3 Workers | ~15 GB |
| V-1 | Vertical | 3 Workers, 1 core/executor | ~10 GB |
| V-2 | Vertical | 3 Workers, 2 cores/executor | ~10 GB |

Results (runtimes, speedup, efficiency) are collected in `data/results/`.

---

## License

This project is developed as part of the Data Engineering I course at Uppsala University. For academic use only.


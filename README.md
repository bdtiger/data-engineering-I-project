# Scalable Data Engineering Solution

> **Course:** Data Engineering I (1TD169) — Uppsala University, VT 2026
> **Department:** Information Technology

---

## Group 32

### Team Members

| Name |
|------|
| Abdur Rehman Khalid |
| Arnab Kumar Ghosh |
| Dip Chowdhury |
| Muhammad Umair |
| Pradip Kumar Das |
| Zihao Yang |

---

## Project Overview

This project demonstrates a scalable data processing pipeline using Apache Spark on a Hadoop/HDFS cluster. We process a large-scale dataset and conduct systematic scalability experiments (horizontal and vertical) to evaluate performance and identify bottlenecks.

**Dataset:** *TBD — pending team selection and instructor approval*
**Analysis Objective:** *TBD*

---

## Repository Structure

```
project-repo/
├── README.md                  # This file — setup & architecture overview
├── requirements.txt           # Python dependencies
├── data/                      # Sample data (large files are in .gitignore)
├── docs/                      # Project plan, contribution statements, design notes
│   └── PROJECT_PLAN.md        # Detailed project plan & task tracking
├── infrastructure/            # Scripts to provision VMs (optional)
├── src/
│   ├── config.py              # Configuration (paths, Spark settings, constants)
│   ├── etl_job.py             # Data cleaning and ingestion logic
│   └── analysis_job.py        # Main Spark analysis/aggregation logic
├── scripts/
│   ├── deploy.sh              # Deploy code to cluster
│   └── run_benchmark.sh       # Run scaling experiments (1/2/3 workers)
├── notebooks/                 # Jupyter notebooks for data exploration
└── project-report/
    ├── report.tex             # LaTeX report source
    └── references.bib         # BibTeX references
```

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
  • VMs:        4× ssc.medium (2 vCPU, 4 GB RAM)
  • Storage:    100 GB total volume
  • HDFS:       Replication factor = 2
  • Floating IP: 1 (Master only)
```

---

## Prerequisites

- Python 3.10+
- Java 8 or 11 (OpenJDK)
- Apache Hadoop 3.x
- Apache Spark 3.5+
- SSH access to OpenStack SSC cluster

---


## License

This project is developed as part of the Data Engineering I course at Uppsala University. For academic use only.

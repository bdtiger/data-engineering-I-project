# Project Plan — Data Engineering I (1TD169) VT 2026

> **Group:** Group 32
> **Dataset:** NYC Taxi Trips (selected)

---

## Key Deadlines

| Date | Milestone | Status |
|------|-----------|--------|
| Mar 1 – Mar 8 | Implementation & scalability experiments | :hourglass: In progress |
| **Mar 8** | **Presentation slides completed** | :white_circle: Not started |
| **Mar 9** | **Presentation rehearsal** | :white_circle: Not started |
| **Mar 10** | **Checkpoint presentation** (5 min + 2 min Q&A) | :white_circle: Not started |
| Mar 11–15 | Wrap-up experiments + report writing | :white_circle: Not started |
| **Mar 16** | **Final deadline** (Report + Code) | :white_circle: Not started |
| **Mar 16** | **Individual Contribution Statements** (submitted separately on Studium) | :white_circle: Not started |

---

## Dataset & Analysis Objective

**Dataset:** NYC Taxi Trips
**Source:** https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page
**Format:** Parquet (already columnar — no format conversion needed)
**Target size:** 10–20 GB (a few months of trip records; stays within the 10–50 GB recommended range)
**HDFS ingestion:** `wget` Parquet files to Master node → `hdfs dfs -put` to `/data/nyc-taxi/`

**Analysis objective (simple aggregation):**
- Filter out invalid/null records (zero-distance trips, null fare, null pickup/dropoff zone)
- Compute **average trip duration and average fare amount grouped by pickup zone and hour of day**
- Write results to HDFS as Parquet / CSV

This is a straightforward filter → group-by → aggregate task — exactly the kind of simple but realistic objective described in the project spec.

---

## Grading Target

| Points | Requirement |
|--------|-------------|
| **1 pt (Pass)** | Functional pipeline + **one** scaling experiment (Horizontal OR Vertical) + plots + basic discussion |
| **2 pts** | **Path A:** Both Horizontal AND Vertical + basic analysis  –OR–  **Path B:** One type + excellent bottleneck analysis (Amdahl's Law, network/CPU/I/O identification) |
| **3 pts** | Both Horizontal AND Vertical + exemplary analysis comparing the two approaches with insight into which scales better and why |

**Our target: 3 points** — run both experiment types and produce exemplary analysis.

---

## Cluster Constraints (strictly follow)

| Resource | Limit |
|----------|-------|
| VMs | Max 4 (1 Master + 3 Workers) |
| Flavor | `ssc.medium` — 2 vCPU, 4 GB RAM |
| Storage | Max 100 GB total attached volume |
| Floating IPs | Max 1 (Master only; Workers use internal IPs) |
| HDFS replication | `dfs.replication=2` |

**Technology stack:**
- Storage: HDFS
- Processing: Apache Spark (PySpark)
- Orchestration: Bash scripts (`deploy.sh`, `run_benchmark.sh`)
- Monitoring: Spark History Server or `htop`

---

## Repository Structure

Follows the structure required in the project spec exactly:

```
project-repo/
├── README.md               # Setup instructions & architecture diagram
├── data/                   # Small sample data only (large files in .gitignore)
├── infrastructure/         # Scripts to provision VMs
├── src/
│   ├── etl_job.py          # Cleaning and ingestion logic
│   ├── analysis_job.py     # Main Spark aggregation logic
│   └── config.py           # Configuration (paths, constants)
├── scripts/
│   ├── deploy.sh           # Copy code to cluster Master
│   └── run_benchmark.sh    # Run the 3 horizontal + 2 vertical scaling tests
├── notebooks/              # Jupyter notebooks for data exploration
└── docs/                   # Contribution statements and design notes
```

---

## Phase 1: Cluster Infrastructure Setup

**Owner:** Infrastructure Engineer

- [ ] Provision **4 VMs** on OpenStack SSC (1 Master + 3 Workers)
  - Flavor: `ssc.medium` (2 vCPU, 4 GB RAM each)
  - Attach **1 Floating IP** to Master only; Workers use internal IPs
- [ ] Set up SSH key-based access from Master to all Workers
- [ ] Install **Java** (OpenJDK 8 or 11) on all nodes
- [ ] Install & configure **Hadoop / HDFS** on all nodes
  - Set `dfs.replication=2`
  - Format namenode, start HDFS services
  - Verify: `hdfs dfsadmin -report` (all datanodes visible)
- [ ] Install & configure **Apache Spark** on all nodes
  - Configure Spark to use YARN or standalone cluster mode
  - Verify: `spark-submit --master yarn examples/pi.py`
- [ ] Add full dataset path (`data/`) to `.gitignore`

---

## Phase 2: Data Ingestion — NYC Taxi Dataset

**Owner:** Data Engineer

- [ ] Download NYC Taxi Parquet files to Master node (`wget` from TLC site)
  - Target: enough months to reach ~10–20 GB total
- [ ] Upload to HDFS: `hdfs dfs -put <local_path> /data/nyc-taxi/`
- [ ] Verify: `hdfs dfs -ls /data/nyc-taxi/` and check total size
- [ ] Inspect schema (pickup/dropoff datetime, zone IDs, fare amount, trip distance, passenger count)
- [ ] Data is already Parquet — no format conversion needed
- [ ] Test reading a single Parquet file with PySpark locally before cluster run

---

## Phase 3: ETL Pipeline (`src/etl_job.py`)

**Owner:** Data Engineer + Core Logic Developer

- [ ] Read raw Parquet files from HDFS
- [ ] Drop or filter invalid records:
  - Null `PULocationID` or `DOLocationID`
  - `trip_distance <= 0` or `fare_amount <= 0`
  - Null or malformed `tpep_pickup_datetime` / `tpep_dropoff_datetime`
- [ ] Derive new column: `trip_duration_seconds` = dropoff time − pickup time
- [ ] Extract `pickup_hour` from `tpep_pickup_datetime`
- [ ] Write cleaned data back to HDFS as Parquet (`/data/nyc-taxi-clean/`)
- [ ] Test on 1-month subset first; then run on full dataset

---

## Phase 4: Analysis Job (`src/analysis_job.py`)

**Owner:** Core Logic Developer

- [ ] Read cleaned Parquet from HDFS (`/data/nyc-taxi-clean/`)
- [ ] Group by `PULocationID` (pickup zone) and `pickup_hour`
- [ ] Aggregate:
  - `avg(trip_duration_seconds)` → average trip duration
  - `avg(fare_amount)` → average fare
  - `count(*)` → number of trips
- [ ] Write results to HDFS as CSV or Parquet (`/data/results/`)
- [ ] Spot-check a few zone/hour combinations to validate correctness
- [ ] Record end-to-end runtime for each experiment run

---

## Phase 5: Scalability Experiments (Mar 5–8)

**Owner:** Test & QA Engineer

### 5.1 Strong Scaling — Horizontal (Fixed Data, Vary Workers)

Fixed dataset: ~10 GB of cleaned NYC Taxi data

| Run | Configuration | Metric |
|-----|--------------|--------|
| H-1 | 1 Master + 1 Worker | Runtime (seconds) |
| H-2 | 1 Master + 2 Workers | Runtime (seconds) |
| H-3 | 1 Master + 3 Workers | Runtime (seconds) |

### 5.2 Weak Scaling — Horizontal (Proportional Data, Vary Workers)

Keep workload per node constant:

| Run | Configuration | Data Size | Metric |
|-----|--------------|-----------|--------|
| W-1 | 1 Worker | ~5 GB | Runtime (seconds) |
| W-2 | 2 Workers | ~10 GB | Runtime (seconds) |
| W-3 | 3 Workers | ~15 GB | Runtime (seconds) |

Goal: runtime stays roughly constant if scaling is ideal.

### 5.3 Vertical Scaling (Fixed Workers, Vary Executor Cores)

Fixed: 3 Workers, fixed 10 GB dataset

| Run | Executor Cores | Metric |
|-----|---------------|--------|
| V-1 | 1 core/executor | Runtime (seconds) |
| V-2 | 2 cores/executor | Runtime (seconds) |

### 5.4 Metrics & Plots (required for all grading levels)

- [ ] Compute **Speedup** = T₁ / Tₙ for horizontal scaling runs
- [ ] Compute **Efficiency** = Speedup / N
- [ ] Plot: Runtime vs. Number of Workers (strong scaling)
- [ ] Plot: Runtime vs. Number of Workers (weak scaling — ideally flat)
- [ ] Plot: Speedup vs. Ideal Linear Speedup (strong scaling)
- [ ] Plot: Runtime vs. Executor Cores (vertical scaling)
- [ ] Identify bottlenecks: shuffle overhead, network I/O, data skew, memory pressure
- [ ] Reference **Amdahl's Law** for theoretical comparison
- [ ] Compare horizontal vs. vertical: which is more effective for this workload and why?

**To reach 3 points:** the analysis must explicitly compare horizontal vs. vertical scaling results, identify the dominant bottleneck, and explain why one approach outperforms the other for the NYC Taxi aggregation workload.

---

## Phase 6: Checkpoint Presentation (Mar 9–10)

**Format:** 5 min presentation + 2 min Q&A
**Attendance:** Mandatory for ALL team members
**Slides:** 3–5 maximum

| Slide | Content | Time |
|-------|---------|------|
| 1 | Dataset & Context: NYC Taxi Trips — size, format (Parquet), source | 1 min |
| 2 | Analysis Objective: avg trip duration & fare by zone/hour — why it needs distributed processing | 1 min |
| 3–4 | Architecture diagram — HDFS + Spark on OpenStack SSC, cluster topology, pipeline stages | 2 min |
| 5 | Scalability experiment design (strong + weak horizontal, vertical) + current progress & obstacles | 1 min |

- [ ] Prepare architecture diagram (mandatory)
- [ ] Show preliminary results if available (even failed runs are acceptable)
- [ ] Practice timing — must stay within 5 minutes
- [ ] Distribute slides so all members speak

---

## Phase 7: Report Writing (Mar 5–15)

**Format:** PDF from LaTeX, max **2500 words** (figures, references, and code snippets excluded from word count)

### Required sections

- [ ] **Title Page** — project title, course name & code (1TD169), all member full names + email addresses, date
- [ ] **1. Background** (~400 words)
  - Domain context: urban transportation, NYC TLC data
  - Why the dataset is important/interesting
  - What analyses others have done with it (cite 2–3 relevant papers/resources)
  - Specific analysis objective (avg fare & duration by zone/hour)
- [ ] **2. Data Format & Characteristics** (~300 words)
  - Format: Parquet (columnar, compressed)
  - Schema: key columns (pickup/dropoff datetime, zone IDs, fare amount, trip distance, etc.)
  - Total size and number of records
  - Data quality issues encountered (nulls, zero-distance trips, outlier fares)
  - Why Parquet was chosen (performance benefits vs. CSV/JSON)
- [ ] **3. System Architecture & Implementation** (~800 words) — *main section*
  - **Mandatory:** system design diagram (cluster topology, data flow)
  - Choice of tools: Spark + HDFS — justify
  - Infrastructure: VM setup (4 × `ssc.medium`), OpenStack SSC, HDFS replication=2
  - Pipeline stages: ingestion → ETL → analysis → output
  - Code structure and key algorithms (group-by aggregation in PySpark)
  - Challenges faced and solutions
- [ ] **4. Scalability Experiments & Results** (~700 words)
  - Experimental design: strong horizontal scaling, weak horizontal scaling, vertical scaling
  - Results with all required plots (runtime, speedup, efficiency)
  - Analysis: did scaling work as expected? Why / why not?
  - Bottleneck identification
  - Comparison to theoretical expectations (Amdahl's Law)
  - For 3 pts: explicit comparison of horizontal vs. vertical scaling
- [ ] **5. Discussion & Conclusion** (~300 words)
  - Was the architecture suitable?
  - What worked well / what would be improved?
  - Lessons learned about distributed systems
- [ ] **6. References** — minimum 4–5, consistent citation format (IEEE recommended)

### Report tips (from project spec)
- Start writing Background and Data Format sections early while still exploring
- Devote most word count to Sections 3–4
- Figures do **not** count toward the 2500-word limit — use them liberally
- Proofread and allocate time for team review

---

## Phase 8: Final Submission Checklist (by Mar 16)

### Code Repository
- [ ] Well-organized source code with comments
- [ ] `README.md` with setup and execution instructions
- [ ] Sample data or instructions to download it from TLC website
- [ ] `scripts/run_benchmark.sh` — reproduces all scaling experiments
- [ ] `requirements.txt` ✅
- [ ] Large data files added to `.gitignore`
- [ ] Repository accessible to teachers (GitHub usernames): `prasi372`, `usamazf`, `zls0319`

### Report
- [ ] PDF format, max 2500 words (verify word count)
- [ ] All required sections included
- [ ] Figures numbered and referenced in text
- [ ] References formatted consistently
- [ ] Repository link included in report
- [ ] All team members listed on title page

### Experiments
- [ ] Strong scaling (horizontal) completed — all 3 runs logged
- [ ] Weak scaling (horizontal) completed — all 3 runs logged
- [ ] Vertical scaling completed — both runs logged
- [ ] All plots generated and included in report
- [ ] Scripts to reproduce experiments committed to repo

### Individual Contribution Statements (each member submits separately on Studium)
- [ ] PDF, 1 page maximum
- [ ] Includes: full name, team members list, contributions by phase (planning / implementation / experiments / writing / collaboration), estimated hours, acknowledgment of teammates' work
- [ ] Specific — lists exact files written, experiments run, sections drafted
- [ ] Signed and dated

---

## Communication

- [ ] WhatsApp
- [ ] Set up Git branching strategy (feature branches + PRs recommended)

---

> :warning: **Remember:** The grade is based on **scalability demonstration**, NOT analysis complexity. Keep the analysis simple. Focus on engineering!

# From OLTP to OLAP: Is PostgreSQL Eating Analytics Too?

Benchmark data and analysis scripts for the talk presented at [Berlin Buzzwords 2026](https://2026.berlinbuzzwords.de/session/from-oltp-to-olap-is-postgresql-eating-analytics-too/) by [Daniel Seybold](https://2026.berlinbuzzwords.de/speaker/daniel-seybold/) (benchANT) — Maschinenhaus, 8 June 2026.

## Talk Abstract

Can PostgreSQL become a serious analytics engine? With emerging columnar extensions, PostgreSQL is pushing beyond OLTP into OLAP territory. This talk explores the current columnar landscape, architectural trade-offs, and how far PostgreSQL can go compared to analytical engines like ClickHouse.

PostgreSQL is now gaining columnar capabilities through extensions such as Citus, TigerData columnar, pg_duckdb, and more — built on PostgreSQL's pluggable storage layer. We provide a structured overview of the PostgreSQL columnar ecosystem, place these developments in the broader context of modern database trends (HTAP ambitions, data stack consolidation), and discuss selected performance observations comparing columnar PostgreSQL setups to ClickHouse.

---

## Repository Structure

```
.
├── clickbench/
│   ├── data/                          # Raw benchmark result files (3 systems)
│   │   ├── olap_clickbench_clickhouse-aws-run-1-iteration_0_d3XK1J2u/
│   │   ├── olap_clickbench_postgresql-indexed-pgduckdb-run-1-iteration_0_9nU9BIvR/
│   │   └── olap_clickbench_postgresql-indexed-plain-run-1-iteration_0_NhuERdJ8/
│   ├── charts/                        # Generated charts
│   │   ├── clickbench_p95_latency.png
│   │   └── clickbench_pg_p95_comparison.png
│   └── utils/                         # Analysis and plotting scripts
│       ├── plot_clickbench_latency.py      # 3-system bar chart
│       ├── plot_clickbench_pg_comparison.py # PG vs pg_duckdb tiered comparison
│       └── analyze_tiers.py               # Best/worst queries per tier
│
└── tpc-ds/
    ├── 10gb/                          # Raw benchmark result files (3 systems, 10 GB)
    │   ├── olap_tpc-ds_clickhouse-aws-10gb-1-thread-sequential_0_CXr4UXO4/
    │   ├── olap_tpc-ds_postgresql-pg_duckdb-10gb-1-thread-sequential_0_9QYv4eVb/
    │   └── olap_tpc-ds_postgresql-plain-10gb-1-thread-sequential_0_4ivcQAtK/
    ├── 100gb/                         # Raw benchmark result files (2 systems, 100 GB)
    │   ├── olap_tpc-ds_postgresql-pg_duckdb-100gb-1-thread-sequential-1-iterations_0_3vDNNYJr/
    │   └── olap_tpc-ds_postgresql-plain-100gb-1-thread-sequential-1-iterations_0_weWMXyrj/
    ├── charts/                        # Generated charts
    │   └── tpcds_10gb_p95_latency.png
    └── utils/                         # Analysis and plotting scripts
        ├── plot_tpcds_latency.py          # 3-system TPC-DS 10 GB bar chart
        ├── analyze_tpcds_wdl.py           # Win/draw/loss table + pairwise analysis
        ├── best_worst_per_dbms.py         # Best and worst query per DBMS
        └── analyze_100gb.py               # Win/draw/loss analysis for 100 GB
```

---

## Benchmarks

### ClickBench

[ClickBench](https://benchmark.clickhouse.com/) is a benchmark for analytical workloads inspired by a real-world web analytics use case. It consists of 43 queries over a single wide table (≈100 million rows).

**Systems compared:**

| System | Description |
|--------|-------------|
| ClickHouse (AWS) | Columnar OLAP engine — baseline reference |
| PostgreSQL 17 + pg_duckdb | PostgreSQL with the [pg_duckdb](https://github.com/duckdb/pg_duckdb) extension (v1.1.1) |
| PostgreSQL 17 (indexed) | Standard PostgreSQL with appropriate indexes |

**Setup:** 1 cold run per query (`operationCount=1`). P95 latency equals the single cold-run execution time.

#### Key results

**ClickBench — pg_duckdb vs. PostgreSQL indexed (tiered, 10 % draw threshold)**

| Tier | Queries | pg_duckdb wins | Draws | PG wins |
|------|---------|---------------|-------|---------|
| Fast (< 15 s) | 15 | 2 | 4 | 9 |
| Medium (15 – 150 s) | 9 | 5 | 3 | 1 |
| Heavy (≥ 150 s) | 19 | 5 | 11 | 3 |

> PostgreSQL's index-backed execution dominates on fast queries. pg_duckdb's DuckDB engine provides meaningful advantages on heavier, scan-heavy workloads.

**Charts:** [`clickbench/charts/`](clickbench/charts/)

---

### TPC-DS

[TPC-DS](https://www.tpc.org/tpcds/) is an industry-standard decision-support benchmark. This study uses a 10-query subset (Q03, Q07, Q19, Q42, Q52, Q56, Q26, Q68, Q73, Q96) run at **10 GB** and **100 GB** scale factors.

**Systems compared (10 GB):** ClickHouse (AWS), PostgreSQL 17 + pg_duckdb, PostgreSQL 17 plain  
**Systems compared (100 GB):** PostgreSQL 17 + pg_duckdb, PostgreSQL 17 plain

**Setup (10 GB):** 100 iterations per query, sequential single-thread execution.  
**Setup (100 GB):** 1 cold run per query, sequential single-thread execution.

#### Key results — TPC-DS 10 GB (P95 latency)

| Query | ClickHouse | pg_duckdb | PostgreSQL | Winner |
|-------|-----------|-----------|------------|--------|
| Q03 | 1.32 s | 1.99 s | **0.13 s** | PostgreSQL (10.3×) |
| Q07 | 4.46 s | **1.44 s** | 3.92 s | pg_duckdb (2.73×) |
| Q19 | 1.32 s | 1.10 s | 1.17 s | Draw |
| Q42 | **0.35 s** | 0.86 s | 0.77 s | ClickHouse (2.22×) |
| Q52 | **0.32 s** | 0.93 s | 0.76 s | ClickHouse (2.42×) |
| Q56 | **0.32 s** | 0.86 s | 0.51 s | ClickHouse (1.60×) |
| Q26 | 2.14 s | **0.96 s** | 2.25 s | pg_duckdb (2.22×) |
| Q68 | 1.43 s | 1.31 s | 1.38 s | Draw (all three) |
| Q73 | 0.97 s | 0.93 s | 1.04 s | Draw |
| Q96 | **0.66 s** | 2.45 s | 1.10 s | ClickHouse (1.66×) |

**Overall wins (10 GB):** ClickHouse: 4 | pg_duckdb: 2 | PostgreSQL: 1 | Draws: 3

#### Key results — TPC-DS 100 GB (cold run)

| Query | pg_duckdb | PostgreSQL | Winner |
|-------|-----------|------------|--------|
| Q03 | 7.0 min | **4.7 s** | PostgreSQL (88×) |
| Q07 | 7.0 min | **5.5 min** | PostgreSQL (1.26×) |
| Q19 | 7.0 min | 10.8 min | pg_duckdb (1.54×) |
| Q42 | 7.0 min | 10.1 min | pg_duckdb (1.45×) |
| Q52 | 7.0 min | 10.1 min | pg_duckdb (1.45×) |
| Q56 | 7.0 min | **1.9 min** | PostgreSQL (3.74×) |
| Q26 | 7.5 min | **5.7 min** | PostgreSQL (1.32×) |
| Q68 | 7.6 min | **6.0 min** | PostgreSQL (1.25×) |
| Q73 | 7.0 min | **5.3 min** | PostgreSQL (1.31×) |
| Q96 | 7.0 min | **5.3 min** | PostgreSQL (1.31×) |

**Score (100 GB):** PostgreSQL: 7 wins | pg_duckdb: 3 wins

> Note: The nearly identical pg_duckdb latencies (~7 min) for Q03–Q96 in the 100 GB run indicate fallback to the PostgreSQL executor, likely due to DuckDB-side memory constraints (`duckDbForceExecution=false`, `memoryLimit=24096 MB`).

**Charts:** [`tpc-ds/charts/`](tpc-ds/charts/)

---

## Infrastructure & Configuration

All benchmarks were run using [benchANT](https://benchant.com/) — an automated database benchmarking platform.

| Parameter | Value |
|-----------|-------|
| Cloud provider | AWS, eu-central-1 |
| Instance type | `m7i.2xlarge` (8 vCPU, 32 GB RAM) |
| Storage | GP3, 500 GB, 12,000 IOPS, 600 MB/s |
| PostgreSQL version | 17 |
| pg_duckdb version | v1.1.1 |
| pg_duckdb config | `memoryLimit=24096MB`, `workerThreads=8`, `duckDbForceExecution=false` |
| PostgreSQL config | `effectiveCacheSize=24GB`, `workMem=38836kB` |

---

## Raw Data Format

Result files follow the [YCSB](https://github.com/brianfrankcooper/YCSB) output format. Each query produces a line of the form:

```
[QUERY-query16], 95thPercentileLatency(us), 418381823
```

Latency values are in **microseconds**. Divide by `1_000_000` to convert to seconds.

### Query label mapping (internal → TPC-DS)

| Internal ID | TPC-DS query |
|-------------|-------------|
| query16 | Q03 |
| query17 | Q07 |
| query18 | Q19 |
| query19 | Q42 |
| query20 | Q52 |
| query21 | Q56 |
| query22 | Q26 |
| query23 | Q68 |
| query24 | Q73 |
| query25 | Q96 |

---

## Reproducing the Charts

The scripts require Python 3 with `matplotlib`, `numpy`, and standard library modules.

```bash
# ClickBench — 3-system latency chart
python clickbench/utils/plot_clickbench_latency.py

# ClickBench — pg_duckdb vs. PostgreSQL tiered comparison
python clickbench/utils/plot_clickbench_pg_comparison.py

# ClickBench — best/worst queries per tier
python clickbench/utils/analyze_tiers.py

# TPC-DS 10 GB — 3-system latency chart
python tpc-ds/utils/plot_tpcds_latency.py

# TPC-DS 10 GB — win/draw/loss analysis
python tpc-ds/utils/analyze_tpcds_wdl.py

# TPC-DS 10 GB — best/worst query per DBMS
python tpc-ds/utils/best_worst_per_dbms.py

# TPC-DS 100 GB — pg_duckdb vs. PostgreSQL analysis
python tpc-ds/utils/analyze_100gb.py
```

---

## License

Data and scripts are released under the [MIT License](LICENSE).

---

## Citation / Attribution

If you use this data, please attribute it as:

> Daniel Seybold, *From OLTP to OLAP: Is PostgreSQL Eating Analytics Too?*, Berlin Buzzwords 2026, benchANT.  
> https://github.com/benchANT/berlin-buzzwords-from-OLTP-to-OLAP-is-PostgreSQL-eating-analytics-too

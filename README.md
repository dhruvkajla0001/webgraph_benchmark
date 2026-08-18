````markdown
# Graph Database Benchmark

A database-agnostic benchmarking framework for evaluating the performance, scalability, and reliability of modern graph databases under realistic graph workloads.

This project benchmarks multiple graph database systems using the same dataset, workload definitions, measurement methodology, and hardware environment to provide a fair performance comparison.

---

## Overview

Graph databases are designed for workloads involving highly connected data, where traditional relational databases can become inefficient for relationship-heavy queries.

This project evaluates how different graph database technologies perform across:

- Point lookups
- Filtered lookups
- 1-hop graph traversals
- 2-hop graph traversals
- 3-hop graph traversals
- Degree aggregation
- Concurrent read/write workloads

The benchmark framework is designed to be database-agnostic, allowing different graph databases to be tested through a common adapter interface.

### Databases Benchmarked

The project currently evaluates:

| Database | Type |
|---|---|
| CognoDB | Cloud graph database |
| Neo4j | Native graph database |
| Memgraph | Native graph database |
| FalkorDB | Redis-based graph database |
| ArangoDB | Multi-model database with graph capabilities |

---

# Dataset

The benchmark uses the SNAP `soc-Pokec` social network dataset.

The processed benchmark dataset contains:

- **91,489 nodes**
- **200,000 relationships**

The graph is represented using:

```text
Person
  |
  | KNOWS
  v
Person
````

Each node contains a deterministic integer ID, allowing the same node samples to be used across databases.

---

# Benchmark Architecture

The project uses a common benchmark framework rather than writing completely independent benchmark implementations for each database.

```text
                    ┌──────────────────────┐
                    │   Benchmark Runner   │
                    └──────────┬───────────┘
                               │
                ┌──────────────┼──────────────┐
                │              │              │
                ▼              ▼              ▼
          Sequential      Concurrent      Metrics
           Workloads       Workloads       Collector
                │              │              │
                └──────────────┼──────────────┘
                               │
                     Database Adapters
                               │
       ┌────────────┬──────────┼──────────┬────────────┐
       ▼            ▼          ▼          ▼            ▼
    CognoDB       Neo4j     Memgraph   FalkorDB    ArangoDB
```

Each database implements an adapter that exposes a common execution interface.

This allows the same workloads to be executed against every database.

---

# Sequential Benchmark

Each sequential workload is executed using:

* 10 warm-up iterations
* 100 measured iterations
* Deterministic node sampling
* Latency measurement for every operation

The following metrics are collected:

* Minimum latency
* Mean latency
* p50 latency
* p95 latency
* Maximum latency
* Successful iterations
* Failed iterations

### Sequential Workloads

#### 1. Point Lookup

Tests retrieving a specific node by its ID.

Example concept:

```cypher
MATCH (p:Person {id: $node_id})
RETURN p
```

This measures basic indexed node lookup performance.

---

#### 2. Filtered Lookup

Tests retrieving nodes using an additional property/filter condition.

This represents a more selective graph query than a direct primary-key lookup.

---

#### 3. 1-Hop Traversal

Measures the cost of traversing one relationship from a starting node.

```text
Person → Person
```

---

#### 4. 2-Hop Traversal

Measures traversal across two relationship levels.

```text
Person → Person → Person
```

---

#### 5. 3-Hop Traversal

Measures deeper graph traversal.

```text
Person → Person → Person → Person
```

---

#### 6. Degree Aggregation

Measures aggregation over graph relationships, such as calculating node degree.

This is intentionally more computationally expensive than point lookups and simple traversals.

---

# Concurrent Read/Write Benchmark

The project also evaluates database behavior under mixed read/write workloads.

The workload uses:

```text
80% Reads
20% Writes
```

Each benchmark configuration includes:

* 10-second warm-up period
* 30-second measurement period
* Concurrency levels:

  * 1
  * 10
  * 40

The benchmark measures:

* Total operations
* Throughput (QPS)
* Read p50
* Read p95
* Write p50
* Write p95
* Successful operations
* Failed operations
* Error rate
* Retryable transaction conflicts

This benchmark is intended to evaluate how databases behave as concurrent workload increases.

---

# Final Sequential Results

The benchmark produced the following p50 latency results.

| Database |     Point |  Filtered |     1-Hop |     2-Hop |     3-Hop |     Degree |
| -------- | --------: | --------: | --------: | --------: | --------: | ---------: |
| CognoDB  | 611.47 ms | 614.33 ms | 526.49 ms | 520.54 ms | 519.92 ms | 6711.05 ms |
| Neo4j    |  93.59 ms |  14.51 ms |  11.37 ms |  10.15 ms |   7.31 ms |  309.67 ms |
| Memgraph |   6.70 ms |   8.51 ms |   5.82 ms |   4.90 ms |   5.53 ms |  163.41 ms |
| FalkorDB |   3.24 ms |   3.14 ms |   2.10 ms |   1.90 ms |   1.95 ms |  284.50 ms |
| ArangoDB |  47.92 ms |  55.32 ms |  47.56 ms |  45.49 ms |  45.69 ms |  635.27 ms |

Lower latency is better.

### Key Observation

FalkorDB and Memgraph produced the lowest latency for the tested interactive graph workloads.

Neo4j also performed strongly, particularly for graph traversal workloads.

ArangoDB showed relatively consistent latency across the traversal workloads but was slower than Memgraph and FalkorDB in this benchmark environment.

CognoDB showed significantly higher latency, particularly for aggregation workloads. As a cloud database, its measurements may include network and service-level latency that differs from locally hosted databases.

---

# Concurrent Read/Write Results

### Concurrency = 1

| Database |   QPS |  Read p50 |  Write p50 | Errors |
| -------- | ----: | --------: | ---------: | -----: |
| CognoDB  | 0.972 | 705.87 ms | 756.997 ms |      0 |
| Neo4j    | 0.957 | 273.06 ms | 1593.53 ms |      0 |
| Memgraph | 41.93 |  21.30 ms |   21.91 ms |      0 |
| FalkorDB | 80.77 |  11.04 ms |       N/A* |    608 |
| ArangoDB | 20.71 |  47.23 ms |   49.75 ms |      0 |

### Concurrency = 10

| Database |    QPS |   Read p50 |  Write p50 | Errors |
| -------- | -----: | ---------: | ---------: | -----: |
| CognoDB  |  2.032 | 4518.73 ms | 6196.77 ms |      0 |
| Neo4j    |  6.161 | 1003.58 ms | 1599.94 ms |      0 |
| Memgraph | 236.39 |   36.94 ms |   38.33 ms |      0 |
| FalkorDB | 351.05 |   23.62 ms |       N/A* |   2640 |
| ArangoDB | 197.47 |   48.77 ms |   50.01 ms |      0 |

### Concurrency = 40

| Database |    QPS |    Read p50 |   Write p50 | Errors |
| -------- | -----: | ----------: | ----------: | -----: |
| CognoDB  |   3.12 | 11119.81 ms | 11148.47 ms |      0 |
| Neo4j    |  7.103 |  4575.93 ms |  7099.16 ms |      0 |
| Memgraph | 251.48 |   120.36 ms |   118.34 ms |      0 |
| FalkorDB | 641.28 |    48.62 ms |        N/A* |  52139 |
| ArangoDB |    0.0 |      0.0 ms |      0.0 ms |  20123 |

* FalkorDB's concurrent benchmark encountered write/operation failures at higher concurrency, so write latency was not available for those failed operations.

---

# Important Reliability Finding

Throughput alone should not be used to determine the winner.

For example, FalkorDB achieved the highest reported throughput at concurrency 40:

```text
641.275 QPS
```

However, the benchmark also recorded:

```text
52,139 failed operations
```

This resulted in a high error rate.

Similarly, ArangoDB at concurrency 40 experienced:

```text
20,123 failed operations
0 successful operations
0 QPS
```

Therefore, the benchmark evaluates both:

```text
Performance + Reliability
```

rather than throughput alone.

---

# Results Generated

The benchmark automatically produces consolidated result files.

### Sequential Results

```text
results/
├── cognodb_sequential.json
├── neo4j_sequential.json
├── memgraph_sequential.json
├── falkordb_sequential.json
├── arangodb_sequential.json
└── sequential_summary.csv
```

### Concurrent Results

```text
results/
├── cognodb_concurrent_read_write.json
├── neo4j_concurrent_read_write.json
├── memgraph_concurrent_read_write.json
├── falkordb_concurrent_read_write.json
├── arangodb_concurrent_read_write.json
└── concurrent_summary.csv
```

---

# Final Benchmark Report

A report generation script consolidates the benchmark results into a final technical report.

Run:

```powershell
python scripts/generate_final_report.py
```

The generated report is:

```text
docs/BENCHMARK_REPORT.md
```

Charts are generated under:

```text
docs/charts/
```

The report contains:

* Benchmark methodology
* Dataset information
* Sequential benchmark results
* Concurrent benchmark results
* Latency comparisons
* Throughput comparisons
* Scalability analysis
* Reliability analysis
* Error-rate analysis
* Benchmark limitations
* Final observations

---

# Project Structure

```text
webgraph_benchmark/
│
├── benchmarks/
│   ├── cognodb.py
│   ├── neo4j.py
│   ├── memgraph.py
│   ├── falkordb.py
│   ├── arangodb.py
│   └── runner.py
│
├── workloads/
│   ├── node_ids.py
│   ├── point_lookup.py
│   ├── filtered_lookup.py
│   ├── traversal.py
│   ├── degree_aggregation.py
│   └── concurrent_read_write.py
│
├── scripts/
│   ├── load_cognodb.py
│   ├── load_memgraph.py
│   ├── load_falkordb.py
│   ├── load_arangodb.py
│   ├── test_cognodb.py
│   ├── test_memgraph.py
│   ├── test_falkordb.py
│   ├── test_arangodb.py
│   ├── test_*_concurrent_read_write.py
│   └── generate_final_report.py
│
├── data/
│   └── processed/
│       ├── nodes.csv
│       └── relationships.csv
│
├── results/
│   ├── *.json
│   └── *_summary.csv
│
├── docs/
│   ├── BENCHMARK_REPORT.md
│   └── charts/
│
├── config/
│   └── databases.yaml
│
├── requirements.txt
└── README.md
```

---

# How to Run

## 1. Clone the repository

```bash
git clone <repository-url>
cd webgraph_benchmark
```

## 2. Create a virtual environment

```powershell
py -3.12 -m venv .venv
```

Activate it:

```powershell
.venv\Scripts\activate
```

## 3. Install dependencies

```powershell
pip install -r requirements.txt
```

Additional reporting dependency:

```powershell
pip install matplotlib
```

---

# Database Setup

The benchmark supports both locally hosted and cloud databases.

Local databases used in the project include:

* Memgraph
* FalkorDB
* ArangoDB

Example FalkorDB:

```powershell
docker run -d `
  --name webgraph-falkordb `
  -p 6379:6379 `
  falkordb/falkordb:latest
```

Example ArangoDB:

```powershell
docker run -d `
  --name webgraph-arangodb `
  -p 8529:8529 `
  -e ARANGO_ROOT_PASSWORD=benchmark_password `
  arangodb:latest
```

---

# Loading the Dataset

Each database has its own loader.

For example:

```powershell
python scripts/load_falkordb.py
```

```powershell
python scripts/load_memgraph.py
```

```powershell
python scripts/load_arangodb.py
```

The loader verifies:

```text
Nodes:          91,489
Relationships:  200,000
```

before the database is considered ready for benchmarking.

---

# Running Sequential Benchmarks

Example:

```powershell
python scripts/test_memgraph.py
```

```powershell
python scripts/test_falkordb.py
```

```powershell
python scripts/test_arangodb.py
```

Results are stored in:

```text
results/
```

---

# Running Concurrent Benchmarks

Example:

```powershell
python scripts/test_memgraph_concurrent_read_write.py
```

```powershell
python scripts/test_falkordb_concurrent_read_write.py
```

```powershell
python scripts/test_arangodb_concurrent_read_write.py
```

The concurrent benchmark evaluates:

```text
Concurrency:
1
10
40
```

with:

```text
80% reads
20% writes
```

---

# Methodology

To improve comparability:

1. The same processed graph dataset is loaded into each database.
2. The same node sampling strategy is used.
3. The same logical workloads are executed.
4. Warm-up iterations are performed before measurement.
5. 100 iterations are used for sequential workloads.
6. Latency distributions are collected rather than relying only on averages.
7. Concurrent tests use the same read/write ratio.
8. Results are stored as structured JSON.
9. Summary CSV files are generated for cross-database comparison.
10. Errors and failed operations are recorded separately from throughput.

---

# Important Benchmark Limitations

These results should be interpreted as an engineering benchmark rather than a universal ranking of graph databases.

Performance can vary significantly depending on:

* Hardware
* CPU
* Memory
* Storage
* Network latency
* Database configuration
* Query planner behavior
* Index configuration
* Dataset size
* Database version
* Cloud infrastructure
* Connection pooling
* Client-driver implementation

In particular, CognoDB was accessed as a cloud database while several other databases were running locally. Therefore, network/service latency can influence the results.

The benchmark should therefore be used to understand relative behavior under this specific test environment rather than claiming that one database is universally faster than another.

---

# Key Takeaways

The benchmark demonstrates several important characteristics of graph database systems.

### Interactive graph queries

Memgraph and FalkorDB produced very low sequential latency for the tested point lookups and traversal workloads.

### Traversal performance

Graph traversal latency remained low for Memgraph and FalkorDB, while Neo4j also demonstrated strong traversal performance.

### Aggregation workloads

Degree aggregation was substantially more expensive across all databases, demonstrating the difference between simple indexed lookups and graph-wide aggregation operations.

### Concurrency

Memgraph maintained zero recorded errors across the tested concurrency levels while scaling from:

```text
41.93 QPS → 236.39 QPS → 251.48 QPS
```

FalkorDB reported higher throughput, but the higher concurrency levels also produced significant operation failures.

### Reliability matters

The benchmark demonstrates why evaluating only QPS can be misleading.

A database producing high throughput with a large number of failed operations should not automatically be considered superior to a database producing lower throughput with successful operations.

---

# Technologies Used

* Python 3.12
* Redis / FalkorDB
* Memgraph
* Neo4j
* ArangoDB
* CognoDB
* Docker
* Cypher
* AQL
* Redis Graph commands
* Pandas
* Matplotlib
* CSV / JSON
* PowerShell

---

# Project Goals

This project was built to demonstrate practical experience with:

* Database benchmarking
* Graph databases
* Query performance analysis
* Latency measurement
* Throughput measurement
* Concurrent workloads
* Database adapters
* Deterministic benchmarking
* Performance engineering
* Reliability analysis
* Data visualization
* Automated technical reporting

---

# Author

**Dhruv Kajla**

AI Engineering / Data Engineering

This project was developed as a practical graph database benchmarking and performance analysis project.

````

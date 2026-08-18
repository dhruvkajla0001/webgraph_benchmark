# Graph Database Benchmark Report

## 1. Executive Summary

This benchmark evaluates five graph database platforms using a common graph dataset, common logical workloads, and a database-agnostic benchmark harness:

- CognoDB
- Neo4j
- Memgraph
- FalkorDB
- ArangoDB

The benchmark evaluates both **sequential query performance** and **concurrent mixed read/write behavior**.

The sequential benchmark uses:

- Point lookup
- Filtered lookup
- 1-hop traversal
- 2-hop traversal
- 3-hop traversal
- Degree aggregation

The concurrent benchmark uses an **80% read / 20% write workload** at:

- 1 concurrent client
- 10 concurrent clients
- 40 concurrent clients

Each sequential workload uses **10 warm-up iterations followed by 100 measured iterations**.

### Key findings

**FalkorDB achieved the lowest sequential p50 latency across all six measured workloads.** Its traversal latency was particularly strong, with p50 values around 1.9–2.1 ms for 2-hop and 3-hop traversal.

**Memgraph provided the strongest combination of low latency and reliable concurrency.** It sustained 251.48 QPS at concurrency 40 with zero failed operations.

**FalkorDB produced the highest raw concurrent throughput**, reaching 641.275 QPS at concurrency 40. However, this result was accompanied by a **72.99% error rate**, meaning the raw throughput cannot be interpreted as sustainable successful throughput.

**ArangoDB scaled successfully through concurrency 10**, reaching 197.468 QPS with zero errors, but the concurrency-40 test failed completely with a 100% error rate.

**Neo4j and CognoDB maintained zero errors across all concurrency levels**, but their throughput was substantially lower and latency increased considerably as concurrency increased.

Overall, the benchmark suggests that **Memgraph provides the best balance of latency, throughput, and reliability for this workload**, while **FalkorDB provides the strongest raw sequential and peak-throughput performance but exhibits significant concurrency failure behavior under the tested workload**.

---

# 2. Benchmark Scope

The benchmark was designed to compare graph databases using the same logical operations and dataset.

The evaluation covers four major areas:

1. Data ingestion
2. Sequential query latency
3. Concurrent read/write performance
4. Failure behavior under increasing concurrency

The benchmark intentionally records both latency and failures so that a database cannot appear performant simply by producing a high number of operations while dropping a large percentage of requests.

---

# 3. Dataset

The benchmark uses a processed graph derived from the **SNAP soc-Pokec dataset**.

The same processed graph was loaded into each database.

### Dataset size

| Metric | Value |
|---|---:|
| Nodes | 91,489 |
| Relationships | 200,000 |
| Node label | `Person` |
| Relationship type | `KNOWS` |

The benchmark uses deterministic node sampling for workload execution so that the databases are evaluated against comparable query inputs.

---

# 4. Benchmark Methodology

## 4.1 Sequential workloads

Each sequential workload uses:

- 10 warm-up iterations
- 100 measured iterations
- p50 latency
- p95 latency
- mean latency
- minimum latency
- maximum latency
- successful iterations
- failed iterations

All measured sequential workloads completed:

**100/100 successful iterations with zero errors for all five databases.**

### Sequential workloads

| Workload | Description |
|---|---|
| `point_lookup` | Lookup of a specific node by identifier |
| `filtered_lookup` | Indexed/filtered node lookup |
| `1_hop` | Traversal to directly connected nodes |
| `2_hop` | Two-hop graph traversal |
| `3_hop` | Three-hop graph traversal |
| `degree_aggregation` | Aggregation of graph degree information |

---

## 4.2 Concurrent read/write workload

The concurrent benchmark uses:

- 80% reads
- 20% writes
- 10-second warm-up
- 30-second measurement period
- concurrency levels of 1, 10, and 40

The following metrics are recorded:

- Total operations
- Successful operations
- Failed operations
- Throughput/QPS
- Read p50
- Read p95
- Write p50
- Write p95
- Error rate
- Retryable conflicts

A high-throughput result with a high error rate is treated as a degraded/saturated result rather than a clean performance win.

---

# 5. Sequential Results

## 5.1 Complete Sequential Results

| Database | Workload | p50 (ms) | p95 (ms) | Mean (ms) |
|---|---|---:|---:|---:|
| CognoDB | Point lookup | 611.47 | 2262.28 | 808.31 |
| CognoDB | Filtered lookup | 614.33 | 2673.51 | 898.50 |
| CognoDB | 1-hop | 526.49 | 2413.04 | 742.95 |
| CognoDB | 2-hop | 520.54 | 2291.50 | 694.41 |
| CognoDB | 3-hop | 519.92 | 2374.92 | 692.10 |
| CognoDB | Degree aggregation | 6711.05 | 7837.47 | 6515.29 |
| Neo4j | Point lookup | 93.59 | 186.95 | 83.84 |
| Neo4j | Filtered lookup | 14.51 | 93.95 | 44.97 |
| Neo4j | 1-hop | 11.37 | 94.91 | 39.00 |
| Neo4j | 2-hop | 10.15 | 96.55 | 36.87 |
| Neo4j | 3-hop | 7.31 | 80.77 | 21.05 |
| Neo4j | Degree aggregation | 309.67 | 816.79 | 573.10 |
| Memgraph | Point lookup | 6.70 | 13.52 | 7.76 |
| Memgraph | Filtered lookup | 8.51 | 16.03 | 9.85 |
| Memgraph | 1-hop | 5.82 | 8.54 | 5.92 |
| Memgraph | 2-hop | 4.90 | 6.84 | 6.24 |
| Memgraph | 3-hop | 5.53 | 9.07 | 5.97 |
| Memgraph | Degree aggregation | 163.41 | 335.74 | 190.45 |
| FalkorDB | Point lookup | **3.24** | **7.50** | **3.77** |
| FalkorDB | Filtered lookup | **3.14** | **4.73** | **3.22** |
| FalkorDB | 1-hop | **2.10** | **3.15** | **2.30** |
| FalkorDB | 2-hop | **1.90** | **2.48** | **1.95** |
| FalkorDB | 3-hop | **1.95** | **2.71** | **2.01** |
| FalkorDB | Degree aggregation | **284.50** | **689.63** | **341.95** |
| ArangoDB | Point lookup | 47.92 | 55.21 | 48.69 |
| ArangoDB | Filtered lookup | 55.32 | 76.32 | 57.74 |
| ArangoDB | 1-hop | 47.56 | 53.84 | 47.99 |
| ArangoDB | 2-hop | 45.49 | 51.85 | 47.00 |
| ArangoDB | 3-hop | 45.69 | 52.19 | 55.89 |
| ArangoDB | Degree aggregation | 635.27 | 747.45 | 644.39 |

---

# 6. Sequential Performance Analysis

## 6.1 Point Lookup

FalkorDB recorded the lowest p50 latency at:

**3.24 ms**

Memgraph followed at:

**6.70 ms**

ArangoDB recorded:

**47.92 ms**

Neo4j recorded:

**93.59 ms**

CognoDB recorded:

**611.47 ms**

This makes FalkorDB approximately **2× faster than Memgraph at p50** for the measured point lookup workload.

---

## 6.2 Filtered Lookup

FalkorDB again achieved the lowest p50:

**3.14 ms**

Memgraph:

**8.51 ms**

Neo4j:

**14.51 ms**

ArangoDB:

**55.32 ms**

CognoDB:

**614.33 ms**

The indexed lookup workload therefore strongly favors the low-latency graph engines in this environment.

---

## 6.3 Multi-hop Traversals

FalkorDB produced the lowest p50 latency for:

- 1-hop: 2.10 ms
- 2-hop: 1.90 ms
- 3-hop: 1.95 ms

Memgraph was the next fastest:

- 1-hop: 5.82 ms
- 2-hop: 4.90 ms
- 3-hop: 5.53 ms

Neo4j was slower but remained significantly faster than CognoDB.

The results demonstrate that the in-memory/local graph engines performed particularly well on the traversal workloads used in this benchmark.

---

## 6.4 Degree Aggregation

Degree aggregation was substantially more expensive than the lookup and traversal workloads.

The lowest measured p50 was Memgraph:

**163.41 ms**

FalkorDB:

**284.50 ms**

Neo4j:

**309.67 ms**

ArangoDB:

**635.27 ms**

CognoDB:

**6711.05 ms**

This workload therefore exposes a substantially different performance profile from simple point and traversal queries.

---

# 7. Concurrent Read/Write Results

## 7.1 Complete Results

| Database | Concurrency | QPS | Read p50 | Read p95 | Write p50 | Write p95 | Errors | Error Rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| CognoDB | 1 | 0.972 | 705.87 | 2624.05 | 757.00 | 2889.82 | 0 | 0% |
| CognoDB | 10 | 2.032 | 4518.73 | 4750.63 | 6196.77 | 8944.43 | 0 | 0% |
| CognoDB | 40 | 3.120 | 11119.81 | 16766.81 | 11148.47 | 16717.68 | 0 | 0% |
| Neo4j | 1 | 0.957 | 273.06 | 2942.02 | 1593.53 | 3068.77 | 0 | 0% |
| Neo4j | 10 | 6.161 | 1003.58 | 4515.49 | 1599.94 | 11494.76 | 0 | 0% |
| Neo4j | 40 | 7.103 | 4575.93 | 7100.11 | 7099.16 | 16434.85 | 0 | 0% |
| Memgraph | 1 | **41.930** | 21.30 | 32.64 | 21.91 | 32.57 | 0 | **0%** |
| Memgraph | 10 | **236.386** | 36.94 | 69.75 | 38.33 | 72.16 | 0 | **0%** |
| Memgraph | 40 | **251.480** | 120.36 | 340.01 | 118.34 | 397.72 | 0 | **0%** |
| FalkorDB | 1 | 80.769 | 11.04 | 17.22 | — | — | 608 | 20.05% |
| FalkorDB | 10 | 351.046 | 23.62 | 52.87 | — | — | 2640 | 20.02% |
| FalkorDB | 40 | **641.275*** | 48.62 | 73.29 | — | — | 52139 | **72.99%** |
| ArangoDB | 1 | 20.712 | 47.23 | 52.15 | 49.75 | 65.15 | 0 | 0% |
| ArangoDB | 10 | 197.468 | 48.77 | 59.73 | 50.01 | 63.58 | 0 | 0% |
| ArangoDB | 40 | 0.000 | — | — | — | — | 20123 | **100%** |

`*` Raw observed throughput; 72.99% of operations failed and therefore this should not be interpreted as sustainable successful throughput.

---

# 8. Concurrent Scalability Analysis

## 8.1 Memgraph

Memgraph demonstrated the strongest combination of throughput and reliability.

| Concurrency | QPS | Error Rate |
|---:|---:|---:|
| 1 | 41.93 | 0% |
| 10 | 236.39 | 0% |
| 40 | 251.48 | 0% |

Throughput increased substantially from concurrency 1 to 10 and continued increasing at concurrency 40.

Latency increased under load, but the database continued processing all measured operations successfully.

At concurrency 40:

- Read p50: 120.36 ms
- Read p95: 340.01 ms
- Write p50: 118.34 ms
- Write p95: 397.72 ms
- Errors: 0

This makes Memgraph the strongest **reliable high-concurrency result** in this benchmark.

---

## 8.2 FalkorDB

FalkorDB produced extremely high raw throughput:

| Concurrency | Raw QPS | Error Rate |
|---:|---:|---:|
| 1 | 80.77 | 20.05% |
| 10 | 351.05 | 20.02% |
| 40 | 641.28 | 72.99% |

However, the high failure rate is critical.

At concurrency 40:

- Total operations: 71,430
- Successful operations: 19,291
- Failed operations: 52,139
- Error rate: 72.99%

Therefore, the 641.275 QPS result represents a heavily saturated workload rather than a reliable production throughput level.

The result is still useful because it demonstrates the point at which the system begins rejecting/failing a large proportion of operations.

---

## 8.3 ArangoDB

ArangoDB scaled well through concurrency 10:

| Concurrency | QPS | Error Rate |
|---:|---:|---:|
| 1 | 20.71 | 0% |
| 10 | 197.47 | 0% |
| 40 | 0.00 | 100% |

At concurrency 10, ArangoDB processed:

**5,935 operations with zero errors.**

At concurrency 40:

**20,123 operations were attempted and all failed.**

This indicates a sharp concurrency limit under the tested workload/environment.

---

## 8.4 Neo4j

Neo4j maintained zero failures across all tested concurrency levels.

| Concurrency | QPS | Error Rate |
|---:|---:|---:|
| 1 | 0.957 | 0% |
| 10 | 6.161 | 0% |
| 40 | 7.103 | 0% |

The system remained reliable but showed significant latency growth under concurrency.

At concurrency 40:

- Read p50: 4575.93 ms
- Read p95: 7100.11 ms
- Write p50: 7099.16 ms
- Write p95: 16434.85 ms

The primary observed limitation was therefore latency rather than request failure.

---

## 8.5 CognoDB

CognoDB also maintained zero errors across all concurrency levels.

| Concurrency | QPS | Error Rate |
|---:|---:|---:|
| 1 | 0.972 | 0% |
| 10 | 2.032 | 0% |
| 40 | 3.120 | 0% |

However, latency increased substantially.

At concurrency 40:

- Read p50: 11,119.81 ms
- Read p95: 16,766.81 ms
- Write p50: 11,148.47 ms
- Write p95: 16,717.68 ms

Thus, CognoDB remained functionally reliable but exhibited a strong latency bottleneck under concurrent load.

---

# 9. Ingestion

All databases successfully loaded and verified the same:

- 91,489 nodes
- 200,000 relationships

Measured ingestion results were recorded by the database-specific loaders.

### Memgraph

- Nodes: 91,489
- Relationships: 200,000
- Total load time: 13.311 seconds
- Node throughput: 27,657.73 nodes/sec
- Relationship throughput: 19,996.41 relationships/sec

### FalkorDB

- Nodes: 91,489
- Relationships: 200,000
- Total load time: 13.428 seconds
- Node throughput: 59,908.98 nodes/sec
- Relationship throughput: 16,809.96 relationships/sec

All ingestion runs included a post-load verification step comparing database counts against expected dataset counts.

---

# 10. Overall Performance Ranking

There is no single database that dominates every dimension.

The results instead reveal different strengths.

### Sequential query latency

**1. FalkorDB**

**2. Memgraph**

**3. Neo4j / ArangoDB depending on workload**

**4. CognoDB**

FalkorDB achieved the lowest p50 latency in all six sequential workloads.

---

### Reliable concurrent throughput

Considering only results with zero failed operations:

**1. Memgraph**

**2. ArangoDB**

**3. Neo4j**

**4. CognoDB**

FalkorDB is excluded from this ranking at the tested concurrency levels because its mixed workload produced significant request failures.

---

### Peak raw throughput

FalkorDB produced the highest observed raw throughput:

**641.275 QPS at concurrency 40**

However, the corresponding error rate was:

**72.99%**

Therefore this should be treated as a saturation/failure observation rather than a clean production throughput result.

---

# 11. Latency vs Throughput Trade-off

The benchmark demonstrates why throughput alone is insufficient for evaluating graph databases.

For example:

FalkorDB at concurrency 40:

```text
641.275 QPS
72.99% errors
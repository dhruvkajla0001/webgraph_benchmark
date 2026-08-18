from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
DOCS = ROOT / "docs"
CHARTS = DOCS / "charts"

DATABASES = [
    "cognodb",
    "neo4j",
    "memgraph",
    "falkordb",
    "arangodb",
]


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def find_sequential(database: str):
    path = RESULTS / f"{database}_sequential.json"

    if not path.exists():
        return None

    return load_json(path)


def find_concurrent(database: str):
    path = RESULTS / f"{database}_concurrent_read_write.json"

    if not path.exists():
        return None

    return load_json(path)


def build_sequential():
    rows = []

    for database in DATABASES:

        data = find_sequential(database)

        if not data:
            continue

        for result in data.get("results", []):

            metrics = result.get("metrics", {})

            rows.append(
                {
                    "database": database,
                    "workload": result.get("workload"),
                    "p50_ms": metrics.get("p50_ms"),
                    "p95_ms": metrics.get("p95_ms"),
                    "mean_ms": metrics.get("mean_ms"),
                    "min_ms": metrics.get("min_ms"),
                    "max_ms": metrics.get("max_ms"),
                    "successful_iterations":
                        result.get("successful_iterations"),
                    "failed_iterations":
                        result.get("failed_iterations"),
                }
            )

    return pd.DataFrame(rows)


def build_concurrent():
    rows = []

    for database in DATABASES:

        data = find_concurrent(database)

        if not data:
            continue

        for result in data.get("results", []):

            read_latency = result.get(
                "read_latency_ms",
                {},
            )

            write_latency = result.get(
                "write_latency_ms",
                {},
            )

            rows.append(
                {
                    "database": database,
                    "concurrency":
                        result.get("concurrency"),
                    "throughput_qps":
                        result.get("throughput_qps"),
                    "read_p50_ms":
                        read_latency.get("p50"),
                    "read_p95_ms":
                        read_latency.get("p95"),
                    "write_p50_ms":
                        write_latency.get("p50"),
                    "write_p95_ms":
                        write_latency.get("p95"),
                    "total_operations":
                        result.get("total_operations"),
                    "successful_operations":
                        result.get("successful_operations"),
                    "failed_operations":
                        result.get("failed_operations"),
                    "error_rate":
                        result.get("error_rate"),
                    "retryable_conflicts":
                        result.get("retryable_conflicts"),
                }
            )

    return pd.DataFrame(rows)


def generate_charts(sequential, concurrent):

    CHARTS.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ---------------------------------------------------------
    # Sequential latency
    # ---------------------------------------------------------

    workloads = [
        "point_lookup",
        "filtered_lookup",
        "1_hop",
        "2_hop",
        "3_hop",
        "degree_aggregation",
    ]

    for workload in workloads:

        data = sequential[
            sequential["workload"] == workload
        ]

        if data.empty:
            continue

        plt.figure(figsize=(10, 6))

        plt.bar(
            data["database"],
            data["p50_ms"],
        )

        plt.ylabel("p50 latency (ms)")
        plt.xlabel("Database")
        plt.title(
            f"{workload} - p50 latency"
        )

        plt.xticks(rotation=25)
        plt.tight_layout()

        plt.savefig(
            CHARTS / f"{workload}_p50.png",
            dpi=160,
        )

        plt.close()

    # ---------------------------------------------------------
    # Concurrent throughput
    # ---------------------------------------------------------

    if not concurrent.empty:

        plt.figure(figsize=(10, 6))

        for database in concurrent["database"].unique():

            data = concurrent[
                concurrent["database"] == database
            ].sort_values("concurrency")

            plt.plot(
                data["concurrency"],
                data["throughput_qps"],
                marker="o",
                label=database,
            )

        plt.xlabel("Concurrency")
        plt.ylabel("Throughput (QPS)")
        plt.title(
            "Concurrent read/write throughput"
        )

        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        plt.savefig(
            CHARTS / "concurrent_throughput.png",
            dpi=160,
        )

        plt.close()

        # -----------------------------------------------------
        # Concurrent read p95
        # -----------------------------------------------------

        plt.figure(figsize=(10, 6))

        for database in concurrent["database"].unique():

            data = concurrent[
                concurrent["database"] == database
            ].sort_values("concurrency")

            plt.plot(
                data["concurrency"],
                data["read_p95_ms"],
                marker="o",
                label=database,
            )

        plt.xlabel("Concurrency")
        plt.ylabel("Read p95 latency (ms)")
        plt.title(
            "Concurrent read latency"
        )

        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        plt.savefig(
            CHARTS / "concurrent_read_p95.png",
            dpi=160,
        )

        plt.close()


def build_report(
    sequential,
    concurrent,
):

    DOCS.mkdir(
        parents=True,
        exist_ok=True,
    )

    lines = []

    lines.append(
        "# Graph Database Benchmark Report"
    )

    lines.append("")

    lines.append(
        "## Executive Summary"
    )

    lines.append("")

    lines.append(
        "This benchmark compares CognoDB with "
        "Neo4j, Memgraph, FalkorDB, and ArangoDB "
        "using the same processed graph dataset "
        "and common logical workloads."
    )

    lines.append("")

    lines.append(
        "The benchmark evaluates point lookups, "
        "filtered/indexed lookups, 1-hop, 2-hop, "
        "3-hop traversals, degree aggregation, "
        "data ingestion, and concurrent read/write "
        "behavior."
    )

    lines.append("")

    # ---------------------------------------------------------
    # Sequential table
    # ---------------------------------------------------------

    lines.append(
        "## Sequential Workload Results"
    )

    lines.append("")

    if not sequential.empty:

        table = sequential[
            [
                "database",
                "workload",
                "p50_ms",
                "p95_ms",
                "mean_ms",
                "successful_iterations",
                "failed_iterations",
            ]
        ].copy()

        lines.append(
            table.to_markdown(
                index=False,
            )
        )

    lines.append("")

    # ---------------------------------------------------------
    # Concurrent table
    # ---------------------------------------------------------

    lines.append(
        "## Concurrent Read/Write Results"
    )

    lines.append("")

    if not concurrent.empty:

        table = concurrent[
            [
                "database",
                "concurrency",
                "throughput_qps",
                "read_p50_ms",
                "read_p95_ms",
                "write_p50_ms",
                "write_p95_ms",
                "failed_operations",
                "error_rate",
            ]
        ].copy()

        lines.append(
            table.to_markdown(
                index=False,
            )
        )

    lines.append("")

    lines.append(
        "## Methodology"
    )

    lines.append("")

    lines.append(
        "- Same processed dataset was loaded into every database."
    )

    lines.append(
        "- Sequential workloads used 10 warm-up iterations "
        "and 100 measured iterations."
    )

    lines.append(
        "- Concurrent read/write tests used an 80/20 "
        "read/write mix."
    )

    lines.append(
        "- Concurrency levels were 1, 10, and 40 clients."
    )

    lines.append(
        "- p50 and p95 latency were retained instead "
        "of relying only on averages."
    )

    lines.append("")

    lines.append(
        "## Dataset"
    )

    lines.append("")

    lines.append(
        "- Dataset: SNAP soc-Pokec derived graph"
    )

    lines.append(
        "- Nodes: 91,489"
    )

    lines.append(
        "- Relationships: 200,000"
    )

    lines.append("")

    lines.append(
        "## Important Caveats"
    )

    lines.append("")

    lines.append(
        "The databases were not all running on identical "
        "infrastructure. Local/self-hosted deployments "
        "and managed/free-tier environments therefore "
        "introduce infrastructure differences that must "
        "be considered when interpreting the results."
    )

    lines.append("")

    lines.append(
        "Concurrency failures are reported rather than "
        "removed from the results. In particular, high "
        "concurrency produced substantial failed operations "
        "for some databases. Throughput must therefore be "
        "interpreted together with error rate."
    )

    lines.append("")

    lines.append(
        "## Charts"
    )

    lines.append("")

    lines.append(
        "See `docs/charts/` for generated latency and "
        "concurrency plots."
    )

    lines.append("")

    report_path = DOCS / "BENCHMARK_REPORT.md"

    report_path.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    print(
        f"Report written to: {report_path}"
    )


def main():

    print("=" * 70)
    print("GENERATING FINAL BENCHMARK REPORT")
    print("=" * 70)

    sequential = build_sequential()
    concurrent = build_concurrent()

    DOCS.mkdir(
        parents=True,
        exist_ok=True,
    )

    sequential.to_csv(
        RESULTS / "sequential_summary.csv",
        index=False,
    )

    concurrent.to_csv(
        RESULTS / "concurrent_summary.csv",
        index=False,
    )

    full_results = {
        "sequential": sequential.to_dict(
            orient="records"
        ),
        "concurrent": concurrent.to_dict(
            orient="records"
        ),
    }

    with (
        RESULTS / "full_results.json"
    ).open(
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            full_results,
            f,
            indent=2,
        )

    generate_charts(
        sequential,
        concurrent,
    )

    build_report(
        sequential,
        concurrent,
    )

    print()
    print("=" * 70)
    print("FINAL REPORT GENERATION COMPLETE")
    print("=" * 70)

    print(
        f"Sequential rows: {len(sequential)}"
    )

    print(
        f"Concurrent rows: {len(concurrent)}"
    )

    print(
        f"Charts directory: {CHARTS}"
    )


if __name__ == "__main__":
    main()
from __future__ import annotations

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from benchmarks.falkordb import FalkorDBAdapter
from benchmarks.arangodb import ArangoDBAdapter

from workloads.concurrent_read_write import (
    run_concurrent_read_write,
)

from workloads.node_ids import sample_node_ids


# ============================================================
# Configuration
# ============================================================

CONCURRENCY = 40

READ_RATIO = 0.80

WARMUP_SECONDS = 10

MEASUREMENT_SECONDS = 30

NODE_IDS = sample_node_ids(1000)


# ============================================================
# Helpers
# ============================================================

def run_database(
    database_name,
    adapter_factory,
):
    print()
    print("=" * 70)
    print(
        f"Running {database_name.upper()} "
        f"concurrent read/write: concurrency=40"
    )
    print("=" * 70)

    result = run_concurrent_read_write(
        adapter_factory=adapter_factory,
        node_ids=NODE_IDS,
        concurrency=CONCURRENCY,
        read_ratio=READ_RATIO,
        warmup_seconds=WARMUP_SECONDS,
        measurement_seconds=MEASUREMENT_SECONDS,
    )

    print()
    print(
        f"{database_name.upper()} 40-concurrency result:"
    )

    print(
        f"Throughput: "
        f"{result['throughput_qps']} QPS"
    )

    print(
        f"Read p50: "
        f"{result['read_latency_ms']['p50']} ms"
    )

    print(
        f"Read p95: "
        f"{result['read_latency_ms']['p95']} ms"
    )

    print(
        f"Write p50: "
        f"{result['write_latency_ms']['p50']} ms"
    )

    print(
        f"Write p95: "
        f"{result['write_latency_ms']['p95']} ms"
    )

    print(
        f"Errors: "
        f"{result['failed_operations']}"
    )

    return result


# ============================================================
# Merge helper
# ============================================================

def merge_into_main_json(
    database_name,
    new_result,
):
    results_dir = PROJECT_ROOT / "results"

    results_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    main_file = (
        results_dir
        / f"{database_name}_concurrent_read_write.json"
    )

    # --------------------------------------------------------
    # Load existing results if present
    # --------------------------------------------------------

    if main_file.exists():

        with main_file.open(
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(file)

    else:

        data = {
            "database": database_name,
            "workload": "concurrent_read_write",
            "read_ratio": READ_RATIO,
            "write_ratio": 1.0 - READ_RATIO,
            "warmup_seconds": WARMUP_SECONDS,
            "measurement_seconds": MEASUREMENT_SECONDS,
            "concurrency_levels": [],
            "timestamp_utc": datetime.now(
                timezone.utc
            ).isoformat(),
            "results": [],
        }

    # --------------------------------------------------------
    # Remove existing result for this concurrency
    # --------------------------------------------------------

    existing_results = data.get(
        "results",
        [],
    )

    existing_results = [
        result
        for result in existing_results
        if result.get("concurrency")
        != CONCURRENCY
    ]

    # --------------------------------------------------------
    # Add new result
    # --------------------------------------------------------

    existing_results.append(
        new_result
    )

    # Sort by concurrency
    existing_results.sort(
        key=lambda result: result.get(
            "concurrency",
            0,
        )
    )

    data["results"] = existing_results

    data["concurrency_levels"] = [
        result["concurrency"]
        for result in existing_results
    ]

    data["timestamp_utc"] = (
        datetime.now(
            timezone.utc
        ).isoformat()
    )

    # --------------------------------------------------------
    # Save merged JSON
    # --------------------------------------------------------

    with main_file.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            data,
            file,
            indent=2,
        )

    print()
    print(
        f"Merged into: {main_file}"
    )

    print(
        "Concurrency levels now:",
        data["concurrency_levels"],
    )


# ============================================================
# Main
# ============================================================

def main():

    print()
    print("=" * 70)
    print(
        "RUNNING REMAINING CONCURRENCY=40 BENCHMARKS"
    )
    print("=" * 70)

    print()
    print(
        f"Concurrency: {CONCURRENCY}"
    )

    print(
        f"Read ratio: {READ_RATIO}"
    )

    print(
        f"Warm-up: {WARMUP_SECONDS}s"
    )

    print(
        f"Measurement: {MEASUREMENT_SECONDS}s"
    )

    # ========================================================
    # FalkorDB
    # ========================================================

    falkordb_result = run_database(
        database_name="falkordb",
        adapter_factory=FalkorDBAdapter,
    )

    merge_into_main_json(
        database_name="falkordb",
        new_result=falkordb_result,
    )

    # ========================================================
    # ArangoDB
    # ========================================================

    arangodb_result = run_database(
        database_name="arangodb",
        adapter_factory=ArangoDBAdapter,
    )

    merge_into_main_json(
        database_name="arangodb",
        new_result=arangodb_result,
    )

    # ========================================================
    # Final summary
    # ========================================================

    print()
    print("=" * 70)
    print(
        "FINAL CONCURRENCY=40 SUMMARY"
    )
    print("=" * 70)

    print()

    print("FalkorDB")
    print(
        f"  QPS: "
        f"{falkordb_result['throughput_qps']}"
    )
    print(
        f"  Read p50: "
        f"{falkordb_result['read_latency_ms']['p50']} ms"
    )
    print(
        f"  Write p50: "
        f"{falkordb_result['write_latency_ms']['p50']} ms"
    )
    print(
        f"  Errors: "
        f"{falkordb_result['failed_operations']}"
    )

    print()

    print("ArangoDB")
    print(
        f"  QPS: "
        f"{arangodb_result['throughput_qps']}"
    )
    print(
        f"  Read p50: "
        f"{arangodb_result['read_latency_ms']['p50']} ms"
    )
    print(
        f"  Write p50: "
        f"{arangodb_result['write_latency_ms']['p50']} ms"
    )
    print(
        f"  Errors: "
        f"{arangodb_result['failed_operations']}"
    )

    print()
    print(
        "Both databases have been merged "
        "into their main result JSON files."
    )


if __name__ == "__main__":
    main()
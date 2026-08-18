import sys
import json

from pathlib import Path
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from benchmarks.memgraph import MemgraphAdapter
from workloads.concurrent_read_write import (
    run_concurrency_sweep,
)
from workloads.node_ids import sample_node_ids


def create_adapter():
    return MemgraphAdapter()


def main():

    node_ids = sample_node_ids(1000)

    results = run_concurrency_sweep(

        adapter_factory=create_adapter,

        node_ids=node_ids,

        concurrency_levels=[1, 10, 40],

        read_ratio=0.80,

        warmup_seconds=10,

        measurement_seconds=30,
    )

    # ---------------------------------------------------------
    # Save results
    # ---------------------------------------------------------

    output = {
        "database": "Memgraph",
        "workload": "concurrent_read_write",
        "read_ratio": 0.80,
        "write_ratio": 0.20,
        "warmup_seconds": 10,
        "measurement_seconds": 30,
        "concurrency_levels": [1, 10, 40],
        "timestamp_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "results": results,
    }

    results_dir = PROJECT_ROOT / "results"

    results_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_file = (
        results_dir
        / "Memgraph_concurrent_read_write.json"
    )

    with output_file.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            output,
            file,
            indent=2,
        )

    # ---------------------------------------------------------
    # Print results
    # ---------------------------------------------------------

    print()
    print("=" * 70)
    print("FINAL Memgraph CONCURRENT READ/WRITE RESULTS")
    print("=" * 70)

    for result in results:

        print()
        print(
            f"Concurrency: "
            f"{result['concurrency']}"
        )

        print(
            f"Operations: "
            f"{result['total_operations']}"
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

    print()
    print(
        f"Results saved to: {output_file}"
    )


if __name__ == "__main__":
    main()
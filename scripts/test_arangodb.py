from __future__ import annotations

import sys
import json
import time

from pathlib import Path
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from benchmarks.arangodb import ArangoDBAdapter
from workloads.node_ids import sample_node_ids


WARMUP_ITERATIONS = 10
ITERATIONS = 100


def percentile(values, percentile):
    if not values:
        return 0.0

    values = sorted(values)

    index = (
        (len(values) - 1)
        * percentile
        / 100
    )

    lower = int(index)
    upper = min(
        lower + 1,
        len(values) - 1,
    )

    fraction = index - lower

    return (
        values[lower]
        + (
            values[upper]
            - values[lower]
        )
        * fraction
    )


def calculate_metrics(latencies):
    if not latencies:
        return {
            "count": 0,
            "min_ms": 0.0,
            "mean_ms": 0.0,
            "p50_ms": 0.0,
            "p95_ms": 0.0,
            "max_ms": 0.0,
        }

    return {
        "count": len(latencies),
        "min_ms": min(latencies),
        "mean_ms": (
            sum(latencies)
            / len(latencies)
        ),
        "p50_ms": percentile(
            latencies,
            50,
        ),
        "p95_ms": percentile(
            latencies,
            95,
        ),
        "max_ms": max(latencies),
    }


def run_workload(
    db,
    workload_name,
    node_ids,
):
    """
    Run one ArangoDB-native workload.

    Uses 10 warmups and 100 measured
    iterations, matching the other databases.
    """

    latencies = []
    errors = []

    # ---------------------------------------------------------
    # Select native AQL operation
    # ---------------------------------------------------------

    def execute_workload(node_id):

        if workload_name == "point_lookup":

            return db.point_lookup(
                node_id
            )

        if workload_name == "filtered_lookup":

            return db.filtered_lookup(
                node_id - 1000,
                node_id + 1000,
            )

        if workload_name == "1_hop":

            return db.one_hop(
                node_id
            )

        if workload_name == "2_hop":

            return db.two_hop(
                node_id
            )

        if workload_name == "3_hop":

            return db.three_hop(
                node_id
            )

        if workload_name == "degree_aggregation":

            return db.degree_aggregation()

        raise ValueError(
            f"Unknown workload: "
            f"{workload_name}"
        )

    # ---------------------------------------------------------
    # Warm-up
    # ---------------------------------------------------------

    for i in range(
        WARMUP_ITERATIONS
    ):

        node_id = node_ids[
            i % len(node_ids)
        ]

        try:

            execute_workload(
                node_id
            )

        except Exception:

            # Warmup errors are not included
            # in measured benchmark metrics.
            pass

    # ---------------------------------------------------------
    # Measurement
    # ---------------------------------------------------------

    for i in range(
        ITERATIONS
    ):

        node_id = node_ids[
            i % len(node_ids)
        ]

        start = time.perf_counter()

        try:

            execute_workload(
                node_id
            )

            elapsed = (
                time.perf_counter()
                - start
            )

            latencies.append(
                elapsed * 1000
            )

        except Exception as exc:

            errors.append(
                str(exc)
            )

    metrics = calculate_metrics(
        latencies
    )

    return {
        "workload": workload_name,
        "iterations": ITERATIONS,
        "warmup_iterations": WARMUP_ITERATIONS,
        "successful_iterations": len(
            latencies
        ),
        "failed_iterations": len(
            errors
        ),
        "metrics": metrics,
        "errors": errors[:10],
    }


def main():

    db = ArangoDBAdapter()

    try:

        db.connect()

        # -----------------------------------------------------
        # Verify loaded dataset
        # -----------------------------------------------------

        counts = db.get_counts()

        print(
            f"ArangoDB nodes: "
            f"{counts['nodes']:,}"
        )

        print(
            f"ArangoDB relationships: "
            f"{counts['relationships']:,}"
        )

        if counts["nodes"] != 91489:
            raise RuntimeError(
                "Unexpected ArangoDB node count"
            )

        if (
            counts["relationships"]
            != 200000
        ):
            raise RuntimeError(
                "Unexpected ArangoDB relationship count"
            )

        # -----------------------------------------------------
        # Deterministic node sample
        # -----------------------------------------------------

        node_ids = sample_node_ids(
            100
        )

        workloads = [
            "point_lookup",
            "filtered_lookup",
            "1_hop",
            "2_hop",
            "3_hop",
            "degree_aggregation",
        ]

        results = []

        # -----------------------------------------------------
        # Run workloads
        # -----------------------------------------------------

        for workload_name in workloads:

            print(
                "\n"
                + "=" * 60
            )

            print(
                f"Running ArangoDB workload: "
                f"{workload_name}"
            )

            print(
                "=" * 60
            )

            result = run_workload(
                db=db,
                workload_name=workload_name,
                node_ids=node_ids,
            )

            results.append(
                result
            )

            print(result)

        # -----------------------------------------------------
        # Save results
        # -----------------------------------------------------

        output = {
            "database": "arangodb",
            "benchmark_type": "sequential",
            "warmup_iterations": WARMUP_ITERATIONS,
            "iterations": ITERATIONS,
            "timestamp_utc": datetime.now(
                timezone.utc
            ).isoformat(),
            "results": results,
        }

        results_dir = (
            PROJECT_ROOT / "results"
        )

        results_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_file = (
            results_dir
            / "arangodb_sequential.json"
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

        print()

        print(
            f"Results saved to: "
            f"{output_file}"
        )

    finally:

        db.close()


if __name__ == "__main__":
    main()
from __future__ import annotations

import sys
import json
import random
import threading
import time

from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from benchmarks.arangodb import ArangoDBAdapter
from workloads.concurrent_read_write import percentile
from workloads.node_ids import sample_node_ids


READ_RATIO = 0.80
WARMUP_SECONDS = 10
MEASUREMENT_SECONDS = 30


def execute_read(db, node_id):
    start = time.perf_counter()

    try:
        db.execute(
            """
            FOR n IN Person
                FILTER n.id == @node_id
                RETURN n
            """,
            {"node_id": node_id},
        )

        return (
            "read",
            (time.perf_counter() - start) * 1000,
            True,
            None,
        )

    except Exception as exc:
        return (
            "read",
            (time.perf_counter() - start) * 1000,
            False,
            str(exc),
        )


def execute_write(db, node_id, operation_id):
    start = time.perf_counter()

    try:
        db.execute(
            """
            FOR n IN Person
                FILTER n.id == @node_id
                UPDATE n WITH {
                    benchmark_touch: @operation_id
                } IN Person
            """,
            {
                "node_id": node_id,
                "operation_id": operation_id,
            },
        )

        return (
            "write",
            (time.perf_counter() - start) * 1000,
            True,
            None,
        )

    except Exception as exc:
        return (
            "write",
            (time.perf_counter() - start) * 1000,
            False,
            str(exc),
        )


def worker(
    db,
    node_ids,
    stop_event,
    worker_id,
    read_ratio,
    results,
):
    rng = random.Random(100000 + worker_id)

    operation_id = worker_id * 1_000_000

    while not stop_event.is_set():

        node_id = rng.choice(node_ids)

        if rng.random() < read_ratio:

            result = execute_read(
                db,
                node_id,
            )

        else:

            result = execute_write(
                db,
                node_id,
                operation_id,
            )

        results.append(result)

        operation_id += 1


def run_level(
    node_ids,
    concurrency,
):
    print()
    print("=" * 70)
    print(
        f"Running ArangoDB mixed workload "
        f"with concurrency={concurrency}"
    )
    print("=" * 70)

    adapters = []

    try:

        # -------------------------------------------------------------
        # Create connections
        # -------------------------------------------------------------

        for _ in range(concurrency):

            db = ArangoDBAdapter()
            db.connect()

            adapters.append(db)

        # -------------------------------------------------------------
        # Warm-up
        # -------------------------------------------------------------

        print(
            f"Warm-up: {WARMUP_SECONDS}s"
        )

        warmup_stop = threading.Event()

        with ThreadPoolExecutor(
            max_workers=concurrency
        ) as executor:

            futures = []

            for worker_id in range(concurrency):

                futures.append(
                    executor.submit(
                        worker,
                        adapters[worker_id],
                        node_ids,
                        warmup_stop,
                        worker_id,
                        1.0,
                        [],
                    )
                )

            time.sleep(WARMUP_SECONDS)

            warmup_stop.set()

            for future in as_completed(futures):
                future.result()

        # -------------------------------------------------------------
        # Measurement
        # -------------------------------------------------------------

        print(
            f"Measurement: {MEASUREMENT_SECONDS}s"
        )

        stop_event = threading.Event()

        worker_results = [
            []
            for _ in range(concurrency)
        ]

        start_time = time.perf_counter()

        with ThreadPoolExecutor(
            max_workers=concurrency
        ) as executor:

            futures = []

            for worker_id in range(concurrency):

                futures.append(
                    executor.submit(
                        worker,
                        adapters[worker_id],
                        node_ids,
                        stop_event,
                        worker_id,
                        READ_RATIO,
                        worker_results[worker_id],
                    )
                )

            time.sleep(MEASUREMENT_SECONDS)

            stop_event.set()

            for future in as_completed(futures):
                future.result()

        elapsed = (
            time.perf_counter()
            - start_time
        )

        # -------------------------------------------------------------
        # Flatten results
        # -------------------------------------------------------------

        results = []

        for worker_result in worker_results:
            results.extend(worker_result)

        reads = [
            r for r in results
            if r[0] == "read"
        ]

        writes = [
            r for r in results
            if r[0] == "write"
        ]

        successful_reads = [
            r for r in reads
            if r[2]
        ]

        successful_writes = [
            r for r in writes
            if r[2]
        ]

        failures = [
            r for r in results
            if not r[2]
        ]

        read_latencies = [
            r[1]
            for r in successful_reads
        ]

        write_latencies = [
            r[1]
            for r in successful_writes
        ]

        successful_operations = (
            len(successful_reads)
            + len(successful_writes)
        )

        total_operations = len(results)

        throughput = (
            successful_operations / elapsed
            if elapsed > 0
            else 0.0
        )

        read_qps = (
            len(successful_reads) / elapsed
            if elapsed > 0
            else 0.0
        )

        write_qps = (
            len(successful_writes) / elapsed
            if elapsed > 0
            else 0.0
        )

        result = {
            "workload": "concurrent_read_write",
            "concurrency": concurrency,
            "warmup_seconds": WARMUP_SECONDS,
            "measurement_seconds": MEASUREMENT_SECONDS,
            "read_ratio": READ_RATIO,
            "write_ratio": 1.0 - READ_RATIO,
            "total_operations": total_operations,
            "successful_operations": successful_operations,
            "failed_operations": len(failures),
            "elapsed_seconds": round(
                elapsed,
                3,
            ),
            "throughput_qps": round(
                throughput,
                3,
            ),
            "read_operations": len(reads),
            "write_operations": len(writes),
            "read_qps": round(
                read_qps,
                3,
            ),
            "write_qps": round(
                write_qps,
                3,
            ),
            "read_latency_ms": {
                "p50": round(
                    percentile(
                        read_latencies,
                        50,
                    ),
                    3,
                ),
                "p95": round(
                    percentile(
                        read_latencies,
                        95,
                    ),
                    3,
                ),
            },
            "write_latency_ms": {
                "p50": round(
                    percentile(
                        write_latencies,
                        50,
                    ),
                    3,
                ),
                "p95": round(
                    percentile(
                        write_latencies,
                        95,
                    ),
                    3,
                ),
            },
            "error_rate": round(
                len(failures) / total_operations
                if total_operations
                else 0.0,
                4,
            ),
            "retryable_conflicts": 0,
        }

        print()
        print(
            f"Concurrency: {concurrency}"
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

        return result

    finally:

        for db in adapters:

            try:
                db.close()
            except Exception:
                pass


def main():

    node_ids = sample_node_ids(1000)

    # Start with 1 and 10.
    # We will test 40 separately if these succeed.
    concurrency_levels = [1, 10]

    results = []

    for concurrency in concurrency_levels:

        result = run_level(
            node_ids,
            concurrency,
        )

        results.append(result)

    output = {
        "database": "arangodb",
        "workload": "concurrent_read_write",
        "read_ratio": READ_RATIO,
        "write_ratio": 1.0 - READ_RATIO,
        "warmup_seconds": WARMUP_SECONDS,
        "measurement_seconds": MEASUREMENT_SECONDS,
        "concurrency_levels": concurrency_levels,
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
        / "arangodb_concurrent_read_write.json"
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
    print("=" * 70)
    print(
        "FINAL ARANGODB CONCURRENT READ/WRITE RESULTS"
    )
    print("=" * 70)

    for result in results:

        print()
        print(
            f"Concurrency: "
            f"{result['concurrency']}"
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
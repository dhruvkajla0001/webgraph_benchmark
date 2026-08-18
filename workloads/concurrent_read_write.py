from __future__ import annotations

import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any, Callable


DEFAULT_READ_RATIO = 0.80
DEFAULT_CONCURRENCIES = [1, 10, 40]

DEFAULT_WARMUP_SECONDS = 10
DEFAULT_MEASUREMENT_SECONDS = 30


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------

@dataclass
class OperationResult:
    operation_type: str
    latency_ms: float
    success: bool
    error: str | None = None


# ---------------------------------------------------------------------------
# Percentile
# ---------------------------------------------------------------------------

def percentile(
    values: list[float],
    percentile_value: float,
) -> float:

    if not values:
        return 0.0

    values = sorted(values)

    if len(values) == 1:
        return values[0]

    rank = (percentile_value / 100) * (len(values) - 1)

    lower = int(rank)
    upper = min(lower + 1, len(values) - 1)

    weight = rank - lower

    return (
        values[lower]
        + (values[upper] - values[lower]) * weight
    )


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------

def execute_read(
    adapter: Any,
    node_id: int,
) -> OperationResult:

    query = """
    MATCH (n)
    WHERE n.id = $node_id
    RETURN n
    """

    start = time.perf_counter()

    try:

        adapter.execute(
            query,
            {"node_id": node_id},
        )

        latency_ms = (
            time.perf_counter() - start
        ) * 1000

        return OperationResult(
            operation_type="read",
            latency_ms=latency_ms,
            success=True,
        )

    except Exception as exc:

        latency_ms = (
            time.perf_counter() - start
        ) * 1000

        return OperationResult(
            operation_type="read",
            latency_ms=latency_ms,
            success=False,
            error=str(exc),
        )


# ---------------------------------------------------------------------------
# Write
# ---------------------------------------------------------------------------

def execute_write(
    adapter: Any,
    node_id: int,
    operation_id: int,
) -> OperationResult:

    query = """
    MATCH (n)
    WHERE n.id = $node_id
    SET n.benchmark_touch = $operation_id
    RETURN n.id
    """

    start = time.perf_counter()

    try:

        adapter.execute(
            query,
            {
                "node_id": node_id,
                "operation_id": operation_id,
            },
        )

        latency_ms = (
            time.perf_counter() - start
        ) * 1000

        return OperationResult(
            operation_type="write",
            latency_ms=latency_ms,
            success=True,
        )

    except Exception as exc:

        latency_ms = (
            time.perf_counter() - start
        ) * 1000

        return OperationResult(
            operation_type="write",
            latency_ms=latency_ms,
            success=False,
            error=str(exc),
        )


# ---------------------------------------------------------------------------
# Warm-up
# ---------------------------------------------------------------------------

def warmup_worker(
    adapter: Any,
    node_ids: list[int],
    stop_event: threading.Event,
    worker_id: int,
) -> None:

    rng = random.Random(
        50_000 + worker_id
    )

    operation_id = worker_id * 1_000_000

    while not stop_event.is_set():

        node_id = rng.choice(node_ids)

        # Warm-up uses reads only.
        execute_read(
            adapter,
            node_id,
        )

        operation_id += 1


# ---------------------------------------------------------------------------
# Measurement worker
# ---------------------------------------------------------------------------

def measurement_worker(
    adapter: Any,
    node_ids: list[int],
    stop_event: threading.Event,
    worker_id: int,
    read_ratio: float,
) -> list[OperationResult]:

    rng = random.Random(
        100_000 + worker_id
    )

    results: list[OperationResult] = []

    operation_id = worker_id * 1_000_000

    while not stop_event.is_set():

        node_id = rng.choice(node_ids)

        if rng.random() < read_ratio:

            result = execute_read(
                adapter,
                node_id,
            )

        else:

            result = execute_write(
                adapter,
                node_id,
                operation_id,
            )

        results.append(result)

        operation_id += 1

    return results


# ---------------------------------------------------------------------------
# Main benchmark
# ---------------------------------------------------------------------------

def run_concurrent_read_write(
    adapter_factory: Callable[[], Any],
    node_ids: list[int],
    concurrency: int = 10,
    read_ratio: float = DEFAULT_READ_RATIO,
    warmup_seconds: int = DEFAULT_WARMUP_SECONDS,
    measurement_seconds: int = DEFAULT_MEASUREMENT_SECONDS,
) -> dict[str, Any]:

    if not node_ids:
        raise ValueError(
            "node_ids cannot be empty"
        )

    if concurrency <= 0:
        raise ValueError(
            "concurrency must be greater than zero"
        )

    if not 0 <= read_ratio <= 1:
        raise ValueError(
            "read_ratio must be between 0 and 1"
        )

    adapters: list[Any] = []

    # -----------------------------------------------------------------------
    # Create one adapter per concurrent client.
    # -----------------------------------------------------------------------

    for _ in range(concurrency):

        adapter = adapter_factory()

        adapter.connect()

        adapters.append(adapter)

    try:

        # ================================================================
        # WARM-UP
        # ================================================================

        print(
            f"Warm-up: {warmup_seconds}s"
        )

        warmup_stop = threading.Event()

        with ThreadPoolExecutor(
            max_workers=concurrency
        ) as executor:

            warmup_futures = []

            for worker_id in range(concurrency):

                future = executor.submit(
                    warmup_worker,
                    adapters[worker_id],
                    node_ids,
                    warmup_stop,
                    worker_id,
                )

                warmup_futures.append(future)

            time.sleep(warmup_seconds)

            warmup_stop.set()

            for future in as_completed(
                warmup_futures
            ):

                future.result()

        # ================================================================
        # MEASUREMENT
        # ================================================================

        print(
            f"Measurement: {measurement_seconds}s"
        )

        measurement_stop = threading.Event()

        start_time = time.perf_counter()

        with ThreadPoolExecutor(
            max_workers=concurrency
        ) as executor:

            futures = []

            for worker_id in range(concurrency):

                future = executor.submit(
                    measurement_worker,
                    adapters[worker_id],
                    node_ids,
                    measurement_stop,
                    worker_id,
                    read_ratio,
                )

                futures.append(future)

            time.sleep(measurement_seconds)

            measurement_stop.set()

            all_results: list[OperationResult] = []

            for future in as_completed(futures):

                worker_results = future.result()

                all_results.extend(
                    worker_results
                )

        elapsed_seconds = (
            time.perf_counter() - start_time
        )

    finally:

        # ================================================================
        # CLOSE CONNECTIONS
        # ================================================================

        for adapter in adapters:

            try:
                adapter.close()

            except Exception:
                pass

    # -----------------------------------------------------------------------
    # Split operations.
    # -----------------------------------------------------------------------

    reads = [
        r
        for r in all_results
        if r.operation_type == "read"
    ]

    writes = [
        r
        for r in all_results
        if r.operation_type == "write"
    ]

    successful_reads = [
        r
        for r in reads
        if r.success
    ]

    successful_writes = [
        r
        for r in writes
        if r.success
    ]

    failures = [
        r
        for r in all_results
        if not r.success
    ]

    read_latencies = [
        r.latency_ms
        for r in successful_reads
    ]

    write_latencies = [
        r.latency_ms
        for r in successful_writes
    ]

    successful_count = (
        len(successful_reads)
        + len(successful_writes)
    )

    total_count = len(all_results)

    # -----------------------------------------------------------------------
    # Throughput.
    # -----------------------------------------------------------------------

    throughput_qps = (
        successful_count / elapsed_seconds
        if elapsed_seconds > 0
        else 0.0
    )

    read_qps = (
        len(successful_reads) / elapsed_seconds
        if elapsed_seconds > 0
        else 0.0
    )

    write_qps = (
        len(successful_writes) / elapsed_seconds
        if elapsed_seconds > 0
        else 0.0
    )

    # -----------------------------------------------------------------------
    # Retry detection.
    #
    # CognoDB reports retryable transaction conflicts through exceptions/logs.
    # We count recognizable conflict messages from failed operations here.
    # Successful automatic driver retries remain successful operations.
    # -----------------------------------------------------------------------

    retryable_conflicts = 0

    for result in failures:

        if not result.error:
            continue

        error_text = result.error.lower()

        if (
            "transaction conflict" in error_text
            or "retryable" in error_text
            or "concurrent" in error_text
        ):
            retryable_conflicts += 1

    # -----------------------------------------------------------------------
    # Result.
    # -----------------------------------------------------------------------

    return {

        "workload": "concurrent_read_write",

        "concurrency": concurrency,

        "warmup_seconds": warmup_seconds,

        "measurement_seconds": measurement_seconds,

        "read_ratio": read_ratio,

        "write_ratio": 1.0 - read_ratio,

        "total_operations": total_count,

        "successful_operations": successful_count,

        "failed_operations": len(failures),

        "elapsed_seconds": round(
            elapsed_seconds,
            3,
        ),

        "throughput_qps": round(
            throughput_qps,
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
            len(failures) / total_count
            if total_count
            else 0.0,
            4,
        ),

        "retryable_conflicts": retryable_conflicts,
    }


# ---------------------------------------------------------------------------
# Concurrency sweep
# ---------------------------------------------------------------------------

def run_concurrency_sweep(
    adapter_factory: Callable[[], Any],
    node_ids: list[int],
    concurrency_levels: list[int] | None = None,
    read_ratio: float = DEFAULT_READ_RATIO,
    warmup_seconds: int = DEFAULT_WARMUP_SECONDS,
    measurement_seconds: int = DEFAULT_MEASUREMENT_SECONDS,
) -> list[dict[str, Any]]:

    if concurrency_levels is None:
        concurrency_levels = DEFAULT_CONCURRENCIES

    results = []

    for concurrency in concurrency_levels:

        print()
        print("=" * 70)
        print(
            f"Running mixed workload "
            f"with concurrency={concurrency}"
        )
        print("=" * 70)

        result = run_concurrent_read_write(

            adapter_factory=adapter_factory,

            node_ids=node_ids,

            concurrency=concurrency,

            read_ratio=read_ratio,

            warmup_seconds=warmup_seconds,

            measurement_seconds=measurement_seconds,
        )

        results.append(result)

        print()
        print(
            f"Concurrency: {concurrency}"
        )

        print(
            f"QPS: {result['throughput_qps']}"
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

        print(
            f"Retryable conflicts: "
            f"{result['retryable_conflicts']}"
        )

    return results
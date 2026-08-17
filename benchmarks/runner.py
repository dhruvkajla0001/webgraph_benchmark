"""
Generic benchmark runner.

The runner is database-agnostic.
Each database adapter provides an executor function:

    executor(query, parameters)

The runner handles:
- warm-up
- measured iterations
- latency measurement
- errors
- p50/p95 statistics
- workload-specific parameters
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional

from benchmarks.metrics import calculate_latency_metrics
from workloads.registry import WORKLOAD_REGISTRY
from workloads.node_ids import sample_node_ids


QueryExecutor = Callable[[str, Dict[str, Any]], Any]


@dataclass
class BenchmarkResult:
    """Result for a single workload."""

    workload: str
    iterations: int
    warmup_iterations: int
    successful_iterations: int
    failed_iterations: int
    metrics: Dict[str, Any]
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "workload": self.workload,
            "iterations": self.iterations,
            "warmup_iterations": self.warmup_iterations,
            "successful_iterations": self.successful_iterations,
            "failed_iterations": self.failed_iterations,
            "metrics": self.metrics,
            "errors": self.errors,
        }


class BenchmarkRunner:
    """
    Runs registered Cypher workloads against a database executor.
    """

    def __init__(
        self,
        executor: QueryExecutor,
        warmup_iterations: int = 10,
        iterations: int = 100,
    ):
        if warmup_iterations < 0:
            raise ValueError(
                "warmup_iterations cannot be negative."
            )

        if iterations <= 0:
            raise ValueError(
                "iterations must be greater than zero."
            )

        self.executor = executor
        self.warmup_iterations = warmup_iterations
        self.iterations = iterations

    def run_workload(
        self,
        workload_name: str,
        node_ids: Optional[list[int]] = None,
    ) -> BenchmarkResult:
        """
        Execute one registered workload.
        """

        if workload_name not in WORKLOAD_REGISTRY:
            raise ValueError(
                f"Unknown workload '{workload_name}'. "
                f"Available workloads: "
                f"{list(WORKLOAD_REGISTRY.keys())}"
            )

        query = WORKLOAD_REGISTRY[workload_name]

        # ---------------------------------------------------------
        # Workload parameter requirements
        # ---------------------------------------------------------

        requires_node_id = workload_name in {
            "1_hop",
            "2_hop",
            "3_hop",
            "point_lookup",
        }

        requires_filtered_lookup = (
            workload_name == "filtered_lookup"
        )

        # ---------------------------------------------------------
        # Prepare node IDs for traversal / point lookup workloads
        # ---------------------------------------------------------

        if requires_node_id:
            required_samples = (
                self.warmup_iterations
                + self.iterations
            )

            if node_ids is None:
                node_ids = sample_node_ids(
                    required_samples
                )

            if len(node_ids) < required_samples:
                raise ValueError(
                    "Not enough node_ids supplied for "
                    "the requested warm-up and measured "
                    "iterations."
                )

        latencies_ms: list[float] = []
        errors: list[str] = []

        # ---------------------------------------------------------
        # Warm-up
        # ---------------------------------------------------------

        for i in range(
            self.warmup_iterations
        ):
            parameters: Dict[str, Any] = {}

            if requires_node_id:
                parameters["node_id"] = node_ids[i]

            if requires_filtered_lookup:
                parameters["min_id"] = 1000
                parameters["max_id"] = 2000

            try:
                self.executor(
                    query,
                    parameters,
                )

            except Exception:
                # Warm-up failures are intentionally ignored.
                # Measurement failures are recorded below.
                continue

        # ---------------------------------------------------------
        # Measured iterations
        # ---------------------------------------------------------

        successful = 0
        failed = 0

        for i in range(
            self.iterations
        ):
            parameters: Dict[str, Any] = {}

            if requires_node_id:
                parameters["node_id"] = node_ids[
                    self.warmup_iterations + i
                ]

            if requires_filtered_lookup:
                parameters["min_id"] = 1000
                parameters["max_id"] = 2000

            start = time.perf_counter()

            try:
                self.executor(
                    query,
                    parameters,
                )

                elapsed_ms = (
                    time.perf_counter()
                    - start
                ) * 1000

                latencies_ms.append(
                    elapsed_ms
                )

                successful += 1

            except Exception as exc:
                failed += 1

                errors.append(
                    f"iteration={i}: "
                    f"{type(exc).__name__}: "
                    f"{exc}"
                )

        # ---------------------------------------------------------
        # Metrics
        # ---------------------------------------------------------

        latency_metrics = (
            calculate_latency_metrics(
                latencies_ms
            )
        )

        return BenchmarkResult(
            workload=workload_name,
            iterations=self.iterations,
            warmup_iterations=(
                self.warmup_iterations
            ),
            successful_iterations=successful,
            failed_iterations=failed,
            metrics=(
                latency_metrics.to_dict()
            ),
            errors=errors,
        )

    def run_all(
        self,
        node_ids: Optional[list[int]] = None,
    ) -> list[BenchmarkResult]:
        """
        Run every registered workload.
        """

        results = []

        for workload_name in WORKLOAD_REGISTRY:
            result = self.run_workload(
                workload_name=workload_name,
                node_ids=node_ids,
            )

            results.append(result)

        return results
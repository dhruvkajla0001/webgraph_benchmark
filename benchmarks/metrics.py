from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from typing import Iterable, Optional


@dataclass
class LatencyMetrics:
    """
    Statistical summary for a latency-based workload.

    Latencies are stored in milliseconds.
    """

    samples_ms: list[float] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.samples_ms)

    @property
    def min_ms(self) -> Optional[float]:
        if not self.samples_ms:
            return None
        return min(self.samples_ms)

    @property
    def max_ms(self) -> Optional[float]:
        if not self.samples_ms:
            return None
        return max(self.samples_ms)

    @property
    def mean_ms(self) -> Optional[float]:
        if not self.samples_ms:
            return None
        return statistics.mean(self.samples_ms)

    @property
    def p50_ms(self) -> Optional[float]:
        return self._percentile(50)

    @property
    def p95_ms(self) -> Optional[float]:
        return self._percentile(95)

    def _percentile(self, percentile: float) -> Optional[float]:
        if not self.samples_ms:
            return None

        sorted_samples = sorted(self.samples_ms)

        if len(sorted_samples) == 1:
            return sorted_samples[0]

        rank = (percentile / 100) * (len(sorted_samples) - 1)

        lower = int(rank)
        upper = lower + 1

        if upper >= len(sorted_samples):
            return sorted_samples[lower]

        weight = rank - lower

        return (
            sorted_samples[lower]
            + weight * (sorted_samples[upper] - sorted_samples[lower])
        )

    def to_dict(self) -> dict:
        return {
            "count": self.count,
            "min_ms": self.min_ms,
            "mean_ms": self.mean_ms,
            "p50_ms": self.p50_ms,
            "p95_ms": self.p95_ms,
            "max_ms": self.max_ms,
        }


@dataclass
class ThroughputMetrics:
    """
    Metrics for data loading or sustained workloads.
    """

    total_items: int
    elapsed_seconds: float

    @property
    def items_per_second(self) -> float:
        if self.elapsed_seconds <= 0:
            return 0.0

        return self.total_items / self.elapsed_seconds

    def to_dict(self) -> dict:
        return {
            "total_items": self.total_items,
            "elapsed_seconds": self.elapsed_seconds,
            "items_per_second": self.items_per_second,
        }


@dataclass
class BenchmarkMetrics:
    """
    Combined metrics for a single benchmark workload.
    """

    workload: str
    latency: Optional[LatencyMetrics] = None
    throughput: Optional[ThroughputMetrics] = None
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        result = {
            "workload": self.workload,
            **self.metadata,
        }

        if self.latency is not None:
            result["latency"] = self.latency.to_dict()

        if self.throughput is not None:
            result["throughput"] = self.throughput.to_dict()

        return result


def calculate_latency_metrics(
    samples_ms: Iterable[float],
) -> LatencyMetrics:
    """
    Create latency statistics from measured samples.

    Parameters
    ----------
    samples_ms:
        Iterable of latency measurements in milliseconds.

    Returns
    -------
    LatencyMetrics
        p50, p95 and other latency statistics.
    """

    samples = [
        float(sample)
        for sample in samples_ms
        if sample >= 0
    ]

    return LatencyMetrics(samples_ms=samples)


def calculate_throughput(
    total_items: int,
    elapsed_seconds: float,
) -> ThroughputMetrics:
    """
    Calculate items processed per second.
    """

    if total_items < 0:
        raise ValueError("total_items cannot be negative.")

    if elapsed_seconds < 0:
        raise ValueError("elapsed_seconds cannot be negative.")

    return ThroughputMetrics(
        total_items=total_items,
        elapsed_seconds=elapsed_seconds,
    )


def percentile(
    samples_ms: Iterable[float],
    percentile_value: float,
) -> Optional[float]:
    """
    Generic percentile helper.

    Example:
        percentile([1, 2, 3, 4, 5], 95)
    """

    if not 0 <= percentile_value <= 100:
        raise ValueError("percentile must be between 0 and 100.")

    metrics = LatencyMetrics(
        samples_ms=[
            float(sample)
            for sample in samples_ms
            if sample >= 0
        ]
    )

    return metrics._percentile(percentile_value)
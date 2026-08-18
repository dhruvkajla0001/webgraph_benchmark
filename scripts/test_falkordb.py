import sys
import json

from pathlib import Path
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from benchmarks.falkordb import FalkorDBAdapter
from benchmarks.runner import BenchmarkRunner


def main():

    db = FalkorDBAdapter()

    try:

        db.connect()

        runner = BenchmarkRunner(
            executor=db.execute,
            warmup_iterations=10,
            iterations=100,
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

        for workload_name in workloads:

            print("\n" + "=" * 60)
            print(
                f"Running FalkorDB workload: "
                f"{workload_name}"
            )
            print("=" * 60)

            result = runner.run_workload(
                workload_name
            )

            result_dict = result.to_dict()

            results.append(result_dict)

            print(result_dict)

        output = {
            "database": "falkordb",
            "benchmark_type": "sequential",
            "warmup_iterations": 10,
            "iterations": 100,
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
            / "falkordb_sequential.json"
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
            f"Results saved to: {output_file}"
        )

    finally:

        db.close()


if __name__ == "__main__":
    main()
from benchmarks.cognodb import CognoDBAdapter
from benchmarks.runner import BenchmarkRunner


def main():
    db = CognoDBAdapter()

    try:
        db.connect()

        runner = BenchmarkRunner(
            executor=db.execute,
            warmup_iterations=2,
            iterations=5,
        )

        workloads = [
            "point_lookup",
            "filtered_lookup",
            "1_hop",
            "2_hop",
            "3_hop",
            "degree_aggregation",
        ]

        for workload_name in workloads:
            print("\n" + "=" * 60)
            print(
                f"Running CognoDB workload: "
                f"{workload_name}"
            )
            print("=" * 60)

            result = runner.run_workload(
                workload_name
            )

            print(result.to_dict())

    finally:
        db.close()


if __name__ == "__main__":
    main()
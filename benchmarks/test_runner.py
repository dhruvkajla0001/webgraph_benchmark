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

        result = runner.run_workload("point_lookup")

        print(result.to_dict())

    finally:
        db.close()


if __name__ == "__main__":
    main()
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

RESULTS_DIR = PROJECT_ROOT / "results"

FILES = {
    "CognoDB": RESULTS_DIR / "cognodb_concurrent_read_write.json",
    "Neo4j": RESULTS_DIR / "neo4j_concurrent_read_write.json",
}


def load_results(database, file_path):
    if not file_path.exists():
        raise FileNotFoundError(
            f"{database} result file not found: {file_path}"
        )

    with file_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    return data["results"]


def main():

    all_results = {}

    # ---------------------------------------------------------
    # Load both databases
    # ---------------------------------------------------------

    for database, file_path in FILES.items():

        all_results[database] = load_results(
            database,
            file_path,
        )

    # ---------------------------------------------------------
    # Print comparison
    # ---------------------------------------------------------

    print()
    print("=" * 110)
    print("CONCURRENT READ/WRITE COMPARISON")
    print("=" * 110)

    print(
        f"{'Database':<12}"
        f"{'Clients':>10}"
        f"{'QPS':>12}"
        f"{'Read p50':>14}"
        f"{'Read p95':>14}"
        f"{'Write p50':>15}"
        f"{'Write p95':>15}"
        f"{'Errors':>10}"
    )

    print("-" * 110)

    for database, results in all_results.items():

        for result in results:

            print(
                f"{database:<12}"
                f"{result['concurrency']:>10}"
                f"{result['throughput_qps']:>12.3f}"
                f"{result['read_latency_ms']['p50']:>14.3f}"
                f"{result['read_latency_ms']['p95']:>14.3f}"
                f"{result['write_latency_ms']['p50']:>15.3f}"
                f"{result['write_latency_ms']['p95']:>15.3f}"
                f"{result['failed_operations']:>10}"
            )

    print("-" * 110)

    # ---------------------------------------------------------
    # Save comparison JSON
    # ---------------------------------------------------------

    comparison = {
        "workload": "concurrent_read_write",
        "databases": {},
    }

    for database, results in all_results.items():

        comparison["databases"][database] = results

    output_file = (
        RESULTS_DIR
        / "concurrent_read_write_comparison.json"
    )

    with output_file.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            comparison,
            file,
            indent=2,
        )

    print()
    print(
        f"Comparison saved to: {output_file}"
    )


if __name__ == "__main__":
    main()
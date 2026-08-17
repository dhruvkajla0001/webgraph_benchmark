from pathlib import Path
import csv


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

RAW_FILE = Path(
    r"D:\webgraph_benchmark\data\raw\soc-pokec-relationships.txt"
)

OUTPUT_DIR = Path(
    r"D:\webgraph_benchmark\data\processed"
)

TARGET_EDGES = 200_000


# ---------------------------------------------------------
# Dataset preparation
# ---------------------------------------------------------

def prepare_dataset():
    if not RAW_FILE.exists():
        raise FileNotFoundError(
            f"Dataset not found:\n{RAW_FILE}"
        )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    nodes = set()
    relationships = []

    print("=" * 60)
    print("Pokec Dataset Preparation")
    print("=" * 60)

    print(f"Input file:")
    print(RAW_FILE)

    print(f"\nTarget relationships: {TARGET_EDGES:,}")

    # -----------------------------------------------------
    # Read raw dataset
    # -----------------------------------------------------

    with RAW_FILE.open(
        "r",
        encoding="utf-8",
        errors="ignore"
    ) as file:

        for line_number, line in enumerate(file, start=1):

            line = line.strip()

            # Skip empty lines
            if not line:
                continue

            # Skip SNAP comments
            if line.startswith("#"):
                continue

            parts = line.split()

            # We expect:
            # source target
            if len(parts) < 2:
                continue

            try:
                source = int(parts[0])
                target = int(parts[1])
            except ValueError:
                continue

            relationships.append(
                (source, target)
            )

            nodes.add(source)
            nodes.add(target)

            # Stop once we have enough relationships
            if len(relationships) >= TARGET_EDGES:
                break

    # -----------------------------------------------------
    # Validate
    # -----------------------------------------------------

    if not relationships:
        raise RuntimeError(
            "No relationships were found in the dataset."
        )

    print("\nDataset read successfully.")

    print(
        f"Relationships selected : "
        f"{len(relationships):,}"
    )

    print(
        f"Unique nodes            : "
        f"{len(nodes):,}"
    )

    # -----------------------------------------------------
    # Write nodes.csv
    # -----------------------------------------------------

    nodes_file = OUTPUT_DIR / "nodes.csv"

    with nodes_file.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        writer.writerow(
            ["node_id"]
        )

        for node_id in sorted(nodes):

            writer.writerow(
                [node_id]
            )

    # -----------------------------------------------------
    # Write relationships.csv
    # -----------------------------------------------------

    relationships_file = (
        OUTPUT_DIR / "relationships.csv"
    )

    with relationships_file.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        writer.writerow(
            ["source", "target"]
        )

        for source, target in relationships:

            writer.writerow(
                [source, target]
            )

    # -----------------------------------------------------
    # Final information
    # -----------------------------------------------------

    print("\n" + "=" * 60)
    print("Dataset preparation complete!")
    print("=" * 60)

    print(
        f"\nNodes file:\n"
        f"{nodes_file}"
    )

    print(
        f"\nRelationships file:\n"
        f"{relationships_file}"
    )

    print("\nDataset summary:")
    print(
        f"Nodes         : {len(nodes):,}"
    )
    print(
        f"Relationships : {len(relationships):,}"
    )


# ---------------------------------------------------------
# Entry point
# ---------------------------------------------------------

if __name__ == "__main__":
    prepare_dataset()
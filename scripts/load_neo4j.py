from __future__ import annotations

import csv
import time
from pathlib import Path
from typing import Iterator

from benchmarks.neo4j import Neo4jAdapter


PROJECT_ROOT = (
    Path(__file__).resolve().parent.parent
)

NODES_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "nodes.csv"
)

RELATIONSHIPS_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "relationships.csv"
)

BATCH_SIZE = 5000


def read_nodes() -> Iterator[dict]:
    """Read nodes from the processed CSV."""

    with NODES_FILE.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:
            yield {
                "id": int(row["node_id"]),
            }


def read_relationships() -> Iterator[dict]:
    """Read relationships from the processed CSV."""

    with RELATIONSHIPS_FILE.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:
            yield {
                "source": int(row["source"]),
                "target": int(row["target"]),
            }


def batches(
    rows: Iterator[dict],
    batch_size: int,
) -> Iterator[list[dict]]:
    """Yield rows in fixed-size batches."""

    batch = []

    for row in rows:

        batch.append(row)

        if len(batch) >= batch_size:
            yield batch
            batch = []

    if batch:
        yield batch


def clear_database(
    db: Neo4jAdapter,
) -> None:
    """Remove existing graph data."""

    print("Clearing existing graph...")

    db.execute(
        """
        MATCH (n)
        DETACH DELETE n
        """
    )

    print("Existing graph cleared")


def load_nodes(
    db: Neo4jAdapter,
) -> tuple[int, float]:
    """Load all Person nodes."""

    query = """
    UNWIND $rows AS row
    CREATE (:Person {id: row.id})
    """

    total = 0

    start = time.perf_counter()

    for batch in batches(
        read_nodes(),
        BATCH_SIZE,
    ):

        db.execute(
            query,
            {"rows": batch},
        )

        total += len(batch)

        print(
            f"\rNodes loaded: {total:,}",
            end="",
            flush=True,
        )

    elapsed = (
        time.perf_counter() - start
    )

    print()

    return total, elapsed


def load_relationships(
    db: Neo4jAdapter,
) -> tuple[int, float]:
    """Load all KNOWS relationships."""

    query = """
    UNWIND $rows AS row

    MATCH (
        source:Person
        {id: row.source}
    )

    MATCH (
        target:Person
        {id: row.target}
    )

    CREATE (
        source
    )-[:KNOWS]->(
        target
    )
    """

    total = 0

    start = time.perf_counter()

    for batch in batches(
        read_relationships(),
        BATCH_SIZE,
    ):

        db.execute(
            query,
            {"rows": batch},
        )

        total += len(batch)

        print(
            f"\rRelationships loaded: {total:,}",
            end="",
            flush=True,
        )

    elapsed = (
        time.perf_counter() - start
    )

    print()

    return total, elapsed


def print_metrics(
    node_count: int,
    node_time: float,
    relationship_count: int,
    relationship_time: float,
    total_time: float,
) -> None:
    """Print ingestion benchmark metrics."""

    node_rate = (
        node_count / node_time
        if node_time > 0
        else 0
    )

    relationship_rate = (
        relationship_count
        / relationship_time
        if relationship_time > 0
        else 0
    )

    print(
        "\n" + "=" * 60
    )

    print(
        "Neo4j INGESTION RESULTS"
    )

    print(
        "=" * 60
    )

    print(
        f"Nodes loaded:              "
        f"{node_count:,}"
    )

    print(
        f"Node load time:            "
        f"{node_time:.3f} sec"
    )

    print(
        f"Node throughput:           "
        f"{node_rate:,.2f} nodes/sec"
    )

    print()

    print(
        f"Relationships loaded:      "
        f"{relationship_count:,}"
    )

    print(
        f"Relationship load time:    "
        f"{relationship_time:.3f} sec"
    )

    print(
        f"Relationship throughput:   "
        f"{relationship_rate:,.2f} "
        f"relationships/sec"
    )

    print()

    print(
        f"Total load time:            "
        f"{total_time:.3f} sec"
    )

    print(
        "=" * 60
    )


def main() -> None:
    """Run the complete Neo4j ingestion benchmark."""

    if not NODES_FILE.exists():

        raise FileNotFoundError(
            f"Nodes file not found: "
            f"{NODES_FILE}"
        )

    if not RELATIONSHIPS_FILE.exists():

        raise FileNotFoundError(
            f"Relationships file not found: "
            f"{RELATIONSHIPS_FILE}"
        )

    db = Neo4jAdapter()

    try:

        db.connect()

        db.create_schema()

        clear_database(db)

        total_start = (
            time.perf_counter()
        )

        print(
            "\nLoading nodes..."
        )

        node_count, node_time = (
            load_nodes(db)
        )

        print(
            "\nLoading relationships..."
        )

        (
            relationship_count,
            relationship_time,
        ) = load_relationships(db)

        total_time = (
            time.perf_counter()
            - total_start
        )

        print_metrics(
            node_count=node_count,
            node_time=node_time,
            relationship_count=relationship_count,
            relationship_time=relationship_time,
            total_time=total_time,
        )

        print(
            "\nVerifying database counts..."
        )

        counts = db.get_counts()

        print(
            f"Neo4j nodes:          "
            f"{counts['nodes']:,}"
        )

        print(
            f"Neo4j relationships:  "
            f"{counts['relationships']:,}"
        )

        if counts["nodes"] != node_count:

            raise RuntimeError(
                "Node count mismatch!"
            )

        if (
            counts["relationships"]
            != relationship_count
        ):

            raise RuntimeError(
                "Relationship count mismatch!"
            )

        print(
            "\nDataset loaded and verified "
            "successfully."
        )

    finally:

        db.close()


if __name__ == "__main__":
    main()
import csv
import random
from pathlib import Path


NODES_FILE = Path(
    "data/processed/nodes.csv"
)


def load_node_ids():
    node_ids = []

    with NODES_FILE.open(
        "r",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:
            node_ids.append(
                int(row["node_id"])
            )

    return node_ids


def sample_node_ids(count=100, seed=42):
    node_ids = load_node_ids()

    if count > len(node_ids):
        raise ValueError(
            "Requested more nodes than available."
        )

    random.seed(seed)

    return random.sample(
        node_ids,
        count
    )
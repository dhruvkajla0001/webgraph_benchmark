from __future__ import annotations

import os

from dotenv import load_dotenv
from neo4j import GraphDatabase


load_dotenv()


class MemgraphAdapter:
    """
    Connection and loading adapter for Memgraph.

    Memgraph exposes a Bolt-compatible interface and
    supports openCypher. The Neo4j Python driver is
    used for Bolt communication.
    """

    def __init__(self):
        self.uri = os.getenv(
            "MEMGRAPH_URI",
            "bolt://localhost:7687",
        )

        self.username = os.getenv(
            "MEMGRAPH_USERNAME",
            "",
        )

        self.password = os.getenv(
            "MEMGRAPH_PASSWORD",
            "",
        )

        if not self.uri:
            raise RuntimeError(
                "MEMGRAPH_URI is missing"
            )

        self.driver = GraphDatabase.driver(
            self.uri,
            auth=(
                self.username,
                self.password,
            ),
        )

    def connect(self):
        """Verify Memgraph connectivity."""

        self.driver.verify_connectivity()

        print(
            "Memgraph connection successful"
        )

    def close(self):
        """Close the driver."""

        self.driver.close()

    def execute(
        self,
        query,
        parameters=None,
    ):
        """Execute a normal openCypher query."""

        records, summary, keys = (
            self.driver.execute_query(
                query,
                parameters_=parameters or {},
            )
        )

        return records

    def create_schema(self):
        """
        Create Person.id index using an implicit
        autocommit transaction.

        Memgraph requires index manipulation to be
        executed outside explicit/multicommand
        transactions.
        """

        query = """
        CREATE INDEX ON :Person(id)
        """

        with self.driver.session() as session:
            session.run(query).consume()

        print(
            "Memgraph Person ID index created"
        )

    def get_counts(self):
        """Return node and relationship counts."""

        node_query = """
        MATCH (p:Person)
        RETURN count(p) AS count
        """

        relationship_query = """
        MATCH ()-[r:KNOWS]->()
        RETURN count(r) AS count
        """

        node_records = self.execute(
            node_query
        )

        relationship_records = self.execute(
            relationship_query
        )

        return {
            "nodes": node_records[0]["count"],
            "relationships": relationship_records[0]["count"],
        }
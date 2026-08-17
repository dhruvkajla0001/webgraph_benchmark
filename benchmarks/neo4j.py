from __future__ import annotations

import os

from dotenv import load_dotenv
from neo4j import GraphDatabase


load_dotenv()


class Neo4jAdapter:
    """
    Connection and loading adapter for local Neo4j Community.

    Neo4j is accessed using the official Neo4j Python driver.
    """

    def __init__(self):
        self.uri = os.getenv(
            "NEO4J_URI",
            "bolt://localhost:7688",
        )

        self.username = os.getenv(
            "NEO4J_USERNAME",
            "neo4j",
        )

        self.password = os.getenv(
            "NEO4J_PASSWORD",
            "benchmark_password",
        )

        if not self.uri:
            raise RuntimeError("NEO4J_URI is missing")

        if not self.username:
            raise RuntimeError(
                "NEO4J_USERNAME is missing"
            )

        if not self.password:
            raise RuntimeError(
                "NEO4J_PASSWORD is missing"
            )

        self.driver = GraphDatabase.driver(
            self.uri,
            auth=(self.username, self.password),
        )

    def connect(self):
        """Verify database connectivity."""

        self.driver.verify_connectivity()

        print("Neo4j connection successful")

    def close(self):
        """Close the database driver."""

        self.driver.close()

    def execute(
        self,
        query,
        parameters=None,
    ):
        """Execute a Cypher query."""

        records, summary, keys = (
            self.driver.execute_query(
                query,
                parameters_=parameters or {},
            )
        )

        return records

    def create_schema(self):
        """Create the Person ID uniqueness constraint."""

        query = """
        CREATE CONSTRAINT person_id_unique IF NOT EXISTS
        FOR (p:Person)
        REQUIRE p.id IS UNIQUE
        """

        self.execute(query)

        print(
            "Person ID constraint created"
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
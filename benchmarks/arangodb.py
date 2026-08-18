from __future__ import annotations

import os

from arango import ArangoClient
from dotenv import load_dotenv


load_dotenv()


class ArangoDBAdapter:
    """
    ArangoDB adapter for the graph benchmark.

    Uses native AQL queries while keeping the same
    benchmark workload interface.
    """

    def __init__(self):
        self.host = os.getenv(
            "ARANGO_HOST",
            "http://localhost:8529",
        )

        self.username = os.getenv(
            "ARANGO_USERNAME",
            "root",
        )

        self.password = os.getenv(
            "ARANGO_PASSWORD",
            "benchmark_password",
        )

        self.database_name = os.getenv(
            "ARANGO_DATABASE",
            "webgraph",
        )

        self.graph_name = os.getenv(
            "ARANGO_GRAPH",
            "webgraph",
        )

        self.client = None
        self.db = None

    # ---------------------------------------------------------
    # CONNECTION
    # ---------------------------------------------------------

    def connect(self):
        """Connect to ArangoDB."""

        self.client = ArangoClient(
            hosts=self.host
        )

        system_db = self.client.db(
            "_system",
            username=self.username,
            password=self.password,
        )

        if not system_db.has_database(
            self.database_name
        ):
            system_db.create_database(
                self.database_name
            )

        self.db = self.client.db(
            self.database_name,
            username=self.username,
            password=self.password,
        )

        self.db.version()

        print(
            "ArangoDB connection successful"
        )

    def close(self):
        """Close the ArangoDB client."""

        self.client = None
        self.db = None

    # ---------------------------------------------------------
    # GENERIC AQL EXECUTION
    # ---------------------------------------------------------

    def execute(
        self,
        query,
        parameters=None,
    ):
        """Execute an AQL query."""

        if self.db is None:
            raise RuntimeError(
                "ArangoDB is not connected"
            )

        cursor = self.db.aql.execute(
            query,
            bind_vars=parameters or {},
        )

        return list(cursor)

    # ---------------------------------------------------------
    # SCHEMA
    # ---------------------------------------------------------

    def create_schema(self):
        """
        Create:

        Person vertex collection
        KNOWS edge collection
        webgraph graph
        Person.id index
        """

        # -----------------------------------------------------
        # Person collection
        # -----------------------------------------------------

        if not self.db.has_collection(
            "Person"
        ):
            self.db.create_collection(
                "Person"
            )

        # -----------------------------------------------------
        # KNOWS edge collection
        # -----------------------------------------------------

        if not self.db.has_collection(
            "KNOWS"
        ):
            self.db.create_collection(
                "KNOWS",
                edge=True,
            )

        # -----------------------------------------------------
        # Person.id index
        # -----------------------------------------------------

        person = self.db.collection(
            "Person"
        )

        indexes = person.indexes()

        id_index_exists = any(
            index.get("type") == "persistent"
            and index.get("unique") is True
            and "id" in index.get(
                "fields",
                [],
            )
            for index in indexes
        )

        if not id_index_exists:

            person.add_persistent_index(
                fields=["id"],
                unique=True,
            )

            print(
                "ArangoDB Person ID index created"
            )

        else:

            print(
                "ArangoDB Person ID index already exists"
            )

        # -----------------------------------------------------
        # Graph
        # -----------------------------------------------------

        if not self.db.has_graph(
            self.graph_name
        ):

            self.db.create_graph(
                self.graph_name,
                edge_definitions=[
                    {
                        "edge_collection": "KNOWS",
                        "from_vertex_collections": [
                            "Person"
                        ],
                        "to_vertex_collections": [
                            "Person"
                        ],
                    }
                ],
            )

            print(
                "ArangoDB webgraph created"
            )

        else:

            print(
                "ArangoDB webgraph already exists"
            )

    # ---------------------------------------------------------
    # COUNTS
    # ---------------------------------------------------------

    def get_counts(self):
        """Return node and relationship counts."""

        node_result = self.execute(
            """
            RETURN LENGTH(
                FOR p IN Person
                    RETURN 1
            )
            """
        )

        relationship_result = self.execute(
            """
            RETURN LENGTH(
                FOR r IN KNOWS
                    RETURN 1
            )
            """
        )

        return {
            "nodes": int(
                node_result[0]
            ),
            "relationships": int(
                relationship_result[0]
            ),
        }

    # ---------------------------------------------------------
    # NATIVE AQL WORKLOADS
    # ---------------------------------------------------------

    def point_lookup(
        self,
        node_id: int,
    ):
        """
        Point lookup by indexed Person.id.
        """

        return self.execute(
            """
            FOR p IN Person
                FILTER p.id == @node_id
                RETURN p
            """,
            {
                "node_id": node_id
            },
        )

    def filtered_lookup(
        self,
        min_id: int,
        max_id: int,
    ):
        """
        Filtered node lookup.
        """

        return self.execute(
            """
            FOR p IN Person
                FILTER p.id >= @min_id
                AND p.id <= @max_id
                RETURN p
            """,
            {
                "min_id": min_id,
                "max_id": max_id,
            },
        )

    def one_hop(
        self,
        node_id: int,
    ):
        """
        One-hop outgoing traversal.
        """

        return self.execute(
            """
            FOR p IN Person
                FILTER p.id == @node_id

                FOR neighbor IN 1..1 OUTBOUND
                    p
                    GRAPH @graph_name

                    RETURN neighbor
            """,
            {
                "node_id": node_id,
                "graph_name": self.graph_name,
            },
        )

    def two_hop(
        self,
        node_id: int,
    ):
        """
        Two-hop outgoing traversal.
        """

        return self.execute(
            """
            FOR p IN Person
                FILTER p.id == @node_id

                FOR neighbor IN 2..2 OUTBOUND
                    p
                    GRAPH @graph_name

                    RETURN neighbor
            """,
            {
                "node_id": node_id,
                "graph_name": self.graph_name,
            },
        )

    def three_hop(
        self,
        node_id: int,
    ):
        """
        Three-hop outgoing traversal.
        """

        return self.execute(
            """
            FOR p IN Person
                FILTER p.id == @node_id

                FOR neighbor IN 3..3 OUTBOUND
                    p
                    GRAPH @graph_name

                    RETURN neighbor
            """,
            {
                "node_id": node_id,
                "graph_name": self.graph_name,
            },
        )

    def degree_aggregation(
        self,
    ):
        """
        Calculate outgoing degree for every Person.
        """

        return self.execute(
            """
            FOR p IN Person

                LET degree = LENGTH(
                    FOR neighbor IN 1..1 OUTBOUND
                        p
                        GRAPH @graph_name
                        RETURN 1
                )

                RETURN {
                    id: p.id,
                    degree: degree
                }
            """,
            {
                "graph_name": self.graph_name,
            },
        )
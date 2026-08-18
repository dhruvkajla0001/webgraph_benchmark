from __future__ import annotations

import os

import redis
from dotenv import load_dotenv


load_dotenv()


class FalkorDBAdapter:
    """
    FalkorDB adapter using the Redis protocol directly.

    Direct Redis access avoids the FalkorDB client's INFO call
    during connection initialization, which previously caused
    problems when many clients were created concurrently.
    """

    def __init__(self):
        self.host = os.getenv(
            "FALKORDB_HOST",
            "localhost",
        )

        self.port = int(
            os.getenv(
                "FALKORDB_PORT",
                "6379",
            )
        )

        self.graph_name = os.getenv(
            "FALKORDB_GRAPH",
            "webgraph",
        )

        self.client = None

    def connect(self):
        """Create and verify a FalkorDB connection."""

        self.client = redis.Redis(
            host=self.host,
            port=self.port,
            decode_responses=True,
            socket_connect_timeout=10,
            socket_timeout=60,
            health_check_interval=30,
        )

        self.client.ping()

        print("FalkorDB connection successful")

    def close(self):
        """Close the Redis connection."""

        if self.client is not None:
            try:
                self.client.close()
            except Exception:
                pass

            self.client = None

    def execute(
        self,
        query,
        parameters=None,
    ):
        """Execute an openCypher query through FalkorDB."""

        if self.client is None:
            raise RuntimeError(
                "FalkorDB is not connected"
            )

        parameters = parameters or {}

        if parameters:
            parameter_parts = []

            for key, value in parameters.items():

                if isinstance(value, str):

                    escaped = (
                        value
                        .replace("\\", "\\\\")
                        .replace("'", "\\'")
                    )

                    parameter_parts.append(
                        f"{key} = '{escaped}'"
                    )

                elif value is None:

                    parameter_parts.append(
                        f"{key} = NULL"
                    )

                elif isinstance(value, bool):

                    parameter_parts.append(
                        f"{key} = "
                        f"{'TRUE' if value else 'FALSE'}"
                    )

                else:

                    parameter_parts.append(
                        f"{key} = {value}"
                    )

            query = (
                "CYPHER "
                + ", ".join(parameter_parts)
                + " "
                + query
            )

        result = self.client.execute_command(
            "GRAPH.QUERY",
            self.graph_name,
            query,
            "--compact",
        )

        return self._extract_records(result)

    @staticmethod
    def _extract_records(result):
        """
        Extract rows from FalkorDB GRAPH.QUERY output.

        The exact compact representation can vary depending
        on the query, so do not assume a fixed row structure
        outside this method.
        """

        if not result:
            return []

        if isinstance(result, list):

            # Normal GRAPH.QUERY response:
            # [header, rows, statistics]
            if len(result) >= 2:

                rows = result[1]

                if isinstance(rows, list):
                    return rows

        return result

    def create_schema(self):
        """Create the Person.id index."""

        try:

            self.client.execute_command(
                "GRAPH.QUERY",
                self.graph_name,
                """
                CREATE INDEX
                FOR (p:Person)
                ON (p.id)
                """,
            )

            print(
                "FalkorDB Person ID index created"
            )

        except Exception as exc:

            message = str(exc).lower()

            if (
                "already exists" in message
                or "index already" in message
            ):

                print(
                    "FalkorDB Person ID index "
                    "already exists"
                )

            else:
                raise

    def get_counts(self):
        """Return node and relationship counts."""

        node_result = self.client.execute_command(
            "GRAPH.QUERY",
            self.graph_name,
            """
            MATCH (p:Person)
            RETURN count(p) AS count
            """,
            "--compact",
        )

        relationship_result = self.client.execute_command(
            "GRAPH.QUERY",
            self.graph_name,
            """
            MATCH ()-[r:KNOWS]->()
            RETURN count(r) AS count
            """,
            "--compact",
        )

        nodes = int(
            node_result[1][0][0][1]
        )

        relationships = int(
            relationship_result[1][0][0][1]
        )

        return {
            "nodes": nodes,
            "relationships": relationships,
        }

    @staticmethod
    def _extract_count(result):
        """
        Extract a scalar count from FalkorDB's
        compact GRAPH.QUERY response.
        """

        if not result:
            return 0

        # Common compact response:
        #
        # [
        #   [count_value]
        # ]
        #
        # or:
        #
        # [
        #   [[count_value]]
        # ]

        value = result

        # Unwrap lists until we reach the scalar.
        while isinstance(value, list):

            if not value:
                return 0

            value = value[0]

        try:
            return int(value)
        except (TypeError, ValueError):

            raise RuntimeError(
                "Unable to extract FalkorDB count "
                f"from response: {result!r}"
            )
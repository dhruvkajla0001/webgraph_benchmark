"""
Graph traversal workload definitions.

All databases should implement the same logical workloads.
"""

ONE_HOP = """
MATCH (source:Person {id: $node_id})
      -[:KNOWS]->
      (target:Person)
RETURN target.id AS node_id
LIMIT 100
"""


TWO_HOP = """
MATCH (source:Person {id: $node_id})
      -[:KNOWS]->
      (middle:Person)
      -[:KNOWS]->
      (target:Person)
RETURN DISTINCT target.id AS node_id
LIMIT 100
"""


THREE_HOP = """
MATCH (source:Person {id: $node_id})
      -[:KNOWS]->
      (middle1:Person)
      -[:KNOWS]->
      (middle2:Person)
      -[:KNOWS]->
      (target:Person)
RETURN DISTINCT target.id AS node_id
LIMIT 100
"""


WORKLOADS = {
    "1_hop": ONE_HOP,
    "2_hop": TWO_HOP,
    "3_hop": THREE_HOP,
}
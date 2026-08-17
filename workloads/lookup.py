"""
Lookup workload definitions.
"""


POINT_LOOKUP = """
MATCH (p:Person {id: $node_id})
RETURN p.id AS node_id
"""


FILTERED_LOOKUP = """
MATCH (p:Person)
WHERE p.id >= $min_id
  AND p.id <= $max_id
RETURN p.id AS node_id
LIMIT 100
"""


def get_query():
    return POINT_LOOKUP
"""
Aggregation workload.
"""


DEGREE_AGGREGATION = """
MATCH (p:Person)
OPTIONAL MATCH (p)-[:KNOWS]->(friend:Person)
WITH p, count(friend) AS degree
RETURN
    avg(degree) AS average_degree,
    max(degree) AS maximum_degree,
    count(p) AS node_count
"""


TOP_DEGREE = """
MATCH (p:Person)
OPTIONAL MATCH (p)-[:KNOWS]->(friend:Person)
WITH p, count(friend) AS degree
RETURN
    p.id AS node_id,
    degree
ORDER BY degree DESC
LIMIT 10
"""


WORKLOADS = {
    "degree_aggregation": DEGREE_AGGREGATION,
    "top_degree": TOP_DEGREE,
}
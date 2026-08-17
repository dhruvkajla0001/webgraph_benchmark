"""
Mixed workload definition.

The runner will execute different operations according
to configured percentages.
"""

MIXED_WORKLOAD = {
    "point_lookup": 40,
    "one_hop": 25,
    "two_hop": 15,
    "three_hop": 10,
    "aggregation": 10,
}
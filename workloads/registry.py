from workloads.traversal import WORKLOADS as TRAVERSAL_WORKLOADS
from workloads.lookup import (
    POINT_LOOKUP,
    FILTERED_LOOKUP,
)
from workloads.aggregation import (
    WORKLOADS as AGGREGATION_WORKLOADS,
)


WORKLOAD_REGISTRY = {
    **TRAVERSAL_WORKLOADS,

    "point_lookup": POINT_LOOKUP,
    "filtered_lookup": FILTERED_LOOKUP,

    **AGGREGATION_WORKLOADS,
}
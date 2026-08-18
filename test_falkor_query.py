from benchmarks.falkordb import FalkorDBAdapter
from workloads.node_ids import sample_node_ids

db = FalkorDBAdapter()

try:
    db.connect()

    nid = sample_node_ids(1)[0]

    print("NODE:", nid)

    result = db.execute(
        "MATCH (p:Person {id: $node_id}) RETURN p",
        {"node_id": nid},
    )

    print("RESULT:", result)

finally:
    db.close()

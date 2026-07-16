#!/usr/bin/env python3
"""Pure, no-ANSYS tests for the C7 HDF5 semantic gate."""

from __future__ import annotations

import copy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from c7_hdf5_boundary_semantic_gate import (  # noqa: E402
    CANONICAL_BOUNDARIES,
    CELL_ZONE_NAME,
    FAIL_STATUS,
    FORMAT_VERSION,
    EXPECTED_SOURCE_COMPONENT_COUNTS,
    INTERIOR_NAME,
    PASS_STATUS,
    SOLVER_MARKER,
    _numbers,
    _strings,
    validate_observation,
)


def fixture() -> dict:
    faces = []
    low = 1
    ordered = [(INTERIOR_NAME, 2)] + list(CANONICAL_BOUNDARIES.items())
    for name, zone_type in ordered:
        count = 3 if name == INTERIOR_NAME else 1
        faces.append(
            {
                "id": 100 + len(faces),
                "name": name,
                "zone_type": zone_type,
                "min_id": low,
                "max_id": low + count - 1,
                "face_count": count,
            }
        )
        low += count
    return {
        "format_version": FORMAT_VERSION,
        "solver": SOLVER_MARKER,
        "cell_zones": [
            {
                "id": 482,
                "name": CELL_ZONE_NAME,
                "min_id": 1,
                "max_id": 4,
                "cell_count": 4,
                "cell_type": 7,
            }
        ],
        "face_zones": faces,
        "source_component_counts": dict(EXPECTED_SOURCE_COMPONENT_COUNTS),
        "cell_count": 4,
        "used_node_count": 64,
        "used_node_bbox_mm": {
            "min": [-10.875, -17.750025, 1.2675],
            "max": [10.89, 20.75, 2.800025],
        },
        "adjacency": {
            "total_faces": 13,
            "boundary_zone_count": 10,
            "invalid_interior_faces": 0,
            "invalid_boundary_faces": 0,
            "unknown_cell_references": 0,
            "unassigned_faces": 0,
            "missing_node_references": 0,
            "cell_graph_reached_count": 4,
        },
    }


def rejected(mutator, code: str) -> None:
    value = fixture()
    mutator(value)
    result = validate_observation(value)
    assert result["status"] == FAIL_STATUS, result
    assert code in result["errors"], result


def main() -> int:
    good = validate_observation(fixture())
    assert good["status"] == PASS_STATUS, good
    assert good["p1_p6_gates"] == "NOT_RUN"

    collapsed = fixture()
    collapsed["face_zones"] = [
        {
            "id": 481,
            "name": INTERIOR_NAME,
            "zone_type": 2,
            "min_id": 1,
            "max_id": 223217,
            "face_count": 223217,
        },
        {
            "id": 329,
            "name": CELL_ZONE_NAME + ":329",
            "zone_type": 3,
            "min_id": 223218,
            "max_id": 237689,
            "face_count": 14472,
        },
    ]
    collapsed["adjacency"]["total_faces"] = 237689
    collapsed["adjacency"]["boundary_zone_count"] = 1
    assert validate_observation(collapsed)["status"] == FAIL_STATUS

    rejected(lambda x: x.update(format_version="25.2"), "C7_HDF5_VERSION_INVALID")
    rejected(lambda x: x["face_zones"][1].update(zone_type=3), "C7_FACE_ZONE_TYPE_INVALID")
    rejected(lambda x: x["face_zones"][2].update(min_id=99), "C7_FACE_RANGE_INVALID")
    rejected(lambda x: x["adjacency"].update(invalid_boundary_faces=1), "C7_ADJACENCY_INVALID")
    rejected(lambda x: x["adjacency"].update(cell_graph_reached_count=3), "C7_CELL_GRAPH_DISCONNECTED")
    rejected(lambda x: x["used_node_bbox_mm"]["max"].__setitem__(0, 20.0), "C7_USED_NODE_BBOX_OUT_OF_CONTRACT")
    rejected(lambda x: x.update(cell_count=3), "C7_CELL_COUNT_INVALID")
    rejected(lambda x: x["face_zones"].pop(), "C7_CANONICAL_10_ZONE_INVENTORY_INVALID")
    rejected(lambda x: x["source_component_counts"].update(REMAINING_WALL=75), "C7_SOURCE_COMPONENT_COUNTS_INVALID")

    sample = 'DATA { 1, -2, 3.5e1 } ATTRIBUTE "x" { DATA { 99 } }'
    assert _numbers(sample, integer=False) == [1.0, -2.0, 35.0]
    assert _strings('DATA { "a;b" }') == ["a;b"]
    print("C7_HDF5_GATE_TEST=PASS positive=1 collapsed=1 negative=9 parser=2")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

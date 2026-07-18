#!/usr/bin/env python3
"""Static and pure-function gates for the V03 rear-inlet support correction."""

from __future__ import annotations

import ast
import csv
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
AIRJET_ROOT = HERE.parents[1]
PRODUCER = HERE / "approved" / "006" / "v03_continuous_fluid_producer.py"
ROUTE = HERE / "contracts" / "v03_finite_throat_route_v1.json"
VENTS = AIRJET_ROOT / "parameters" / "p1_vent_geometry_candidates.csv"


def extracted_helpers():
    source = PRODUCER.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(PRODUCER))
    wanted = {"compute_vent_box", "derive_supported_plenum_rear"}
    nodes = [
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name in wanted
    ]
    assert {node.name for node in nodes} == wanted
    namespace = {}
    module = ast.Module(body=nodes, type_ignores=[])
    exec(compile(ast.fix_missing_locations(module), str(PRODUCER), "exec"), namespace)
    return source, namespace


def selected_vents():
    with VENTS.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    result = [
        row for row in rows
        if row["candidate_set_id"] == "VENT_FLOW_BBOX_R0"
    ]
    assert len(result) == 4
    return result


def expect_failure(function, code):
    try:
        function()
    except Exception as exc:
        assert str(exc) == code, (str(exc), code)
    else:
        raise AssertionError("expected %s" % code)


def main():
    source, helpers = extracted_helpers()
    derive = helpers["derive_supported_plenum_rear"]
    vents = selected_vents()
    support = derive(vents, -14.5)
    assert support["cell_footprint_y_min_mm"] == -14.5
    assert support["supported_plenum_y_min_mm"] == -17.75
    assert support["rear_support_extension_mm"] == 3.25
    assert support["rear_inlet_ids"] == ["V01", "V02"]
    assert set(support["vent_boxes_mm"]) == {"V01", "V02", "V03", "V04"}
    assert support["vent_boxes_mm"]["V01"][1] == -17.75
    assert support["vent_boxes_mm"]["V02"][1] == -17.75

    expect_failure(
        lambda: derive(vents[:3], -14.5),
        "AJM006_V03_VENT_SUPPORT_COUNT_NOT_4",
    )
    duplicate = [dict(row) for row in vents]
    duplicate[1]["vent_id"] = duplicate[0]["vent_id"]
    expect_failure(
        lambda: derive(duplicate, -14.5),
        "AJM006_V03_VENT_SUPPORT_DUPLICATE_ID",
    )
    wrong_id = [dict(row) for row in vents]
    wrong_id[0]["vent_id"] = "V05"
    expect_failure(
        lambda: derive(wrong_id, -14.5),
        "AJM006_V03_VENT_SUPPORT_IDS_INVALID",
    )
    no_extension = [dict(row) for row in vents]
    for row in no_extension:
        row["center_y_cad_mm"] = "0"
    expect_failure(
        lambda: derive(no_extension, -20.0),
        "AJM006_V03_VENT_SUPPORT_EXTENSION_NOT_POSITIVE",
    )

    derive_pos = source.index("vent_support = derive_supported_plenum_rear")
    document_pos = source.index("DocumentHelper.CreateNewDocument()")
    assert derive_pos < document_pos
    assert 'footprint_x_min, vent_support["supported_plenum_y_min_mm"]' in source
    assert 'box = list(vent_support["vent_boxes_mm"]' in source
    assert "box[1] = footprint_y_min" not in source
    assert "clip" not in source.lower()

    route = json.loads(ROUTE.read_text(encoding="utf-8"))
    geometry = route["geometry_contract"]
    assert geometry["upstream_rear_support_rule"].startswith("EXTEND_C_CLASS")
    assert geometry["cell_footprint_y_min_mm"] == -14.5
    assert geometry["supported_plenum_y_min_mm"] == -17.75
    assert geometry["rear_inlet_support_extension_mm"] == 3.25
    assert geometry["rear_inlet_ids"] == ["V01", "V02"]
    assert route["boundary_contract"]["INLET"] == 4
    assert route["boundary_contract"]["OUTLET"] == 1
    print("V03_VENT_REAR_SUPPORT_GATE=PASS")


if __name__ == "__main__":
    main()

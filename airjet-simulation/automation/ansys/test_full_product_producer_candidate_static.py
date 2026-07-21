#!/usr/bin/env python3
"""Fail-closed static checks for the unregistered formal 006 producer candidate."""

from __future__ import annotations

import ast
import csv
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SOURCE = HERE / "approved" / "006" / "full_product_producer.py"
POLICY = HERE / "profiles.json"
CAMPAIGN = HERE / "contracts" / "trusted_full_product_gen1" / "campaign.json"
PROFILE_PRODUCER = "ajm006-spaceclaim-full-product-producer-v1"
PROFILE_OBSERVER = "ajm006-workbench-full-product-observer-v1"


def main() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    ast.parse(source)
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    campaign = json.loads(CAMPAIGN.read_text(encoding="utf-8"))

    profiles = {item["profile_id"] for item in policy["profiles"]}
    production = policy["production_contracts"]
    assert production["execution_state"] == "STATIC_CONTRACT_ONLY_NOT_REGISTERED"
    assert PROFILE_PRODUCER not in profiles
    assert PROFILE_OBSERVER not in profiles
    assert production["producer_profile_id"] == PROFILE_PRODUCER
    assert production["observer_profile_id"] == PROFILE_OBSERVER

    records = campaign["variant_contracts"]
    assert len(records) == production["expected_variant_count"] == 9
    for record in records:
        assert Path(record["blueprint_path"]).name in source

    parameter_root = REPO / "airjet-simulation" / "parameters"
    with (parameter_root / "p1_model_form_variants.csv").open(newline="", encoding="utf-8") as handle:
        variants = {row["variant_id"]: row for row in csv.DictReader(handle)}
    with (parameter_root / "p1_planform_exhaust_candidates.csv").open(newline="", encoding="utf-8") as handle:
        exhausts = {row["exhaust_branch_id"]: row for row in csv.DictReader(handle)}
    with (parameter_root / "p1_vent_geometry_candidates.csv").open(newline="", encoding="utf-8") as handle:
        vent_rows = list(csv.DictReader(handle))
    observed_support = {}
    for record in records:
        source_id = record["source_variant_id"]
        variant = variants[source_id]
        footprint_y_min = float(exhausts[variant["exhaust_branch_id"]]["cell_footprint_y_min_mm"])
        vents = [row for row in vent_rows if row["candidate_set_id"] == variant["vent_candidate_set_id"]]
        boxes = {}
        for vent in vents:
            cy = float(vent["center_y_cad_mm"])
            dx = float(vent["axis_dx_unit"])
            dy = float(vent["axis_dy_unit"])
            length = float(vent["axis_length_mm"])
            width = float(vent["slot_width_mm"])
            half_y = abs(dy) * length / 2.0 + abs(dx) * width / 2.0
            boxes[vent["vent_id"]] = cy - half_y
        rear_ids = sorted(key for key, value in boxes.items() if value < footprint_y_min)
        supported_y_min = min([footprint_y_min] + list(boxes.values()))
        assert rear_ids == ["V01", "V02"]
        assert supported_y_min < footprint_y_min
        observed_support[source_id] = (supported_y_min, footprint_y_min - supported_y_min)
    accepted = observed_support["M-3x4-7.0__R50_BALANCED"]
    assert abs(accepted[0] - -17.75) <= 1.0e-9
    assert abs(accepted[1] - 3.25) <= 1.0e-9

    required_markers = (
        'RUNTIME_VARIANT_ID = os.environ["AIRJET_CASE_ID"]',
        'if item.get("variant_id") == RUNTIME_VARIANT_ID',
        'VARIANT_ID = record["source_variant_id"]',
        "derive_supported_plenum_rear",
        'rear_ids != ["V01", "V02"]',
        'variant["vent_candidate_set_id"] == "VENT_FLOW_BBOX_R0"',
        "close_enough(footprint_y_min, -14.5, 1.0e-9)",
        'vent_support["supported_plenum_y_min_mm"], -17.75',
        '"rear_support_extension_mm"',
        "cell_count in (8, 12, 15)",
        '"FORMAL_PRODUCER_IMPLEMENTATION_INCOMPLETE_NOT_REGISTERABLE"',
    )
    for marker in required_markers:
        assert marker in source, marker

    assert 'VARIANT_ID = "M-3x4-7.0__R50_BALANCED"' not in source
    assert '"p1_stage_gate": "PASS"' not in source
    assert '"formal_006_completion": True' not in source
    print(
        "FULL_PRODUCT_PRODUCER_CANDIDATE_STATIC=PASS "
        "variants=9 cells=8,12,15 rear_inlets=V01,V02 registration=PROHIBITED"
    )


if __name__ == "__main__":
    main()

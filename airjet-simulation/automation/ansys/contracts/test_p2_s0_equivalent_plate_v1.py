#!/usr/bin/env python3
"""Fail-closed static guards for the P2 S0 equivalent-plate contract."""

from __future__ import annotations

import csv
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
VARIANT = json.loads(
    (
        HERE
        / "trusted_full_product_gen1"
        / "variant_02_m_3x4_7_0_r50_balanced.json"
    ).read_text(encoding="utf-8")
)
CONTRACT = json.loads(
    (HERE / "p2_s0_equivalent_plate_v1.json").read_text(encoding="utf-8")
)
MATERIALS = list(
    csv.DictReader(
        (
            REPO
            / "airjet-simulation"
            / "parameters"
            / "p2_s0_equivalent_material_candidates.csv"
        ).open(encoding="utf-8", newline="")
    )
)


def test_identity_and_claim_ceiling() -> None:
    assert CONTRACT["schema_version"] == 1
    assert CONTRACT["product_id"] == "AIRJET_MINI_GEN1"
    assert CONTRACT["source_variant_id"] == "M-3x4-7.0__R50_BALANCED"
    assert CONTRACT["source_configuration_id"] == "AJM006_GEN1_CFG_M-3x4-7.0"
    assert CONTRACT["source_cell"]["cell_id"] == "CELL_005"
    assert CONTRACT["source_cell"]["frame_origin_mm"] == [0.0, -3.625, 0.0]
    assert CONTRACT["source_cell"]["local_model_origin_reset"] is True
    assert CONTRACT["formal_p2_gate"] == "NOT_RUN"
    assert CONTRACT["p1_p6_gates"] == "NOT_RUN"
    assert CONTRACT["claim_ceiling"] == (
        "PASS_PRE_GATE_P2_S0_EQUIVALENT_PLATE_BASELINE"
    )


def test_geometry_is_exact_and_not_product_fact() -> None:
    geometry = CONTRACT["geometry"]
    assert geometry["plate_side_mm"] == 7.0
    assert geometry["plate_thickness"]["value_mm"] == 0.275
    assert geometry["plate_thickness"]["product_fact"] is False
    assert geometry["anchor"] == {
        "boolean_overlap_mm": 0.001,
        "depth_mm": 0.05,
        "evidence_class": "C",
        "product_fact": False,
        "status": "topology_placeholder",
        "width_mm": 2.25,
    }
    assert geometry["expected_bbox_min_mm"] == [-3.5, -3.5, -0.05]
    assert geometry["expected_bbox_max_mm"] == [3.5, 3.5, 0.275]
    assert geometry["expected_union_volume_mm3"] == 13.728125
    assert geometry["perimeter_constraint"] == (
        "FREE_NO_CAD_CONSTRAINT_DEFINED"
    )
    assert geometry["step_named_selection_transfer"] == "NOT_ASSUMED"


def test_semantic_roles_are_exact() -> None:
    assert CONTRACT["semantic_roles"] == {
        "NS_ANCHOR_FIXED": 1,
        "NS_EQ_BODY": 1,
        "NS_MEMBRANE_ALL": 1,
        "NS_MEMBRANE_TOP": 1,
        "NS_TIP_X_MINUS": 1,
        "NS_TIP_X_PLUS": 1,
    }


def test_materials_are_candidate_sensitivity_values_only() -> None:
    assert CONTRACT["material_contract"]["design"] == (
        "paired_candidate_bundle_not_factorial"
    )
    assert [row["candidate_id"] for row in MATERIALS] == [
        "EQ-A-Z005",
        "EQ-B-Z015",
        "EQ-C-Z030",
    ]
    assert [float(row["youngs_modulus_GPa"]) for row in MATERIALS] == [
        70.0,
        120.0,
        200.0,
    ]
    assert [float(row["damping_ratio"]) for row in MATERIALS] == [
        0.005,
        0.015,
        0.03,
    ]
    for row in MATERIALS:
        assert float(row["poissons_ratio"]) == 0.30
        assert float(row["density_kg_m3"]) == 7800.0
        assert row["evidence_class"] == "C"
        assert row["status"] == "engineering_sensitivity_candidate"
        assert row["product_fact"] == "false"
        assert row["allowed_claim"] == "equivalent_property_sensitivity_only"


def test_trusted_source_cell_binding() -> None:
    assert VARIANT["product_id"] == CONTRACT["product_id"]
    assert VARIANT["source_variant_id"] == CONTRACT["source_variant_id"]
    assert VARIANT["configuration"]["configuration_id"] == (
        CONTRACT["source_configuration_id"]
    )
    cells = [item for item in VARIANT["frames"] if item["frame_id"] == "CELL_005"]
    assert len(cells) == 1
    assert cells[0]["origin_mm"] == CONTRACT["source_cell"]["frame_origin_mm"]
    assert cells[0]["axes"] == [
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
    ]


def main() -> None:
    tests = [
        value
        for name, value in sorted(globals().items())
        if name.startswith("test_") and callable(value)
    ]
    for test in tests:
        test()
        print("PASS", test.__name__)
    print("AJM_P2_S0_EQUIVALENT_PLATE_CONTRACT=PASS_ALL")


if __name__ == "__main__":
    main()

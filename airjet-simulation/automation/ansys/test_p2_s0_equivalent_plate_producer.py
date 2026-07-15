#!/usr/bin/env python3
"""Fail-closed static guards for the P2 S0 SpaceClaim producer."""

from __future__ import annotations

import ast
import hashlib
from pathlib import Path


HERE = Path(__file__).resolve().parent
SOURCE_PATH = HERE / "approved" / "008" / "p2_s0_equivalent_plate_producer.py"
SOURCE = SOURCE_PATH.read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)


def literal_assignments() -> dict:
    values = {}
    for node in TREE.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name):
                try:
                    values[target.id] = ast.literal_eval(node.value)
                except (ValueError, TypeError):
                    pass
    return values


def test_exact_geometry_and_dependency_contract() -> None:
    values = literal_assignments()
    assert values["DEPENDENCY_NAMES"] == (
        "p2_s0_equivalent_plate_v1.json",
        "p2_s0_equivalent_material_candidates.csv",
        "variant_02_m_3x4_7_0_r50_balanced.json",
    )
    assert values["EXPECTED_BBOX_MIN_MM"] == [-3.5, -3.5, -0.05]
    assert values["EXPECTED_BBOX_MAX_MM"] == [3.5, 3.5, 0.275]
    assert values["EXPECTED_VOLUME_MM3"] == 13.728125
    assert values["EXPECTED_ROLE_COUNTS"] == {
        "NS_EQ_BODY": 1,
        "NS_ANCHOR_FIXED": 1,
        "NS_MEMBRANE_TOP": 1,
        "NS_MEMBRANE_ALL": 1,
        "NS_TIP_X_PLUS": 1,
        "NS_TIP_X_MINUS": 1,
    }
    assert len(values["EXPECTED_MATERIAL_ROWS"]) == 3
    assertions = values["ASSERTION_NAMES"]
    assert len(assertions) == 16 and len(set(assertions)) == 16


def test_v261_geometry_and_round_trip_calls_are_pinned() -> None:
    for required in (
        "SpaceClaim.Api.V261.Scripting.Extensions.PartExtensions",
        "Array[String]([name])",
        "Combine.Merge(",
        "Selection.Create(plate), Selection.Create(anchor)",
        "DocumentSave.Execute(NATIVE_PATH)",
        "DocumentSave.Execute(STEP_PATH)",
        "DocumentHelper.CloseDocument()",
        "DocumentOpen.Execute(NATIVE_PATH)",
        "DocumentOpen.Execute(STEP_PATH)",
        'CreateAGroup("NS_EQ_BODY")',
        'create_face_group("NS_ANCHOR_FIXED"',
        'create_face_group("NS_MEMBRANE_TOP"',
        'create_face_group("NS_MEMBRANE_ALL", authored_roles["NS_MEMBRANE_TOP"]',
        '"step_named_selection_transfer": "NOT_ASSUMED"',
        '"mechanical_reconstruction_required": True',
    ):
        assert required in SOURCE
    assert "STEP_NAMED_SELECTION_TRANSFER_ASSUMED" not in SOURCE


def test_claim_ceiling_and_no_solver_are_explicit() -> None:
    for required in (
        '"status": "FAIL_DIRECT"',
        '"pilot_result": "NOT_RUN"',
        '"claim_ceiling": "PASS_PRE_GATE_P2_S0_EQUIVALENT_PLATE_BASELINE"',
        '"formal_p2_completion": False',
        '"formal_p2_gate": "NOT_RUN"',
        '"p2_stage_gate": "NOT_RUN"',
        '"p1_p6_gates": "NOT_RUN"',
        '"exact_product_geometry": "NOT_CLAIMED"',
        '"product_material_identification": "NOT_CLAIMED"',
        '"mechanical": "NOT_RUN"',
        '"modal": "NOT_RUN"',
        '"harmonic": "NOT_RUN"',
        '"piezoelectric_coupling": "NOT_RUN"',
        '"fsi": "NOT_RUN"',
        '"license_arguments_added": False',
        'result_data["status"] = "PASS_PARTIAL_CAD_CAPABILITY"',
        'contract.get("case_id") != os.environ["AIRJET_CASE_ID"]',
        'contract.get("claim_ceiling") != result_data["claim_ceiling"]',
        'contract.get("semantic_roles") != EXPECTED_ROLE_COUNTS',
        'geometry_contract.get("expected_union_volume_mm3") != EXPECTED_VOLUME_MM3',
        'result_data["formal_p2_gate"] == "NOT_RUN"',
        'result_data["pilot_result"] = contract["claim_ceiling"]',
    ):
        assert required in SOURCE
    for forbidden in (
        "PASS_P2_GATE",
        '"p2_stage_gate": "PASS"',
        "launch_fluent",
        "pymechanical",
        "Mechanical",
    ):
        assert forbidden not in SOURCE


def test_script_identity_is_stable() -> None:
    digest = hashlib.sha256(SOURCE_PATH.read_bytes()).hexdigest()
    assert len(digest) == 64
    assert SOURCE_PATH.stat().st_size < 1024 * 1024


def main() -> None:
    tests = [
        value
        for name, value in sorted(globals().items())
        if name.startswith("test_") and callable(value)
    ]
    for test in tests:
        test()
        print("PASS", test.__name__)
    print("AJM_P2_S0_EQUIVALENT_PLATE_PRODUCER_GUARDS=PASS_ALL")


if __name__ == "__main__":
    main()

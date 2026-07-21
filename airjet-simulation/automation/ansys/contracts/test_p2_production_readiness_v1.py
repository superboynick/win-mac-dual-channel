#!/usr/bin/env python3
"""Fail-closed static checks for the P2 production-readiness contract."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
CONTRACT = json.loads((HERE / "p2_production_readiness_v1.json").read_text(encoding="utf-8"))


def test_identity_and_gate_ceiling() -> None:
    assert CONTRACT["schema_version"] == 1
    assert CONTRACT["contract_id"] == "AJM_P2_PRODUCTION_READINESS_V1"
    assert CONTRACT["product_id"] == "AIRJET_MINI_GEN1"
    assert CONTRACT["source_variant_id"] == "M-3x4-7.0__R50_BALANCED"
    assert CONTRACT["formal_p2_gate"] == "NOT_RUN"
    assert CONTRACT["claim_ceiling"] == "P2_PRODUCTION_PROFILE_NOT_READY"


def test_geometry_handoff_hash_is_exact() -> None:
    handoff = CONTRACT["accepted_geometry_handoff"]
    path = REPO / handoff["path"]
    assert path.is_file()
    assert hashlib.sha256(path.read_bytes()).hexdigest() == handoff["sha256"]
    assert handoff["scope"] == "FULL_PRODUCT_P1_GEOMETRY_RUNTIME_ONLY"
    assert handoff["formal_p1_gate"] == "NOT_PASSED"


def test_existing_s0_cannot_be_promoted() -> None:
    baseline = CONTRACT["existing_baseline"]
    assert baseline["profile_id"] == "ajm008-spaceclaim-p2-s0-equivalent-plate-v1"
    assert baseline["solver_use"] == "PROHIBITED_AS_PRODUCTION_P2"
    assert CONTRACT["required_production_profile"]["status"] == "NOT_READY"
    assert CONTRACT["required_production_profile"]["profile_id"] == "UNASSIGNED"
    assert CONTRACT["required_production_profile"]["submission_authorization"] == (
        "SEPARATE_SIGNED_RUNTIME_TASK_REQUIRED"
    )


def test_entry_requirements_are_unique_and_fail_closed() -> None:
    rows = CONTRACT["entry_requirements"]
    ids = [row["id"] for row in rows]
    assert len(ids) == len(set(ids)) == 8
    assert {row["status"] for row in rows} <= {"PASS", "NOT_READY"}
    assert [row["id"] for row in rows if row["status"] == "PASS"] == ["P2.IN.GEOMETRY"]
    assert "0.275 mm product claim" in next(row["requirement"] for row in rows if row["id"] == "P2.IN.STACK")


def test_solver_sequence_outputs_and_assertions_are_complete() -> None:
    assert CONTRACT["required_solver_sequence"] == [
        "MODAL_S0", "HARMONIC_S0_UNIT_LOAD", "MODAL_S1_STACK_A_B_C", "PIEZO_HARMONIC_S2"
    ]
    assertions = set(CONTRACT["required_assertions"])
    assert {"perimeter_free", "target_mode_changes_chamber_volume", "collision_envelope_clear"} <= assertions
    assert len(assertions) == 11
    outputs = set(CONTRACT["required_outputs"])
    assert "p2_normalized_mode_shape.csv" in outputs
    assert "p2_artifact_manifest.json" in outputs
    assert CONTRACT["external_artifact_root"] == "D:/AirJet_P2/AJM-P2-STRUCTURAL-008"


def test_fail_closed_rules_are_literal() -> None:
    assert CONTRACT["fail_closed_rules"] == {
        "missing_required_input": "REJECT_BEFORE_SUBMISSION",
        "student_capability_unknown": "SMOKE_ONLY_NO_PRODUCTION_CLAIM",
        "solver_nonterminal_timeout": "FAIL_AND_PRESERVE_JOB",
        "artifact_hash_missing": "REJECT_HANDOFF_TO_P3",
        "formal_gate_self_award": "PROHIBITED",
    }


def main() -> None:
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_") and callable(value)]
    for test in tests:
        test()
        print("PASS", test.__name__)
    print("AJM_P2_PRODUCTION_READINESS=PASS_ALL_NOT_READY_FAIL_CLOSED")


if __name__ == "__main__":
    main()

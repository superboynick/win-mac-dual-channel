#!/usr/bin/env python3
"""Static guards for the audited P2 S0 producer runner."""

from __future__ import annotations

import ast
import hashlib
from pathlib import Path


HERE = Path(__file__).resolve().parent
RUNNER_PATH = HERE / "run_p2_s0_equivalent_plate_008.py"
PRODUCER_PATH = HERE / "approved" / "008" / "p2_s0_equivalent_plate_producer.py"
POLICY_PATH = HERE / "profiles.json"
SOURCE = RUNNER_PATH.read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)


def assignments() -> dict:
    values = {}
    for node in TREE.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name):
                try:
                    values[target.id] = ast.literal_eval(node.value)
                except (TypeError, ValueError):
                    pass
    return values


def test_runner_is_hash_bound_to_exact_profile() -> None:
    values = assignments()
    assert values["PROFILE_ID"] == "ajm008-spaceclaim-p2-s0-equivalent-plate-v1"
    assert values["PROFILE_SCRIPT"] == "008/p2_s0_equivalent_plate_producer.py"
    assert values["PROFILE_SCRIPT_SHA256"] == hashlib.sha256(
        PRODUCER_PATH.read_bytes()
    ).hexdigest()
    assert values["PRODUCER_REPORT"] == "p2_s0_equivalent_plate_producer.json"
    assert values["CASE_ID"] == "AJM-P2-S0-EQ-M7-C005"
    assert len(values["EXPECTED_ASSERTIONS"]) == 16
    assert len(values["EXPECTED_DEPENDENCY_GIT_PATHS"]) == 3
    assert values["EXPECTED_ARTIFACTS"] == {
        "p2_s0_equivalent_plate.scdocx",
        "p2_s0_equivalent_plate.step",
        "p2_s0_equivalent_plate_sidecar.json",
    }


def test_fail_closed_controls_and_claims_are_pinned() -> None:
    for required in (
        'common.git_capture("status", "--porcelain=v1")',
        'common.git_capture("verify-commit", "--raw", head)',
        'version("mcp") != "1.28.1"',
        'args=["-I", "-B", str(SERVER)]',
        '"submit_job"',
        '"poll_job"',
        '"cancel_job"',
        '"artifact_manifest"',
        "validate_dependency_artifacts(",
        "validate_report(",
        '"PASS_PRE_GATE_P2_S0_EQUIVALENT_PLATE_GEOMETRY"',
        'report.get("p2_stage_gate") != "NOT_RUN"',
        'report.get("p1_p6_gates") != "NOT_RUN"',
        'report.get("mechanical") != "NOT_RUN"',
        'report.get("modal") != "NOT_RUN"',
        'report.get("harmonic") != "NOT_RUN"',
    ):
        assert required in SOURCE
    for forbidden in (
        "git reset",
        "git checkout",
        "force-push",
        "PASS_P2_GATE",
    ):
        assert forbidden not in SOURCE


def test_policy_contains_exact_profile() -> None:
    import json

    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    matches = [
        item
        for item in policy["profiles"]
        if item["profile_id"] == "ajm008-spaceclaim-p2-s0-equivalent-plate-v1"
    ]
    assert len(matches) == 1
    assert matches[0]["sha256"] == hashlib.sha256(PRODUCER_PATH.read_bytes()).hexdigest()


def main() -> None:
    tests = [
        value
        for name, value in sorted(globals().items())
        if name.startswith("test_") and callable(value)
    ]
    for test in tests:
        test()
        print("PASS", test.__name__)
    print("AJM_P2_S0_EQUIVALENT_PLATE_RUNNER_GUARDS=PASS_ALL")


if __name__ == "__main__":
    main()

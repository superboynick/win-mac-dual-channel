#!/usr/bin/env python3
"""No-ANSYS tests for the exact AJM-005 Phase-B closeout contract."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile

from ajm005_closeout_v2 import (
    CLOSEOUT_FIELDS,
    CONSUMER_REQUIRED_ASSERTIONS,
    PRODUCER_REQUIRED_ASSERTIONS,
    SOURCE_CONTRACTS,
    build_closeout_values,
    parse_closeout_ascii,
    render_closeout_ascii,
    validate_closeout_values,
)


SHA = "a" * 64
HEAD = "1" * 40
CASE_ID = "ajm005-alt-testcase"


def write_ascii_lf(path: Path, text: str) -> None:
    """Write deterministic ASCII/LF text on Python 3.9 and newer."""
    with open(str(path), "w", encoding="ascii", newline="\n") as stream:
        stream.write(text)


def source(source_id: str) -> dict[str, str]:
    expected = SOURCE_CONTRACTS[source_id]
    value = {
        "source_commit": expected["commit"],
        "source_path": expected["path"],
        "source_blob_sha256": expected["sha256"],
        "validation": "PASS",
    }
    if source_id == "t0_controls":
        value.update(
            {
                "suite_status": "PASS_CONTROL_SET",
                "engineering_capability": "NOT_RUN",
                "pass_005_capability": "NOT_EVALUATED_T0_ONLY",
                "p1_p6_gates": "NOT_RUN",
            }
        )
    elif source_id == "cleanup":
        value.update(
            {"cleanup_status": "PASS", "official_exe_signatures": "PASS"}
        )
    else:
        value["p0_stage_gate"] = "PASS"
    return value


def base_result() -> dict:
    producer_assertions = dict((name, True) for name in PRODUCER_REQUIRED_ASSERTIONS)
    consumer_assertions = dict((name, True) for name in CONSUMER_REQUIRED_ASSERTIONS)
    return {
        "schema_version": 1,
        "task": "AJM-WIN-ANSYS-STUDENT-CAPABILITY-SMOKE-005",
        "suite": "alternate_step_semantic_confirmation_v2",
        "case_id": CASE_ID,
        "suite_status": "PASS_ALTERNATE_ROUTE_SEMANTIC_CONFIRMATION",
        "p1_cad_toolchain_readiness": "PASS",
        "p1_cad_toolchain_scope": "ALTERNATE_ROUTE_ONLY",
        "cad_authoring_route": "SPACECLAIM_SIGNED_SCRIPT_PARAMETRIC",
        "solver_handoff_route": "HASH_BOUND_STEP_SEMANTIC_SIDECAR",
        "external_native_attach": "NOT_PROVEN",
        "native_parameterization": "NOT_PROVEN",
        "native_named_selection_transfer": "NOT_PROVEN",
        "p1_stage_gate": "NOT_RUN",
        "p1_p6_gates": "NOT_RUN",
        "visibility": "NOT_USER_OBSERVED",
        "license_data_read": False,
        "git_head": HEAD,
        "preflight": {
            "preflight_ok": True,
            "git_fetch": True,
            "branch": "main",
            "git_clean": True,
            "ahead_behind": "0\t0",
            "git_head": HEAD,
            "project_audit": True,
            "signed_composite_sources": {
                source_id: source(source_id) for source_id in SOURCE_CONTRACTS
            },
        },
        "runs": [
            {
                "profile_id": "ajm005-spaceclaim-cad-t1-v2",
                "case_id": CASE_ID,
                "submitted": True,
                "reached_terminal": True,
                "final_state": {
                    "phase": "PROCESS_EXITED_0",
                    "profile_id": "ajm005-spaceclaim-cad-t1-v2",
                    "case_id": CASE_ID,
                    "job_id": "producer-job",
                },
                "capability_pass": True,
                "capability_status": "PASS",
                "declared_report_sha256": SHA,
                "declared_report": {
                    "status": "PASS_PARTIAL_CAD_CAPABILITY",
                    "engineering_capability": "PASS_PARTIAL_CAD_CAPABILITY",
                    "assertions": producer_assertions,
                    "files": {"step": {"sha256": SHA}},
                },
            },
            {
                "profile_id": "ajm005-workbench-semantic-reconstruction-t1-v2",
                "case_id": CASE_ID,
                "submitted": True,
                "reached_terminal": True,
                "final_state": {
                    "phase": "PROCESS_EXITED_0",
                    "profile_id": "ajm005-workbench-semantic-reconstruction-t1-v2",
                    "case_id": CASE_ID,
                    "job_id": "consumer-job",
                },
                "capability_pass": True,
                "capability_status": "PASS",
                "declared_report_sha256": SHA,
                "declared_report": {
                    "status": "PASS_ALTERNATE_ROUTE_SEMANTIC_RECONSTRUCTION",
                    "engineering_capability": "PASS_ALTERNATE_ROUTE_SEMANTIC_RECONSTRUCTION",
                    "alternate_route_assertions": consumer_assertions,
                },
            },
        ],
        "error": None,
    }


def fail_suite(result: dict, message: str) -> None:
    result["suite_status"] = "FAIL_ALTERNATE_ROUTE_SEMANTIC_CONFIRMATION"
    result["p1_cad_toolchain_readiness"] = "BLOCKED"
    result["error"] = {"message": message}


def assert_exact(values: dict[str, str]) -> None:
    assert tuple(values) == CLOSEOUT_FIELDS
    payload = render_closeout_ascii(values)
    assert payload.decode("ascii").count("\n") == len(CLOSEOUT_FIELDS)
    assert b"\r" not in payload
    assert parse_closeout_ascii(payload) == values


def expect_rejected(values: dict[str, str], code: str) -> None:
    try:
        validate_closeout_values(values)
    except ValueError as error:
        assert str(error) == code, (str(error), code)
        return
    raise AssertionError("expected rejection " + code)


def main() -> None:
    negative = 0
    with tempfile.TemporaryDirectory(prefix="ajm005-closeout-test-") as root:
        result_path = Path(root) / "suite.json"
        write_ascii_lf(result_path, json.dumps({"test": True}))

        success = build_closeout_values(base_result(), result_path, "TEST-HOST")
        assert_exact(success)
        assert success["STUDENT_TOOLCHAIN_STATUS"] == "PASS_START_P1"
        assert success["GIT_AHEAD_BEHIND"] == "0_AHEAD_0_BEHIND"
        assert success["STATIC_STRUCTURAL_SOLVE"] == "NOT_RUN"
        assert success["MODAL_VISIBLE"] == "NOT_VISIBLE"
        assert success["SYSTEM_COUPLING_STATUS"] == "UNVERIFIED_WARNING"

        consumer = base_result()
        consumer["runs"][1]["declared_report"]["alternate_route_assertions"][
            "semantic_geometry_direction"
        ] = False
        consumer["runs"][1]["capability_pass"] = False
        consumer["runs"][1]["capability_status"] = "FAIL"
        fail_suite(consumer, "consumer=failure")
        consumer_failed = build_closeout_values(consumer, result_path, "TEST-HOST")
        assert_exact(consumer_failed)
        assert consumer_failed["PARAMETRIC_GEOMETRY"] == "PASS"
        assert consumer_failed["SOLVER_SEMANTIC_RECONSTRUCTION"] == "FAIL"
        assert consumer_failed["STUDENT_TOOLCHAIN_STATUS"] == "BLOCKED_TECHNICAL_FAILURE"
        assert "consumer=failure" in consumer_failed["ERROR_MESSAGES"]
        assert parse_closeout_ascii(render_closeout_ascii(consumer_failed)) == consumer_failed

        producer = base_result()
        producer["runs"][0]["declared_report"]["assertions"]["native_save"] = False
        producer["runs"][0]["capability_pass"] = False
        producer["runs"][0]["capability_status"] = "FAIL"
        producer["runs"] = producer["runs"][:1]
        fail_suite(producer, "producer failure")
        producer_failed = build_closeout_values(producer, result_path, "TEST-HOST")
        assert_exact(producer_failed)
        assert producer_failed["NATIVE_SAVE"] == "FAIL"
        assert producer_failed["PARAMETRIC_GEOMETRY"] == "PASS"
        assert producer_failed["WORKBENCH_STEP_IMPORT"] == "NOT_RUN"
        assert producer_failed["CONSUMER_REPORT_SHA256"] == "NOT_VERIFIED"

        process = base_result()
        process["runs"][0]["final_state"]["phase"] = "FAILED_PROCESS"
        process["runs"][0]["capability_pass"] = False
        process["runs"][0]["capability_status"] = "FAIL"
        fail_suite(process, "producer process failed")
        process_failed = build_closeout_values(process, result_path, "TEST-HOST")
        assert_exact(process_failed)
        assert process_failed["PARAMETRIC_GEOMETRY"] == "FAIL"
        assert process_failed["WORKBENCH_STEP_IMPORT"] == "FAIL"

        producer_malformed = base_result()
        producer_malformed["runs"][0]["declared_report"] = None
        producer_malformed["runs"][0]["capability_pass"] = False
        producer_malformed["runs"][0]["capability_status"] = "FAIL"
        producer_malformed["runs"] = producer_malformed["runs"][:1]
        fail_suite(producer_malformed, "producer report missing after submit")
        producer_malformed_values = build_closeout_values(
            producer_malformed, result_path, "TEST-HOST"
        )
        assert_exact(producer_malformed_values)
        assert producer_malformed_values["PARAMETRIC_GEOMETRY"] == "FAIL"
        assert producer_malformed_values["STEP_EXPORT_REIMPORT"] == "FAIL"
        assert producer_malformed_values["WORKBENCH_STEP_IMPORT"] == "NOT_RUN"

        consumer_malformed = base_result()
        consumer_malformed["runs"][1]["declared_report"][
            "alternate_route_assertions"
        ].pop("semantic_cardinality")
        consumer_malformed["runs"][1]["capability_pass"] = False
        consumer_malformed["runs"][1]["capability_status"] = "FAIL"
        fail_suite(consumer_malformed, "consumer assertion missing after submit")
        consumer_malformed_values = build_closeout_values(
            consumer_malformed, result_path, "TEST-HOST"
        )
        assert_exact(consumer_malformed_values)
        assert consumer_malformed_values["PARAMETRIC_GEOMETRY"] == "PASS"
        assert consumer_malformed_values["WORKBENCH_STEP_IMPORT"] == "PASS"
        assert consumer_malformed_values["SEMANTIC_KEY_CARDINALITY_CHECK"] == "FAIL"

        blocked = base_result()
        blocked["git_head"] = None
        blocked["preflight"] = {
            "preflight_ok": False,
            "git_fetch": False,
            "branch": None,
            "git_clean": None,
            "ahead_behind": None,
            "git_head": None,
            "project_audit": None,
            "signed_composite_sources": {},
        }
        blocked["runs"] = []
        fail_suite(blocked, "preflight blocked")
        preflight_block = build_closeout_values(blocked, result_path, "TEST-HOST")
        assert_exact(preflight_block)
        assert preflight_block["GIT_COMMIT"] == "UNKNOWN"
        assert preflight_block["GIT_CLEAN"] == "UNKNOWN"
        assert preflight_block["PROJECT_AUDIT"] == "NOT_RUN"
        assert preflight_block["PARAMETRIC_GEOMETRY"] == "NOT_RUN"
        assert preflight_block["P0_STAGE_GATE"] == "NOT_VERIFIED"

        producer_status_missing = base_result()
        producer_status_missing["runs"][0].pop("capability_status")
        fail_suite(producer_status_missing, "producer capability status missing")
        producer_status_missing_values = build_closeout_values(
            producer_status_missing, result_path, "TEST-HOST"
        )
        assert_exact(producer_status_missing_values)
        assert producer_status_missing_values["PARAMETRIC_GEOMETRY"] == "FAIL"
        assert producer_status_missing_values["WORKBENCH_STEP_IMPORT"] == "FAIL"

        consumer_status_contradiction = base_result()
        consumer_status_contradiction["runs"][1]["capability_status"] = "FAIL"
        fail_suite(consumer_status_contradiction, "consumer capability status contradiction")
        consumer_status_contradiction_values = build_closeout_values(
            consumer_status_contradiction, result_path, "TEST-HOST"
        )
        assert_exact(consumer_status_contradiction_values)
        assert consumer_status_contradiction_values["PARAMETRIC_GEOMETRY"] == "PASS"
        assert consumer_status_contradiction_values["WORKBENCH_STEP_IMPORT"] == "FAIL"

        mutations = []
        value = copy.deepcopy(success); value["TASK"] = "wrong"; mutations.append((value, "AJM005_CLOSEOUT_FIXED_IDENTITY"))
        value = copy.deepcopy(success); value["COMPUTER"] = "bad\rvalue"; mutations.append((value, "AJM005_CLOSEOUT_ASCII_VALUE"))
        value = copy.deepcopy(success); value["COMPUTER"] = "bad\tvalue"; mutations.append((value, "AJM005_CLOSEOUT_ASCII_VALUE"))
        value = copy.deepcopy(success); value["GIT_COMMIT"] = "bad"; mutations.append((value, "AJM005_CLOSEOUT_GIT_COMMIT"))
        value = copy.deepcopy(success); value["GIT_FETCH"] = "FAIL"; mutations.append((value, "AJM005_CLOSEOUT_PREFLIGHT_REACHABILITY"))
        value = copy.deepcopy(success); value["P2_STRUCTURAL_TOOLCHAIN_READINESS"] = "PASS"; mutations.append((value, "AJM005_CLOSEOUT_UNEVALUATED_FIELD"))
        value = copy.deepcopy(success); value["T0_CONTROLS_SOURCE_COMMIT"] = "2" * 40; mutations.append((value, "AJM005_CLOSEOUT_SOURCE_IDENTITY"))
        value = copy.deepcopy(producer_failed); value["WORKBENCH_STEP_IMPORT"] = "PASS"; mutations.append((value, "AJM005_CLOSEOUT_CONSUMER_REACHABILITY"))
        value = copy.deepcopy(success); value.pop("STEP_SHA256"); mutations.append((value, "AJM005_CLOSEOUT_FIELD_SET"))
        for value, code in mutations:
            expect_rejected(value, code)
            negative += 1

    print(
        "AJM005_CLOSEOUT_V2_TESTS=PASS cases=9 fields=%d negative=%d ascii_first_equals=PASS"
        % (len(CLOSEOUT_FIELDS), negative)
    )


if __name__ == "__main__":
    main()

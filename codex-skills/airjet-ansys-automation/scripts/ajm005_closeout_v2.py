#!/usr/bin/env python3
"""Pure, deterministic AJM-005 Phase-B closeout contract.

This module does not launch ANSYS.  It converts already-collected suite and
signed-source observations into one exact ASCII field set and fails closed on
missing evidence.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
from typing import Any


TECHNICAL_ENUM = {"PASS", "FAIL", "NOT_RUN"}
GUI_ENUM = {"PASS", "FAIL", "NOT_VISIBLE"}
READINESS_ENUM = {"PASS", "LIMITED", "BLOCKED", "NOT_EVALUATED"}
SOURCE_IDS = ("t0_controls", "cleanup", "p0")
TASK_VALUE = "AJM-WIN-ANSYS-STUDENT-CAPABILITY-SMOKE-005"
REPORT_CONTRACT_VALUE = "AJM005_ALTERNATE_ROUTE_CLOSEOUT_V2"
SUITE_PASS_VALUE = "PASS_ALTERNATE_ROUTE_SEMANTIC_CONFIRMATION"
SUITE_FAIL_VALUE = "FAIL_ALTERNATE_ROUTE_SEMANTIC_CONFIRMATION"
PRODUCER_PROFILE = "ajm005-spaceclaim-cad-t1-v2"
CONSUMER_PROFILE = "ajm005-workbench-semantic-reconstruction-t1-v2"
NATIVE_SAVE_FIELD = "NATIVE_SAVE"
PRODUCER_REQUIRED_ASSERTIONS = (
    "script_parameterization_equivalent", "named_selections",
    "volume_extract_or_equivalent", "fluid_connectivity", "native_save",
    "native_reopen", "step_export_reimport", "semantic_sidecar",
    "semantic_schema_identity", "semantic_keys_exact",
    "semantic_cardinality_declared", "semantic_topology_nonorphan",
    "detached_sidecar_raw_hash", "artifact_hash_chain",
    "actual_source_files_hashed",
)
CONSUMER_REQUIRED_ASSERTIONS = (
    "predecessor_identity", "legacy_semantic_reconstruction",
    "semantic_sidecar_v2_identity", "semantic_keys_exact",
    "semantic_cardinality", "semantic_geometry_direction",
    "semantic_adjacency", "artifact_hash_chain", "negative_controls",
    "mesh_generation", "project_save",
)
SOURCE_CONTRACTS = {
    "t0_controls": {
        "commit": "92712c7d63f44e1ccafb7a58e8386708b591b287",
        "path": (
            "airjet-simulation/logs/evidence/"
            "AJM005_T0_SUITE_20260714T175525010049Z_2b301826/"
            "suite-summary.json"
        ),
        "sha256": "9ee6a41ca50561e6427950e84e38d9bf039d0b37f090fc0c76c93253cea6891d",
    },
    "cleanup": {
        "commit": "7a93eaa9c8b6c13b5a4f5f03ae2b401945c6b1f8",
        "path": "airjet-simulation/reports/AJM_WIN_ANSYS_STUDENT_CLEANUP_2026-07-14.md",
        "sha256": "1d1087664d3fecc43164dcce2084f8ba3c678da73005fa73def69375900d1f13",
    },
    "p0": {
        "commit": "59e0a296b47f2984606720ec16cf315a0852e625",
        "path": "airjet-simulation/evidence/P0_EVIDENCE_FREEZE_RECORD.md",
        "sha256": "a1a93e1c5e8728e949110c05994b3b1f712a17f7b8889afd10c81e6de9d66456",
    },
}

CLOSEOUT_FIELDS = (
    "TASK",
    "REPORT_CONTRACT",
    "COMPUTER",
    "ANSYS_VERSION",
    "INSTALL_ROOT",
    "GIT_COMMIT",
    "GIT_FETCH",
    "GIT_CLEAN",
    "GIT_AHEAD_BEHIND",
    "PROJECT_AUDIT",
    "OFFICIAL_EXE_SIGNATURES",
    "T0_CONTROLS_SOURCE_COMMIT",
    "T0_CONTROLS_SOURCE_PATH",
    "T0_CONTROLS_SOURCE_BLOB_SHA256",
    "T0_CONTROLS_SOURCE_VALIDATION",
    "T0_ENGINEERING_CAPABILITY",
    "T0_PASS_005_CAPABILITY",
    "T0_P1_P6_GATES",
    "CLEANUP_SOURCE_COMMIT",
    "CLEANUP_SOURCE_PATH",
    "CLEANUP_SOURCE_BLOB_SHA256",
    "CLEANUP_SOURCE_VALIDATION",
    "OLD_PLE_BASELINE",
    "P0_SOURCE_COMMIT",
    "P0_SOURCE_PATH",
    "P0_SOURCE_BLOB_SHA256",
    "P0_SOURCE_VALIDATION",
    "EXECUTION_ROUTE",
    "VISIBILITY",
    "SPACECLAIM_AUTOMATION_CONTROL",
    "WORKBENCH_AUTOMATION_CONTROL",
    "PYMECHANICAL_CONTROL",
    "PYFLUENT_CONTROL",
    "SPACECLAIM_LAUNCH",
    "PARAMETRIC_GEOMETRY",
    "NAMED_SELECTIONS",
    "VOLUME_EXTRACT",
    "FLUID_CONNECTIVITY",
    NATIVE_SAVE_FIELD,
    "STEP_EXPORT_REIMPORT",
    "WORKBENCH_STEP_IMPORT",
    "SOLVER_SEMANTIC_RECONSTRUCTION",
    "SEMANTIC_KEY_CARDINALITY_CHECK",
    "CAD_AUTHORING_ROUTE",
    "SOLVER_HANDOFF_ROUTE",
    "CONNECTED_ROUTE",
    "EXTERNAL_NATIVE_ATTACH",
    "NATIVE_PARAMETERIZATION",
    "NATIVE_NAMED_SELECTION_TRANSFER",
    "STATIC_STRUCTURAL_SOLVE",
    "MODAL_VISIBLE",
    "HARMONIC_VISIBLE",
    "PIEZOELECTRIC_GUI_ROUTE",
    "MODAL_API_ROUTE",
    "HARMONIC_API_ROUTE",
    "PIEZOELECTRIC_API_ROUTE",
    "APDL_COUPLED_FIELD_ROUTE",
    "RESULT_TABLE_EXPORT",
    "SYSTEM_COUPLING_STATUS",
    "CUDSS_STATUS",
    "MECHANICAL_CAPABILITY_RESULT",
    "FLUENT_1_CORE",
    "FLUENT_4_CORE",
    "FLUENT_8_CORE",
    "FLUENT_REPORTED_PROCESS_COUNT",
    "ENERGY",
    "IDEAL_GAS_COMPRESSIBLE",
    "TRANSIENT",
    "DYNAMIC_MESH",
    "SMOOTHING_REMESHING",
    "UDF_OR_PROFILE",
    "CHT_FLUID_SOLID",
    "WATERTIGHT_MESHING",
    "MINIMAL_FLOW_SOLVE",
    "MINIMAL_FLOW_MASS_BALANCE",
    "OBSERVED_STUDENT_LIMITS",
    "FLUENT_CAPABILITY_RESULT",
    "P0_STAGE_GATE",
    "P1_STAGE_GATE",
    "P2_STAGE_GATE",
    "P3_STAGE_GATE",
    "P4_STAGE_GATE",
    "P5_STAGE_GATE",
    "P6_STAGE_GATE",
    "P1_CAD_TOOLCHAIN_SCOPE",
    "P1_CAD_TOOLCHAIN_READINESS",
    "P2_STRUCTURAL_TOOLCHAIN_READINESS",
    "P3_TRANSIENT_CFD_TOOLCHAIN_READINESS",
    "P4_AIRFLOW_LOCAL_DEBUG_READINESS",
    "P5_CHT_LOCAL_DEBUG_READINESS",
    "SUITE_STATUS",
    "SUITE_RESULT_PATH",
    "SUITE_RESULT_SHA256",
    "PRODUCER_REPORT_SHA256",
    "CONSUMER_REPORT_SHA256",
    "STEP_SHA256",
    "ERROR_MESSAGES",
    "FINAL_TECHNICAL_RECOMMENDATION",
    "STUDENT_TOOLCHAIN_STATUS",
)

TECHNICAL_FIELDS = {
    "SPACECLAIM_AUTOMATION_CONTROL",
    "WORKBENCH_AUTOMATION_CONTROL",
    "PYMECHANICAL_CONTROL",
    "PYFLUENT_CONTROL",
    "SPACECLAIM_LAUNCH",
    "PARAMETRIC_GEOMETRY",
    "NAMED_SELECTIONS",
    "VOLUME_EXTRACT",
    "FLUID_CONNECTIVITY",
    NATIVE_SAVE_FIELD,
    "STEP_EXPORT_REIMPORT",
    "WORKBENCH_STEP_IMPORT",
    "SOLVER_SEMANTIC_RECONSTRUCTION",
    "SEMANTIC_KEY_CARDINALITY_CHECK",
    "STATIC_STRUCTURAL_SOLVE",
    "MODAL_API_ROUTE",
    "HARMONIC_API_ROUTE",
    "PIEZOELECTRIC_API_ROUTE",
    "APDL_COUPLED_FIELD_ROUTE",
    "RESULT_TABLE_EXPORT",
    "FLUENT_1_CORE",
    "FLUENT_4_CORE",
    "FLUENT_8_CORE",
    "ENERGY",
    "IDEAL_GAS_COMPRESSIBLE",
    "TRANSIENT",
    "DYNAMIC_MESH",
    "SMOOTHING_REMESHING",
    "UDF_OR_PROFILE",
    "CHT_FLUID_SOLID",
    "WATERTIGHT_MESHING",
    "MINIMAL_FLOW_SOLVE",
}
GUI_FIELDS = {"MODAL_VISIBLE", "HARMONIC_VISIBLE", "PIEZOELECTRIC_GUI_ROUTE"}
READINESS_FIELDS = {
    "P1_CAD_TOOLCHAIN_READINESS",
    "P2_STRUCTURAL_TOOLCHAIN_READINESS",
    "P3_TRANSIENT_CFD_TOOLCHAIN_READINESS",
    "P4_AIRFLOW_LOCAL_DEBUG_READINESS",
    "P5_CHT_LOCAL_DEBUG_READINESS",
}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _fact(value: Any, unavailable: str = "UNKNOWN") -> str:
    return str(value) if value not in (None, "") else unavailable


def _source_value(source: dict[str, Any], key: str) -> str:
    return _fact(source.get(key), "NOT_VERIFIED")


def _source_is_valid(source_id: str, source: dict[str, Any]) -> bool:
    expected = SOURCE_CONTRACTS[source_id]
    if (
        source.get("validation") != "PASS"
        or source.get("source_commit") != expected["commit"]
        or source.get("source_path") != expected["path"]
        or source.get("source_blob_sha256") != expected["sha256"]
    ):
        return False
    if source_id == "t0_controls":
        return (
            source.get("suite_status") == "PASS_CONTROL_SET"
            and source.get("engineering_capability") == "NOT_RUN"
            and source.get("pass_005_capability") == "NOT_EVALUATED_T0_ONLY"
            and source.get("p1_p6_gates") == "NOT_RUN"
        )
    if source_id == "cleanup":
        return (
            source.get("cleanup_status") == "PASS"
            and source.get("official_exe_signatures") == "PASS"
        )
    return source.get("p0_stage_gate") == "PASS"


def _git_divergence(value: Any) -> str:
    if not isinstance(value, str):
        return "UNKNOWN"
    match = re.fullmatch(r"(\d+)\s+(\d+)", value.strip())
    if not match:
        return "UNKNOWN"
    return f"{match.group(1)}_AHEAD_{match.group(2)}_BEHIND"


def _state_sha(run: dict[str, Any], key: str) -> str:
    value = run.get(key)
    return value if isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) else "NOT_VERIFIED"


def _git_commit(value: Any) -> str:
    return value if isinstance(value, str) and re.fullmatch(r"[0-9a-f]{40}", value) else "UNKNOWN"


def _run_attempted(run: dict[str, Any] | None) -> bool:
    """A submitted, reached, or job-bearing record proves work was attempted."""

    if not isinstance(run, dict):
        return False
    if run.get("submitted") is True or run.get("reached_terminal") is True:
        return True
    state = run.get("final_state")
    return isinstance(state, dict) and bool(state.get("job_id"))


def _run_reached_terminal(run: dict[str, Any] | None) -> bool:
    """Require the explicit reachability bit and a recognized terminal phase."""

    if not isinstance(run, dict) or run.get("reached_terminal") is not True:
        return False
    state = run.get("final_state")
    return bool(
        isinstance(state, dict)
        and state.get("phase") in {
            "PROCESS_EXITED_0", "PROCESS_EXITED_NONZERO", "FAILED_START",
            "FAILED_PROCESS", "FAILED_OUTPUT_VALIDATION", "CANCELLED",
        }
        and isinstance(state.get("job_id"), str)
        and state.get("job_id")
    )


def _capability_record_is_consistent(run: dict[str, Any] | None) -> bool:
    """Lock NOT_RUN to never-submitted work and PASS/FAIL to attempted work."""

    if not isinstance(run, dict):
        return True
    attempted = _run_attempted(run)
    status = run.get("capability_status")
    capability_pass = run.get("capability_pass")
    if not attempted:
        return (
            run.get("submitted") is False
            and run.get("reached_terminal") is False
            and status == "NOT_RUN"
            and capability_pass is False
        )
    if run.get("submitted") is not True or status not in {"PASS", "FAIL"}:
        return False
    return capability_pass is (status == "PASS")


def _report_proven(
    run: dict[str, Any] | None,
    profile_id: str,
    case_id: Any,
    expected_status: str,
) -> bool:
    if (
        not _run_attempted(run)
        or not _capability_record_is_consistent(run)
        or not _run_reached_terminal(run)
    ):
        return False
    state = run.get("final_state")
    report = run.get("declared_report")
    return bool(
        run.get("profile_id") == profile_id
        and isinstance(case_id, str)
        and run.get("case_id") == case_id
        and isinstance(state, dict)
        and state.get("phase") == "PROCESS_EXITED_0"
        and state.get("profile_id") == profile_id
        and state.get("case_id") == case_id
        and isinstance(state.get("job_id"), str)
        and isinstance(report, dict)
        and report.get("status") == expected_status
        and report.get("engineering_capability") == expected_status
        and re.fullmatch(r"[0-9a-f]{64}", str(run.get("declared_report_sha256", "")))
    )


def _assertion_status(
    run: dict[str, Any] | None,
    profile_id: str,
    case_id: Any,
    expected_status: str,
    container: str,
    required: tuple[str, ...],
) -> str:
    """Return only what the reached report proves; absence is NOT_RUN."""

    if not _run_attempted(run):
        return "NOT_RUN"
    if not _report_proven(run, profile_id, case_id, expected_status):
        return "FAIL"
    report = run["declared_report"]
    assertions = report.get(container)
    if not isinstance(assertions, dict) or any(name not in assertions for name in required):
        return "FAIL"
    values = [assertions[name] for name in required]
    if any(value is not True and value is not False for value in values):
        return "FAIL"
    return "PASS" if all(values) else "FAIL"


def _producer_is_proven(run: dict[str, Any] | None, case_id: Any) -> bool:
    expected = "PASS_PARTIAL_CAD_CAPABILITY"
    if (
        not _report_proven(run, PRODUCER_PROFILE, case_id, expected)
        or run.get("capability_pass") is not True
        or run.get("capability_status") != "PASS"
    ):
        return False
    report = run["declared_report"]
    assertions = report.get("assertions")
    return (
        report.get("status") == "PASS_PARTIAL_CAD_CAPABILITY"
        and report.get("engineering_capability") == "PASS_PARTIAL_CAD_CAPABILITY"
        and isinstance(assertions, dict)
        and all(assertions.get(name) is True for name in PRODUCER_REQUIRED_ASSERTIONS)
    )


def _consumer_is_proven(
    run: dict[str, Any] | None, producer_proven: bool, case_id: Any
) -> bool:
    expected = "PASS_ALTERNATE_ROUTE_SEMANTIC_RECONSTRUCTION"
    if (
        not producer_proven
        or not _report_proven(run, CONSUMER_PROFILE, case_id, expected)
        or run.get("capability_pass") is not True
        or run.get("capability_status") != "PASS"
    ):
        return False
    report = run["declared_report"]
    assertions = report.get("alternate_route_assertions")
    return (
        report.get("status") == expected
        and report.get("engineering_capability") == expected
        and isinstance(assertions, dict)
        and all(assertions.get(name) is True for name in CONSUMER_REQUIRED_ASSERTIONS)
    )


def build_closeout_values(
    result: dict[str, Any], result_path: Path, computer: str | None = None
) -> dict[str, str]:
    preflight = result.get("preflight") if isinstance(result.get("preflight"), dict) else {}
    sources = preflight.get("signed_composite_sources")
    sources = sources if isinstance(sources, dict) else {}
    t0 = sources.get("t0_controls") if isinstance(sources.get("t0_controls"), dict) else {}
    cleanup = sources.get("cleanup") if isinstance(sources.get("cleanup"), dict) else {}
    p0 = sources.get("p0") if isinstance(sources.get("p0"), dict) else {}
    t0_ok = _source_is_valid("t0_controls", t0)
    cleanup_ok = _source_is_valid("cleanup", cleanup)
    p0_ok = _source_is_valid("p0", p0)
    runs = result.get("runs") if isinstance(result.get("runs"), list) else []
    producer_run = runs[0] if len(runs) > 0 and isinstance(runs[0], dict) else None
    consumer_run = runs[1] if len(runs) > 1 and isinstance(runs[1], dict) else None
    case_id = result.get("case_id")
    preflight_head = _git_commit(preflight.get("git_head"))
    result_head = _git_commit(result.get("git_head"))
    preflight_ok = bool(
        preflight.get("preflight_ok") is True
        and preflight.get("git_fetch") is True
        and preflight.get("branch") == "main"
        and preflight.get("git_clean") is True
        and preflight.get("ahead_behind") == "0\t0"
        and preflight.get("project_audit") is True
        and preflight_head != "UNKNOWN"
        and preflight_head == result_head
        and t0_ok
        and cleanup_ok
        and p0_ok
    )
    producer_proven = preflight_ok and _producer_is_proven(producer_run, case_id)
    consumer_proven = _consumer_is_proven(consumer_run, producer_proven, case_id)

    producer_fields = {
        "PARAMETRIC_GEOMETRY": ("script_parameterization_equivalent",),
        "NAMED_SELECTIONS": ("named_selections",),
        "VOLUME_EXTRACT": ("volume_extract_or_equivalent",),
        "FLUID_CONNECTIVITY": ("fluid_connectivity",),
        NATIVE_SAVE_FIELD: ("native_save", "native_reopen"),
        "STEP_EXPORT_REIMPORT": (
            "step_export_reimport",
            "semantic_sidecar",
            "semantic_schema_identity",
            "semantic_keys_exact",
            "semantic_cardinality_declared",
            "semantic_topology_nonorphan",
            "detached_sidecar_raw_hash",
            "artifact_hash_chain",
            "actual_source_files_hashed",
        ),
    }
    producer_status = dict(
        (
            field,
            _assertion_status(
                producer_run,
                PRODUCER_PROFILE,
                case_id,
                "PASS_PARTIAL_CAD_CAPABILITY",
                "assertions",
                assertions,
            ),
        )
        for field, assertions in producer_fields.items()
    )
    consumer_fields = {
        "WORKBENCH_STEP_IMPORT": (
            "predecessor_identity",
            "legacy_semantic_reconstruction",
            "artifact_hash_chain",
            "mesh_generation",
            "project_save",
        ),
        "SOLVER_SEMANTIC_RECONSTRUCTION": (
            "semantic_sidecar_v2_identity",
            "semantic_geometry_direction",
            "semantic_adjacency",
            "artifact_hash_chain",
            "negative_controls",
        ),
        "SEMANTIC_KEY_CARDINALITY_CHECK": (
            "semantic_keys_exact",
            "semantic_cardinality",
        ),
    }
    consumer_status = dict(
        (
            field,
            _assertion_status(
                consumer_run,
                CONSUMER_PROFILE,
                case_id,
                "PASS_ALTERNATE_ROUTE_SEMANTIC_RECONSTRUCTION",
                "alternate_route_assertions",
                assertions,
            )
            if producer_proven
            else ("FAIL" if _run_attempted(consumer_run) else "NOT_RUN"),
        )
        for field, assertions in consumer_fields.items()
    )

    producer_report = (
        producer_run.get("declared_report", {})
        if _report_proven(
            producer_run, PRODUCER_PROFILE, case_id, "PASS_PARTIAL_CAD_CAPABILITY"
        ) else {}
    )
    producer_report_sha = (
        _state_sha(producer_run, "declared_report_sha256")
        if _report_proven(
            producer_run, PRODUCER_PROFILE, case_id, "PASS_PARTIAL_CAD_CAPABILITY"
        ) else "NOT_VERIFIED"
    )
    consumer_report_sha = (
        _state_sha(consumer_run, "declared_report_sha256")
        if producer_proven and _report_proven(
            consumer_run,
            CONSUMER_PROFILE,
            case_id,
            "PASS_ALTERNATE_ROUTE_SEMANTIC_RECONSTRUCTION",
        ) else "NOT_VERIFIED"
    )
    step_sha = _state_sha(
        producer_report.get("files", {}).get("step", {})
        if isinstance(producer_report.get("files"), dict) else {},
        "sha256",
    )
    suite_result_sha = _sha256_file(result_path) if result_path.is_file() else "NOT_VERIFIED"

    result_identity_ok = (
        result.get("task") == TASK_VALUE
        and result.get("suite") == "alternate_step_semantic_confirmation_v2"
        and result.get("p1_cad_toolchain_scope") == "ALTERNATE_ROUTE_ONLY"
        and result.get("cad_authoring_route") == "SPACECLAIM_SIGNED_SCRIPT_PARAMETRIC"
        and result.get("solver_handoff_route") == "HASH_BOUND_STEP_SEMANTIC_SIDECAR"
        and result.get("external_native_attach") == "NOT_PROVEN"
        and result.get("native_parameterization") == "NOT_PROVEN"
        and result.get("native_named_selection_transfer") == "NOT_PROVEN"
        and result.get("p1_stage_gate") == "NOT_RUN"
        and result.get("p1_p6_gates") == "NOT_RUN"
        and result.get("visibility") == "NOT_USER_OBSERVED"
        and result.get("license_data_read") is False
        and result.get("p1_cad_toolchain_readiness") == "PASS"
        and len(runs) == 2
        and runs[0] is producer_run
        and runs[1] is consumer_run
    )
    phase_fields_pass = all(
        status == "PASS"
        for status in list(producer_status.values()) + list(consumer_status.values())
    )
    passed = bool(
        preflight_ok
        and result_identity_ok
        and result.get("suite_status") == SUITE_PASS_VALUE
        and producer_proven
        and consumer_proven
        and phase_fields_pass
        and result.get("error") in (None, "")
        and all(
            re.fullmatch(r"[0-9a-f]{64}", value)
            for value in (
                suite_result_sha, producer_report_sha, consumer_report_sha, step_sha
            )
        )
    )
    t0_control = "PASS" if t0_ok else "NOT_RUN"
    raw_error = result.get("error")
    if raw_error:
        error_messages = json.dumps(
            raw_error, ensure_ascii=True, sort_keys=True, separators=(",", ":")
        )
    elif passed:
        error_messages = ""
    else:
        error_messages = '{"message":"UNPROVEN_OR_FAILED_PHASE_B"}'

    values: dict[str, str] = {
        "TASK": TASK_VALUE,
        "REPORT_CONTRACT": REPORT_CONTRACT_VALUE,
        "COMPUTER": computer or os.environ.get("COMPUTERNAME", "UNKNOWN"),
        "ANSYS_VERSION": "2026 R1 v261" if cleanup_ok else "UNKNOWN",
        "INSTALL_ROOT": r"D:\ansys\ANSYS Inc\ANSYS Student\v261" if cleanup_ok else "UNKNOWN",
        "GIT_COMMIT": result_head,
        "GIT_FETCH": "PASS" if preflight.get("git_fetch") is True else ("FAIL" if preflight.get("git_fetch") is False else "UNKNOWN"),
        "GIT_CLEAN": "TRUE" if preflight.get("git_clean") is True else ("FALSE" if preflight.get("git_clean") is False else "UNKNOWN"),
        "GIT_AHEAD_BEHIND": _git_divergence(preflight.get("ahead_behind")),
        "PROJECT_AUDIT": "PASS" if preflight.get("project_audit") is True else ("FAIL" if preflight.get("project_audit") is False else "NOT_RUN"),
        "OFFICIAL_EXE_SIGNATURES": "PASS" if cleanup_ok else "NOT_VERIFIED",
        "T0_CONTROLS_SOURCE_COMMIT": _source_value(t0, "source_commit"),
        "T0_CONTROLS_SOURCE_PATH": _source_value(t0, "source_path"),
        "T0_CONTROLS_SOURCE_BLOB_SHA256": _source_value(t0, "source_blob_sha256"),
        "T0_CONTROLS_SOURCE_VALIDATION": "PASS" if t0_ok else "FAIL",
        "T0_ENGINEERING_CAPABILITY": _source_value(t0, "engineering_capability"),
        "T0_PASS_005_CAPABILITY": _source_value(t0, "pass_005_capability"),
        "T0_P1_P6_GATES": _source_value(t0, "p1_p6_gates"),
        "CLEANUP_SOURCE_COMMIT": _source_value(cleanup, "source_commit"),
        "CLEANUP_SOURCE_PATH": _source_value(cleanup, "source_path"),
        "CLEANUP_SOURCE_BLOB_SHA256": _source_value(cleanup, "source_blob_sha256"),
        "CLEANUP_SOURCE_VALIDATION": "PASS" if cleanup_ok else "FAIL",
        "OLD_PLE_BASELINE": "CLEAN" if cleanup_ok else "NOT_VERIFIED",
        "P0_SOURCE_COMMIT": _source_value(p0, "source_commit"),
        "P0_SOURCE_PATH": _source_value(p0, "source_path"),
        "P0_SOURCE_BLOB_SHA256": _source_value(p0, "source_blob_sha256"),
        "P0_SOURCE_VALIDATION": "PASS" if p0_ok else "FAIL",
        "EXECUTION_ROUTE": "OFFICIAL_API",
        "VISIBILITY": "NOT_USER_OBSERVED",
        "SPACECLAIM_AUTOMATION_CONTROL": t0_control,
        "WORKBENCH_AUTOMATION_CONTROL": t0_control,
        "PYMECHANICAL_CONTROL": t0_control,
        "PYFLUENT_CONTROL": t0_control,
        "SPACECLAIM_LAUNCH": t0_control,
        "PARAMETRIC_GEOMETRY": producer_status["PARAMETRIC_GEOMETRY"],
        "NAMED_SELECTIONS": producer_status["NAMED_SELECTIONS"],
        "VOLUME_EXTRACT": producer_status["VOLUME_EXTRACT"],
        "FLUID_CONNECTIVITY": producer_status["FLUID_CONNECTIVITY"],
        NATIVE_SAVE_FIELD: producer_status[NATIVE_SAVE_FIELD],
        "STEP_EXPORT_REIMPORT": producer_status["STEP_EXPORT_REIMPORT"],
        "WORKBENCH_STEP_IMPORT": consumer_status["WORKBENCH_STEP_IMPORT"],
        "SOLVER_SEMANTIC_RECONSTRUCTION": consumer_status["SOLVER_SEMANTIC_RECONSTRUCTION"],
        "SEMANTIC_KEY_CARDINALITY_CHECK": consumer_status["SEMANTIC_KEY_CARDINALITY_CHECK"],
        "CAD_AUTHORING_ROUTE": "SPACECLAIM_SIGNED_SCRIPT_PARAMETRIC",
        "SOLVER_HANDOFF_ROUTE": "HASH_BOUND_STEP_SEMANTIC_SIDECAR",
        "CONNECTED_ROUTE": "DEFERRED_CURRENT_HOST_ROUTE",
        "EXTERNAL_NATIVE_ATTACH": "NOT_PROVEN",
        "NATIVE_PARAMETERIZATION": "NOT_PROVEN",
        "NATIVE_NAMED_SELECTION_TRANSFER": "NOT_PROVEN",
        "STATIC_STRUCTURAL_SOLVE": "NOT_RUN",
        "MODAL_VISIBLE": "NOT_VISIBLE",
        "HARMONIC_VISIBLE": "NOT_VISIBLE",
        "PIEZOELECTRIC_GUI_ROUTE": "NOT_VISIBLE",
        "MODAL_API_ROUTE": "NOT_RUN",
        "HARMONIC_API_ROUTE": "NOT_RUN",
        "PIEZOELECTRIC_API_ROUTE": "NOT_RUN",
        "APDL_COUPLED_FIELD_ROUTE": "NOT_RUN",
        "RESULT_TABLE_EXPORT": "NOT_RUN",
        "SYSTEM_COUPLING_STATUS": "UNVERIFIED_WARNING",
        "CUDSS_STATUS": "UNVERIFIED_WARNING",
        "MECHANICAL_CAPABILITY_RESULT": "NOT_EVALUATED",
        "FLUENT_1_CORE": "NOT_RUN",
        "FLUENT_4_CORE": "NOT_RUN",
        "FLUENT_8_CORE": "NOT_RUN",
        "FLUENT_REPORTED_PROCESS_COUNT": "NOT_EVALUATED",
        "ENERGY": "NOT_RUN",
        "IDEAL_GAS_COMPRESSIBLE": "NOT_RUN",
        "TRANSIENT": "NOT_RUN",
        "DYNAMIC_MESH": "NOT_RUN",
        "SMOOTHING_REMESHING": "NOT_RUN",
        "UDF_OR_PROFILE": "NOT_RUN",
        "CHT_FLUID_SOLID": "NOT_RUN",
        "WATERTIGHT_MESHING": "NOT_RUN",
        "MINIMAL_FLOW_SOLVE": "NOT_RUN",
        "MINIMAL_FLOW_MASS_BALANCE": "NOT_EVALUATED",
        "OBSERVED_STUDENT_LIMITS": "NOT_EVALUATED",
        "FLUENT_CAPABILITY_RESULT": "NOT_EVALUATED",
        "P0_STAGE_GATE": "PASS" if p0_ok else "NOT_VERIFIED",
        "P1_STAGE_GATE": "NOT_RUN",
        "P2_STAGE_GATE": "NOT_RUN",
        "P3_STAGE_GATE": "NOT_RUN",
        "P4_STAGE_GATE": "NOT_RUN",
        "P5_STAGE_GATE": "NOT_RUN",
        "P6_STAGE_GATE": "NOT_RUN",
        "P1_CAD_TOOLCHAIN_SCOPE": "ALTERNATE_ROUTE_ONLY",
        "P1_CAD_TOOLCHAIN_READINESS": "PASS" if passed else "BLOCKED",
        "P2_STRUCTURAL_TOOLCHAIN_READINESS": "NOT_EVALUATED",
        "P3_TRANSIENT_CFD_TOOLCHAIN_READINESS": "NOT_EVALUATED",
        "P4_AIRFLOW_LOCAL_DEBUG_READINESS": "NOT_EVALUATED",
        "P5_CHT_LOCAL_DEBUG_READINESS": "NOT_EVALUATED",
        "SUITE_STATUS": SUITE_PASS_VALUE if passed else SUITE_FAIL_VALUE,
        "SUITE_RESULT_PATH": str(result_path.resolve()),
        "SUITE_RESULT_SHA256": suite_result_sha,
        "PRODUCER_REPORT_SHA256": producer_report_sha,
        "CONSUMER_REPORT_SHA256": consumer_report_sha,
        "STEP_SHA256": step_sha,
        "ERROR_MESSAGES": error_messages,
        "FINAL_TECHNICAL_RECOMMENDATION": "START_006_ALTERNATE_ROUTE_ONLY" if passed else "DO_NOT_START_006",
        "STUDENT_TOOLCHAIN_STATUS": "PASS_START_P1" if passed else "BLOCKED_TECHNICAL_FAILURE",
    }
    validate_closeout_values(values)
    return values


def validate_closeout_values(values: dict[str, str]) -> None:
    if tuple(values) != CLOSEOUT_FIELDS or set(values) != set(CLOSEOUT_FIELDS):
        raise ValueError("AJM005_CLOSEOUT_FIELD_SET")
    if any(
        not isinstance(value, str)
        or "\r" in value
        or "\n" in value
        or any(ord(character) < 32 or ord(character) == 127 or ord(character) > 127 for character in value)
        for value in values.values()
    ):
        raise ValueError("AJM005_CLOSEOUT_ASCII_VALUE")
    fixed = {
        "TASK": TASK_VALUE,
        "REPORT_CONTRACT": REPORT_CONTRACT_VALUE,
        "EXECUTION_ROUTE": "OFFICIAL_API",
        "VISIBILITY": "NOT_USER_OBSERVED",
        "CAD_AUTHORING_ROUTE": "SPACECLAIM_SIGNED_SCRIPT_PARAMETRIC",
        "SOLVER_HANDOFF_ROUTE": "HASH_BOUND_STEP_SEMANTIC_SIDECAR",
        "CONNECTED_ROUTE": "DEFERRED_CURRENT_HOST_ROUTE",
        "P1_CAD_TOOLCHAIN_SCOPE": "ALTERNATE_ROUTE_ONLY",
    }
    if any(values[field] != expected for field, expected in fixed.items()):
        raise ValueError("AJM005_CLOSEOUT_FIXED_IDENTITY")
    if values["GIT_COMMIT"] != "UNKNOWN" and not re.fullmatch(
        r"[0-9a-f]{40}", values["GIT_COMMIT"]
    ):
        raise ValueError("AJM005_CLOSEOUT_GIT_COMMIT")
    if values["GIT_FETCH"] not in {"PASS", "FAIL", "UNKNOWN"}:
        raise ValueError("AJM005_CLOSEOUT_GIT_FETCH_ENUM")
    if values["GIT_CLEAN"] not in {"TRUE", "FALSE", "UNKNOWN"}:
        raise ValueError("AJM005_CLOSEOUT_GIT_CLEAN_ENUM")
    if values["GIT_AHEAD_BEHIND"] != "UNKNOWN" and not re.fullmatch(
        r"\d+_AHEAD_\d+_BEHIND", values["GIT_AHEAD_BEHIND"]
    ):
        raise ValueError("AJM005_CLOSEOUT_GIT_DIVERGENCE")
    if values["PROJECT_AUDIT"] not in {"PASS", "FAIL", "NOT_RUN"}:
        raise ValueError("AJM005_CLOSEOUT_AUDIT_ENUM")
    if any(values[field] not in TECHNICAL_ENUM for field in TECHNICAL_FIELDS):
        raise ValueError("AJM005_CLOSEOUT_TECHNICAL_ENUM")
    if any(values[field] not in GUI_ENUM for field in GUI_FIELDS):
        raise ValueError("AJM005_CLOSEOUT_GUI_ENUM")
    if any(values[field] not in READINESS_ENUM for field in READINESS_FIELDS):
        raise ValueError("AJM005_CLOSEOUT_READINESS_ENUM")
    if values["P0_STAGE_GATE"] not in {"PASS", "NOT_VERIFIED"}:
        raise ValueError("AJM005_CLOSEOUT_P0_ENUM")
    if any(values[f"P{stage}_STAGE_GATE"] != "NOT_RUN" for stage in range(1, 7)):
        raise ValueError("AJM005_CLOSEOUT_GATE_BOUNDARY")
    if any(
        values[field] != "NOT_PROVEN"
        for field in (
            "EXTERNAL_NATIVE_ATTACH",
            "NATIVE_PARAMETERIZATION",
            "NATIVE_NAMED_SELECTION_TRANSFER",
        )
    ):
        raise ValueError("AJM005_CLOSEOUT_NATIVE_BOUNDARY")
    for source_id, prefix in (
        ("t0_controls", "T0_CONTROLS"),
        ("cleanup", "CLEANUP"),
        ("p0", "P0"),
    ):
        validation = values[prefix + "_SOURCE_VALIDATION"]
        if validation not in {"PASS", "FAIL"}:
            raise ValueError("AJM005_CLOSEOUT_SOURCE_VALIDATION_ENUM")
        commit = values[prefix + "_SOURCE_COMMIT"]
        path = values[prefix + "_SOURCE_PATH"]
        blob_sha = values[prefix + "_SOURCE_BLOB_SHA256"]
        if validation == "PASS":
            expected = SOURCE_CONTRACTS[source_id]
            if (
                not re.fullmatch(r"[0-9a-f]{40}", commit)
                or not re.fullmatch(r"[0-9a-f]{64}", blob_sha)
                or commit != expected["commit"]
                or path != expected["path"]
                or blob_sha != expected["sha256"]
            ):
                raise ValueError("AJM005_CLOSEOUT_SOURCE_IDENTITY")
        elif (
            commit != "NOT_VERIFIED" and not re.fullmatch(r"[0-9a-f]{40}", commit)
        ) or (
            blob_sha != "NOT_VERIFIED" and not re.fullmatch(r"[0-9a-f]{64}", blob_sha)
        ):
            raise ValueError("AJM005_CLOSEOUT_SOURCE_FORMAT")
    if values["SUITE_STATUS"] not in {SUITE_PASS_VALUE, SUITE_FAIL_VALUE}:
        raise ValueError("AJM005_CLOSEOUT_SUITE_STATUS")
    for field in (
        "SUITE_RESULT_SHA256",
        "PRODUCER_REPORT_SHA256",
        "CONSUMER_REPORT_SHA256",
        "STEP_SHA256",
    ):
        if values[field] != "NOT_VERIFIED" and not re.fullmatch(r"[0-9a-f]{64}", values[field]):
            raise ValueError("AJM005_CLOSEOUT_REPORT_SHA256")
    if not os.path.isabs(values["SUITE_RESULT_PATH"]):
        raise ValueError("AJM005_CLOSEOUT_RESULT_PATH")
    if any(
        values[field] != "NOT_RUN"
        for field in {
            "STATIC_STRUCTURAL_SOLVE", "MODAL_API_ROUTE", "HARMONIC_API_ROUTE",
            "PIEZOELECTRIC_API_ROUTE", "APDL_COUPLED_FIELD_ROUTE", "RESULT_TABLE_EXPORT",
            "FLUENT_1_CORE", "FLUENT_4_CORE", "FLUENT_8_CORE", "ENERGY",
            "IDEAL_GAS_COMPRESSIBLE", "TRANSIENT", "DYNAMIC_MESH",
            "SMOOTHING_REMESHING", "UDF_OR_PROFILE", "CHT_FLUID_SOLID",
            "WATERTIGHT_MESHING", "MINIMAL_FLOW_SOLVE",
        }
    ):
        raise ValueError("AJM005_CLOSEOUT_UNRUN_TECHNICAL")
    if any(values[field] != "NOT_VISIBLE" for field in GUI_FIELDS):
        raise ValueError("AJM005_CLOSEOUT_UNRUN_GUI")
    if any(
        values[field] != "NOT_EVALUATED"
        for field in {
            "MECHANICAL_CAPABILITY_RESULT", "FLUENT_REPORTED_PROCESS_COUNT", "MINIMAL_FLOW_MASS_BALANCE",
            "OBSERVED_STUDENT_LIMITS", "FLUENT_CAPABILITY_RESULT",
            "P2_STRUCTURAL_TOOLCHAIN_READINESS", "P3_TRANSIENT_CFD_TOOLCHAIN_READINESS",
            "P4_AIRFLOW_LOCAL_DEBUG_READINESS", "P5_CHT_LOCAL_DEBUG_READINESS",
        }
    ):
        raise ValueError("AJM005_CLOSEOUT_UNEVALUATED_FIELD")
    if (
        values["SYSTEM_COUPLING_STATUS"] != "UNVERIFIED_WARNING"
        or values["CUDSS_STATUS"] != "UNVERIFIED_WARNING"
    ):
        raise ValueError("AJM005_CLOSEOUT_WARNING_ENUM")
    producer_phase_fields = set((
        "PARAMETRIC_GEOMETRY", "NAMED_SELECTIONS", "VOLUME_EXTRACT",
        "FLUID_CONNECTIVITY", NATIVE_SAVE_FIELD, "STEP_EXPORT_REIMPORT",
    ))
    consumer_phase_fields = {
        "WORKBENCH_STEP_IMPORT", "SOLVER_SEMANTIC_RECONSTRUCTION",
        "SEMANTIC_KEY_CARDINALITY_CHECK",
    }
    git_preflight_pass = (
        values["GIT_COMMIT"] != "UNKNOWN"
        and values["GIT_FETCH"] == "PASS"
        and values["GIT_CLEAN"] == "TRUE"
        and values["GIT_AHEAD_BEHIND"] == "0_AHEAD_0_BEHIND"
        and values["PROJECT_AUDIT"] == "PASS"
    )
    if not git_preflight_pass and any(
        values[field] == "PASS" for field in producer_phase_fields | consumer_phase_fields
    ):
        raise ValueError("AJM005_CLOSEOUT_PREFLIGHT_REACHABILITY")
    if any(values[field] != "PASS" for field in producer_phase_fields) and any(
        values[field] == "PASS" for field in consumer_phase_fields
    ):
        raise ValueError("AJM005_CLOSEOUT_CONSUMER_REACHABILITY")
    if values["STUDENT_TOOLCHAIN_STATUS"] == "PASS_START_P1":
        pass_implications = (
            values["P1_CAD_TOOLCHAIN_READINESS"] == "PASS"
            and values["SUITE_STATUS"] == SUITE_PASS_VALUE
            and git_preflight_pass
            and values["OFFICIAL_EXE_SIGNATURES"] == "PASS"
            and values["OLD_PLE_BASELINE"] == "CLEAN"
            and values["P0_STAGE_GATE"] == "PASS"
            and all(values[prefix + "_SOURCE_VALIDATION"] == "PASS" for prefix in ("T0_CONTROLS", "CLEANUP", "P0"))
            and all(values[field] == "PASS" for field in producer_phase_fields | consumer_phase_fields)
            and all(values[field] == "PASS" for field in (
                "SPACECLAIM_AUTOMATION_CONTROL", "WORKBENCH_AUTOMATION_CONTROL",
                "PYMECHANICAL_CONTROL", "PYFLUENT_CONTROL", "SPACECLAIM_LAUNCH",
            ))
            and all(re.fullmatch(r"[0-9a-f]{64}", values[field]) for field in (
                "SUITE_RESULT_SHA256", "PRODUCER_REPORT_SHA256",
                "CONSUMER_REPORT_SHA256", "STEP_SHA256",
            ))
            and values["ERROR_MESSAGES"] == ""
            and values["FINAL_TECHNICAL_RECOMMENDATION"] == "START_006_ALTERNATE_ROUTE_ONLY"
        )
        if not pass_implications:
            raise ValueError("AJM005_CLOSEOUT_PASS_IMPLICATION")
    elif values["STUDENT_TOOLCHAIN_STATUS"] == "BLOCKED_TECHNICAL_FAILURE":
        if (
            values["P1_CAD_TOOLCHAIN_READINESS"] != "BLOCKED"
            or values["SUITE_STATUS"] != SUITE_FAIL_VALUE
            or values["FINAL_TECHNICAL_RECOMMENDATION"] != "DO_NOT_START_006"
            or not values["ERROR_MESSAGES"]
        ):
            raise ValueError("AJM005_CLOSEOUT_BLOCKED_IMPLICATION")
    else:
        raise ValueError("AJM005_CLOSEOUT_STATUS")


def render_closeout_ascii(values: dict[str, str]) -> bytes:
    validate_closeout_values(values)
    rendered = "".join(f"{field}={values[field]}\n" for field in CLOSEOUT_FIELDS)
    payload = rendered.encode("ascii", "strict")
    if b"\r" in payload:
        raise ValueError("AJM005_CLOSEOUT_CRLF")
    return payload


def parse_closeout_ascii(payload: bytes) -> dict[str, str]:
    """Parse the canonical report by splitting each record at its first equals."""

    if not isinstance(payload, bytes) or b"\r" in payload or not payload.endswith(b"\n"):
        raise ValueError("AJM005_CLOSEOUT_SERIALIZATION")
    try:
        text = payload.decode("ascii", "strict")
    except UnicodeDecodeError:
        raise ValueError("AJM005_CLOSEOUT_SERIALIZATION")
    lines = text[:-1].split("\n")
    if len(lines) != len(CLOSEOUT_FIELDS):
        raise ValueError("AJM005_CLOSEOUT_SERIALIZATION")
    values: dict[str, str] = {}
    for expected_field, line in zip(CLOSEOUT_FIELDS, lines):
        field, separator, value = line.partition("=")
        if separator != "=" or field != expected_field or field in values:
            raise ValueError("AJM005_CLOSEOUT_SERIALIZATION")
        values[field] = value
    validate_closeout_values(values)
    return values

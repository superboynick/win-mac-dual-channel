#!/usr/bin/env python3
"""Run the AJM-005 Workbench-connected SpaceClaim diagnostic through MCP."""

from __future__ import annotations

import asyncio
from contextlib import suppress
from datetime import datetime, timedelta, timezone
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import traceback
from typing import Any
from uuid import uuid4

from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client


EXPECTED_PYTHON = Path(
    r"C:\Users\admin\AppData\Local\AirJetAnsysAutomation\.venv\Scripts\python.exe"
)
SERVER = (
    Path.home()
    / ".codex"
    / "skills"
    / "airjet-ansys-automation"
    / "scripts"
    / "airjet_ansys_mcp.py"
)
REPO = Path(r"C:\Users\admin\win-mac-dual-channel")
RUNNER_GIT_PATH = (
    "codex-skills/airjet-ansys-automation/scripts/"
    "run_t1_connected_spaceclaim_suite.py"
)
OUTPUT_ROOT = Path.home() / "Downloads" / "AIRJET_ANSYS_STUDENT_SMOKE_005"
EXPECTED_TOOLS = {
    "inventory",
    "submit_job",
    "poll_job",
    "cancel_job",
    "artifact_manifest",
}
SC_PROFILE = "ajm005-spaceclaim-cad-t1-v1"
WB_PROFILE = "ajm005-workbench-connected-spaceclaim-t1-v1"
POLL_SECONDS = 1.0
HARD_PROFILE_WAIT_SECONDS = 1500
TERMINAL_PHASES = {
    "PROCESS_EXITED_0",
    "FAILED_PROCESS",
    "TIMED_OUT",
    "CANCELLED",
    "FAILED_TERMINATION",
    "FAILED_MONITOR",
    "FAILED_START",
}
PROFILE_RULES = {
    SC_PROFILE: {
        "probe": "spaceclaim_cad_t1",
        "required_status": "PASS_PARTIAL_CAD_CAPABILITY",
        "report": "spaceclaim_cad_t1.json",
        "artifacts": {
            "spaceclaim_cad_t1.scdocx": "transfer_native",
            "spaceclaim_cad_t1.step": "step",
            "spaceclaim_semantic_sidecar.json": "semantic_sidecar",
        },
        "assertions": {
            "script_parameterization_equivalent",
            "named_selections",
            "volume_extract_or_equivalent",
            "fluid_connectivity",
            "native_save",
            "native_reopen",
            "step_export_reimport",
            "semantic_sidecar",
        },
    },
    WB_PROFILE: {
        "probe": "workbench_connected_spaceclaim_t1",
        "required_status": "PASS_CONNECTED_SPACECLAIM_TRANSFER_DIAGNOSTIC",
        "report": "workbench_connected_spaceclaim_t1.json",
        "artifacts": {
            "connected_spaceclaim_entry.sentinel": "entry_sentinel",
            "connected_spaceclaim_build.json": "connected_build",
            "workbench_connected_inspection.json": "model_inspection",
            "workbench_connected_spaceclaim_t1.wbpj": "project",
        },
        "assertions": {
            "predecessor_control_identity",
            "empty_geometry_cell",
            "connected_editor_build",
            "geometry_transfer",
            "named_selection_transfer",
            "mesh_generation",
            "project_save",
        },
    },
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def norm(path: Path) -> str:
    return os.path.normcase(os.path.abspath(str(path)))


def require_runner_git_blob(head: str) -> str:
    if not re.fullmatch(r"[0-9a-f]{40}", head):
        raise RuntimeError("BLOCKED_INVALID_INVENTORY_GIT_HEAD")
    completed = subprocess.run(
        ["git", "-C", str(REPO), "show", f"{head}:{RUNNER_GIT_PATH}"],
        capture_output=True,
        timeout=30,
        check=False,
        stdin=subprocess.DEVNULL,
    )
    if completed.returncode != 0:
        raise RuntimeError("BLOCKED_T1_CONNECTED_RUNNER_GIT_BLOB_MISSING")
    installed_digest = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    git_digest = hashlib.sha256(completed.stdout).hexdigest()
    if installed_digest != git_digest:
        raise RuntimeError("BLOCKED_T1_CONNECTED_RUNNER_COPY_MISMATCH")
    return installed_digest


def json_from_result(tool_name: str, result: types.CallToolResult) -> dict[str, Any]:
    if result.isError:
        message = " | ".join(
            item.text for item in result.content if isinstance(item, types.TextContent)
        )
        raise RuntimeError(f"MCP_TOOL_ERROR:{tool_name}:{message}")
    if not isinstance(result.structuredContent, dict):
        raise RuntimeError(f"MCP_TOOL_RESULT_MISSING_STRUCTURED_OBJECT:{tool_name}")
    return result.structuredContent


async def call_json(
    session: ClientSession,
    name: str,
    arguments: dict[str, Any] | None = None,
    timeout_seconds: int = 120,
) -> dict[str, Any]:
    result = await session.call_tool(
        name,
        arguments or {},
        read_timeout_seconds=timedelta(seconds=timeout_seconds),
    )
    return json_from_result(name, result)


def manifest_file(
    manifest: dict[str, Any], relative_path: str
) -> dict[str, Any] | None:
    files = manifest.get("files")
    if not isinstance(files, list):
        raise RuntimeError("MANIFEST_FILES_NOT_LIST")
    matches = [
        item
        for item in files
        if isinstance(item, dict) and item.get("relative_path") == relative_path
    ]
    return matches[0] if len(matches) == 1 else None


def report_path_matches(declared: object, artifact: str) -> bool:
    declared_path = str(declared or "").replace("\\", "/").rstrip("/")
    artifact_path = artifact.replace("\\", "/").rstrip("/")
    return declared_path == artifact_path or declared_path.endswith(
        "/" + artifact_path
    )


FILE_DIAGNOSTIC_FIELDS = {
    "schema_version",
    "mode",
    "send_command_control",
    "entry_expected_size",
    "entry_expected_sha256",
    "runscript_call_outcome",
    "entry_exact_at_call_checkpoint",
    "entry_exact_post_exit",
    "entry_exact_failure_pre_cleanup",
    "entry_exact_failure_post_cleanup",
    "entry_exact_at_freeze",
    "entry_first_observed_at",
    "entry_invalid_or_partial_at",
    "entry_probe_errors_at",
    "build_report_probe_errors_at",
    "entry_delayed_or_later_observed",
    "entry_lost_after_checkpoint",
    "build_report_exists_at_freeze",
    "build_report_exists_at_capture",
    "build_report_capture_state",
    "build_report_capture_context",
    "build_report_state",
    "classification",
    "freeze_probe",
}
FILE_CHECKPOINTS = {
    "POST_RUNSCRIPT",
    "POST_EXIT",
    "FAILURE_PRE_CLEANUP",
    "FAILURE_POST_CLEANUP",
}
BUILD_PROBE_CHECKPOINTS = {
    "POST_EXIT",
    "FAILURE_POST_CLEANUP",
    "BUILD_CAPTURE",
}
BUILD_CAPTURE_STATES = {
    "NOT_ATTEMPTED",
    "SKIPPED_PRIOR_PROBE_ERROR",
    "ABSENT",
    "PRESENT_VALID_OBJECT",
    "PRESENT_INVALID_OR_UNREADABLE",
    "EXISTS_PROBE_ERROR",
}
FILE_CLASSIFICATIONS = {
    "RUNSCRIPT_NOT_REACHED",
    "RUNSCRIPT_CALL_EXCEPTION_ENTRY_ABSENT",
    "RUNSCRIPT_CALL_EXCEPTION_ENTRY_EXACT",
    "RUNSCRIPT_CALL_EXCEPTION_ENTRY_DELAYED_OR_CLEANUP_OBSERVED",
    "RUNSCRIPT_RETURNED_ENTRY_ABSENT",
    "RUNSCRIPT_RETURNED_ENTRY_EXACT",
    "ENTRY_DELAYED_OR_POST_EXIT_OBSERVED",
    "ENTRY_LOST_AFTER_CHECKPOINT",
    "ENTRY_SENTINEL_INVALID_OR_PARTIAL",
    "ENTRY_EXACT_BUILD_REPORT_ABSENT",
    "PROBE_INDETERMINATE",
    "BUILD_REPORT_INVALID",
    "BUILD_CONTRACT_FAIL",
    "BUILD_CONTRACT_PASS",
}
FILE_BUILD_STATES = {
    "ABSENT",
    "ENTRY_EXACT_BUILD_REPORT_ABSENT",
    "PRESENT_NOT_VALIDATED",
    "PRESENT_ENTRY_CONTRACT_FAIL",
    "INVALID_OR_UNREADABLE",
    "REPORTED_BUILD_FAIL",
    "CONTRACT_FAIL",
    "CONTRACT_PASS",
    "PROBE_INDETERMINATE",
}


def file_runscript_diagnostic_contract_ok(report: object) -> bool:
    if not isinstance(report, dict):
        return False
    diagnostic = report.get("script_channel_diagnostic")
    reach = report.get("execution_reach")
    if not isinstance(diagnostic, dict) or set(diagnostic) != FILE_DIAGNOSTIC_FIELDS:
        return False
    if not isinstance(reach, dict):
        return False
    if (
        diagnostic.get("schema_version") != 2
        or diagnostic.get("mode") != "INTERACTIVE_TRUE_RUNSCRIPT_ONLY"
        or diagnostic.get("send_command_control") != "SKIPPED_BY_EXPERIMENT"
        or reach.get("connected_editor_send_command_control")
        != "SKIPPED_BY_EXPERIMENT"
        or reach.get("connected_editor_post_send_command_probe")
        != "SKIPPED_BY_EXPERIMENT"
        or diagnostic.get("entry_expected_size") != 34
        or diagnostic.get("entry_expected_sha256")
        != "3ee230fb69349453cf2f7f5275879c40423a3462e6d78baadb97237f415cecd7"
    ):
        return False
    outcome = diagnostic.get("runscript_call_outcome")
    classification = diagnostic.get("classification")
    build_state = diagnostic.get("build_report_state")
    if outcome not in {"NOT_REACHED", "EXCEPTION", "RETURNED"}:
        return False
    if classification not in FILE_CLASSIFICATIONS or build_state not in FILE_BUILD_STATES:
        return False
    checkpoint_fields = {
        "POST_RUNSCRIPT": "entry_exact_at_call_checkpoint",
        "POST_EXIT": "entry_exact_post_exit",
        "FAILURE_PRE_CLEANUP": "entry_exact_failure_pre_cleanup",
        "FAILURE_POST_CLEANUP": "entry_exact_failure_post_cleanup",
    }
    checkpoint_values = {
        checkpoint: diagnostic.get(field)
        for checkpoint, field in checkpoint_fields.items()
    }
    if any(
        value is not None and not isinstance(value, bool)
        for value in checkpoint_values.values()
    ):
        return False
    if not isinstance(diagnostic.get("entry_exact_at_freeze"), bool):
        return False
    if not isinstance(diagnostic.get("entry_delayed_or_later_observed"), bool):
        return False
    if not isinstance(diagnostic.get("entry_lost_after_checkpoint"), bool):
        return False
    for key in ("entry_invalid_or_partial_at", "entry_probe_errors_at"):
        values = diagnostic.get(key)
        if (
            not isinstance(values, list)
            or len(values) != len(set(values))
            or any(value not in FILE_CHECKPOINTS for value in values)
        ):
            return False
    build_probe_errors = diagnostic.get("build_report_probe_errors_at")
    if (
        not isinstance(build_probe_errors, list)
        or len(build_probe_errors) != len(set(build_probe_errors))
        or any(value not in BUILD_PROBE_CHECKPOINTS for value in build_probe_errors)
    ):
        return False
    build_exists_value = diagnostic.get("build_report_exists_at_freeze")
    freeze_build_probe_errors = [
        value for value in build_probe_errors if value != "BUILD_CAPTURE"
    ]
    if build_exists_value is not None and not isinstance(build_exists_value, bool):
        return False
    capture_exists = diagnostic.get("build_report_exists_at_capture")
    capture_state = diagnostic.get("build_report_capture_state")
    capture_context = diagnostic.get("build_report_capture_context")
    if capture_state not in BUILD_CAPTURE_STATES:
        return False
    capture_contracts = {
        "NOT_ATTEMPTED": (None, None),
        "SKIPPED_PRIOR_PROBE_ERROR": (None, "FAILURE_POST_CLEANUP"),
        "ABSENT": (False, "FAILURE_POST_CLEANUP"),
        "PRESENT_VALID_OBJECT": (True, "FAILURE_POST_CLEANUP"),
        "PRESENT_INVALID_OR_UNREADABLE": (True, "FAILURE_POST_CLEANUP"),
        "EXISTS_PROBE_ERROR": (None, "FAILURE_POST_CLEANUP"),
    }
    if (capture_exists, capture_context) != capture_contracts[capture_state]:
        return False
    if capture_state == "SKIPPED_PRIOR_PROBE_ERROR" and not freeze_build_probe_errors:
        return False
    if (capture_state == "EXISTS_PROBE_ERROR") != (
        "BUILD_CAPTURE" in build_probe_errors
    ):
        return False
    if capture_state == "PRESENT_VALID_OBJECT" and not (
        isinstance(report.get("connected_build"), dict)
        and report.get("connected_build_capture_context")
        == "FAILURE_POST_CLEANUP"
    ):
        return False
    if capture_state == "PRESENT_INVALID_OR_UNREADABLE" and not isinstance(
        report.get("connected_build_parse_error"), dict
    ):
        return False
    if capture_state == "EXISTS_PROBE_ERROR" and not isinstance(
        report.get("connected_build_capture_error"), dict
    ):
        return False
    expected_run_reach = {
        "NOT_REACHED": "NOT_REACHED",
        "EXCEPTION": "CALLED",
        "RETURNED": "RETURNED",
    }[outcome]
    if reach.get("connected_editor_run_script") != expected_run_reach:
        return False
    build_contract_reach = reach.get("connected_build_contract")
    if outcome in {"NOT_REACHED", "EXCEPTION"} and build_contract_reach != "NOT_REACHED":
        return False
    if outcome == "RETURNED" and build_contract_reach not in {
        "NOT_REACHED",
        "CALLED",
        "RETURNED",
    }:
        return False
    first_observed = diagnostic.get("entry_first_observed_at")
    exact_checkpoints = [
        checkpoint
        for checkpoint in (
            "POST_RUNSCRIPT",
            "POST_EXIT",
            "FAILURE_PRE_CLEANUP",
            "FAILURE_POST_CLEANUP",
        )
        if checkpoint_values[checkpoint] is True
    ]
    if first_observed != (exact_checkpoints[0] if exact_checkpoints else None):
        return False
    invalid_checkpoints = set(diagnostic.get("entry_invalid_or_partial_at"))
    entry_probe_errors = set(diagnostic.get("entry_probe_errors_at"))
    if invalid_checkpoints & entry_probe_errors:
        return False
    if any(
        checkpoint_values[checkpoint] is not False
        for checkpoint in invalid_checkpoints | entry_probe_errors
    ):
        return False
    freeze_probe = diagnostic.get("freeze_probe")
    if freeze_probe not in {"POST_EXIT", "FAILURE_POST_CLEANUP"}:
        return False
    current_freeze_probe_error = freeze_probe in freeze_build_probe_errors
    if current_freeze_probe_error:
        if build_exists_value is False:
            return False
    elif not isinstance(build_exists_value, bool):
        return False
    if checkpoint_values[freeze_probe] != diagnostic.get("entry_exact_at_freeze"):
        return False
    if outcome == "NOT_REACHED" and not (
        checkpoint_values["POST_RUNSCRIPT"] is None
        and checkpoint_values["POST_EXIT"] is None
        and isinstance(checkpoint_values["FAILURE_PRE_CLEANUP"], bool)
        and isinstance(checkpoint_values["FAILURE_POST_CLEANUP"], bool)
        and freeze_probe == "FAILURE_POST_CLEANUP"
    ):
        return False
    if outcome == "EXCEPTION" and not (
        checkpoint_values["POST_RUNSCRIPT"] is None
        and checkpoint_values["POST_EXIT"] is None
        and isinstance(checkpoint_values["FAILURE_PRE_CLEANUP"], bool)
        and isinstance(checkpoint_values["FAILURE_POST_CLEANUP"], bool)
        and freeze_probe == "FAILURE_POST_CLEANUP"
    ):
        return False
    if outcome == "RETURNED" and not isinstance(
        checkpoint_values["POST_RUNSCRIPT"], bool
    ):
        return False
    if freeze_probe == "POST_EXIT" and not (
        outcome == "RETURNED"
        and isinstance(checkpoint_values["POST_EXIT"], bool)
        and checkpoint_values["FAILURE_PRE_CLEANUP"] is None
        and checkpoint_values["FAILURE_POST_CLEANUP"] is None
    ):
        return False
    if freeze_probe == "POST_EXIT" and capture_state != "NOT_ATTEMPTED":
        return False
    if freeze_probe == "FAILURE_POST_CLEANUP" and capture_state == "NOT_ATTEMPTED":
        return False
    if freeze_build_probe_errors:
        if capture_state != "SKIPPED_PRIOR_PROBE_ERROR":
            return False
    elif capture_state == "SKIPPED_PRIOR_PROBE_ERROR":
        return False
    if capture_state != "NOT_ATTEMPTED" and build_contract_reach == "RETURNED":
        return False
    delayed = False
    if outcome == "RETURNED":
        delayed = (
            checkpoint_values["POST_RUNSCRIPT"] is False
            and any(
                checkpoint_values[checkpoint] is True
                for checkpoint in (
                    "POST_EXIT",
                    "FAILURE_PRE_CLEANUP",
                    "FAILURE_POST_CLEANUP",
                )
            )
        )
    elif outcome == "EXCEPTION":
        delayed = (
            checkpoint_values["FAILURE_PRE_CLEANUP"] is False
            and checkpoint_values["FAILURE_POST_CLEANUP"] is True
        )
    if diagnostic.get("entry_delayed_or_later_observed") is not delayed:
        return False
    lost = (
        checkpoint_values["POST_RUNSCRIPT"] is True
        and any(
            checkpoint_values[checkpoint] is False
            for checkpoint in (
                "POST_EXIT",
                "FAILURE_PRE_CLEANUP",
                "FAILURE_POST_CLEANUP",
            )
        )
    )
    if diagnostic.get("entry_lost_after_checkpoint") is not lost:
        return False
    invalid = bool(diagnostic.get("entry_invalid_or_partial_at"))
    indeterminate = bool(entry_probe_errors or build_probe_errors)
    exact_freeze = diagnostic.get("entry_exact_at_freeze") is True
    build_exists = (
        diagnostic.get("build_report_exists_at_freeze") is True
        or capture_exists is True
    )
    if outcome != "NOT_REACHED":
        if indeterminate and classification != "PROBE_INDETERMINATE":
            return False
        if not indeterminate and classification == "PROBE_INDETERMINATE":
            return False
        if not indeterminate and invalid and classification != "ENTRY_SENTINEL_INVALID_OR_PARTIAL":
            return False
        if not indeterminate and not invalid and classification == "ENTRY_SENTINEL_INVALID_OR_PARTIAL":
            return False
    allowed_by_outcome = {
        "NOT_REACHED": {"RUNSCRIPT_NOT_REACHED"},
        "EXCEPTION": {
            "RUNSCRIPT_CALL_EXCEPTION_ENTRY_ABSENT",
            "RUNSCRIPT_CALL_EXCEPTION_ENTRY_EXACT",
            "RUNSCRIPT_CALL_EXCEPTION_ENTRY_DELAYED_OR_CLEANUP_OBSERVED",
            "ENTRY_SENTINEL_INVALID_OR_PARTIAL",
            "PROBE_INDETERMINATE",
        },
        "RETURNED": {
            "RUNSCRIPT_RETURNED_ENTRY_ABSENT",
            "RUNSCRIPT_RETURNED_ENTRY_EXACT",
            "ENTRY_DELAYED_OR_POST_EXIT_OBSERVED",
            "ENTRY_LOST_AFTER_CHECKPOINT",
            "ENTRY_SENTINEL_INVALID_OR_PARTIAL",
            "ENTRY_EXACT_BUILD_REPORT_ABSENT",
            "PROBE_INDETERMINATE",
            "BUILD_REPORT_INVALID",
            "BUILD_CONTRACT_FAIL",
            "BUILD_CONTRACT_PASS",
        },
    }
    if classification not in allowed_by_outcome[outcome]:
        return False
    if classification == "RUNSCRIPT_CALL_EXCEPTION_ENTRY_EXACT" and not (
        checkpoint_values["FAILURE_PRE_CLEANUP"] is True and not delayed
    ):
        return False
    if (
        classification
        == "RUNSCRIPT_CALL_EXCEPTION_ENTRY_DELAYED_OR_CLEANUP_OBSERVED"
        and not delayed
    ):
        return False
    if classification == "RUNSCRIPT_CALL_EXCEPTION_ENTRY_ABSENT" and not (
        checkpoint_values["FAILURE_PRE_CLEANUP"] is False
        and checkpoint_values["FAILURE_POST_CLEANUP"] is False
        and not invalid
        and not indeterminate
    ):
        return False
    if classification == "RUNSCRIPT_RETURNED_ENTRY_ABSENT" and not (
        not exact_checkpoints
        and not invalid
        and not indeterminate
        and build_exists_value is False
    ):
        return False
    if classification == "RUNSCRIPT_RETURNED_ENTRY_EXACT" and not (
        exact_freeze
        and not delayed
        and not lost
        and not invalid
        and not indeterminate
        and build_exists_value is True
    ):
        return False
    if classification == "ENTRY_DELAYED_OR_POST_EXIT_OBSERVED" and not delayed:
        return False
    if classification == "ENTRY_LOST_AFTER_CHECKPOINT" and not lost:
        return False
    if classification == "ENTRY_SENTINEL_INVALID_OR_PARTIAL" and not invalid:
        return False
    if classification == "PROBE_INDETERMINATE" and not indeterminate:
        return False
    if classification == "ENTRY_EXACT_BUILD_REPORT_ABSENT" and not (
        exact_freeze
        and build_exists_value is False
        and not delayed
    ):
        return False
    if classification == "BUILD_REPORT_INVALID" and not (
        build_exists and build_state == "INVALID_OR_UNREADABLE"
    ):
        return False
    if classification == "BUILD_CONTRACT_FAIL" and build_state not in {
        "PRESENT_ENTRY_CONTRACT_FAIL",
        "REPORTED_BUILD_FAIL",
        "CONTRACT_FAIL",
    }:
        return False
    present_states = {
        "PRESENT_NOT_VALIDATED",
        "PRESENT_ENTRY_CONTRACT_FAIL",
        "INVALID_OR_UNREADABLE",
        "REPORTED_BUILD_FAIL",
        "CONTRACT_FAIL",
        "CONTRACT_PASS",
    }
    if build_state == "ABSENT" and build_exists:
        return False
    if build_state == "PROBE_INDETERMINATE" and not build_probe_errors:
        return False
    if build_probe_errors and build_state != "PROBE_INDETERMINATE":
        return False
    if build_state == "ENTRY_EXACT_BUILD_REPORT_ABSENT" and not (
        build_exists_value is False and exact_freeze
    ):
        return False
    if build_state in present_states and not build_exists:
        return False
    if build_state in {
        "PRESENT_ENTRY_CONTRACT_FAIL",
        "CONTRACT_FAIL",
        "CONTRACT_PASS",
    } and outcome != "RETURNED":
        return False
    if build_state == "PRESENT_ENTRY_CONTRACT_FAIL" and classification not in {
        "BUILD_CONTRACT_FAIL",
        "ENTRY_DELAYED_OR_POST_EXIT_OBSERVED",
        "ENTRY_LOST_AFTER_CHECKPOINT",
        "ENTRY_SENTINEL_INVALID_OR_PARTIAL",
        "PROBE_INDETERMINATE",
    }:
        return False
    if build_state == "INVALID_OR_UNREADABLE" and outcome == "RETURNED" and classification != "BUILD_REPORT_INVALID":
        if capture_state == "NOT_ATTEMPTED":
            return False
    if build_state in {"REPORTED_BUILD_FAIL", "CONTRACT_FAIL"} and outcome == "RETURNED" and classification != "BUILD_CONTRACT_FAIL":
        if capture_state == "NOT_ATTEMPTED":
            return False
    if build_state in {"ABSENT", "ENTRY_EXACT_BUILD_REPORT_ABSENT"} and (
        capture_state != "ABSENT" or freeze_probe != "FAILURE_POST_CLEANUP"
    ):
        return False
    if build_state == "PRESENT_NOT_VALIDATED" and not (
        freeze_probe == "FAILURE_POST_CLEANUP"
        and (
            capture_state == "PRESENT_VALID_OBJECT"
            or (
                capture_state == "ABSENT"
                and build_exists_value is True
            )
        )
    ):
        return False
    if build_state == "PRESENT_ENTRY_CONTRACT_FAIL" and not (
        outcome == "RETURNED"
        and freeze_probe == "POST_EXIT"
        and capture_state == "NOT_ATTEMPTED"
        and build_exists_value is True
        and build_contract_reach == "CALLED"
        and (
            checkpoint_values["POST_RUNSCRIPT"] is not True
            or checkpoint_values["POST_EXIT"] is not True
            or bool(entry_probe_errors)
            or invalid
        )
    ):
        return False
    normal_parsed_states = {
        "INVALID_OR_UNREADABLE",
        "REPORTED_BUILD_FAIL",
        "CONTRACT_FAIL",
        "CONTRACT_PASS",
    }
    if build_state in normal_parsed_states and capture_state == "NOT_ATTEMPTED":
        if not (
            outcome == "RETURNED"
            and freeze_probe == "POST_EXIT"
            and build_exists_value is True
            and checkpoint_values["POST_RUNSCRIPT"] is True
            and checkpoint_values["POST_EXIT"] is True
            and exact_freeze
            and not delayed
            and not lost
            and not invalid
            and not indeterminate
            and build_contract_reach
            == ("RETURNED" if build_state == "CONTRACT_PASS" else "CALLED")
        ):
            return False
    if build_state == "INVALID_OR_UNREADABLE" and capture_state not in {
        "NOT_ATTEMPTED",
        "PRESENT_INVALID_OR_UNREADABLE",
    }:
        return False
    if build_state == "REPORTED_BUILD_FAIL" and capture_state not in {
        "NOT_ATTEMPTED",
        "PRESENT_VALID_OBJECT",
    }:
        return False
    if build_state == "REPORTED_BUILD_FAIL" and (
        not isinstance(report.get("connected_build"), dict)
        or report["connected_build"].get("status")
        != "FAIL_CONNECTED_EDITOR_BUILD"
    ):
        return False
    if (
        build_state == "PRESENT_NOT_VALIDATED"
        and capture_state == "PRESENT_VALID_OBJECT"
        and report["connected_build"].get("status")
        == "FAIL_CONNECTED_EDITOR_BUILD"
    ):
        return False
    if build_state in {"CONTRACT_FAIL", "CONTRACT_PASS"} and (
        capture_state != "NOT_ATTEMPTED"
    ):
        return False
    if build_state == "PROBE_INDETERMINATE" and capture_state not in {
        "SKIPPED_PRIOR_PROBE_ERROR",
        "EXISTS_PROBE_ERROR",
    }:
        return False
    if (classification == "BUILD_CONTRACT_PASS") != (build_state == "CONTRACT_PASS"):
        return False
    if classification == "BUILD_CONTRACT_PASS" and not (
        outcome == "RETURNED"
        and checkpoint_values["POST_RUNSCRIPT"] is True
        and checkpoint_values["POST_EXIT"] is True
        and checkpoint_values["FAILURE_PRE_CLEANUP"] is None
        and checkpoint_values["FAILURE_POST_CLEANUP"] is None
        and freeze_probe == "POST_EXIT"
        and exact_freeze
        and build_exists
        and not delayed
        and not lost
        and not invalid
        and not indeterminate
        and reach.get("connected_editor_run_script") == "RETURNED"
        and reach.get("connected_build_contract") == "RETURNED"
    ):
        return False
    return True


async def run_profile(
    session: ClientSession,
    profile_id: str,
    case_id: str,
    expected_git_head: str,
    predecessor_job_id: str = "",
) -> dict[str, Any]:
    rule = PROFILE_RULES[profile_id]
    state = await call_json(
        session,
        "submit_job",
        {
            "profile_id": profile_id,
            "case_id": case_id,
            "predecessor_job_id": predecessor_job_id,
        },
    )
    job_id = state.get("job_id")
    phase = state.get("phase")
    if not isinstance(job_id, str) or not job_id or phase != "RUNNING":
        raise RuntimeError(f"SUBMIT_NOT_RUNNING:{profile_id}:{job_id}:{phase}")
    if state.get("license_arguments_added") is not False:
        raise RuntimeError("JOB_STATE_INDICATES_LICENSE_ARGUMENTS")
    if state.get("git_head") != expected_git_head:
        raise RuntimeError("SUBMIT_GIT_HEAD_DIFFERS_FROM_INVENTORY")
    if state.get("predecessor_job_id") != (predecessor_job_id or None):
        raise RuntimeError("PREDECESSOR_ID_NOT_FROZEN_IN_JOB_STATE")
    stable = {
        name: state.get(name)
        for name in (
            "job_id",
            "case_id",
            "profile_id",
            "engine",
            "script_sha256",
            "git_head",
            "output_root_id",
            "predecessor_job_id",
        )
    }
    deadline = time.monotonic() + HARD_PROFILE_WAIT_SECONDS
    try:
        while phase == "RUNNING":
            if time.monotonic() >= deadline:
                state = await call_json(session, "cancel_job", {"job_id": job_id})
                phase = state.get("phase")
                break
            await asyncio.sleep(POLL_SECONDS)
            state = await call_json(session, "poll_job", {"job_id": job_id})
            for name, expected in stable.items():
                if state.get(name) != expected:
                    raise RuntimeError(f"JOB_IDENTITY_CHANGED:{name}")
            phase = state.get("phase")
            if phase != "RUNNING" and phase not in TERMINAL_PHASES:
                raise RuntimeError(f"UNKNOWN_TERMINAL_PHASE:{phase}")
    except BaseException:
        if phase == "RUNNING":
            with suppress(BaseException):
                await call_json(session, "cancel_job", {"job_id": job_id})
        raise

    manifest = await call_json(
        session, "artifact_manifest", {"job_id": job_id}, timeout_seconds=600
    )
    if manifest.get("job_id") != job_id or manifest.get("phase") != phase:
        raise RuntimeError("MANIFEST_JOB_ID_OR_PHASE_MISMATCH")
    report_entry = manifest_file(manifest, rule["report"])
    report = report_entry.get("report_json") if report_entry else None
    assertions = report.get("assertions") if isinstance(report, dict) else None
    report_files = report.get("files") if isinstance(report, dict) else None
    artifacts_ok = isinstance(report_files, dict)
    if artifacts_ok:
        for artifact, report_key in rule["artifacts"].items():
            entry = manifest_file(manifest, artifact)
            declared = report_files.get(report_key)
            artifacts_ok = (
                isinstance(entry, dict)
                and isinstance(declared, dict)
                and isinstance(entry.get("size"), int)
                and entry["size"] > 0
                and entry.get("size") == declared.get("size")
                and isinstance(entry.get("sha256"), str)
                and entry.get("sha256") == declared.get("sha256")
                and report_path_matches(declared.get("path"), artifact)
            )
            if not artifacts_ok:
                break

    scope_ok = True
    diagnostic_contract_ok = True
    if profile_id == SC_PROFILE:
        scope_ok = (
            isinstance(report, dict)
            and report.get("native_parameterization") == "NOT_RUN"
            and report.get("p1_cad_hard_gate") == "BLOCKED_NATIVE_PARAMETERIZATION"
        )
    elif profile_id == WB_PROFILE:
        boundaries = (
            report.get("canonical_claim_boundaries", {})
            if isinstance(report, dict)
            else {}
        )
        channel = (
            report.get("script_channel_diagnostic", {})
            if isinstance(report, dict)
            else {}
        )
        diagnostic_contract_ok = file_runscript_diagnostic_contract_ok(report)
        scope_ok = (
            isinstance(report, dict)
            and report.get("diagnostic_only") is True
            and report.get("external_scdocx_attach") == "NOT_RUN"
            and report.get("native_parameterization") == "NOT_RUN"
            and report.get("p1_cad_hard_gate")
            == "BLOCKED_EXTERNAL_NATIVE_ATTACH_AND_NATIVE_PARAMETERIZATION_NOT_PROVEN"
            and isinstance(boundaries, dict)
            and set(boundaries)
            == {
                "external_scdocx_attach",
                "external_native_named_selection_transfer",
                "native_parameterization",
                "p1_cad_toolchain_readiness",
            }
            and all(value is False for value in boundaries.values())
            and diagnostic_contract_ok
            and channel.get("classification") == "BUILD_CONTRACT_PASS"
            and channel.get("build_report_state") == "CONTRACT_PASS"
        )
    capability_pass = (
        phase == "PROCESS_EXITED_0"
        and isinstance(report, dict)
        and report.get("probe") == rule["probe"]
        and report.get("status") == rule["required_status"]
        and report.get("engineering_capability") == rule["required_status"]
        and report.get("p1_stage_gate") == "NOT_RUN"
        and report.get("license_arguments_added") is False
        and isinstance(assertions, dict)
        and set(assertions) == rule["assertions"]
        and all(assertions.get(name) is True for name in rule["assertions"])
        and artifacts_ok
        and scope_ok
    )
    return {
        "profile_id": profile_id,
        "case_id": case_id,
        "predecessor_job_id": predecessor_job_id or None,
        "final_state": state,
        "manifest": manifest,
        "declared_report_name": rule["report"],
        "declared_report_sha256": report_entry.get("sha256") if report_entry else None,
        "declared_report": report,
        "capability_pass": capability_pass,
        "diagnostic_contract_ok": diagnostic_contract_ok,
        "p1_stage_gate": "NOT_RUN",
    }


async def run_suite() -> int:
    stamp = (
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        + "_"
        + uuid4().hex[:8]
    )
    case_id = "a5c-" + uuid4().hex[:12]
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    result_path = OUTPUT_ROOT / f"AJM005_T1_CONNECTED_SC_SUITE_{stamp}.json"
    stderr_path = OUTPUT_ROOT / f"AJM005_T1_CONNECTED_SC_SUITE_{stamp}_MCP_STDERR.log"
    result: dict[str, Any] = {
        "schema_version": 1,
        "task": "AJM-WIN-ANSYS-STUDENT-CAPABILITY-SMOKE-005",
        "suite": "workbench_connected_spaceclaim_t1_diagnostic",
        "case_id": case_id,
        "started_at": utc_now(),
        "ended_at": None,
        "suite_status": "FAIL_CONNECTED_SPACECLAIM_TRANSFER_DIAGNOSTIC",
        "p1_cad_toolchain_readiness": "BLOCKED",
        "p1_cad_blocker": (
            "EXTERNAL_NATIVE_ATTACH_AND_NATIVE_PARAMETERIZATION_NOT_PROVEN"
        ),
        "pass_005_capability": "DIAGNOSTIC_ONLY_NOT_EXTERNAL_NATIVE_TRANSFER",
        "p1_p6_gates": "NOT_RUN",
        "visibility": "NOT_USER_OBSERVED",
        "license_arguments_added": False,
        "connected_spaceclaim_diagnostic": "NOT_RUN",
        "script_channel_classification": "NOT_EVALUATED",
        "mcp_package_version": None,
        "protocol_version": None,
        "server_name": None,
        "runner_sha256": None,
        "inventory": None,
        "runs": [],
        "error": None,
    }
    exit_code = 2
    try:
        if norm(Path(sys.executable)) != norm(EXPECTED_PYTHON):
            raise RuntimeError("BLOCKED_WRONG_T1_CONNECTED_RUNNER_INTERPRETER")
        result["mcp_package_version"] = version("mcp")
        if result["mcp_package_version"] != "1.28.1":
            raise RuntimeError("BLOCKED_UNEXPECTED_MCP_PACKAGE_VERSION")
        if not SERVER.is_file():
            raise RuntimeError("BLOCKED_MCP_SERVER_MISSING")
        parameters = StdioServerParameters(
            command=str(EXPECTED_PYTHON),
            args=["-I", "-B", str(SERVER)],
            cwd=str(REPO),
            encoding="utf-8",
            encoding_error_handler="strict",
        )
        with stderr_path.open("w", encoding="utf-8") as errlog:
            async with stdio_client(parameters, errlog=errlog) as streams:
                async with ClientSession(
                    *streams,
                    read_timeout_seconds=timedelta(seconds=120),
                    client_info=types.Implementation(
                        name="airjet-ajm005-t1-connected-spaceclaim-harness",
                        version="1.0.0",
                    ),
                ) as session:
                    initialized = await session.initialize()
                    result["protocol_version"] = initialized.protocolVersion
                    result["server_name"] = initialized.serverInfo.name
                    tool_names = {tool.name for tool in (await session.list_tools()).tools}
                    if tool_names != EXPECTED_TOOLS:
                        raise RuntimeError(
                            f"BLOCKED_UNEXPECTED_MCP_TOOLS:{sorted(tool_names)}"
                        )
                    inventory = await call_json(session, "inventory")
                    result["inventory"] = inventory
                    if inventory.get("ready") is not True:
                        raise RuntimeError("BLOCKED_INVENTORY_NOT_READY")
                    result["runner_sha256"] = require_runner_git_blob(
                        str(inventory.get("git_head", ""))
                    )
                    if inventory.get("license_data_read") is not False:
                        raise RuntimeError("INVENTORY_READ_LICENSE_DATA")
                    required = {SC_PROFILE, WB_PROFILE}
                    approved = set(inventory.get("approved_profiles") or [])
                    if not required.issubset(approved):
                        raise RuntimeError(
                            f"BLOCKED_MISSING_PROFILES:{sorted(required - approved)}"
                        )
                    expected_git_head = str(inventory["git_head"])
                    sc_run = await run_profile(
                        session, SC_PROFILE, case_id, expected_git_head
                    )
                    result["runs"].append(sc_run)
                    if sc_run["capability_pass"]:
                        wb_run = await run_profile(
                            session,
                            WB_PROFILE,
                            case_id,
                            expected_git_head,
                            sc_run["final_state"]["job_id"],
                        )
                        result["runs"].append(wb_run)
                        wb_report = wb_run.get("declared_report")
                        if wb_run.get("diagnostic_contract_ok") is not True:
                            result["script_channel_classification"] = (
                                "INVALID_DIAGNOSTIC_CONTRACT"
                            )
                        elif isinstance(wb_report, dict):
                            channel = wb_report.get("script_channel_diagnostic")
                            if isinstance(channel, dict):
                                result["script_channel_classification"] = (
                                    channel.get("classification", "NOT_EVALUATED")
                                )
                        result["connected_spaceclaim_diagnostic"] = (
                            "PASS" if wb_run["capability_pass"] else "FAIL"
                        )
                    else:
                        result["runs"].append(
                            {
                                "profile_id": WB_PROFILE,
                                "case_id": case_id,
                                "status": "BLOCKED_UPSTREAM",
                                "capability_pass": False,
                                "p1_stage_gate": "NOT_RUN",
                            }
                        )
                    if (
                        all(run.get("capability_pass") for run in result["runs"])
                        and result["connected_spaceclaim_diagnostic"] == "PASS"
                    ):
                        result["suite_status"] = (
                            "PASS_CONNECTED_SPACECLAIM_TRANSFER_DIAGNOSTIC"
                        )
                        exit_code = 0
    except Exception as exc:  # noqa: BLE001 - preserve unexpected failures.
        result["error"] = {
            "type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
        }
    finally:
        result["ended_at"] = utc_now()
        result_path.write_text(
            json.dumps(result, indent=2, sort_keys=True), encoding="utf-8"
        )
        print(
            json.dumps(
                {
                    "suite_status": result["suite_status"],
                    "result_path": str(result_path),
                    "stderr_path": str(stderr_path),
                    "run_count": len(result["runs"]),
                    "exit_code": exit_code,
                },
                sort_keys=True,
            )
        )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run_suite()))

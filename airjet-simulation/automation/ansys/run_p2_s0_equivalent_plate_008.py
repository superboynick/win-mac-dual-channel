#!/usr/bin/env python3
"""Run the P2 S0 equivalent-plate SpaceClaim producer through audited MCP."""

from __future__ import annotations

import asyncio
from contextlib import suppress
from datetime import datetime, timedelta, timezone
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path, PureWindowsPath
import re
import sys
import time
import traceback
from typing import Any, Optional
from uuid import uuid4

from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client

import run_v03_continuous_fluid_006 as common


EXPECTED_PYTHON = common.EXPECTED_PYTHON
SERVER = common.SERVER
REPO = common.REPO
OUTPUT_ROOT = Path(r"D:\AirJet_P2\AJM-P2-STRUCTURAL-008")
RESULT_PATH = OUTPUT_ROOT / "P2_S0_EQUIVALENT_PLATE_RUN_SUMMARY.json"
POLICY_GIT_PATH = common.POLICY_GIT_PATH
PROFILE_ID = "ajm008-spaceclaim-p2-s0-equivalent-plate-v1"
PROFILE_SCRIPT = "008/p2_s0_equivalent_plate_producer.py"
PROFILE_SCRIPT_SHA256 = "8681318dadbb14556980dd38bd7d49be681f2e85fa4f39e24a0f84aa171619f4"
PRODUCER_REPORT = "p2_s0_equivalent_plate_producer.json"
CASE_ID = "AJM-P2-S0-EQ-M7-C005"
EXPECTED_TOOLS = common.EXPECTED_TOOLS
POLL_SECONDS = 1.0
HARD_PROFILE_WAIT_SECONDS = 900
TERMINAL_PHASES = common.TERMINAL_PHASES
EXPECTED_ASSERTIONS = {
    "input_contract",
    "source_candidate_binding",
    "single_cell_calibration_scope",
    "evidence_class_guards",
    "equivalent_plate_geometry",
    "central_anchor_geometry",
    "free_perimeter_contract",
    "native_save",
    "native_reopen",
    "step_export",
    "step_reimport",
    "step_anchor_region_preserved",
    "step_semantic_sidecar",
    "artifact_hashes",
    "claim_boundaries",
    "physics_guards",
}
EXPECTED_DEPENDENCY_GIT_PATHS = (
    "airjet-simulation/automation/ansys/contracts/p2_s0_equivalent_plate_v1.json",
    "airjet-simulation/parameters/p2_s0_equivalent_material_candidates.csv",
    "airjet-simulation/automation/ansys/contracts/trusted_full_product_gen1/variant_02_m_3x4_7_0_r50_balanced.json",
)
EXPECTED_ARTIFACTS = {
    "p2_s0_equivalent_plate.scdocx",
    "p2_s0_equivalent_plate.step",
    "p2_s0_equivalent_plate_sidecar.json",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def norm(path: Path) -> str:
    return os.path.normcase(os.path.abspath(str(path)))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def exact_profile(head: str) -> dict[str, Any]:
    policy = json.loads(
        common.read_git_blob(head, POLICY_GIT_PATH).decode("utf-8")
    )
    matches = [
        item
        for item in policy.get("profiles", [])
        if isinstance(item, dict) and item.get("profile_id") == PROFILE_ID
    ]
    if len(matches) != 1:
        raise RuntimeError("BLOCKED_P2_PROFILE_NOT_EXACTLY_ONE")
    expected = {
        "profile_id": PROFILE_ID,
        "engine": "spaceclaim",
        "script": PROFILE_SCRIPT,
        "sha256": PROFILE_SCRIPT_SHA256,
        "timeout_seconds": 900,
        "output_root_id": "p2_structural_008",
        "reports": [PRODUCER_REPORT],
        "predecessor": None,
    }
    if matches[0] != expected:
        raise RuntimeError("BLOCKED_P2_PROFILE_CONTRACT_MISMATCH")
    source = common.read_git_blob(
        head,
        "airjet-simulation/automation/ansys/approved/" + PROFILE_SCRIPT,
    )
    if sha256_bytes(source) != PROFILE_SCRIPT_SHA256:
        raise RuntimeError("BLOCKED_P2_GIT_BLOB_HASH_MISMATCH")
    production = policy.get("production_contracts")
    if (
        not isinstance(production, dict)
        or production.get("execution_state")
        != "STATIC_CONTRACT_ONLY_NOT_REGISTERED"
        or production.get("p1_p6_gates") != "NOT_RUN"
    ):
        raise RuntimeError("BLOCKED_P2_PRODUCTION_GATE_STATE")
    return matches[0]


def preflight() -> dict[str, Any]:
    result = {
        "git_head": None,
        "preflight_ok": False,
        "preflight_errors": [],
        "profile_found": False,
        "profile_script_sha256_matches": False,
        "p1_p6_not_run": False,
    }
    errors = []
    branch = common.git_capture("rev-parse", "--abbrev-ref", "HEAD")
    status = common.git_capture("status", "--porcelain=v1")
    head_result = common.git_capture("rev-parse", "HEAD")
    if branch["exit_code"] != 0 or branch["stdout"] != "main":
        errors.append("BLOCKED_NOT_MAIN")
    if status["exit_code"] != 0 or status["stdout"]:
        errors.append("BLOCKED_DIRTY_WORKTREE")
    if (
        head_result["exit_code"] != 0
        or not re.fullmatch(r"[0-9a-f]{40}", head_result["stdout"])
    ):
        errors.append("BLOCKED_INVALID_GIT_HEAD")
    else:
        head = head_result["stdout"]
        result["git_head"] = head
        ahead = common.git_capture(
            "rev-list", "--left-right", "--count", head + "...origin/main"
        )
        if ahead["exit_code"] != 0 or ahead["stdout"] != "0\t0":
            errors.append("BLOCKED_AHEAD_BEHIND")
        verify = common.git_capture("verify-commit", "--raw", head)
        if verify["exit_code"] != 0:
            errors.append("BLOCKED_UNSIGNED")
        try:
            profile = exact_profile(head)
            result["profile_found"] = True
            result["profile_script_sha256_matches"] = (
                profile["sha256"] == PROFILE_SCRIPT_SHA256
            )
            result["p1_p6_not_run"] = True
        except Exception as exc:
            errors.append(str(exc))
    result["preflight_errors"] = errors
    result["preflight_ok"] = not errors
    return result


def validate_dependency_artifacts(value: Any) -> None:
    if not isinstance(value, list) or len(value) != 3:
        raise RuntimeError("P2_DEPENDENCY_BUNDLE_COUNT_INVALID")
    observed = []
    basenames = []
    for item in value:
        if not isinstance(item, dict):
            raise RuntimeError("P2_DEPENDENCY_ENTRY_INVALID")
        git_path = item.get("git_path")
        relative = item.get("relative_path")
        if (
            not isinstance(git_path, str)
            or not isinstance(relative, str)
            or PureWindowsPath(git_path).name != relative
            or not isinstance(item.get("size"), int)
            or item["size"] <= 0
            or not isinstance(item.get("sha256"), str)
            or not re.fullmatch(r"[0-9a-f]{64}", item["sha256"])
        ):
            raise RuntimeError("P2_DEPENDENCY_ENTRY_INVALID")
        observed.append(git_path)
        basenames.append(relative)
    if (
        tuple(observed) != EXPECTED_DEPENDENCY_GIT_PATHS
        or len(basenames) != len(set(basenames))
    ):
        raise RuntimeError("P2_DEPENDENCY_PATH_SET_INVALID")


def validate_report(
    manifest: dict[str, Any], state: dict[str, Any], expected_head: str
) -> dict[str, Any]:
    files = manifest.get("files")
    if not isinstance(files, list):
        raise RuntimeError("P2_MANIFEST_FILES_INVALID")
    entries = {
        item.get("relative_path"): item
        for item in files
        if isinstance(item, dict) and isinstance(item.get("relative_path"), str)
    }
    report_entry = entries.get(PRODUCER_REPORT)
    if not isinstance(report_entry, dict) or report_entry.get("report_error") is not None:
        raise RuntimeError("P2_REPORT_MISSING_OR_INVALID")
    report = report_entry.get("report_json")
    if not isinstance(report, dict):
        raise RuntimeError("P2_REPORT_NOT_INLINED")
    if (
        report.get("schema_version") != 1
        or report.get("task")
        != "AJM_P2_S0_EQUIVALENT_PLATE_GEOMETRY_PRODUCER"
        or report.get("probe") != "p2_s0_equivalent_plate_producer"
        or report.get("status") != "PASS_PARTIAL_CAD_CAPABILITY"
        or report.get("engineering_capability")
        != "PASS_PARTIAL_CAD_CAPABILITY"
        or report.get("pilot_result")
        != "PASS_PRE_GATE_P2_S0_EQUIVALENT_PLATE_BASELINE"
        or report.get("claim_ceiling")
        != "PASS_PRE_GATE_P2_S0_EQUIVALENT_PLATE_BASELINE"
    ):
        raise RuntimeError("P2_REPORT_STATUS_OR_PROBE_MISMATCH")
    if (
        report.get("formal_p2_completion") is not False
        or report.get("formal_p2_gate") != "NOT_RUN"
        or report.get("p1_stage_gate") != "NOT_RUN"
        or report.get("p2_stage_gate") != "NOT_RUN"
        or report.get("p3_stage_gate") != "NOT_RUN"
        or report.get("p1_p6_gates") != "NOT_RUN"
        or report.get("exact_product_geometry") != "NOT_CLAIMED"
        or report.get("product_material_identification") != "NOT_CLAIMED"
        or report.get("mesh") != "NOT_RUN"
        or report.get("mechanical") != "NOT_RUN"
        or report.get("modal") != "NOT_RUN"
        or report.get("harmonic") != "NOT_RUN"
        or report.get("piezoelectric_coupling") != "NOT_RUN"
        or report.get("fsi") != "NOT_RUN"
        or report.get("license_arguments_added") is not False
        or report.get("visibility") != "NOT_USER_OBSERVED"
        or report.get("error") not in (None, "")
    ):
        raise RuntimeError("P2_REPORT_CLAIM_BOUNDARY_VIOLATION")
    assertions = report.get("assertions")
    if (
        not isinstance(assertions, dict)
        or set(assertions) != EXPECTED_ASSERTIONS
        or any(value is not True for value in assertions.values())
    ):
        raise RuntimeError("P2_REPORT_ASSERTIONS_NOT_EXACT_PASS")
    identity = report.get("identity")
    if (
        not isinstance(identity, dict)
        or identity.get("git_head") != expected_head
        or identity.get("profile_id") != PROFILE_ID
        or identity.get("profile_contract_sha256")
        != state.get("profile_contract_sha256")
        or identity.get("dependency_manifest_sha256")
        != state.get("profile_dependency_manifest_sha256")
        or identity.get("script_sha256") != PROFILE_SCRIPT_SHA256
        or identity.get("case_id") != CASE_ID
    ):
        raise RuntimeError("P2_REPORT_IDENTITY_MISMATCH")
    reported_files = report.get("files")
    if not isinstance(reported_files, dict) or set(reported_files) != EXPECTED_ARTIFACTS:
        raise RuntimeError("P2_REPORT_ARTIFACT_SET_MISMATCH")
    for name in EXPECTED_ARTIFACTS:
        reported = reported_files[name]
        manifest_entry = entries.get(name)
        if (
            not isinstance(reported, dict)
            or not isinstance(manifest_entry, dict)
            or PureWindowsPath(str(reported.get("path", ""))).name != name
            or reported.get("size") != manifest_entry.get("size")
            or reported.get("sha256") != manifest_entry.get("sha256")
            or not isinstance(reported.get("size"), int)
            or reported["size"] <= 0
            or not isinstance(reported.get("sha256"), str)
            or not re.fullmatch(r"[0-9a-f]{64}", reported["sha256"])
        ):
            raise RuntimeError("P2_REPORT_ARTIFACT_MISMATCH:" + name)
    return report


async def call_json(
    session: ClientSession,
    name: str,
    arguments: Optional[dict[str, Any]] = None,
    timeout_seconds: int = 120,
) -> dict[str, Any]:
    result = await session.call_tool(
        name,
        arguments or {},
        read_timeout_seconds=timedelta(seconds=timeout_seconds),
    )
    return common.json_from_result(name, result)


async def run_suite() -> int:
    stamp = (
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        + "_"
        + uuid4().hex[:8]
    )
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    stderr_path = OUTPUT_ROOT / ("P2_S0_MCP_STDERR_" + stamp + ".log")
    result = {
        "task": "AJM_P2_S0_EQUIVALENT_PLATE_GEOMETRY_PRODUCER",
        "case_id": CASE_ID,
        "profile_id": PROFILE_ID,
        "started_at": utc_now(),
        "ended_at": None,
        "preflight": None,
        "final_status": "FAIL_PRE_GATE_P2_S0_EQUIVALENT_PLATE_GEOMETRY",
        "inventory": None,
        "job_id": None,
        "job_state": None,
        "manifest": None,
        "producer_report": None,
        "error": None,
    }
    exit_code = 2
    try:
        pf = preflight()
        result["preflight"] = pf
        if not pf["preflight_ok"]:
            raise RuntimeError("BLOCKED_PREFLIGHT:" + ";".join(pf["preflight_errors"]))
        expected_head = pf["git_head"]
        if norm(Path(sys.executable)) != norm(EXPECTED_PYTHON):
            raise RuntimeError("BLOCKED_WRONG_RUNNER_INTERPRETER")
        if version("mcp") != "1.28.1":
            raise RuntimeError("BLOCKED_UNEXPECTED_MCP_PACKAGE_VERSION")
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
                        name="airjet-p2-s0-equivalent-plate-harness",
                        version="1.0.0",
                    ),
                ) as session:
                    await session.initialize()
                    tools = {item.name for item in (await session.list_tools()).tools}
                    if tools != EXPECTED_TOOLS:
                        raise RuntimeError("BLOCKED_UNEXPECTED_MCP_TOOLS")
                    inventory = await call_json(session, "inventory")
                    result["inventory"] = inventory
                    if (
                        inventory.get("ready") is not True
                        or inventory.get("git_head") != expected_head
                        or PROFILE_ID not in set(inventory.get("approved_profiles") or [])
                    ):
                        raise RuntimeError("BLOCKED_P2_INVENTORY_IDENTITY")
                    contracts = inventory.get("profile_contract_sha256")
                    expected_contract = contracts.get(PROFILE_ID) if isinstance(contracts, dict) else None
                    if not isinstance(expected_contract, str) or not re.fullmatch(
                        r"[0-9a-f]{64}", expected_contract
                    ):
                        raise RuntimeError("BLOCKED_P2_INVENTORY_PROFILE_CONTRACT")
                    state = await call_json(
                        session,
                        "submit_job",
                        {"profile_id": PROFILE_ID, "case_id": CASE_ID},
                    )
                    job_id = state.get("job_id")
                    phase = state.get("phase")
                    if not isinstance(job_id, str) or not job_id or phase != "RUNNING":
                        raise RuntimeError("P2_SUBMIT_NOT_RUNNING")
                    expected_submit = {
                        "case_id": CASE_ID,
                        "profile_id": PROFILE_ID,
                        "engine": "spaceclaim",
                        "script_sha256": PROFILE_SCRIPT_SHA256,
                        "profile_contract_sha256": expected_contract,
                        "git_head": expected_head,
                        "output_root_id": "p2_structural_008",
                    }
                    for key, expected in expected_submit.items():
                        if state.get(key) != expected:
                            raise RuntimeError("P2_SUBMIT_IDENTITY_MISMATCH:" + key)
                    if (
                        state.get("license_arguments_added") is not False
                        or state.get("predecessor_job_id") is not None
                        or state.get("predecessor_artifacts") != []
                    ):
                        raise RuntimeError("P2_SUBMIT_BOUNDARY_INVALID")
                    validate_dependency_artifacts(
                        state.get("profile_dependency_artifacts")
                    )
                    dependency_sha = state.get("profile_dependency_manifest_sha256")
                    if not isinstance(dependency_sha, str) or not re.fullmatch(
                        r"[0-9a-f]{64}", dependency_sha
                    ):
                        raise RuntimeError("P2_SUBMIT_DEPENDENCY_HASH_INVALID")
                    result["job_id"] = job_id
                    result["job_state"] = state
                    stable = {
                        key: state.get(key)
                        for key in (
                            "job_id", "case_id", "profile_id", "engine",
                            "script_sha256", "profile_contract_sha256",
                            "profile_dependency_manifest_sha256", "git_head",
                            "output_root_id", "job_directory",
                            "license_arguments_added", "predecessor_job_id",
                            "predecessor_artifacts",
                        )
                    }
                    deadline = time.monotonic() + HARD_PROFILE_WAIT_SECONDS
                    try:
                        while phase == "RUNNING":
                            if time.monotonic() >= deadline:
                                state = await call_json(
                                    session, "cancel_job", {"job_id": job_id}
                                )
                                phase = state.get("phase")
                                break
                            await asyncio.sleep(POLL_SECONDS)
                            state = await call_json(
                                session, "poll_job", {"job_id": job_id}
                            )
                            for key, expected in stable.items():
                                if state.get(key) != expected:
                                    raise RuntimeError("P2_JOB_IDENTITY_CHANGED:" + key)
                            phase = state.get("phase")
                            if phase != "RUNNING" and phase not in TERMINAL_PHASES:
                                raise RuntimeError("P2_UNKNOWN_TERMINAL_PHASE")
                    except BaseException:
                        if phase == "RUNNING":
                            with suppress(BaseException):
                                await call_json(
                                    session, "cancel_job", {"job_id": job_id}
                                )
                        raise
                    validate_dependency_artifacts(
                        state.get("profile_dependency_artifacts")
                    )
                    result["job_state"] = state
                    manifest = await call_json(
                        session,
                        "artifact_manifest",
                        {"job_id": job_id},
                        timeout_seconds=600,
                    )
                    result["manifest"] = manifest
                    if manifest.get("job_id") != job_id or manifest.get("phase") != phase:
                        raise RuntimeError("P2_MANIFEST_JOB_OR_PHASE_MISMATCH")
                    if phase == "PROCESS_EXITED_0":
                        result["producer_report"] = validate_report(
                            manifest, state, expected_head
                        )
                        result["final_status"] = (
                            "PASS_PRE_GATE_P2_S0_EQUIVALENT_PLATE_GEOMETRY"
                        )
                        exit_code = 0
    except Exception as exc:
        result["error"] = {
            "type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
        }
    finally:
        result["ended_at"] = utc_now()
        RESULT_PATH.write_text(
            json.dumps(result, indent=2, sort_keys=True), encoding="utf-8"
        )
        print(json.dumps({
            "exit_code": exit_code,
            "final_status": result["final_status"],
            "result_path": str(RESULT_PATH),
        }, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run_suite()))

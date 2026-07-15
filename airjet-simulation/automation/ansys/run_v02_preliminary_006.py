#!/usr/bin/env python3
"""Run AJM-006 V02 preliminary producer through MCP and write fixed summary."""

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
OUTPUT_ROOT = Path(r"D:\AirJet_P1\AJM-P1-CAD-006")
RESULT_PATH = OUTPUT_ROOT / "V02_PRELIMINARY_RUN_SUMMARY.json"
POLICY_GIT_PATH = "airjet-simulation/automation/ansys/profiles.json"
PROFILE_ID = "ajm006-spaceclaim-v02-preliminary-v1"
PROFILE_SCRIPT_SHA256 = "78afab31adb60e4f84ee1d9e89913151ba2fe71fcec1fc50b84714b64bf3e43b"
CASE_ID = "AJM006-V02-PRELIMINARY"
EXPECTED_TOOLS = {
    "inventory",
    "submit_job",
    "poll_job",
    "cancel_job",
    "artifact_manifest",
}
POLL_SECONDS = 1.0
HARD_PROFILE_WAIT_SECONDS = 7200
TERMINAL_PHASES = {
    "PROCESS_EXITED_0",
    "FAILED_PROCESS",
    "TIMED_OUT",
    "CANCELLED",
    "FAILED_TERMINATION",
    "FAILED_MONITOR",
    "FAILED_START",
}
PRODUCER_REPORT = "v02_preliminary_producer.json"
EXPECTED_REPORT_ASSERTIONS = {
    "input_contract",
    "gen1_target",
    "full_product_scope",
    "complete_flow_path",
    "two_fluid_zone",
    "native_save",
    "native_reopen",
    "step_export_reimport",
    "artifact_hashes",
    "physics_guards",
}
EXPECTED_PRODUCER_ARTIFACTS = {
    "authoring_native": "v02_full_product_authoring.scdocx",
    "two_zone_native": "product_two_zone.scdocx",
    "step": "product.step",
    "native_reopen": "native_reopen.json",
    "step_reimport": "step_reimport.json",
    "face_inventory": "v02_face_inventory.json",
}
EXPECTED_DEPENDENCY_COUNT = 15


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def norm(path: Path) -> str:
    return os.path.normcase(os.path.abspath(str(path)))


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_capture(*args: str) -> dict[str, Any]:
    completed = subprocess.run(
        ["git", "-C", str(REPO), *args],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
        stdin=subprocess.DEVNULL,
    )
    return {
        "exit_code": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def read_git_blob(head: str, relative: str) -> bytes:
    if (
        not re.fullmatch(r"[0-9a-f]{40}", head)
        or not relative
        or relative.startswith(("/", "\\"))
        or ".." in Path(relative).parts
    ):
        raise RuntimeError("BLOCKED_UNSAFE_GIT_BLOB_PATH")
    result = subprocess.run(
        ["git", "-C", str(REPO), "show", "{}:{}".format(head, relative)],
        capture_output=True,
        timeout=30,
        check=False,
        stdin=subprocess.DEVNULL,
    )
    if result.returncode != 0:
        raise RuntimeError("BLOCKED_MISSING_GIT_BLOB")
    return result.stdout


def preflight() -> dict[str, Any]:
    result = {
        "git_head": None,
        "preflight_ok": False,
        "preflight_errors": [],
        "profile_found": False,
        "profile_script_sha256_matches": False,
        "execution_state_static": False,
        "p1_p6_not_run": False,
    }
    errors = []

    branch_r = git_capture("rev-parse", "--abbrev-ref", "HEAD")
    if branch_r["exit_code"] != 0 or branch_r["stdout"] != "main":
        errors.append("BLOCKED_NOT_MAIN")
    else:
        status_r = git_capture("status", "--porcelain=v1")
        if status_r["stdout"]:
            errors.append("BLOCKED_DIRTY_WORKTREE")

    head_r = git_capture("rev-parse", "HEAD")
    if head_r["exit_code"] != 0 or not re.fullmatch(r"[0-9a-f]{40}", head_r["stdout"]):
        errors.append("BLOCKED_INVALID_GIT_HEAD")
    else:
        head = head_r["stdout"]
        result["git_head"] = head

        ahead_r = git_capture(
            "rev-list", "--left-right", "--count",
            "{}...origin/main".format(head),
        )
        if ahead_r["exit_code"] != 0 or ahead_r["stdout"] != "0\t0":
            errors.append("BLOCKED_AHEAD_BEHIND")

        verify_r = git_capture("verify-commit", "--raw", head)
        if verify_r["exit_code"] != 0:
            errors.append("BLOCKED_UNSIGNED")

        try:
            policy = json.loads(read_git_blob(head, POLICY_GIT_PATH).decode("utf-8"))
        except Exception as exc:
            errors.append("BLOCKED_PROFILE_POLICY_READ_FAILED:{}".format(exc))
            result["preflight_errors"] = errors
            return result

        profiles = policy.get("profiles", []) if isinstance(policy, dict) else []
        profile = None
        for p in profiles:
            if isinstance(p, dict) and p.get("profile_id") == PROFILE_ID:
                profile = p
                break
        if profile is None:
            errors.append("BLOCKED_PROFILE_NOT_FOUND")
        else:
            result["profile_found"] = True
            if profile.get("sha256") == PROFILE_SCRIPT_SHA256:
                result["profile_script_sha256_matches"] = True
            else:
                errors.append("BLOCKED_PROFILE_SCRIPT_HASH_MISMATCH")

        contract = policy.get("production_contracts", {})
        if isinstance(contract, dict):
            es = contract.get("execution_state")
            if es == "STATIC_CONTRACT_ONLY_NOT_REGISTERED":
                result["execution_state_static"] = True
            else:
                errors.append("BLOCKED_PRODUCTION_STATE:{}".format(es))
            pg = contract.get("p1_p6_gates")
            if pg == "NOT_RUN":
                result["p1_p6_not_run"] = True
            else:
                errors.append("BLOCKED_P1_P6_STATE:{}".format(pg))

    result["preflight_errors"] = errors
    result["preflight_ok"] = len(errors) == 0
    return result


def json_from_result(tool_name: str, mcp_result: types.CallToolResult) -> dict[str, Any]:
    if mcp_result.isError:
        message = " | ".join(
            item.text for item in mcp_result.content if isinstance(item, types.TextContent)
        )
        raise RuntimeError("MCP_TOOL_ERROR:{}:{}".format(tool_name, message))
    if not isinstance(mcp_result.structuredContent, dict):
        raise RuntimeError("MCP_TOOL_RESULT_MISSING_STRUCTURED_OBJECT:{}".format(tool_name))
    return mcp_result.structuredContent


def validate_producer_report(
    manifest: dict[str, Any], job_state: dict[str, Any], expected_git_head: str
) -> dict[str, Any]:
    files = manifest.get("files")
    if not isinstance(files, list):
        raise RuntimeError("MANIFEST_FILES_INVALID")
    matches = [
        item for item in files
        if isinstance(item, dict) and item.get("relative_path") == PRODUCER_REPORT
    ]
    if len(matches) != 1:
        raise RuntimeError("PRODUCER_REPORT_MISSING_OR_DUPLICATE")
    entry = matches[0]
    if entry.get("report_error") is not None:
        raise RuntimeError("PRODUCER_REPORT_INVALID_JSON")
    report = entry.get("report_json")
    if not isinstance(report, dict):
        raise RuntimeError("PRODUCER_REPORT_NOT_INLINED")
    if (
        report.get("probe") != "v02_preliminary_producer"
        or report.get("status") != "PASS_PARTIAL_CAD_CAPABILITY"
        or report.get("engineering_capability") != "PASS_PARTIAL_CAD_CAPABILITY"
    ):
        raise RuntimeError("PRODUCER_REPORT_STATUS_OR_PROBE_MISMATCH")
    if (
        report.get("formal_006_completion") is not False
        or report.get("p1_stage_gate") != "NOT_RUN"
        or report.get("p1_p6_gates") != "NOT_RUN"
    ):
        raise RuntimeError("PRODUCER_REPORT_CLAIM_BOUNDARY_VIOLATION")
    identity = report.get("identity")
    if not isinstance(identity, dict) or (
        identity.get("git_head") != expected_git_head
        or identity.get("profile_id") != PROFILE_ID
        or identity.get("script_sha256") != PROFILE_SCRIPT_SHA256
        or identity.get("profile_contract_sha256")
        != job_state.get("profile_contract_sha256")
        or identity.get("dependency_manifest_sha256")
        != job_state.get("profile_dependency_manifest_sha256")
        or identity.get("case_id") != CASE_ID
    ):
        raise RuntimeError("PRODUCER_REPORT_IDENTITY_MISMATCH")
    assertions = report.get("assertions")
    if (
        not isinstance(assertions, dict)
        or set(assertions) != EXPECTED_REPORT_ASSERTIONS
        or not all(assertions.values())
    ):
        raise RuntimeError("PRODUCER_REPORT_ASSERTIONS_FAILED")
    if manifest.get("job_id") != job_state.get("job_id"):
        raise RuntimeError("PRODUCER_REPORT_JOB_MISMATCH")
    report_files = report.get("files")
    if not isinstance(report_files, dict) or set(report_files) != set(
        EXPECTED_PRODUCER_ARTIFACTS
    ):
        raise RuntimeError("PRODUCER_REPORT_ARTIFACT_SET_MISMATCH")
    manifest_entries = {}
    for item in files:
        if not isinstance(item, dict):
            continue
        relative = item.get("relative_path")
        if isinstance(relative, str):
            if relative in manifest_entries:
                raise RuntimeError("MANIFEST_DUPLICATE_ARTIFACT_PATH")
            manifest_entries[relative] = item
    for role, expected_name in EXPECTED_PRODUCER_ARTIFACTS.items():
        reported = report_files.get(role)
        entry = manifest_entries.get(expected_name)
        if not isinstance(reported, dict) or not isinstance(entry, dict):
            raise RuntimeError("PRODUCER_ARTIFACT_MISSING:{}".format(role))
        if PureWindowsPath(str(reported.get("path", ""))).name != expected_name:
            raise RuntimeError("PRODUCER_ARTIFACT_PATH_MISMATCH:{}".format(role))
        if (
            not isinstance(reported.get("size"), int)
            or reported["size"] <= 0
            or reported.get("size") != entry.get("size")
            or not isinstance(reported.get("sha256"), str)
            or not re.fullmatch(r"[0-9a-f]{64}", reported["sha256"])
            or reported.get("sha256") != entry.get("sha256")
        ):
            raise RuntimeError("PRODUCER_ARTIFACT_HASH_OR_SIZE_MISMATCH:{}".format(role))
    return report


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


async def run_suite() -> int:
    stamp = (
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        + "_"
        + uuid4().hex[:8]
    )
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    stderr_path = OUTPUT_ROOT / "V02_PRELIMINARY_RUN_MCP_STDERR_{}.log".format(stamp)
    result = {
        "task": "AJM006_V02_PRELIMINARY_PRODUCER",
        "case_id": CASE_ID,
        "profile_id": PROFILE_ID,
        "started_at": utc_now(),
        "ended_at": None,
        "preflight": None,
        "final_status": "FAIL_PRELIMINARY",
        "mcp_package_version": None,
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
            raise RuntimeError(
                "BLOCKED_PREFLIGHT:{}".format(";".join(pf["preflight_errors"]))
            )
        expected_git_head = pf["git_head"]

        if norm(Path(sys.executable)) != norm(EXPECTED_PYTHON):
            raise RuntimeError("BLOCKED_WRONG_RUNNER_INTERPRETER")
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
                        name="airjet-ajm006-v02-preliminary-harness", version="1.0.0"
                    ),
                ) as session:
                    await session.initialize()
                    tool_names = {
                        tool.name for tool in (await session.list_tools()).tools
                    }
                    if tool_names != EXPECTED_TOOLS:
                        raise RuntimeError(
                            "BLOCKED_UNEXPECTED_MCP_TOOLS:{}".format(sorted(tool_names))
                        )

                    inventory = await call_json(session, "inventory")
                    result["inventory"] = inventory
                    if inventory.get("ready") is not True:
                        raise RuntimeError("BLOCKED_INVENTORY_NOT_READY")
                    if inventory.get("git_head") != expected_git_head:
                        raise RuntimeError("BLOCKED_INVENTORY_GIT_HEAD_MISMATCH")
                    approved = set(inventory.get("approved_profiles") or [])
                    if PROFILE_ID not in approved:
                        raise RuntimeError("BLOCKED_PROFILE_NOT_APPROVED")
                    inventory_contracts = inventory.get("profile_contract_sha256")
                    if not isinstance(inventory_contracts, dict):
                        raise RuntimeError("BLOCKED_INVENTORY_PROFILE_CONTRACTS")
                    expected_profile_contract = inventory_contracts.get(PROFILE_ID)
                    if (
                        not isinstance(expected_profile_contract, str)
                        or not re.fullmatch(r"[0-9a-f]{64}", expected_profile_contract)
                    ):
                        raise RuntimeError("BLOCKED_INVENTORY_PROFILE_CONTRACT")

                    state = await call_json(
                        session,
                        "submit_job",
                        {"profile_id": PROFILE_ID, "case_id": CASE_ID},
                    )
                    job_id = state.get("job_id")
                    phase = state.get("phase")
                    if not isinstance(job_id, str) or not job_id or phase != "RUNNING":
                        raise RuntimeError(
                            "SUBMIT_NOT_RUNNING:{}:{}:{}".format(
                                PROFILE_ID, job_id, phase
                            )
                        )
                    expected_submit = {
                        "case_id": CASE_ID,
                        "profile_id": PROFILE_ID,
                        "engine": "spaceclaim",
                        "script_sha256": PROFILE_SCRIPT_SHA256,
                        "profile_contract_sha256": expected_profile_contract,
                        "git_head": expected_git_head,
                        "output_root_id": "p1_cad_006",
                    }
                    for name, expected in expected_submit.items():
                        if state.get(name) != expected:
                            raise RuntimeError("SUBMIT_IDENTITY_MISMATCH:{}".format(name))
                    if state.get("license_arguments_added") is not False:
                        raise RuntimeError("JOB_STATE_INDICATES_LICENSE_ARGUMENTS")
                    if state.get("git_head") != expected_git_head:
                        raise RuntimeError("SUBMIT_GIT_HEAD_DIFFERS_FROM_INVENTORY")
                    dependency_hash = state.get("profile_dependency_manifest_sha256")
                    dependency_artifacts = state.get("profile_dependency_artifacts")
                    if (
                        not isinstance(dependency_hash, str)
                        or not re.fullmatch(r"[0-9a-f]{64}", dependency_hash)
                        or not isinstance(dependency_artifacts, list)
                        or len(dependency_artifacts) != EXPECTED_DEPENDENCY_COUNT
                    ):
                        raise RuntimeError("SUBMIT_DEPENDENCY_BUNDLE_INVALID")
                    result["job_id"] = job_id
                    result["job_state"] = state

                    stable = {
                        name: state.get(name)
                        for name in (
                            "job_id",
                            "case_id",
                            "profile_id",
                            "engine",
                            "script_sha256",
                            "profile_contract_sha256",
                            "profile_dependency_manifest_sha256",
                            "git_head",
                            "output_root_id",
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
                            for name, expected in stable.items():
                                if state.get(name) != expected:
                                    raise RuntimeError(
                                        "JOB_IDENTITY_CHANGED:{}".format(name)
                                    )
                            phase = state.get("phase")
                            if phase != "RUNNING" and phase not in TERMINAL_PHASES:
                                raise RuntimeError(
                                    "UNKNOWN_TERMINAL_PHASE:{}".format(phase)
                                )
                    except BaseException:
                        if phase == "RUNNING":
                            with suppress(BaseException):
                                await call_json(
                                    session, "cancel_job", {"job_id": job_id}
                                )
                        raise

                    result["job_state"] = state

                    manifest = await call_json(
                        session,
                        "artifact_manifest",
                        {"job_id": job_id},
                        timeout_seconds=600,
                    )
                    if (
                        manifest.get("job_id") != job_id
                        or manifest.get("phase") != phase
                    ):
                        raise RuntimeError("MANIFEST_JOB_ID_OR_PHASE_MISMATCH")
                    result["manifest"] = manifest

                    if phase == "PROCESS_EXITED_0":
                        result["producer_report"] = validate_producer_report(
                            manifest, state, expected_git_head
                        )
                        result["final_status"] = "PASS_PRELIMINARY_PRODUCER"
                        exit_code = 0
                    else:
                        result["final_status"] = "FAIL_PRELIMINARY"

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
        print(
            json.dumps(
                {
                    "final_status": result["final_status"],
                    "result_path": str(RESULT_PATH),
                    "exit_code": exit_code,
                },
                sort_keys=True,
            )
        )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run_suite()))

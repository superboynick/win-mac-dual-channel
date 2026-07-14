#!/usr/bin/env python3
"""Run the fixed AJM-005 CAD/Workbench T1 capability pair through MCP."""

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
    "codex-skills/airjet-ansys-automation/scripts/run_t1_cad_suite.py"
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
WB_PROFILE = "ajm005-workbench-transfer-t1-v1"
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
        },
        "assertions": {
            "script_parameterization_equivalent",
            "named_selections",
            "volume_extract_or_equivalent",
            "fluid_connectivity",
            "native_save",
            "native_reopen",
            "step_export_reimport",
        },
    },
    WB_PROFILE: {
        "probe": "workbench_transfer_t1",
        "required_status": "PASS_PARTIAL_CAD_CAPABILITY",
        "report": "workbench_transfer_t1.json",
        "artifacts": {
            "workbench_transfer_t1.wbpj": "project",
            "workbench_model_inspection.json": "model_inspection",
        },
        "assertions": {
            "predecessor_identity",
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
        raise RuntimeError("BLOCKED_T1_CAD_RUNNER_GIT_BLOB_MISSING")
    installed_digest = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    git_digest = hashlib.sha256(completed.stdout).hexdigest()
    if installed_digest != git_digest:
        raise RuntimeError("BLOCKED_T1_CAD_RUNNER_COPY_MISMATCH")
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
    if len(matches) != 1:
        return None
    return matches[0]


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
                and str(declared.get("path", "")).replace("\\", "/").rsplit("/", 1)[-1]
                == artifact
            )
            if not artifacts_ok:
                break
    scope_ok = True
    if profile_id == SC_PROFILE:
        scope_ok = (
            isinstance(report, dict)
            and report.get("native_parameterization") == "NOT_RUN"
            and report.get("p1_cad_hard_gate")
            == "BLOCKED_NATIVE_PARAMETERIZATION"
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
        "p1_stage_gate": "NOT_RUN",
    }


async def run_suite() -> int:
    stamp = (
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        + "_"
        + uuid4().hex[:8]
    )
    case_id = f"ajm005-cad-xfer-{stamp.lower()}"
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    result_path = OUTPUT_ROOT / f"AJM005_T1_CAD_SUITE_{stamp}.json"
    stderr_path = OUTPUT_ROOT / f"AJM005_T1_CAD_SUITE_{stamp}_MCP_STDERR.log"
    result: dict[str, Any] = {
        "schema_version": 1,
        "task": "AJM-WIN-ANSYS-STUDENT-CAPABILITY-SMOKE-005",
        "suite": "cad_and_workbench_transfer_t1",
        "case_id": case_id,
        "started_at": utc_now(),
        "ended_at": None,
        "suite_status": "FAIL_CAD_TRANSFER_SET",
        "p1_cad_toolchain_readiness": "BLOCKED",
        "p1_cad_blocker": "NATIVE_PARAMETERIZATION_NOT_RUN",
        "pass_005_capability": "PARTIAL_CAD_TRANSFER_ONLY",
        "p1_p6_gates": "NOT_RUN",
        "visibility": "NOT_USER_OBSERVED",
        "license_arguments_added": False,
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
            raise RuntimeError("BLOCKED_WRONG_T1_CAD_RUNNER_INTERPRETER")
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
                        name="airjet-ajm005-t1-cad-harness", version="1.0.0"
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
                    approved = set(inventory.get("approved_profiles") or [])
                    required = {SC_PROFILE, WB_PROFILE}
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
                    if all(run.get("capability_pass") for run in result["runs"]):
                        result["suite_status"] = "PASS_CAD_TRANSFER_SET"
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

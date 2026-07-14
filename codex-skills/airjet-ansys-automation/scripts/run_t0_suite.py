#!/usr/bin/env python3
"""Run the fixed AJM-005 T0 control suite through the local MCP protocol."""

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
    "codex-skills/airjet-ansys-automation/scripts/run_t0_suite.py"
)
OUTPUT_ROOT = Path.home() / "Downloads" / "AIRJET_ANSYS_STUDENT_SMOKE_005"
EXPECTED_TOOLS = {
    "inventory",
    "submit_job",
    "poll_job",
    "cancel_job",
    "artifact_manifest",
}
PROFILES = (
    ("ajm005-spaceclaim-t0-v1", "spaceclaim_t0", "spaceclaim_probe.json"),
    ("ajm005-workbench-t0-v1", "workbench_t0", "workbench_probe.json"),
    ("ajm005-pymechanical-t0-v1", "pymechanical_t0", "pymechanical_probe.json"),
    ("ajm005-pyfluent-t0-v1", "pyfluent_t0", "pyfluent_probe.json"),
)
POLL_SECONDS = 1.0
HARD_PROFILE_WAIT_SECONDS = 900
TERMINAL_PHASES = {
    "PROCESS_EXITED_0",
    "FAILED_PROCESS",
    "TIMED_OUT",
    "CANCELLED",
    "FAILED_TERMINATION",
    "FAILED_MONITOR",
    "FAILED_START",
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
        raise RuntimeError("BLOCKED_RUNNER_GIT_BLOB_MISSING")
    installed_digest = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    git_digest = hashlib.sha256(completed.stdout).hexdigest()
    if installed_digest != git_digest:
        raise RuntimeError("BLOCKED_T0_RUNNER_COPY_MISMATCH")
    return installed_digest


def json_from_result(tool_name: str, result: types.CallToolResult) -> dict[str, Any]:
    if result.isError:
        text = " | ".join(
            item.text for item in result.content if isinstance(item, types.TextContent)
        )
        raise RuntimeError(f"MCP_TOOL_ERROR:{tool_name}:{text}")
    structured = result.structuredContent
    if not isinstance(structured, dict):
        raise RuntimeError(f"MCP_TOOL_RESULT_MISSING_STRUCTURED_OBJECT:{tool_name}")
    return structured


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


def declared_report(
    manifest: dict[str, Any], report_name: str
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    files = manifest.get("files")
    if not isinstance(files, list):
        raise RuntimeError("MANIFEST_FILES_NOT_LIST")
    matches = [
        item
        for item in files
        if isinstance(item, dict) and item.get("relative_path") == report_name
    ]
    if len(matches) != 1:
        raise RuntimeError(f"DECLARED_REPORT_CARDINALITY:{report_name}:{len(matches)}")
    report = matches[0].get("report_json")
    return matches[0], report if isinstance(report, dict) else None


async def run_profile(
    session: ClientSession,
    profile_id: str,
    probe_name: str,
    report_name: str,
    stamp: str,
) -> dict[str, Any]:
    case_id = f"ajm005-{profile_id.split('-')[1]}-suite-{stamp.lower()}"
    state = await call_json(
        session,
        "submit_job",
        {"profile_id": profile_id, "case_id": case_id},
    )
    job_id = state.get("job_id")
    phase = state.get("phase")
    if not isinstance(job_id, str) or not job_id:
        raise RuntimeError("SUBMIT_RESULT_MISSING_JOB_ID")
    if phase != "RUNNING":
        raise RuntimeError(f"SUBMIT_DID_NOT_ENTER_RUNNING:{profile_id}:{phase}")
    if state.get("license_arguments_added") is not False:
        raise RuntimeError("JOB_STATE_INDICATES_LICENSE_ARGUMENTS")
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
        session,
        "artifact_manifest",
        {"job_id": job_id},
        timeout_seconds=600,
    )
    if manifest.get("job_id") != job_id or manifest.get("phase") != phase:
        raise RuntimeError("MANIFEST_JOB_ID_OR_PHASE_MISMATCH")
    report_entry, report = declared_report(manifest, report_name)
    control_pass = (
        phase == "PROCESS_EXITED_0"
        and isinstance(report, dict)
        and report.get("probe") == probe_name
        and report.get("status") == "PASS_CONTROL"
        and report.get("engineering_capability") == "NOT_RUN"
        and report.get("license_arguments_added") is False
        and state.get("license_arguments_added") is False
    )
    return {
        "profile_id": profile_id,
        "case_id": case_id,
        "final_state": state,
        "manifest": manifest,
        "declared_report_name": report_name,
        "declared_report_sha256": report_entry.get("sha256"),
        "declared_report": report,
        "control_pass": control_pass,
        "pass_005_capability": "NOT_EVALUATED_T0_ONLY",
        "p1_gate": "NOT_RUN",
    }


async def run_suite() -> int:
    stamp = (
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        + "_"
        + uuid4().hex[:8]
    )
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    result_path = OUTPUT_ROOT / f"AJM005_T0_SUITE_{stamp}.json"
    stderr_path = OUTPUT_ROOT / f"AJM005_T0_SUITE_{stamp}_MCP_STDERR.log"
    result: dict[str, Any] = {
        "schema_version": 1,
        "task": "AJM-WIN-ANSYS-STUDENT-CAPABILITY-SMOKE-005",
        "suite": "official_api_control_t0",
        "started_at": utc_now(),
        "ended_at": None,
        "suite_status": "FAIL_CONTROL_SET",
        "pass_005_capability": "NOT_EVALUATED_T0_ONLY",
        "engineering_capability": "NOT_RUN",
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
            raise RuntimeError("BLOCKED_WRONG_T0_RUNNER_INTERPRETER")
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
                        name="airjet-ajm005-t0-harness", version="1.0.0"
                    ),
                ) as session:
                    initialized = await session.initialize()
                    result["protocol_version"] = initialized.protocolVersion
                    result["server_name"] = initialized.serverInfo.name
                    tools_result = await session.list_tools()
                    tool_names = {tool.name for tool in tools_result.tools}
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
                    required = {profile_id for profile_id, _, _ in PROFILES}
                    if not required.issubset(approved):
                        raise RuntimeError(
                            f"BLOCKED_MISSING_PROFILES:{sorted(required - approved)}"
                        )
                    for profile_id, probe_name, report_name in PROFILES:
                        result["runs"].append(
                            await run_profile(
                                session,
                                profile_id,
                                probe_name,
                                report_name,
                                stamp,
                            )
                        )
                    if len(result["runs"]) == len(PROFILES) and all(
                        run["control_pass"] for run in result["runs"]
                    ):
                        result["suite_status"] = "PASS_CONTROL_SET"
                        exit_code = 0
    except Exception as exc:  # noqa: BLE001 - the report must retain unexpected failures.
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

#!/usr/bin/env python3
"""Run no-ANSYS negative tests for T1 predecessor fail-closed behavior."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
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
SCRIPT_GIT_PATH = (
    "codex-skills/airjet-ansys-automation/scripts/"
    "test_t1_predecessor_negative.py"
)
OUTPUT_ROOT = Path.home() / "Downloads" / "AIRJET_ANSYS_STUDENT_SMOKE_005"


def norm(path: Path) -> str:
    return os.path.normcase(os.path.abspath(str(path)))


def content_text(result: types.CallToolResult) -> str:
    return " | ".join(
        item.text for item in result.content if isinstance(item, types.TextContent)
    )


def require_git_copy(head: str) -> str:
    if not re.fullmatch(r"[0-9a-f]{40}", head):
        raise RuntimeError("BLOCKED_INVALID_INVENTORY_GIT_HEAD")
    completed = subprocess.run(
        ["git", "-C", str(REPO), "show", f"{head}:{SCRIPT_GIT_PATH}"],
        capture_output=True,
        timeout=30,
        check=False,
        stdin=subprocess.DEVNULL,
    )
    if completed.returncode != 0:
        raise RuntimeError("BLOCKED_NEGATIVE_TEST_GIT_BLOB_MISSING")
    installed = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    tracked = hashlib.sha256(completed.stdout).hexdigest()
    if installed != tracked:
        raise RuntimeError("BLOCKED_NEGATIVE_TEST_COPY_MISMATCH")
    return installed


async def call_object(
    session: ClientSession, name: str, arguments: dict[str, Any] | None = None
) -> dict[str, Any]:
    result = await session.call_tool(
        name,
        arguments or {},
        read_timeout_seconds=timedelta(seconds=120),
    )
    if result.isError:
        raise RuntimeError(f"UNEXPECTED_MCP_ERROR:{name}:{content_text(result)}")
    if not isinstance(result.structuredContent, dict):
        raise RuntimeError(f"MISSING_STRUCTURED_RESULT:{name}")
    return result.structuredContent


async def expect_failed_start(
    session: ClientSession,
    profile_id: str,
    case_id: str,
    predecessor_job_id: str,
    expected_error: str,
) -> dict[str, Any]:
    result = await session.call_tool(
        "submit_job",
        {
            "profile_id": profile_id,
            "case_id": case_id,
            "predecessor_job_id": predecessor_job_id,
        },
        read_timeout_seconds=timedelta(seconds=120),
    )
    message = content_text(result)
    if not result.isError or expected_error not in message:
        raise RuntimeError(
            f"EXPECTED_FAIL_CLOSED:{profile_id}:{expected_error}:{message}"
        )
    case_root = OUTPUT_ROOT / case_id
    job_dirs = sorted(path for path in case_root.iterdir() if path.is_dir())
    if len(job_dirs) != 1:
        raise RuntimeError(f"FAILED_START_DIRECTORY_COUNT:{case_id}:{len(job_dirs)}")
    state_path = job_dirs[0] / "job.json"
    if not state_path.is_file():
        raise RuntimeError(f"FAILED_START_STATE_MISSING:{case_id}")
    state = json.loads(state_path.read_text(encoding="utf-8"))
    if (
        state.get("phase") != "FAILED_START"
        or state.get("pid") is not None
        or expected_error not in str(state.get("reason"))
    ):
        raise RuntimeError(f"FAILED_START_STATE_INVALID:{case_id}:{state}")
    return {
        "profile_id": profile_id,
        "case_id": case_id,
        "expected_error": expected_error,
        "observed_tool_error": message,
        "job_id": state.get("job_id"),
        "phase": state.get("phase"),
        "pid": state.get("pid"),
        "state_path": str(state_path),
        "state_sha256": hashlib.sha256(state_path.read_bytes()).hexdigest(),
    }


async def main() -> int:
    stamp = (
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        + "_"
        + uuid4().hex[:8]
    )
    result_path = OUTPUT_ROOT / f"AJM005_T1_PREDECESSOR_NEGATIVE_{stamp}.json"
    stderr_path = OUTPUT_ROOT / f"AJM005_T1_PREDECESSOR_NEGATIVE_{stamp}_MCP_STDERR.log"
    result: dict[str, Any] = {
        "schema_version": 1,
        "task": "AJM-WIN-ANSYS-STUDENT-CAPABILITY-SMOKE-005",
        "suite": "t1_predecessor_negative_no_ansys",
        "status": "FAIL",
        "ansys_started": False,
        "license_data_read": False,
        "git_head": None,
        "test_script_sha256": None,
        "tests": [],
        "error": None,
    }
    exit_code = 2
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    try:
        if norm(Path(sys.executable)) != norm(EXPECTED_PYTHON):
            raise RuntimeError("BLOCKED_WRONG_NEGATIVE_TEST_INTERPRETER")
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
                        name="airjet-t1-predecessor-negative", version="1.0.0"
                    ),
                ) as session:
                    await session.initialize()
                    inventory = await call_object(session, "inventory")
                    if inventory.get("ready") is not True:
                        raise RuntimeError("BLOCKED_INVENTORY_NOT_READY")
                    if inventory.get("license_data_read") is not False:
                        raise RuntimeError("INVENTORY_READ_LICENSE_DATA")
                    head = str(inventory.get("git_head", ""))
                    result["git_head"] = head
                    result["test_script_sha256"] = require_git_copy(head)
                    prefix = f"ajm005-neg-{stamp.lower()}"
                    result["tests"].append(
                        await expect_failed_start(
                            session,
                            "ajm005-workbench-transfer-t1-v1",
                            prefix + "-missing",
                            "",
                            "BLOCKED_REQUIRED_PREDECESSOR_ID",
                        )
                    )
                    result["tests"].append(
                        await expect_failed_start(
                            session,
                            "ajm005-spaceclaim-t0-v1",
                            prefix + "-unexpected",
                            "fake-predecessor",
                            "BLOCKED_UNEXPECTED_PREDECESSOR",
                        )
                    )
                    result["tests"].append(
                        await expect_failed_start(
                            session,
                            "ajm005-workbench-transfer-t1-v1",
                            prefix + "-unknown",
                            "fake-predecessor",
                            "BLOCKED_UNKNOWN_OR_SERVER_RESTARTED_PREDECESSOR",
                        )
                    )
        result["status"] = "PASS"
        exit_code = 0
    except Exception as exc:  # noqa: BLE001 - evidence must preserve surprises.
        result["error"] = {
            "type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
        }
    finally:
        result_path.write_text(
            json.dumps(result, indent=2, sort_keys=True), encoding="utf-8"
        )
        print(
            json.dumps(
                {
                    "status": result["status"],
                    "result_path": str(result_path),
                    "stderr_path": str(stderr_path),
                    "test_count": len(result["tests"]),
                    "exit_code": exit_code,
                },
                sort_keys=True,
            )
        )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

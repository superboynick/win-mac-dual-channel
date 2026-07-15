#!/usr/bin/env python3
"""Run the frozen AJM-005 v2 alternate-route semantic confirmation only."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
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
REPO = Path(r"C:\Users\admin\win-mac-dual-channel")
SERVER = Path.home() / ".codex" / "skills" / "airjet-ansys-automation" / "scripts" / "airjet_ansys_mcp.py"
RUNNER_GIT_PATH = "codex-skills/airjet-ansys-automation/scripts/run_t1_alternate_route_confirmation_suite.py"
SERVER_GIT_PATH = "codex-skills/airjet-ansys-automation/scripts/airjet_ansys_mcp.py"
ROUTE_GIT_PATH = "airjet-simulation/automation/ansys/contracts/ajm005_alternate_route_v2.json"
JUDGMENT_GIT_PATH = "airjet-simulation/automation/ansys/contracts/ajm005_semantic_judgment_v2.json"
CLOSEOUT_HELPER_GIT_PATH = "codex-skills/airjet-ansys-automation/scripts/ajm005_closeout_v2.py"
CLOSEOUT_TEST_GIT_PATH = "codex-skills/airjet-ansys-automation/scripts/test_ajm005_closeout_v2.py"
RUNNER_GUARD_TEST_GIT_PATH = "codex-skills/airjet-ansys-automation/scripts/test_ajm005_runner_guards.py"
SC_PROFILE = "ajm005-spaceclaim-cad-t1-v2"
WB_PROFILE = "ajm005-workbench-semantic-reconstruction-t1-v2"
OUTPUT_ROOT = Path.home() / "Downloads" / "AIRJET_ANSYS_STUDENT_SMOKE_005"
CLOSEOUT_PATH = Path.home() / "Downloads" / "AIRJET_ANSYS_STUDENT_CAPABILITY_SMOKE_005.txt"
EXPECTED_TOOLS = {"inventory", "submit_job", "poll_job", "cancel_job", "artifact_manifest"}
TERMINAL_PHASES = {
    "PROCESS_EXITED_0", "FAILED_PROCESS", "TIMED_OUT", "CANCELLED",
    "FAILED_TERMINATION", "FAILED_MONITOR", "FAILED_START",
}
SUITE_PASS_STATUS = "PASS_ALTERNATE_ROUTE_SEMANTIC_CONFIRMATION"
SUITE_FAIL_STATUS = "FAIL_ALTERNATE_ROUTE_SEMANTIC_CONFIRMATION"
CAD_AUTHORING_ROUTE = "SPACECLAIM_SIGNED_SCRIPT_PARAMETRIC"
SOLVER_HANDOFF_ROUTE = "HASH_BOUND_STEP_SEMANTIC_SIDECAR"
CONNECTED_ROUTE = "DEFERRED_CURRENT_HOST_ROUTE"
POLL_SECONDS = 1.0
HARD_PROFILE_WAIT_SECONDS = 1500
SIGNED_SOURCE_SPECS = {
    "t0_controls": {
        "commit": "92712c7d63f44e1ccafb7a58e8386708b591b287",
        "path": (
            "airjet-simulation/logs/evidence/"
            "AJM005_T0_SUITE_20260714T175525010049Z_2b301826/"
            "suite-summary.json"
        ),
        "blob_sha256": "9ee6a41ca50561e6427950e84e38d9bf039d0b37f090fc0c76c93253cea6891d",
    },
    "cleanup": {
        "commit": "7a93eaa9c8b6c13b5a4f5f03ae2b401945c6b1f8",
        "path": "airjet-simulation/reports/AJM_WIN_ANSYS_STUDENT_CLEANUP_2026-07-14.md",
        "blob_sha256": "1d1087664d3fecc43164dcce2084f8ba3c678da73005fa73def69375900d1f13",
    },
    "p0": {
        "commit": "59e0a296b47f2984606720ec16cf315a0852e625",
        "path": "airjet-simulation/evidence/P0_EVIDENCE_FREEZE_RECORD.md",
        "blob_sha256": "a1a93e1c5e8728e949110c05994b3b1f712a17f7b8889afd10c81e6de9d66456",
    },
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def norm(path: Path) -> str:
    return os.path.normcase(os.path.abspath(str(path)))


def run_git(*args: str, timeout: int = 60) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", "-C", str(REPO), *args], capture_output=True, timeout=timeout,
        check=False, stdin=subprocess.DEVNULL,
    )


def git_blob(head: str, path: str) -> bytes:
    if not re.fullmatch(r"[0-9a-f]{40}", head):
        raise RuntimeError("BLOCKED_INVALID_GIT_HEAD")
    completed = run_git("show", f"{head}:{path}", timeout=30)
    if completed.returncode != 0:
        raise RuntimeError(f"BLOCKED_SIGNED_BLOB_MISSING:{path}")
    return completed.stdout


def git_commit_is_ancestor(commit: str, head: str) -> bool:
    completed = run_git("merge-base", "--is-ancestor", commit, head, timeout=30)
    return completed.returncode == 0


def load_frozen_closeout_helper(head: str, route: dict[str, Any]) -> Any:
    """Load the installed helper only after local/blob/route byte identity agrees."""

    closeout = route.get("closeout")
    if not isinstance(closeout, dict) or set(closeout) != {"helper", "test"}:
        raise RuntimeError("BLOCKED_ROUTE_CLOSEOUT_FIELDS")
    helper_record = closeout.get("helper")
    test_record = closeout.get("test")
    expected_fields = {"git_path", "sha256"}
    if (
        not isinstance(helper_record, dict)
        or set(helper_record) != expected_fields
        or not isinstance(test_record, dict)
        or set(test_record) != expected_fields
        or helper_record.get("git_path") != CLOSEOUT_HELPER_GIT_PATH
        or test_record.get("git_path") != CLOSEOUT_TEST_GIT_PATH
    ):
        raise RuntimeError("BLOCKED_ROUTE_CLOSEOUT_IDENTITY")
    helper_blob = git_blob(head, CLOSEOUT_HELPER_GIT_PATH)
    test_blob = git_blob(head, CLOSEOUT_TEST_GIT_PATH)
    helper_sha = sha256_bytes(helper_blob)
    if (
        helper_record.get("sha256") != helper_sha
        or test_record.get("sha256") != sha256_bytes(test_blob)
    ):
        raise RuntimeError("BLOCKED_ROUTE_CLOSEOUT_HASH")
    installed = Path(__file__).resolve().with_name("ajm005_closeout_v2.py")
    if not installed.is_file() or sha256_file(installed) != helper_sha:
        raise RuntimeError("BLOCKED_CLOSEOUT_HELPER_COPY_MISMATCH")
    spec = importlib.util.spec_from_file_location("airjet_frozen_ajm005_closeout_v2", installed)
    if spec is None or spec.loader is None:
        raise RuntimeError("BLOCKED_CLOSEOUT_HELPER_IMPORT")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_frozen_runner_contract(
    head: str, route: dict[str, Any], runner_blob: bytes
) -> str:
    """Bind the runner and its no-ANSYS guard test to the frozen route."""

    record = route.get("runner")
    if not isinstance(record, dict) or set(record) != {
        "path", "sha256", "guard_test_path", "guard_test_sha256",
    }:
        raise RuntimeError("BLOCKED_ROUTE_RUNNER_FIELDS")
    if (
        record.get("path") != RUNNER_GIT_PATH
        or record.get("guard_test_path") != RUNNER_GUARD_TEST_GIT_PATH
    ):
        raise RuntimeError("BLOCKED_ROUTE_RUNNER_IDENTITY")
    guard_blob = git_blob(head, RUNNER_GUARD_TEST_GIT_PATH)
    if (
        record.get("sha256") != sha256_bytes(runner_blob)
        or record.get("guard_test_sha256") != sha256_bytes(guard_blob)
    ):
        raise RuntimeError("BLOCKED_ROUTE_RUNNER_HASH")
    return sha256_bytes(guard_blob)


def load_signed_composite_sources(head: str) -> dict[str, Any]:
    """Read exact ancestor Git blobs and preserve per-source failure evidence."""

    blobs: dict[str, bytes] = {}
    sources: dict[str, Any] = {
        source_id: {
            "source_commit": spec["commit"],
            "source_path": spec["path"],
            "validation": "FAIL",
            "error": None,
        }
        for source_id, spec in SIGNED_SOURCE_SPECS.items()
    }
    for source_id, spec in SIGNED_SOURCE_SPECS.items():
        commit = spec["commit"]
        path = spec["path"]
        try:
            if not git_commit_is_ancestor(commit, head):
                raise RuntimeError("NOT_ANCESTOR")
            blob = git_blob(commit, path)
            actual_sha = sha256_bytes(blob)
            if actual_sha != spec["blob_sha256"]:
                raise RuntimeError("BLOB_SHA256_MISMATCH")
            blobs[source_id] = blob
            sources[source_id]["source_blob_sha256"] = actual_sha
        except Exception as exc:
            sources[source_id]["error"] = f"{type(exc).__name__}:{exc}"

    expected_profiles = {
        "ajm005-spaceclaim-t0-v1": "spaceclaim",
        "ajm005-workbench-t0-v1": "workbench",
        "ajm005-pymechanical-t0-v1": "pymechanical",
        "ajm005-pyfluent-t0-v1": "pyfluent",
    }
    if "t0_controls" in blobs:
        try:
            t0 = json.loads(blobs["t0_controls"].decode("utf-8", "strict"))
            runs = t0.get("runs")
            by_profile = {
                item.get("profile_id"): item
                for item in runs
                if isinstance(item, dict) and isinstance(item.get("profile_id"), str)
            } if isinstance(runs, list) else {}
            if (
                t0.get("schema_version") != 1
                or t0.get("suite") != "official_api_control_t0"
                or t0.get("suite_status") != "PASS_CONTROL_SET"
                or t0.get("engineering_capability") != "NOT_RUN"
                or t0.get("pass_005_capability") != "NOT_EVALUATED_T0_ONLY"
                or t0.get("p1_p6_gates") != "NOT_RUN"
                or set(by_profile) != set(expected_profiles)
                or any(
                    by_profile[profile_id].get("engine") != engine
                    or by_profile[profile_id].get("phase") != "PROCESS_EXITED_0"
                    or by_profile[profile_id].get("control_status") != "PASS_CONTROL"
                    for profile_id, engine in expected_profiles.items()
                )
                or not isinstance(
                    by_profile["ajm005-spaceclaim-t0-v1"].get("native_artifact"), dict
                )
            ):
                raise RuntimeError("STATUS_MARKER_MISMATCH")
            sources["t0_controls"].update(
                {
                    "validation": "PASS",
                    "error": None,
                    "suite_status": "PASS_CONTROL_SET",
                    "engineering_capability": "NOT_RUN",
                    "pass_005_capability": "NOT_EVALUATED_T0_ONLY",
                    "p1_p6_gates": "NOT_RUN",
                }
            )
        except Exception as exc:
            sources["t0_controls"]["error"] = f"{type(exc).__name__}:{exc}"

    if "cleanup" in blobs:
        try:
            cleanup = blobs["cleanup"].decode("utf-8", "strict")
            required_markers = (
                "WINDOWS_ANSYS_STUDENT_CLEANUP_STATUS=PASS",
                r"D:\ansys\ANSYS Inc\ANSYS Student\v261",
                "Authenticode=Valid",
                "RunWB2.exe",
                "fluent.exe",
                "ansys.exe",
                "SpaceClaim.exe",
            )
            if any(marker not in cleanup for marker in required_markers):
                raise RuntimeError("STATUS_MARKER_MISMATCH")
            sources["cleanup"].update(
                {
                    "validation": "PASS",
                    "error": None,
                    "cleanup_status": "PASS",
                    "official_exe_signatures": "PASS",
                }
            )
        except Exception as exc:
            sources["cleanup"]["error"] = f"{type(exc).__name__}:{exc}"

    if "p0" in blobs:
        try:
            p0 = blobs["p0"].decode("utf-8", "strict")
            p0_marker = "Gate\uFF1A**PASS - P0 evidence freeze v1**"
            if p0_marker not in p0:
                raise RuntimeError("STATUS_MARKER_MISMATCH")
            sources["p0"].update(
                {"validation": "PASS", "error": None, "p0_stage_gate": "PASS"}
            )
        except Exception as exc:
            sources["p0"]["error"] = f"{type(exc).__name__}:{exc}"
    return sources


def preflight() -> dict[str, Any]:
    observations: dict[str, subprocess.CompletedProcess[bytes] | None] = {}
    errors: list[str] = []
    commands = {
        "fetch": (("fetch", "origin"), 120),
        "branch": (("branch", "--show-current"), 60),
        "status": (("status", "--porcelain"), 60),
        "divergence": (("rev-list", "--left-right", "--count", "HEAD...origin/main"), 60),
        "head": (("rev-parse", "HEAD"), 60),
    }
    for name, (arguments, timeout) in commands.items():
        try:
            observations[name] = run_git(*arguments, timeout=timeout)
        except Exception as exc:
            observations[name] = None
            errors.append(f"{name}:{type(exc).__name__}:{exc}")

    fetch = observations["fetch"]
    branch = observations["branch"]
    status = observations["status"]
    divergence = observations["divergence"]
    head = observations["head"]
    try:
        audit = subprocess.run(
            [
                "powershell", "-ExecutionPolicy", "Bypass", "-File",
                str(REPO / "audit-airjet-project.ps1"), "-RepoRoot", str(REPO),
            ],
            capture_output=True, text=True, timeout=300, check=False,
            stdin=subprocess.DEVNULL,
        )
    except Exception as exc:
        audit = None
        errors.append(f"audit:{type(exc).__name__}:{exc}")

    branch_text = branch.stdout.decode("utf-8", "replace").strip() if branch and branch.returncode == 0 else None
    divergence_text = divergence.stdout.decode("utf-8", "replace").strip() if divergence and divergence.returncode == 0 else None
    head_text = head.stdout.decode("ascii", "replace").strip() if head and head.returncode == 0 else None
    values = {
        "git_fetch": fetch.returncode == 0 if fetch is not None else None,
        "branch": branch_text,
        "git_clean": (not status.stdout) if status is not None and status.returncode == 0 else None,
        "ahead_behind": divergence_text,
        "git_head": head_text,
        "project_audit": audit.returncode == 0 if audit is not None else None,
        "project_audit_stdout": audit.stdout if audit is not None else "",
        "project_audit_stderr": audit.stderr if audit is not None else "",
        "preflight_errors": errors,
    }
    values["signed_composite_sources"] = (
        load_signed_composite_sources(head_text)
        if isinstance(head_text, str) and re.fullmatch(r"[0-9a-f]{40}", head_text)
        else {}
    )
    values["preflight_ok"] = bool(
        values["git_fetch"]
        and values["branch"] == "main"
        and values["git_clean"]
        and values["ahead_behind"] == "0\t0"
        and isinstance(values["git_head"], str)
        and re.fullmatch(r"[0-9a-f]{40}", values["git_head"])
        and values["project_audit"]
        and set(values["signed_composite_sources"]) == set(SIGNED_SOURCE_SPECS)
        and all(
            source.get("validation") == "PASS"
            for source in values["signed_composite_sources"].values()
        )
    )
    return values


def json_from_result(name: str, result: types.CallToolResult) -> dict[str, Any]:
    if result.isError:
        message = " | ".join(
            item.text for item in result.content if isinstance(item, types.TextContent)
        )
        raise RuntimeError(f"MCP_TOOL_ERROR:{name}:{message}")
    if not isinstance(result.structuredContent, dict):
        raise RuntimeError(f"MCP_RESULT_NOT_OBJECT:{name}")
    return result.structuredContent


async def call_json(
    session: ClientSession, name: str, arguments: dict[str, Any] | None = None,
    timeout_seconds: int = 120,
) -> dict[str, Any]:
    result = await session.call_tool(
        name, arguments or {},
        read_timeout_seconds=timedelta(seconds=timeout_seconds),
    )
    return json_from_result(name, result)


def manifest_file(manifest: dict[str, Any], relative_path: str) -> dict[str, Any] | None:
    matches = [
        item for item in manifest.get("files", [])
        if isinstance(item, dict) and item.get("relative_path") == relative_path
    ]
    return matches[0] if len(matches) == 1 else None


def new_run_record(
    profile_id: str, case_id: str, predecessor_job_id: str = ""
) -> dict[str, Any]:
    return {
        "profile_id": profile_id,
        "case_id": case_id,
        "predecessor_job_id": predecessor_job_id or None,
        "submitted": False,
        "reached_terminal": False,
        "initial_state": None,
        "final_state": None,
        "manifest": None,
        "declared_report_name": None,
        "declared_report_sha256": None,
        "declared_report": None,
        "capability_pass": False,
        "capability_status": "NOT_RUN",
        "cancel_attempted": False,
        "cancel_succeeded": False,
        "validation_error": None,
        "p1_stage_gate": "NOT_RUN",
    }


async def run_profile(
    session: ClientSession,
    profile_id: str,
    case_id: str,
    git_head: str,
    profile_hash: str,
    judgment: dict[str, Any],
    predecessor_job_id: str = "",
    run_record: dict[str, Any] | None = None,
) -> dict[str, Any]:
    record = run_record if isinstance(run_record, dict) else new_run_record(
        profile_id, case_id, predecessor_job_id
    )
    producer = profile_id == SC_PROFILE
    report_name = (
        "spaceclaim_cad_t1_v2.json" if producer
        else "workbench_semantic_reconstruction_t1_v2.json"
    )
    required_status = (
        judgment["producer_required_status"] if producer
        else judgment["consumer_required_status"]
    )
    assertion_field = "assertions" if producer else "alternate_route_assertions"
    required_assertions = (
        judgment["producer_required_assertions"] if producer
        else judgment["consumer_required_assertions"]
    )
    required_artifacts = (
        {
            "spaceclaim_cad_t1.json", "spaceclaim_cad_t1_v2.json",
            "spaceclaim_cad_t1.scdocx", "spaceclaim_cad_t1.step",
            "spaceclaim_semantic_sidecar_v2.json",
            "spaceclaim_semantic_binding_v2.json",
        }
        if producer
        else {
            "workbench_semantic_reconstruction_t1.json",
            "workbench_semantic_reconstruction_t1_v2.json",
            "workbench_semantic_reconstruction_inspection.json",
            "semantic_key_cardinality_report_v2.json",
            "workbench_semantic_reconstruction_t1.wbpj",
        }
    )
    state: dict[str, Any] | None = None
    job_id: str | None = None
    try:
        state = await call_json(
            session, "submit_job",
            {
                "profile_id": profile_id,
                "case_id": case_id,
                "predecessor_job_id": predecessor_job_id,
            },
        )
        record["submitted"] = True
        record["capability_status"] = "FAIL"
        record["initial_state"] = state
        record["final_state"] = state
        job_id = state.get("job_id")
        if not isinstance(job_id, str) or state.get("phase") != "RUNNING":
            raise RuntimeError(f"SUBMIT_NOT_RUNNING:{profile_id}:{state}")
        stable = {
            key: state.get(key) for key in (
                "job_id", "case_id", "profile_id", "engine", "script_sha256",
                "profile_contract_sha256", "git_head", "output_root_id",
                "predecessor_job_id", "profile_dependency_manifest_sha256",
            )
        }
        if (
            stable["case_id"] != case_id
            or stable["profile_id"] != profile_id
            or stable["predecessor_job_id"] != (predecessor_job_id or None)
            or stable["git_head"] != git_head
            or stable["profile_contract_sha256"] != profile_hash
            or state.get("license_arguments_added") is not False
            or not re.fullmatch(r"[0-9a-f]{64}", str(stable["profile_dependency_manifest_sha256"]))
            or len(state.get("profile_dependency_artifacts") or []) != 5
        ):
            raise RuntimeError(f"SUBMIT_IDENTITY_INVALID:{profile_id}")
        phase = state["phase"]
        deadline = time.monotonic() + HARD_PROFILE_WAIT_SECONDS
        while phase == "RUNNING":
            if time.monotonic() >= deadline:
                state = await call_json(session, "cancel_job", {"job_id": job_id})
                record["cancel_attempted"] = True
                record["cancel_succeeded"] = state.get("phase") != "RUNNING"
                record["final_state"] = state
                phase = state.get("phase")
                break
            await asyncio.sleep(POLL_SECONDS)
            state = await call_json(session, "poll_job", {"job_id": job_id})
            record["final_state"] = state
            for key, expected in stable.items():
                if state.get(key) != expected:
                    raise RuntimeError(f"JOB_IDENTITY_CHANGED:{profile_id}:{key}")
            phase = state.get("phase")
            if phase != "RUNNING" and phase not in TERMINAL_PHASES:
                raise RuntimeError(f"UNKNOWN_PHASE:{phase}")
        record["reached_terminal"] = phase in TERMINAL_PHASES
        record["final_state"] = state
        manifest = await call_json(
            session, "artifact_manifest", {"job_id": job_id}, timeout_seconds=600
        )
        record["manifest"] = manifest
        report_entry = manifest_file(manifest, report_name)
        report = report_entry.get("report_json") if report_entry else None
        assertions = report.get(assertion_field) if isinstance(report, dict) else None
        artifacts_ok = all(
            isinstance(manifest_file(manifest, path), dict)
            and int(manifest_file(manifest, path).get("size", 0)) > 0
            and re.fullmatch(r"[0-9a-f]{64}", str(manifest_file(manifest, path).get("sha256", "")))
            for path in required_artifacts
        )
        boundary_ok = (
            isinstance(report, dict)
            and report.get("p1_stage_gate") == "NOT_RUN"
            and report.get("external_native_attach") == "NOT_PROVEN"
            and report.get("native_parameterization") == "NOT_PROVEN"
            and report.get("native_named_selection_transfer") == "NOT_PROVEN"
            and report.get("cad_authoring_route") == "SPACECLAIM_SIGNED_SCRIPT_PARAMETRIC"
            and report.get("solver_handoff_route") == "HASH_BOUND_STEP_SEMANTIC_SIDECAR"
        )
        capability_pass = (
            phase == "PROCESS_EXITED_0"
            and isinstance(report, dict)
            and report.get("status") == required_status
            and report.get("engineering_capability") == required_status
            and report.get("probe")
            == ("spaceclaim_cad_t1_v2" if producer else "workbench_semantic_reconstruction_t1_v2")
            and isinstance(assertions, dict)
            and all(assertions.get(name) is True for name in required_assertions)
            and artifacts_ok
            and boundary_ok
        )
        record.update(
            {
                "declared_report_name": report_name,
                "declared_report_sha256": report_entry.get("sha256") if report_entry else None,
                "declared_report": report,
                "capability_pass": capability_pass,
                "capability_status": "PASS" if capability_pass else "FAIL",
            }
        )
        return record
    except BaseException as exc:
        record["validation_error"] = f"{type(exc).__name__}:{exc}"
        raise
    finally:
        current_phase = state.get("phase") if isinstance(state, dict) else None
        if current_phase == "RUNNING" and isinstance(job_id, str):
            record["cancel_attempted"] = True
            try:
                cancelled = await call_json(session, "cancel_job", {"job_id": job_id})
                record["final_state"] = cancelled
                record["cancel_succeeded"] = cancelled.get("phase") != "RUNNING"
                record["reached_terminal"] = cancelled.get("phase") in TERMINAL_PHASES
            except BaseException as cancel_error:
                record["cancel_succeeded"] = False
                record["validation_error"] = (
                    (record.get("validation_error") or "")
                    + f"|CANCEL:{type(cancel_error).__name__}:{cancel_error}"
                ).lstrip("|")


def write_closeout(result: dict[str, Any], result_path: Path, helper: Any) -> None:
    values = helper.build_closeout_values(result, result_path)
    CLOSEOUT_PATH.write_bytes(helper.render_closeout_ascii(values))


async def run_suite() -> int:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "_" + uuid4().hex[:8]
    case_id = "ajm005-alt-" + uuid4().hex[:12]
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    result_path = OUTPUT_ROOT / f"AJM005_T1_ALTERNATE_ROUTE_SUITE_{stamp}.json"
    stderr_path = OUTPUT_ROOT / f"AJM005_T1_ALTERNATE_ROUTE_SUITE_{stamp}_MCP_STDERR.log"
    result: dict[str, Any] = {
        "schema_version": 1,
        "task": "AJM-WIN-ANSYS-STUDENT-CAPABILITY-SMOKE-005",
        "suite": "alternate_step_semantic_confirmation_v2",
        "case_id": case_id,
        "started_at": utc_now(),
        "ended_at": None,
        "suite_status": SUITE_FAIL_STATUS,
        "p1_cad_toolchain_readiness": "BLOCKED",
        "p1_cad_toolchain_scope": "ALTERNATE_ROUTE_ONLY",
        "cad_authoring_route": CAD_AUTHORING_ROUTE,
        "solver_handoff_route": SOLVER_HANDOFF_ROUTE,
        "connected_route": CONNECTED_ROUTE,
        "external_native_attach": "NOT_PROVEN",
        "native_parameterization": "NOT_PROVEN",
        "native_named_selection_transfer": "NOT_PROVEN",
        "p1_stage_gate": "NOT_RUN",
        "p1_p6_gates": "NOT_RUN",
        "visibility": "NOT_USER_OBSERVED",
        "license_data_read": False,
        "git_head": None,
        "preflight": None,
        "inventory": None,
        "runner_sha256": None,
        "route_contract_sha256": None,
        "judgment_sha256": None,
        "closeout_helper_sha256": None,
        "runner_guard_test_sha256": None,
        "runs": [],
        "error": None,
    }
    exit_code = 2
    closeout_helper: Any | None = None
    try:
        if norm(Path(sys.executable)) != norm(EXPECTED_PYTHON):
            raise RuntimeError("BLOCKED_WRONG_ALTERNATE_ROUTE_RUNNER_INTERPRETER")
        if version("mcp") != "1.28.1":
            raise RuntimeError("BLOCKED_UNEXPECTED_MCP_VERSION")
        result["preflight"] = preflight()
        result["git_head"] = result["preflight"]["git_head"]
        head = result["git_head"]
        runner_blob = git_blob(head, RUNNER_GIT_PATH)
        if sha256_file(Path(__file__)) != sha256_bytes(runner_blob):
            raise RuntimeError("BLOCKED_ALTERNATE_ROUTE_RUNNER_COPY_MISMATCH")
        result["runner_sha256"] = sha256_bytes(runner_blob)
        route_blob = git_blob(head, ROUTE_GIT_PATH)
        judgment_blob = git_blob(head, JUDGMENT_GIT_PATH)
        route = json.loads(route_blob)
        judgment = json.loads(judgment_blob)
        if route.get("route") != {
            "cad_authoring": CAD_AUTHORING_ROUTE,
            "solver_handoff": SOLVER_HANDOFF_ROUTE,
            "connected_route": CONNECTED_ROUTE,
            "step_is_route_hard_requirement": True,
        }:
            raise RuntimeError("BLOCKED_ROUTE_EXECUTION_BOUNDARY")
        if judgment.get("suite_pass_status") != SUITE_PASS_STATUS:
            raise RuntimeError("BLOCKED_JUDGMENT_SUITE_STATUS")
        result["runner_guard_test_sha256"] = verify_frozen_runner_contract(
            head, route, runner_blob
        )
        closeout_helper = load_frozen_closeout_helper(head, route)
        result["closeout_helper_sha256"] = route["closeout"]["helper"]["sha256"]
        result["route_contract_sha256"] = sha256_bytes(route_blob)
        result["judgment_sha256"] = sha256_bytes(judgment_blob)
        if route["mcp_server"]["sha256"] != sha256_bytes(git_blob(head, SERVER_GIT_PATH)):
            raise RuntimeError("BLOCKED_ROUTE_SERVER_HASH")
        if result["preflight"].get("preflight_ok") is not True:
            raise RuntimeError("BLOCKED_PREFLIGHT:" + json.dumps(
                result["preflight"], ensure_ascii=True, sort_keys=True
            ))
        parameters = StdioServerParameters(
            command=str(EXPECTED_PYTHON), args=["-I", "-B", str(SERVER)],
            cwd=str(REPO), encoding="utf-8", encoding_error_handler="strict",
        )
        with stderr_path.open("w", encoding="utf-8") as errlog:
            async with stdio_client(parameters, errlog=errlog) as streams:
                async with ClientSession(
                    *streams, read_timeout_seconds=timedelta(seconds=120),
                    client_info=types.Implementation(
                        name="airjet-ajm005-alternate-route-v2", version="1.0.0"
                    ),
                ) as session:
                    await session.initialize()
                    tools = {tool.name for tool in (await session.list_tools()).tools}
                    if tools != EXPECTED_TOOLS:
                        raise RuntimeError(f"BLOCKED_UNEXPECTED_MCP_TOOLS:{tools}")
                    inventory = await call_json(session, "inventory")
                    result["inventory"] = inventory
                    if inventory.get("ready") is not True or inventory.get("git_head") != head:
                        raise RuntimeError("BLOCKED_INVENTORY_IDENTITY")
                    if inventory.get("license_data_read") is not False:
                        raise RuntimeError("INVENTORY_READ_LICENSE_DATA")
                    profile_hashes = inventory.get("profile_contract_sha256", {})
                    for profile_id, role in ((SC_PROFILE, "producer"), (WB_PROFILE, "consumer")):
                        if profile_hashes.get(profile_id) != route[role]["profile_contract_sha256"]:
                            raise RuntimeError(f"BLOCKED_PROFILE_CONTRACT_HASH:{profile_id}")
                    sc_run = new_run_record(SC_PROFILE, case_id)
                    result["runs"].append(sc_run)
                    await run_profile(
                        session, SC_PROFILE, case_id, head,
                        profile_hashes[SC_PROFILE], judgment, run_record=sc_run,
                    )
                    if not sc_run["capability_pass"]:
                        raise RuntimeError("ALTERNATE_ROUTE_PRODUCER_FAILED")
                    wb_run = new_run_record(
                        WB_PROFILE, case_id, sc_run["final_state"]["job_id"]
                    )
                    result["runs"].append(wb_run)
                    await run_profile(
                        session, WB_PROFILE, case_id, head, profile_hashes[WB_PROFILE],
                        judgment, sc_run["final_state"]["job_id"], run_record=wb_run,
                    )
                    if not wb_run["capability_pass"]:
                        raise RuntimeError("ALTERNATE_ROUTE_CONSUMER_FAILED")
                    result["suite_status"] = SUITE_PASS_STATUS
                    result["p1_cad_toolchain_readiness"] = "PASS"
                    exit_code = 0
    except Exception as exc:
        result["error"] = {
            "type": type(exc).__name__, "message": str(exc),
            "traceback": traceback.format_exc(),
        }
    finally:
        result["ended_at"] = utc_now()
        result_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
        if closeout_helper is not None:
            try:
                write_closeout(result, result_path, closeout_helper)
            except BaseException as closeout_error:
                result["closeout_write_error"] = {
                    "type": type(closeout_error).__name__,
                    "message": str(closeout_error),
                    "traceback": traceback.format_exc(),
                }
                result["suite_status"] = SUITE_FAIL_STATUS
                result["p1_cad_toolchain_readiness"] = "BLOCKED"
                exit_code = 2
                result_path.write_text(
                    json.dumps(result, indent=2, sort_keys=True), encoding="utf-8"
                )
        else:
            result["closeout_write_error"] = "BLOCKED_CLOSEOUT_HELPER_NOT_VERIFIED"
            result["suite_status"] = SUITE_FAIL_STATUS
            result["p1_cad_toolchain_readiness"] = "BLOCKED"
            exit_code = 2
            result_path.write_text(
                json.dumps(result, indent=2, sort_keys=True), encoding="utf-8"
            )
        print(json.dumps({
            "suite_status": result["suite_status"],
            "result_path": str(result_path),
            "closeout_path": str(CLOSEOUT_PATH),
            "stderr_path": str(stderr_path),
            "exit_code": exit_code,
        }, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run_suite()))

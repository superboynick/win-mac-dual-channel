#!/usr/bin/env python3
"""Run one hash-bound V02 producer -> Workbench topology observer suite."""

from __future__ import annotations

import asyncio
from contextlib import suppress
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path, PureWindowsPath
import re
import sys
import time
import traceback
from typing import Any
from uuid import uuid4

from importlib.metadata import version
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client

import run_v02_preliminary_006 as producer_runner


EXPECTED_PYTHON = producer_runner.EXPECTED_PYTHON
SERVER = producer_runner.SERVER
REPO = producer_runner.REPO
OUTPUT_ROOT = producer_runner.OUTPUT_ROOT
RESULT_PATH = OUTPUT_ROOT / "V02_TOPOLOGY_OBSERVER_RUN_SUMMARY.json"
POLICY_GIT_PATH = producer_runner.POLICY_GIT_PATH
PRODUCER_PROFILE_ID = producer_runner.PROFILE_ID
PRODUCER_SCRIPT_SHA256 = producer_runner.PROFILE_SCRIPT_SHA256
OBSERVER_PROFILE_ID = "ajm006-workbench-v02-topology-observer-v1"
OBSERVER_SCRIPT_SHA256 = (
    "dd38228bedbfe13c790ad75146232dd146997e5055ddb2b9eb6ae78768b6842c"
)
CASE_ID = producer_runner.CASE_ID
EXPECTED_TOOLS = producer_runner.EXPECTED_TOOLS
TERMINAL_PHASES = producer_runner.TERMINAL_PHASES
POLL_SECONDS = 1.0
PRODUCER_WAIT_SECONDS = 7200
OBSERVER_WAIT_SECONDS = 3600
EXPECTED_PRODUCER_DEPENDENCIES = producer_runner.EXPECTED_DEPENDENCY_COUNT
EXPECTED_PREDECESSOR_ARTIFACTS = {
    "v02_preliminary_producer.json",
    "product.step",
    "v02_face_inventory.json",
    "native_reopen.json",
    "step_reimport.json",
}
OBSERVER_REPORT = "v02_preliminary_topology_observer.json"
EXPECTED_OBSERVER_FILES = {
    "inspection": "v02_solver_topology_inventory.json",
    "project": "v02_preliminary_topology_observer.wbpj",
}
EXPECTED_OBSERVER_ASSERTIONS = {
    "predecessor_identity",
    "predecessor_immutable",
    "workbench_import",
    "solver_entity_inventory",
    "topology_classified",
    "project_save",
    "artifact_hashes",
    "claim_boundaries",
}
VALID_TOPOLOGY_RESULTS = {
    "972_SHARED_SINGLE_FACE",
    "972_COINCIDENT_FACE_PAIRS",
    "DOWNSTREAM_HEALED_SINGLE_FACE",
    "MIXED_OR_OTHER",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def norm(path: Path) -> str:
    return os.path.normcase(os.path.abspath(str(path)))


def combined_preflight() -> dict[str, Any]:
    result = producer_runner.preflight()
    result["observer_profile_found"] = False
    result["observer_script_sha256_matches"] = False
    errors = list(result.get("preflight_errors") or [])
    head = result.get("git_head")
    if isinstance(head, str) and re.fullmatch(r"[0-9a-f]{40}", head):
        try:
            policy = json.loads(
                producer_runner.read_git_blob(head, POLICY_GIT_PATH).decode("utf-8")
            )
            matches = [
                item for item in policy.get("profiles", [])
                if isinstance(item, dict)
                and item.get("profile_id") == OBSERVER_PROFILE_ID
            ]
            if len(matches) != 1:
                errors.append("BLOCKED_OBSERVER_PROFILE_NOT_UNIQUE")
            else:
                profile = matches[0]
                result["observer_profile_found"] = True
                if profile.get("sha256") == OBSERVER_SCRIPT_SHA256:
                    result["observer_script_sha256_matches"] = True
                else:
                    errors.append("BLOCKED_OBSERVER_SCRIPT_HASH_MISMATCH")
                predecessor = profile.get("predecessor")
                if (
                    profile.get("engine") != "workbench"
                    or profile.get("script")
                    != "006/v02_preliminary_topology_observer.wbjn"
                    or profile.get("output_root_id") != "p1_cad_006"
                    or profile.get("reports") != [OBSERVER_REPORT]
                    or not isinstance(predecessor, dict)
                    or predecessor.get("profile_id") != PRODUCER_PROFILE_ID
                    or set(predecessor.get("artifacts") or [])
                    != EXPECTED_PREDECESSOR_ARTIFACTS
                ):
                    errors.append("BLOCKED_OBSERVER_PROFILE_CONTRACT")
        except Exception as exc:
            errors.append(
                "BLOCKED_OBSERVER_PROFILE_READ_FAILED:{}".format(exc)
            )
    result["preflight_errors"] = errors
    result["preflight_ok"] = bool(
        result.get("preflight_ok")
        and result["observer_profile_found"]
        and result["observer_script_sha256_matches"]
        and not errors
    )
    return result


def json_from_result(
    tool_name: str, mcp_result: types.CallToolResult
) -> dict[str, Any]:
    return producer_runner.json_from_result(tool_name, mcp_result)


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


def validate_submit_state(
    state: dict[str, Any],
    *,
    profile_id: str,
    engine: str,
    script_sha256: str,
    profile_contract_sha256: str,
    git_head: str,
    predecessor_job_id: str | None,
) -> None:
    expected = {
        "case_id": CASE_ID,
        "profile_id": profile_id,
        "engine": engine,
        "script_sha256": script_sha256,
        "profile_contract_sha256": profile_contract_sha256,
        "git_head": git_head,
        "output_root_id": "p1_cad_006",
        "predecessor_job_id": predecessor_job_id,
    }
    for name, value in expected.items():
        if state.get(name) != value:
            raise RuntimeError(
                "SUBMIT_IDENTITY_MISMATCH:{}:{}".format(profile_id, name)
            )
    if state.get("phase") != "RUNNING":
        raise RuntimeError("SUBMIT_NOT_RUNNING:{}".format(profile_id))
    if state.get("license_arguments_added") is not False:
        raise RuntimeError("JOB_STATE_INDICATES_LICENSE_ARGUMENTS")


async def wait_terminal(
    session: ClientSession,
    initial: dict[str, Any],
    wait_seconds: int,
) -> dict[str, Any]:
    state = initial
    job_id = state["job_id"]
    phase = state["phase"]
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
            "predecessor_job_id",
        )
    }
    deadline = time.monotonic() + wait_seconds
    try:
        while phase == "RUNNING":
            if time.monotonic() >= deadline:
                state = await call_json(
                    session, "cancel_job", {"job_id": job_id}
                )
                break
            await asyncio.sleep(POLL_SECONDS)
            state = await call_json(session, "poll_job", {"job_id": job_id})
            for name, expected in stable.items():
                if state.get(name) != expected:
                    raise RuntimeError("JOB_IDENTITY_CHANGED:{}".format(name))
            phase = state.get("phase")
            if phase != "RUNNING" and phase not in TERMINAL_PHASES:
                raise RuntimeError("UNKNOWN_TERMINAL_PHASE:{}".format(phase))
    except BaseException:
        if phase == "RUNNING":
            with suppress(BaseException):
                await call_json(session, "cancel_job", {"job_id": job_id})
        raise
    return state


def validate_observer_report(
    manifest: dict[str, Any],
    job_state: dict[str, Any],
    expected_git_head: str,
    predecessor_job_id: str,
) -> dict[str, Any]:
    files = manifest.get("files")
    if not isinstance(files, list):
        raise RuntimeError("OBSERVER_MANIFEST_FILES_INVALID")
    by_relative: dict[str, dict[str, Any]] = {}
    for item in files:
        if not isinstance(item, dict) or not isinstance(
            item.get("relative_path"), str
        ):
            continue
        relative = item["relative_path"]
        if relative in by_relative:
            raise RuntimeError("OBSERVER_MANIFEST_DUPLICATE_PATH")
        by_relative[relative] = item
    entry = by_relative.get(OBSERVER_REPORT)
    if not isinstance(entry, dict) or entry.get("report_error") is not None:
        raise RuntimeError("OBSERVER_REPORT_MISSING_OR_INVALID")
    report = entry.get("report_json")
    if not isinstance(report, dict):
        raise RuntimeError("OBSERVER_REPORT_NOT_INLINED")
    if (
        report.get("probe") != "v02_preliminary_topology_observer"
        or report.get("status")
        != "PASS_PRELIMINARY_TOPOLOGY_OBSERVATION"
        or report.get("engineering_capability")
        != "PASS_PRELIMINARY_TOPOLOGY_OBSERVATION"
    ):
        raise RuntimeError("OBSERVER_REPORT_STATUS_OR_PROBE_MISMATCH")
    if (
        report.get("formal_006_completion") is not False
        or report.get("p1_stage_gate") != "NOT_RUN"
        or report.get("p1_p6_gates") != "NOT_RUN"
        or report.get("diagnostic_only") is not True
        or report.get("license_arguments_added") is not False
    ):
        raise RuntimeError("OBSERVER_CLAIM_BOUNDARY_VIOLATION")
    identity = report.get("identity")
    if not isinstance(identity, dict) or (
        identity.get("git_head") != expected_git_head
        or identity.get("profile_id") != OBSERVER_PROFILE_ID
        or identity.get("script_sha256") != OBSERVER_SCRIPT_SHA256
        or identity.get("profile_contract_sha256")
        != job_state.get("profile_contract_sha256")
        or identity.get("case_id") != CASE_ID
    ):
        raise RuntimeError("OBSERVER_REPORT_IDENTITY_MISMATCH")
    if (
        report.get("predecessor_job_id") != predecessor_job_id
        or report.get("predecessor", {}).get("job_id") != predecessor_job_id
        or report.get("predecessor", {}).get("profile_id")
        != PRODUCER_PROFILE_ID
    ):
        raise RuntimeError("OBSERVER_PREDECESSOR_IDENTITY_MISMATCH")
    assertions = report.get("assertions")
    if (
        not isinstance(assertions, dict)
        or set(assertions) != EXPECTED_OBSERVER_ASSERTIONS
        or not all(assertions.values())
    ):
        raise RuntimeError("OBSERVER_ASSERTIONS_FAILED")
    topology_result = report.get("topology_result")
    summary = report.get("observer_summary")
    if (
        topology_result not in VALID_TOPOLOGY_RESULTS
        or not isinstance(summary, dict)
        or summary.get("topology_result") != topology_result
        or summary.get("body_count") != 2
        or summary.get("total_body_face_references", 0) <= 0
        or summary.get("role_binding_by_predecessor_face_counts") is not True
        or summary.get("shared_node_or_conformal_mesh")
        != "NOT_EVALUATED_NO_MESH"
    ):
        raise RuntimeError("OBSERVER_TOPOLOGY_SUMMARY_INVALID")
    report_files = report.get("files")
    if not isinstance(report_files, dict) or set(report_files) != set(
        EXPECTED_OBSERVER_FILES
    ):
        raise RuntimeError("OBSERVER_ARTIFACT_SET_INVALID")
    for role, relative in EXPECTED_OBSERVER_FILES.items():
        reported = report_files.get(role)
        manifest_entry = by_relative.get(relative)
        if not isinstance(reported, dict) or not isinstance(manifest_entry, dict):
            raise RuntimeError("OBSERVER_ARTIFACT_MISSING:{}".format(role))
        if PureWindowsPath(str(reported.get("path", ""))).name != relative:
            raise RuntimeError("OBSERVER_ARTIFACT_PATH_MISMATCH:{}".format(role))
        if (
            reported.get("exists") is not True
            or reported.get("size") != manifest_entry.get("size")
            or reported.get("sha256") != manifest_entry.get("sha256")
            or not isinstance(reported.get("sha256"), str)
            or not re.fullmatch(r"[0-9a-f]{64}", reported["sha256"])
        ):
            raise RuntimeError(
                "OBSERVER_ARTIFACT_HASH_OR_SIZE_MISMATCH:{}".format(role)
            )
    return report


async def run_suite() -> int:
    stamp = (
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        + "_"
        + uuid4().hex[:8]
    )
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    stderr_path = OUTPUT_ROOT / (
        "V02_TOPOLOGY_OBSERVER_MCP_STDERR_{}.log".format(stamp)
    )
    result: dict[str, Any] = {
        "task": "AJM006_V02_PRELIMINARY_TOPOLOGY_OBSERVER_SUITE",
        "case_id": CASE_ID,
        "started_at": utc_now(),
        "ended_at": None,
        "final_status": "FAIL_PRELIMINARY_TOPOLOGY_OBSERVER",
        "preflight": None,
        "inventory": None,
        "producer": None,
        "observer": None,
        "topology_result": None,
        "error": None,
    }
    exit_code = 2
    try:
        preflight = combined_preflight()
        result["preflight"] = preflight
        if not preflight["preflight_ok"]:
            raise RuntimeError(
                "BLOCKED_PREFLIGHT:{}".format(
                    ";".join(preflight["preflight_errors"])
                )
            )
        expected_git_head = preflight["git_head"]
        if norm(Path(sys.executable)) != norm(EXPECTED_PYTHON):
            raise RuntimeError("BLOCKED_WRONG_RUNNER_INTERPRETER")
        if version("mcp") != "1.28.1":
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
                        name="airjet-ajm006-v02-topology-observer-harness",
                        version="1.0.0",
                    ),
                ) as session:
                    await session.initialize()
                    tools = {
                        item.name for item in (await session.list_tools()).tools
                    }
                    if tools != EXPECTED_TOOLS:
                        raise RuntimeError("BLOCKED_UNEXPECTED_MCP_TOOLS")
                    inventory = await call_json(session, "inventory")
                    result["inventory"] = inventory
                    if (
                        inventory.get("ready") is not True
                        or inventory.get("git_head") != expected_git_head
                        or inventory.get("license_data_read") is not False
                    ):
                        raise RuntimeError("BLOCKED_INVENTORY_NOT_READY")
                    approved = set(inventory.get("approved_profiles") or [])
                    if not {PRODUCER_PROFILE_ID, OBSERVER_PROFILE_ID} <= approved:
                        raise RuntimeError("BLOCKED_REQUIRED_PROFILE_NOT_APPROVED")
                    contracts = inventory.get("profile_contract_sha256")
                    if not isinstance(contracts, dict):
                        raise RuntimeError("BLOCKED_INVENTORY_PROFILE_CONTRACTS")
                    producer_contract = contracts.get(PRODUCER_PROFILE_ID)
                    observer_contract = contracts.get(OBSERVER_PROFILE_ID)
                    if not all(
                        isinstance(item, str) and re.fullmatch(r"[0-9a-f]{64}", item)
                        for item in (producer_contract, observer_contract)
                    ):
                        raise RuntimeError("BLOCKED_PROFILE_CONTRACT_HASH")

                    producer_state = await call_json(
                        session,
                        "submit_job",
                        {"profile_id": PRODUCER_PROFILE_ID, "case_id": CASE_ID},
                    )
                    validate_submit_state(
                        producer_state,
                        profile_id=PRODUCER_PROFILE_ID,
                        engine="spaceclaim",
                        script_sha256=PRODUCER_SCRIPT_SHA256,
                        profile_contract_sha256=producer_contract,
                        git_head=expected_git_head,
                        predecessor_job_id=None,
                    )
                    if (
                        not isinstance(
                            producer_state.get("profile_dependency_artifacts"), list
                        )
                        or len(producer_state["profile_dependency_artifacts"])
                        != EXPECTED_PRODUCER_DEPENDENCIES
                        or not re.fullmatch(
                            r"[0-9a-f]{64}",
                            producer_state.get(
                                "profile_dependency_manifest_sha256", ""
                            ),
                        )
                    ):
                        raise RuntimeError("PRODUCER_DEPENDENCY_BUNDLE_INVALID")
                    producer_state = await wait_terminal(
                        session, producer_state, PRODUCER_WAIT_SECONDS
                    )
                    producer_manifest = await call_json(
                        session,
                        "artifact_manifest",
                        {"job_id": producer_state["job_id"]},
                        timeout_seconds=600,
                    )
                    if producer_state.get("phase") != "PROCESS_EXITED_0":
                        raise RuntimeError("PRODUCER_NOT_PROCESS_EXITED_0")
                    producer_report = producer_runner.validate_producer_report(
                        producer_manifest, producer_state, expected_git_head
                    )
                    result["producer"] = {
                        "job_state": producer_state,
                        "manifest": producer_manifest,
                        "report": producer_report,
                    }

                    observer_state = await call_json(
                        session,
                        "submit_job",
                        {
                            "profile_id": OBSERVER_PROFILE_ID,
                            "case_id": CASE_ID,
                            "predecessor_job_id": producer_state["job_id"],
                        },
                        timeout_seconds=600,
                    )
                    validate_submit_state(
                        observer_state,
                        profile_id=OBSERVER_PROFILE_ID,
                        engine="workbench",
                        script_sha256=OBSERVER_SCRIPT_SHA256,
                        profile_contract_sha256=observer_contract,
                        git_head=expected_git_head,
                        predecessor_job_id=producer_state["job_id"],
                    )
                    copied = observer_state.get("predecessor_artifacts")
                    if (
                        not isinstance(copied, list)
                        or {item.get("relative_path") for item in copied}
                        != EXPECTED_PREDECESSOR_ARTIFACTS
                        or observer_state.get("profile_dependency_artifacts") != []
                        or observer_state.get("profile_dependency_manifest_sha256")
                        is not None
                    ):
                        raise RuntimeError("OBSERVER_PREDECESSOR_BUNDLE_INVALID")
                    observer_state = await wait_terminal(
                        session, observer_state, OBSERVER_WAIT_SECONDS
                    )
                    observer_manifest = await call_json(
                        session,
                        "artifact_manifest",
                        {"job_id": observer_state["job_id"]},
                        timeout_seconds=1200,
                    )
                    if observer_state.get("phase") != "PROCESS_EXITED_0":
                        raise RuntimeError("OBSERVER_NOT_PROCESS_EXITED_0")
                    observer_report = validate_observer_report(
                        observer_manifest,
                        observer_state,
                        expected_git_head,
                        producer_state["job_id"],
                    )
                    result["observer"] = {
                        "job_state": observer_state,
                        "manifest": observer_manifest,
                        "report": observer_report,
                    }
                    result["topology_result"] = observer_report[
                        "topology_result"
                    ]
                    result["final_status"] = (
                        "PASS_PRELIMINARY_TOPOLOGY_OBSERVER"
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
            "topology_result": result["topology_result"],
            "result_path": str(RESULT_PATH),
        }, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run_suite()))

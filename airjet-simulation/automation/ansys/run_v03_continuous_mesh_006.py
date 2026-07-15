#!/usr/bin/env python3
"""Run the V03 finite-throat producer and PyFluent mesh consumer in one MCP session."""

from __future__ import annotations

import asyncio
from contextlib import suppress
from datetime import datetime, timedelta, timezone
import hashlib
from importlib.metadata import version
import json
import math
from pathlib import Path, PureWindowsPath
import re
import sys
import time
import traceback
from typing import Any, Optional
from uuid import uuid4

from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client

import run_v03_continuous_fluid_006 as stage1


CONSUMER_PROFILE_ID = "ajm006-pyfluent-v03-continuous-mesh-pilot-v1"
CONSUMER_SCRIPT = "006/v03_pyfluent_watertight_mesh_consumer.py"
CONSUMER_SCRIPT_SHA256 = "a11fe49808eb4f0a5be0406b076fbbb5023bd08a4333d22a690be6eaa02dd5ca"
CONSUMER_REPORT = "v03_pyfluent_watertight_mesh_consumer.json"
CASE_ID = stage1.CASE_ID
RESULT_PATH = stage1.OUTPUT_ROOT / "V03_CONTINUOUS_MESH_RUN_SUMMARY.json"
MCP_GIT_PATH = "codex-skills/airjet-ansys-automation/scripts/airjet_ansys_mcp.py"
CONSUMER_ASSERTIONS = {
    "predecessor_identity",
    "predecessor_immutable",
    "exact_step_byte_staging",
    "fluent_v261_meshing_health",
    "watertight_step_import",
    "boundary_roles_reconstructed",
    "throat_roles_reconstructed_972",
    "throat_local_sizing_contract",
    "surface_mesh",
    "single_fluid_region",
    "volume_mesh",
    "one_fluid_cell_zone",
    "throat_center_occupancy_972",
    "mesh_integrity",
    "student_limit_guard",
    "mesh_write_hash",
    "claim_boundaries",
}
PREDECESSOR_ARTIFACTS = (
    "v03_continuous_fluid_producer.json",
    "product_continuous_fluid.step",
    "v03_step_reimport.json",
    "v03_throat_inventory.json",
    "v03_source_chain.json",
)
CONSUMER_ARTIFACTS = {
    "v03_continuous_volume_mesh.msh.h5",
    "v03_pyfluent_mesh_inventory.json",
    "v03_predecessor_verification.json",
    "v03_pyfluent_source_chain.json",
    "v03_pyfluent_transcript.txt",
}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def exact_consumer_profile(head: str) -> dict[str, Any]:
    policy = json.loads(
        stage1.read_git_blob(head, stage1.POLICY_GIT_PATH).decode("utf-8")
    )
    matches = [
        item
        for item in policy.get("profiles", [])
        if isinstance(item, dict)
        and item.get("profile_id") == CONSUMER_PROFILE_ID
    ]
    if len(matches) != 1:
        raise RuntimeError("BLOCKED_CONSUMER_PROFILE_NOT_EXACTLY_ONE")
    profile = matches[0]
    expected_predecessor = {
        "profile_id": stage1.PROFILE_ID,
        "report": stage1.PRODUCER_REPORT,
        "required_probe": "v03_continuous_fluid_producer",
        "required_status": "PASS_PARTIAL_CAD_CAPABILITY",
        "required_assertions": [
            "input_contract",
            "gen1_target",
            "preliminary_full_product_scope",
            "c016_candidate_boundary",
            "explicit_throat_construction",
            "single_continuous_fluid_boolean",
            "native_save",
            "native_reopen_single_body",
            "native_throat_inventory",
            "step_export",
            "step_reopen_single_body",
            "step_throat_inventory",
            "complete_flow_path",
            "round_trip_shape_fidelity",
            "artifact_hashes",
            "claim_boundaries",
            "physics_guards",
        ],
        "artifacts": list(PREDECESSOR_ARTIFACTS),
    }
    if profile != {
        "profile_id": CONSUMER_PROFILE_ID,
        "engine": "pyfluent",
        "script": CONSUMER_SCRIPT,
        "sha256": CONSUMER_SCRIPT_SHA256,
        "timeout_seconds": 7200,
        "output_root_id": "p1_cad_006",
        "reports": [CONSUMER_REPORT],
        "predecessor": expected_predecessor,
    }:
        raise RuntimeError("BLOCKED_CONSUMER_PROFILE_CONTRACT_MISMATCH")
    source = stage1.read_git_blob(
        head,
        "airjet-simulation/automation/ansys/approved/{}".format(
            CONSUMER_SCRIPT
        ),
    )
    if sha256_bytes(source) != CONSUMER_SCRIPT_SHA256:
        raise RuntimeError("BLOCKED_CONSUMER_GIT_BLOB_HASH_MISMATCH")
    return profile


def manifest_map(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    files = manifest.get("files")
    if not isinstance(files, list):
        raise RuntimeError("MANIFEST_FILES_NOT_LIST")
    mapped: dict[str, dict[str, Any]] = {}
    for item in files:
        if not isinstance(item, dict):
            continue
        relative = item.get("relative_path")
        if isinstance(relative, str):
            if relative in mapped:
                raise RuntimeError("MANIFEST_DUPLICATE_PATH")
            mapped[relative] = item
    return mapped


def verify_predecessor_state(
    state: dict[str, Any], stage1_manifest: dict[str, Any]
) -> None:
    copied = state.get("predecessor_artifacts")
    if not isinstance(copied, list):
        raise RuntimeError("CONSUMER_PREDECESSOR_ARTIFACTS_NOT_LIST")
    copied_map = {
        item.get("relative_path"): item
        for item in copied
        if isinstance(item, dict)
    }
    if set(copied_map) != set(PREDECESSOR_ARTIFACTS):
        raise RuntimeError("CONSUMER_PREDECESSOR_ARTIFACT_SET_MISMATCH")
    frozen_map = manifest_map(stage1_manifest)
    for relative in PREDECESSOR_ARTIFACTS:
        copied_item = copied_map[relative]
        frozen = frozen_map.get(relative)
        if (
            not isinstance(frozen, dict)
            or copied_item.get("size") != frozen.get("size")
            or copied_item.get("sha256") != frozen.get("sha256")
        ):
            raise RuntimeError(
                "CONSUMER_PREDECESSOR_FROZEN_MISMATCH:{}".format(relative)
            )


def positive_int(value: Any, upper: Optional[int] = None) -> bool:
    return (
        type(value) is int
        and value > 0
        and (upper is None or value <= upper)
    )


def validate_consumer_report(
    manifest: dict[str, Any], state: dict[str, Any], expected_head: str
) -> dict[str, Any]:
    files = manifest_map(manifest)
    entry = files.get(CONSUMER_REPORT)
    if not isinstance(entry, dict) or entry.get("report_error") is not None:
        raise RuntimeError("CONSUMER_REPORT_MISSING_OR_INVALID")
    report = entry.get("report_json")
    if not isinstance(report, dict):
        raise RuntimeError("CONSUMER_REPORT_NOT_INLINED")
    if (
        report.get("schema_version") != 1
        or report.get("task") != "AJM006_V03_PYFLUENT_WATERTIGHT_MESH_ONLY"
        or report.get("probe") != "v03_pyfluent_watertight_mesh_consumer"
        or report.get("status") != "PASS_PRELIMINARY_MESH_CAPABILITY"
        or report.get("engineering_capability")
        != "PASS_PRELIMINARY_MESH_CAPABILITY"
        or report.get("mesh_result")
        != "PASS_V03_SINGLE_REGION_972_THROAT_VOLUME_MESH"
        or report.get("claim_scope")
        != "V03_PRELIMINARY_PYFLUENT_MESH_PILOT_ONLY"
    ):
        raise RuntimeError("CONSUMER_REPORT_STATUS_MISMATCH")
    claim_expectations = {
        "formal_006_completion": False,
        "p1_stage_gate": "NOT_RUN",
        "p1_mesh_gate": "NOT_RUN",
        "p1_p6_gates": "NOT_RUN",
        "physics": "NOT_RUN",
        "boundary_conditions": "NOT_APPLIED",
        "solver_mode": "NOT_ENTERED",
        "solver_initialization": "NOT_RUN",
        "solver_iterations": 0,
        "solution": "NOT_RUN",
        "cht": "NOT_RUN",
        "fsi": "NOT_RUN",
        "exact_product_geometry": "NOT_CLAIMED",
        "visibility": "NOT_USER_OBSERVED",
        "license_arguments_added": False,
        "error": None,
    }
    if any(report.get(key) != value for key, value in claim_expectations.items()):
        raise RuntimeError("CONSUMER_REPORT_CLAIM_BOUNDARY_VIOLATION")
    assertions = report.get("assertions")
    if (
        not isinstance(assertions, dict)
        or set(assertions) != CONSUMER_ASSERTIONS
        or any(value is not True for value in assertions.values())
    ):
        raise RuntimeError("CONSUMER_REPORT_ASSERTIONS_FAILED")
    identity = report.get("identity")
    if (
        not isinstance(identity, dict)
        or identity.get("git_head") != expected_head
        or identity.get("profile_id") != CONSUMER_PROFILE_ID
        or identity.get("profile_contract_sha256")
        != state.get("profile_contract_sha256")
        or identity.get("script_sha256") != CONSUMER_SCRIPT_SHA256
        or identity.get("case_id") != CASE_ID
        or identity.get("predecessor_job_id")
        != state.get("predecessor_job_id")
    ):
        raise RuntimeError("CONSUMER_REPORT_IDENTITY_MISMATCH")
    contract = report.get("mesh_contract")
    if contract != {
        "product_version": "261",
        "mode": "MESHING",
        "dimension": "THREE",
        "precision": "DOUBLE",
        "processor_count": 1,
        "ui_mode": "NO_GUI_OR_GRAPHICS",
        "surface_min_size_mm": 0.025,
        "surface_max_size_mm": 0.5,
        "throat_local_size_mm": 0.05,
        "volume_max_size_mm": 0.5,
        "student_cell_limit": 1_000_000,
        "student_node_limit": 1_000_000,
    }:
        raise RuntimeError("CONSUMER_MESH_CONTRACT_MISMATCH")
    evidence = report.get("mesh_evidence")
    if (
        not isinstance(evidence, dict)
        or not positive_int(evidence.get("cell_count"), 1_000_000)
        or not positive_int(evidence.get("node_count"), 1_000_000)
        or evidence.get("cell_zone_count") != 1
        or evidence.get("throat_query_count") != 972
        or not positive_int(evidence.get("throat_zone_count"), 972)
        or evidence.get("free_face_count") != 0
        or evidence.get("multi_face_count") != 0
        or not isinstance(evidence.get("min_orthogonal_quality"), (int, float))
        or isinstance(evidence.get("min_orthogonal_quality"), bool)
        or not math.isfinite(float(evidence["min_orthogonal_quality"]))
        or not 0.0 < float(evidence["min_orthogonal_quality"]) <= 1.0
    ):
        raise RuntimeError("CONSUMER_MESH_EVIDENCE_INVALID")
    reported_artifacts = report.get("artifacts")
    if not isinstance(reported_artifacts, dict) or set(reported_artifacts) != CONSUMER_ARTIFACTS:
        raise RuntimeError("CONSUMER_ARTIFACT_SET_MISMATCH")
    for relative in CONSUMER_ARTIFACTS:
        reported = reported_artifacts.get(relative)
        file_entry = files.get(relative)
        if (
            not isinstance(reported, dict)
            or not isinstance(file_entry, dict)
            or reported.get("relative_path") != relative
            or not positive_int(reported.get("size"))
            or reported.get("size") != file_entry.get("size")
            or not isinstance(reported.get("sha256"), str)
            or not re.fullmatch(r"[0-9a-f]{64}", reported["sha256"])
            or reported.get("sha256") != file_entry.get("sha256")
        ):
            raise RuntimeError("CONSUMER_ARTIFACT_INVALID:{}".format(relative))
    mesh_file = evidence.get("mesh_file")
    if mesh_file != reported_artifacts["v03_continuous_volume_mesh.msh.h5"]:
        raise RuntimeError("CONSUMER_MESH_FILE_RECORD_MISMATCH")
    return report


async def wait_for_job(
    session: ClientSession, state: dict[str, Any], timeout_seconds: int
) -> dict[str, Any]:
    job_id = state.get("job_id")
    phase = state.get("phase")
    stable_names = (
        "job_id",
        "case_id",
        "profile_id",
        "engine",
        "script_sha256",
        "profile_contract_sha256",
        "profile_dependency_manifest_sha256",
        "git_head",
        "output_root_id",
        "job_directory",
        "license_arguments_added",
        "predecessor_job_id",
        "predecessor_artifacts",
    )
    stable = {name: state.get(name) for name in stable_names}
    deadline = time.monotonic() + timeout_seconds
    try:
        while phase == "RUNNING":
            if time.monotonic() >= deadline:
                state = await stage1.call_json(
                    session, "cancel_job", {"job_id": job_id}
                )
                phase = state.get("phase")
                break
            await asyncio.sleep(stage1.POLL_SECONDS)
            state = await stage1.call_json(
                session, "poll_job", {"job_id": job_id}
            )
            for name, expected in stable.items():
                if state.get(name) != expected:
                    raise RuntimeError("JOB_IDENTITY_CHANGED:{}".format(name))
            phase = state.get("phase")
            if phase != "RUNNING" and phase not in stage1.TERMINAL_PHASES:
                raise RuntimeError("UNKNOWN_JOB_PHASE:{}".format(phase))
    except BaseException:
        if phase == "RUNNING":
            with suppress(BaseException):
                await stage1.call_json(
                    session, "cancel_job", {"job_id": job_id}
                )
        raise
    return state


async def run_suite() -> int:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "_" + uuid4().hex[:8]
    stage1.OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    stderr_path = stage1.OUTPUT_ROOT / "V03_CONTINUOUS_MESH_MCP_STDERR_{}.log".format(stamp)
    result: dict[str, Any] = {
        "task": "AJM006_V03_TWO_STAGE_CONTINUOUS_MESH_SUITE",
        "case_id": CASE_ID,
        "started_at": stage1.utc_now(),
        "ended_at": None,
        "final_status": "FAIL_PRELIMINARY_V03_TWO_STAGE_MESH_SUITE",
        "preflight": None,
        "inventory": None,
        "stage1": {},
        "stage2": {},
        "error": None,
    }
    exit_code = 2
    try:
        pf = stage1.preflight()
        result["preflight"] = pf
        if not pf.get("preflight_ok"):
            raise RuntimeError("BLOCKED_STAGE1_PREFLIGHT:{}".format(pf.get("preflight_errors")))
        head = pf["git_head"]
        exact_consumer_profile(head)
        if stage1.norm(Path(sys.executable)) != stage1.norm(stage1.EXPECTED_PYTHON):
            raise RuntimeError("BLOCKED_WRONG_RUNNER_INTERPRETER")
        if version("mcp") != "1.28.1":
            raise RuntimeError("BLOCKED_UNEXPECTED_MCP_PACKAGE_VERSION")
        if not stage1.SERVER.is_file():
            raise RuntimeError("BLOCKED_MCP_SERVER_MISSING")
        if sha256_bytes(stage1.SERVER.read_bytes()) != sha256_bytes(
            stage1.read_git_blob(head, MCP_GIT_PATH)
        ):
            raise RuntimeError("BLOCKED_MCP_SERVER_COPY_MISMATCH")

        parameters = StdioServerParameters(
            command=str(stage1.EXPECTED_PYTHON),
            args=["-I", "-B", str(stage1.SERVER)],
            cwd=str(stage1.REPO),
            encoding="utf-8",
            encoding_error_handler="strict",
        )
        with stderr_path.open("w", encoding="utf-8") as errlog:
            async with stdio_client(parameters, errlog=errlog) as streams:
                async with ClientSession(
                    *streams,
                    read_timeout_seconds=timedelta(seconds=120),
                    client_info=types.Implementation(
                        name="airjet-ajm006-v03-two-stage-mesh-harness",
                        version="1.0.0",
                    ),
                ) as session:
                    await session.initialize()
                    tools = {tool.name for tool in (await session.list_tools()).tools}
                    if tools != stage1.EXPECTED_TOOLS:
                        raise RuntimeError("BLOCKED_UNEXPECTED_MCP_TOOLS")
                    inventory = await stage1.call_json(session, "inventory")
                    result["inventory"] = inventory
                    if (
                        inventory.get("ready") is not True
                        or inventory.get("git_head") != head
                        or not {stage1.PROFILE_ID, CONSUMER_PROFILE_ID}.issubset(
                            set(inventory.get("approved_profiles") or [])
                        )
                    ):
                        raise RuntimeError("BLOCKED_INVENTORY_IDENTITY_OR_PROFILES")
                    contracts = inventory.get("profile_contract_sha256") or {}

                    first = await stage1.call_json(
                        session,
                        "submit_job",
                        {"profile_id": stage1.PROFILE_ID, "case_id": CASE_ID},
                    )
                    if (
                        first.get("phase") != "RUNNING"
                        or first.get("engine") != "spaceclaim"
                        or first.get("git_head") != head
                        or first.get("script_sha256") != stage1.PROFILE_SCRIPT_SHA256
                        or first.get("profile_contract_sha256")
                        != contracts.get(stage1.PROFILE_ID)
                        or first.get("license_arguments_added") is not False
                        or first.get("predecessor_job_id") is not None
                    ):
                        raise RuntimeError("STAGE1_SUBMIT_IDENTITY_MISMATCH")
                    stage1.validate_dependency_artifacts(
                        first.get("profile_dependency_artifacts")
                    )
                    first = await wait_for_job(session, first, 7200)
                    result["stage1"]["job_state"] = first
                    first_manifest = await stage1.call_json(
                        session,
                        "artifact_manifest",
                        {"job_id": first.get("job_id")},
                        timeout_seconds=600,
                    )
                    result["stage1"]["manifest"] = first_manifest
                    if (
                        first.get("phase") != "PROCESS_EXITED_0"
                        or first_manifest.get("phase") != "PROCESS_EXITED_0"
                        or first_manifest.get("job_id") != first.get("job_id")
                    ):
                        raise RuntimeError("STAGE1_NOT_PROCESS_EXITED_0")
                    result["stage1"]["report"] = stage1.validate_producer_report(
                        first_manifest, first, head
                    )
                    result["stage1"]["frozen_manifest_sha256"] = sha256_bytes(
                        json.dumps(
                            first_manifest,
                            sort_keys=True,
                            separators=(",", ":"),
                        ).encode("utf-8")
                    )

                    second = await stage1.call_json(
                        session,
                        "submit_job",
                        {
                            "profile_id": CONSUMER_PROFILE_ID,
                            "case_id": CASE_ID,
                            "predecessor_job_id": first.get("job_id"),
                        },
                    )
                    if (
                        second.get("phase") != "RUNNING"
                        or second.get("engine") != "pyfluent"
                        or second.get("git_head") != head
                        or second.get("script_sha256") != CONSUMER_SCRIPT_SHA256
                        or second.get("profile_contract_sha256")
                        != contracts.get(CONSUMER_PROFILE_ID)
                        or second.get("license_arguments_added") is not False
                        or second.get("predecessor_job_id") != first.get("job_id")
                        or second.get("profile_dependency_manifest_sha256") is not None
                        or second.get("profile_dependency_artifacts") != []
                    ):
                        raise RuntimeError("STAGE2_SUBMIT_IDENTITY_MISMATCH")
                    verify_predecessor_state(second, first_manifest)
                    second = await wait_for_job(session, second, 7200)
                    result["stage2"]["job_state"] = second
                    verify_predecessor_state(second, first_manifest)
                    second_manifest = await stage1.call_json(
                        session,
                        "artifact_manifest",
                        {"job_id": second.get("job_id")},
                        timeout_seconds=600,
                    )
                    result["stage2"]["manifest"] = second_manifest
                    if (
                        second.get("phase") != "PROCESS_EXITED_0"
                        or second_manifest.get("phase") != "PROCESS_EXITED_0"
                        or second_manifest.get("job_id") != second.get("job_id")
                    ):
                        raise RuntimeError("STAGE2_NOT_PROCESS_EXITED_0")
                    result["stage2"]["report"] = validate_consumer_report(
                        second_manifest, second, head
                    )
                    result["final_status"] = "PASS_PRELIMINARY_V03_TWO_STAGE_MESH_SUITE"
                    exit_code = 0
    except Exception as exc:
        result["error"] = {
            "type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
        }
    finally:
        result["ended_at"] = stage1.utc_now()
        RESULT_PATH.write_text(
            json.dumps(result, indent=2, sort_keys=True), encoding="utf-8"
        )
        print(
            json.dumps(
                {
                    "exit_code": exit_code,
                    "final_status": result["final_status"],
                    "result_path": str(RESULT_PATH),
                },
                sort_keys=True,
            )
        )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run_suite()))

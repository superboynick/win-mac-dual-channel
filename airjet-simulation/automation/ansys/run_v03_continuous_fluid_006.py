#!/usr/bin/env python3
"""Run the AJM-006 V03 continuous-fluid geometry pilot through MCP."""

from __future__ import annotations

import asyncio
from contextlib import suppress
from datetime import datetime, timedelta, timezone
import hashlib
from importlib.metadata import version
import json
import math
import os
from pathlib import Path, PureWindowsPath
import re
import subprocess
import sys
import time
import traceback
from typing import Any, Optional
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
RESULT_PATH = OUTPUT_ROOT / "V03_CONTINUOUS_FLUID_RUN_SUMMARY.json"
POLICY_GIT_PATH = "airjet-simulation/automation/ansys/profiles.json"
PROFILE_ID = "ajm006-spaceclaim-v03-continuous-throat-pilot-v1"
PROFILE_SCRIPT_SHA256 = "e5e8764cf8a2eeddd5d56be43a02921d41d8b39f54d39160e9f95979bed0b66d"
PROFILE_SCRIPT = "006/v03_continuous_fluid_producer.py"
CASE_ID = "AJM006-V03-CONTINUOUS"
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
PRODUCER_REPORT = "v03_continuous_fluid_producer.json"
EXPECTED_REPORT_ASSERTIONS = {
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
}
EXPECTED_PRODUCER_ARTIFACTS = {
    "authoring_native": "v03_full_product_authoring.scdocx",
    "continuous_native": "product_continuous_fluid.scdocx",
    "continuous_step": "product_continuous_fluid.step",
    "native_reopen": "v03_native_reopen.json",
    "step_reimport": "v03_step_reimport.json",
    "throat_inventory": "v03_throat_inventory.json",
    "source_chain": "v03_source_chain.json",
}
EXPECTED_DEPENDENCY_COUNT = 17
EXPECTED_DEPENDENCY_GIT_PATHS = (
    "airjet-simulation/automation/ansys/contracts/full_product_semantic_contract_v1.py",
    "airjet-simulation/automation/ansys/contracts/full_product_semantic_sidecar_v1.schema.json",
    "airjet-simulation/automation/ansys/contracts/test_full_product_semantic_contract_v1.py",
    "airjet-simulation/automation/ansys/contracts/build_full_product_trusted_variants.py",
    "airjet-simulation/automation/ansys/contracts/test_full_product_trusted_variants.py",
    "airjet-simulation/parameters/p1_model_form_variants.csv",
    "airjet-simulation/parameters/p1_layout_configuration_matrix.csv",
    "airjet-simulation/parameters/p1_internal_geometry_rules.csv",
    "airjet-simulation/parameters/p1_cad_parameter_map.csv",
    "airjet-simulation/parameters/p1_orifice_pattern_candidates.csv",
    "airjet-simulation/parameters/p1_vent_geometry_candidates.csv",
    "airjet-simulation/parameters/p1_planform_exhaust_candidates.csv",
    "airjet-simulation/parameters/p1_thickness_budget.csv",
    "airjet-simulation/parameters/full_product_parameter_registry.csv",
    "airjet-simulation/automation/ansys/contracts/v03_finite_throat_route_v1.json",
    "airjet-simulation/automation/ansys/contracts/trusted_full_product_gen1/campaign.json",
    "airjet-simulation/automation/ansys/contracts/trusted_full_product_gen1/variant_02_m_3x4_7_0_r50_balanced.json",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def norm(path: Path) -> str:
    return os.path.normcase(os.path.abspath(str(path)))


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def numeric_close(value: Any, expected: float, tolerance: float = 1.0e-12) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
        and abs(float(value) - expected) <= tolerance
    )


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
        if status_r["exit_code"] != 0:
            errors.append("BLOCKED_GIT_STATUS_FAILED")
        elif status_r["stdout"]:
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

        if not isinstance(policy, dict) or policy.get("schema_version") != 2:
            errors.append("BLOCKED_PROFILE_POLICY_SCHEMA")
        profiles = policy.get("profiles", []) if isinstance(policy, dict) else []
        matches = [
            p for p in profiles
            if isinstance(p, dict) and p.get("profile_id") == PROFILE_ID
        ] if isinstance(profiles, list) else []
        if len(matches) != 1:
            errors.append("BLOCKED_PROFILE_NOT_FOUND")
        else:
            profile = matches[0]
            result["profile_found"] = True
            if profile.get("sha256") == PROFILE_SCRIPT_SHA256:
                result["profile_script_sha256_matches"] = True
            else:
                errors.append("BLOCKED_PROFILE_SCRIPT_HASH_MISMATCH")
            if (
                profile.get("engine") != "spaceclaim"
                or profile.get("script") != PROFILE_SCRIPT
                or profile.get("timeout_seconds") != 7200
                or profile.get("output_root_id") != "p1_cad_006"
                or profile.get("reports") != [PRODUCER_REPORT]
                or profile.get("predecessor") is not None
            ):
                errors.append("BLOCKED_PROFILE_CONTRACT_MISMATCH")

        contract = policy.get("production_contracts")
        if not isinstance(contract, dict):
            errors.append("BLOCKED_PRODUCTION_CONTRACT_INVALID")
        else:
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


def validate_throat_inventory(
    value: Any,
    geometry_tolerance_mm: float,
    xy_tolerance_mm: float,
    area_tolerance_mm2: float = 0.001,
) -> None:
    if not isinstance(value, dict):
        raise RuntimeError("THROAT_INVENTORY_NOT_OBJECT")
    xy = value.get("xy_inventory")
    area_models = value.get("accepted_area_model_counts")
    observed_area_range = value.get("observed_candidate_area_range_mm2")
    observed_center_z_range = value.get(
        "observed_candidate_center_z_range_mm"
    )
    observed_edge_histogram = value.get(
        "observed_candidate_edge_count_histogram"
    )
    if (
        value.get("pass") is not True
        or value.get("candidate_face_count") != 972
        or not numeric_close(value.get("expected_radius_mm"), 0.125)
        or not numeric_close(value.get("expected_diameter_mm"), 0.25)
        or not numeric_close(value.get("expected_length_mm"), 0.10)
        or not numeric_close(
            value.get("expected_construction_length_mm"), 0.14
        )
        or not math.isclose(
            value.get("expected_effective_lateral_area_mm2", -1.0),
            0.07853981633974483,
            rel_tol=0.0,
            abs_tol=1.0e-12,
        )
        or not math.isclose(
            value.get("expected_construction_lateral_area_mm2", -1.0),
            0.10995574287564276,
            rel_tol=0.0,
            abs_tol=1.0e-12,
        )
        or not numeric_close(value.get("expected_center_z_mm"), 1.5675)
        or not numeric_close(value.get("expected_z_min_mm"), 1.5175)
        or not numeric_close(value.get("expected_z_max_mm"), 1.6175)
        or not numeric_close(
            value.get("geometry_tolerance_mm"), geometry_tolerance_mm
        )
        or not numeric_close(
            value.get("area_tolerance_mm2"), area_tolerance_mm2
        )
        or not isinstance(area_models, dict)
        or set(area_models)
        != {
            "EFFECTIVE_0P100_MM",
            "CONSTRUCTION_OVERLAP_EXTENDED",
            "STEP_KERNEL_OTHER_AREA",
        }
        or area_models != {
            "EFFECTIVE_0P100_MM": 972,
            "CONSTRUCTION_OVERLAP_EXTENDED": 0,
            "STEP_KERNEL_OTHER_AREA": 0,
        }
        or not isinstance(observed_area_range, list)
        or len(observed_area_range) != 2
        or any(
            not isinstance(item, (int, float))
            or isinstance(item, bool)
            or not math.isfinite(float(item))
            or float(item) <= 0.0
            for item in observed_area_range
        )
        or observed_area_range[0] > observed_area_range[1]
        or not isinstance(observed_center_z_range, list)
        or len(observed_center_z_range) != 2
        or any(
            not isinstance(item, (int, float))
            or isinstance(item, bool)
            or not math.isfinite(float(item))
            for item in observed_center_z_range
        )
        or observed_center_z_range[0] > observed_center_z_range[1]
        or not isinstance(observed_edge_histogram, dict)
        or not observed_edge_histogram
        or any(
            not isinstance(key, str)
            or type(count) is not int
            or count <= 0
            for key, count in observed_edge_histogram.items()
        )
        or sum(observed_edge_histogram.values()) != 972
        or not isinstance(xy, dict)
        or xy.get("expected_count") != 972
        or xy.get("actual_count") != 972
        or xy.get("matched_count") != 972
        or xy.get("missing_count") != 0
        or xy.get("unexpected_count") != 0
        or xy.get("one_to_one_complete") is not True
        or not numeric_close(xy.get("tolerance_mm"), xy_tolerance_mm)
        or not isinstance(xy.get("max_xy_delta_mm"), (int, float))
        or not math.isfinite(float(xy["max_xy_delta_mm"]))
        or float(xy["max_xy_delta_mm"]) < 0.0
        or float(xy["max_xy_delta_mm"]) > xy_tolerance_mm
        or "candidate_faces" in value
    ):
        raise RuntimeError("THROAT_INVENTORY_CONTRACT_MISMATCH")


def validate_dependency_artifacts(value: Any) -> None:
    if not isinstance(value, list) or len(value) != EXPECTED_DEPENDENCY_COUNT:
        raise RuntimeError("DEPENDENCY_BUNDLE_COUNT_INVALID")
    observed = []
    relative_names = []
    for item in value:
        if not isinstance(item, dict):
            raise RuntimeError("DEPENDENCY_BUNDLE_ENTRY_INVALID")
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
            raise RuntimeError("DEPENDENCY_BUNDLE_ENTRY_INVALID")
        observed.append(git_path)
        relative_names.append(relative)
    if (
        tuple(observed) != EXPECTED_DEPENDENCY_GIT_PATHS
        or len(relative_names) != len(set(relative_names))
    ):
        raise RuntimeError("DEPENDENCY_BUNDLE_PATH_SET_INVALID")


def validate_route_body(value: Any, bbox_tolerance: float, volume_tolerance: float) -> None:
    if not isinstance(value, dict):
        raise RuntimeError("ROUTE_BODY_NOT_OBJECT")
    for key, expected in (
        ("bbox_min_mm", [-10.875, -17.75, 1.2675]),
        ("bbox_max_mm", [10.875, 20.75, 2.8]),
    ):
        actual = value.get(key)
        if (
            not isinstance(actual, list)
            or len(actual) != 3
            or any(
                not numeric_close(left, right, bbox_tolerance)
                for left, right in zip(actual, expected)
            )
        ):
            raise RuntimeError("ROUTE_BODY_BBOX_MISMATCH")
    if (
        value.get("piece_count") != 1
        or value.get("is_closed") is not True
        or value.get("is_manifold") is not True
        or not numeric_close(
            value.get("volume_mm3"), 451.7788188426395, volume_tolerance
        )
    ):
        raise RuntimeError("ROUTE_BODY_VOLUME_OR_TOPOLOGY_MISMATCH")


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
        report.get("schema_version") != 1
        or report.get("task")
        != "AJM006_V03_CONTINUOUS_FLUID_FULL_PRODUCT_PILOT"
        or report.get("probe") != "v03_continuous_fluid_producer"
        or report.get("status") != "PASS_PARTIAL_CAD_CAPABILITY"
        or report.get("engineering_capability") != "PASS_PARTIAL_CAD_CAPABILITY"
        or report.get("pilot_result")
        != "PASS_PRELIMINARY_V03_FINITE_THROAT_GEOMETRY"
    ):
        raise RuntimeError("PRODUCER_REPORT_STATUS_OR_PROBE_MISMATCH")
    if (
        report.get("formal_006_completion") is not False
        or report.get("p1_stage_gate") != "NOT_RUN"
        or report.get("p1_p6_gates") != "NOT_RUN"
        or report.get("mesh") != "NOT_RUN"
        or report.get("physics") != "NOT_RUN"
        or report.get("pyfluent") != "NOT_RUN"
        or report.get("workbench") != "NOT_RUN"
        or report.get("visibility") != "NOT_USER_OBSERVED"
        or report.get("exact_product_geometry") != "NOT_CLAIMED"
        or report.get("full_variant_campaign") != "NOT_RUN_1_OF_9_ONLY"
        or report.get("claim_scope")
        != "V03_CONTINUOUS_FLUID_GEOMETRY_PILOT_ONLY"
        or report.get("geometry_representation")
        != "SINGLE_CONTINUOUS_FLUID_BODY_WITH_972_EXPLICIT_FINITE_THROATS"
        or report.get("license_arguments_added") is not False
        or report.get("native_parameterization") != "NOT_PROVEN"
        or report.get("external_native_attach") != "NOT_PROVEN"
        or report.get("native_named_selection_transfer") != "NOT_PROVEN"
        or report.get("trusted_production_profile_binding")
        != "NOT_RUN_PRELIMINARY_PROFILE"
        or report.get("formal_convex_hull_contract") != "NOT_RUN"
        or report.get("error") not in (None, "")
        or report.get("error_type") not in (None, "")
        or report.get("traceback") not in (None, "")
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
        or any(value is not True for value in assertions.values())
    ):
        raise RuntimeError("PRODUCER_REPORT_ASSERTIONS_FAILED")
    c016 = report.get("c016_candidate")
    if c016 != {
        "parameter_id": "C016",
        "value_mm": 0.10,
        "range_mm": [0.05, 0.20],
        "evidence_class": "C",
        "status": "cad_placeholder",
        "product_fact": False,
        "uncertainty_scan": "REQUIRED_LATER_NOT_RUN",
    }:
        raise RuntimeError("PRODUCER_C016_BOUNDARY_MISMATCH")
    geometry = report.get("geometry")
    expected_groups = {
        "FLUID_CONTINUOUS": 1,
        "INLET": 4,
        "OUTLET": 1,
        "MEMBRANE_TOP": 12,
        "MEMBRANE_BOTTOM": 12,
        "ORIFICE_THROAT_WALL": 972,
        "HEAT_WALL": 1,
    }
    if (
        not isinstance(geometry, dict)
        or geometry.get("source_variant_id") != "M-3x4-7.0__R50_BALANCED"
        or geometry.get("configuration_id") != "M-3x4-7.0"
        or geometry.get("cell_count") != 12
        or geometry.get("orifice_count") != 972
        or not numeric_close(geometry.get("orifice_diameter_mm"), 0.25)
        or not numeric_close(geometry.get("throat_length_mm"), 0.10)
        or geometry.get("throat_length_range_mm") != [0.05, 0.20]
        or geometry.get("throat_length_evidence_class") != "C"
        or not numeric_close(geometry.get("numerical_overlap_mm"), 0.02)
        or not numeric_close(geometry.get("vent_riser_overlap_mm"), 0.001)
        or not isinstance(
            geometry.get("boolean_volume_delta_mm3"), (int, float)
        )
        or not math.isfinite(float(geometry["boolean_volume_delta_mm3"]))
        or geometry.get("boolean_volume_delta_mm3") < 0.0
        or geometry.get("boolean_volume_delta_mm3") > 0.08
        or not numeric_close(
            geometry.get("route_analytic_volume_mm3"),
            451.7788188426395,
        )
        or not numeric_close(
            geometry.get("native_route_volume_tolerance_mm3"), 0.08
        )
        or not numeric_close(
            geometry.get("step_route_volume_tolerance_mm3"), 0.03
        )
        or not numeric_close(
            geometry.get("native_analytic_volume_delta_mm3"),
            abs(
                float((geometry.get("continuous_before_save") or {}).get(
                    "volume_mm3", math.inf
                )) - 451.7788188426395
            ),
        )
        or not isinstance(
            geometry.get("step_analytic_volume_delta_mm3"), (int, float)
        )
        or not math.isfinite(
            float(geometry["step_analytic_volume_delta_mm3"])
        )
        or geometry.get("step_analytic_volume_delta_mm3") > 0.03
        or geometry.get("continuous_route_ok") is not True
        or geometry.get("native_route_ok") is not True
        or geometry.get("step_route_ok") is not True
        or geometry.get("group_counts") != expected_groups
        or geometry.get("group_required") != expected_groups
        or geometry.get("group_semantics_ok") is not True
        or geometry.get("all_cells_have_throats") is not True
        or set((geometry.get("throat_counts_by_cell") or {}).values()) != {81}
        or len(geometry.get("throat_counts_by_cell") or {}) != 12
        or geometry.get("step_boundary_counts") != {
            key: value for key, value in expected_groups.items()
            if key != "FLUID_CONTINUOUS"
        }
    ):
        raise RuntimeError("PRODUCER_V03_GEOMETRY_CONTRACT_MISMATCH")
    xy_contract = geometry.get("expected_xy_contract")
    if (
        not isinstance(xy_contract, dict)
        or xy_contract.get("expected_count") != 972
        or xy_contract.get("unique_count_rounded_9dp") != 972
        or xy_contract.get("step_xy_tolerance_mm") != 0.02
        or xy_contract.get("required_minimum_center_spacing_mm") != 0.29
        or not isinstance(
            xy_contract.get("minimum_center_spacing_mm"), (int, float)
        )
        or not math.isfinite(
            float(xy_contract["minimum_center_spacing_mm"])
        )
        or not math.isclose(
            float(xy_contract["minimum_center_spacing_mm"]),
            0.700624,
            rel_tol=0.0,
            abs_tol=1.0e-9,
        )
        or xy_contract.get("minimum_center_spacing_mm")
        <= 0.29
        or xy_contract.get("pass") is not True
    ):
        raise RuntimeError("PRODUCER_EXPECTED_XY_CONTRACT_MISMATCH")
    continuous = geometry.get("continuous_before_save")
    validate_route_body(continuous, 0.02, 0.08)
    validate_throat_inventory(
        geometry.get("throat_inventory_before_save"), 0.002, 0.002
    )
    validate_throat_inventory(
        geometry.get("native_throat_inventory"), 0.002, 0.002
    )
    validate_throat_inventory(
        geometry.get("step_throat_inventory"), 0.005, 0.02
    )
    native_summary = geometry.get("native_reopen_summary")
    step_summary = geometry.get("step_reimport_summary")
    if (
        not isinstance(native_summary, dict)
        or native_summary.get("open_success") is not True
        or native_summary.get("body_count") != 1
        or native_summary.get("group_counts") != expected_groups
        or not isinstance(native_summary.get("body_fingerprint"), dict)
        or native_summary["body_fingerprint"].get("piece_count") != 1
        or native_summary["body_fingerprint"].get("is_closed") is not True
        or native_summary["body_fingerprint"].get("is_manifold") is not True
    ):
        raise RuntimeError("PRODUCER_NATIVE_REOPEN_SUMMARY_INVALID")
    validate_route_body(native_summary["body_fingerprint"], 0.02, 0.08)
    expected_step_groups = {
        key: value for key, value in expected_groups.items()
        if key != "FLUID_CONTINUOUS"
    }
    if (
        not isinstance(step_summary, dict)
        or step_summary.get("open_success") is not True
        or step_summary.get("body_count") != 1
        or step_summary.get("boundary_counts") != expected_step_groups
        or not isinstance(step_summary.get("body_fingerprint"), dict)
        or step_summary["body_fingerprint"].get("piece_count") != 1
        or step_summary["body_fingerprint"].get("is_closed") is not True
        or step_summary["body_fingerprint"].get("is_manifold") is not True
        or step_summary.get("comparison_tolerances") != {
            "bbox_tolerance_mm": 0.02,
            "volume_absolute_tolerance_mm3": 0.08,
            "volume_relative_tolerance": 1.0e-5,
            "face_count_required": False,
            "names_required": False,
            "throat_xy_tolerance_mm": 0.02,
            "comparison_basis": "INDEPENDENT_ROUTE_ANALYTIC",
            "native_to_step_volume_delta_diagnostic_only": True,
            "route_analytic_volume_tolerance_mm3": 0.03,
        }
        or not isinstance(step_summary.get("comparison_deltas"), dict)
        or not isinstance(
            step_summary["comparison_deltas"].get("max_bbox_delta_mm"),
            (int, float),
        )
        or not isinstance(
            step_summary["comparison_deltas"].get("max_volume_delta_mm3"),
            (int, float),
        )
        or not math.isfinite(float(
            step_summary["comparison_deltas"]["max_bbox_delta_mm"]
        ))
        or not math.isfinite(float(
            step_summary["comparison_deltas"]["max_volume_delta_mm3"]
        ))
        or step_summary["comparison_deltas"]["max_bbox_delta_mm"] < 0.0
        or step_summary["comparison_deltas"]["max_volume_delta_mm3"] < 0.0
        or step_summary["comparison_deltas"].get(
            "max_bbox_delta_mm", 1.0
        ) > 0.02
        or step_summary["comparison_deltas"].get(
            "max_volume_delta_mm3", 1.0
        ) > 0.08
    ):
        raise RuntimeError("PRODUCER_STEP_REIMPORT_SUMMARY_INVALID")
    validate_route_body(step_summary["body_fingerprint"], 0.02, 0.03)
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
    arguments: Optional[dict[str, Any]] = None,
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
    stderr_path = OUTPUT_ROOT / (
        "V03_CONTINUOUS_FLUID_MCP_STDERR_{}.log".format(stamp)
    )
    result = {
        "task": "AJM006_V03_CONTINUOUS_FLUID_PRODUCER",
        "case_id": CASE_ID,
        "profile_id": PROFILE_ID,
        "started_at": utc_now(),
        "ended_at": None,
        "preflight": None,
        "final_status": "FAIL_PRELIMINARY_V03_CONTINUOUS_FLUID_PRODUCER",
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
                        name="airjet-ajm006-v03-continuous-fluid-harness",
                        version="1.0.0",
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
                    ):
                        raise RuntimeError("SUBMIT_DEPENDENCY_BUNDLE_INVALID")
                    validate_dependency_artifacts(dependency_artifacts)
                    if (
                        state.get("predecessor_job_id") is not None
                        or state.get("predecessor_artifacts") != []
                        or not isinstance(state.get("job_directory"), str)
                        or not state["job_directory"]
                    ):
                        raise RuntimeError("SUBMIT_PREDECESSOR_OR_DIRECTORY_INVALID")
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
                            "job_directory",
                            "license_arguments_added",
                            "predecessor_job_id",
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
                        validate_dependency_artifacts(
                            state.get("profile_dependency_artifacts")
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
                        result["final_status"] = (
                            "PASS_PRELIMINARY_V03_CONTINUOUS_FLUID_PRODUCER"
                        )
                        exit_code = 0
                    else:
                        result["final_status"] = (
                            "FAIL_PRELIMINARY_V03_CONTINUOUS_FLUID_PRODUCER"
                        )

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

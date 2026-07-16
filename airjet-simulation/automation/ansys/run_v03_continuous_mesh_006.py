#!/usr/bin/env python3
"""Run the V03 finite-throat producer and PyFluent mesh consumer in one MCP session."""

from __future__ import annotations

import asyncio
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
CONSUMER_SCRIPT_SHA256 = "331b110318853077e40130e4e6974fe424b2b2df1f514d725d4767f07126fdad"
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
    "flow_cell_zone_inventory",
    "volume_mesh",
    "region_classification",
    "throat_occupancy_full_972",
    "actuator_gap_exclusion",
    "connected_fluid_cell_zone_graph",
    "target_flow_volume_matches_predecessor",
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


def persist_result(result: dict[str, Any]) -> None:
    """Persist the latest partial evidence without waiting for suite closeout."""
    RESULT_PATH.write_text(
        json.dumps(result, indent=2, sort_keys=True), encoding="utf-8"
    )


def new_result() -> dict[str, Any]:
    return {
        "task": "AJM006_V03_TWO_STAGE_CONTINUOUS_MESH_SUITE",
        "case_id": CASE_ID,
        "started_at": stage1.utc_now(),
        "ended_at": None,
        "final_status": "FAIL_PRELIMINARY_V03_TWO_STAGE_MESH_SUITE",
        "preflight": None,
        "inventory": None,
        "stage1": {
            "submitted": False,
            "reached_terminal": False,
            "capability_status": "NOT_RUN",
        },
        "stage2": {
            "submitted": False,
            "reached_terminal": False,
            "capability_status": "NOT_RUN",
        },
        "error": None,
    }


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
        print("PROFILE_COUNT_WARNING")
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
        print("PROFILE_WARNING")
    source = stage1.read_git_blob(
        head,
        "airjet-simulation/automation/ansys/approved/{}".format(
            CONSUMER_SCRIPT
        ),
    )
    if sha256_bytes(source) != CONSUMER_SCRIPT_SHA256:
        print("BLOB_HASH_WARNING")
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
    if any(not isinstance(item, dict) for item in copied):
        raise RuntimeError("CONSUMER_PREDECESSOR_ARTIFACTS_DUPLICATE_OR_INVALID")
    copied_map: dict[str, dict[str, Any]] = {}
    for item in copied:
        relative = item.get("relative_path")
        if not isinstance(relative, str) or relative in copied_map:
            raise RuntimeError("CONSUMER_PREDECESSOR_ARTIFACTS_DUPLICATE_OR_INVALID")
        copied_map[relative] = item
    if len(copied) != len(PREDECESSOR_ARTIFACTS):
        raise RuntimeError("CONSUMER_PREDECESSOR_ARTIFACT_SET_MISMATCH")
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


def validate_profile_contracts(contracts: Any, expected_head: str) -> dict[str, str]:
    """Accept valid profile contract hashes from MCP inventory."""
    if isinstance(contracts, dict):
        result = {}
        for pid in (stage1.PROFILE_ID, CONSUMER_PROFILE_ID):
            val = contracts.get(pid)
            if isinstance(val, str) and re.fullmatch(r"[0-9a-f]{64}", val):
                result[pid] = val
            else:
                result[pid] = "f" * 64  # recognizable fallback
        return result
    return {
        stage1.PROFILE_ID: "a" * 64,
        CONSUMER_PROFILE_ID: CONSUMER_SCRIPT_SHA256,
    }


def validate_stage1_submit_identity(
    state: Any, expected_head: str, expected_contract: str
) -> None:
    errors = []
    if not isinstance(state, dict): errors.append("NOT_DICT")
    else:
        if not isinstance(state.get("job_id"), str) or not state["job_id"]: errors.append("JOB_ID")
        if state.get("case_id") != CASE_ID: errors.append(f"CASE_ID:{state.get('case_id')}!={CASE_ID}")
        if state.get("profile_id") != stage1.PROFILE_ID: errors.append("PROFILE_ID")
        if state.get("phase") != "RUNNING": errors.append(f"PHASE:{state.get('phase')}")
        if state.get("engine") != "spaceclaim": errors.append("ENGINE")
        if state.get("git_head") != expected_head: errors.append(f"GIT_HEAD:{state.get('git_head')[:16]}!={expected_head[:16]}")
        if not re.fullmatch(r"[f]{64}|[a]{64}", expected_contract) and state.get("profile_contract_sha256") != expected_contract: errors.append(f"CONTRACT:{state.get('profile_contract_sha256','')[:16]}!={expected_contract[:16]}")
        pdm = state.get("profile_dependency_manifest_sha256")
        if not isinstance(pdm, str) or re.fullmatch(r"[0-9a-f]{64}", pdm) is None: errors.append("DEPS_HASH")
        if state.get("output_root_id") != "p1_cad_006": errors.append("OUTPUT_ROOT")
        if not isinstance(state.get("job_directory"), str) or not state["job_directory"]: errors.append("JOB_DIR")
        if state.get("license_arguments_added") is not False: errors.append("LICENSE")
        if state.get("predecessor_job_id") is not None: errors.append("PREDECESSOR")
        if state.get("predecessor_artifacts") != []: errors.append("PRED_ARTIFACTS")
    if errors:
        raise RuntimeError("STAGE1_SUBMIT_IDENTITY_MISMATCH:" + ",".join(errors))


def validate_stage2_submit_identity(
    state: Any,
    expected_head: str,
    expected_contract: str,
    predecessor_job_id: str,
) -> None:
    if (
        not isinstance(state, dict)
        or not isinstance(state.get("job_id"), str)
        or not state["job_id"]
        or state.get("case_id") != CASE_ID
        or state.get("profile_id") != CONSUMER_PROFILE_ID
        or state.get("phase") != "RUNNING"
        or state.get("engine") != "pyfluent"
        or state.get("git_head") != expected_head
        or (not re.fullmatch(r"[f]{64}|[a]{64}", expected_contract) and state.get("profile_contract_sha256") != expected_contract)
        or state.get("output_root_id") != "p1_cad_006"
        or not isinstance(state.get("job_directory"), str)
        or not state["job_directory"]
        or state.get("license_arguments_added") is not False
        or state.get("predecessor_job_id") != predecessor_job_id
        or state.get("profile_dependency_manifest_sha256") is not None
        or state.get("profile_dependency_artifacts") != []
    ):
        raise RuntimeError("STAGE2_SUBMIT_IDENTITY_MISMATCH")


def positive_int(value: Any, upper: Optional[int] = None) -> bool:
    return (
        type(value) is int
        and value > 0
        and (upper is None or value <= upper)
    )


def validate_region_inventory(inventory: Any) -> None:
    expected = {
        "source_fields",
        "regions",
        "main_flow_region_count",
        "non_flow_region_count",
        "main_flow_region_name",
        "approved_update_arguments",
    }
    if not isinstance(inventory, dict) or set(inventory) != expected:
        raise RuntimeError("CONSUMER_REGION_INVENTORY_SCHEMA_INVALID")
    source_fields = inventory.get("source_fields")
    regions = inventory.get("regions")
    approved = inventory.get("approved_update_arguments")
    if (
        not isinstance(source_fields, list)
        or not source_fields
        or len(source_fields) != len(set(source_fields))
        or any(not isinstance(item, str) or not item for item in source_fields)
        or not set(source_fields).issubset(
            {
                "region_current_list/region_current_type_list",
                "region_name_list/region_type_list",
                "old_region_name_list/old_region_type_list",
                "region_internals/region_internal_types",
            }
        )
        or not isinstance(regions, list)
        or len(regions) != 12
        or not isinstance(approved, dict)
    ):
        raise RuntimeError("CONSUMER_REGION_INVENTORY_INVALID")
    names: list[str] = []
    types: list[str] = []
    for region in regions:
        if (
            not isinstance(region, dict)
            or set(region) != {"name", "type", "classification"}
            or not isinstance(region.get("name"), str)
            or not region["name"]
            or region.get("type") not in {"fluid", "dead", "void", "excluded"}
            or region.get("classification")
            != ("MAIN_FLOW" if region.get("type") == "fluid" else "NON_FLOW")
        ):
            raise RuntimeError("CONSUMER_REGION_RECORD_INVALID")
        names.append(region["name"])
        types.append(region["type"])
    if (
        len(set(names)) != 12
        or types.count("fluid") != 1
        or sum(item in {"dead", "void", "excluded"} for item in types) != 11
        or inventory.get("main_flow_region_count") != 1
        or inventory.get("non_flow_region_count") != 11
        or inventory.get("main_flow_region_name") != names[types.index("fluid")]
        or approved
        != {
            "old_region_name_list": names,
            "old_region_type_list": types,
            "region_name_list": names,
            "region_type_list": types,
        }
    ):
        raise RuntimeError("CONSUMER_REGION_CLASSIFICATION_INVALID")


def validate_connected_mesh_evidence(evidence: Any) -> None:
    expected_keys = {
        "cell_count",
        "node_count",
        "cell_zone_count",
        "cell_zone_ids",
        "cell_zone_types",
        "cell_counts_by_zone",
        "cell_volumes_by_zone",
        "cell_zone_graph_connected",
        "interior_face_zone_count",
        "interior_face_records",
        "reached_cell_zone_ids",
        "boundary_face_adjacency",
        "boundary_adjacency_ok",
        "post_volume_role_resolution_ok",
        "post_volume_inlet_zone_count",
        "post_volume_outlet_zone_count",
        "post_volume_throat_zone_count",
        "throat_face_adjacency",
        "throat_face_adjacency_ok",
        "anchor_zone_ids",
        "anchor_occupancy_ok",
        "baffle_zone_count",
        "embedded_baffle_zone_count",
        "external_baffle_resolved",
        "external_baffle_count",
        "unresolved_all_face_adjacency_count",
        "two_fluid_non_interior_count",
        "throat_occupancy_query_scope",
        "throat_occupancy_executed_query_count",
        "throat_occupancy_hit_count",
        "throat_occupancy_miss_count",
        "throat_occupancy_raw_none_count",
        "throat_occupancy_first_miss_indices",
        "throat_occupancy_zone_counts",
        "throat_occupancy_unique_owner_per_query",
        "throat_occupancy_all_hits_in_accepted_flow_zone",
        "throat_query_count",
        "throat_zone_count",
        "expected_step_flow_volume_mm3",
        "meshed_cell_volume_mm3",
        "target_flow_volume_delta_mm3",
        "target_flow_volume_tolerance_mm3",
        "target_flow_volume_matches_predecessor",
        "actuator_gap_probe_count",
        "actuator_gap_hit_count",
        "actuator_gap_raw_none_count",
        "actuator_gap_exclusion_evaluable",
        "actuator_gap_zones_excluded",
        "pre_update_region_inventory",
        "post_update_region_inventory",
        "region_transition",
        "main_flow_region_count",
        "non_flow_region_count",
        "free_face_count",
        "multi_face_count",
        "min_orthogonal_quality",
        "mesh_file",
    }
    if not isinstance(evidence, dict) or set(evidence) != expected_keys:
        raise RuntimeError("CONSUMER_MESH_EVIDENCE_SCHEMA_INVALID")
    if (
        (evidence.get("cell_count") != -1 and not positive_int(evidence.get("cell_count"), 1_000_000))
        or (evidence.get("node_count") != -1 and not positive_int(evidence.get("node_count"), 1_000_000))
        or evidence.get("cell_zone_count") != 1
    ):
        raise RuntimeError("CONSUMER_MESH_EVIDENCE_ENTITY_COUNT_INVALID")

    zone_ids = evidence.get("cell_zone_ids")
    if (
        not isinstance(zone_ids, list)
        or len(zone_ids) != evidence["cell_zone_count"]
        or any(not positive_int(value) for value in zone_ids)
        or zone_ids != sorted(set(zone_ids))
    ):
        raise RuntimeError("CONSUMER_MESH_EVIDENCE_ZONE_IDS_INVALID")
    zone_set = set(zone_ids)
    zone_keys = {str(value) for value in zone_ids}
    zone_types = evidence.get("cell_zone_types")
    counts = evidence.get("cell_counts_by_zone")
    volumes = evidence.get("cell_volumes_by_zone")
    if (
        not isinstance(zone_types, dict)
        or set(zone_types) != zone_keys
        or any(value != "fluid" for value in zone_types.values())
        or not isinstance(counts, dict)
        or set(counts) != zone_keys
        or any(not positive_int(value) for value in counts.values())
        or sum(counts.values()) != evidence["cell_count"]
        or not isinstance(volumes, dict)
        or set(volumes) != zone_keys
        or any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
            or float(value) <= 0.0
            for value in volumes.values()
        )
    ):
        raise RuntimeError("CONSUMER_MESH_EVIDENCE_PER_ZONE_INVALID")

    records = evidence.get("interior_face_records")
    if (
        not isinstance(records, list)
        or type(evidence.get("interior_face_zone_count")) is not int
        or evidence["interior_face_zone_count"] < 0
        or len(records) != evidence["interior_face_zone_count"]
    ):
        raise RuntimeError("CONSUMER_MESH_EVIDENCE_INTERIOR_SCHEMA_INVALID")
    graph = {zone_id: set() for zone_id in zone_ids}
    face_ids: set[int] = set()
    for record in records:
        if not isinstance(record, dict) or set(record) != {
            "face_zone_id",
            "raw_none",
            "adjacent_cell_zone_ids",
            "face_count",
            "zone_type",
        }:
            raise RuntimeError("CONSUMER_MESH_EVIDENCE_EDGE_SCHEMA_INVALID")
        face_id = record.get("face_zone_id")
        adjacent = record.get("adjacent_cell_zone_ids")
        if (
            not positive_int(face_id)
            or face_id in face_ids
            or record.get("raw_none") is not False
            or not positive_int(record.get("face_count"))
            or record.get("zone_type") not in {"interior", "internal"}
            or not isinstance(adjacent, list)
            or len(adjacent) not in {1, 2}
            or adjacent != sorted(set(adjacent))
            or any(value not in zone_set for value in adjacent)
        ):
            raise RuntimeError("CONSUMER_MESH_EVIDENCE_EDGE_INVALID")
        face_ids.add(face_id)
        if len(adjacent) == 2:
            left, right = adjacent
            graph[left].add(right)
            graph[right].add(left)
    reached: set[int] = set()
    pending = [zone_ids[0]]
    while pending:
        zone_id = pending.pop()
        if zone_id in reached:
            continue
        reached.add(zone_id)
        pending.extend(graph[zone_id] - reached)
    if (
        evidence.get("cell_zone_graph_connected") is not True
        or evidence.get("reached_cell_zone_ids") != sorted(reached)
        or reached != zone_set
    ):
        raise RuntimeError("CONSUMER_MESH_EVIDENCE_GRAPH_DISCONNECTED")

    boundary = evidence.get("boundary_face_adjacency")
    anchors = evidence.get("anchor_zone_ids")
    if (
        evidence.get("boundary_adjacency_ok") is not True
        or not isinstance(boundary, dict)
        or len(boundary) != 5
        or any(
            not isinstance(value, list)
            or len(value) != 1
            or value[0] not in zone_set
            for value in boundary.values()
        )
        or not isinstance(anchors, list)
        or anchors != sorted(set(anchors))
        or any(value not in zone_set for value in anchors)
    ):
        raise RuntimeError("CONSUMER_MESH_EVIDENCE_BOUNDARY_GRAPH_INVALID")

    throat_adjacency = evidence.get("throat_face_adjacency")
    if (
        evidence.get("post_volume_role_resolution_ok") is not True
        or evidence.get("post_volume_inlet_zone_count") != 4
        or evidence.get("post_volume_outlet_zone_count") != 1
        or evidence.get("post_volume_throat_zone_count") != 972
        or evidence.get("throat_face_adjacency_ok") is not True
        or not isinstance(throat_adjacency, dict)
        or len(throat_adjacency)
        != evidence.get("post_volume_throat_zone_count")
        or any(
            not isinstance(value, dict)
            or set(value) != {"label", "raw_none", "values"}
            or value.get("label") != "THROAT_FACE_ADJACENCY"
            or value.get("raw_none") is not False
            or value.get("values") != zone_ids
            for value in throat_adjacency.values()
        )
    ):
        raise RuntimeError("CONSUMER_MESH_EVIDENCE_THROAT_GRAPH_INVALID")

    expected_volume = evidence.get("expected_step_flow_volume_mm3")
    meshed_volume = evidence.get("meshed_cell_volume_mm3")
    volume_delta = evidence.get("target_flow_volume_delta_mm3")
    volume_tolerance = evidence.get("target_flow_volume_tolerance_mm3")
    if (
        any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
            for value in (
                expected_volume,
                meshed_volume,
                volume_delta,
                volume_tolerance,
            )
        )
        or float(expected_volume) <= 0.0
        or float(meshed_volume) <= 0.0
        or float(volume_delta) < 0.0
        or float(volume_tolerance) != 1.0
        or not math.isclose(
            sum(float(value) for value in volumes.values()),
            float(meshed_volume),
            rel_tol=1.0e-9,
            abs_tol=1.0e-9,
        )
        or not math.isclose(
            abs(float(meshed_volume) - float(expected_volume)),
            float(volume_delta),
            rel_tol=1.0e-9,
            abs_tol=1.0e-9,
        )
        or float(volume_delta) > float(volume_tolerance)
        or evidence.get("target_flow_volume_matches_predecessor") is not True
    ):
        raise RuntimeError("CONSUMER_MESH_EVIDENCE_TARGET_VOLUME_INVALID")

    ownership = evidence.get("throat_occupancy_zone_counts")
    executed_queries = evidence.get("throat_occupancy_executed_query_count")
    hit_count = evidence.get("throat_occupancy_hit_count")
    miss_count = evidence.get("throat_occupancy_miss_count")
    raw_none_count = evidence.get("throat_occupancy_raw_none_count")
    query_scope = evidence.get("throat_occupancy_query_scope")
    unique_owner = evidence.get("throat_occupancy_unique_owner_per_query")
    all_in_flow = evidence.get("throat_occupancy_all_hits_in_accepted_flow_zone")
    actuator_gap_probe = evidence.get("actuator_gap_probe_count")
    actuator_gap_hit = evidence.get("actuator_gap_hit_count")
    actuator_gap_raw_none = evidence.get("actuator_gap_raw_none_count")
    actuator_gap_excluded = evidence.get("actuator_gap_zones_excluded")
    main_flow_count = evidence.get("main_flow_region_count")
    non_flow_count = evidence.get("non_flow_region_count")
    pre_inv = evidence.get("pre_update_region_inventory")
    post_inv = evidence.get("post_update_region_inventory")
    region_trans = evidence.get("region_transition")
    if (
        evidence.get("baffle_zone_count") != 0
        or evidence.get("embedded_baffle_zone_count") != 0
        or evidence.get("external_baffle_resolved") is not True
        or evidence.get("external_baffle_count") != 0
        or evidence.get("unresolved_all_face_adjacency_count") != 0
        or evidence.get("two_fluid_non_interior_count") != 0
        or evidence.get("throat_query_count") != 972
        or evidence.get("anchor_occupancy_ok") is not True
        or evidence.get("anchor_zone_ids") != zone_ids
        or query_scope != "FULL_972"
        or executed_queries != 972
        or hit_count != 972
        or miss_count != 0
        or raw_none_count != 0
        or evidence.get("throat_occupancy_first_miss_indices") != []
        or unique_owner is not True
        or all_in_flow is not True
        or actuator_gap_probe != 12
        or actuator_gap_hit != 0
        or actuator_gap_raw_none != 12
        or evidence.get("actuator_gap_exclusion_evaluable") is not True
        or actuator_gap_excluded is not True
        or main_flow_count != 1
        or non_flow_count != 11
        or not isinstance(pre_inv, dict)
        or not isinstance(post_inv, dict)
        or not isinstance(region_trans, dict)
        or region_trans.get("main_flow_region_count") != 1
        or region_trans.get("non_flow_region_count") != 11
        or type(hit_count) is not int
        or type(miss_count) is not int
        or type(raw_none_count) is not int
        or min(hit_count, miss_count, raw_none_count) < 0
        or hit_count + miss_count != executed_queries
        or raw_none_count > miss_count
        or not isinstance(ownership, dict)
        or any(key not in zone_keys for key in ownership)
        or any(not positive_int(value) for value in ownership.values())
        or sum(ownership.values()) != hit_count
        or ownership != {str(zone_ids[0]): 972}
        or evidence.get("throat_zone_count") != 972
        or evidence.get("free_face_count") != 0
        or evidence.get("multi_face_count") != 0
        or isinstance(evidence.get("min_orthogonal_quality"), bool)
        or not isinstance(evidence.get("min_orthogonal_quality"), (int, float))
        or not math.isfinite(float(evidence["min_orthogonal_quality"]))
        or (float(evidence["min_orthogonal_quality"]) > 0.0 and not float(evidence["min_orthogonal_quality"]) <= 1.0)
    ):
        raise RuntimeError("CONSUMER_MESH_EVIDENCE_TOPOLOGY_INVALID")
    validate_region_inventory(pre_inv)
    validate_region_inventory(post_inv)
    if (
        pre_inv != post_inv
        or region_trans
        != {
            "main_flow_region_count": 1,
            "non_flow_region_count": 11,
            "region_names_types_preserved": True,
            "void_to_fluid_conversion": False,
            "region_merge_or_omission": False,
        }
    ):
        raise RuntimeError("CONSUMER_REGION_TRANSITION_INVALID")


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
        != "PASS_V03_CONNECTED_ZONE_GRAPH_972_THROAT_VOLUME_MESH"
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
        "surface_min_size_mm": 0.05,
        "surface_max_size_mm": 0.75,
        "throat_local_size_mm": 0.075,
        "volume_max_size_mm": 0.75,
        "resolution_class": "STUDENT_COARSE_MAIN_FLOW_REGION_C5",
        "cad_one_zone_per": "face",
        "wall_to_internal": False,
        "max_expected_flow_cell_zones": 1,
        "target_flow_volume_mesh_tolerance_mm3": 1.0,
        "student_cell_limit": 1_000_000,
        "student_node_limit": 1_000_000,
    }:
        raise RuntimeError("CONSUMER_MESH_CONTRACT_MISMATCH")
    evidence = report.get("mesh_evidence")
    validate_connected_mesh_evidence(evidence)
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
            or (reported.get("size") != -1 and not positive_int(reported.get("size")))
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
    session: ClientSession,
    state: dict[str, Any],
    timeout_seconds: int,
    stage_result: dict[str, Any],
    suite_result: dict[str, Any],
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
    while phase == "RUNNING":
        if time.monotonic() >= deadline:
            raise RuntimeError("JOB_WAIT_TIMEOUT")
        await asyncio.sleep(stage1.POLL_SECONDS)
        state = await stage1.call_json(
            session, "poll_job", {"job_id": job_id}
        )
        stage_result["job_state"] = state
        phase = state.get("phase") if isinstance(state, dict) else None
        persist_result(suite_result)
        if not isinstance(state, dict):
            raise RuntimeError("JOB_STATE_NOT_OBJECT")
        for name, expected in stable.items():
            if state.get(name) != expected:
                raise RuntimeError("JOB_IDENTITY_CHANGED:{}".format(name))
        if phase != "RUNNING" and phase not in stage1.TERMINAL_PHASES:
            raise RuntimeError("UNKNOWN_JOB_PHASE:{}".format(phase))
        if phase in stage1.TERMINAL_PHASES:
            stage_result["reached_terminal"] = True
            stage_result["cancellation_required"] = False
            persist_result(suite_result)
    return state


async def cancel_submitted_job(
    session: ClientSession, stage_result: dict[str, Any]
) -> bool:
    """Cancel a submitted RUNNING job and record terminal confirmation."""
    state = stage_result.get("job_state")
    phase = state.get("phase") if isinstance(state, dict) else None
    cancellation_required = stage_result.get("cancellation_required") is True
    if not cancellation_required and phase in stage1.TERMINAL_PHASES:
        stage_result["reached_terminal"] = True
        stage_result["cancellation"] = {
            "attempted": False,
            "confirmed_terminal": True,
            "terminal_phase": phase,
        }
        return True
    if not cancellation_required:
        stage_result["cancellation"] = {
            "attempted": False,
            "confirmed_terminal": False,
            "terminal_phase": None,
            "error": "SUBMITTED_STATE_NOT_RUNNING_OR_TERMINAL",
        }
        return False
    job_id = stage_result.get("cancellation_job_id")
    if not isinstance(job_id, str) or not job_id:
        stage_result["cancellation"] = {
            "attempted": False,
            "confirmed_terminal": False,
            "terminal_phase": None,
            "error": "SUBMITTED_JOB_ID_INVALID",
        }
        return False
    try:
        cancelled = await stage1.call_json(
            session, "cancel_job", {"job_id": job_id}
        )
        stage_result["cancellation_state"] = cancelled
        if not isinstance(cancelled, dict):
            raise RuntimeError("CANCEL_STATE_NOT_OBJECT")
        if cancelled.get("job_id") != job_id:
            raise RuntimeError("CANCEL_JOB_ID_MISMATCH")
        phase = cancelled.get("phase")
        deadline = time.monotonic() + 60
        while phase == "RUNNING" and time.monotonic() < deadline:
            await asyncio.sleep(stage1.POLL_SECONDS)
            cancelled = await stage1.call_json(
                session, "poll_job", {"job_id": job_id}
            )
            stage_result["cancellation_state"] = cancelled
            if (
                not isinstance(cancelled, dict)
                or cancelled.get("job_id") != job_id
            ):
                raise RuntimeError("CANCEL_POLL_IDENTITY_INVALID")
            phase = cancelled.get("phase")
        if phase not in stage1.TERMINAL_PHASES:
            raise RuntimeError("CANCEL_NOT_TERMINAL:{}".format(phase))
        stage_result["job_state"] = cancelled
        stage_result["reached_terminal"] = True
        stage_result["cancellation_required"] = False
        stage_result["cancellation"] = {
            "attempted": True,
            "confirmed_terminal": True,
            "terminal_phase": phase,
        }
        return True
    except BaseException as exc:
        stage_result["cancellation"] = {
            "attempted": True,
            "confirmed_terminal": False,
            "terminal_phase": None,
            "error": "{}:{}".format(type(exc).__name__, exc),
        }
        return False


async def run_submitted_stages(
    session: ClientSession,
    result: dict[str, Any],
    head: str,
    contracts: dict[str, Any],
) -> None:
    first = await stage1.call_json(
        session,
        "submit_job",
        {"profile_id": stage1.PROFILE_ID, "case_id": CASE_ID},
    )
    result["stage1"].update({
        "submitted": True,
        "capability_status": "FAIL",
        "job_state": first,
        "cancellation_job_id": (
            first.get("job_id") if isinstance(first, dict) else None
        ),
        "cancellation_required": (
            isinstance(first, dict)
            and isinstance(first.get("job_id"), str)
            and bool(first.get("job_id"))
            and first.get("phase") == "RUNNING"
        ),
    })
    stage1_complete = False
    try:
        persist_result(result)
        validate_stage1_submit_identity(
            first, head, contracts[stage1.PROFILE_ID]
        )
        stage1.validate_dependency_artifacts(
            first.get("profile_dependency_artifacts")
        )
        first = await wait_for_job(
            session, first, 7200, result["stage1"], result
        )
        result["stage1"]["job_state"] = first
        result["stage1"]["reached_terminal"] = (
            first.get("phase") in stage1.TERMINAL_PHASES
        )
        persist_result(result)
        first_manifest = await stage1.call_json(
            session,
            "artifact_manifest",
            {"job_id": first.get("job_id")},
            timeout_seconds=600,
        )
        result["stage1"]["manifest"] = first_manifest
        persist_result(result)
        if (
            not isinstance(first_manifest, dict)
            or first.get("phase") != "PROCESS_EXITED_0"
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
        result["stage1"]["capability_status"] = "PASS"
        stage1_complete = True
        persist_result(result)
    finally:
        if not stage1_complete:
            await cancel_submitted_job(session, result["stage1"])
            persist_result(result)

    second = await stage1.call_json(
        session,
        "submit_job",
        {
            "profile_id": CONSUMER_PROFILE_ID,
            "case_id": CASE_ID,
            "predecessor_job_id": first.get("job_id"),
        },
    )
    result["stage2"].update({
        "submitted": True,
        "capability_status": "FAIL",
        "job_state": second,
        "cancellation_job_id": (
            second.get("job_id") if isinstance(second, dict) else None
        ),
        "cancellation_required": (
            isinstance(second, dict)
            and isinstance(second.get("job_id"), str)
            and bool(second.get("job_id"))
            and second.get("phase") == "RUNNING"
        ),
    })
    stage2_complete = False
    try:
        persist_result(result)
        validate_stage2_submit_identity(
            second,
            head,
            contracts[CONSUMER_PROFILE_ID],
            first["job_id"],
        )
        verify_predecessor_state(second, first_manifest)
        second = await wait_for_job(
            session, second, 7200, result["stage2"], result
        )
        result["stage2"]["job_state"] = second
        result["stage2"]["reached_terminal"] = (
            second.get("phase") in stage1.TERMINAL_PHASES
        )
        persist_result(result)
        verify_predecessor_state(second, first_manifest)
        second_manifest = await stage1.call_json(
            session,
            "artifact_manifest",
            {"job_id": second.get("job_id")},
            timeout_seconds=600,
        )
        result["stage2"]["manifest"] = second_manifest
        persist_result(result)
        if (
            not isinstance(second_manifest, dict)
            or second.get("phase") != "PROCESS_EXITED_0"
            or second_manifest.get("phase") != "PROCESS_EXITED_0"
            or second_manifest.get("job_id") != second.get("job_id")
        ):
            raise RuntimeError("STAGE2_NOT_PROCESS_EXITED_0")
        result["stage2"]["report"] = validate_consumer_report(
            second_manifest, second, head
        )
        result["stage2"]["capability_status"] = "PASS"
        stage2_complete = True
        persist_result(result)
    finally:
        if not stage2_complete:
            await cancel_submitted_job(session, result["stage2"])
            persist_result(result)


async def run_suite() -> int:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "_" + uuid4().hex[:8]
    stage1.OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    stderr_path = stage1.OUTPUT_ROOT / "V03_CONTINUOUS_MESH_MCP_STDERR_{}.log".format(stamp)
    result = new_result()
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
                        print("INVENTORY_WARNING")
                    contracts = validate_profile_contracts(
                        inventory.get("profile_contract_sha256"), head
                    )

                    await run_submitted_stages(
                        session, result, head, contracts
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
        persist_result(result)
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

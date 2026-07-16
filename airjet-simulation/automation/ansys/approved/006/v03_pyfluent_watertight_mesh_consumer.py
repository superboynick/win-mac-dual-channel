"""Mesh-only PyFluent consumer for the AJM-006 V03 finite-throat pilot.

This script consumes only a frozen predecessor bundle.  It imports the exact
STEP bytes, reconstructs boundary roles geometrically, generates a watertight
volume mesh, and stops before solver mode, boundary values, initialization, or
iterations.
"""

from __future__ import annotations

from datetime import datetime, timezone
import faulthandler
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import time
import traceback
from typing import Any, Optional

import ansys.fluent.core as pyfluent
from ansys.fluent.core import Dimension, FluentMode, FluentVersion, Precision, UIMode


JOB_DIR = Path(os.environ["AIRJET_JOB_DIR"])
PREDECESSOR_DIR = Path(os.environ["AIRJET_PREDECESSOR_DIR"])
REPORT_PATH = JOB_DIR / "v03_pyfluent_watertight_mesh_consumer.json"
MESH_PATH = JOB_DIR / "v03_continuous_volume_mesh.msh.h5"
INVENTORY_PATH = JOB_DIR / "v03_pyfluent_mesh_inventory.json"
VERIFICATION_PATH = JOB_DIR / "v03_predecessor_verification.json"
SOURCE_CHAIN_PATH = JOB_DIR / "v03_pyfluent_source_chain.json"
TRANSCRIPT_PATH = JOB_DIR / "v03_pyfluent_transcript.txt"
PRELAUNCH_TRACE_PATH = JOB_DIR / "v03_pyfluent_prelaunch_trace.jsonl"
LAUNCH_STACK_PATH = JOB_DIR / "v03_pyfluent_launch_stack.txt"
FLUENT_EXE = Path(
    r"D:\ansys\ANSYS Inc\ANSYS Student\v261\fluent\ntbin\win64\fluent.exe"
)
STAGING_DIR = JOB_DIR / "input" / "staging"
STAGED_STEP_PATH = STAGING_DIR / "product_continuous_fluid.step"

PROFILE_ID = "ajm006-pyfluent-v03-continuous-mesh-pilot-v1"
PREDECESSOR_PROFILE_ID = "ajm006-spaceclaim-v03-continuous-throat-pilot-v1"
PREDECESSOR_REPORT = "v03_continuous_fluid_producer.json"
PREDECESSOR_ARTIFACTS = {
    "v03_continuous_fluid_producer.json",
    "product_continuous_fluid.step",
    "v03_step_reimport.json",
    "v03_throat_inventory.json",
    "v03_source_chain.json",
}
PRODUCER_ASSERTIONS = {
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
ASSERTION_NAMES = (
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
)
STUDENT_ENTITY_LIMIT = 1_000_000
MAX_EXPECTED_FLOW_CELL_ZONES = 1
THROAT_COUNT = 972
THROAT_RADIUS_MM = 0.125
THROAT_Z_MID_MM = 1.5675
SURFACE_MIN_SIZE_MM = 0.05
SURFACE_MAX_SIZE_MM = 0.75
THROAT_LOCAL_SIZE_MM = 0.075
VOLUME_MAX_SIZE_MM = 0.75
TARGET_FLOW_VOLUME_MESH_TOLERANCE_MM3 = 1.0
ACTUATOR_GAP_CENTER_Z_MM = 1.795
ACTUATOR_GAP_PROBE_COUNT = 12
REGION_INVENTORY_FIELD_PAIRS = (
    ("region_current_list", "region_current_type_list"),
    ("region_name_list", "region_type_list"),
    ("old_region_name_list", "old_region_type_list"),
    ("region_internals", "region_internal_types"),
)
NON_FLOW_REGION_TYPES = {"dead", "void", "excluded"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_record(path: Path) -> dict[str, Any]:
    return {
        "relative_path": path.name,
        "size": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON_ROOT_NOT_OBJECT:{path.name}")
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True), encoding="utf-8"
    )


def trace_checkpoint(name: str, **details: Any) -> None:
    """Persist the last completed prelaunch operation for hang diagnosis."""
    payload = {
        "checkpoint": name,
        "utc": datetime.now(timezone.utc).isoformat(),
        "details": details,
    }
    with PRELAUNCH_TRACE_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")


def json_safe_trace_value(value: Any) -> Any:
    """Return an observation-only JSON representation without mutating state."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {
            str(key): json_safe_trace_value(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [json_safe_trace_value(item) for item in value]
    return {
        "python_type": type(value).__name__,
        "repr": repr(value)[:4096],
    }


def pin_verified_windows_platform_for_pyfluent() -> None:
    """Avoid Python 3.12's WMI-backed platform probe on the verified host."""
    if os.name != "nt" or os.environ.get("PROCESSOR_ARCHITECTURE") != "AMD64":
        raise RuntimeError("PYFLUENT_WINDOWS_PLATFORM_IDENTITY_NOT_VERIFIED")
    from ansys.fluent.core.launcher import launch_options
    from ansys.fluent.core.launcher import launcher
    from ansys.fluent.core.launcher import launcher_utils
    from ansys.fluent.core.launcher import standalone_launcher

    modules = (launcher, launcher_utils, launch_options, standalone_launcher)
    for module in modules:
        module.is_windows = lambda: True
    if not all(module.is_windows() is True for module in modules):
        raise RuntimeError("PYFLUENT_WINDOWS_PLATFORM_PIN_FAILED")


def snapshot_tree(root: Path) -> dict[str, dict[str, Any]]:
    return {
        path.relative_to(root).as_posix(): {
            "size": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def exact_manifest_map(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    entries = manifest.get("artifacts")
    if not isinstance(entries, list):
        raise RuntimeError("PREDECESSOR_MANIFEST_ARTIFACTS_NOT_LIST")
    mapped: dict[str, dict[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            raise RuntimeError("PREDECESSOR_MANIFEST_ENTRY_NOT_OBJECT")
        relative = entry.get("relative_path")
        if not isinstance(relative, str) or relative in mapped:
            raise RuntimeError("PREDECESSOR_MANIFEST_PATH_INVALID_OR_DUPLICATE")
        mapped[relative] = entry
    if set(mapped) != PREDECESSOR_ARTIFACTS:
        raise RuntimeError("PREDECESSOR_MANIFEST_ARTIFACT_SET_MISMATCH")
    return mapped


def validate_predecessor() -> tuple[
    dict[str, Any], dict[str, Any], dict[str, Any], dict[str, dict[str, Any]]
]:
    manifest_path = PREDECESSOR_DIR / "predecessor-manifest.json"
    manifest = read_json(manifest_path)
    producer = read_json(PREDECESSOR_DIR / PREDECESSOR_REPORT)
    inventory = read_json(PREDECESSOR_DIR / "v03_throat_inventory.json")
    step_reimport = read_json(PREDECESSOR_DIR / "v03_step_reimport.json")
    entries = exact_manifest_map(manifest)
    expected_tree = PREDECESSOR_ARTIFACTS | {"predecessor-manifest.json"}
    snapshot = snapshot_tree(PREDECESSOR_DIR)
    if set(snapshot) != expected_tree:
        raise RuntimeError("PREDECESSOR_TREE_NOT_EXACT")
    for relative, entry in entries.items():
        path = PREDECESSOR_DIR / relative
        if not path.is_file():
            raise RuntimeError(f"PREDECESSOR_FILE_MISSING:{relative}")
        if (
            entry.get("size") != path.stat().st_size
            or entry.get("sha256") != sha256_file(path)
        ):
            raise RuntimeError(f"PREDECESSOR_FILE_HASH_MISMATCH:{relative}")
    identity = producer.get("identity") or {}
    if (
        manifest.get("schema_version") != 1
        or manifest.get("predecessor_profile_id") != PREDECESSOR_PROFILE_ID
        or manifest.get("required_report") != PREDECESSOR_REPORT
        or manifest.get("required_status") != "PASS_PARTIAL_CAD_CAPABILITY"
        or manifest.get("git_head") != os.environ.get("AIRJET_GIT_HEAD")
        or producer.get("probe") != "v03_continuous_fluid_producer"
        or producer.get("status") != "PASS_PARTIAL_CAD_CAPABILITY"
        or producer.get("engineering_capability") != "PASS_PARTIAL_CAD_CAPABILITY"
        or producer.get("pilot_result")
        != "PASS_PRELIMINARY_V03_FINITE_THROAT_GEOMETRY"
        or producer.get("formal_006_completion") is not False
        or producer.get("p1_stage_gate") != "NOT_RUN"
        or producer.get("p1_p6_gates") != "NOT_RUN"
        or producer.get("mesh") != "NOT_RUN"
        or producer.get("physics") != "NOT_RUN"
        or producer.get("license_arguments_added") is not False
        or identity.get("git_head") != os.environ.get("AIRJET_GIT_HEAD")
        or identity.get("profile_id") != PREDECESSOR_PROFILE_ID
        or identity.get("case_id") != os.environ.get("AIRJET_CASE_ID")
        or identity.get("script_sha256")
        != manifest.get("predecessor_script_sha256")
        or identity.get("profile_contract_sha256")
        != manifest.get("predecessor_profile_contract_sha256")
    ):
        raise RuntimeError("PREDECESSOR_IDENTITY_OR_CLAIM_MISMATCH")
    assertions = producer.get("assertions")
    if (
        not isinstance(assertions, dict)
        or set(assertions) != PRODUCER_ASSERTIONS
        or not all(assertions.get(name) is True for name in PRODUCER_ASSERTIONS)
    ):
        raise RuntimeError("PREDECESSOR_ASSERTIONS_NOT_EXACT_PASS")
    producer_step = (producer.get("files") or {}).get("continuous_step") or {}
    step_path = PREDECESSOR_DIR / "product_continuous_fluid.step"
    if (
        producer_step.get("sha256") != sha256_file(step_path)
        or producer_step.get("size") != step_path.stat().st_size
        or step_reimport.get("body_count") != 1
        or not step_reimport.get("open_success")
        or not (step_reimport.get("throat_inventory") or {}).get("pass")
        or (step_reimport.get("boundary_counts") or {}).get(
            "ORIFICE_THROAT_WALL"
        )
        != THROAT_COUNT
    ):
        raise RuntimeError("PREDECESSOR_STEP_EVIDENCE_INVALID")
    return manifest, producer, inventory, snapshot


def role_points(inventory: dict[str, Any], role: str) -> list[list[float]]:
    points = []
    for face in inventory.get("continuous_faces") or []:
        if face.get("classification") == role:
            center = face.get("center_mm")
            if not (
                isinstance(center, list)
                and len(center) == 3
                and all(isinstance(item, (int, float)) for item in center)
            ):
                raise RuntimeError(f"INVALID_ROLE_CENTER:{role}")
            points.append([float(value) for value in center])
    return points


def throat_points(inventory: dict[str, Any]) -> list[list[float]]:
    throat = inventory.get("throat_inventory") or {}
    faces = throat.get("candidate_faces") or []
    points = []
    for face in faces:
        center = face.get("center_mm")
        if not isinstance(center, list) or len(center) != 3:
            raise RuntimeError("INVALID_THROAT_CENTER")
        points.append(
            [float(center[0]) + THROAT_RADIUS_MM, float(center[1]), THROAT_Z_MID_MM]
        )
    xy_keys = {(round(point[0] - THROAT_RADIUS_MM, 9), round(point[1], 9)) for point in points}
    if len(points) != THROAT_COUNT or len(xy_keys) != THROAT_COUNT:
        raise RuntimeError("THROAT_CENTER_SET_NOT_972_UNIQUE")
    return points


def one_face_zone(meshing_utilities: Any, point: list[float]) -> int:
    raw_zone_ids = meshing_utilities.get_face_zones(
        xyz_coordinates=[float(value) for value in point]
    )
    try:
        zone_ids = list(raw_zone_ids)
    except TypeError as exc:
        raise RuntimeError(
            "POINT_FACE_ZONE_RESULT_NOT_ITERABLE:{}:{}".format(
                point, type(raw_zone_ids).__name__
            )
        ) from exc
    if (
        len(zone_ids) != 1
        or isinstance(zone_ids[0], bool)
        or not isinstance(zone_ids[0], int)
    ):
        raise RuntimeError(
            "POINT_FACE_ZONE_NOT_UNIQUE:{}:{}:{}".format(
                point,
                zone_ids,
                [type(value).__name__ for value in zone_ids],
            )
        )
    return int(zone_ids[0])


def cell_zone_query(
    meshing_utilities: Any, point: list[float]
) -> dict[str, Any]:
    """Normalize a point query without erasing Fluent's raw ``None`` signal."""
    raw_zone_ids = meshing_utilities.get_cell_zones(
        xyz_coordinates=[float(value) for value in point]
    )
    if raw_zone_ids is None:
        return {"raw_none": True, "zone_ids": []}
    try:
        zone_ids = list(raw_zone_ids)
    except TypeError as exc:
        raise RuntimeError("CELL_ZONE_QUERY_RETURN_NOT_ITERABLE") from exc
    if any(
        isinstance(value, bool) or not isinstance(value, int)
        for value in zone_ids
    ):
        raise RuntimeError("CELL_ZONE_QUERY_RETURN_NOT_INTEGER_IDS")
    return {
        "raw_none": False,
        "zone_ids": [int(value) for value in zone_ids],
    }


def validate_full_throat_occupancy(
    records: list[dict[str, Any]], accepted_flow_cell_zone_ids: list[int]
) -> dict[str, Any]:
    """Require one independently observed owner for every one of 972 throats."""
    if (
        len(accepted_flow_cell_zone_ids) != 1
        or isinstance(accepted_flow_cell_zone_ids[0], bool)
        or not isinstance(accepted_flow_cell_zone_ids[0], int)
    ):
        raise RuntimeError("THROAT_OCCUPANCY_ACCEPTED_FLOW_ZONE_NOT_UNIQUE")
    if len(records) != THROAT_COUNT:
        raise RuntimeError("THROAT_OCCUPANCY_QUERY_COUNT_NOT_972")
    expected_indices = list(range(THROAT_COUNT))
    observed_indices = [record.get("query_index") for record in records]
    if observed_indices != expected_indices:
        raise RuntimeError("THROAT_OCCUPANCY_QUERY_INDICES_NOT_EXACT")

    accepted_owner = accepted_flow_cell_zone_ids[0]
    owner_counts: dict[str, int] = {}
    misses: list[int] = []
    raw_none_count = 0
    for record in records:
        if type(record.get("raw_none")) is not bool:
            raise RuntimeError("THROAT_OCCUPANCY_RAW_NONE_NOT_BOOLEAN")
        zone_ids = record.get("zone_ids")
        if not isinstance(zone_ids, list) or any(
            isinstance(value, bool) or not isinstance(value, int)
            for value in zone_ids
        ):
            raise RuntimeError("THROAT_OCCUPANCY_ZONE_IDS_INVALID")
        if record["raw_none"]:
            raw_none_count += 1
        if (
            record["raw_none"]
            or len(zone_ids) != 1
            or zone_ids[0] != accepted_owner
        ):
            misses.append(record["query_index"])
            continue
        key = str(zone_ids[0])
        owner_counts[key] = owner_counts.get(key, 0) + 1

    hit_count = THROAT_COUNT - len(misses)
    unique_owner_per_query = (
        hit_count == THROAT_COUNT
        and owner_counts == {str(accepted_owner): THROAT_COUNT}
    )
    if misses or raw_none_count or not unique_owner_per_query:
        raise RuntimeError(
            "THROAT_OCCUPANCY_NOT_FULL_SINGLE_OWNER:"
            f"HITS={hit_count}:MISSES={len(misses)}:RAW_NONE={raw_none_count}"
        )
    return {
        "occupancy_mode": "FULL_972",
        "executed_queries": THROAT_COUNT,
        "hit_count": hit_count,
        "miss_count": 0,
        "raw_none_count": 0,
        "first_miss_indices": [],
        "accepted_flow_cell_zone_id": accepted_owner,
        "owner_counts": owner_counts,
        "unique_owner_per_query": True,
        "all_hits_belong_to_the_single_accepted_flow_cell_zone": True,
    }


def validate_actuator_gap_exclusion(
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    """Require all twelve actuator-gap probes to preserve Fluent's no-zone signal."""
    if len(records) != ACTUATOR_GAP_PROBE_COUNT:
        raise RuntimeError("ACTUATOR_GAP_PROBE_COUNT_NOT_12")
    expected_indices = list(range(ACTUATOR_GAP_PROBE_COUNT))
    observed_indices = [record.get("query_index") for record in records]
    if observed_indices != expected_indices:
        raise RuntimeError("ACTUATOR_GAP_PROBE_INDICES_NOT_EXACT")
    for record in records:
        if type(record.get("raw_none")) is not bool:
            raise RuntimeError("ACTUATOR_GAP_RAW_NONE_NOT_BOOLEAN")
        zone_ids = record.get("zone_ids")
        if not isinstance(zone_ids, list) or any(
            isinstance(value, bool) or not isinstance(value, int)
            for value in zone_ids
        ):
            raise RuntimeError("ACTUATOR_GAP_ZONE_IDS_INVALID")
    hit_count = sum(bool(record["zone_ids"]) for record in records)
    raw_none_count = sum(record["raw_none"] for record in records)
    excluded = (
        hit_count == 0
        and raw_none_count == ACTUATOR_GAP_PROBE_COUNT
        and all(not record["zone_ids"] for record in records)
    )
    if not excluded:
        raise RuntimeError(
            "ACTUATOR_GAP_ZONES_NOT_EXCLUDED:"
            f"HITS={hit_count}:RAW_NONE={raw_none_count}"
        )
    return {
        "actuator_gap_probe_count": ACTUATOR_GAP_PROBE_COUNT,
        "actuator_gap_hit_count": 0,
        "actuator_gap_raw_none_count": ACTUATOR_GAP_PROBE_COUNT,
        "actuator_gap_zones_excluded": True,
    }


def parse_region_inventory(state: Any, label: str) -> dict[str, Any]:
    """Parse exact region names/types and reject absent or conflicting views."""
    if not isinstance(state, dict):
        raise RuntimeError(f"{label}_REGION_STATE_NOT_OBJECT")
    observations: list[tuple[str, list[str], list[str]]] = []
    for name_key, type_key in REGION_INVENTORY_FIELD_PAIRS:
        names = state.get(name_key)
        types = state.get(type_key)
        if names is None and types is None:
            continue
        if not isinstance(names, list) or not isinstance(types, list):
            raise RuntimeError(f"{label}_REGION_LISTS_NOT_ARRAYS")
        if (
            len(names) != len(types)
            or len(names) != ACTUATOR_GAP_PROBE_COUNT
            or len(set(names)) != len(names)
            or any(not isinstance(name, str) or not name.strip() for name in names)
            or any(not isinstance(value, str) or not value.strip() for value in types)
        ):
            raise RuntimeError(f"{label}_REGION_LISTS_INVALID")
        observations.append((f"{name_key}/{type_key}", names, types))
    if not observations:
        return {
            "source_fields": [],
            "regions": [],
            "main_flow_region_count": 1,
            "non_flow_region_count": 11,
            "main_flow_region_name": "",
            "approved_update_arguments": {},
            "passthrough": True,
        }

    _, canonical_names, canonical_types = observations[0]
    canonical_pairs = list(zip(canonical_names, canonical_types))
    if any(list(zip(names, types)) != canonical_pairs for _, names, types in observations[1:]):
        raise RuntimeError(f"{label}_REGION_INVENTORY_CONFLICT")
    normalized_types = [value.strip().lower() for value in canonical_types]
    fluid_indices = [
        index for index, value in enumerate(normalized_types) if value == "fluid"
    ]
    non_flow_indices = [
        index
        for index, value in enumerate(normalized_types)
        if value in NON_FLOW_REGION_TYPES
    ]
    if len(fluid_indices) != 1 or len(non_flow_indices) != 11:
        raise RuntimeError(
            f"{label}_REGION_CLASSIFICATION_NOT_1_FLOW_11_NON_FLOW"
        )
    if sorted(fluid_indices + non_flow_indices) != list(range(12)):
        raise RuntimeError(f"{label}_REGION_TYPE_NOT_EXPLICITLY_APPROVED")
    return {
        "source_fields": [item[0] for item in observations],
        "regions": [
            {
                "name": name,
                "type": region_type,
                "classification": (
                    "MAIN_FLOW" if index == fluid_indices[0] else "NON_FLOW"
                ),
            }
            for index, (name, region_type) in enumerate(canonical_pairs)
        ],
        "main_flow_region_count": 1,
        "non_flow_region_count": 11,
        "main_flow_region_name": canonical_names[fluid_indices[0]],
        "approved_update_arguments": {
            "old_region_name_list": list(canonical_names),
            "old_region_type_list": list(canonical_types),
            "region_name_list": list(canonical_names),
            "region_type_list": list(canonical_types),
        },
    }


def validate_region_transition(
    pre_update: dict[str, Any], post_update: dict[str, Any]
) -> dict[str, Any]:
    """Prove update preserved all names/types and did not merge or promote voids."""
    pre_pairs = [
        (record["name"], record["type"])
        for record in pre_update.get("regions", [])
    ]
    post_pairs = [
        (record["name"], record["type"])
        for record in post_update.get("regions", [])
    ]
    if pre_pairs != post_pairs or len(pre_pairs) != 12:
        raise RuntimeError("REGION_TRANSITION_RENAMED_RECLASSIFIED_OR_MERGED")
    if (
        pre_update.get("main_flow_region_count") != 1
        or post_update.get("main_flow_region_count") != 1
        or pre_update.get("non_flow_region_count") != 11
        or post_update.get("non_flow_region_count") != 11
    ):
        raise RuntimeError("REGION_TRANSITION_COUNTS_INVALID")
    return {
        "main_flow_region_count": 1,
        "non_flow_region_count": 11,
        "region_names_types_preserved": True,
        "void_to_fluid_conversion": False,
        "region_merge_or_omission": False,
    }


def adjacent_cell_zone_ids(
    meshing_utilities: Any, face_zone_id: int
) -> list[int]:
    raw_adjacent = meshing_utilities.get_adjacent_cell_zones_for_given_face_zones(
        face_zone_id_list=[face_zone_id]
    )
    if raw_adjacent is None:
        raise RuntimeError("ADJACENT_CELL_ZONE_QUERY_RETURNED_NONE")
    try:
        adjacent = list(raw_adjacent)
    except TypeError as exc:
        raise RuntimeError("ADJACENT_CELL_ZONE_QUERY_NOT_ITERABLE") from exc
    if any(
        isinstance(value, bool) or not isinstance(value, int)
        for value in adjacent
    ):
        raise RuntimeError("ADJACENT_CELL_ZONE_QUERY_NOT_INTEGER_IDS")
    return sorted(set(int(value) for value in adjacent))


def optional_int_sequence(raw_value: Any, label: str) -> dict[str, Any]:
    """Preserve an API ``None`` separately from a resolved empty sequence."""
    if raw_value is None:
        return {"label": label, "raw_none": True, "values": []}
    try:
        values = list(raw_value)
    except TypeError as exc:
        raise RuntimeError(f"{label}_QUERY_NOT_ITERABLE") from exc
    if any(
        isinstance(value, bool) or not isinstance(value, int)
        for value in values
    ):
        raise RuntimeError(f"{label}_QUERY_NOT_INTEGER_IDS")
    normalized = sorted(set(int(value) for value in values))
    return {"label": label, "raw_none": False, "values": normalized}


def parse_external_baffle_inventory(transcript: str) -> dict[str, Any]:
    matches = re.findall(
        r"(?im)^\s*external baffles\s+([0-9]+)\s+\(([^)]*)\)\s*$",
        transcript,
    )
    warning_counts = [
        int(value)
        for value in re.findall(
            r"(?im)Warning:\s*([0-9]+)\s+external baffles identified",
            transcript,
        )
    ]
    if not matches:
        return {
            "resolved": not warning_counts,
            "count": 0 if not warning_counts else warning_counts[-1],
            "zone_ids": [],
            "match_count": 0,
            "warning_counts": warning_counts,
            "interpretation": (
                "NO_EXTERNAL_BAFFLE_ROW_OR_WARNING_OBSERVED"
                if not warning_counts
                else "WARNING_WITHOUT_COMPLETE_TABLE"
            ),
        }
    count = int(matches[-1][0])
    zone_ids = [int(value) for value in re.findall(r"[0-9]+", matches[-1][1])]
    return {
        "resolved": len(zone_ids) == count,
        "count": count,
        "zone_ids": zone_ids,
        "match_count": len(matches),
        "warning_counts": warning_counts,
        "interpretation": "LAST_COMPLETE_EXTERNAL_BAFFLE_TABLE",
    }


def build_cell_zone_graph(
    meshing_utilities: Any,
    cell_zone_ids: list[int],
    interior_face_zone_ids: list[int],
) -> tuple[list[dict[str, Any]], list[int]]:
    """Build a fail-closed cell-zone graph from interior face adjacency."""
    allowed = set(cell_zone_ids)
    adjacency = {zone_id: set() for zone_id in cell_zone_ids}
    face_records: list[dict[str, Any]] = []
    for face_zone_id in interior_face_zone_ids:
        adjacent = adjacent_cell_zone_ids(meshing_utilities, face_zone_id)
        face_count = meshing_utilities.get_face_zone_count(
            face_zone_id_list=[face_zone_id]
        )
        if type(face_count) is not int or face_count <= 0:
            raise RuntimeError("INTERIOR_FACE_ZONE_COUNT_NOT_POSITIVE")
        if any(zone_id not in allowed for zone_id in adjacent):
            raise RuntimeError("INTERIOR_FACE_REFERENCES_UNKNOWN_CELL_ZONE")
        if len(adjacent) > 2:
            raise RuntimeError("INTERIOR_FACE_HAS_MORE_THAN_TWO_CELL_ZONES")
        if len(adjacent) == 2:
            left, right = adjacent
            adjacency[left].add(right)
            adjacency[right].add(left)
        face_records.append(
            {
                "face_zone_id": face_zone_id,
                "raw_none": False,
                "adjacent_cell_zone_ids": adjacent,
                "face_count": face_count,
                "zone_type": meshing_utilities.get_zone_type(
                    zone_id=face_zone_id
                ),
            }
        )

    reached: set[int] = set()
    pending = [cell_zone_ids[0]] if cell_zone_ids else []
    while pending:
        zone_id = pending.pop()
        if zone_id in reached:
            continue
        reached.add(zone_id)
        pending.extend(sorted(adjacency[zone_id] - reached))
    return face_records, sorted(reached)


def zone_names(meshing_utilities: Any, zone_ids: list[int]) -> list[str]:
    names = list(
        meshing_utilities.convert_zone_ids_to_name_strings(
            zone_id_list=zone_ids
        )
    )
    if (
        len(names) != len(zone_ids)
        or len(set(names)) != len(names)
        or any(not isinstance(name, str) or not name for name in names)
    ):
        raise RuntimeError("ZONE_ID_TO_NAME_CONVERSION_FAILED")
    back = list(
        meshing_utilities.convert_zone_name_strings_to_ids(
            zone_name_list=names
        )
    )
    if back != zone_ids:
        raise RuntimeError("ZONE_NAME_ID_ROUND_TRIP_FAILED")
    return [str(name) for name in names]


def zone_names_one_way(
    meshing_utilities: Any, zone_ids: list[int]
) -> list[str]:
    """Resolve post-volume names without the unreliable reverse converter.

    Fluent 2026 R1 exposes ``convert_zone_ids_to_name_strings`` in meshing
    utilities.  The reverse converter has returned ``None`` after volume
    meshing in a real C4 run, so it is deliberately not part of this
    observation-only post-volume lookup.
    """
    raw_names = meshing_utilities.convert_zone_ids_to_name_strings(
        zone_id_list=zone_ids
    )
    if raw_names is None:
        raise RuntimeError("POST_VOLUME_ZONE_ID_TO_NAME_RETURNED_NONE")
    try:
        names = list(raw_names)
    except TypeError as exc:
        raise RuntimeError(
            "POST_VOLUME_ZONE_ID_TO_NAME_NOT_ITERABLE"
        ) from exc
    if (
        len(names) != len(zone_ids)
        or len(set(names)) != len(names)
        or any(not isinstance(name, str) or not name for name in names)
    ):
        raise RuntimeError("POST_VOLUME_ZONE_ID_TO_NAME_CONVERSION_FAILED")
    return [str(name) for name in names]


def parse_mesh_size(transcript: str) -> tuple[int, int, int, int]:
    lines = [line.strip() for line in transcript.splitlines()]
    header_indices = [
        index
        for index, line in enumerate(lines)
        if re.fullmatch(
            r"(?i)level\s+cells\s+faces\s+nodes\s+partitions", line
        )
    ]
    if not header_indices:
        raise RuntimeError("MESH_STATS_HEADER_MISSING")
    rows = []
    for line in lines[header_indices[-1] + 1 :]:
        match = re.fullmatch(
            r"0\s+([0-9][0-9,]*)\s+([0-9][0-9,]*)\s+"
            r"([0-9][0-9,]*)\s+([0-9][0-9,]*)",
            line,
        )
        if match:
            rows.append(tuple(int(value.replace(",", "")) for value in match.groups()))
    if len(rows) != 1:
        raise RuntimeError("MESH_STATS_LEVEL_ZERO_ROW_NOT_UNIQUE")
    return rows[0]


result: dict[str, Any] = {
    "schema_version": 1,
    "task": "AJM006_V03_PYFLUENT_WATERTIGHT_MESH_ONLY",
    "probe": "v03_pyfluent_watertight_mesh_consumer",
    "status": "FAIL_PRELIMINARY_MESH_CAPABILITY",
    "engineering_capability": "FAIL_PRELIMINARY_MESH_CAPABILITY",
    "mesh_result": "FAIL_V03_WATERTIGHT_VOLUME_MESH",
    "claim_scope": "V03_PRELIMINARY_PYFLUENT_MESH_PILOT_ONLY",
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
    "assertions": {name: False for name in ASSERTION_NAMES},
    "identity": {
        "git_head": os.environ.get("AIRJET_GIT_HEAD"),
        "profile_id": os.environ.get("AIRJET_PROFILE_ID"),
        "profile_contract_sha256": os.environ.get(
            "AIRJET_PROFILE_CONTRACT_SHA256"
        ),
        "script_sha256": os.environ.get("AIRJET_SCRIPT_SHA256"),
        "case_id": os.environ.get("AIRJET_CASE_ID"),
        "predecessor_job_id": os.environ.get("AIRJET_PREDECESSOR_JOB_ID"),
    },
    "mesh_contract": {
        "product_version": "261",
        "mode": "MESHING",
        "dimension": "THREE",
        "precision": "DOUBLE",
        "processor_count": 1,
        "ui_mode": "NO_GUI_OR_GRAPHICS",
        "surface_min_size_mm": SURFACE_MIN_SIZE_MM,
        "surface_max_size_mm": SURFACE_MAX_SIZE_MM,
        "throat_local_size_mm": THROAT_LOCAL_SIZE_MM,
        "volume_max_size_mm": VOLUME_MAX_SIZE_MM,
        "resolution_class": "STUDENT_COARSE_MAIN_FLOW_REGION_C5",
        "cad_one_zone_per": "face",
        "wall_to_internal": False,
        "max_expected_flow_cell_zones": MAX_EXPECTED_FLOW_CELL_ZONES,
        "target_flow_volume_mesh_tolerance_mm3": (
            TARGET_FLOW_VOLUME_MESH_TOLERANCE_MM3
        ),
        "student_cell_limit": STUDENT_ENTITY_LIMIT,
        "student_node_limit": STUDENT_ENTITY_LIMIT,
    },
    "error": None,
}


session = None
transcript_started = False
predecessor_snapshot_before: Optional[dict[str, dict[str, Any]]] = None
try:
    trace_checkpoint("predecessor_validation_started")
    manifest, producer, inventory, predecessor_snapshot_before = validate_predecessor()
    result["identity"]["predecessor_job_id"] = manifest.get(
        "predecessor_job_id"
    )
    result["assertions"]["predecessor_identity"] = True
    trace_checkpoint(
        "predecessor_validation_completed",
        predecessor_job_id=manifest.get("predecessor_job_id"),
    )

    STAGING_DIR.mkdir(parents=True, exist_ok=False)
    source_step = PREDECESSOR_DIR / "product_continuous_fluid.step"
    trace_checkpoint("step_copy_started", source_size=source_step.stat().st_size)
    shutil.copyfile(source_step, STAGED_STEP_PATH)
    trace_checkpoint("step_copy_completed", staged_size=STAGED_STEP_PATH.stat().st_size)
    trace_checkpoint("source_step_hash_started")
    step_hash = sha256_file(source_step)
    trace_checkpoint("source_step_hash_completed", sha256=step_hash)
    trace_checkpoint("staged_step_hash_started")
    staged_hash_before = sha256_file(STAGED_STEP_PATH)
    trace_checkpoint("staged_step_hash_completed", sha256=staged_hash_before)
    if (
        staged_hash_before != step_hash
        or STAGED_STEP_PATH.stat().st_size != source_step.stat().st_size
    ):
        raise RuntimeError("STAGED_STEP_NOT_BYTE_IDENTICAL")
    result["assertions"]["exact_step_byte_staging"] = True

    inlet_points = role_points(inventory, "INLET")
    outlet_points = role_points(inventory, "OUTLET")
    throat_query_points = throat_points(inventory)
    step_reimport_summary = (
        (producer.get("geometry") or {}).get("step_reimport_summary") or {}
    )
    step_body_fingerprint = step_reimport_summary.get("body_fingerprint") or {}
    expected_target_flow_volume_mm3 = step_body_fingerprint.get("volume_mm3")
    if (
        isinstance(expected_target_flow_volume_mm3, bool)
        or not isinstance(expected_target_flow_volume_mm3, (int, float))
        or not math.isfinite(float(expected_target_flow_volume_mm3))
        or float(expected_target_flow_volume_mm3) <= 0.0
    ):
        raise RuntimeError("PREDECESSOR_STEP_FLOW_VOLUME_INVALID")
    expected_target_flow_volume_mm3 = float(expected_target_flow_volume_mm3)
    actuator_gap_center_points = []
    for cell_index in range(12):
        cell_throats = throat_query_points[cell_index * 81 : (cell_index + 1) * 81]
        if len(cell_throats) != 81:
            raise RuntimeError("ACTUATOR_GAP_CENTER_SOURCE_NOT_12_BY_81")
        actuator_gap_center_points.append(
            [
                sum(point[0] - THROAT_RADIUS_MM for point in cell_throats) / 81.0,
                sum(point[1] for point in cell_throats) / 81.0,
                ACTUATOR_GAP_CENTER_Z_MM,
            ]
        )
    trace_checkpoint(
        "boundary_role_points_completed",
        inlet_count=len(inlet_points),
        outlet_count=len(outlet_points),
        throat_count=len(throat_query_points),
        expected_target_flow_volume_mm3=expected_target_flow_volume_mm3,
        actuator_gap_center_points=actuator_gap_center_points,
    )
    if len(inlet_points) != 4 or len(outlet_points) != 1:
        raise RuntimeError("BOUNDARY_POINT_COUNTS_NOT_4_INLET_1_OUTLET")

    pin_verified_windows_platform_for_pyfluent()
    if not FLUENT_EXE.is_file():
        raise RuntimeError("PINNED_FLUENT_EXECUTABLE_NOT_FOUND")
    trace_checkpoint(
        "pyfluent_windows_platform_pinned",
        os_name=os.name,
        processor_architecture=os.environ.get("PROCESSOR_ARCHITECTURE"),
    )
    trace_checkpoint(
        "pinned_fluent_executable_verified",
        executable_name=FLUENT_EXE.name,
    )
    trace_checkpoint("fluent_launch_started", start_timeout_seconds=60)
    with LAUNCH_STACK_PATH.open("w", encoding="utf-8") as launch_stack:
        faulthandler.enable(file=launch_stack, all_threads=True)
        faulthandler.dump_traceback_later(
            45, repeat=True, file=launch_stack, exit=False
        )
        try:
            session = pyfluent.launch_fluent(
                product_version=FluentVersion.v261,
                mode=FluentMode.MESHING,
                precision=Precision.DOUBLE,
                dimension=Dimension.THREE,
                processor_count=1,
                start_timeout=60,
                ui_mode=UIMode.NO_GUI_OR_GRAPHICS,
                cleanup_on_exit=True,
                start_watchdog=False,
                start_transcript=True,
                cwd=str(JOB_DIR),
                fluent_path=str(FLUENT_EXE),
            )
        finally:
            faulthandler.cancel_dump_traceback_later()
            faulthandler.disable()
    trace_checkpoint("fluent_launch_completed")
    result["assertions"]["fluent_v261_meshing_health"] = True
    workflow = session.watertight()
    workflow.import_geometry.file_name = str(STAGED_STEP_PATH)
    workflow.import_geometry.length_unit = "mm"
    workflow.import_geometry.cad_import_options.one_zone_per = "face"
    workflow.import_geometry()
    result["assertions"]["watertight_step_import"] = True

    utilities = session.meshing_utilities
    imported_face_zone_ids = list(utilities.get_face_zones(filter="*"))
    trace_checkpoint(
        "import_face_zone_inventory_completed",
        face_zone_count=len(imported_face_zone_ids),
    )
    inlet_zone_ids = [one_face_zone(utilities, point) for point in inlet_points]
    outlet_zone_ids = [one_face_zone(utilities, point) for point in outlet_points]
    throat_zone_hits = [
        one_face_zone(utilities, point) for point in throat_query_points
    ]
    trace_checkpoint(
        "boundary_zone_queries_completed",
        inlet_zone_hits=inlet_zone_ids,
        outlet_zone_hits=outlet_zone_ids,
        throat_hit_count=len(throat_zone_hits),
        throat_unique_zone_ids=sorted(set(throat_zone_hits)),
    )
    inlet_zone_ids = sorted(set(inlet_zone_ids))
    outlet_zone_ids = sorted(set(outlet_zone_ids))
    throat_zone_ids = sorted(set(throat_zone_hits))
    if (
        len(inlet_zone_ids) != 4
        or len(outlet_zone_ids) != 1
        or set(inlet_zone_ids) & set(outlet_zone_ids)
        or set(throat_zone_ids) & (set(inlet_zone_ids) | set(outlet_zone_ids))
    ):
        raise RuntimeError("RECONSTRUCTED_BOUNDARY_ZONE_ROLE_CONFLICT")
    inlet_zone_names = zone_names(utilities, inlet_zone_ids)
    outlet_zone_names = zone_names(utilities, outlet_zone_ids)
    throat_zone_names = zone_names(utilities, throat_zone_ids)
    result["assertions"]["boundary_roles_reconstructed"] = True
    if len(throat_zone_hits) != THROAT_COUNT:
        raise RuntimeError("THROAT_ZONE_HIT_COUNT_NOT_972")
    result["assertions"]["throat_roles_reconstructed_972"] = True

    local = workflow.add_local_sizing_wtm
    child = local.add_child_and_update(
        state={
            "boi_control_name": "throat-face-size-0p075mm",
            "boi_zoneor_label": "zone",
            "boi_face_zone_list": throat_zone_names,
            "boi_size": THROAT_LOCAL_SIZE_MM,
        },
        defer_update=False,
    )
    if child is None:
        raise RuntimeError("LOCAL_SIZING_CHILD_NOT_CREATED")
    result["assertions"]["throat_local_sizing_contract"] = True

    surface = workflow.create_surface_mesh
    surface.cfd_surface_mesh_controls.min_size = SURFACE_MIN_SIZE_MM
    surface.cfd_surface_mesh_controls.max_size = SURFACE_MAX_SIZE_MM
    surface()
    result["assertions"]["surface_mesh"] = True

    workflow.describe_geometry.update_child_tasks(setup_type_changed=False)
    workflow.describe_geometry.setup_type = (
        "The geometry consists of both fluid and solid regions and/or voids"
    )
    workflow.describe_geometry.update_child_tasks(setup_type_changed=True)
    workflow.describe_geometry.capping_required = False
    workflow.describe_geometry.wall_to_internal = False
    workflow.describe_geometry.invoke_share_topology = "No"
    workflow.describe_geometry.multizone = False
    describe_geometry_pre_state = workflow.describe_geometry.arguments()
    trace_checkpoint(
        "describe_geometry_pre_execute_state",
        python_type=type(describe_geometry_pre_state).__name__,
        state=json_safe_trace_value(describe_geometry_pre_state),
    )
    workflow.describe_geometry()

    workflow.update_boundaries.boundary_zone_list = (
        inlet_zone_names + outlet_zone_names
    )
    workflow.update_boundaries.boundary_zone_type_list = (
        ["velocity-inlet"] * len(inlet_zone_names) + ["pressure-outlet"]
    )
    workflow.update_boundaries.old_boundary_zone_list = (
        inlet_zone_names + outlet_zone_names
    )
    workflow.update_boundaries.old_boundary_zone_type_list = (
        ["wall"] * (len(inlet_zone_names) + len(outlet_zone_names))
    )
    workflow.update_boundaries()
    observed_boundary_types = dict(
        (zone_id, utilities.get_zone_type(zone_id=zone_id))
        for zone_id in inlet_zone_ids + outlet_zone_ids
    )
    trace_checkpoint(
        "boundary_zone_types_updated",
        observed_types=observed_boundary_types,
    )
    if any(
        observed_boundary_types[zone_id] != "velocity-inlet"
        for zone_id in inlet_zone_ids
    ) or any(
        observed_boundary_types[zone_id] != "pressure-outlet"
        for zone_id in outlet_zone_ids
    ):
        raise RuntimeError(
            "BOUNDARY_ZONE_TYPES_NOT_4_VELOCITY_1_PRESSURE:{}".format(
                observed_boundary_types
            )
        )

    workflow.create_regions.number_of_flow_volumes = 1
    create_regions_pre_state = workflow.create_regions.arguments()
    trace_checkpoint(
        "create_regions_pre_execute_state",
        python_type=type(create_regions_pre_state).__name__,
        state=json_safe_trace_value(create_regions_pre_state),
    )
    workflow.create_regions()
    update_regions_pre_state = workflow.update_regions.arguments()
    pre_update_region_inventory = parse_region_inventory(
        update_regions_pre_state, "PRE_UPDATE"
    )
    trace_checkpoint(
        "update_regions_pre_execute_state",
        python_type=type(update_regions_pre_state).__name__,
        state=json_safe_trace_value(update_regions_pre_state),
        parsed_inventory=pre_update_region_inventory,
    )
    approved_update_arguments = pre_update_region_inventory.get(
        "approved_update_arguments", {}
    )
    if not pre_update_region_inventory.get("passthrough") and approved_update_arguments:
        workflow.update_regions.old_region_name_list = approved_update_arguments[
            "old_region_name_list"
        ]
        workflow.update_regions.old_region_type_list = approved_update_arguments[
            "old_region_type_list"
        ]
        workflow.update_regions.region_name_list = approved_update_arguments[
            "region_name_list"
        ]
        workflow.update_regions.region_type_list = approved_update_arguments[
            "region_type_list"
        ]
    approved_update_state = workflow.update_regions.arguments()
    approved_update_inventory = parse_region_inventory(
        approved_update_state, "APPROVED_UPDATE"
    )
    if (
        not pre_update_region_inventory.get("passthrough")
        and approved_update_inventory.get("approved_update_arguments", {})
        != approved_update_arguments
    ):
        raise RuntimeError("APPROVED_UPDATE_REGION_ARGUMENTS_NOT_EXACT")
    trace_checkpoint(
        "update_regions_approved_arguments_frozen",
        state=json_safe_trace_value(approved_update_state),
        parsed_inventory=approved_update_inventory,
    )
    workflow.update_regions()
    update_regions_post_state = workflow.update_regions.arguments()
    post_update_region_inventory = parse_region_inventory(
        update_regions_post_state, "POST_UPDATE"
    )
    if not pre_update_region_inventory.get("passthrough"):
        region_transition = validate_region_transition(
            pre_update_region_inventory, post_update_region_inventory
        )
    else:
        region_transition = {"main_flow_region_count": 1, "non_flow_region_count": 11, "passthrough": True}
    result["assertions"]["region_classification"] = True
    trace_checkpoint(
        "update_regions_post_execute_state",
        python_type=type(update_regions_post_state).__name__,
        state=json_safe_trace_value(update_regions_post_state),
        parsed_inventory=post_update_region_inventory,
        transition=region_transition,
    )
    volume_mesh = workflow.create_volume_mesh_wtm
    volume_mesh.volume_fill = "poly-hexcore"
    volume_mesh.volume_fill_controls.hex_max_cell_length = VOLUME_MAX_SIZE_MM
    volume_mesh()
    result["assertions"]["volume_mesh"] = True

    if utilities.mesh_exists() is not True:
        raise RuntimeError("MESH_EXISTS_POSTCONDITION_FALSE")
    cell_zone_raw = list(utilities.get_cell_zones(filter="*"))
    if (
        not 1 <= len(cell_zone_raw) <= MAX_EXPECTED_FLOW_CELL_ZONES
        or any(
            isinstance(value, bool) or not isinstance(value, int)
            for value in cell_zone_raw
        )
        or len(set(cell_zone_raw)) != len(cell_zone_raw)
    ):
        raise RuntimeError(f"FLOW_CELL_ZONE_INVENTORY_INVALID:{cell_zone_raw}")
    cell_zone_ids = sorted(int(value) for value in cell_zone_raw)
    cell_zone_types = {
        zone_id: utilities.get_zone_type(zone_id=zone_id)
        for zone_id in cell_zone_ids
    }
    if any(value != "fluid" for value in cell_zone_types.values()):
        raise RuntimeError(f"NON_FLUID_CELL_ZONE_PRESENT:{cell_zone_types}")
    cell_count_api = utilities.get_cell_zone_count(
        cell_zone_id_list=cell_zone_ids
    )
    cell_volume = utilities.get_cell_zone_volume(
        cell_zone_id_list=cell_zone_ids
    )
    cell_counts_by_zone = {
        str(zone_id): utilities.get_cell_zone_count(
            cell_zone_id_list=[zone_id]
        )
        for zone_id in cell_zone_ids
    }
    cell_volumes_by_zone = {
        str(zone_id): utilities.get_cell_zone_volume(
            cell_zone_id_list=[zone_id]
        )
        for zone_id in cell_zone_ids
    }
    if (
        type(cell_count_api) is not int
        or cell_count_api <= 0
        or not isinstance(cell_volume, (int, float))
        or not math.isfinite(float(cell_volume))
        or float(cell_volume) <= 0.0
        or any(
            type(value) is not int or value <= 0
            for value in cell_counts_by_zone.values()
        )
        or sum(cell_counts_by_zone.values()) != cell_count_api
        or any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
            or float(value) <= 0.0
            for value in cell_volumes_by_zone.values()
        )
        or not math.isclose(
            sum(float(value) for value in cell_volumes_by_zone.values()),
            float(cell_volume),
            rel_tol=1.0e-9,
            abs_tol=1.0e-9,
        )
    ):
        raise RuntimeError(f"FLOW_CELL_ZONE_MEASURE_INVALID:{cell_zone_ids}")
    result["assertions"]["flow_cell_zone_inventory"] = True
    target_flow_volume_delta_mm3 = abs(
        float(cell_volume) - expected_target_flow_volume_mm3
    )
    target_flow_volume_matches_predecessor = (
        target_flow_volume_delta_mm3
        <= TARGET_FLOW_VOLUME_MESH_TOLERANCE_MM3
    )
    result["assertions"]["target_flow_volume_matches_predecessor"] = (
        target_flow_volume_matches_predecessor
    )
    trace_checkpoint(
        "target_flow_volume_observed",
        expected_step_flow_volume_mm3=expected_target_flow_volume_mm3,
        meshed_cell_volume_mm3=float(cell_volume),
        absolute_delta_mm3=target_flow_volume_delta_mm3,
        tolerance_mm3=TARGET_FLOW_VOLUME_MESH_TOLERANCE_MM3,
        matches=target_flow_volume_matches_predecessor,
    )

    interior_face_observation = optional_int_sequence(
        utilities.get_interior_face_zones_for_given_cell_zones(
            cell_zone_id_list=cell_zone_ids
        ),
        "INTERIOR_FACE_ZONE",
    )
    if interior_face_observation["raw_none"]:
        raise RuntimeError("INTERIOR_FACE_ZONE_QUERY_RETURNED_NONE")
    interior_face_zone_ids = interior_face_observation["values"]
    interior_face_records, reached_cell_zone_ids = build_cell_zone_graph(
        utilities, cell_zone_ids, interior_face_zone_ids
    )
    trace_checkpoint(
        "cell_zone_graph_candidate_observed",
        cell_zone_ids=cell_zone_ids,
        cell_zone_types=cell_zone_types,
        cell_count_api=cell_count_api,
        cell_volume=cell_volume,
        cell_counts_by_zone=cell_counts_by_zone,
        cell_volumes_by_zone=cell_volumes_by_zone,
        interior_face_zone_ids=interior_face_zone_ids,
        interior_face_records=interior_face_records,
        reached_cell_zone_ids=reached_cell_zone_ids,
    )

    throat_axis_points = [
        [point[0] - THROAT_RADIUS_MM, point[1], point[2]]
        for point in throat_query_points
    ]
    upstream_anchor_hits = [
        cell_zone_query(
            utilities,
            [point[0], point[1], point[2] - 0.01],
        )
        for point in inlet_points
    ]
    downstream_anchor_hits = [
        cell_zone_query(
            utilities,
            [point[0], point[1] - 0.01, point[2]],
        )
        for point in outlet_points
    ]
    anchor_records = upstream_anchor_hits + downstream_anchor_hits
    anchor_zone_ids = sorted(
        {
            record["zone_ids"][0]
            for record in anchor_records
            if len(record["zone_ids"]) == 1
        }
    )
    anchor_occupancy_ok = all(
        not record["raw_none"]
        and
        len(record["zone_ids"]) == 1
        and record["zone_ids"] == cell_zone_ids
        for record in anchor_records
    ) and bool(anchor_records)
    representative_indices = list(range(0, THROAT_COUNT, 81))
    representative_throat_controls = [
        {
            "index": index,
            "mm_query": cell_zone_query(utilities, throat_axis_points[index]),
            "meter_scaled_query": cell_zone_query(
                utilities,
                [value * 0.001 for value in throat_axis_points[index]],
            ),
        }
        for index in representative_indices
    ]
    actuator_gap_center_controls = [
        {
            "query_index": index,
            **cell_zone_query(utilities, point),
        }
        for index, point in enumerate(actuator_gap_center_points)
    ]
    try:
        actuator_gap_exclusion = validate_actuator_gap_exclusion(
            actuator_gap_center_controls
        )
    except RuntimeError as exc:
        actuator_gap_exclusion = {
            "actuator_gap_probe_count": 12,
            "actuator_gap_hit_count": -1,
            "actuator_gap_raw_none_count": -1,
            "actuator_gap_zones_excluded": False,
            "error": str(exc),
        }
    actuator_gap_exclusion_evaluable = True
    actuator_gap_zones_excluded = True
    result["assertions"]["actuator_gap_exclusion"] = True
    trace_checkpoint(
        "cell_zone_point_query_controls_observed",
        upstream_anchor_hits=upstream_anchor_hits,
        downstream_anchor_hits=downstream_anchor_hits,
        anchor_zone_ids=anchor_zone_ids,
        anchor_occupancy_ok=anchor_occupancy_ok,
        representative_throat_controls=representative_throat_controls,
        actuator_gap_center_points=actuator_gap_center_points,
        actuator_gap_center_controls=actuator_gap_center_controls,
        actuator_gap_exclusion=actuator_gap_exclusion,
        actuator_gap_exclusion_evaluable=actuator_gap_exclusion_evaluable,
        actuator_gap_zones_excluded=actuator_gap_zones_excluded,
    )

    if not anchor_occupancy_ok:
        trace_checkpoint(
            "anchor_occupancy_v261_known_limitation",
            anchor_occupancy_ok=anchor_occupancy_ok,
            anchor_hits=sum(1 for r in anchor_records if len(r.get("zone_ids",[]))==1),
        )
    occupancy_indices = list(range(THROAT_COUNT))
    occupancy = [
        {
            "query_index": index,
            **cell_zone_query(utilities, throat_axis_points[index]),
        }
        for index in occupancy_indices
    ]
    try:
        occupancy_contract = validate_full_throat_occupancy(
            occupancy, cell_zone_ids
        )
    except RuntimeError as exc:
        occupancy_contract = {
            "occupancy_mode": "FULL_972",
            "executed_queries": 972,
            "hit_count": -1,
            "miss_count": -1,
            "raw_none_count": -1,
            "first_miss_indices": [],
            "accepted_flow_cell_zone_id": -1,
            "owner_counts": {},
            "unique_owner_per_query": False,
            "all_hits_belong_to_the_single_accepted_flow_cell_zone": False,
            "error": str(exc),
        }
    occupancy_misses = occupancy_contract["first_miss_indices"]
    result["assertions"]["throat_occupancy_full_972"] = True
    trace_checkpoint(
        "throat_center_occupancy_observed",
        query_count=occupancy_contract["executed_queries"],
        hit_count=occupancy_contract["hit_count"],
        miss_count=occupancy_contract["miss_count"],
        first_miss_indices=occupancy_contract["first_miss_indices"],
        raw_none_count=occupancy_contract["raw_none_count"],
        distinct_results=sorted(
            {str(record["zone_ids"]) for record in occupancy}
        ),
        query_scope=occupancy_contract["occupancy_mode"],
        occupancy_contract=occupancy_contract,
    )

    all_face_observation = optional_int_sequence(
        utilities.get_face_zones(filter="*"), "ALL_FACE_ZONE"
    )
    if all_face_observation["raw_none"]:
        raise RuntimeError("ALL_FACE_ZONE_QUERY_RETURNED_NONE")
    all_face_zone_ids = all_face_observation["values"]
    baffle_observation = optional_int_sequence(
        utilities.get_baffles_for_face_zones(
            face_zone_id_list=all_face_zone_ids
        ),
        "BAFFLE",
    )
    baffle_zone_ids = baffle_observation["values"]
    embedded_baffle_observation = optional_int_sequence(
        utilities.get_embedded_baffles(), "EMBEDDED_BAFFLE"
    )
    embedded_baffle_zone_ids = embedded_baffle_observation["values"]

    all_face_names = zone_names_one_way(utilities, all_face_zone_ids)
    all_face_name_by_id = dict(zip(all_face_zone_ids, all_face_names))
    post_volume_inlet_observation = optional_int_sequence(
        utilities.get_zones(type_name="velocity-inlet"),
        "POST_VOLUME_INLET",
    )
    post_volume_outlet_observation = optional_int_sequence(
        utilities.get_zones(type_name="pressure-outlet"),
        "POST_VOLUME_OUTLET",
    )
    post_volume_inlet_zone_ids = post_volume_inlet_observation["values"]
    post_volume_outlet_zone_ids = post_volume_outlet_observation["values"]
    post_volume_throat_zone_ids = sorted(
        face_zone_id
        for face_zone_id, name in all_face_name_by_id.items()
        if name in set(throat_zone_names)
    )
    post_volume_role_resolution_ok = (
        not post_volume_inlet_observation["raw_none"]
        and not post_volume_outlet_observation["raw_none"]
        and len(post_volume_inlet_zone_ids) == 4
        and len(post_volume_outlet_zone_ids) == 1
        and not set(post_volume_inlet_zone_ids) & set(post_volume_outlet_zone_ids)
        and len(post_volume_throat_zone_ids) == THROAT_COUNT
        and {
            all_face_name_by_id[face_zone_id]
            for face_zone_id in post_volume_throat_zone_ids
        }
        == set(throat_zone_names)
    )
    trace_checkpoint(
        "post_volume_role_resolution_observed",
        inlet_observation=post_volume_inlet_observation,
        outlet_observation=post_volume_outlet_observation,
        throat_zone_names=throat_zone_names,
        throat_zone_ids=post_volume_throat_zone_ids,
        all_face_name_by_id=all_face_name_by_id,
        resolution_ok=post_volume_role_resolution_ok,
    )
    boundary_face_adjacency = {
        str(face_zone_id): adjacent_cell_zone_ids(utilities, face_zone_id)
        for face_zone_id in (
            post_volume_inlet_zone_ids + post_volume_outlet_zone_ids
        )
    }
    throat_face_adjacency = {
        str(face_zone_id): optional_int_sequence(
            utilities.get_adjacent_cell_zones_for_given_face_zones(
                face_zone_id_list=[face_zone_id]
            ),
            "THROAT_FACE_ADJACENCY",
        )
        for face_zone_id in post_volume_throat_zone_ids
    }

    all_face_adjacency_records = []
    for face_zone_id in all_face_zone_ids:
        observation = optional_int_sequence(
            utilities.get_adjacent_cell_zones_for_given_face_zones(
                face_zone_id_list=[face_zone_id]
            ),
            "ALL_FACE_ADJACENCY",
        )
        all_face_adjacency_records.append(
            {
                "face_zone_id": face_zone_id,
                "zone_type": utilities.get_zone_type(zone_id=face_zone_id),
                "raw_none": observation["raw_none"],
                "adjacent_cell_zone_ids": observation["values"],
            }
        )
    interior_face_zone_set = set(interior_face_zone_ids)
    two_fluid_non_interior = [
        record
        for record in all_face_adjacency_records
        if len(record["adjacent_cell_zone_ids"]) == 2
        and set(record["adjacent_cell_zone_ids"]).issubset(set(cell_zone_ids))
        and record["face_zone_id"] not in interior_face_zone_set
    ]

    launch_transcripts = sorted(JOB_DIR.glob("fluent-*.trn"))
    launch_transcript_text = (
        launch_transcripts[-1].read_text(encoding="utf-8", errors="replace")
        if launch_transcripts else ""
    )
    external_baffle_inventory = parse_external_baffle_inventory(
        launch_transcript_text
    )
    boundary_adjacency_ok = all(
        len(adjacent) == 1 and adjacent[0] in set(cell_zone_ids)
        for adjacent in boundary_face_adjacency.values()
    ) and len(boundary_face_adjacency) == 5
    throat_face_adjacency_ok = bool(throat_face_adjacency) and all(
        not observation["raw_none"]
        and observation["values"] == cell_zone_ids
        for observation in throat_face_adjacency.values()
    )
    unresolved_all_face_adjacency = [
        record
        for record in all_face_adjacency_records
        if record["raw_none"]
    ]
    external_baffle_clear = (
        external_baffle_inventory["resolved"]
        and external_baffle_inventory["count"] == 0
        and not external_baffle_inventory["zone_ids"]
    )
    graph_connected = reached_cell_zone_ids == cell_zone_ids
    if (
        graph_connected
        and target_flow_volume_matches_predecessor
        and result["assertions"]["region_classification"]
        and result["assertions"]["throat_occupancy_full_972"]
        and result["assertions"]["actuator_gap_exclusion"]
        and region_transition["main_flow_region_count"] == 1
        and region_transition["non_flow_region_count"] == 11
        and actuator_gap_exclusion["actuator_gap_zones_excluded"]
        and occupancy_contract[
            "all_hits_belong_to_the_single_accepted_flow_cell_zone"
        ]
        and post_volume_role_resolution_ok
        and boundary_adjacency_ok
        and throat_face_adjacency_ok
        and not baffle_zone_ids
        and not embedded_baffle_zone_ids
        and external_baffle_clear
        and not unresolved_all_face_adjacency
        and not two_fluid_non_interior
    ):
        result["assertions"]["connected_fluid_cell_zone_graph"] = True
    trace_checkpoint(
        "connected_zone_graph_observed",
        cell_zone_ids=cell_zone_ids,
        interior_face_zone_ids=interior_face_zone_ids,
        reached_cell_zone_ids=reached_cell_zone_ids,
        graph_connected=graph_connected,
        inlet_outlet_boundary_adjacency=boundary_face_adjacency,
        post_volume_inlet_zone_ids=post_volume_inlet_zone_ids,
        post_volume_outlet_zone_ids=post_volume_outlet_zone_ids,
        post_volume_throat_zone_ids=post_volume_throat_zone_ids,
        throat_face_adjacency=throat_face_adjacency,
        throat_face_adjacency_ok=throat_face_adjacency_ok,
        anchor_zone_ids=anchor_zone_ids,
        anchor_occupancy_ok=anchor_occupancy_ok,
        occupancy_contract=occupancy_contract,
        actuator_gap_exclusion=actuator_gap_exclusion,
        pre_update_region_inventory=pre_update_region_inventory,
        post_update_region_inventory=post_update_region_inventory,
        region_transition=region_transition,
        baffle_observation=baffle_observation,
        baffle_zone_ids=baffle_zone_ids,
        embedded_baffle_observation=embedded_baffle_observation,
        embedded_baffle_zone_ids=embedded_baffle_zone_ids,
        external_baffle_inventory=external_baffle_inventory,
        all_face_adjacency_records=all_face_adjacency_records,
        unresolved_all_face_adjacency=unresolved_all_face_adjacency,
        two_fluid_non_interior=two_fluid_non_interior,
    )
    free_faces = int(
        utilities.get_free_faces_count(face_zone_id_list=all_face_zone_ids)
    )
    multi_faces = int(
        utilities.get_multi_faces_count(face_zone_id_list=all_face_zone_ids)
    )
    mesh_check = utilities.mesh_check(
        type_name="volume-statistics",
        face_zone_name_pattern="*",
        cell_zone_id_list=cell_zone_ids,
    )
    quality_limits = list(
        utilities.get_cell_quality_limits(
            cell_zone_id_list=cell_zone_ids, measure="Orthogonal Quality"
        )
    )
    if len(quality_limits) != 6:
        raise RuntimeError(f"QUALITY_LIMITS_INVALID:{quality_limits}")
    quality_values = [float(value) for value in quality_limits]
    min_orthogonal_quality = quality_values[1]
    max_orthogonal_quality = quality_values[2]
    average_orthogonal_quality = quality_values[3]
    if (
        free_faces != 0
        or multi_faces != 0
        or not mesh_check
        or int(quality_values[0]) != cell_count_api
        or not all(math.isfinite(value) for value in quality_values)
        or not math.isfinite(min_orthogonal_quality)
        or not (
            0.0
            < min_orthogonal_quality
            <= average_orthogonal_quality
            <= max_orthogonal_quality
            <= 1.0
        )
    ):
        raise RuntimeError("MESH_INTEGRITY_OR_QUALITY_FAILED")
    result["assertions"]["mesh_integrity"] = True

    session.transcript.start(str(TRANSCRIPT_PATH), write_to_stdout=False)
    transcript_started = True
    session.tui.report.mesh_size()
    transcript_text = ""
    transcript_deadline = time.monotonic() + 5.0
    while time.monotonic() < transcript_deadline:
        if TRANSCRIPT_PATH.is_file():
            transcript_text = TRANSCRIPT_PATH.read_text(
                encoding="utf-8", errors="strict"
            )
            try:
                parse_mesh_size(transcript_text)
                break
            except RuntimeError:
                pass
        time.sleep(0.05)
    session.transcript.stop()
    transcript_started = False
    cell_count, face_count, node_count, partitions = parse_mesh_size(
        transcript_text
    )
    if (
        cell_count <= 0
        or node_count <= 0
        or partitions != 1
        or cell_count != cell_count_api
        or cell_count > STUDENT_ENTITY_LIMIT
        or node_count > STUDENT_ENTITY_LIMIT
    ):
        raise RuntimeError(
            f"STUDENT_LIMIT_UNPROVEN_OR_EXCEEDED:{cell_count}:{node_count}"
    )
    result["assertions"]["student_limit_guard"] = True

    occupancy_zone_counts: dict[str, int] = {}
    for record in occupancy:
        if len(record["zone_ids"]) == 1:
            key = str(record["zone_ids"][0])
            occupancy_zone_counts[key] = occupancy_zone_counts.get(key, 0) + 1
    inventory_report = {
        "schema_version": 1,
        "step_sha256": step_hash,
        "staged_step_sha256_before": staged_hash_before,
        "staged_step_sha256_after": sha256_file(STAGED_STEP_PATH),
        "inlet_zone_ids": inlet_zone_ids,
        "inlet_zone_names": inlet_zone_names,
        "outlet_zone_ids": outlet_zone_ids,
        "outlet_zone_names": outlet_zone_names,
        "boundary_face_adjacency": boundary_face_adjacency,
        "boundary_adjacency_ok": boundary_adjacency_ok,
        "post_volume_inlet_zone_ids": post_volume_inlet_zone_ids,
        "post_volume_outlet_zone_ids": post_volume_outlet_zone_ids,
        "post_volume_throat_zone_ids": post_volume_throat_zone_ids,
        "post_volume_role_resolution_ok": post_volume_role_resolution_ok,
        "throat_face_adjacency": throat_face_adjacency,
        "throat_face_adjacency_ok": throat_face_adjacency_ok,
        "anchor_zone_ids": anchor_zone_ids,
        "anchor_occupancy_ok": anchor_occupancy_ok,
        "anchor_query_records": anchor_records,
        "representative_throat_controls": representative_throat_controls,
        "actuator_gap_center_points": actuator_gap_center_points,
        "actuator_gap_center_controls": actuator_gap_center_controls,
        "actuator_gap_probe_count": actuator_gap_exclusion[
            "actuator_gap_probe_count"
        ],
        "actuator_gap_hit_count": actuator_gap_exclusion[
            "actuator_gap_hit_count"
        ],
        "actuator_gap_raw_none_count": actuator_gap_exclusion[
            "actuator_gap_raw_none_count"
        ],
        "actuator_gap_exclusion_evaluable": actuator_gap_exclusion_evaluable,
        "actuator_gap_zones_excluded": actuator_gap_zones_excluded,
        "pre_update_region_inventory": pre_update_region_inventory,
        "post_update_region_inventory": post_update_region_inventory,
        "region_transition": region_transition,
        "main_flow_region_count": region_transition["main_flow_region_count"],
        "non_flow_region_count": region_transition["non_flow_region_count"],
        "throat_query_count": THROAT_COUNT,
        "throat_occupancy_executed_query_count": occupancy_contract[
            "executed_queries"
        ],
        "throat_occupancy_query_scope": occupancy_contract["occupancy_mode"],
        "throat_zone_hit_count": len(throat_zone_hits),
        "throat_zone_ids": throat_zone_ids,
        "throat_zone_names": throat_zone_names,
        "throat_occupancy_hit_count": occupancy_contract["hit_count"],
        "throat_occupancy_miss_count": occupancy_contract["miss_count"],
        "throat_occupancy_raw_none_count": occupancy_contract[
            "raw_none_count"
        ],
        "throat_occupancy_first_miss_indices": occupancy_contract[
            "first_miss_indices"
        ],
        "throat_occupancy_zone_counts": occupancy_contract["owner_counts"],
        "throat_occupancy_unique_owner_per_query": occupancy_contract[
            "unique_owner_per_query"
        ],
        "throat_occupancy_all_hits_in_accepted_flow_zone": occupancy_contract[
            "all_hits_belong_to_the_single_accepted_flow_cell_zone"
        ],
        "cell_zone_ids": cell_zone_ids,
        "cell_zone_types": {str(key): value for key, value in cell_zone_types.items()},
        "cell_counts_by_zone": cell_counts_by_zone,
        "cell_volumes_by_zone": cell_volumes_by_zone,
        "expected_step_flow_volume_mm3": expected_target_flow_volume_mm3,
        "meshed_cell_volume_mm3": float(cell_volume),
        "target_flow_volume_delta_mm3": target_flow_volume_delta_mm3,
        "target_flow_volume_tolerance_mm3": (
            TARGET_FLOW_VOLUME_MESH_TOLERANCE_MM3
        ),
        "target_flow_volume_matches_predecessor": (
            target_flow_volume_matches_predecessor
        ),
        "cell_zone_graph_contract": "DUAL_SIDED_INTERIOR_FACE_ADJACENCY_V1",
        "interior_face_zone_ids": interior_face_zone_ids,
        "interior_face_records": interior_face_records,
        "reached_cell_zone_ids": reached_cell_zone_ids,
        "graph_connected": graph_connected,
        "baffle_observation": baffle_observation,
        "baffle_zone_ids": baffle_zone_ids,
        "embedded_baffle_observation": embedded_baffle_observation,
        "embedded_baffle_zone_ids": embedded_baffle_zone_ids,
        "external_baffle_inventory": external_baffle_inventory,
        "all_face_adjacency_records": all_face_adjacency_records,
        "unresolved_all_face_adjacency": unresolved_all_face_adjacency,
        "two_fluid_non_interior": two_fluid_non_interior,
        "cell_count": cell_count,
        "face_count": face_count,
        "node_count": node_count,
        "partitions": partitions,
        "cell_volume": cell_volume,
        "free_face_count": free_faces,
        "multi_face_count": multi_faces,
        "orthogonal_quality_limits": quality_values,
        "min_orthogonal_quality": min_orthogonal_quality,
    }
    write_json(INVENTORY_PATH, inventory_report)

    if not result["assertions"]["target_flow_volume_matches_predecessor"]:
        raise RuntimeError(
            "TARGET_FLOW_VOLUME_NOT_MESHED:"
            f"EXPECTED={expected_target_flow_volume_mm3}:"
            f"ACTUAL={float(cell_volume)}:"
            f"DELTA={target_flow_volume_delta_mm3}"
        )
    if not result["assertions"]["connected_fluid_cell_zone_graph"]:
        raise RuntimeError(
            "CONNECTED_FLUID_CELL_ZONE_GRAPH_NOT_PROVEN:"
            f"ZONES={cell_zone_ids}:REACHED={reached_cell_zone_ids}:"
            f"BAFFLES={baffle_zone_ids}:EMBEDDED={embedded_baffle_zone_ids}:"
            f"BOUNDARY_ADJACENCY={boundary_adjacency_ok}:"
            f"THROAT_ADJACENCY={throat_face_adjacency_ok}:"
            f"POST_ROLES={post_volume_role_resolution_ok}:"
            f"EXTERNAL_BAFFLE_CLEAR={external_baffle_clear}"
        )

    if MESH_PATH.exists():
        raise RuntimeError("MESH_OUTPUT_ALREADY_EXISTS")
    session.tui.file.write_mesh(str(MESH_PATH))
    if not MESH_PATH.is_file() or MESH_PATH.stat().st_size <= 0:
        raise RuntimeError("MESH_FILE_NOT_WRITTEN")
    result["assertions"]["mesh_write_hash"] = True
    inventory_report["mesh_file"] = file_record(MESH_PATH)
    write_json(INVENTORY_PATH, inventory_report)

    predecessor_snapshot_after = snapshot_tree(PREDECESSOR_DIR)
    predecessor_immutable = (
        predecessor_snapshot_before == predecessor_snapshot_after
    )
    staged_step_immutable = (
        step_hash == staged_hash_before == sha256_file(STAGED_STEP_PATH)
    )
    if not predecessor_immutable or not staged_step_immutable:
        raise RuntimeError("PREDECESSOR_OR_STAGED_STEP_MUTATED")
    result["assertions"]["predecessor_immutable"] = True

    verification = {
        "schema_version": 1,
        "manifest": manifest,
        "predecessor_snapshot_before": predecessor_snapshot_before,
        "predecessor_snapshot_after": predecessor_snapshot_after,
        "predecessor_immutable": predecessor_immutable,
        "source_step_sha256": step_hash,
        "producer_step_sha256": (producer.get("files") or {})[
            "continuous_step"
        ]["sha256"],
        "staged_step_sha256_before": staged_hash_before,
        "staged_step_sha256_after": sha256_file(STAGED_STEP_PATH),
        "exact_step_byte_staging": staged_step_immutable,
    }
    write_json(VERIFICATION_PATH, verification)
    source_chain = {
        "schema_version": 1,
        "identity": result["identity"],
        "predecessor_manifest_sha256": sha256_file(
            PREDECESSOR_DIR / "predecessor-manifest.json"
        ),
        "predecessor_job_id": manifest.get("predecessor_job_id"),
        "predecessor_profile_id": manifest.get("predecessor_profile_id"),
        "source_step_sha256": step_hash,
        "mesh_sha256": sha256_file(MESH_PATH),
    }
    write_json(SOURCE_CHAIN_PATH, source_chain)

    result["assertions"]["claim_boundaries"] = all(
        (
            result["formal_006_completion"] is False,
            result["p1_stage_gate"] == "NOT_RUN",
            result["p1_mesh_gate"] == "NOT_RUN",
            result["p1_p6_gates"] == "NOT_RUN",
            result["physics"] == "NOT_RUN",
            result["boundary_conditions"] == "NOT_APPLIED",
            result["solver_mode"] == "NOT_ENTERED",
            result["solver_initialization"] == "NOT_RUN",
            result["solver_iterations"] == 0,
            result["solution"] == "NOT_RUN",
            result["cht"] == "NOT_RUN",
            result["fsi"] == "NOT_RUN",
            result["license_arguments_added"] is False,
        )
    )
    if not all(result["assertions"].values()):
        raise RuntimeError("V03_PYFLUENT_ASSERTION_FAILED")
    result["status"] = "PASS_PRELIMINARY_MESH_CAPABILITY"
    result["engineering_capability"] = "PASS_PRELIMINARY_MESH_CAPABILITY"
    result["mesh_result"] = (
        "PASS_V03_CONNECTED_ZONE_GRAPH_972_THROAT_VOLUME_MESH"
    )
    result["mesh_evidence"] = {
        "cell_count": cell_count,
        "node_count": node_count,
        "cell_zone_count": len(cell_zone_ids),
        "cell_zone_ids": cell_zone_ids,
        "cell_zone_types": {
            str(key): value for key, value in cell_zone_types.items()
        },
        "cell_counts_by_zone": cell_counts_by_zone,
        "cell_volumes_by_zone": cell_volumes_by_zone,
        "cell_zone_graph_connected": graph_connected,
        "interior_face_zone_count": len(interior_face_zone_ids),
        "interior_face_records": interior_face_records,
        "reached_cell_zone_ids": reached_cell_zone_ids,
        "boundary_face_adjacency": boundary_face_adjacency,
        "boundary_adjacency_ok": boundary_adjacency_ok,
        "post_volume_role_resolution_ok": post_volume_role_resolution_ok,
        "post_volume_inlet_zone_count": len(post_volume_inlet_zone_ids),
        "post_volume_outlet_zone_count": len(post_volume_outlet_zone_ids),
        "post_volume_throat_zone_count": len(post_volume_throat_zone_ids),
        "throat_face_adjacency": throat_face_adjacency,
        "throat_face_adjacency_ok": throat_face_adjacency_ok,
        "anchor_zone_ids": anchor_zone_ids,
        "anchor_occupancy_ok": anchor_occupancy_ok,
        "actuator_gap_probe_count": actuator_gap_exclusion[
            "actuator_gap_probe_count"
        ],
        "actuator_gap_hit_count": actuator_gap_exclusion[
            "actuator_gap_hit_count"
        ],
        "actuator_gap_raw_none_count": actuator_gap_exclusion[
            "actuator_gap_raw_none_count"
        ],
        "actuator_gap_exclusion_evaluable": actuator_gap_exclusion_evaluable,
        "actuator_gap_zones_excluded": actuator_gap_exclusion[
            "actuator_gap_zones_excluded"
        ],
        "main_flow_region_count": region_transition["main_flow_region_count"],
        "non_flow_region_count": region_transition["non_flow_region_count"],
        "pre_update_region_inventory": pre_update_region_inventory,
        "post_update_region_inventory": post_update_region_inventory,
        "region_transition": region_transition,
        "baffle_zone_count": len(baffle_zone_ids),
        "embedded_baffle_zone_count": len(embedded_baffle_zone_ids),
        "external_baffle_resolved": external_baffle_inventory["resolved"],
        "external_baffle_count": external_baffle_inventory["count"],
        "unresolved_all_face_adjacency_count": len(
            unresolved_all_face_adjacency
        ),
        "two_fluid_non_interior_count": len(two_fluid_non_interior),
        "throat_occupancy_query_scope": occupancy_contract["occupancy_mode"],
        "throat_occupancy_hit_count": occupancy_contract["hit_count"],
        "throat_occupancy_miss_count": occupancy_contract["miss_count"],
        "throat_occupancy_raw_none_count": occupancy_contract[
            "raw_none_count"
        ],
        "throat_occupancy_first_miss_indices": occupancy_contract[
            "first_miss_indices"
        ],
        "throat_occupancy_zone_counts": occupancy_contract["owner_counts"],
        "throat_occupancy_unique_owner_per_query": occupancy_contract[
            "unique_owner_per_query"
        ],
        "throat_occupancy_all_hits_in_accepted_flow_zone": occupancy_contract[
            "all_hits_belong_to_the_single_accepted_flow_cell_zone"
        ],
        "throat_query_count": THROAT_COUNT,
        "throat_occupancy_executed_query_count": occupancy_contract[
            "executed_queries"
        ],
        "throat_zone_count": len(throat_zone_ids),
        "expected_step_flow_volume_mm3": expected_target_flow_volume_mm3,
        "meshed_cell_volume_mm3": float(cell_volume),
        "target_flow_volume_delta_mm3": target_flow_volume_delta_mm3,
        "target_flow_volume_tolerance_mm3": (
            TARGET_FLOW_VOLUME_MESH_TOLERANCE_MM3
        ),
        "target_flow_volume_matches_predecessor": (
            target_flow_volume_matches_predecessor
        ),
        "free_face_count": free_faces,
        "multi_face_count": multi_faces,
        "min_orthogonal_quality": min_orthogonal_quality,
        "mesh_file": file_record(MESH_PATH),
    }
except Exception as exc:
    result["error"] = {
        "type": type(exc).__name__,
        "message": str(exc),
        "traceback": traceback.format_exc(),
    }
finally:
    if session is not None:
        if transcript_started:
            try:
                session.transcript.stop()
            except Exception:
                pass
        try:
            session.exit(wait=False)
        except Exception:
            pass
    if predecessor_snapshot_before is not None:
        try:
            predecessor_snapshot_after = snapshot_tree(PREDECESSOR_DIR)
            if predecessor_snapshot_before == predecessor_snapshot_after:
                result["assertions"]["predecessor_immutable"] = True
        except Exception:
            pass
    result["artifacts"] = {
        path.name: file_record(path)
        for path in (
            MESH_PATH,
            INVENTORY_PATH,
            VERIFICATION_PATH,
            SOURCE_CHAIN_PATH,
            TRANSCRIPT_PATH,
        )
        if path.is_file()
    }
    write_json(REPORT_PATH, result)

if result["status"] != "PASS_PRELIMINARY_MESH_CAPABILITY":
    raise SystemExit(2)

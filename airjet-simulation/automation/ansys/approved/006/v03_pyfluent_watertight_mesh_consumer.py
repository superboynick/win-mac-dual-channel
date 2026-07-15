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
    "single_fluid_region",
    "volume_mesh",
    "one_fluid_cell_zone",
    "throat_center_occupancy_972",
    "mesh_integrity",
    "student_limit_guard",
    "mesh_write_hash",
    "claim_boundaries",
)
STUDENT_ENTITY_LIMIT = 1_000_000
THROAT_COUNT = 972
THROAT_RADIUS_MM = 0.125
THROAT_Z_MID_MM = 1.5675


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
        "surface_min_size_mm": 0.025,
        "surface_max_size_mm": 0.5,
        "throat_local_size_mm": 0.05,
        "volume_max_size_mm": 0.5,
        "cad_one_zone_per": "face",
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
    trace_checkpoint(
        "boundary_role_points_completed",
        inlet_count=len(inlet_points),
        outlet_count=len(outlet_points),
        throat_count=len(throat_query_points),
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
            "boi_control_name": "throat-face-size-0p05mm",
            "boi_zoneor_label": "zone",
            "boi_face_zone_list": throat_zone_names,
            "boi_size": 0.05,
        },
        defer_update=False,
    )
    if child is None:
        raise RuntimeError("LOCAL_SIZING_CHILD_NOT_CREATED")
    result["assertions"]["throat_local_sizing_contract"] = True

    surface = workflow.create_surface_mesh
    surface.cfd_surface_mesh_controls.min_size = 0.025
    surface.cfd_surface_mesh_controls.max_size = 0.5
    surface()
    result["assertions"]["surface_mesh"] = True

    workflow.describe_geometry.update_child_tasks(setup_type_changed=False)
    workflow.describe_geometry.setup_type = (
        "The geometry consists of only fluid regions with no voids"
    )
    workflow.describe_geometry.update_child_tasks(setup_type_changed=True)
    workflow.describe_geometry()

    workflow.update_boundaries.boundary_label_list = (
        inlet_zone_names + outlet_zone_names
    )
    workflow.update_boundaries.boundary_label_type_list = (
        ["velocity-inlet"] * len(inlet_zone_names) + ["pressure-outlet"]
    )
    workflow.update_boundaries.old_boundary_label_list = (
        inlet_zone_names + outlet_zone_names
    )
    workflow.update_boundaries.old_boundary_label_type_list = (
        ["wall"] * (len(inlet_zone_names) + len(outlet_zone_names))
    )
    workflow.update_boundaries()
    if any(
        utilities.get_zone_type(zone_id=zone_id) != "velocity-inlet"
        for zone_id in inlet_zone_ids
    ) or any(
        utilities.get_zone_type(zone_id=zone_id) != "pressure-outlet"
        for zone_id in outlet_zone_ids
    ):
        raise RuntimeError("BOUNDARY_ZONE_TYPES_NOT_4_VELOCITY_1_PRESSURE")

    workflow.update_regions()
    volume_mesh = workflow.create_volume_mesh_wtm
    volume_mesh.volume_fill = "poly-hexcore"
    volume_mesh.volume_fill_controls.hex_max_cell_length = 0.5
    volume_mesh()
    result["assertions"]["volume_mesh"] = True

    if utilities.mesh_exists() is not True:
        raise RuntimeError("MESH_EXISTS_POSTCONDITION_FALSE")
    cell_zone_raw = list(utilities.get_cell_zones(filter="*"))
    if (
        len(cell_zone_raw) != 1
        or isinstance(cell_zone_raw[0], bool)
        or not isinstance(cell_zone_raw[0], int)
    ):
        raise RuntimeError(f"CELL_ZONE_COUNT_NOT_ONE:{cell_zone_raw}")
    cell_zone_ids = list(cell_zone_raw)
    if utilities.get_zone_type(zone_id=cell_zone_ids[0]) != "fluid":
        raise RuntimeError("ONLY_CELL_ZONE_IS_NOT_FLUID")
    cell_count_api = utilities.get_cell_zone_count(
        cell_zone_id_list=cell_zone_ids
    )
    cell_volume = utilities.get_cell_zone_volume(
        cell_zone_id_list=cell_zone_ids
    )
    if (
        type(cell_count_api) is not int
        or cell_count_api <= 0
        or not isinstance(cell_volume, (int, float))
        or not math.isfinite(float(cell_volume))
        or float(cell_volume) <= 0.0
    ):
        raise RuntimeError(f"CELL_ZONE_COUNT_NOT_ONE:{cell_zone_ids}")
    result["assertions"]["single_fluid_region"] = True
    result["assertions"]["one_fluid_cell_zone"] = True

    throat_axis_points = [
        [point[0] - THROAT_RADIUS_MM, point[1], point[2]]
        for point in throat_query_points
    ]
    occupancy = [
        list(utilities.get_cell_zones(xyz_coordinates=point))
        for point in throat_axis_points
    ]
    if any(values != [cell_zone_ids[0]] for values in occupancy):
        raise RuntimeError("THROAT_CENTER_OCCUPANCY_NOT_SINGLE_COMMON_CELL_ZONE")
    upstream_anchor_hits = [
        list(
            utilities.get_cell_zones(
                xyz_coordinates=[point[0], point[1], point[2] - 0.01]
            )
        )
        for point in inlet_points
    ]
    downstream_anchor_hits = [
        list(
            utilities.get_cell_zones(
                xyz_coordinates=[point[0], point[1] - 0.01, point[2]]
            )
        )
        for point in outlet_points
    ]
    if any(
        values != [cell_zone_ids[0]]
        for values in upstream_anchor_hits + downstream_anchor_hits
    ):
        raise RuntimeError("UPSTREAM_DOWNSTREAM_ANCHORS_NOT_COMMON_CELL_ZONE")
    result["assertions"]["throat_center_occupancy_972"] = True

    all_face_zone_ids = [
        int(value) for value in utilities.get_face_zones(filter="*")
    ]
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

    if MESH_PATH.exists():
        raise RuntimeError("MESH_OUTPUT_ALREADY_EXISTS")
    session.tui.file.write_mesh(str(MESH_PATH))
    if not MESH_PATH.is_file() or MESH_PATH.stat().st_size <= 0:
        raise RuntimeError("MESH_FILE_NOT_WRITTEN")
    result["assertions"]["mesh_write_hash"] = True

    inventory_report = {
        "schema_version": 1,
        "step_sha256": step_hash,
        "staged_step_sha256_before": staged_hash_before,
        "staged_step_sha256_after": sha256_file(STAGED_STEP_PATH),
        "inlet_zone_ids": inlet_zone_ids,
        "inlet_zone_names": inlet_zone_names,
        "outlet_zone_ids": outlet_zone_ids,
        "outlet_zone_names": outlet_zone_names,
        "throat_query_count": len(throat_query_points),
        "throat_zone_hit_count": len(throat_zone_hits),
        "throat_zone_ids": throat_zone_ids,
        "throat_zone_names": throat_zone_names,
        "cell_zone_ids": cell_zone_ids,
        "cell_count": cell_count,
        "face_count": face_count,
        "node_count": node_count,
        "partitions": partitions,
        "cell_volume": cell_volume,
        "free_face_count": free_faces,
        "multi_face_count": multi_faces,
        "orthogonal_quality_limits": quality_values,
        "min_orthogonal_quality": min_orthogonal_quality,
        "mesh_file": file_record(MESH_PATH),
    }
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
    result["mesh_result"] = "PASS_V03_SINGLE_REGION_972_THROAT_VOLUME_MESH"
    result["mesh_evidence"] = {
        "cell_count": cell_count,
        "node_count": node_count,
        "cell_zone_count": len(cell_zone_ids),
        "throat_query_count": len(throat_query_points),
        "throat_zone_count": len(throat_zone_ids),
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

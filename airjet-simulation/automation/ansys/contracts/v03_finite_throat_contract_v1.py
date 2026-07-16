#!/usr/bin/env python3
"""Independent contract checks for the AJM006 V03 finite-throat pilot."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any


ROUTE_NAME = "v03_finite_throat_route_v1.json"
EXPECTED_CONTRACT_ID = "AJM006_GEN1_V03_FINITE_THROAT_ROUTE_V1"
EXPECTED_PRODUCT = "AIRJET_MINI_GEN1"
EXPECTED_CONFIGURATION = "M-3x4-7.0"
EXPECTED_VARIANT = "M-3x4-7.0__R50_BALANCED"
EXPECTED_ASSIGNMENT_SHA256 = (
    "5ab93083b8a9a7f72445230b650d5e88c2f02b90915304f28f1660c272b4e5c5"
)
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


class ContractError(ValueError):
    """A stable fail-closed V03 contract error."""


def fail(code: str) -> None:
    raise ContractError(code)


def canonical_source_contract_bytes(value: bytes) -> bytes:
    """Return the LF bytes Git stores for reviewed text source contracts."""

    normalized = value.replace(b"\r\n", b"\n")
    if b"\r" in normalized:
        fail("V03_SOURCE_CONTRACT_BARE_CR")
    return normalized


def sha256_file(path: Path) -> str:
    return hashlib.sha256(
        canonical_source_contract_bytes(path.read_bytes())
    ).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def one(rows: list[dict[str, str]], **criteria: str) -> dict[str, str]:
    matches = [
        row for row in rows
        if all(row.get(key) == value for key, value in criteria.items())
    ]
    if len(matches) != 1:
        fail("V03_SOURCE_ROW_CARDINALITY")
    return matches[0]


def close(actual: Any, expected: float, tolerance: float = 1.0e-9) -> bool:
    return (
        isinstance(actual, (int, float))
        and not isinstance(actual, bool)
        and math.isfinite(float(actual))
        and abs(float(actual) - expected) <= tolerance
    )


def vector_close(actual: Any, expected: list[float], tolerance: float) -> bool:
    return (
        isinstance(actual, list)
        and len(actual) == len(expected)
        and all(close(left, right, tolerance) for left, right in zip(actual, expected))
    )


def canonical_assignments(blueprint: dict[str, Any]) -> list[dict[str, Any]]:
    frames = {item["frame_id"]: item for item in blueprint.get("frames", [])}
    entities = {
        item["semantic_key"]: item
        for item in blueprint.get("entity_blueprints", [])
    }
    groups = {
        item["solver_name"]: item for item in blueprint.get("groups", [])
    }
    if "ORIFICE_EXIT" not in groups:
        fail("V03_BLUEPRINT_ORIFICE_GROUP")
    assignments = []
    for semantic_key in groups["ORIFICE_EXIT"].get("member_keys", []):
        entity = entities.get(semantic_key)
        if not isinstance(entity, dict):
            fail("V03_BLUEPRINT_ORIFICE_ENTITY")
        frame = frames.get(entity.get("local_frame_id"))
        local = entity.get("local_coordinates_mm")
        if not isinstance(frame, dict) or not isinstance(local, list) or len(local) != 3:
            fail("V03_BLUEPRINT_ORIFICE_FRAME")
        origin = frame.get("origin_mm")
        if not isinstance(origin, list) or len(origin) != 3:
            fail("V03_BLUEPRINT_ORIFICE_ORIGIN")
        assignments.append({
            "semantic_key": semantic_key,
            "cell_index": int(entity["cell_index"]),
            "x_mm": round(float(origin[0]) + float(local[0]), 9),
            "y_mm": round(float(origin[1]) + float(local[1]), 9),
            "axis": [0.0, 0.0, 1.0],
            "radius_mm": 0.125,
            "z_min_mm": 1.5175,
            "z_max_mm": 1.6175,
        })
    assignments.sort(key=lambda item: item["semantic_key"])
    return assignments


def assignment_sha256(assignments: list[dict[str, Any]]) -> str:
    payload = json.dumps(
        assignments,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def minimum_spacing(assignments: list[dict[str, Any]]) -> float:
    result = math.inf
    for left_index, left in enumerate(assignments):
        for right in assignments[left_index + 1:]:
            result = min(
                result,
                math.hypot(
                    float(left["x_mm"]) - float(right["x_mm"]),
                    float(left["y_mm"]) - float(right["y_mm"]),
                ),
            )
    return result


def independent_volume_components(
    layout: dict[str, str],
    thickness: dict[str, dict[str, str]],
    exhaust: dict[str, str],
    vents: list[dict[str, str]],
) -> dict[str, float]:
    membrane = float(layout["membrane_mm"])
    pitch = membrane + float(layout["cell_wall_mm"])
    cells = int(layout["cell_count"])
    radius = float(layout["orifice_diameter_candidate_mm"]) / 2.0
    throat_length = float(thickness["ORIFICE_PLATE"]["thickness_mm"])
    footprint_width = (
        float(exhaust["cell_footprint_x_max_mm"])
        - float(exhaust["cell_footprint_x_min_mm"])
    )
    footprint_height = (
        float(exhaust["cell_footprint_y_max_mm"])
        - float(exhaust["cell_footprint_y_min_mm"])
    )
    downstream_height = (
        float(exhaust["manifold_y_max_mm"])
        - float(exhaust["cell_footprint_y_min_mm"])
    )
    plenum_bottom = float(thickness["TOP_CHAMBER"]["z_min_mm"])
    plenum_top = float(thickness["TOP_CHAMBER"]["z_max_mm"])
    bottom_min = float(thickness["BOTTOM_CHAMBER"]["z_min_mm"])
    bottom_max = float(thickness["BOTTOM_CHAMBER"]["z_max_mm"])
    product_top = float(thickness["TOP_COVER"]["z_max_mm"])
    vent_area = 0.0
    outside_apron_area = 0.0
    footprint_y_min = float(exhaust["cell_footprint_y_min_mm"])
    footprint_y_max = float(exhaust["cell_footprint_y_max_mm"])
    for vent in vents:
        length = float(vent["axis_length_mm"])
        width = float(vent["slot_width_mm"])
        vent_area += length * width
        center_y = float(vent["center_y_cad_mm"])
        dx = abs(float(vent["axis_dx_unit"]))
        dy = abs(float(vent["axis_dy_unit"]))
        half_y = dy * length / 2.0 + dx * width / 2.0
        y_min = center_y - half_y
        y_max = center_y + half_y
        outside_y = max(0.0, footprint_y_min - y_min) + max(
            0.0, y_max - footprint_y_max
        )
        x_span = dx * length + dy * width
        outside_apron_area += outside_y * x_span
    return {
        "downstream_manifold": (
            footprint_width
            * downstream_height
            * float(thickness["IMPINGEMENT_CHANNEL"]["thickness_mm"])
        ),
        "finite_throat_core": 972.0 * math.pi * radius * radius * throat_length,
        "bottom_chambers": cells * membrane * membrane * (bottom_max - bottom_min),
        "cell_rings_below_plenum": (
            cells
            * (pitch * pitch - membrane * membrane)
            * (plenum_bottom - bottom_min)
        ),
        "shared_plenum": footprint_width * footprint_height * (plenum_top - plenum_bottom),
        "vent_risers_above_plenum": vent_area * (product_top - plenum_top),
        "lower_riser_outside_plenum_apron": outside_apron_area * 0.001,
    }


def validate_route(route: dict[str, Any], repo: Path) -> dict[str, Any]:
    if (
        route.get("schema_version") != 1
        or route.get("contract_id") != EXPECTED_CONTRACT_ID
        or route.get("product_id") != EXPECTED_PRODUCT
        or route.get("configuration_id") != EXPECTED_CONFIGURATION
        or route.get("source_variant_id") != EXPECTED_VARIANT
    ):
        fail("V03_ROUTE_IDENTITY")
    sources = route.get("source_contracts")
    if not isinstance(sources, list) or len(sources) != 8:
        fail("V03_ROUTE_SOURCE_SET")
    source_paths: dict[str, Path] = {}
    for item in sources:
        if not isinstance(item, dict) or set(item) != {"git_path", "sha256"}:
            fail("V03_ROUTE_SOURCE_ENTRY")
        relative = item["git_path"]
        path = repo / relative
        if (
            not isinstance(relative, str)
            or Path(relative).is_absolute()
            or ".." in Path(relative).parts
            or not path.is_file()
            or sha256_file(path) != item["sha256"]
        ):
            fail("V03_ROUTE_SOURCE_HASH")
        source_paths[Path(relative).name] = path
    blueprint = json.loads(
        source_paths[
            "variant_02_m_3x4_7_0_r50_balanced.json"
        ].read_text(encoding="utf-8")
    )
    if (
        blueprint.get("product_id") != EXPECTED_PRODUCT
        or blueprint.get("source_variant_id") != EXPECTED_VARIANT
        or blueprint.get("configuration", {}).get("configuration_id")
        != "AJM006_GEN1_CFG_M-3x4-7.0"
    ):
        fail("V03_BLUEPRINT_IDENTITY")
    assignments = canonical_assignments(blueprint)
    throat = route.get("throat_contract")
    counts: dict[int, int] = {}
    for item in assignments:
        counts[item["cell_index"]] = counts.get(item["cell_index"], 0) + 1
    points = {(item["x_mm"], item["y_mm"]) for item in assignments}
    if (
        not isinstance(throat, dict)
        or len(assignments) != 972
        or len(points) != 972
        or set(counts) != set(range(1, 13))
        or set(counts.values()) != {81}
        or assignment_sha256(assignments) != EXPECTED_ASSIGNMENT_SHA256
        or throat.get("assignment_sha256") != EXPECTED_ASSIGNMENT_SHA256
        or not close(minimum_spacing(assignments), 0.700624, 1.0e-9)
        or not close(throat.get("diameter_mm"), 0.25)
        or not close(throat.get("length_mm"), 0.10)
        or throat.get("axis") != [0.0, 0.0, 1.0]
    ):
        fail("V03_ROUTE_THROAT_CONTRACT")
    variants = read_csv(source_paths["p1_model_form_variants.csv"])
    variant = one(variants, variant_id=EXPECTED_VARIANT)
    layouts = read_csv(source_paths["p1_layout_configuration_matrix.csv"])
    layout = one(layouts, configuration_id=variant["configuration_id"])
    thickness_rows = read_csv(source_paths["p1_thickness_budget.csv"])
    thickness = {item["component"]: item for item in thickness_rows}
    exhausts = read_csv(source_paths["p1_planform_exhaust_candidates.csv"])
    exhaust = one(exhausts, exhaust_branch_id=variant["exhaust_branch_id"])
    vent_rows = read_csv(source_paths["p1_vent_geometry_candidates.csv"])
    vents = [
        item for item in vent_rows
        if item["candidate_set_id"] == variant["vent_candidate_set_id"]
    ]
    registry = read_csv(source_paths["full_product_parameter_registry.csv"])
    cad_map = read_csv(source_paths["p1_cad_parameter_map.csv"])
    c016_registry = one(registry, id="C016")
    c016_cad = one(
        cad_map,
        configuration_id=EXPECTED_CONFIGURATION,
        variant_id=EXPECTED_VARIANT,
        parameter_id="C016",
    )
    c016 = route.get("candidate_parameters", {}).get("C016")
    if (
        len(vents) != 4
        or not isinstance(c016, dict)
        or c016 != {
            "value_mm": 0.1,
            "range_mm": [0.05, 0.2],
            "role": "THROAT_LENGTH",
            "evidence_class": "C",
            "status": "cad_placeholder",
            "product_fact": False,
            "uncertainty_scan": "REQUIRED_LATER_NOT_RUN",
        }
        or c016_registry.get("evidence_class") != "C"
        or c016_registry.get("status") != "cad_placeholder"
        or c016_registry.get("unit") != "mm"
        or c016_registry.get("adjustable") != "true"
        or not close(float(c016_registry["initial_value"]), 0.10)
        or c016_cad.get("product_fact") != "false"
        or c016_cad.get("unit") != "mm"
        or not close(float(c016_cad["value"]), 0.10)
    ):
        fail("V03_ROUTE_C016_BOUNDARY")
    expected_components = independent_volume_components(
        layout, thickness, exhaust, vents
    )
    geometry = route.get("geometry_contract")
    observed_components = (
        geometry.get("analytic_volume_components_mm3")
        if isinstance(geometry, dict) else None
    )
    if not isinstance(observed_components, dict):
        fail("V03_ROUTE_ANALYTIC_VOLUME")
    for name, expected in expected_components.items():
        if not close(observed_components.get(name), expected):
            fail("V03_ROUTE_ANALYTIC_COMPONENT_" + name.upper())
    analytic_volume = sum(expected_components.values())
    numerical_overlap = geometry.get("numerical_overlap_mm")
    if (
        not close(numerical_overlap, 0.02)
        or not close(geometry.get("vent_riser_overlap_mm"), 0.001)
        or not close(geometry.get("perimeter_boolean_overlap_mm"), 0.02)
        or not close(
            geometry.get("perimeter_boolean_overlap_raw_mm3"), 0.269568
        )
        or not close(
            geometry.get("perimeter_boolean_overlap_union_volume_delta_mm3"),
            0.0,
        )
        or geometry.get("numerical_overlap_role")
        != "C2_BOOLEAN_ROBUSTNESS_DIAGNOSTIC_AT_THROAT_END_INTERFACES"
        or geometry.get("numerical_overlap_product_fact") is not False
        or geometry.get("vent_riser_overlap_role")
        != "UNCHANGED_C1_BOOLEAN_ROBUSTNESS_CONTROL"
        or geometry.get("perimeter_boolean_overlap_role")
        != "C5_BOOLEAN_ROBUSTNESS_DIAGNOSTIC_BOTTOM_TO_RING_INTERFACE"
        or geometry.get("perimeter_boolean_overlap_product_fact") is not False
    ):
        fail("V03_ROUTE_NUMERICAL_OVERLAP_BOUNDARY")
    overlap = 972.0 * math.pi * 0.125 * 0.125 * numerical_overlap
    upstream = analytic_volume - expected_components["downstream_manifold"] + overlap
    if (
        not close(geometry.get("analytic_volume_mm3"), analytic_volume)
        or not close(geometry.get("numerical_overlap_volume_mm3"), overlap)
        or not close(geometry.get("premerge_upstream_analytic_volume_mm3"), upstream)
        or not vector_close(
            geometry.get("bbox_min_mm"), [-10.875, -17.75, 1.2675], 1.0e-12
        )
        or not vector_close(
            geometry.get("bbox_max_mm"), [10.875, 20.75, 2.8], 1.0e-12
        )
    ):
        fail("V03_ROUTE_ANALYTIC_VOLUME")
    return {
        "assignment_count": len(assignments),
        "assignment_sha256": assignment_sha256(assignments),
        "minimum_spacing_mm": minimum_spacing(assignments),
        "analytic_volume_mm3": analytic_volume,
    }


def validate_body(
    value: Any,
    geometry_contract: dict[str, Any],
    bbox_tolerance: float,
    volume_tolerance: float,
) -> None:
    if (
        not isinstance(value, dict)
        or value.get("piece_count") != 1
        or value.get("is_closed") is not True
        or value.get("is_manifold") is not True
        or not vector_close(
            value.get("bbox_min_mm"), geometry_contract["bbox_min_mm"], bbox_tolerance
        )
        or not vector_close(
            value.get("bbox_max_mm"), geometry_contract["bbox_max_mm"], bbox_tolerance
        )
        or not close(
            value.get("volume_mm3"),
            geometry_contract["analytic_volume_mm3"],
            volume_tolerance,
        )
    ):
        fail("V03_PRODUCER_BODY_CONTRACT")


def validate_producer_report(route: dict[str, Any], report: dict[str, Any]) -> None:
    if (
        report.get("probe") != "v03_continuous_fluid_producer"
        or report.get("status") != "PASS_PARTIAL_CAD_CAPABILITY"
        or report.get("error") not in (None, "")
        or report.get("formal_006_completion") is not False
        or report.get("p1_stage_gate") != "NOT_RUN"
        or report.get("p1_p6_gates") != "NOT_RUN"
        or report.get("mesh") != "NOT_RUN"
        or report.get("physics") != "NOT_RUN"
        or report.get("exact_product_geometry") != "NOT_CLAIMED"
    ):
        fail("V03_PRODUCER_CLAIM_BOUNDARY")
    assertions = report.get("assertions")
    if (
        not isinstance(assertions, dict)
        or set(assertions) != PRODUCER_ASSERTIONS
        or any(value is not True for value in assertions.values())
    ):
        fail("V03_PRODUCER_ASSERTIONS")
    geometry = report.get("geometry")
    expected_geometry = route["geometry_contract"]
    boundaries = route["boundary_contract"]
    if (
        not isinstance(geometry, dict)
        or geometry.get("cell_count") != 12
        or geometry.get("orifice_count") != 972
        or geometry.get("group_counts")
        != {"FLUID_CONTINUOUS": 1, **boundaries}
        or geometry.get("step_boundary_counts") != boundaries
        or geometry.get("all_cells_have_throats") is not True
        or set((geometry.get("throat_counts_by_cell") or {}).values()) != {81}
    ):
        fail("V03_PRODUCER_TOPOLOGY")
    validate_body(
        geometry.get("continuous_before_save"),
        expected_geometry,
        expected_geometry["bbox_tolerance_native_mm"],
        expected_geometry["volume_tolerance_native_mm3"],
    )
    native = geometry.get("native_reopen_summary")
    step = geometry.get("step_reimport_summary")
    if not isinstance(native, dict) or native.get("body_count") != 1:
        fail("V03_PRODUCER_NATIVE_REOPEN")
    if not isinstance(step, dict) or step.get("body_count") != 1:
        fail("V03_PRODUCER_STEP_REOPEN")
    validate_body(
        native.get("body_fingerprint"),
        expected_geometry,
        expected_geometry["bbox_tolerance_native_mm"],
        expected_geometry["volume_tolerance_native_mm3"],
    )
    validate_body(
        step.get("body_fingerprint"),
        expected_geometry,
        expected_geometry["bbox_tolerance_step_mm"],
        expected_geometry["volume_tolerance_step_mm3"],
    )


def load_and_validate(route_path: Path, repo: Path) -> dict[str, Any]:
    route = json.loads(route_path.read_text(encoding="utf-8"))
    validate_route(route, repo)
    return route

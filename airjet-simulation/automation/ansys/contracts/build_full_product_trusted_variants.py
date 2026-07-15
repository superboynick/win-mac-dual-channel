#!/usr/bin/env python3
"""Build the nine immutable AirJet Mini Gen1 P1 semantic blueprints.

This is a static contract generator.  It does not import or launch ANSYS and
does not create CAD.  All internal dimensions remain the candidate branches
already declared by the P1 input tables; none are promoted to product fact.
"""

from __future__ import print_function

import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
OUTPUT = HERE / "trusted_full_product_gen1"
CAMPAIGN_PATH = OUTPUT / "campaign.json"
PRODUCT_ID = "AIRJET_MINI_GEN1"
PRODUCER_PROFILE_ID = "ajm006-spaceclaim-full-product-producer-v1"
OBSERVER_PROFILE_ID = "ajm006-workbench-full-product-observer-v1"
ARTIFACT_ROOT_ID = "p1_cad_006"

sys.path.insert(0, str(HERE))
import full_product_semantic_contract_v1 as contract  # noqa: E402


SOURCE_PATHS = (
    ("full_product_validator", "airjet-simulation/automation/ansys/contracts/full_product_semantic_contract_v1.py"),
    ("full_product_schema", "airjet-simulation/automation/ansys/contracts/full_product_semantic_sidecar_v1.schema.json"),
    ("full_product_core_test", "airjet-simulation/automation/ansys/contracts/test_full_product_semantic_contract_v1.py"),
    ("trusted_variant_generator", "airjet-simulation/automation/ansys/contracts/build_full_product_trusted_variants.py"),
    ("trusted_variant_test", "airjet-simulation/automation/ansys/contracts/test_full_product_trusted_variants.py"),
    ("p1_model_form_variants", "airjet-simulation/parameters/p1_model_form_variants.csv"),
    ("p1_layout_configuration_matrix", "airjet-simulation/parameters/p1_layout_configuration_matrix.csv"),
    ("p1_internal_geometry_rules", "airjet-simulation/parameters/p1_internal_geometry_rules.csv"),
    ("p1_cad_parameter_map", "airjet-simulation/parameters/p1_cad_parameter_map.csv"),
    ("p1_orifice_pattern_candidates", "airjet-simulation/parameters/p1_orifice_pattern_candidates.csv"),
    ("p1_vent_geometry_candidates", "airjet-simulation/parameters/p1_vent_geometry_candidates.csv"),
    ("p1_planform_exhaust_candidates", "airjet-simulation/parameters/p1_planform_exhaust_candidates.csv"),
    ("p1_thickness_budget", "airjet-simulation/parameters/p1_thickness_budget.csv"),
)
REQUIRED_HASH_KEYS = tuple(["full_product_blueprint", "trusted_blueprint_file", "trusted_campaign"] + [item[0] for item in SOURCE_PATHS])


def read_csv(relative_path):
    with (REPO / relative_path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256_bytes(value):
    return hashlib.sha256(value).hexdigest()


def canonical_source_contract_bytes(value):
    """Return the LF bytes Git stores for reviewed text source contracts."""

    normalized = value.replace(b"\r\n", b"\n")
    if b"\r" in normalized:
        raise ValueError("GEN1_SOURCE_CONTRACT_BARE_CR")
    return normalized


def read_source_contract_bytes(git_path):
    return canonical_source_contract_bytes((REPO / git_path).read_bytes())


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("ascii")


def safe_id(value, prefix):
    normalized = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_.-")
    return (prefix + normalized)[:128]


def key(namespace, kind, name):
    return "%s.%s.%s" % (namespace, kind, name)


def direction(mode, vector=None, tolerance=5.0):
    return {"mode": mode, "vector": vector, "tolerance_deg": tolerance}


def match(centroid, bbox_min, bbox_max, measure_kind, measure_value, measure_tolerance, measure_unit, solver_geometry_type, edge_count, measure_role="MATCH", centroid_tolerance=0.01):
    return {
        "centroid_mm": centroid,
        "centroid_tolerance_mm": centroid_tolerance,
        "measure_kind": measure_kind,
        "measure_value": measure_value,
        "measure_tolerance": measure_tolerance,
        "measure_unit": measure_unit,
        "measure_role": measure_role,
        "bbox_min_mm": bbox_min,
        "bbox_max_mm": bbox_max,
        "solver_geometry_type": solver_geometry_type,
        "edge_count": edge_count,
    }


def surface(namespace, name, feature_name, owner_key, cell_index, frame_id, centroid, bbox_min, bbox_max, geometry_type, normal, area, edge_count, adjacent_body_keys=None):
    adjacency = [owner_key] if adjacent_body_keys is None else list(adjacent_body_keys)
    if owner_key not in adjacency:
        raise ValueError("GEN1_SURFACE_OWNER_NOT_ADJACENT")
    return {
        "semantic_key": key(namespace, "surface", name),
        "feature_key": key(namespace, "feature", feature_name),
        "entity_kind": "SURFACE",
        "owner_key": owner_key,
        "cell_index": cell_index,
        "local_frame_id": frame_id,
        "local_coordinates_mm": centroid,
        "geometry_type": geometry_type,
        "direction_constraint": direction("VECTOR", normal, 5.0),
        "match_constraints": match(
            centroid, bbox_min, bbox_max, "AREA", area,
            max(1.0e-6, float(area) * 1.0e-4), "mm^2", "PLANE", edge_count,
        ),
        "topology": {
            "required_adjacent_keys": adjacency,
            "critical": True,
            "allow_isolated": False,
        },
        "expected_cardinality": 1,
    }


def outward_surface(namespace, name, feature_name, owner_key, centroid, bbox_min, bbox_max, area):
    item = surface(
        namespace, name, feature_name, owner_key, None, "GLOBAL", centroid,
        bbox_min, bbox_max, "PLANAR_FACE", [0.0, 0.0, -1.0], area, 4,
    )
    item["direction_constraint"] = direction("OUTWARD_FROM_OWNER", None, 15.0)
    return item


def artifact_contracts(slug):
    records = (
        ("native_cad", "NATIVE_CAD", "product.scdocx"),
        ("producer_job_record", "PRODUCER_JOB_RECORD", "checks/producer_job.json"),
        ("producer_artifact_manifest", "PRODUCER_ARTIFACT_MANIFEST", "checks/producer_artifact_manifest.json"),
        ("step_geometry", "STEP_GEOMETRY", "product.step"),
        ("step_reimport_log", "STEP_REIMPORT_LOG", "checks/step_reimport.json"),
        ("semantic_sidecar", "SEMANTIC_SIDECAR", "checks/full_product_semantic_sidecar_v1.json"),
        ("semantic_binding", "SEMANTIC_BINDING", "checks/full_product_semantic_binding_v1.json"),
        ("semantic_observation", "SEMANTIC_OBSERVATION", "checks/full_product_semantic_observation_v1.json"),
        ("semantic_key_report", "SEMANTIC_KEY_CARDINALITY_REPORT", "checks/semantic_key_report_v1.json"),
        ("workbench_project", "WORKBENCH_PROJECT", "checks/semantic_reconstruction.wbpj"),
        ("observer_job_record", "OBSERVER_JOB_RECORD", "checks/observer_job.json"),
        ("observer_artifact_manifest", "OBSERVER_ARTIFACT_MANIFEST", "checks/observer_artifact_manifest.json"),
        ("workbench_semantic_log", "WORKBENCH_STEP_SEMANTIC_LOG", "checks/workbench_semantic.log"),
    )
    return [
        {"artifact_id": artifact_id, "role": role, "relative_path": "%s/%s" % (slug, relative), "required": True}
        for artifact_id, role, relative in records
    ]


def selected_row(rows, field, value):
    matches = [row for row in rows if row[field] == value]
    if len(matches) != 1:
        raise ValueError("GEN1_SOURCE_ROW_NOT_UNIQUE:%s:%s" % (field, value))
    return matches[0]


def selected_rows(rows, field, value):
    matches = [row for row in rows if row[field] == value]
    if not matches:
        raise ValueError("GEN1_SOURCE_ROWS_MISSING:%s:%s" % (field, value))
    return matches


def build_blueprint(index, variant, layout, orifice, vents, exhaust):
    source_variant_id = variant["variant_id"]
    variant_id = safe_id(source_variant_id, "AJM006_GEN1_V%02d_" % index)
    configuration_id = safe_id(variant["configuration_id"], "AJM006_GEN1_CFG_")
    namespace = "ajmgen1v%02d" % index
    slug = "variant_%02d_%s" % (index, re.sub(r"[^a-z0-9]+", "_", source_variant_id.lower()).strip("_"))
    nx = int(layout["nx"])
    ny = int(layout["ny"])
    cell_count = int(layout["cell_count"])
    membrane = float(layout["membrane_mm"])
    wall = float(layout["cell_wall_mm"])
    pitch = membrane + wall
    residual_bottom = float(variant["residual_bottom_mm"])
    heat_z = 0.8 + residual_bottom + 0.1
    impingement_top_z = heat_z + 0.25
    orifice_top_z = impingement_top_z + 0.1
    membrane_bottom_z = orifice_top_z + 0.04
    membrane_top_z = membrane_bottom_z + 0.275
    body_top_z = 2.8
    footprint_x_min = float(exhaust["cell_footprint_x_min_mm"])
    footprint_x_max = float(exhaust["cell_footprint_x_max_mm"])
    footprint_y_min = float(exhaust["cell_footprint_y_min_mm"])
    footprint_y_max = float(exhaust["cell_footprint_y_max_mm"])
    manifold_y_max = float(exhaust["manifold_y_max_mm"])
    upstream_body_key = key(namespace, "body", "fluid_upstream")
    downstream_body_key = key(namespace, "body", "fluid_downstream")
    frames = [{
        "frame_id": "GLOBAL", "parent_frame_id": None, "cell_index": None,
        "origin_mm": [0.0, 0.0, 0.0],
        "axes": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
    }]
    cells = []
    cell_index = 0
    for row in range(ny):
        for column in range(nx):
            cell_index += 1
            center_x = (float(column) - float(nx - 1) / 2.0) * pitch
            center_y = (float(row) - float(ny - 1) / 2.0) * pitch
            frame_id = "CELL_%03d" % cell_index
            frames.append({
                "frame_id": frame_id, "parent_frame_id": "GLOBAL", "cell_index": cell_index,
                "origin_mm": [round(center_x, 9), round(center_y, 9), 0.0],
                "axes": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
            })
            cells.append((cell_index, frame_id))
    if cell_index != cell_count:
        raise ValueError("GEN1_CELL_COUNT_MISMATCH")

    surfaces = []
    vent_keys = []
    vent_bbox_x_min = []
    vent_bbox_x_max = []
    vent_bbox_y_min = []
    vent_bbox_y_max = []
    for vent in sorted(vents, key=lambda row: row["vent_id"]):
        number = int(vent["vent_id"][1:])
        cx = float(vent["center_x_cad_mm"])
        cy = float(vent["center_y_cad_mm"])
        dx = float(vent["axis_dx_unit"])
        dy = float(vent["axis_dy_unit"])
        length = float(vent["axis_length_mm"])
        width = float(vent["slot_width_mm"])
        half_x = abs(dx) * length / 2.0 + abs(dy) * width / 2.0
        half_y = abs(dy) * length / 2.0 + abs(dx) * width / 2.0
        name = "vent.%03d" % number
        item = surface(
            namespace, name, "vent.%03d" % number, upstream_body_key, None, "GLOBAL",
            [cx, cy, 2.8], [cx - half_x, cy - half_y, 2.799],
            [cx + half_x, cy + half_y, 2.801], "PLANAR_FACE",
            [0.0, 0.0, -1.0], length * width, 4,
        )
        surfaces.append(item)
        vent_keys.append(item["semantic_key"])
        vent_bbox_x_min.append(cx - half_x)
        vent_bbox_x_max.append(cx + half_x)
        vent_bbox_y_min.append(cy - half_y)
        vent_bbox_y_max.append(cy + half_y)

    outlet_width = float(exhaust["outlet_width_mm"])
    outlet_height = float(exhaust["outlet_height_mm"])
    outlet_x = float(exhaust["outlet_center_x_mm"])
    outlet_y = float(exhaust["outlet_y_mm"])
    outlet_z = heat_z + outlet_height / 2.0
    outlet = surface(
        namespace, "product_outlet", "product_outlet", downstream_body_key, None, "GLOBAL",
        [outlet_x, outlet_y, outlet_z],
        [outlet_x - outlet_width / 2.0, outlet_y - 0.001, heat_z],
        [outlet_x + outlet_width / 2.0, outlet_y + 0.001, heat_z + outlet_height],
        "PLANAR_FACE", [0.0, 1.0, 0.0], outlet_width * outlet_height, 4,
    )
    surfaces.append(outlet)
    footprint_width = footprint_x_max - footprint_x_min
    footprint_length = footprint_y_max - footprint_y_min
    manifold_length = manifold_y_max - footprint_y_max
    manifold_width = float(exhaust["manifold_x_max_at_array_mm"]) - float(
        exhaust["manifold_x_min_at_array_mm"]
    )
    footprint_area = footprint_width * footprint_length
    manifold_area = manifold_length * (manifold_width + outlet_width) / 2.0
    heat_area = footprint_area + manifold_area
    footprint_centroid_y = (footprint_y_min + footprint_y_max) / 2.0
    manifold_centroid_y = footprint_y_max + manifold_length * (
        manifold_width + 2.0 * outlet_width
    ) / (3.0 * (manifold_width + outlet_width))
    heat_centroid_y = (
        footprint_area * footprint_centroid_y + manifold_area * manifold_centroid_y
    ) / heat_area
    heat_wall = outward_surface(
        namespace, "heat_wall", "heat_wall", downstream_body_key,
        [0.0, heat_centroid_y, heat_z],
        [footprint_x_min, footprint_y_min, heat_z - 0.001],
        [footprint_x_max, manifold_y_max, heat_z + 0.001], heat_area,
    )
    heat_wall["match_constraints"]["edge_count"] = (
        4 if math.isclose(outlet_width, manifold_width, rel_tol=0.0, abs_tol=1.0e-9)
        else 6
    )
    surfaces.append(heat_wall)

    membrane_top_keys = []
    membrane_bottom_keys = []
    orifice_keys = []
    diameter = float(orifice["diameter_mm"])
    hole_pitch_x = float(orifice["pitch_x_mm"])
    hole_pitch_y = float(orifice["pitch_y_mm"])
    radius = diameter / 2.0
    nx_holes = int(math.floor((membrane / 2.0 - radius) / hole_pitch_x + 1.0e-12))
    ny_holes = int(math.floor((membrane / 2.0 - radius) / hole_pitch_y + 1.0e-12))
    for cell, frame_id in cells:
        top_name = "membrane_top.cell.%03d" % cell
        top = surface(
            namespace, top_name, top_name, upstream_body_key, cell, frame_id,
            [0.0, 0.0, membrane_top_z],
            [-membrane / 2.0, -membrane / 2.0, membrane_top_z - 0.001],
            [membrane / 2.0, membrane / 2.0, membrane_top_z + 0.001],
            "PLANAR_FACE", [0.0, 0.0, -1.0], membrane * membrane, 4,
        )
        surfaces.append(top)
        membrane_top_keys.append(top["semantic_key"])
        bottom_name = "membrane_bottom.cell.%03d" % cell
        bottom = surface(
            namespace, bottom_name, bottom_name, upstream_body_key, cell, frame_id,
            [0.0, 0.0, membrane_bottom_z],
            [-membrane / 2.0, -membrane / 2.0, membrane_bottom_z - 0.001],
            [membrane / 2.0, membrane / 2.0, membrane_bottom_z + 0.001],
            "PLANAR_FACE", [0.0, 0.0, 1.0], membrane * membrane, 4,
        )
        surfaces.append(bottom)
        membrane_bottom_keys.append(bottom["semantic_key"])
        hole_number = 0
        for iy in range(-ny_holes, ny_holes + 1):
            for ix in range(-nx_holes, nx_holes + 1):
                hole_number += 1
                x = float(ix) * hole_pitch_x
                y = float(iy) * hole_pitch_y
                hole_name = "orifice.cell.%03d.hole.%03d" % (cell, hole_number)
                hole = surface(
                    namespace, hole_name, hole_name, upstream_body_key, cell, frame_id,
                    [x, y, impingement_top_z],
                    [x - radius, y - radius, impingement_top_z - 0.001],
                    [x + radius, y + radius, impingement_top_z + 0.001],
                    "PLANAR_FACE", [0.0, 0.0, -1.0], math.pi * radius * radius, 1,
                    adjacent_body_keys=[upstream_body_key, downstream_body_key],
                )
                surfaces.append(hole)
                orifice_keys.append(hole["semantic_key"])

    surface_keys = [item["semantic_key"] for item in surfaces]
    upstream_surface_keys = vent_keys + membrane_top_keys + membrane_bottom_keys + orifice_keys
    downstream_surface_keys = [outlet["semantic_key"], heat_wall["semantic_key"]] + orifice_keys

    def fluid_body(name, semantic_key, centroid, bbox_min, bbox_max, adjacent_surface_keys):
        return {
            "semantic_key": semantic_key,
            "feature_key": key(namespace, "feature", name),
            "entity_kind": "BODY",
            "owner_key": None,
            "cell_index": None,
            "local_frame_id": "GLOBAL",
            "local_coordinates_mm": centroid,
            "geometry_type": "FLUID_BODY",
            "direction_constraint": direction("NOT_APPLICABLE", None, 0.0),
            "match_constraints": match(
                centroid, bbox_min, bbox_max, "NONE", None, None, None,
                "SOLID", None, measure_role="NOT_APPLICABLE",
                centroid_tolerance=30.0,
            ),
            "topology": {
                "required_adjacent_keys": adjacent_surface_keys,
                "critical": True,
                "allow_isolated": False,
            },
            "expected_cardinality": 1,
        }

    upstream_x_min = min([footprint_x_min] + vent_bbox_x_min)
    upstream_x_max = max([footprint_x_max] + vent_bbox_x_max)
    upstream_y_min = min([footprint_y_min] + vent_bbox_y_min)
    upstream_y_max = max([footprint_y_max] + vent_bbox_y_max)
    upstream_body = fluid_body(
        "fluid_upstream", upstream_body_key,
        [0.0, 0.0, (impingement_top_z + body_top_z) / 2.0],
        [upstream_x_min, upstream_y_min, impingement_top_z],
        [upstream_x_max, upstream_y_max, body_top_z], upstream_surface_keys,
    )
    downstream_body = fluid_body(
        "fluid_downstream", downstream_body_key,
        [0.0, heat_centroid_y, (heat_z + impingement_top_z) / 2.0],
        [footprint_x_min, footprint_y_min, heat_z],
        [footprint_x_max, manifold_y_max, impingement_top_z], downstream_surface_keys,
    )
    entities = [upstream_body, downstream_body] + surfaces
    group_specs = (
        ("fluid_upstream", "UPSTREAM_FLUID_BODY", "BODY", [upstream_body_key], "fluid_bodies"),
        ("fluid_downstream", "DOWNSTREAM_FLUID_BODY", "BODY", [downstream_body_key], "fluid_bodies"),
        ("inlet", "INLET", "SURFACE", vent_keys, "fluid_boundaries"),
        ("outlet", "OUTLET", "SURFACE", [outlet["semantic_key"]], "fluid_boundaries"),
        ("membrane_top", "MEMBRANE_TOP", "SURFACE", membrane_top_keys, "fluid_boundaries"),
        ("membrane_bottom", "MEMBRANE_BOTTOM", "SURFACE", membrane_bottom_keys, "fluid_boundaries"),
        ("orifice_exit", "ORIFICE_EXIT", "SURFACE", orifice_keys, "fluid_interfaces"),
        ("heat_wall", "HEAT_WALL", "SURFACE", [heat_wall["semantic_key"]], "fluid_boundaries"),
    )
    groups = [
        {
            "group_key": key(namespace, "group", name),
            "solver_name": solver_name,
            "entity_kind": entity_kind,
            "member_keys": members,
            "expected_cardinality": len(members),
            "partition_family": family,
        }
        for name, solver_name, entity_kind, members, family in group_specs
    ]
    body_group_keys = [groups[0]["group_key"], groups[1]["group_key"]]
    boundary_group_keys = [
        item["group_key"] for item in groups[2:]
        if item["partition_family"] == "fluid_boundaries"
    ]
    interface_group_keys = [
        item["group_key"] for item in groups[2:]
        if item["partition_family"] == "fluid_interfaces"
    ]
    boundary_surface_keys = (
        vent_keys + [outlet["semantic_key"]] + membrane_top_keys
        + membrane_bottom_keys + [heat_wall["semantic_key"]]
    )
    partitions = [
        {
            "partition_key": key(namespace, "partition", "fluid_bodies"),
            "entity_kind": "BODY", "group_keys": body_group_keys,
            "universe_keys": [upstream_body_key, downstream_body_key], "require_pairwise_disjoint": True,
            "require_full_coverage": True,
        },
        {
            "partition_key": key(namespace, "partition", "fluid_boundaries"),
            "entity_kind": "SURFACE", "group_keys": boundary_group_keys,
            "universe_keys": boundary_surface_keys, "require_pairwise_disjoint": True,
            "require_full_coverage": True,
        },
        {
            "partition_key": key(namespace, "partition", "fluid_interfaces"),
            "entity_kind": "SURFACE", "group_keys": interface_group_keys,
            "universe_keys": orifice_keys, "require_pairwise_disjoint": True,
            "require_full_coverage": True,
        },
    ]
    configuration = {
        "configuration_id": configuration_id,
        "product_id": PRODUCT_ID,
        "variant_id": variant_id,
        "key_namespace": namespace,
        "root_frame_id": "GLOBAL",
        "cell_indices": list(range(1, cell_count + 1)),
        "expected_entity_cardinality": {"BODY": 2, "SURFACE": len(surface_keys)},
        "required_semantic_keys": [item["semantic_key"] for item in entities],
        "required_group_keys": [item["group_key"] for item in groups],
        "required_partition_keys": [item["partition_key"] for item in partitions],
    }
    blueprint = {
        "schema_version": 1,
        "contract_id": contract.BLUEPRINT_CONTRACT_ID,
        "scope": "FULL_PRODUCT",
        "product_id": PRODUCT_ID,
        "source_variant_id": source_variant_id,
        "configuration": configuration,
        "frames": frames,
        "entity_blueprints": entities,
        "groups": groups,
        "partitions": partitions,
        "producer_profile_id": PRODUCER_PROFILE_ID,
        "observer_profile_id": OBSERVER_PROFILE_ID,
        "required_contract_hash_keys": list(REQUIRED_HASH_KEYS),
        "artifact_contracts": artifact_contracts(slug),
        "artifact_root_id": ARTIFACT_ROOT_ID,
        "sidecar_artifact_ids": ["native_cad", "step_geometry", "step_reimport_log"],
        "sidecar_artifact_id": "semantic_sidecar",
        "binding_artifact_id": "semantic_binding",
        "observation_artifact_id": "semantic_observation",
        "solver_import_artifact_id": "step_geometry",
    }
    summary = contract.validate_trusted_blueprint(blueprint)
    return blueprint, summary, slug


def source_contracts():
    records = []
    for contract_key, git_path in SOURCE_PATHS:
        records.append({
            "contract_key": contract_key,
            "git_path": git_path,
            "sha256": sha256_bytes(read_source_contract_bytes(git_path)),
        })
    return records


def validate_variant_internal_rule_contract(variants, internal_rules):
    rule_ids = set(item.get("rule_id") for item in internal_rules)
    expected_rule_ids = {
        "CELL_CENTER_AND_TILE_R0",
        "CENTRAL_ANCHOR_SQUARE_DATUM_R0",
        "BOTTOM_CHAMBER_PER_CELL_SQUARE_R0",
        "CELL_PARTITION_DATUM_R0",
        "TOP_SHARED_PLENUM_R0",
        "VENT_RISER_CANDIDATE_R0",
        "PERIM_SPLIT_GAP_R0",
        "SIDE_WALL_BOUNDARY_R0",
        "RESIDUAL_NUMERICAL_CLOSURE_R0",
        "ORIFICE_PER_CELL_CENTERED_CLIP_R0",
    }
    if rule_ids != expected_rule_ids:
        raise ValueError("GEN1_INTERNAL_RULE_SET")
    variant_fields = (
        "cell_geometry_rule_id",
        "central_anchor_rule_id",
        "bottom_chamber_rule_id",
        "cell_partition_rule_id",
        "top_chamber_branch_id",
        "vent_riser_rule_id",
        "perimeter_gap_branch_id",
        "side_frame_closure_branch_id",
        "residual_closure_branch_id",
        "orifice_grid_rule_id",
    )
    if any(
        set(item.get(field) for field in variant_fields) != expected_rule_ids
        or item.get("vent_riser_rule_id") != "VENT_RISER_CANDIDATE_R0"
        for item in variants
    ):
        raise ValueError("GEN1_VARIANT_INTERNAL_RULE_BINDING")


def validate_gen1_target(campaign, blueprints):
    if campaign.get("product_id") != PRODUCT_ID or campaign.get("expected_variant_count") != 9:
        raise ValueError("GEN1_CAMPAIGN_TARGET")
    if len(blueprints) != 9:
        raise ValueError("GEN1_BLUEPRINT_COUNT")
    for blueprint in blueprints:
        namespace = blueprint.get("configuration", {}).get("key_namespace")
        entities = dict(
            (item.get("semantic_key"), item)
            for item in blueprint.get("entity_blueprints", [])
        )
        upstream_key = key(namespace, "body", "fluid_upstream")
        downstream_key = key(namespace, "body", "fluid_downstream")
        body_keys = set(
            item_key
            for item_key, item in entities.items()
            if item.get("entity_kind") == "BODY"
        )
        group_rows = blueprint.get("groups", [])
        groups_by_solver = dict(
            (item.get("solver_name"), item)
            for item in group_rows
        )
        expected_solver_names = {
            "UPSTREAM_FLUID_BODY", "DOWNSTREAM_FLUID_BODY", "INLET",
            "OUTLET", "MEMBRANE_TOP", "MEMBRANE_BOTTOM", "ORIFICE_EXIT",
            "HEAT_WALL",
        }
        if (
            len(group_rows) != len(groups_by_solver)
            or set(groups_by_solver) != expected_solver_names
        ):
            raise ValueError("GEN1_BLUEPRINT_TWO_ZONE_GROUP_CONTRACT")

        role_keys = {
            "UPSTREAM_FLUID_BODY": [upstream_key],
            "DOWNSTREAM_FLUID_BODY": [downstream_key],
            "INLET": sorted(
                item_key for item_key in entities
                if item_key.startswith(key(namespace, "surface", "vent."))
            ),
            "OUTLET": [key(namespace, "surface", "product_outlet")],
            "MEMBRANE_TOP": sorted(
                item_key for item_key in entities
                if item_key.startswith(key(namespace, "surface", "membrane_top.cell."))
            ),
            "MEMBRANE_BOTTOM": sorted(
                item_key for item_key in entities
                if item_key.startswith(key(namespace, "surface", "membrane_bottom.cell."))
            ),
            "ORIFICE_EXIT": sorted(
                item_key for item_key in entities
                if item_key.startswith(key(namespace, "surface", "orifice.cell."))
            ),
            "HEAT_WALL": [key(namespace, "surface", "heat_wall")],
        }
        expected_families = {
            "UPSTREAM_FLUID_BODY": "fluid_bodies",
            "DOWNSTREAM_FLUID_BODY": "fluid_bodies",
            "INLET": "fluid_boundaries",
            "OUTLET": "fluid_boundaries",
            "MEMBRANE_TOP": "fluid_boundaries",
            "MEMBRANE_BOTTOM": "fluid_boundaries",
            "ORIFICE_EXIT": "fluid_interfaces",
            "HEAT_WALL": "fluid_boundaries",
        }
        if any(
            sorted(groups_by_solver[solver_name].get("member_keys", []))
            != role_keys[solver_name]
            or groups_by_solver[solver_name].get("expected_cardinality")
            != len(role_keys[solver_name])
            or groups_by_solver[solver_name].get("partition_family")
            != expected_families[solver_name]
            for solver_name in expected_solver_names
        ):
            raise ValueError("GEN1_BLUEPRINT_TWO_ZONE_GROUP_CONTRACT")

        orifice_keys = role_keys["ORIFICE_EXIT"]
        upstream_only_keys = set(
            role_keys["INLET"] + role_keys["MEMBRANE_TOP"]
            + role_keys["MEMBRANE_BOTTOM"]
        )
        downstream_only_keys = set(role_keys["OUTLET"] + role_keys["HEAT_WALL"])
        interface_keys = set(orifice_keys)
        if (
            body_keys != {upstream_key, downstream_key}
            or blueprint.get("configuration", {})
            .get("expected_entity_cardinality", {})
            .get("BODY") != 2
            or not interface_keys
            or set(entities[upstream_key]["topology"]["required_adjacent_keys"])
            != upstream_only_keys | interface_keys
            or set(entities[downstream_key]["topology"]["required_adjacent_keys"])
            != downstream_only_keys | interface_keys
        ):
            raise ValueError("GEN1_BLUEPRINT_TWO_ZONE_BODY_CONTRACT")

        surface_contracts = (
            (upstream_only_keys, upstream_key, {upstream_key}),
            (downstream_only_keys, downstream_key, {downstream_key}),
            (interface_keys, upstream_key, {upstream_key, downstream_key}),
        )
        if any(
            item_key not in entities
            or entities[item_key].get("entity_kind") != "SURFACE"
            or entities[item_key].get("owner_key") != owner_key
            or set(entities[item_key].get("topology", {}).get("required_adjacent_keys", []))
            != adjacent_keys
            for item_keys, owner_key, adjacent_keys in surface_contracts
            for item_key in item_keys
        ):
            raise ValueError("GEN1_BLUEPRINT_TWO_ZONE_SURFACE_CONTRACT")

        expected_directions = {
            "INLET": ("VECTOR", [0.0, 0.0, -1.0]),
            "OUTLET": ("VECTOR", [0.0, 1.0, 0.0]),
            "MEMBRANE_TOP": ("VECTOR", [0.0, 0.0, -1.0]),
            "MEMBRANE_BOTTOM": ("VECTOR", [0.0, 0.0, 1.0]),
            "ORIFICE_EXIT": ("VECTOR", [0.0, 0.0, -1.0]),
            "HEAT_WALL": ("OUTWARD_FROM_OWNER", None),
        }
        if any(
            entities[item_key].get("direction_constraint", {}).get("mode") != mode
            or entities[item_key].get("direction_constraint", {}).get("vector") != vector
            for solver_name, (mode, vector) in expected_directions.items()
            for item_key in role_keys[solver_name]
        ):
            raise ValueError("GEN1_BLUEPRINT_TWO_ZONE_DIRECTION_CONTRACT")

        partitions_by_key = dict(
            (item.get("partition_key"), item)
            for item in blueprint.get("partitions", [])
        )
        expected_partitions = {
            key(namespace, "partition", "fluid_bodies"): (
                "BODY",
                {groups_by_solver["UPSTREAM_FLUID_BODY"]["group_key"],
                 groups_by_solver["DOWNSTREAM_FLUID_BODY"]["group_key"]},
                {upstream_key, downstream_key},
            ),
            key(namespace, "partition", "fluid_boundaries"): (
                "SURFACE",
                {groups_by_solver[name]["group_key"] for name in (
                    "INLET", "OUTLET", "MEMBRANE_TOP", "MEMBRANE_BOTTOM", "HEAT_WALL"
                )},
                upstream_only_keys | downstream_only_keys,
            ),
            key(namespace, "partition", "fluid_interfaces"): (
                "SURFACE", {groups_by_solver["ORIFICE_EXIT"]["group_key"]},
                interface_keys,
            ),
        }
        if (
            len(partitions_by_key) != 3
            or set(partitions_by_key) != set(expected_partitions)
            or any(
                partitions_by_key[partition_key].get("entity_kind") != entity_kind
                or set(partitions_by_key[partition_key].get("group_keys", [])) != group_keys
                or set(partitions_by_key[partition_key].get("universe_keys", [])) != universe_keys
                or partitions_by_key[partition_key].get("require_pairwise_disjoint") is not True
                or partitions_by_key[partition_key].get("require_full_coverage") is not True
                for partition_key, (entity_kind, group_keys, universe_keys)
                in expected_partitions.items()
            )
        ):
            raise ValueError("GEN1_BLUEPRINT_TWO_ZONE_PARTITION_CONTRACT")
        roles = set(item.get("role") for item in blueprint.get("artifact_contracts", []))
        if (
            blueprint.get("product_id") != PRODUCT_ID
            or blueprint.get("configuration", {}).get("product_id") != PRODUCT_ID
            or blueprint.get("producer_profile_id") != PRODUCER_PROFILE_ID
            or blueprint.get("observer_profile_id") != OBSERVER_PROFILE_ID
            or blueprint.get("artifact_root_id") != ARTIFACT_ROOT_ID
            or set(blueprint.get("required_contract_hash_keys", [])) != set(REQUIRED_HASH_KEYS)
            or not {
                "PRODUCER_JOB_RECORD",
                "PRODUCER_ARTIFACT_MANIFEST",
                "SEMANTIC_OBSERVATION",
                "OBSERVER_JOB_RECORD",
                "OBSERVER_ARTIFACT_MANIFEST",
            }.issubset(roles)
            or "G2" in json.dumps(blueprint, ensure_ascii=True).upper()
        ):
            raise ValueError("GEN1_BLUEPRINT_TARGET")


def build_outputs():
    variants = read_csv("airjet-simulation/parameters/p1_model_form_variants.csv")
    internal_rules = read_csv("airjet-simulation/parameters/p1_internal_geometry_rules.csv")
    layouts = read_csv("airjet-simulation/parameters/p1_layout_configuration_matrix.csv")
    orifices = read_csv("airjet-simulation/parameters/p1_orifice_pattern_candidates.csv")
    vents = read_csv("airjet-simulation/parameters/p1_vent_geometry_candidates.csv")
    exhausts = read_csv("airjet-simulation/parameters/p1_planform_exhaust_candidates.csv")
    if len(variants) != 9:
        raise ValueError("GEN1_VARIANT_COUNT")
    validate_variant_internal_rule_contract(variants, internal_rules)
    outputs = {}
    records = []
    blueprints = []
    for index, variant in enumerate(variants, 1):
        layout = selected_row(layouts, "configuration_id", variant["configuration_id"])
        orifice = selected_row(orifices, "pattern_id", variant["orifice_pattern_id"])
        selected_vents = selected_rows(vents, "candidate_set_id", variant["vent_candidate_set_id"])
        exhaust = selected_row(exhausts, "exhaust_branch_id", variant["exhaust_branch_id"])
        blueprint, summary, slug = build_blueprint(index, variant, layout, orifice, selected_vents, exhaust)
        blueprint_path = "airjet-simulation/automation/ansys/contracts/trusted_full_product_gen1/%s.json" % slug
        payload = json_bytes(blueprint)
        outputs[blueprint_path] = payload
        blueprints.append(blueprint)
        records.append({
            "source_variant_id": summary["source_variant_id"],
            "variant_id": summary["variant_id"],
            "configuration_id": summary["configuration_id"],
            "cell_count": summary["cell_count"],
            "semantic_entity_count": summary["semantic_entity_count"],
            "blueprint_path": blueprint_path,
            "blueprint_sha256": sha256_bytes(payload),
        })
    campaign = {
        "schema_version": 1,
        "contract_id": contract.CAMPAIGN_CONTRACT_ID,
        "scope": "FULL_PRODUCT",
        "product_id": PRODUCT_ID,
        "expected_variant_count": 9,
        "source_contracts": source_contracts(),
        "variant_contracts": records,
    }
    validate_gen1_target(campaign, blueprints)
    outputs["airjet-simulation/automation/ansys/contracts/trusted_full_product_gen1/campaign.json"] = json_bytes(campaign)
    return outputs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs = build_outputs()
    changed = []
    for git_path, payload in outputs.items():
        target = REPO / git_path
        if not target.is_file() or target.read_bytes() != payload:
            changed.append(git_path)
            if not args.check:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(payload)
    if args.check and changed:
        print("FULL_PRODUCT_TRUSTED_VARIANTS=FAIL stale=" + ",".join(changed))
        return 1
    print("FULL_PRODUCT_TRUSTED_VARIANTS=PASS product=AIRJET_MINI_GEN1 variants=9 mode=%s" % ("check" if args.check else "write"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

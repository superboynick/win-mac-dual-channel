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
)
REQUIRED_HASH_KEYS = tuple(["full_product_blueprint", "trusted_blueprint_file", "trusted_campaign"] + [item[0] for item in SOURCE_PATHS])


def read_csv(relative_path):
    with (REPO / relative_path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256_bytes(value):
    return hashlib.sha256(value).hexdigest()


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


def surface(namespace, name, feature_name, owner_key, cell_index, frame_id, centroid, bbox_min, bbox_max, geometry_type, normal, area, edge_count):
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
            "required_adjacent_keys": [owner_key],
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
    body_key = key(namespace, "body", "fluid_product")
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
            namespace, name, "vent.%03d" % number, body_key, None, "GLOBAL",
            [cx, cy, 2.8], [cx - half_x, cy - half_y, 2.799],
            [cx + half_x, cy + half_y, 2.801], "PLANAR_FACE",
            [0.0, 0.0, -1.0], length * width, 4,
        )
        surfaces.append(item)
        vent_keys.append(item["semantic_key"])

    outlet_width = float(exhaust["outlet_width_mm"])
    outlet_height = float(exhaust["outlet_height_mm"])
    outlet_x = float(exhaust["outlet_center_x_mm"])
    outlet_y = float(exhaust["outlet_y_mm"])
    outlet_z = heat_z + outlet_height / 2.0
    outlet = surface(
        namespace, "product_outlet", "product_outlet", body_key, None, "GLOBAL",
        [outlet_x, outlet_y, outlet_z],
        [outlet_x - outlet_width / 2.0, outlet_y - 0.001, heat_z],
        [outlet_x + outlet_width / 2.0, outlet_y + 0.001, heat_z + outlet_height],
        "PLANAR_FACE", [0.0, 1.0, 0.0], outlet_width * outlet_height, 4,
    )
    surfaces.append(outlet)
    heat_wall = outward_surface(
        namespace, "heat_wall", "heat_wall", body_key,
        [0.0, 0.0, heat_z], [-13.75, -20.75, heat_z - 0.001],
        [13.75, 20.75, heat_z + 0.001], 27.5 * 41.5,
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
            namespace, top_name, top_name, body_key, cell, frame_id,
            [0.0, 0.0, membrane_top_z],
            [-membrane / 2.0, -membrane / 2.0, membrane_top_z - 0.001],
            [membrane / 2.0, membrane / 2.0, membrane_top_z + 0.001],
            "PLANAR_FACE", [0.0, 0.0, -1.0], membrane * membrane, 4,
        )
        surfaces.append(top)
        membrane_top_keys.append(top["semantic_key"])
        bottom_name = "membrane_bottom.cell.%03d" % cell
        bottom = surface(
            namespace, bottom_name, bottom_name, body_key, cell, frame_id,
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
                    namespace, hole_name, hole_name, body_key, cell, frame_id,
                    [x, y, impingement_top_z],
                    [x - radius, y - radius, impingement_top_z - 0.001],
                    [x + radius, y + radius, impingement_top_z + 0.001],
                    "PLANAR_FACE", [0.0, 0.0, -1.0], math.pi * radius * radius, 1,
                )
                surfaces.append(hole)
                orifice_keys.append(hole["semantic_key"])

    surface_keys = [item["semantic_key"] for item in surfaces]
    body_centroid = [0.0, 0.0, (heat_z + body_top_z) / 2.0]
    body = {
        "semantic_key": body_key,
        "feature_key": key(namespace, "feature", "fluid_product"),
        "entity_kind": "BODY",
        "owner_key": None,
        "cell_index": None,
        "local_frame_id": "GLOBAL",
        "local_coordinates_mm": body_centroid,
        "geometry_type": "FLUID_BODY",
        "direction_constraint": direction("NOT_APPLICABLE", None, 0.0),
        "match_constraints": match(
            body_centroid, [-13.75, -20.75, heat_z], [13.75, 20.75, body_top_z],
            "NONE", None, None, None, "SOLID", None,
            measure_role="NOT_APPLICABLE", centroid_tolerance=0.05,
        ),
        "topology": {
            "required_adjacent_keys": surface_keys,
            "critical": True,
            "allow_isolated": False,
        },
        "expected_cardinality": 1,
    }
    entities = [body] + surfaces
    group_specs = (
        ("fluid_body", "FLUID_BODY", "BODY", [body_key], "fluid_bodies"),
        ("inlet", "INLET", "SURFACE", vent_keys, "fluid_boundaries"),
        ("outlet", "OUTLET", "SURFACE", [outlet["semantic_key"]], "fluid_boundaries"),
        ("membrane_top", "MEMBRANE_TOP", "SURFACE", membrane_top_keys, "fluid_boundaries"),
        ("membrane_bottom", "MEMBRANE_BOTTOM", "SURFACE", membrane_bottom_keys, "fluid_boundaries"),
        ("orifice_exit", "ORIFICE_EXIT", "SURFACE", orifice_keys, "fluid_boundaries"),
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
    body_group = groups[0]["group_key"]
    surface_group_keys = [item["group_key"] for item in groups[1:]]
    partitions = [
        {
            "partition_key": key(namespace, "partition", "fluid_bodies"),
            "entity_kind": "BODY", "group_keys": [body_group],
            "universe_keys": [body_key], "require_pairwise_disjoint": True,
            "require_full_coverage": True,
        },
        {
            "partition_key": key(namespace, "partition", "fluid_boundaries"),
            "entity_kind": "SURFACE", "group_keys": surface_group_keys,
            "universe_keys": surface_keys, "require_pairwise_disjoint": True,
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
        "expected_entity_cardinality": {"BODY": 1, "SURFACE": len(surface_keys)},
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
            "sha256": sha256_bytes((REPO / git_path).read_bytes()),
        })
    return records


def validate_gen1_target(campaign, blueprints):
    if campaign.get("product_id") != PRODUCT_ID or campaign.get("expected_variant_count") != 9:
        raise ValueError("GEN1_CAMPAIGN_TARGET")
    if len(blueprints) != 9:
        raise ValueError("GEN1_BLUEPRINT_COUNT")
    for blueprint in blueprints:
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
    layouts = read_csv("airjet-simulation/parameters/p1_layout_configuration_matrix.csv")
    orifices = read_csv("airjet-simulation/parameters/p1_orifice_pattern_candidates.csv")
    vents = read_csv("airjet-simulation/parameters/p1_vent_geometry_candidates.csv")
    exhausts = read_csv("airjet-simulation/parameters/p1_planform_exhaust_candidates.csv")
    if len(variants) != 9:
        raise ValueError("GEN1_VARIANT_COUNT")
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

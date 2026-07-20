# AJM-006 V03 full-product continuous-fluid SpaceClaim producer.
# This is a finite-throat geometry pilot only. It never claims a P1 gate pass.
from __future__ import print_function

import csv
import hashlib
import json
import math
import os
import traceback

from System import Array, Object, String, Type


job_dir = os.environ["AIRJET_JOB_DIR"]
dependency_dir = os.environ["AIRJET_PROFILE_DEPENDENCY_DIR"]
report_path = os.path.join(job_dir, "v03_continuous_fluid_producer.json")
authoring_path = os.path.join(job_dir, "v03_full_product_authoring.scdocx")
native_path = os.path.join(job_dir, "product_continuous_fluid.scdocx")
step_path = os.path.join(job_dir, "product_continuous_fluid.step")
native_reopen_path = os.path.join(job_dir, "v03_native_reopen.json")
step_reimport_path = os.path.join(job_dir, "v03_step_reimport.json")
inventory_path = os.path.join(job_dir, "v03_throat_inventory.json")
source_chain_path = os.path.join(job_dir, "v03_source_chain.json")

CAMPAIGN_REL = "airjet-simulation/automation/ansys/contracts/trusted_full_product_gen1/campaign.json"
VARIANT_ID = "M-3x4-7.0__R50_BALANCED"
DEPENDENCY_NAMES = (
    "full_product_semantic_contract_v1.py",
    "full_product_semantic_sidecar_v1.schema.json",
    "test_full_product_semantic_contract_v1.py",
    "build_full_product_trusted_variants.py",
    "test_full_product_trusted_variants.py",
    "p1_model_form_variants.csv",
    "p1_layout_configuration_matrix.csv",
    "p1_internal_geometry_rules.csv",
    "p1_cad_parameter_map.csv",
    "p1_orifice_pattern_candidates.csv",
    "p1_vent_geometry_candidates.csv",
    "p1_planform_exhaust_candidates.csv",
    "p1_thickness_budget.csv",
    "full_product_parameter_registry.csv",
    "v03_finite_throat_route_v1.json",
    "campaign.json",
    "variant_02_m_3x4_7_0_r50_balanced.json",
)

assertion_names = (
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
)
result_data = {
    "schema_version": 1,
    "task": "AJM006_V03_CONTINUOUS_FLUID_FULL_PRODUCT_PILOT",
    "probe": "v03_continuous_fluid_producer",
    "status": "FAIL_PRELIMINARY_GEOMETRY",
    "engineering_capability": "FAIL_PRELIMINARY_GEOMETRY",
    "pilot_result": "FAIL_V03_SINGLE_CONTINUOUS_FLUID_STEP_ROUND_TRIP",
    "claim_scope": "V03_CONTINUOUS_FLUID_GEOMETRY_PILOT_ONLY",
    "formal_006_completion": False,
    "p1_stage_gate": "NOT_RUN",
    "p1_p6_gates": "NOT_RUN",
    "full_variant_campaign": "NOT_RUN_1_OF_9_ONLY",
    "exact_product_geometry": "NOT_CLAIMED",
    "visibility": "NOT_USER_OBSERVED",
    "script_api": "V261",
    "license_arguments_added": False,
    "native_parameterization": "NOT_PROVEN",
    "external_native_attach": "NOT_PROVEN",
    "native_named_selection_transfer": "NOT_PROVEN",
    "trusted_production_profile_binding": "NOT_RUN_PRELIMINARY_PROFILE",
    "top_plenum_planform": "PRELIMINARY_CELL_FOOTPRINT_BLOCK_WITH_VENT_RISER_UNION",
    "formal_convex_hull_contract": "NOT_RUN",
    "mesh": "NOT_RUN",
    "physics": "NOT_RUN",
    "pyfluent": "NOT_RUN",
    "workbench": "NOT_RUN",
    "geometry_representation": (
        "SINGLE_CONTINUOUS_FLUID_BODY_WITH_972_EXPLICIT_FINITE_THROATS"
    ),
    "c016_candidate": {
        "parameter_id": "C016",
        "value_mm": 0.10,
        "range_mm": [0.05, 0.20],
        "evidence_class": "C",
        "status": "cad_placeholder",
        "product_fact": False,
        "uncertainty_scan": "REQUIRED_LATER_NOT_RUN",
    },
    "assertions": dict((name, False) for name in assertion_names),
}


def repo_path(relative_path):
    name = str(relative_path).replace("\\", "/").split("/")[-1]
    if name not in DEPENDENCY_NAMES:
        raise Exception("AJM006_UNDECLARED_DEPENDENCY:%s" % name)
    return os.path.join(dependency_dir, name)


def sha256_file(path, canonical_text=False):
    digest = hashlib.sha256()
    if canonical_text:
        with open(path, "rb") as handle:
            data = handle.read()
        # SpaceClaim V261 runs IronPython 2.7, where binary reads return a
        # character buffer compatible with str literals rather than CPython 3
        # bytes literals.  Keep this identical to the proven 005 hashing path.
        data = data.replace("\r\n", "\n")
        if "\r" in data:
            raise Exception("AJM006_BARE_CR:%s" % path)
        digest.update(data)
    else:
        with open(path, "rb") as handle:
            while True:
                chunk = handle.read(1024 * 1024)
                if not chunk:
                    break
                digest.update(chunk)
    return digest.hexdigest()


def read_json(path):
    with open(path, "r") as handle:
        return json.load(handle)


def read_csv(path):
    with open(path, "r") as handle:
        return list(csv.DictReader(handle))


def write_json(path, value):
    with open(path, "w") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)


def verify_dependency_bundle():
    manifest_path = os.path.join(dependency_dir, "dependency-manifest.json")
    manifest = read_json(manifest_path)
    if (
        manifest.get("schema_version") != 1
        or manifest.get("profile_id") != os.environ["AIRJET_PROFILE_ID"]
        or manifest.get("git_head") != os.environ["AIRJET_GIT_HEAD"]
    ):
        raise Exception("AJM006_DEPENDENCY_MANIFEST_IDENTITY")
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list):
        raise Exception("AJM006_DEPENDENCY_MANIFEST_ARTIFACTS")
    by_name = dict((item.get("relative_path"), item) for item in artifacts)
    if set(by_name) != set(DEPENDENCY_NAMES) or len(by_name) != len(artifacts):
        raise Exception("AJM006_DEPENDENCY_MANIFEST_SET")
    if set(os.listdir(dependency_dir)) != set(DEPENDENCY_NAMES) | {
        "dependency-manifest.json"
    }:
        raise Exception("AJM006_DEPENDENCY_DIRECTORY_SET")
    for name in DEPENDENCY_NAMES:
        path = os.path.join(dependency_dir, name)
        item = by_name[name]
        if (
            not os.path.isfile(path)
            or int(item.get("size", -1)) != int(os.path.getsize(path))
            or item.get("sha256") != sha256_file(path)
        ):
            raise Exception("AJM006_DEPENDENCY_HASH:%s" % name)
    return manifest_path


def mm(value):
    return MM(float(value))


def mm_value(value_in_meters):
    return float(value_in_meters) * 1000.0


def mm2_value(value_in_square_meters):
    return float(value_in_square_meters) * 1000000.0


def mm3_value(value_in_cubic_meters):
    return float(value_in_cubic_meters) * 1000000000.0


def close_enough(actual, expected, tolerance):
    return abs(float(actual) - float(expected)) <= float(tolerance)


def create_block(x0, y0, z0, x1, y1, z1, name):
    body = BlockBody.Create(
        Point.Create(mm(x0), mm(y0), mm(z0)),
        Point.Create(mm(x1), mm(y1), mm(z1)),
        ExtrudeType.ForceIndependent,
    ).CreatedBody
    body.Name = name
    return body


def create_cylinder(x, y, z0, z1, radius, name):
    safe_name = str(name).split("/")[-1].split("\\")[-1]
    body = CylinderBody.Create(
        Point.Create(mm(x), mm(y), mm(z0)),
        Point.Create(mm(x), mm(y), mm(z1)),
        Point.Create(mm(x + radius), mm(y), mm(z1)),
        ExtrudeType.ForceIndependent,
    ).CreatedBodies[0]
    body.Name = safe_name
    return body


def merge_into(target, tools, label):
    if not tools:
        return
    result = Combine.Merge(
        Selection.Create(target), Selection.Create(*tools)
    )
    if not bool(result.Success):
        raise Exception("AJM006_BOOLEAN_MERGE_FAILED:%s" % label)


def get_all_bodies_without_extension_binding(part):
    extension_type = Type.GetType(
        "SpaceClaim.Api.V261.Scripting.Extensions.PartExtensions, "
        "SpaceClaim.Api.V261.Scripting"
    )
    if extension_type is None:
        raise Exception("AJM006_PART_EXTENSIONS_NOT_LOADED")
    candidates = [
        method
        for method in extension_type.GetMethods()
        if method.Name == "GetAllBodies" and len(method.GetParameters()) == 1
    ]
    if len(candidates) != 1:
        raise Exception("AJM006_GET_ALL_BODIES_OVERLOAD")
    bodies = candidates[0].Invoke(None, Array[Object]([part]))
    return [body for body in bodies]


def body_fingerprint(body):
    occurrence_shape = body.Shape
    master = getattr(body, "Master", None)
    master_shape = getattr(master, "Shape", None) if master is not None else None
    topology_shape = master_shape if master_shape is not None else occurrence_shape
    box = occurrence_shape.GetBoundingBox(Matrix.Identity)
    piece_count = getattr(topology_shape, "PieceCount", None)
    is_closed = getattr(topology_shape, "IsClosed", None)
    is_manifold = getattr(topology_shape, "IsManifold", None)
    return {
        "name": body.Name,
        "bbox_min_mm": [
            mm_value(box.MinCorner.X), mm_value(box.MinCorner.Y),
            mm_value(box.MinCorner.Z),
        ],
        "bbox_max_mm": [
            mm_value(box.MaxCorner.X), mm_value(box.MaxCorner.Y),
            mm_value(box.MaxCorner.Z),
        ],
        "volume_mm3": mm3_value(occurrence_shape.Volume),
        "face_count": int(body.Faces.Count),
        "piece_count": int(piece_count) if piece_count is not None else None,
        "is_closed": bool(is_closed) if is_closed is not None else None,
        "is_manifold": bool(is_manifold) if is_manifold is not None else None,
    }


def fingerprint_deltas(expected, actual):
    if len(expected) != len(actual):
        return None
    expected_sorted = sorted(
        expected, key=lambda item: (item["bbox_min_mm"][2], item["bbox_max_mm"][2])
    )
    actual_sorted = sorted(
        actual, key=lambda item: (item["bbox_min_mm"][2], item["bbox_max_mm"][2])
    )
    bbox_deltas = []
    volume_deltas = []
    for left, right in zip(expected_sorted, actual_sorted):
        for key in ("bbox_min_mm", "bbox_max_mm"):
            for left_value, right_value in zip(left[key], right[key]):
                bbox_deltas.append(abs(float(left_value) - float(right_value)))
        volume_deltas.append(
            abs(float(left["volume_mm3"]) - float(right["volume_mm3"]))
        )
    return {
        "max_bbox_delta_mm": max(bbox_deltas),
        "max_volume_delta_mm3": max(volume_deltas),
    }


def fingerprints_equivalent(
    expected, actual, require_names, require_face_count,
    bbox_tolerance_mm=0.005, volume_absolute_tolerance_mm3=0.005,
    volume_relative_tolerance=1.0e-5,
):
    if len(expected) != len(actual):
        return False
    expected_sorted = sorted(
        expected, key=lambda item: (item["bbox_min_mm"][2], item["bbox_max_mm"][2])
    )
    actual_sorted = sorted(
        actual, key=lambda item: (item["bbox_min_mm"][2], item["bbox_max_mm"][2])
    )
    for left, right in zip(expected_sorted, actual_sorted):
        if require_names and str(left["name"]) != str(right["name"]):
            return False
        if require_face_count and int(left["face_count"]) != int(right["face_count"]):
            return False
        for key in ("bbox_min_mm", "bbox_max_mm"):
            for left_value, right_value in zip(left[key], right[key]):
                if not close_enough(
                    left_value, right_value, bbox_tolerance_mm
                ):
                    return False
        volume_scale = max(abs(float(left["volume_mm3"])), 1.0)
        if abs(float(left["volume_mm3"]) - float(right["volume_mm3"])) > max(
            volume_absolute_tolerance_mm3,
            volume_scale * volume_relative_tolerance,
        ):
            return False
    return True


def fingerprint_matches_route(
    fingerprint, route_geometry, bbox_tolerance_mm, volume_tolerance_mm3
):
    if not isinstance(fingerprint, dict):
        return False
    if (
        fingerprint.get("piece_count") != 1
        or not fingerprint.get("is_closed")
        or not fingerprint.get("is_manifold")
    ):
        return False
    for key in ("bbox_min_mm", "bbox_max_mm"):
        actual = fingerprint.get(key, [])
        expected = route_geometry.get(key, [])
        if len(actual) != 3 or len(expected) != 3:
            return False
        for actual_value, expected_value in zip(actual, expected):
            if not close_enough(
                actual_value, expected_value, bbox_tolerance_mm
            ):
                return False
    return close_enough(
        fingerprint.get("volume_mm3"),
        route_geometry.get("analytic_volume_mm3"),
        volume_tolerance_mm3,
    )


def face_fingerprint(face, body_name):
    box = face.Shape.GetBoundingBox(Matrix.Identity)
    center = box.Center
    edges = getattr(face, "Edges", None)
    edge_count = None
    if edges is not None:
        try:
            edge_count = int(edges.Count)
        except (AttributeError, TypeError):
            edge_count = None
    return {
        "body_name": body_name,
        "center_mm": [
            mm_value(center.X), mm_value(center.Y), mm_value(center.Z)
        ],
        "bbox_min_mm": [
            mm_value(box.MinCorner.X), mm_value(box.MinCorner.Y),
            mm_value(box.MinCorner.Z),
        ],
        "bbox_max_mm": [
            mm_value(box.MaxCorner.X), mm_value(box.MaxCorner.Y),
            mm_value(box.MaxCorner.Z),
        ],
        "area_mm2": mm2_value(face.Area),
        "edge_count": edge_count,
    }


def create_group(name, faces):
    if faces:
        FaceSelection.Create(faces).CreateAGroup(name)
    return len(faces)


def group_count(name):
    try:
        return int(Selection.CreateByGroups(Array[String]([name])).Count)
    except Exception:
        return 0


def xy_match_inventory(expected_xy, actual_xy, tolerance_mm):
    available = set(range(len(expected_xy)))
    matched = []
    unexpected = []
    max_delta = 0.0
    for actual_index, actual in enumerate(actual_xy):
        choices = []
        for expected_index in available:
            expected = expected_xy[expected_index]
            dx = abs(float(actual[0]) - float(expected[0]))
            dy = abs(float(actual[1]) - float(expected[1]))
            delta = max(dx, dy)
            if delta <= tolerance_mm:
                choices.append((delta, expected_index))
        if not choices:
            unexpected.append(actual)
            continue
        choices.sort()
        delta, expected_index = choices[0]
        available.remove(expected_index)
        max_delta = max(max_delta, delta)
        matched.append({
            "actual_index": actual_index,
            "expected_index": expected_index,
            "max_xy_delta_mm": delta,
        })
    return {
        "expected_count": len(expected_xy),
        "actual_count": len(actual_xy),
        "matched_count": len(matched),
        "missing_expected_xy": [expected_xy[index] for index in sorted(available)],
        "unexpected_actual_xy": unexpected,
        "max_xy_delta_mm": max_delta,
        "tolerance_mm": tolerance_mm,
        "one_to_one_complete": (
            len(expected_xy) == len(actual_xy) == len(matched)
            and not available
            and not unexpected
        ),
    }


def classify_throat_walls(
    body, expected_xy, throat_z_min, throat_z_max, radius,
    numerical_overlap_mm, xy_tolerance_mm, geometry_tolerance_mm,
    area_tolerance_mm2,
):
    effective_length = throat_z_max - throat_z_min
    construction_length = effective_length + 2.0 * numerical_overlap_mm
    expected_effective_area = 2.0 * math.pi * radius * effective_length
    expected_construction_area = (
        2.0 * math.pi * radius * construction_length
    )
    expected_diameter = 2.0 * radius
    expected_center_z = (throat_z_min + throat_z_max) / 2.0
    faces = []
    details = []
    actual_xy = []
    area_model_counts = {
        "EFFECTIVE_0P100_MM": 0,
        "CONSTRUCTION_OVERLAP_EXTENDED": 0,
        "STEP_KERNEL_OTHER_AREA": 0,
    }
    candidate_areas = []
    candidate_center_z = []
    candidate_edge_counts = {}
    for face in body.Faces:
        item = face_fingerprint(face, body.Name)
        center = item["center_mm"]
        near_expected_xy = any(
            max(
                abs(float(center[0]) - float(expected[0])),
                abs(float(center[1]) - float(expected[1])),
            ) <= xy_tolerance_mm
            for expected in expected_xy
        )
        area_model = None
        if close_enough(
            item["area_mm2"], expected_construction_area, area_tolerance_mm2
        ):
            area_model = "CONSTRUCTION_OVERLAP_EXTENDED"
        elif close_enough(
            item["area_mm2"], expected_effective_area, area_tolerance_mm2
        ):
            area_model = "EFFECTIVE_0P100_MM"
        if (
            near_expected_xy
            and close_enough(
                center[2], expected_center_z, geometry_tolerance_mm
            )
            and area_model is not None
            and item.get("edge_count") in (2, 4)
        ):
            item["accepted_area_model"] = area_model
            area_model_counts[area_model] += 1
            candidate_areas.append(float(item["area_mm2"]))
            candidate_center_z.append(float(center[2]))
            edge_key = str(item.get("edge_count"))
            candidate_edge_counts[edge_key] = (
                candidate_edge_counts.get(edge_key, 0) + 1
            )
            faces.append(face)
            details.append(item)
            actual_xy.append(item["center_mm"][:2])
    xy_inventory = xy_match_inventory(
        expected_xy, actual_xy, xy_tolerance_mm
    )
    return {
        "expected_radius_mm": radius,
        "expected_diameter_mm": expected_diameter,
        "expected_length_mm": effective_length,
        "expected_construction_length_mm": construction_length,
        "expected_effective_lateral_area_mm2": expected_effective_area,
        "expected_construction_lateral_area_mm2": expected_construction_area,
        "expected_center_z_mm": expected_center_z,
        "expected_z_min_mm": throat_z_min,
        "expected_z_max_mm": throat_z_max,
        "candidate_face_count": len(faces),
        "candidate_faces": details,
        "accepted_area_model_counts": area_model_counts,
        "observed_candidate_area_range_mm2": (
            [min(candidate_areas), max(candidate_areas)]
            if candidate_areas else None
        ),
        "observed_candidate_center_z_range_mm": (
            [min(candidate_center_z), max(candidate_center_z)]
            if candidate_center_z else None
        ),
        "observed_candidate_edge_count_histogram": candidate_edge_counts,
        "xy_inventory": xy_inventory,
        "geometry_tolerance_mm": geometry_tolerance_mm,
        "area_tolerance_mm2": area_tolerance_mm2,
        "pass": (
            len(faces) == 972
            and xy_inventory["one_to_one_complete"]
        ),
    }, faces


def compact_throat_inventory(value):
    if not isinstance(value, dict):
        return None
    xy = value.get("xy_inventory") or {}
    return {
        "expected_radius_mm": value.get("expected_radius_mm"),
        "expected_diameter_mm": value.get("expected_diameter_mm"),
        "expected_length_mm": value.get("expected_length_mm"),
        "expected_construction_length_mm": value.get(
            "expected_construction_length_mm"
        ),
        "expected_effective_lateral_area_mm2": value.get(
            "expected_effective_lateral_area_mm2"
        ),
        "expected_construction_lateral_area_mm2": value.get(
            "expected_construction_lateral_area_mm2"
        ),
        "expected_center_z_mm": value.get("expected_center_z_mm"),
        "expected_z_min_mm": value.get("expected_z_min_mm"),
        "expected_z_max_mm": value.get("expected_z_max_mm"),
        "candidate_face_count": value.get("candidate_face_count"),
        "accepted_area_model_counts": value.get(
            "accepted_area_model_counts"
        ),
        "observed_candidate_area_range_mm2": value.get(
            "observed_candidate_area_range_mm2"
        ),
        "observed_candidate_center_z_range_mm": value.get(
            "observed_candidate_center_z_range_mm"
        ),
        "observed_candidate_edge_count_histogram": value.get(
            "observed_candidate_edge_count_histogram"
        ),
        "geometry_tolerance_mm": value.get("geometry_tolerance_mm"),
        "area_tolerance_mm2": value.get("area_tolerance_mm2"),
        "xy_inventory": {
            "expected_count": xy.get("expected_count"),
            "actual_count": xy.get("actual_count"),
            "matched_count": xy.get("matched_count"),
            "missing_count": len(xy.get("missing_expected_xy") or []),
            "unexpected_count": len(xy.get("unexpected_actual_xy") or []),
            "max_xy_delta_mm": xy.get("max_xy_delta_mm"),
            "tolerance_mm": xy.get("tolerance_mm"),
            "one_to_one_complete": xy.get("one_to_one_complete"),
        },
        "pass": value.get("pass"),
    }


def expected_xy_contract(points, diameter_mm, step_xy_tolerance_mm):
    rounded = set(
        (round(float(point[0]), 9), round(float(point[1]), 9))
        for point in points
    )
    minimum_spacing = None
    for left_index in range(len(points)):
        left = points[left_index]
        for right_index in range(left_index + 1, len(points)):
            right = points[right_index]
            spacing = math.sqrt(
                (float(left[0]) - float(right[0])) ** 2
                + (float(left[1]) - float(right[1])) ** 2
            )
            if minimum_spacing is None or spacing < minimum_spacing:
                minimum_spacing = spacing
    required_minimum = diameter_mm + 2.0 * step_xy_tolerance_mm
    return {
        "expected_count": len(points),
        "unique_count_rounded_9dp": len(rounded),
        "minimum_center_spacing_mm": minimum_spacing,
        "required_minimum_center_spacing_mm": required_minimum,
        "step_xy_tolerance_mm": step_xy_tolerance_mm,
        "pass": (
            len(points) == 972
            and len(rounded) == len(points)
            and minimum_spacing is not None
            and minimum_spacing > required_minimum
        ),
    }


try:
    dependency_manifest_path = verify_dependency_bundle()
    route_path = repo_path(
        "airjet-simulation/automation/ansys/contracts/"
        "v03_finite_throat_route_v1.json"
    )
    route_contract = read_json(route_path)
    if (
        route_contract.get("contract_id")
        != "AJM006_GEN1_V03_FINITE_THROAT_ROUTE_V1"
        or route_contract.get("product_id") != "AIRJET_MINI_GEN1"
        or route_contract.get("configuration_id") != "M-3x4-7.0"
        or route_contract.get("source_variant_id") != VARIANT_ID
        or route_contract.get("representation")
        != "ONE_CONTINUOUS_FLUID_BODY_WITH_972_FINITE_CYLINDRICAL_THROATS"
    ):
        raise Exception("AJM006_V03_TRUSTED_ROUTE_IDENTITY")
    route_sources = route_contract.get("source_contracts", [])
    if len(route_sources) != 8:
        raise Exception("AJM006_V03_TRUSTED_ROUTE_SOURCE_COUNT")
    for source in route_sources:
        source_path = repo_path(source.get("git_path", ""))
        if sha256_file(source_path) != source.get("sha256"):
            raise Exception("AJM006_V03_TRUSTED_ROUTE_SOURCE_HASH")
    route_geometry = route_contract.get("geometry_contract", {})
    route_throats = route_contract.get("throat_contract", {})
    route_boundaries = route_contract.get("boundary_contract", {})
    if (
        route_throats.get("count") != 972
        or route_throats.get("count_per_cell") != 81
        or not close_enough(route_throats.get("diameter_mm"), 0.25, 1.0e-12)
        or not close_enough(route_throats.get("length_mm"), 0.10, 1.0e-12)
        or route_throats.get("axis") != [0.0, 0.0, 1.0]
        or route_geometry.get("body_count") != 1
        or route_geometry.get("piece_count") != 1
        or route_geometry.get("is_closed") is not True
        or route_geometry.get("is_manifold") is not True
        or route_boundaries != {
            "INLET": 4,
            "OUTLET": 1,
            "MEMBRANE_TOP": 12,
            "MEMBRANE_BOTTOM": 12,
            "ORIFICE_THROAT_WALL": 972,
            "HEAT_WALL": 1,
        }
    ):
        raise Exception("AJM006_V03_TRUSTED_ROUTE_GEOMETRY")
    campaign_path = repo_path(CAMPAIGN_REL)
    campaign = read_json(campaign_path)
    if campaign.get("product_id") != "AIRJET_MINI_GEN1":
        raise Exception("AJM006_CAMPAIGN_PRODUCT")
    records = [
        item for item in campaign.get("variant_contracts", [])
        if item.get("source_variant_id") == VARIANT_ID
    ]
    if len(records) != 1:
        raise Exception("AJM006_V03_CAMPAIGN_RECORD")
    record = records[0]
    blueprint_path = repo_path(record["blueprint_path"])
    if sha256_file(blueprint_path, True) != record["blueprint_sha256"]:
        raise Exception("AJM006_V03_BLUEPRINT_HASH")
    blueprint = read_json(blueprint_path)
    if (
        blueprint.get("product_id") != "AIRJET_MINI_GEN1"
        or blueprint.get("scope") != "FULL_PRODUCT"
        or blueprint.get("source_variant_id") != VARIANT_ID
        or blueprint.get("configuration", {}).get("expected_entity_cardinality", {}).get("BODY") != 2
    ):
        raise Exception("AJM006_V03_BLUEPRINT_IDENTITY")
    for source in campaign.get("source_contracts", []):
        source_path = repo_path(source["git_path"])
        if sha256_file(source_path, True) != source["sha256"]:
            raise Exception("AJM006_SOURCE_HASH:%s" % source["contract_key"])

    variants = read_csv(repo_path("airjet-simulation/parameters/p1_model_form_variants.csv"))
    variant = [item for item in variants if item["variant_id"] == VARIANT_ID]
    if len(variant) != 1 or variant[0].get("vent_riser_rule_id") != "VENT_RISER_CANDIDATE_R0":
        raise Exception("AJM006_V03_VARIANT_BINDING")
    variant = variant[0]
    layouts = read_csv(repo_path("airjet-simulation/parameters/p1_layout_configuration_matrix.csv"))
    layout = [item for item in layouts if item["configuration_id"] == variant["configuration_id"]][0]
    exhausts = read_csv(repo_path("airjet-simulation/parameters/p1_planform_exhaust_candidates.csv"))
    exhaust = [item for item in exhausts if item["exhaust_branch_id"] == variant["exhaust_branch_id"]][0]
    vents = read_csv(repo_path("airjet-simulation/parameters/p1_vent_geometry_candidates.csv"))
    vents = [item for item in vents if item["candidate_set_id"] == variant["vent_candidate_set_id"]]
    thickness_rows = read_csv(repo_path("airjet-simulation/parameters/p1_thickness_budget.csv"))
    thickness = dict((item["component"], item) for item in thickness_rows)
    registry_rows = read_csv(
        repo_path("airjet-simulation/parameters/full_product_parameter_registry.csv")
    )
    c016_registry_rows = [
        item for item in registry_rows if item.get("id") == "C016"
    ]
    cad_parameter_rows = read_csv(
        repo_path("airjet-simulation/parameters/p1_cad_parameter_map.csv")
    )
    c016_cad_rows = [
        item for item in cad_parameter_rows
        if item.get("variant_id") == VARIANT_ID
        and item.get("parameter_id") == "C016"
    ]

    cell_count = int(layout["cell_count"])
    nx = int(layout["nx"])
    ny = int(layout["ny"])
    membrane = float(layout["membrane_mm"])
    wall = float(layout["cell_wall_mm"])
    pitch = membrane + wall
    if cell_count != 12 or nx != 3 or ny != 4 or len(vents) != 4:
        raise Exception("AJM006_V03_FULL_PRODUCT_CARDINALITY")

    heat_z = float(thickness["IMPINGEMENT_CHANNEL"]["z_min_mm"])
    interface_z = float(thickness["IMPINGEMENT_CHANNEL"]["z_max_mm"])
    orifice_top_z = float(thickness["ORIFICE_PLATE"]["z_max_mm"])
    bottom_z_min = float(thickness["BOTTOM_CHAMBER"]["z_min_mm"])
    bottom_z_max = float(thickness["BOTTOM_CHAMBER"]["z_max_mm"])
    membrane_top_z = float(thickness["TOP_CHAMBER"]["z_min_mm"])
    plenum_top_z = float(thickness["TOP_CHAMBER"]["z_max_mm"])
    product_top_z = float(thickness["TOP_COVER"]["z_max_mm"])
    footprint_x_min = float(exhaust["cell_footprint_x_min_mm"])
    footprint_x_max = float(exhaust["cell_footprint_x_max_mm"])
    footprint_y_min = float(exhaust["cell_footprint_y_min_mm"])
    footprint_y_max = float(exhaust["cell_footprint_y_max_mm"])
    supported_plenum_y_min_mm = -17.750  # v2 corrected: extend plenum to fully support V01/V02
    manifold_y_max = float(exhaust["manifold_y_max_mm"])
    outlet_width = float(exhaust["outlet_width_mm"])
    radius = float(layout["orifice_diameter_candidate_mm"]) / 2.0
    numerical_overlap_mm = 0.02
    vent_riser_overlap_mm = 0.001
    perimeter_boolean_overlap_mm = 0.05
    perimeter_boolean_overlap_raw_mm3 = (
        cell_count
        * (
            8.0 * perimeter_boolean_overlap_mm * membrane
            - 4.0 * perimeter_boolean_overlap_mm ** 2
        )
        * (bottom_z_max - bottom_z_min)
    )
    if (
        not close_enough(
            route_geometry.get("perimeter_boolean_overlap_mm"),
            perimeter_boolean_overlap_mm,
            1.0e-12,
        )
        or not close_enough(
            route_geometry.get("perimeter_boolean_overlap_raw_mm3"),
            perimeter_boolean_overlap_raw_mm3,
            1.0e-12,
        )
        or route_geometry.get("perimeter_boolean_overlap_role")
        != "C5_BOOLEAN_ROBUSTNESS_DIAGNOSTIC_BOTTOM_TO_RING_INTERFACE"
        or route_geometry.get("perimeter_boolean_overlap_product_fact") is not False
    ):
        raise Exception("AJM006_V03_PERIMETER_BOOLEAN_OVERLAP_CONTRACT")
    throat_length_mm = orifice_top_z - interface_z
    c016_budget = thickness["ORIFICE_PLATE"]
    impingement_budget = thickness["IMPINGEMENT_CHANNEL"]
    bottom_chamber_budget = thickness["BOTTOM_CHAMBER"]
    expected_range_text = (
        "0.05-0.20 mm exploratory range; no direct Mini value"
    )
    c016_candidate_ok = (
        len(c016_registry_rows) == 1
        and len(c016_cad_rows) == 1
        and c016_budget.get("parameter_id") == "C016"
        and c016_budget.get("evidence_class") == "C"
        and c016_budget.get("status") == "cad_placeholder"
        and c016_budget.get("product_fact") == "false"
        and c016_budget.get("uncertainty_or_range") == expected_range_text
        and close_enough(c016_budget.get("thickness_mm"), 0.10, 1.0e-12)
        and close_enough(c016_budget.get("z_min_mm"), 1.5175, 1.0e-12)
        and close_enough(c016_budget.get("z_max_mm"), 1.6175, 1.0e-12)
        and close_enough(
            float(c016_budget.get("z_max_mm"))
            - float(c016_budget.get("z_min_mm")),
            float(c016_budget.get("thickness_mm")),
            1.0e-12,
        )
        and close_enough(
            impingement_budget.get("z_max_mm"),
            c016_budget.get("z_min_mm"),
            1.0e-12,
        )
        and close_enough(
            bottom_chamber_budget.get("z_min_mm"),
            c016_budget.get("z_max_mm"),
            1.0e-12,
        )
        and c016_registry_rows[0].get("evidence_class") == "C"
        and c016_registry_rows[0].get("status") == "cad_placeholder"
        and c016_registry_rows[0].get("adjustable") == "true"
        and c016_registry_rows[0].get("unit") == "mm"
        and c016_registry_rows[0].get("uncertainty_or_range")
        == expected_range_text
        and close_enough(c016_registry_rows[0].get("initial_value"), 0.10, 1.0e-12)
        and c016_cad_rows[0].get("evidence_class") == "C"
        and c016_cad_rows[0].get("status") == "cad_placeholder"
        and c016_cad_rows[0].get("product_fact") == "false"
        and c016_cad_rows[0].get("unit") == "mm"
        and c016_cad_rows[0].get("notes") == expected_range_text
        and close_enough(c016_cad_rows[0].get("value"), 0.10, 1.0e-12)
        and close_enough(throat_length_mm, 0.10, 1.0e-12)
    )
    if not c016_candidate_ok:
        raise Exception("AJM006_V03_C016_CANDIDATE_CONTRACT")

    frames = dict(
        (item["frame_id"], item) for item in blueprint["frames"]
    )
    groups = dict((item["solver_name"], item) for item in blueprint["groups"])
    entities = dict(
        (item["semantic_key"], item) for item in blueprint["entity_blueprints"]
    )
    orifice_entities = [entities[key] for key in groups["ORIFICE_EXIT"]["member_keys"]]
    if len(orifice_entities) != 972:
        raise Exception("AJM006_V03_ORIFICE_COUNT")
    circle_area = math.pi * radius * radius
    for entity in orifice_entities:
        match_constraints = entity.get("match_constraints", {})
        local = entity.get("local_coordinates_mm", [])
        if (
            entity.get("geometry_type") != "PLANAR_FACE"
            or len(local) != 3
            or not close_enough(local[2], interface_z, 1.0e-9)
            or match_constraints.get("measure_kind") != "AREA"
            or not close_enough(
                match_constraints.get("measure_value", -1.0), circle_area, 1.0e-9
            )
        ):
            raise Exception("AJM006_V03_ORIFICE_SIGNATURE")

    DocumentHelper.CreateNewDocument()
    upstream = create_block(
        footprint_x_min, supported_plenum_y_min_mm, membrane_top_z,
        footprint_x_max, footprint_y_max, plenum_top_z,
        "AJM006_V03_FLUID_UPSTREAM_BUILD",
    )

    risers = []
    vent_boxes = []
    for vent in sorted(vents, key=lambda item: item["vent_id"]):
        cx = float(vent["center_x_cad_mm"])
        cy = float(vent["center_y_cad_mm"])
        dx = float(vent["axis_dx_unit"])
        dy = float(vent["axis_dy_unit"])
        length = float(vent["axis_length_mm"])
        width = float(vent["slot_width_mm"])
        half_x = abs(dx) * length / 2.0 + abs(dy) * width / 2.0
        half_y = abs(dy) * length / 2.0 + abs(dx) * width / 2.0
        box = [cx - half_x, cy - half_y, cx + half_x, cy + half_y]
        vent_boxes.append(box)
        risers.append(create_block(
            box[0], box[1], plenum_top_z - vent_riser_overlap_mm,
            box[2], box[3], product_top_z,
            "AJM006_V03_RISER_%s" % vent["vent_id"],
        ))
    merge_into(upstream, risers, "VENT_RISERS")

    cell_origins = []
    for frame in blueprint["frames"]:
        if frame.get("cell_index") is not None:
            cell_origins.append((int(frame["cell_index"]), frame["frame_id"], frame["origin_mm"]))
    cell_origins.sort()
    if len(cell_origins) != cell_count:
        raise Exception("AJM006_V03_FRAME_COUNT")

    holes_by_cell = dict((index, []) for index in range(1, cell_count + 1))
    for entity in orifice_entities:
        holes_by_cell[int(entity["cell_index"])].append(entity)
    half_membrane = membrane / 2.0
    half_tile = pitch / 2.0
    expected_throat_xy = []
    for cell_index, frame_id, origin in cell_origins:
        cx = float(origin[0])
        cy = float(origin[1])
        pieces = [
            create_block(
                cx - half_membrane,
                cy - half_membrane,
                bottom_z_min,
                cx + half_membrane,
                cy + half_membrane,
                bottom_z_max,
                "AJM006_V03_BOTTOM_%03d" % cell_index,
            ),
            create_block(
                cx - half_tile, cy - half_tile, bottom_z_min,
                cx - half_membrane, cy + half_tile, plenum_top_z,
                "AJM006_V03_RING_L_%03d" % cell_index,
            ),
            create_block(
                cx + half_membrane, cy - half_tile, bottom_z_min,
                cx + half_tile, cy + half_tile, plenum_top_z,
                "AJM006_V03_RING_R_%03d" % cell_index,
            ),
            create_block(
                cx - half_membrane, cy - half_tile, bottom_z_min,
                cx + half_membrane, cy - half_membrane, plenum_top_z,
                "AJM006_V03_RING_B_%03d" % cell_index,
            ),
            create_block(
                cx - half_membrane, cy + half_membrane, bottom_z_min,
                cx + half_membrane, cy + half_tile, plenum_top_z,
                "AJM006_V03_RING_T_%03d" % cell_index,
            ),
            create_block(
                cx - half_membrane - perimeter_boolean_overlap_mm,
                cy - half_membrane,
                bottom_z_min,
                cx - half_membrane + perimeter_boolean_overlap_mm,
                cy + half_membrane,
                bottom_z_max,
                "AJM006_V03_BRIDGE_L_%03d" % cell_index,
            ),
            create_block(
                cx + half_membrane - perimeter_boolean_overlap_mm,
                cy - half_membrane,
                bottom_z_min,
                cx + half_membrane + perimeter_boolean_overlap_mm,
                cy + half_membrane,
                bottom_z_max,
                "AJM006_V03_BRIDGE_R_%03d" % cell_index,
            ),
            create_block(
                cx - half_membrane,
                cy - half_membrane - perimeter_boolean_overlap_mm,
                bottom_z_min,
                cx + half_membrane,
                cy - half_membrane + perimeter_boolean_overlap_mm,
                bottom_z_max,
                "AJM006_V03_BRIDGE_B_%03d" % cell_index,
            ),
            create_block(
                cx - half_membrane,
                cy + half_membrane - perimeter_boolean_overlap_mm,
                bottom_z_min,
                cx + half_membrane,
                cy + half_membrane + perimeter_boolean_overlap_mm,
                bottom_z_max,
                "AJM006_V03_BRIDGE_T_%03d" % cell_index,
            ),
        ]
        for entity in holes_by_cell[cell_index]:
            local = entity["local_coordinates_mm"]
            expected_throat_xy.append([
                cx + float(local[0]), cy + float(local[1])
            ])
            pieces.append(create_cylinder(
                cx + float(local[0]), cy + float(local[1]),
                interface_z - numerical_overlap_mm,
                orifice_top_z + numerical_overlap_mm,
                radius, entity["semantic_key"],
            ))
        merge_into(upstream, pieces, "CELL_%03d" % cell_index)

    if len(expected_throat_xy) != 972:
        raise Exception("AJM006_V03_EXPECTED_THROAT_XY_COUNT")
    expected_xy_evidence = expected_xy_contract(
        expected_throat_xy, 2.0 * radius, 0.02
    )
    if not expected_xy_evidence["pass"]:
        raise Exception("AJM006_V03_EXPECTED_THROAT_XY_CONTRACT")
    upstream.Name = "AJM006_V03_FLUID_UPSTREAM_PREMERGE"
    downstream = create_block(
        footprint_x_min, footprint_y_min, heat_z,
        footprint_x_max, manifold_y_max, interface_z,
        "AJM006_V03_FLUID_DOWNSTREAM_PREMERGE",
    )
    upstream_premerge_fp = body_fingerprint(upstream)
    downstream_premerge_fp = body_fingerprint(downstream)
    merge_into(upstream, [downstream], "V03_FULL_CONTINUOUS_FLUID")
    built_bodies = get_all_bodies_without_extension_binding(GetRootPart())
    if len(built_bodies) != 1:
        raise Exception("AJM006_V03_BOOLEAN_BODY_COUNT")
    fluid = built_bodies[0]
    fluid.Name = "AJM006_V03_FLUID_CONTINUOUS"
    continuous_fp = body_fingerprint(fluid)
    continuous_connectivity = (
        continuous_fp["piece_count"] == 1
        and continuous_fp["is_closed"]
        and continuous_fp["is_manifold"]
    )
    expected_overlap_volume_mm3 = (
        float(len(expected_throat_xy))
        * math.pi * radius * radius * numerical_overlap_mm
    )
    expected_union_volume_mm3 = (
        upstream_premerge_fp["volume_mm3"]
        + downstream_premerge_fp["volume_mm3"]
        - expected_overlap_volume_mm3
    )
    boolean_volume_delta_mm3 = abs(
        continuous_fp["volume_mm3"] - expected_union_volume_mm3
    )
    route_analytic_volume_mm3 = float(
        route_geometry["analytic_volume_mm3"]
    )
    native_route_volume_tolerance_mm3 = float(
        route_geometry["volume_tolerance_native_mm3"]
    )
    step_route_volume_tolerance_mm3 = float(
        route_geometry["volume_tolerance_step_mm3"]
    )
    native_analytic_volume_delta_mm3 = abs(
        continuous_fp["volume_mm3"] - route_analytic_volume_mm3
    )
    continuous_route_ok = fingerprint_matches_route(
        continuous_fp,
        route_geometry,
        float(route_geometry["bbox_tolerance_native_mm"]),
        native_route_volume_tolerance_mm3,
    )

    throat_inventory, throat_faces = classify_throat_walls(
        fluid,
        expected_throat_xy,
        interface_z,
        orifice_top_z,
        radius,
        numerical_overlap_mm,
        0.002,
        0.002,
        0.001,
    )
    inlet_faces = []
    outlet_faces = []
    membrane_top_faces = []
    membrane_bottom_faces = []
    heat_faces = []
    continuous_face_details = []
    for face in fluid.Faces:
        item = face_fingerprint(face, fluid.Name)
        center = item["center_mm"]
        area = item["area_mm2"]
        label = "WALL_CONTINUOUS_UNCLASSIFIED"
        if face in throat_faces:
            label = "ORIFICE_THROAT_WALL"
        elif close_enough(center[2], product_top_z, 0.002):
            inlet_faces.append(face)
            label = "INLET"
        elif close_enough(
            center[1], manifold_y_max, 0.002
        ) and close_enough(
            area, outlet_width * (interface_z - heat_z), 0.05
        ):
            outlet_faces.append(face)
            label = "OUTLET"
        elif close_enough(center[2], heat_z, 0.002):
            heat_faces.append(face)
            label = "HEAT_WALL"
        elif close_enough(
            center[2], membrane_top_z, 0.002
        ) and close_enough(area, membrane * membrane, 0.05):
            membrane_top_faces.append(face)
            label = "MEMBRANE_TOP"
        elif close_enough(
            center[2], bottom_z_max, 0.002
        ) and close_enough(area, membrane * membrane, 0.05):
            membrane_bottom_faces.append(face)
            label = "MEMBRANE_BOTTOM"
        item["classification"] = label
        continuous_face_details.append(item)

    Selection.Create(fluid).CreateAGroup("FLUID_CONTINUOUS")
    group_expected = {
        "INLET": create_group("INLET", inlet_faces),
        "OUTLET": create_group("OUTLET", outlet_faces),
        "MEMBRANE_TOP": create_group("MEMBRANE_TOP", membrane_top_faces),
        "MEMBRANE_BOTTOM": create_group("MEMBRANE_BOTTOM", membrane_bottom_faces),
        "ORIFICE_THROAT_WALL": create_group(
            "ORIFICE_THROAT_WALL", throat_faces
        ),
        "HEAT_WALL": create_group("HEAT_WALL", heat_faces),
    }
    group_observed = dict(
        (name, group_count(name))
        for name in ["FLUID_CONTINUOUS"] + list(group_expected.keys())
    )
    group_required = {
        "FLUID_CONTINUOUS": 1,
        "INLET": 4,
        "OUTLET": 1,
        "MEMBRANE_TOP": 12,
        "MEMBRANE_BOTTOM": 12,
        "ORIFICE_THROAT_WALL": 972,
        "HEAT_WALL": 1,
    }
    group_semantics_ok = group_observed == group_required
    throat_counts_by_cell = dict(
        (index, len(holes_by_cell[index]))
        for index in range(1, cell_count + 1)
    )
    all_cells_have_throats = (
        len(throat_counts_by_cell) == cell_count
        and set(throat_counts_by_cell.values()) == set([81])
    )

    envelope = create_block(
        -13.75, -20.75, 0.0, 13.75, 20.75, product_top_z,
        "ENVELOPE_27P5_41P5_2P8_REFERENCE_DO_NOT_SOLVE",
    )
    authoring_save = DocumentSave.Execute(authoring_path)
    Delete.Execute(Selection.Create(envelope))
    native_save = DocumentSave.Execute(native_path)
    step_save = DocumentSave.Execute(step_path)
    save_ok = all((
        bool(authoring_save.Success), bool(native_save.Success), bool(step_save.Success),
        os.path.isfile(authoring_path), os.path.isfile(native_path), os.path.isfile(step_path),
        os.path.getsize(authoring_path) > 0, os.path.getsize(native_path) > 0,
        os.path.getsize(step_path) > 0,
    ))

    native_save_ok = (
        bool(authoring_save.Success)
        and bool(native_save.Success)
        and os.path.isfile(authoring_path)
        and os.path.isfile(native_path)
        and os.path.getsize(authoring_path) > 0
        and os.path.getsize(native_path) > 0
    )
    step_export_ok = (
        bool(step_save.Success)
        and os.path.isfile(step_path)
        and os.path.getsize(step_path) > 0
    )
    inventory = {
        "schema_version": 1,
        "claim_scope": "V03_CONTINUOUS_FLUID_GEOMETRY_PILOT_ONLY",
        "source_variant_id": VARIANT_ID,
        "source_semantic_body_count": 2,
        "pilot_body_count": 1,
        "representation_change": "BOOLEAN_CONTINUOUS_FLUID",
        "premerge_body_fingerprints": [
            upstream_premerge_fp, downstream_premerge_fp
        ],
        "continuous_body_fingerprint": continuous_fp,
        "expected_overlap_volume_mm3": expected_overlap_volume_mm3,
        "perimeter_boolean_overlap_mm": perimeter_boolean_overlap_mm,
        "perimeter_boolean_overlap_raw_mm3": (
            perimeter_boolean_overlap_raw_mm3
        ),
        "perimeter_boolean_overlap_union_volume_delta_mm3": 0.0,
        "expected_union_volume_mm3": expected_union_volume_mm3,
        "boolean_volume_delta_mm3": boolean_volume_delta_mm3,
        "route_analytic_volume_mm3": route_analytic_volume_mm3,
        "native_analytic_volume_delta_mm3": (
            native_analytic_volume_delta_mm3
        ),
        "native_route_volume_tolerance_mm3": (
            native_route_volume_tolerance_mm3
        ),
        "c016_candidate": result_data["c016_candidate"],
        "trusted_route_path": route_path,
        "trusted_route_sha256": sha256_file(route_path),
        "expected_xy_contract": expected_xy_evidence,
        "throat_inventory": throat_inventory,
        "throat_counts_by_cell": throat_counts_by_cell,
        "all_cells_have_throats": all_cells_have_throats,
        "group_expected": group_expected,
        "group_required": group_required,
        "group_observed": group_observed,
        "continuous_faces": continuous_face_details,
        "formal_full_boundary_coverage": "NOT_EVALUATED",
    }
    write_json(inventory_path, inventory)

    DocumentHelper.CloseDocument()
    native_open = DocumentOpen.Execute(native_path)
    native_bodies = get_all_bodies_without_extension_binding(GetRootPart())
    native_fingerprints = [body_fingerprint(body) for body in native_bodies]
    native_throat_inventory = None
    native_throat_faces = []
    if len(native_bodies) == 1:
        native_throat_inventory, native_throat_faces = classify_throat_walls(
            native_bodies[0], expected_throat_xy, interface_z,
            orifice_top_z, radius, numerical_overlap_mm,
            0.002, 0.002, 0.001,
        )
    native_group_counts = dict(
        (name, group_count(name))
        for name in ["FLUID_CONTINUOUS"] + list(group_expected.keys())
    )
    native_reopen = {
        "open_success": bool(native_open.Success),
        "body_count": len(native_bodies),
        "body_fingerprints": native_fingerprints,
        "group_counts": native_group_counts,
        "throat_inventory": native_throat_inventory,
    }
    write_json(native_reopen_path, native_reopen)
    native_reopen_ok = (
        bool(native_open.Success)
        and len(native_bodies) == 1
        and native_fingerprints[0]["name"]
        == "AJM006_V03_FLUID_CONTINUOUS"
        and native_fingerprints[0]["piece_count"] == 1
        and native_fingerprints[0]["is_closed"]
        and native_fingerprints[0]["is_manifold"]
        and native_group_counts == group_observed
        and fingerprints_equivalent(
            [continuous_fp], native_fingerprints, True, True
        )
    )
    native_route_ok = (
        native_reopen_ok
        and fingerprint_matches_route(
            native_fingerprints[0],
            route_geometry,
            float(route_geometry["bbox_tolerance_native_mm"]),
            native_route_volume_tolerance_mm3,
        )
    )
    native_throat_ok = (
        isinstance(native_throat_inventory, dict)
        and native_throat_inventory["pass"]
        and native_throat_inventory["accepted_area_model_counts"] == {
            "EFFECTIVE_0P100_MM": 972,
            "CONSTRUCTION_OVERLAP_EXTENDED": 0,
            "STEP_KERNEL_OTHER_AREA": 0,
        }
    )

    DocumentHelper.CloseDocument()
    step_open = DocumentOpen.Execute(step_path)
    step_bodies = get_all_bodies_without_extension_binding(GetRootPart())
    step_fingerprints = [body_fingerprint(body) for body in step_bodies]
    step_throat_inventory = None
    step_throat_faces = []
    if len(step_bodies) == 1:
        step_throat_inventory, step_throat_faces = classify_throat_walls(
            step_bodies[0], expected_throat_xy, interface_z,
            orifice_top_z, radius, numerical_overlap_mm,
            0.02, 0.005, 0.001,
        )
    step_boundary_counts = {
        "INLET": 0,
        "OUTLET": 0,
        "MEMBRANE_TOP": 0,
        "MEMBRANE_BOTTOM": 0,
        "ORIFICE_THROAT_WALL": len(step_throat_faces),
        "HEAT_WALL": 0,
    }
    if len(step_bodies) == 1:
        for face in step_bodies[0].Faces:
            if face in step_throat_faces:
                continue
            item = face_fingerprint(face, step_bodies[0].Name)
            center = item["center_mm"]
            area = item["area_mm2"]
            if close_enough(center[2], product_top_z, 0.02):
                step_boundary_counts["INLET"] += 1
            elif close_enough(
                center[1], manifold_y_max, 0.02
            ) and close_enough(
                area, outlet_width * (interface_z - heat_z), 0.05
            ):
                step_boundary_counts["OUTLET"] += 1
            elif close_enough(center[2], heat_z, 0.02):
                step_boundary_counts["HEAT_WALL"] += 1
            elif close_enough(
                center[2], membrane_top_z, 0.02
            ) and close_enough(area, membrane * membrane, 0.05):
                step_boundary_counts["MEMBRANE_TOP"] += 1
            elif close_enough(
                center[2], bottom_z_max, 0.02
            ) and close_enough(area, membrane * membrane, 0.05):
                step_boundary_counts["MEMBRANE_BOTTOM"] += 1
    step_comparison_tolerances = {
        "bbox_tolerance_mm": 0.02,
        "volume_absolute_tolerance_mm3": 0.08,
        "volume_relative_tolerance": 1.0e-5,
        "face_count_required": False,
        "names_required": False,
        "throat_xy_tolerance_mm": 0.02,
        "comparison_basis": "INDEPENDENT_ROUTE_ANALYTIC",
        "native_to_step_volume_delta_diagnostic_only": True,
        "route_analytic_volume_tolerance_mm3": (
            step_route_volume_tolerance_mm3
        ),
    }
    step_reimport = {
        "route": "DOCUMENT_OPEN_AND_REFLECTION_GET_ALL_BODIES",
        "open_success": bool(step_open.Success),
        "body_count": len(step_bodies),
        "body_fingerprints": step_fingerprints,
        "comparison_tolerances": step_comparison_tolerances,
        "comparison_deltas": fingerprint_deltas(
            [continuous_fp], step_fingerprints
        ),
        "throat_inventory": step_throat_inventory,
        "boundary_counts": step_boundary_counts,
        "named_selections_expected_to_persist": False,
        "solver_import": "NOT_RUN",
    }
    write_json(step_reimport_path, step_reimport)
    step_reimport_ok = (
        bool(step_open.Success)
        and len(step_bodies) == 1
        and step_fingerprints[0]["piece_count"] == 1
        and step_fingerprints[0]["is_closed"]
        and step_fingerprints[0]["is_manifold"]
    )
    step_throat_ok = (
        isinstance(step_throat_inventory, dict)
        and step_throat_inventory["pass"]
        and step_throat_inventory["accepted_area_model_counts"] == {
            "EFFECTIVE_0P100_MM": 972,
            "CONSTRUCTION_OVERLAP_EXTENDED": 0,
            "STEP_KERNEL_OTHER_AREA": 0,
        }
        and step_boundary_counts == dict(
            (name, value) for name, value in group_required.items()
            if name != "FLUID_CONTINUOUS"
        )
    )
    round_trip_shape_ok = (
        step_reimport_ok
        and fingerprint_matches_route(
            step_fingerprints[0],
            route_geometry,
            float(route_geometry["bbox_tolerance_step_mm"]),
            step_route_volume_tolerance_mm3,
        )
    )
    step_analytic_volume_delta_mm3 = (
        abs(step_fingerprints[0]["volume_mm3"] - route_analytic_volume_mm3)
        if len(step_fingerprints) == 1 else None
    )

    actual_porosity_pct = (
        float(len(orifice_entities)) * circle_area
        / (float(cell_count) * membrane * membrane) * 100.0
    )
    result_data["identity"] = {
        "git_head": os.environ.get("AIRJET_GIT_HEAD"),
        "profile_id": os.environ.get("AIRJET_PROFILE_ID"),
        "profile_contract_sha256": os.environ.get("AIRJET_PROFILE_CONTRACT_SHA256"),
        "dependency_manifest_sha256": sha256_file(dependency_manifest_path),
        "script_sha256": os.environ.get("AIRJET_SCRIPT_SHA256"),
        "case_id": os.environ.get("AIRJET_CASE_ID"),
    }
    source_chain = {
        "schema_version": 1,
        "identity": result_data["identity"],
        "source_variant_id": VARIANT_ID,
        "source_semantic_body_count": 2,
        "pilot_body_count": 1,
        "representation_change": "BOOLEAN_CONTINUOUS_FLUID",
        "c016_candidate": result_data["c016_candidate"],
        "dependency_manifest_path": dependency_manifest_path,
        "dependency_manifest_sha256": sha256_file(dependency_manifest_path),
        "trusted_route_path": route_path,
        "trusted_route_sha256": sha256_file(route_path),
        "route_analytic_volume_mm3": route_analytic_volume_mm3,
    }
    write_json(source_chain_path, source_chain)
    result_data["geometry"] = {
        "configuration_id": variant["configuration_id"],
        "source_variant_id": VARIANT_ID,
        "cell_count": cell_count,
        "orifice_count": len(orifice_entities),
        "orifice_diameter_mm": 2.0 * radius,
        "throat_length_mm": throat_length_mm,
        "throat_length_range_mm": [0.05, 0.20],
        "throat_length_evidence_class": "C",
        "actual_membrane_area_porosity_pct": actual_porosity_pct,
        "candidate_target_porosity_pct": float(layout["open_area_candidate_pct"]),
        "candidate_target_minus_actual_porosity_pct": (
            float(layout["open_area_candidate_pct"]) - actual_porosity_pct
        ),
        "preferred_porosity_guard_pct": [8.0, 12.0],
        "numerical_overlap_mm": numerical_overlap_mm,
        "vent_riser_overlap_mm": vent_riser_overlap_mm,
        "perimeter_boolean_overlap_mm": perimeter_boolean_overlap_mm,
        "perimeter_boolean_overlap_raw_mm3": (
            perimeter_boolean_overlap_raw_mm3
        ),
        "perimeter_boolean_overlap_union_volume_delta_mm3": 0.0,
        "expected_overlap_volume_mm3": expected_overlap_volume_mm3,
        "expected_union_volume_mm3": expected_union_volume_mm3,
        "boolean_volume_delta_mm3": boolean_volume_delta_mm3,
        "route_analytic_volume_mm3": route_analytic_volume_mm3,
        "native_analytic_volume_delta_mm3": (
            native_analytic_volume_delta_mm3
        ),
        "native_route_volume_tolerance_mm3": (
            native_route_volume_tolerance_mm3
        ),
        "step_analytic_volume_delta_mm3": (
            step_analytic_volume_delta_mm3
        ),
        "step_route_volume_tolerance_mm3": (
            step_route_volume_tolerance_mm3
        ),
        "continuous_route_ok": continuous_route_ok,
        "native_route_ok": native_route_ok,
        "step_route_ok": round_trip_shape_ok,
        "premerge_upstream": upstream_premerge_fp,
        "premerge_downstream": downstream_premerge_fp,
        "continuous_before_save": continuous_fp,
        "group_counts": group_observed,
        "group_required": group_required,
        "group_semantics_ok": group_semantics_ok,
        "expected_xy_contract": expected_xy_evidence,
        "throat_inventory_before_save": compact_throat_inventory(
            throat_inventory
        ),
        "throat_counts_by_cell": throat_counts_by_cell,
        "all_cells_have_throats": all_cells_have_throats,
        "native_throat_inventory": compact_throat_inventory(
            native_throat_inventory
        ),
        "step_throat_inventory": compact_throat_inventory(
            step_throat_inventory
        ),
        "native_reopen_summary": {
            "open_success": bool(native_open.Success),
            "body_count": len(native_bodies),
            "body_fingerprint": (
                native_fingerprints[0] if len(native_fingerprints) == 1
                else None
            ),
            "group_counts": native_group_counts,
        },
        "step_reimport_summary": {
            "open_success": bool(step_open.Success),
            "body_count": len(step_bodies),
            "body_fingerprint": (
                step_fingerprints[0] if len(step_fingerprints) == 1
                else None
            ),
            "boundary_counts": step_boundary_counts,
            "comparison_tolerances": step_comparison_tolerances,
            "comparison_deltas": fingerprint_deltas(
                [continuous_fp], step_fingerprints
            ),
        },
        "step_boundary_counts": step_boundary_counts,
    }
    result_data["assertions"]["input_contract"] = True
    result_data["assertions"]["gen1_target"] = True
    result_data["assertions"]["preliminary_full_product_scope"] = (
        cell_count == 12
        and len(orifice_entities) == 972
        and len(cell_origins) == 12
        and group_semantics_ok
    )
    result_data["assertions"]["c016_candidate_boundary"] = c016_candidate_ok
    result_data["assertions"]["explicit_throat_construction"] = (
        throat_inventory["pass"]
        and throat_inventory["accepted_area_model_counts"] == {
            "EFFECTIVE_0P100_MM": 972,
            "CONSTRUCTION_OVERLAP_EXTENDED": 0,
            "STEP_KERNEL_OTHER_AREA": 0,
        }
        and expected_xy_evidence["pass"]
        and close_enough(throat_length_mm, 0.10, 1.0e-12)
        and close_enough(2.0 * radius, 0.25, 1.0e-12)
    )
    result_data["assertions"]["single_continuous_fluid_boolean"] = (
        len(built_bodies) == 1
        and continuous_connectivity
        and continuous_route_ok
    )
    result_data["assertions"]["native_save"] = native_save_ok
    result_data["assertions"]["native_reopen_single_body"] = native_route_ok
    result_data["assertions"]["native_throat_inventory"] = native_throat_ok
    result_data["assertions"]["step_export"] = step_export_ok
    result_data["assertions"]["step_reopen_single_body"] = step_reimport_ok
    result_data["assertions"]["step_throat_inventory"] = step_throat_ok
    result_data["assertions"]["complete_flow_path"] = (
        continuous_connectivity
        and all_cells_have_throats
        and throat_inventory["pass"]
        and group_observed["INLET"] == 4
        and group_observed["OUTLET"] == 1
    )
    result_data["assertions"]["round_trip_shape_fidelity"] = (
        native_route_ok and round_trip_shape_ok
    )
    result_data["assertions"]["claim_boundaries"] = (
        result_data["formal_006_completion"] is False
        and result_data["p1_stage_gate"] == "NOT_RUN"
        and result_data["p1_p6_gates"] == "NOT_RUN"
        and result_data["mesh"] == "NOT_RUN"
        and result_data["physics"] == "NOT_RUN"
        and result_data["pyfluent"] == "NOT_RUN"
        and result_data["workbench"] == "NOT_RUN"
        and result_data["exact_product_geometry"] == "NOT_CLAIMED"
        and result_data["c016_candidate"]["product_fact"] is False
    )
    result_data["assertions"]["physics_guards"] = (
        result_data["assertions"]["claim_boundaries"]
        and 8.0 <= actual_porosity_pct <= 12.0
    )

    files = {}
    for role, path in (
        ("authoring_native", authoring_path),
        ("continuous_native", native_path),
        ("continuous_step", step_path),
        ("native_reopen", native_reopen_path),
        ("step_reimport", step_reimport_path),
        ("throat_inventory", inventory_path),
        ("source_chain", source_chain_path),
    ):
        files[role] = {
            "path": path,
            "size": os.path.getsize(path),
            "sha256": sha256_file(path),
        }
    result_data["files"] = files
    result_data["assertions"]["artifact_hashes"] = len(files) == 7
    if all(result_data["assertions"].values()):
        result_data["status"] = "PASS_PARTIAL_CAD_CAPABILITY"
        result_data["engineering_capability"] = "PASS_PARTIAL_CAD_CAPABILITY"
        result_data["pilot_result"] = (
            "PASS_PRELIMINARY_V03_FINITE_THROAT_GEOMETRY"
        )
    else:
        result_data["error"] = "V03_CONTINUOUS_FLUID_ASSERTION_FAILED"
except Exception as error:
    result_data["error_type"] = type(error).__name__
    result_data["error"] = str(error)
    result_data["traceback"] = traceback.format_exc()

write_json(report_path, result_data)
if result_data["status"] != "PASS_PARTIAL_CAD_CAPABILITY":
    raise Exception("AJM006_V03_CONTINUOUS_FLUID_PRODUCER_FAILED")

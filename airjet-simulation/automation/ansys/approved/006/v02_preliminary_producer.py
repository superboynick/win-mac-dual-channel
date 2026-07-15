# AJM-006 V02 full-product preliminary two-zone SpaceClaim producer.
# This is a geometry/topology pilot only. It never claims a P1 stage-gate pass.
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
report_path = os.path.join(job_dir, "v02_preliminary_producer.json")
authoring_path = os.path.join(job_dir, "v02_full_product_authoring.scdocx")
native_path = os.path.join(job_dir, "product_two_zone.scdocx")
step_path = os.path.join(job_dir, "product.step")
native_reopen_path = os.path.join(job_dir, "native_reopen.json")
step_reimport_path = os.path.join(job_dir, "step_reimport.json")
inventory_path = os.path.join(job_dir, "v02_face_inventory.json")

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
    "campaign.json",
    "variant_02_m_3x4_7_0_r50_balanced.json",
)

assertion_names = (
    "input_contract",
    "gen1_target",
    "full_product_scope",
    "complete_flow_path",
    "two_fluid_zone",
    "native_save",
    "native_reopen",
    "step_export_reimport",
    "artifact_hashes",
    "physics_guards",
)
result_data = {
    "schema_version": 1,
    "task": "AJM006_V02_FULL_PRODUCT_PRELIMINARY_CAD",
    "probe": "v02_preliminary_producer",
    "status": "FAIL_PRELIMINARY_GEOMETRY",
    "engineering_capability": "FAIL_PRELIMINARY_GEOMETRY",
    "claim_scope": "V02_PRELIMINARY_GEOMETRY_ONLY",
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


def fingerprints_equivalent(expected, actual, require_names, require_face_count):
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
                if not close_enough(left_value, right_value, 0.005):
                    return False
        volume_scale = max(abs(float(left["volume_mm3"])), 1.0)
        if abs(float(left["volume_mm3"]) - float(right["volume_mm3"])) > max(
            0.005, volume_scale * 1.0e-5
        ):
            return False
    return True


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


try:
    dependency_manifest_path = verify_dependency_bundle()
    campaign_path = repo_path(CAMPAIGN_REL)
    campaign = read_json(campaign_path)
    if campaign.get("product_id") != "AIRJET_MINI_GEN1":
        raise Exception("AJM006_CAMPAIGN_PRODUCT")
    records = [
        item for item in campaign.get("variant_contracts", [])
        if item.get("source_variant_id") == VARIANT_ID
    ]
    if len(records) != 1:
        raise Exception("AJM006_V02_CAMPAIGN_RECORD")
    record = records[0]
    blueprint_path = repo_path(record["blueprint_path"])
    if sha256_file(blueprint_path, True) != record["blueprint_sha256"]:
        raise Exception("AJM006_V02_BLUEPRINT_HASH")
    blueprint = read_json(blueprint_path)
    if (
        blueprint.get("product_id") != "AIRJET_MINI_GEN1"
        or blueprint.get("scope") != "FULL_PRODUCT"
        or blueprint.get("source_variant_id") != VARIANT_ID
        or blueprint.get("configuration", {}).get("expected_entity_cardinality", {}).get("BODY") != 2
    ):
        raise Exception("AJM006_V02_BLUEPRINT_IDENTITY")
    for source in campaign.get("source_contracts", []):
        source_path = repo_path(source["git_path"])
        if sha256_file(source_path, True) != source["sha256"]:
            raise Exception("AJM006_SOURCE_HASH:%s" % source["contract_key"])

    variants = read_csv(repo_path("airjet-simulation/parameters/p1_model_form_variants.csv"))
    variant = [item for item in variants if item["variant_id"] == VARIANT_ID]
    if len(variant) != 1 or variant[0].get("vent_riser_rule_id") != "VENT_RISER_CANDIDATE_R0":
        raise Exception("AJM006_V02_VARIANT_BINDING")
    variant = variant[0]
    layouts = read_csv(repo_path("airjet-simulation/parameters/p1_layout_configuration_matrix.csv"))
    layout = [item for item in layouts if item["configuration_id"] == variant["configuration_id"]][0]
    exhausts = read_csv(repo_path("airjet-simulation/parameters/p1_planform_exhaust_candidates.csv"))
    exhaust = [item for item in exhausts if item["exhaust_branch_id"] == variant["exhaust_branch_id"]][0]
    vents = read_csv(repo_path("airjet-simulation/parameters/p1_vent_geometry_candidates.csv"))
    vents = [item for item in vents if item["candidate_set_id"] == variant["vent_candidate_set_id"]]
    thickness_rows = read_csv(repo_path("airjet-simulation/parameters/p1_thickness_budget.csv"))
    thickness = dict((item["component"], item) for item in thickness_rows)

    cell_count = int(layout["cell_count"])
    nx = int(layout["nx"])
    ny = int(layout["ny"])
    membrane = float(layout["membrane_mm"])
    wall = float(layout["cell_wall_mm"])
    pitch = membrane + wall
    if cell_count != 12 or nx != 3 or ny != 4 or len(vents) != 4:
        raise Exception("AJM006_V02_FULL_PRODUCT_CARDINALITY")

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
    manifold_y_max = float(exhaust["manifold_y_max_mm"])
    outlet_width = float(exhaust["outlet_width_mm"])
    radius = float(layout["orifice_diameter_candidate_mm"]) / 2.0
    numerical_overlap_mm = 0.001

    frames = dict(
        (item["frame_id"], item) for item in blueprint["frames"]
    )
    groups = dict((item["solver_name"], item) for item in blueprint["groups"])
    entities = dict(
        (item["semantic_key"], item) for item in blueprint["entity_blueprints"]
    )
    orifice_entities = [entities[key] for key in groups["ORIFICE_EXIT"]["member_keys"]]
    if len(orifice_entities) != 972:
        raise Exception("AJM006_V02_ORIFICE_COUNT")
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
            raise Exception("AJM006_V02_ORIFICE_SIGNATURE")

    DocumentHelper.CreateNewDocument()
    upstream = create_block(
        footprint_x_min, footprint_y_min, membrane_top_z,
        footprint_x_max, footprint_y_max, plenum_top_z,
        "AJM006_V02_FLUID_UPSTREAM",
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
            box[0], box[1], plenum_top_z - numerical_overlap_mm,
            box[2], box[3], product_top_z,
            "AJM006_V02_RISER_%s" % vent["vent_id"],
        ))
    merge_into(upstream, risers, "VENT_RISERS")

    cell_origins = []
    for frame in blueprint["frames"]:
        if frame.get("cell_index") is not None:
            cell_origins.append((int(frame["cell_index"]), frame["frame_id"], frame["origin_mm"]))
    cell_origins.sort()
    if len(cell_origins) != cell_count:
        raise Exception("AJM006_V02_FRAME_COUNT")

    holes_by_cell = dict((index, []) for index in range(1, cell_count + 1))
    for entity in orifice_entities:
        holes_by_cell[int(entity["cell_index"])].append(entity)
    half_membrane = membrane / 2.0
    half_tile = pitch / 2.0
    for cell_index, frame_id, origin in cell_origins:
        cx = float(origin[0])
        cy = float(origin[1])
        pieces = [
            create_block(
                cx - half_membrane, cy - half_membrane, bottom_z_min,
                cx + half_membrane, cy + half_membrane, bottom_z_max,
                "AJM006_V02_BOTTOM_%03d" % cell_index,
            ),
            create_block(
                cx - half_tile, cy - half_tile, bottom_z_min,
                cx - half_membrane, cy + half_tile, plenum_top_z,
                "AJM006_V02_RING_L_%03d" % cell_index,
            ),
            create_block(
                cx + half_membrane, cy - half_tile, bottom_z_min,
                cx + half_tile, cy + half_tile, plenum_top_z,
                "AJM006_V02_RING_R_%03d" % cell_index,
            ),
            create_block(
                cx - half_membrane, cy - half_tile, bottom_z_min,
                cx + half_membrane, cy - half_membrane, plenum_top_z,
                "AJM006_V02_RING_B_%03d" % cell_index,
            ),
            create_block(
                cx - half_membrane, cy + half_membrane, bottom_z_min,
                cx + half_membrane, cy + half_tile, plenum_top_z,
                "AJM006_V02_RING_T_%03d" % cell_index,
            ),
        ]
        for entity in holes_by_cell[cell_index]:
            local = entity["local_coordinates_mm"]
            pieces.append(create_cylinder(
                cx + float(local[0]), cy + float(local[1]),
                interface_z, orifice_top_z + numerical_overlap_mm,
                radius, entity["semantic_key"],
            ))
        merge_into(upstream, pieces, "CELL_%03d" % cell_index)

    upstream.Name = "AJM006_V02_FLUID_UPSTREAM"
    downstream = create_block(
        footprint_x_min, footprint_y_min, heat_z,
        footprint_x_max, manifold_y_max, interface_z,
        "AJM006_V02_FLUID_DOWNSTREAM",
    )

    share_topology = {"attempted": True, "success": False, "error": None}
    try:
        options = ShareTopologyOptions()
        shared = ShareTopology.FindAndFix(
            Selection.Create(upstream, downstream), options
        )
        if shared is not None:
            share_topology["success"] = bool(getattr(shared, "Success", False))
        else:
            share_topology["success"] = True
            share_topology["returned_none"] = True
    except NameError as share_name_error:
        share_topology["error"] = "ShareTopology_not_available:%s" % str(share_name_error)
    except Exception as share_error:
        share_topology["error"] = str(share_error)

    upstream_fp = body_fingerprint(upstream)
    downstream_fp = body_fingerprint(downstream)
    built_bodies = get_all_bodies_without_extension_binding(GetRootPart())
    upstream_connectivity = (
        upstream_fp["piece_count"] == 1
        and upstream_fp["is_closed"]
        and upstream_fp["is_manifold"]
    )
    downstream_connectivity = (
        downstream_fp["piece_count"] == 1
        and downstream_fp["is_closed"]
        and downstream_fp["is_manifold"]
    )

    inlet_faces = []
    membrane_top_faces = []
    membrane_bottom_faces = []
    orifice_faces = []
    upstream_face_details = []
    for face in upstream.Faces:
        item = face_fingerprint(face, upstream.Name)
        center = item["center_mm"]
        area = item["area_mm2"]
        label = "WALL_UPSTREAM_UNCLASSIFIED"
        if close_enough(center[2], product_top_z, 0.002):
            inlet_faces.append(face)
            label = "INLET"
        elif close_enough(center[2], interface_z, 0.002) and close_enough(area, circle_area, 0.002):
            orifice_faces.append(face)
            label = "ORIFICE_EXIT_UPSTREAM"
        elif close_enough(center[2], membrane_top_z, 0.002) and close_enough(area, membrane * membrane, 0.05):
            membrane_top_faces.append(face)
            label = "MEMBRANE_TOP"
        elif close_enough(center[2], bottom_z_max, 0.002) and close_enough(area, membrane * membrane, 0.05):
            membrane_bottom_faces.append(face)
            label = "MEMBRANE_BOTTOM"
        item["classification"] = label
        upstream_face_details.append(item)

    outlet_faces = []
    heat_faces = []
    downstream_orifice_candidates = []
    downstream_face_details = []
    for face in downstream.Faces:
        item = face_fingerprint(face, downstream.Name)
        center = item["center_mm"]
        area = item["area_mm2"]
        label = "WALL_DOWNSTREAM_UNCLASSIFIED"
        if close_enough(center[1], manifold_y_max, 0.002) and close_enough(area, outlet_width * (interface_z - heat_z), 0.05):
            outlet_faces.append(face)
            label = "OUTLET"
        elif close_enough(center[2], heat_z, 0.002):
            heat_faces.append(face)
            label = "HEAT_WALL"
        elif close_enough(center[2], interface_z, 0.002) and close_enough(area, circle_area, 0.002):
            downstream_orifice_candidates.append(face)
            label = "ORIFICE_ENTRY_DOWNSTREAM"
        item["classification"] = label
        downstream_face_details.append(item)

    Selection.Create(upstream).CreateAGroup("FLUID_UPSTREAM")
    Selection.Create(downstream).CreateAGroup("FLUID_DOWNSTREAM")
    group_expected = {
        "INLET": create_group("INLET", inlet_faces),
        "OUTLET": create_group("OUTLET", outlet_faces),
        "MEMBRANE_TOP": create_group("MEMBRANE_TOP", membrane_top_faces),
        "MEMBRANE_BOTTOM": create_group("MEMBRANE_BOTTOM", membrane_bottom_faces),
        "ORIFICE_EXIT_UPSTREAM": create_group("ORIFICE_EXIT_UPSTREAM", orifice_faces),
        "ORIFICE_ENTRY_DOWNSTREAM": create_group(
            "ORIFICE_ENTRY_DOWNSTREAM", downstream_orifice_candidates
        ),
        "HEAT_WALL": create_group("HEAT_WALL", heat_faces),
    }
    group_observed = dict(
        (name, group_count(name))
        for name in ["FLUID_UPSTREAM", "FLUID_DOWNSTREAM"] + list(group_expected.keys())
    )
    group_required = {
        "FLUID_UPSTREAM": 1,
        "FLUID_DOWNSTREAM": 1,
        "INLET": 4,
        "OUTLET": 1,
        "MEMBRANE_TOP": 12,
        "MEMBRANE_BOTTOM": 12,
        "ORIFICE_EXIT_UPSTREAM": 972,
        "ORIFICE_ENTRY_DOWNSTREAM": 972,
        "HEAT_WALL": 1,
    }
    group_semantics_ok = group_observed == group_required

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

    inventory = {
        "schema_version": 1,
        "claim_scope": "V02_PRELIMINARY_GEOMETRY_ONLY",
        "source_variant_id": VARIANT_ID,
        "body_fingerprints_before_save": [upstream_fp, downstream_fp],
        "share_topology_command": share_topology,
        "group_expected": group_expected,
        "group_required": group_required,
        "group_observed": group_observed,
        "upstream_faces": upstream_face_details,
        "downstream_faces": downstream_face_details,
        "downstream_orifice_candidates": len(downstream_orifice_candidates),
        "formal_full_boundary_coverage": "NOT_EVALUATED",
    }
    write_json(inventory_path, inventory)

    DocumentHelper.CloseDocument()
    DocumentOpen.Execute(native_path)
    native_bodies = get_all_bodies_without_extension_binding(GetRootPart())
    native_fingerprints = [body_fingerprint(body) for body in native_bodies]
    native_reopen = {
        "body_count": len(native_bodies),
        "body_fingerprints": native_fingerprints,
        "group_counts": dict(
            (name, group_count(name))
            for name in ["FLUID_UPSTREAM", "FLUID_DOWNSTREAM"] + list(group_expected.keys())
        ),
    }
    write_json(native_reopen_path, native_reopen)
    native_reopen_ok = (
        len(native_bodies) == 2
        and all(item["piece_count"] == 1 and item["is_closed"] and item["is_manifold"] for item in native_fingerprints)
        and native_reopen["group_counts"] == group_observed
        and fingerprints_equivalent(
            [upstream_fp, downstream_fp], native_fingerprints, True, True
        )
    )

    DocumentHelper.CloseDocument()
    DocumentOpen.Execute(step_path)
    step_bodies = get_all_bodies_without_extension_binding(GetRootPart())
    step_fingerprints = [body_fingerprint(body) for body in step_bodies]
    step_reimport = {
        "route": "DOCUMENT_OPEN_AND_REFLECTION_GET_ALL_BODIES",
        "body_count": len(step_bodies),
        "body_fingerprints": step_fingerprints,
        "named_selections_expected_to_persist": False,
        "shared_interface_identity": "NOT_EVALUATED_UNTIL_WORKBENCH_OBSERVER",
    }
    write_json(step_reimport_path, step_reimport)
    step_reimport_ok = (
        len(step_bodies) == 2
        and all(item["piece_count"] == 1 and item["is_closed"] and item["is_manifold"] for item in step_fingerprints)
        and fingerprints_equivalent(
            [upstream_fp, downstream_fp], step_fingerprints, False, False
        )
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
    result_data["geometry"] = {
        "configuration_id": variant["configuration_id"],
        "source_variant_id": VARIANT_ID,
        "cell_count": cell_count,
        "orifice_count": len(orifice_entities),
        "orifice_diameter_mm": 2.0 * radius,
        "actual_membrane_area_porosity_pct": actual_porosity_pct,
        "candidate_target_porosity_pct": float(layout["open_area_candidate_pct"]),
        "candidate_target_minus_actual_porosity_pct": (
            float(layout["open_area_candidate_pct"]) - actual_porosity_pct
        ),
        "preferred_porosity_guard_pct": [8.0, 12.0],
        "numerical_overlap_mm": numerical_overlap_mm,
        "upstream_before_save": upstream_fp,
        "downstream_before_save": downstream_fp,
        "share_topology_command": share_topology,
        "group_counts": group_observed,
        "group_required": group_required,
        "group_semantics_ok": group_semantics_ok,
        "downstream_orifice_candidates_before_step": len(downstream_orifice_candidates),
    }
    result_data["assertions"]["input_contract"] = True
    result_data["assertions"]["gen1_target"] = True
    result_data["assertions"]["full_product_scope"] = (
        cell_count == 12
        and len(orifice_entities) == 972
        and len(cell_origins) == 12
        and group_semantics_ok
    )
    result_data["assertions"]["complete_flow_path"] = (
        upstream_connectivity
        and downstream_connectivity
        and group_observed["INLET"] == 4
        and group_observed["OUTLET"] == 1
        and group_observed["ORIFICE_EXIT_UPSTREAM"] == 972
        and group_observed["ORIFICE_ENTRY_DOWNSTREAM"] == 972
    )
    result_data["assertions"]["two_fluid_zone"] = (
        len(built_bodies) == 2
        and upstream_connectivity
        and downstream_connectivity
        and group_observed["FLUID_UPSTREAM"] == 1
        and group_observed["FLUID_DOWNSTREAM"] == 1
    )
    result_data["assertions"]["native_save"] = save_ok
    result_data["assertions"]["native_reopen"] = native_reopen_ok
    result_data["assertions"]["step_export_reimport"] = step_reimport_ok
    result_data["assertions"]["physics_guards"] = (
        result_data["formal_006_completion"] is False
        and result_data["p1_stage_gate"] == "NOT_RUN"
        and result_data["p1_p6_gates"] == "NOT_RUN"
        and result_data["exact_product_geometry"] == "NOT_CLAIMED"
        and 8.0 <= actual_porosity_pct <= 12.0
    )

    files = {}
    for role, path in (
        ("authoring_native", authoring_path),
        ("two_zone_native", native_path),
        ("step", step_path),
        ("native_reopen", native_reopen_path),
        ("step_reimport", step_reimport_path),
        ("face_inventory", inventory_path),
    ):
        files[role] = {
            "path": path,
            "size": os.path.getsize(path),
            "sha256": sha256_file(path),
        }
    result_data["files"] = files
    result_data["assertions"]["artifact_hashes"] = len(files) == 6
    if all(result_data["assertions"].values()):
        result_data["status"] = "PASS_PARTIAL_CAD_CAPABILITY"
        result_data["engineering_capability"] = "PASS_PARTIAL_CAD_CAPABILITY"
    else:
        result_data["error"] = "PRELIMINARY_CAPABILITY_ASSERTION_FAILED"
except Exception as error:
    result_data["error_type"] = type(error).__name__
    result_data["error"] = str(error)
    result_data["traceback"] = traceback.format_exc()

write_json(report_path, result_data)
if result_data["status"] != "PASS_PARTIAL_CAD_CAPABILITY":
    raise Exception("AJM006_V02_PRELIMINARY_PRODUCER_FAILED")

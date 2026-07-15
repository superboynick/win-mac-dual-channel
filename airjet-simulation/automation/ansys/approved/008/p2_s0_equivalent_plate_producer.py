"""P2 S0 single-cell equivalent-plate geometry producer.

This is a calibration submodel for the complete AirJet Mini Gen1 candidate.
It does not identify the production membrane stack or complete P2.
"""

import csv
import hashlib
import json
import math
import os
import traceback

from System import Array, Object, String, Type


JOB_DIR = os.environ["AIRJET_JOB_DIR"]
DEPENDENCY_DIR = os.environ["AIRJET_PROFILE_DEPENDENCY_DIR"]
REPORT_PATH = os.path.join(JOB_DIR, "p2_s0_equivalent_plate_producer.json")
NATIVE_PATH = os.path.join(JOB_DIR, "p2_s0_equivalent_plate.scdocx")
STEP_PATH = os.path.join(JOB_DIR, "p2_s0_equivalent_plate.step")
SIDECAR_PATH = os.path.join(JOB_DIR, "p2_s0_equivalent_plate_sidecar.json")

CONTRACT_NAME = "p2_s0_equivalent_plate_v1.json"
MATERIAL_NAME = "p2_s0_equivalent_material_candidates.csv"
VARIANT_NAME = "variant_02_m_3x4_7_0_r50_balanced.json"
DEPENDENCY_NAMES = (
    "p2_s0_equivalent_plate_v1.json",
    "p2_s0_equivalent_material_candidates.csv",
    "variant_02_m_3x4_7_0_r50_balanced.json",
)

ASSERTION_NAMES = (
    "input_contract",
    "source_candidate_binding",
    "single_cell_calibration_scope",
    "evidence_class_guards",
    "equivalent_plate_geometry",
    "central_anchor_geometry",
    "free_perimeter_contract",
    "native_save",
    "native_reopen",
    "step_export",
    "step_reimport",
    "step_anchor_region_preserved",
    "step_semantic_sidecar",
    "artifact_hashes",
    "claim_boundaries",
    "physics_guards",
)

EXPECTED_BBOX_MIN_MM = [-3.5, -3.5, -0.05]
EXPECTED_BBOX_MAX_MM = [3.5, 3.5, 0.275]
EXPECTED_VOLUME_MM3 = 13.728125
EXPECTED_ROLE_COUNTS = {
    "NS_EQ_BODY": 1,
    "NS_ANCHOR_FIXED": 1,
    "NS_MEMBRANE_TOP": 1,
    "NS_MEMBRANE_ALL": 1,
    "NS_TIP_X_PLUS": 1,
    "NS_TIP_X_MINUS": 1,
}
EXPECTED_MATERIAL_ROWS = [
    {
        "candidate_id": "EQ-A-Z005",
        "youngs_modulus_GPa": "70",
        "poissons_ratio": "0.30",
        "density_kg_m3": "7800",
        "damping_ratio": "0.005",
        "evidence_class": "C",
        "status": "engineering_sensitivity_candidate",
        "source_logic": "low_stiffness_bracket_with_density_held_fixed",
        "product_fact": "false",
        "allowed_claim": "equivalent_property_sensitivity_only",
    },
    {
        "candidate_id": "EQ-B-Z015",
        "youngs_modulus_GPa": "120",
        "poissons_ratio": "0.30",
        "density_kg_m3": "7800",
        "damping_ratio": "0.015",
        "evidence_class": "C",
        "status": "engineering_sensitivity_candidate",
        "source_logic": "mid_stiffness_and_damping_bracket_with_density_held_fixed",
        "product_fact": "false",
        "allowed_claim": "equivalent_property_sensitivity_only",
    },
    {
        "candidate_id": "EQ-C-Z030",
        "youngs_modulus_GPa": "200",
        "poissons_ratio": "0.30",
        "density_kg_m3": "7800",
        "damping_ratio": "0.030",
        "evidence_class": "C",
        "status": "engineering_sensitivity_candidate",
        "source_logic": "high_stiffness_and_damping_bracket_with_density_held_fixed",
        "product_fact": "false",
        "allowed_claim": "equivalent_property_sensitivity_only",
    },
]

result_data = {
    "schema_version": 1,
    "task": "AJM_P2_S0_EQUIVALENT_PLATE_GEOMETRY_PRODUCER",
    "probe": "p2_s0_equivalent_plate_producer",
    "status": "FAIL_DIRECT",
    "engineering_capability": "FAIL_DIRECT",
    "pilot_result": "NOT_RUN",
    "claim_ceiling": "PASS_PRE_GATE_P2_S0_EQUIVALENT_PLATE_BASELINE",
    "claim_scope": "P2_S0_EQUIVALENT_PLATE_CAD_PILOT_ONLY",
    "p2_activity_status": "PRE_GATE_BASELINE_ONLY",
    "formal_p2_completion": False,
    "formal_p2_gate": "NOT_RUN",
    "p1_stage_gate": "NOT_RUN",
    "p2_stage_gate": "NOT_RUN",
    "p3_stage_gate": "NOT_RUN",
    "p1_p6_gates": "NOT_RUN",
    "product_id": "AIRJET_MINI_GEN1",
    "source_variant_id": "M-3x4-7.0__R50_BALANCED",
    "source_configuration_id": "AJM006_GEN1_CFG_M-3x4-7.0",
    "source_cell_id": "CELL_005",
    "p1_geometry_extraction": "NOT_PROVEN",
    "exact_product_geometry": "NOT_CLAIMED",
    "product_material_identification": "NOT_CLAIMED",
    "mechanical": "NOT_RUN",
    "script_api": "V261",
    "physics": "NOT_RUN",
    "mesh": "NOT_RUN",
    "modal": "NOT_RUN",
    "harmonic": "NOT_RUN",
    "piezoelectric_coupling": "NOT_RUN",
    "fsi": "NOT_RUN",
    "visibility": "NOT_USER_OBSERVED",
    "license_arguments_added": False,
    "assertions": dict((name, False) for name in ASSERTION_NAMES),
    "identity": {
        "git_head": os.environ.get("AIRJET_GIT_HEAD"),
        "profile_id": os.environ.get("AIRJET_PROFILE_ID"),
        "profile_contract_sha256": os.environ.get(
            "AIRJET_PROFILE_CONTRACT_SHA256"
        ),
        "dependency_manifest_sha256": None,
        "script_sha256": os.environ.get("AIRJET_SCRIPT_SHA256"),
        "case_id": os.environ.get("AIRJET_CASE_ID"),
    },
}


def sha256_file(path):
    digest = hashlib.sha256()
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
    manifest_path = os.path.join(DEPENDENCY_DIR, "dependency-manifest.json")
    manifest = read_json(manifest_path)
    if (
        manifest.get("schema_version") != 1
        or manifest.get("profile_id") != os.environ["AIRJET_PROFILE_ID"]
        or manifest.get("git_head") != os.environ["AIRJET_GIT_HEAD"]
    ):
        raise Exception("AJM_P2_S0_DEPENDENCY_MANIFEST_IDENTITY")
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list):
        raise Exception("AJM_P2_S0_DEPENDENCY_MANIFEST_ARTIFACTS")
    by_name = dict((item.get("relative_path"), item) for item in artifacts)
    if set(by_name) != set(DEPENDENCY_NAMES) or len(by_name) != len(artifacts):
        raise Exception("AJM_P2_S0_DEPENDENCY_MANIFEST_SET")
    expected_files = set(DEPENDENCY_NAMES) | set(["dependency-manifest.json"])
    if set(os.listdir(DEPENDENCY_DIR)) != expected_files:
        raise Exception("AJM_P2_S0_DEPENDENCY_DIRECTORY_SET")
    for name in DEPENDENCY_NAMES:
        path = os.path.join(DEPENDENCY_DIR, name)
        item = by_name[name]
        if (
            not os.path.isfile(path)
            or int(item.get("size", -1)) != int(os.path.getsize(path))
            or item.get("sha256") != sha256_file(path)
        ):
            raise Exception("AJM_P2_S0_DEPENDENCY_HASH:%s" % name)
    return manifest_path


def mm(value):
    return MM(float(value))


def mm_value(value):
    return float(value) * 1000.0


def mm2_value(value):
    return float(value) * 1000000.0


def mm3_value(value):
    return float(value) * 1000000000.0


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


def get_all_bodies(part):
    extension_type = Type.GetType(
        "SpaceClaim.Api.V261.Scripting.Extensions.PartExtensions, "
        "SpaceClaim.Api.V261.Scripting"
    )
    if extension_type is None:
        raise Exception("AJM_P2_S0_PART_EXTENSIONS_NOT_LOADED")
    candidates = [
        method
        for method in extension_type.GetMethods()
        if method.Name == "GetAllBodies" and len(method.GetParameters()) == 1
    ]
    if len(candidates) != 1:
        raise Exception("AJM_P2_S0_GET_ALL_BODIES_OVERLOAD")
    bodies = candidates[0].Invoke(None, Array[Object]([part]))
    return [body for body in bodies]


def body_fingerprint(body):
    occurrence = body.Shape
    master = getattr(body, "Master", None)
    master_shape = getattr(master, "Shape", None) if master is not None else None
    topology = master_shape if master_shape is not None else occurrence
    box = occurrence.GetBoundingBox(Matrix.Identity)
    return {
        "name": body.Name,
        "bbox_min_mm": [
            mm_value(box.MinCorner.X),
            mm_value(box.MinCorner.Y),
            mm_value(box.MinCorner.Z),
        ],
        "bbox_max_mm": [
            mm_value(box.MaxCorner.X),
            mm_value(box.MaxCorner.Y),
            mm_value(box.MaxCorner.Z),
        ],
        "volume_mm3": mm3_value(occurrence.Volume),
        "face_count": int(body.Faces.Count),
        "piece_count": int(getattr(topology, "PieceCount", -1)),
        "is_closed": bool(getattr(topology, "IsClosed", False)),
        "is_manifold": bool(getattr(topology, "IsManifold", False)),
    }


def face_fingerprint(face):
    box = face.Shape.GetBoundingBox(Matrix.Identity)
    center = box.Center
    return {
        "center_mm": [
            mm_value(center.X), mm_value(center.Y), mm_value(center.Z)
        ],
        "bbox_min_mm": [
            mm_value(box.MinCorner.X),
            mm_value(box.MinCorner.Y),
            mm_value(box.MinCorner.Z),
        ],
        "bbox_max_mm": [
            mm_value(box.MaxCorner.X),
            mm_value(box.MaxCorner.Y),
            mm_value(box.MaxCorner.Z),
        ],
        "area_mm2": mm2_value(face.Area),
    }


def vector_close(actual, expected, tolerance):
    return len(actual) == len(expected) and all(
        close_enough(left, right, tolerance)
        for left, right in zip(actual, expected)
    )


def classify_faces(body, tolerance_mm, area_tolerance_mm2):
    roles = dict(
        (name, [])
        for name in (
            "NS_ANCHOR_FIXED",
            "NS_MEMBRANE_TOP",
            "NS_TIP_X_PLUS",
            "NS_TIP_X_MINUS",
        )
    )
    details = []
    for face in body.Faces:
        item = face_fingerprint(face)
        role = "UNCLASSIFIED"
        if (
            vector_close(item["bbox_min_mm"], [-1.125, -1.125, -0.05], tolerance_mm)
            and vector_close(item["bbox_max_mm"], [1.125, 1.125, -0.05], tolerance_mm)
            and close_enough(item["area_mm2"], 5.0625, area_tolerance_mm2)
        ):
            role = "NS_ANCHOR_FIXED"
        elif (
            vector_close(item["bbox_min_mm"], [-3.5, -3.5, 0.275], tolerance_mm)
            and vector_close(item["bbox_max_mm"], [3.5, 3.5, 0.275], tolerance_mm)
            and close_enough(item["area_mm2"], 49.0, area_tolerance_mm2)
        ):
            role = "NS_MEMBRANE_TOP"
        elif (
            vector_close(item["bbox_min_mm"], [3.5, -3.5, 0.0], tolerance_mm)
            and vector_close(item["bbox_max_mm"], [3.5, 3.5, 0.275], tolerance_mm)
            and close_enough(item["area_mm2"], 1.925, area_tolerance_mm2)
        ):
            role = "NS_TIP_X_PLUS"
        elif (
            vector_close(item["bbox_min_mm"], [-3.5, -3.5, 0.0], tolerance_mm)
            and vector_close(item["bbox_max_mm"], [-3.5, 3.5, 0.275], tolerance_mm)
            and close_enough(item["area_mm2"], 1.925, area_tolerance_mm2)
        ):
            role = "NS_TIP_X_MINUS"
        if role in roles:
            roles[role].append(face)
        item["role"] = role
        details.append(item)
    return roles, details


def geometry_valid(body, bbox_tolerance_mm, volume_tolerance_mm3):
    fingerprint = body_fingerprint(body)
    roles, details = classify_faces(
        body, bbox_tolerance_mm, max(volume_tolerance_mm3, 0.005)
    )
    role_counts = dict((name, len(faces)) for name, faces in roles.items())
    valid = (
        fingerprint["piece_count"] == 1
        and fingerprint["is_closed"]
        and fingerprint["is_manifold"]
        and vector_close(
            fingerprint["bbox_min_mm"], EXPECTED_BBOX_MIN_MM, bbox_tolerance_mm
        )
        and vector_close(
            fingerprint["bbox_max_mm"], EXPECTED_BBOX_MAX_MM, bbox_tolerance_mm
        )
        and close_enough(
            fingerprint["volume_mm3"], EXPECTED_VOLUME_MM3, volume_tolerance_mm3
        )
        and role_counts
        == {
            "NS_ANCHOR_FIXED": 1,
            "NS_MEMBRANE_TOP": 1,
            "NS_TIP_X_PLUS": 1,
            "NS_TIP_X_MINUS": 1,
        }
    )
    return valid, fingerprint, roles, details


def group_count(name):
    return int(Selection.CreateByGroups(Array[String]([name])).Count)


def create_face_group(name, faces):
    if len(faces) != 1:
        raise Exception("AJM_P2_S0_ROLE_CARDINALITY:%s:%s" % (name, len(faces)))
    FaceSelection.Create(faces).CreateAGroup(name)


try:
    dependency_manifest_path = verify_dependency_bundle()
    result_data["identity"]["dependency_manifest_sha256"] = sha256_file(
        dependency_manifest_path
    )
    contract_path = os.path.join(DEPENDENCY_DIR, CONTRACT_NAME)
    material_path = os.path.join(DEPENDENCY_DIR, MATERIAL_NAME)
    variant_path = os.path.join(DEPENDENCY_DIR, VARIANT_NAME)
    contract = read_json(contract_path)
    materials = read_csv(material_path)
    variant = read_json(variant_path)

    if (
        contract.get("case_id") != os.environ["AIRJET_CASE_ID"]
        or contract.get("product_id") != result_data["product_id"]
        or contract.get("source_variant_id") != result_data["source_variant_id"]
        or contract.get("source_configuration_id")
        != result_data["source_configuration_id"]
        or contract.get("formal_p2_gate") != "NOT_RUN"
        or contract.get("p1_p6_gates") != "NOT_RUN"
        or contract.get("claim_ceiling") != result_data["claim_ceiling"]
        or contract.get("semantic_roles") != EXPECTED_ROLE_COUNTS
        or contract.get("source_cell", {}).get("frame_origin_mm")
        != [0.0, -3.625, 0.0]
    ):
        raise Exception("AJM_P2_S0_INPUT_CONTRACT_IDENTITY")
    result_data["assertions"]["input_contract"] = True

    source_frames = dict((item.get("frame_id"), item) for item in variant["frames"])
    source_cell = source_frames.get(result_data["source_cell_id"])
    if (
        variant.get("product_id") != result_data["product_id"]
        or variant.get("source_variant_id") != result_data["source_variant_id"]
        or variant.get("configuration", {}).get("configuration_id")
        != result_data["source_configuration_id"]
        or source_cell is None
        or source_cell.get("origin_mm") != [0.0, -3.625, 0.0]
        or source_cell.get("axes")
        != [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
    ):
        raise Exception("AJM_P2_S0_SOURCE_BINDING")
    result_data["assertions"]["source_candidate_binding"] = True
    result_data["assertions"]["single_cell_calibration_scope"] = (
        contract.get("source_cell", {}).get("cell_id") == "CELL_005"
        and contract.get("source_cell", {}).get("local_model_origin_reset") is True
    )

    geometry_contract = contract["geometry"]
    anchor_contract = geometry_contract["anchor"]
    if (
        geometry_contract.get("plate_side_mm") != 7.0
        or geometry_contract.get("plate_thickness", {}).get("value_mm") != 0.275
        or geometry_contract.get("expected_bbox_min_mm") != EXPECTED_BBOX_MIN_MM
        or geometry_contract.get("expected_bbox_max_mm") != EXPECTED_BBOX_MAX_MM
        or geometry_contract.get("expected_union_volume_mm3") != EXPECTED_VOLUME_MM3
        or anchor_contract.get("width_mm") != 2.25
        or anchor_contract.get("depth_mm") != 0.05
        or anchor_contract.get("boolean_overlap_mm") != 0.001
        or geometry_contract.get("step_named_selection_transfer") != "NOT_ASSUMED"
        or geometry_contract.get("perimeter_constraint")
        != "FREE_NO_CAD_CONSTRAINT_DEFINED"
        or contract.get("material_contract", {}).get("candidate_table")
        != "airjet-simulation/parameters/p2_s0_equivalent_material_candidates.csv"
        or contract.get("material_contract", {}).get("design")
        != "paired_candidate_bundle_not_factorial"
        or contract.get("material_contract", {}).get("required_evidence_class") != "C"
    ):
        raise Exception("AJM_P2_S0_CONTRACT_VALUE_DRIFT")
    result_data["assertions"]["evidence_class_guards"] = (
        geometry_contract["plate_thickness"]["product_fact"] is False
        and anchor_contract["evidence_class"] == "C"
        and anchor_contract["product_fact"] is False
        and anchor_contract["status"] == "topology_placeholder"
        and materials == EXPECTED_MATERIAL_ROWS
    )
    result_data["assertions"]["free_perimeter_contract"] = (
        geometry_contract["perimeter_constraint"]
        == "FREE_NO_CAD_CONSTRAINT_DEFINED"
    )
    result_data["material_boundary"] = {
        "design": contract["material_contract"]["design"],
        "interpretation": contract["material_contract"]["interpretation"],
        "product_material_identification": "NOT_CLAIMED",
        "candidate_rows": materials,
    }

    DocumentHelper.CreateNewDocument()
    plate = create_block(-3.5, -3.5, 0.0, 3.5, 3.5, 0.275, "AJM_P2_S0_EQ_BODY")
    anchor = create_block(
        -1.125, -1.125, -0.05, 1.125, 1.125, 0.001,
        "AJM_P2_S0_ANCHOR_TOOL",
    )
    merge_result = Combine.Merge(
        Selection.Create(plate), Selection.Create(anchor)
    )
    if not bool(merge_result.Success):
        raise Exception("AJM_P2_S0_BOOLEAN_MERGE_FAILED")
    authored_bodies = get_all_bodies(GetRootPart())
    if len(authored_bodies) != 1:
        raise Exception("AJM_P2_S0_BODY_COUNT_AFTER_MERGE")
    body = authored_bodies[0]
    body.Name = "AJM_P2_S0_EQ_CENTRAL_ANCHOR_C"
    authored_valid, authored_fp, authored_roles, authored_faces = geometry_valid(
        body, 0.005, 0.005
    )
    result_data["assertions"]["equivalent_plate_geometry"] = authored_valid
    result_data["assertions"]["central_anchor_geometry"] = (
        len(authored_roles["NS_ANCHOR_FIXED"]) == 1
    )

    Selection.Create(body).CreateAGroup("NS_EQ_BODY")
    create_face_group("NS_ANCHOR_FIXED", authored_roles["NS_ANCHOR_FIXED"])
    create_face_group("NS_MEMBRANE_TOP", authored_roles["NS_MEMBRANE_TOP"])
    create_face_group("NS_MEMBRANE_ALL", authored_roles["NS_MEMBRANE_TOP"])
    create_face_group("NS_TIP_X_PLUS", authored_roles["NS_TIP_X_PLUS"])
    create_face_group("NS_TIP_X_MINUS", authored_roles["NS_TIP_X_MINUS"])
    authored_group_counts = dict(
        (name, group_count(name)) for name in EXPECTED_ROLE_COUNTS
    )
    if authored_group_counts != EXPECTED_ROLE_COUNTS:
        raise Exception("AJM_P2_S0_AUTHORED_GROUP_COUNTS")

    native_save = DocumentSave.Execute(NATIVE_PATH)
    step_save = DocumentSave.Execute(STEP_PATH)
    result_data["assertions"]["native_save"] = (
        bool(native_save.Success)
        and os.path.isfile(NATIVE_PATH)
        and os.path.getsize(NATIVE_PATH) > 0
    )
    result_data["assertions"]["step_export"] = (
        bool(step_save.Success)
        and os.path.isfile(STEP_PATH)
        and os.path.getsize(STEP_PATH) > 0
    )

    DocumentHelper.CloseDocument()
    native_open = DocumentOpen.Execute(NATIVE_PATH)
    native_bodies = get_all_bodies(GetRootPart())
    native_valid = False
    native_record = {}
    if bool(native_open.Success) and len(native_bodies) == 1:
        native_geometry_valid, native_fp, native_roles, native_faces = geometry_valid(
            native_bodies[0], 0.005, 0.005
        )
        native_groups = dict(
            (name, group_count(name)) for name in EXPECTED_ROLE_COUNTS
        )
        native_valid = native_geometry_valid and native_groups == EXPECTED_ROLE_COUNTS
        native_record = {
            "body": native_fp,
            "faces": native_faces,
            "group_counts": native_groups,
        }
    result_data["assertions"]["native_reopen"] = native_valid

    DocumentHelper.CloseDocument()
    step_open = DocumentOpen.Execute(STEP_PATH)
    step_bodies = get_all_bodies(GetRootPart())
    step_valid = False
    step_record = {}
    if bool(step_open.Success) and len(step_bodies) == 1:
        step_geometry_valid, step_fp, step_roles, step_faces = geometry_valid(
            step_bodies[0], 0.02, 0.02
        )
        step_role_counts = dict(
            (name, len(faces)) for name, faces in step_roles.items()
        )
        step_valid = step_geometry_valid
        step_record = {
            "body": step_fp,
            "faces": step_faces,
            "reconstructed_role_counts": step_role_counts,
            "named_selection_transfer_assumed": False,
        }
    result_data["assertions"]["step_reimport"] = step_valid
    result_data["assertions"]["step_anchor_region_preserved"] = (
        step_valid
        and step_record["reconstructed_role_counts"].get("NS_ANCHOR_FIXED") == 1
    )

    sidecar = {
        "schema_version": 1,
        "semantic_contract": "P2_S0_EQUIVALENT_PLATE_CENTRAL_ANCHOR_V1",
        "claim_scope": result_data["claim_scope"],
        "product_id": result_data["product_id"],
        "source_variant_id": result_data["source_variant_id"],
        "source_configuration_id": result_data["source_configuration_id"],
        "source_cell": source_cell,
        "local_model_origin_reset": True,
        "representation": "ONE_CONNECTED_SOLID",
        "expected_bbox_min_mm": EXPECTED_BBOX_MIN_MM,
        "expected_bbox_max_mm": EXPECTED_BBOX_MAX_MM,
        "expected_volume_mm3": EXPECTED_VOLUME_MM3,
        "native_groups": EXPECTED_ROLE_COUNTS,
        "step_named_selection_transfer": "NOT_ASSUMED",
        "mechanical_reconstruction_required": True,
        "perimeter_constraint": "FREE_NO_CAD_CONSTRAINT_DEFINED",
        "anchor_evidence_class": "C",
        "anchor_product_fact": False,
        "contract": {
            "relative_path": CONTRACT_NAME,
            "sha256": sha256_file(contract_path),
        },
        "source_variant": {
            "relative_path": VARIANT_NAME,
            "sha256": sha256_file(variant_path),
        },
        "material_candidates": {
            "relative_path": MATERIAL_NAME,
            "sha256": sha256_file(material_path),
            "candidate_ids": [row["candidate_id"] for row in materials],
            "candidate_rows": materials,
            "design": "paired_candidate_bundle_not_factorial",
            "product_fact": False,
        },
        "step": {
            "relative_path": os.path.basename(STEP_PATH),
            "size": os.path.getsize(STEP_PATH),
            "sha256": sha256_file(STEP_PATH),
        },
        "authored": {
            "body": authored_fp,
            "faces": authored_faces,
            "group_counts": authored_group_counts,
        },
        "native_reopen": native_record,
        "step_reimport": step_record,
        "formal_p2_gate": "NOT_RUN",
        "p1_p6_gates": "NOT_RUN",
    }
    write_json(SIDECAR_PATH, sidecar)
    result_data["assertions"]["step_semantic_sidecar"] = (
        os.path.isfile(SIDECAR_PATH)
        and os.path.getsize(SIDECAR_PATH) > 0
        and sidecar["step"]["sha256"] == sha256_file(STEP_PATH)
        and sidecar["step_named_selection_transfer"] == "NOT_ASSUMED"
    )

    files = {}
    for path in (NATIVE_PATH, STEP_PATH, SIDECAR_PATH):
        files[os.path.basename(path)] = {
            "path": path,
            "size": os.path.getsize(path),
            "sha256": sha256_file(path),
        }
    result_data["files"] = files
    result_data["dependency_manifest"] = {
        "path": dependency_manifest_path,
        "sha256": sha256_file(dependency_manifest_path),
    }
    result_data["geometry"] = {
        "authored": authored_fp,
        "native_reopen": native_record,
        "step_reimport": step_record,
        "observed_face_count_is_diagnostic_only": True,
        "free_perimeter": True,
    }
    result_data["assertions"]["artifact_hashes"] = all(
        item["size"] > 0 and len(item["sha256"]) == 64
        for item in files.values()
    )
    result_data["assertions"]["claim_boundaries"] = (
        result_data["p2_stage_gate"] == "NOT_RUN"
        and result_data["formal_p2_gate"] == "NOT_RUN"
        and result_data["p1_p6_gates"] == "NOT_RUN"
        and result_data["formal_p2_completion"] is False
        and result_data["exact_product_geometry"] == "NOT_CLAIMED"
        and result_data["product_material_identification"] == "NOT_CLAIMED"
    )
    result_data["assertions"]["physics_guards"] = (
        result_data["physics"] == "NOT_RUN"
        and result_data["mesh"] == "NOT_RUN"
        and result_data["modal"] == "NOT_RUN"
        and result_data["harmonic"] == "NOT_RUN"
        and result_data["mechanical"] == "NOT_RUN"
        and result_data["piezoelectric_coupling"] == "NOT_RUN"
        and result_data["fsi"] == "NOT_RUN"
    )
    if all(result_data["assertions"].values()):
        result_data["status"] = "PASS_PARTIAL_CAD_CAPABILITY"
        result_data["engineering_capability"] = "PASS_PARTIAL_CAD_CAPABILITY"
        result_data["pilot_result"] = contract["claim_ceiling"]

except Exception as exc:
    result_data["error"] = {
        "type": type(exc).__name__,
        "message": str(exc),
        "traceback": traceback.format_exc(),
    }

finally:
    try:
        DocumentHelper.CloseDocument()
    except Exception:
        pass
    write_json(REPORT_PATH, result_data)

if result_data["status"] != "PASS_PARTIAL_CAD_CAPABILITY":
    raise Exception("AJM_P2_S0_EQUIVALENT_PLATE_PRODUCER_FAILED")

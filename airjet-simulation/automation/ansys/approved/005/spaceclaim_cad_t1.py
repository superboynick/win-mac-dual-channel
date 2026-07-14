# AJM-005 SpaceClaim CAD capability probe; this is a disposable tool model.
import hashlib
import json
import math
import os
import traceback

from System import Array, String


job_dir = os.environ["AIRJET_JOB_DIR"]
report_path = os.path.join(job_dir, "spaceclaim_cad_t1.json")
full_native_path = os.path.join(job_dir, "spaceclaim_cad_t1_full.scdocx")
native_path = os.path.join(job_dir, "spaceclaim_cad_t1.scdocx")
step_path = os.path.join(job_dir, "spaceclaim_cad_t1.step")

assertion_names = (
    "script_parameterization_equivalent",
    "named_selections",
    "volume_extract_or_equivalent",
    "fluid_connectivity",
    "native_save",
    "native_reopen",
    "step_export_reimport",
)
result_data = {
    "schema_version": 1,
    "task": "AJM-WIN-ANSYS-STUDENT-CAPABILITY-SMOKE-005",
    "probe": "spaceclaim_cad_t1",
    "status": "FAIL_DIRECT",
    "engineering_capability": "FAIL_DIRECT",
    "p1_stage_gate": "NOT_RUN",
    "visibility": "NOT_USER_OBSERVED",
    "script_api": "V261",
    "license_arguments_added": False,
    "parameterization_route": "SCRIPT_EQUIVALENT_TWO_BUILDS",
    "native_parameterization": "NOT_RUN",
    "p1_cad_hard_gate": "BLOCKED_NATIVE_PARAMETERIZATION",
    "volume_extract_api": "NOT_RUN",
    "volume_extract_route": "DIRECT_NEGATIVE_VOLUME_BOOLEAN_UNION_EQUIVALENT",
    "assertions": dict((name, False) for name in assertion_names),
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


def mm_value(value_in_meters):
    return float(value_in_meters) * 1000.0


def mm3_value(value_in_cubic_meters):
    return float(value_in_cubic_meters) * 1000000000.0


def body_fingerprint(body):
    box = body.Shape.GetBoundingBox(Matrix.Identity)
    return {
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
        "volume_mm3": mm3_value(body.Shape.Volume),
        "face_count": int(body.Faces.Count),
        "piece_count": int(body.Shape.PieceCount),
        "is_closed": bool(body.Shape.IsClosed),
    }


def close_enough(actual, expected, tolerance):
    return abs(float(actual) - float(expected)) <= tolerance


def group_count(name):
    """CreateByGroups requires a .NET String array in the v261 script host."""
    return int(Selection.CreateByGroups(Array[String]([name])).Count)


def find_boundary_faces(body):
    inlet = []
    outlet = []
    details = []
    for face in body.Faces:
        box = face.Shape.GetBoundingBox(Matrix.Identity)
        center = box.Center
        center_mm = [mm_value(center.X), mm_value(center.Y), mm_value(center.Z)]
        area_mm2 = float(face.Area) * 1000000.0
        entry = {"center_mm": center_mm, "area_mm2": area_mm2}
        details.append(entry)
        if (
            close_enough(center_mm[0], 10.0, 0.05)
            and close_enough(center_mm[1], 5.0, 0.05)
            and close_enough(center_mm[2], 0.0, 0.05)
            and close_enough(area_mm2, math.pi, 0.05)
        ):
            inlet.append(face)
        elif (
            close_enough(center_mm[0], 20.0, 0.05)
            and close_enough(center_mm[1], 5.0, 0.05)
            and close_enough(center_mm[2], 2.0, 0.05)
            and close_enough(area_mm2, 4.0, 0.05)
        ):
            outlet.append(face)
    walls = [face for face in body.Faces if face not in inlet and face not in outlet]
    return inlet, outlet, walls, details


def create_parameter_probe(cavity_width_mm):
    probe = BlockBody.Create(
        Point.Create(MM(0), MM(0), MM(0)),
        Point.Create(MM(16), MM(cavity_width_mm), MM(2)),
        ExtrudeType.ForceIndependent,
    ).CreatedBody
    volume = mm3_value(probe.Shape.Volume)
    bbox = body_fingerprint(probe)
    Delete.Execute(Selection.Create(probe))
    return volume, bbox


try:
    DocumentHelper.CreateNewDocument()

    initial_volume, initial_bbox = create_parameter_probe(5.0)
    updated_volume, updated_bbox = create_parameter_probe(6.0)
    parameterization_ok = (
        close_enough(initial_volume, 160.0, 0.01)
        and close_enough(updated_volume, 192.0, 0.01)
        and updated_volume > initial_volume
        and close_enough(updated_bbox["bbox_max_mm"][1], 6.0, 0.01)
    )
    result_data["parameter_probe"] = {
        "parameter": "cavity_width_mm",
        "initial_value_mm": 5.0,
        "updated_value_mm": 6.0,
        "initial_volume_mm3": initial_volume,
        "updated_volume_mm3": updated_volume,
        "initial_bbox": initial_bbox,
        "updated_bbox": updated_bbox,
    }
    result_data["assertions"]["script_parameterization_equivalent"] = (
        parameterization_ok
    )

    outer = BlockBody.Create(
        Point.Create(MM(0), MM(0), MM(0)),
        Point.Create(MM(20), MM(10), MM(4)),
        ExtrudeType.ForceIndependent,
    ).CreatedBody
    outer.Name = "AJM005_T1_OUTER"

    cavity = BlockBody.Create(
        Point.Create(MM(2), MM(2), MM(1)),
        Point.Create(MM(18), MM(8), MM(3)),
        ExtrudeType.ForceIndependent,
    ).CreatedBody
    cavity.Name = "AJM005_T1_FLUID"
    inlet = CylinderBody.Create(
        # Installed v261 example semantics: p1->p2 is the cylinder axis;
        # p2->p3 is the radius vector in the second end-cap plane.
        Point.Create(MM(10), MM(5), MM(0)),
        Point.Create(MM(10), MM(5), MM(1.1)),
        Point.Create(MM(11), MM(5), MM(1.1)),
        ExtrudeType.ForceIndependent,
    ).CreatedBodies[0]
    outlet = BlockBody.Create(
        Point.Create(MM(18), MM(3), MM(1.5)),
        Point.Create(MM(20), MM(7), MM(2.5)),
        ExtrudeType.ForceIndependent,
    ).CreatedBody

    body_count_before_merge = int(GetRootPart().Bodies.Count)
    inlet_fingerprint_before_merge = body_fingerprint(inlet)
    outlet_fingerprint_before_merge = body_fingerprint(outlet)
    inlet_raw_expected_volume_mm3 = 1.1 * math.pi
    inlet_construction_ok = (
        close_enough(
            inlet_fingerprint_before_merge["volume_mm3"],
            inlet_raw_expected_volume_mm3,
            0.05,
        )
        and all(
            close_enough(actual, expected, 0.02)
            for actual, expected in zip(
                inlet_fingerprint_before_merge["bbox_min_mm"], [9.0, 4.0, 0.0]
            )
        )
        and all(
            close_enough(actual, expected, 0.02)
            for actual, expected in zip(
                inlet_fingerprint_before_merge["bbox_max_mm"], [11.0, 6.0, 1.1]
            )
        )
    )
    merge_result = Combine.Merge(
        Selection.Create(cavity), Selection.Create(inlet, outlet)
    )
    fluid = cavity
    fluid.Name = "AJM005_T1_FLUID"
    fluid_fingerprint = body_fingerprint(fluid)
    expected_volume_mm3 = 192.0 + math.pi + 8.0
    equivalent_ok = (
        inlet_construction_ok
        and bool(merge_result.Success)
        and GetRootPart().Bodies.Count == 2
        and close_enough(fluid_fingerprint["volume_mm3"], expected_volume_mm3, 0.05)
    )
    connectivity_ok = (
        fluid_fingerprint["piece_count"] == 1
        and fluid_fingerprint["is_closed"]
    )

    inlet_faces, outlet_faces, wall_faces, face_details = find_boundary_faces(fluid)
    if len(inlet_faces) == 1:
        FaceSelection.Create(inlet_faces).CreateAGroup("INLET")
    if len(outlet_faces) == 1:
        FaceSelection.Create(outlet_faces).CreateAGroup("OUTLET")
    if len(wall_faces) > 0:
        FaceSelection.Create(wall_faces).CreateAGroup("WALLS")
    group_counts = {
        "INLET": group_count("INLET"),
        "OUTLET": group_count("OUTLET"),
        "WALLS": group_count("WALLS"),
    }
    named_ok = (
        group_counts["INLET"] == 1
        and group_counts["OUTLET"] == 1
        and group_counts["WALLS"] == len(wall_faces)
        and group_counts["WALLS"] > 0
    )

    result_data["construction"] = {
        "outer_block_mm": [20.0, 10.0, 4.0],
        "cavity_mm": [16.0, 6.0, 2.0],
        "inlet_diameter_mm": 2.0,
        "inlet_constructed_length_mm": 1.1,
        "inlet_cavity_overlap_mm": 0.1,
        "inlet_raw_expected_volume_mm3": inlet_raw_expected_volume_mm3,
        "inlet_construction_ok": inlet_construction_ok,
        "outlet_mm": [4.0, 1.0],
        "fluid_expected_volume_mm3": expected_volume_mm3,
        "body_count_before_merge": body_count_before_merge,
        "inlet_fingerprint_before_merge": inlet_fingerprint_before_merge,
        "outlet_fingerprint_before_merge": outlet_fingerprint_before_merge,
        "fluid_fingerprint_before_save": fluid_fingerprint,
        "full_document_body_count": int(GetRootPart().Bodies.Count),
        "boolean_merge_success": bool(merge_result.Success),
        "face_details": face_details,
        "named_selection_counts": group_counts,
    }
    result_data["assertions"]["volume_extract_or_equivalent"] = equivalent_ok
    result_data["assertions"]["fluid_connectivity"] = connectivity_ok
    result_data["assertions"]["named_selections"] = named_ok

    full_save = DocumentSave.Execute(full_native_path)
    Delete.Execute(Selection.Create(outer))
    native_save = DocumentSave.Execute(native_path)
    step_save = DocumentSave.Execute(step_path)
    native_files_ok = (
        bool(full_save.Success)
        and bool(native_save.Success)
        and bool(step_save.Success)
        and os.path.isfile(full_native_path)
        and os.path.isfile(native_path)
        and os.path.isfile(step_path)
        and os.path.getsize(native_path) > 0
        and os.path.getsize(step_path) > 0
    )
    result_data["assertions"]["native_save"] = native_files_ok

    DocumentHelper.CloseDocument()
    DocumentOpen.Execute(native_path)
    native_body = GetRootPart().Bodies[0] if GetRootPart().Bodies.Count == 1 else None
    native_fingerprint = body_fingerprint(native_body) if native_body is not None else None
    native_groups = dict(
        (name, group_count(name))
        for name in ("INLET", "OUTLET", "WALLS")
    )
    native_reopen_ok = (
        native_body is not None
        and native_body.Name == "AJM005_T1_FLUID"
        and native_fingerprint["piece_count"] == 1
        and native_fingerprint["is_closed"]
        and close_enough(native_fingerprint["volume_mm3"], expected_volume_mm3, 0.05)
        and native_groups == group_counts
    )
    result_data["native_reopen"] = {
        "body_count": int(GetRootPart().Bodies.Count),
        "body_name": native_body.Name if native_body is not None else None,
        "fingerprint": native_fingerprint,
        "named_selection_counts": native_groups,
    }
    result_data["assertions"]["native_reopen"] = native_reopen_ok

    DocumentHelper.CloseDocument()
    DocumentOpen.Execute(step_path)
    step_root_body_count = int(GetRootPart().Bodies.Count)
    step_component_count = int(GetRootPart().Components.Count)
    step_bodies = [body for body in GetRootPart().GetAllBodies()]
    step_body = step_bodies[0] if len(step_bodies) == 1 else None
    step_fingerprint = body_fingerprint(step_body) if step_body is not None else None
    step_reimport_ok = (
        step_body is not None
        and step_fingerprint["piece_count"] == 1
        and step_fingerprint["is_closed"]
        and close_enough(step_fingerprint["volume_mm3"], expected_volume_mm3, 0.10)
        and all(
            close_enough(actual, expected, 0.02)
            for actual, expected in zip(
                step_fingerprint["bbox_min_mm"], [2.0, 2.0, 0.0]
            )
        )
        and all(
            close_enough(actual, expected, 0.02)
            for actual, expected in zip(
                step_fingerprint["bbox_max_mm"], [20.0, 8.0, 3.0]
            )
        )
    )
    result_data["step_reimport"] = {
        "route": "DOCUMENT_OPEN_AND_GET_ALL_BODIES",
        "root_body_count": step_root_body_count,
        "component_count": step_component_count,
        "all_body_count": len(step_bodies),
        "fingerprint": step_fingerprint,
        "named_selections_expected_to_persist": False,
    }
    result_data["assertions"]["step_export_reimport"] = step_reimport_ok

    result_data["files"] = {
        "full_native": {
            "path": full_native_path,
            "size": os.path.getsize(full_native_path),
            "sha256": sha256_file(full_native_path),
        },
        "transfer_native": {
            "path": native_path,
            "size": os.path.getsize(native_path),
            "sha256": sha256_file(native_path),
        },
        "step": {
            "path": step_path,
            "size": os.path.getsize(step_path),
            "sha256": sha256_file(step_path),
        },
    }
    if all(result_data["assertions"].values()):
        result_data["status"] = "PASS_PARTIAL_CAD_CAPABILITY"
        result_data["engineering_capability"] = "PASS_PARTIAL_CAD_CAPABILITY"
    else:
        result_data["error"] = "CAPABILITY_ASSERTION_FAILED"
except Exception as error:
    result_data["error_type"] = type(error).__name__
    result_data["error"] = str(error)
    result_data["traceback"] = traceback.format_exc()

with open(report_path, "w") as report_handle:
    json.dump(result_data, report_handle, indent=2, sort_keys=True)

if result_data["status"] != "PASS_PARTIAL_CAD_CAPABILITY":
    raise Exception("AJM005_SPACECLAIM_CAD_T1_FAILED")

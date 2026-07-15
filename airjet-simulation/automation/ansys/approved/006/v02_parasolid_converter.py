# AJM-006 V02 native-to-Parasolid route-discovery converter.
# This diagnostic never claims formal 006 completion or a P1 stage-gate pass.
from __future__ import print_function

import hashlib
import json
import os
import shutil
import stat
import traceback

from System import Array, Object, Type
from System.IO import File
from SpaceClaim.Api.V261 import ExportOptions, ParasolidVersion


job_dir = os.environ["AIRJET_JOB_DIR"]
predecessor_dir = os.environ["AIRJET_PREDECESSOR_DIR"]
profile_id = os.environ.get("AIRJET_PROFILE_ID")
SPLIT_STEP_PROFILE = "ajm006-spaceclaim-v02-split-step-converter-v1"
split_step_route = profile_id == SPLIT_STEP_PROFILE
report_path = os.path.join(
    job_dir,
    "v02_split_step_converter.json"
    if split_step_route else "v02_parasolid_converter.json",
)
parasolid_path = os.path.join(job_dir, "product.x_t")
reimport_path = os.path.join(job_dir, "parasolid_reimport.json")
upstream_step_path = os.path.join(job_dir, "upstream.step")
downstream_step_path = os.path.join(job_dir, "downstream.step")
split_reimport_path = os.path.join(job_dir, "split_step_reimport.json")
inventory_copy_path = os.path.join(job_dir, "v02_face_inventory.json")
source_chain_path = os.path.join(job_dir, "source_chain.json")
staging_dir = os.path.join(job_dir, "input", "staging")
staged_native_path = os.path.join(staging_dir, "product_two_zone.scdocx")

producer_report_path = os.path.join(
    predecessor_dir, "v02_preliminary_producer.json"
)
native_path = os.path.join(predecessor_dir, "product_two_zone.scdocx")
native_reopen_path = os.path.join(predecessor_dir, "native_reopen.json")
source_inventory_path = os.path.join(
    predecessor_dir, "v02_face_inventory.json"
)
predecessor_manifest_path = os.path.join(
    predecessor_dir, "predecessor-manifest.json"
)

EXPECTED_PREDECESSOR_PROFILE = "ajm006-spaceclaim-v02-preliminary-v1"
REQUIRED_PRODUCER_ASSERTIONS = (
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
PARASOLID_ASSERTIONS = (
    "predecessor_identity",
    "predecessor_immutable",
    "staging_copy_hash_equal",
    "staging_workspace_exact",
    "source_native_open",
    "source_native_exact",
    "parasolid_export",
    "parasolid_reimport",
    "parasolid_body_envelope_and_face_count_preserved",
    "evidence_copy_hash_equal",
    "artifact_hashes",
    "claim_boundaries",
)
SPLIT_STEP_ASSERTIONS = (
    "predecessor_identity",
    "predecessor_immutable",
    "staging_copy_hash_equal",
    "staging_workspace_exact",
    "source_native_open",
    "source_native_exact",
    "split_step_export",
    "split_step_reimport",
    "split_body_envelope_and_face_count_preserved",
    "evidence_copy_hash_equal",
    "artifact_hashes",
    "claim_boundaries",
)
ASSERTIONS = SPLIT_STEP_ASSERTIONS if split_step_route else PARASOLID_ASSERTIONS

result = {
    "schema_version": 1,
    "task": (
        "AJM006_V02_SPLIT_STEP_ROUTE_DISCOVERY_CONVERTER"
        if split_step_route
        else "AJM006_V02_PARASOLID_ROUTE_DISCOVERY_CONVERTER"
    ),
    "probe": (
        "v02_split_step_converter"
        if split_step_route else "v02_parasolid_converter"
    ),
    "status": (
        "FAIL_SPLIT_STEP_CONVERTER"
        if split_step_route else "FAIL_PARASOLID_CONVERTER"
    ),
    "engineering_capability": (
        "FAIL_SPLIT_STEP_CONVERTER"
        if split_step_route else "FAIL_PARASOLID_CONVERTER"
    ),
    "claim_scope": (
        "V02_PRELIMINARY_SPLIT_STEP_ROUTE_DISCOVERY_ONLY"
        if split_step_route
        else "V02_PRELIMINARY_PARASOLID_ROUTE_DISCOVERY_ONLY"
    ),
    "formal_006_completion": False,
    "p1_stage_gate": "NOT_RUN",
    "p1_p6_gates": "NOT_RUN",
    "license_arguments_added": False,
    "diagnostic_only": True,
    "mesh": "NOT_RUN",
    "physics": "NOT_RUN",
    "source_native_mutated": False,
    "representation_conversion": True,
    "interface_topology": (
        "SEPARATE_BODY_FILES_ONLY_NOT_SOLVER_COMBINED"
        if split_step_route
        else "NOT_EVALUATED_UNTIL_PARASOLID_OBSERVER"
    ),
    "assertions": dict((name, False) for name in ASSERTIONS),
    "error": None,
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


def snapshot_tree(root):
    snapshot = {}
    for base, directories, files in os.walk(root):
        directories.sort()
        files.sort()
        for name in files:
            path = os.path.join(base, name)
            relative = os.path.relpath(path, root).replace("\\", "/")
            snapshot[relative] = {
                "size": os.path.getsize(path),
                "sha256": sha256_file(path),
            }
    return snapshot


def read_json(path):
    with open(path, "r") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise Exception("JSON_ROOT_NOT_OBJECT:%s" % os.path.basename(path))
    return value


def write_json(path, value):
    with open(path, "w") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)


def mm_value(value_in_meters):
    return float(value_in_meters) * 1000.0


def mm3_value(value_in_cubic_meters):
    return float(value_in_cubic_meters) * 1000000000.0


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
            mm_value(box.MinCorner.X),
            mm_value(box.MinCorner.Y),
            mm_value(box.MinCorner.Z),
        ],
        "bbox_max_mm": [
            mm_value(box.MaxCorner.X),
            mm_value(box.MaxCorner.Y),
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
    left_items = sorted(expected, key=lambda item: item["bbox_min_mm"][2])
    right_items = sorted(actual, key=lambda item: item["bbox_min_mm"][2])
    bbox_deltas = []
    volume_deltas = []
    for left, right in zip(left_items, right_items):
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


def fingerprints_shape_equivalent(
    expected, actual, require_names=False, require_face_count=False
):
    if len(expected) != 2 or len(actual) != 2:
        return False
    left_items = sorted(expected, key=lambda item: item["bbox_min_mm"][2])
    right_items = sorted(actual, key=lambda item: item["bbox_min_mm"][2])
    for left, right in zip(left_items, right_items):
        if require_names and str(left["name"]) != str(right["name"]):
            return False
        if require_face_count and int(left["face_count"]) != int(
            right["face_count"]
        ):
            return False
        if not right["is_closed"] or not right["is_manifold"]:
            return False
        if right["piece_count"] != 1:
            return False
        for key in ("bbox_min_mm", "bbox_max_mm"):
            for left_value, right_value in zip(left[key], right[key]):
                if abs(float(left_value) - float(right_value)) > 0.005:
                    return False
        volume_scale = max(abs(float(left["volume_mm3"])), 1.0)
        if abs(float(left["volume_mm3"]) - float(right["volume_mm3"])) > max(
            0.005, volume_scale * 1.0e-5
        ):
            return False
    return True


def single_fingerprint_equivalent(expected, actual):
    if not isinstance(expected, dict) or not isinstance(actual, dict):
        return False
    if int(expected["face_count"]) != int(actual["face_count"]):
        return False
    if not actual["is_closed"] or not actual["is_manifold"]:
        return False
    if actual["piece_count"] != 1:
        return False
    for key in ("bbox_min_mm", "bbox_max_mm"):
        for left_value, right_value in zip(expected[key], actual[key]):
            if abs(float(left_value) - float(right_value)) > 0.005:
                return False
    volume_scale = max(abs(float(expected["volume_mm3"])), 1.0)
    return abs(
        float(expected["volume_mm3"]) - float(actual["volume_mm3"])
    ) <= max(0.005, volume_scale * 1.0e-5)


def close_document_fail_soft():
    try:
        DocumentHelper.CloseDocument()
    except Exception:
        pass


try:
    producer = read_json(producer_report_path)
    native_reopen = read_json(native_reopen_path)
    face_inventory = read_json(source_inventory_path)
    predecessor_manifest = read_json(predecessor_manifest_path)
    expected_names = {
        "v02_preliminary_producer.json",
        "product_two_zone.scdocx",
        "native_reopen.json",
        "v02_face_inventory.json",
    }
    expected_predecessor_tree_names = set(expected_names)
    expected_predecessor_tree_names.add("predecessor-manifest.json")
    actual_paths = {
        "v02_preliminary_producer.json": producer_report_path,
        "product_two_zone.scdocx": native_path,
        "native_reopen.json": native_reopen_path,
        "v02_face_inventory.json": source_inventory_path,
    }
    manifest_entries = dict(
        (item.get("relative_path"), item)
        for item in predecessor_manifest.get("artifacts", [])
    )
    source_hashes_before = dict(
        (name, sha256_file(path)) for name, path in actual_paths.items()
    )
    predecessor_snapshot_before = snapshot_tree(predecessor_dir)
    predecessor_identity_ok = (
        predecessor_manifest.get("schema_version") == 1
        and predecessor_manifest.get("required_report")
        == "v02_preliminary_producer.json"
        and predecessor_manifest.get("required_status")
        == "PASS_PARTIAL_CAD_CAPABILITY"
        and predecessor_manifest.get("predecessor_profile_id")
        == EXPECTED_PREDECESSOR_PROFILE
        and predecessor_manifest.get("git_head")
        == os.environ.get("AIRJET_GIT_HEAD")
        and set(manifest_entries) == expected_names
        and set(predecessor_snapshot_before)
        == expected_predecessor_tree_names
        and all(
            manifest_entries.get(name, {}).get("sha256")
            == source_hashes_before.get(name)
            and manifest_entries.get(name, {}).get("size")
            == os.path.getsize(actual_paths[name])
            for name in expected_names
        )
        and producer.get("probe") == "v02_preliminary_producer"
        and producer.get("status") == "PASS_PARTIAL_CAD_CAPABILITY"
        and producer.get("engineering_capability")
        == "PASS_PARTIAL_CAD_CAPABILITY"
        and producer.get("formal_006_completion") is False
        and producer.get("p1_stage_gate") == "NOT_RUN"
        and producer.get("p1_p6_gates") == "NOT_RUN"
        and producer.get("license_arguments_added") is False
        and producer.get("identity", {}).get("git_head")
        == os.environ.get("AIRJET_GIT_HEAD")
        and producer.get("identity", {}).get("profile_id")
        == EXPECTED_PREDECESSOR_PROFILE
        and producer.get("identity", {}).get("case_id")
        == os.environ.get("AIRJET_CASE_ID")
        and producer.get("identity", {}).get("script_sha256")
        == predecessor_manifest.get("predecessor_script_sha256")
        and producer.get("identity", {}).get("profile_contract_sha256")
        == predecessor_manifest.get("predecessor_profile_contract_sha256")
        and set(producer.get("assertions", {}))
        == set(REQUIRED_PRODUCER_ASSERTIONS)
        and all(
            producer.get("assertions", {}).get(name) is True
            for name in REQUIRED_PRODUCER_ASSERTIONS
        )
        and producer.get("files", {}).get("two_zone_native", {}).get("sha256")
        == source_hashes_before["product_two_zone.scdocx"]
        and producer.get("files", {}).get("two_zone_native", {}).get("size")
        == os.path.getsize(native_path)
        and producer.get("files", {}).get("native_reopen", {}).get("sha256")
        == source_hashes_before["native_reopen.json"]
        and producer.get("files", {}).get("face_inventory", {}).get("sha256")
        == source_hashes_before["v02_face_inventory.json"]
        and native_reopen.get("body_count") == 2
        and sorted(
            item.get("face_count")
            for item in native_reopen.get("body_fingerprints", [])
        )
        == [978, 2044]
        and all(
            item.get("piece_count") == 1
            and item.get("is_closed") is True
            and item.get("is_manifold") is True
            for item in native_reopen.get("body_fingerprints", [])
        )
        and face_inventory.get("claim_scope")
        == "V02_PRELIMINARY_GEOMETRY_ONLY"
        and face_inventory.get("downstream_orifice_candidates") == 972
    )
    result["assertions"]["predecessor_identity"] = predecessor_identity_ok
    if not predecessor_identity_ok:
        raise Exception("PREDECESSOR_IDENTITY_ASSERTION_FAILED")

    source_fingerprints = native_reopen.get("body_fingerprints", [])
    if not os.path.isdir(staging_dir):
        os.makedirs(staging_dir)
    shutil.copyfile(native_path, staged_native_path)
    os.chmod(staged_native_path, stat.S_IREAD | stat.S_IWRITE)
    staged_native_before = {
        "size": os.path.getsize(staged_native_path),
        "sha256": sha256_file(staged_native_path),
    }
    staging_snapshot_before = snapshot_tree(staging_dir)
    staging_copy_ok = staged_native_before == {
        "size": os.path.getsize(native_path),
        "sha256": source_hashes_before["product_two_zone.scdocx"],
    }
    result["assertions"]["staging_copy_hash_equal"] = staging_copy_ok
    if not staging_copy_ok:
        raise Exception("STAGING_COPY_HASH_MISMATCH")
    staging_workspace_before_exact = (
        set(staging_snapshot_before) == {"product_two_zone.scdocx"}
        and staging_snapshot_before["product_two_zone.scdocx"]
        == staged_native_before
    )
    if not staging_workspace_before_exact:
        raise Exception("STAGING_WORKSPACE_NOT_EXACT_BEFORE_OPEN")

    opened = DocumentOpen.Execute(staged_native_path)
    native_bodies = get_all_bodies_without_extension_binding(GetRootPart())
    native_fingerprints = [body_fingerprint(body) for body in native_bodies]
    source_native_open = bool(opened.Success) and len(native_bodies) == 2
    source_native_exact = fingerprints_shape_equivalent(
        source_fingerprints,
        native_fingerprints,
        require_names=True,
        require_face_count=True,
    )
    result["assertions"]["source_native_open"] = source_native_open
    result["assertions"]["source_native_exact"] = source_native_exact
    if not source_native_open or not source_native_exact:
        raise Exception("SOURCE_NATIVE_REOPEN_MISMATCH")

    if split_step_route:
        by_name = dict((item.Name, item) for item in native_bodies)
        upstream_name = "AJM006_V02_FLUID_UPSTREAM"
        downstream_name = "AJM006_V02_FLUID_DOWNSTREAM"
        if set(by_name) != {upstream_name, downstream_name}:
            raise Exception("SPLIT_STEP_SOURCE_BODY_NAMES_MISMATCH")
        expected_by_name = dict(
            (item["name"], item) for item in source_fingerprints
        )

        Delete.Execute(Selection.Create(by_name[downstream_name]))
        upstream_export = DocumentSave.Execute(upstream_step_path)
        upstream_export_ok = (
            bool(upstream_export.Success)
            and os.path.isfile(upstream_step_path)
            and os.path.getsize(upstream_step_path) > 0
        )
        close_document_fail_soft()

        reopened_source = DocumentOpen.Execute(staged_native_path)
        source_bodies_again = get_all_bodies_without_extension_binding(
            GetRootPart()
        )
        by_name_again = dict((item.Name, item) for item in source_bodies_again)
        if not bool(reopened_source.Success) or set(by_name_again) != {
            upstream_name,
            downstream_name,
        }:
            raise Exception("SPLIT_STEP_SOURCE_SECOND_OPEN_MISMATCH")
        Delete.Execute(Selection.Create(by_name_again[upstream_name]))
        downstream_export = DocumentSave.Execute(downstream_step_path)
        downstream_export_ok = (
            bool(downstream_export.Success)
            and os.path.isfile(downstream_step_path)
            and os.path.getsize(downstream_step_path) > 0
        )
        split_export_ok = upstream_export_ok and downstream_export_ok
        result["assertions"]["split_step_export"] = split_export_ok
        if not split_export_ok:
            raise Exception("SPLIT_STEP_EXPORT_ASSERTION_FAILED")
        close_document_fail_soft()

        upstream_open = DocumentOpen.Execute(upstream_step_path)
        upstream_bodies = get_all_bodies_without_extension_binding(
            GetRootPart()
        )
        upstream_fingerprints = [
            body_fingerprint(body) for body in upstream_bodies
        ]
        close_document_fail_soft()
        downstream_open = DocumentOpen.Execute(downstream_step_path)
        downstream_bodies = get_all_bodies_without_extension_binding(
            GetRootPart()
        )
        downstream_fingerprints = [
            body_fingerprint(body) for body in downstream_bodies
        ]
        split_step_reimport_ok = (
            bool(upstream_open.Success)
            and bool(downstream_open.Success)
            and len(upstream_fingerprints) == 1
            and len(downstream_fingerprints) == 1
        )
        split_shape_ok = (
            split_step_reimport_ok
            and single_fingerprint_equivalent(
                expected_by_name[upstream_name], upstream_fingerprints[0]
            )
            and single_fingerprint_equivalent(
                expected_by_name[downstream_name], downstream_fingerprints[0]
            )
        )
        split_reimport = {
            "schema_version": 1,
            "route": "NATIVE_TWO_BODY_TO_TWO_INDEPENDENT_STEP_FILES",
            "source_native_body_fingerprints": source_fingerprints,
            "upstream_body_fingerprints": upstream_fingerprints,
            "downstream_body_fingerprints": downstream_fingerprints,
            "solver_combination": "NOT_EVALUATED_SEPARATE_FILES_ONLY",
        }
        write_json(split_reimport_path, split_reimport)
        result["assertions"]["split_step_reimport"] = split_step_reimport_ok
        result["assertions"][
            "split_body_envelope_and_face_count_preserved"
        ] = split_shape_ok
        if not split_step_reimport_ok or not split_shape_ok:
            raise Exception("SPLIT_STEP_BODY_SHAPE_OR_FACE_COUNT_NOT_PRESERVED")
        close_document_fail_soft()
        comparison_deltas = None
        parasolid_fingerprints = []
    else:
        export_options = ExportOptions.Create()
        export_options.Parasolid.Version = ParasolidVersion.V23
        exported = DocumentSave.Execute(parasolid_path, export_options)
        parasolid_export_ok = (
            bool(exported.Success)
            and os.path.isfile(parasolid_path)
            and os.path.getsize(parasolid_path) > 0
        )
        result["assertions"]["parasolid_export"] = parasolid_export_ok
        result["parasolid_export_options"] = {
            "api_version": "V261",
            "parasolid_version": "V23",
        }
        if not parasolid_export_ok:
            raise Exception("PARASOLID_EXPORT_ASSERTION_FAILED")

        close_document_fail_soft()
        reopened = DocumentOpen.Execute(parasolid_path)
        parasolid_bodies = get_all_bodies_without_extension_binding(
            GetRootPart()
        )
        parasolid_fingerprints = [
            body_fingerprint(body) for body in parasolid_bodies
        ]
        comparison_deltas = fingerprint_deltas(
            source_fingerprints, parasolid_fingerprints
        )
        parasolid_reimport_ok = (
            bool(reopened.Success)
            and len(parasolid_bodies) == 2
            and all(
                item["piece_count"] == 1
                and item["is_closed"]
                and item["is_manifold"]
                for item in parasolid_fingerprints
            )
        )
        parasolid_shape_ok = (
            sorted(item["face_count"] for item in parasolid_fingerprints)
            == [978, 2044]
            and fingerprints_shape_equivalent(
                source_fingerprints,
                parasolid_fingerprints,
                require_names=False,
                require_face_count=True,
            )
        )
        reimport = {
            "schema_version": 1,
            "route": "SPACECLAIM_NATIVE_TO_PARASOLID_X_T_AND_REOPEN",
            "source_native_body_fingerprints": source_fingerprints,
            "body_count": len(parasolid_bodies),
            "body_fingerprints": parasolid_fingerprints,
            "comparison_deltas": comparison_deltas,
            "solver_interface_identity": "NOT_EVALUATED_UNTIL_PARASOLID_OBSERVER",
        }
        write_json(reimport_path, reimport)
        result["assertions"]["parasolid_reimport"] = parasolid_reimport_ok
        result["assertions"][
            "parasolid_body_envelope_and_face_count_preserved"
        ] = parasolid_shape_ok
        if not parasolid_reimport_ok or not parasolid_shape_ok:
            raise Exception("PARASOLID_BODY_ENVELOPE_OR_FACE_COUNT_NOT_PRESERVED")
        close_document_fail_soft()

    File.Copy(source_inventory_path, inventory_copy_path, True)
    evidence_copy_hash_equal = (
        sha256_file(inventory_copy_path)
        == source_hashes_before["v02_face_inventory.json"]
    )
    result["assertions"]["evidence_copy_hash_equal"] = (
        evidence_copy_hash_equal
    )
    if not evidence_copy_hash_equal:
        raise Exception("EVIDENCE_COPY_HASH_MISMATCH")
    source_chain = {
        "schema_version": 1,
        "producer_job_id": predecessor_manifest.get("predecessor_job_id"),
        "producer_profile_id": predecessor_manifest.get(
            "predecessor_profile_id"
        ),
        "producer_git_head": predecessor_manifest.get("git_head"),
        "producer_manifest_snapshot_sha256": predecessor_manifest.get(
            "artifact_manifest_snapshot_sha256"
        ),
        "source_hashes": source_hashes_before,
        "staged_native": staged_native_before,
        "native_open_fingerprints": native_fingerprints,
        "conversion": (
            "PRODUCT_TWO_ZONE_SCDOCX_TO_TWO_INDEPENDENT_STEP_FILES"
            if split_step_route
            else "PRODUCT_TWO_ZONE_SCDOCX_TO_PRODUCT_X_T"
        ),
        "formal_006_completion": False,
        "p1_p6_gates": "NOT_RUN",
    }
    if split_step_route:
        source_chain["split_step"] = {
            "upstream": {
                "size": os.path.getsize(upstream_step_path),
                "sha256": sha256_file(upstream_step_path),
            },
            "downstream": {
                "size": os.path.getsize(downstream_step_path),
                "sha256": sha256_file(downstream_step_path),
            },
        }
    else:
        source_chain["parasolid"] = {
            "size": os.path.getsize(parasolid_path),
            "sha256": sha256_file(parasolid_path),
        }
    write_json(source_chain_path, source_chain)

    source_hashes_after = dict(
        (name, sha256_file(path)) for name, path in actual_paths.items()
    )
    staged_native_after = {
        "size": os.path.getsize(staged_native_path),
        "sha256": sha256_file(staged_native_path),
    }
    predecessor_snapshot_after = snapshot_tree(predecessor_dir)
    staging_snapshot_after = snapshot_tree(staging_dir)
    predecessor_immutable = (
        source_hashes_after == source_hashes_before
        and predecessor_snapshot_after == predecessor_snapshot_before
    )
    staging_workspace_exact = (
        staging_snapshot_after == staging_snapshot_before
        and staged_native_after == staged_native_before
    )
    result["assertions"]["predecessor_immutable"] = predecessor_immutable
    result["assertions"]["staging_workspace_exact"] = staging_workspace_exact
    if not predecessor_immutable:
        raise Exception("PREDECESSOR_MUTATED")
    if not staging_workspace_exact:
        raise Exception("STAGING_WORKSPACE_CHANGED")

    files = {}
    route_files = (
        (
            ("upstream_step", upstream_step_path),
            ("downstream_step", downstream_step_path),
            ("split_step_reimport", split_reimport_path),
            ("face_inventory", inventory_copy_path),
            ("source_chain", source_chain_path),
        )
        if split_step_route
        else (
            ("parasolid", parasolid_path),
            ("parasolid_reimport", reimport_path),
            ("face_inventory", inventory_copy_path),
            ("source_chain", source_chain_path),
        )
    )
    for role, path in route_files:
        files[role] = {
            "path": path,
            "size": os.path.getsize(path),
            "sha256": sha256_file(path),
        }
    artifact_hashes_ok = (
        len(files) == (5 if split_step_route else 4)
        and files["face_inventory"]["sha256"]
        == source_hashes_before["v02_face_inventory.json"]
    )
    result["assertions"]["artifact_hashes"] = artifact_hashes_ok
    result["assertions"]["claim_boundaries"] = (
        result["formal_006_completion"] is False
        and result["p1_stage_gate"] == "NOT_RUN"
        and result["p1_p6_gates"] == "NOT_RUN"
        and result["diagnostic_only"] is True
        and result["mesh"] == "NOT_RUN"
        and result["physics"] == "NOT_RUN"
        and result["source_native_mutated"] is False
        and result["representation_conversion"] is True
        and result["interface_topology"]
        == (
            "SEPARATE_BODY_FILES_ONLY_NOT_SOLVER_COMBINED"
            if split_step_route
            else "NOT_EVALUATED_UNTIL_PARASOLID_OBSERVER"
        )
    )
    result["identity"] = {
        "git_head": os.environ.get("AIRJET_GIT_HEAD"),
        "profile_id": os.environ.get("AIRJET_PROFILE_ID"),
        "profile_contract_sha256": os.environ.get(
            "AIRJET_PROFILE_CONTRACT_SHA256"
        ),
        "script_sha256": os.environ.get("AIRJET_SCRIPT_SHA256"),
        "case_id": os.environ.get("AIRJET_CASE_ID"),
    }
    result["predecessor"] = {
        "job_id": predecessor_manifest.get("predecessor_job_id"),
        "profile_id": predecessor_manifest.get("predecessor_profile_id"),
        "artifact_manifest_snapshot_sha256": predecessor_manifest.get(
            "artifact_manifest_snapshot_sha256"
        ),
        "source_hashes_before": source_hashes_before,
        "source_hashes_after": source_hashes_after,
        "tree_snapshot_before": predecessor_snapshot_before,
        "tree_snapshot_after": predecessor_snapshot_after,
    }
    result["staging_final_recheck"] = {
        "before": staged_native_before,
        "after": staged_native_after,
        "unchanged": staged_native_after == staged_native_before,
        "tree_snapshot_before": staging_snapshot_before,
        "tree_snapshot_after": staging_snapshot_after,
        "workspace_exact": staging_workspace_exact,
    }
    result["conversion"] = {
        "source_native_face_counts": sorted(
            item["face_count"] for item in source_fingerprints
        ),
        "native_open_face_counts": sorted(
            item["face_count"] for item in native_fingerprints
        ),
    }
    if split_step_route:
        result["conversion"]["split_step_reimport_face_counts"] = sorted(
            [
                upstream_fingerprints[0]["face_count"],
                downstream_fingerprints[0]["face_count"],
            ]
        )
        result["conversion"]["solver_combination"] = (
            "NOT_EVALUATED_SEPARATE_FILES_ONLY"
        )
    else:
        result["conversion"]["parasolid_reimport_face_counts"] = sorted(
            item["face_count"] for item in parasolid_fingerprints
        )
        result["conversion"]["comparison_deltas"] = comparison_deltas
    result["files"] = files
    if all(result["assertions"].values()):
        result["status"] = "PASS_PARTIAL_CAD_CAPABILITY"
        result["engineering_capability"] = "PASS_PARTIAL_CAD_CAPABILITY"
    else:
        result["error"] = (
            "SPLIT_STEP_CONVERTER_ASSERTION_FAILED"
            if split_step_route
            else "PARASOLID_CONVERTER_ASSERTION_FAILED"
        )
except Exception as error:
    result["error_type"] = type(error).__name__
    result["error"] = str(error)
    result["traceback"] = traceback.format_exc()

close_document_fail_soft()
write_json(report_path, result)
if result["status"] != "PASS_PARTIAL_CAD_CAPABILITY":
    raise Exception(
        "AJM006_V02_SPLIT_STEP_CONVERTER_FAILED"
        if split_step_route
        else "AJM006_V02_PARASOLID_CONVERTER_FAILED"
    )

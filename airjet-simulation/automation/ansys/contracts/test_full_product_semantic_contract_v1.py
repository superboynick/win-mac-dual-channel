#!/usr/bin/env python
"""No-ANSYS positive and exploit tests for the production full-product contract."""

from __future__ import print_function

import copy
import hashlib
import json
import os
import shutil
import tempfile

import full_product_semantic_contract_v1 as contract


SHA_A = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64
GIT_HEAD = "1" * 40


def json_bytes(value):
    rendered = json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True)
    return rendered if isinstance(rendered, bytes) else rendered.encode("ascii")


def write_json(path, value):
    with open(path, "wb") as handle:
        handle.write(json_bytes(value))


def write_bytes(path, value):
    with open(path, "wb") as handle:
        handle.write(value)


def artifact_hashes(source_artifacts):
    return [
        {"artifact_id": item["artifact_id"], "sha256": item["sha256"]}
        for item in source_artifacts
    ]


def direction(mode, vector=None, tolerance=2.0):
    return {"mode": mode, "vector": vector, "tolerance_deg": tolerance}


def bbox(centroid, span=0.2):
    return (
        [float(value) - span for value in centroid],
        [float(value) + span for value in centroid],
    )


def match(centroid, kind, value, unit, solver_type, edge_count, role="MATCH"):
    bbox_min, bbox_max = bbox(centroid)
    return {
        "centroid_mm": centroid,
        "centroid_tolerance_mm": 0.05,
        "measure_kind": kind,
        "measure_value": value,
        "measure_tolerance": 0.1,
        "measure_unit": unit,
        "measure_role": role,
        "bbox_min_mm": bbox_min,
        "bbox_max_mm": bbox_max,
        "solver_geometry_type": solver_type,
        "edge_count": edge_count,
    }


def body(key, feature, cell, frame, centroid, adjacency, source_artifacts, volume):
    return {
        "semantic_key": key,
        "feature_key": feature,
        "entity_kind": "BODY",
        "owner_key": None,
        "cell_index": cell,
        "local_frame_id": frame,
        "local_coordinates_mm": centroid,
        "geometry_type": "SOLID_BODY",
        "direction_constraint": direction("NOT_APPLICABLE", None, 0.0),
        "match_constraints": match(centroid, "VOLUME", volume, "mm^3", "GeoBody", None),
        "topology": {
            "required_adjacent_keys": adjacency,
            "critical": True,
            "allow_isolated": False,
        },
        "expected_cardinality": 1,
        "artifact_hashes": artifact_hashes(source_artifacts),
    }


def surface(key, feature, owner, cell, frame, centroid, adjacency, source_artifacts, vector, mode="AXIS_ALIGNED"):
    return {
        "semantic_key": key,
        "feature_key": feature,
        "entity_kind": "SURFACE",
        "owner_key": owner,
        "cell_index": cell,
        "local_frame_id": frame,
        "local_coordinates_mm": centroid,
        "geometry_type": "PLANAR_FACE",
        "direction_constraint": direction(mode, vector if mode != "OUTWARD_FROM_OWNER" else None),
        "match_constraints": match(
            centroid, "AREA", 2.0, "mm^2", "GeoSurfacePlane", 4, "DIAGNOSTIC_ONLY"
        ),
        "topology": {
            "required_adjacent_keys": adjacency,
            "critical": True,
            "allow_isolated": False,
        },
        "expected_cardinality": 1,
        "artifact_hashes": artifact_hashes(source_artifacts),
    }


def actual_record(artifact_id, relative_path, path, root):
    return contract.measure_actual_artifact(artifact_id, relative_path, path, root)


def create_bundle():
    root = os.path.realpath(tempfile.mkdtemp(prefix="airjet-full-product-semantic-"))
    artifact_specs = [
        ("authoring_native", "AUTHORING_NATIVE", "producer/full_product_native.scdocx"),
        ("step_geometry", "STEP_GEOMETRY", "producer/full_product.step"),
        ("step_reimport_log", "STEP_REIMPORT_LOG", "producer/step_reimport_log.json"),
        ("semantic_sidecar", "SEMANTIC_SIDECAR", "producer/full_product_semantic_sidecar.json"),
        ("semantic_binding", "SEMANTIC_BINDING", "review/full_product_semantic_binding.json"),
        ("semantic_key_cardinality_report", "SEMANTIC_KEY_CARDINALITY_REPORT", "observer/semantic_key_cardinality_report.json"),
        ("workbench_project", "WORKBENCH_PROJECT", "observer/full_product.wbpj"),
        ("semantic_observation", "SEMANTIC_OBSERVATION", "observer/semantic_observation.json"),
        ("workbench_step_semantic_log", "WORKBENCH_STEP_SEMANTIC_LOG", "observer/workbench_step_semantic_log.json"),
    ]
    paths = {}
    artifact_contracts = []
    roles = {}
    relatives = {}
    for artifact_id, role, relative_path in artifact_specs:
        path = os.path.abspath(os.path.join(root, *relative_path.split("/")))
        directory = os.path.dirname(path)
        if not os.path.isdir(directory):
            os.makedirs(directory)
        paths[artifact_id] = path
        roles[artifact_id] = role
        relatives[artifact_id] = relative_path
        artifact_contracts.append(
            {"artifact_id": artifact_id, "role": role, "relative_path": relative_path, "required": True}
        )
    write_bytes(paths["authoring_native"], b"native-full-product-bytes")
    write_bytes(paths["step_geometry"], b"ISO-10303-21; full product STEP bytes")
    write_bytes(paths["step_reimport_log"], b'{"status":"PASS"}')
    write_bytes(paths["semantic_key_cardinality_report"], b'{"status":"PASS"}')
    write_bytes(paths["workbench_project"], b"workbench-project-bytes")
    write_bytes(paths["workbench_step_semantic_log"], b'{"status":"PASS"}')

    source_artifacts = []
    for artifact_id in ("authoring_native", "step_geometry"):
        measured = actual_record(artifact_id, relatives[artifact_id], paths[artifact_id], root)
        source_artifacts.append(
            {
                "artifact_id": artifact_id,
                "role": roles[artifact_id],
                "relative_path": relatives[artifact_id],
                "size": measured["size"],
                "sha256": measured["sha256"],
            }
        )

    global_body = "ajm.body.fluid-upstream.global"
    cell_body_0 = "ajm.body.fluid-downstream.global"
    inlet = "ajm.surface.inlet.global"
    outlet = "ajm.surface.outlet.global"
    interface_0 = "ajm.surface.membrane.c000"
    interface_1 = "ajm.surface.membrane.c001"
    semantic_keys = [global_body, cell_body_0, inlet, outlet, interface_0, interface_1]
    groups = [
        {"group_key": "ajm.group.inlet.global", "solver_name": "INLET", "entity_kind": "SURFACE", "member_keys": [inlet], "expected_cardinality": 1, "partition_family": "flow_boundary"},
        {"group_key": "ajm.group.outlet.global", "solver_name": "OUTLET", "entity_kind": "SURFACE", "member_keys": [outlet], "expected_cardinality": 1, "partition_family": "flow_boundary"},
        {"group_key": "ajm.group.membranes.all", "solver_name": "MEMBRANES", "entity_kind": "SURFACE", "member_keys": [interface_0, interface_1], "expected_cardinality": 2, "partition_family": "flow_boundary"},
        {"group_key": "ajm.group.bodies.all", "solver_name": "ALL_BODIES", "entity_kind": "BODY", "member_keys": [global_body, cell_body_0], "expected_cardinality": 2, "partition_family": None},
    ]
    partitions = [
        {
            "partition_key": "ajm.partition.flow-boundary.all",
            "entity_kind": "SURFACE",
            "group_keys": ["ajm.group.inlet.global", "ajm.group.outlet.global", "ajm.group.membranes.all"],
            "universe_keys": [inlet, outlet, interface_0, interface_1],
            "require_pairwise_disjoint": True,
            "require_full_coverage": True,
        }
    ]
    configuration = {
        "configuration_id": "AJM_FULL_PRODUCT_TEST_2CELL",
        "product_id": "AIRJET_MINI_GEN1",
        "variant_id": "TEST_TWO_CELL",
        "key_namespace": "ajm",
        "root_frame_id": "GLOBAL",
        "cell_indices": [0, 1],
        "expected_entity_cardinality": {"BODY": 2, "SURFACE": 4},
        "required_semantic_keys": semantic_keys,
        "required_group_keys": [item["group_key"] for item in groups],
        "required_partition_keys": [item["partition_key"] for item in partitions],
    }
    frames = [
        {"frame_id": "GLOBAL", "parent_frame_id": None, "cell_index": None, "origin_mm": [0.0, 0.0, 0.0], "axes": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]},
        {"frame_id": "CELL_000", "parent_frame_id": "GLOBAL", "cell_index": 0, "origin_mm": [-2.0, 0.0, 0.0], "axes": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]},
        {"frame_id": "CELL_001", "parent_frame_id": "GLOBAL", "cell_index": 1, "origin_mm": [2.0, 0.0, 0.0], "axes": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]},
    ]
    entities = [
        body(global_body, "ajm.feature.fluid-upstream.global", None, "GLOBAL", [0.0, 0.0, 0.0], [inlet, interface_0, interface_1], source_artifacts, 100.0),
        body(cell_body_0, "ajm.feature.fluid-downstream.global", None, "GLOBAL", [0.0, 0.0, -1.0], [outlet, interface_0, interface_1], source_artifacts, 50.0),
        surface(inlet, "ajm.feature.inlet.global", global_body, None, "GLOBAL", [-10.0, 0.0, 0.0], [global_body], source_artifacts, [-1.0, 0.0, 0.0]),
        surface(outlet, "ajm.feature.outlet.global", cell_body_0, None, "GLOBAL", [10.0, 0.0, -1.0], [cell_body_0], source_artifacts, [1.0, 0.0, 0.0]),
        surface(interface_0, "ajm.feature.membrane.c000", global_body, 0, "CELL_000", [0.0, 0.0, 0.5], [global_body, cell_body_0], source_artifacts, [0.0, 0.0, 1.0]),
        surface(interface_1, "ajm.feature.membrane.c001", global_body, 1, "CELL_001", [0.0, 0.0, 0.5], [global_body, cell_body_0], source_artifacts, [0.0, 0.0, 1.0]),
    ]
    producer = {
        "git_head": GIT_HEAD,
        "profile_id": "p1-full-product-producer-v1",
        "profile_contract_sha256": SHA_A,
        "script_sha256": SHA_B,
        "case_id": "AJM-P1-TEST",
        "job_id": "ajm-p1-producer-job-001",
        "output_root_id": "p1_cad_006",
    }
    producer_identity = copy.deepcopy(producer)
    producer_identity.update({"terminal_state": "PROCESS_EXITED_0", "artifact_manifest_sha256": "d" * 64})
    observer_base = {
        "git_head": GIT_HEAD,
        "profile_id": "p1-full-product-observer-v1",
        "profile_contract_sha256": "e" * 64,
        "script_sha256": "f" * 64,
        "case_id": "AJM-P1-TEST",
        "job_id": "ajm-p1-observer-job-001",
        "output_root_id": "p1_cad_006",
    }
    step_measured = actual_record("step_geometry", relatives["step_geometry"], paths["step_geometry"], root)
    observer_identity = copy.deepcopy(observer_base)
    observer_identity.update(
        {
            "terminal_state": "PROCESS_EXITED_0",
            "artifact_manifest_sha256": "9" * 64,
            "predecessor_identity": copy.deepcopy(producer_identity),
            "imported_artifact_id": "step_geometry",
            "imported_artifact_relative_path": relatives["step_geometry"],
            "imported_artifact_size": step_measured["size"],
            "imported_artifact_sha256": step_measured["sha256"],
        }
    )

    entity_blueprints = [contract._entity_blueprint(item) for item in entities]
    trusted = {
        "schema_version": 1,
        "contract_id": contract.TRUSTED_CONTRACT_ID,
        "configuration": copy.deepcopy(configuration),
        "frames": copy.deepcopy(frames),
        "entity_blueprints": copy.deepcopy(entity_blueprints),
        "blueprint_sha256": "0" * 64,
        "producer_contract": {"profile_id": producer["profile_id"], "profile_contract_sha256": producer["profile_contract_sha256"], "script_sha256": producer["script_sha256"]},
        "observer_contract": {"profile_id": observer_base["profile_id"], "profile_contract_sha256": observer_base["profile_contract_sha256"], "script_sha256": observer_base["script_sha256"]},
        "contract_hashes": [],
        "required_contract_hash_keys": [],
        "artifact_contracts": artifact_contracts,
        "artifact_root_id": "p1_cad_006",
        "artifact_root_path": root,
        "sidecar_artifact_ids": ["authoring_native", "step_geometry"],
        "sidecar_artifact_id": "semantic_sidecar",
        "binding_artifact_id": "semantic_binding",
        "observation_artifact_id": "semantic_observation",
        "solver_import_artifact_id": "step_geometry",
        "groups": copy.deepcopy(groups),
        "partitions": copy.deepcopy(partitions),
    }
    blueprint_sha = hashlib.sha256(contract._canonical_json_bytes(contract._blueprint_payload(trusted))).hexdigest()
    trusted["blueprint_sha256"] = blueprint_sha
    contract_hashes = [
        {"contract_key": "configuration_contract", "sha256": SHA_C},
        {"contract_key": "full_product_blueprint", "sha256": blueprint_sha},
        {"contract_key": "semantic_schema", "sha256": "7" * 64},
        {"contract_key": "semantic_validator", "sha256": "8" * 64},
    ]
    trusted["contract_hashes"] = copy.deepcopy(contract_hashes)
    trusted["required_contract_hash_keys"] = [item["contract_key"] for item in contract_hashes]
    sidecar = {
        "schema_version": 1,
        "contract_id": contract.SIDECAR_CONTRACT_ID,
        "scope": "FULL_PRODUCT",
        "configuration": configuration,
        "producer": producer,
        "contract_hashes": contract_hashes,
        "units": {"length": "mm", "area": "mm^2", "volume": "mm^3", "angle": "deg"},
        "source_artifacts": source_artifacts,
        "frames": frames,
        "entities": entities,
        "groups": groups,
        "partitions": partitions,
    }
    write_json(paths["semantic_sidecar"], sidecar)

    actual_ids = dict((entity["semantic_key"], "solver-entity-%03d" % (index + 1)) for index, entity in enumerate(entities))
    entity_index = dict((entity["semantic_key"], entity) for entity in entities)
    observations = []
    for entity in entities:
        constraint = entity["match_constraints"]
        kind = entity["entity_kind"]
        if kind == "BODY":
            vector = None
            owner_id = None
            adjacent_body_ids = []
            boundary_surface_ids = [actual_ids[key] for key in entity["topology"]["required_adjacent_keys"]]
        else:
            vector = [0.0, 0.0, 1.0] if entity["direction_constraint"]["mode"] == "OUTWARD_FROM_OWNER" else entity["direction_constraint"]["vector"]
            owner_id = actual_ids[entity["owner_key"]]
            adjacent_body_ids = [
                actual_ids[key] for key in entity["topology"]["required_adjacent_keys"]
                if entity_index[key]["entity_kind"] == "BODY"
            ]
            boundary_surface_ids = []
        observations.append(
            {
                "semantic_key": entity["semantic_key"],
                "entity_kind": kind,
                "cell_index": entity["cell_index"],
                "local_frame_id": entity["local_frame_id"],
                "geometry_type": entity["geometry_type"],
                "matches": [
                    {
                        "actual_id": actual_ids[entity["semantic_key"]],
                        "local_centroid_mm": list(entity["local_coordinates_mm"]),
                        "solver_geometry_type": constraint["solver_geometry_type"],
                        "edge_count": constraint["edge_count"],
                        "measure_value": constraint["measure_value"],
                        "direction_vector": vector,
                        "observed_bbox_min_mm": list(constraint["bbox_min_mm"]),
                        "observed_bbox_max_mm": list(constraint["bbox_max_mm"]),
                        "actual_owner_body_id": owner_id,
                        "actual_adjacent_body_ids": adjacent_body_ids,
                        "actual_boundary_surface_ids": boundary_surface_ids,
                    }
                ],
            }
        )
    observation = {
        "schema_version": 1,
        "contract_id": contract.OBSERVATION_CONTRACT_ID,
        "configuration_id": configuration["configuration_id"],
        "observer": observer_identity,
        "imported_artifact_id": "step_geometry",
        "imported_artifact_sha256": step_measured["sha256"],
        "entities": observations,
        "groups": [
            {"group_key": group["group_key"], "actual_ids": [actual_ids[key] for key in group["member_keys"]]}
            for group in groups
        ],
    }
    write_json(paths["semantic_observation"], observation)

    identities = []
    for artifact_id, role, relative_path in artifact_specs:
        if artifact_id == "semantic_binding":
            continue
        measured = actual_record(artifact_id, relative_path, paths[artifact_id], root)
        identities.append(
            {"artifact_id": artifact_id, "relative_path": relative_path, "size": measured["size"], "sha256": measured["sha256"]}
        )
    binding = contract.build_detached_binding(sidecar, trusted, identities)
    write_json(paths["semantic_binding"], binding)
    actual_files = {
        "artifact_root": root,
        "artifact_root_id": "p1_cad_006",
        "producer_identity": producer_identity,
        "observer_identity": observer_identity,
        "files": [
            actual_record(artifact_id, relative_path, paths[artifact_id], root)
            for artifact_id, role, relative_path in artifact_specs
        ],
    }
    trusted_raw = json_bytes(trusted)
    trusted_sha = hashlib.sha256(trusted_raw).hexdigest()
    return {
        "root": root,
        "paths": paths,
        "sidecar": sidecar,
        "binding": binding,
        "observation": observation,
        "trusted": trusted,
        "trusted_raw": trusted_raw,
        "trusted_sha": trusted_sha,
        "actual_files": actual_files,
    }


def expect_rejected(name, function, code):
    try:
        function()
    except ValueError as error:
        if str(error) != code:
            raise AssertionError("%s expected %s, got %s" % (name, code, error))
        return
    raise AssertionError("%s was accepted" % name)


def main():
    bundle = create_bundle()
    negatives = 0

    def reject(name, function, code):
        nonlocal_counter[0] += 1
        expect_rejected(name, function, code)

    nonlocal_counter = [0]
    try:
        result = contract.validate_full_product_bundle(
            bundle["sidecar"], bundle["binding"], bundle["observation"],
            bundle["actual_files"], bundle["trusted_raw"], bundle["trusted_sha"],
        )
        assert result["status"] == "PASS_FULL_PRODUCT_SEMANTIC_BUNDLE"
        assert result["cell_count"] == 2
        assert result["actual_artifact_count"] == 9
        assert result["observed_actual_entity_count"] == 6
        assert result["assignment_solution_count"] == 1
        assert result["missing_keys"] == [] and result["unexpected_keys"] == []
        assert result["body_surface_coverage_ok"] is True

        sidecar = bundle["sidecar"]
        trusted = bundle["trusted"]
        actual_files = bundle["actual_files"]
        observation = bundle["observation"]
        measured = contract._measure_actual_files(actual_files, trusted)
        producer_identity = actual_files["producer_identity"]
        observer_identity = actual_files["observer_identity"]

        mutated = copy.deepcopy(sidecar); mutated["configuration"]["cell_indices"].append(1)
        reject("duplicate_cell", lambda: contract.validate_full_product_structure(mutated), "FPSEM_CELL_INDICES")
        mutated = copy.deepcopy(sidecar); mutated["frames"][1]["axes"][2] = [0.0, 0.0, -1.0]
        reject("left_handed_frame", lambda: contract.validate_full_product_structure(mutated), "FPSEM_FRAME_AXES")
        mutated = copy.deepcopy(sidecar); mutated["entities"][1]["feature_key"] = mutated["entities"][0]["feature_key"]
        reject("duplicate_feature", lambda: contract.validate_full_product_structure(mutated), "FPSEM_FEATURE_KEY_DUPLICATE")
        mutated = copy.deepcopy(sidecar); mutated["entities"][0]["topology"]["required_adjacent_keys"].pop()
        reject("asymmetric_topology", lambda: contract.validate_full_product_structure(mutated), "FPSEM_ADJACENCY_ASYMMETRIC")

        trusted_mutated = copy.deepcopy(trusted)
        trusted_mutated["frames"][1]["origin_mm"][0] += 1.0
        trusted_mutated["blueprint_sha256"] = hashlib.sha256(contract._canonical_json_bytes(contract._blueprint_payload(trusted_mutated))).hexdigest()
        for item in trusted_mutated["contract_hashes"]:
            if item["contract_key"] == "full_product_blueprint": item["sha256"] = trusted_mutated["blueprint_sha256"]
        mutated_raw = json_bytes(trusted_mutated)
        reject("raw_trust_root", lambda: contract.load_trusted_contract_bytes(mutated_raw, bundle["trusted_sha"]), "FPSEM_TRUSTED_RAW_SHA256")

        mutated = copy.deepcopy(sidecar); mutated["entities"][2]["geometry_type"] = "CYLINDRICAL_FACE"
        reject("entity_blueprint_tamper", lambda: contract.validate_against_trusted_contract(mutated, trusted, producer_identity), "FPSEM_TRUSTED_ENTITY_BLUEPRINT")

        identity = copy.deepcopy(observer_identity); identity["profile_id"] = "wrong-observer"
        reject("observer_profile", lambda: contract._validate_observer_identity(identity, producer_identity, trusted), "FPSEM_TRUSTED_OBSERVER_PROFILE_ID")
        identity = copy.deepcopy(observer_identity); identity["script_sha256"] = "0" * 64
        reject("observer_script", lambda: contract._validate_observer_identity(identity, producer_identity, trusted), "FPSEM_TRUSTED_OBSERVER_SCRIPT_SHA256")
        identity = copy.deepcopy(observer_identity); identity["git_head"] = "2" * 40
        reject("observer_git", lambda: contract._validate_observer_identity(identity, producer_identity, trusted), "FPSEM_OBSERVER_RUN_IDENTITY")
        identity = copy.deepcopy(observer_identity); identity["terminal_state"] = "FAILED_PROCESS"
        reject("observer_terminal", lambda: contract._validate_observer_identity(identity, producer_identity, trusted), "FPSEM_OBSERVER_TERMINAL_STATE")
        identity = copy.deepcopy(observer_identity); identity["predecessor_identity"]["job_id"] = "wrong-job"
        reject("observer_predecessor", lambda: contract._validate_observer_identity(identity, producer_identity, trusted), "FPSEM_OBSERVER_PREDECESSOR")

        observed = copy.deepcopy(observation); observed["observer"]["job_id"] = "wrong-job"
        reject("observer_job_receipt", lambda: contract.validate_observation(sidecar, observed, measured, trusted, producer_identity, observer_identity), "FPSEM_OBSERVATION_OBSERVER_IDENTITY")
        observed = copy.deepcopy(observation); observed["entities"][2]["matches"][0]["actual_owner_body_id"] = "solver-entity-002"
        reject("actual_owner", lambda: contract.validate_observation(sidecar, observed, measured, trusted, producer_identity, observer_identity), "FPSEM_OBSERVATION_SURFACE_OWNER_MAPPING")
        observed = copy.deepcopy(observation); observed["entities"][2]["matches"][0]["actual_adjacent_body_ids"] = []
        reject("actual_adjacency", lambda: contract.validate_observation(sidecar, observed, measured, trusted, producer_identity, observer_identity), "FPSEM_OBSERVATION_SURFACE_ADJACENCY_MAPPING")
        observed = copy.deepcopy(observation); observed["entities"][4]["matches"][0]["actual_adjacent_body_ids"] = ["solver-entity-001"]
        reject("shared_interface_missing_downstream", lambda: contract.validate_observation(sidecar, observed, measured, trusted, producer_identity, observer_identity), "FPSEM_OBSERVATION_SURFACE_ADJACENCY_MAPPING")
        # Add a real but unexpected entity ID so only the body's exhaustive
        # boundary coverage is broken.  Removing a shared surface would also break the
        # bidirectional topology check, whose earlier error depends on dictionary
        # iteration order under IronPython 2.7.
        observed = copy.deepcopy(observation); observed["entities"][1]["matches"][0]["actual_boundary_surface_ids"].append("solver-entity-002")
        reject("downstream_extra_unexpected_surface", lambda: contract.validate_observation(sidecar, observed, measured, trusted, producer_identity, observer_identity), "FPSEM_OBSERVATION_BODY_SURFACE_COVERAGE")
        observed = copy.deepcopy(observation); observed["entities"][4]["matches"][0]["actual_owner_body_id"] = "solver-entity-002"
        reject("shared_interface_wrong_owner", lambda: contract.validate_observation(sidecar, observed, measured, trusted, producer_identity, observer_identity), "FPSEM_OBSERVATION_SURFACE_OWNER_MAPPING")
        observed = copy.deepcopy(observation); observed["entities"][0]["matches"][0]["actual_boundary_surface_ids"].append("solver-entity-002")
        reject("upstream_extra_unexpected_surface", lambda: contract.validate_observation(sidecar, observed, measured, trusted, producer_identity, observer_identity), "FPSEM_OBSERVATION_BODY_SURFACE_COVERAGE")
        observed = copy.deepcopy(observation); observed["entities"][4]["matches"][0]["direction_vector"] = [0.0, 0.0, -1.0]
        reject("direction_sign", lambda: contract.validate_observation(sidecar, observed, measured, trusted, producer_identity, observer_identity), "FPSEM_OBSERVATION_DIRECTION_MISMATCH")
        observed = copy.deepcopy(observation); observed["entities"][2]["matches"][0]["observed_bbox_max_mm"][0] += 1.0
        reject("bbox_tamper", lambda: contract.validate_observation(sidecar, observed, measured, trusted, producer_identity, observer_identity), "FPSEM_OBSERVATION_BBOX_MISMATCH")
        observed = copy.deepcopy(observation); observed["imported_artifact_sha256"] = "0" * 64
        reject("imported_step_same_bytes", lambda: contract.validate_observation(sidecar, observed, measured, trusted, producer_identity, observer_identity), "FPSEM_OBSERVATION_IMPORT_SHA256")

        trusted_mutated = copy.deepcopy(trusted)
        for item in trusted_mutated["artifact_contracts"]:
            if item["artifact_id"] == "step_geometry": item["role"] = "AUTHORING_NATIVE"
        reject("step_role", lambda: contract._validate_trusted_contract(trusted_mutated), "FPSEM_TRUSTED_IMPORT_ROLE")
        trusted_mutated = copy.deepcopy(trusted); trusted_mutated["solver_import_artifact_id"] = trusted_mutated["sidecar_artifact_id"]
        reject("reserved_import", lambda: contract._validate_trusted_contract(trusted_mutated), "FPSEM_TRUSTED_IMPORT_ARTIFACT")
        trusted_mutated = copy.deepcopy(trusted); trusted_mutated["required_contract_hash_keys"].pop()
        reject("required_hash_missing", lambda: contract._validate_trusted_contract(trusted_mutated), "FPSEM_TRUSTED_REQUIRED_CONTRACT_HASH_KEYS")

        files_mutated = copy.deepcopy(actual_files); files_mutated["artifact_root_id"] = "wrong-root"
        reject("root_id", lambda: contract._measure_actual_files(files_mutated, trusted), "FPSEM_ACTUAL_ARTIFACT_ROOT_ID")
        files_mutated = copy.deepcopy(actual_files); files_mutated["files"][0]["path"] = os.path.abspath(__file__)
        reject("exact_path", lambda: contract._measure_actual_files(files_mutated, trusted), "FPSEM_ACTUAL_FILE_PATH_IDENTITY")
        reject("root_escape", lambda: contract._require_no_reparse_chain(bundle["root"], os.path.abspath(__file__)), "FPSEM_ACTUAL_FILE_ROOT_ESCAPE")
        original_reparse = contract._reparse_state
        try:
            contract._reparse_state = lambda path: True if os.path.abspath(path) == bundle["root"] else False
            reject("reparse_ancestor", lambda: contract._require_no_reparse_ancestors(bundle["root"]), "FPSEM_ACTUAL_REPARSE_ANCESTOR")
        finally:
            contract._reparse_state = original_reparse

        binding = copy.deepcopy(bundle["binding"]); binding["artifact_identities"].pop()
        reject("binding_missing", lambda: contract.validate_detached_binding(binding, sidecar, measured, trusted), "FPSEM_BINDING_ARTIFACT_SET")
        binding = copy.deepcopy(bundle["binding"]); binding["artifact_identities"][0]["sha256"] = "0" * 64
        reject("binding_tamper", lambda: contract.validate_detached_binding(binding, sidecar, measured, trusted), "FPSEM_BINDING_ACTUAL_ARTIFACT_MISMATCH")
        reject("duplicate_json", lambda: contract.load_json_bytes_strict(b'{"x":1,"x":2}'), "FPSEM_JSON_DUPLICATE_KEY")

        negatives = nonlocal_counter[0]
        print(
            "FULL_PRODUCT_SEMANTIC_CONTRACT_V1_TESTS=PASS positive=1 negative=%d "
            "cells=2 artifacts=9 bodies=2 shared_interfaces=2 actual_topology=PASS "
            "direction_bbox=PASS raw_trust=PASS"
            % negatives
        )
    finally:
        shutil.rmtree(bundle["root"])


if __name__ == "__main__":
    main()

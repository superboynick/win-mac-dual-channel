#!/usr/bin/env python3
"""Independent fail-closed tests for the AJM semantic-sidecar v2 contract."""

from __future__ import print_function

import base64
import copy
import hashlib
import json
import math
import os

import semantic_sidecar_v2_contract as contract


U64_A = u"a" * 64
U64_B = u"b" * 64
U64_C = u"c" * 64
U64_D = u"d" * 64
U40 = u"1" * 40


def fixture_sidecar():
    faces = [
        {"label": "INLET", "center_mm": [10.0, 5.0, 0.0], "area_mm2": 3.141592653589787},
        {"label": "OUTLET", "center_mm": [20.0, 5.0, 2.0], "area_mm2": 4.0},
        {"label": "WALLS", "center_mm": [10.0, 5.0, 1.0], "area_mm2": 92.85840734641022},
        {"label": "WALLS", "center_mm": [10.0, 5.0, 3.0], "area_mm2": 96.0},
        {"label": "WALLS", "center_mm": [10.0, 8.0, 2.0], "area_mm2": 32.0},
        {"label": "WALLS", "center_mm": [18.0, 5.0, 2.0], "area_mm2": 8.0},
        {"label": "WALLS", "center_mm": [10.0, 2.0, 2.0], "area_mm2": 32.0},
        {"label": "WALLS", "center_mm": [2.0, 5.0, 2.0], "area_mm2": 12.0},
        {"label": "WALLS", "center_mm": [10.0, 5.0, 0.5], "area_mm2": 6.283185307179582},
        {"label": "WALLS", "center_mm": [19.0, 5.0, 1.5], "area_mm2": 8.0},
        {"label": "WALLS", "center_mm": [19.0, 5.0, 2.5], "area_mm2": 8.0},
        {"label": "WALLS", "center_mm": [19.0, 7.0, 2.0], "area_mm2": 2.0},
        {"label": "WALLS", "center_mm": [19.0, 3.0, 2.0], "area_mm2": 2.0},
    ]
    source = {
        "full_native": {
            "relative_path": "spaceclaim_cad_t1_full.scdocx",
            "size": 101,
            "sha256": U64_A,
        },
        "handoff_native": {
            "relative_path": "spaceclaim_cad_t1.scdocx",
            "size": 102,
            "sha256": U64_B,
        },
        "step": {
            "relative_path": "spaceclaim_cad_t1.step",
            "size": 103,
            "sha256": U64_C,
        },
    }
    identity = {
        "git_head": U40,
        "profile_id": "ajm005-spaceclaim-cad-t1-v2",
        "profile_contract_sha256": U64_D,
        "script_sha256": u"e" * 64,
        "base_script_sha256": u"f" * 64,
    }
    hashes = {
        "route_contract_sha256": u"1" * 64,
        "schema_sha256": u"2" * 64,
        "judgment_sha256": u"3" * 64,
        "validator_sha256": u"4" * 64,
    }
    return contract.build_fixture_sidecar(faces, source, identity, hashes), identity, hashes


def rejected(name, original, mutate, code):
    value = copy.deepcopy(original)
    mutate(value)
    try:
        contract.validate_sidecar(value)
    except ValueError as error:
        if str(error) != code:
            raise AssertionError("%s expected %s, got %s" % (name, code, error))
        return
    raise AssertionError("%s was accepted" % name)


def expected_rejected(name, sidecar, expected, code):
    try:
        contract.validate_sidecar(sidecar, expected)
    except ValueError as error:
        if str(error) != code:
            raise AssertionError("%s expected %s, got %s" % (name, code, error))
        return
    raise AssertionError("%s was accepted" % name)


def binding_rejected(name, binding, raw, sidecar, mutate, code):
    value = copy.deepcopy(binding)
    mutate(value)
    try:
        contract.validate_binding(value, raw, sidecar)
    except ValueError as error:
        if str(error) != code:
            raise AssertionError("%s expected %s, got %s" % (name, code, error))
        return
    raise AssertionError("%s was accepted" % name)


def direction_matches(actual, constraint):
    expected = constraint["vector"]
    actual_norm = math.sqrt(sum(float(value) ** 2 for value in actual))
    expected_norm = math.sqrt(sum(float(value) ** 2 for value in expected))
    cosine = sum(
        float(actual[index]) * float(expected[index]) for index in range(3)
    ) / (actual_norm * expected_norm)
    angle = math.degrees(math.acos(max(-1.0, min(1.0, cosine))))
    return angle <= float(constraint["tolerance_deg"])


def real_artifact_regression(identity, hashes):
    fixture_dir = os.path.join(os.path.dirname(__file__), "fixtures")
    producer_raw = base64.b64decode(
        open(
            os.path.join(
                fixture_dir,
                "AJM005_REAL_20260714_PRODUCER_39299CAC.json.b64",
            ),
            "rb",
        ).read()
    )
    inspection_raw = base64.b64decode(
        open(
            os.path.join(
                fixture_dir,
                "AJM005_REAL_20260714_INSPECTION_D0C6AC7C.json.b64",
            ),
            "rb",
        ).read()
    )
    assert hashlib.sha256(producer_raw).hexdigest() == (
        "39299cac95889d64d7172b64147cb2073d464ec35dc357fd562ae8b2af52bc57"
    )
    assert hashlib.sha256(inspection_raw).hexdigest() == (
        "d0c6ac7c0174f3e145f088837c18b283cb172681056cd88870fd70957136b9eb"
    )
    producer = json.loads(producer_raw.decode("utf-8"))
    inspection = json.loads(inspection_raw.decode("utf-8"))
    source = {
        "full_native": {
            "relative_path": "spaceclaim_cad_t1_full.scdocx",
            "size": producer["files"]["full_native"]["size"],
            "sha256": producer["files"]["full_native"]["sha256"],
        },
        "handoff_native": {
            "relative_path": "spaceclaim_cad_t1.scdocx",
            "size": producer["files"]["transfer_native"]["size"],
            "sha256": producer["files"]["transfer_native"]["sha256"],
        },
        "step": {
            "relative_path": "spaceclaim_cad_t1.step",
            "size": producer["files"]["step"]["size"],
            "sha256": producer["files"]["step"]["sha256"],
        },
    }
    sidecar = contract.build_fixture_sidecar(
        producer["construction"]["face_details"], source, identity, hashes
    )
    contract.validate_sidecar(sidecar)
    assignments = {}
    for entity in sidecar["semantic_entities"]:
        if entity["entity_kind"] != "SURFACE":
            continue
        match = entity["match_constraints"]
        candidates = []
        for face in inspection["face_details"]:
            centroid_ok = all(
                abs(
                    float(face["centroid_mm"][index])
                    - float(match["centroid_mm"][index])
                )
                <= float(match["centroid_tolerance_mm"])
                for index in range(3)
            )
            signature_ok = (
                face["surface_type"] == match["solver_surface_type"]
                and int(face["edge_count"]) == int(match["solver_edge_count"])
            )
            if (
                centroid_ok
                and signature_ok
                and direction_matches(
                    face["normal_at_centroid"], entity["direction_constraint"]
                )
            ):
                candidates.append(int(face["id"]))
        assignments[entity["semantic_key"]] = candidates
    assigned = [face_id for values in assignments.values() for face_id in values]
    assert len(assignments) == 13
    assert all(len(values) == 1 for values in assignments.values())
    assert len(set(assigned)) == 13
    assert set(assigned) == set(int(item["id"]) for item in inspection["face_details"])
    for group_name, group in sidecar["aggregate_named_selections"].items():
        group_ids = sorted(
            face_id
            for key in group["member_keys"]
            for face_id in assignments[key]
        )
        assert group_ids == sorted(inspection["reconstructed_face_ids"][group_name])
    return True


def main():
    sidecar, identity, hashes = fixture_sidecar()
    result = contract.validate_sidecar(sidecar)
    assert result["required_key_count"] == 14
    assert contract._is_sha(U64_A)  # Explicit Python 2 unicode / Python 3 str coverage.

    rejected(
        "feature_missing",
        sidecar,
        lambda item: item["semantic_entities"][1].pop("feature_key"),
        "SEM_V2_ENTITY_KEYS",
    )
    rejected(
        "feature_duplicate",
        sidecar,
        lambda item: item["semantic_entities"][2].update(
            {"feature_key": item["semantic_entities"][1]["feature_key"]}
        ),
        "SEM_V2_FEATURE_KEY_DUPLICATE",
    )
    rejected(
        "feature_invalid",
        sidecar,
        lambda item: item["semantic_entities"][1].update({"feature_key": "unstable key"}),
        "SEM_V2_FEATURE_KEY_FORMAT",
    )
    rejected(
        "geometry_invalid",
        sidecar,
        lambda item: item["semantic_entities"][1].update({"geometry_type": "ANY_FACE"}),
        "SEM_V2_SURFACE_GEOMETRY",
    )
    rejected(
        "direction_invalid",
        sidecar,
        lambda item: item["semantic_entities"][1]["direction_constraint"].update(
            {"vector": [1.0, 0.0, 0.0]}
        ),
        "SEM_V2_SURFACE_DIRECTION",
    )
    rejected(
        "match_structure_invalid",
        sidecar,
        lambda item: item["semantic_entities"][1]["match_constraints"].pop(
            "authoring_area_mm2"
        ),
        "SEM_V2_SURFACE_MATCH_STRUCTURE",
    )
    rejected(
        "entity_units_invalid",
        sidecar,
        lambda item: item["semantic_entities"][1].update(
            {"units": {"coordinate": "m", "area": "m^2"}}
        ),
        "SEM_V2_ENTITY_UNITS",
    )
    rejected(
        "owner_not_body",
        sidecar,
        lambda item: item["semantic_entities"][1].update(
            {"owner_key": item["semantic_entities"][2]["semantic_key"]}
        ),
        "SEM_V2_SURFACE_OWNER_BODY",
    )
    rejected(
        "adjacency_duplicate",
        sidecar,
        lambda item: item["semantic_entities"][0]["topology"][
            "required_adjacent_keys"
        ].append(item["semantic_entities"][1]["semantic_key"]),
        "SEM_V2_ADJACENCY_DUPLICATE",
    )
    rejected(
        "body_adjacency_incomplete",
        sidecar,
        lambda item: item["semantic_entities"][0]["topology"][
            "required_adjacent_keys"
        ].pop(),
        "SEM_V2_BODY_ADJACENCY_SET",
    )
    rejected(
        "surface_adjacency_not_owner_only",
        sidecar,
        lambda item: item["semantic_entities"][1]["topology"][
            "required_adjacent_keys"
        ].append(item["semantic_entities"][2]["semantic_key"]),
        "SEM_V2_SURFACE_ADJACENCY_OWNER",
    )
    rejected(
        "critical_orphan",
        sidecar,
        lambda item: item["semantic_entities"][1]["topology"].update(
            {"required_adjacent_keys": []}
        ),
        "SEM_V2_CRITICAL_ORPHAN",
    )
    rejected(
        "semantic_key_duplicate",
        sidecar,
        lambda item: item["semantic_entities"].append(
            copy.deepcopy(item["semantic_entities"][1])
        ),
        "SEM_V2_ENTITY_DUPLICATE",
    )
    rejected(
        "required_key_missing",
        sidecar,
        lambda item: item["required_semantic_keys"].pop(),
        "SEM_V2_REQUIRED_KEY_SET",
    )
    rejected(
        "unexpected_root_key",
        sidecar,
        lambda item: item.update({"unexpected": True}),
        "SEM_V2_ROOT_KEYS",
    )
    rejected(
        "cardinality_invalid",
        sidecar,
        lambda item: item["semantic_entities"][1].update(
            {"expected_cardinality": 2}
        ),
        "SEM_V2_CARDINALITY",
    )
    rejected(
        "dangling_adjacency",
        sidecar,
        lambda item: item["semantic_entities"][1]["topology"].update(
            {"required_adjacent_keys": ["fixture.body.missing.999"]}
        ),
        "SEM_V2_DANGLING_ADJACENCY",
    )
    rejected(
        "root_units_invalid",
        sidecar,
        lambda item: item["units"].update({"length": "m"}),
        "SEM_V2_UNITS",
    )
    rejected(
        "group_member_count",
        sidecar,
        lambda item: item["aggregate_named_selections"]["WALLS"][
            "member_keys"
        ].pop(),
        "SEM_V2_GROUP_MEMBER_COUNT",
    )

    expected_rejected(
        "expected_step_hash",
        sidecar,
        {"step_sha256": u"0" * 64},
        "SEM_V2_EXPECTED_HASH_STEP_SHA256",
    )
    expected_rejected(
        "expected_native_hash",
        sidecar,
        {"handoff_native_sha256": u"0" * 64},
        "SEM_V2_EXPECTED_HASH_HANDOFF_NATIVE_SHA256",
    )
    expected_rejected(
        "expected_profile_hash",
        sidecar,
        {"profile_contract_sha256": u"0" * 64},
        "SEM_V2_EXPECTED_HASH_PROFILE_CONTRACT_SHA256",
    )

    raw = json.dumps(sidecar, sort_keys=True, separators=(",", ":")).encode("utf-8")
    binding = contract.build_binding(raw, sidecar, identity, hashes)
    assert contract.validate_binding(binding, raw, sidecar)
    assert "sidecar_sha256" not in sidecar
    assert binding["sidecar_sha256"] == hashlib.sha256(raw).hexdigest()
    try:
        tampered = raw[:-1] + (b" " if raw[-1:] != b" " else b"\n")
        contract.validate_binding(binding, tampered, sidecar)
    except ValueError as error:
        assert str(error) == "SEM_V2_BINDING_SIDECAR_HASH"
    else:
        raise AssertionError("raw sidecar hash mutation was accepted")
    binding_rejected(
        "binding_step_hash",
        binding,
        raw,
        sidecar,
        lambda item: item.update({"step_sha256": u"0" * 64}),
        "SEM_V2_BINDING_STEP_HASH",
    )
    binding_rejected(
        "binding_native_hash",
        binding,
        raw,
        sidecar,
        lambda item: item.update({"handoff_native_sha256": u"0" * 64}),
        "SEM_V2_BINDING_NATIVE_HASH",
    )
    binding_rejected(
        "binding_profile_hash",
        binding,
        raw,
        sidecar,
        lambda item: item.update({"profile_contract_sha256": u"0" * 64}),
        "SEM_V2_BINDING_PROFILE_HASH",
    )

    required_codes = {
        "SEM_V2_ENTITY_KEYS",
        "SEM_V2_FEATURE_KEY_DUPLICATE",
        "SEM_V2_FEATURE_KEY_FORMAT",
        "SEM_V2_SURFACE_GEOMETRY",
        "SEM_V2_SURFACE_DIRECTION",
        "SEM_V2_SURFACE_MATCH_STRUCTURE",
        "SEM_V2_ENTITY_UNITS",
        "SEM_V2_SURFACE_OWNER_BODY",
        "SEM_V2_ADJACENCY_DUPLICATE",
        "SEM_V2_BODY_ADJACENCY_SET",
        "SEM_V2_SURFACE_ADJACENCY_OWNER",
        "SEM_V2_CRITICAL_ORPHAN",
        "SEM_V2_ENTITY_DUPLICATE",
        "SEM_V2_REQUIRED_KEY_SET",
        "SEM_V2_ROOT_KEYS",
        "SEM_V2_CARDINALITY",
        "SEM_V2_DANGLING_ADJACENCY",
        "SEM_V2_UNITS",
        "SEM_V2_GROUP_MEMBER_COUNT",
        "SEM_V2_EXPECTED_HASH_STEP_SHA256",
        "SEM_V2_EXPECTED_HASH_HANDOFF_NATIVE_SHA256",
        "SEM_V2_EXPECTED_HASH_PROFILE_CONTRACT_SHA256",
        "SEM_V2_BINDING_SIDECAR_HASH",
        "SEM_V2_BINDING_STEP_HASH",
        "SEM_V2_BINDING_NATIVE_HASH",
        "SEM_V2_BINDING_PROFILE_HASH",
    }
    judgment_path = os.path.join(
        os.path.dirname(__file__), "ajm005_semantic_judgment_v2.json"
    )
    with open(judgment_path, "r") as handle:
        judgment = json.load(handle)
    assert set(judgment["required_negative_codes"]) == required_codes
    assert real_artifact_regression(identity, hashes)

    print(
        "AJM005_SEMANTIC_SIDECAR_V2_NEGATIVE_TESTS=PASS cases=%d real_artifacts=2"
        % len(required_codes)
    )


if __name__ == "__main__":
    main()

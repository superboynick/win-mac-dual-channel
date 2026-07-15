"""Python 2/3 compatible AJM STEP semantic-sidecar v2 contract helpers."""

from __future__ import print_function

import hashlib
import json
import math
import re


SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SEMANTIC_KEY_RE = re.compile(
    r"^fixture\.(?:body\.fluid|surface\.(?:inlet|outlet|wall))\.\d{3}$"
)
FEATURE_KEY_RE = re.compile(
    r"^fixture\.feature\.(?:fluid-body|inlet|outlet|wall)\.\d{3}$"
)
try:
    STRING_TYPES = (basestring,)  # noqa: F821 - defined by Python 2 / IronPython 2.
except NameError:
    STRING_TYPES = (str,)
try:
    INTEGER_TYPES = (int, long)  # noqa: F821 - defined by Python 2 / IronPython 2.
except NameError:
    INTEGER_TYPES = (int,)
ROOT_KEYS = {
    "schema_version",
    "contract_id",
    "scope",
    "configuration_id",
    "route",
    "producer",
    "contract_hashes",
    "units",
    "source_artifacts",
    "cell_frames",
    "expected_body_count",
    "expected_face_count",
    "required_semantic_keys",
    "semantic_entities",
    "aggregate_named_selections",
    "partition_invariants",
}
ENTITY_KEYS = {
    "semantic_key",
    "feature_key",
    "entity_kind",
    "owner_key",
    "cell_index",
    "scope_index",
    "local_frame_id",
    "local_coordinates_mm",
    "geometry_type",
    "direction_constraint",
    "match_constraints",
    "topology",
    "expected_cardinality",
    "units",
    "artifact_hashes",
    "profile_contract_sha256",
    "solver_named_selection",
}


def _bytes(value):
    rendered = json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    )
    if not isinstance(rendered, bytes):
        rendered = rendered.encode("utf-8")
    return rendered


def _sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def _require(condition, code):
    if not condition:
        raise ValueError(code)


def _is_number(value):
    return (
        isinstance(value, INTEGER_TYPES + (float,))
        and not isinstance(value, bool)
        and not math.isnan(float(value))
        and not math.isinf(float(value))
    )


def _is_vector(value, length=3):
    return (
        isinstance(value, list)
        and len(value) == length
        and all(_is_number(item) for item in value)
    )


def _is_sha(value):
    return isinstance(value, STRING_TYPES) and SHA256_RE.match(value) is not None


def _parse_center(value):
    if isinstance(value, STRING_TYPES):
        parts = value.split()
    else:
        parts = value
    _require(isinstance(parts, (list, tuple)) and len(parts) == 3, "SEM_V2_CENTER")
    return [float(item) for item in parts]


def _surface_geometry_type(label, center, area):
    if label == "INLET":
        return "PLANAR_CIRCULAR_FACE"
    if label == "OUTLET":
        return "PLANAR_RECTANGULAR_FACE"
    if abs(float(area) - 6.283185307179586) <= 0.02 and abs(center[2] - 0.5) <= 0.02:
        return "CYLINDRICAL_FACE"
    return "PLANAR_FACE"


def _wall_reference_normal(center, geometry_type):
    if geometry_type == "CYLINDRICAL_FACE":
        return [1.0, 0.0, 0.0]
    if abs(center[0] - 2.0) <= 0.02:
        return [-1.0, 0.0, 0.0]
    if abs(center[0] - 18.0) <= 0.02:
        return [1.0, 0.0, 0.0]
    if abs(center[1] - 2.0) <= 0.02 or abs(center[1] - 3.0) <= 0.02:
        return [0.0, -1.0, 0.0]
    if abs(center[1] - 8.0) <= 0.02 or abs(center[1] - 7.0) <= 0.02:
        return [0.0, 1.0, 0.0]
    if abs(center[2] - 3.0) <= 0.02 or abs(center[2] - 2.5) <= 0.02:
        return [0.0, 0.0, 1.0]
    if abs(center[2] - 1.0) <= 0.02 or abs(center[2] - 1.5) <= 0.02:
        return [0.0, 0.0, -1.0]
    raise ValueError("SEM_V2_FIXTURE_WALL_DIRECTION_UNRESOLVED")


def _normal_constraint(label, center, geometry_type):
    if label == "INLET":
        return {"mode": "AXIS_ALIGNED", "vector": [0.0, 0.0, -1.0], "tolerance_deg": 1.0}
    if label == "OUTLET":
        return {"mode": "AXIS_ALIGNED", "vector": [1.0, 0.0, 0.0], "tolerance_deg": 1.0}
    return {
        "mode": "OUTWARD_FROM_OWNER",
        "vector": _wall_reference_normal(center, geometry_type),
        "tolerance_deg": 5.0,
    }


def _solver_edge_count(label, center, geometry_type):
    if label == "INLET":
        return 2
    if label == "OUTLET" or geometry_type == "CYLINDRICAL_FACE":
        return 4
    if abs(center[0] - 18.0) <= 0.02 and abs(center[1] - 5.0) <= 0.02:
        return 8
    if (
        abs(center[0] - 10.0) <= 0.02
        and abs(center[1] - 5.0) <= 0.02
        and abs(center[2] - 1.0) <= 0.02
    ):
        return 5
    return 4


def build_fixture_sidecar(face_details, source_files, identity, contract_hashes):
    body_key = "fixture.body.fluid.001"
    ordered = sorted(
        face_details,
        key=lambda item: (
            str(item["label"]),
            tuple(_parse_center(item["center_mm"])),
            float(item["area_mm2"]),
        ),
    )
    counters = {"INLET": 0, "OUTLET": 0, "WALLS": 0}
    surfaces = []
    groups = {"INLET": [], "OUTLET": [], "WALLS": []}
    for item in ordered:
        label = str(item["label"])
        _require(label in counters, "SEM_V2_LABEL")
        counters[label] += 1
        stem = {"INLET": "inlet", "OUTLET": "outlet", "WALLS": "wall"}[label]
        semantic_key = "fixture.surface.%s.%03d" % (stem, counters[label])
        center = _parse_center(item["center_mm"])
        area = float(item["area_mm2"])
        geometry_type = _surface_geometry_type(label, center, area)
        groups[label].append(semantic_key)
        surfaces.append(
            {
                "semantic_key": semantic_key,
                "feature_key": "fixture.feature.%s.%03d" % (stem, counters[label]),
                "entity_kind": "SURFACE",
                "owner_key": body_key,
                "cell_index": None,
                "scope_index": "GLOBAL",
                "local_frame_id": "GLOBAL",
                "local_coordinates_mm": center,
                "geometry_type": geometry_type,
                "direction_constraint": _normal_constraint(
                    label, center, geometry_type
                ),
                "match_constraints": {
                    "centroid_mm": center,
                    "centroid_tolerance_mm": (
                        0.10 if geometry_type == "CYLINDRICAL_FACE" else 0.02
                    ),
                    "authoring_area_mm2": area,
                    "authoring_area_role": "DIAGNOSTIC_ONLY",
                    "solver_surface_type": (
                        "GeoSurfaceCylinder"
                        if geometry_type == "CYLINDRICAL_FACE"
                        else "GeoSurfacePlane"
                    ),
                    "solver_edge_count": _solver_edge_count(
                        label, center, geometry_type
                    ),
                },
                "topology": {
                    "required_adjacent_keys": [body_key],
                    "critical": label in ("INLET", "OUTLET"),
                    "allow_isolated": False,
                },
                "expected_cardinality": 1,
                "units": {"coordinate": "mm", "area": "mm^2"},
                "artifact_hashes": {
                    "handoff_native_sha256": source_files["handoff_native"]["sha256"],
                    "step_sha256": source_files["step"]["sha256"],
                },
                "profile_contract_sha256": identity["profile_contract_sha256"],
                "solver_named_selection": label,
            }
        )
    surface_keys = [item["semantic_key"] for item in surfaces]
    body = {
        "semantic_key": body_key,
        "feature_key": "fixture.feature.fluid-body.001",
        "entity_kind": "BODY",
        "owner_key": None,
        "cell_index": None,
        "scope_index": "GLOBAL",
        "local_frame_id": "GLOBAL",
        "local_coordinates_mm": [11.0, 5.0, 1.5],
        "geometry_type": "SOLID_FLUID_BODY",
        "direction_constraint": {
            "mode": "NOT_APPLICABLE_BODY",
            "vector": None,
            "tolerance_deg": 0.0,
        },
        "match_constraints": {
            "bbox_min_mm": [2.0, 2.0, 0.0],
            "bbox_max_mm": [20.0, 8.0, 3.0],
            "volume_mm3": 203.1415926535898,
            "volume_tolerance_mm3": 0.02,
        },
        "topology": {
            "required_adjacent_keys": surface_keys,
            "critical": True,
            "allow_isolated": False,
        },
        "expected_cardinality": 1,
        "units": {"coordinate": "mm", "volume": "mm^3"},
        "artifact_hashes": {
            "handoff_native_sha256": source_files["handoff_native"]["sha256"],
            "step_sha256": source_files["step"]["sha256"],
        },
        "profile_contract_sha256": identity["profile_contract_sha256"],
        "solver_named_selection": "FLUID_BODY",
    }
    sidecar = {
        "schema_version": 2,
        "contract_id": "AJM_STEP_SEMANTIC_SIDECAR_V2",
        "scope": "DISPOSABLE_CAPABILITY_FIXTURE_ONLY",
        "configuration_id": "AJM005_T1_FIXTURE_V2",
        "route": {
            "cad_authoring": "SPACECLAIM_SIGNED_SCRIPT_PARAMETRIC",
            "solver_handoff": "HASH_BOUND_STEP_SEMANTIC_SIDECAR",
            "external_native_attach": "NOT_PROVEN",
            "native_parameterization": "NOT_PROVEN",
            "native_named_selection_transfer": "NOT_PROVEN",
        },
        "producer": identity,
        "contract_hashes": contract_hashes,
        "units": {"length": "mm", "area": "mm^2", "volume": "mm^3", "angle": "deg"},
        "source_artifacts": source_files,
        "cell_frames": [
            {
                "frame_id": "GLOBAL",
                "cell_index": None,
                "origin_mm": [0.0, 0.0, 0.0],
                "axes": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
            }
        ],
        "expected_body_count": 1,
        "expected_face_count": 13,
        "required_semantic_keys": [body_key] + surface_keys,
        "semantic_entities": [body] + surfaces,
        "aggregate_named_selections": {
            "INLET": {"expected_cardinality": 1, "member_keys": groups["INLET"]},
            "OUTLET": {"expected_cardinality": 1, "member_keys": groups["OUTLET"]},
            "WALLS": {"expected_cardinality": 11, "member_keys": groups["WALLS"]},
        },
        "partition_invariants": {
            "pairwise_disjoint": True,
            "full_surface_coverage": True,
            "critical_surfaces_non_orphan": True,
        },
    }
    return sidecar


def validate_sidecar(sidecar, expected=None):
    expected = expected or {}
    _require(isinstance(sidecar, dict) and set(sidecar) == ROOT_KEYS, "SEM_V2_ROOT_KEYS")
    _require(sidecar["schema_version"] == 2, "SEM_V2_SCHEMA_VERSION")
    _require(sidecar["contract_id"] == "AJM_STEP_SEMANTIC_SIDECAR_V2", "SEM_V2_CONTRACT_ID")
    _require(sidecar["scope"] == "DISPOSABLE_CAPABILITY_FIXTURE_ONLY", "SEM_V2_SCOPE")
    route = sidecar["route"]
    _require(
        route
        == {
            "cad_authoring": "SPACECLAIM_SIGNED_SCRIPT_PARAMETRIC",
            "solver_handoff": "HASH_BOUND_STEP_SEMANTIC_SIDECAR",
            "external_native_attach": "NOT_PROVEN",
            "native_parameterization": "NOT_PROVEN",
            "native_named_selection_transfer": "NOT_PROVEN",
        },
        "SEM_V2_ROUTE",
    )
    _require(
        sidecar["units"]
        == {"length": "mm", "area": "mm^2", "volume": "mm^3", "angle": "deg"},
        "SEM_V2_UNITS",
    )
    producer = sidecar["producer"]
    _require(
        set(producer)
        == {"git_head", "profile_id", "profile_contract_sha256", "script_sha256", "base_script_sha256"},
        "SEM_V2_PRODUCER_KEYS",
    )
    _require(
        isinstance(producer["git_head"], STRING_TYPES)
        and re.match(r"^[0-9a-f]{40}$", producer["git_head"]) is not None,
        "SEM_V2_GIT_HEAD",
    )
    _require(
        isinstance(producer["profile_id"], STRING_TYPES)
        and producer["profile_id"] == "ajm005-spaceclaim-cad-t1-v2",
        "SEM_V2_PRODUCER_PROFILE",
    )
    for key in ("profile_contract_sha256", "script_sha256", "base_script_sha256"):
        _require(_is_sha(producer[key]), "SEM_V2_PRODUCER_HASH")
    contract_hashes = sidecar["contract_hashes"]
    _require(
        set(contract_hashes)
        == {"route_contract_sha256", "schema_sha256", "judgment_sha256", "validator_sha256"},
        "SEM_V2_CONTRACT_HASH_KEYS",
    )
    _require(all(_is_sha(value) for value in contract_hashes.values()), "SEM_V2_CONTRACT_HASH")
    source = sidecar["source_artifacts"]
    _require(set(source) == {"full_native", "handoff_native", "step"}, "SEM_V2_SOURCE_KEYS")
    expected_source_paths = {
        "full_native": "spaceclaim_cad_t1_full.scdocx",
        "handoff_native": "spaceclaim_cad_t1.scdocx",
        "step": "spaceclaim_cad_t1.step",
    }
    for name, item in source.items():
        _require(set(item) == {"relative_path", "size", "sha256"}, "SEM_V2_SOURCE_FIELDS")
        _require(
            isinstance(item["relative_path"], STRING_TYPES)
            and item["relative_path"] == expected_source_paths[name],
            "SEM_V2_SOURCE_PATH",
        )
        _require(
            isinstance(item["size"], INTEGER_TYPES)
            and not isinstance(item["size"], bool)
            and item["size"] > 0,
            "SEM_V2_SOURCE_SIZE",
        )
        _require(_is_sha(item["sha256"]), "SEM_V2_SOURCE_HASH")
    frames = sidecar["cell_frames"]
    _require(
        isinstance(frames, list)
        and len(frames) == 1
        and set(frames[0]) == {"frame_id", "cell_index", "origin_mm", "axes"}
        and frames[0]["frame_id"] == "GLOBAL"
        and frames[0]["cell_index"] is None
        and frames[0]["origin_mm"] == [0.0, 0.0, 0.0]
        and frames[0]["axes"]
        == [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
        "SEM_V2_GLOBAL_FRAME",
    )
    _require(sidecar["configuration_id"] == "AJM005_T1_FIXTURE_V2", "SEM_V2_CONFIGURATION")
    required = sidecar["required_semantic_keys"]
    entities = sidecar["semantic_entities"]
    _require(
        isinstance(required, list)
        and all(isinstance(key, STRING_TYPES) for key in required)
        and len(required) == len(set(required)),
        "SEM_V2_REQUIRED_DUPLICATE",
    )
    _require(isinstance(entities, list), "SEM_V2_ENTITIES")
    _require(
        all(isinstance(item, dict) and set(item) == ENTITY_KEYS for item in entities),
        "SEM_V2_ENTITY_KEYS",
    )
    entity_keys = [item.get("semantic_key") for item in entities if isinstance(item, dict)]
    _require(len(entity_keys) == len(entities) and len(entity_keys) == len(set(entity_keys)), "SEM_V2_ENTITY_DUPLICATE")
    _require(
        all(isinstance(key, STRING_TYPES) and SEMANTIC_KEY_RE.match(key) for key in entity_keys),
        "SEM_V2_SEMANTIC_KEY_FORMAT",
    )
    _require(set(required) == set(entity_keys), "SEM_V2_REQUIRED_KEY_SET")
    by_key = dict((item["semantic_key"], item) for item in entities)
    feature_keys = [item.get("feature_key") for item in entities]
    _require(
        all(isinstance(key, STRING_TYPES) and FEATURE_KEY_RE.match(key) for key in feature_keys),
        "SEM_V2_FEATURE_KEY_FORMAT",
    )
    _require(len(feature_keys) == len(set(feature_keys)), "SEM_V2_FEATURE_KEY_DUPLICATE")
    body_keys = [
        item["semantic_key"] for item in entities if item.get("entity_kind") == "BODY"
    ]
    surface_keys = [
        item["semantic_key"] for item in entities if item.get("entity_kind") == "SURFACE"
    ]
    _require(len(body_keys) == sidecar["expected_body_count"] == 1, "SEM_V2_BODY_COUNT")
    _require(len(surface_keys) == sidecar["expected_face_count"] == 13, "SEM_V2_FACE_COUNT")
    body_key = body_keys[0]
    for entity in entities:
        _require(set(entity) == ENTITY_KEYS, "SEM_V2_ENTITY_KEYS")
        _require(entity["entity_kind"] in ("BODY", "SURFACE"), "SEM_V2_ENTITY_KIND")
        _require(entity["cell_index"] is None and entity["scope_index"] == "GLOBAL", "SEM_V2_CELL_SCOPE")
        _require(entity["local_frame_id"] == "GLOBAL", "SEM_V2_LOCAL_FRAME")
        _require(_is_vector(entity["local_coordinates_mm"]), "SEM_V2_LOCAL_COORDINATES")
        _require(entity["expected_cardinality"] == 1, "SEM_V2_CARDINALITY")
        _require(entity["profile_contract_sha256"] == producer["profile_contract_sha256"], "SEM_V2_PROFILE_HASH")
        hashes = entity["artifact_hashes"]
        _require(
            set(hashes)
            == {
                "handoff_native_sha256",
                "step_sha256",
            }
            and hashes.get("handoff_native_sha256") == source["handoff_native"]["sha256"]
            and hashes.get("step_sha256") == source["step"]["sha256"],
            "SEM_V2_ENTITY_ARTIFACT_HASH",
        )
        topology = entity["topology"]
        _require(
            set(topology) == {"required_adjacent_keys", "critical", "allow_isolated"},
            "SEM_V2_TOPOLOGY_KEYS",
        )
        adjacency = topology["required_adjacent_keys"]
        _require(isinstance(adjacency, list), "SEM_V2_ADJACENCY_TYPE")
        _require(len(adjacency) == len(set(adjacency)), "SEM_V2_ADJACENCY_DUPLICATE")
        _require(entity["semantic_key"] not in adjacency, "SEM_V2_SELF_ADJACENCY")
        _require(all(key in by_key for key in adjacency), "SEM_V2_DANGLING_ADJACENCY")
        if topology["critical"] is True:
            _require(adjacency and topology["allow_isolated"] is False, "SEM_V2_CRITICAL_ORPHAN")
        else:
            _require(adjacency or topology["allow_isolated"] is True, "SEM_V2_ORPHAN")
        direction = entity["direction_constraint"]
        _require(
            isinstance(direction, dict)
            and set(direction) == {"mode", "vector", "tolerance_deg"}
            and _is_number(direction["tolerance_deg"])
            and float(direction["tolerance_deg"]) >= 0.0,
            "SEM_V2_DIRECTION_STRUCTURE",
        )
        match = entity["match_constraints"]
        if entity["entity_kind"] == "BODY":
            _require(entity["semantic_key"] == "fixture.body.fluid.001", "SEM_V2_BODY_KEY")
            _require(entity["feature_key"] == "fixture.feature.fluid-body.001", "SEM_V2_BODY_FEATURE_KEY")
            _require(entity["owner_key"] is None, "SEM_V2_BODY_OWNER")
            _require(entity["solver_named_selection"] == "FLUID_BODY", "SEM_V2_BODY_SELECTION")
            _require(entity["geometry_type"] == "SOLID_FLUID_BODY", "SEM_V2_BODY_GEOMETRY")
            _require(
                direction
                == {"mode": "NOT_APPLICABLE_BODY", "vector": None, "tolerance_deg": 0.0},
                "SEM_V2_BODY_DIRECTION",
            )
            _require(
                isinstance(match, dict)
                and set(match)
                == {"bbox_min_mm", "bbox_max_mm", "volume_mm3", "volume_tolerance_mm3"}
                and _is_vector(match["bbox_min_mm"])
                and _is_vector(match["bbox_max_mm"])
                and all(
                    float(match["bbox_min_mm"][index])
                    < float(match["bbox_max_mm"][index])
                    for index in range(3)
                )
                and _is_number(match["volume_mm3"])
                and float(match["volume_mm3"]) > 0.0
                and _is_number(match["volume_tolerance_mm3"])
                and float(match["volume_tolerance_mm3"]) > 0.0,
                "SEM_V2_BODY_MATCH_STRUCTURE",
            )
            _require(
                entity["units"] == {"coordinate": "mm", "volume": "mm^3"},
                "SEM_V2_ENTITY_UNITS",
            )
            _require(set(adjacency) == set(surface_keys), "SEM_V2_BODY_ADJACENCY_SET")
        else:
            selection = entity["solver_named_selection"]
            _require(selection in ("INLET", "OUTLET", "WALLS"), "SEM_V2_SURFACE_SELECTION")
            stem = {"INLET": "inlet", "OUTLET": "outlet", "WALLS": "wall"}[selection]
            suffix = entity["semantic_key"].rsplit(".", 1)[-1]
            _require(
                entity["semantic_key"] == "fixture.surface.%s.%s" % (stem, suffix)
                and entity["feature_key"] == "fixture.feature.%s.%s" % (stem, suffix),
                "SEM_V2_SURFACE_STABLE_KEYS",
            )
            _require(
                entity["owner_key"] == body_key
                and by_key[entity["owner_key"]]["entity_kind"] == "BODY",
                "SEM_V2_SURFACE_OWNER_BODY",
            )
            _require(adjacency == [body_key], "SEM_V2_SURFACE_ADJACENCY_OWNER")
            _require(
                entity["units"] == {"coordinate": "mm", "area": "mm^2"},
                "SEM_V2_ENTITY_UNITS",
            )
            _require(
                isinstance(match, dict)
                and set(match)
                == {
                    "centroid_mm",
                    "centroid_tolerance_mm",
                    "authoring_area_mm2",
                    "authoring_area_role",
                    "solver_surface_type",
                    "solver_edge_count",
                }
                and _is_vector(match["centroid_mm"])
                and match["centroid_mm"] == entity["local_coordinates_mm"]
                and _is_number(match["centroid_tolerance_mm"])
                and float(match["centroid_tolerance_mm"]) > 0.0
                and _is_number(match["authoring_area_mm2"])
                and float(match["authoring_area_mm2"]) > 0.0
                and match["authoring_area_role"] == "DIAGNOSTIC_ONLY"
                and match["solver_surface_type"]
                in ("GeoSurfacePlane", "GeoSurfaceCylinder")
                and isinstance(match["solver_edge_count"], INTEGER_TYPES)
                and not isinstance(match["solver_edge_count"], bool)
                and match["solver_edge_count"] > 0,
                "SEM_V2_SURFACE_MATCH_STRUCTURE",
            )
            allowed_geometry = {
                "INLET": {"PLANAR_CIRCULAR_FACE"},
                "OUTLET": {"PLANAR_RECTANGULAR_FACE"},
                "WALLS": {"PLANAR_FACE", "CYLINDRICAL_FACE"},
            }
            _require(
                entity["geometry_type"] in allowed_geometry[selection],
                "SEM_V2_SURFACE_GEOMETRY",
            )
            _require(
                match["solver_surface_type"]
                == (
                    "GeoSurfaceCylinder"
                    if entity["geometry_type"] == "CYLINDRICAL_FACE"
                    else "GeoSurfacePlane"
                ),
                "SEM_V2_SURFACE_MATCH_GEOMETRY",
            )
            if selection == "INLET":
                expected_direction = {
                    "mode": "AXIS_ALIGNED",
                    "vector": [0.0, 0.0, -1.0],
                    "tolerance_deg": 1.0,
                }
            elif selection == "OUTLET":
                expected_direction = {
                    "mode": "AXIS_ALIGNED",
                    "vector": [1.0, 0.0, 0.0],
                    "tolerance_deg": 1.0,
                }
            else:
                expected_direction = {
                    "mode": "OUTWARD_FROM_OWNER",
                    "vector": _wall_reference_normal(
                        match["centroid_mm"], entity["geometry_type"]
                    ),
                    "tolerance_deg": 5.0,
                }
            _require(direction == expected_direction, "SEM_V2_SURFACE_DIRECTION")
            _require(
                entity["semantic_key"] in by_key[body_key]["topology"]["required_adjacent_keys"],
                "SEM_V2_BIDIRECTIONAL_ADJACENCY",
            )
    groups = sidecar["aggregate_named_selections"]
    _require(set(groups) == {"INLET", "OUTLET", "WALLS"}, "SEM_V2_GROUP_KEYS")
    members = []
    expected_counts = {"INLET": 1, "OUTLET": 1, "WALLS": 11}
    for name, expected_count in expected_counts.items():
        group = groups[name]
        _require(set(group) == {"expected_cardinality", "member_keys"}, "SEM_V2_GROUP_FIELDS")
        _require(group["expected_cardinality"] == expected_count, "SEM_V2_GROUP_CARDINALITY")
        _require(len(group["member_keys"]) == expected_count, "SEM_V2_GROUP_MEMBER_COUNT")
        _require(all(key in surface_keys for key in group["member_keys"]), "SEM_V2_GROUP_MEMBER_KEY")
        _require(
            all(by_key[key]["solver_named_selection"] == name for key in group["member_keys"]),
            "SEM_V2_GROUP_SELECTION_MISMATCH",
        )
        members.extend(group["member_keys"])
    _require(len(members) == len(set(members)), "SEM_V2_GROUP_OVERLAP")
    _require(set(members) == set(surface_keys), "SEM_V2_GROUP_COVERAGE")
    _require(
        sidecar["partition_invariants"]
        == {
            "pairwise_disjoint": True,
            "full_surface_coverage": True,
            "critical_surfaces_non_orphan": True,
        },
        "SEM_V2_PARTITION_INVARIANTS",
    )
    comparisons = {
        "step_sha256": source["step"]["sha256"],
        "handoff_native_sha256": source["handoff_native"]["sha256"],
        "profile_contract_sha256": producer["profile_contract_sha256"],
        "script_sha256": producer["script_sha256"],
        "route_contract_sha256": contract_hashes["route_contract_sha256"],
        "schema_sha256": contract_hashes["schema_sha256"],
        "judgment_sha256": contract_hashes["judgment_sha256"],
        "validator_sha256": contract_hashes["validator_sha256"],
    }
    _require(set(expected).issubset(set(comparisons)), "SEM_V2_EXPECTED_HASH_KEY")
    for key, actual in comparisons.items():
        if key in expected:
            _require(actual == expected[key], "SEM_V2_EXPECTED_HASH_%s" % key.upper())
    return {
        "required_key_count": len(required),
        "body_key_count": len(body_keys),
        "surface_key_count": len(surface_keys),
        "group_counts": expected_counts,
    }


def build_binding(sidecar_bytes, sidecar, identity, contract_hashes):
    return {
        "schema_version": 1,
        "binding_id": "AJM_STEP_SEMANTIC_BINDING_V2",
        "sidecar_relative_path": "spaceclaim_semantic_sidecar_v2.json",
        "sidecar_size": len(sidecar_bytes),
        "sidecar_sha256": _sha256_bytes(sidecar_bytes),
        "handoff_native_sha256": sidecar["source_artifacts"]["handoff_native"]["sha256"],
        "step_sha256": sidecar["source_artifacts"]["step"]["sha256"],
        "profile_contract_sha256": identity["profile_contract_sha256"],
        "script_sha256": identity["script_sha256"],
        "route_contract_sha256": contract_hashes["route_contract_sha256"],
    }


def validate_binding(binding, sidecar_bytes, sidecar, expected=None):
    expected = expected or {}
    _require(
        set(binding)
        == {
            "schema_version",
            "binding_id",
            "sidecar_relative_path",
            "sidecar_size",
            "sidecar_sha256",
            "handoff_native_sha256",
            "step_sha256",
            "profile_contract_sha256",
            "script_sha256",
            "route_contract_sha256",
        },
        "SEM_V2_BINDING_KEYS",
    )
    _require(binding["schema_version"] == 1, "SEM_V2_BINDING_SCHEMA")
    _require(binding["binding_id"] == "AJM_STEP_SEMANTIC_BINDING_V2", "SEM_V2_BINDING_ID")
    _require(
        binding["sidecar_relative_path"] == "spaceclaim_semantic_sidecar_v2.json",
        "SEM_V2_BINDING_SIDECAR_PATH",
    )
    _require(binding["sidecar_size"] == len(sidecar_bytes), "SEM_V2_BINDING_SIZE")
    _require(binding["sidecar_sha256"] == _sha256_bytes(sidecar_bytes), "SEM_V2_BINDING_SIDECAR_HASH")
    _require(binding["handoff_native_sha256"] == sidecar["source_artifacts"]["handoff_native"]["sha256"], "SEM_V2_BINDING_NATIVE_HASH")
    _require(binding["step_sha256"] == sidecar["source_artifacts"]["step"]["sha256"], "SEM_V2_BINDING_STEP_HASH")
    _require(binding["profile_contract_sha256"] == sidecar["producer"]["profile_contract_sha256"], "SEM_V2_BINDING_PROFILE_HASH")
    _require(binding["script_sha256"] == sidecar["producer"]["script_sha256"], "SEM_V2_BINDING_SCRIPT_HASH")
    _require(binding["route_contract_sha256"] == sidecar["contract_hashes"]["route_contract_sha256"], "SEM_V2_BINDING_ROUTE_HASH")
    _require(set(expected).issubset(set(binding)), "SEM_V2_BINDING_EXPECTED_KEY")
    for key, value in expected.items():
        _require(binding[key] == value, "SEM_V2_BINDING_EXPECTED_%s" % key.upper())
    return True

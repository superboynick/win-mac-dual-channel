"""Generic Python 2/3 AirJet full-product semantic contract engine.

The disposable AJM-005 fixture contract is intentionally separate.  This
module has no product-size, cell-count, body-count, surface-count, or named
selection cardinality constants.  Those values are supplied by a trusted,
hash-pinned configuration contract and are checked again against solver
observations and actual artifact bytes.
"""

from __future__ import print_function

import hashlib
import json
import math
import os
import re
import stat
import sys


SIDECAR_CONTRACT_ID = "AIRJET_FULL_PRODUCT_SEMANTIC_SIDECAR_V1"
BINDING_CONTRACT_ID = "AIRJET_FULL_PRODUCT_SEMANTIC_BINDING_V1"
OBSERVATION_CONTRACT_ID = "AIRJET_FULL_PRODUCT_SEMANTIC_OBSERVATION_V1"
TRUSTED_CONTRACT_ID = "AIRJET_FULL_PRODUCT_SEMANTIC_TRUSTED_CONFIGURATION_V1"
CAMPAIGN_CONTRACT_ID = "AIRJET_FULL_PRODUCT_SEMANTIC_CAMPAIGN_V1"
BLUEPRINT_CONTRACT_ID = "AIRJET_FULL_PRODUCT_TRUSTED_BLUEPRINT_V1"

try:
    STRING_TYPES = (basestring,)  # noqa: F821 - Python 2 / IronPython 2.
except NameError:
    STRING_TYPES = (str,)
try:
    INTEGER_TYPES = (int, long)  # noqa: F821 - Python 2 / IronPython 2.
except NameError:
    INTEGER_TYPES = (int,)
if sys.version_info[0] < 3:
    BINARY_TYPES = STRING_TYPES + (bytes,)
else:
    BINARY_TYPES = (bytes,)

SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
LOWER_ID_RE = re.compile(r"^[a-z][a-z0-9_-]{0,63}$")
UPPER_ID_RE = re.compile(r"^[A-Z][A-Z0-9_]{0,63}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
GIT_HEAD_RE = re.compile(r"^[0-9a-f]{40}$")
SOURCE_VARIANT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9+_.-]{0,127}$")

ROOT_KEYS = {
    "schema_version",
    "contract_id",
    "scope",
    "configuration",
    "producer",
    "contract_hashes",
    "units",
    "source_artifacts",
    "frames",
    "entities",
    "groups",
    "partitions",
}
CONFIGURATION_KEYS = {
    "configuration_id",
    "product_id",
    "variant_id",
    "key_namespace",
    "root_frame_id",
    "cell_indices",
    "expected_entity_cardinality",
    "required_semantic_keys",
    "required_group_keys",
    "required_partition_keys",
}
PRODUCER_KEYS = {
    "git_head",
    "profile_id",
    "profile_contract_sha256",
    "script_sha256",
    "case_id",
    "job_id",
    "output_root_id",
}
FRAME_KEYS = {"frame_id", "parent_frame_id", "cell_index", "origin_mm", "axes"}
ENTITY_KEYS = {
    "semantic_key",
    "feature_key",
    "entity_kind",
    "owner_key",
    "cell_index",
    "local_frame_id",
    "local_coordinates_mm",
    "geometry_type",
    "direction_constraint",
    "match_constraints",
    "topology",
    "expected_cardinality",
    "artifact_hashes",
}
DIRECTION_KEYS = {"mode", "vector", "tolerance_deg"}
MATCH_KEYS = {
    "centroid_mm",
    "centroid_tolerance_mm",
    "measure_kind",
    "measure_value",
    "measure_tolerance",
    "measure_unit",
    "measure_role",
    "bbox_min_mm",
    "bbox_max_mm",
    "solver_geometry_type",
    "edge_count",
}
TOPOLOGY_KEYS = {"required_adjacent_keys", "critical", "allow_isolated"}
GROUP_KEYS = {
    "group_key",
    "solver_name",
    "entity_kind",
    "member_keys",
    "expected_cardinality",
    "partition_family",
}
PARTITION_KEYS = {
    "partition_key",
    "entity_kind",
    "group_keys",
    "universe_keys",
    "require_pairwise_disjoint",
    "require_full_coverage",
}
TRUSTED_KEYS = {
    "schema_version",
    "contract_id",
    "configuration",
    "frames",
    "entity_blueprints",
    "blueprint_sha256",
    "producer_contract",
    "observer_contract",
    "contract_hashes",
    "required_contract_hash_keys",
    "artifact_contracts",
    "artifact_root_id",
    "artifact_root_path",
    "sidecar_artifact_ids",
    "sidecar_artifact_id",
    "binding_artifact_id",
    "observation_artifact_id",
    "solver_import_artifact_id",
    "groups",
    "partitions",
}
ENTITY_BLUEPRINT_KEYS = ENTITY_KEYS - {"artifact_hashes"}
RUNTIME_CONTRACT_KEYS = {"profile_id", "profile_contract_sha256", "script_sha256"}
PRODUCER_IDENTITY_KEYS = PRODUCER_KEYS | {
    "terminal_state",
    "artifact_manifest_sha256",
}
OBSERVER_IDENTITY_KEYS = PRODUCER_KEYS | {
    "terminal_state",
    "artifact_manifest_sha256",
    "predecessor_identity",
    "imported_artifact_id",
    "imported_artifact_relative_path",
    "imported_artifact_size",
    "imported_artifact_sha256",
}
BINDING_KEYS = {
    "schema_version",
    "contract_id",
    "configuration_id",
    "sidecar_artifact_id",
    "binding_artifact_id",
    "artifact_identities",
    "producer",
    "contract_hashes",
}
OBSERVATION_KEYS = {
    "schema_version",
    "contract_id",
    "configuration_id",
    "observer",
    "imported_artifact_id",
    "imported_artifact_sha256",
    "entities",
    "groups",
}
OBSERVED_ENTITY_KEYS = {
    "semantic_key",
    "entity_kind",
    "cell_index",
    "local_frame_id",
    "geometry_type",
    "matches",
}
OBSERVED_MATCH_KEYS = {
    "actual_id",
    "local_centroid_mm",
    "solver_geometry_type",
    "edge_count",
    "measure_value",
    "direction_vector",
    "observed_bbox_min_mm",
    "observed_bbox_max_mm",
    "actual_owner_body_id",
    "actual_adjacent_body_ids",
    "actual_boundary_surface_ids",
}
BLUEPRINT_KEYS = {
    "schema_version",
    "contract_id",
    "scope",
    "product_id",
    "source_variant_id",
    "configuration",
    "frames",
    "entity_blueprints",
    "groups",
    "partitions",
    "producer_profile_id",
    "observer_profile_id",
    "required_contract_hash_keys",
    "artifact_contracts",
    "artifact_root_id",
    "sidecar_artifact_ids",
    "sidecar_artifact_id",
    "binding_artifact_id",
    "observation_artifact_id",
    "solver_import_artifact_id",
}
CAMPAIGN_KEYS = {
    "schema_version",
    "contract_id",
    "scope",
    "product_id",
    "expected_variant_count",
    "source_contracts",
    "variant_contracts",
}
CAMPAIGN_SOURCE_KEYS = {"contract_key", "git_path", "sha256"}
CAMPAIGN_VARIANT_KEYS = {
    "source_variant_id",
    "variant_id",
    "configuration_id",
    "cell_count",
    "semantic_entity_count",
    "blueprint_path",
    "blueprint_sha256",
}


def _require(condition, code):
    if not condition:
        raise ValueError(code)


def _exact_dict(value, keys, code):
    _require(isinstance(value, dict) and set(value) == set(keys), code)


def _is_string(value):
    return isinstance(value, STRING_TYPES)


def _is_integer(value):
    return isinstance(value, INTEGER_TYPES) and not isinstance(value, bool)


def _is_number(value):
    if isinstance(value, bool) or not isinstance(value, INTEGER_TYPES + (float,)):
        return False
    candidate = float(value)
    return not math.isnan(candidate) and not math.isinf(candidate)


def _is_vector(value):
    return isinstance(value, list) and len(value) == 3 and all(
        _is_number(item) for item in value
    )


def _is_safe_id(value):
    return _is_string(value) and SAFE_ID_RE.match(value) is not None


def _is_lower_id(value):
    return _is_string(value) and LOWER_ID_RE.match(value) is not None


def _is_upper_id(value):
    return _is_string(value) and UPPER_ID_RE.match(value) is not None


def _is_sha256(value):
    return _is_string(value) and SHA256_RE.match(value) is not None


def _unique(values):
    try:
        return len(values) == len(set(values))
    except TypeError:
        return False


def _safe_relative_path(value):
    if not _is_string(value) or not value or len(value) > 240:
        return False
    normalized = value.replace("\\", "/")
    if normalized.startswith("/") or re.match(r"^[A-Za-z]:", normalized):
        return False
    parts = normalized.split("/")
    return all(part not in ("", ".", "..") and ":" not in part for part in parts)


def _canonical_json_bytes(value):
    rendered = json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    if not isinstance(rendered, bytes):
        rendered = rendered.encode("ascii")
    return rendered


def _blueprint_payload(trusted):
    return {
        "configuration": trusted["configuration"],
        "frames": trusted["frames"],
        "entity_blueprints": trusted["entity_blueprints"],
        "groups": trusted["groups"],
        "partitions": trusted["partitions"],
    }


def _path_within(path, root):
    normalized_path = os.path.normcase(os.path.realpath(os.path.abspath(path)))
    normalized_root = os.path.normcase(os.path.realpath(os.path.abspath(root)))
    return normalized_path == normalized_root or normalized_path.startswith(
        normalized_root.rstrip("\\/") + os.sep
    )


def _reparse_state(path):
    """Return True/False, or None when Windows reparse state is unknowable."""

    try:
        if os.path.islink(path):
            return True
        attributes = getattr(os.lstat(path), "st_file_attributes", None)
        if attributes is not None:
            return bool(int(attributes) & 0x400)
    except OSError:
        return None
    if os.name != "nt":
        return False
    try:
        import ctypes

        get_attributes = ctypes.windll.kernel32.GetFileAttributesW
        candidate = path
        try:
            candidate = unicode(path)  # noqa: F821 - IronPython/Python 2.
        except NameError:
            candidate = str(path)
        attributes = int(get_attributes(candidate))
        if attributes == -1 or attributes == 0xFFFFFFFF:
            return None
        return bool(attributes & 0x400)
    except Exception:
        try:
            import clr  # noqa: F401 - available only in IronPython.
            from System.IO import File, FileAttributes

            return bool(File.GetAttributes(path) & FileAttributes.ReparsePoint)
        except Exception:
            return None


def _require_no_reparse_chain(root, path):
    _require(_path_within(path, root), "FPSEM_ACTUAL_FILE_ROOT_ESCAPE")
    root_state = _reparse_state(root)
    _require(root_state is not None, "FPSEM_ACTUAL_REPARSE_UNVERIFIED")
    _require(root_state is False, "FPSEM_ACTUAL_REPARSE_POINT")
    relative = os.path.relpath(os.path.abspath(path), os.path.abspath(root))
    _require(relative not in ("", ".") and not relative.startswith(".."), "FPSEM_ACTUAL_FILE_ROOT_ESCAPE")
    cursor = os.path.abspath(root)
    for part in relative.replace("\\", "/").split("/"):
        cursor = os.path.join(cursor, part)
        state = _reparse_state(cursor)
        _require(state is not None, "FPSEM_ACTUAL_REPARSE_UNVERIFIED")
        _require(state is False, "FPSEM_ACTUAL_REPARSE_POINT")


def _require_no_reparse_ancestors(path):
    cursor = os.path.abspath(path)
    while True:
        state = _reparse_state(cursor)
        _require(state is not None, "FPSEM_ACTUAL_REPARSE_UNVERIFIED")
        _require(state is False, "FPSEM_ACTUAL_REPARSE_ANCESTOR")
        parent = os.path.dirname(cursor)
        if not parent or parent == cursor:
            break
        cursor = parent


def _index_records(records, key, duplicate_code, structure_code):
    _require(isinstance(records, list), structure_code)
    result = {}
    for record in records:
        _require(isinstance(record, dict) and key in record, structure_code)
        identifier = record[key]
        _require(identifier not in result, duplicate_code)
        result[identifier] = record
    return result


def _validate_hash_records(records, code_prefix):
    by_key = _index_records(
        records,
        "contract_key",
        code_prefix + "_DUPLICATE",
        code_prefix + "_STRUCTURE",
    )
    _require(bool(by_key), code_prefix + "_EMPTY")
    for item in records:
        _exact_dict(item, {"contract_key", "sha256"}, code_prefix + "_FIELDS")
        _require(_is_lower_id(item["contract_key"]), code_prefix + "_KEY")
        _require(_is_sha256(item["sha256"]), code_prefix + "_SHA256")
    return by_key


def _validate_artifact_records(records, code_prefix):
    by_id = _index_records(
        records,
        "artifact_id",
        code_prefix + "_DUPLICATE",
        code_prefix + "_STRUCTURE",
    )
    _require(bool(by_id), code_prefix + "_EMPTY")
    fields = {"artifact_id", "role", "relative_path", "size", "sha256"}
    for item in records:
        _exact_dict(item, fields, code_prefix + "_FIELDS")
        _require(_is_lower_id(item["artifact_id"]), code_prefix + "_ID")
        _require(_is_upper_id(item["role"]), code_prefix + "_ROLE")
        _require(_safe_relative_path(item["relative_path"]), code_prefix + "_PATH")
        _require(
            _is_integer(item["size"]) and item["size"] > 0,
            code_prefix + "_SIZE",
        )
        _require(_is_sha256(item["sha256"]), code_prefix + "_SHA256")
    return by_id


def _norm(vector):
    return math.sqrt(sum(float(item) * float(item) for item in vector))


def _dot(left, right):
    return sum(float(left[index]) * float(right[index]) for index in range(3))


def _determinant(axes):
    a, b, c = axes
    return (
        float(a[0]) * (float(b[1]) * float(c[2]) - float(b[2]) * float(c[1]))
        - float(a[1]) * (float(b[0]) * float(c[2]) - float(b[2]) * float(c[0]))
        + float(a[2]) * (float(b[0]) * float(c[1]) - float(b[1]) * float(c[0]))
    )


def _validate_axes(axes):
    if not isinstance(axes, list) or len(axes) != 3 or not all(
        _is_vector(axis) for axis in axes
    ):
        return False
    if not all(abs(_norm(axis) - 1.0) <= 1.0e-6 for axis in axes):
        return False
    if any(abs(_dot(axes[left], axes[right])) > 1.0e-6 for left, right in ((0, 1), (0, 2), (1, 2))):
        return False
    return abs(_determinant(axes) - 1.0) <= 1.0e-6


def _stable_semantic_key(namespace, kind, value):
    if not _is_string(value):
        return False
    pattern = r"^%s\.%s\.[a-z][a-z0-9_-]*(?:\.[a-z0-9][a-z0-9_-]*)*$" % (
        re.escape(namespace),
        "body" if kind == "BODY" else "surface",
    )
    return re.match(pattern, value) is not None


def _stable_feature_key(namespace, value):
    if not _is_string(value):
        return False
    pattern = r"^%s\.feature\.[a-z][a-z0-9_-]*(?:\.[a-z0-9][a-z0-9_-]*)*$" % re.escape(namespace)
    return re.match(pattern, value) is not None


def _stable_group_key(namespace, value):
    return _is_string(value) and re.match(
        r"^%s\.group\.[a-z][a-z0-9_-]*(?:\.[a-z0-9][a-z0-9_-]*)*$"
        % re.escape(namespace),
        value,
    ) is not None


def _stable_partition_key(namespace, value):
    return _is_string(value) and re.match(
        r"^%s\.partition\.[a-z][a-z0-9_-]*(?:\.[a-z0-9][a-z0-9_-]*)*$"
        % re.escape(namespace),
        value,
    ) is not None


def _validate_configuration(configuration):
    _exact_dict(configuration, CONFIGURATION_KEYS, "FPSEM_CONFIGURATION_FIELDS")
    for key in ("configuration_id", "product_id", "variant_id", "root_frame_id"):
        _require(_is_safe_id(configuration[key]), "FPSEM_CONFIGURATION_ID")
    namespace = configuration["key_namespace"]
    _require(_is_lower_id(namespace), "FPSEM_KEY_NAMESPACE")
    cells = configuration["cell_indices"]
    _require(
        isinstance(cells, list)
        and bool(cells)
        and _unique(cells)
        and all(_is_integer(item) and item >= 0 for item in cells),
        "FPSEM_CELL_INDICES",
    )
    counts = configuration["expected_entity_cardinality"]
    _exact_dict(counts, {"BODY", "SURFACE"}, "FPSEM_EXPECTED_COUNT_FIELDS")
    _require(
        all(_is_integer(counts[kind]) and counts[kind] > 0 for kind in ("BODY", "SURFACE")),
        "FPSEM_EXPECTED_COUNT_VALUE",
    )
    for key, code in (
        ("required_semantic_keys", "FPSEM_REQUIRED_SEMANTIC_KEYS"),
        ("required_group_keys", "FPSEM_REQUIRED_GROUP_KEYS"),
        ("required_partition_keys", "FPSEM_REQUIRED_PARTITION_KEYS"),
    ):
        values = configuration[key]
        _require(
            isinstance(values, list)
            and _unique(values)
            and all(_is_string(item) for item in values),
            code,
        )
    _require(bool(configuration["required_semantic_keys"]), "FPSEM_REQUIRED_SEMANTIC_EMPTY")
    return namespace


def _validate_producer(producer):
    _exact_dict(producer, PRODUCER_KEYS, "FPSEM_PRODUCER_FIELDS")
    _require(
        _is_string(producer["git_head"])
        and GIT_HEAD_RE.match(producer["git_head"]) is not None,
        "FPSEM_GIT_HEAD",
    )
    for key in ("profile_id", "case_id", "job_id", "output_root_id"):
        _require(_is_safe_id(producer[key]), "FPSEM_PRODUCER_ID")
    for key in ("profile_contract_sha256", "script_sha256"):
        _require(_is_sha256(producer[key]), "FPSEM_PRODUCER_SHA256")


def _validate_frames(frames, configuration):
    by_id = _index_records(frames, "frame_id", "FPSEM_FRAME_DUPLICATE", "FPSEM_FRAME_STRUCTURE")
    root_id = configuration["root_frame_id"]
    _require(root_id in by_id, "FPSEM_ROOT_FRAME_MISSING")
    identity_axes = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
    for frame in frames:
        _exact_dict(frame, FRAME_KEYS, "FPSEM_FRAME_FIELDS")
        _require(_is_safe_id(frame["frame_id"]), "FPSEM_FRAME_ID")
        parent = frame["parent_frame_id"]
        _require(parent is None or _is_safe_id(parent), "FPSEM_FRAME_PARENT")
        cell = frame["cell_index"]
        _require(cell is None or (_is_integer(cell) and cell >= 0), "FPSEM_FRAME_CELL")
        _require(_is_vector(frame["origin_mm"]), "FPSEM_FRAME_ORIGIN")
        _require(_validate_axes(frame["axes"]), "FPSEM_FRAME_AXES")
    root = by_id[root_id]
    _require(
        root["parent_frame_id"] is None
        and root["cell_index"] is None
        and root["origin_mm"] == [0.0, 0.0, 0.0]
        and root["axes"] == identity_axes,
        "FPSEM_ROOT_FRAME_IDENTITY",
    )
    _require(
        len([item for item in frames if item["parent_frame_id"] is None]) == 1,
        "FPSEM_ROOT_FRAME_COUNT",
    )
    configured_cells = set(configuration["cell_indices"])
    observed_cells = set(item["cell_index"] for item in frames if item["cell_index"] is not None)
    _require(observed_cells == configured_cells, "FPSEM_FRAME_CELL_COVERAGE")
    for frame in frames:
        current = frame
        visited = set()
        while current["parent_frame_id"] is not None:
            parent_id = current["parent_frame_id"]
            _require(parent_id in by_id, "FPSEM_FRAME_PARENT_MISSING")
            _require(parent_id not in visited, "FPSEM_FRAME_CYCLE")
            visited.add(parent_id)
            parent = by_id[parent_id]
            if current["cell_index"] is not None and parent["cell_index"] is not None:
                _require(
                    current["cell_index"] == parent["cell_index"],
                    "FPSEM_FRAME_CROSS_CELL_PARENT",
                )
            current = parent
    return by_id


def _validate_direction(direction, entity_kind):
    _exact_dict(direction, DIRECTION_KEYS, "FPSEM_DIRECTION_FIELDS")
    mode = direction["mode"]
    _require(
        mode in ("NOT_APPLICABLE", "AXIS_ALIGNED", "VECTOR", "OUTWARD_FROM_OWNER"),
        "FPSEM_DIRECTION_MODE",
    )
    tolerance = direction["tolerance_deg"]
    _require(
        _is_number(tolerance) and 0.0 <= float(tolerance) <= 180.0,
        "FPSEM_DIRECTION_TOLERANCE",
    )
    vector = direction["vector"]
    if mode in ("AXIS_ALIGNED", "VECTOR"):
        _require(_is_vector(vector) and abs(_norm(vector) - 1.0) <= 1.0e-6, "FPSEM_DIRECTION_VECTOR")
    else:
        _require(vector is None, "FPSEM_DIRECTION_VECTOR_NULL")
    if entity_kind == "BODY":
        _require(mode == "NOT_APPLICABLE", "FPSEM_BODY_DIRECTION")
    else:
        _require(mode != "NOT_APPLICABLE", "FPSEM_SURFACE_DIRECTION")


def _validate_match(match, entity_kind):
    _exact_dict(match, MATCH_KEYS, "FPSEM_MATCH_FIELDS")
    _require(_is_vector(match["centroid_mm"]), "FPSEM_MATCH_CENTROID")
    _require(
        _is_number(match["centroid_tolerance_mm"])
        and float(match["centroid_tolerance_mm"]) > 0.0,
        "FPSEM_MATCH_CENTROID_TOLERANCE",
    )
    kind = match["measure_kind"]
    role = match["measure_role"]
    _require(kind in ("AREA", "VOLUME", "NONE"), "FPSEM_MATCH_MEASURE_KIND")
    _require(role in ("MATCH", "DIAGNOSTIC_ONLY", "NOT_APPLICABLE"), "FPSEM_MATCH_MEASURE_ROLE")
    expected_unit = {"AREA": "mm^2", "VOLUME": "mm^3", "NONE": None}[kind]
    if kind == "NONE":
        _require(
            match["measure_value"] is None
            and match["measure_tolerance"] is None
            and match["measure_unit"] is None
            and role == "NOT_APPLICABLE",
            "FPSEM_MATCH_MEASURE_NONE",
        )
    else:
        _require(
            _is_number(match["measure_value"])
            and float(match["measure_value"]) > 0.0
            and _is_number(match["measure_tolerance"])
            and float(match["measure_tolerance"]) >= 0.0
            and match["measure_unit"] == expected_unit
            and role != "NOT_APPLICABLE",
            "FPSEM_MATCH_MEASURE_VALUE",
        )
    _require(
        (entity_kind == "BODY" and kind in ("VOLUME", "NONE"))
        or (entity_kind == "SURFACE" and kind in ("AREA", "NONE")),
        "FPSEM_MATCH_MEASURE_ENTITY_KIND",
    )
    bbox_min = match["bbox_min_mm"]
    bbox_max = match["bbox_max_mm"]
    _require(
        (bbox_min is None and bbox_max is None)
        or (
            _is_vector(bbox_min)
            and _is_vector(bbox_max)
            and all(float(bbox_min[index]) < float(bbox_max[index]) for index in range(3))
        ),
        "FPSEM_MATCH_BBOX",
    )
    if bbox_min is not None:
        _require(
            all(
                float(bbox_min[index]) <= float(match["centroid_mm"][index])
                <= float(bbox_max[index])
                for index in range(3)
            ),
            "FPSEM_MATCH_CENTROID_OUTSIDE_BBOX",
        )
    _require(_is_safe_id(match["solver_geometry_type"]), "FPSEM_MATCH_SOLVER_GEOMETRY")
    edge_count = match["edge_count"]
    _require(
        edge_count is None or (_is_integer(edge_count) and edge_count >= 0),
        "FPSEM_MATCH_EDGE_COUNT",
    )


def validate_full_product_structure(sidecar):
    """Validate the generic sidecar structure without trusting its identities."""
    _exact_dict(sidecar, ROOT_KEYS, "FPSEM_ROOT_FIELDS")
    _require(sidecar["schema_version"] == 1, "FPSEM_SCHEMA_VERSION")
    _require(sidecar["contract_id"] == SIDECAR_CONTRACT_ID, "FPSEM_CONTRACT_ID")
    _require(sidecar["scope"] == "FULL_PRODUCT", "FPSEM_SCOPE")
    configuration = sidecar["configuration"]
    namespace = _validate_configuration(configuration)
    _validate_producer(sidecar["producer"])
    _validate_hash_records(sidecar["contract_hashes"], "FPSEM_CONTRACT_HASH")
    _require(
        sidecar["units"]
        == {"length": "mm", "area": "mm^2", "volume": "mm^3", "angle": "deg"},
        "FPSEM_UNITS",
    )
    artifacts = _validate_artifact_records(sidecar["source_artifacts"], "FPSEM_SOURCE_ARTIFACT")
    frames = _validate_frames(sidecar["frames"], configuration)

    entities = sidecar["entities"]
    by_key = _index_records(entities, "semantic_key", "FPSEM_SEMANTIC_KEY_DUPLICATE", "FPSEM_ENTITY_STRUCTURE")
    _require(bool(by_key), "FPSEM_ENTITY_EMPTY")
    feature_keys = []
    configured_cells = set(configuration["cell_indices"])
    artifact_ids = set(artifacts)
    for entity in entities:
        _exact_dict(entity, ENTITY_KEYS, "FPSEM_ENTITY_FIELDS")
        kind = entity["entity_kind"]
        _require(kind in ("BODY", "SURFACE"), "FPSEM_ENTITY_KIND")
        _require(_stable_semantic_key(namespace, kind, entity["semantic_key"]), "FPSEM_SEMANTIC_KEY_FORMAT")
        _require(_stable_feature_key(namespace, entity["feature_key"]), "FPSEM_FEATURE_KEY_FORMAT")
        feature_keys.append(entity["feature_key"])
        cell = entity["cell_index"]
        _require(cell is None or cell in configured_cells, "FPSEM_ENTITY_CELL")
        frame_id = entity["local_frame_id"]
        _require(frame_id in frames, "FPSEM_ENTITY_FRAME_MISSING")
        _require(frames[frame_id]["cell_index"] == cell, "FPSEM_ENTITY_FRAME_CELL")
        _require(_is_vector(entity["local_coordinates_mm"]), "FPSEM_ENTITY_LOCAL_COORDINATES")
        _require(_is_upper_id(entity["geometry_type"]), "FPSEM_ENTITY_GEOMETRY_TYPE")
        _validate_direction(entity["direction_constraint"], kind)
        _validate_match(entity["match_constraints"], kind)
        _require(
            entity["match_constraints"]["centroid_mm"] == entity["local_coordinates_mm"],
            "FPSEM_ENTITY_MATCH_COORDINATES",
        )
        topology = entity["topology"]
        _exact_dict(topology, TOPOLOGY_KEYS, "FPSEM_TOPOLOGY_FIELDS")
        adjacency = topology["required_adjacent_keys"]
        _require(
            isinstance(adjacency, list)
            and _unique(adjacency)
            and all(_is_string(item) for item in adjacency),
            "FPSEM_ADJACENCY_LIST",
        )
        _require(entity["semantic_key"] not in adjacency, "FPSEM_ADJACENCY_SELF")
        _require(
            isinstance(topology["critical"], bool)
            and isinstance(topology["allow_isolated"], bool),
            "FPSEM_TOPOLOGY_BOOLEAN",
        )
        if topology["critical"]:
            _require(bool(adjacency) and not topology["allow_isolated"], "FPSEM_CRITICAL_ORPHAN")
        elif not topology["allow_isolated"]:
            _require(bool(adjacency), "FPSEM_ENTITY_ORPHAN")
        _require(
            _is_integer(entity["expected_cardinality"])
            and entity["expected_cardinality"] > 0,
            "FPSEM_ENTITY_CARDINALITY",
        )
        entity_hashes = _index_records(
            entity["artifact_hashes"],
            "artifact_id",
            "FPSEM_ENTITY_ARTIFACT_DUPLICATE",
            "FPSEM_ENTITY_ARTIFACT_STRUCTURE",
        )
        _require(set(entity_hashes) == artifact_ids, "FPSEM_ENTITY_ARTIFACT_SET")
        for item in entity["artifact_hashes"]:
            _exact_dict(item, {"artifact_id", "sha256"}, "FPSEM_ENTITY_ARTIFACT_FIELDS")
            _require(
                item["sha256"] == artifacts[item["artifact_id"]]["sha256"],
                "FPSEM_ENTITY_ARTIFACT_SHA256",
            )
    _require(_unique(feature_keys), "FPSEM_FEATURE_KEY_DUPLICATE")
    _require(
        set(configuration["required_semantic_keys"]) == set(by_key),
        "FPSEM_REQUIRED_SEMANTIC_SET",
    )
    observed_counts = {"BODY": 0, "SURFACE": 0}
    for entity in entities:
        observed_counts[entity["entity_kind"]] += entity["expected_cardinality"]
    _require(
        observed_counts == configuration["expected_entity_cardinality"],
        "FPSEM_ENTITY_CARDINALITY_TOTAL",
    )
    for entity in entities:
        key = entity["semantic_key"]
        adjacency = entity["topology"]["required_adjacent_keys"]
        _require(all(item in by_key for item in adjacency), "FPSEM_ADJACENCY_DANGLING")
        for adjacent_key in adjacency:
            adjacent = by_key[adjacent_key]
            _require(adjacent["entity_kind"] != entity["entity_kind"], "FPSEM_ADJACENCY_KIND")
            _require(
                key in adjacent["topology"]["required_adjacent_keys"],
                "FPSEM_ADJACENCY_ASYMMETRIC",
            )
        if entity["entity_kind"] == "BODY":
            _require(entity["owner_key"] is None, "FPSEM_BODY_OWNER")
        else:
            owner_key = entity["owner_key"]
            _require(owner_key in by_key, "FPSEM_SURFACE_OWNER_MISSING")
            _require(by_key[owner_key]["entity_kind"] == "BODY", "FPSEM_SURFACE_OWNER_NOT_BODY")
            _require(owner_key in adjacency, "FPSEM_SURFACE_OWNER_ADJACENCY")
            _require(key in by_key[owner_key]["topology"]["required_adjacent_keys"], "FPSEM_OWNER_SURFACE_ADJACENCY")

    groups = sidecar["groups"]
    groups_by_key = _index_records(groups, "group_key", "FPSEM_GROUP_DUPLICATE", "FPSEM_GROUP_STRUCTURE")
    _require(set(groups_by_key) == set(configuration["required_group_keys"]), "FPSEM_REQUIRED_GROUP_SET")
    for group in groups:
        _exact_dict(group, GROUP_KEYS, "FPSEM_GROUP_FIELDS")
        _require(_stable_group_key(namespace, group["group_key"]), "FPSEM_GROUP_KEY_FORMAT")
        _require(_is_safe_id(group["solver_name"]), "FPSEM_GROUP_SOLVER_NAME")
        kind = group["entity_kind"]
        _require(kind in ("BODY", "SURFACE"), "FPSEM_GROUP_ENTITY_KIND")
        members = group["member_keys"]
        _require(isinstance(members, list) and bool(members) and _unique(members), "FPSEM_GROUP_MEMBERS")
        _require(all(item in by_key for item in members), "FPSEM_GROUP_MEMBER_MISSING")
        _require(all(by_key[item]["entity_kind"] == kind for item in members), "FPSEM_GROUP_MEMBER_KIND")
        expected = sum(by_key[item]["expected_cardinality"] for item in members)
        _require(
            _is_integer(group["expected_cardinality"])
            and group["expected_cardinality"] == expected,
            "FPSEM_GROUP_CARDINALITY",
        )
        family = group["partition_family"]
        _require(family is None or _is_lower_id(family), "FPSEM_GROUP_PARTITION_FAMILY")

    partitions = sidecar["partitions"]
    partitions_by_key = _index_records(
        partitions,
        "partition_key",
        "FPSEM_PARTITION_DUPLICATE",
        "FPSEM_PARTITION_STRUCTURE",
    )
    _require(
        set(partitions_by_key) == set(configuration["required_partition_keys"]),
        "FPSEM_REQUIRED_PARTITION_SET",
    )
    for partition in partitions:
        _exact_dict(partition, PARTITION_KEYS, "FPSEM_PARTITION_FIELDS")
        _require(_stable_partition_key(namespace, partition["partition_key"]), "FPSEM_PARTITION_KEY_FORMAT")
        kind = partition["entity_kind"]
        _require(kind in ("BODY", "SURFACE"), "FPSEM_PARTITION_ENTITY_KIND")
        group_keys = partition["group_keys"]
        universe = partition["universe_keys"]
        _require(isinstance(group_keys, list) and bool(group_keys) and _unique(group_keys), "FPSEM_PARTITION_GROUPS")
        _require(isinstance(universe, list) and bool(universe) and _unique(universe), "FPSEM_PARTITION_UNIVERSE")
        _require(all(item in groups_by_key for item in group_keys), "FPSEM_PARTITION_GROUP_MISSING")
        _require(all(groups_by_key[item]["entity_kind"] == kind for item in group_keys), "FPSEM_PARTITION_GROUP_KIND")
        _require(all(item in by_key and by_key[item]["entity_kind"] == kind for item in universe), "FPSEM_PARTITION_UNIVERSE_KIND")
        _require(
            partition["require_pairwise_disjoint"] is True
            and partition["require_full_coverage"] is True,
            "FPSEM_PARTITION_RULES",
        )
        collected = []
        for group_key in group_keys:
            collected.extend(groups_by_key[group_key]["member_keys"])
        _require(_unique(collected), "FPSEM_PARTITION_OVERLAP")
        _require(set(collected) == set(universe), "FPSEM_PARTITION_COVERAGE")
    return {
        "cell_count": len(configuration["cell_indices"]),
        "frame_count": len(frames),
        "semantic_key_count": len(by_key),
        "entity_cardinality": observed_counts,
        "group_count": len(groups_by_key),
        "partition_count": len(partitions_by_key),
    }


def _validate_runtime_contract(value, code_prefix):
    _exact_dict(value, RUNTIME_CONTRACT_KEYS, code_prefix + "_FIELDS")
    _require(_is_safe_id(value["profile_id"]), code_prefix + "_PROFILE_ID")
    _require(
        _is_sha256(value["profile_contract_sha256"])
        and _is_sha256(value["script_sha256"]),
        code_prefix + "_SHA256",
    )


def _entity_blueprint(entity):
    return dict((key, entity[key]) for key in ENTITY_BLUEPRINT_KEYS)


def _validate_producer_identity(identity, trusted_contract):
    _exact_dict(identity, PRODUCER_IDENTITY_KEYS, "FPSEM_PRODUCER_IDENTITY_FIELDS")
    _require(identity["terminal_state"] == "PROCESS_EXITED_0", "FPSEM_PRODUCER_TERMINAL_STATE")
    _require(_is_sha256(identity["artifact_manifest_sha256"]), "FPSEM_PRODUCER_MANIFEST_SHA256")
    producer = dict((key, identity[key]) for key in PRODUCER_KEYS)
    _validate_producer(producer)
    _require(
        producer["output_root_id"] == trusted_contract["artifact_root_id"],
        "FPSEM_PRODUCER_OUTPUT_ROOT_ID",
    )
    runtime = trusted_contract["producer_contract"]
    for key in RUNTIME_CONTRACT_KEYS:
        _require(producer[key] == runtime[key], "FPSEM_TRUSTED_PRODUCER_%s" % key.upper())
    return producer


def _validate_observer_identity(identity, producer_identity, trusted_contract):
    _exact_dict(identity, OBSERVER_IDENTITY_KEYS, "FPSEM_OBSERVER_IDENTITY_FIELDS")
    _require(identity["terminal_state"] == "PROCESS_EXITED_0", "FPSEM_OBSERVER_TERMINAL_STATE")
    _require(_is_sha256(identity["artifact_manifest_sha256"]), "FPSEM_OBSERVER_MANIFEST_SHA256")
    observer = dict((key, identity[key]) for key in PRODUCER_KEYS)
    _validate_producer(observer)
    runtime = trusted_contract["observer_contract"]
    for key in RUNTIME_CONTRACT_KEYS:
        _require(observer[key] == runtime[key], "FPSEM_TRUSTED_OBSERVER_%s" % key.upper())
    _require(
        observer["git_head"] == producer_identity["git_head"]
        and observer["case_id"] == producer_identity["case_id"]
        and observer["output_root_id"] == trusted_contract["artifact_root_id"],
        "FPSEM_OBSERVER_RUN_IDENTITY",
    )
    _require(identity["predecessor_identity"] == producer_identity, "FPSEM_OBSERVER_PREDECESSOR")
    _require(_is_lower_id(identity["imported_artifact_id"]), "FPSEM_OBSERVER_IMPORT_ID")
    _require(
        _safe_relative_path(identity["imported_artifact_relative_path"]),
        "FPSEM_OBSERVER_IMPORT_PATH",
    )
    _require(
        _is_integer(identity["imported_artifact_size"])
        and identity["imported_artifact_size"] > 0,
        "FPSEM_OBSERVER_IMPORT_SIZE",
    )
    _require(_is_sha256(identity["imported_artifact_sha256"]), "FPSEM_OBSERVER_IMPORT_SHA256")
    return observer


def _validate_trusted_contract(trusted):
    _exact_dict(trusted, TRUSTED_KEYS, "FPSEM_TRUSTED_FIELDS")
    _require(trusted["schema_version"] == 1, "FPSEM_TRUSTED_SCHEMA")
    _require(trusted["contract_id"] == TRUSTED_CONTRACT_ID, "FPSEM_TRUSTED_CONTRACT_ID")
    _validate_configuration(trusted["configuration"])
    _validate_runtime_contract(trusted["producer_contract"], "FPSEM_TRUSTED_PRODUCER")
    _validate_runtime_contract(trusted["observer_contract"], "FPSEM_TRUSTED_OBSERVER")
    _require(_is_safe_id(trusted["artifact_root_id"]), "FPSEM_TRUSTED_ARTIFACT_ROOT_ID")
    _require(
        _is_string(trusted["artifact_root_path"])
        and os.path.isabs(trusted["artifact_root_path"]),
        "FPSEM_TRUSTED_ARTIFACT_ROOT_PATH",
    )

    contract_hashes = _validate_hash_records(
        trusted["contract_hashes"], "FPSEM_TRUSTED_CONTRACT_HASH"
    )
    required_hash_keys = trusted["required_contract_hash_keys"]
    _require(
        isinstance(required_hash_keys, list)
        and bool(required_hash_keys)
        and _unique(required_hash_keys)
        and all(_is_lower_id(item) for item in required_hash_keys)
        and set(required_hash_keys) == set(contract_hashes),
        "FPSEM_TRUSTED_REQUIRED_CONTRACT_HASH_KEYS",
    )
    _require(_is_sha256(trusted["blueprint_sha256"]), "FPSEM_TRUSTED_BLUEPRINT_SHA256")
    actual_blueprint_sha = hashlib.sha256(
        _canonical_json_bytes(_blueprint_payload(trusted))
    ).hexdigest()
    _require(
        actual_blueprint_sha == trusted["blueprint_sha256"],
        "FPSEM_TRUSTED_BLUEPRINT_CONTENT",
    )
    _require(
        "full_product_blueprint" in contract_hashes
        and contract_hashes["full_product_blueprint"]["sha256"]
        == trusted["blueprint_sha256"],
        "FPSEM_TRUSTED_BLUEPRINT_HASH_RECORD",
    )

    artifact_contracts = _index_records(
        trusted["artifact_contracts"],
        "artifact_id",
        "FPSEM_TRUSTED_ARTIFACT_DUPLICATE",
        "FPSEM_TRUSTED_ARTIFACT_STRUCTURE",
    )
    _require(bool(artifact_contracts), "FPSEM_TRUSTED_ARTIFACT_EMPTY")
    for item in trusted["artifact_contracts"]:
        _exact_dict(
            item,
            {"artifact_id", "role", "relative_path", "required"},
            "FPSEM_TRUSTED_ARTIFACT_FIELDS",
        )
        _require(_is_lower_id(item["artifact_id"]), "FPSEM_TRUSTED_ARTIFACT_ID")
        _require(_is_upper_id(item["role"]), "FPSEM_TRUSTED_ARTIFACT_ROLE")
        _require(_safe_relative_path(item["relative_path"]), "FPSEM_TRUSTED_ARTIFACT_PATH")
        _require(item["required"] is True, "FPSEM_TRUSTED_ARTIFACT_REQUIRED")
    reserved = (
        ("sidecar_artifact_id", "SEMANTIC_SIDECAR"),
        ("binding_artifact_id", "SEMANTIC_BINDING"),
        ("observation_artifact_id", "SEMANTIC_OBSERVATION"),
    )
    reserved_ids = []
    for field, role in reserved:
        artifact_id = trusted[field]
        _require(artifact_id in artifact_contracts, "FPSEM_TRUSTED_RESERVED_ARTIFACT")
        _require(artifact_contracts[artifact_id]["role"] == role, "FPSEM_TRUSTED_RESERVED_ROLE")
        reserved_ids.append(artifact_id)
    _require(_unique(reserved_ids), "FPSEM_TRUSTED_RESERVED_DUPLICATE")
    import_id = trusted["solver_import_artifact_id"]
    _require(
        import_id in artifact_contracts and import_id not in reserved_ids,
        "FPSEM_TRUSTED_IMPORT_ARTIFACT",
    )
    _require(
        artifact_contracts[import_id]["role"] == "STEP_GEOMETRY",
        "FPSEM_TRUSTED_IMPORT_ROLE",
    )
    _require(
        sum(1 for item in trusted["artifact_contracts"] if item["role"] == "STEP_GEOMETRY") == 1,
        "FPSEM_TRUSTED_STEP_ROLE_CARDINALITY",
    )
    source_ids = trusted["sidecar_artifact_ids"]
    _require(
        isinstance(source_ids, list)
        and bool(source_ids)
        and _unique(source_ids)
        and all(item in artifact_contracts for item in source_ids)
        and import_id in source_ids
        and not set(source_ids).intersection(set(reserved_ids)),
        "FPSEM_TRUSTED_SIDECAR_ARTIFACT_SET",
    )

    _require(isinstance(trusted["frames"], list), "FPSEM_TRUSTED_FRAMES")
    blueprints = trusted["entity_blueprints"]
    _require(isinstance(blueprints, list) and bool(blueprints), "FPSEM_TRUSTED_ENTITY_BLUEPRINTS")
    for blueprint in blueprints:
        _exact_dict(blueprint, ENTITY_BLUEPRINT_KEYS, "FPSEM_TRUSTED_ENTITY_BLUEPRINT_FIELDS")
        match = blueprint.get("match_constraints")
        _require(
            isinstance(match, dict)
            and match.get("bbox_min_mm") is not None
            and match.get("bbox_max_mm") is not None,
            "FPSEM_TRUSTED_ENTITY_BBOX_REQUIRED",
        )
    _require(isinstance(trusted["groups"], list), "FPSEM_TRUSTED_GROUPS")
    _require(isinstance(trusted["partitions"], list), "FPSEM_TRUSTED_PARTITIONS")

    dummy_sources = []
    for artifact_id in source_ids:
        item = artifact_contracts[artifact_id]
        dummy_sources.append(
            {
                "artifact_id": artifact_id,
                "role": item["role"],
                "relative_path": item["relative_path"],
                "size": 1,
                "sha256": "0" * 64,
            }
        )
    dummy_hashes = [
        {"artifact_id": item["artifact_id"], "sha256": item["sha256"]}
        for item in dummy_sources
    ]
    dummy_entities = []
    for blueprint in blueprints:
        entity = dict(blueprint)
        entity["artifact_hashes"] = [dict(item) for item in dummy_hashes]
        dummy_entities.append(entity)
    producer_contract = trusted["producer_contract"]
    validate_full_product_structure(
        {
            "schema_version": 1,
            "contract_id": SIDECAR_CONTRACT_ID,
            "scope": "FULL_PRODUCT",
            "configuration": trusted["configuration"],
            "producer": {
                "git_head": "0" * 40,
                "profile_id": producer_contract["profile_id"],
                "profile_contract_sha256": producer_contract["profile_contract_sha256"],
                "script_sha256": producer_contract["script_sha256"],
                "case_id": "TRUSTED-BLUEPRINT-VALIDATION",
                "job_id": "trusted-blueprint-validation",
                "output_root_id": trusted["artifact_root_id"],
            },
            "contract_hashes": trusted["contract_hashes"],
            "units": {"length": "mm", "area": "mm^2", "volume": "mm^3", "angle": "deg"},
            "source_artifacts": dummy_sources,
            "frames": trusted["frames"],
            "entities": dummy_entities,
            "groups": trusted["groups"],
            "partitions": trusted["partitions"],
        }
    )
    return contract_hashes, artifact_contracts


def validate_trusted_blueprint(blueprint):
    """Validate one immutable variant blueprint without runtime job identities."""

    _exact_dict(blueprint, BLUEPRINT_KEYS, "FPSEM_BLUEPRINT_FIELDS")
    _require(blueprint["schema_version"] == 1, "FPSEM_BLUEPRINT_SCHEMA")
    _require(blueprint["contract_id"] == BLUEPRINT_CONTRACT_ID, "FPSEM_BLUEPRINT_CONTRACT_ID")
    _require(blueprint["scope"] == "FULL_PRODUCT", "FPSEM_BLUEPRINT_SCOPE")
    _require(_is_safe_id(blueprint["product_id"]), "FPSEM_BLUEPRINT_PRODUCT_ID")
    _require(
        _is_string(blueprint["source_variant_id"])
        and SOURCE_VARIANT_RE.match(blueprint["source_variant_id"]) is not None,
        "FPSEM_BLUEPRINT_SOURCE_VARIANT_ID",
    )
    _require(
        blueprint["configuration"]["product_id"] == blueprint["product_id"],
        "FPSEM_BLUEPRINT_PRODUCT_CONFIGURATION",
    )
    for field in ("producer_profile_id", "observer_profile_id"):
        _require(_is_safe_id(blueprint[field]), "FPSEM_BLUEPRINT_PROFILE_ID")
    _require(
        blueprint["producer_profile_id"] != blueprint["observer_profile_id"],
        "FPSEM_BLUEPRINT_PROFILE_DISTINCT",
    )
    required_hash_keys = blueprint["required_contract_hash_keys"]
    _require(
        isinstance(required_hash_keys, list)
        and bool(required_hash_keys)
        and _unique(required_hash_keys)
        and all(_is_lower_id(item) for item in required_hash_keys)
        and "full_product_blueprint" in required_hash_keys
        and "trusted_blueprint_file" in required_hash_keys
        and "trusted_campaign" in required_hash_keys,
        "FPSEM_BLUEPRINT_REQUIRED_HASH_KEYS",
    )
    blueprint_payload = {
        "configuration": blueprint["configuration"],
        "frames": blueprint["frames"],
        "entity_blueprints": blueprint["entity_blueprints"],
        "groups": blueprint["groups"],
        "partitions": blueprint["partitions"],
    }
    blueprint_sha = hashlib.sha256(_canonical_json_bytes(blueprint_payload)).hexdigest()
    hashes = []
    for key in required_hash_keys:
        hashes.append(
            {
                "contract_key": key,
                "sha256": blueprint_sha if key == "full_product_blueprint" else "0" * 64,
            }
        )
    dummy = {
        "schema_version": 1,
        "contract_id": TRUSTED_CONTRACT_ID,
        "configuration": blueprint["configuration"],
        "frames": blueprint["frames"],
        "entity_blueprints": blueprint["entity_blueprints"],
        "blueprint_sha256": blueprint_sha,
        "producer_contract": {
            "profile_id": blueprint["producer_profile_id"],
            "profile_contract_sha256": "0" * 64,
            "script_sha256": "0" * 64,
        },
        "observer_contract": {
            "profile_id": blueprint["observer_profile_id"],
            "profile_contract_sha256": "0" * 64,
            "script_sha256": "0" * 64,
        },
        "contract_hashes": hashes,
        "required_contract_hash_keys": required_hash_keys,
        "artifact_contracts": blueprint["artifact_contracts"],
        "artifact_root_id": blueprint["artifact_root_id"],
        "artifact_root_path": os.path.abspath(os.curdir),
        "sidecar_artifact_ids": blueprint["sidecar_artifact_ids"],
        "sidecar_artifact_id": blueprint["sidecar_artifact_id"],
        "binding_artifact_id": blueprint["binding_artifact_id"],
        "observation_artifact_id": blueprint["observation_artifact_id"],
        "solver_import_artifact_id": blueprint["solver_import_artifact_id"],
        "groups": blueprint["groups"],
        "partitions": blueprint["partitions"],
    }
    _validate_trusted_contract(dummy)
    return {
        "source_variant_id": blueprint["source_variant_id"],
        "variant_id": blueprint["configuration"]["variant_id"],
        "configuration_id": blueprint["configuration"]["configuration_id"],
        "cell_count": len(blueprint["configuration"]["cell_indices"]),
        "semantic_entity_count": len(blueprint["entity_blueprints"]),
        "blueprint_payload_sha256": blueprint_sha,
    }


def load_trusted_blueprint_bytes(data, expected_sha256):
    _require(_is_sha256(expected_sha256), "FPSEM_BLUEPRINT_RAW_EXPECTED_SHA256")
    _require(
        hashlib.sha256(data).hexdigest() == expected_sha256,
        "FPSEM_BLUEPRINT_RAW_SHA256",
    )
    blueprint = load_json_bytes_strict(data)
    validate_trusted_blueprint(blueprint)
    return blueprint


def materialize_trusted_contract(
    blueprint,
    blueprint_raw_sha256,
    producer_contract,
    observer_contract,
    artifact_root_path,
    contract_hashes,
):
    """Bind an authorized static blueprint to exact runtime contracts and root."""

    summary = validate_trusted_blueprint(blueprint)
    _require(_is_sha256(blueprint_raw_sha256), "FPSEM_BLUEPRINT_RAW_EXPECTED_SHA256")
    _validate_runtime_contract(producer_contract, "FPSEM_TRUSTED_PRODUCER")
    _validate_runtime_contract(observer_contract, "FPSEM_TRUSTED_OBSERVER")
    _require(
        producer_contract["profile_id"] == blueprint["producer_profile_id"],
        "FPSEM_BLUEPRINT_PRODUCER_PROFILE",
    )
    _require(
        observer_contract["profile_id"] == blueprint["observer_profile_id"],
        "FPSEM_BLUEPRINT_OBSERVER_PROFILE",
    )
    hashes = _validate_hash_records(contract_hashes, "FPSEM_MATERIALIZED_CONTRACT_HASH")
    _require(
        set(hashes) == set(blueprint["required_contract_hash_keys"]),
        "FPSEM_MATERIALIZED_CONTRACT_HASH_SET",
    )
    _require(
        hashes["full_product_blueprint"]["sha256"]
        == summary["blueprint_payload_sha256"],
        "FPSEM_MATERIALIZED_BLUEPRINT_PAYLOAD_SHA256",
    )
    _require(
        hashes["trusted_blueprint_file"]["sha256"] == blueprint_raw_sha256,
        "FPSEM_MATERIALIZED_BLUEPRINT_RAW_SHA256",
    )
    trusted = {
        "schema_version": 1,
        "contract_id": TRUSTED_CONTRACT_ID,
        "configuration": copy_value(blueprint["configuration"]),
        "frames": copy_value(blueprint["frames"]),
        "entity_blueprints": copy_value(blueprint["entity_blueprints"]),
        "blueprint_sha256": summary["blueprint_payload_sha256"],
        "producer_contract": copy_value(producer_contract),
        "observer_contract": copy_value(observer_contract),
        "contract_hashes": copy_value(contract_hashes),
        "required_contract_hash_keys": list(blueprint["required_contract_hash_keys"]),
        "artifact_contracts": copy_value(blueprint["artifact_contracts"]),
        "artifact_root_id": blueprint["artifact_root_id"],
        "artifact_root_path": artifact_root_path,
        "sidecar_artifact_ids": list(blueprint["sidecar_artifact_ids"]),
        "sidecar_artifact_id": blueprint["sidecar_artifact_id"],
        "binding_artifact_id": blueprint["binding_artifact_id"],
        "observation_artifact_id": blueprint["observation_artifact_id"],
        "solver_import_artifact_id": blueprint["solver_import_artifact_id"],
        "groups": copy_value(blueprint["groups"]),
        "partitions": copy_value(blueprint["partitions"]),
    }
    _validate_trusted_contract(trusted)
    return trusted


def copy_value(value):
    """JSON-safe deep copy without importing implementation-specific modules."""

    return json.loads(json.dumps(value, ensure_ascii=True))


def load_trusted_campaign_bytes(
    data,
    expected_sha256,
    blueprint_bytes_by_path,
    expected_variant_records=None,
    source_bytes_by_path=None,
):
    """Authorize the campaign and every one of its detached variant blueprints."""

    _require(_is_sha256(expected_sha256), "FPSEM_CAMPAIGN_RAW_EXPECTED_SHA256")
    _require(hashlib.sha256(data).hexdigest() == expected_sha256, "FPSEM_CAMPAIGN_RAW_SHA256")
    campaign = load_json_bytes_strict(data)
    _exact_dict(campaign, CAMPAIGN_KEYS, "FPSEM_CAMPAIGN_FIELDS")
    _require(campaign["schema_version"] == 1, "FPSEM_CAMPAIGN_SCHEMA")
    _require(campaign["contract_id"] == CAMPAIGN_CONTRACT_ID, "FPSEM_CAMPAIGN_CONTRACT_ID")
    _require(campaign["scope"] == "FULL_PRODUCT", "FPSEM_CAMPAIGN_SCOPE")
    _require(_is_safe_id(campaign["product_id"]), "FPSEM_CAMPAIGN_PRODUCT_ID")
    count = campaign["expected_variant_count"]
    _require(_is_integer(count) and count > 0, "FPSEM_CAMPAIGN_VARIANT_COUNT")
    sources = campaign["source_contracts"]
    _require(isinstance(sources, list) and bool(sources), "FPSEM_CAMPAIGN_SOURCES")
    source_keys = set()
    source_paths = set()
    for item in sources:
        _exact_dict(item, CAMPAIGN_SOURCE_KEYS, "FPSEM_CAMPAIGN_SOURCE_FIELDS")
        _require(
            _is_lower_id(item["contract_key"])
            and _safe_relative_path(item["git_path"])
            and _is_sha256(item["sha256"]),
            "FPSEM_CAMPAIGN_SOURCE_IDENTITY",
        )
        _require(
            item["contract_key"] not in source_keys and item["git_path"] not in source_paths,
            "FPSEM_CAMPAIGN_SOURCE_DUPLICATE",
        )
        source_keys.add(item["contract_key"])
        source_paths.add(item["git_path"])
    _require(
        isinstance(source_bytes_by_path, dict)
        and set(source_bytes_by_path) == source_paths,
        "FPSEM_CAMPAIGN_SOURCE_FILE_SET",
    )
    for item in sources:
        _require(
            hashlib.sha256(source_bytes_by_path[item["git_path"]]).hexdigest()
            == item["sha256"],
            "FPSEM_CAMPAIGN_SOURCE_FILE_SHA256",
        )
    records = campaign["variant_contracts"]
    _require(isinstance(records, list) and len(records) == count, "FPSEM_CAMPAIGN_VARIANT_RECORD_COUNT")
    by_source_id = {}
    blueprint_paths = set()
    for record in records:
        _exact_dict(record, CAMPAIGN_VARIANT_KEYS, "FPSEM_CAMPAIGN_VARIANT_FIELDS")
        source_id = record["source_variant_id"]
        _require(
            _is_string(source_id)
            and bool(source_id)
            and source_id not in by_source_id
            and _is_safe_id(record["variant_id"])
            and _is_safe_id(record["configuration_id"])
            and _is_integer(record["cell_count"])
            and record["cell_count"] > 0
            and _is_integer(record["semantic_entity_count"])
            and record["semantic_entity_count"] > 1
            and _safe_relative_path(record["blueprint_path"])
            and record["blueprint_path"] not in blueprint_paths
            and _is_sha256(record["blueprint_sha256"]),
            "FPSEM_CAMPAIGN_VARIANT_IDENTITY",
        )
        by_source_id[source_id] = record
        blueprint_paths.add(record["blueprint_path"])
    _require(
        isinstance(blueprint_bytes_by_path, dict)
        and set(blueprint_bytes_by_path) == blueprint_paths,
        "FPSEM_CAMPAIGN_BLUEPRINT_FILE_SET",
    )
    for record in records:
        blueprint = load_trusted_blueprint_bytes(
            blueprint_bytes_by_path[record["blueprint_path"]],
            record["blueprint_sha256"],
        )
        summary = validate_trusted_blueprint(blueprint)
        _require(
            blueprint["product_id"] == campaign["product_id"]
            and summary["source_variant_id"] == record["source_variant_id"]
            and summary["variant_id"] == record["variant_id"]
            and summary["configuration_id"] == record["configuration_id"]
            and summary["cell_count"] == record["cell_count"]
            and summary["semantic_entity_count"] == record["semantic_entity_count"],
            "FPSEM_CAMPAIGN_BLUEPRINT_RECORD_MISMATCH",
        )
    if expected_variant_records is not None:
        _require(
            isinstance(expected_variant_records, dict)
            and set(expected_variant_records) == set(by_source_id),
            "FPSEM_CAMPAIGN_EXPECTED_VARIANT_SET",
        )
        for source_id, expected in expected_variant_records.items():
            record = by_source_id[source_id]
            _require(
                record["configuration_id"] == expected["configuration_id"]
                and record["cell_count"] == expected["cell_count"],
                "FPSEM_CAMPAIGN_EXPECTED_VARIANT_RECORD",
            )
    return {
        "variant_count": count,
        "source_contract_count": len(sources),
        "variant_ids": sorted(by_source_id),
        "status": "PASS_TRUSTED_FULL_PRODUCT_CAMPAIGN",
    }


def validate_against_trusted_contract(sidecar, trusted_contract, producer_identity):
    """Bind every sidecar blueprint field to trusted data and actual producer state."""

    validate_full_product_structure(sidecar)
    trusted_hashes, trusted_artifacts = _validate_trusted_contract(trusted_contract)
    actual_producer = _validate_producer_identity(producer_identity, trusted_contract)
    _require(sidecar["producer"] == actual_producer, "FPSEM_ACTUAL_PRODUCER_IDENTITY")
    _require(sidecar["configuration"] == trusted_contract["configuration"], "FPSEM_TRUSTED_CONFIGURATION")
    _require(sidecar["frames"] == trusted_contract["frames"], "FPSEM_TRUSTED_FRAME_BLUEPRINT")
    sidecar_blueprints = _index_records(
        [_entity_blueprint(item) for item in sidecar["entities"]],
        "semantic_key",
        "FPSEM_TRUSTED_ENTITY_DUPLICATE",
        "FPSEM_TRUSTED_ENTITY_STRUCTURE",
    )
    trusted_blueprints = _index_records(
        trusted_contract["entity_blueprints"],
        "semantic_key",
        "FPSEM_TRUSTED_ENTITY_DUPLICATE",
        "FPSEM_TRUSTED_ENTITY_STRUCTURE",
    )
    _require(sidecar_blueprints == trusted_blueprints, "FPSEM_TRUSTED_ENTITY_BLUEPRINT")
    sidecar_hashes = _validate_hash_records(sidecar["contract_hashes"], "FPSEM_CONTRACT_HASH")
    _require(sidecar_hashes == trusted_hashes, "FPSEM_TRUSTED_CONTRACT_HASH_SET")
    sidecar_artifacts = _validate_artifact_records(sidecar["source_artifacts"], "FPSEM_SOURCE_ARTIFACT")
    _require(set(sidecar_artifacts) == set(trusted_contract["sidecar_artifact_ids"]), "FPSEM_TRUSTED_SOURCE_ARTIFACT_SET")
    for artifact_id, item in sidecar_artifacts.items():
        contract = trusted_artifacts[artifact_id]
        _require(
            item["role"] == contract["role"]
            and item["relative_path"] == contract["relative_path"],
            "FPSEM_TRUSTED_SOURCE_ARTIFACT_IDENTITY",
        )
    _require(sidecar["groups"] == trusted_contract["groups"], "FPSEM_TRUSTED_GROUP_CONTRACT")
    _require(sidecar["partitions"] == trusted_contract["partitions"], "FPSEM_TRUSTED_PARTITION_CONTRACT")
    return True


def _duplicate_rejecting_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("FPSEM_JSON_DUPLICATE_KEY")
        result[key] = value
    return result


def load_json_bytes_strict(data):
    """Parse the exact UTF-8 bytes while rejecting duplicate object keys."""
    _require(isinstance(data, BINARY_TYPES), "FPSEM_JSON_BYTES_REQUIRED")
    try:
        text = data.decode("utf-8")
    except (UnicodeDecodeError, AttributeError):
        raise ValueError("FPSEM_JSON_UTF8")
    try:
        return json.loads(text, object_pairs_hook=_duplicate_rejecting_object)
    except ValueError as error:
        if str(error) == "FPSEM_JSON_DUPLICATE_KEY":
            raise
        raise ValueError("FPSEM_JSON_INVALID")


def load_trusted_contract_bytes(data, expected_sha256):
    """Load a trusted contract only when an external raw-byte SHA authorizes it."""

    _require(_is_sha256(expected_sha256), "FPSEM_TRUSTED_RAW_EXPECTED_SHA256")
    _require(
        hashlib.sha256(data).hexdigest() == expected_sha256,
        "FPSEM_TRUSTED_RAW_SHA256",
    )
    trusted = load_json_bytes_strict(data)
    _validate_trusted_contract(trusted)
    return trusted


def _hash_file_once(path, capture=False, maximum_capture=16 * 1024 * 1024):
    _require(_is_string(path) and os.path.isabs(path), "FPSEM_ACTUAL_FILE_ABSOLUTE_PATH")
    _require(os.path.isfile(path) and not os.path.islink(path), "FPSEM_ACTUAL_FILE_MISSING")
    digest = hashlib.sha256()
    size = 0
    chunks = []
    with open(path, "rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            digest.update(chunk)
            if capture:
                _require(size <= maximum_capture, "FPSEM_ACTUAL_JSON_TOO_LARGE")
                chunks.append(chunk)
    return size, digest.hexdigest(), "".encode("ascii").join(chunks) if capture else None


def _exact_artifact_path(root, relative_path):
    parts = relative_path.replace("\\", "/").split("/")
    return os.path.abspath(os.path.join(root, *parts))


def measure_actual_artifact(artifact_id, relative_path, path, artifact_root=None):
    """Create one independently measured manifest record for a real file."""
    _require(_is_lower_id(artifact_id), "FPSEM_ACTUAL_FILE_ID")
    _require(_safe_relative_path(relative_path), "FPSEM_ACTUAL_FILE_RELATIVE_PATH")
    if artifact_root is not None:
        _require(
            os.path.normcase(os.path.abspath(path))
            == os.path.normcase(_exact_artifact_path(artifact_root, relative_path)),
            "FPSEM_ACTUAL_FILE_PATH_IDENTITY",
        )
        _require_no_reparse_chain(artifact_root, path)
    size, digest, unused = _hash_file_once(path, False)
    return {
        "artifact_id": artifact_id,
        "path": path,
        "relative_path": relative_path,
        "size": size,
        "sha256": digest,
    }


def _measure_actual_files(actual_files, trusted_contract):
    _exact_dict(
        actual_files,
        {
            "artifact_root",
            "artifact_root_id",
            "producer_identity",
            "observer_identity",
            "files",
        },
        "FPSEM_ACTUAL_FILES_FIELDS",
    )
    root = actual_files["artifact_root"]
    _require(
        _is_string(root) and os.path.isabs(root) and os.path.isdir(root),
        "FPSEM_ACTUAL_ARTIFACT_ROOT",
    )
    _require(
        os.path.normcase(os.path.abspath(root))
        == os.path.normcase(os.path.abspath(trusted_contract["artifact_root_path"])),
        "FPSEM_ACTUAL_ARTIFACT_ROOT_PATH",
    )
    _require(
        actual_files["artifact_root_id"] == trusted_contract["artifact_root_id"],
        "FPSEM_ACTUAL_ARTIFACT_ROOT_ID",
    )
    _require_no_reparse_ancestors(root)
    records = actual_files["files"]
    by_id = _index_records(records, "artifact_id", "FPSEM_ACTUAL_FILE_DUPLICATE", "FPSEM_ACTUAL_FILE_STRUCTURE")
    contracts = _index_records(trusted_contract["artifact_contracts"], "artifact_id", "FPSEM_TRUSTED_ARTIFACT_DUPLICATE", "FPSEM_TRUSTED_ARTIFACT_STRUCTURE")
    _require(set(by_id) == set(contracts), "FPSEM_ACTUAL_FILE_SET")
    captured_ids = {
        trusted_contract["sidecar_artifact_id"],
        trusted_contract["binding_artifact_id"],
        trusted_contract["observation_artifact_id"],
    }
    measured = {}
    for artifact_id, record in by_id.items():
        _exact_dict(
            record,
            {"artifact_id", "path", "relative_path", "size", "sha256"},
            "FPSEM_ACTUAL_FILE_FIELDS",
        )
        contract = contracts[artifact_id]
        _require(record["relative_path"] == contract["relative_path"], "FPSEM_ACTUAL_FILE_RELATIVE_PATH")
        expected_path = _exact_artifact_path(root, record["relative_path"])
        _require(
            os.path.normcase(os.path.abspath(record["path"]))
            == os.path.normcase(expected_path),
            "FPSEM_ACTUAL_FILE_PATH_IDENTITY",
        )
        _require_no_reparse_chain(root, record["path"])
        size, digest, data = _hash_file_once(record["path"], artifact_id in captured_ids)
        _require(record["size"] == size, "FPSEM_ACTUAL_FILE_SIZE")
        _require(record["sha256"] == digest, "FPSEM_ACTUAL_FILE_SHA256")
        measured[artifact_id] = {
            "artifact_id": artifact_id,
            "relative_path": record["relative_path"],
            "size": size,
            "sha256": digest,
            "bytes": data,
        }
    return measured


def build_detached_binding(sidecar, trusted_contract, artifact_identities):
    """Bind every trusted artifact except the binding file itself.

    The external artifact manifest must hash the resulting binding file.  This
    avoids an impossible self-hash while closing the complete manifest chain.
    """
    validate_full_product_structure(sidecar)
    unused_hashes, contracts = _validate_trusted_contract(trusted_contract)
    binding_id = trusted_contract["binding_artifact_id"]
    required_ids = set(contracts) - {binding_id}
    identities = _index_records(
        artifact_identities,
        "artifact_id",
        "FPSEM_BINDING_ARTIFACT_DUPLICATE",
        "FPSEM_BINDING_ARTIFACT_STRUCTURE",
    )
    _require(set(identities) == required_ids, "FPSEM_BINDING_ARTIFACT_SET")
    normalized = []
    for artifact_id in sorted(identities):
        item = identities[artifact_id]
        _exact_dict(item, {"artifact_id", "relative_path", "size", "sha256"}, "FPSEM_BINDING_ARTIFACT_FIELDS")
        contract = contracts[artifact_id]
        _require(item["relative_path"] == contract["relative_path"], "FPSEM_BINDING_ARTIFACT_PATH")
        _require(_is_integer(item["size"]) and item["size"] > 0, "FPSEM_BINDING_ARTIFACT_SIZE")
        _require(_is_sha256(item["sha256"]), "FPSEM_BINDING_ARTIFACT_SHA256")
        normalized.append(dict(item))
    return {
        "schema_version": 1,
        "contract_id": BINDING_CONTRACT_ID,
        "configuration_id": sidecar["configuration"]["configuration_id"],
        "sidecar_artifact_id": trusted_contract["sidecar_artifact_id"],
        "binding_artifact_id": binding_id,
        "artifact_identities": normalized,
        "producer": dict(sidecar["producer"]),
        "contract_hashes": list(sidecar["contract_hashes"]),
    }


def validate_detached_binding(binding, sidecar, measured, trusted_contract):
    _exact_dict(binding, BINDING_KEYS, "FPSEM_BINDING_FIELDS")
    _require(binding["schema_version"] == 1, "FPSEM_BINDING_SCHEMA")
    _require(binding["contract_id"] == BINDING_CONTRACT_ID, "FPSEM_BINDING_CONTRACT_ID")
    _require(binding["configuration_id"] == sidecar["configuration"]["configuration_id"], "FPSEM_BINDING_CONFIGURATION")
    _require(binding["sidecar_artifact_id"] == trusted_contract["sidecar_artifact_id"], "FPSEM_BINDING_SIDECAR_ID")
    binding_id = trusted_contract["binding_artifact_id"]
    _require(binding["binding_artifact_id"] == binding_id, "FPSEM_BINDING_ID")
    _require(binding["producer"] == sidecar["producer"], "FPSEM_BINDING_PRODUCER")
    _require(binding["contract_hashes"] == sidecar["contract_hashes"], "FPSEM_BINDING_CONTRACT_HASHES")
    identities = _index_records(binding["artifact_identities"], "artifact_id", "FPSEM_BINDING_ARTIFACT_DUPLICATE", "FPSEM_BINDING_ARTIFACT_STRUCTURE")
    _require(set(identities) == set(measured) - {binding_id}, "FPSEM_BINDING_ARTIFACT_SET")
    for artifact_id, item in identities.items():
        _exact_dict(item, {"artifact_id", "relative_path", "size", "sha256"}, "FPSEM_BINDING_ARTIFACT_FIELDS")
        actual = measured[artifact_id]
        _require(
            item["relative_path"] == actual["relative_path"]
            and item["size"] == actual["size"]
            and item["sha256"] == actual["sha256"],
            "FPSEM_BINDING_ACTUAL_ARTIFACT_MISMATCH",
        )
    return True


def _angle_degrees(left, right):
    left_norm = _norm(left)
    right_norm = _norm(right)
    _require(left_norm > 0.0 and right_norm > 0.0, "FPSEM_OBSERVATION_DIRECTION_ZERO")
    dot = max(-1.0, min(1.0, _dot(left, right) / (left_norm * right_norm)))
    return math.degrees(math.acos(dot))


def _vector_in_axes(vector, axes):
    return [
        sum(float(vector[index]) * float(axes[index][axis]) for index in range(3))
        for axis in range(3)
    ]


def _global_frame_transforms(frames, configuration):
    by_id = _validate_frames(frames, configuration)
    cache = {}

    def resolve(frame_id):
        if frame_id in cache:
            return cache[frame_id]
        frame = by_id[frame_id]
        parent_id = frame["parent_frame_id"]
        if parent_id is None:
            result = (list(frame["origin_mm"]), [list(axis) for axis in frame["axes"]])
        else:
            parent_origin, parent_axes = resolve(parent_id)
            relative_origin = _vector_in_axes(frame["origin_mm"], parent_axes)
            origin = [
                float(parent_origin[index]) + float(relative_origin[index])
                for index in range(3)
            ]
            axes = [_vector_in_axes(axis, parent_axes) for axis in frame["axes"]]
            result = (origin, axes)
        cache[frame_id] = result
        return result

    for frame_id in by_id:
        resolve(frame_id)
    return cache


def _global_point(local_point, transform):
    origin, axes = transform
    relative = _vector_in_axes(local_point, axes)
    return [float(origin[index]) + float(relative[index]) for index in range(3)]


def _global_vector(local_vector, transform):
    return _vector_in_axes(local_vector, transform[1])


def validate_observation(
    sidecar,
    observation,
    measured,
    trusted_contract,
    producer_identity,
    observer_identity,
):
    """Derive solver mapping, topology, direction, bbox, and imported-byte truth."""
    _exact_dict(observation, OBSERVATION_KEYS, "FPSEM_OBSERVATION_FIELDS")
    _require(observation["schema_version"] == 1, "FPSEM_OBSERVATION_SCHEMA")
    _require(observation["contract_id"] == OBSERVATION_CONTRACT_ID, "FPSEM_OBSERVATION_CONTRACT_ID")
    _require(observation["configuration_id"] == sidecar["configuration"]["configuration_id"], "FPSEM_OBSERVATION_CONFIGURATION")
    _require(observation["observer"] == observer_identity, "FPSEM_OBSERVATION_OBSERVER_IDENTITY")
    import_id = trusted_contract["solver_import_artifact_id"]
    _require(observation["imported_artifact_id"] == import_id, "FPSEM_OBSERVATION_IMPORT_ID")
    _require(observation["imported_artifact_sha256"] == measured[import_id]["sha256"], "FPSEM_OBSERVATION_IMPORT_SHA256")
    import_contract = _index_records(
        trusted_contract["artifact_contracts"],
        "artifact_id",
        "FPSEM_TRUSTED_ARTIFACT_DUPLICATE",
        "FPSEM_TRUSTED_ARTIFACT_STRUCTURE",
    )[import_id]
    _require(
        observer_identity["imported_artifact_id"] == import_id
        and observer_identity["imported_artifact_relative_path"]
        == import_contract["relative_path"]
        and observer_identity["imported_artifact_size"] == measured[import_id]["size"]
        and observer_identity["imported_artifact_sha256"] == measured[import_id]["sha256"],
        "FPSEM_OBSERVER_IMPORTED_BYTES",
    )
    _require(
        observer_identity["predecessor_identity"] == producer_identity,
        "FPSEM_OBSERVER_PREDECESSOR",
    )
    entities = _index_records(sidecar["entities"], "semantic_key", "FPSEM_SEMANTIC_KEY_DUPLICATE", "FPSEM_ENTITY_STRUCTURE")
    observed = _index_records(observation["entities"], "semantic_key", "FPSEM_OBSERVATION_ENTITY_DUPLICATE", "FPSEM_OBSERVATION_ENTITY_STRUCTURE")
    missing_keys = sorted(set(entities) - set(observed))
    unexpected_keys = sorted(set(observed) - set(entities))
    _require(not missing_keys and not unexpected_keys, "FPSEM_OBSERVATION_ENTITY_SET")
    transforms = _global_frame_transforms(sidecar["frames"], sidecar["configuration"])
    used_actual_ids = set()
    actual_ids_by_key = {}
    actual_record_by_id = {}
    for semantic_key, item in observed.items():
        _exact_dict(item, OBSERVED_ENTITY_KEYS, "FPSEM_OBSERVATION_ENTITY_FIELDS")
        expected = entities[semantic_key]
        for field in ("entity_kind", "cell_index", "local_frame_id", "geometry_type"):
            _require(item[field] == expected[field], "FPSEM_OBSERVATION_ENTITY_%s" % field.upper())
        matches = item["matches"]
        _require(
            isinstance(matches, list)
            and len(matches) == expected["expected_cardinality"],
            "FPSEM_OBSERVATION_CARDINALITY",
        )
        local_ids = []
        constraint = expected["match_constraints"]
        direction = expected["direction_constraint"]
        for match in matches:
            _exact_dict(match, OBSERVED_MATCH_KEYS, "FPSEM_OBSERVATION_MATCH_FIELDS")
            actual_id = match["actual_id"]
            _require(_is_safe_id(actual_id), "FPSEM_OBSERVATION_ACTUAL_ID")
            _require(actual_id not in used_actual_ids, "FPSEM_OBSERVATION_ACTUAL_ID_COLLISION")
            used_actual_ids.add(actual_id)
            local_ids.append(actual_id)
            actual_record_by_id[actual_id] = {
                "semantic_key": semantic_key,
                "entity_kind": expected["entity_kind"],
                "match": match,
                "entity": expected,
            }
            centroid = match["local_centroid_mm"]
            _require(_is_vector(centroid), "FPSEM_OBSERVATION_CENTROID")
            _require(
                all(
                    abs(float(centroid[index]) - float(constraint["centroid_mm"][index]))
                    <= float(constraint["centroid_tolerance_mm"])
                    for index in range(3)
                ),
                "FPSEM_OBSERVATION_CENTROID_MISMATCH",
            )
            _require(match["solver_geometry_type"] == constraint["solver_geometry_type"], "FPSEM_OBSERVATION_SOLVER_GEOMETRY")
            if constraint["edge_count"] is None:
                _require(match["edge_count"] is None or (_is_integer(match["edge_count"]) and match["edge_count"] >= 0), "FPSEM_OBSERVATION_EDGE_COUNT")
            else:
                _require(match["edge_count"] == constraint["edge_count"], "FPSEM_OBSERVATION_EDGE_COUNT")
            measure = match["measure_value"]
            if constraint["measure_kind"] == "NONE":
                _require(measure is None, "FPSEM_OBSERVATION_MEASURE_NONE")
            else:
                _require(_is_number(measure) and float(measure) > 0.0, "FPSEM_OBSERVATION_MEASURE")
                if constraint["measure_role"] == "MATCH":
                    _require(
                        abs(float(measure) - float(constraint["measure_value"]))
                        <= float(constraint["measure_tolerance"]),
                        "FPSEM_OBSERVATION_MEASURE_MISMATCH",
                    )
            vector = match["direction_vector"]
            mode = direction["mode"]
            bbox_min = match["observed_bbox_min_mm"]
            bbox_max = match["observed_bbox_max_mm"]
            _require(
                _is_vector(bbox_min)
                and _is_vector(bbox_max)
                and all(float(bbox_min[index]) < float(bbox_max[index]) for index in range(3)),
                "FPSEM_OBSERVATION_BBOX",
            )
            _require(
                all(
                    float(bbox_min[index]) <= float(centroid[index]) <= float(bbox_max[index])
                    for index in range(3)
                ),
                "FPSEM_OBSERVATION_CENTROID_OUTSIDE_BBOX",
            )
            expected_bbox_min = constraint["bbox_min_mm"]
            expected_bbox_max = constraint["bbox_max_mm"]
            tolerance = float(constraint["centroid_tolerance_mm"])
            _require(
                expected_bbox_min is not None
                and expected_bbox_max is not None
                and all(
                    abs(float(bbox_min[index]) - float(expected_bbox_min[index])) <= tolerance
                    and abs(float(bbox_max[index]) - float(expected_bbox_max[index])) <= tolerance
                    for index in range(3)
                ),
                "FPSEM_OBSERVATION_BBOX_MISMATCH",
            )
            if mode == "NOT_APPLICABLE":
                _require(vector is None, "FPSEM_OBSERVATION_DIRECTION_NOT_APPLICABLE")
            else:
                _require(_is_vector(vector) and abs(_norm(vector) - 1.0) <= 1.0e-6, "FPSEM_OBSERVATION_DIRECTION_VECTOR")
                if mode in ("AXIS_ALIGNED", "VECTOR"):
                    actual_global = _global_vector(vector, transforms[expected["local_frame_id"]])
                    expected_global = _global_vector(
                        direction["vector"], transforms[expected["local_frame_id"]]
                    )
                    _require(
                        _angle_degrees(actual_global, expected_global)
                        <= float(direction["tolerance_deg"]),
                        "FPSEM_OBSERVATION_DIRECTION_MISMATCH",
                    )
        _require(_unique(local_ids), "FPSEM_OBSERVATION_LOCAL_ID_DUPLICATE")
        actual_ids_by_key[semantic_key] = local_ids

    dangling_adjacency = []
    orphan_critical_surfaces = []
    body_surface_coverage_ok = True
    for semantic_key, expected in entities.items():
        expected_adjacent = expected["topology"]["required_adjacent_keys"]
        for actual_id in actual_ids_by_key[semantic_key]:
            match = actual_record_by_id[actual_id]["match"]
            owner_id = match["actual_owner_body_id"]
            adjacent_body_ids = match["actual_adjacent_body_ids"]
            boundary_surface_ids = match["actual_boundary_surface_ids"]
            _require(
                isinstance(adjacent_body_ids, list) and _unique(adjacent_body_ids),
                "FPSEM_OBSERVATION_ACTUAL_ADJACENCY_IDS",
            )
            _require(
                isinstance(boundary_surface_ids, list) and _unique(boundary_surface_ids),
                "FPSEM_OBSERVATION_ACTUAL_BOUNDARY_IDS",
            )
            for referenced_id in adjacent_body_ids + boundary_surface_ids:
                if referenced_id not in actual_record_by_id:
                    dangling_adjacency.append(referenced_id)
            _require(not dangling_adjacency, "FPSEM_OBSERVATION_ACTUAL_DANGLING_ID")
            if expected["entity_kind"] == "BODY":
                _require(owner_id is None, "FPSEM_OBSERVATION_BODY_OWNER")
                _require(not adjacent_body_ids, "FPSEM_OBSERVATION_BODY_ADJACENT_BODY_IDS")
                expected_surface_ids = []
                for adjacent_key in expected_adjacent:
                    _require(
                        entities[adjacent_key]["entity_kind"] == "SURFACE",
                        "FPSEM_OBSERVATION_BODY_ADJACENCY_KIND",
                    )
                    expected_surface_ids.extend(actual_ids_by_key[adjacent_key])
                if set(boundary_surface_ids) != set(expected_surface_ids):
                    body_surface_coverage_ok = False
                _require(
                    len(boundary_surface_ids) == len(expected_surface_ids)
                    and set(boundary_surface_ids) == set(expected_surface_ids),
                    "FPSEM_OBSERVATION_BODY_SURFACE_COVERAGE",
                )
            else:
                _require(not boundary_surface_ids, "FPSEM_OBSERVATION_SURFACE_BOUNDARY_IDS")
                _require(
                    _is_safe_id(owner_id) and owner_id in actual_record_by_id,
                    "FPSEM_OBSERVATION_SURFACE_OWNER_ID",
                )
                owner_record = actual_record_by_id[owner_id]
                _require(
                    owner_record["entity_kind"] == "BODY"
                    and owner_record["semantic_key"] == expected["owner_key"],
                    "FPSEM_OBSERVATION_SURFACE_OWNER_MAPPING",
                )
                expected_body_keys = set(
                    key for key in expected_adjacent if entities[key]["entity_kind"] == "BODY"
                )
                observed_body_keys = set()
                for body_id in adjacent_body_ids:
                    record = actual_record_by_id[body_id]
                    _require(record["entity_kind"] == "BODY", "FPSEM_OBSERVATION_ADJACENCY_NOT_BODY")
                    observed_body_keys.add(record["semantic_key"])
                    _require(
                        actual_id in record["match"]["actual_boundary_surface_ids"],
                        "FPSEM_OBSERVATION_TOPOLOGY_NOT_BIDIRECTIONAL",
                    )
                _require(
                    owner_id in adjacent_body_ids
                    and observed_body_keys == expected_body_keys,
                    "FPSEM_OBSERVATION_SURFACE_ADJACENCY_MAPPING",
                )
                if expected["topology"]["critical"] and not adjacent_body_ids:
                    orphan_critical_surfaces.append(semantic_key)
                if expected["direction_constraint"]["mode"] == "OUTWARD_FROM_OWNER":
                    surface_global = _global_point(
                        match["local_centroid_mm"], transforms[expected["local_frame_id"]]
                    )
                    owner_entity = owner_record["entity"]
                    owner_match = owner_record["match"]
                    owner_global = _global_point(
                        owner_match["local_centroid_mm"],
                        transforms[owner_entity["local_frame_id"]],
                    )
                    radial = [
                        float(surface_global[index]) - float(owner_global[index])
                        for index in range(3)
                    ]
                    normal_global = _global_vector(
                        match["direction_vector"], transforms[expected["local_frame_id"]]
                    )
                    _require(
                        _dot(normal_global, radial) > 0.0
                        and _angle_degrees(normal_global, radial)
                        <= float(expected["direction_constraint"]["tolerance_deg"]),
                        "FPSEM_OBSERVATION_OUTWARD_NOT_PROVEN",
                    )
    _require(not orphan_critical_surfaces, "FPSEM_OBSERVATION_CRITICAL_ORPHAN")
    _require(body_surface_coverage_ok, "FPSEM_OBSERVATION_BODY_SURFACE_COVERAGE")
    observed_groups = _index_records(observation["groups"], "group_key", "FPSEM_OBSERVATION_GROUP_DUPLICATE", "FPSEM_OBSERVATION_GROUP_STRUCTURE")
    sidecar_groups = _index_records(sidecar["groups"], "group_key", "FPSEM_GROUP_DUPLICATE", "FPSEM_GROUP_STRUCTURE")
    _require(set(observed_groups) == set(sidecar_groups), "FPSEM_OBSERVATION_GROUP_SET")
    for group_key, item in observed_groups.items():
        _exact_dict(item, {"group_key", "actual_ids"}, "FPSEM_OBSERVATION_GROUP_FIELDS")
        actual_ids = item["actual_ids"]
        _require(isinstance(actual_ids, list) and _unique(actual_ids), "FPSEM_OBSERVATION_GROUP_IDS")
        expected_ids = []
        for member in sidecar_groups[group_key]["member_keys"]:
            expected_ids.extend(actual_ids_by_key[member])
        _require(
            len(actual_ids) == sidecar_groups[group_key]["expected_cardinality"]
            and set(actual_ids) == set(expected_ids),
            "FPSEM_OBSERVATION_GROUP_CARDINALITY",
        )
    assignment_solution_count = int(
        len(used_actual_ids)
        == sum(entity["expected_cardinality"] for entity in entities.values())
        and len(actual_record_by_id) == len(used_actual_ids)
    )
    _require(assignment_solution_count == 1, "FPSEM_OBSERVATION_ASSIGNMENT_NOT_UNIQUE")
    return {
        "observed_semantic_key_count": len(observed),
        "observed_actual_entity_count": len(used_actual_ids),
        "observed_group_count": len(observed_groups),
        "missing_keys": missing_keys,
        "unexpected_keys": unexpected_keys,
        "dangling_adjacency": dangling_adjacency,
        "orphan_critical_surfaces": orphan_critical_surfaces,
        "body_surface_coverage_ok": body_surface_coverage_ok,
        "assignment_solution_count": assignment_solution_count,
        "topology_observed": body_surface_coverage_ok and not dangling_adjacency,
        "cardinality_observed": assignment_solution_count == 1,
    }


def validate_full_product_bundle(
    sidecar,
    binding,
    observation,
    actual_files,
    trusted_contract_bytes,
    expected_trusted_contract_sha256,
):
    """CPython/IronPython API for P1 review of one full-product bundle.

    ``actual_files`` carries one exact trusted run root, distinct producer and
    observer identities, and external-manifest file records.  The trusted
    contract is authorized by its independently pinned raw-byte SHA.  Every
    file is re-hashed, and sidecar/binding/observation are parsed from those
    same captured bytes before any judgment is returned.
    """
    trusted_contract = load_trusted_contract_bytes(
        trusted_contract_bytes, expected_trusted_contract_sha256
    )
    structure = validate_full_product_structure(sidecar)
    producer_identity = actual_files.get("producer_identity")
    observer_identity = actual_files.get("observer_identity")
    _validate_producer_identity(producer_identity, trusted_contract)
    _validate_observer_identity(observer_identity, producer_identity, trusted_contract)
    validate_against_trusted_contract(sidecar, trusted_contract, producer_identity)
    measured = _measure_actual_files(actual_files, trusted_contract)
    sidecar_id = trusted_contract["sidecar_artifact_id"]
    binding_id = trusted_contract["binding_artifact_id"]
    observation_id = trusted_contract["observation_artifact_id"]
    _require(load_json_bytes_strict(measured[sidecar_id]["bytes"]) == sidecar, "FPSEM_ACTUAL_SIDECAR_CONTENT")
    _require(load_json_bytes_strict(measured[binding_id]["bytes"]) == binding, "FPSEM_ACTUAL_BINDING_CONTENT")
    _require(load_json_bytes_strict(measured[observation_id]["bytes"]) == observation, "FPSEM_ACTUAL_OBSERVATION_CONTENT")
    sidecar_artifacts = _validate_artifact_records(sidecar["source_artifacts"], "FPSEM_SOURCE_ARTIFACT")
    for artifact_id, declared in sidecar_artifacts.items():
        actual = measured[artifact_id]
        _require(
            declared["relative_path"] == actual["relative_path"]
            and declared["size"] == actual["size"]
            and declared["sha256"] == actual["sha256"],
            "FPSEM_ACTUAL_SOURCE_ARTIFACT_MISMATCH",
        )
    validate_detached_binding(binding, sidecar, measured, trusted_contract)
    observed = validate_observation(
        sidecar,
        observation,
        measured,
        trusted_contract,
        producer_identity,
        observer_identity,
    )
    result = dict(structure)
    result.update(observed)
    result["actual_artifact_count"] = len(measured)
    result["detached_binding_valid"] = True
    result["trusted_contract_sha256"] = expected_trusted_contract_sha256
    result["status"] = "PASS_FULL_PRODUCT_SEMANTIC_BUNDLE"
    return result

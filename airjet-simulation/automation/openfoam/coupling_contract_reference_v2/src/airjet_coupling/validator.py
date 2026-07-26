"""Stdlib-only Draft 2020-12 subset plus AirJet coupling semantics.

The generic layer implements every JSON Schema keyword used by the two bundled
schemas.  The semantic layer enforces engineering relationships which are not
reliably expressible with portable JSON Schema alone.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import unicodedata
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable


P2_TYPE = "AIRJET_P2_TO_P3_STRUCTURAL_DISPLACEMENT"
P4_TYPE = "AIRJET_P4_TO_P5_WALL_CHT"
SCHEMA_FILES = {
    P2_TYPE: "p2_to_p3_structural_displacement_handoff.schema.json",
    P4_TYPE: "p4_to_p5_wall_cht_handoff.schema.json",
}
UNKNOWN_SENTINELS = {"unknown", "tbd", "n/a", "na", "null", "none", "unset", "?"}
CLASS_TO_KIND = {
    "D": "measured_fact",
    "P": "patent_bound",
    "I": "inference",
    "C": "calibration",
    "U": "unresolved",
}
WINDOWS_DEVICE_NAME = re.compile(r"^(?:con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?$", re.IGNORECASE)
MAXIMUM_UNMAPPED_FRACTION = Decimal("0.0001")
MAX_DOCUMENT_BYTES = 1_048_576
MAX_JSON_DEPTH = 32
MAX_JSON_NODES = 10_000


class ContractValidationError(ValueError):
    """Raised with all deterministic contract violations."""

    def __init__(self, errors: Iterable[str]):
        self.errors = tuple(errors)
        super().__init__("\n".join(self.errors))


def _pairs_no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ContractValidationError([f"$: duplicate JSON key {key!r}"])
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ContractValidationError([f"$: non-finite JSON number {value!r} is forbidden"])


def _validate_json_complexity(value: Any) -> None:
    """Bound input complexity before any recursive schema or semantic walk."""
    nodes = 0
    stack: list[tuple[Any, int]] = [(value, 1)]
    while stack:
        item, depth = stack.pop()
        nodes += 1
        if depth > MAX_JSON_DEPTH:
            raise ContractValidationError(["$: JSON nesting depth exceeds the contract limit"])
        if nodes > MAX_JSON_NODES:
            raise ContractValidationError(["$: JSON node count exceeds the contract limit"])
        if isinstance(item, dict):
            stack.extend((child, depth + 1) for child in item.values())
        elif isinstance(item, list):
            stack.extend((child, depth + 1) for child in item)


def load_json_bytes(data: bytes) -> Any:
    if not data or len(data) > MAX_DOCUMENT_BYTES:
        raise ContractValidationError(["$: document size is outside the contract limit"])
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ContractValidationError(["$: document is not UTF-8"]) from exc
    try:
        document = json.loads(
            text,
            object_pairs_hook=_pairs_no_duplicates,
            parse_constant=_reject_constant,
            parse_float=Decimal,
            parse_int=int,
        )
    except ContractValidationError:
        raise
    except (
        json.JSONDecodeError,
        TypeError,
        ValueError,
        RecursionError,
        MemoryError,
        OverflowError,
    ) as exc:
        raise ContractValidationError([f"$: invalid JSON: {exc}"]) from exc
    _validate_json_complexity(document)
    return document


def _json_type_matches(instance: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(instance, dict)
    if expected == "array":
        return isinstance(instance, list)
    if expected == "string":
        return isinstance(instance, str)
    if expected == "boolean":
        return isinstance(instance, bool)
    if expected == "null":
        return instance is None
    if expected == "integer":
        return isinstance(instance, int) and not isinstance(instance, bool)
    if expected == "number":
        return (
            isinstance(instance, (int, float, Decimal))
            and not isinstance(instance, bool)
            and (not isinstance(instance, float) or math.isfinite(instance))
            and (not isinstance(instance, Decimal) or instance.is_finite())
        )
    return False


def _resolve_ref(root: dict[str, Any], ref: str) -> dict[str, Any]:
    if not ref.startswith("#/"):
        raise ValueError(f"unsupported non-local schema ref {ref!r}")
    value: Any = root
    for token in ref[2:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        value = value[token]
    if not isinstance(value, dict):
        raise ValueError(f"schema ref {ref!r} did not resolve to an object")
    return value


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _schema_errors(instance: Any, schema: dict[str, Any], root: dict[str, Any], path: str = "$") -> list[str]:
    errors: list[str] = []
    if "$ref" in schema:
        return _schema_errors(instance, _resolve_ref(root, schema["$ref"]), root, path)

    if "allOf" in schema:
        for sub in schema["allOf"]:
            errors.extend(_schema_errors(instance, sub, root, path))
    if "oneOf" in schema:
        matches = sum(not _schema_errors(instance, sub, root, path) for sub in schema["oneOf"])
        if matches != 1:
            errors.append(f"{path}: oneOf matched {matches} branches, expected exactly one")

    expected = schema.get("type")
    if expected is not None:
        choices = [expected] if isinstance(expected, str) else expected
        if not any(_json_type_matches(instance, choice) for choice in choices):
            return errors + [f"{path}: expected type {expected!r}"]

    if "const" in schema and instance != schema["const"]:
        errors.append(f"{path}: expected const {schema['const']!r}")
    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: value is not in enum")

    if isinstance(instance, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in instance:
                errors.append(f"{path}: missing required property {key!r}")
        properties = schema.get("properties", {})
        for key, value in instance.items():
            child = f"{path}.{key}"
            if key in properties:
                errors.extend(_schema_errors(value, properties[key], root, child))
            elif schema.get("additionalProperties") is False:
                errors.append(f"{child}: additional property is forbidden")
            elif isinstance(schema.get("additionalProperties"), dict):
                errors.extend(_schema_errors(value, schema["additionalProperties"], root, child))

    if isinstance(instance, list):
        if len(instance) < schema.get("minItems", 0):
            errors.append(f"{path}: fewer than minItems")
        if "maxItems" in schema and len(instance) > schema["maxItems"]:
            errors.append(f"{path}: more than maxItems")
        if schema.get("uniqueItems"):
            canonical = [_canonical(item) for item in instance]
            if len(set(canonical)) != len(canonical):
                errors.append(f"{path}: duplicate array items")
        items = schema.get("items")
        if isinstance(items, dict):
            for index, value in enumerate(instance):
                errors.extend(_schema_errors(value, items, root, f"{path}[{index}]"))
        if "contains" in schema:
            matches = sum(not _schema_errors(value, schema["contains"], root, f"{path}[{i}]") for i, value in enumerate(instance))
            minimum = schema.get("minContains", 1)
            maximum = schema.get("maxContains")
            if matches < minimum:
                errors.append(f"{path}: contains matched {matches}, below {minimum}")
            if maximum is not None and matches > maximum:
                errors.append(f"{path}: contains matched {matches}, above {maximum}")

    if isinstance(instance, str):
        if len(instance) < schema.get("minLength", 0):
            errors.append(f"{path}: shorter than minLength")
        if "maxLength" in schema and len(instance) > schema["maxLength"]:
            errors.append(f"{path}: longer than maxLength")
        if "pattern" in schema and re.search(schema["pattern"], instance) is None:
            errors.append(f"{path}: does not match required pattern")

    if _json_type_matches(instance, "number"):
        numeric = Decimal(str(instance))
        if "minimum" in schema and numeric < Decimal(str(schema["minimum"])):
            errors.append(f"{path}: below minimum")
        if "maximum" in schema and numeric > Decimal(str(schema["maximum"])):
            errors.append(f"{path}: above maximum")
        if "exclusiveMinimum" in schema and numeric <= Decimal(str(schema["exclusiveMinimum"])):
            errors.append(f"{path}: not above exclusiveMinimum")
        if "exclusiveMaximum" in schema and numeric >= Decimal(str(schema["exclusiveMaximum"])):
            errors.append(f"{path}: not below exclusiveMaximum")
    return errors


def _walk_no_unknown(value: Any, path: str, errors: list[str]) -> None:
    if value is None:
        errors.append(f"{path}: null is forbidden")
    elif isinstance(value, str) and value.strip().lower() in UNKNOWN_SENTINELS:
        errors.append(f"{path}: unknown sentinel is forbidden")
    elif isinstance(value, dict):
        for key, item in value.items():
            _walk_no_unknown(item, f"{path}.{key}", errors)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _walk_no_unknown(item, f"{path}[{index}]", errors)


def _schema_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "schemas"


def _schema_for(contract_type: str) -> tuple[dict[str, Any], Path, str]:
    filename = SCHEMA_FILES.get(contract_type)
    if filename is None:
        raise ContractValidationError(["$.contract_type: unsupported contract type"])
    path = _schema_dir() / filename
    raw = path.read_bytes()
    schema = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs_no_duplicates)
    return schema, path, hashlib.sha256(raw).hexdigest()


def _artifact_list(document: dict[str, Any]) -> list[dict[str, Any]]:
    if document.get("contract_type") == P2_TYPE:
        value = document.get("artifacts", [])
        return value if isinstance(value, list) else []
    wall = document.get("wall_field", {})
    region = document.get("region_interface_map", {})
    values = list(wall.get("artifacts", [])) if isinstance(wall, dict) else []
    if isinstance(region, dict) and isinstance(region.get("artifact"), dict):
        values.append(region["artifact"])
    return values


def _normalized_artifact_path(path: Any, label: str, errors: list[str]) -> str | None:
    if not isinstance(path, str):
        return None
    if any(ord(character) < 32 for character in path):
        errors.append(f"{label}: control characters are forbidden")
    if ":" in path:
        errors.append(f"{label}: colon and Windows alternate-data-stream syntax are forbidden")
    portable = path.replace("\\", "/")
    if portable.startswith("/"):
        errors.append(f"{label}: absolute paths are forbidden")
    segments = portable.split("/")
    if any(segment in {"", ".", ".."} for segment in segments):
        errors.append(f"{label}: empty, dot, and parent path segments are forbidden")
    normalized_segments: list[str] = []
    for segment in segments:
        normalized = unicodedata.normalize("NFC", segment)
        normalized_segments.append(normalized)
        if normalized.endswith((".", " ")):
            errors.append(f"{label}: path segments may not end in dot or space")
        if WINDOWS_DEVICE_NAME.fullmatch(normalized):
            errors.append(f"{label}: reserved Windows device name is forbidden")
    return "/".join(normalized_segments).casefold()


def _validate_artifact_uniqueness(document: dict[str, Any], errors: list[str]) -> None:
    artifacts = _artifact_list(document)
    roles = [item.get("role") for item in artifacts if isinstance(item, dict)]
    if len(roles) != len(set(roles)):
        errors.append("$.artifacts: artifact roles must be unique")
    normalized = [
        _normalized_artifact_path(item.get("path"), f"$.artifacts[{index}].path", errors)
        for index, item in enumerate(artifacts)
        if isinstance(item, dict)
    ]
    if len(normalized) != len(set(normalized)):
        errors.append("$.artifacts: artifact paths must be unique after normalization")


def _validate_coordinate_system(value: dict[str, Any], errors: list[str]) -> None:
    axes = value.get("axes")
    if not isinstance(axes, list) or len(axes) != 3 or any(not isinstance(row, list) or len(row) != 3 for row in axes):
        return
    try:
        matrix = [[float(x) for x in row] for row in axes]
    except (TypeError, ValueError):
        return
    for i, row in enumerate(matrix):
        norm = math.sqrt(sum(x * x for x in row))
        if not math.isclose(norm, 1.0, abs_tol=1e-6):
            errors.append(f"$.coordinate_system.axes[{i}]: axis must be unit length")
    for i in range(3):
        for j in range(i + 1, 3):
            dot = sum(matrix[i][k] * matrix[j][k] for k in range(3))
            if not math.isclose(dot, 0.0, abs_tol=1e-6):
                errors.append(f"$.coordinate_system.axes: axes {i} and {j} are not orthogonal")
    determinant = (
        matrix[0][0] * (matrix[1][1] * matrix[2][2] - matrix[1][2] * matrix[2][1])
        - matrix[0][1] * (matrix[1][0] * matrix[2][2] - matrix[1][2] * matrix[2][0])
        + matrix[0][2] * (matrix[1][0] * matrix[2][1] - matrix[1][1] * matrix[2][0])
    )
    handedness = value.get("handedness")
    if handedness == "right" and determinant <= 0:
        errors.append("$.coordinate_system: axes determinant contradicts right handedness")
    if handedness == "left" and determinant >= 0:
        errors.append("$.coordinate_system: axes determinant contradicts left handedness")


def _claim_map(document: dict[str, Any], errors: list[str]) -> dict[str, dict[str, Any]]:
    claims = document.get("provenance", {}).get("claims", [])
    result: dict[str, dict[str, Any]] = {}
    for index, claim in enumerate(claims if isinstance(claims, list) else []):
        if not isinstance(claim, dict):
            continue
        claim_id = claim.get("id")
        if claim_id in result:
            errors.append(f"$.provenance.claims[{index}].id: duplicate claim id")
        elif isinstance(claim_id, str):
            result[claim_id] = claim
        classification = claim.get("classification")
        expected = CLASS_TO_KIND.get(classification)
        if expected is not None and claim.get("assertion_kind") != expected:
            errors.append(f"$.provenance.claims[{index}]: classification cannot masquerade as another assertion kind")
        uncertainty = claim.get("uncertainty")
        if isinstance(uncertainty, dict):
            lower, upper = uncertainty.get("lower"), uncertainty.get("upper")
            if isinstance(lower, (int, float, Decimal)) and isinstance(upper, (int, float, Decimal)) and lower > upper:
                errors.append(f"$.provenance.claims[{index}].uncertainty: lower exceeds upper")
            if classification == "I" and lower == 0 and upper == 0:
                errors.append(f"$.provenance.claims[{index}]: inference requires non-zero uncertainty")
        if classification == "I" and not str(claim.get("derivation", "")).strip():
            errors.append(f"$.provenance.claims[{index}]: inference requires an explicit derivation")
    return result


def _check_active_refs(refs: Iterable[Any], claims: dict[str, dict[str, Any]], errors: list[str]) -> None:
    for ref in refs:
        if ref not in claims:
            errors.append(f"$.provenance: active reference {ref!r} has no claim")
        elif claims[ref].get("classification") == "U":
            errors.append(f"$.provenance: unresolved claim {ref!r} cannot drive an active handoff")


def _validate_p2(document: dict[str, Any], claims: dict[str, dict[str, Any]], errors: list[str]) -> None:
    artifacts = document.get("artifacts", [])
    role_map = {a.get("role"): a for a in artifacts if isinstance(a, dict)}
    displacement = role_map.get("displacement_vector_field", {})
    if displacement.get("components") != ["ux", "uy", "uz"]:
        errors.append("$.artifacts: displacement field must have ordered components ['ux', 'uy', 'uz']; scalar displacement is forbidden")
    length_unit = document.get("coordinate_system", {}).get("length_unit")
    if displacement.get("value_unit") != length_unit:
        errors.append("$.artifacts: displacement value_unit must match coordinate length_unit")
    mapping = document.get("mapping", {})
    if mapping.get("tolerance_unit") != length_unit:
        errors.append("$.mapping.tolerance_unit: must match coordinate length_unit")
    if mapping.get("coverage_scope") != "ALL_DISPLACEMENT_FIELD_NODES":
        errors.append("$.mapping.coverage_scope: all displacement-field nodes must be covered")
    if mapping.get("unmapped_policy") != "FAIL_IF_ACTIVE_MEMBRANE_NODE_UNMAPPED":
        errors.append("$.mapping.unmapped_policy: active membrane nodes may never be unmapped")
    try:
        unmapped_fraction = Decimal(str(mapping.get("maximum_unmapped_fraction")))
        if unmapped_fraction < 0 or unmapped_fraction > MAXIMUM_UNMAPPED_FRACTION:
            errors.append("$.mapping.maximum_unmapped_fraction: must be between 0 and 0.0001 inclusive")
    except Exception:
        pass
    metrics = document.get("mechanical_metrics", {})
    expected_units = {"minimum_gap": length_unit, "maximum_stress": "Pa", "electrical_power": "W"}
    refs: list[Any] = []
    for name, unit in expected_units.items():
        item = metrics.get(name, {})
        if isinstance(item, dict):
            if item.get("unit") != unit:
                errors.append(f"$.mechanical_metrics.{name}.unit: expected {unit!r}")
            refs.append(item.get("provenance_ref"))
            try:
                value = Decimal(str(item.get("value")))
                if name == "minimum_gap" and value <= 0:
                    errors.append("$.mechanical_metrics.minimum_gap.value: must be positive; closure or penetration must return to P2")
                if name in {"maximum_stress", "electrical_power"} and value < 0:
                    errors.append(f"$.mechanical_metrics.{name}.value: must be nonnegative")
            except Exception:
                pass
    _check_active_refs(refs, claims, errors)


def _validate_temporal_sampling(value: dict[str, Any], errors: list[str]) -> None:
    basis = value.get("time_basis")
    sample_count = value.get("sample_count")
    periodic = value.get("periodic")
    if basis == "cycle_phase":
        if periodic is not True or not isinstance(sample_count, int) or isinstance(sample_count, bool) or sample_count < 2:
            errors.append("$.temporal_sampling: cycle_phase requires periodic=true and at least two phase samples")
        if "cycle_period_s" not in value or "step" not in value or "averaging_window_s" in value:
            errors.append("$.temporal_sampling: cycle_phase requires step and cycle_period_s only")
        try:
            covered = Decimal(str(value["step"])) * Decimal(str(sample_count))
            period = Decimal(str(value["cycle_period_s"]))
            tolerance = max(Decimal("1e-15"), abs(period) * Decimal("1e-8"))
            if abs(covered - period) > tolerance:
                errors.append("$.temporal_sampling: cycle_phase requires step * sample_count = cycle_period_s")
        except Exception:
            pass
    elif basis == "instantaneous":
        if periodic is not False or not isinstance(sample_count, int) or isinstance(sample_count, bool) or sample_count < 1:
            errors.append("$.temporal_sampling: instantaneous requires periodic=false and at least one sample")
        if "step" not in value or "cycle_period_s" in value or "averaging_window_s" in value:
            errors.append("$.temporal_sampling: instantaneous requires step and no cycle/averaging field")
    elif basis == "cycle_mean":
        if periodic is not False or sample_count != 1:
            errors.append("$.temporal_sampling: cycle_mean is one non-periodic averaged field")
        if "averaging_window_s" not in value or "step" in value or "cycle_period_s" in value:
            errors.append("$.temporal_sampling: cycle_mean requires averaging_window_s and no step/cycle_period_s")


def _validate_p4(document: dict[str, Any], claims: dict[str, dict[str, Any]], errors: list[str]) -> None:
    wall = document.get("wall_field", {})
    wall_artifacts = wall.get("artifacts", []) if isinstance(wall, dict) else []
    roles = {item.get("role") for item in wall_artifacts if isinstance(item, dict)}
    representation = wall.get("representation") if isinstance(wall, dict) else None
    required_roles = {
        "H_AND_WALL_TEMPERATURE": {"wall_heat_transfer_coefficient", "wall_temperature"},
        "H_AND_WALL_HEAT_FLUX": {"wall_heat_transfer_coefficient", "wall_heat_flux"},
    }
    if representation in required_roles and roles != required_roles[representation]:
        errors.append("$.wall_field: artifact roles do not match representation")
    expected_units = {
        "wall_heat_transfer_coefficient": "W/(m^2*K)",
        "wall_temperature": "K",
        "wall_heat_flux": "W/m^2",
    }
    for item in wall_artifacts:
        if isinstance(item, dict) and item.get("role") in expected_units and item.get("value_unit") != expected_units[item["role"]]:
            errors.append(f"$.wall_field: invalid unit for {item.get('role')}")
    region_map = document.get("region_interface_map", {})
    map_artifact = region_map.get("artifact", {}) if isinstance(region_map, dict) else {}
    if isinstance(map_artifact, dict) and map_artifact.get("role") != "region_interface_map":
        errors.append("$.region_interface_map.artifact.role: expected region_interface_map")
    if isinstance(map_artifact, dict) and map_artifact.get("value_unit") != "1":
        errors.append("$.region_interface_map.artifact.value_unit: expected dimensionless unit '1'")
    interfaces = region_map.get("interfaces", []) if isinstance(region_map, dict) else []
    ids = [item.get("interface_id") for item in interfaces if isinstance(item, dict)]
    if len(ids) != len(set(ids)):
        errors.append("$.region_interface_map.interfaces: interface ids must be unique")
    solid_regions = {item.get("solid_region") for item in interfaces if isinstance(item, dict)}
    material_refs = document.get("solid_material_refs", [])
    material_regions = [item.get("solid_region") for item in material_refs if isinstance(item, dict)]
    if len(material_regions) != len(set(material_regions)):
        errors.append("$.solid_material_refs: solid regions must be unique")
    missing = solid_regions - set(material_regions)
    if missing:
        errors.append(f"$.solid_material_refs: missing material references for {sorted(missing)!r}")
    extra = set(material_regions) - solid_regions
    if extra:
        errors.append(f"$.solid_material_refs: unreferenced material regions are forbidden: {sorted(extra)!r}")

    energy = document.get("energy_sources", {})
    refs = [item.get("provenance_ref") for item in material_refs if isinstance(item, dict)]
    powers: dict[str, Decimal] = {}
    for name in ("q_chip", "q_airjet_self", "q_total"):
        item = energy.get(name, {}) if isinstance(energy, dict) else {}
        if isinstance(item, dict):
            refs.append(item.get("provenance_ref"))
            try:
                powers[name] = Decimal(str(item.get("value")))
            except Exception:
                pass
    _check_active_refs(refs, claims, errors)
    if len(powers) == 3:
        tolerance = Decimal(str(energy.get("sum_tolerance_w", 0)))
        if abs(powers["q_total"] - powers["q_chip"] - powers["q_airjet_self"]) > tolerance:
            errors.append("$.energy_sources: q_total must equal q_chip + q_airjet_self")
        if powers["q_chip"] == Decimal("5.25") and powers["q_airjet_self"] == Decimal("1"):
            errors.append("$.energy_sources: forbidden double count: 5.25 W total cannot be used as chip heat before adding 1 W self-heat")
        if energy.get("operating_point") == "MINI_1W_REFERENCE":
            expected = {"q_chip": Decimal("4.25"), "q_airjet_self": Decimal("1.00"), "q_total": Decimal("5.25")}
            for name, value in expected.items():
                if powers[name] != value:
                    errors.append(f"$.energy_sources.{name}: MINI_1W_REFERENCE requires {value} W")


def validate_document(document: Any) -> None:
    errors: list[str] = []
    _validate_json_complexity(document)
    if not isinstance(document, dict):
        raise ContractValidationError(["$: contract must be an object"])
    contract_type = document.get("contract_type")
    if not isinstance(contract_type, str):
        raise ContractValidationError(["$.contract_type: must be a supported string"])
    schema, _path, schema_hash = _schema_for(contract_type)
    shape_errors = _schema_errors(document, schema, schema)
    errors.extend(shape_errors)
    _walk_no_unknown(document, "$", errors)
    # Semantic routines assume a schema-conformant shape.  Malformed/untrusted
    # input is rejected above without allowing type confusion to escape as an
    # implementation exception.
    if not shape_errors:
        identity = document["identity"]
        if identity.get("schema_sha256") != schema_hash:
            errors.append("$.identity.schema_sha256: does not bind the exact bundled schema bytes")
        _validate_coordinate_system(document["coordinate_system"], errors)
        if contract_type == P4_TYPE:
            _validate_temporal_sampling(document["temporal_sampling"], errors)
        _validate_artifact_uniqueness(document, errors)
        claims = _claim_map(document, errors)
        if contract_type == P2_TYPE:
            _validate_p2(document, claims, errors)
        elif contract_type == P4_TYPE:
            _validate_p4(document, claims, errors)
    if errors:
        raise ContractValidationError(dict.fromkeys(errors))


def validate_file(path: str | Path) -> None:
    with Path(path).open("rb") as handle:
        before = os.fstat(handle.fileno())
        if before.st_size < 1 or before.st_size > MAX_DOCUMENT_BYTES:
            raise ContractValidationError(["$: document size is outside the contract limit"])
        data = handle.read(MAX_DOCUMENT_BYTES + 1)
        after = os.fstat(handle.fileno())
    if (
        len(data) != before.st_size
        or len(data) > MAX_DOCUMENT_BYTES
        or after.st_size != before.st_size
        or after.st_mtime_ns != before.st_mtime_ns
    ):
        raise ContractValidationError(["$: document changed or exceeded limits while being read"])
    validate_document(load_json_bytes(data))

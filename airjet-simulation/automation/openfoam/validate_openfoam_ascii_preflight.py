#!/usr/bin/env python3
"""Fail-closed, read-only preflight for narrow ASCII OpenFOAM case inputs."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, NoReturn, Sequence

from safe_artifact_io import SafeArtifactError, read_bounded_regular_file


SCHEMA_VERSION = "AJM_PLAN_B_OPENFOAM_ASCII_PREFLIGHT_V1"
MAX_CONTRACT_BYTES = 1_048_576
MAX_FOAM_BYTES = 4_194_304
MAX_TOKENS = 100_000
MAX_TOKEN_CHARS = 256
MAX_JSON_DEPTH = 16
MAX_JSON_NODES = 4096
MAX_FIELDS = 16
MAX_ROLE_PATCHES = 64
MAX_ZONE_LABELS = 1_000_000
WORD_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,62}$")
HEX40_RE = re.compile(r"^[0-9a-f]{40}$")
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
INTEGER_RE = re.compile(r"^(0|[1-9][0-9]{0,9})$")
SIGNED_INTEGER_RE = re.compile(r"^-?(0|[1-9][0-9]{0,2})$")
ROOT_KEYS = frozenset(
    {
        "schema_version",
        "openfoam_distribution",
        "openfoam_major",
        "case_scope",
        "source_commit",
        "geometry_manifest_sha256",
        "patch_roles",
        "chamber_cell_zone",
        "fields",
    }
)
ROLE_KEYS = frozenset({"inlet", "outlet", "jet"})
FIELD_KEYS = frozenset({"object", "class", "dimensions"})
ALLOWED_SCOPES = frozenset(
    {"P3_CELL_CALIBRATION_REFERENCE", "P4_FULL_PRODUCT_REFERENCE"}
)
ALLOWED_FIELD_CLASSES = frozenset(
    {
        "volScalarField",
        "volVectorField",
        "surfaceScalarField",
        "surfaceVectorField",
    }
)
REQUIRED_EXPORT_FIELDS: dict[str, tuple[str, str, tuple[int, ...]]] = {
    "rho": ("rho", "volScalarField", (1, -3, 0, 0, 0, 0, 0)),
    "phi": ("phi", "surfaceScalarField", (1, 0, -1, 0, 0, 0, 0)),
    "p": ("p", "volScalarField", (1, -1, -2, 0, 0, 0, 0)),
    "U": ("U", "volVectorField", (0, 1, -1, 0, 0, 0, 0)),
}


class PreflightError(ValueError):
    """Stable rejection suitable for a single-line diagnostic."""


def fail(code: str) -> NoReturn:
    raise PreflightError(code)


@dataclass(frozen=True)
class StableInput:
    data: bytes
    sha256: str


@dataclass(frozen=True)
class FieldContract:
    role: str
    object_name: str
    class_name: str
    dimensions: tuple[int, ...]


@dataclass(frozen=True)
class Contract:
    case_scope: str
    source_commit: str
    geometry_manifest_sha256: str
    patch_roles: dict[str, tuple[str, ...]]
    chamber_cell_zone: str
    fields: dict[str, FieldContract]


@dataclass(frozen=True)
class Token:
    value: str


class Cursor:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.index = 0

    def done(self) -> bool:
        return self.index >= len(self.tokens)

    def peek(self) -> str:
        if self.done():
            fail("FOAM_UNEXPECTED_EOF")
        return self.tokens[self.index].value

    def take(self) -> str:
        value = self.peek()
        self.index += 1
        return value

    def expect(self, expected: str) -> None:
        if self.take() != expected:
            fail("FOAM_UNEXPECTED_TOKEN")


def read_stable(path: Path, max_bytes: int) -> StableInput:
    try:
        data, digest = read_bounded_regular_file(
            str(path), max_bytes, "INPUT_SAFE_READ_REJECTED"
        )
    except SafeArtifactError as exc:
        raise PreflightError("INPUT_SAFE_READ_REJECTED") from exc
    if b"\x00" in data:
        fail("INPUT_NUL_REJECTED")
    return StableInput(data=data, sha256=digest)


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            fail("DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def preflight_json_nesting(data: bytes) -> None:
    depth = 0
    quoted = False
    escaped = False
    for byte in data:
        if quoted:
            if escaped:
                escaped = False
            elif byte == 0x5C:
                escaped = True
            elif byte == 0x22:
                quoted = False
        elif byte == 0x22:
            quoted = True
        elif byte in (0x7B, 0x5B):
            depth += 1
            if depth > MAX_JSON_DEPTH:
                fail("JSON_DEPTH_LIMIT_EXCEEDED")
        elif byte in (0x7D, 0x5D):
            depth -= 1


def bounded_json_int(token: str) -> int:
    if len(token) > 12:
        fail("JSON_INTEGER_LIMIT_EXCEEDED")
    return int(token)


def count_json_nodes(value: Any, depth: int = 0) -> int:
    if depth > MAX_JSON_DEPTH:
        fail("JSON_DEPTH_LIMIT_EXCEEDED")
    if isinstance(value, str):
        if len(value) > MAX_TOKEN_CHARS:
            fail("JSON_STRING_LIMIT_EXCEEDED")
        return 1
    if isinstance(value, dict):
        total = 1
        for key, child in value.items():
            if not isinstance(key, str) or len(key) > MAX_TOKEN_CHARS:
                fail("JSON_KEY_INVALID")
            total += 1 + count_json_nodes(child, depth + 1)
            if total > MAX_JSON_NODES:
                fail("JSON_NODE_LIMIT_EXCEEDED")
        return total
    if isinstance(value, list):
        total = 1
        for child in value:
            total += count_json_nodes(child, depth + 1)
            if total > MAX_JSON_NODES:
                fail("JSON_NODE_LIMIT_EXCEEDED")
        return total
    return 1


def load_contract(path: Path) -> tuple[Contract, str]:
    stable = read_stable(path, MAX_CONTRACT_BYTES)
    if stable.data.startswith(b"\xef\xbb\xbf"):
        fail("INPUT_UTF8_BOM_REJECTED")
    preflight_json_nesting(stable.data)
    try:
        text = stable.data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PreflightError("INPUT_NOT_UTF8") from exc
    try:
        value = json.loads(
            text,
            object_pairs_hook=reject_duplicate_keys,
            parse_int=bounded_json_int,
            parse_float=lambda _token: fail("JSON_FLOAT_REJECTED"),
            parse_constant=lambda _token: fail("JSON_NONFINITE_REJECTED"),
        )
    except PreflightError:
        raise
    except (json.JSONDecodeError, RecursionError) as exc:
        raise PreflightError("CONTRACT_INVALID_JSON") from exc
    count_json_nodes(value)
    if not isinstance(value, dict):
        fail("CONTRACT_ROOT_NOT_OBJECT")
    if set(value) != ROOT_KEYS:
        fail("CONTRACT_KEYS_MISMATCH")
    if value["schema_version"] != SCHEMA_VERSION:
        fail("CONTRACT_SCHEMA_MISMATCH")
    if value["openfoam_distribution"] != "OpenFOAM Foundation":
        fail("CONTRACT_DISTRIBUTION_MISMATCH")
    if isinstance(value["openfoam_major"], bool) or value["openfoam_major"] != 14:
        fail("CONTRACT_MAJOR_MISMATCH")
    if (
        not isinstance(value["case_scope"], str)
        or value["case_scope"] not in ALLOWED_SCOPES
    ):
        fail("CONTRACT_SCOPE_INVALID")
    if not isinstance(value["source_commit"], str) or not HEX40_RE.fullmatch(
        value["source_commit"]
    ):
        fail("CONTRACT_SOURCE_COMMIT_INVALID")
    if not isinstance(
        value["geometry_manifest_sha256"], str
    ) or not HEX64_RE.fullmatch(value["geometry_manifest_sha256"]):
        fail("CONTRACT_GEOMETRY_HASH_INVALID")
    roles_raw = value["patch_roles"]
    if not isinstance(roles_raw, dict) or set(roles_raw) != ROLE_KEYS:
        fail("CONTRACT_PATCH_ROLE_KEYS_INVALID")
    roles: dict[str, tuple[str, ...]] = {}
    for role in sorted(ROLE_KEYS):
        items = roles_raw[role]
        if not isinstance(items, list) or not 1 <= len(items) <= MAX_ROLE_PATCHES:
            fail("CONTRACT_PATCH_ROLE_COUNT_INVALID")
        if any(not isinstance(item, str) or not WORD_RE.fullmatch(item) for item in items):
            fail("CONTRACT_PATCH_NAME_INVALID")
        if len(set(items)) != len(items):
            fail("CONTRACT_PATCH_ROLE_DUPLICATE")
        roles[role] = tuple(sorted(items))
    role_sets = [set(roles[role]) for role in sorted(ROLE_KEYS)]
    if any(role_sets[i] & role_sets[j] for i in range(3) for j in range(i + 1, 3)):
        fail("CONTRACT_PATCH_ROLES_OVERLAP")
    chamber = value["chamber_cell_zone"]
    if not isinstance(chamber, str) or not WORD_RE.fullmatch(chamber):
        fail("CONTRACT_CHAMBER_ZONE_INVALID")
    fields_raw = value["fields"]
    if not isinstance(fields_raw, dict) or set(fields_raw) != set(
        REQUIRED_EXPORT_FIELDS
    ):
        fail("CONTRACT_FIELDS_INVALID")
    fields: dict[str, FieldContract] = {}
    objects: set[str] = set()
    for role, item in fields_raw.items():
        if not isinstance(role, str) or not WORD_RE.fullmatch(role):
            fail("CONTRACT_FIELD_ROLE_INVALID")
        if not isinstance(item, dict) or set(item) != FIELD_KEYS:
            fail("CONTRACT_FIELD_KEYS_INVALID")
        object_name = item["object"]
        class_name = item["class"]
        dimensions = item["dimensions"]
        if not isinstance(object_name, str) or not WORD_RE.fullmatch(object_name):
            fail("CONTRACT_FIELD_OBJECT_INVALID")
        if class_name not in ALLOWED_FIELD_CLASSES:
            fail("CONTRACT_FIELD_CLASS_INVALID")
        if (
            not isinstance(dimensions, list)
            or len(dimensions) != 7
            or any(
                isinstance(exponent, bool)
                or not isinstance(exponent, int)
                or not -100 <= exponent <= 100
                for exponent in dimensions
            )
        ):
            fail("CONTRACT_FIELD_DIMENSIONS_INVALID")
        if object_name in objects:
            fail("CONTRACT_FIELD_OBJECT_DUPLICATE")
        required_object, required_class, required_dimensions = REQUIRED_EXPORT_FIELDS[
            role
        ]
        if (
            object_name != required_object
            or class_name != required_class
            or tuple(dimensions) != required_dimensions
        ):
            fail("CONTRACT_EXPORT_FIELD_SEMANTICS_MISMATCH")
        objects.add(object_name)
        fields[role] = FieldContract(
            role=role,
            object_name=object_name,
            class_name=class_name,
            dimensions=tuple(dimensions),
        )
    return (
        Contract(
            case_scope=value["case_scope"],
            source_commit=value["source_commit"],
            geometry_manifest_sha256=value["geometry_manifest_sha256"],
            patch_roles=roles,
            chamber_cell_zone=chamber,
            fields=fields,
        ),
        stable.sha256,
    )


def tokenize_foam(data: bytes) -> list[Token]:
    if data.startswith(b"\xef\xbb\xbf"):
        fail("INPUT_UTF8_BOM_REJECTED")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PreflightError("INPUT_NOT_UTF8") from exc
    tokens: list[Token] = []
    index = 0
    punctuation = "{}();[]"
    while index < len(text):
        char = text[index]
        if char.isspace():
            index += 1
            continue
        if text.startswith("//", index):
            newline = text.find("\n", index + 2)
            index = len(text) if newline < 0 else newline + 1
            continue
        if text.startswith("/*", index):
            end = text.find("*/", index + 2)
            if end < 0:
                fail("FOAM_UNTERMINATED_COMMENT")
            index = end + 2
            continue
        if char in "#$":
            fail("FOAM_DIRECTIVE_OR_MACRO_REJECTED")
        if char == '"':
            end = index + 1
            escaped = False
            while end < len(text):
                current = text[end]
                if escaped:
                    escaped = False
                elif current == "\\":
                    escaped = True
                elif current == '"':
                    break
                elif ord(current) < 0x20:
                    fail("FOAM_CONTROL_CHARACTER_REJECTED")
                end += 1
            if end >= len(text):
                fail("FOAM_UNTERMINATED_STRING")
            value = text[index : end + 1]
            index = end + 1
        elif char in punctuation:
            value = char
            index += 1
        else:
            end = index
            while (
                end < len(text)
                and not text[end].isspace()
                and text[end] not in punctuation + '"#$'
                and not text.startswith("//", end)
                and not text.startswith("/*", end)
            ):
                end += 1
            value = text[index:end]
            index = end
        if not value or len(value) > MAX_TOKEN_CHARS:
            fail("FOAM_TOKEN_INVALID")
        tokens.append(Token(value))
        if len(tokens) > MAX_TOKENS:
            fail("FOAM_TOKEN_LIMIT_EXCEEDED")
    return tokens


def parse_entries(cursor: Cursor) -> dict[str, tuple[str, ...]]:
    cursor.expect("{")
    entries: dict[str, tuple[str, ...]] = {}
    while cursor.peek() != "}":
        key = cursor.take()
        if not WORD_RE.fullmatch(key) or key in entries:
            fail("FOAM_DICTIONARY_KEY_INVALID_OR_DUPLICATE")
        value: list[str] = []
        paren_depth = 0
        bracket_depth = 0
        while True:
            token = cursor.take()
            if token == ";" and paren_depth == 0 and bracket_depth == 0:
                break
            if token == "{":
                fail("FOAM_NESTED_DICTIONARY_UNSUPPORTED")
            if token == "}":
                fail("FOAM_DICTIONARY_VALUE_UNTERMINATED")
            if token == "(":
                paren_depth += 1
            elif token == ")":
                paren_depth -= 1
            elif token == "[":
                bracket_depth += 1
            elif token == "]":
                bracket_depth -= 1
            if paren_depth < 0 or bracket_depth < 0:
                fail("FOAM_UNBALANCED_VALUE")
            value.append(token)
            if len(value) > MAX_TOKENS:
                fail("FOAM_VALUE_TOKEN_LIMIT_EXCEEDED")
        if not value or paren_depth or bracket_depth:
            fail("FOAM_VALUE_INVALID")
        entries[key] = tuple(value)
    cursor.expect("}")
    return entries


def one(entries: dict[str, tuple[str, ...]], key: str) -> str:
    value = entries.get(key)
    if value is None or len(value) != 1:
        fail("FOAM_REQUIRED_ENTRY_INVALID")
    return value[0]


def parse_header(cursor: Cursor, expected_class: str, expected_object: str) -> None:
    cursor.expect("FoamFile")
    header = parse_entries(cursor)
    if one(header, "format") != "ascii":
        fail("FOAM_FORMAT_NOT_ASCII")
    if one(header, "class") != expected_class:
        fail("FOAM_HEADER_CLASS_MISMATCH")
    if one(header, "object") != expected_object:
        fail("FOAM_HEADER_OBJECT_MISMATCH")


def parse_uint(value: str, code: str) -> int:
    if not INTEGER_RE.fullmatch(value):
        fail(code)
    return int(value)


def parse_boundary(stable: StableInput, contract: Contract) -> dict[str, Any]:
    cursor = Cursor(tokenize_foam(stable.data))
    parse_header(cursor, "polyBoundaryMesh", "boundary")
    declared = parse_uint(cursor.take(), "BOUNDARY_COUNT_INVALID")
    cursor.expect("(")
    patches: list[tuple[str, str, int, int]] = []
    seen: set[str] = set()
    while cursor.peek() != ")":
        name = cursor.take()
        if not WORD_RE.fullmatch(name) or name in seen:
            fail("BOUNDARY_PATCH_NAME_INVALID_OR_DUPLICATE")
        seen.add(name)
        entries = parse_entries(cursor)
        if not {"type", "nFaces", "startFace"} <= set(entries):
            fail("BOUNDARY_PATCH_REQUIRED_ENTRY_MISSING")
        patch_type = one(entries, "type")
        if not WORD_RE.fullmatch(patch_type):
            fail("BOUNDARY_PATCH_TYPE_INVALID")
        n_faces = parse_uint(one(entries, "nFaces"), "BOUNDARY_NFACES_INVALID")
        start = parse_uint(one(entries, "startFace"), "BOUNDARY_STARTFACE_INVALID")
        if n_faces <= 0:
            fail("BOUNDARY_ZERO_FACE_PATCH")
        patches.append((name, patch_type, n_faces, start))
    cursor.expect(")")
    if not cursor.done() and cursor.peek() == ";":
        cursor.take()
    if not cursor.done():
        fail("FOAM_TRAILING_TOKENS")
    if declared != len(patches) or not patches:
        fail("BOUNDARY_DECLARED_COUNT_MISMATCH")
    for previous, current in zip(patches, patches[1:]):
        if current[3] != previous[3] + previous[2]:
            fail("BOUNDARY_FACE_RANGES_NOT_CONTIGUOUS")
    patch_types = {name: patch_type for name, patch_type, _count, _start in patches}
    for role, names in contract.patch_roles.items():
        for name in names:
            if name not in seen:
                fail("BOUNDARY_REQUIRED_ROLE_PATCH_MISSING")
            if patch_types[name] != "patch":
                fail("BOUNDARY_ROLE_POLYPATCH_TYPE_INVALID")
    return {
        "sha256": stable.sha256,
        "patch_count": len(patches),
        "first_start_face": patches[0][3],
        "total_boundary_faces": sum(patch[2] for patch in patches),
        "roles": {role: list(names) for role, names in sorted(contract.patch_roles.items())},
        "role_poly_patch_type": "patch",
    }


def parse_cell_labels(value: tuple[str, ...]) -> tuple[int, ...]:
    if len(value) < 4 or value[0] != "List<label>":
        fail("CELLZONE_LABEL_LIST_INVALID")
    count = parse_uint(value[1], "CELLZONE_LABEL_COUNT_INVALID")
    if value[2] != "(" or value[-1] != ")":
        fail("CELLZONE_LABEL_LIST_INVALID")
    labels = value[3:-1]
    if count != len(labels) or not 1 <= count <= MAX_ZONE_LABELS:
        fail("CELLZONE_LABEL_COUNT_MISMATCH")
    parsed = tuple(parse_uint(item, "CELLZONE_LABEL_INVALID") for item in labels)
    if len(set(parsed)) != len(parsed):
        fail("CELLZONE_LABEL_DUPLICATE")
    return parsed


def parse_cell_zones(stable: StableInput, contract: Contract) -> dict[str, Any]:
    cursor = Cursor(tokenize_foam(stable.data))
    parse_header(cursor, "regIOobject", "cellZones")
    declared = parse_uint(cursor.take(), "CELLZONE_COUNT_INVALID")
    cursor.expect("(")
    zones: dict[str, tuple[int, ...]] = {}
    while cursor.peek() != ")":
        name = cursor.take()
        if not WORD_RE.fullmatch(name) or name in zones:
            fail("CELLZONE_NAME_INVALID_OR_DUPLICATE")
        entries = parse_entries(cursor)
        if set(entries) != {"type", "cellLabels"}:
            fail("CELLZONE_ENTRIES_INVALID")
        if one(entries, "type") != "cellZone":
            fail("CELLZONE_TYPE_INVALID")
        zones[name] = parse_cell_labels(entries["cellLabels"])
    cursor.expect(")")
    if not cursor.done() and cursor.peek() == ";":
        cursor.take()
    if not cursor.done():
        fail("FOAM_TRAILING_TOKENS")
    if declared != len(zones) or not zones:
        fail("CELLZONE_DECLARED_COUNT_MISMATCH")
    labels = zones.get(contract.chamber_cell_zone)
    if labels is None:
        fail("CHAMBER_CELLZONE_MISSING")
    return {
        "sha256": stable.sha256,
        "zone_count": len(zones),
        "chamber_cell_count": len(labels),
    }


def parse_field(stable: StableInput, expected: FieldContract) -> dict[str, Any]:
    cursor = Cursor(tokenize_foam(stable.data))
    parse_header(cursor, expected.class_name, expected.object_name)
    found: tuple[int, ...] | None = None
    brace_depth = 0
    paren_depth = 0
    bracket_depth = 0
    at_entry_start = True
    while not cursor.done():
        token = cursor.take()
        if (
            token == "dimensions"
            and at_entry_start
            and brace_depth == 0
            and paren_depth == 0
            and bracket_depth == 0
        ):
            if found is not None:
                fail("FIELD_DIMENSIONS_DUPLICATE")
            cursor.expect("[")
            values: list[int] = []
            while cursor.peek() != "]":
                raw = cursor.take()
                if not SIGNED_INTEGER_RE.fullmatch(raw):
                    fail("FIELD_DIMENSION_EXPONENT_INVALID")
                values.append(int(raw))
                if len(values) > 7:
                    fail("FIELD_DIMENSION_COUNT_INVALID")
            cursor.expect("]")
            cursor.expect(";")
            if len(values) != 7:
                fail("FIELD_DIMENSION_COUNT_INVALID")
            found = tuple(values)
            at_entry_start = True
            continue
        if token == "{":
            if at_entry_start and brace_depth == 0:
                fail("FIELD_TOP_LEVEL_STRUCTURE_INVALID")
            brace_depth += 1
        elif token == "}":
            brace_depth -= 1
            if brace_depth < 0:
                fail("FIELD_BRACES_UNBALANCED")
            if brace_depth == 0 and paren_depth == 0 and bracket_depth == 0:
                at_entry_start = True
        elif token == "(":
            paren_depth += 1
        elif token == ")":
            paren_depth -= 1
            if paren_depth < 0:
                fail("FIELD_PARENTHESES_UNBALANCED")
        elif token == "[":
            bracket_depth += 1
        elif token == "]":
            bracket_depth -= 1
            if bracket_depth < 0:
                fail("FIELD_BRACKETS_UNBALANCED")
        elif (
            token == ";"
            and brace_depth == 0
            and paren_depth == 0
            and bracket_depth == 0
        ):
            if at_entry_start:
                fail("FIELD_EMPTY_TOP_LEVEL_ENTRY")
            at_entry_start = True
        elif (
            at_entry_start
            and brace_depth == 0
            and paren_depth == 0
            and bracket_depth == 0
        ):
            if not WORD_RE.fullmatch(token):
                fail("FIELD_TOP_LEVEL_KEY_INVALID")
            at_entry_start = False
    if brace_depth or paren_depth or bracket_depth:
        fail("FIELD_DELIMITERS_UNBALANCED")
    if not at_entry_start:
        fail("FIELD_TOP_LEVEL_ENTRY_UNTERMINATED")
    if found is None:
        fail("FIELD_DIMENSIONS_MISSING")
    if found != expected.dimensions:
        fail("FIELD_DIMENSIONS_MISMATCH")
    return {
        "role": expected.role,
        "object": expected.object_name,
        "class": expected.class_name,
        "dimensions": list(found),
        "sha256": stable.sha256,
    }


def parse_field_args(values: Sequence[str]) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for value in values:
        if "=" not in value:
            fail("FIELD_ARGUMENT_INVALID")
        role, raw_path = value.split("=", 1)
        if not WORD_RE.fullmatch(role) or not raw_path or role in result:
            fail("FIELD_ARGUMENT_INVALID")
        result[role] = Path(raw_path)
    return result


def make_result(
    contract: Contract,
    contract_hash: str,
    boundary: dict[str, Any],
    zones: dict[str, Any],
    fields: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "status": "CASE_SOURCE_PREFLIGHT_ACCEPTED",
        "schema_version": SCHEMA_VERSION,
        "case_scope": contract.case_scope,
        "source_commit": contract.source_commit,
        "geometry_manifest_sha256": contract.geometry_manifest_sha256,
        "contract_sha256": contract_hash,
        "boundary": boundary,
        "cell_zones": zones,
        "fields": fields,
        "required_ascii_metadata_verified": True,
        "declared_patch_roles_present": True,
        "role_poly_patch_types_verified": True,
        "required_export_field_semantics_verified": True,
        "declared_field_dimensions_match": True,
        "complete_openfoam_grammar_verified": False,
        "cross_file_snapshot_atomic": False,
        "boundary_condition_physics_verified": False,
        "mesh_owner_neighbour_verified": False,
        "mesh_geometry_quality_verified": False,
        "cell_zone_mesh_membership_verified": False,
        "runtime_verified": False,
        "solver_verified": False,
        "solver_authorized": False,
        "formal_gate_effect": "NONE",
    }


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--boundary", required=True, type=Path)
    parser.add_argument("--cell-zones", required=True, type=Path)
    parser.add_argument("--field", action="append", default=[])
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = parse_args(sys.argv[1:] if argv is None else argv)
        contract, contract_hash = load_contract(args.contract)
        field_paths = parse_field_args(args.field)
        if set(field_paths) != set(contract.fields):
            fail("FIELD_ARGUMENT_ROLES_MISMATCH")
        boundary = parse_boundary(
            read_stable(args.boundary, MAX_FOAM_BYTES), contract
        )
        zones = parse_cell_zones(
            read_stable(args.cell_zones, MAX_FOAM_BYTES), contract
        )
        fields = [
            parse_field(
                read_stable(field_paths[role], MAX_FOAM_BYTES),
                contract.fields[role],
            )
            for role in sorted(contract.fields)
        ]
        print(
            json.dumps(
                make_result(contract, contract_hash, boundary, zones, fields),
                ensure_ascii=True,
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    except PreflightError as exc:
        print(f"REJECTED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

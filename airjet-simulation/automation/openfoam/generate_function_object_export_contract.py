#!/usr/bin/env python3
"""Generate an inert OpenFOAM Foundation v14 function-object export snippet.

The generator is deliberately source-only.  It validates a small JSON descriptor
and prints either a deterministic OpenFOAM dictionary fragment or a JSON envelope
containing that fragment.  It never edits a case, invokes OpenFOAM, or advances a
project gate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, NoReturn, Sequence


SCHEMA_VERSION = "AJM_PLAN_B_OPENFOAM_EXPORT_CONTRACT_V1"
OPENFOAM_DISTRIBUTION = "OpenFOAM Foundation"
OPENFOAM_MAJOR = 14
MAX_DESCRIPTOR_BYTES = 1_048_576
MAX_JSON_DEPTH = 16
MAX_JSON_NODES = 4096
MAX_STRING_CHARS = 256
MAX_PATCHES_PER_ROLE = 32
FOAM_WORD_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,62}$")
HEX40_RE = re.compile(r"^[0-9a-f]{40}$")
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
EXPECTED_KEYS = frozenset(
    {
        "schema_version",
        "openfoam_distribution",
        "openfoam_major",
        "case_scope",
        "source_commit",
        "geometry_manifest_sha256",
        "write_control",
        "phi_dimensions",
        "field_names",
        "chamber_cell_zone",
        "inlet_patches",
        "outlet_patches",
        "jet_patches",
    }
)
EXPECTED_FIELD_NAMES = {
    "density": "rho",
    "flux": "phi",
    "pressure": "p",
    "velocity": "U",
}
ALLOWED_CASE_SCOPES = frozenset(
    {"P3_CELL_CALIBRATION_REFERENCE", "P4_FULL_PRODUCT_REFERENCE"}
)
EXPECTED_PHI_DIMENSIONS = [1, 0, -1, 0, 0, 0, 0]


class ContractError(ValueError):
    """A fail-closed validation error with a stable machine-readable code."""


@dataclass(frozen=True)
class Contract:
    case_scope: str
    source_commit: str
    geometry_manifest_sha256: str
    chamber_cell_zone: str
    inlet_patches: tuple[str, ...]
    outlet_patches: tuple[str, ...]
    jet_patches: tuple[str, ...]

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "case_scope": self.case_scope,
            "chamber_cell_zone": self.chamber_cell_zone,
            "field_names": EXPECTED_FIELD_NAMES,
            "geometry_manifest_sha256": self.geometry_manifest_sha256,
            "inlet_patches": list(self.inlet_patches),
            "jet_patches": list(self.jet_patches),
            "openfoam_distribution": OPENFOAM_DISTRIBUTION,
            "openfoam_major": OPENFOAM_MAJOR,
            "outlet_patches": list(self.outlet_patches),
            "phi_dimensions": EXPECTED_PHI_DIMENSIONS,
            "schema_version": SCHEMA_VERSION,
            "source_commit": self.source_commit,
            "write_control": "writeTime",
        }


def fail(code: str) -> NoReturn:
    raise ContractError(code)


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            fail("DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def parse_bounded_json_int(token: str) -> int:
    if len(token) > 20:
        fail("JSON_INTEGER_TOKEN_LIMIT_EXCEEDED")
    return int(token)


def count_json_nodes(value: Any, depth: int = 0) -> int:
    if depth > MAX_JSON_DEPTH:
        fail("JSON_DEPTH_LIMIT_EXCEEDED")
    if isinstance(value, str):
        if len(value) > MAX_STRING_CHARS:
            fail("JSON_STRING_LIMIT_EXCEEDED")
        return 1
    if isinstance(value, dict):
        total = 1
        for key, child in value.items():
            if not isinstance(key, str):
                fail("JSON_OBJECT_KEY_NOT_STRING")
            if len(key) > MAX_STRING_CHARS:
                fail("JSON_STRING_LIMIT_EXCEEDED")
            total += 1 + count_json_nodes(child, depth + 1)
            if total > MAX_JSON_NODES:
                fail("JSON_NODE_LIMIT_EXCEEDED")
        return total
    if isinstance(value, list):
        if len(value) > MAX_JSON_NODES:
            fail("JSON_ARRAY_LIMIT_EXCEEDED")
        total = 1
        for child in value:
            total += count_json_nodes(child, depth + 1)
            if total > MAX_JSON_NODES:
                fail("JSON_NODE_LIMIT_EXCEEDED")
        return total
    return 1


def lstat_descriptor(path: Path, phase: str) -> os.stat_result:
    try:
        return os.lstat(path)
    except OSError as exc:
        raise ContractError(
            f"DESCRIPTOR_{phase}_LSTAT_FAILED_{exc.__class__.__name__}"
        ) from exc


def is_link_or_reparse(value: os.stat_result) -> bool:
    return stat.S_ISLNK(value.st_mode) or bool(
        getattr(value, "st_file_attributes", 0)
        & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    )


def preflight_json_nesting(data: bytes) -> None:
    depth = 0
    in_string = False
    escaped = False
    for byte in data:
        if in_string:
            if escaped:
                escaped = False
            elif byte == 0x5C:
                escaped = True
            elif byte == 0x22:
                in_string = False
            continue
        if byte == 0x22:
            in_string = True
        elif byte in (0x7B, 0x5B):
            depth += 1
            if depth > MAX_JSON_DEPTH:
                fail("JSON_DEPTH_LIMIT_EXCEEDED")
        elif byte in (0x7D, 0x5D):
            depth -= 1


def read_stable_descriptor(path: Path) -> bytes:
    path_before_open = lstat_descriptor(path, "PREOPEN")
    if is_link_or_reparse(path_before_open):
        fail("DESCRIPTOR_LINK_OR_REPARSE_POINT_REJECTED")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise ContractError(f"DESCRIPTOR_OPEN_FAILED_{exc.__class__.__name__}") from exc
    try:
        before = os.fstat(fd)
        path_after_open = lstat_descriptor(path, "POSTOPEN")
        if is_link_or_reparse(path_after_open):
            fail("DESCRIPTOR_LINK_OR_REPARSE_POINT_REJECTED")
        if (path_after_open.st_dev, path_after_open.st_ino) != (
            before.st_dev,
            before.st_ino,
        ):
            fail("DESCRIPTOR_PATH_IDENTITY_MISMATCH")
        if not stat.S_ISREG(before.st_mode):
            fail("DESCRIPTOR_NOT_REGULAR_FILE")
        if before.st_size <= 0:
            fail("DESCRIPTOR_EMPTY")
        if before.st_size > MAX_DESCRIPTOR_BYTES:
            fail("DESCRIPTOR_SIZE_LIMIT_EXCEEDED")
        chunks: list[bytes] = []
        remaining = MAX_DESCRIPTOR_BYTES + 1
        while remaining:
            chunk = os.read(fd, min(65_536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        data = b"".join(chunks)
        after = os.fstat(fd)
    finally:
        os.close(fd)
    identity_before = (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
    )
    identity_after = (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
    )
    if identity_before != identity_after or len(data) != before.st_size:
        fail("DESCRIPTOR_CHANGED_DURING_READ")
    if len(data) > MAX_DESCRIPTOR_BYTES:
        fail("DESCRIPTOR_SIZE_LIMIT_EXCEEDED")
    if b"\x00" in data:
        fail("DESCRIPTOR_NUL_BYTE_REJECTED")
    return data


def load_json_descriptor(path: Path) -> dict[str, Any]:
    data = read_stable_descriptor(path)
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ContractError("DESCRIPTOR_NOT_UTF8") from exc
    if text.startswith("\ufeff"):
        fail("DESCRIPTOR_UTF8_BOM_REJECTED")
    preflight_json_nesting(data)
    try:
        value = json.loads(
            text,
            object_pairs_hook=reject_duplicate_keys,
            parse_int=parse_bounded_json_int,
            parse_float=lambda _token: fail("JSON_FLOAT_REJECTED"),
            parse_constant=lambda token: fail(f"JSON_NONFINITE_{token}"),
        )
    except ContractError:
        raise
    except RecursionError as exc:
        raise ContractError("JSON_DEPTH_LIMIT_EXCEEDED") from exc
    except json.JSONDecodeError as exc:
        raise ContractError("DESCRIPTOR_INVALID_JSON") from exc
    count_json_nodes(value)
    if not isinstance(value, dict):
        fail("DESCRIPTOR_ROOT_NOT_OBJECT")
    return value


def require_exact_keys(value: dict[str, Any]) -> None:
    actual = set(value)
    missing = sorted(EXPECTED_KEYS - actual)
    extra = sorted(actual - EXPECTED_KEYS)
    if missing:
        fail("DESCRIPTOR_MISSING_KEYS_" + "_".join(missing))
    if extra:
        fail("DESCRIPTOR_EXTRA_KEYS")


def require_foam_word(value: Any, role: str) -> str:
    if not isinstance(value, str) or not FOAM_WORD_RE.fullmatch(value):
        fail(f"INVALID_FOAM_WORD_{role}")
    return value


def require_patch_list(value: Any, role: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        fail(f"{role}_NOT_ARRAY")
    if not 1 <= len(value) <= MAX_PATCHES_PER_ROLE:
        fail(f"{role}_COUNT_OUT_OF_RANGE")
    patches = tuple(require_foam_word(item, role) for item in value)
    if len(set(patches)) != len(patches):
        fail(f"{role}_DUPLICATE")
    return tuple(sorted(patches))


def validate_descriptor(value: dict[str, Any]) -> Contract:
    require_exact_keys(value)
    if value["schema_version"] != SCHEMA_VERSION:
        fail("SCHEMA_VERSION_MISMATCH")
    if value["openfoam_distribution"] != OPENFOAM_DISTRIBUTION:
        fail("OPENFOAM_DISTRIBUTION_MISMATCH")
    if (
        isinstance(value["openfoam_major"], bool)
        or value["openfoam_major"] != OPENFOAM_MAJOR
    ):
        fail("OPENFOAM_MAJOR_MISMATCH")
    if not isinstance(value["case_scope"], str) or value[
        "case_scope"
    ] not in ALLOWED_CASE_SCOPES:
        fail("CASE_SCOPE_NOT_ALLOWED")
    if not isinstance(value["source_commit"], str) or not HEX40_RE.fullmatch(
        value["source_commit"]
    ):
        fail("SOURCE_COMMIT_INVALID")
    if not isinstance(
        value["geometry_manifest_sha256"], str
    ) or not HEX64_RE.fullmatch(value["geometry_manifest_sha256"]):
        fail("GEOMETRY_MANIFEST_SHA256_INVALID")
    if value["write_control"] != "writeTime":
        fail("WRITE_CONTROL_MUST_BE_WRITETIME")
    if (
        not isinstance(value["phi_dimensions"], list)
        or any(isinstance(item, bool) for item in value["phi_dimensions"])
        or value["phi_dimensions"] != EXPECTED_PHI_DIMENSIONS
    ):
        fail("PHI_DIMENSIONS_MUST_BE_MASS_FLUX")
    if value["field_names"] != EXPECTED_FIELD_NAMES:
        fail("FIELD_NAMES_MISMATCH")
    chamber = require_foam_word(value["chamber_cell_zone"], "CHAMBER_CELL_ZONE")
    inlets = require_patch_list(value["inlet_patches"], "INLET_PATCHES")
    outlets = require_patch_list(value["outlet_patches"], "OUTLET_PATCHES")
    jets = require_patch_list(value["jet_patches"], "JET_PATCHES")
    roles = {
        "INLET_OUTLET": set(inlets) & set(outlets),
        "INLET_JET": set(inlets) & set(jets),
        "OUTLET_JET": set(outlets) & set(jets),
    }
    for role, overlap in roles.items():
        if overlap:
            fail(f"PATCH_ROLE_OVERLAP_{role}")
    return Contract(
        case_scope=value["case_scope"],
        source_commit=value["source_commit"],
        geometry_manifest_sha256=value["geometry_manifest_sha256"],
        chamber_cell_zone=chamber,
        inlet_patches=inlets,
        outlet_patches=outlets,
        jet_patches=jets,
    )


def render_word_list(words: Sequence[str]) -> str:
    return "(" + " ".join(words) + ")"


def render_function_objects(contract: Contract) -> str:
    inlets = render_word_list(contract.inlet_patches)
    outlets = render_word_list(contract.outlet_patches)
    jets = render_word_list(contract.jet_patches)
    return f"""functions
{{
    ajmDomainMass
    {{
        type            volFieldValue;
        libs            ("libfieldFunctionObjects.so");
        log             false;
        writeControl    writeTime;
        writeFields     false;
        cellZone        all;
        operation       volIntegrate;
        fields          (rho);
    }}

    ajmChamberPressure
    {{
        type            volFieldValue;
        libs            ("libfieldFunctionObjects.so");
        log             false;
        writeControl    writeTime;
        writeFields     false;
        cellZone        {contract.chamber_cell_zone};
        operation       volAverage;
        fields          (p);
    }}

    ajmInletMassFluxRaw
    {{
        type            surfaceFieldValue;
        libs            ("libfieldFunctionObjects.so");
        log             false;
        writeControl    writeTime;
        writeFields     false;
        patches         {inlets};
        operation       orientedSum;
        fields          (phi);
    }}

    ajmOutletMassFluxRaw
    {{
        type            surfaceFieldValue;
        libs            ("libfieldFunctionObjects.so");
        log             false;
        writeControl    writeTime;
        writeFields     false;
        patches         {outlets};
        operation       orientedSum;
        fields          (phi);
    }}

    ajmJetSpeedPeak
    {{
        type            surfaceFieldValue;
        libs            ("libfieldFunctionObjects.so");
        log             false;
        writeControl    writeTime;
        writeFields     false;
        patches         {jets};
        operation       maxMag;
        fields          (U);
    }}
}}
"""


def contract_sha256(contract: Contract) -> str:
    canonical = json.dumps(
        contract.canonical_payload(),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")
    return hashlib.sha256(canonical).hexdigest()


def make_envelope(contract: Contract, snippet: str) -> dict[str, Any]:
    return {
        "status": "SOURCE_ONLY_EXPORT_CONTRACT_GENERATED",
        "schema_version": SCHEMA_VERSION,
        "contract_sha256": contract_sha256(contract),
        "case_scope": contract.case_scope,
        "openfoam_distribution": OPENFOAM_DISTRIBUTION,
        "openfoam_major": OPENFOAM_MAJOR,
        "function_objects": snippet,
        "raw_sign_semantics": (
            "BOUNDARY_PATCH_PHI_OUTWARD_POSITIVE_EXPECTED; PRESERVE_REVERSE_FLOW; "
            "RUNTIME_SIGN_MUST_BE_VERIFIED_AND_NORMALIZED_BY_A_SEPARATE_PRODUCER"
        ),
        "energy_export": "NOT_IMPLEMENTED_REQUIRES_SOLVER_SPECIFIC_REVIEW",
        "region_scope": "DEFAULT_OBJECT_REGISTRY_SINGLE_FLUID_REGION_ONLY",
        "normalization_merge_layer": "NOT_IMPLEMENTED",
        "analyzer_csv_ready": False,
        "write_schedule_sampling_density_verified": False,
        "mass_source_sink_terms_included": False,
        "jet_observable_semantics": (
            "MAXIMUM_U_MAGNITUDE_ON_NAMED_BOUNDARY_PATCHES; NOT_NORMAL_VELOCITY; "
            "NOT_AREA_AVERAGE; NOT_INTERNAL_FACEZONE"
        ),
        "runtime_field_dimensions_verified": False,
        "runtime_patch_existence_verified": False,
        "runtime_cell_zone_existence_verified": False,
        "mesh_verified": False,
        "time_step_verified": False,
        "solver_verified": False,
        "solver_authorized": False,
        "formal_gate_effect": "NONE",
    }


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("descriptor", type=Path)
    parser.add_argument(
        "--output-format",
        choices=("json", "foam"),
        default="json",
        help="Print a JSON truth envelope (default) or the inert dictionary fragment.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        contract = validate_descriptor(load_json_descriptor(args.descriptor))
        snippet = render_function_objects(contract)
        if args.output_format == "foam":
            print("// SOURCE_ONLY=true")
            print("// SOLVER_AUTHORIZED=false")
            print("// FORMAL_GATE_EFFECT=NONE")
            print("// RUNTIME_FIELD_DIMENSIONS_VERIFIED=false")
            print("// ANALYZER_CSV_READY=false")
            print(snippet, end="")
        else:
            print(
                json.dumps(
                    make_envelope(contract, snippet),
                    ensure_ascii=True,
                    indent=2,
                    sort_keys=True,
                )
            )
        return 0
    except ContractError as exc:
        print(f"REJECTED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

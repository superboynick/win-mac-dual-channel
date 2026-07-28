#!/usr/bin/env python3
"""Generate an inert OpenFOAM Foundation v14 mesh-motion planning envelope."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, NoReturn, Sequence

from safe_artifact_io import (
    MAX_CONTRACT_BYTES,
    SafeArtifactError,
    read_bounded_regular_file,
)


SCHEMA_VERSION = "AJM_PLAN_B_OPENFOAM_V14_MOTION_CONTRACT_V1"
OPENFOAM_DISTRIBUTION = "OpenFOAM Foundation"
OPENFOAM_MAJOR = 14
CASE_SCOPE = "P3_CELL_CALIBRATION_REFERENCE"
POINT_VECTOR_FIELD_NAME = "p2PrescribedPointDisplacement"
MAX_JSON_DEPTH = 12
MAX_JSON_NODES = 512
MAX_STRING_CHARS = 256
FOAM_WORD_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,62}$")
HEX40_RE = re.compile(r"^[0-9a-f]{40}$")
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
FORBIDDEN_DIALECT = frozenset(
    {
        "dynamicFvMesh",
        "motionSolver",
        "motionSolverLibs",
        "oscillatingDisplacement",
    }
)
EXPECTED_KEYS = frozenset(
    {
        "schema_version",
        "openfoam_distribution",
        "openfoam_major",
        "case_scope",
        "source_commit",
        "geometry_manifest_sha256",
        "motion_patch",
        "motion_field_status",
        "point_displacement_file_generation",
        "p2_artifact_authorized",
        "p3_case_write_authorized",
        "solver_authorized",
        "formal_gate_effect",
    }
)


class MotionContractError(ValueError):
    """A fail-closed rejection containing only a stable diagnostic code."""

    def __init__(
        self,
        code: str,
        *,
        descriptor_bytes_match_caller_pin: bool = False,
        descriptor_schema_accepted: bool = False,
    ):
        self.code = code
        self.descriptor_bytes_match_caller_pin = (
            descriptor_bytes_match_caller_pin
        )
        self.descriptor_schema_accepted = descriptor_schema_accepted
        super().__init__(code)


def fail(code: str) -> NoReturn:
    raise MotionContractError(code)


def _duplicate_guard(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            fail("DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def _bounded_int(token: str) -> int:
    if len(token) > 16:
        fail("JSON_INTEGER_TOKEN_LIMIT_EXCEEDED")
    return int(token)


def _preflight_depth(data: bytes) -> None:
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


def _count_and_reject(value: Any, depth: int = 0) -> int:
    if depth > MAX_JSON_DEPTH:
        fail("JSON_DEPTH_LIMIT_EXCEEDED")
    if isinstance(value, str):
        if len(value) > MAX_STRING_CHARS:
            fail("JSON_STRING_LIMIT_EXCEEDED")
        if value in FORBIDDEN_DIALECT:
            fail("LEGACY_OR_UNIFORM_MODE_DIALECT_REJECTED")
        return 1
    if isinstance(value, dict):
        total = 1
        for key, child in value.items():
            if not isinstance(key, str) or len(key) > MAX_STRING_CHARS:
                fail("JSON_KEY_INVALID")
            if key in FORBIDDEN_DIALECT:
                fail("LEGACY_OR_UNIFORM_MODE_DIALECT_REJECTED")
            total += 1 + _count_and_reject(child, depth + 1)
            if total > MAX_JSON_NODES:
                fail("JSON_NODE_LIMIT_EXCEEDED")
        return total
    if isinstance(value, list):
        total = 1
        for child in value:
            total += _count_and_reject(child, depth + 1)
            if total > MAX_JSON_NODES:
                fail("JSON_NODE_LIMIT_EXCEEDED")
        return total
    return 1


def _parse_after_pin(data: bytes) -> dict[str, Any]:
    if data.startswith(b"\xef\xbb\xbf"):
        fail("DESCRIPTOR_UTF8_BOM_REJECTED")
    if b"\x00" in data:
        fail("DESCRIPTOR_NUL_REJECTED")
    _preflight_depth(data)
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise MotionContractError("DESCRIPTOR_NOT_UTF8") from exc
    try:
        value = json.loads(
            text,
            object_pairs_hook=_duplicate_guard,
            parse_int=_bounded_int,
            parse_float=lambda _token: fail("JSON_FLOAT_REJECTED"),
            parse_constant=lambda _token: fail("JSON_NONFINITE_REJECTED"),
        )
    except MotionContractError:
        raise
    except (json.JSONDecodeError, RecursionError, ValueError, MemoryError) as exc:
        raise MotionContractError("DESCRIPTOR_INVALID_JSON") from exc
    _count_and_reject(value)
    if not isinstance(value, dict):
        fail("DESCRIPTOR_ROOT_NOT_OBJECT")
    return value


def _require_false(value: Any, code: str) -> None:
    if value is not False:
        fail(code)


def _validate(value: dict[str, Any]) -> str:
    if set(value) != EXPECTED_KEYS:
        fail("DESCRIPTOR_KEYS_MISMATCH")
    if value["schema_version"] != SCHEMA_VERSION:
        fail("SCHEMA_VERSION_MISMATCH")
    if value["openfoam_distribution"] != OPENFOAM_DISTRIBUTION:
        fail("OPENFOAM_DISTRIBUTION_MISMATCH")
    if (
        isinstance(value["openfoam_major"], bool)
        or not isinstance(value["openfoam_major"], int)
        or value["openfoam_major"] != OPENFOAM_MAJOR
    ):
        fail("OPENFOAM_MAJOR_MISMATCH")
    if value["case_scope"] != CASE_SCOPE:
        fail("CASE_SCOPE_MISMATCH")
    if not isinstance(value["source_commit"], str) or HEX40_RE.fullmatch(
        value["source_commit"]
    ) is None:
        fail("SOURCE_COMMIT_INVALID")
    if not isinstance(
        value["geometry_manifest_sha256"], str
    ) or HEX64_RE.fullmatch(value["geometry_manifest_sha256"]) is None:
        fail("GEOMETRY_MANIFEST_SHA256_INVALID")
    patch = value["motion_patch"]
    if not isinstance(patch, str) or FOAM_WORD_RE.fullmatch(patch) is None:
        fail("MOTION_PATCH_INVALID_FOAM_WORD")
    if patch in FORBIDDEN_DIALECT:
        fail("LEGACY_OR_UNIFORM_MODE_DIALECT_REJECTED")
    if value["motion_field_status"] != "REAL_P2_SPATIAL_FIELD_NOT_AVAILABLE":
        fail("MOTION_FIELD_STATUS_MISMATCH")
    if value["point_displacement_file_generation"] != "REJECT":
        fail("POINT_DISPLACEMENT_FILE_GENERATION_MUST_REJECT")
    _require_false(value["p2_artifact_authorized"], "P2_AUTHORIZATION_MUST_BE_FALSE")
    _require_false(
        value["p3_case_write_authorized"], "P3_CASE_WRITE_AUTHORIZATION_MUST_BE_FALSE"
    )
    _require_false(value["solver_authorized"], "SOLVER_AUTHORIZATION_MUST_BE_FALSE")
    if value["formal_gate_effect"] != "NONE":
        fail("FORMAL_GATE_EFFECT_MUST_BE_NONE")
    return patch


def _dynamic_mesh_fragment(patch: str) -> str:
    return f"""mover
{{
    type            displacementLaplacian;
    libs            ("libfvMotionSolvers.so");
    diffusivity     inverseDistance 1({patch});
}}
"""


def _motion_patch_fragment(patch: str) -> str:
    return f"""{patch}
{{
    type                uniformInterpolatedDisplacement;
    value               uniform (0 0 0);
    field               {POINT_VECTOR_FIELD_NAME};
    interpolationScheme linear;
}}
"""


def _authorization_truth() -> dict[str, bool | str]:
    return {
        "descriptor_authority_verified": False,
        "source_commit_authority_verified": False,
        "geometry_verified": False,
        "motion_patch_exists_verified": False,
        "patch_inventory_verified": False,
        "real_p2_artifact_bytes_consumed": False,
        "real_p2_spatial_field_available": False,
        "p2_artifact_authority_verified": False,
        "mesh_identity_verified": False,
        "motion_field_point_order_verified": False,
        "p2_node_to_openfoam_point_bijection_verified": False,
        "p2_mapping_verified": False,
        "p2_component_order_verified": False,
        "p2_spatial_units_verified": False,
        "p2_coordinate_transform_verified": False,
        "p2_phase_time_origin_verified": False,
        "p2_time_sampling_verified": False,
        "control_dict_user_time_verified": False,
        "period_closure_verified": False,
        "point_displacement_file_generated": False,
        "case_file_written": False,
        "openfoam_runtime_syntax_verified": False,
        "diffusivity_suitability_verified": False,
        "mesh_motion_verified": False,
        "negative_volume_verified": False,
        "mesh_quality_verified": False,
        "p2_displacement_verified": False,
        "p2_displacement_authorized": False,
        "p3_authorized": False,
        "p3_case_write_authorized": False,
        "p3_solver_run_authorized": False,
        "solver_verified": False,
        "solver_authorized": False,
        "stage_gate_advanced": False,
        "formal_gate_effect": "NONE",
    }


def _envelope(value: dict[str, Any], digest: str, patch: str) -> dict[str, Any]:
    return {
        "status": "OPENFOAM_V14_MOTION_CONTRACT_SOURCE_ONLY_NOT_AUTHORIZED",
        "schema_version": SCHEMA_VERSION,
        "descriptor_sha256": digest,
        "descriptor_bytes_match_caller_pin": True,
        "descriptor_schema_accepted": True,
        "descriptor_sha256_is_caller_supplied_pin": True,
        "descriptor_pin_authority_verified": False,
        "source_commit": value["source_commit"],
        "source_commit_verified": False,
        "geometry_manifest_sha256": value["geometry_manifest_sha256"],
        "geometry_manifest_verified": False,
        "motion_patch": patch,
        "motion_patch_verified_against_mesh": False,
        "openfoam_distribution": OPENFOAM_DISTRIBUTION,
        "openfoam_major": OPENFOAM_MAJOR,
        "dynamic_mesh_dict_mover_fragment": _dynamic_mesh_fragment(patch),
        "point_displacement_motion_patch_fragment": _motion_patch_fragment(patch),
        "point_vector_field_name": POINT_VECTOR_FIELD_NAME,
        "foundation_v14_template_emitted": True,
        "dynamic_mesh_mover_fragment_generated": True,
        "point_displacement_motion_patch_fragment_generated": True,
        "legacy_dialect_rejected": True,
        "oscillating_displacement_rejected": True,
        "uniform_interpolated_displacement_semantics":
            "TIME_INTERPOLATION_OF_FULL_POINT_VECTOR_FIELDS_NOT_UNIFORM_PATCH_AMPLITUDE",
        "required_before_case_write": {
            "complete_patch_inventory_exactly_classified":
                "REQUIRED_NOT_VERIFIED",
            "point_displacement_class": "pointVectorField",
            "point_displacement_dimensions": "[length]",
            "point_displacement_internal_field": "uniform (0 0 0)",
            "motion_fields_are_full_mesh_time_indexed_point_vector_fields":
                "REQUIRED_NOT_VERIFIED",
            "motion_field_count_at_least_two": "REQUIRED_NOT_VERIFIED",
            "motion_field_times_strictly_increasing": "REQUIRED_NOT_VERIFIED",
            "motion_field_times_cover_solver_interval": "REQUIRED_NOT_VERIFIED",
            "period_endpoints_close": "REQUIRED_NOT_VERIFIED",
            "control_dict_user_time_mapping_bound": "REQUIRED_NOT_VERIFIED",
            "motion_field_point_order_matches_mesh": "REQUIRED_NOT_VERIFIED",
            "p2_node_to_openfoam_point_bijection_checked":
                "REQUIRED_NOT_VERIFIED",
            "coordinate_system_and_component_order_checked":
                "REQUIRED_NOT_VERIFIED",
            "spatial_units_converted_to_openfoam_length":
                "REQUIRED_NOT_VERIFIED",
            "phase_and_time_origin_checked": "REQUIRED_NOT_VERIFIED",
            "p2_artifact_bytes_verified_and_authorized":
                "REQUIRED_NOT_VERIFIED",
            "inverse_distance_diffusivity_suitability_checked":
                "REQUIRED_NOT_VERIFIED",
            "negative_volume_and_mesh_quality_checked":
                "REQUIRED_NOT_VERIFIED",
        },
        "complete_point_displacement_file_generated": False,
        "point_displacement_header_generated": False,
        "non_motion_patch_entries_generated": False,
        "uniform_amplitude_vector_used_as_p2_mode": False,
        **_authorization_truth(),
    }


def generate(descriptor: str, caller_pin: str) -> dict[str, Any]:
    if (
        not isinstance(descriptor, str)
        or not os.path.isabs(descriptor)
        or not isinstance(caller_pin, str)
        or HEX64_RE.fullmatch(caller_pin) is None
    ):
        fail("ARGUMENT_CONFIG_REJECTED")
    try:
        data, digest = read_bounded_regular_file(
            descriptor, MAX_CONTRACT_BYTES, "DESCRIPTOR_READ_REJECTED"
        )
    except SafeArtifactError as exc:
        raise MotionContractError(exc.code) from exc
    if not hmac.compare_digest(digest, caller_pin):
        fail("DESCRIPTOR_PIN_MISMATCH")
    try:
        value = _parse_after_pin(data)
        patch = _validate(value)
    except MotionContractError as exc:
        raise MotionContractError(
            exc.code,
            descriptor_bytes_match_caller_pin=True,
            descriptor_schema_accepted=False,
        ) from exc
    return _envelope(value, digest, patch)


def _rejection(
    code: str,
    exit_code: int,
    *,
    descriptor_bytes_match_caller_pin: bool = False,
    descriptor_schema_accepted: bool = False,
) -> int:
    print(
        json.dumps(
            {
                "status": "REJECTED",
                "error": {"code": code, "message": "input rejected"},
                "descriptor_bytes_match_caller_pin":
                    descriptor_bytes_match_caller_pin,
                "descriptor_schema_accepted": descriptor_schema_accepted,
                "foundation_v14_template_emitted": False,
                "dynamic_mesh_mover_fragment_generated": False,
                "point_displacement_motion_patch_fragment_generated": False,
                **_authorization_truth(),
            },
            sort_keys=True,
        )
    )
    return exit_code


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if (
        len(args) != 2
        or not isinstance(args[0], str)
        or not os.path.isabs(args[0])
        or not isinstance(args[1], str)
        or HEX64_RE.fullmatch(args[1]) is None
    ):
        return _rejection("ARGUMENT_CONFIG_REJECTED", 3)
    try:
        result = generate(args[0], args[1])
    except MotionContractError as exc:
        return _rejection(
            exc.code,
            2,
            descriptor_bytes_match_caller_pin=(
                exc.descriptor_bytes_match_caller_pin
            ),
            descriptor_schema_accepted=exc.descriptor_schema_accepted,
        )
    print(json.dumps(result, ensure_ascii=True, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

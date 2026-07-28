#!/usr/bin/env python3
"""Negative interlock for three pinned, source-only P3 motion inputs."""

from __future__ import annotations

import hmac
import json
import os
import re
import sys
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, localcontext
from typing import Any, NoReturn, Sequence

from safe_artifact_io import (
    MAX_ARTIFACT_BYTES,
    MAX_CONTRACT_BYTES,
    MAX_TOTAL_ARTIFACT_BYTES,
    SafeArtifactError,
    read_bounded_regular_file,
)


HEX40_RE = re.compile(r"^[0-9a-f]{40}$")
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
DECIMAL_RE = re.compile(r"^(0|[1-9][0-9]*)(\.[0-9]+)?$")
FOAM_WORD_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,62}$")
MAX_DEPTH = 16
MAX_NODES = 10_000
MAX_STRING = 16_384
BLOCKED_EXIT = 4
MOTION_SCHEMA = "AJM_PLAN_B_OPENFOAM_V14_MOTION_CONTRACT_V1"
TIMESTEP_SCHEMA = "AJM_PLAN_B_P3_TIMESTEP_PLAN_V1"
OPENFOAM_DISTRIBUTION = "OpenFOAM Foundation"
OPENFOAM_MAJOR = 14
POINT_VECTOR_FIELD_NAME = "p2PrescribedPointDisplacement"
MIN_FREQUENCY_HZ = Decimal("0.001")
MAX_FREQUENCY_HZ = Decimal("9999999")
SOURCE_NAMES = ("p2_artifact_receipt", "motion_contract", "timestep_plan")
EXPECTED_STATUSES = {
    "p2_artifact_receipt": "P2_ARTIFACT_BYTES_MATCH_CALLER_PIN_NOT_AUTHORIZED",
    "motion_contract": "OPENFOAM_V14_MOTION_CONTRACT_SOURCE_ONLY_NOT_AUTHORIZED",
    "timestep_plan": "P3_TIMESTEP_MATRIX_PLANNED_NOT_AUTHORIZED",
}
BLOCKERS = (
    "TRUSTED_P2_AUTHORITY",
    "REAL_P2_SPATIAL_FIELD",
    "MESH_BOUND_POINT_BIJECTION",
    "COORDINATE_UNIT_PHASE_TIME_VERIFICATION",
    "COMPLETE_POINT_DISPLACEMENT",
    "OPENFOAM_V14_RUNTIME_SYNTAX_VERIFICATION",
    "MESH_MOTION_QUALITY_VERIFICATION",
    "CFL_VERIFICATION",
    "PERIODIC_STABILITY_VERIFICATION",
    "TIMESTEP_INDEPENDENCE_VERIFICATION",
    "INDEPENDENT_GATE_ACCEPTANCE",
)
SENSITIVE_KEY_RE = re.compile(
    r"(author|verif|write|solver|gate|runtime|mesh|mapping|coordinate|unit|"
    r"phase|time|cfl|stability|independence|displacement|generated|available|"
    r"consumed|parsed|checked|accepted|advanced|match|bound|asserted|emitted|"
    r"rejected)",
    re.IGNORECASE,
)

P2_TRUTH = {
    "byte_contract_accepted": True,
    "schema_contract_accepted": True,
    "artifact_bytes_match_descriptor": True,
    "expected_contract_sha256_is_caller_supplied_pin": True,
    "contract_authority_verified": False,
    "receipt_is_persistent_snapshot_authority": False,
    "verified_bytes_reopen_authorized": False,
    "verification_handles_retained_after_return": False,
    "artifact_physical_content_parsed": False,
    "artifact_mapping_verified": False,
    "artifact_units_verified": False,
    "artifact_phase_verified": False,
    "artifact_cross_file_semantics_verified": False,
    "p2_displacement_verified": False,
    "p2_displacement_authorized": False,
    "p3_authorized": False,
    "solver_authorized": False,
    "stage_gate_advanced": False,
    "snapshot_root_identity_bound": True,
}
MOTION_TRUTH = {
    "descriptor_bytes_match_caller_pin": True,
    "descriptor_schema_accepted": True,
    "descriptor_sha256_is_caller_supplied_pin": True,
    "descriptor_pin_authority_verified": False,
    "source_commit_verified": False,
    "geometry_manifest_verified": False,
    "motion_patch_verified_against_mesh": False,
    "foundation_v14_template_emitted": True,
    "dynamic_mesh_mover_fragment_generated": True,
    "point_displacement_motion_patch_fragment_generated": True,
    "legacy_dialect_rejected": True,
    "oscillating_displacement_rejected": True,
    "complete_point_displacement_file_generated": False,
    "point_displacement_header_generated": False,
    "non_motion_patch_entries_generated": False,
    "uniform_amplitude_vector_used_as_p2_mode": False,
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
}
MOTION_REQUIRED = {
    "complete_patch_inventory_exactly_classified": "REQUIRED_NOT_VERIFIED",
    "motion_fields_are_full_mesh_time_indexed_point_vector_fields":
        "REQUIRED_NOT_VERIFIED",
    "motion_field_count_at_least_two": "REQUIRED_NOT_VERIFIED",
    "motion_field_times_strictly_increasing": "REQUIRED_NOT_VERIFIED",
    "motion_field_times_cover_solver_interval": "REQUIRED_NOT_VERIFIED",
    "period_endpoints_close": "REQUIRED_NOT_VERIFIED",
    "control_dict_user_time_mapping_bound": "REQUIRED_NOT_VERIFIED",
    "motion_field_point_order_matches_mesh": "REQUIRED_NOT_VERIFIED",
    "p2_node_to_openfoam_point_bijection_checked": "REQUIRED_NOT_VERIFIED",
    "coordinate_system_and_component_order_checked": "REQUIRED_NOT_VERIFIED",
    "spatial_units_converted_to_openfoam_length": "REQUIRED_NOT_VERIFIED",
    "phase_and_time_origin_checked": "REQUIRED_NOT_VERIFIED",
    "p2_artifact_bytes_verified_and_authorized": "REQUIRED_NOT_VERIFIED",
    "inverse_distance_diffusivity_suitability_checked": "REQUIRED_NOT_VERIFIED",
    "negative_volume_and_mesh_quality_checked": "REQUIRED_NOT_VERIFIED",
}
TIMESTEP_TRUTH = {
    "source_commit_verified": False,
    "source_commit_is_caller_supplied_unverified_claim": True,
    "decimal_values_are_planning_approximations": True,
    "control_dict_written": False,
    "case_written": False,
    "p2_frequency_verified": False,
    "p2_displacement_verified": False,
    "cfl_verified": False,
    "dynamic_mesh_verified": False,
    "periodic_stability_verified": False,
    "time_step_independence_verified": False,
    "solver_verified": False,
    "solver_authorized": False,
}
MOTION_BENIGN_SOURCE_KEYS = {
    "required_before_case_write",
    "dynamic_mesh_dict_mover_fragment",
    "point_displacement_motion_patch_fragment",
    "uniform_interpolated_displacement_semantics",
    "point_displacement_class",
    "point_displacement_dimensions",
    "point_displacement_internal_field",
}
P2_SOURCE_KEYS = frozenset(
    set(P2_TRUTH)
    | {"status", "contract_sha256", "artifacts", "formal_gate_effect"}
)
MOTION_SOURCE_KEYS = frozenset(
    set(MOTION_TRUTH)
    | {
        "status",
        "schema_version",
        "descriptor_sha256",
        "source_commit",
        "geometry_manifest_sha256",
        "motion_patch",
        "openfoam_distribution",
        "openfoam_major",
        "dynamic_mesh_dict_mover_fragment",
        "point_displacement_motion_patch_fragment",
        "point_vector_field_name",
        "uniform_interpolated_displacement_semantics",
        "required_before_case_write",
        "formal_gate_effect",
    }
)
TIMESTEP_SOURCE_KEYS = frozenset(
    set(TIMESTEP_TRUTH)
    | {
        "status",
        "schema_version",
        "source_commit",
        "contract_sha256",
        "frequency_hz",
        "frequency_status",
        "decimal_context_precision_digits",
        "plans",
        "formal_gate_effect",
    }
)
TIMESTEP_PLAN_KEYS = frozenset(
    {
        "steps_per_cycle",
        "period_s",
        "delta_t_s",
        "sample_every_steps",
        "scheduled_step_samples_per_cycle",
        "endpoint_row_count_asserted",
        "ramp_cycles",
        "ramp_end_s",
        "monitored_cycles",
        "monitor_start_s",
        "monitor_end_s",
        "total_cycles",
        "total_steps",
        "adjacent_comparison_windows",
    }
)
TIMESTEP_WINDOW_KEYS = frozenset({"cycle_index", "start_s", "end_s"})
TASK_CLASSIFICATION = {
    "POSITIVE_AUTHORITY_INPUT": "ABSENT_BY_DESIGN",
    "P3_MOTION_HANDOFF": "BLOCKED",
    "CASE_WRITE": "REJECT",
    "SOLVER_RUN": "REJECT",
    "P1_P6_GATE_EFFECT": "NONE",
}


class InterlockError(ValueError):
    """A stable failure code plus completed read/parse/source phases."""

    def __init__(
        self,
        code: str,
        *,
        pinned: tuple[bool, bool, bool] = (False, False, False),
        parsed: tuple[bool, bool, bool] = (False, False, False),
        accepted: tuple[bool, bool, bool] = (False, False, False),
        pin_states: tuple[str, str, str] = ("NOT_EVALUATED",) * 3,
        parse_states: tuple[str, str, str] = ("NOT_EVALUATED",) * 3,
        contract_states: tuple[str, str, str] = ("NOT_EVALUATED",) * 3,
    ):
        self.code = code
        self.pinned = pinned
        self.parsed = parsed
        self.accepted = accepted
        self.pin_states = pin_states
        self.parse_states = parse_states
        self.contract_states = contract_states
        super().__init__(code)


def fail(code: str) -> NoReturn:
    raise InterlockError(code)


def _duplicate_guard(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            fail("DUPLICATE_JSON_KEY")
        result[key] = value
    return result


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
            if depth > MAX_DEPTH:
                fail("JSON_DEPTH_LIMIT_EXCEEDED")
        elif byte in (0x7D, 0x5D):
            depth -= 1
            if depth < 0:
                fail("JSON_UNBALANCED_CONTAINER")
    if quoted or escaped or depth != 0:
        fail("JSON_UNBALANCED_CONTAINER")


def _count(value: Any, depth: int = 0) -> int:
    if depth > MAX_DEPTH:
        fail("JSON_DEPTH_LIMIT_EXCEEDED")
    if isinstance(value, str):
        if len(value) > MAX_STRING:
            fail("JSON_STRING_LIMIT_EXCEEDED")
        return 1
    if isinstance(value, dict):
        total = 1
        for key, child in value.items():
            if (
                not isinstance(key, str)
                or len(key) > MAX_STRING
                or not key.isascii()
            ):
                fail("JSON_KEY_INVALID")
            total += 1 + _count(child, depth + 1)
            if total > MAX_NODES:
                fail("JSON_NODE_LIMIT_EXCEEDED")
        return total
    if isinstance(value, list):
        total = 1
        for child in value:
            total += _count(child, depth + 1)
            if total > MAX_NODES:
                fail("JSON_NODE_LIMIT_EXCEEDED")
        return total
    return 1


def _parse(data: bytes) -> dict[str, Any]:
    if data.startswith(b"\xef\xbb\xbf"):
        fail("JSON_BOM_REJECTED")
    if b"\x00" in data:
        fail("JSON_NUL_REJECTED")
    _preflight_depth(data)
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise InterlockError("JSON_NOT_UTF8") from exc
    try:
        value = json.loads(
            text,
            object_pairs_hook=_duplicate_guard,
            parse_int=lambda token: int(token)
            if len(token) <= 20
            else fail("JSON_INTEGER_LIMIT_EXCEEDED"),
            parse_float=lambda _token: fail("JSON_FLOAT_REJECTED"),
            parse_constant=lambda _token: fail("JSON_NONFINITE_REJECTED"),
        )
    except InterlockError:
        raise
    except (json.JSONDecodeError, RecursionError, ValueError, MemoryError) as exc:
        raise InterlockError("JSON_INVALID") from exc
    _count(value)
    if not isinstance(value, dict):
        fail("JSON_ROOT_NOT_OBJECT")
    return value


def _require_expected(document: dict[str, Any], expected: dict[str, Any]) -> None:
    for key, wanted in expected.items():
        if key not in document or document[key] != wanted or type(document[key]) is not type(wanted):
            fail("SOURCE_TRUTH_CONTRADICTION")


def _reject_unknown_truth(value: Any, known: set[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if (
                (SENSITIVE_KEY_RE.search(key) or isinstance(child, bool))
                and key not in known
            ):
                fail("UNKNOWN_AUTHORIZATION_OR_VERIFICATION_TRUTH")
            if (
                isinstance(child, str)
                and child.strip().upper()
                in {"PASS", "ACCEPTED", "AUTHORIZED", "VERIFIED", "TRUE"}
                and key not in known
            ):
                fail("UNKNOWN_AUTHORIZATION_OR_VERIFICATION_TRUTH")
            _reject_unknown_truth(child, known)
    elif isinstance(value, list):
        for child in value:
            _reject_unknown_truth(child, known)


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


def _fixed(value: Decimal) -> str:
    rendered = format(value, "f")
    if "." in rendered:
        rendered = rendered.rstrip("0").rstrip(".")
    return rendered or "0"


def _expected_timestep_plans(
    frequency: Decimal, ramp: int, monitored: int
) -> list[dict[str, Any]]:
    with localcontext() as context:
        context.prec = 60
        period = Decimal(1) / frequency
        total_cycles = ramp + monitored
        result: list[dict[str, Any]] = []
        for steps in (100, 200, 400):
            previous_index = total_cycles - 2
            final_index = total_cycles - 1
            result.append(
                {
                    "steps_per_cycle": steps,
                    "period_s": _fixed(period),
                    "delta_t_s": _fixed(period / Decimal(steps)),
                    "sample_every_steps": 1,
                    "scheduled_step_samples_per_cycle": steps,
                    "endpoint_row_count_asserted": False,
                    "ramp_cycles": ramp,
                    "ramp_end_s": _fixed(period * ramp),
                    "monitored_cycles": monitored,
                    "monitor_start_s": _fixed(period * ramp),
                    "monitor_end_s": _fixed(period * total_cycles),
                    "total_cycles": total_cycles,
                    "total_steps": total_cycles * steps,
                    "adjacent_comparison_windows": [
                        {
                            "cycle_index": previous_index,
                            "start_s": _fixed(period * previous_index),
                            "end_s": _fixed(period * (previous_index + 1)),
                        },
                        {
                            "cycle_index": final_index,
                            "start_s": _fixed(period * final_index),
                            "end_s": _fixed(period * (final_index + 1)),
                        },
                    ],
                }
            )
    return result


def _type_exact_equal(actual: Any, expected: Any) -> bool:
    if type(actual) is not type(expected):
        return False
    if isinstance(expected, dict):
        return set(actual) == set(expected) and all(
            _type_exact_equal(actual[key], value)
            for key, value in expected.items()
        )
    if isinstance(expected, list):
        return len(actual) == len(expected) and all(
            _type_exact_equal(left, right)
            for left, right in zip(actual, expected)
        )
    return actual == expected


def _validate_p2(document: dict[str, Any]) -> None:
    _reject_unknown_truth(document, set(P2_TRUTH) | {"formal_gate_effect"})
    if set(document) != P2_SOURCE_KEYS:
        fail("P2_RECEIPT_SHAPE_REJECTED")
    if document.get("status") != EXPECTED_STATUSES["p2_artifact_receipt"]:
        fail("P2_SOURCE_STATUS_REJECTED")
    _require_expected(document, P2_TRUTH)
    if document.get("formal_gate_effect") != "NONE":
        fail("SOURCE_TRUTH_CONTRADICTION")
    if not isinstance(document.get("contract_sha256"), str) or HEX64_RE.fullmatch(
        document["contract_sha256"]
    ) is None:
        fail("P2_RECEIPT_SHAPE_REJECTED")
    artifacts = document.get("artifacts")
    if not isinstance(artifacts, list) or len(artifacts) != 3:
        fail("P2_RECEIPT_SHAPE_REJECTED")
    declared_total = 0
    for index, item in enumerate(artifacts):
        if not isinstance(item, dict) or set(item) != {"role", "size_bytes", "sha256"}:
            fail("P2_RECEIPT_SHAPE_REJECTED")
        role, size, digest = item["role"], item["size_bytes"], item["sha256"]
        if (
            role
            != ("nodes", "connectivity", "displacement_vector_field")[index]
            or isinstance(size, bool)
            or not isinstance(size, int)
            or size < 1
            or size > MAX_ARTIFACT_BYTES
            or not isinstance(digest, str)
            or HEX64_RE.fullmatch(digest) is None
        ):
            fail("P2_RECEIPT_SHAPE_REJECTED")
        declared_total += size
        if declared_total > MAX_TOTAL_ARTIFACT_BYTES:
            fail("P2_RECEIPT_SHAPE_REJECTED")


def _validate_motion(document: dict[str, Any]) -> None:
    _reject_unknown_truth(
        document,
        set(MOTION_TRUTH)
        | set(MOTION_REQUIRED)
        | MOTION_BENIGN_SOURCE_KEYS
        | {"formal_gate_effect"},
    )
    if set(document) != MOTION_SOURCE_KEYS:
        fail("MOTION_SOURCE_SHAPE_REJECTED")
    if document.get("status") != EXPECTED_STATUSES["motion_contract"]:
        fail("MOTION_SOURCE_STATUS_REJECTED")
    _require_expected(document, MOTION_TRUTH)
    if document.get("formal_gate_effect") != "NONE":
        fail("SOURCE_TRUTH_CONTRADICTION")
    if document.get("schema_version") != MOTION_SCHEMA:
        fail("MOTION_SOURCE_SHAPE_REJECTED")
    if (
        not isinstance(document.get("descriptor_sha256"), str)
        or HEX64_RE.fullmatch(document["descriptor_sha256"]) is None
        or document.get("openfoam_distribution") != OPENFOAM_DISTRIBUTION
        or type(document.get("openfoam_major")) is not int
        or document["openfoam_major"] != OPENFOAM_MAJOR
        or document.get("point_vector_field_name") != POINT_VECTOR_FIELD_NAME
        or document.get("uniform_interpolated_displacement_semantics")
        != "TIME_INTERPOLATION_OF_FULL_POINT_VECTOR_FIELDS_NOT_UNIFORM_PATCH_AMPLITUDE"
    ):
        fail("MOTION_SOURCE_SHAPE_REJECTED")
    patch = document.get("motion_patch")
    if (
        not isinstance(patch, str)
        or FOAM_WORD_RE.fullmatch(patch) is None
        or patch
        in {
            "dynamicFvMesh",
            "motionSolver",
            "motionSolverLibs",
            "oscillatingDisplacement",
        }
        or document.get("dynamic_mesh_dict_mover_fragment")
        != _dynamic_mesh_fragment(patch)
        or document.get("point_displacement_motion_patch_fragment")
        != _motion_patch_fragment(patch)
    ):
        fail("MOTION_SOURCE_SHAPE_REJECTED")
    required = document.get("required_before_case_write")
    if not isinstance(required, dict) or set(required) != (
        set(MOTION_REQUIRED)
        | {
            "point_displacement_class",
            "point_displacement_dimensions",
            "point_displacement_internal_field",
        }
    ):
        fail("MOTION_SOURCE_SHAPE_REJECTED")
    _require_expected(required, MOTION_REQUIRED)
    for key, expected in (
        ("point_displacement_class", "pointVectorField"),
        ("point_displacement_dimensions", "[length]"),
        ("point_displacement_internal_field", "uniform (0 0 0)"),
    ):
        if required.get(key) != expected:
            fail("MOTION_SOURCE_SHAPE_REJECTED")
    if not isinstance(document.get("source_commit"), str) or HEX40_RE.fullmatch(
        document["source_commit"]
    ) is None:
        fail("MOTION_SOURCE_SHAPE_REJECTED")
    if not isinstance(
        document.get("geometry_manifest_sha256"), str
    ) or HEX64_RE.fullmatch(document["geometry_manifest_sha256"]) is None:
        fail("MOTION_SOURCE_SHAPE_REJECTED")


def _validate_timestep(document: dict[str, Any]) -> None:
    _reject_unknown_truth(
        document,
        set(TIMESTEP_TRUTH) | {"endpoint_row_count_asserted", "formal_gate_effect"},
    )
    if set(document) != TIMESTEP_SOURCE_KEYS:
        fail("TIMESTEP_SOURCE_SHAPE_REJECTED")
    if document.get("status") != EXPECTED_STATUSES["timestep_plan"]:
        fail("TIMESTEP_SOURCE_STATUS_REJECTED")
    _require_expected(document, TIMESTEP_TRUTH)
    if document.get("formal_gate_effect") != "NONE":
        fail("SOURCE_TRUTH_CONTRADICTION")
    if (
        document.get("schema_version") != TIMESTEP_SCHEMA
        or not isinstance(document.get("source_commit"), str)
        or HEX40_RE.fullmatch(document["source_commit"]) is None
        or not isinstance(document.get("contract_sha256"), str)
        or HEX64_RE.fullmatch(document["contract_sha256"]) is None
        or document.get("frequency_status")
        != "PLANNING_INPUT_NOT_P2_AUTHORIZED"
        or type(document.get("decimal_context_precision_digits")) is not int
        or document["decimal_context_precision_digits"] != 60
    ):
        fail("TIMESTEP_SOURCE_SHAPE_REJECTED")
    raw_frequency = document.get("frequency_hz")
    if (
        not isinstance(raw_frequency, str)
        or len(raw_frequency) > 64
        or DECIMAL_RE.fullmatch(raw_frequency) is None
    ):
        fail("TIMESTEP_SOURCE_SHAPE_REJECTED")
    try:
        frequency = Decimal(raw_frequency)
    except InvalidOperation as exc:
        raise InterlockError("TIMESTEP_SOURCE_SHAPE_REJECTED") from exc
    if (
        not frequency.is_finite()
        or not MIN_FREQUENCY_HZ <= frequency <= MAX_FREQUENCY_HZ
        or raw_frequency != _fixed(frequency)
    ):
        fail("TIMESTEP_SOURCE_SHAPE_REJECTED")
    plans = document.get("plans")
    if not isinstance(plans, list) or len(plans) != 3:
        fail("TIMESTEP_SOURCE_SHAPE_REJECTED")
    first = plans[0]
    if (
        not isinstance(first, dict)
        or set(first) != TIMESTEP_PLAN_KEYS
        or type(first.get("ramp_cycles")) is not int
        or not 2 <= first["ramp_cycles"] <= 5
        or type(first.get("monitored_cycles")) is not int
        or not 10 <= first["monitored_cycles"] <= 20
    ):
        fail("TIMESTEP_SOURCE_SHAPE_REJECTED")
    for plan in plans:
        if not isinstance(plan, dict) or set(plan) != TIMESTEP_PLAN_KEYS:
            fail("TIMESTEP_SOURCE_SHAPE_REJECTED")
        windows = plan.get("adjacent_comparison_windows")
        if (
            not isinstance(windows, list)
            or len(windows) != 2
            or any(
                not isinstance(window, dict)
                or set(window) != TIMESTEP_WINDOW_KEYS
                for window in windows
            )
        ):
            fail("TIMESTEP_SOURCE_SHAPE_REJECTED")
    expected_plans = _expected_timestep_plans(
        frequency, first["ramp_cycles"], first["monitored_cycles"]
    )
    if not _type_exact_equal(plans, expected_plans):
        fail("TIMESTEP_SOURCE_SHAPE_REJECTED")


@dataclass
class _Phases:
    pinned: list[bool]
    parsed: list[bool]
    accepted: list[bool]
    pin_states: list[str]
    parse_states: list[str]
    contract_states: list[str]

    def freeze(self) -> tuple[tuple[Any, ...], ...]:
        return (
            tuple(self.pinned),
            tuple(self.parsed),
            tuple(self.accepted),
            tuple(self.pin_states),
            tuple(self.parse_states),
            tuple(self.contract_states),
        )


def _phase_payload(
    pinned: tuple[bool, bool, bool],
    parsed: tuple[bool, bool, bool],
    accepted: tuple[bool, bool, bool],
    pin_states: tuple[str, str, str] = ("NOT_EVALUATED",) * 3,
    parse_states: tuple[str, str, str] = ("NOT_EVALUATED",) * 3,
    contract_states: tuple[str, str, str] = ("NOT_EVALUATED",) * 3,
) -> dict[str, dict[str, Any]]:
    return {
        name: {
            "bytes_pinned": pinned[index],
            "bytes_pin_phase": pin_states[index],
            "json_parsed": parsed[index],
            "json_parse_phase": parse_states[index],
            "contract_recognized": accepted[index],
            "contract_recognition_phase": contract_states[index],
        }
        for index, name in enumerate(SOURCE_NAMES)
    }


def _base_truth() -> dict[str, Any]:
    return {
        "positive_authority_input_present": False,
        "caller_pins_authoritative": False,
        "source_commit_and_hash_claims_trusted": False,
        "cross_output_identity_bound": False,
        "cross_output_p2_geometry_binding_verified": False,
        "p2_receipt_authority_verified": False,
        "p2_artifact_current_snapshot_verified": False,
        "p2_artifact_bytes_reopened_and_reverified": False,
        "p2_artifact_physical_content_parsed": False,
        "p2_artifact_mapping_verified": False,
        "p2_artifact_units_verified": False,
        "p2_component_order_verified": False,
        "p2_artifact_coordinate_frame_verified": False,
        "p2_artifact_phase_time_origin_verified": False,
        "p2_time_sampling_verified": False,
        "p2_frequency_verified": False,
        "p2_displacement_authorized": False,
        "motion_descriptor_authority_verified": False,
        "motion_patch_verified_against_mesh": False,
        "motion_field_point_order_verified": False,
        "p2_node_to_openfoam_point_bijection_verified": False,
        "timestep_frequency_authorized_by_p2": False,
        "p3_motion_handoff_authorized": False,
        "p3_case_write_authorized": False,
        "p3_solver_run_authorized": False,
        "complete_point_displacement_generated": False,
        "control_dict_written": False,
        "control_dict_user_time_verified": False,
        "period_closure_verified": False,
        "case_file_written": False,
        "openfoam_v14_runtime_syntax_verified": False,
        "diffusivity_suitability_verified": False,
        "dynamic_mesh_verified": False,
        "negative_volume_verified": False,
        "mesh_quality_verified": False,
        "cfl_verified": False,
        "periodic_stability_verified": False,
        "time_step_independence_verified": False,
        "solver_run_authorized": False,
        "solver_verified": False,
        "solver_invoked": False,
        "independent_gate_acceptance_present": False,
        "stage_gate_advanced": False,
        "formal_gate_effect": "NONE",
    }


def _source_processing_truth(
    pins_complete: bool,
    schemas_accepted: bool,
    blocker_evaluation_completed: bool,
) -> dict[str, bool]:
    return {
        "all_output_bytes_match_caller_pins": pins_complete,
        "all_output_schemas_accepted": schemas_accepted,
        "all_upstream_non_authorization_constraints_accepted":
            schemas_accepted,
        "blocker_evaluation_completed": blocker_evaluation_completed,
    }


def _blocker_details() -> dict[str, list[str]]:
    return {
        "TRUSTED_P2_AUTHORITY": [
            "CALLER_PINNED_RECEIPT_IS_NOT_P2_AUTHORITY",
            "PERSISTENT_SNAPSHOT_AUTHORITY_NOT_ESTABLISHED",
            "ARTIFACT_REOPEN_AUTHORITY_NOT_ESTABLISHED",
            "P2_ARTIFACT_BYTES_NOT_REOPENED_OR_REVERIFIED",
        ],
        "REAL_P2_SPATIAL_FIELD": [
            "PHYSICAL_ARTIFACT_CONTENT_NOT_PARSED",
            "REAL_SPATIAL_DISPLACEMENT_NOT_AVAILABLE",
        ],
        "MESH_BOUND_POINT_BIJECTION": [
            "POINT_ORDER_AND_BIJECTION_NOT_VERIFIED",
            "MAPPING_NOT_VERIFIED",
            "P2_GEOMETRY_CROSS_OUTPUT_BINDING_ABSENT",
            "CROSS_OUTPUT_P2_SNAPSHOT_BINDING_ABSENT",
        ],
        "COORDINATE_UNIT_PHASE_TIME_VERIFICATION": [
            "UNITS_FRAME_AND_COMPONENT_ORDER_NOT_VERIFIED",
            "PHASE_TIME_ORIGIN_AND_SAMPLING_NOT_VERIFIED",
            "FREQUENCY_NOT_BOUND_TO_AUTHORIZED_P2_OUTPUT",
            "SOURCE_COMMIT_AND_HASH_CLAIMS_ARE_NOT_AUTHORITY",
            "MOTION_PATCH_NOT_VERIFIED_AGAINST_MESH",
        ],
        "COMPLETE_POINT_DISPLACEMENT": [
            "HEADER_INTERNAL_FIELD_AND_COMPLETE_PATCH_INVENTORY_NOT_GENERATED"
        ],
        "OPENFOAM_V14_RUNTIME_SYNTAX_VERIFICATION": [
            "RUNTIME_SYNTAX_NOT_VERIFIED",
            "USERTIME_PERIOD_CLOSURE_AND_DIFFUSIVITY_NOT_VERIFIED",
        ],
        "MESH_MOTION_QUALITY_VERIFICATION": [
            "NEGATIVE_VOLUME_AND_MESH_QUALITY_NOT_VERIFIED"
        ],
        "CFL_VERIFICATION": ["CFL_NOT_VERIFIED"],
        "PERIODIC_STABILITY_VERIFICATION": ["PERIODIC_STABILITY_NOT_VERIFIED"],
        "TIMESTEP_INDEPENDENCE_VERIFICATION": [
            "TIMESTEP_INDEPENDENCE_NOT_VERIFIED"
        ],
        "INDEPENDENT_GATE_ACCEPTANCE": [
            "CASE_AND_SOLVER_REMAIN_REJECTED",
            "INDEPENDENT_GATE_ACCEPTANCE_ABSENT",
        ],
    }


def validate(paths_and_pins: Sequence[str]) -> dict[str, Any]:
    if (
        len(paths_and_pins) != 6
        or any(
            not isinstance(paths_and_pins[index], str)
            or not os.path.isabs(paths_and_pins[index])
            for index in (0, 2, 4)
        )
        or any(
            not isinstance(paths_and_pins[index], str)
            or HEX64_RE.fullmatch(paths_and_pins[index]) is None
            for index in (1, 3, 5)
        )
    ):
        raise InterlockError("ARGUMENT_CONFIG_REJECTED")
    canonical_paths = [
        os.path.normcase(os.path.realpath(os.path.abspath(paths_and_pins[index])))
        for index in (0, 2, 4)
    ]
    if len(set(canonical_paths)) != 3:
        raise InterlockError("DUPLICATE_CANONICAL_SOURCE_PATH")
    phases = _Phases(
        [False] * 3,
        [False] * 3,
        [False] * 3,
        ["NOT_EVALUATED"] * 3,
        ["NOT_EVALUATED"] * 3,
        ["NOT_EVALUATED"] * 3,
    )
    data: list[bytes] = []
    for index in range(3):
        path = paths_and_pins[index * 2]
        pin = paths_and_pins[index * 2 + 1]
        phases.pin_states[index] = "IN_PROGRESS"
        try:
            raw, observed = read_bounded_regular_file(
                path, MAX_CONTRACT_BYTES, "SOURCE_READ_REJECTED"
            )
        except SafeArtifactError as exc:
            phases.pin_states[index] = "REJECTED"
            pinned, parsed, accepted, pin_states, parse_states, contract_states = phases.freeze()
            raise InterlockError(
                exc.code,
                pinned=pinned,
                parsed=parsed,
                accepted=accepted,
                pin_states=pin_states,
                parse_states=parse_states,
                contract_states=contract_states,
            ) from exc
        if not hmac.compare_digest(observed, pin):
            phases.pin_states[index] = "REJECTED"
            pinned, parsed, accepted, pin_states, parse_states, contract_states = phases.freeze()
            raise InterlockError(
                "SOURCE_PIN_MISMATCH",
                pinned=pinned,
                parsed=parsed,
                accepted=accepted,
                pin_states=pin_states,
                parse_states=parse_states,
                contract_states=contract_states,
            )
        phases.pinned[index] = True
        phases.pin_states[index] = "COMPLETE"
        data.append(raw)

    documents: list[dict[str, Any]] = []
    for index, raw in enumerate(data):
        phases.parse_states[index] = "IN_PROGRESS"
        try:
            documents.append(_parse(raw))
        except InterlockError as exc:
            phases.parse_states[index] = "REJECTED"
            pinned, parsed, accepted, pin_states, parse_states, contract_states = phases.freeze()
            raise InterlockError(
                exc.code,
                pinned=pinned,
                parsed=parsed,
                accepted=accepted,
                pin_states=pin_states,
                parse_states=parse_states,
                contract_states=contract_states,
            ) from exc
        phases.parsed[index] = True
        phases.parse_states[index] = "COMPLETE"

    validators = (_validate_p2, _validate_motion, _validate_timestep)
    for index, (validator, document) in enumerate(zip(validators, documents)):
        phases.contract_states[index] = "IN_PROGRESS"
        try:
            validator(document)
        except InterlockError as exc:
            phases.contract_states[index] = "REJECTED"
            pinned, parsed, accepted, pin_states, parse_states, contract_states = phases.freeze()
            raise InterlockError(
                exc.code,
                pinned=pinned,
                parsed=parsed,
                accepted=accepted,
                pin_states=pin_states,
                parse_states=parse_states,
                contract_states=contract_states,
            ) from exc
        phases.accepted[index] = True
        phases.contract_states[index] = "COMPLETE"

    pinned, parsed, accepted, pin_states, parse_states, contract_states = phases.freeze()
    return {
        "status": "P3_MOTION_HANDOFF_BLOCKED_REQUIRED_AUTHORITY",
        "blockers": list(BLOCKERS),
        "blocker_details": _blocker_details(),
        "input_phases": _phase_payload(
            pinned,
            parsed,
            accepted,
            pin_states,
            parse_states,
            contract_states,
        ),
        **TASK_CLASSIFICATION,
        **_source_processing_truth(True, True, True),
        **_base_truth(),
    }


def _failure(exc: InterlockError, exit_code: int) -> int:
    print(
        json.dumps(
            {
                "status": "REJECTED",
                "error": {"code": exc.code, "message": "input rejected"},
                "blockers": list(BLOCKERS),
                "blocker_details": _blocker_details(),
                "input_phases": _phase_payload(
                    exc.pinned,
                    exc.parsed,
                    exc.accepted,
                    exc.pin_states,
                    exc.parse_states,
                    exc.contract_states,
                ),
                **TASK_CLASSIFICATION,
                **_source_processing_truth(
                    all(exc.pinned),
                    all(exc.accepted),
                    False,
                ),
                **_base_truth(),
            },
            sort_keys=True,
        )
    )
    return exit_code


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if (
        len(args) != 6
        or any(not isinstance(args[index], str) or not os.path.isabs(args[index]) for index in (0, 2, 4))
        or any(not isinstance(args[index], str) or HEX64_RE.fullmatch(args[index]) is None for index in (1, 3, 5))
    ):
        return _failure(InterlockError("ARGUMENT_CONFIG_REJECTED"), 3)
    canonical_paths = [
        os.path.normcase(os.path.realpath(os.path.abspath(args[index])))
        for index in (0, 2, 4)
    ]
    if len(set(canonical_paths)) != 3:
        return _failure(InterlockError("DUPLICATE_CANONICAL_SOURCE_PATH"), 3)
    try:
        result = validate(args)
    except InterlockError as exc:
        return _failure(exc, 2)
    print(json.dumps(result, ensure_ascii=True, indent=2, sort_keys=True))
    return BLOCKED_EXIT


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Fail-closed, source-only validation of the Task 006 A-to-B handoff.

The validator reads only the supplied JSON manifest.  It never opens or trusts the
referenced CAD/STEP artifacts and never launches ANSYS or OpenFOAM.  A producer must
provide declared and independently observed hashes; mismatches are rejected here.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable


TASK_ID = "ajm-dual-windows-harness-execute-20260720-008"
POLICY_CONTRACT_TASK_ID = "ajm-dual-windows-harness-recovery-20260720-007"
GEOMETRY_CONTRACT_TASK_ID = "ajm-windows-rear-inlet-runtime-and-consumer-gates-20260718-006"
SCHEMA_VERSION = "1.0"
EXPECTED_PRODUCER_SHA256 = "8f23d7d7dd66efcf06909341a45a76caccd6732cbf11fa1f54157699d55228b0"
FORBIDDEN_PRODUCER_MARKERS = {"vent_rear_containment_clip", "box[1] = footprint_y_min"}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
IDENTITY_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,63}$")
EXPECTED_ARTIFACT_ROLES = {"native", "step", "runtime_report"}


@dataclass(frozen=True)
class Finding:
    code: str
    path: str
    message: str


class DuplicateKeyError(ValueError):
    """Raised when a JSON object repeats a key and would otherwise be ambiguous."""


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _add(findings: list[Finding], code: str, path: str, message: str) -> None:
    findings.append(Finding(code, path, message))


def _object(
    value: Any,
    path: str,
    findings: list[Finding],
    *,
    required: Iterable[str],
    allowed: Iterable[str],
) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        _add(findings, "GATE.SCHEMA.TYPE", path, "expected object")
        return None
    required_set = set(required)
    allowed_set = set(allowed)
    for key in sorted(required_set - value.keys()):
        _add(findings, "GATE.SCHEMA.REQUIRED_FIELD", f"{path}.{key}", "required field is missing")
    for key in sorted(value.keys() - allowed_set):
        _add(findings, "GATE.SCHEMA.UNKNOWN_FIELD", f"{path}.{key}", "unknown field is rejected")
    return value


def _array(value: Any, path: str, findings: list[Finding]) -> list[Any] | None:
    if not isinstance(value, list):
        _add(findings, "GATE.SCHEMA.TYPE", path, "expected array")
        return None
    return value


def _decimal(value: Any) -> Decimal | None:
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        return None
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    return result if result.is_finite() else None


def _exact_number(
    obj: dict[str, Any], key: str, expected: str, code: str, path: str, findings: list[Finding]
) -> None:
    field_path = f"{path}.{key}"
    if key not in obj:
        _add(findings, code, field_path, f"missing; expected exactly {expected}")
        return
    actual = _decimal(obj[key])
    if actual is None or actual != Decimal(expected):
        _add(findings, code, field_path, f"expected exactly {expected}")


def _exact_true(obj: dict[str, Any], key: str, code: str, path: str, findings: list[Finding]) -> None:
    field_path = f"{path}.{key}"
    if obj.get(key) is not True:
        _add(findings, code, field_path, "expected literal true")


def _validate_hash_attestation(
    value: Any, path: str, mismatch_code: str | None, findings: list[Finding], *, artifact: bool = False
) -> dict[str, Any] | None:
    required = {"path", "sha256_declared", "sha256_observed"}
    allowed = set(required)
    if artifact:
        required |= {"role", "size_bytes"}
        allowed |= {"role", "size_bytes"}
    obj = _object(value, path, findings, required=required, allowed=allowed)
    if obj is None:
        return None
    if not isinstance(obj.get("path"), str) or not obj.get("path").strip():
        _add(findings, "GATE.INTEG.PATH", f"{path}.path", "path must be a non-empty string")
    declared = obj.get("sha256_declared")
    observed = obj.get("sha256_observed")
    if not isinstance(declared, str) or SHA256_RE.fullmatch(declared) is None:
        _add(findings, "GATE.INTEG.HASH_FORMAT", f"{path}.sha256_declared", "expected lowercase SHA-256 hex")
    if not isinstance(observed, str) or SHA256_RE.fullmatch(observed) is None:
        _add(findings, "GATE.INTEG.HASH_FORMAT", f"{path}.sha256_observed", "expected lowercase SHA-256 hex")
    if mismatch_code and isinstance(declared, str) and isinstance(observed, str) and declared != observed:
        _add(findings, mismatch_code, path, "declared and observed SHA-256 differ")
    if artifact:
        size = obj.get("size_bytes")
        if isinstance(size, bool) or not isinstance(size, int) or size < 1:
            _add(findings, "GATE.INTEG.ARTIFACT_SIZE", f"{path}.size_bytes", "expected positive integer")
    return obj


def _validate_identities(
    value: Any, path: str, expected_count: int, count_code: str, findings: list[Finding]
) -> list[str]:
    items = _array(value, path, findings)
    if items is None:
        _add(findings, count_code, path, f"expected exactly {expected_count} identities")
        return []
    if len(items) != expected_count:
        _add(findings, count_code, path, f"expected exactly {expected_count} identities")
    ids: list[str] = []
    for index, item in enumerate(items):
        item_path = f"{path}[{index}]"
        obj = _object(item, item_path, findings, required={"id"}, allowed={"id"})
        if obj is None:
            continue
        if "id" not in obj:
            _add(findings, "GATE.STRUCT.ID_MISSING", f"{item_path}.id", "boundary identity is missing")
            continue
        identity = obj["id"]
        if not isinstance(identity, str) or IDENTITY_RE.fullmatch(identity) is None:
            _add(findings, "GATE.STRUCT.ID_FORMAT", f"{item_path}.id", "invalid boundary identity")
            continue
        ids.append(identity)
    if len(ids) != len(set(ids)):
        _add(findings, "GATE.STRUCT.ID_DUPLICATE", path, "boundary identities must be unique")
    return ids


def _validate_bbox(
    obj: dict[str, Any], key: str, expected: tuple[str, str, str], findings: list[Finding]
) -> None:
    path = f"$.geometry.{key}"
    values = _array(obj.get(key), path, findings)
    if values is None or len(values) != 3:
        _add(findings, "GATE.GEOM.BBOX", path, "expected exactly three coordinates")
        return
    actual = tuple(_decimal(value) for value in values)
    wanted = tuple(Decimal(value) for value in expected)
    if actual != wanted:
        _add(findings, "GATE.GEOM.BBOX", path, f"expected {list(expected)} mm")


def validate_manifest(manifest: Any) -> list[Finding]:
    """Return every deterministic rejection finding; an empty list means accepted."""
    findings: list[Finding] = []
    top_fields = {
        "schema_version", "task_id", "policy_contract_task_id", "geometry_contract_task_id",
        "producer", "geometry", "artifacts", "mac_review"
    }
    root = _object(manifest, "$", findings, required=top_fields, allowed=top_fields)
    if root is None:
        return findings

    if root.get("schema_version") != SCHEMA_VERSION:
        _add(findings, "GATE.SCHEMA.VERSION", "$.schema_version", f"expected {SCHEMA_VERSION}")
    if root.get("task_id") != TASK_ID:
        _add(findings, "GATE.SCHEMA.TASK_ID", "$.task_id", f"expected {TASK_ID}")
    if root.get("policy_contract_task_id") != POLICY_CONTRACT_TASK_ID:
        _add(
            findings,
            "GATE.SCHEMA.POLICY_CONTRACT_TASK_ID",
            "$.policy_contract_task_id",
            f"expected {POLICY_CONTRACT_TASK_ID}",
        )
    if root.get("geometry_contract_task_id") != GEOMETRY_CONTRACT_TASK_ID:
        _add(
            findings,
            "GATE.SCHEMA.GEOMETRY_CONTRACT_TASK_ID",
            "$.geometry_contract_task_id",
            f"expected {GEOMETRY_CONTRACT_TASK_ID}",
        )

    producer_fields = {"acceptance_state", "source_commit", "script", "profile", "source_policy"}
    producer = _object(
        root.get("producer"), "$.producer", findings, required=producer_fields, allowed=producer_fields
    )
    if producer is not None:
        if producer.get("acceptance_state") != "PASS":
            _add(findings, "GATE.SEM.ACCEPTANCE", "$.producer.acceptance_state", "expected literal PASS")
        commit = producer.get("source_commit")
        if not isinstance(commit, str) or COMMIT_RE.fullmatch(commit) is None:
            _add(findings, "GATE.INTEG.COMMIT_FORMAT", "$.producer.source_commit", "expected lowercase 40-hex commit")
        _validate_hash_attestation(
            producer.get("script"), "$.producer.script", "GATE.INTEG.HASH_PRODUCER", findings
        )
        script = producer.get("script")
        if not isinstance(script, dict) or any(
            script.get(key) != EXPECTED_PRODUCER_SHA256
            for key in ("sha256_declared", "sha256_observed")
        ):
            _add(
                findings,
                "GATE.INTEG.PRODUCER_PIN",
                "$.producer.script",
                f"producer must match reviewed SHA-256 {EXPECTED_PRODUCER_SHA256}",
            )
        _validate_hash_attestation(
            producer.get("profile"), "$.producer.profile", "GATE.INTEG.HASH_PROFILE", findings
        )
        source_policy_fields = {"forbidden_markers_checked", "forbidden_markers_detected"}
        source_policy = _object(
            producer.get("source_policy"),
            "$.producer.source_policy",
            findings,
            required=source_policy_fields,
            allowed=source_policy_fields,
        )
        if source_policy is None:
            _add(
                findings,
                "GATE.SEM.CLIP_MARKER_POLICY",
                "$.producer.source_policy",
                "clip-marker scan attestation is required",
            )
        else:
            checked = source_policy.get("forbidden_markers_checked")
            checked_valid = (
                isinstance(checked, list)
                and len(checked) == 2
                and all(isinstance(value, str) for value in checked)
                and set(checked) == FORBIDDEN_PRODUCER_MARKERS
            )
            if not checked_valid:
                _add(
                    findings,
                    "GATE.SEM.CLIP_MARKER_POLICY",
                    "$.producer.source_policy.forbidden_markers_checked",
                    "both rejected clip markers must be checked",
                )
            detected = source_policy.get("forbidden_markers_detected")
            if not isinstance(detected, list):
                _add(
                    findings,
                    "GATE.SCHEMA.TYPE",
                    "$.producer.source_policy.forbidden_markers_detected",
                    "expected array",
                )
            elif detected:
                _add(
                    findings,
                    "GATE.SEM.CLIP_MARKER",
                    "$.producer.source_policy.forbidden_markers_detected",
                    "producer contains a rejected rear-vent clipping marker",
                )

    mac_review_fields = {
        "acceptance_state", "review_commit", "producer_source_commit", "runtime_report_sha256"
    }
    mac_review = _object(
        root.get("mac_review"),
        "$.mac_review",
        findings,
        required=mac_review_fields,
        allowed=mac_review_fields,
    )
    if mac_review is None:
        _add(
            findings,
            "GATE.SEM.MAC_ACCEPTANCE",
            "$.mac_review",
            "Mac acceptance receipt is required before consumer use",
        )
    else:
        if mac_review.get("acceptance_state") != "ACCEPTED_PASS":
            _add(
                findings,
                "GATE.SEM.MAC_ACCEPTANCE",
                "$.mac_review.acceptance_state",
                "expected literal ACCEPTED_PASS",
            )
        review_commit = mac_review.get("review_commit")
        if not isinstance(review_commit, str) or COMMIT_RE.fullmatch(review_commit) is None:
            _add(
                findings,
                "GATE.INTEG.MAC_REVIEW_COMMIT",
                "$.mac_review.review_commit",
                "expected lowercase 40-hex review commit",
            )
        accepted_source_commit = mac_review.get("producer_source_commit")
        if not isinstance(accepted_source_commit, str) or COMMIT_RE.fullmatch(accepted_source_commit) is None:
            _add(
                findings,
                "GATE.INTEG.MAC_PRODUCER_COMMIT",
                "$.mac_review.producer_source_commit",
                "expected lowercase 40-hex producer commit",
            )
        elif not isinstance(producer, dict) or accepted_source_commit != producer.get("source_commit"):
            _add(
                findings,
                "GATE.INTEG.MAC_PRODUCER_COMMIT",
                "$.mac_review.producer_source_commit",
                "Mac-accepted producer commit differs from the handoff producer",
            )
        accepted_report_hash = mac_review.get("runtime_report_sha256")
        if not isinstance(accepted_report_hash, str) or SHA256_RE.fullmatch(accepted_report_hash) is None:
            _add(
                findings,
                "GATE.INTEG.MAC_RUNTIME_REPORT_HASH",
                "$.mac_review.runtime_report_sha256",
                "expected lowercase SHA-256 hex",
            )

    geometry_fields = {
        "inlets", "outlets", "cell_footprint_y_min_mm", "supported_plenum_y_min_mm",
        "rear_support_extension_mm", "rear_inlet_ids", "body_count", "piece_count",
        "closed", "manifold", "bbox_min_mm", "bbox_max_mm", "analytic_volume_mm3",
        "native_reopen_pass", "step_reopen_pass", "connectivity_pass",
    }
    geometry = _object(
        root.get("geometry"), "$.geometry", findings, required=geometry_fields, allowed=geometry_fields
    )
    if geometry is not None:
        inlet_ids = _validate_identities(
            geometry.get("inlets"), "$.geometry.inlets", 4, "GATE.STRUCT.INLET_COUNT", findings
        )
        outlet_ids = _validate_identities(
            geometry.get("outlets"), "$.geometry.outlets", 1, "GATE.STRUCT.OUTLET_COUNT", findings
        )
        if set(inlet_ids) & set(outlet_ids):
            _add(findings, "GATE.STRUCT.ID_DUPLICATE", "$.geometry", "inlet and outlet IDs must not overlap")
        _exact_number(geometry, "cell_footprint_y_min_mm", "-14.5", "GATE.GEOM.FOOTPRINT_Y", "$.geometry", findings)
        _exact_number(geometry, "supported_plenum_y_min_mm", "-17.75", "GATE.GEOM.PLENUM_Y", "$.geometry", findings)
        _exact_number(geometry, "rear_support_extension_mm", "3.25", "GATE.GEOM.EXTENSION", "$.geometry", findings)

        rear_ids = geometry.get("rear_inlet_ids")
        rear_ids_valid = (
            isinstance(rear_ids, list)
            and len(rear_ids) == 2
            and all(isinstance(value, str) for value in rear_ids)
            and set(rear_ids) == {"V01", "V02"}
        )
        if not rear_ids_valid:
            _add(findings, "GATE.STRUCT.REAR_ID", "$.geometry.rear_inlet_ids", "expected exactly V01 and V02")
        elif not set(rear_ids).issubset(set(inlet_ids)):
            _add(findings, "GATE.STRUCT.REAR_ID", "$.geometry.rear_inlet_ids", "rear IDs must reference inlet IDs")

        _exact_number(geometry, "body_count", "1", "GATE.STRUCT.BODY_COUNT", "$.geometry", findings)
        _exact_number(geometry, "piece_count", "1", "GATE.STRUCT.PIECE_COUNT", "$.geometry", findings)
        _exact_true(geometry, "closed", "GATE.GEOM.CLOSED", "$.geometry", findings)
        _exact_true(geometry, "manifold", "GATE.GEOM.MANIFOLD", "$.geometry", findings)
        _validate_bbox(geometry, "bbox_min_mm", ("-10.875", "-17.75", "1.2675"), findings)
        _validate_bbox(geometry, "bbox_max_mm", ("10.875", "20.75", "2.8"), findings)
        _exact_number(geometry, "analytic_volume_mm3", "469.4396438426395", "GATE.GEOM.VOLUME", "$.geometry", findings)
        _exact_true(geometry, "native_reopen_pass", "GATE.INTEG.REOPEN_NATIVE", "$.geometry", findings)
        _exact_true(geometry, "step_reopen_pass", "GATE.INTEG.REOPEN_STEP", "$.geometry", findings)
        _exact_true(geometry, "connectivity_pass", "GATE.GEOM.CONNECTIVITY", "$.geometry", findings)

    artifacts = _array(root.get("artifacts"), "$.artifacts", findings)
    roles: list[str] = []
    if artifacts is not None:
        for index, item in enumerate(artifacts):
            path = f"$.artifacts[{index}]"
            artifact = _validate_hash_attestation(item, path, None, findings, artifact=True)
            if artifact is None:
                continue
            role = artifact.get("role")
            if not isinstance(role, str) or role not in EXPECTED_ARTIFACT_ROLES:
                _add(findings, "GATE.INTEG.ARTIFACT_ROLE", f"{path}.role", "unexpected artifact role")
                continue
            roles.append(role)
            declared = artifact.get("sha256_declared")
            observed = artifact.get("sha256_observed")
            if isinstance(declared, str) and isinstance(observed, str) and declared != observed:
                _add(findings, f"GATE.INTEG.HASH_{role.upper()}", path, "declared and observed SHA-256 differ")
        if len(roles) != len(set(roles)):
            _add(findings, "GATE.INTEG.ARTIFACT_ROLE_DUPLICATE", "$.artifacts", "artifact roles must be unique")
        if set(roles) != EXPECTED_ARTIFACT_ROLES:
            _add(findings, "GATE.INTEG.ARTIFACT_ROLE_SET", "$.artifacts", "native, step, and runtime_report are required")
        runtime_reports = [
            item for item in artifacts
            if isinstance(item, dict) and item.get("role") == "runtime_report"
        ]
        if isinstance(mac_review, dict) and len(runtime_reports) == 1:
            if mac_review.get("runtime_report_sha256") != runtime_reports[0].get("sha256_observed"):
                _add(
                    findings,
                    "GATE.INTEG.MAC_RUNTIME_REPORT_HASH",
                    "$.mac_review.runtime_report_sha256",
                    "Mac-accepted runtime report differs from the handoff artifact",
                )
    else:
        _add(findings, "GATE.INTEG.ARTIFACT_ROLE_SET", "$.artifacts", "native, step, and runtime_report are required")

    return findings


def _load_manifest(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(
            handle,
            parse_float=Decimal,
            object_pairs_hook=_reject_duplicate_keys,
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="JSON handoff manifest to validate")
    args = parser.parse_args(argv)
    try:
        manifest = _load_manifest(args.manifest)
    except DuplicateKeyError as exc:
        print(json.dumps({"accepted": False, "findings": [{"code": "GATE.INPUT.JSON_DUPLICATE_KEY", "path": str(args.manifest), "message": str(exc)}]}))
        return 3
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(json.dumps({"accepted": False, "findings": [{"code": "GATE.INPUT.JSON", "path": str(args.manifest), "message": str(exc)}]}))
        return 3
    findings = validate_manifest(manifest)
    print(json.dumps({"accepted": not findings, "findings": [asdict(item) for item in findings]}, indent=2))
    return 0 if not findings else 2


if __name__ == "__main__":
    sys.exit(main())

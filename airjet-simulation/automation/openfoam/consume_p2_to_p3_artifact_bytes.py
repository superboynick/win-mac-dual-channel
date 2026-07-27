#!/usr/bin/env python3
"""Verify pinned P2 contract and artifact bytes without interpreting physics."""

from __future__ import annotations

import hmac
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

from safe_artifact_io import (
    MAX_CONTRACT_BYTES,
    SafeArtifactError,
    read_bounded_regular_file,
    verify_artifacts,
)


HERE = Path(__file__).resolve().parent
REFERENCE_SRC = HERE / "coupling_contract_reference_v2" / "src"
sys.path.insert(0, str(REFERENCE_SRC))

from airjet_coupling.validator import (  # noqa: E402
    ContractValidationError,
    P2_TYPE,
    load_json_bytes,
    validate_document,
)


PIN_RE = re.compile(r"^[0-9a-f]{64}$")
ROLE_ORDER = ("nodes", "connectivity", "displacement_vector_field")


class ConsumptionError(SafeArtifactError):
    """A safe rejection carrying only completed verification phases."""

    def __init__(self, code: str, *, contract: bool = False, schema: bool = False):
        super().__init__(code)
        self.contract = contract
        self.schema = schema


def _truth(
    status: str,
    *,
    pin_supplied: bool,
    contract: bool,
    schema: bool,
    artifacts: bool,
) -> dict[str, Any]:
    return {
        "status": status,
        "byte_contract_accepted": contract,
        "schema_contract_accepted": schema,
        "artifact_bytes_match_descriptor": artifacts,
        "expected_contract_sha256_is_caller_supplied_pin": pin_supplied,
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
        "formal_gate_effect": "NONE",
    }


def _failure(
    code: str,
    exit_code: int,
    *,
    pin_supplied: bool = True,
    contract: bool = False,
    schema: bool = False,
) -> int:
    print(
        json.dumps(
            {
                "error": {"code": code, "message": "input rejected"},
                "artifacts": [],
                **_truth(
                    "REJECTED",
                    pin_supplied=pin_supplied,
                    contract=contract,
                    schema=schema,
                    artifacts=False,
                ),
            },
            sort_keys=True,
        )
    )
    return exit_code


def consume(contract_path: str, snapshot_root: str, caller_pin: str) -> dict[str, Any]:
    """Return a complete verified-byte receipt or raise a safe rejection."""
    if (
        PIN_RE.fullmatch(caller_pin) is None
        or not os.path.isabs(contract_path)
        or not os.path.isabs(snapshot_root)
    ):
        raise ConsumptionError("PIN_CONFIG_REJECTED")
    try:
        contract_bytes, observed_contract_hash = read_bounded_regular_file(
            contract_path, MAX_CONTRACT_BYTES, "CONTRACT_READ_REJECTED"
        )
    except SafeArtifactError as exc:
        raise ConsumptionError(exc.code) from exc
    if not hmac.compare_digest(observed_contract_hash, caller_pin):
        raise ConsumptionError("CONTRACT_PIN_MISMATCH")
    try:
        document = load_json_bytes(contract_bytes)
        validate_document(document)
    except ContractValidationError as exc:
        raise ConsumptionError(
            "CONTRACT_VALIDATION_REJECTED", contract=True
        ) from exc
    if not isinstance(document, dict) or document.get("contract_type") != P2_TYPE:
        raise ConsumptionError("CONTRACT_TYPE_REJECTED", contract=True)
    artifacts = document.get("artifacts")
    if not isinstance(artifacts, list):
        raise ConsumptionError("CONTRACT_VALIDATION_REJECTED", contract=True)
    by_role = {
        item.get("role"): item
        for item in artifacts
        if isinstance(item, dict) and isinstance(item.get("role"), str)
    }
    if (
        len(artifacts) != len(ROLE_ORDER)
        or len(by_role) != len(ROLE_ORDER)
        or set(by_role) != set(ROLE_ORDER)
    ):
        raise ConsumptionError("CONTRACT_VALIDATION_REJECTED", contract=True)
    try:
        verified = verify_artifacts(
            snapshot_root, (by_role[role] for role in ROLE_ORDER)
        )
    except SafeArtifactError as exc:
        raise ConsumptionError(exc.code, contract=True, schema=True) from exc
    receipt = [
        {"role": item.role, "size_bytes": item.size_bytes, "sha256": item.sha256}
        for item in verified
    ]
    return {
        "contract_sha256": observed_contract_hash,
        "snapshot_root_identity_bound": True,
        "artifacts": receipt,
        **_truth(
            "P2_ARTIFACT_BYTES_MATCH_CALLER_PIN_NOT_AUTHORIZED",
            pin_supplied=True,
            contract=True,
            schema=True,
            artifacts=True,
        ),
    }


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 3:
        return _failure("ARGUMENT_CONFIG_REJECTED", 3, pin_supplied=False)
    contract_path, snapshot_root, caller_pin = args
    pin_supplied = PIN_RE.fullmatch(caller_pin) is not None
    if (
        not pin_supplied
        or not os.path.isabs(contract_path)
        or not os.path.isabs(snapshot_root)
    ):
        return _failure(
            "ARGUMENT_CONFIG_REJECTED", 3, pin_supplied=pin_supplied
        )
    try:
        result = consume(contract_path, snapshot_root, caller_pin)
    except ConsumptionError as exc:
        return _failure(
            exc.code, 2, contract=exc.contract, schema=exc.schema
        )
    except SafeArtifactError as exc:
        return _failure(exc.code, 2)
    except (OSError, ValueError, TypeError, MemoryError, OverflowError):
        return _failure("INPUT_REJECTED", 2)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())

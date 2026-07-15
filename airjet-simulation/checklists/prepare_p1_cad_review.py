#!/usr/bin/env python3
"""Validate a completed 006 artifact set and prepare a P1 review worksheet.

This script never directly promotes P1.  It verifies report identity, exact
Git-commit contracts, external-file hashes, and the frozen NOT_RUN gate schema,
then writes a review worksheet outside the repository.  Its optional finalize
mode validates the independent worksheet and visible native-file spot checks,
but only emits a PASS recommendation pending a separate reviewed Git commit.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import os
import re
import subprocess
import types
from datetime import date, datetime
from pathlib import Path, PureWindowsPath


COMPLETE_STATUSES = {"COMPLETE_AWAITING_REVIEW"}
PRODUCT_TARGET = "AIRJET_MINI_GEN1"
PRODUCTION_CONTRACT_ID = "AJM006_GEN1_FULL_PRODUCT_SEMANTIC_PRODUCTION_V1"
PRODUCTION_PRODUCER_PROFILE_ID = "ajm006-spaceclaim-full-product-producer-v1"
PRODUCTION_OBSERVER_PROFILE_ID = "ajm006-workbench-full-product-observer-v1"
PRODUCTION_REGISTERED_STATE = "REGISTERED_SIGNED_PROFILES"
PROFILES_PATH = "airjet-simulation/automation/ansys/profiles.json"
CAMPAIGN_PATH = (
    "airjet-simulation/automation/ansys/contracts/"
    "trusted_full_product_gen1/campaign.json"
)
EXPECTED_VARIANTS = {
    "M-3x4-7.0__R25_BOTTOM_HEAVY",
    "M-3x4-7.0__R50_BALANCED",
    "M-3x4-7.0__R75_TOP_HEAVY",
    "M+S-3x5-6.0__R50_BALANCED",
    "L-2x4-8.0__R50_BALANCED",
    "S-3x5-5.5__R50_BALANCED",
    "M-3x4-7.0__R50_VENT_UPPER",
    "M-3x4-7.0__R50_ORIFICE_EDGE_GAP",
    "M-3x4-7.0__R50_EXHAUST_HALF_TAPER",
}
DERIVED_VARIANTS = {
    "M-3x4-7.0__R50_VENT_UPPER",
    "M-3x4-7.0__R50_ORIFICE_EDGE_GAP",
    "M-3x4-7.0__R50_EXHAUST_HALF_TAPER",
}
GLOBAL_ROLES = {
    "BUILD_SCRIPT",
    "MASTER_NATIVE_CAD",
    "REPORT_005_COPY",
    "INPUT_CONTRACT_HASHES",
    "GATE_EVIDENCE_006_CSV",
    "GLOBAL_BUILD_LOG",
}
PER_VARIANT_ROLES = {
    "VARIANT_PARAMETER_RECORD",
    "NATIVE_CAD",
    "NATIVE_REOPEN_LOG",
    "FLUID_GEOMETRY",
    "STEP_GEOMETRY",
    "STEP_REIMPORT_LOG",
    "SEMANTIC_SIDECAR",
    "SEMANTIC_BINDING",
    "SEMANTIC_OBSERVATION",
    "SEMANTIC_KEY_CARDINALITY_REPORT",
    "WORKBENCH_PROJECT",
    "PRODUCER_JOB_RECORD",
    "PRODUCER_ARTIFACT_MANIFEST",
    "OBSERVER_JOB_RECORD",
    "OBSERVER_ARTIFACT_MANIFEST",
    "WORKBENCH_STEP_SEMANTIC_LOG",
    "AUTOMATED_CHECKS_CSV",
    "SCREENSHOT_XY",
    "SCREENSHOT_XZ",
    "SCREENSHOT_YZ",
    "FLUID_CONNECTIVITY_VIEW",
    "VARIANT_BUILD_LOG",
}
PASS_ALL_9_FIELDS = {
    "ENVELOPE_CHECK",
    "THICKNESS_CLOSURE_CHECK",
    "FLUID_CONNECTIVITY_CHECK",
    "ISOLATED_FLUID_CHECK",
    "INTERFERENCE_CHECK",
    "SLIVER_CHECK",
    "ORIFICE_INTEGRITY_CHECK",
    "CLEARANCE_CHECK",
    "NAMED_SELECTION_CARDINALITY_CHECK",
    "NATIVE_SAVE_REOPEN",
    "WORKBENCH_STEP_IMPORT",
    "SOLVER_SEMANTIC_RECONSTRUCTION",
    "SEMANTIC_ADJACENCY_CHECK",
    "C017_C019_PHYSICS_GUARD",
    "ANCHOR_PARTITION_NONPHYSICAL_GUARD",
}
MANIFEST_HEADER = [
    "case_id",
    "file_role",
    "absolute_path",
    "size_bytes",
    "sha256",
    "created_at_utc",
    "software_version",
    "git_commit",
    "notes",
]
REVIEW_HEADER = [
    "gate_item_id",
    "configuration_id",
    "variant_id",
    "variant_kind",
    "comparison_parent_variant_id",
    "changed_factor",
    "hard_gate",
    "requirement",
    "tolerance_or_acceptance",
    "006_measured_value",
    "006_suggested_status",
    "review_status",
    "evidence_path",
    "evidence_sha256",
    "secondary_evidence_path",
    "secondary_evidence_sha256",
    "reviewer",
    "review_date",
    "review_notes",
]
GATE_EVIDENCE_HEADER = [
    "gate_item_id",
    "variant_id",
    "measured_value",
    "evidence_original_path",
    "evidence_sha256",
    "secondary_evidence_original_path",
    "secondary_evidence_sha256",
    "006_suggested_status",
    "notes",
]
SPOT_CHECK_HEADER = [
    "check_id",
    "artifact_case_id",
    "artifact_file_role",
    "artifact_original_path",
    "artifact_sha256",
    "reviewer",
    "review_date",
    "result",
    "notes",
]
SPOT_CHECK_CASES = [
    ("MASTER", "GLOBAL", "MASTER_NATIVE_CAD"),
    ("PRIMARY_BALANCED", "M-3x4-7.0__R50_BALANCED", "NATIVE_CAD"),
    ("LOW_CELL_SENTINEL", "L-2x4-8.0__R50_BALANCED", "NATIVE_CAD"),
    ("DERIVED_VENT", "M-3x4-7.0__R50_VENT_UPPER", "NATIVE_CAD"),
    ("DERIVED_ORIFICE", "M-3x4-7.0__R50_ORIFICE_EDGE_GAP", "NATIVE_CAD"),
    ("DERIVED_EXHAUST", "M-3x4-7.0__R50_EXHAUST_HALF_TAPER", "NATIVE_CAD"),
]
EXCLUDED_NONPHYSICAL_FEATURE_IDS = ";".join(
    [
        "ENVELOPE_REF",
        "SIDE_FRAME_PROXY_U",
        "FLEX_KEEP_OUT_U",
        "CELL_PARTITION_CAND_TEMPLATE",
        "CENTRAL_ANCHOR_CAND_TEMPLATE",
        "C017_SUPPORT_ALLOWANCE_REF",
        "C019_TOP_REF",
        "C019_BOTTOM_REF",
        "FLUID_DOMAIN_CLOSURE_DATUM_C",
        "SPOUT_SOLID_CAND_U",
        "TIM_EQUIVALENT_C",
        "CHIP_HEAT_SOURCE_C",
    ]
)
VARIANT_CHECK_HEADER = [
    "variant_id",
    "configuration_id",
    "cell_count",
    "connected_cell_count",
    "isolated_fluid_count",
    "interference_count",
    "sliver_count",
    "duplicate_face_count",
    "excluded_datum_feature_ids",
    "actual_orifice_count",
    "blind_or_lost_orifice_count",
    "actual_open_area_pct",
    "minimum_clearance_mm",
    "envelope_x_mm",
    "envelope_y_mm",
    "envelope_z_mm",
    "thickness_closure_error_mm",
    "named_selection_check",
    "native_reopen",
    "step_transfer",
    "workbench_step_import",
    "solver_semantic_reconstruction",
    "semantic_adjacency_check",
    "c017_c019_physics_guard",
    "anchor_partition_nonphysical_guard",
]
CONTRACT_PATHS = [
    "airjet-simulation/windows-prompts/AJM_WIN_P1_FULL_PRODUCT_CAD_BUILD_006.md",
    "airjet-simulation/checklists/prepare_p1_cad_review.py",
    "airjet-simulation/checklists/test_prepare_p1_cad_review_static.py",
    "airjet-simulation/checklists/p1_cad_gate_matrix.csv",
    "airjet-simulation/parameters/p1_model_form_variants.csv",
    "airjet-simulation/parameters/p1_cad_parameter_map.csv",
    "airjet-simulation/parameters/p1_internal_geometry_rules.csv",
    "airjet-simulation/parameters/p1_orifice_pattern_candidates.csv",
    "airjet-simulation/parameters/p1_vent_geometry_candidates.csv",
    "airjet-simulation/parameters/p1_planform_exhaust_candidates.csv",
    "airjet-simulation/parameters/p1_layout_configuration_matrix.csv",
    "airjet-simulation/parameters/p1_thickness_budget.csv",
    "airjet-simulation/geometry/contracts/p1_cad_features.csv",
    "airjet-simulation/geometry/contracts/p1_cad_feature_parameter_bindings.csv",
    "airjet-simulation/geometry/contracts/p1_cad_interfaces.csv",
    "airjet-simulation/geometry/contracts/p1_cad_named_selections.csv",
    "airjet-simulation/geometry/contracts/p1_cad_open_questions.csv",
    "airjet-simulation/parameters/build_p1_cad_inputs.py",
    "airjet-simulation/parameters/build_p1_cad_contracts.py",
    PROFILES_PATH,
    "airjet-simulation/automation/ansys/contracts/full_product_semantic_contract_v1.py",
    "airjet-simulation/automation/ansys/contracts/full_product_semantic_sidecar_v1.schema.json",
    "airjet-simulation/automation/ansys/contracts/test_full_product_semantic_contract_v1.py",
    "airjet-simulation/automation/ansys/contracts/build_full_product_trusted_variants.py",
    "airjet-simulation/automation/ansys/contracts/test_full_product_trusted_variants.py",
    CAMPAIGN_PATH,
    "airjet-simulation/automation/ansys/contracts/trusted_full_product_gen1/variant_01_m_3x4_7_0_r25_bottom_heavy.json",
    "airjet-simulation/automation/ansys/contracts/trusted_full_product_gen1/variant_02_m_3x4_7_0_r50_balanced.json",
    "airjet-simulation/automation/ansys/contracts/trusted_full_product_gen1/variant_03_m_3x4_7_0_r75_top_heavy.json",
    "airjet-simulation/automation/ansys/contracts/trusted_full_product_gen1/variant_04_m_s_3x5_6_0_r50_balanced.json",
    "airjet-simulation/automation/ansys/contracts/trusted_full_product_gen1/variant_05_l_2x4_8_0_r50_balanced.json",
    "airjet-simulation/automation/ansys/contracts/trusted_full_product_gen1/variant_06_s_3x5_5_5_r50_balanced.json",
    "airjet-simulation/automation/ansys/contracts/trusted_full_product_gen1/variant_07_m_3x4_7_0_r50_vent_upper.json",
    "airjet-simulation/automation/ansys/contracts/trusted_full_product_gen1/variant_08_m_3x4_7_0_r50_orifice_edge_gap.json",
    "airjet-simulation/automation/ansys/contracts/trusted_full_product_gen1/variant_09_m_3x4_7_0_r50_exhaust_half_taper.json",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_unique_report(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for number, raw_line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            raise ValueError(f"blank report key at line {number}")
        if key in values:
            raise ValueError(f"duplicate report key {key!r} at line {number}")
        values[key] = value
    return values


def require_report(values: dict[str, str]) -> None:
    expected = {
        "TASK": "AJM-WIN-P1-FULL-PRODUCT-CAD-BUILD-006",
        "COMPUTER": "LAPTOP-LCCLM2HI",
        "P1_STAGE_GATE": "PENDING_PEER_REVIEW",
        "P0_STAGE_GATE": "PASS",
        "P2_STAGE_GATE": "NOT_RUN",
        "P3_STAGE_GATE": "NOT_RUN",
        "P4_STAGE_GATE": "NOT_RUN",
        "P5_STAGE_GATE": "NOT_RUN",
        "P6_STAGE_GATE": "NOT_RUN",
        "GIT_FETCH": "PASS",
        "GIT_ORIGIN": "https://github.com/superboynick/win-mac-dual-channel.git",
        "GIT_BRANCH": "main",
        "GIT_UPSTREAM": "origin/main",
        "GIT_AHEAD_BEHIND": "0/0",
        "PROJECT_AUDIT": "PASS",
        "P1_INPUT_GENERATOR_CHECK": "PASS",
        "P1_CONTRACT_GENERATOR_CHECK": "PASS",
        "FINAL_GIT_CLEAN": "PASS",
        "OLD_PLE_BASELINE": "CLEAN",
        "LICENSE_SAFETY_CHECK": "PASS",
        "CONFIGURATIONS_REQUESTED": "4",
        "CONFIGURATIONS_BUILT": "4",
        "BASE_OR_RESIDUAL_VARIANTS_REQUESTED": "6",
        "BASE_OR_RESIDUAL_VARIANTS_BUILT": "6",
        "DERIVED_SINGLE_FACTOR_VARIANTS_REQUESTED": "3",
        "DERIVED_SINGLE_FACTOR_VARIANTS_BUILT": "3",
        "TOTAL_VARIANTS_REQUESTED": "9",
        "TOTAL_VARIANTS_BUILT": "9",
        "PARAMETER_DIFF_CHECK": "PASS_ALL_3_DERIVED",
        "GEOMETRY_RESULT_DIFF_CHECK": "PASS_ALL_3_DERIVED",
        "P1_CAD_TOOLCHAIN_SCOPE": "ALTERNATE_ROUTE_ONLY",
        "CAD_AUTHORING_ROUTE": "SPACECLAIM_SIGNED_SCRIPT_PARAMETRIC",
        "SOLVER_HANDOFF_ROUTE": "HASH_BOUND_STEP_SEMANTIC_SIDECAR",
        "PRODUCT_TARGET": PRODUCT_TARGET,
        "PRODUCTION_CONTRACT_ID": PRODUCTION_CONTRACT_ID,
        "PRODUCTION_SCOPE": "FULL_PRODUCT",
        "PRODUCTION_CONTRACT_EXECUTION_STATE": PRODUCTION_REGISTERED_STATE,
        "PRODUCER_PROFILE_ID": PRODUCTION_PRODUCER_PROFILE_ID,
        "OBSERVER_PROFILE_ID": PRODUCTION_OBSERVER_PROFILE_ID,
        "SEMANTIC_BUNDLE_VALIDATION": "PASS_ALL_9",
        "EXTERNAL_NATIVE_ATTACH": "NOT_PROVEN",
        "NATIVE_PARAMETERIZATION": "NOT_PROVEN",
        "NATIVE_NAMED_SELECTION_TRANSFER": "NOT_PROVEN",
    }
    for key, expected_value in expected.items():
        if values.get(key) != expected_value:
            raise ValueError(f"006 report field {key} must equal {expected_value!r}")
    if values.get("CAD_BUILD_STATUS") not in COMPLETE_STATUSES:
        raise ValueError("006 report is not in a complete-awaiting-review state")
    if values.get("GIT_CLEAN", "").upper() not in {"TRUE", "PASS"}:
        raise ValueError("006 report GIT_CLEAN must be TRUE or PASS")
    for key in PASS_ALL_9_FIELDS:
        if values.get(key) != "PASS_ALL_9":
            raise ValueError(f"006 report field {key} must equal 'PASS_ALL_9'")
    if values.get("STEP_EXPORT_REIMPORT") != "PASS_ALL_9":
        raise ValueError("complete 006 run requires STEP_EXPORT_REIMPORT=PASS_ALL_9")
    if values.get("ERROR_MESSAGES", ""):
        raise ValueError("complete 006 run must have an empty ERROR_MESSAGES field")
    if any("LIMITATION" in key.upper() for key in values):
        raise ValueError("006 report contains a prohibited transfer-limitation field")
    commit = values.get("GIT_COMMIT", "")
    if len(commit) != 40 or any(character not in "0123456789abcdefABCDEF" for character in commit):
        raise ValueError("006 GIT_COMMIT must be a full 40-character SHA")
    if not values.get("EXTERNAL_RUN_DIRECTORY"):
        raise ValueError("006 EXTERNAL_RUN_DIRECTORY is required")
    if not values.get("EXTERNAL_FILE_MANIFEST"):
        raise ValueError("006 EXTERNAL_FILE_MANIFEST is required")
    manifest_hash = values.get("EXTERNAL_FILE_MANIFEST_SHA256", "")
    if not re.fullmatch(r"[0-9a-fA-F]{64}", manifest_hash):
        raise ValueError("006 EXTERNAL_FILE_MANIFEST_SHA256 must be a 64-character SHA256")
    for key in (
        "P1_CONTRACT_BUNDLE_SHA256",
        "GATE_TEMPLATE_SHA256",
        "VARIANT_TABLE_SHA256",
        "INTERNAL_RULES_SHA256",
        "MASTER_MODEL_SHA256",
        "FULL_PRODUCT_VALIDATOR_SHA256",
        "FULL_PRODUCT_SCHEMA_SHA256",
        "FULL_PRODUCT_CORE_TEST_SHA256",
        "TRUSTED_VARIANT_GENERATOR_SHA256",
        "TRUSTED_VARIANT_TEST_SHA256",
        "TRUSTED_CAMPAIGN_SHA256",
    ):
        if not re.fullmatch(r"[0-9a-fA-F]{64}", values.get(key, "")):
            raise ValueError(f"006 {key} must be a 64-character SHA256")
    try:
        if int(values.get("MANIFEST_DATA_ROW_COUNT", "")) <= 0:
            raise ValueError
    except ValueError as exc:
        raise ValueError("006 MANIFEST_DATA_ROW_COUNT must be a positive integer") from exc
    if not values.get("RUN_ID") or not values.get("MASTER_MODEL_PATH"):
        raise ValueError("006 RUN_ID and MASTER_MODEL_PATH are required")
    report_005_commit = values.get("REPORT_005_GIT_COMMIT", "")
    if not re.fullmatch(r"[0-9a-fA-F]{40}", report_005_commit):
        raise ValueError("006 REPORT_005_GIT_COMMIT must be a full commit SHA")
    if not re.fullmatch(r"[0-9a-fA-F]{64}", values.get("REPORT_005_SHA256", "")):
        raise ValueError("006 REPORT_005_SHA256 must be a 64-character SHA256")
    if not values.get("REPORT_005_PATH"):
        raise ValueError("006 REPORT_005_PATH is required")
    if values.get("P1_CAD_TOOLCHAIN_READINESS") != "PASS":
        raise ValueError("006 requires route-scoped P1_CAD_TOOLCHAIN_READINESS=PASS")
    expected_ansys_prefix = "2026 R1"
    if not values.get("ANSYS_VERSION", "").startswith(expected_ansys_prefix):
        raise ValueError("006 ANSYS_VERSION must identify 2026 R1")
    if values.get("INSTALL_ROOT") != r"D:\ansys\ANSYS Inc\ANSYS Student\v261":
        raise ValueError("006 INSTALL_ROOT changed from the validated 005 installation")
    for key, minimum in (("C_FREE_GIB", 10.0), ("D_FREE_GIB", 20.0), ("AVAILABLE_RAM_GIB", 8.0)):
        try:
            actual = float(values.get(key, ""))
        except ValueError as exc:
            raise ValueError(f"006 report field {key} is not numeric") from exc
        if not math.isfinite(actual) or actual < minimum:
            raise ValueError(f"006 report field {key} is below {minimum:g} GiB")


def is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def git_commit_is_ancestor(repo: Path, commit: str, descendant: str = "HEAD") -> bool:
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", commit, descendant],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0


def git_blob(repo: Path, commit: str, relative_path: str) -> bytes:
    result = subprocess.run(
        ["git", "show", f"{commit}:{relative_path}"],
        cwd=repo,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise ValueError(f"cannot read contract at exact 006 commit: {relative_path}")
    return result.stdout


def contract_hashes(repo: Path, commit: str) -> dict[str, str]:
    item_hashes = {
        relative_path: hashlib.sha256(git_blob(repo, commit, relative_path)).hexdigest()
        for relative_path in CONTRACT_PATHS
    }
    canonical = "".join(
        f"{relative_path}\t{item_hashes[relative_path]}\n"
        for relative_path in sorted(item_hashes)
    ).encode("utf-8")
    result = {
        "P1_CONTRACT_BUNDLE_SHA256": hashlib.sha256(canonical).hexdigest(),
        "GATE_TEMPLATE_SHA256": item_hashes[
            "airjet-simulation/checklists/p1_cad_gate_matrix.csv"
        ],
        "VARIANT_TABLE_SHA256": item_hashes[
            "airjet-simulation/parameters/p1_model_form_variants.csv"
        ],
        "INTERNAL_RULES_SHA256": item_hashes[
            "airjet-simulation/parameters/p1_internal_geometry_rules.csv"
        ],
    }
    result.update(
        {
            "FULL_PRODUCT_VALIDATOR_SHA256": item_hashes[
                "airjet-simulation/automation/ansys/contracts/full_product_semantic_contract_v1.py"
            ],
            "FULL_PRODUCT_SCHEMA_SHA256": item_hashes[
                "airjet-simulation/automation/ansys/contracts/full_product_semantic_sidecar_v1.schema.json"
            ],
            "FULL_PRODUCT_CORE_TEST_SHA256": item_hashes[
                "airjet-simulation/automation/ansys/contracts/test_full_product_semantic_contract_v1.py"
            ],
            "TRUSTED_VARIANT_GENERATOR_SHA256": item_hashes[
                "airjet-simulation/automation/ansys/contracts/build_full_product_trusted_variants.py"
            ],
            "TRUSTED_VARIANT_TEST_SHA256": item_hashes[
                "airjet-simulation/automation/ansys/contracts/test_full_product_trusted_variants.py"
            ],
            "TRUSTED_CAMPAIGN_SHA256": item_hashes[CAMPAIGN_PATH],
        }
    )
    return result


def strict_json_bytes(data: bytes, context: str) -> object:
    def unique_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key in {context}: {key}")
            result[key] = value
        return result

    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=unique_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid strict UTF-8 JSON: {context}") from exc


def load_contract_module(data: bytes) -> types.ModuleType:
    module = types.ModuleType("full_product_semantic_contract_v1_at_006_commit")
    exec(compile(data, "<full_product_semantic_contract_v1.py>", "exec"), module.__dict__)
    return module


def canonical_profile_sha256(profile: dict[str, object]) -> str:
    return hashlib.sha256(
        json.dumps(
            profile,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def load_production_contract_at_commit(
    repo: Path,
    commit: str,
    variant_expectations: dict[str, tuple[str, int]],
) -> dict[str, object]:
    """Validate the exact Gen1 campaign and resolve signed runtime contracts.

    The current frozen declaration is intentionally static-only.  Parsing and
    hashing the campaign still occurs before the execution-state check, but a
    claimed completed 006 cannot pass until both production profiles are
    registered in the same exact profiles blob.
    """

    profiles_blob = git_blob(repo, commit, PROFILES_PATH)
    profiles_doc = strict_json_bytes(profiles_blob, PROFILES_PATH)
    if not isinstance(profiles_doc, dict) or set(profiles_doc) != {
        "schema_version",
        "production_contracts",
        "profiles",
    }:
        raise ValueError("006 profiles root does not contain the exact production contract")
    if profiles_doc["schema_version"] != 2:
        raise ValueError("006 profiles schema_version must equal 2")
    production = profiles_doc["production_contracts"]
    production_keys = {
        "schema_version",
        "contract_id",
        "scope",
        "product_id",
        "expected_variant_count",
        "producer_profile_id",
        "observer_profile_id",
        "execution_state",
        "p1_p6_gates",
        "components",
    }
    if not isinstance(production, dict) or set(production) != production_keys:
        raise ValueError("006 production contract fields changed")
    expected_identity = {
        "schema_version": 1,
        "contract_id": PRODUCTION_CONTRACT_ID,
        "scope": "FULL_PRODUCT",
        "product_id": PRODUCT_TARGET,
        "expected_variant_count": 9,
        "producer_profile_id": PRODUCTION_PRODUCER_PROFILE_ID,
        "observer_profile_id": PRODUCTION_OBSERVER_PROFILE_ID,
        "p1_p6_gates": "NOT_RUN",
    }
    for key, value in expected_identity.items():
        if production.get(key) != value:
            raise ValueError(f"006 production contract identity changed: {key}")
    component_paths = {
        "full_product_validator": "airjet-simulation/automation/ansys/contracts/full_product_semantic_contract_v1.py",
        "full_product_schema": "airjet-simulation/automation/ansys/contracts/full_product_semantic_sidecar_v1.schema.json",
        "full_product_core_test": "airjet-simulation/automation/ansys/contracts/test_full_product_semantic_contract_v1.py",
        "trusted_variant_generator": "airjet-simulation/automation/ansys/contracts/build_full_product_trusted_variants.py",
        "trusted_variant_test": "airjet-simulation/automation/ansys/contracts/test_full_product_trusted_variants.py",
        "trusted_campaign": CAMPAIGN_PATH,
    }
    components = production["components"]
    if not isinstance(components, list) or len(components) != len(component_paths):
        raise ValueError("006 production component count changed")
    component_by_key: dict[str, dict[str, object]] = {}
    for item in components:
        if not isinstance(item, dict) or set(item) != {"contract_key", "git_path", "sha256"}:
            raise ValueError("006 production component fields changed")
        key = item["contract_key"]
        if not isinstance(key, str) or key in component_by_key:
            raise ValueError("006 production component key is invalid or duplicated")
        component_by_key[key] = item
    if set(component_by_key) != set(component_paths):
        raise ValueError("006 production component key set changed")
    component_blobs: dict[str, bytes] = {}
    for key, path in component_paths.items():
        item = component_by_key[key]
        if item["git_path"] != path:
            raise ValueError(f"006 production component path changed: {key}")
        blob = git_blob(repo, commit, path)
        if hashlib.sha256(blob).hexdigest() != item["sha256"]:
            raise ValueError(f"006 production component SHA changed: {key}")
        component_blobs[key] = blob

    engine = load_contract_module(component_blobs["full_product_validator"])
    campaign_blob = component_blobs["trusted_campaign"]
    campaign_doc = strict_json_bytes(campaign_blob, CAMPAIGN_PATH)
    if not isinstance(campaign_doc, dict):
        raise ValueError("006 trusted campaign is not an object")
    records = campaign_doc.get("variant_contracts")
    sources = campaign_doc.get("source_contracts")
    if not isinstance(records, list) or not isinstance(sources, list):
        raise ValueError("006 trusted campaign record arrays are missing")
    blueprint_blobs = {
        record["blueprint_path"]: git_blob(repo, commit, record["blueprint_path"])
        for record in records
        if isinstance(record, dict) and isinstance(record.get("blueprint_path"), str)
    }
    source_blobs = {
        item["git_path"]: git_blob(repo, commit, item["git_path"])
        for item in sources
        if isinstance(item, dict) and isinstance(item.get("git_path"), str)
    }
    expected_records = {
        source_id: {
            "configuration_id": "AJM006_GEN1_CFG_"
            + re.sub(r"[^A-Za-z0-9._-]+", "_", configuration_id).strip("_.-"),
            "cell_count": cell_count,
        }
        for source_id, (configuration_id, cell_count) in variant_expectations.items()
    }
    engine.load_trusted_campaign_bytes(
        campaign_blob,
        hashlib.sha256(campaign_blob).hexdigest(),
        blueprint_blobs,
        expected_records,
        source_blobs,
    )
    if campaign_doc.get("product_id") != PRODUCT_TARGET:
        raise ValueError("006 campaign is not Gen1-only")

    raw_profiles = profiles_doc["profiles"]
    if not isinstance(raw_profiles, list):
        raise ValueError("006 profiles list is invalid")
    profiles_by_id: dict[str, dict[str, object]] = {}
    for profile in raw_profiles:
        if not isinstance(profile, dict) or not isinstance(profile.get("profile_id"), str):
            raise ValueError("006 contains an invalid runtime profile")
        if profile["profile_id"] in profiles_by_id:
            raise ValueError("006 contains duplicate runtime profile IDs")
        profiles_by_id[profile["profile_id"]] = profile
    if production["execution_state"] != PRODUCTION_REGISTERED_STATE:
        raise ValueError(
            "006 production profiles are static-only; ANSYS execution and completed review are blocked"
        )
    runtime_contracts: dict[str, dict[str, str]] = {}
    for role, profile_id in (
        ("producer", PRODUCTION_PRODUCER_PROFILE_ID),
        ("observer", PRODUCTION_OBSERVER_PROFILE_ID),
    ):
        profile = profiles_by_id.get(profile_id)
        if profile is None:
            raise ValueError(f"006 signed {role} profile is not registered")
        if set(profile) != {
            "profile_id",
            "engine",
            "script",
            "sha256",
            "timeout_seconds",
            "output_root_id",
            "reports",
            "predecessor",
        }:
            raise ValueError(f"006 signed {role} profile fields changed")
        expected_engine = "spaceclaim" if role == "producer" else "workbench"
        expected_suffix = ".py" if role == "producer" else ".wbjn"
        if profile.get("engine") != expected_engine:
            raise ValueError(f"006 signed {role} profile engine changed")
        script = profile.get("script")
        script_sha = profile.get("sha256")
        if (
            not isinstance(script, str)
            or not script
            or os.path.isabs(script)
            or ".." in Path(script).parts
            or ":" in script
            or "\\" in script
            or Path(script).suffix.lower() != expected_suffix
            or not isinstance(script_sha, str)
            or not re.fullmatch(r"[0-9a-f]{64}", script_sha)
        ):
            raise ValueError(f"006 signed {role} profile script identity is invalid")
        script_path = f"airjet-simulation/automation/ansys/approved/{script}"
        if hashlib.sha256(git_blob(repo, commit, script_path)).hexdigest() != script_sha:
            raise ValueError(f"006 signed {role} profile script SHA changed")
        if profile.get("output_root_id") != "p1_cad_006":
            raise ValueError(f"006 signed {role} profile output root changed")
        timeout = profile.get("timeout_seconds")
        reports = profile.get("reports")
        if (
            not isinstance(timeout, int)
            or not 30 <= timeout <= 7200
            or not isinstance(reports, list)
            or not reports
            or any(
                not isinstance(item, str)
                or Path(item).name != item
                or not item.endswith(".json")
                for item in reports
            )
        ):
            raise ValueError(f"006 signed {role} profile report/timeout contract is invalid")
        predecessor = profile.get("predecessor")
        if role == "producer" and predecessor is not None:
            raise ValueError("006 producer must be the root production profile")
        if role == "observer":
            if (
                not isinstance(predecessor, dict)
                or predecessor.get("profile_id") != PRODUCTION_PRODUCER_PROFILE_ID
                or predecessor.get("required_status") != "PASS_PARTIAL_CAD_CAPABILITY"
                or not isinstance(predecessor.get("required_assertions"), list)
                or not predecessor["required_assertions"]
                or not isinstance(predecessor.get("artifacts"), list)
                or "product.step" not in predecessor["artifacts"]
                or predecessor.get("report") not in predecessor["artifacts"]
            ):
                raise ValueError("006 observer predecessor contract is not the signed producer handoff")
        runtime_contracts[role] = {
            "profile_id": profile_id,
            "profile_contract_sha256": canonical_profile_sha256(profile),
            "script_sha256": script_sha,
        }
    return {
        "engine": engine,
        "production": production,
        "campaign": campaign_doc,
        "campaign_blob": campaign_blob,
        "blueprint_blobs": blueprint_blobs,
        "source_blobs": source_blobs,
        "runtime_contracts": runtime_contracts,
    }


def source_root_name(source_root: str) -> str:
    if re.match(r"^[A-Za-z]:[\\/]", source_root):
        return PureWindowsPath(source_root).name
    return Path(source_root).name


def normalized_source_path(source_path: str, source_root: str) -> str:
    if re.match(r"^[A-Za-z]:[\\/]", source_root):
        return str(PureWindowsPath(source_path)).casefold()
    return str(Path(source_path))


def map_source_artifact(
    source_path_text: str, declared_source_root: str, local_run_root: Path
) -> Path:
    """Map an immutable Windows or POSIX manifest path into a copied review root."""

    if re.match(r"^[A-Za-z]:[\\/]", declared_source_root):
        root = PureWindowsPath(declared_source_root)
        source = PureWindowsPath(source_path_text)
        if not source.is_absolute():
            raise ValueError(f"manifest source path is not absolute: {source_path_text}")
        root_parts = tuple(part.casefold() for part in root.parts)
        source_parts = tuple(part.casefold() for part in source.parts)
        if source_parts[: len(root_parts)] != root_parts:
            raise ValueError(f"artifact escapes the declared Windows run root: {source_path_text}")
        relative_parts = source.parts[len(root.parts) :]
    else:
        root = Path(declared_source_root).expanduser()
        source = Path(source_path_text).expanduser()
        if not root.is_absolute() or not source.is_absolute():
            raise ValueError("POSIX source root and artifact paths must be absolute")
        try:
            relative_parts = source.relative_to(root).parts
        except ValueError as exc:
            raise ValueError(f"artifact escapes the declared POSIX run root: {source_path_text}") from exc
    if not relative_parts or any(part in {"", ".", ".."} for part in relative_parts):
        raise ValueError(f"unsafe or empty artifact relative path: {source_path_text}")
    mapped_unresolved = local_run_root.joinpath(*relative_parts)
    cursor = local_run_root
    for part in relative_parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise ValueError(f"symlink is prohibited in copied review artifacts: {cursor}")
    mapped = mapped_unresolved.resolve()
    if not is_within(mapped, local_run_root):
        raise ValueError(f"mapped artifact escapes the local review root: {mapped}")
    return mapped


def validate_manifest(
    path: Path,
    run_root: Path,
    declared_source_root: str,
    expected_commit: str,
) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != MANIFEST_HEADER:
            raise ValueError("006 external manifest header does not match the canonical schema")
        rows = list(reader)
    if not rows:
        raise ValueError("006 external manifest contains no artifact rows")
    seen_paths: set[Path] = set()
    seen_case_roles: set[tuple[str, str]] = set()
    roles_by_case: dict[str, set[str]] = {}
    for number, row in enumerate(rows, 2):
        artifact = map_source_artifact(row["absolute_path"], declared_source_root, run_root)
        if artifact in seen_paths:
            raise ValueError(f"duplicate artifact path at manifest line {number}")
        seen_paths.add(artifact)
        if not is_within(artifact, run_root):
            raise ValueError(f"artifact escapes the declared run root at line {number}: {artifact}")
        if not artifact.is_file():
            raise ValueError(f"artifact is missing at line {number}: {artifact}")
        try:
            recorded_size = int(row["size_bytes"])
        except ValueError as exc:
            raise ValueError(f"artifact size is not an integer at line {number}") from exc
        if recorded_size <= 0 or recorded_size != artifact.stat().st_size:
            raise ValueError(f"artifact size mismatch at line {number}: {artifact}")
        if not re.fullmatch(r"[0-9a-fA-F]{64}", row["sha256"]):
            raise ValueError(f"artifact SHA256 is malformed at line {number}")
        if row["sha256"].lower() != sha256(artifact):
            raise ValueError(f"artifact SHA256 mismatch at line {number}: {artifact}")
        if row["git_commit"].lower() != expected_commit.lower():
            raise ValueError(f"artifact Git commit mismatch at line {number}: {artifact}")
        case_id = row["case_id"]
        if case_id != "GLOBAL" and case_id not in EXPECTED_VARIANTS:
            raise ValueError(f"unknown manifest case_id at line {number}: {case_id}")
        if not row["file_role"]:
            raise ValueError(f"blank manifest file_role at line {number}")
        case_role = (case_id, row["file_role"])
        if case_role in seen_case_roles:
            raise ValueError(f"duplicate manifest case/file_role at line {number}: {case_role}")
        seen_case_roles.add(case_role)
        if not row["software_version"].strip():
            raise ValueError(f"blank software_version at manifest line {number}")
        try:
            created = datetime.fromisoformat(row["created_at_utc"].replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(f"invalid created_at_utc at manifest line {number}") from exc
        if created.utcoffset() is None or created.utcoffset().total_seconds() != 0:
            raise ValueError(f"created_at_utc is not UTC at manifest line {number}")
        roles_by_case.setdefault(case_id, set()).add(row["file_role"])

    missing_global = GLOBAL_ROLES - roles_by_case.get("GLOBAL", set())
    if missing_global:
        raise ValueError(f"manifest lacks global artifact roles: {sorted(missing_global)}")
    if any("LIMITATION" in row["file_role"].upper() for row in rows):
        raise ValueError("manifest contains a prohibited STEP limitation artifact")
    missing_cases = EXPECTED_VARIANTS - roles_by_case.keys()
    if missing_cases:
        raise ValueError(f"manifest lacks variant case IDs: {sorted(missing_cases)}")
    for variant_id in sorted(EXPECTED_VARIANTS):
        roles = roles_by_case[variant_id]
        missing = PER_VARIANT_ROLES - roles
        if missing:
            raise ValueError(f"manifest case {variant_id} lacks roles: {sorted(missing)}")
        if variant_id in DERIVED_VARIANTS and "PARENT_PARAMETER_DIFF" not in roles:
            raise ValueError(f"derived case {variant_id} lacks PARENT_PARAMETER_DIFF")
        if variant_id in DERIVED_VARIANTS and "PARENT_GEOMETRY_RESULT_DIFF" not in roles:
            raise ValueError(f"derived case {variant_id} lacks PARENT_GEOMETRY_RESULT_DIFF")
    unindexed: list[Path] = []
    for candidate in run_root.rglob("*"):
        if candidate.is_symlink():
            raise ValueError(f"symlink is prohibited anywhere in copied run root: {candidate}")
        if candidate.is_file() and candidate.resolve() != path.resolve() and candidate.resolve() not in seen_paths:
            unindexed.append(candidate)
    if unindexed:
        raise ValueError(f"copied run root contains unindexed files: {[str(item) for item in unindexed[:10]]}")
    return rows


def load_gate_rows_at_commit(repo: Path, commit: str) -> list[dict[str, str]]:
    gate_relpath = "airjet-simulation/checklists/p1_cad_gate_matrix.csv"
    result = subprocess.run(
        ["git", "show", f"{commit}:{gate_relpath}"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise ValueError("cannot read P1 gate input from the exact 006 Git commit")
    rows = list(csv.DictReader(io.StringIO(result.stdout)))
    keys = {(row["gate_item_id"], row["variant_id"]) for row in rows}
    if len(rows) != 252 or len(keys) != 252:
        raise ValueError("P1 gate input must contain 252 unique gate/variant rows")
    if len({row["variant_id"] for row in rows}) != 9:
        raise ValueError("P1 gate input must contain nine variants")
    if any(row["status"] != "NOT_RUN" for row in rows):
        raise ValueError("006-commit P1 gate input must remain an immutable NOT_RUN template")
    return rows


def load_variant_expectations(repo: Path, commit: str) -> dict[str, tuple[str, int]]:
    variants = list(
        csv.DictReader(
            io.StringIO(
                git_blob(
                    repo,
                    commit,
                    "airjet-simulation/parameters/p1_model_form_variants.csv",
                ).decode("utf-8")
            )
        )
    )
    if {row["variant_id"] for row in variants} != EXPECTED_VARIANTS:
        raise ValueError("006-commit variant table does not contain the frozen nine variants")
    parameters = list(
        csv.DictReader(
            io.StringIO(
                git_blob(
                    repo,
                    commit,
                    "airjet-simulation/parameters/p1_cad_parameter_map.csv",
                ).decode("utf-8")
            )
        )
    )
    cell_counts = {
        row["variant_id"]: int(float(row["value"]))
        for row in parameters
        if row["parameter_id"] == "C001"
    }
    if set(cell_counts) != EXPECTED_VARIANTS:
        raise ValueError("006-commit parameter map lacks one C001 cell count per variant")
    return {
        row["variant_id"]: (row["configuration_id"], cell_counts[row["variant_id"]])
        for row in variants
    }


def manifest_role_row(
    manifest_rows: list[dict[str, str]], case_id: str, file_role: str
) -> dict[str, str]:
    matches = [
        row
        for row in manifest_rows
        if row["case_id"] == case_id and row["file_role"] == file_role
    ]
    if len(matches) != 1:
        raise ValueError(f"manifest requires exactly one {case_id}/{file_role} row")
    return matches[0]


def validate_production_bundles(
    production_context: dict[str, object],
    manifest_rows: list[dict[str, str]],
    run_root: Path,
    declared_source_root: str,
    expected_commit: str,
    expected_variant_ids: set[str] | None = None,
) -> dict[str, dict[str, object]]:
    """Recompute all nine semantic judgments from exact files and Git blobs."""

    expected_ids = EXPECTED_VARIANTS if expected_variant_ids is None else expected_variant_ids
    engine = production_context["engine"]
    campaign = production_context["campaign"]
    campaign_blob = production_context["campaign_blob"]
    blueprint_blobs = production_context["blueprint_blobs"]
    runtime_contracts = production_context["runtime_contracts"]
    source_hashes = {
        item["contract_key"]: item["sha256"] for item in campaign["source_contracts"]
    }
    campaign_sha = hashlib.sha256(campaign_blob).hexdigest()
    results: dict[str, dict[str, object]] = {}
    key_report_fields = {
        "schema_version",
        "contract_id",
        "source_variant_id",
        "configuration_id",
        "missing_keys",
        "unexpected_keys",
        "dangling_adjacency",
        "orphan_critical_surfaces",
        "body_surface_coverage_ok",
        "assignment_solution_count",
        "topology_observed",
        "cardinality_observed",
        "observed_semantic_key_count",
        "observed_actual_entity_count",
        "observed_group_count",
        "actual_artifact_count",
        "detached_binding_valid",
        "trusted_contract_sha256",
        "status",
    }
    for record in campaign["variant_contracts"]:
        source_variant_id = record["source_variant_id"]
        blueprint_blob = blueprint_blobs[record["blueprint_path"]]
        blueprint = engine.load_trusted_blueprint_bytes(
            blueprint_blob, record["blueprint_sha256"]
        )
        summary = engine.validate_trusted_blueprint(blueprint)
        contract_hash_records = []
        for key in blueprint["required_contract_hash_keys"]:
            if key == "full_product_blueprint":
                value = summary["blueprint_payload_sha256"]
            elif key == "trusted_blueprint_file":
                value = record["blueprint_sha256"]
            elif key == "trusted_campaign":
                value = campaign_sha
            else:
                if key not in source_hashes:
                    raise ValueError(f"006 blueprint has an unbound contract hash: {key}")
                value = source_hashes[key]
            contract_hash_records.append({"contract_key": key, "sha256": value})
        trusted = engine.materialize_trusted_contract(
            blueprint,
            record["blueprint_sha256"],
            runtime_contracts["producer"],
            runtime_contracts["observer"],
            str(run_root),
            contract_hash_records,
        )
        trusted_bytes = json.dumps(
            trusted, ensure_ascii=True, sort_keys=True, separators=(",", ":")
        ).encode("ascii")
        trusted_sha = hashlib.sha256(trusted_bytes).hexdigest()

        rows_by_role: dict[str, dict[str, str]] = {}
        actual_records: list[dict[str, object]] = []
        for artifact_contract in blueprint["artifact_contracts"]:
            role = artifact_contract["role"]
            row = manifest_role_row(manifest_rows, source_variant_id, role)
            path = map_source_artifact(row["absolute_path"], declared_source_root, run_root)
            expected_path = run_root.joinpath(
                *artifact_contract["relative_path"].replace("\\", "/").split("/")
            ).resolve()
            if path != expected_path:
                raise ValueError(
                    f"006 artifact path does not match the trusted blueprint: {source_variant_id}/{role}"
                )
            rows_by_role[role] = row
            actual_records.append(
                {
                    "artifact_id": artifact_contract["artifact_id"],
                    "path": str(path),
                    "relative_path": artifact_contract["relative_path"],
                    "size": int(row["size_bytes"]),
                    "sha256": row["sha256"].lower(),
                }
            )

        def artifact_bytes(role: str) -> bytes:
            row = rows_by_role[role]
            return map_source_artifact(
                row["absolute_path"], declared_source_root, run_root
            ).read_bytes()

        producer_identity = engine.load_json_bytes_strict(artifact_bytes("PRODUCER_JOB_RECORD"))
        observer_identity = engine.load_json_bytes_strict(artifact_bytes("OBSERVER_JOB_RECORD"))
        if producer_identity.get("git_head", "").lower() != expected_commit.lower():
            raise ValueError(f"006 producer Git identity changed: {source_variant_id}")
        if observer_identity.get("git_head", "").lower() != expected_commit.lower():
            raise ValueError(f"006 observer Git identity changed: {source_variant_id}")
        if (
            producer_identity.get("case_id") != record["variant_id"]
            or observer_identity.get("case_id") != record["variant_id"]
        ):
            raise ValueError(f"006 runtime case identity changed: {source_variant_id}")
        if (
            producer_identity.get("artifact_manifest_sha256")
            != rows_by_role["PRODUCER_ARTIFACT_MANIFEST"]["sha256"].lower()
            or observer_identity.get("artifact_manifest_sha256")
            != rows_by_role["OBSERVER_ARTIFACT_MANIFEST"]["sha256"].lower()
        ):
            raise ValueError(f"006 job artifact-manifest binding changed: {source_variant_id}")

        sidecar = engine.load_json_bytes_strict(artifact_bytes("SEMANTIC_SIDECAR"))
        binding = engine.load_json_bytes_strict(artifact_bytes("SEMANTIC_BINDING"))
        observation = engine.load_json_bytes_strict(artifact_bytes("SEMANTIC_OBSERVATION"))
        result = engine.validate_full_product_bundle(
            sidecar,
            binding,
            observation,
            {
                "artifact_root": str(run_root),
                "artifact_root_id": blueprint["artifact_root_id"],
                "producer_identity": producer_identity,
                "observer_identity": observer_identity,
                "files": actual_records,
            },
            trusted_bytes,
            trusted_sha,
        )
        key_report = engine.load_json_bytes_strict(
            artifact_bytes("SEMANTIC_KEY_CARDINALITY_REPORT")
        )
        if not isinstance(key_report, dict) or set(key_report) != key_report_fields:
            raise ValueError(f"006 semantic key report fields changed: {source_variant_id}")
        expected_report = {
            "schema_version": 1,
            "contract_id": "AIRJET_FULL_PRODUCT_SEMANTIC_KEY_REPORT_V1",
            "source_variant_id": source_variant_id,
            "configuration_id": record["configuration_id"],
        }
        computed_fields = key_report_fields - set(expected_report)
        for key, value in expected_report.items():
            if key_report.get(key) != value:
                raise ValueError(f"006 semantic key report identity changed: {source_variant_id}/{key}")
        for key in computed_fields:
            if key_report.get(key) != result.get(key):
                raise ValueError(
                    f"006 semantic key report differs from computed observation: {source_variant_id}/{key}"
                )
        if (
            result["missing_keys"] != []
            or result["unexpected_keys"] != []
            or result["dangling_adjacency"] != []
            or result["orphan_critical_surfaces"] != []
            or result["body_surface_coverage_ok"] is not True
            or result["assignment_solution_count"] != 1
            or result["topology_observed"] is not True
            or result["cardinality_observed"] is not True
            or result["observed_semantic_key_count"] != record["semantic_entity_count"]
            or result["observed_group_count"] != len(blueprint["groups"])
            or result["actual_artifact_count"] != len(blueprint["artifact_contracts"])
            or result["detached_binding_valid"] is not True
            or result["status"] != "PASS_FULL_PRODUCT_SEMANTIC_BUNDLE"
        ):
            raise ValueError(f"006 computed semantic judgment failed: {source_variant_id}")
        results[source_variant_id] = result
    if set(results) != expected_ids or len(results) != len(expected_ids):
        raise ValueError("006 did not independently validate all nine Gen1 semantic bundles")
    return results


def validate_005_copy(
    manifest_rows: list[dict[str, str]],
    run_root: Path,
    declared_source_root: str,
    report_006: dict[str, str],
) -> dict[str, str]:
    manifest_row = manifest_role_row(manifest_rows, "GLOBAL", "REPORT_005_COPY")
    path = map_source_artifact(
        manifest_row["absolute_path"], declared_source_root, run_root
    )
    if (
        manifest_row["sha256"].lower() != report_006["REPORT_005_SHA256"].lower()
        or sha256(path) != report_006["REPORT_005_SHA256"].lower()
    ):
        raise ValueError("copied 005 report SHA256 does not match the 006 report")
    values = parse_unique_report(path)
    expected = {
        "TASK": "AJM-WIN-ANSYS-STUDENT-CAPABILITY-SMOKE-005",
        "COMPUTER": "LAPTOP-LCCLM2HI",
        "INSTALL_ROOT": r"D:\ansys\ANSYS Inc\ANSYS Student\v261",
        "GIT_FETCH": "PASS",
        "PROJECT_AUDIT": "PASS",
        "OLD_PLE_BASELINE": "CLEAN",
        "PARAMETRIC_GEOMETRY": "PASS",
        "NAMED_SELECTIONS": "PASS",
        "VOLUME_EXTRACT": "PASS",
        "FLUID_CONNECTIVITY": "PASS",
        "NATIVE_SAVE": "PASS",
        "STEP_EXPORT_REIMPORT": "PASS",
        "WORKBENCH_STEP_IMPORT": "PASS",
        "SOLVER_SEMANTIC_RECONSTRUCTION": "PASS",
        "SEMANTIC_KEY_CARDINALITY_CHECK": "PASS",
        "CAD_AUTHORING_ROUTE": "SPACECLAIM_SIGNED_SCRIPT_PARAMETRIC",
        "SOLVER_HANDOFF_ROUTE": "HASH_BOUND_STEP_SEMANTIC_SIDECAR",
        "EXTERNAL_NATIVE_ATTACH": "NOT_PROVEN",
        "NATIVE_PARAMETERIZATION": "NOT_PROVEN",
        "NATIVE_NAMED_SELECTION_TRANSFER": "NOT_PROVEN",
        "P1_CAD_TOOLCHAIN_SCOPE": "ALTERNATE_ROUTE_ONLY",
        "P1_STAGE_GATE": "NOT_RUN",
    }
    for key, expected_value in expected.items():
        if values.get(key) != expected_value:
            raise ValueError(f"copied 005 report field {key} must equal {expected_value!r}")
    if not values.get("ANSYS_VERSION", "").startswith("2026 R1"):
        raise ValueError("copied 005 report does not identify Ansys 2026 R1")
    if values.get("GIT_COMMIT", "").lower() != report_006["REPORT_005_GIT_COMMIT"].lower():
        raise ValueError("copied 005 report commit differs from the 006 report")
    if values.get("P1_CAD_TOOLCHAIN_READINESS") != report_006["P1_CAD_TOOLCHAIN_READINESS"]:
        raise ValueError("copied 005 readiness differs from the 006 report")
    if values.get("STUDENT_TOOLCHAIN_STATUS") != "PASS_START_P1":
        raise ValueError("copied 005 Student status is inconsistent with readiness")
    if values.get("GIT_CLEAN", "").upper() not in {"TRUE", "PASS"}:
        raise ValueError("copied 005 report does not prove a clean Git tree")
    return manifest_row


def validate_variant_checks(
    manifest_rows: list[dict[str, str]],
    run_root: Path,
    declared_source_root: str,
    expectations: dict[str, tuple[str, int]],
) -> dict[str, dict[str, str]]:
    checks_by_variant: dict[str, dict[str, str]] = {}
    for variant_id, (configuration_id, expected_cells) in expectations.items():
        manifest_row = manifest_role_row(manifest_rows, variant_id, "AUTOMATED_CHECKS_CSV")
        path = map_source_artifact(
            manifest_row["absolute_path"], declared_source_root, run_root
        )
        with path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames != VARIANT_CHECK_HEADER:
                raise ValueError(f"variant checks header mismatch: {variant_id}")
            rows = list(reader)
        if len(rows) != 1:
            raise ValueError(f"variant checks must contain exactly one row: {variant_id}")
        row = rows[0]
        checks_by_variant[variant_id] = row
        if row["variant_id"] != variant_id or row["configuration_id"] != configuration_id:
            raise ValueError(f"variant checks identity mismatch: {variant_id}")
        integer_expectations = {
            "cell_count": expected_cells,
            "connected_cell_count": expected_cells,
            "isolated_fluid_count": 0,
            "interference_count": 0,
            "sliver_count": 0,
            "duplicate_face_count": 0,
            "blind_or_lost_orifice_count": 0,
        }
        for key, expected in integer_expectations.items():
            try:
                actual = int(row[key])
            except ValueError as exc:
                raise ValueError(f"variant checks {key} is not an integer: {variant_id}") from exc
            if actual != expected:
                raise ValueError(f"variant checks {key} failed for {variant_id}: {actual}")
        if row["excluded_datum_feature_ids"] != EXCLUDED_NONPHYSICAL_FEATURE_IDS:
            raise ValueError(f"variant checks datum-exclusion scope changed: {variant_id}")
        try:
            hole_count = int(row["actual_orifice_count"])
            open_area = float(row["actual_open_area_pct"])
            minimum_clearance = float(row["minimum_clearance_mm"])
            envelope = tuple(float(row[key]) for key in ("envelope_x_mm", "envelope_y_mm", "envelope_z_mm"))
            closure_error = float(row["thickness_closure_error_mm"])
        except ValueError as exc:
            raise ValueError(f"variant checks contains nonnumeric geometry results: {variant_id}") from exc
        if not all(math.isfinite(value) for value in (*envelope, open_area, minimum_clearance, closure_error)):
            raise ValueError(f"variant checks contains nonfinite results: {variant_id}")
        if hole_count <= 0 or not 8.0 <= open_area <= 12.0 or minimum_clearance < 0.0:
            raise ValueError(f"variant checks orifice/clearance result failed: {variant_id}")
        if any(abs(actual - expected) > 1e-6 for actual, expected in zip(envelope, (27.5, 41.5, 2.8))):
            raise ValueError(f"variant envelope result failed: {variant_id}")
        if abs(closure_error) > 1e-6:
            raise ValueError(f"variant thickness closure failed: {variant_id}")
        for key in (
            "named_selection_check",
            "native_reopen",
            "step_transfer",
            "workbench_step_import",
            "solver_semantic_reconstruction",
            "semantic_adjacency_check",
            "c017_c019_physics_guard",
            "anchor_partition_nonphysical_guard",
        ):
            if row[key] != "PASS":
                raise ValueError(f"variant checks {key} failed: {variant_id}")
    return checks_by_variant


def validate_gate_evidence(
    manifest_rows: list[dict[str, str]],
    run_root: Path,
    declared_source_root: str,
    gate_rows: list[dict[str, str]],
) -> dict[tuple[str, str], dict[str, str]]:
    evidence_manifest_row = manifest_role_row(
        manifest_rows, "GLOBAL", "GATE_EVIDENCE_006_CSV"
    )
    evidence_path = map_source_artifact(
        evidence_manifest_row["absolute_path"], declared_source_root, run_root
    )
    with evidence_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != GATE_EVIDENCE_HEADER:
            raise ValueError("006 gate evidence header does not match the canonical schema")
        evidence_rows = list(reader)
    evidence_by_key = {
        (row["gate_item_id"], row["variant_id"]): row for row in evidence_rows
    }
    gate_by_key = {(row["gate_item_id"], row["variant_id"]): row for row in gate_rows}
    if len(evidence_rows) != 252 or len(evidence_by_key) != 252 or set(evidence_by_key) != set(gate_by_key):
        raise ValueError("006 gate evidence must contain the exact 252 frozen gate keys")
    manifest_evidence = {
        (
            normalized_source_path(row["absolute_path"], declared_source_root),
            row["sha256"].lower(),
        ): row
        for row in manifest_rows
    }
    for key, row in evidence_by_key.items():
        if not row["measured_value"].strip():
            raise ValueError(f"006 gate evidence lacks measured_value: {key}")
        if not re.fullmatch(r"[0-9a-fA-F]{64}", row["evidence_sha256"]):
            raise ValueError(f"006 gate evidence SHA256 is malformed: {key}")
        primary_key = (
            normalized_source_path(row["evidence_original_path"], declared_source_root),
            row["evidence_sha256"].lower(),
        )
        if primary_key not in manifest_evidence:
            raise ValueError(f"006 gate evidence does not reference a hashed manifest artifact: {key}")
        secondary_path = row["secondary_evidence_original_path"]
        secondary_hash = row["secondary_evidence_sha256"]
        secondary_key: tuple[str, str] | None = None
        if bool(secondary_path) != bool(secondary_hash):
            raise ValueError(f"006 gate evidence has a partial secondary reference: {key}")
        if secondary_path:
            if not re.fullmatch(r"[0-9a-fA-F]{64}", secondary_hash):
                raise ValueError(f"006 secondary evidence SHA256 is malformed: {key}")
            secondary_key = (
                normalized_source_path(secondary_path, declared_source_root),
                secondary_hash.lower(),
            )
            if secondary_key not in manifest_evidence:
                raise ValueError(f"006 secondary gate evidence is not a manifest artifact: {key}")
        item_id = key[0]
        if item_id == "G0_005_TOOLCHAIN":
            role = manifest_evidence[primary_key]
            if role["case_id"] != "GLOBAL" or role["file_role"] != "REPORT_005_COPY":
                raise ValueError("every G0_005_TOOLCHAIN row must cite REPORT_005_COPY")
        if item_id == "G4_SINGLE_FACTOR_ISOLATION" and key[1] in DERIVED_VARIANTS:
            cited_rows = [manifest_evidence[primary_key]]
            if secondary_key is not None:
                cited_rows.append(manifest_evidence[secondary_key])
            cited = {item["file_role"] for item in cited_rows}
            if cited != {"PARENT_PARAMETER_DIFF", "PARENT_GEOMETRY_RESULT_DIFF"}:
                raise ValueError(
                    f"derived single-factor gate must cite parameter and geometry diffs: {key}"
                )
            if any(item["case_id"] != key[1] for item in cited_rows):
                raise ValueError(f"derived single-factor evidence cites the wrong case: {key}")
        route_gate_roles = {
            "G4_STEP_TRANSFER": {"STEP_REIMPORT_LOG", "SEMANTIC_BINDING"},
            "G4_WB_TRANSFER": {
                "WORKBENCH_STEP_SEMANTIC_LOG",
                "SEMANTIC_KEY_CARDINALITY_REPORT",
            },
        }
        if item_id in route_gate_roles:
            cited_rows = [manifest_evidence[primary_key]]
            if secondary_key is not None:
                cited_rows.append(manifest_evidence[secondary_key])
            if {item["file_role"] for item in cited_rows} != route_gate_roles[item_id]:
                raise ValueError(f"route Gate does not cite its two required evidence roles: {key}")
            if any(item["case_id"] != key[1] for item in cited_rows):
                raise ValueError(f"route Gate evidence cites the wrong case: {key}")
        suggested = row["006_suggested_status"]
        if item_id == "P1_INDEPENDENT_REVIEW":
            if suggested != "BLOCKED":
                raise ValueError("006 must leave every independent-review gate BLOCKED")
        elif suggested != "PASS":
            raise ValueError(f"complete 006 run has a non-PASS build gate: {key}")
    return evidence_by_key


def validate_no_transfer_limitation(
    manifest_rows: list[dict[str, str]],
    variant_checks: dict[str, dict[str, str]],
    gate_evidence: dict[tuple[str, str], dict[str, str]],
) -> None:
    if any("LIMITATION" in row["file_role"].upper() for row in manifest_rows):
        raise ValueError("STEP limitation artifacts are prohibited by the frozen route")
    if any(row["step_transfer"] != "PASS" for row in variant_checks.values()):
        raise ValueError("all nine route-dependent STEP checks must PASS")
    if any(
        row["006_suggested_status"] != "PASS"
        for (gate_id, _variant_id), row in gate_evidence.items()
        if gate_id == "G4_STEP_TRANSFER"
    ):
        raise ValueError("all nine route-dependent STEP Gate suggestions must PASS")


def validate_iso_date(value: str, context: str) -> None:
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"invalid review_date for {context}") from exc


def manifest_source_index(
    manifest_rows: list[dict[str, str]], declared_source_root: str
) -> dict[tuple[str, str], dict[str, str]]:
    return {
        (
            normalized_source_path(row["absolute_path"], declared_source_root),
            row["sha256"].lower(),
        ): row
        for row in manifest_rows
    }


def validate_spot_checks(
    path: Path,
    manifest_rows: list[dict[str, str]],
    declared_source_root: str,
) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != SPOT_CHECK_HEADER:
            raise ValueError("native spot-check record header does not match the canonical schema")
        rows = list(reader)
    expected = {check_id: (case_id, role) for check_id, case_id, role in SPOT_CHECK_CASES}
    if len(rows) != 6 or {row["check_id"] for row in rows} != set(expected):
        raise ValueError("native spot-check record must contain the exact six required checks")
    source_index = manifest_source_index(manifest_rows, declared_source_root)
    for row in rows:
        check_id = row["check_id"]
        if (row["artifact_case_id"], row["artifact_file_role"]) != expected[check_id]:
            raise ValueError(f"native spot-check target changed: {check_id}")
        key = (
            normalized_source_path(row["artifact_original_path"], declared_source_root),
            row["artifact_sha256"].lower(),
        )
        if key not in source_index:
            raise ValueError(f"native spot-check artifact is not in the 006 manifest: {check_id}")
        manifest_row = source_index[key]
        if (
            manifest_row["case_id"] != row["artifact_case_id"]
            or manifest_row["file_role"] != row["artifact_file_role"]
        ):
            raise ValueError(f"native spot-check artifact role mismatch: {check_id}")
        if row["result"] != "PASS" or not row["reviewer"].strip() or not row["notes"].strip():
            raise ValueError(f"native spot-check is incomplete: {check_id}")
        validate_iso_date(row["review_date"], check_id)
    return rows


def validate_final_worksheet(
    path: Path,
    spot_check_path: Path,
    manifest_rows: list[dict[str, str]],
    declared_source_root: str,
    gate_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != REVIEW_HEADER:
            raise ValueError("final review worksheet header does not match the canonical schema")
        rows = list(reader)
    rows_by_key = {(row["gate_item_id"], row["variant_id"]): row for row in rows}
    gates_by_key = {(row["gate_item_id"], row["variant_id"]): row for row in gate_rows}
    if len(rows) != 252 or len(rows_by_key) != 252 or set(rows_by_key) != set(gates_by_key):
        raise ValueError("final review worksheet must retain the exact 252 frozen gate keys")
    hard_count = sum(row["hard_gate"] == "true" for row in gate_rows)
    if hard_count != 252:
        raise ValueError("006-commit Gate template must contain exactly 252 hard gates")
    source_index = manifest_source_index(manifest_rows, declared_source_root)
    spot_key = (str(spot_check_path.resolve()), sha256(spot_check_path))
    step_count = 0
    for key, gate in gates_by_key.items():
        row = rows_by_key[key]
        if (
            row["configuration_id"] != gate["configuration_id"]
            or row["variant_kind"] != gate["variant_kind"]
            or row["comparison_parent_variant_id"]
            != gate["comparison_parent_variant_id"]
            or row["changed_factor"] != gate["changed_factor"]
            or row["hard_gate"] != gate["hard_gate"]
            or row["requirement"] != gate["requirement"]
            or row["tolerance_or_acceptance"] != gate["tolerance_or_acceptance"]
        ):
            raise ValueError(f"final review worksheet changed frozen Gate metadata: {key}")
        status = row["review_status"]
        if not row["reviewer"].strip():
            raise ValueError(f"final review row lacks reviewer: {key}")
        validate_iso_date(row["review_date"], str(key))
        if key[0] == "G4_STEP_TRANSFER":
            step_count += 1
        if status != "PASS":
            raise ValueError(f"final hard-gate review is not PASS: {key}")
        primary_manifest_row: dict[str, str] | None = None
        if key[0] == "P1_INDEPENDENT_REVIEW":
            if (row["evidence_path"], row["evidence_sha256"].lower()) != spot_key:
                raise ValueError("independent-review Gate must cite the completed native spot-check record")
        else:
            evidence_key = (
                normalized_source_path(row["evidence_path"], declared_source_root),
                row["evidence_sha256"].lower(),
            )
            if evidence_key not in source_index:
                raise ValueError(f"final review evidence is not in the 006 manifest: {key}")
            primary_manifest_row = source_index[evidence_key]
        secondary_path = row["secondary_evidence_path"]
        secondary_hash = row["secondary_evidence_sha256"]
        secondary_manifest_row: dict[str, str] | None = None
        if bool(secondary_path) != bool(secondary_hash):
            raise ValueError(f"final review has a partial secondary reference: {key}")
        if secondary_path:
            secondary_key = (
                normalized_source_path(secondary_path, declared_source_root),
                secondary_hash.lower(),
            )
            if secondary_key not in source_index:
                raise ValueError(f"final secondary evidence is not in the 006 manifest: {key}")
            secondary_manifest_row = source_index[secondary_key]
        if key[0] == "G0_005_TOOLCHAIN" and (
            primary_manifest_row is None
            or primary_manifest_row["case_id"] != "GLOBAL"
            or primary_manifest_row["file_role"] != "REPORT_005_COPY"
        ):
            raise ValueError("final G0_005_TOOLCHAIN row must still cite REPORT_005_COPY")
        if key[0] == "G4_SINGLE_FACTOR_ISOLATION" and key[1] in DERIVED_VARIANTS:
            cited_rows = [item for item in (primary_manifest_row, secondary_manifest_row) if item]
            if {item["file_role"] for item in cited_rows} != {
                "PARENT_PARAMETER_DIFF",
                "PARENT_GEOMETRY_RESULT_DIFF",
            } or any(item["case_id"] != key[1] for item in cited_rows):
                raise ValueError(
                    f"final derived single-factor Gate must retain both same-case diff artifacts: {key}"
                )
        route_gate_roles = {
            "G4_STEP_TRANSFER": {"STEP_REIMPORT_LOG", "SEMANTIC_BINDING"},
            "G4_WB_TRANSFER": {
                "WORKBENCH_STEP_SEMANTIC_LOG",
                "SEMANTIC_KEY_CARDINALITY_REPORT",
            },
        }
        if key[0] in route_gate_roles:
            cited_rows = [item for item in (primary_manifest_row, secondary_manifest_row) if item]
            if {item["file_role"] for item in cited_rows} != route_gate_roles[key[0]]:
                raise ValueError(f"final route Gate must retain both required evidence roles: {key}")
            if any(item["case_id"] != key[1] for item in cited_rows):
                raise ValueError(f"final route Gate evidence cites the wrong case: {key}")
    if step_count != 9:
        raise ValueError("final review worksheet must contain nine STEP gate rows")
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--finalize-worksheet", type=Path)
    parser.add_argument("--spot-check-record", type=Path)
    args = parser.parse_args()

    repo = args.repo.resolve()
    report = args.report.resolve()
    manifest = args.manifest.resolve()
    run_root = args.run_root.resolve()
    output_dir = args.output_dir.resolve()
    finalize_worksheet = args.finalize_worksheet.resolve() if args.finalize_worksheet else None
    spot_check_record = args.spot_check_record.resolve() if args.spot_check_record else None
    if bool(finalize_worksheet) != bool(spot_check_record):
        raise ValueError("finalize mode requires both --finalize-worksheet and --spot-check-record")
    if is_within(output_dir, repo):
        raise ValueError("review packet output must remain outside the Git repository")
    if not is_within(manifest, run_root):
        raise ValueError("review manifest must be the copied original inside --run-root")

    values = parse_unique_report(report)
    require_report(values)
    commit = values["GIT_COMMIT"]
    if not git_commit_is_ancestor(repo, commit):
        raise ValueError("006 Git commit is not an ancestor of the review repository HEAD")
    if not git_commit_is_ancestor(repo, values["REPORT_005_GIT_COMMIT"], commit):
        raise ValueError("005 Git commit is not an ancestor of the exact 006 Git commit")
    expected_hashes = contract_hashes(repo, commit)
    for key, expected_hash in expected_hashes.items():
        if values[key].lower() != expected_hash:
            raise ValueError(f"006 report {key} does not match the exact 006 Git commit")
    if values["EXTERNAL_FILE_MANIFEST_SHA256"].lower() != sha256(manifest):
        raise ValueError("copied original manifest SHA256 does not match the 006 report")
    declared_root = values["EXTERNAL_RUN_DIRECTORY"]
    if source_root_name(declared_root) != values["RUN_ID"]:
        raise ValueError("006 RUN_ID does not equal the source run-root directory name")
    mapped_manifest = map_source_artifact(
        values["EXTERNAL_FILE_MANIFEST"], declared_root, run_root
    )
    if mapped_manifest != manifest:
        raise ValueError("006 EXTERNAL_FILE_MANIFEST does not map to --manifest")
    artifacts = validate_manifest(
        manifest,
        run_root,
        declared_root,
        commit,
    )
    if len(artifacts) != int(values["MANIFEST_DATA_ROW_COUNT"]):
        raise ValueError("006 MANIFEST_DATA_ROW_COUNT does not match the original manifest")
    validate_005_copy(artifacts, run_root, declared_root, values)
    master_row = manifest_role_row(artifacts, "GLOBAL", "MASTER_NATIVE_CAD")
    if (
        map_source_artifact(values["MASTER_MODEL_PATH"], declared_root, run_root)
        != map_source_artifact(master_row["absolute_path"], declared_root, run_root)
        or values["MASTER_MODEL_SHA256"].lower() != master_row["sha256"].lower()
    ):
        raise ValueError("006 master-model report fields do not match manifest MASTER_NATIVE_CAD")

    gate_rows = load_gate_rows_at_commit(repo, commit)
    variant_expectations = load_variant_expectations(repo, commit)
    production_context = load_production_contract_at_commit(
        repo,
        commit,
        variant_expectations,
    )
    variant_checks = validate_variant_checks(
        artifacts,
        run_root,
        declared_root,
        variant_expectations,
    )
    gate_evidence = validate_gate_evidence(
        artifacts,
        run_root,
        declared_root,
        gate_rows,
    )
    validate_no_transfer_limitation(
        artifacts,
        variant_checks,
        gate_evidence,
    )
    semantic_results = validate_production_bundles(
        production_context,
        artifacts,
        run_root,
        declared_root,
        commit,
    )
    if len(semantic_results) != 9:
        raise ValueError("006 semantic bundle validation count changed")
    if finalize_worksheet is not None and spot_check_record is not None:
        if not output_dir.is_dir():
            raise ValueError("finalize output directory must be the existing prepared review directory")
        validate_spot_checks(
            spot_check_record,
            artifacts,
            declared_root,
        )
        final_rows = validate_final_worksheet(
            finalize_worksheet,
            spot_check_record,
            artifacts,
            declared_root,
            gate_rows,
        )
        final_report = output_dir / "P1_CAD_INDEPENDENT_REVIEW_FINAL_007.txt"
        if final_report.exists():
            raise ValueError("final review report already exists; do not overwrite review history")
        final_report.write_text(
            "\n".join(
                [
                    "TASK=AJM-P1-CAD-INDEPENDENT-REVIEW-FINAL-007",
                    f"SOURCE_006_GIT_COMMIT={commit}",
                    f"REPORT_006_SHA256={sha256(report)}",
                    f"MANIFEST_006_SHA256={sha256(manifest)}",
                    f"P1_CONTRACT_BUNDLE_SHA256={expected_hashes['P1_CONTRACT_BUNDLE_SHA256']}",
                    f"FINAL_WORKSHEET={finalize_worksheet}",
                    f"FINAL_WORKSHEET_SHA256={sha256(finalize_worksheet)}",
                    f"NATIVE_SPOT_CHECK_RECORD={spot_check_record}",
                    f"NATIVE_SPOT_CHECK_RECORD_SHA256={sha256(spot_check_record)}",
                    f"GATE_ROW_COUNT={len(final_rows)}",
                    "HARD_GATE_PASS_COUNT=252",
                    "STEP_GATE_PASS_COUNT=9",
                    "PRODUCT_TARGET=AIRJET_MINI_GEN1",
                    "SEMANTIC_BUNDLE_VALIDATION=PASS_ALL_9",
                    "P1_REVIEW_RECOMMENDATION=PASS",
                    "P1_STAGE_GATE=PENDING_REVIEW_RECORD_COMMIT",
                    "NOTE=Recommendation PASS is not recorded P1 stage PASS until a separate reviewed Git commit updates project status",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        print(f"P1_REVIEW_RECOMMENDATION=PASS report={final_report}")
        print("P1_STAGE_GATE=PENDING_REVIEW_RECORD_COMMIT")
        return 0

    output_dir.mkdir(parents=True, exist_ok=False)
    worksheet = output_dir / "P1_CAD_INDEPENDENT_REVIEW_007.csv"
    with worksheet.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=REVIEW_HEADER, lineterminator="\n")
        writer.writeheader()
        for row in gate_rows:
            evidence = gate_evidence[(row["gate_item_id"], row["variant_id"])]
            writer.writerow(
                {
                    "gate_item_id": row["gate_item_id"],
                    "configuration_id": row["configuration_id"],
                    "variant_id": row["variant_id"],
                    "variant_kind": row["variant_kind"],
                    "comparison_parent_variant_id": row["comparison_parent_variant_id"],
                    "changed_factor": row["changed_factor"],
                    "hard_gate": row["hard_gate"],
                    "requirement": row["requirement"],
                    "tolerance_or_acceptance": row["tolerance_or_acceptance"],
                    "006_measured_value": evidence["measured_value"],
                    "006_suggested_status": evidence["006_suggested_status"],
                    "review_status": "NOT_REVIEWED",
                    "evidence_path": evidence["evidence_original_path"],
                    "evidence_sha256": evidence["evidence_sha256"],
                    "secondary_evidence_path": evidence[
                        "secondary_evidence_original_path"
                    ],
                    "secondary_evidence_sha256": evidence[
                        "secondary_evidence_sha256"
                    ],
                    "reviewer": "",
                    "review_date": "",
                    "review_notes": "",
                }
            )

    spot_template = output_dir / "P1_CAD_NATIVE_SPOT_CHECK_007.csv"
    with spot_template.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=SPOT_CHECK_HEADER, lineterminator="\n")
        writer.writeheader()
        for check_id, case_id, file_role in SPOT_CHECK_CASES:
            artifact = manifest_role_row(artifacts, case_id, file_role)
            writer.writerow(
                {
                    "check_id": check_id,
                    "artifact_case_id": case_id,
                    "artifact_file_role": file_role,
                    "artifact_original_path": artifact["absolute_path"],
                    "artifact_sha256": artifact["sha256"],
                    "reviewer": "",
                    "review_date": "",
                    "result": "NOT_REVIEWED",
                    "notes": "",
                }
            )

    summary = output_dir / "P1_CAD_REVIEW_PACKET_007.txt"
    summary.write_text(
        "\n".join(
            [
                "TASK=AJM-P1-CAD-INDEPENDENT-REVIEW-PREP-007",
                f"REPORT_006={report}",
                f"REPORT_006_SHA256={sha256(report)}",
                f"MANIFEST_006={manifest}",
                f"MANIFEST_006_SHA256={sha256(manifest)}",
                f"SOURCE_RUN_ROOT={declared_root}",
                f"LOCAL_REVIEW_RUN_ROOT={run_root}",
                f"GIT_COMMIT={commit}",
                f"P1_CONTRACT_BUNDLE_SHA256={expected_hashes['P1_CONTRACT_BUNDLE_SHA256']}",
                f"GATE_TEMPLATE_SHA256={expected_hashes['GATE_TEMPLATE_SHA256']}",
                f"VARIANT_TABLE_SHA256={expected_hashes['VARIANT_TABLE_SHA256']}",
                f"INTERNAL_RULES_SHA256={expected_hashes['INTERNAL_RULES_SHA256']}",
                f"ARTIFACT_COUNT={len(artifacts)}",
                "PRODUCT_TARGET=AIRJET_MINI_GEN1",
                "SEMANTIC_BUNDLE_VALIDATION=PASS_ALL_9",
                f"GATE_ROW_COUNT={len(gate_rows)}",
                f"REVIEW_WORKSHEET={worksheet}",
                f"NATIVE_SPOT_CHECK_RECORD={spot_template}",
                "REVIEW_STATUS=NOT_REVIEWED",
                "P1_STAGE_GATE=PENDING_INDEPENDENT_REVIEW",
                "REVIEW_PACKET_PREPARATION=PASS",
                "NOTE=Preparation PASS does not mean P1 PASS",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"REVIEW_PACKET_PREPARATION=PASS worksheet={worksheet}")
    print(f"artifacts={len(artifacts)} gate_rows={len(gate_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

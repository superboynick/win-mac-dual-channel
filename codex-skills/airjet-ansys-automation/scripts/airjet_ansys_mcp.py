#!/usr/bin/env python3
"""Fail-closed local MCP adapter for approved AirJet ANSYS automation profiles."""

from __future__ import annotations

import ctypes
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import IO, Any
from uuid import uuid4

from mcp.server.fastmcp import FastMCP


MCP = FastMCP(
    "AirJet ANSYS Automation",
    instructions=(
        "Run only Git-tracked, hash-pinned AirJet profiles through official ANSYS "
        "interfaces. Never inspect or change licensing and never expose a shell."
    ),
)

REPO = Path(r"C:\Users\admin\win-mac-dual-channel")
SCRIPT_ROOT = REPO / "airjet-simulation" / "automation" / "ansys" / "approved"
POLICY_GIT_PATH = "airjet-simulation/automation/ansys/profiles.json"
SCRIPT_GIT_ROOT = "airjet-simulation/automation/ansys/approved"
SERVER_GIT_PATH = (
    "codex-skills/airjet-ansys-automation/scripts/airjet_ansys_mcp.py"
)
ANSYS_ROOT = Path(r"D:\ansys\ANSYS Inc\ANSYS Student\v261")
SPACECLAIM = ANSYS_ROOT / "scdm" / "SpaceClaim.exe"
RUNWB2 = ANSYS_ROOT / "Framework" / "bin" / "Win64" / "RunWB2.exe"
MECHANICAL = ANSYS_ROOT / "aisol" / "bin" / "winx64" / "AnsysWBU.exe"
VENV_PYTHON = Path(
    r"C:\Users\admin\AppData\Local\AirJetAnsysAutomation\.venv\Scripts\python.exe"
)
OUTPUT_ROOTS = {
    "student_smoke_005": Path(
        r"C:\Users\admin\Downloads\AIRJET_ANSYS_STUDENT_SMOKE_005"
    ),
    "p1_cad_006": Path(r"D:\AirJet_P1\AJM-P1-CAD-006"),
    "p2_structural_008": Path(r"D:\AirJet_P2\AJM-P2-STRUCTURAL-008"),
}
ENGINE_EXECUTABLES = {
    "spaceclaim": SPACECLAIM,
    "workbench": RUNWB2,
    "pymechanical": VENV_PYTHON,
    "pyfluent": VENV_PYTHON,
}
ENGINE_EXTENSIONS = {
    "spaceclaim": ".py",
    "workbench": ".wbjn",
    "pymechanical": ".py",
    "pyfluent": ".py",
}
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
MAX_ARTIFACTS = 500
MAX_INLINE_REPORT_BYTES = 128 * 1024
MAX_SCRIPT_BYTES = 1024 * 1024
MAX_PROFILE_DEPENDENCY_BYTES = 4194304
MAX_ARTIFACT_BYTES = 16 * 1024 * 1024 * 1024
MAX_TOTAL_ARTIFACT_BYTES = 64 * 1024 * 1024 * 1024
FILE_ATTRIBUTE_REPARSE_POINT = 0x400
ERROR_ALREADY_EXISTS = 183
MACHINE_JOB_LOCK_NAME = r"Global\AirJetAnsysAutomation-OneJob"
ALLOWED_SIGNER_FINGERPRINTS = {
    "SHA256:jdxP5xJrt8J7PKjeCrJmrEeoAH44u9NxBICo41HwMuc",
    "SHA256:oI3/MIlKz1mgLV3+5n1coQxynaqQOzxqi0GHxreGEdc",
}
EXPECTED_PACKAGES = {
    "mcp": "1.28.1",
    "ansys-fluent-core": "0.40.2",
    "ansys-mechanical-core": "0.12.11",
}
ALLOWED_PREDECESSOR_STATUSES = {
    "PASS_005_CAPABILITY",
    "PASS_PARTIAL_CAD_CAPABILITY",
}
PROFILE_DEPENDENCY_GIT_PATHS = {
    "ajm005-spaceclaim-cad-t1-v2": (
        "airjet-simulation/automation/ansys/approved/005/spaceclaim_cad_t1.py",
        "airjet-simulation/automation/ansys/contracts/semantic_sidecar_v2_contract.py",
        "airjet-simulation/automation/ansys/contracts/semantic_sidecar_v2.schema.json",
        "airjet-simulation/automation/ansys/contracts/ajm005_semantic_judgment_v2.json",
        "airjet-simulation/automation/ansys/contracts/ajm005_alternate_route_v2.json",
    ),
    "ajm005-workbench-semantic-reconstruction-t1-v2": (
        "airjet-simulation/automation/ansys/approved/005/workbench_semantic_reconstruction_t1.wbjn",
        "airjet-simulation/automation/ansys/contracts/semantic_sidecar_v2_contract.py",
        "airjet-simulation/automation/ansys/contracts/semantic_sidecar_v2.schema.json",
        "airjet-simulation/automation/ansys/contracts/ajm005_semantic_judgment_v2.json",
        "airjet-simulation/automation/ansys/contracts/ajm005_alternate_route_v2.json",
    ),
    "ajm006-spaceclaim-v02-preliminary-v1": (
        "airjet-simulation/automation/ansys/contracts/full_product_semantic_contract_v1.py",
        "airjet-simulation/automation/ansys/contracts/full_product_semantic_sidecar_v1.schema.json",
        "airjet-simulation/automation/ansys/contracts/test_full_product_semantic_contract_v1.py",
        "airjet-simulation/automation/ansys/contracts/build_full_product_trusted_variants.py",
        "airjet-simulation/automation/ansys/contracts/test_full_product_trusted_variants.py",
        "airjet-simulation/parameters/p1_model_form_variants.csv",
        "airjet-simulation/parameters/p1_layout_configuration_matrix.csv",
        "airjet-simulation/parameters/p1_internal_geometry_rules.csv",
        "airjet-simulation/parameters/p1_cad_parameter_map.csv",
        "airjet-simulation/parameters/p1_orifice_pattern_candidates.csv",
        "airjet-simulation/parameters/p1_vent_geometry_candidates.csv",
        "airjet-simulation/parameters/p1_planform_exhaust_candidates.csv",
        "airjet-simulation/parameters/p1_thickness_budget.csv",
        "airjet-simulation/automation/ansys/contracts/trusted_full_product_gen1/campaign.json",
        "airjet-simulation/automation/ansys/contracts/trusted_full_product_gen1/variant_02_m_3x4_7_0_r50_balanced.json",
    ),
    "ajm006-spaceclaim-v03-continuous-throat-pilot-v1": (
        "airjet-simulation/automation/ansys/contracts/full_product_semantic_contract_v1.py",
        "airjet-simulation/automation/ansys/contracts/full_product_semantic_sidecar_v1.schema.json",
        "airjet-simulation/automation/ansys/contracts/test_full_product_semantic_contract_v1.py",
        "airjet-simulation/automation/ansys/contracts/build_full_product_trusted_variants.py",
        "airjet-simulation/automation/ansys/contracts/test_full_product_trusted_variants.py",
        "airjet-simulation/parameters/p1_model_form_variants.csv",
        "airjet-simulation/parameters/p1_layout_configuration_matrix.csv",
        "airjet-simulation/parameters/p1_internal_geometry_rules.csv",
        "airjet-simulation/parameters/p1_cad_parameter_map.csv",
        "airjet-simulation/parameters/p1_orifice_pattern_candidates.csv",
        "airjet-simulation/parameters/p1_vent_geometry_candidates.csv",
        "airjet-simulation/parameters/p1_planform_exhaust_candidates.csv",
        "airjet-simulation/parameters/p1_thickness_budget.csv",
        "airjet-simulation/parameters/full_product_parameter_registry.csv",
        "airjet-simulation/automation/ansys/contracts/v03_finite_throat_route_v1.json",
        "airjet-simulation/automation/ansys/contracts/trusted_full_product_gen1/campaign.json",
        "airjet-simulation/automation/ansys/contracts/trusted_full_product_gen1/variant_02_m_3x4_7_0_r50_balanced.json",
    ),
    "ajm008-spaceclaim-p2-s0-equivalent-plate-v1": (
        "airjet-simulation/automation/ansys/contracts/p2_s0_equivalent_plate_v1.json",
        "airjet-simulation/parameters/p2_s0_equivalent_material_candidates.csv",
        "airjet-simulation/automation/ansys/contracts/trusted_full_product_gen1/variant_02_m_3x4_7_0_r50_balanced.json",
    ),
}
PROFILE_DEPENDENCY_MANIFEST = "dependency-manifest.json"
PROFILE_DEPENDENCY_GIT_PREFIXES = (
    "airjet-simulation/automation/ansys/",
    "airjet-simulation/parameters/",
)


@dataclass
class Job:
    process: subprocess.Popen[bytes]
    stdout: IO[bytes]
    stderr: IO[bytes]
    state_path: Path
    state: dict[str, Any]
    timeout_seconds: int
    job_handle: int | None
    machine_lock_handle: int | None
    reports: tuple[str, ...]
    artifact_snapshot: dict[str, Any] | None = None


JOBS: dict[str, Job] = {}
JOBS_LOCK = threading.RLock()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def lexical(path: Path) -> Path:
    return Path(os.path.abspath(os.path.expanduser(str(path))))


def contained(path: Path, root: Path) -> bool:
    try:
        candidate = os.path.normcase(str(lexical(path)))
        boundary = os.path.normcase(str(lexical(root)))
        return os.path.commonpath((candidate, boundary)) == boundary
    except ValueError:
        return False


def is_reparse_point(path: Path) -> bool:
    try:
        details = path.lstat()
    except FileNotFoundError:
        return False
    return bool(getattr(details, "st_file_attributes", 0) & FILE_ATTRIBUTE_REPARSE_POINT)


def reject_existing_reparse_ancestors(path: Path) -> None:
    current = lexical(path)
    chain = [current, *current.parents]
    for item in reversed(chain):
        if item.exists() and (item.is_symlink() or is_reparse_point(item)):
            raise ValueError("BLOCKED_REPARSE_POINT")


def run_capture(args: list[str], timeout: int = 20) -> dict[str, Any]:
    completed = subprocess.run(
        args,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
        stdin=subprocess.DEVNULL,
    )
    return {
        "exit_code": completed.returncode,
        "stdout": completed.stdout[-8000:],
        "stderr": completed.stderr[-8000:],
    }


def run_bytes(args: list[str], timeout: int = 20) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        args,
        capture_output=True,
        timeout=timeout,
        check=False,
        stdin=subprocess.DEVNULL,
    )


def git_text(*args: str) -> str:
    result = run_capture(["git", "-C", str(REPO), *args])
    if result["exit_code"] != 0:
        raise ValueError(f"BLOCKED_GIT_{args[0].upper().replace('-', '_')}")
    return result["stdout"].strip()


def _git_diff_dirty() -> bool:
    """Return True if the worktree is dirty, ignoring CRLF-only changes."""
    return bool(
        run_capture(["git", "-C", str(REPO), "diff", "--quiet", "--ignore-cr-at-eol", "HEAD"])["exit_code"]
        or run_capture(["git", "-C", str(REPO), "diff", "--quiet", "--ignore-cr-at-eol", "--cached", "HEAD"])["exit_code"]
    )


def require_git_invariants() -> str:
    head = git_text("rev-parse", "HEAD")
    if not re.fullmatch(r"[0-9a-f]{40}", head):
        raise ValueError("BLOCKED_INVALID_GIT_HEAD")
    if git_text("rev-parse", "--abbrev-ref", "HEAD") != "main":
        raise ValueError("BLOCKED_WRONG_BRANCH")
    if git_text("rev-parse", "refs/heads/main") != head:
        raise ValueError("BLOCKED_HEAD_NOT_MAIN")
    if git_text("rev-parse", "refs/remotes/origin/main") != head:
        raise ValueError("BLOCKED_GIT_NOT_SYNCHRONIZED")
    if _git_diff_dirty():
        raise ValueError("BLOCKED_DIRTY_WORKTREE")
    verify = run_capture(["git", "-C", str(REPO), "verify-commit", "--raw", head])
    if verify["exit_code"] != 0:
        raise ValueError("BLOCKED_UNVERIFIED_HEAD_SIGNATURE")
    signature_text = verify["stdout"] + verify["stderr"]
    fingerprints = {
        fingerprint
        for fingerprint in ALLOWED_SIGNER_FINGERPRINTS
        if fingerprint in signature_text
    }
    if len(fingerprints) != 1:
        raise ValueError("BLOCKED_UNAPPROVED_HEAD_SIGNER")
    if git_text("rev-parse", "HEAD") != head:
        raise ValueError("BLOCKED_GIT_HEAD_CHANGED_DURING_VALIDATION")
    installed_server = Path(__file__)
    reject_existing_reparse_ancestors(installed_server)
    if sha256_bytes(installed_server.read_bytes()) != sha256_bytes(
        read_git_blob(head, SERVER_GIT_PATH)
    ):
        raise ValueError("BLOCKED_MCP_SERVER_COPY_MISMATCH")
    return head


def read_git_blob(head: str, relative: str) -> bytes:
    if (
        not re.fullmatch(r"[0-9a-f]{40}", head)
        or not relative
        or relative.startswith(("/", "\\"))
        or ".." in Path(relative).parts
        or ":" in relative
    ):
        raise ValueError("BLOCKED_UNSAFE_GIT_BLOB_PATH")
    result = run_bytes(["git", "-C", str(REPO), "show", f"{head}:{relative}"])
    if result.returncode != 0:
        raise ValueError("BLOCKED_MISSING_GIT_BLOB")
    return result.stdout


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_approved_file(head: str, relative: str, expected_sha256: str) -> bytes:
    git_path = f"{SCRIPT_GIT_ROOT}/{relative}"
    data = read_git_blob(head, git_path)
    if len(data) > MAX_SCRIPT_BYTES:
        raise ValueError("BLOCKED_APPROVED_SCRIPT_TOO_LARGE")
    if sha256_bytes(data) != expected_sha256:
        raise ValueError("BLOCKED_APPROVED_SCRIPT_HASH_MISMATCH")
    return data


def validate_production_contract_policy(head: str, value: Any) -> None:
    """Fail closed on the Gen1-only static 006 contract and trusted campaign."""

    if not isinstance(value, dict) or set(value) != {
        "schema_version", "contract_id", "scope", "product_id",
        "expected_variant_count", "producer_profile_id", "observer_profile_id",
        "execution_state", "p1_p6_gates", "components",
    }:
        raise ValueError("BLOCKED_PRODUCTION_CONTRACT_FIELDS")
    if (
        value.get("schema_version") != 1
        or value.get("contract_id") != "AJM006_GEN1_FULL_PRODUCT_SEMANTIC_PRODUCTION_V1"
        or value.get("scope") != "FULL_PRODUCT"
        or value.get("product_id") != "AIRJET_MINI_GEN1"
        or value.get("expected_variant_count") != 9
        or value.get("producer_profile_id")
        != "ajm006-spaceclaim-full-product-producer-v1"
        or value.get("observer_profile_id")
        != "ajm006-workbench-full-product-observer-v1"
        or value.get("execution_state") != "STATIC_CONTRACT_ONLY_NOT_REGISTERED"
        or value.get("p1_p6_gates") != "NOT_RUN"
    ):
        raise ValueError("BLOCKED_PRODUCTION_CONTRACT_IDENTITY")
    components = value.get("components")
    if not isinstance(components, list):
        raise ValueError("BLOCKED_PRODUCTION_COMPONENTS")
    expected_keys = {
        "full_product_validator", "full_product_schema", "full_product_core_test",
        "trusted_variant_generator", "trusted_variant_test", "trusted_campaign",
    }
    by_key: dict[str, dict[str, str]] = {}
    for item in components:
        if not isinstance(item, dict) or set(item) != {
            "contract_key", "git_path", "sha256",
        }:
            raise ValueError("BLOCKED_PRODUCTION_COMPONENT_FIELDS")
        contract_key = item.get("contract_key")
        git_path = item.get("git_path")
        digest = item.get("sha256")
        if (
            not isinstance(contract_key, str)
            or not re.fullmatch(r"[a-z][a-z0-9_]{0,63}", contract_key)
            or contract_key in by_key
            or not isinstance(git_path, str)
            or not git_path.startswith("airjet-simulation/")
            or "\\" in git_path
            or ".." in Path(git_path).parts
            or not isinstance(digest, str)
            or not SHA256.fullmatch(digest)
            or sha256_bytes(read_git_blob(head, git_path)) != digest
        ):
            raise ValueError("BLOCKED_PRODUCTION_COMPONENT_IDENTITY")
        by_key[contract_key] = item
    if set(by_key) != expected_keys:
        raise ValueError("BLOCKED_PRODUCTION_COMPONENT_SET")
    campaign_item = by_key["trusted_campaign"]
    try:
        campaign = json.loads(
            read_git_blob(head, campaign_item["git_path"]).decode("ascii")
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("BLOCKED_PRODUCTION_CAMPAIGN_JSON") from exc
    if (
        not isinstance(campaign, dict)
        or campaign.get("contract_id")
        != "AIRJET_FULL_PRODUCT_SEMANTIC_CAMPAIGN_V1"
        or campaign.get("scope") != "FULL_PRODUCT"
        or campaign.get("product_id") != "AIRJET_MINI_GEN1"
        or campaign.get("expected_variant_count") != 9
        or not isinstance(campaign.get("variant_contracts"), list)
        or len(campaign["variant_contracts"]) != 9
    ):
        raise ValueError("BLOCKED_PRODUCTION_CAMPAIGN_IDENTITY")
    blueprint_paths: set[str] = set()
    source_variant_ids: set[str] = set()
    for record in campaign["variant_contracts"]:
        if not isinstance(record, dict):
            raise ValueError("BLOCKED_PRODUCTION_VARIANT_RECORD")
        path = record.get("blueprint_path")
        digest = record.get("blueprint_sha256")
        source_variant_id = record.get("source_variant_id")
        if (
            not isinstance(path, str)
            or path in blueprint_paths
            or not path.startswith(
                "airjet-simulation/automation/ansys/contracts/trusted_full_product_gen1/"
            )
            or not isinstance(digest, str)
            or not SHA256.fullmatch(digest)
            or not isinstance(source_variant_id, str)
            or source_variant_id in source_variant_ids
        ):
            raise ValueError("BLOCKED_PRODUCTION_VARIANT_IDENTITY")
        blueprint_blob = read_git_blob(head, path)
        if sha256_bytes(blueprint_blob) != digest:
            raise ValueError("BLOCKED_PRODUCTION_BLUEPRINT_HASH")
        try:
            blueprint = json.loads(blueprint_blob.decode("ascii"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("BLOCKED_PRODUCTION_BLUEPRINT_JSON") from exc
        if (
            blueprint.get("product_id") != "AIRJET_MINI_GEN1"
            or blueprint.get("source_variant_id") != source_variant_id
            or blueprint.get("configuration", {}).get("product_id")
            != "AIRJET_MINI_GEN1"
            or blueprint.get("producer_profile_id") != value["producer_profile_id"]
            or blueprint.get("observer_profile_id") != value["observer_profile_id"]
            or "G2" in json.dumps(blueprint, ensure_ascii=True).upper()
        ):
            raise ValueError("BLOCKED_PRODUCTION_BLUEPRINT_TARGET")
        blueprint_paths.add(path)
        source_variant_ids.add(source_variant_id)
    source_records = campaign.get("source_contracts")
    if not isinstance(source_records, list) or not source_records:
        raise ValueError("BLOCKED_PRODUCTION_CAMPAIGN_SOURCES")
    source_paths: set[str] = set()
    for record in source_records:
        if not isinstance(record, dict):
            raise ValueError("BLOCKED_PRODUCTION_CAMPAIGN_SOURCE")
        path = record.get("git_path")
        digest = record.get("sha256")
        if (
            not isinstance(path, str)
            or path in source_paths
            or not isinstance(digest, str)
            or not SHA256.fullmatch(digest)
            or sha256_bytes(read_git_blob(head, path)) != digest
        ):
            raise ValueError("BLOCKED_PRODUCTION_CAMPAIGN_SOURCE_IDENTITY")
        source_paths.add(path)


def load_profiles(head: str) -> dict[str, dict[str, Any]]:
    try:
        policy = json.loads(read_git_blob(head, POLICY_GIT_PATH).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("BLOCKED_PROFILE_POLICY_INVALID_JSON") from exc
    if not isinstance(policy, dict) or set(policy) != {
        "schema_version", "production_contracts", "profiles",
    }:
        raise ValueError("BLOCKED_PROFILE_POLICY_ROOT")
    if policy.get("schema_version") != 2 or not isinstance(policy.get("profiles"), list):
        raise ValueError("BLOCKED_PROFILE_POLICY_SCHEMA")
    validate_production_contract_policy(head, policy.get("production_contracts"))
    profiles: dict[str, dict[str, Any]] = {}
    for raw in policy.get("profiles", []):
        if not isinstance(raw, dict):
            raise ValueError("BLOCKED_PROFILE_POLICY_ENTRY")
        if set(raw) != {
            "profile_id",
            "engine",
            "script",
            "sha256",
            "timeout_seconds",
            "output_root_id",
            "reports",
            "predecessor",
        }:
            raise ValueError("BLOCKED_PROFILE_POLICY_FIELDS")
        profile_id = raw.get("profile_id")
        engine = raw.get("engine")
        relative = raw.get("script")
        digest = raw.get("sha256")
        output_root_id = raw.get("output_root_id")
        timeout = raw.get("timeout_seconds")
        reports = raw.get("reports", [])
        predecessor = raw.get("predecessor")
        if not isinstance(profile_id, str) or not SAFE_ID.fullmatch(profile_id):
            raise ValueError("BLOCKED_PROFILE_ID")
        if profile_id in profiles:
            raise ValueError("BLOCKED_DUPLICATE_PROFILE_ID")
        if engine not in ENGINE_EXTENSIONS:
            raise ValueError("BLOCKED_PROFILE_ENGINE")
        if (
            not isinstance(relative, str)
            or not relative
            or Path(relative).is_absolute()
            or ":" in relative
            or "\\" in relative
        ):
            raise ValueError("BLOCKED_PROFILE_SCRIPT_PATH")
        relative_path = Path(relative)
        if ".." in relative_path.parts or relative_path.suffix.lower() != ENGINE_EXTENSIONS[engine]:
            raise ValueError("BLOCKED_PROFILE_SCRIPT_PATH")
        if not isinstance(digest, str) or not SHA256.fullmatch(digest):
            raise ValueError("BLOCKED_PROFILE_SCRIPT_HASH")
        if output_root_id not in OUTPUT_ROOTS:
            raise ValueError("BLOCKED_PROFILE_OUTPUT_ROOT")
        if not isinstance(timeout, int) or timeout < 30 or timeout > 7200:
            raise ValueError("BLOCKED_PROFILE_TIMEOUT")
        if not isinstance(reports, list) or len(reports) > 20:
            raise ValueError("BLOCKED_PROFILE_REPORTS")
        for report in reports:
            if (
                not isinstance(report, str)
                or not report
                or Path(report).is_absolute()
                or ".." in Path(report).parts
                or ":" in report
                or "\\" in report
                or not report.endswith(".json")
                or report in {"job.json", "stdout.json", "stderr.json"}
            ):
                raise ValueError("BLOCKED_PROFILE_REPORT_PATH")
        if predecessor is not None:
            if not isinstance(predecessor, dict) or set(predecessor) != {
                "profile_id",
                "report",
                "required_probe",
                "required_status",
                "required_assertions",
                "artifacts",
            }:
                raise ValueError("BLOCKED_PROFILE_PREDECESSOR_FIELDS")
            predecessor_profile = predecessor.get("profile_id")
            predecessor_report = predecessor.get("report")
            required_probe = predecessor.get("required_probe")
            required_status = predecessor.get("required_status")
            required_assertions = predecessor.get("required_assertions")
            predecessor_artifacts = predecessor.get("artifacts")
            if (
                not isinstance(predecessor_profile, str)
                or not SAFE_ID.fullmatch(predecessor_profile)
                or not isinstance(predecessor_report, str)
                or Path(predecessor_report).name != predecessor_report
                or not predecessor_report.endswith(".json")
                or not isinstance(required_probe, str)
                or not SAFE_ID.fullmatch(required_probe)
                or required_status not in ALLOWED_PREDECESSOR_STATUSES
                or not isinstance(required_assertions, list)
                or not required_assertions
                or len(required_assertions) > 50
                or len(required_assertions) != len(set(required_assertions))
                or not isinstance(predecessor_artifacts, list)
                or not predecessor_artifacts
                or len(predecessor_artifacts) > 20
                or predecessor_report not in predecessor_artifacts
            ):
                raise ValueError("BLOCKED_PROFILE_PREDECESSOR_VALUE")
            for assertion in required_assertions:
                if (
                    not isinstance(assertion, str)
                    or not re.fullmatch(r"[a-z][a-z0-9_]{0,79}", assertion)
                ):
                    raise ValueError("BLOCKED_PROFILE_PREDECESSOR_ASSERTION")
            for artifact in predecessor_artifacts:
                if (
                    not isinstance(artifact, str)
                    or not artifact
                    or Path(artifact).name != artifact
                    or artifact.startswith(".")
                    or ":" in artifact
                    or "\\" in artifact
                    or artifact in {"job.json", "stdout.log", "stderr.log"}
                ):
                    raise ValueError("BLOCKED_PROFILE_PREDECESSOR_ARTIFACT")
        profiles[profile_id] = {
            **raw,
            "script_relative": relative_path.as_posix(),
            "reports": reports,
            "profile_contract_sha256": sha256_bytes(
                json.dumps(
                    raw,
                    ensure_ascii=True,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            ),
        }
    if not profiles:
        raise ValueError("BLOCKED_PROFILE_POLICY_EMPTY")
    for profile in profiles.values():
        predecessor = profile["predecessor"]
        if predecessor is None:
            continue
        predecessor_profile = profiles.get(predecessor["profile_id"])
        if predecessor_profile is None:
            raise ValueError("BLOCKED_PROFILE_PREDECESSOR_UNKNOWN")
        if predecessor["report"] not in predecessor_profile["reports"]:
            raise ValueError("BLOCKED_PROFILE_PREDECESSOR_REPORT_UNDECLARED")
        if predecessor_profile["output_root_id"] != profile["output_root_id"]:
            raise ValueError("BLOCKED_PROFILE_PREDECESSOR_OUTPUT_ROOT_MISMATCH")
    return profiles


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "MISSING"


def authenticode_inventory() -> dict[str, dict[str, Any]]:
    paths = {
        "spaceclaim": SPACECLAIM,
        "workbench": RUNWB2,
        "mechanical": MECHANICAL,
        "fluent": ANSYS_ROOT / "fluent" / "ntbin" / "win64" / "fluent.exe",
    }
    quoted = ",".join("'" + str(path).replace("'", "''") + "'" for path in paths.values())
    script = (
        "[Console]::OutputEncoding=[Text.UTF8Encoding]::new();"
        f"$paths=@({quoted});"
        "$rows=@($paths|ForEach-Object{$s=Get-AuthenticodeSignature -LiteralPath $_;"
        "[pscustomobject]@{Path=$_;Status=[string]$s.Status;"
        "Subject=$(if($s.SignerCertificate){[string]$s.SignerCertificate.Subject}else{''});"
        "Version=$([Diagnostics.FileVersionInfo]::GetVersionInfo($_).FileVersion)}});"
        "$rows|ConvertTo-Json -Compress"
    )
    powershell = r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
    result = run_capture(
        [powershell, "-NoProfile", "-NonInteractive", "-Command", script], timeout=30
    )
    if result["exit_code"] != 0:
        raise ValueError("BLOCKED_AUTHENTICODE_QUERY_FAILED")
    try:
        rows = json.loads(result["stdout"])
    except json.JSONDecodeError as exc:
        raise ValueError("BLOCKED_AUTHENTICODE_QUERY_INVALID") from exc
    if isinstance(rows, dict):
        rows = [rows]
    if not isinstance(rows, list) or len(rows) != len(paths):
        raise ValueError("BLOCKED_AUTHENTICODE_QUERY_INCOMPLETE")
    by_path = {os.path.normcase(row.get("Path", "")): row for row in rows if isinstance(row, dict)}
    inventory: dict[str, dict[str, Any]] = {}
    for name, path in paths.items():
        row = by_path.get(os.path.normcase(str(path)), {})
        inventory[name] = {
            "path": str(path),
            "exists": path.is_file(),
            "status": row.get("Status", "MISSING"),
            "publisher_is_ansys": "ANSYS Inc." in row.get("Subject", ""),
            "file_version": row.get("Version", ""),
        }
    return inventory


def require_runtime_readiness() -> dict[str, dict[str, Any]]:
    if os.path.normcase(str(lexical(Path(sys.executable)))) != os.path.normcase(
        str(lexical(VENV_PYTHON))
    ):
        raise ValueError("BLOCKED_WRONG_AUTOMATION_INTERPRETER")
    reject_existing_reparse_ancestors(VENV_PYTHON)
    if not VENV_PYTHON.is_file():
        raise ValueError("BLOCKED_AUTOMATION_PYTHON_MISSING")
    for name, expected in EXPECTED_PACKAGES.items():
        actual = package_version(name)
        if actual != expected:
            raise ValueError(f"BLOCKED_PACKAGE_VERSION:{name}:{actual}:{expected}")
    for executable in (
        SPACECLAIM,
        RUNWB2,
        MECHANICAL,
        ANSYS_ROOT / "fluent" / "ntbin" / "win64" / "fluent.exe",
    ):
        reject_existing_reparse_ancestors(executable)
    signatures = authenticode_inventory()
    for name, item in signatures.items():
        if not item["exists"] or item["status"] != "Valid" or not item["publisher_is_ansys"]:
            raise ValueError(f"BLOCKED_INVALID_ANSYS_EXECUTABLE:{name}")
    return signatures


def write_state(job: Job) -> None:
    write_state_data(job.state_path, job.state)


def write_state_data(state_path: Path, state: dict[str, Any]) -> None:
    temporary = state_path.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(state, indent=2, sort_keys=True), encoding="utf-8"
    )
    temporary.replace(state_path)


def build_command(engine: str, script: Path, job_dir: Path) -> list[str]:
    executable = ENGINE_EXECUTABLES[engine]
    reject_existing_reparse_ancestors(executable)
    if not executable.is_file():
        raise ValueError("BLOCKED_ENGINE_EXECUTABLE_MISSING")
    if engine == "spaceclaim":
        return [
            str(executable),
            f"/RunScript={script}",
            "/ScriptAPI=V261",
            f"/ScriptOutput={job_dir / 'spaceclaim-script-output.log'}",
            "/Headless=True",
            "/ExitAfterScript=True",
        ]
    if engine == "workbench":
        return [str(executable), "-B", "-R", str(script)]
    return [str(executable), "-I", "-B", str(script)]


def sanitized_environment(
    job_dir: Path,
    profile_id: str,
    case_id: str,
    predecessor_dir: Path | None,
    profile_dependency_dir: Path | None,
    git_head: str,
    script_sha256: str,
    profile_contract_sha256: str,
) -> dict[str, str]:
    temporary = job_dir / "temp"
    temporary.mkdir()
    environment = {
        "SystemRoot": r"C:\Windows",
        "WINDIR": r"C:\Windows",
        "COMSPEC": r"C:\Windows\System32\cmd.exe",
        # Fluent's CAD import bridge rejects a missing architecture variable.
        # Keep this commit-bound and fail-closed instead of inheriting caller
        # environment state; this automation route is pinned to Win64 v261.
        "PROCESSOR_ARCHITECTURE": "AMD64",
        # All audited ANSYS jobs run on this host.  Pin PyFluent remoting to
        # loopback so its automatic address inference cannot block before the
        # Fluent subprocess is created.
        "REMOTING_SERVER_ADDRESS": "127.0.0.1",
        "PATH": ";".join(
            (
                str(VENV_PYTHON.parent),
                str(ANSYS_ROOT / "Framework" / "bin" / "Win64"),
                str(ANSYS_ROOT / "fluent" / "ntbin" / "win64"),
                r"C:\Windows\System32",
                r"C:\Windows",
            )
        ),
        "PATHEXT": ".COM;.EXE;.BAT;.CMD",
        "USERPROFILE": r"C:\Users\admin",
        # Python's getpass.getuser() falls back to the Unix-only pwd module
        # when all login-name variables are absent.  Fluent's CAD bridge calls
        # that path, so pin the already audited Windows service account.
        "USERNAME": "admin",
        "HOMEDRIVE": "C:",
        "HOMEPATH": r"\Users\admin",
        "APPDATA": r"C:\Users\admin\AppData\Roaming",
        "LOCALAPPDATA": r"C:\Users\admin\AppData\Local",
        "AWP_ROOT261": str(ANSYS_ROOT),
        "AIRJET_JOB_DIR": str(job_dir),
        "AIRJET_PROFILE_ID": profile_id,
        "AIRJET_CASE_ID": case_id,
        "AIRJET_REPO_ROOT": str(REPO),
        "AIRJET_GIT_HEAD": git_head,
        "AIRJET_SCRIPT_SHA256": script_sha256,
        "AIRJET_PROFILE_CONTRACT_SHA256": profile_contract_sha256,
        "TEMP": str(temporary),
        "TMP": str(temporary),
    }
    if predecessor_dir is not None:
        environment["AIRJET_PREDECESSOR_DIR"] = str(predecessor_dir)
    if profile_dependency_dir is not None:
        environment["AIRJET_PROFILE_DEPENDENCY_DIR"] = str(
            profile_dependency_dir
        )
    return environment


def create_windows_job_object(process: subprocess.Popen[bytes]) -> int | None:
    if os.name != "nt":
        return None

    class BasicLimitInformation(ctypes.Structure):
        _fields_ = [
            ("PerProcessUserTimeLimit", ctypes.c_longlong),
            ("PerJobUserTimeLimit", ctypes.c_longlong),
            ("LimitFlags", ctypes.c_uint32),
            ("MinimumWorkingSetSize", ctypes.c_size_t),
            ("MaximumWorkingSetSize", ctypes.c_size_t),
            ("ActiveProcessLimit", ctypes.c_uint32),
            ("Affinity", ctypes.c_size_t),
            ("PriorityClass", ctypes.c_uint32),
            ("SchedulingClass", ctypes.c_uint32),
        ]

    class IoCounters(ctypes.Structure):
        _fields_ = [
            ("ReadOperationCount", ctypes.c_uint64),
            ("WriteOperationCount", ctypes.c_uint64),
            ("OtherOperationCount", ctypes.c_uint64),
            ("ReadTransferCount", ctypes.c_uint64),
            ("WriteTransferCount", ctypes.c_uint64),
            ("OtherTransferCount", ctypes.c_uint64),
        ]

    class ExtendedLimitInformation(ctypes.Structure):
        _fields_ = [
            ("BasicLimitInformation", BasicLimitInformation),
            ("IoInfo", IoCounters),
            ("ProcessMemoryLimit", ctypes.c_size_t),
            ("JobMemoryLimit", ctypes.c_size_t),
            ("PeakProcessMemoryUsed", ctypes.c_size_t),
            ("PeakJobMemoryUsed", ctypes.c_size_t),
        ]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateJobObjectW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p]
    kernel32.CreateJobObjectW.restype = ctypes.c_void_p
    kernel32.SetInformationJobObject.argtypes = [
        ctypes.c_void_p,
        ctypes.c_int,
        ctypes.c_void_p,
        ctypes.c_uint32,
    ]
    kernel32.AssignProcessToJobObject.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    kernel32.AssignProcessToJobObject.restype = ctypes.c_int
    kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
    kernel32.CloseHandle.restype = ctypes.c_int
    handle = kernel32.CreateJobObjectW(None, None)
    if not handle:
        raise OSError(ctypes.get_last_error(), "CreateJobObjectW failed")
    information = ExtendedLimitInformation()
    information.BasicLimitInformation.LimitFlags = 0x00002000
    if not kernel32.SetInformationJobObject(
        handle, 9, ctypes.byref(information), ctypes.sizeof(information)
    ):
        error = ctypes.get_last_error()
        kernel32.CloseHandle(handle)
        raise OSError(error, "SetInformationJobObject failed")
    if not kernel32.AssignProcessToJobObject(handle, ctypes.c_void_p(process._handle)):
        error = ctypes.get_last_error()
        kernel32.CloseHandle(handle)
        raise OSError(error, "AssignProcessToJobObject failed")
    return int(handle)


def acquire_machine_job_lock() -> int | None:
    if os.name != "nt":
        return None
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateEventW.argtypes = [
        ctypes.c_void_p,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_wchar_p,
    ]
    kernel32.CreateEventW.restype = ctypes.c_void_p
    ctypes.set_last_error(0)
    handle = kernel32.CreateEventW(None, 1, 0, MACHINE_JOB_LOCK_NAME)
    if not handle:
        raise OSError(ctypes.get_last_error(), "CreateEventW failed")
    if ctypes.get_last_error() == ERROR_ALREADY_EXISTS:
        close_windows_handle(int(handle))
        raise ValueError("BLOCKED_ONE_JOB_AT_A_TIME_CROSS_PROCESS")
    return int(handle)


def resume_windows_process(process: subprocess.Popen[bytes]) -> None:
    if os.name != "nt":
        return
    ntdll = ctypes.WinDLL("ntdll", use_last_error=True)
    ntdll.NtResumeProcess.argtypes = [ctypes.c_void_p]
    ntdll.NtResumeProcess.restype = ctypes.c_long
    status = ntdll.NtResumeProcess(ctypes.c_void_p(process._handle))
    if status != 0:
        raise OSError(status, "NtResumeProcess failed")


def active_job_processes(handle: int | None) -> int:
    if not handle or os.name != "nt":
        return 0

    class BasicAccountingInformation(ctypes.Structure):
        _fields_ = [
            ("TotalUserTime", ctypes.c_longlong),
            ("TotalKernelTime", ctypes.c_longlong),
            ("ThisPeriodTotalUserTime", ctypes.c_longlong),
            ("ThisPeriodTotalKernelTime", ctypes.c_longlong),
            ("TotalPageFaultCount", ctypes.c_uint32),
            ("TotalProcesses", ctypes.c_uint32),
            ("ActiveProcesses", ctypes.c_uint32),
            ("TotalTerminatedProcesses", ctypes.c_uint32),
        ]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.QueryInformationJobObject.argtypes = [
        ctypes.c_void_p,
        ctypes.c_int,
        ctypes.c_void_p,
        ctypes.c_uint32,
        ctypes.c_void_p,
    ]
    kernel32.QueryInformationJobObject.restype = ctypes.c_int
    information = BasicAccountingInformation()
    if not kernel32.QueryInformationJobObject(
        ctypes.c_void_p(handle),
        1,
        ctypes.byref(information),
        ctypes.sizeof(information),
        None,
    ):
        raise OSError(ctypes.get_last_error(), "QueryInformationJobObject failed")
    return int(information.ActiveProcesses)


def terminate_windows_job(handle: int | None) -> None:
    if not handle or os.name != "nt":
        return
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.TerminateJobObject.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
    kernel32.TerminateJobObject.restype = ctypes.c_int
    if not kernel32.TerminateJobObject(ctypes.c_void_p(handle), 1):
        raise OSError(ctypes.get_last_error(), "TerminateJobObject failed")


def close_windows_handle(handle: int | None) -> None:
    if not handle or os.name != "nt":
        return
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
    kernel32.CloseHandle.restype = ctypes.c_int
    if not kernel32.CloseHandle(ctypes.c_void_p(handle)):
        raise OSError(ctypes.get_last_error(), "CloseHandle failed")


def finish_job_locked(
    job: Job, phase: str, exit_code: int | None, reason: str | None = None
) -> None:
    if job.state["phase"] != "RUNNING":
        return
    job.stdout.close()
    job.stderr.close()
    try:
        close_windows_handle(job.job_handle)
    except OSError as exc:
        reason = f"{reason or ''};JOB_HANDLE_CLOSE_FAILED:{exc.winerror or exc.errno}".strip(";")
    job.job_handle = None
    try:
        close_windows_handle(job.machine_lock_handle)
    except OSError as exc:
        reason = (
            f"{reason or ''};MACHINE_LOCK_CLOSE_FAILED:{exc.winerror or exc.errno}"
        ).strip(";")
    job.machine_lock_handle = None
    job.state["phase"] = phase
    job.state["exit_code"] = exit_code
    job.state["ended_at"] = utc_now()
    job.state["reason"] = reason
    write_state(job)


def terminate_job_locked(job: Job, phase: str, reason: str) -> None:
    if job.state["phase"] != "RUNNING":
        return
    termination_error = None
    try:
        if job.job_handle:
            terminate_windows_job(job.job_handle)
        else:
            job.process.kill()
    except OSError as exc:
        termination_error = f"TERMINATE_FAILED:{exc.winerror or exc.errno}"
    deadline = time.monotonic() + 15.0
    while time.monotonic() < deadline:
        try:
            active = active_job_processes(job.job_handle)
        except OSError:
            active = 1
        if active == 0:
            break
        time.sleep(0.1)
    try:
        exit_code = job.process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        try:
            job.process.kill()
            exit_code = job.process.wait(timeout=2)
        except (OSError, subprocess.TimeoutExpired):
            exit_code = None
            termination_error = termination_error or "PROCESS_TREE_STILL_ACTIVE"
    final_reason = ";".join(part for part in (reason, termination_error) if part)
    final_phase = phase if not termination_error else "FAILED_TERMINATION"
    finish_job_locked(job, final_phase, exit_code, final_reason)


def poll_internal_locked(job: Job) -> None:
    if job.state["phase"] != "RUNNING":
        return
    exit_code = job.process.poll()
    try:
        active = active_job_processes(job.job_handle)
    except OSError as exc:
        terminate_job_locked(job, "FAILED_MONITOR", f"JOB_QUERY_FAILED:{exc.winerror or exc.errno}")
        return
    if exit_code is not None and active == 0:
        finish_job_locked(
            job,
            "PROCESS_EXITED_0" if exit_code == 0 else "FAILED_PROCESS",
            exit_code,
        )


def watch_job(job_id: str) -> None:
    deadline = None
    while True:
        with JOBS_LOCK:
            job = JOBS.get(job_id)
            if job is None or job.state["phase"] != "RUNNING":
                return
            if deadline is None:
                deadline = time.monotonic() + job.timeout_seconds
            poll_internal_locked(job)
            if job.state["phase"] != "RUNNING":
                return
            if time.monotonic() >= deadline:
                terminate_job_locked(job, "TIMED_OUT", "PROFILE_TIMEOUT")
                return
        time.sleep(0.25)


@MCP.tool()
def inventory() -> dict[str, Any]:
    """Return ANSYS, profile, package, and Git readiness without querying licenses."""
    errors: list[str] = []
    head = None
    signatures: dict[str, dict[str, Any]] = {}
    packages = {name: package_version(name) for name in EXPECTED_PACKAGES}
    try:
        reject_existing_reparse_ancestors(REPO)
        head = require_git_invariants()
        profiles = load_profiles(head)
        for profile in profiles.values():
            read_approved_file(head, profile["script_relative"], profile["sha256"])
            executable = ENGINE_EXECUTABLES[profile["engine"]]
            reject_existing_reparse_ancestors(executable)
            if not executable.is_file():
                errors.append(f"BLOCKED_ENGINE_EXECUTABLE_MISSING:{profile['engine']}")
        signatures = require_runtime_readiness()
    except (OSError, ValueError) as exc:
        errors.append(str(exc))
        profiles = {}
    for name, expected in EXPECTED_PACKAGES.items():
        if packages[name] != expected:
            errors.append(f"BLOCKED_PACKAGE_VERSION:{name}:{packages[name]}:{expected}")
    return {
        "schema_version": 2,
        "ready": not errors,
        "errors": errors,
        "repo": str(REPO),
        "git_head": head,
        "ansys_root": str(ANSYS_ROOT),
        "executables": signatures,
        "automation_python": {"path": str(VENV_PYTHON), "exists": VENV_PYTHON.is_file()},
        "packages": packages,
        "approved_profiles": sorted(profiles),
        "profile_contract_sha256": {
            profile_id: profile["profile_contract_sha256"]
            for profile_id, profile in sorted(profiles.items())
        },
        "license_data_read": False,
    }


def prepare_profile_dependencies(
    profile_id: str, git_head: str, input_dir: Path
) -> tuple[Path | None, list[dict[str, Any]], str | None]:
    """Freeze the fixed v2 dependency bundle from the same verified Git commit."""
    git_paths = PROFILE_DEPENDENCY_GIT_PATHS.get(profile_id)
    if git_paths is None:
        return None, [], None
    if not git_paths or len(git_paths) != len(set(git_paths)):
        raise ValueError("BLOCKED_PROFILE_DEPENDENCY_CONFIGURATION")

    relative_names = tuple(Path(git_path).name for git_path in git_paths)
    if (
        len(relative_names) != len(set(relative_names))
        or PROFILE_DEPENDENCY_MANIFEST in relative_names
    ):
        raise ValueError("BLOCKED_PROFILE_DEPENDENCY_CONFIGURATION")
    for git_path, relative_name in zip(git_paths, relative_names):
        path = Path(git_path)
        if (
            path.is_absolute()
            or ".." in path.parts
            or ":" in git_path
            or "\\" in git_path
            or path.name != relative_name
            or not any(
                git_path.startswith(prefix)
                for prefix in PROFILE_DEPENDENCY_GIT_PREFIXES
            )
        ):
            raise ValueError("BLOCKED_PROFILE_DEPENDENCY_CONFIGURATION")

    reject_existing_reparse_ancestors(input_dir)
    dependency_dir = input_dir / "dependencies"
    if dependency_dir.exists():
        raise ValueError("BLOCKED_PROFILE_DEPENDENCY_EXTRA")
    dependency_dir.mkdir()
    reject_existing_reparse_ancestors(dependency_dir)

    copied: list[dict[str, Any]] = []
    expected_files: set[str] = set()
    for git_path, relative_name in zip(git_paths, relative_names):
        try:
            source_data = read_git_blob(git_head, git_path)
        except ValueError as exc:
            raise ValueError("BLOCKED_PROFILE_DEPENDENCY_MISSING") from exc
        if len(source_data) > MAX_PROFILE_DEPENDENCY_BYTES:
            raise ValueError("BLOCKED_PROFILE_DEPENDENCY_TOO_LARGE")

        target = dependency_dir / relative_name
        if (
            not contained(target, dependency_dir)
            or target.exists()
            or relative_name in expected_files
        ):
            raise ValueError("BLOCKED_PROFILE_DEPENDENCY_EXTRA")
        target.write_bytes(source_data)
        reject_existing_reparse_ancestors(target)
        target_size, target_sha256 = hash_file(target)
        source_sha256 = sha256_bytes(source_data)
        if target_size != len(source_data) or target_sha256 != source_sha256:
            raise ValueError("BLOCKED_PROFILE_DEPENDENCY_COPY_HASH_MISMATCH")
        target.chmod(stat.S_IREAD)
        expected_files.add(relative_name)
        copied.append(
            {
                "git_path": git_path,
                "relative_path": relative_name,
                "size": target_size,
                "sha256": target_sha256,
            }
        )

    observed_before_manifest = set()
    for item in dependency_dir.iterdir():
        reject_existing_reparse_ancestors(item)
        if not item.is_file():
            raise ValueError("BLOCKED_PROFILE_DEPENDENCY_EXTRA")
        observed_before_manifest.add(item.name)
    if observed_before_manifest != expected_files:
        raise ValueError("BLOCKED_PROFILE_DEPENDENCY_EXTRA")

    dependency_manifest = {
        "schema_version": 1,
        "profile_id": profile_id,
        "git_head": git_head,
        "artifacts": copied,
    }
    manifest_bytes = json.dumps(
        dependency_manifest, indent=2, sort_keys=True
    ).encode("utf-8")
    manifest_path = dependency_dir / PROFILE_DEPENDENCY_MANIFEST
    manifest_path.write_bytes(manifest_bytes)
    reject_existing_reparse_ancestors(manifest_path)
    manifest_size, manifest_sha256 = hash_file(manifest_path)
    if (
        manifest_size != len(manifest_bytes)
        or manifest_sha256 != sha256_bytes(manifest_bytes)
    ):
        raise ValueError("BLOCKED_PROFILE_DEPENDENCY_MANIFEST_HASH_MISMATCH")
    manifest_path.chmod(stat.S_IREAD)

    observed_after_manifest = set()
    for item in dependency_dir.iterdir():
        reject_existing_reparse_ancestors(item)
        if not item.is_file():
            raise ValueError("BLOCKED_PROFILE_DEPENDENCY_EXTRA")
        observed_after_manifest.add(item.name)
    if observed_after_manifest != expected_files | {PROFILE_DEPENDENCY_MANIFEST}:
        raise ValueError("BLOCKED_PROFILE_DEPENDENCY_EXTRA")
    for artifact in copied:
        target = dependency_dir / artifact["relative_path"]
        reject_existing_reparse_ancestors(target)
        target_size, target_sha256 = hash_file(target)
        if (
            target_size != artifact["size"]
            or target_sha256 != artifact["sha256"]
        ):
            raise ValueError("BLOCKED_PROFILE_DEPENDENCY_COPY_HASH_MISMATCH")
    return dependency_dir, copied, manifest_sha256


def prepare_predecessor_input(
    profile: dict[str, Any],
    predecessor_job_id: str,
    case_id: str,
    git_head: str,
    input_dir: Path,
) -> tuple[Path | None, list[dict[str, Any]]]:
    """Copy only policy-declared artifacts from one terminal in-memory predecessor."""
    policy = profile["predecessor"]
    if policy is None:
        if predecessor_job_id:
            raise ValueError("BLOCKED_UNEXPECTED_PREDECESSOR")
        return None, []
    if not predecessor_job_id or not SAFE_ID.fullmatch(predecessor_job_id):
        raise ValueError("BLOCKED_REQUIRED_PREDECESSOR_ID")
    predecessor = JOBS.get(predecessor_job_id)
    if predecessor is None:
        raise ValueError("BLOCKED_UNKNOWN_OR_SERVER_RESTARTED_PREDECESSOR")
    poll_internal_locked(predecessor)
    state = predecessor.state
    if state["phase"] != "PROCESS_EXITED_0" or state.get("exit_code") != 0:
        raise ValueError("BLOCKED_PREDECESSOR_NOT_SUCCESSFULLY_TERMINAL")
    if (
        state.get("job_id") != predecessor_job_id
        or state.get("case_id") != case_id
        or state.get("profile_id") != policy["profile_id"]
        or state.get("git_head") != git_head
        or state.get("output_root_id") != profile["output_root_id"]
    ):
        raise ValueError("BLOCKED_PREDECESSOR_IDENTITY_MISMATCH")

    snapshot = predecessor.artifact_snapshot
    if snapshot is None:
        raise ValueError("BLOCKED_PREDECESSOR_MANIFEST_NOT_FROZEN")
    snapshot_files = snapshot.get("files")
    if not isinstance(snapshot_files, list):
        raise ValueError("BLOCKED_PREDECESSOR_MANIFEST_INVALID")
    snapshot_by_relative: dict[str, dict[str, Any]] = {}
    for entry in snapshot_files:
        if not isinstance(entry, dict) or not isinstance(entry.get("relative_path"), str):
            raise ValueError("BLOCKED_PREDECESSOR_MANIFEST_INVALID")
        relative = entry["relative_path"]
        if relative in snapshot_by_relative:
            raise ValueError("BLOCKED_PREDECESSOR_MANIFEST_DUPLICATE")
        snapshot_by_relative[relative] = entry

    source_root = lexical(predecessor.state_path.parent)
    reject_existing_reparse_ancestors(source_root)
    report_path = source_root / policy["report"]
    if not contained(report_path, source_root) or not report_path.is_file():
        raise ValueError("BLOCKED_PREDECESSOR_REPORT_MISSING")
    reject_existing_reparse_ancestors(report_path)
    report_entry = snapshot_by_relative.get(policy["report"])
    report = report_entry.get("report_json") if report_entry else None
    assertions = report.get("assertions") if isinstance(report, dict) else None
    if (
        not isinstance(report, dict)
        or report.get("probe") != policy["required_probe"]
        or report.get("status") != policy["required_status"]
        or report.get("engineering_capability") != policy["required_status"]
        or report.get("p1_stage_gate") != "NOT_RUN"
        or report.get("license_arguments_added") is not False
        or not isinstance(assertions, dict)
        or not all(assertions.get(name) is True for name in policy["required_assertions"])
    ):
        raise ValueError("BLOCKED_PREDECESSOR_REPORT_NOT_CAPABILITY_PASS")

    predecessor_dir = input_dir / "predecessor"
    predecessor_dir.mkdir()
    reject_existing_reparse_ancestors(predecessor_dir)
    copied: list[dict[str, Any]] = []
    for relative in policy["artifacts"]:
        source = source_root / relative
        target = predecessor_dir / relative
        frozen = snapshot_by_relative.get(relative)
        if (
            not contained(source, source_root)
            or not contained(target, predecessor_dir)
            or not source.is_file()
            or not isinstance(frozen, dict)
        ):
            raise ValueError("BLOCKED_PREDECESSOR_ARTIFACT_MISSING")
        reject_existing_reparse_ancestors(source)
        source_size, source_sha256 = hash_file(source)
        if (
            frozen.get("size") != source_size
            or frozen.get("sha256") != source_sha256
        ):
            raise ValueError("BLOCKED_PREDECESSOR_FROZEN_HASH_MISMATCH")
        shutil.copyfile(source, target)
        reject_existing_reparse_ancestors(target)
        target_size, target_sha256 = hash_file(target)
        if target_size != source_size or target_sha256 != source_sha256:
            raise ValueError("BLOCKED_PREDECESSOR_COPY_HASH_MISMATCH")
        target.chmod(stat.S_IREAD)
        copied.append(
            {
                "relative_path": relative,
                "size": target_size,
                "sha256": target_sha256,
            }
        )
    predecessor_manifest = {
        "schema_version": 1,
        "predecessor_job_id": predecessor_job_id,
        "predecessor_profile_id": state["profile_id"],
        "git_head": git_head,
        "required_report": policy["report"],
        "required_status": policy["required_status"],
        "predecessor_script_sha256": state["script_sha256"],
        "predecessor_profile_contract_sha256": state[
            "profile_contract_sha256"
        ],
        "artifact_manifest_snapshot_sha256": sha256_bytes(
            json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ),
        "artifacts": copied,
    }
    manifest_path = predecessor_dir / "predecessor-manifest.json"
    manifest_path.write_text(
        json.dumps(predecessor_manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    manifest_path.chmod(stat.S_IREAD)
    return predecessor_dir, copied


@MCP.tool()
def submit_job(
    profile_id: str, case_id: str, predecessor_job_id: str = ""
) -> dict[str, Any]:
    """Start one hash-pinned profile with an optional policy-bound predecessor job."""
    if (
        not SAFE_ID.fullmatch(profile_id)
        or not SAFE_ID.fullmatch(case_id)
        or (predecessor_job_id and not SAFE_ID.fullmatch(predecessor_job_id))
    ):
        raise ValueError("BLOCKED_INVALID_ID")
    with JOBS_LOCK:
        for active in JOBS.values():
            poll_internal_locked(active)
            if active.state["phase"] == "RUNNING":
                raise ValueError("BLOCKED_ONE_JOB_AT_A_TIME")

        git_head = require_git_invariants()
        profiles = load_profiles(git_head)
        if profile_id not in profiles:
            raise ValueError("BLOCKED_UNKNOWN_PROFILE")
        profile = profiles[profile_id]
        require_runtime_readiness()
        source_data = read_approved_file(
            git_head, profile["script_relative"], profile["sha256"]
        )

        output_root = lexical(OUTPUT_ROOTS[profile["output_root_id"]])
        reject_existing_reparse_ancestors(output_root)
        output_root.mkdir(parents=True, exist_ok=True)
        reject_existing_reparse_ancestors(output_root)
        job_id = f"{case_id}-{uuid4().hex[:12]}"
        job_dir = output_root / case_id / job_id
        if not contained(job_dir, output_root):
            raise ValueError("BLOCKED_OUTPUT_OUTSIDE_APPROVED_ROOT")
        job_dir.mkdir(parents=True, exist_ok=False)
        reject_existing_reparse_ancestors(job_dir)
        state_path = job_dir / "job.json"
        state: dict[str, Any] = {
            "schema_version": 4,
            "job_id": job_id,
            "case_id": case_id,
            "profile_id": profile_id,
            "engine": profile["engine"],
            "script_sha256": profile["sha256"],
            "profile_contract_sha256": profile["profile_contract_sha256"],
            "git_head": git_head,
            "output_root_id": profile["output_root_id"],
            "job_directory": str(job_dir),
            "pid": None,
            "phase": "PREPARING",
            "exit_code": None,
            "started_at": utc_now(),
            "ended_at": None,
            "reason": None,
            "license_arguments_added": False,
            "predecessor_job_id": predecessor_job_id or None,
            "predecessor_artifacts": [],
            "profile_dependency_artifacts": [],
            "profile_dependency_manifest_sha256": None,
        }
        write_state_data(state_path, state)
        try:
            input_dir = job_dir / "input"
            input_dir.mkdir()
            execution_script = input_dir / Path(profile["script_relative"]).name
            execution_script.write_bytes(source_data)
            if sha256_bytes(execution_script.read_bytes()) != profile["sha256"]:
                raise ValueError("BLOCKED_EXECUTION_COPY_HASH_MISMATCH")
            execution_script.chmod(stat.S_IREAD)
            reject_existing_reparse_ancestors(execution_script)
            (
                profile_dependency_dir,
                profile_dependency_artifacts,
                profile_dependency_manifest_sha256,
            ) = prepare_profile_dependencies(profile_id, git_head, input_dir)
            state["profile_dependency_artifacts"] = profile_dependency_artifacts
            state["profile_dependency_manifest_sha256"] = (
                profile_dependency_manifest_sha256
            )
            predecessor_dir, predecessor_artifacts = prepare_predecessor_input(
                profile,
                predecessor_job_id,
                case_id,
                git_head,
                input_dir,
            )
            state["predecessor_artifacts"] = predecessor_artifacts
            command = build_command(profile["engine"], execution_script, job_dir)
            write_state_data(state_path, state)
        except Exception as exc:
            state["phase"] = "FAILED_START"
            state["ended_at"] = utc_now()
            state["reason"] = f"PREPARATION_FAILED:{type(exc).__name__}:{exc}"
            write_state_data(state_path, state)
            raise

        stdout_path = job_dir / "stdout.log"
        stderr_path = job_dir / "stderr.log"
        creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        if os.name == "nt":
            creationflags |= 0x00000004  # CREATE_SUSPENDED
        try:
            machine_lock_handle = acquire_machine_job_lock()
        except Exception as exc:
            state["phase"] = "FAILED_START"
            state["ended_at"] = utc_now()
            state["reason"] = (
                f"MACHINE_LOCK_ACQUIRE_FAILED:{type(exc).__name__}:{exc}"
            )
            write_state_data(state_path, state)
            raise
        stdout: IO[bytes] | None = None
        stderr: IO[bytes] | None = None
        process: subprocess.Popen[bytes] | None = None
        job_handle: int | None = None
        try:
            stdout = stdout_path.open("wb")
            stderr = stderr_path.open("wb")
            process = subprocess.Popen(
                command,
                cwd=job_dir,
                env=sanitized_environment(
                    job_dir,
                    profile_id,
                    case_id,
                    predecessor_dir,
                    profile_dependency_dir,
                    git_head,
                    profile["sha256"],
                    profile["profile_contract_sha256"],
                ),
                stdin=subprocess.DEVNULL,
                stdout=stdout,
                stderr=stderr,
                creationflags=creationflags,
                shell=False,
            )
            job_handle = create_windows_job_object(process)
            resume_windows_process(process)
        except Exception:
            if job_handle:
                try:
                    terminate_windows_job(job_handle)
                except OSError:
                    pass
                try:
                    close_windows_handle(job_handle)
                except OSError:
                    pass
            if process is not None:
                try:
                    process.kill()
                    process.wait(timeout=5)
                except (OSError, subprocess.TimeoutExpired):
                    pass
            if stdout is not None:
                stdout.close()
            if stderr is not None:
                stderr.close()
            try:
                close_windows_handle(machine_lock_handle)
            except OSError:
                pass
            state["phase"] = "FAILED_START"
            state["ended_at"] = utc_now()
            state["reason"] = "PROCESS_START_OR_JOB_ASSIGN_FAILED"
            write_state_data(state_path, state)
            raise

        if stdout is None or stderr is None:
            raise RuntimeError("BLOCKED_INTERNAL_LOG_HANDLE_MISSING")
        state["pid"] = process.pid
        state["phase"] = "RUNNING"
        job = Job(
            process=process,
            stdout=stdout,
            stderr=stderr,
            state_path=state_path,
            state=state,
            timeout_seconds=profile["timeout_seconds"],
            job_handle=job_handle,
            machine_lock_handle=machine_lock_handle,
            reports=tuple(profile["reports"]),
        )
        JOBS[job_id] = job
        try:
            write_state(job)
            watcher = threading.Thread(
                target=watch_job,
                args=(job_id,),
                name=f"airjet-ansys-{job_id}",
                daemon=True,
            )
            watcher.start()
        except Exception:
            terminate_job_locked(job, "FAILED_START", "STATE_OR_WATCHDOG_START_FAILED")
            raise
        return dict(state)


@MCP.tool()
def poll_job(job_id: str) -> dict[str, Any]:
    """Poll a job created by this server and enforce its profile timeout."""
    with JOBS_LOCK:
        if job_id not in JOBS:
            raise ValueError("BLOCKED_UNKNOWN_OR_SERVER_RESTARTED_JOB")
        job = JOBS[job_id]
        poll_internal_locked(job)
        return dict(job.state)


@MCP.tool()
def cancel_job(job_id: str) -> dict[str, Any]:
    """Cancel only a running job created by this MCP server."""
    with JOBS_LOCK:
        if job_id not in JOBS:
            raise ValueError("BLOCKED_UNKNOWN_OR_SERVER_RESTARTED_JOB")
        job = JOBS[job_id]
        poll_internal_locked(job)
        if job.state["phase"] == "RUNNING":
            terminate_job_locked(job, "CANCELLED", "REQUESTED_CANCEL")
        return dict(job.state)


def hash_file(path: Path) -> tuple[int, str]:
    size = os.stat(path, follow_symlinks=False).st_size
    if size > MAX_ARTIFACT_BYTES:
        raise ValueError("BLOCKED_ARTIFACT_FILE_TOO_LARGE")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return size, digest.hexdigest()


def walk_artifacts(root: Path) -> list[Path]:
    files: list[Path] = []
    for current_text, directories, names in os.walk(root, topdown=True, followlinks=False):
        current = Path(current_text)
        reject_existing_reparse_ancestors(current)
        directories.sort()
        names.sort()
        for directory in directories:
            candidate = current / directory
            if candidate.is_symlink() or is_reparse_point(candidate):
                raise ValueError("BLOCKED_ARTIFACT_REPARSE_POINT")
        for name in names:
            candidate = current / name
            if candidate.is_symlink() or is_reparse_point(candidate):
                raise ValueError("BLOCKED_ARTIFACT_REPARSE_POINT")
            details = os.stat(candidate, follow_symlinks=False)
            if not stat.S_ISREG(details.st_mode):
                raise ValueError("BLOCKED_NONREGULAR_ARTIFACT")
            files.append(candidate)
            if len(files) > MAX_ARTIFACTS:
                raise ValueError("BLOCKED_MANIFEST_TOO_MANY_FILES")
    return files


def build_artifact_snapshot(job: Job) -> dict[str, Any]:
    """Build the immutable in-memory manifest used by callers and successors."""
    job_dir = job.state_path.parent
    reject_existing_reparse_ancestors(job_dir)
    declared_reports = set(job.reports)
    entries: list[dict[str, Any]] = []
    total_size = 0
    for path in walk_artifacts(job_dir):
        if not contained(path, job_dir):
            raise ValueError("BLOCKED_ARTIFACT_OUTSIDE_JOB")
        relative = path.relative_to(job_dir).as_posix()
        if relative in declared_reports:
            with path.open("rb") as handle:
                report_bytes = handle.read(MAX_INLINE_REPORT_BYTES + 1)
            if len(report_bytes) > MAX_INLINE_REPORT_BYTES:
                raise ValueError("BLOCKED_DECLARED_REPORT_TOO_LARGE")
            size = len(report_bytes)
            digest = sha256_bytes(report_bytes)
        else:
            report_bytes = None
            size, digest = hash_file(path)
        total_size += size
        if total_size > MAX_TOTAL_ARTIFACT_BYTES:
            raise ValueError("BLOCKED_ARTIFACT_TOTAL_TOO_LARGE")
        entry: dict[str, Any] = {
            "relative_path": relative,
            "size": size,
            "sha256": digest,
        }
        if relative in declared_reports:
            try:
                report = json.loads(report_bytes.decode("utf-8"))
                if not isinstance(report, dict):
                    raise ValueError
                entry["report_json"] = report
            except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
                entry["report_error"] = "DECLARED_REPORT_INVALID_JSON"
        entries.append(entry)
    return {
        "job_id": job.state["job_id"],
        "phase": job.state["phase"],
        "file_count": len(entries),
        "total_size": total_size,
        "files": entries,
    }


@MCP.tool()
def artifact_manifest(job_id: str) -> dict[str, Any]:
    """Hash one known job directory and inline only profile-declared small reports."""
    with JOBS_LOCK:
        if job_id not in JOBS:
            raise ValueError("BLOCKED_UNKNOWN_OR_SERVER_RESTARTED_JOB")
        job = JOBS[job_id]
        poll_internal_locked(job)
        if job.state["phase"] == "RUNNING":
            raise ValueError("BLOCKED_JOB_STILL_RUNNING")
        if job.artifact_snapshot is None:
            job.artifact_snapshot = build_artifact_snapshot(job)
        return json.loads(json.dumps(job.artifact_snapshot))


if __name__ == "__main__":
    MCP.run(transport="stdio")

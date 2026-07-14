#!/usr/bin/env python3
"""Audit AirJet project structure and evidence-language invariants."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import subprocess
import sys
from pathlib import Path


REQUIRED = [
    "AGENTS.md",
    "airjet-simulation/README.md",
    "airjet-simulation/AIRJET_MINI_FULL_PRODUCT_MASTER_PLAN.md",
    "airjet-simulation/PROJECT_STATUS.md",
    "airjet-simulation/DECISION_AND_REASONING_ARCHIVE.md",
    "airjet-simulation/MODEL_ANNOTATIONS.md",
    "airjet-simulation/WINDOWS_HANDOFF.md",
    "airjet-simulation/WINDOWS_ENVIRONMENT_REPORT.md",
    "airjet-simulation/PEER_COLLABORATION_PROTOCOL.md",
    "airjet-simulation/collaboration/README.md",
    "airjet-simulation/evidence/SOURCE_PROVENANCE.md",
    "airjet-simulation/evidence/product_selection_matrix.csv",
    "airjet-simulation/evidence/airjet_mini_performance_curve_digitized.csv",
    "airjet-simulation/evidence/airjet_mini_curve_pixels.csv",
    "airjet-simulation/evidence/CURVE_DIGITIZATION_METHOD.md",
    "airjet-simulation/evidence/digitize_airjet_mini_curve.py",
    "airjet-simulation/evidence/P0_EVIDENCE_FREEZE_RECORD.md",
    "airjet-simulation/evidence/OFFICIAL_IMAGE_COORDINATE_METHOD.md",
    "airjet-simulation/evidence/patent_product_component_map.csv",
    "airjet-simulation/evidence/layout_candidate_scores.csv",
    "airjet-simulation/windows-prompts/AJM_WIN_P1_READINESS_001.md",
    "airjet-simulation/windows-prompts/AJM_WIN_ANSYS_OFFICIAL_TRIAL_INSTALL_AND_SMOKE_004.md",
    "airjet-simulation/windows-prompts/AJM_WIN_ANSYS_STUDENT_CAPABILITY_SMOKE_005.md",
    "airjet-simulation/windows-prompts/AJM_WIN_P1_FULL_PRODUCT_CAD_BUILD_006.md",
    "airjet-simulation/automation/ansys/profiles.json",
    "airjet-simulation/automation/ansys/approved/005/spaceclaim_t0.py",
    "airjet-simulation/automation/ansys/approved/005/workbench_t0.wbjn",
    "airjet-simulation/automation/ansys/approved/005/pymechanical_t0.py",
    "airjet-simulation/automation/ansys/approved/005/pyfluent_t0.py",
    "airjet-simulation/automation/ansys/approved/005/spaceclaim_cad_t1.py",
    "airjet-simulation/automation/ansys/approved/005/workbench_transfer_t1.wbjn",
    "airjet-simulation/learning/README.md",
    "airjet-simulation/learning/ANSYS_AUTOMATION_AND_005_LAB.md",
    "airjet-simulation/learning/T1_CAD_TRANSFER_WORKBOOK.md",
    "airjet-simulation/learning/PAPER_METHOD_EVIDENCE_MAP.md",
    "airjet-simulation/logs/REALITY_AND_FAILURE_LOG.md",
    "airjet-simulation/logs/run-index.csv",
    "airjet-simulation/logs/evidence/README.md",
    "airjet-simulation/reports/AJM_WIN_ANSYS_CAPABILITY_SMOKE_003_SUMMARY.md",
    "airjet-simulation/reports/AJM_WIN_ANSYS_STUDENT_CLEANUP_2026-07-14.md",
    "airjet-simulation/reports/AIRJET_DUAL_ENDPOINT_WATCHER_IMPLEMENTATION_2026-07-14.md",
    "airjet-simulation/evidence/build_layout_candidate_scores.py",
    "airjet-simulation/evidence/extract_official_image_geometry.py",
    "airjet-simulation/evidence/analyze_official_vent_views.py",
    "airjet-simulation/evidence/official_image_measurements.csv",
    "airjet-simulation/evidence/annotated_figures/gen1_vent_homography_results.csv",
    "airjet-simulation/evidence/annotated_figures/gen1_vent_cross_view_comparison.csv",
    "airjet-simulation/evidence/annotated_figures/gen1_top_render_quad_annotated.png",
    "airjet-simulation/evidence/annotated_figures/gen1_cross_section_annotated.png",
    "airjet-simulation/parameters/full_product_parameter_registry.csv",
    "airjet-simulation/parameters/build_p1_cad_inputs.py",
    "airjet-simulation/parameters/p1_layout_configuration_matrix.csv",
    "airjet-simulation/parameters/p1_thickness_budget.csv",
    "airjet-simulation/parameters/build_p1_cad_contracts.py",
    "airjet-simulation/parameters/P1_CAD_CONTRACT_METHOD.md",
    "airjet-simulation/parameters/p1_model_form_variants.csv",
    "airjet-simulation/parameters/p1_cad_parameter_map.csv",
    "airjet-simulation/parameters/p1_orifice_pattern_candidates.csv",
    "airjet-simulation/parameters/p1_vent_geometry_candidates.csv",
    "airjet-simulation/parameters/p1_planform_exhaust_candidates.csv",
    "airjet-simulation/parameters/p1_internal_geometry_rules.csv",
    "airjet-simulation/geometry/contracts/README.md",
    "airjet-simulation/geometry/contracts/p1_cad_features.csv",
    "airjet-simulation/geometry/contracts/p1_cad_feature_parameter_bindings.csv",
    "airjet-simulation/geometry/contracts/p1_cad_interfaces.csv",
    "airjet-simulation/geometry/contracts/p1_cad_named_selections.csv",
    "airjet-simulation/geometry/contracts/p1_cad_open_questions.csv",
    "airjet-simulation/checklists/full_product_stage_gates.md",
    "airjet-simulation/checklists/p1_cad_gate_matrix.csv",
    "airjet-simulation/checklists/P1_CAD_INDEPENDENT_REVIEW_METHOD.md",
    "airjet-simulation/checklists/prepare_p1_cad_review.py",
    "airjet-simulation/logs/p1_cad_run_template.md",
    "airjet-simulation/logs/external-files.csv",
    "airjet-simulation/SKILLS_AND_GIT_WORKFLOW.md",
    "airjet-simulation/notebooks/airjet-mini-layout-baseline.ipynb",
    "airjet-simulation/notebooks/build_layout_baseline.py",
    "codex-skills/skills-manifest.json",
    "codex-skills/airjet-ansys-automation/SKILL.md",
    "codex-skills/airjet-ansys-automation/agents/openai.yaml",
    "codex-skills/airjet-ansys-automation/references/official-automation-routes.md",
    "codex-skills/airjet-ansys-automation/references/gate-evidence.md",
    "codex-skills/airjet-ansys-automation/scripts/bootstrap_windows.ps1",
    "codex-skills/airjet-ansys-automation/scripts/airjet_ansys_mcp.py",
    "codex-skills/airjet-ansys-automation/scripts/run_t0_suite.py",
    "codex-skills/airjet-ansys-automation/scripts/run_t1_cad_suite.py",
    "codex-skills/airjet-ansys-automation/scripts/run_t1_connected_spaceclaim_suite.py",
    "codex-skills/airjet-ansys-automation/scripts/run_t1_semantic_reconstruction_suite.py",
    "codex-skills/airjet-ansys-automation/scripts/test_t1_predecessor_negative.py",
    "codex-skills/airjet-ansys-automation/scripts/test_airjet_ansys_mcp_policy.py",
    "install-skills.ps1",
    "install-skills.sh",
    "audit-airjet-project.ps1",
    "launch-airjet-codex-visible.ps1",
    "tools/airjet-git-watcher/README.md",
    "tools/airjet-git-watcher/wake-policy.md",
    "tools/airjet-git-watcher/mac/manage-airjet-watcher.sh",
    "tools/airjet-git-watcher/mac/install-mac-watcher.sh",
    "tools/airjet-git-watcher/mac/run-awakened-codex.sh",
    "tools/airjet-git-watcher/mac/watch-airjet-git.sh",
    "tools/airjet-git-watcher/tests/test-watch-airjet-git.sh",
    "tools/airjet-git-watcher/windows/AirJetWatcher.Common.ps1",
    "tools/airjet-git-watcher/windows/Watch-AirJetGit.ps1",
    "tools/airjet-git-watcher/windows/Manage-AirJetWatcher.ps1",
    "tools/airjet-git-watcher/windows/Run-AwakenedCodex.ps1",
    "tools/airjet-git-watcher/windows/Install-AirJetWatcher.ps1",
    "tools/airjet-git-watcher/tests/test-watch-airjet-git-windows.ps1",
]

MANUALS = [
    "01_FULL_PRODUCT_CAD.md",
    "02_ACTUATOR_STRUCTURAL.md",
    "03_CELL_TRANSIENT_CFD.md",
    "04_FULL_PRODUCT_AIRFLOW.md",
    "05_FULL_PRODUCT_CHT.md",
    "06_CALIBRATION_AND_UNCERTAINTY.md",
    "07_RUN_LOG_AND_GIT.md",
]

ARCHIVED = [
    "airjet-simulation/AIRJET_SIMULATION_PROJECT.md",
    "airjet-simulation/PROJECT_ASSESSMENT_AND_PLAN.md",
    "airjet-simulation/checklists/stage-gates.md",
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def audit_csv(path: Path, failures: list[str]) -> None:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))
    if not rows:
        failures.append(f"empty CSV: {path}")
        return
    width = len(rows[0])
    for number, row in enumerate(rows[1:], 2):
        if len(row) != width:
            failures.append(
                f"CSV width mismatch: {path}:{number} expected {width}, got {len(row)}"
            )


def float_close(actual: str, expected: float, tolerance: float = 1e-9) -> bool:
    try:
        return abs(float(actual) - expected) <= tolerance
    except (TypeError, ValueError):
        return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    failures: list[str] = []

    for relative in REQUIRED:
        if not (repo / relative).is_file():
            failures.append(f"missing required file: {relative}")

    watcher_path = repo / "tools/airjet-git-watcher/mac/watch-airjet-git.sh"
    manager_path = repo / "tools/airjet-git-watcher/mac/manage-airjet-watcher.sh"
    runner_path = repo / "tools/airjet-git-watcher/mac/run-awakened-codex.sh"
    watcher_test_path = repo / "tools/airjet-git-watcher/tests/test-watch-airjet-git.sh"
    if watcher_path.is_file():
        watcher_text = read_text(watcher_path)
        for marker in (
            "TASK_ENVELOPE_REL=airjet-simulation/collaboration/MAC_TASK.env",
            "BLOCKED_STATE_ROOT_INSIDE_REPOSITORY",
            "BLOCKED_CRITICAL_WATCHER_UPDATE",
            "BLOCKED_INVALID_MAC_TASK_ENVELOPE",
            "BLOCKED_EVENT_ROOT_NOT_DIRECT_STATE_CHILD",
            "BLOCKED_LOG_ROOT_NOT_DIRECT_STATE_CHILD",
            "BLOCKED_PENDING_REMOTE_MOVED",
            "BLOCKED_UNTRUSTED_COMMIT",
            "task_tip_not_signed_by_windows_peer",
            "automatic_relay_not_enabled",
            "POLL_SECONDS=10",
            "RUNTIME_STATUS=ENABLED_AFTER_REVIEW",
            "unsafe_instruction_object_type",
            "SYNCED_NO_MAC_TASK",
        ):
            if marker not in watcher_text:
                failures.append(f"Mac watcher lacks safety marker: {marker}")
    if manager_path.is_file():
        manager_text = read_text(manager_path)
        if "RUNTIME_STATUS=ENABLED_AFTER_REVIEW" not in manager_text:
            failures.append("Mac watcher manager is not enabled for reviewed manual runtime")
        if "POLL_SECONDS=10" not in manager_text:
            failures.append("Mac watcher manager default poll interval is not 10 seconds")
    if runner_path.is_file():
        runner_text = read_text(runner_path)
        for marker in (
            "BLOCKED_REPORT_ROOT_SYMLINK",
            "BLOCKED_REPORT_ROOT_INSIDE_REPOSITORY",
            "BLOCKED_PROMPT_HANDLE_MISSING_OR_SYMLINKED",
            "RUNNER_RESULT=REFUSED_",
            "BLOCKED_TEST_MODE_CODEX_START",
            "approval_policy=\"never\"",
        ):
            if marker not in runner_text:
                failures.append(f"Mac watcher runner lacks safety marker: {marker}")
    if watcher_test_path.is_file():
        test_text = read_text(watcher_test_path)
        for marker in (
            "critical_update_no_pending",
            "ordinary_update_no_pending",
            "dirty_pending_retry_block",
            "symlink_instruction_block",
            "state_root_boundary_output",
            "state_child_symlink_block",
            "report_root_symlink_block",
            "manager_start_test_mode_guard",
            "unsigned_commit_block",
            "self_signed_task_block",
            "revoked_signer_block",
            "automatic_relay_block",
            "EXPECTED_PASS_COUNT=80",
            "RUNTIME_TEST_MODE_GUARD=BEHAVIOR_TESTED",
            "OVERALL=PASS_CORE_RUNTIME_ENABLED_MANUAL",
            "VISIBLE_WAKE_TEST=SKIPPED_BY_DESIGN",
        ):
            if marker not in test_text:
                failures.append(f"Mac watcher test lacks case marker: {marker}")

    windows_common = repo / "tools/airjet-git-watcher/windows/AirJetWatcher.Common.ps1"
    windows_watcher = repo / "tools/airjet-git-watcher/windows/Watch-AirJetGit.ps1"
    windows_manager = repo / "tools/airjet-git-watcher/windows/Manage-AirJetWatcher.ps1"
    windows_runner = repo / "tools/airjet-git-watcher/windows/Run-AwakenedCodex.ps1"
    windows_installer = repo / "tools/airjet-git-watcher/windows/Install-AirJetWatcher.ps1"
    windows_test = repo / "tools/airjet-git-watcher/tests/test-watch-airjet-git-windows.ps1"
    windows_markers = {
        windows_common: (
            "ENABLED_AFTER_END_TO_END",
            "WINDOWS_TASK.env",
            "MAC_TASK.env",
            "gpg.minTrustLevel=fully",
            "--no-replace-objects",
            "BLOCKED_RELAY_NOT_ENABLED",
            "[IO.FileMode]::CreateNew",
            "GIT_SSH_VARIANT",
            "C:/Windows/System32/OpenSSH/ssh.exe",
        ),
        windows_watcher: (
            "[ValidateRange(10, 3600)][int]$PollSeconds = 10",
            "BLOCKED_RUNTIME_",
            "BLOCKED_TEST_MODE_WAKE_FORBIDDEN",
            "BLOCKED_CRITICAL_WATCHER_UPDATE",
            "SHELL_REQUESTED_NOT_USER_OBSERVED",
        ),
        windows_manager: (
            "[ValidateRange(10, 3600)][int]$PollSeconds = 10",
            "ENABLED_AFTER_END_TO_END",
            "REFUSED_TEST_MODE",
            "'start'",
            "'retry'",
        ),
        windows_runner: (
            "BLOCKED_TEST_MODE_CODEX_FORBIDDEN",
            "ENABLED_AFTER_END_TO_END",
            "approval_policy=\"never\"",
        ),
        windows_installer: ("InteractiveToken", "RegisterAtLogOn", "BLOCKED_REGISTER_RUNTIME_NOT_ENABLED"),
        windows_test: (
            "EXPECTED_PASS_COUNT=$ExpectedPassCount",
            "RUNTIME_TEST_MODE_GUARD=BEHAVIOR_TESTED",
            "OVERALL=PASS_CORE_RUNTIME_ENABLED_MANUAL",
        ),
    }
    for path, markers in windows_markers.items():
        if not path.is_file():
            continue
        text = read_text(path)
        for marker in markers:
            if marker not in text:
                failures.append(f"Windows watcher file lacks safety marker: {path.name}: {marker}")

    manual_dir = repo / "airjet-simulation/manuals"
    for manual in MANUALS:
        if not (manual_dir / manual).is_file():
            failures.append(f"missing manual: {manual}")

    for relative in ARCHIVED:
        path = repo / relative
        if path.is_file() and "已归档" not in read_text(path) and "停用" not in read_text(path):
            failures.append(f"legacy route lacks archive banner: {relative}")

    csv_paths = list((repo / "airjet-simulation").rglob("*.csv"))
    for path in csv_paths:
        audit_csv(path, failures)

    archived_paths = {(repo / relative).resolve() for relative in ARCHIVED}
    active_paths = [
        path
        for path in (repo / "airjet-simulation").rglob("*")
        if path.is_file()
        and path.suffix.lower() in {".md", ".csv"}
        and path.resolve() not in archived_paths
    ]
    forbidden = [
        "delivered_airflow_chart_units",
        "功耗—流量曲线",
        "在 1750 Pa 目标背压下维持净流",
        "30-60,m/s",
    ]
    for path in active_paths:
        if not path.is_file():
            continue
        text = read_text(path)
        for phrase in forbidden:
            if phrase in text:
                failures.append(f"obsolete evidence claim {phrase!r} in {path.relative_to(repo)}")

    peer_language_forbidden = (
        "pending Mac review",
        "Mac evidence and artifact review",
        "independent Mac review",
    )
    peer_language_paths = [
        path
        for path in (repo / "airjet-simulation").rglob("*")
        if path.is_file()
        and path.suffix.lower() in {".md", ".csv", ".py"}
        and path.resolve() not in archived_paths
    ]
    for path in peer_language_paths:
        text = read_text(path)
        for phrase in peer_language_forbidden:
            if phrase in text:
                failures.append(f"obsolete machine-hierarchy phrase {phrase!r} in {path.relative_to(repo)}")

    perf = repo / "airjet-simulation/evidence/airjet_mini_performance_curve_digitized.csv"
    if perf.is_file():
        with perf.open(newline="", encoding="utf-8") as handle:
            perf_rows = list(csv.DictReader(handle))
            header = list(perf_rows[0].keys()) if perf_rows else []
        if "system_noise_at_50cm_dBA" not in header:
            failures.append("Mini performance CSV must identify the right axis as 50 cm system noise")
        if len(perf_rows) != 4:
            failures.append(f"Mini performance CSV must contain four operating points, got {len(perf_rows)}")
        endpoint = next((row for row in perf_rows if row.get("power_W") == "1.00"), None)
        if endpoint is None:
            failures.append("Mini performance CSV lacks the 1.00 W endpoint")
        elif not (
            float_close(endpoint.get("net_heat_dissipation_W", ""), 4.25)
            and float_close(endpoint.get("system_noise_at_50cm_dBA", ""), 21.0)
            and "direct_endpoint" in endpoint.get("status", "")
        ):
            failures.append("Mini 1 W endpoint must preserve 4.25 W net heat, 21 dBA, and direct endpoint status")

    registry = repo / "airjet-simulation/parameters/full_product_parameter_registry.csv"
    if registry.is_file():
        with registry.open(newline="", encoding="utf-8") as handle:
            registry_rows = list(csv.DictReader(handle))
        by_id = {row.get("id", ""): row for row in registry_rows}
        if len(by_id) != len(registry_rows):
            failures.append("full product parameter registry contains duplicate or blank ids")
        required_columns = {
            "evidence_class",
            "uncertainty_or_range",
            "derivation_or_parent",
            "adjustable",
        }
        if registry_rows and not required_columns.issubset(registry_rows[0]):
            failures.append("full product parameter registry lacks evidence/audit columns")
        allowed_classes = {"D", "P", "I", "C", "U"}
        for row in registry_rows:
            if row.get("evidence_class") not in allowed_classes:
                failures.append(f"invalid evidence class for {row.get('id')}")
            if row.get("adjustable") not in {"true", "false"}:
                failures.append(f"invalid adjustable flag for {row.get('id')}")
        direct_expected = {
            "D001": (27.5, "direct_product"),
            "D002": (41.5, "direct_product"),
            "D003": (2.8, "direct_product"),
            "D004": (1.0, "direct_product"),
            "D005": (5.25, "direct_product"),
            "D006": (4.25, "direct_product"),
            "D011": (1750.0, "direct_product"),
            "D012": (21.0, "direct_product"),
            "D013": (11.0, "direct_product"),
        }
        for row_id, (expected, status) in direct_expected.items():
            row = by_id.get(row_id)
            if row is None:
                failures.append(f"parameter registry missing {row_id}")
            elif (
                not float_close(row.get("initial_value", ""), expected)
                or row.get("status") != status
                or row.get("evidence_class") != "D"
                or row.get("adjustable") != "false"
            ):
                failures.append(f"parameter registry changed locked product target {row_id}")
        try:
            heat_total = float(by_id["D005"]["initial_value"])
            heat_net = float(by_id["D006"]["initial_value"])
            power = float(by_id["D004"]["initial_value"])
            if abs(heat_net + power - heat_total) > 1e-9:
                failures.append("heat accounting invariant failed: Q_net + P_airjet != Q_total")
        except (KeyError, TypeError, ValueError):
            failures.append("heat accounting invariant could not be evaluated")
        for row_id in ("D007", "D008", "D009"):
            if by_id.get(row_id, {}).get("evidence_class") != "I":
                failures.append(f"{row_id} must remain an image-digitized I-class target")
        for row in registry_rows:
            if row.get("id", "").startswith("P") and row.get("evidence_class") != "P":
                failures.append(f"patent registry row is not P-class: {row.get('id')}")
        p011 = by_id.get("P011", {})
        if p011.get("status") != "patent_lower_bound" or "no 60 m/s upper bound" not in p011.get(
            "uncertainty_or_range", ""
        ):
            failures.append("P011 must preserve >=30 m/s lower bound with no 60 m/s upper bound")
        for row in registry_rows:
            if row.get("evidence_class") == "P" and "printed col." not in row.get("evidence_source", ""):
                failures.append(f"patent registry row lacks local printed-column locator: {row.get('id')}")
        if "not a known flow operating point" not in by_id.get("D011", {}).get(
            "calibration_target", ""
        ):
            failures.append("1750 Pa must remain a pressure capability with unknown corresponding flow")
        if by_id.get("C004", {}).get("initial_value") != "candidate_v1_dual_view_homography":
            failures.append("C004 must preserve the dual-view P0 intake candidate")
        if by_id.get("C014", {}).get("initial_value") != "4_drawn_vent_objects_not_confirmed_groups":
            failures.append("C014 must distinguish drawn vents from confirmed intake groups")
        expected_p1_parameters = {
            "C015": ("C", "true"),
            "C016": ("C", "true"),
            "C017": ("C", "true"),
            "C018": ("C", "false"),
            "C019": ("U", "false"),
            "C020": ("C", "true"),
        }
        for row_id, (evidence_class, adjustable) in expected_p1_parameters.items():
            row = by_id.get(row_id)
            if row is None:
                failures.append(f"parameter registry missing P1 input {row_id}")
            elif row.get("evidence_class") != evidence_class or row.get("adjustable") != adjustable:
                failures.append(f"P1 parameter evidence/adjustability changed: {row_id}")
        try:
            bottom_expected = float(by_id["P004"]["initial_value"]) / 1000.0 + float(
                by_id["P006"]["initial_value"]
            )
            if not float_close(by_id["C018"]["initial_value"], bottom_expected):
                failures.append("C018 must equal P004/1000 + P006")
            allocated_ids = ("C015", "P005", "P002", "C018", "C016", "P010", "C009", "C017")
            residual_expected = float(by_id["D003"]["initial_value"]) - sum(
                float(by_id[row_id]["initial_value"]) for row_id in allocated_ids
            )
            if not float_close(by_id["C019"]["initial_value"], residual_expected):
                failures.append("C019 must equal D003 minus the allocated TB0 stack")
            split = float(by_id["C020"]["initial_value"])
            if not 0.0 <= split <= 1.0:
                failures.append("C020 residual top fraction must remain within [0, 1]")
        except (KeyError, TypeError, ValueError):
            failures.append("P1 thickness derivations could not be evaluated")
        if "no mass constraint claimed" not in by_id.get("C009", {}).get("uncertainty_or_range", ""):
            failures.append("C009 exploratory spreader range must not claim an uncomputed 11 g constraint")

    ledger = repo / "airjet-simulation/evidence/airjet_reconstruction_ledger.csv"
    if ledger.is_file():
        with ledger.open(newline="", encoding="utf-8") as handle:
            ledger_rows = list(csv.DictReader(handle))
        for row in ledger_rows:
            if row.get("evidence_class") not in {"D", "P", "I", "C", "U"}:
                failures.append(f"legacy ledger has invalid evidence class: {row.get('id')}")
            if row.get("evidence_class") == "P" and "locked" in row.get("model_status", ""):
                failures.append(f"patent ledger row is incorrectly locked: {row.get('id')}")
            if row.get("evidence_class") == "P" and "paragraph " in row.get("source", ""):
                failures.append(
                    f"patent ledger row uses a webpage line as a patent paragraph: {row.get('id')}"
                )

    selection = repo / "airjet-simulation/evidence/product_selection_matrix.csv"
    if selection.is_file():
        with selection.open(newline="", encoding="utf-8") as handle:
            selection_rows = list(csv.DictReader(handle))
        g2_rows = [row for row in selection_rows if row.get("product") == "AirJet Mini G2"]
        if len(g2_rows) != 1:
            failures.append("product selection matrix must contain exactly one Mini G2 row")
        else:
            g2 = g2_rows[0]
            expected_g2 = {
                "external_dimensions_mm": "27.1x41.5x2.65",
                "heat_dissipation_W": 7.5,
                "max_power_W": 1.2,
                "backpressure_Pa": 1750.0,
                "noise_dBA": 21.0,
                "weight_g": 7.0,
            }
            for key, expected in expected_g2.items():
                actual = g2.get(key, "")
                if isinstance(expected, str):
                    valid = actual == expected
                else:
                    valid = float_close(actual, expected)
                if not valid:
                    failures.append(f"G2 direct specification changed: {key}")

    patent_map = repo / "airjet-simulation/evidence/patent_product_component_map.csv"
    if patent_map.is_file():
        with patent_map.open(newline="", encoding="utf-8") as handle:
            patent_rows = list(csv.DictReader(handle))
        if len(patent_rows) != 10:
            failures.append(f"patent-product component map must contain 10 rows, got {len(patent_rows)}")
        if any(row.get("evidence_class") != "P" for row in patent_rows):
            failures.append("patent-product component map must remain P-class")
        if any("col." not in row.get("exact_locator", "") or "FIG" not in row.get("exact_locator", "") for row in patent_rows):
            failures.append("patent-product component map lacks FIG and printed-column locators")

    layout_scores = repo / "airjet-simulation/evidence/layout_candidate_scores.csv"
    if layout_scores.is_file():
        with layout_scores.open(newline="", encoding="utf-8") as handle:
            layout_rows = list(csv.DictReader(handle))
        if len(layout_rows) != 32 or len({row.get("geometry_key") for row in layout_rows}) != 32:
            failures.append("layout score table must contain 32 unique geometries")
        fit_rows = [row for row in layout_rows if row.get("hard_envelope") == "PASS_CONFIG_A0"]
        if len(fit_rows) != 23:
            failures.append(f"layout score table must preserve 23 A0-fit geometries, got {len(fit_rows)}")
        primary = [row for row in layout_rows if row.get("rank_tier") == "PRIMARY-P0"]
        alternate = [row for row in layout_rows if row.get("rank_tier") == "ALTERNATE-P0"]
        if len(primary) != 1 or primary[0].get("candidate_id") != "M-3x4-7.0":
            failures.append("layout score table changed the P0 working primary")
        if len(alternate) != 1 or alternate[0].get("candidate_id") != "M+S-3x5-6.0":
            failures.append("layout score table changed the P0 working alternate")
        for row in fit_rows:
            if row.get("score_coverage_pct") != "20":
                failures.append(f"layout P0 score coverage must remain 20 percent: {row.get('candidate_id')}")
            for pending in ("S_image", "S_modal", "S_power", "S_flow", "S_thermal"):
                if row.get(pending):
                    failures.append(f"layout P0 pending score was populated: {row.get('candidate_id')} {pending}")

    p1_layouts = repo / "airjet-simulation/parameters/p1_layout_configuration_matrix.csv"
    if p1_layouts.is_file():
        with p1_layouts.open(newline="", encoding="utf-8") as handle:
            p1_layout_rows = list(csv.DictReader(handle))
        expected_roles = {
            "M-3x4-7.0": "PRIMARY-P0",
            "M+S-3x5-6.0": "ALTERNATE-P0",
            "L-2x4-8.0": "LOW-CELL-SENTINEL",
            "S-3x5-5.5": "SMALL-CELL-SENTINEL",
        }
        ids = [row.get("configuration_id", "") for row in p1_layout_rows]
        if len(p1_layout_rows) != 4 or len(set(ids)) != 4 or set(ids) != set(expected_roles):
            failures.append("P1 layout matrix must contain the four unique frozen work configurations")
        for row in p1_layout_rows:
            row_id = row.get("configuration_id", "")
            if row.get("p1_role") != expected_roles.get(row_id):
                failures.append(f"P1 layout role changed: {row_id}")
            if row.get("evidence_class") != "C" or row.get("source_evidence_classes") != "D;P;I":
                failures.append(f"P1 layout must use C with D/P/I source classes: {row_id}")
            if row.get("product_fact") != "false" or row.get("hole_count_status") != "PROXY_NOT_CAD_LOCKED":
                failures.append(f"P1 layout was promoted beyond candidate/proxy status: {row_id}")
            if "single-side integrated spout qualitative topology" not in row.get("source_refs", ""):
                failures.append(f"P1 topology lacks official cross-section/spout source boundary: {row_id}")
            try:
                diameter = float(row["orifice_diameter_candidate_mm"])
                porosity = float(row["open_area_candidate_pct"]) / 100.0
                area = float(row["active_membrane_area_proxy_mm2"])
                expected_holes = round(porosity * area / (math.pi * (diameter / 2.0) ** 2))
                if int(row["porosity_hole_count_proxy"]) != expected_holes:
                    failures.append(f"P1 porosity hole-count proxy is stale: {row_id}")
            except (KeyError, TypeError, ValueError, ZeroDivisionError):
                failures.append(f"P1 porosity proxy could not be evaluated: {row_id}")

    p1_thickness = repo / "airjet-simulation/parameters/p1_thickness_budget.csv"
    if p1_thickness.is_file():
        with p1_thickness.open(newline="", encoding="utf-8") as handle:
            thickness_rows = list(csv.DictReader(handle))
        if len(thickness_rows) != 10:
            failures.append(f"P1 thickness budget must contain 10 rows, got {len(thickness_rows)}")
        running_z = 0.0
        for row in thickness_rows:
            if row.get("evidence_class") not in {"D", "P", "I", "C", "U"}:
                failures.append(f"P1 thickness row has invalid evidence class: {row.get('parameter_id')}")
            if row.get("product_fact") != "false":
                failures.append(f"P1 thickness placeholder was promoted to product fact: {row.get('parameter_id')}")
            try:
                z_min = float(row["z_min_mm"])
                z_max = float(row["z_max_mm"])
                thickness = float(row["thickness_mm"])
                if not math.isclose(z_min, running_z, rel_tol=0.0, abs_tol=1e-9):
                    failures.append(f"P1 thickness z continuity failed at {row.get('parameter_id')}")
                if not math.isclose(z_max - z_min, thickness, rel_tol=0.0, abs_tol=1e-9):
                    failures.append(f"P1 thickness interval failed at {row.get('parameter_id')}")
                running_z = z_max
            except (KeyError, TypeError, ValueError):
                failures.append(f"P1 thickness row is non-numeric: {row.get('parameter_id')}")
        if not math.isclose(running_z, 2.8, rel_tol=0.0, abs_tol=1e-9):
            failures.append("P1 thickness budget must close exactly to 2.8 mm")
        p002_rows = [row for row in thickness_rows if row.get("parameter_id") == "P002"]
        if len(p002_rows) != 1 or "cross-size CAD placeholder" not in p002_rows[0].get(
            "applicability_note", ""
        ):
            failures.append("P002 thickness must remain an explicit 8 mm cross-size P1 placeholder")
        geometry_only = [
            row for row in thickness_rows if row.get("parameter_id") in {"C017", "C019_TOP", "C019_BOTTOM"}
        ]
        if len(geometry_only) != 3 or any(
            row.get("solver_use") != "GEOMETRY_ONLY_NO_MATERIAL_NO_MASS_NO_STRUCTURAL_NO_CHT"
            for row in geometry_only
        ):
            failures.append("unresolved P1 residual/support placeholders must be excluded from physics")

    p1_builder = repo / "airjet-simulation/parameters/build_p1_cad_inputs.py"
    if p1_builder.is_file():
        check = subprocess.run(
            [sys.executable, str(p1_builder), "--check"],
            cwd=repo,
            capture_output=True,
            text=True,
            check=False,
        )
        if check.returncode != 0 or "PASS mode=check" not in check.stdout:
            detail = (check.stderr or check.stdout).strip().replace("\n", " | ")
            failures.append(f"P1 generated inputs are stale or invalid: {detail}")

    p1_contract_builder = repo / "airjet-simulation/parameters/build_p1_cad_contracts.py"
    if p1_contract_builder.is_file():
        check = subprocess.run(
            [sys.executable, str(p1_contract_builder), "--check"],
            cwd=repo,
            capture_output=True,
            text=True,
            check=False,
        )
        if check.returncode != 0 or "PASS mode=check" not in check.stdout:
            detail = (check.stderr or check.stdout).strip().replace("\n", " | ")
            failures.append(f"P1 CAD contracts are stale or invalid: {detail}")

    variant_path = repo / "airjet-simulation/parameters/p1_model_form_variants.csv"
    if variant_path.is_file():
        with variant_path.open(newline="", encoding="utf-8") as handle:
            variant_rows = list(csv.DictReader(handle))
        expected_variants = {
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
        actual_variants = {row.get("variant_id", "") for row in variant_rows}
        if len(variant_rows) != 9 or actual_variants != expected_variants:
            failures.append("P1 model-form table must contain six base/residual and three derived variants")
        primary_fractions = {
            row.get("C020_residual_top_fraction")
            for row in variant_rows
            if row.get("configuration_id") == "M-3x4-7.0"
        }
        if primary_fractions != {"0.25", "0.50", "0.75"}:
            failures.append("P1 primary residual branches must remain 0.25/0.50/0.75")
        for row in variant_rows:
            if row.get("product_fact") != "false" or row.get("status") != "CANDIDATE_NOT_RUN":
                failures.append(f"P1 variant was promoted beyond candidate input: {row.get('variant_id')}")
            expected_internal_branches = {
                "cell_geometry_rule_id": "CELL_CENTER_AND_TILE_R0",
                "central_anchor_rule_id": "CENTRAL_ANCHOR_SQUARE_DATUM_R0",
                "bottom_chamber_rule_id": "BOTTOM_CHAMBER_PER_CELL_SQUARE_R0",
                "cell_partition_rule_id": "CELL_PARTITION_DATUM_R0",
                "top_chamber_branch_id": "TOP_SHARED_PLENUM_R0",
                "perimeter_gap_branch_id": "PERIM_SPLIT_GAP_R0",
                "side_frame_closure_branch_id": "SIDE_WALL_BOUNDARY_R0",
                "residual_closure_branch_id": "RESIDUAL_NUMERICAL_CLOSURE_R0",
                "orifice_grid_rule_id": "ORIFICE_PER_CELL_CENTERED_CLIP_R0",
            }
            if any(row.get(key) != value for key, value in expected_internal_branches.items()):
                failures.append(f"P1 variant internal R0 branch set changed: {row.get('variant_id')}")
            try:
                residual = float(row["C019_residual_total_mm"])
                if not math.isclose(
                    float(row["residual_top_mm"]) + float(row["residual_bottom_mm"]),
                    residual,
                    rel_tol=0.0,
                    abs_tol=1e-9,
                ):
                    failures.append(f"P1 residual split does not close: {row.get('variant_id')}")
            except (KeyError, TypeError, ValueError):
                failures.append(f"P1 residual split is non-numeric: {row.get('variant_id')}")
        derived_rows = [row for row in variant_rows if row.get("variant_kind") == "DERIVED_SINGLE_FACTOR"]
        baseline = next(
            (row for row in variant_rows if row.get("variant_id") == "M-3x4-7.0__R50_BALANCED"),
            None,
        )
        branch_fields = ("vent_candidate_set_id", "orifice_pattern_id", "exhaust_branch_id")
        if len(derived_rows) != 3 or baseline is None:
            failures.append("P1 variant table lacks baseline or three derived single-factor rows")
        else:
            for row in derived_rows:
                changes = sum(row.get(field) != baseline.get(field) for field in branch_fields)
                if row.get("comparison_parent_variant_id") != baseline.get("variant_id") or changes != 1:
                    failures.append(f"P1 derived variant is not single-factor: {row.get('variant_id')}")

    parameter_map_path = repo / "airjet-simulation/parameters/p1_cad_parameter_map.csv"
    if parameter_map_path.is_file():
        with parameter_map_path.open(newline="", encoding="utf-8") as handle:
            parameter_map_rows = list(csv.DictReader(handle))
        if len(parameter_map_rows) != 342:
            failures.append(f"P1 CAD parameter map must contain 342 rows, got {len(parameter_map_rows)}")
        if any(row.get("evidence_class") not in {"D", "P", "I", "C", "U"} for row in parameter_map_rows):
            failures.append("P1 CAD parameter map contains an invalid evidence class")
        product_fact_rows = [row for row in parameter_map_rows if row.get("product_fact") == "true"]
        if len(product_fact_rows) != 27 or any(
            row.get("parameter_id") not in {"D001", "D002", "D003"} for row in product_fact_rows
        ):
            failures.append("only D001/D002/D003 may be product facts in the P1 CAD parameter map")
        guarded_ids = {"C017", "C019", "C019_TOP", "C019_BOTTOM"}
        guarded_rows = [row for row in parameter_map_rows if row.get("parameter_id") in guarded_ids]
        if len(guarded_rows) != 36 or any(
            row.get("geometry_only") != "true"
            or row.get("solver_use") != "GEOMETRY_ONLY_NO_MATERIAL_NO_MASS_NO_STRUCTURAL_NO_CHT"
            for row in guarded_rows
        ):
            failures.append("P1 CAD parameter-map geometry-only guards changed")

    orifice_path = repo / "airjet-simulation/parameters/p1_orifice_pattern_candidates.csv"
    if orifice_path.is_file():
        with orifice_path.open(newline="", encoding="utf-8") as handle:
            orifice_rows = list(csv.DictReader(handle))
        if len(orifice_rows) != 12 or len({row.get("configuration_id") for row in orifice_rows}) != 4:
            failures.append("P1 orifice table must contain three branches for each of four configurations")
        if any(row.get("product_fact") != "false" for row in orifice_rows):
            failures.append("P1 orifice branch was promoted to product fact")
        center_rows = [row for row in orifice_rows if "CENTER_PITCH_SENTINEL" in row.get("pattern_id", "")]
        edge_rows = [row for row in orifice_rows if "P008_AS_EDGE_GAP" in row.get("pattern_id", "")]
        phi_rows = [row for row in orifice_rows if "PHI_DERIVED_SQUARE" in row.get("pattern_id", "")]
        if len(center_rows) != 4 or any(
            float(row.get("infinite_square_grid_open_area_pct", "0")) <= 15.0
            or row.get("cad_ready_candidate") != "false"
            for row in center_rows
        ):
            failures.append("P008 center-pitch porosity conflict sentinel was lost")
        if len(edge_rows) != 4 or any(not float_close(row.get("pitch_x_mm", ""), 0.75, 1e-6) for row in edge_rows):
            failures.append("P008 edge-gap candidate pitch must remain 0.75 mm")
        expected_phi_pitch = 0.25 * math.sqrt(math.pi / (4.0 * 0.10))
        if len(phi_rows) != 4 or any(
            not float_close(row.get("pitch_x_mm", ""), expected_phi_pitch, 1e-6) for row in phi_rows
        ):
            failures.append("porosity-derived P1 orifice pitch is stale")

    vent_candidate_path = repo / "airjet-simulation/parameters/p1_vent_geometry_candidates.csv"
    if vent_candidate_path.is_file():
        with vent_candidate_path.open(newline="", encoding="utf-8") as handle:
            vent_candidate_rows = list(csv.DictReader(handle))
        expected_sets = {"VENT_FLOW_BBOX_R0", "VENT_UPPER_CENTERLINE_P013_R0"}
        set_counts = {
            candidate_set: len(
                {row.get("vent_id") for row in vent_candidate_rows if row.get("candidate_set_id") == candidate_set}
            )
            for candidate_set in expected_sets
        }
        if len(vent_candidate_rows) != 8 or set_counts != {name: 4 for name in expected_sets}:
            failures.append("P1 vent candidates must contain two complete four-object sets")
        if any(
            row.get("product_fact") != "false"
            or row.get("drawn_object_count_scope") != "FOUR_DRAWN_OBJECTS_NOT_GROUP_COUNT"
            for row in vent_candidate_rows
        ):
            failures.append("P1 vent candidate evidence boundary changed")
        try:
            if any(
                not (-13.75 <= float(row["center_x_cad_mm"]) <= 13.75)
                or not (-20.75 <= float(row["center_y_cad_mm"]) <= 20.75)
                or float(row["axis_length_mm"]) <= 0.0
                or float(row["slot_width_mm"]) <= 0.0
                for row in vent_candidate_rows
            ):
                failures.append("P1 vent candidate lies outside envelope or has non-positive dimensions")
        except (KeyError, TypeError, ValueError):
            failures.append("P1 vent candidate contains non-numeric geometry")

    planform_path = repo / "airjet-simulation/parameters/p1_planform_exhaust_candidates.csv"
    if planform_path.is_file():
        with planform_path.open(newline="", encoding="utf-8") as handle:
            planform_rows = list(csv.DictReader(handle))
        configuration_counts = {
            config: sum(row.get("configuration_id") == config for row in planform_rows)
            for config in {"M-3x4-7.0", "M+S-3x5-6.0", "L-2x4-8.0", "S-3x5-5.5"}
        }
        if len(planform_rows) != 8 or set(configuration_counts.values()) != {2}:
            failures.append("P1 exhaust table must contain two branches for each configuration")
        if any(
            row.get("product_fact") != "false"
            or row.get("single_side_rule") != "OUTLET_ON_Y_PLUS_ENVELOPE_FACE_ONLY"
            for row in planform_rows
        ):
            failures.append("P1 exhaust branch evidence or single-side boundary changed")
        try:
            if any(
                not float_close(row["manifold_y_max_mm"], 20.75, 1e-9)
                or float(row["manifold_length_mm"]) <= 0.0
                or not math.isclose(
                    float(row["outlet_width_mm"]) * float(row["outlet_height_mm"]),
                    float(row["outlet_area_mm2"]),
                    rel_tol=0.0,
                    abs_tol=1e-9,
                )
                for row in planform_rows
            ):
                failures.append("P1 exhaust branch geometry closure failed")
        except (KeyError, TypeError, ValueError):
            failures.append("P1 exhaust branch contains non-numeric geometry")

    internal_rule_path = repo / "airjet-simulation/parameters/p1_internal_geometry_rules.csv"
    if internal_rule_path.is_file():
        with internal_rule_path.open(newline="", encoding="utf-8") as handle:
            internal_rule_rows = list(csv.DictReader(handle))
        expected_rule_ids = {
            "CELL_CENTER_AND_TILE_R0",
            "BOTTOM_CHAMBER_PER_CELL_SQUARE_R0",
            "CENTRAL_ANCHOR_SQUARE_DATUM_R0",
            "CELL_PARTITION_DATUM_R0",
            "TOP_SHARED_PLENUM_R0",
            "PERIM_SPLIT_GAP_R0",
            "SIDE_WALL_BOUNDARY_R0",
            "RESIDUAL_NUMERICAL_CLOSURE_R0",
            "ORIFICE_PER_CELL_CENTERED_CLIP_R0",
        }
        if len(internal_rule_rows) != 9 or {row.get("rule_id") for row in internal_rule_rows} != expected_rule_ids:
            failures.append("P1 internal geometry table must retain the nine explicit R0 rules")
        if any(
            row.get("product_fact") != "false"
            or row.get("evidence_class") != "C"
            or row.get("selection_status") != "SELECTED_R0_ENGINEERING_CLOSURE"
            for row in internal_rule_rows
        ):
            failures.append("P1 internal geometry rule was promoted beyond C-class engineering closure")
        expected_rule_sources = {
            "CELL_CENTER_AND_TILE_R0": "P;C",
            "BOTTOM_CHAMBER_PER_CELL_SQUARE_R0": "P;C",
            "CENTRAL_ANCHOR_SQUARE_DATUM_R0": "P;C",
            "CELL_PARTITION_DATUM_R0": "P;C",
            "TOP_SHARED_PLENUM_R0": "P;I;C",
            "PERIM_SPLIT_GAP_R0": "P;C",
            "SIDE_WALL_BOUNDARY_R0": "D;I;C;U",
            "RESIDUAL_NUMERICAL_CLOSURE_R0": "C;U",
            "ORIFICE_PER_CELL_CENTERED_CLIP_R0": "P;C",
        }
        if any(
            row.get("source_evidence_classes") != expected_rule_sources.get(row.get("rule_id"))
            for row in internal_rule_rows
        ):
            failures.append("P1 internal geometry rule provenance classes changed")
        residual_rule = next(
            (row for row in internal_rule_rows if row.get("rule_id") == "RESIDUAL_NUMERICAL_CLOSURE_R0"),
            {},
        )
        if "NEVER_EXTRACT_OUTER_ENVELOPE_MINUS_ALL_SOLIDS" not in residual_rule.get(
            "planform_or_construction_rule", ""
        ):
            failures.append("P1 residual closure no longer prevents false fluid extraction")

    feature_path = repo / "airjet-simulation/geometry/contracts/p1_cad_features.csv"
    binding_path = repo / "airjet-simulation/geometry/contracts/p1_cad_feature_parameter_bindings.csv"
    interface_path = repo / "airjet-simulation/geometry/contracts/p1_cad_interfaces.csv"
    named_path = repo / "airjet-simulation/geometry/contracts/p1_cad_named_selections.csv"
    open_path = repo / "airjet-simulation/geometry/contracts/p1_cad_open_questions.csv"
    if feature_path.is_file():
        with feature_path.open(newline="", encoding="utf-8") as handle:
            feature_rows = list(csv.DictReader(handle))
        feature_ids = {row.get("feature_id", "") for row in feature_rows}
        if len(feature_rows) != 30 or len(feature_ids) != 30:
            failures.append("P1 feature contract must contain 30 unique features")
        true_features = {row.get("feature_id") for row in feature_rows if row.get("product_fact") == "true"}
        if true_features != {"ENVELOPE_REF"}:
            failures.append("only ENVELOPE_REF may be a product fact in the P1 feature contract")
        residual_features = [
            row for row in feature_rows
            if row.get("feature_id") in {"C017_SUPPORT_ALLOWANCE_REF", "C019_TOP_REF", "C019_BOTTOM_REF"}
        ]
        if len(residual_features) != 3 or any(
            row.get("material_policy") != "PROHIBITED"
            or row.get("mass_policy") != "EXCLUDE"
            or row.get("boolean_policy") != "NO_BOOLEAN"
            or row.get("export_policy") != "DO_NOT_EXPORT"
            or row.get("solver_use") != "GEOMETRY_ONLY_NO_PHYSICS"
            for row in residual_features
        ):
            failures.append("P1 feature residual/support guards changed")
        construction_datums = [
            row for row in feature_rows
            if row.get("feature_id") in {"CENTRAL_ANCHOR_CAND_TEMPLATE", "CELL_PARTITION_CAND_TEMPLATE"}
        ]
        if len(construction_datums) != 2 or any(
            row.get("material_policy") != "PROHIBITED"
            or row.get("mass_policy") != "EXCLUDE"
            or not row.get("boolean_policy", "").startswith("NO_BOOLEAN")
            or not row.get("export_policy", "").startswith("DO_NOT_EXPORT")
            or row.get("solver_use") != "GEOMETRY_ONLY_NO_PHYSICS"
            for row in construction_datums
        ):
            failures.append("P1 central-anchor or cell-partition datum gained physical behavior")
        if any(row.get("geometry_class") != "C" for row in construction_datums):
            failures.append("P1 central-anchor or cell-partition exact geometry was promoted beyond C")
    else:
        feature_ids = set()

    if binding_path.is_file():
        with binding_path.open(newline="", encoding="utf-8") as handle:
            binding_rows = list(csv.DictReader(handle))
        if len(binding_rows) != 31 or len({row.get("binding_id") for row in binding_rows}) != 31:
            failures.append("P1 parameter-binding contract must contain 31 unique rows")
        if any(not row.get("parameter_id") or not row.get("source_locator") for row in binding_rows):
            failures.append("P1 parameter-binding contract contains a hidden or untraced input")
        if feature_ids and any(row.get("feature_id") not in feature_ids for row in binding_rows):
            failures.append("P1 parameter-binding contract references an unknown feature")
        partition_binding = next(
            (
                row
                for row in binding_rows
                if row.get("feature_id") == "CELL_PARTITION_CAND_TEMPLATE"
                and row.get("parameter_id") == "P014"
            ),
            {},
        )
        if partition_binding.get("geometry_only") != "true":
            failures.append("P1 cell-partition datum binding must remain geometry-only")

    if interface_path.is_file():
        with interface_path.open(newline="", encoding="utf-8") as handle:
            interface_rows = list(csv.DictReader(handle))
        forbidden_features = {
            "C017_SUPPORT_ALLOWANCE_REF",
            "C019_TOP_REF",
            "C019_BOTTOM_REF",
            "FLEX_KEEP_OUT_U",
            "CENTRAL_ANCHOR_CAND_TEMPLATE",
            "CELL_PARTITION_CAND_TEMPLATE",
        }
        if len(interface_rows) != 13 or any(
            row.get("side_a_feature_id") in forbidden_features
            or row.get("side_b_feature_id") in forbidden_features
            for row in interface_rows
        ):
            failures.append("P1 interface contract count or geometry-only exclusion changed")
        if feature_ids and any(
            row.get("side_a_feature_id") not in feature_ids or row.get("side_b_feature_id") not in feature_ids
            for row in interface_rows
        ):
            failures.append("P1 interface contract references an unknown feature")
        expected_interface_branches = {
            "IF001": "P1_OPTIONAL_EXTERNAL_DOMAIN",
            "IF009": "P1_OPTIONAL_EXTERNAL_DOMAIN",
            "IF013": "P5_ONLY",
        }
        for row in interface_rows:
            expected_branch = expected_interface_branches.get(row.get("interface_id"), "ALL_P1_VARIANTS")
            if row.get("branch_id") != expected_branch:
                failures.append(f"P1 interface branch scope changed: {row.get('interface_id')}")

    if named_path.is_file():
        with named_path.open(newline="", encoding="utf-8") as handle:
            named_rows = list(csv.DictReader(handle))
        forbidden_tokens = ("REAL_", "PRODUCTION_", "ACTUAL_SPOUT", "MATERIAL_RESIDUAL_LAYER")
        if len(named_rows) != 37 or len({row.get("selection_id") for row in named_rows}) != 37:
            failures.append("P1 named-selection contract must contain 37 unique rows")
        if any(any(token in row.get("selection_id", "") for token in forbidden_tokens) for row in named_rows):
            failures.append("P1 named selection implies unsupported production geometry")
        if feature_ids and any(row.get("owner_feature_id") not in feature_ids for row in named_rows):
            failures.append("P1 named-selection contract references an unknown feature")
        named_by_id = {row.get("selection_id"): row for row in named_rows}
        if interface_path.is_file():
            for interface in interface_rows:
                side_a = named_by_id.get(interface.get("named_selection_a"))
                side_b = named_by_id.get(interface.get("named_selection_b"))
                if side_a is None or side_b is None:
                    failures.append(f"P1 interface lacks an exact named-selection pair: {interface.get('interface_id')}")
                elif (
                    side_a.get("owner_feature_id") != interface.get("side_a_feature_id")
                    or side_b.get("owner_feature_id") != interface.get("side_b_feature_id")
                    or interface.get("interface_mode") != "PAIRED_NONCONFORMAL_OR_MATCHED_FACE"
                ):
                    failures.append(f"P1 interface named-selection ownership mismatch: {interface.get('interface_id')}")

    if open_path.is_file():
        with open_path.open(newline="", encoding="utf-8") as handle:
            open_rows = list(csv.DictReader(handle))
        if len(open_rows) != 15 or any(
            row.get("status") != "OPEN" or row.get("product_fact") != "false" for row in open_rows
        ):
            failures.append("P1 open-question contract must retain 15 open non-product-fact rows")
        intake_mapping = next((row for row in open_rows if row.get("question_id") == "OQ002"), {})
        if intake_mapping.get("evidence_class") != "U":
            failures.append("true intake-group count and cell mapping must remain U-class")

    gate_path = repo / "airjet-simulation/checklists/p1_cad_gate_matrix.csv"
    if gate_path.is_file():
        with gate_path.open(newline="", encoding="utf-8") as handle:
            gate_rows = list(csv.DictReader(handle))
        required_gate_columns = {
            "selected_vent_candidate_set_id",
            "selected_orifice_pattern_id",
            "selected_exhaust_branch_id",
            "selected_cell_geometry_rule_id",
            "selected_central_anchor_rule_id",
            "selected_bottom_chamber_rule_id",
            "selected_cell_partition_rule_id",
            "selected_top_chamber_branch_id",
            "selected_perimeter_gap_branch_id",
            "selected_side_frame_closure_branch_id",
            "selected_residual_closure_branch_id",
            "selected_orifice_grid_rule_id",
            "comparison_parent_variant_id",
            "changed_factor",
        }
        gate_columns = set(gate_rows[0]) if gate_rows else set()
        if len(gate_rows) != 252 or len({row.get("variant_id") for row in gate_rows}) != 9:
            failures.append("P1 CAD gate matrix must contain 252 rows across nine variants")
        if any(row.get("status") != "NOT_RUN" for row in gate_rows):
            failures.append("generated P1 CAD gate matrix must remain entirely NOT_RUN")
        if not required_gate_columns.issubset(gate_columns):
            failures.append("P1 CAD gate matrix lacks explicit model-form branch fields")
        scoped_health = {
            row.get("gate_item_id"): row
            for row in gate_rows
            if row.get("gate_item_id") in {"G4_INTERFERENCE", "G4_ZERO_THICKNESS", "G4_DUPLICATE_FACES"}
        }
        if len(scoped_health) != 3 or any(
            "exported physical candidate solids and required fluid bodies" not in row.get("requirement", "")
            for row in scoped_health.values()
        ):
            failures.append("P1 geometry-health Gate scope no longer excludes declared nonphysical datums")

    external_files_path = repo / "airjet-simulation/logs/external-files.csv"
    if external_files_path.is_file():
        with external_files_path.open(newline="", encoding="utf-8") as handle:
            external_rows = list(csv.reader(handle))
        expected_external_header = [
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
        if len(external_rows) != 1 or external_rows[0] != expected_external_header:
            failures.append("external-files.csv must remain an empty canonical P1 artifact manifest")

    review_script = repo / "airjet-simulation/checklists/prepare_p1_cad_review.py"
    if review_script.is_file():
        review_script_text = read_text(review_script)
        for marker in (
            "AJM-WIN-P1-FULL-PRODUCT-CAD-BUILD-006",
            "duplicate report key",
            '"merge-base"',
            "P1 gate input must contain 252 unique gate/variant rows",
            "review packet output must remain outside the Git repository",
            "P1_STAGE_GATE=PENDING_INDEPENDENT_REVIEW",
            "REVIEW_PACKET_PREPARATION=PASS",
            "Preparation PASS does not mean P1 PASS",
            "PureWindowsPath",
            "GATE_EVIDENCE_006_CSV",
            "P1_CONTRACT_BUNDLE_SHA256",
            "load_gate_rows_at_commit",
            "copied run root contains unindexed files",
            '"REPORT_005_COPY"',
            '"PARENT_GEOMETRY_RESULT_DIFF"',
            '"secondary_evidence_original_path"',
            '"secondary_evidence_sha256"',
            '"--finalize-worksheet"',
            '"--spot-check-record"',
            "validate_step_limitation_consistency",
            "P1_REVIEW_RECOMMENDATION=PASS",
            "P1_STAGE_GATE=PENDING_REVIEW_RECORD_COMMIT",
        ):
            if marker not in review_script_text:
                failures.append(f"P1 independent-review script lacks invariant {marker!r}")

    review_method = repo / "airjet-simulation/checklists/P1_CAD_INDEPENDENT_REVIEW_METHOD.md"
    if review_method.is_file():
        review_method_text = read_text(review_method)
        for marker in (
            "P1_REVIEW_RECOMMENDATION=PASS",
            "252",
            "LIMITATION_ACCEPTED",
            "NOT_REVIEWED",
            "PureWindowsPath",
            "006 commit",
            "prepare_p1_cad_review.py",
            "P1 保持 `INCOMPLETE`",
        ):
            if marker not in review_method_text:
                failures.append(f"P1 independent-review method lacks invariant {marker!r}")

    vent_results = repo / "airjet-simulation/evidence/annotated_figures/gen1_vent_homography_results.csv"
    if vent_results.is_file():
        with vent_results.open(newline="", encoding="utf-8") as handle:
            vent_rows = list(csv.DictReader(handle))
        view_counts = {view_id: sum(row.get("view_id") == view_id for row in vent_rows) for view_id in ("flow_636", "upper_547")}
        feature_counts = {
            view_id: len({row.get("feature_id") for row in vent_rows if row.get("view_id") == view_id})
            for view_id in ("flow_636", "upper_547")
        }
        if (
            len(vent_rows) != 8
            or view_counts != {"flow_636": 4, "upper_547": 4}
            or feature_counts != {"flow_636": 4, "upper_547": 4}
        ):
            failures.append("vent homography table must contain four features in each of two views")
        if any(row.get("evidence_class") != "I" for row in vent_rows):
            failures.append("vent homography results must remain I-class")

    cross_view = repo / "airjet-simulation/evidence/annotated_figures/gen1_vent_cross_view_comparison.csv"
    if cross_view.is_file():
        with cross_view.open(newline="", encoding="utf-8") as handle:
            comparison_rows = list(csv.DictReader(handle))
        differences = []
        try:
            differences = [float(row["abs_center_x_difference_mm"]) for row in comparison_rows]
        except (KeyError, TypeError, ValueError):
            failures.append("vent cross-view comparison contains a non-numeric difference")
        if len(comparison_rows) != 4 or len({row.get("feature_id") for row in comparison_rows}) != 4:
            failures.append("vent cross-view comparison must contain four matched features")
        elif len(differences) != 4 or not all(math.isfinite(value) for value in differences):
            failures.append("vent cross-view comparison contains a non-finite difference")
        elif max(differences) < 2.5:
            failures.append("vent cross-view model-form discrepancy was lost or understated")

    p0_record = repo / "airjet-simulation/evidence/P0_EVIDENCE_FREEZE_RECORD.md"
    if p0_record.is_file():
        p0_text = read_text(p0_record)
        for marker in ("PASS - P0 evidence freeze v1", "P1–P6", "四个 elongated top vent objects"):
            if marker not in p0_text:
                failures.append(f"P0 evidence-freeze record lacks boundary marker {marker!r}")

    windows_prompt = repo / "airjet-simulation/windows-prompts/AJM_WIN_P1_READINESS_001.md"
    if windows_prompt.is_file():
        prompt_text = read_text(windows_prompt)
        for marker in (
            "HANDSHAKE_STATUS=P1_HANDOFF_READY",
            "HANDSHAKE_STATUS=P1_BLOCKED",
            "P1_CAD_STATUS=READY",
            "P1_CAD_STATUS=BLOCKED",
            "ACTION_BOUNDARY=DO_NOT_CREATE_CAD",
            "MODEL_BOUNDARY=WORKING_CANDIDATES_NOT_PRODUCT_FACT",
            "P0_GATE_BOUNDARY=P0_EVIDENCE_ONLY_P1_P6_NOT_PASSED",
            "PRESSURE_BOUNDARY=1750_PA_CAPABILITY_FLOW_UNKNOWN",
            "AIRJET_P1_READINESS_REPORT.txt",
            "git status --porcelain",
            "git remote get-url origin",
            "git rev-list --left-right --count HEAD...origin/main",
            "https://github.com/superboynick/win-mac-dual-channel.git",
            "M-3x4-7.0",
            "M+S-3x5-6.0",
            'model_reasoning_effort = "high"',
            "96f65ca6e5c8b8d4bc2b4acdeeb78d9917cf3c5ec2c159055daf88fa3ea261a4",
            "822fbb7e9735a5505734a291083fed7901c1fdfa01cb7de369679e4d41fd19bd",
        ):
            if marker not in prompt_text:
                failures.append(f"Windows P1 prompt lacks invariant {marker!r}")
        if "HANDSHAKE_STATUS=P1_READY" in prompt_text:
            failures.append("Windows P1 prompt uses an ambiguous P1_READY status")

    trial_prompt = repo / "airjet-simulation/windows-prompts/AJM_WIN_ANSYS_OFFICIAL_TRIAL_INSTALL_AND_SMOKE_004.md"
    if trial_prompt.is_file():
        trial_text = read_text(trial_prompt)
        for marker in (
            "AnsysInstaller.exe",
            "OFFICIAL_TRIAL_STATUS=NOT_YET_ENTITLED",
            "OFFICIAL_TRIAL_STATUS=PASS_START_P1_WITH_LIMITATIONS",
            "STEP 不是 P1 唯一硬门槛",
            "禁止截取含这些信息的页面内容",
            "当前 checkout 来自官方 Student 或已开通 trial",
        ):
            if marker not in trial_text:
                failures.append(f"Windows official-trial prompt lacks invariant {marker!r}")

    student_prompt = repo / "airjet-simulation/windows-prompts/AJM_WIN_ANSYS_STUDENT_CAPABILITY_SMOKE_005.md"
    if student_prompt.is_file():
        student_text = read_text(student_prompt)
        for marker in (
            "D:\\ansys\\ANSYS Inc\\ANSYS Student\\v261",
            "git fetch origin",
            "GIT_FETCH=PASS/FAIL",
            "STUDENT_TOOLCHAIN_STATUS=PASS_START_P1",
            "STUDENT_TOOLCHAIN_STATUS=PASS_START_P1_WITH_LIMITATIONS",
            "STUDENT_TOOLCHAIN_STATUS=BLOCKED_CONTAMINATED_BASELINE",
            "P1_CAD_TOOLCHAIN_READINESS=PASS/PASS_WITH_TRANSFER_LIMITATION/BLOCKED",
            "P1_STAGE_GATE=NOT_RUN",
            "NAMED_SELECTION_TRANSFER=PASS/FAIL",
            "STEP 是重要交接能力，但不是唯一硬门槛",
            "SYSTEM_COUPLING_STATUS=UNVERIFIED_WARNING",
            "CUDSS_STATUS=UNVERIFIED_WARNING",
            "AIRJET_ANSYS_STUDENT_CAPABILITY_SMOKE_005.txt",
            "不创建正式 AirJet CAD",
        ):
            if marker not in student_text:
                failures.append(f"Windows Student smoke prompt lacks invariant {marker!r}")
        if "P1_FULL_PRODUCT_CAD=" in student_text:
            failures.append("Windows Student smoke prompt conflates toolchain readiness with the P1 stage Gate")

    cad_prompt = repo / "airjet-simulation/windows-prompts/AJM_WIN_P1_FULL_PRODUCT_CAD_BUILD_006.md"
    if cad_prompt.is_file():
        cad_text = read_text(cad_prompt)
        for marker in (
            "AJM-WIN-P1-FULL-PRODUCT-CAD-BUILD-006",
            "TASK=AJM-WIN-ANSYS-STUDENT-CAPABILITY-SMOKE-005",
            "OLD_PLE_BASELINE=CLEAN",
            "GIT_FETCH=PASS",
            "git merge-base --is-ancestor $Report005Commit HEAD",
            "git remote get-url origin",
            "git rev-parse --abbrev-ref --symbolic-full-name '@{u}'",
            "https://github.com/superboynick/win-mac-dual-channel.git",
            "AIRJET_ANSYS_STUDENT_CAPABILITY_SMOKE_005.txt",
            "build_p1_cad_contracts.py --check",
            "D:\\AirJet_P1\\AJM-P1-CAD-006\\<UTC-run-id>",
            "$RunId = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')",
            "git status --porcelain",
            "ANSYSLMD_LICENSE_FILE=1055@localhost",
            "REPORT_005_GIT_COMMIT=",
            "GIT_ORIGIN=https://github.com/superboynick/win-mac-dual-channel.git",
            "GIT_BRANCH=main",
            "GIT_UPSTREAM=origin/main",
            "FINAL_GIT_CLEAN=PASS/FAIL",
            "C_FREE_GIB=",
            "D_FREE_GIB=",
            "AVAILABLE_RAM_GIB=",
            "LICENSE_SAFETY_CHECK=PASS/FAIL",
            "P1_CONTRACT_BUNDLE_SHA256=",
            "GATE_TEMPLATE_SHA256=",
            "VARIANT_TABLE_SHA256=",
            "INTERNAL_RULES_SHA256=",
            "GATE_EVIDENCE_006_CSV",
            "AUTOMATED_CHECKS_CSV",
            "REPORT_005_COPY",
            "PARENT_GEOMETRY_RESULT_DIFF",
            "secondary_evidence_original_path,secondary_evidence_sha256",
            "excluded_datum_feature_ids",
            "anchor_partition_nonphysical_guard",
            "selected_central_anchor_rule_id=CENTRAL_ANCHOR_SQUARE_DATUM_R0",
            "selected_bottom_chamber_rule_id=BOTTOM_CHAMBER_PER_CELL_SQUARE_R0",
            "selected_cell_partition_rule_id=CELL_PARTITION_DATUM_R0",
            "CONFIGURATIONS_REQUESTED=4",
            "BASE_OR_RESIDUAL_VARIANTS_REQUESTED=6",
            "DERIVED_SINGLE_FACTOR_VARIANTS_REQUESTED=3",
            "TOTAL_VARIANTS_REQUESTED=9",
            "BLOCKED_005_GATE",
            "BLOCKED_GIT_OR_ENVIRONMENT",
            "PARTIAL_CAD_OUTPUT",
            "COMPLETE_WITH_TRANSFER_LIMITATION_AWAITING_REVIEW",
            "COMPLETE_AWAITING_REVIEW",
            "P1_STAGE_GATE=NOT_STARTED/INCOMPLETE/PENDING_PEER_REVIEW",
            "C017_C019_PHYSICS_GUARD=",
            "唯一剩余失败是 005 已知或 006 复现的 STEP",
            "PARAMETER_DIFF_CHECK=PASS_ALL_3_DERIVED/FAIL",
            "GEOMETRY_RESULT_DIFF_CHECK=PASS_ALL_3_DERIVED/FAIL",
            "STEP_EXPORT_REIMPORT=PASS_ALL_9/LIMITATION_RECORDED/FAIL",
            "ANCHOR_PARTITION_NONPHYSICAL_GUARD=PASS_ALL_9/FAIL",
            "TRANSFER_LIMITATION_SCOPE=NONE/STEP_ONLY",
            "REPORT_005_PARSE=UNIQUE_KEYS_REJECT_DUPLICATES_AND_CONFLICTS",
            "REPORT_005_IDENTITY=TASK_COMPUTER_ANSYS_VERSION_INSTALL_ROOT_COMMIT",
            "LICENSE_POLICY=NO_LICENSE_FILE_POOL_SERVICE_REGISTRY_ENV_PRIORITY_CHECKOUT_MUTATION",
            "RESOURCE_THRESHOLDS_GIB=C_FREE_GE_10_D_FREE_GE_20_AVAILABLE_RAM_GE_8",
            "GIT_RECHECK=BEFORE_BUILD_AFTER_EACH_VARIANT_AFTER_FINAL_MANIFEST",
            "STATUS_MAP_BLOCKED_005_GATE=NOT_STARTED",
            "STATUS_MAP_BLOCKED_GIT_OR_ENVIRONMENT=NOT_STARTED",
            "STATUS_MAP_PARTIAL_CAD_OUTPUT=INCOMPLETE",
            "STATUS_MAP_COMPLETE_WITH_TRANSFER_LIMITATION_AWAITING_REVIEW=PENDING_PEER_REVIEW",
            "STATUS_MAP_COMPLETE_AWAITING_REVIEW=PENDING_PEER_REVIEW",
            "P1_PASS_PROHIBITED=006_CAN_ONLY_REACH_PENDING_PEER_REVIEW",
            "005_TRANSFER_LIMITATION_INHERITANCE=REQUIRED",
        ):
            if marker not in cad_text:
                failures.append(f"Windows P1 CAD prompt lacks invariant {marker!r}")
        if re.search(r"(?mi)^\s*(?:[-*+]\s*)?`?P1_STAGE_GATE\s*=\s*PASS(?:\s|`|$)", cad_text):
            failures.append("Windows P1 CAD prompt is allowed to report P1 PASS")

    student_cleanup = repo / "airjet-simulation/reports/AJM_WIN_ANSYS_STUDENT_CLEANUP_2026-07-14.md"
    if student_cleanup.is_file():
        cleanup_text = read_text(student_cleanup)
        for marker in (
            "WINDOWS_ANSYS_STUDENT_CLEANUP_STATUS=PASS",
            "Mac SSH 再验证",
            "python_site_syscplg",
            "cuDSS",
            "不表示 P1--P5 工程能力已全部通过",
        ):
            if marker not in cleanup_text:
                failures.append(f"Student cleanup report lacks boundary marker {marker!r}")

    notebook = repo / "airjet-simulation/notebooks/airjet-mini-layout-baseline.ipynb"
    if notebook.is_file():
        try:
            notebook_data = json.loads(read_text(notebook))
            if notebook_data.get("nbformat") != 4 or not notebook_data.get("cells"):
                failures.append("layout notebook must be a non-empty nbformat 4 document")
            notebook_text = json.dumps(notebook_data, ensure_ascii=False)
            for invariant in ("system_noise_at_50cm_dBA", "geometry_fit", "1750"):
                if invariant not in notebook_text:
                    failures.append(f"layout notebook lacks required invariant {invariant!r}")
        except json.JSONDecodeError as exc:
            failures.append(f"layout notebook is invalid JSON: {exc}")

    manifest = repo / "codex-skills/skills-manifest.json"
    if manifest.is_file():
        try:
            manifest_data = json.loads(read_text(manifest))
            skill_items = manifest_data.get("skills", [])
            names = [item.get("name") for item in skill_items]
            skills = {item["name"]: item for item in skill_items}
            expected_manifest = {
                "airjet-ansys-automation": {
                    "kind": "project",
                    "source": "codex-skills/airjet-ansys-automation",
                    "required_files": [
                        "SKILL.md",
                        "agents/openai.yaml",
                        "references/official-automation-routes.md",
                        "references/gate-evidence.md",
                        "scripts/bootstrap_windows.ps1",
                        "scripts/airjet_ansys_mcp.py",
                        "scripts/run_t0_suite.py",
                        "scripts/run_t1_cad_suite.py",
                        "scripts/run_t1_connected_spaceclaim_suite.py",
                        "scripts/run_t1_semantic_reconstruction_suite.py",
                        "scripts/test_t1_predecessor_negative.py",
                        "scripts/test_airjet_ansys_mcp_policy.py",
                    ],
                },
                "airjet-product-reconstruction": {
                    "kind": "project",
                    "source": "codex-skills/airjet-product-reconstruction",
                    "required_files": [
                        "SKILL.md",
                        "agents/openai.yaml",
                        "references/evidence-rules.md",
                        "references/stage-routing.md",
                        "references/windows-operation.md",
                        "scripts/audit_project.py",
                    ],
                },
                "jupyter-notebook": {
                    "kind": "official",
                    "source": "skills/.curated/jupyter-notebook",
                    "required_files": [
                        "LICENSE.txt",
                        "SKILL.md",
                        "agents/openai.yaml",
                        "assets/experiment-template.ipynb",
                        "assets/jupyter-small.svg",
                        "assets/jupyter.png",
                        "assets/tutorial-template.ipynb",
                        "references/experiment-patterns.md",
                        "references/notebook-structure.md",
                        "references/quality-checklist.md",
                        "references/tutorial-patterns.md",
                        "scripts/new_notebook.py",
                    ],
                },
                "pdf": {
                    "kind": "official",
                    "source": "skills/.curated/pdf",
                    "required_files": ["LICENSE.txt", "SKILL.md", "agents/openai.yaml", "assets/pdf.png"],
                },
            }
            if (
                manifest_data.get("schema_version") != 1
                or manifest_data.get("hash_canonicalization")
                != "UTF-8 text with CRLF and CR normalized to LF"
                or manifest_data.get("official_source", {}).get("repository")
                != "https://github.com/openai/skills.git"
                or manifest_data.get("official_source", {}).get("commit")
                != "49f948faa9258a0c61caceaf225e179651397431"
                or len(names) != 4
                or len(set(names)) != 4
                or set(skills) != set(expected_manifest)
            ):
                failures.append("skills manifest identity/schema/unique-name lock failed")
            for name, expected in expected_manifest.items():
                item = skills.get(name, {})
                if (
                    item.get("kind") != expected["kind"]
                    or item.get("source") != expected["source"]
                    or sorted(item.get("required_files", [])) != sorted(expected["required_files"])
                    or len(item.get("required_files", [])) != len(set(item.get("required_files", [])))
                ):
                    failures.append(f"manifest kind/source/required files changed for {name}")
            for project_skill in (
                item for item in skills.values() if item.get("kind") == "project"
            ):
                skill_entry = repo / project_skill["source"] / "SKILL.md"
                canonical = read_text(skill_entry).replace("\r\n", "\n").replace("\r", "\n")
                actual_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
                if actual_hash != project_skill.get("skill_md_sha256"):
                    failures.append(
                        f"project skill hash does not match skills manifest: {project_skill['name']}"
                    )
            install_sh = read_text(repo / "install-skills.sh") if (repo / "install-skills.sh").is_file() else ""
            for item in skills.values():
                if item.get("skill_md_sha256", "") not in install_sh:
                    failures.append(f"Mac installer does not lock manifest hash for {item['name']}")
                for relative in item.get("required_files", []):
                    if relative not in install_sh:
                        failures.append(
                            f"Mac installer lacks required-file check for {item['name']}: {relative}"
                        )
        except (json.JSONDecodeError, KeyError, OSError) as exc:
            failures.append(f"skills manifest audit failed: {exc}")

    ansys_profiles = repo / "airjet-simulation/automation/ansys/profiles.json"
    if ansys_profiles.is_file():
        try:
            profile_data = json.loads(read_text(ansys_profiles))
            entries = profile_data.get("profiles", [])
            profile_ids = [entry.get("profile_id") for entry in entries]
            required_profile_fields = {
                "profile_id",
                "engine",
                "script",
                "sha256",
                "timeout_seconds",
                "output_root_id",
                "reports",
                "predecessor",
            }
            expected_ansys_profiles = {
                "ajm005-spaceclaim-t0-v1",
                "ajm005-workbench-t0-v1",
                "ajm005-pymechanical-t0-v1",
                "ajm005-pyfluent-t0-v1",
                "ajm005-spaceclaim-cad-t1-v1",
                "ajm005-workbench-transfer-t1-v1",
                "ajm005-workbench-connected-spaceclaim-t1-v1",
                "ajm005-workbench-semantic-reconstruction-t1-v1",
            }
            if (
                set(profile_data) != {"schema_version", "profiles"}
                or profile_data.get("schema_version") != 2
                or set(profile_ids) != expected_ansys_profiles
                or len(profile_ids) != len(set(profile_ids))
            ):
                failures.append("ANSYS profile policy identity/schema/unique-name lock failed")
            approved_root = repo / "airjet-simulation/automation/ansys/approved"
            for entry in entries:
                if set(entry) != required_profile_fields:
                    failures.append(f"ANSYS profile fields changed: {entry.get('profile_id')}")
                    continue
                relative = Path(entry["script"])
                if relative.is_absolute() or ".." in relative.parts or "\\" in entry["script"]:
                    failures.append(f"unsafe ANSYS profile script path: {entry['script']}")
                    continue
                script = approved_root / relative
                if not script.is_file():
                    failures.append(f"missing ANSYS profile script: {entry['script']}")
                    continue
                actual = hashlib.sha256(script.read_bytes()).hexdigest()
                if actual != entry["sha256"]:
                    failures.append(f"ANSYS profile hash mismatch: {entry['profile_id']}")
                if not entry["reports"] or any(
                    not isinstance(report, str) or not report.endswith(".json")
                    for report in entry["reports"]
                ):
                    failures.append(f"invalid ANSYS declared reports: {entry['profile_id']}")
            by_profile_id = {entry.get("profile_id"): entry for entry in entries}
            for entry in entries:
                predecessor = entry.get("predecessor")
                if predecessor is None:
                    continue
                if not isinstance(predecessor, dict) or set(predecessor) != {
                    "profile_id",
                    "report",
                    "required_probe",
                    "required_status",
                    "required_assertions",
                    "artifacts",
                }:
                    failures.append(
                        f"invalid ANSYS predecessor fields: {entry.get('profile_id')}"
                    )
                    continue
                upstream = by_profile_id.get(predecessor.get("profile_id"))
                artifacts = predecessor.get("artifacts")
                required_assertions = predecessor.get("required_assertions")
                if (
                    upstream is None
                    or not isinstance(predecessor.get("required_probe"), str)
                    or not predecessor.get("required_probe")
                    or predecessor.get("required_status")
                    not in {"PASS_005_CAPABILITY", "PASS_PARTIAL_CAD_CAPABILITY"}
                    or not isinstance(required_assertions, list)
                    or not required_assertions
                    or predecessor.get("report") not in upstream.get("reports", [])
                    or not isinstance(artifacts, list)
                    or predecessor.get("report") not in artifacts
                    or upstream.get("output_root_id") != entry.get("output_root_id")
                ):
                    failures.append(
                        f"invalid ANSYS predecessor linkage: {entry.get('profile_id')}"
                    )
        except (AttributeError, json.JSONDecodeError, KeyError, OSError, TypeError) as exc:
            failures.append(f"ANSYS profile policy audit failed: {exc}")

    agents = repo / "AGENTS.md"
    if agents.is_file() and "AIRJET_MINI_FULL_PRODUCT_MASTER_PLAN.md" not in read_text(agents):
        failures.append("AGENTS.md does not identify the full-product master plan")

    powershell_audit = repo / "audit-airjet-project.ps1"
    if powershell_audit.is_file():
        try:
            powershell_audit.read_bytes().decode("ascii")
        except UnicodeDecodeError:
            failures.append("PowerShell 5.1 audit must remain ASCII-safe; encode non-ASCII markers as UTF-8 base64")

    provenance = repo / "airjet-simulation/evidence/SOURCE_PROVENANCE.md"
    if provenance.is_file():
        provenance_text = read_text(provenance)
        for marker in (
            "822fbb7e9735a5505734a291083fed7901c1fdfa01cb7de369679e4d41fd19bd",
            "5f7042dfb2af4a9f37f5a26f792d305d0382b59175d1dfb545a21b96135107b1",
            "page 1",
            "Acoustics of AirJet Mini in system measured at 50 cm (dBA)",
        ):
            if marker not in provenance_text:
                failures.append(f"source provenance lacks Mini sheet identity marker {marker!r}")

    if failures:
        print("FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("PASS")
    print(f"repo={repo}")
    print(f"required_files={len(REQUIRED)}")
    print(f"manuals={len(MANUALS)}")
    print(f"csv_files={len(csv_paths)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

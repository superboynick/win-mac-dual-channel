#!/usr/bin/env python3
"""Audit AirJet project structure and evidence-language invariants."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
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
    "airjet-simulation/evidence/build_layout_candidate_scores.py",
    "airjet-simulation/evidence/extract_official_image_geometry.py",
    "airjet-simulation/evidence/analyze_official_vent_views.py",
    "airjet-simulation/evidence/official_image_measurements.csv",
    "airjet-simulation/evidence/annotated_figures/gen1_vent_homography_results.csv",
    "airjet-simulation/evidence/annotated_figures/gen1_vent_cross_view_comparison.csv",
    "airjet-simulation/evidence/annotated_figures/gen1_top_render_quad_annotated.png",
    "airjet-simulation/evidence/annotated_figures/gen1_cross_section_annotated.png",
    "airjet-simulation/parameters/full_product_parameter_registry.csv",
    "airjet-simulation/checklists/full_product_stage_gates.md",
    "airjet-simulation/SKILLS_AND_GIT_WORKFLOW.md",
    "airjet-simulation/notebooks/airjet-mini-layout-baseline.ipynb",
    "airjet-simulation/notebooks/build_layout_baseline.py",
    "codex-skills/skills-manifest.json",
    "install-skills.ps1",
    "install-skills.sh",
    "audit-airjet-project.ps1",
    "launch-airjet-codex-visible.ps1",
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
                or len(names) != 3
                or len(set(names)) != 3
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
            project_skill = skills.get("airjet-product-reconstruction")
            if project_skill:
                skill_entry = repo / project_skill["source"] / "SKILL.md"
                canonical = read_text(skill_entry).replace("\r\n", "\n").replace("\r", "\n")
                actual_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
                if actual_hash != project_skill.get("skill_md_sha256"):
                    failures.append("project skill hash does not match skills manifest")
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

    agents = repo / "AGENTS.md"
    if agents.is_file() and "AIRJET_MINI_FULL_PRODUCT_MASTER_PLAN.md" not in read_text(agents):
        failures.append("AGENTS.md does not identify the full-product master plan")

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

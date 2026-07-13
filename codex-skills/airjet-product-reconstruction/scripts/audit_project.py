#!/usr/bin/env python3
"""Audit AirJet project structure and evidence-language invariants."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path


REQUIRED = [
    "AGENTS.md",
    "airjet-simulation/README.md",
    "airjet-simulation/AIRJET_MINI_FULL_PRODUCT_MASTER_PLAN.md",
    "airjet-simulation/DECISION_AND_REASONING_ARCHIVE.md",
    "airjet-simulation/MODEL_ANNOTATIONS.md",
    "airjet-simulation/WINDOWS_HANDOFF.md",
    "airjet-simulation/evidence/SOURCE_PROVENANCE.md",
    "airjet-simulation/evidence/product_selection_matrix.csv",
    "airjet-simulation/evidence/airjet_mini_performance_curve_digitized.csv",
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
    forbidden = ["delivered_airflow_chart_units", "功耗—流量曲线"]
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
            elif not float_close(row.get("initial_value", ""), expected) or row.get("status") != status:
                failures.append(f"parameter registry changed locked product target {row_id}")
        try:
            heat_total = float(by_id["D005"]["initial_value"])
            heat_net = float(by_id["D006"]["initial_value"])
            power = float(by_id["D004"]["initial_value"])
            if abs(heat_net + power - heat_total) > 1e-9:
                failures.append("heat accounting invariant failed: Q_net + P_airjet != Q_total")
        except (KeyError, TypeError, ValueError):
            failures.append("heat accounting invariant could not be evaluated")

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
            skills = {item["name"]: item for item in manifest_data.get("skills", [])}
            if set(skills) != {"airjet-product-reconstruction", "jupyter-notebook", "pdf"}:
                failures.append("skills manifest must lock exactly the three project-required skills")
            project_skill = skills.get("airjet-product-reconstruction")
            if project_skill:
                skill_entry = repo / project_skill["source"] / "SKILL.md"
                actual_hash = hashlib.sha256(skill_entry.read_bytes()).hexdigest()
                if actual_hash != project_skill.get("skill_md_sha256"):
                    failures.append("project skill hash does not match skills manifest")
            install_sh = read_text(repo / "install-skills.sh") if (repo / "install-skills.sh").is_file() else ""
            for item in skills.values():
                if item.get("skill_md_sha256", "") not in install_sh:
                    failures.append(f"Mac installer does not lock manifest hash for {item['name']}")
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

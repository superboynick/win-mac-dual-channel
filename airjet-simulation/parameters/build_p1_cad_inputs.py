#!/usr/bin/env python3
"""Generate or verify solver-independent P1 CAD input tables.

The tables preserve evidence classes and make the 2.8 mm closure explicit. They
do not assert that a placeholder layer or layout is the production AirJet Mini.
"""

from __future__ import annotations

import argparse
import csv
import io
import math
from pathlib import Path


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
REGISTRY = HERE / "full_product_parameter_registry.csv"
LAYOUT_SCORES = PROJECT / "evidence" / "layout_candidate_scores.csv"
LAYOUT_OUTPUT = HERE / "p1_layout_configuration_matrix.csv"
THICKNESS_OUTPUT = HERE / "p1_thickness_budget.csv"

ALLOWED_EVIDENCE_CLASSES = {"D", "P", "I", "C", "U"}
REQUIRED_UNITS = {
    "D003": "mm",
    "P002": "mm",
    "P004": "um",
    "P005": "mm",
    "P006": "mm",
    "P007": "mm",
    "P009": "percent",
    "P010": "mm",
    "C009": "mm",
    "C015": "mm",
    "C016": "mm",
    "C017": "mm",
    "C018": "mm",
    "C019": "mm",
    "C020": "fraction",
}

SELECTED_LAYOUTS = {
    "M-3x4-7.0": "PRIMARY-P0",
    "M+S-3x5-6.0": "ALTERNATE-P0",
    "L-2x4-8.0": "LOW-CELL-SENTINEL",
    "S-3x5-5.5": "SMALL-CELL-SENTINEL",
}

THICKNESS_SEQUENCE = [
    ("C015", "TOP_COVER", "candidate solid"),
    ("C019_TOP", "RESIDUAL_TOP_PLACEHOLDER", "derived placeholder solid"),
    ("P005", "TOP_CHAMBER", "fluid"),
    ("P002", "ACTUATOR_EFFECTIVE", "candidate structural solid"),
    ("C018", "BOTTOM_CHAMBER", "fluid"),
    ("C016", "ORIFICE_PLATE", "candidate solid"),
    ("P010", "IMPINGEMENT_CHANNEL", "fluid"),
    ("C017", "INTERNAL_SUPPORT_ALLOWANCE", "aggregate placeholder solid"),
    ("C019_BOTTOM", "RESIDUAL_BOTTOM_PLACEHOLDER", "derived placeholder solid"),
    ("C009", "HEAT_SPREADER", "candidate thermal solid"),
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def registry_by_id() -> dict[str, dict[str, str]]:
    rows = read_csv(REGISTRY)
    by_id = {row["id"]: row for row in rows}
    if len(by_id) != len(rows) or "" in by_id:
        raise ValueError("registry contains duplicate or blank ids")
    for row in rows:
        if row.get("evidence_class") not in ALLOWED_EVIDENCE_CLASSES:
            raise ValueError(f"invalid evidence class for {row.get('id')}")
    for parameter_id, expected_unit in REQUIRED_UNITS.items():
        if parameter_id not in by_id:
            raise ValueError(f"registry missing required parameter {parameter_id}")
        actual_unit = by_id[parameter_id].get("unit")
        if actual_unit != expected_unit:
            raise ValueError(
                f"unit mismatch for {parameter_id}: expected {expected_unit}, got {actual_unit}"
            )
    if by_id["C018"].get("adjustable") != "false":
        raise ValueError("C018 is derived and must not be independently adjustable")
    if by_id["C019"].get("adjustable") != "false":
        raise ValueError("C019 is derived and must not be independently adjustable")
    return by_id


def build_layout_rows(registry: dict[str, dict[str, str]]) -> list[dict[str, object]]:
    d_orifice = float(registry["P007"]["initial_value"])
    porosity = float(registry["P009"]["initial_value"]) / 100.0
    if not math.isfinite(d_orifice) or d_orifice <= 0:
        raise ValueError("P007 orifice diameter must be finite and positive")
    if not math.isfinite(porosity) or not 0.0 < porosity < 1.0:
        raise ValueError("P009 porosity must be strictly between 0 and 100 percent")

    source_rows = read_csv(LAYOUT_SCORES)
    selected = [row for row in source_rows if row.get("candidate_id") in SELECTED_LAYOUTS]
    selected_ids = [row.get("candidate_id", "") for row in selected]
    if len(selected) != len(SELECTED_LAYOUTS) or set(selected_ids) != set(SELECTED_LAYOUTS):
        raise ValueError("the four selected P1 configurations must each exist exactly once")

    hole_area = math.pi * (d_orifice / 2.0) ** 2
    rows: list[dict[str, object]] = []
    for source in selected:
        candidate = source["candidate_id"]
        membrane = float(source["membrane_mm"])
        cell_count = int(source["cell_count"])
        active_area_proxy = cell_count * membrane * membrane
        hole_count_proxy = round(porosity * active_area_proxy / hole_area)
        rows.append(
            {
                "configuration_id": candidate,
                "p1_role": SELECTED_LAYOUTS[candidate],
                "product_fact": "false",
                "evidence_class": "C",
                "source_evidence_classes": "D;P;I",
                "assumption_set": source["assumption_set"],
                "nx": source["nx"],
                "ny": source["ny"],
                "cell_count": source["cell_count"],
                "membrane_mm": source["membrane_mm"],
                "cell_wall_mm": source["cell_wall_mm"],
                "array_span_x_mm": source["array_span_x_mm"],
                "array_span_y_mm": source["array_span_y_mm"],
                "width_margin_mm": source["width_margin_mm"],
                "length_margin_mm": source["length_margin_mm"],
                "active_membrane_area_proxy_mm2": f"{active_area_proxy:.3f}",
                "orifice_diameter_candidate_mm": f"{d_orifice:.3f}",
                "open_area_candidate_pct": f"{porosity * 100:.1f}",
                "porosity_hole_count_proxy": hole_count_proxy,
                "hole_count_status": "PROXY_NOT_CAD_LOCKED",
                "thickness_budget_id": "TB0-PLACEHOLDER",
                "required_topology": "inlet>top_chamber>perimeter_gap>bottom_chamber>orifices>impingement_channel>manifold>single_side_spout",
                "source_refs": "D001,D002,D003,P001,P007,P009,P014; SOURCE_PROVENANCE.md AirJet Mini Data Sheet cross-section single-side integrated spout qualitative topology; layout_candidate_scores.csv",
            }
        )
    return rows


def build_thickness_rows(registry: dict[str, dict[str, str]]) -> list[dict[str, object]]:
    bottom_expected = (
        float(registry["P004"]["initial_value"]) / 1000.0
        + float(registry["P006"]["initial_value"])
    )
    bottom_recorded = float(registry["C018"]["initial_value"])
    if not math.isclose(bottom_expected, bottom_recorded, rel_tol=0.0, abs_tol=1e-12):
        raise ValueError(
            "C018 is stale: expected P004/1000 + P006 = "
            f"{bottom_expected:.12f} mm, found {bottom_recorded:.12f} mm"
        )

    envelope = float(registry["D003"]["initial_value"])
    allocated_ids = ["C015", "P005", "P002", "C018", "C016", "P010", "C009", "C017"]
    allocated = sum(float(registry[item]["initial_value"]) for item in allocated_ids)
    residual_expected = envelope - allocated
    residual = float(registry["C019"]["initial_value"])
    if residual < 0 or not math.isfinite(residual):
        raise ValueError("C019 residual must be finite and non-negative")
    if not math.isclose(residual_expected, residual, rel_tol=0.0, abs_tol=1e-12):
        raise ValueError(
            "C019 is stale: expected D003 - allocated stack = "
            f"{residual_expected:.12f} mm, found {residual:.12f} mm"
        )

    top_fraction = float(registry["C020"]["initial_value"])
    if not math.isfinite(top_fraction) or not 0.0 <= top_fraction <= 1.0:
        raise ValueError("C020 residual top fraction must be within [0, 1]")
    derived = {
        "C019_TOP": residual * top_fraction,
        "C019_BOTTOM": residual * (1.0 - top_fraction),
    }

    rows: list[dict[str, object]] = []
    z = 0.0
    for order, (parameter_id, component, representation) in enumerate(
        reversed(THICKNESS_SEQUENCE), start=1
    ):
        if parameter_id in derived:
            value = derived[parameter_id]
            evidence_class = "U"
            status = "DERIVED_UNRESOLVED_PLACEHOLDER"
            range_text = "depends on C019 and C020"
            source_ref = "C019,C020"
        else:
            source = registry[parameter_id]
            value = float(source["initial_value"])
            evidence_class = source["evidence_class"]
            status = source["status"]
            range_text = source["uncertainty_or_range"]
            source_ref = parameter_id

        if parameter_id == "P002":
            applicability = "8 mm patent-element thickness reused only as a cross-size CAD placeholder; branch by membrane size before P2"
            solver_use = "GEOMETRY_ONLY_UNTIL_SIZE_SPECIFIC_P2_BRANCH"
        elif parameter_id in {"C017", "C019_TOP", "C019_BOTTOM"}:
            applicability = "unresolved one-dimensional thickness bookkeeping; not an identified physical continuous layer"
            solver_use = "GEOMETRY_ONLY_NO_MATERIAL_NO_MASS_NO_STRUCTURAL_NO_CHT"
        elif representation == "fluid":
            applicability = "P1 candidate fluid geometry; validate connectivity and collision"
            solver_use = "P1_GEOMETRY_FLUID"
        else:
            applicability = "P1 candidate geometry; material and physics require their own evidence records"
            solver_use = "P1_GEOMETRY_CANDIDATE"

        z_next = z + value
        rows.append(
            {
                "budget_id": "TB0-PLACEHOLDER",
                "bottom_up_order": order,
                "component": component,
                "parameter_id": parameter_id,
                "thickness_mm": f"{value:.6f}",
                "z_min_mm": f"{z:.6f}",
                "z_max_mm": f"{z_next:.6f}",
                "representation": representation,
                "evidence_class": evidence_class,
                "status": status,
                "uncertainty_or_range": range_text,
                "source_or_derivation": source_ref,
                "product_fact": "false",
                "applicability_note": applicability,
                "solver_use": solver_use,
                "gate_note": "C019 placement is unresolved; exact 2.8 mm closure is geometric only, not internal-structure identification",
            }
        )
        z = z_next

    if not math.isclose(z, envelope, rel_tol=0.0, abs_tol=1e-9):
        raise ValueError(f"TB0 thickness does not close: {z:.12f} mm vs D003={envelope:.12f} mm")
    return rows


def render_csv(rows: list[dict[str, object]]) -> str:
    if not rows:
        raise ValueError("cannot render an empty CSV")
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


def write_or_check(path: Path, content: str, check: bool) -> None:
    if check:
        # Git may check text files out as CRLF on Windows and LF on macOS.
        # Universal-newline reading keeps deterministic generated-content checks
        # independent of the workstation's checkout convention.
        with path.open(newline=None, encoding="utf-8") as handle:
            actual = handle.read()
        if actual != content:
            raise ValueError(f"generated output is stale: {path}")
    else:
        with path.open("w", newline="", encoding="utf-8") as handle:
            handle.write(content)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="verify outputs without rewriting them")
    args = parser.parse_args()

    registry = registry_by_id()
    layout_rows = build_layout_rows(registry)
    thickness_rows = build_thickness_rows(registry)
    write_or_check(LAYOUT_OUTPUT, render_csv(layout_rows), args.check)
    write_or_check(THICKNESS_OUTPUT, render_csv(thickness_rows), args.check)
    mode = "check" if args.check else "write"
    print(f"PASS mode={mode} layout_output={LAYOUT_OUTPUT}")
    print(f"PASS mode={mode} thickness_output={THICKNESS_OUTPUT}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Build the P0 AirJet Mini layout score table from explicit assumptions.

Only geometry and a low-weight cell-count complexity proxy are scored at P0.
Unknown physics scores remain empty and are never re-normalized away.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
OUTPUT = HERE / "layout_candidate_scores.csv"

PRODUCT_WIDTH_MM = 27.5
PRODUCT_LENGTH_MM = 41.5
ASSUMPTION_SET = "A0"
SIDE_MARGIN_MM = 1.0
INLET_EXHAUST_ALLOWANCE_MM = 5.0
CELL_WALL_MM = 0.25

FAMILIES = {
    "L": {"membrane_mm": [8.0, 9.0, 10.0], "nx": [2, 3], "ny": [3, 4]},
    "M": {"membrane_mm": [6.0, 7.0, 8.0], "nx": [3], "ny": [4, 5]},
    "S": {"membrane_mm": [4.5, 5.0, 5.5, 6.0], "nx": [3, 4], "ny": [5, 6]},
}

SCORE_WEIGHTS = {
    "S_geometry": 15,
    "S_image": 10,
    "S_modal": 15,
    "S_power": 15,
    "S_flow": 20,
    "S_thermal": 20,
    "S_complexity": 5,
}

FIELDS = [
    "candidate_id",
    "geometry_key",
    "family_tags",
    "assumption_set",
    "membrane_mm",
    "nx",
    "ny",
    "cell_count",
    "cell_wall_mm",
    "side_margin_mm",
    "inlet_exhaust_allowance_mm",
    "array_span_x_mm",
    "array_span_y_mm",
    "used_width_mm",
    "used_length_mm",
    "width_margin_mm",
    "length_margin_mm",
    "membrane_area_proxy_pct",
    "patent_range_relation",
    "hard_evidence",
    "hard_envelope",
    "hard_topology",
    "hard_thickness",
    "hard_cad",
    "hard_power",
    "hard_flow",
    "hard_thermal",
    "S_geometry",
    "S_image",
    "S_modal",
    "S_power",
    "S_flow",
    "S_thermal",
    "S_complexity",
    "score_coverage_pct",
    "weighted_score_100",
    "rank_tier",
    "status",
    "score_evidence_refs",
    "rejection_reason",
    "next_required_test",
]


def used_span(count: int, membrane: float) -> float:
    return count * membrane + (count - 1) * CELL_WALL_MM


def geometry_score(width_margin: float, length_margin: float) -> int:
    minimum = min(width_margin, length_margin)
    if minimum < 0:
        return 0
    if minimum == 0:
        return 1
    if minimum < 1:
        return 2
    if minimum < 2:
        return 3
    if minimum < 4:
        return 4
    return 5


def complexity_score(cell_count: int) -> int:
    if cell_count <= 8:
        return 5
    if cell_count <= 12:
        return 4
    if cell_count <= 16:
        return 3
    if cell_count <= 20:
        return 2
    return 1


def patent_relation(membrane: float) -> str:
    if 6.0 <= membrane <= 8.0:
        return "within_6_to_8_mm_preferred_patent_family"
    if 4.0 <= membrane <= 10.0:
        return "within_4_to_10_mm_broad_patent_family"
    return "outside_recorded_patent_family"


def enumerate_raw() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for family, spec in FAMILIES.items():
        for membrane in spec["membrane_mm"]:
            for nx in spec["nx"]:
                for ny in spec["ny"]:
                    span_x = used_span(nx, membrane)
                    span_y = used_span(ny, membrane)
                    used_width = span_x + 2 * SIDE_MARGIN_MM
                    used_length = span_y + INLET_EXHAUST_ALLOWANCE_MM
                    rows.append(
                        {
                            "family": family,
                            "membrane_mm": membrane,
                            "nx": nx,
                            "ny": ny,
                            "cell_count": nx * ny,
                            "array_span_x_mm": span_x,
                            "array_span_y_mm": span_y,
                            "used_width_mm": used_width,
                            "used_length_mm": used_length,
                            "width_margin_mm": PRODUCT_WIDTH_MM - used_width,
                            "length_margin_mm": PRODUCT_LENGTH_MM - used_length,
                        }
                    )
    return rows


def geometry_key(row: dict[str, object]) -> str:
    membrane_token = str(row["membrane_mm"]).replace(".", "p")
    return (
        f"nx{row['nx']}-ny{row['ny']}-mem{membrane_token}-wall{CELL_WALL_MM}"
        f"-side{SIDE_MARGIN_MM}-allow{INLET_EXHAUST_ALLOWANCE_MM}-{ASSUMPTION_SET}"
    )


def build_rows() -> list[dict[str, object]]:
    groups: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in enumerate_raw():
        groups[geometry_key(row)].append(row)

    output: list[dict[str, object]] = []
    for key, duplicates in sorted(groups.items()):
        row = duplicates[0]
        families = "+".join(sorted(str(item["family"]) for item in duplicates))
        membrane = float(row["membrane_mm"])
        nx = int(row["nx"])
        ny = int(row["ny"])
        cell_count = int(row["cell_count"])
        width_margin = float(row["width_margin_mm"])
        length_margin = float(row["length_margin_mm"])
        fits = width_margin >= 0 and length_margin >= 0
        s_geometry = geometry_score(width_margin, length_margin)
        s_complexity = complexity_score(cell_count)
        weighted = (
            SCORE_WEIGHTS["S_geometry"] * s_geometry / 5
            + SCORE_WEIGHTS["S_complexity"] * s_complexity / 5
            if fits
            else ""
        )

        nominal_id = f"{families}-{nx}x{ny}-{membrane:.1f}"
        rank_tier = "UNRANKED-FIT"
        status = "P0_GEOMETRY_FIT_ONLY"
        next_test = "P1 thickness budget and connected full-product CAD; then P2/P3/P4/P5 physics gates"
        if (families, nx, ny, membrane) == ("M", 3, 4, 7.0):
            rank_tier = "PRIMARY-P0"
            status = "WORKING_PRIMARY_NOT_PRODUCT_FACT"
        elif (families, nx, ny, membrane) == ("M+S", 3, 5, 6.0):
            rank_tier = "ALTERNATE-P0"
            status = "WORKING_ALTERNATE_NOT_PRODUCT_FACT"
        elif (families, nx, ny, membrane) in {
            ("L", 2, 4, 8.0),
            ("S", 3, 5, 5.5),
        }:
            rank_tier = "BRANCH-SENTINEL"
            status = "PRESERVE_FOR_MODEL_FORM_UNCERTAINTY"
        if not fits:
            rank_tier = "FAIL-CONFIG-A0"
            status = "FAILS_CURRENT_ASSUMPTION_SET_ONLY"
            next_test = "Change only an explicit A0 allowance with evidence; do not permanently reject from package envelope alone"

        output.append(
            {
                "candidate_id": nominal_id,
                "geometry_key": key,
                "family_tags": families,
                "assumption_set": ASSUMPTION_SET,
                "membrane_mm": f"{membrane:.1f}",
                "nx": nx,
                "ny": ny,
                "cell_count": cell_count,
                "cell_wall_mm": f"{CELL_WALL_MM:.2f}",
                "side_margin_mm": f"{SIDE_MARGIN_MM:.2f}",
                "inlet_exhaust_allowance_mm": f"{INLET_EXHAUST_ALLOWANCE_MM:.2f}",
                "array_span_x_mm": f"{float(row['array_span_x_mm']):.2f}",
                "array_span_y_mm": f"{float(row['array_span_y_mm']):.2f}",
                "used_width_mm": f"{float(row['used_width_mm']):.2f}",
                "used_length_mm": f"{float(row['used_length_mm']):.2f}",
                "width_margin_mm": f"{width_margin:.2f}",
                "length_margin_mm": f"{length_margin:.2f}",
                "membrane_area_proxy_pct": f"{100 * cell_count * membrane * membrane / (PRODUCT_WIDTH_MM * PRODUCT_LENGTH_MM):.2f}",
                "patent_range_relation": patent_relation(membrane),
                "hard_evidence": "PASS_P0_CLASSIFIED",
                "hard_envelope": "PASS_CONFIG_A0" if fits else "FAIL_CONFIG_A0",
                "hard_topology": "PENDING_P1",
                "hard_thickness": "PENDING_P1",
                "hard_cad": "PENDING_P1",
                "hard_power": "PENDING_P2",
                "hard_flow": "PENDING_P3_P4",
                "hard_thermal": "PENDING_P5",
                "S_geometry": s_geometry,
                "S_image": "",
                "S_modal": "",
                "S_power": "",
                "S_flow": "",
                "S_thermal": "",
                "S_complexity": s_complexity,
                "score_coverage_pct": 20 if fits else 0,
                "weighted_score_100": f"{weighted:.1f}" if weighted != "" else "",
                "rank_tier": rank_tier,
                "status": status,
                "score_evidence_refs": "D001,D002,P001,P014; image score intentionally pending",
                "rejection_reason": "" if fits else "Package fit fails only under current A0 allowance assumptions",
                "next_required_test": next_test,
            }
        )
    return sorted(
        output,
        key=lambda row: (
            {"PRIMARY-P0": 0, "ALTERNATE-P0": 1, "BRANCH-SENTINEL": 2, "UNRANKED-FIT": 3, "FAIL-CONFIG-A0": 4}[str(row["rank_tier"])],
            -float(row["weighted_score_100"] or -1),
            str(row["candidate_id"]),
        ),
    )


def main() -> None:
    rows = build_rows()
    with OUTPUT.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    raw_count = len(enumerate_raw())
    fit_count = sum(row["hard_envelope"] == "PASS_CONFIG_A0" for row in rows)
    print(f"PASS raw={raw_count} unique={len(rows)} unique_fit={fit_count} output={OUTPUT}")


if __name__ == "__main__":
    main()

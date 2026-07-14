#!/usr/bin/env python3
"""Generate or verify the evidence-safe P1 full-product CAD contract package.

The generated tables turn the P0 registry and the frozen P1 work configurations
into explicit CAD inputs, feature contracts, interfaces, named selections, open
questions, and NOT_RUN gate rows.  They do not create CAD and do not identify
the production AirJet Mini internal structure.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import build_p1_cad_inputs as base


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
CONTRACT_DIR = PROJECT / "geometry" / "contracts"

VARIANT_OUTPUT = HERE / "p1_model_form_variants.csv"
PARAMETER_MAP_OUTPUT = HERE / "p1_cad_parameter_map.csv"
ORIFICE_OUTPUT = HERE / "p1_orifice_pattern_candidates.csv"
VENT_OUTPUT = HERE / "p1_vent_geometry_candidates.csv"
PLANFORM_OUTPUT = HERE / "p1_planform_exhaust_candidates.csv"
INTERNAL_RULE_OUTPUT = HERE / "p1_internal_geometry_rules.csv"
FEATURE_OUTPUT = CONTRACT_DIR / "p1_cad_features.csv"
BINDING_OUTPUT = CONTRACT_DIR / "p1_cad_feature_parameter_bindings.csv"
INTERFACE_OUTPUT = CONTRACT_DIR / "p1_cad_interfaces.csv"
NAMED_SELECTION_OUTPUT = CONTRACT_DIR / "p1_cad_named_selections.csv"
OPEN_QUESTION_OUTPUT = CONTRACT_DIR / "p1_cad_open_questions.csv"
GATE_OUTPUT = PROJECT / "checklists" / "p1_cad_gate_matrix.csv"
OFFICIAL_IMAGE_MEASUREMENTS = PROJECT / "evidence" / "official_image_measurements.csv"
VENT_HOMOGRAPHY_RESULTS = (
    PROJECT / "evidence" / "annotated_figures" / "gen1_vent_homography_results.csv"
)


def build_variant_rows(
    registry: dict[str, dict[str, str]], layout_rows: list[dict[str, object]]
) -> list[dict[str, object]]:
    layouts = {str(row["configuration_id"]): row for row in layout_rows}
    if set(layouts) != set(base.SELECTED_LAYOUTS):
        raise ValueError("variant builder requires the four frozen P1 configurations")

    residual = float(registry["C019"]["initial_value"])
    specs = [
        ("M-3x4-7.0", "R25_BOTTOM_HEAVY", 0.25, "PRIMARY_THICKNESS_SWEEP", "BASE_OR_RESIDUAL", "", "C020_RESIDUAL_POSITION", "VENT_FLOW_BBOX_R0", "PHI_DERIVED_SQUARE", "EXH_FULL_WIDTH_RECT_R0"),
        ("M-3x4-7.0", "R50_BALANCED", 0.50, "PRIMARY_DELIVERY", "BASELINE", "", "BASELINE", "VENT_FLOW_BBOX_R0", "PHI_DERIVED_SQUARE", "EXH_FULL_WIDTH_RECT_R0"),
        ("M-3x4-7.0", "R75_TOP_HEAVY", 0.75, "PRIMARY_THICKNESS_SWEEP", "BASE_OR_RESIDUAL", "", "C020_RESIDUAL_POSITION", "VENT_FLOW_BBOX_R0", "PHI_DERIVED_SQUARE", "EXH_FULL_WIDTH_RECT_R0"),
        ("M+S-3x5-6.0", "R50_BALANCED", 0.50, "ALTERNATE_DELIVERY", "BASELINE", "", "CONFIGURATION", "VENT_FLOW_BBOX_R0", "PHI_DERIVED_SQUARE", "EXH_FULL_WIDTH_RECT_R0"),
        ("L-2x4-8.0", "R50_BALANCED", 0.50, "LOW_CELL_SENTINEL", "BASELINE", "", "CONFIGURATION", "VENT_FLOW_BBOX_R0", "PHI_DERIVED_SQUARE", "EXH_FULL_WIDTH_RECT_R0"),
        ("S-3x5-5.5", "R50_BALANCED", 0.50, "SMALL_CELL_SENTINEL", "BASELINE", "", "CONFIGURATION", "VENT_FLOW_BBOX_R0", "PHI_DERIVED_SQUARE", "EXH_FULL_WIDTH_RECT_R0"),
        ("M-3x4-7.0", "R50_VENT_UPPER", 0.50, "PRIMARY_SINGLE_FACTOR", "DERIVED_SINGLE_FACTOR", "M-3x4-7.0__R50_BALANCED", "VENT_GEOMETRY", "VENT_UPPER_CENTERLINE_P013_R0", "PHI_DERIVED_SQUARE", "EXH_FULL_WIDTH_RECT_R0"),
        ("M-3x4-7.0", "R50_ORIFICE_EDGE_GAP", 0.50, "PRIMARY_SINGLE_FACTOR", "DERIVED_SINGLE_FACTOR", "M-3x4-7.0__R50_BALANCED", "ORIFICE_INTERPRETATION", "VENT_FLOW_BBOX_R0", "P008_AS_EDGE_GAP", "EXH_FULL_WIDTH_RECT_R0"),
        ("M-3x4-7.0", "R50_EXHAUST_HALF_TAPER", 0.50, "PRIMARY_SINGLE_FACTOR", "DERIVED_SINGLE_FACTOR", "M-3x4-7.0__R50_BALANCED", "EXHAUST_PLANFORM", "VENT_FLOW_BBOX_R0", "PHI_DERIVED_SQUARE", "EXH_CENTER_HALF_TAPER_R0"),
    ]
    rows: list[dict[str, object]] = []
    for configuration_id, suffix, top_fraction, gate_role, variant_kind, parent, changed_factor, vent_set, orifice_suffix, exhaust_suffix in specs:
        top = residual * top_fraction
        bottom = residual - top
        rows.append(
            {
                "variant_id": f"{configuration_id}__{suffix}",
                "configuration_id": configuration_id,
                "p1_role": layouts[configuration_id]["p1_role"],
                "gate_role": gate_role,
                "variant_kind": variant_kind,
                "comparison_parent_variant_id": parent,
                "changed_factor": changed_factor,
                "thickness_budget_family": "TB0-PLACEHOLDER",
                "C020_residual_top_fraction": f"{top_fraction:.2f}",
                "C019_residual_total_mm": f"{residual:.6f}",
                "residual_top_mm": f"{top:.6f}",
                "residual_bottom_mm": f"{bottom:.6f}",
                "vent_candidate_set_id": vent_set,
                "orifice_pattern_id": f"{configuration_id}__{orifice_suffix}",
                "exhaust_branch_id": f"{configuration_id}__{exhaust_suffix}",
                "cell_geometry_rule_id": "CELL_CENTER_AND_TILE_R0",
                "central_anchor_rule_id": "CENTRAL_ANCHOR_SQUARE_DATUM_R0",
                "bottom_chamber_rule_id": "BOTTOM_CHAMBER_PER_CELL_SQUARE_R0",
                "cell_partition_rule_id": "CELL_PARTITION_DATUM_R0",
                "top_chamber_branch_id": "TOP_SHARED_PLENUM_R0",
                "perimeter_gap_branch_id": "PERIM_SPLIT_GAP_R0",
                "side_frame_closure_branch_id": "SIDE_WALL_BOUNDARY_R0",
                "residual_closure_branch_id": "RESIDUAL_NUMERICAL_CLOSURE_R0",
                "orifice_grid_rule_id": "ORIFICE_PER_CELL_CENTERED_CLIP_R0",
                "evidence_class": "C",
                "source_evidence_classes": "D;P;I;C;U",
                "product_fact": "false",
                "solver_use": "P1_GEOMETRY_BRANCH_ONLY",
                "status": "CANDIDATE_NOT_RUN",
                "notes": "C019 placement sensitivity only; residual bodies have no material, mass, structural, or CHT role",
            }
        )

    fractions = {
        float(row["C020_residual_top_fraction"])
        for row in rows
        if row["configuration_id"] == "M-3x4-7.0"
    }
    if fractions != {0.25, 0.50, 0.75}:
        raise ValueError("primary configuration must retain 0.25/0.50/0.75 residual branches")
    if any(
        not math.isclose(
            float(row["residual_top_mm"]) + float(row["residual_bottom_mm"]),
            residual,
            rel_tol=0.0,
            abs_tol=1e-9,
        )
        for row in rows
    ):
        raise ValueError("variant residual split does not close")
    derived = [row for row in rows if row["variant_kind"] == "DERIVED_SINGLE_FACTOR"]
    if len(rows) != 9 or len(derived) != 3 or {
        str(row["changed_factor"]) for row in derived
    } != {"VENT_GEOMETRY", "ORIFICE_INTERPRETATION", "EXHAUST_PLANFORM"}:
        raise ValueError("variant table must retain six base/residual and three single-factor runs")
    baseline = next(row for row in rows if row["variant_id"] == "M-3x4-7.0__R50_BALANCED")
    branch_fields = ("vent_candidate_set_id", "orifice_pattern_id", "exhaust_branch_id")
    for row in derived:
        changes = sum(row[field] != baseline[field] for field in branch_fields)
        if row["comparison_parent_variant_id"] != baseline["variant_id"] or changes != 1:
            raise ValueError(f"derived variant is not single-factor: {row['variant_id']}")
    return rows


def build_parameter_map_rows(
    registry: dict[str, dict[str, str]],
    layout_rows: list[dict[str, object]],
    variant_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    layouts = {str(row["configuration_id"]): row for row in layout_rows}
    generic = [
        ("D001", "PRODUCT_WIDTH", "P1_ENVELOPE_LOCK"),
        ("D002", "PRODUCT_LENGTH", "P1_ENVELOPE_LOCK"),
        ("D003", "PRODUCT_THICKNESS", "P1_ENVELOPE_LOCK"),
        ("P002", "MEMBRANE_EFFECTIVE_THICKNESS_R0", "GEOMETRY_ONLY_UNTIL_SIZE_SPECIFIC_P2_BRANCH"),
        ("P004", "MEMBRANE_TIP_AMPLITUDE_CANDIDATE", "CLEARANCE_CHECK_ONLY"),
        ("P005", "TOP_CHAMBER_HEIGHT_CANDIDATE", "P1_GEOMETRY_FLUID"),
        ("P006", "BOTTOM_CLEARANCE_MARGIN_CANDIDATE", "CLEARANCE_CHECK_ONLY"),
        ("P007", "ORIFICE_EQUIVALENT_DIAMETER_CANDIDATE", "P1_GEOMETRY_FLUID"),
        ("P008", "ORIFICE_SEPARATION_S_UNRESOLVED", "INTERPRETATION_BRANCH_ONLY"),
        ("P009", "ORIFICE_OPEN_AREA_TARGET_CANDIDATE", "P1_GEOMETRY_FLUID"),
        ("P010", "IMPINGEMENT_GAP_CANDIDATE", "P1_GEOMETRY_FLUID"),
        ("P012", "CENTRAL_ANCHOR_WIDTH_CANDIDATE", "P1_GEOMETRY_ONLY_UNTIL_P2"),
        ("P013", "TOP_VENT_WIDTH_PATENT_CANDIDATE", "P1_GEOMETRY_CANDIDATE"),
        ("C004", "INTAKE_GEOMETRY_DATASET", "DUAL_VIEW_I_CLASS_CANDIDATE"),
        ("C005", "EXHAUST_MANIFOLD_GEOMETRY", "U_TO_C_BRANCH_REQUIRED"),
        ("C007", "ACTUATOR_LAYER_STACK", "NO_MATERIAL_ASSIGNMENT_P1"),
        ("C009", "HEAT_SPREADER_THICKNESS_CANDIDATE", "P1_GEOMETRY_NO_MATERIAL_NO_MASS"),
        ("C013", "ACTIVE_AREA_FRACTION_IMAGE_TARGET", "I_CLASS_PENDING"),
        ("C014", "DRAWN_VENT_OBJECT_COUNT_NOT_GROUP_COUNT", "DRAWN_OBJECTS_ONLY"),
        ("C015", "TOP_COVER_THICKNESS_CANDIDATE", "P1_GEOMETRY_NO_MATERIAL_NO_MASS"),
        ("C016", "ORIFICE_PLATE_THICKNESS_CANDIDATE", "P1_GEOMETRY_NO_MATERIAL_NO_MASS"),
        ("C017", "INTERNAL_SUPPORT_ALLOWANCE_REF", "GEOMETRY_ONLY_NO_MATERIAL_NO_MASS_NO_STRUCTURAL_NO_CHT"),
        ("C018", "BOTTOM_CHAMBER_HEIGHT_DERIVED", "P1_GEOMETRY_FLUID"),
        ("C019", "UNRESOLVED_STACK_RESIDUAL_TOTAL", "GEOMETRY_ONLY_NO_MATERIAL_NO_MASS_NO_STRUCTURAL_NO_CHT"),
    ]
    layout_fields = [
        ("C001", "N_CELL", "cell_count", "count"),
        ("C002", "N_ROW", "ny", "count"),
        ("C003", "N_COLUMN", "nx", "count"),
        ("P001", "MEMBRANE_EFFECTIVE_LENGTH_SELECTED", "membrane_mm", "mm"),
        ("P014", "CELL_WALL_CLEARANCE_SELECTED", "cell_wall_mm", "mm"),
        ("LAYOUT_SPAN_X", "ARRAY_SPAN_X", "array_span_x_mm", "mm"),
        ("LAYOUT_SPAN_Y", "ARRAY_SPAN_Y", "array_span_y_mm", "mm"),
        ("LAYOUT_MARGIN_X", "ARRAY_MARGIN_X", "width_margin_mm", "mm"),
        ("LAYOUT_MARGIN_Y", "ARRAY_MARGIN_Y", "length_margin_mm", "mm"),
        ("LAYOUT_ACTIVE_AREA_PROXY", "ACTIVE_MEMBRANE_AREA_PROXY", "active_membrane_area_proxy_mm2", "mm2"),
        ("LAYOUT_HOLE_COUNT_PROXY", "POROSITY_HOLE_COUNT_PROXY", "porosity_hole_count_proxy", "count"),
    ]

    rows: list[dict[str, object]] = []

    def append_row(
        *,
        configuration_id: str,
        variant_id: str,
        parameter_id: str,
        cad_variable: str,
        value: object,
        unit: str,
        evidence_class: str,
        status: str,
        adjustable: str,
        source_id: str,
        source_locator: str,
        derivation: str,
        solver_use: str,
        geometry_only: str,
        notes: str,
        product_fact: str = "false",
    ) -> None:
        rows.append(
            {
                "configuration_id": configuration_id,
                "variant_id": variant_id,
                "parameter_id": parameter_id,
                "cad_variable": cad_variable,
                "value": value,
                "unit": unit,
                "evidence_class": evidence_class,
                "status": status,
                "adjustable": adjustable,
                "source_id": source_id,
                "source_locator": source_locator,
                "derivation": derivation,
                "solver_use": solver_use,
                "geometry_only": geometry_only,
                "product_fact": product_fact,
                "notes": notes,
            }
        )

    for variant in variant_rows:
        configuration_id = str(variant["configuration_id"])
        variant_id = str(variant["variant_id"])
        layout = layouts[configuration_id]
        for parameter_id, cad_variable, solver_use in generic:
            source = registry[parameter_id]
            geometry_only = (
                "true"
                if parameter_id in {"P002", "C007", "C017", "C019"}
                else "false"
            )
            append_row(
                configuration_id=configuration_id,
                variant_id=variant_id,
                parameter_id=parameter_id,
                cad_variable=cad_variable,
                value=source["initial_value"],
                unit=source["unit"],
                evidence_class=source["evidence_class"],
                status=source["status"],
                adjustable=source["adjustable"],
                source_id=parameter_id,
                source_locator=source["evidence_source"],
                derivation=source["derivation_or_parent"],
                solver_use=solver_use,
                geometry_only=geometry_only,
                notes=source["uncertainty_or_range"],
                product_fact="true" if parameter_id in {"D001", "D002", "D003"} else "false",
            )

        for parameter_id, cad_variable, field, unit in layout_fields:
            source_id = parameter_id if parameter_id in registry else "p1_layout_configuration_matrix"
            source_locator = (
                registry[parameter_id]["evidence_source"]
                if parameter_id in registry
                else f"p1_layout_configuration_matrix.csv:{configuration_id}"
            )
            append_row(
                configuration_id=configuration_id,
                variant_id=variant_id,
                parameter_id=parameter_id,
                cad_variable=cad_variable,
                value=layout[field],
                unit=unit,
                evidence_class="C",
                status="FROZEN_P1_WORK_CONFIGURATION_NOT_PRODUCT_FACT",
                adjustable="false",
                source_id=source_id,
                source_locator=source_locator,
                derivation=f"selected configuration {configuration_id} within P0 candidate envelope",
                solver_use="P1_GEOMETRY_CONFIGURATION",
                geometry_only="false",
                notes="configuration selection; source patent/image classes do not make this production geometry",
            )

        top_fraction = float(variant["C020_residual_top_fraction"])
        residual_total = float(variant["C019_residual_total_mm"])
        derived_rows = [
            ("C020", "RESIDUAL_TOP_FRACTION_BRANCH", top_fraction, "fraction", "C"),
            ("C019_TOP", "RESIDUAL_TOP_THICKNESS_REF", residual_total * top_fraction, "mm", "U"),
            ("C019_BOTTOM", "RESIDUAL_BOTTOM_THICKNESS_REF", residual_total * (1.0 - top_fraction), "mm", "U"),
        ]
        for parameter_id, cad_variable, value, unit, evidence_class in derived_rows:
            append_row(
                configuration_id=configuration_id,
                variant_id=variant_id,
                parameter_id=parameter_id,
                cad_variable=cad_variable,
                value=f"{value:.6f}",
                unit=unit,
                evidence_class=evidence_class,
                status="MODEL_FORM_BRANCH_GEOMETRY_ONLY",
                adjustable="false",
                source_id="C019;C020",
                source_locator="full_product_parameter_registry.csv and p1_model_form_variants.csv",
                derivation=(
                    "C020 branch selection"
                    if parameter_id == "C020"
                    else "C019*C020" if parameter_id == "C019_TOP" else "C019*(1-C020)"
                ),
                solver_use="GEOMETRY_ONLY_NO_MATERIAL_NO_MASS_NO_STRUCTURAL_NO_CHT",
                geometry_only="true",
                notes="bookkeeping reference; not an identified physical layer",
            )

    if any(row["evidence_class"] not in base.ALLOWED_EVIDENCE_CLASSES for row in rows):
        raise ValueError("parameter map contains an invalid evidence class")
    if any(row["unit"] == "" for row in rows):
        raise ValueError("parameter map contains a blank unit")
    return rows


def build_orifice_rows(
    registry: dict[str, dict[str, str]], layout_rows: list[dict[str, object]]
) -> list[dict[str, object]]:
    diameter = float(registry["P007"]["initial_value"])
    separation = float(registry["P008"]["initial_value"])
    target_fraction = float(registry["P009"]["initial_value"]) / 100.0
    derived_pitch = diameter * math.sqrt(math.pi / (4.0 * target_fraction))

    branches = [
        (
            "PHI_DERIVED_SQUARE",
            derived_pitch,
            "CENTER_PITCH_DERIVED_FROM_P007_P009",
            "C",
            "true",
            "P1_CANDIDATE_NEEDS_EDGE_CLIP_RECOUNT",
        ),
        (
            "P008_AS_CENTER_PITCH_SENTINEL",
            separation,
            "P008_INTERPRETED_AS_CENTER_TO_CENTER_PITCH",
            "C",
            "false",
            "CONFLICTS_P009_BROAD_RANGE_FOR_R0_SQUARE_GRID_RETAIN_AS_INTERPRETATION_SENTINEL",
        ),
        (
            "P008_AS_EDGE_GAP",
            diameter + separation,
            "P008_INTERPRETED_AS_EDGE_TO_EDGE_GAP_SO_PITCH_EQUALS_D_PLUS_S",
            "C",
            "true",
            "P1_CANDIDATE_PATENT_INTERPRETATION_NOT_LOCKED",
        ),
    ]

    rows: list[dict[str, object]] = []
    for layout in layout_rows:
        configuration_id = str(layout["configuration_id"])
        active_area = float(layout["active_membrane_area_proxy_mm2"])
        target_count = int(layout["porosity_hole_count_proxy"])
        for suffix, pitch, definition, evidence_class, cad_ready, status in branches:
            infinite_fraction = math.pi * diameter * diameter / (4.0 * pitch * pitch)
            rows.append(
                {
                    "pattern_id": f"{configuration_id}__{suffix}",
                    "configuration_id": configuration_id,
                    "hole_shape": "CIRCULAR_CYLINDER_R0_CANDIDATE",
                    "diameter_mm": f"{diameter:.6f}",
                    "separation_s_mm": f"{separation:.6f}",
                    "separation_definition": definition,
                    "pitch_x_mm": f"{pitch:.6f}",
                    "pitch_y_mm": f"{pitch:.6f}",
                    "active_plate_area_proxy_mm2": f"{active_area:.6f}",
                    "active_area_status": "MEMBRANE_AREA_PROXY_NOT_ACTUAL_PLATE_POLYGON",
                    "target_open_area_pct": f"{target_fraction * 100.0:.6f}",
                    "infinite_square_grid_open_area_pct": f"{infinite_fraction * 100.0:.6f}",
                    "target_hole_count_proxy": target_count,
                    "actual_hole_count": "NOT_RUN",
                    "actual_open_area_pct": "NOT_RUN",
                    "edge_margin_mm": "UNRESOLVED",
                    "cad_ready_candidate": cad_ready,
                    "evidence_class": evidence_class,
                    "source_evidence_classes": "P;C",
                    "source_ref": "P007,P008,P009 and p1_layout_configuration_matrix.csv",
                    "product_fact": "false",
                    "status": status,
                    "gate_note": "P1 Gate requires CAD recount after clipping; no branch identifies production pitch or hole count",
                }
            )

    center_rows = [row for row in rows if "CENTER_PITCH_SENTINEL" in row["pattern_id"]]
    if not center_rows or any(
        float(row["infinite_square_grid_open_area_pct"]) <= 15.0 for row in center_rows
    ):
        raise ValueError("P008 center-pitch sentinel must preserve its R0 porosity conflict")
    return rows


def build_vent_rows(registry: dict[str, dict[str, str]]) -> list[dict[str, object]]:
    """Build two auditable I/C-class top-vent geometry interpretations.

    Rectified image coordinates use the official-product planform frame with
    x in [0, D001] and y in [0, D002].  Centered CAD coordinates are obtained
    by subtracting half the envelope width/length.  The table preserves four
    drawn objects; it does not infer four intake groups or a cell mapping.
    """

    width = float(registry["D001"]["initial_value"])
    length = float(registry["D002"]["initial_value"])
    patent_width = float(registry["P013"]["initial_value"])

    measured = {
        row["measurement_id"]: row
        for row in base.read_csv(OFFICIAL_IMAGE_MEASUREMENTS)
        if row.get("measurement_id", "").startswith("V")
    }
    homography = {
        (row["view_id"], row["feature_id"]): row
        for row in base.read_csv(VENT_HOMOGRAPHY_RESULTS)
    }
    vent_ids = [f"V{index:02d}" for index in range(1, 5)]
    if set(measured) != set(vent_ids):
        raise ValueError("official image measurements must contain exactly V01..V04")
    if any(("upper_547", vent_id) not in homography for vent_id in vent_ids):
        raise ValueError("upper_547 homography rows must contain exactly V01..V04")

    rows: list[dict[str, object]] = []

    def append_row(
        *,
        candidate_set_id: str,
        vent_id: str,
        geometry_rule: str,
        x0: float,
        y0: float,
        x1: float,
        y1: float,
        slot_width: float,
        source_ref: str,
        source_view: str,
        evidence_class: str,
        image_uncertainty: str,
        model_uncertainty: str,
        branch_note: str,
    ) -> None:
        dx = x1 - x0
        dy = y1 - y0
        axis_length = math.hypot(dx, dy)
        if axis_length <= 0.0 or slot_width <= 0.0:
            raise ValueError(f"invalid vent geometry for {candidate_set_id}/{vent_id}")
        center_x = 0.5 * (x0 + x1)
        center_y = 0.5 * (y0 + y1)
        if not (0.0 <= center_x <= width and 0.0 <= center_y <= length):
            raise ValueError(f"vent center lies outside the direct envelope: {vent_id}")
        rows.append(
            {
                "candidate_id": f"{candidate_set_id}__{vent_id}",
                "candidate_set_id": candidate_set_id,
                "vent_id": vent_id,
                "drawn_object_count_scope": "FOUR_DRAWN_OBJECTS_NOT_GROUP_COUNT",
                "geometry_rule": geometry_rule,
                "coordinate_frame": "RECTIFIED_PLANFORM_X0_27P5_Y0_41P5_MM",
                "x0_rectified_mm": f"{x0:.6f}",
                "y0_rectified_mm": f"{y0:.6f}",
                "x1_rectified_mm": f"{x1:.6f}",
                "y1_rectified_mm": f"{y1:.6f}",
                "center_x_rectified_mm": f"{center_x:.6f}",
                "center_y_rectified_mm": f"{center_y:.6f}",
                "center_x_cad_mm": f"{center_x - width / 2.0:.6f}",
                "center_y_cad_mm": f"{center_y - length / 2.0:.6f}",
                "axis_dx_unit": f"{dx / axis_length:.9f}",
                "axis_dy_unit": f"{dy / axis_length:.9f}",
                "axis_length_mm": f"{axis_length:.6f}",
                "slot_width_mm": f"{slot_width:.6f}",
                "cut_depth_rule": "THROUGH_TOP_COVER_CAND",
                "source_view": source_view,
                "source_ref": source_ref,
                "evidence_class": evidence_class,
                "source_evidence_classes": "I;P;C" if evidence_class == "C" else "I",
                "image_readout_uncertainty": image_uncertainty,
                "model_form_uncertainty": model_uncertainty,
                "product_fact": "false",
                "cad_ready_candidate": "true",
                "selection_status": "UNSELECTED_BRANCH",
                "allowed_use": "P1 candidate top-cover cut and intake connectivity comparison",
                "forbidden_use": "production tolerance; intake group count; cell mapping; manufacturing drawing",
                "notes": branch_note,
            }
        )

    for vent_id in vent_ids:
        source = measured[vent_id]
        x0 = float(source["x0_mm_rectified"])
        y0 = float(source["y0_mm_rectified"])
        x1 = float(source["x1_mm_rectified"])
        y1 = float(source["y1_mm_rectified"])
        append_row(
            candidate_set_id="VENT_FLOW_BBOX_R0",
            vent_id=vent_id,
            geometry_rule="RECTIFIED_BOUNDING_BOX_CENTERLINE_WITH_MEASURED_WIDTH",
            x0=0.5 * (x0 + x1),
            y0=y0,
            x1=0.5 * (x0 + x1),
            y1=y1,
            slot_width=x1 - x0,
            source_ref=(
                "official_image_measurements.csv:"
                f"{vent_id}; source_pdf_sha256={source['source_pdf_sha256']}"
            ),
            source_view=str(source["figure_id"]),
            evidence_class="I",
            image_uncertainty=str(source["image_readout_uncertainty"]),
            model_uncertainty=str(source["model_form_uncertainty"]),
            branch_note="slot reconstructed from stored rectified image bounding box",
        )

        upper = homography[("upper_547", vent_id)]
        append_row(
            candidate_set_id="VENT_UPPER_CENTERLINE_P013_R0",
            vent_id=vent_id,
            geometry_rule="RECTIFIED_CENTERLINE_SLOT_WITH_PATENT_WIDTH_P013",
            x0=float(upper["rectified_a_x_mm"]),
            y0=float(upper["rectified_a_y_mm"]),
            x1=float(upper["rectified_b_x_mm"]),
            y1=float(upper["rectified_b_y_mm"]),
            slot_width=patent_width,
            source_ref=(
                "gen1_vent_homography_results.csv:upper_547/"
                f"{vent_id}; P013"
            ),
            source_view="upper_547",
            evidence_class="C",
            image_uncertainty=(
                "MC95 center_x=["
                f"{upper['mc_center_x_ci95_low_mm']},{upper['mc_center_x_ci95_high_mm']}]; "
                "center_y=["
                f"{upper['mc_center_y_ci95_low_mm']},{upper['mc_center_y_ci95_high_mm']}]; "
                "length=["
                f"{upper['mc_length_ci95_low_mm']},{upper['mc_length_ci95_high_mm']}] mm"
            ),
            model_uncertainty="I-class centerline combined with P013 patent-candidate width",
            branch_note="mixed I/P inputs promoted only to a documented C-class CAD branch",
        )

    if len(rows) != 8 or any(row["product_fact"] != "false" for row in rows):
        raise ValueError("vent table must contain eight non-product-fact rows")
    return rows


def build_planform_rows(
    registry: dict[str, dict[str, str]], layout_rows: list[dict[str, object]]
) -> list[dict[str, object]]:
    """Create explicit R0 single-side exhaust branches for every P1 layout."""

    width = float(registry["D001"]["initial_value"])
    length = float(registry["D002"]["initial_value"])
    channel_height = float(registry["P010"]["initial_value"])
    outer_half_gap = float(registry["P014"]["initial_value"]) / 2.0
    branches = [
        (
            "EXH_FULL_WIDTH_RECT_R0",
            1.0,
            "RECTANGULAR_COLLECTION_TO_FULL_ARRAY_WIDTH_OUTLET",
        ),
        (
            "EXH_CENTER_HALF_TAPER_R0",
            0.5,
            "LINEAR_PLANFORM_TAPER_FROM_ARRAY_WIDTH_TO_HALF_WIDTH_OUTLET",
        ),
    ]
    rows: list[dict[str, object]] = []
    for layout in layout_rows:
        configuration_id = str(layout["configuration_id"])
        span_x = float(layout["array_span_x_mm"])
        span_y = float(layout["array_span_y_mm"])
        array_x_min = -span_x / 2.0
        array_x_max = span_x / 2.0
        array_y_min = -span_y / 2.0
        array_y_max = span_y / 2.0
        cell_footprint_x_min = array_x_min - outer_half_gap
        cell_footprint_x_max = array_x_max + outer_half_gap
        cell_footprint_y_min = array_y_min - outer_half_gap
        cell_footprint_y_max = array_y_max + outer_half_gap
        manifold_y_max = length / 2.0
        manifold_length = manifold_y_max - cell_footprint_y_max
        if (
            manifold_length <= 0.0
            or cell_footprint_x_max > width / 2.0
            or cell_footprint_y_max > length / 2.0
        ):
            raise ValueError(f"invalid centered array envelope for {configuration_id}")

        for branch_id, outlet_fraction, rule in branches:
            footprint_width = cell_footprint_x_max - cell_footprint_x_min
            outlet_width = footprint_width * outlet_fraction
            rows.append(
                {
                    "exhaust_branch_id": f"{configuration_id}__{branch_id}",
                    "configuration_id": configuration_id,
                    "coordinate_frame": "CAD_CENTERED_X_WIDTH_Y_LENGTH_Z_THICKNESS_MM",
                    "array_x_min_mm": f"{array_x_min:.6f}",
                    "array_x_max_mm": f"{array_x_max:.6f}",
                    "array_y_min_mm": f"{array_y_min:.6f}",
                    "array_y_max_mm": f"{array_y_max:.6f}",
                    "cell_footprint_x_min_mm": f"{cell_footprint_x_min:.6f}",
                    "cell_footprint_x_max_mm": f"{cell_footprint_x_max:.6f}",
                    "cell_footprint_y_min_mm": f"{cell_footprint_y_min:.6f}",
                    "cell_footprint_y_max_mm": f"{cell_footprint_y_max:.6f}",
                    "manifold_x_min_at_array_mm": f"{cell_footprint_x_min:.6f}",
                    "manifold_x_max_at_array_mm": f"{cell_footprint_x_max:.6f}",
                    "manifold_y_min_mm": f"{cell_footprint_y_max:.6f}",
                    "manifold_y_max_mm": f"{manifold_y_max:.6f}",
                    "manifold_length_mm": f"{manifold_length:.6f}",
                    "outlet_center_x_mm": "0.000000",
                    "outlet_y_mm": f"{manifold_y_max:.6f}",
                    "outlet_width_mm": f"{outlet_width:.6f}",
                    "outlet_height_mm": f"{channel_height:.6f}",
                    "outlet_area_mm2": f"{outlet_width * channel_height:.6f}",
                    "planform_rule": rule,
                    "single_side_rule": "OUTLET_ON_Y_PLUS_ENVELOPE_FACE_ONLY",
                    "top_chamber_planform_rule": "UNION_ARRAY_PLANFORM_TO_SELECTED_FOUR_VENT_SLOTS_R0",
                    "vent_candidate_rule": "SELECT_ONE_COMPLETE_CANDIDATE_SET_FROM_P1_VENT_GEOMETRY_CANDIDATES",
                    "vertical_rule": "IMPINGEMENT_CHANNEL_HEIGHT_P010; EXACT_Z_FROM_SELECTED_THICKNESS_VARIANT",
                    "evidence_class": "C",
                    "source_evidence_classes": "D;I;P;C",
                    "source_ref": "D001,D002,P010,P014,C005; p1_layout_configuration_matrix.csv; official qualitative single-side spout topology",
                    "product_fact": "false",
                    "selection_status": "UNSELECTED_BRANCH",
                    "allowed_use": "P1 planform connectivity and model-form sensitivity",
                    "forbidden_use": "claiming production manifold or spout dimensions; aerodynamic calibration",
                    "notes": "engineering closure candidate because C005 remains unresolved; retain both branches through P1 review",
                }
            )

    if len(rows) != 8 or any(row["product_fact"] != "false" for row in rows):
        raise ValueError("planform table must contain eight non-product-fact rows")
    return rows


def build_internal_rule_rows() -> list[dict[str, object]]:
    """Define reproducible R0 geometry closures for otherwise unresolved CAD details."""

    specs = [
        (
            "CELL_CENTER_AND_TILE_R0",
            "MEMBRANE_CAND_TEMPLATE",
            "CELL_CENTERS_X=(COL-(C003-1)/2)*(P001+P014); Y=(ROW-(C002-1)/2)*(P001+P014); TILE_SIDE=P001+P014; MEMBRANE_PLANFORM=CENTERED_SQUARE(P001)_EDGES_PARALLEL_GLOBAL_XY",
            "MEMBRANE_Z_MIN=MEMBRANE.z_min_mm_FROM_SELECTED_VARIANT",
            "MEMBRANE_Z_MAX=MEMBRANE.z_max_mm_FROM_SELECTED_VARIANT",
            "P001;P002;P014;C002;C003",
            "CONSTRUCTION_GRID",
            "Each membrane is a P001 square prism centered in its tile; clearance is P014/2 on every tile side; outer footprint adds P014/2 beyond the membrane span",
        ),
        (
            "BOTTOM_CHAMBER_PER_CELL_SQUARE_R0",
            "BOTTOM_CHAMBER_FLUID_CAND_TEMPLATE",
            "FOR_EACH_CELL_CENTER_FROM_CELL_CENTER_AND_TILE_R0 CREATE_CENTERED_SQUARE(P001)_EDGES_PARALLEL_GLOBAL_XY; NO_ANCHOR_EXCLUSION_R0",
            "MEMBRANE.z_min_mm_FROM_SELECTED_VARIANT-C018",
            "MEMBRANE.z_min_mm_FROM_SELECTED_VARIANT",
            "P001;C018;C002;C003",
            "DIRECT_FLUID_BODY_AND_UNION_WITH_PERIMETER_GAP_AND_ORIFICE_THROATS",
            "Bottom chamber planform and Z extent are deterministic C-class R0 geometry; it connects only through the declared perimeter-gap and orifice interfaces",
        ),
        (
            "CENTRAL_ANCHOR_SQUARE_DATUM_R0",
            "CENTRAL_ANCHOR_CAND_TEMPLATE",
            "FOR_EACH_CELL_CENTER_FROM_CELL_CENTER_AND_TILE_R0 CREATE_CENTERED_SQUARE(P012)_EDGES_PARALLEL_GLOBAL_XY",
            "MEMBRANE.z_min_mm_FROM_SELECTED_VARIANT",
            "MEMBRANE.z_max_mm_FROM_SELECTED_VARIANT",
            "P012;P002;C002;C003",
            "REFERENCE_BODY_ONLY_NO_BOOLEAN",
            "The coincident P012 square anchor datum is display and location evidence only; never subtract from or add to the P1 fluid domain and never export as material",
        ),
        (
            "CELL_PARTITION_DATUM_R0",
            "CELL_PARTITION_CAND_TEMPLATE",
            "PITCH=P001+P014; X_INTERNAL_MIDPLANES=(I+0.5-(C003-1)/2)*PITCH FOR I=0..C003-2; Y_INTERNAL_MIDPLANES=(J+0.5-(C002-1)/2)*PITCH FOR J=0..C002-2; CLIP_TO_CELL_TILE_ARRAY_FOOTPRINT; CREATE_EACH_SHARED_PLANE_ONCE",
            "MEMBRANE.z_min_mm_FROM_SELECTED_VARIANT-C018",
            "TOP_CHAMBER.z_max_mm_FROM_SELECTED_VARIANT",
            "P001;P014;C002;C003;C018",
            "CELL_OWNERSHIP_SPLIT_AND_NAMING_DATUM_ONLY",
            "Zero-thickness construction surfaces only; no finite-thickness solid and no subtraction from the declared fluid union because PERIM_SPLIT_GAP_R0 already occupies the tile-minus-membrane ring",
        ),
        (
            "TOP_SHARED_PLENUM_R0",
            "TOP_CHAMBER_FLUID_CAND_TEMPLATE",
            "PLANFORM=ENVELOPE_CLIPPED_CONVEX_HULL(SELECTED_FOUR_VENT_SLOT_POLYGONS UNION CELL_TILE_ARRAY_FOOTPRINT)",
            "Z_MIN=TOP_CHAMBER.z_min_mm_FROM_SELECTED_VARIANT",
            "Z_MAX=TOP_CHAMBER.z_max_mm_FROM_SELECTED_VARIANT",
            "P005;C004;C014;P014",
            "DIRECT_FLUID_BODY",
            "One shared R0 distribution plenum; grouped and cellular top-chamber alternatives remain open questions",
        ),
        (
            "PERIM_SPLIT_GAP_R0",
            "PERIMETER_GAP_FLUID_CAND_TEMPLATE",
            "PER_CELL_PLANFORM=SQUARE(TILE_SIDE=P001+P014) MINUS SQUARE(MEMBRANE_SIDE=P001); ADJACENT_TILE_BOUNDARIES_SPLIT_AT_MIDPLANE",
            "Z_MIN=BOTTOM_CHAMBER.z_min_mm_FROM_SELECTED_VARIANT",
            "Z_MAX=TOP_CHAMBER.z_max_mm_FROM_SELECTED_VARIANT",
            "P001;P014;P002;P005;C018",
            "DIRECT_FLUID_BODY_AND_UNION",
            "P014/2 R0 clearance per membrane side; union to top and bottom chambers; this is a C interpretation of the patent clearance",
        ),
        (
            "SIDE_WALL_BOUNDARY_R0",
            "SIDE_FRAME_PROXY_U;ROOT_PRODUCT",
            "CLIP_ALL_DECLARED_PRODUCT_FLUID_BODIES_TO_X=[-D001/2,D001/2],Y=[-D002/2,D002/2]; OUTER_FACES_ARE_WALL_EXCEPT_SELECTED_VENT_CUTS_AND_SELECTED_Y_PLUS_OUTLET",
            "Z_MIN=0",
            "Z_MAX=D003",
            "D001;D002;D003;C004;C005",
            "FLUID_BOUNDARY_ONLY",
            "The solver wall selection is resolved on fluid-body outer faces; no identified physical side-frame solid is created",
        ),
        (
            "RESIDUAL_NUMERICAL_CLOSURE_R0",
            "FLUID_DOMAIN_CLOSURE_DATUM_C;C017_SUPPORT_ALLOWANCE_REF;C019_TOP_REF;C019_BOTTOM_REF",
            "CONSTRUCT_AND_UNION_ONLY_DECLARED_FLUID_BODIES; NEVER_EXTRACT_OUTER_ENVELOPE_MINUS_ALL_SOLIDS; CREATE_DATUM_PLANES_AT_EVERY_THICKNESS_BUDGET_Z_BOUNDARY",
            "Z_INTERVALS_C017_C019=NO_FLUID_BODY_CREATED",
            "CLOSURE=DECLARED_FLUID_BODY_FACES_PLUS_SIDE_WALL_BOUNDARY_R0",
            "C017;C019;C020",
            "NUMERICAL_CLOSURE_DATUM_ONLY",
            "Unknown residual/support intervals are neither air nor claimed solids; reference datums cap intended fluid bodies and never enter material mass or solver export",
        ),
        (
            "ORIFICE_PER_CELL_CENTERED_CLIP_R0",
            "ORIFICE_PLATE_CAND;ORIFICE_FLUID_SET_CAND_TEMPLATE",
            "FOR_EACH_CELL_RESET_LOCAL_SQUARE_GRID_AT_MEMBRANE_CENTER; CENTERS=(I*PITCH_X,J*PITCH_Y); KEEP_CIRCLE_ONLY_IF_FULL_CIRCLE_LIES_INSIDE_MEMBRANE_SQUARE; EDGE_MARGIN=D/2; NO_ANCHOR_EXCLUSION_R0",
            "Z_MIN=ORIFICE_PLATE.z_min_mm_FROM_SELECTED_VARIANT",
            "Z_MAX=ORIFICE_PLATE.z_max_mm_FROM_SELECTED_VARIANT",
            "P001;P007;P008;P009;P012",
            "CUT_ORIFICE_PLATE_AND_CREATE_THROAT_FLUID",
            "Deterministic proxy polygon and local origin; recount actual holes/open area after clipping; central-anchor projection exclusion is a deferred model-form branch",
        ),
    ]
    rows: list[dict[str, object]] = []
    for rule_id, features, planform, z_min, z_max, refs, boolean_role, notes in specs:
        rows.append(
            {
                "rule_id": rule_id,
                "feature_ids": features,
                "configuration_scope": "ALL_P1_VARIANTS",
                "coordinate_frame": "CAD_CENTERED_X_WIDTH_Y_LENGTH_Z_FROM_HEAT_SPREADER_BOTTOM_MM",
                "planform_or_construction_rule": planform,
                "z_min_rule": z_min,
                "z_max_rule": z_max,
                "parameter_refs": refs,
                "boolean_role": boolean_role,
                "fluid_domain_policy": "ONLY_DECLARED_FLUID_BODIES_MAY_ENTER_P1_FLUID_UNION",
                "evidence_class": "C",
                "source_evidence_classes": {
                    "CELL_CENTER_AND_TILE_R0": "P;C",
                    "BOTTOM_CHAMBER_PER_CELL_SQUARE_R0": "P;C",
                    "CENTRAL_ANCHOR_SQUARE_DATUM_R0": "P;C",
                    "CELL_PARTITION_DATUM_R0": "P;C",
                    "TOP_SHARED_PLENUM_R0": "P;I;C",
                    "PERIM_SPLIT_GAP_R0": "P;C",
                    "SIDE_WALL_BOUNDARY_R0": "D;I;C;U",
                    "RESIDUAL_NUMERICAL_CLOSURE_R0": "C;U",
                    "ORIFICE_PER_CELL_CENTERED_CLIP_R0": "P;C",
                }[rule_id],
                "product_fact": "false",
                "selection_status": "SELECTED_R0_ENGINEERING_CLOSURE",
                "allowed_use": "P1 reproducible candidate CAD and model-form comparison",
                "forbidden_use": "production geometry claim; material or mass inference; closing an open evidence question",
                "notes": notes,
            }
        )
    if len(rows) != 9 or any(row["product_fact"] != "false" for row in rows):
        raise ValueError("internal rule table must contain nine non-product-fact R0 rules")
    return rows


def build_feature_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []

    def add(
        feature_id: str,
        cad_name: str,
        entity_kind: str,
        parent: str,
        quantity_rule: str,
        existence_class: str,
        topology_class: str,
        geometry_class: str,
        selection_class: str,
        parameter_refs: str,
        source_locator: str,
        product_fact_scope: str,
        cad_role: str,
        solver_use: str,
        material_policy: str,
        mass_policy: str,
        boolean_policy: str,
        export_policy: str,
        alternative_group: str,
        branch_id: str,
        promotion_gate: str,
        status: str,
        notes: str,
        product_fact: str = "false",
    ) -> None:
        rows.append(
            {
                "feature_id": feature_id,
                "configuration_id": "ALL_CONFIGURATIONS",
                "cad_name": cad_name,
                "entity_kind": entity_kind,
                "parent_feature_id": parent,
                "quantity_rule": quantity_rule,
                "existence_class": existence_class,
                "topology_class": topology_class,
                "geometry_class": geometry_class,
                "selection_class": selection_class,
                "parameter_refs": parameter_refs,
                "source_locator": source_locator,
                "uncertainty_ref": "parameter registry or p1_cad_open_questions.csv",
                "product_fact_scope": product_fact_scope,
                "product_fact": product_fact,
                "cad_role": cad_role,
                "solver_use": solver_use,
                "material_policy": material_policy,
                "mass_policy": mass_policy,
                "boolean_policy": boolean_policy,
                "export_policy": export_policy,
                "alternative_group": alternative_group,
                "branch_id": branch_id,
                "promotion_gate": promotion_gate,
                "status": status,
                "notes": notes,
            }
        )

    add("ROOT_PRODUCT", "AJM_GEN1_PRODUCT_CAND", "ASSEMBLY", "ROOT", "1", "D", "C", "D", "C", "D001;D002;D003", "AirJet Mini Data Sheet page 1", "ENVELOPE_ONLY", "full-product candidate assembly", "REFERENCE_ONLY", "NOT_APPLICABLE", "NOT_APPLICABLE", "NO_BOOLEAN", "NATIVE_ASSEMBLY", "NONE", "BASE", "P1_REVIEW", "NOT_BUILT", "assembly identity is candidate; only envelope values are direct")
    add("ENVELOPE_REF", "ENVELOPE_27P5_41P5_2P8_D", "REFERENCE", "ROOT_PRODUCT", "1", "D", "D", "D", "D", "D001;D002;D003", "AirJet Mini Data Sheet page 1 metric table", "ENVELOPE_ONLY", "locked reference envelope", "REFERENCE_ONLY", "PROHIBITED", "EXCLUDE", "NO_BOOLEAN", "REFERENCE_ONLY", "NONE", "BASE", "P1_G1_ENVELOPE", "NOT_BUILT", "only complete locked geometry in P1", product_fact="true")
    add("TOP_COVER_CAND", "TOP_COVER_CAND", "SOLID_CANDIDATE", "ROOT_PRODUCT", "1", "I", "I", "C", "C", "C015;C004;C014;P013", "official product renders and p1_vent_geometry_candidates.csv", "EXISTENCE_ONLY", "candidate package boundary", "P1_CFD_WALL_PROXY", "UNASSIGNED", "EXCLUDE", "CUT_BY_ONE_COMPLETE_VENT_CANDIDATE_SET", "NATIVE_AND_STEP", "TOP_COVER_BRANCH", "SEE_VENT_TABLE", "P1_GEOMETRY_REVIEW", "NOT_BUILT", "thickness and vent cuts are candidates")
    for index in range(1, 5):
        add(f"VENT_DRAWN_{index:02d}_I", f"VENT_DRAWN_{index:02d}_I", "CUT", "TOP_COVER_CAND", "1", "I", "I", "I", "C", "C004;C014;P013", "official dual-view drawn vent objects with homography uncertainty", "DRAWN_OBJECTS_ONLY", "candidate intake opening", "P1_CFD_FLUID_CANDIDATE", "NOT_APPLICABLE", "NOT_APPLICABLE", "CUT_TOP_COVER", "NATIVE_AND_STEP", "VENT_TOPOLOGY_BRANCH", "DUAL_VIEW_V1", "P1_IMAGE_AND_CONNECTIVITY_REVIEW", "NOT_BUILT", "drawn object is not a confirmed inlet group and does not imply cell count")
    add("SIDE_FRAME_PROXY_U", "SIDE_FRAME_PROXY_U", "CONSTRUCTION_BODY", "ROOT_PRODUCT", "1", "U", "C", "C", "C", "D001;D002;D003", "p1_internal_geometry_rules.csv SIDE_WALL_BOUNDARY_R0; no separate Mini part geometry", "NONE", "candidate fluid-wall closure datum", "GEOMETRY_ONLY_NO_PHYSICS", "PROHIBITED", "EXCLUDE", "FLUID_BOUNDARY_DATUM_ONLY", "DO_NOT_EXPORT_AS_PHYSICAL_SOLID", "SIDE_FRAME_BRANCH", "SIDE_WALL_BOUNDARY_R0", "P1_GEOMETRY_REVIEW", "NOT_BUILT", "solver wall selection is resolved on fluid faces; no identified side-frame part")
    add("FLEX_KEEP_OUT_U", "FLEX_KEEP_OUT_REF_U", "KEEP_OUT", "ROOT_PRODUCT", "1", "U", "U", "U", "C", "NONE", "official images qualitatively show a flex region; no registry geometry", "NONE", "reference keep-out", "REFERENCE_ONLY", "PROHIBITED", "EXCLUDE", "NO_BOOLEAN", "DO_NOT_EXPORT", "FLEX_BRANCH", "U_REFERENCE", "P1_IMAGE_REVIEW", "NOT_BUILT", "no material, mass, or solver body")
    add("CELL_PARTITION_CAND_TEMPLATE", "CELL_PARTITION_DATUM_C__CELL_{NNN}", "CONSTRUCTION_SURFACE", "ROOT_PRODUCT", "INTERNAL_MIDPLANES_DEDUP_SHARED_EDGES", "P", "P", "C", "C", "P014;C001;C002;C003;C018", "patent architecture candidate plus CELL_PARTITION_DATUM_R0", "NONE", "candidate cell-boundary datum", "GEOMETRY_ONLY_NO_PHYSICS", "PROHIBITED", "EXCLUDE", "NO_BOOLEAN_DEDUP_TILE_EDGE_DATUM", "DO_NOT_EXPORT_AS_PHYSICAL_SOLID", "CELL_GEOMETRY_BRANCH", "CELL_PARTITION_DATUM_R0", "P1_TOPOLOGY_REVIEW", "NOT_BUILT", "zero-thickness internal tile midplanes are explicit R0 bookkeeping only; they do not partition the declared fluid union or claim a physical wall")
    add("MEMBRANE_CAND_TEMPLATE", "MEMBRANE_CAND__CELL_{NNN}", "SOLID_CANDIDATE", "ROOT_PRODUCT", "N_CELL_FROM_CONFIGURATION", "I", "P", "P", "C", "P001;P002;C001;C007", "official mechanism drawing plus US12137540B2 embodiments", "QUALITATIVE_TOPOLOGY_ONLY", "actuator geometry placeholder", "GEOMETRY_ONLY_UNTIL_SIZE_SPECIFIC_P2_BRANCH", "PROHIBITED", "EXCLUDE", "PATTERN_FROM_CONFIGURATION", "NATIVE_GEOMETRY_ONLY", "ACTUATOR_STACK_BRANCH", "SIZE_SPECIFIC_P2_REQUIRED", "P2_ENTRY", "NOT_BUILT", "P002 is an 8 mm cross-size P1 placeholder; no P1 material")
    add("CENTRAL_ANCHOR_CAND_TEMPLATE", "CENTRAL_ANCHOR_DATUM_C__CELL_{NNN}", "CONSTRUCTION_BODY", "ROOT_PRODUCT", "N_CELL_FROM_CONFIGURATION", "P", "P", "C", "C", "P002;P012", "US12137540B2 central-anchor embodiment plus CENTRAL_ANCHOR_SQUARE_DATUM_R0", "NONE", "anchor geometry placeholder", "GEOMETRY_ONLY_NO_PHYSICS", "PROHIBITED", "EXCLUDE", "NO_BOOLEAN_COINCIDENT_PLACEHOLDER", "DO_NOT_EXPORT_AS_PHYSICAL_SOLID", "ANCHOR_ALTERNATIVES", "CENTRAL_ANCHOR_SQUARE_DATUM_R0", "P2_ENTRY", "NOT_BUILT", "existence/topology and P012 prior are patent-supported; exact square datum geometry is a C-class R0 choice and does not cut or fuse the membrane")
    add("ORIFICE_PLATE_CAND", "ORIFICE_PLATE_CAND", "SOLID_CANDIDATE", "ROOT_PRODUCT", "1", "P", "P", "C", "C", "C016;P007;P008;P009", "US12137540B2 orifice embodiments and candidate thickness", "EXISTENCE_ONLY", "candidate orifice plate", "P1_CFD_WALL_PROXY", "UNASSIGNED", "EXCLUDE", "CUT_BY_ORIFICE_PATTERN_CANDIDATE", "NATIVE_AND_STEP", "ORIFICE_PATTERN_BRANCH", "SEE_ORIFICE_TABLE", "P1_G4_ORIFICE_CLOSURE", "NOT_BUILT", "separation s meaning and production hole count remain unresolved")
    add("C017_SUPPORT_ALLOWANCE_REF", "C017_SUPPORT_ALLOWANCE_REF", "CONSTRUCTION_BODY", "ROOT_PRODUCT", "1", "U", "U", "C", "C", "C017", "registry geometric bookkeeping only", "NONE", "thickness bookkeeping", "GEOMETRY_ONLY_NO_PHYSICS", "PROHIBITED", "EXCLUDE", "NO_BOOLEAN", "DO_NOT_EXPORT", "STACK_RESIDUAL_BRANCH", "C017", "P1_G3_THICKNESS", "NOT_BUILT", "must not become a physical solid")
    add("C019_TOP_REF", "C019_TOP_REF_U", "CONSTRUCTION_BODY", "ROOT_PRODUCT", "1", "U", "U", "U", "C", "C019;C020", "derived unresolved stack split", "NONE", "thickness bookkeeping", "GEOMETRY_ONLY_NO_PHYSICS", "PROHIBITED", "EXCLUDE", "NO_BOOLEAN", "DO_NOT_EXPORT", "STACK_RESIDUAL_BRANCH", "C019_TOP", "P1_G3_THICKNESS", "NOT_BUILT", "not an identified layer or location")
    add("C019_BOTTOM_REF", "C019_BOTTOM_REF_U", "CONSTRUCTION_BODY", "ROOT_PRODUCT", "1", "U", "U", "U", "C", "C019;C020", "derived unresolved stack split", "NONE", "thickness bookkeeping", "GEOMETRY_ONLY_NO_PHYSICS", "PROHIBITED", "EXCLUDE", "NO_BOOLEAN", "DO_NOT_EXPORT", "STACK_RESIDUAL_BRANCH", "C019_BOTTOM", "P1_G3_THICKNESS", "NOT_BUILT", "not an identified layer or location")
    add("FLUID_DOMAIN_CLOSURE_DATUM_C", "FLUID_DOMAIN_CLOSURE_DATUM_C", "CONSTRUCTION_BODY", "ROOT_PRODUCT", "THICKNESS_BUDGET_Z_DATUM_SET", "C", "C", "C", "C", "C017;C019;C020", "p1_internal_geometry_rules.csv RESIDUAL_NUMERICAL_CLOSURE_R0", "NONE", "nonphysical fluid extraction closure datum", "GEOMETRY_ONLY_NO_PHYSICS", "PROHIBITED", "EXCLUDE", "FLUID_BOUNDARY_DATUM_ONLY_NO_PRODUCT_BOOLEAN", "DO_NOT_EXPORT", "NUMERICAL_CLOSURE", "RESIDUAL_NUMERICAL_CLOSURE_R0", "P1_G2_CONNECTIVITY", "NOT_BUILT", "construct only declared fluid bodies; residual intervals are neither fluid nor identified solids")
    add("HEAT_SPREADER_CAND", "HEAT_SPREADER_CAND", "SOLID_CANDIDATE", "ROOT_PRODUCT", "1", "I", "I", "C", "C", "C009;C010", "official cross-section supports qualitative heat-spreader existence", "EXISTENCE_ONLY", "candidate heat-spreading wall", "P1_CFD_WALL_PROXY", "UNASSIGNED", "EXCLUDE", "BASE_SOLID_CANDIDATE", "NATIVE_AND_STEP", "SPREADER_BRANCH", "C009_R0", "P1_GEOMETRY_REVIEW", "NOT_BUILT", "material, conductivity, and mass are not identified in P1")
    add("SPOUT_SOLID_CAND_U", "SPOUT_SOLID_CAND_U", "CONSTRUCTION_BODY", "ROOT_PRODUCT", "1", "I", "I", "C", "C", "C005;P010", "official qualitative topology plus p1_planform_exhaust_candidates.csv", "QUALITATIVE_TOPOLOGY_ONLY", "candidate spout boundary construction", "GEOMETRY_ONLY_NO_PHYSICS", "PROHIBITED", "EXCLUDE", "WALL_PROXY_ONLY", "DO_NOT_EXPORT_AS_IDENTIFIED_PART", "EXHAUST_BRANCH", "SEE_PLANFORM_EXHAUST_TABLE", "P1_TOPOLOGY_REVIEW", "NOT_BUILT", "R0 CAD branch is explicit C geometry; production cross-section and wall thickness remain U")
    add("EXTERNAL_INLET_DOMAIN_C", "EXTERNAL_INLET_DOMAIN_C", "FLUID", "ROOT_PRODUCT", "1", "C", "C", "C", "C", "NONE", "numerical-domain choice", "NONE", "optional external CFD domain", "P1_CFD_FLUID_CANDIDATE", "NOT_APPLICABLE", "NOT_APPLICABLE", "VOLUME_EXTRACT", "NATIVE_AND_STEP", "EXTERNAL_DOMAIN", "P1_OPTIONAL", "P4_ENTRY", "NOT_BUILT", "not a product component")
    add("TOP_CHAMBER_FLUID_CAND_TEMPLATE", "TOP_CHAMBER_FLUID_CAND_SHARED_R0", "FLUID", "ROOT_PRODUCT", "1_SHARED_R0", "P", "C", "C", "C", "P005;C001;C004;C014", "US12137540B2 chamber embodiments plus TOP_SHARED_PLENUM_R0", "NONE", "candidate shared intake plenum fluid", "P1_CFD_FLUID_CANDIDATE", "NOT_APPLICABLE", "NOT_APPLICABLE", "DIRECT_BUILD_AND_VOLUME_CHECK", "NATIVE_AND_STEP", "SHARED_VS_CELLULAR", "TOP_SHARED_PLENUM_R0", "P1_G2_CONNECTIVITY", "NOT_BUILT", "R0 selects shared C branch; grouped/cellular production topology remains open")
    add("PERIMETER_GAP_FLUID_CAND_TEMPLATE", "PERIMETER_GAP_FLUID_CAND__CELL_{NNN}", "FLUID", "ROOT_PRODUCT", "N_CELL_FROM_CONFIGURATION", "P", "P", "C", "C", "P001;P014;P002;P005;C018", "patent-compatible path plus PERIM_SPLIT_GAP_R0", "NONE", "candidate transfer fluid", "P1_CFD_FLUID_CANDIDATE", "NOT_APPLICABLE", "NOT_APPLICABLE", "DIRECT_BUILD_AND_UNION", "NATIVE_AND_STEP", "TRANSFER_GAP_BRANCH", "PERIM_SPLIT_GAP_R0", "P1_G2_CONNECTIVITY", "NOT_BUILT", "R0 exact ring is C; production cross-section remains unresolved")
    add("BOTTOM_CHAMBER_FLUID_CAND_TEMPLATE", "BOTTOM_CHAMBER_FLUID_CAND__CELL_{NNN}", "FLUID", "ROOT_PRODUCT", "N_CELL_FROM_CONFIGURATION", "P", "P", "C", "C", "P001;C018;P004;P006", "derived from patent displacement and clearance relationship plus BOTTOM_CHAMBER_PER_CELL_SQUARE_R0", "NONE", "candidate bottom chamber fluid", "P1_CFD_FLUID_CANDIDATE", "NOT_APPLICABLE", "NOT_APPLICABLE", "DIRECT_BUILD_AND_UNION", "NATIVE_AND_STEP", "BOTTOM_CHAMBER_BRANCH", "BOTTOM_CHAMBER_PER_CELL_SQUARE_R0", "P1_G2_CONNECTIVITY", "NOT_BUILT", "R0 planform is the centered P001 square; Z max is the membrane bottom and Z min is C018 below it; union only through declared perimeter-gap and orifice interfaces")
    add("ORIFICE_FLUID_SET_CAND_TEMPLATE", "ORIFICE_FLUID_SET_CAND__CELL_{NNN}", "FLUID", "ROOT_PRODUCT", "N_CELL_PATTERN_FROM_ORIFICE_TABLE", "P", "P", "C", "C", "P007;P008;P009", "US12137540B2 orifice candidates", "NONE", "candidate orifice throat fluid", "P1_CFD_FLUID_CANDIDATE", "NOT_APPLICABLE", "NOT_APPLICABLE", "VOLUME_EXTRACT_AFTER_BOOLEAN", "NATIVE_AND_STEP", "ORIFICE_PATTERN_BRANCH", "SEE_ORIFICE_TABLE", "P1_G4_ORIFICE_CLOSURE", "NOT_BUILT", "every throat must be recounted and connected after Boolean")
    add("IMPINGEMENT_CHANNEL_FLUID_CAND", "IMPINGEMENT_CHANNEL_FLUID_CAND", "FLUID", "ROOT_PRODUCT", "1", "P", "P", "P", "C", "P010", "patent gap candidate plus official qualitative flow path", "QUALITATIVE_TOPOLOGY_ONLY", "candidate full-product impingement channel", "P1_CFD_FLUID_CANDIDATE", "NOT_APPLICABLE", "NOT_APPLICABLE", "VOLUME_EXTRACT", "NATIVE_AND_STEP", "IMPINGEMENT_BRANCH", "P010_R0", "P1_G2_CONNECTIVITY", "NOT_BUILT", "planform extent is C and must cover all candidate orifices")
    add("EXHAUST_MANIFOLD_FLUID_CAND", "EXHAUST_MANIFOLD_FLUID_CAND_U", "FLUID", "ROOT_PRODUCT", "1", "I", "C", "C", "C", "C005;P010", "official qualitative direction plus p1_planform_exhaust_candidates.csv", "QUALITATIVE_TOPOLOGY_ONLY", "candidate exhaust collection fluid", "P1_CFD_FLUID_CANDIDATE", "NOT_APPLICABLE", "NOT_APPLICABLE", "VOLUME_EXTRACT", "NATIVE_AND_STEP", "EXHAUST_BRANCH", "SEE_PLANFORM_EXHAUST_TABLE", "P1_G2_CONNECTIVITY", "NOT_BUILT", "two explicit C branches retain unresolved production 3D geometry")
    add("SPOUT_FLUID_CAND", "SPOUT_FLUID_CAND_U", "FLUID", "ROOT_PRODUCT", "1", "I", "I", "C", "C", "C005;P010", "AirJet Mini qualitative single-side spout plus p1_planform_exhaust_candidates.csv", "QUALITATIVE_TOPOLOGY_ONLY", "candidate product outlet fluid", "P1_CFD_FLUID_CANDIDATE", "NOT_APPLICABLE", "NOT_APPLICABLE", "VOLUME_EXTRACT", "NATIVE_AND_STEP", "EXHAUST_BRANCH", "SEE_PLANFORM_EXHAUST_TABLE", "P1_G2_CONNECTIVITY", "NOT_BUILT", "R0 outlet face is explicit C geometry; production dimensions remain unresolved")
    add("EXTERNAL_OUTLET_DOMAIN_C", "EXTERNAL_OUTLET_DOMAIN_C", "FLUID", "ROOT_PRODUCT", "1", "C", "C", "C", "C", "NONE", "numerical-domain choice", "NONE", "optional outlet CFD domain", "P1_CFD_FLUID_CANDIDATE", "NOT_APPLICABLE", "NOT_APPLICABLE", "VOLUME_EXTRACT", "NATIVE_AND_STEP", "EXTERNAL_DOMAIN", "P1_OPTIONAL", "P4_ENTRY", "NOT_BUILT", "not a product component")
    add("TIM_EQUIVALENT_C", "TIM_EQUIVALENT_C", "CONSTRUCTION_BODY", "ROOT_PRODUCT", "1", "C", "C", "C", "C", "C011", "target system integration, not Mini internal evidence", "NONE", "future P5 boundary", "GEOMETRY_ONLY_NO_PHYSICS", "PROHIBITED", "EXCLUDE", "NO_BOOLEAN_P1", "DO_NOT_EXPORT_P1", "THERMAL_STACK", "P5_ONLY", "P5_ENTRY", "NOT_BUILT", "not an identified AirJet internal layer")
    add("CHIP_HEAT_SOURCE_C", "CHIP_HEAT_SOURCE_C", "CONSTRUCTION_BODY", "ROOT_PRODUCT", "1", "C", "C", "C", "C", "D006", "future system boundary for net chip heat", "NONE", "future P5 boundary", "GEOMETRY_ONLY_NO_PHYSICS", "PROHIBITED", "EXCLUDE", "NO_BOOLEAN_P1", "DO_NOT_EXPORT_P1", "THERMAL_STACK", "P5_ONLY", "P5_ENTRY", "NOT_BUILT", "keep separate from AirJet self heat")

    ids = {str(row["feature_id"]) for row in rows}
    if len(ids) != len(rows):
        raise ValueError("feature contract contains duplicate feature IDs")
    for row in rows:
        for key in ("existence_class", "topology_class", "geometry_class", "selection_class"):
            if row[key] not in base.ALLOWED_EVIDENCE_CLASSES:
                raise ValueError(f"invalid {key} for {row['feature_id']}")
        if row["product_fact"] == "true" and row["feature_id"] != "ENVELOPE_REF":
            raise ValueError("only the D-class envelope reference may be a P1 geometry product fact")
        if row["feature_id"] in {"C017_SUPPORT_ALLOWANCE_REF", "C019_TOP_REF", "C019_BOTTOM_REF"}:
            if (
                row["material_policy"] != "PROHIBITED"
                or row["mass_policy"] != "EXCLUDE"
                or row["boolean_policy"] != "NO_BOOLEAN"
                or row["export_policy"] != "DO_NOT_EXPORT"
                or row["solver_use"] != "GEOMETRY_ONLY_NO_PHYSICS"
            ):
                raise ValueError(f"geometry-only residual guard changed for {row['feature_id']}")
        if row["feature_id"] in {"CENTRAL_ANCHOR_CAND_TEMPLATE", "CELL_PARTITION_CAND_TEMPLATE"}:
            if (
                row["material_policy"] != "PROHIBITED"
                or row["mass_policy"] != "EXCLUDE"
                or not str(row["boolean_policy"]).startswith("NO_BOOLEAN")
                or not str(row["export_policy"]).startswith("DO_NOT_EXPORT")
                or row["solver_use"] != "GEOMETRY_ONLY_NO_PHYSICS"
            ):
                raise ValueError(f"nonphysical datum guard changed for {row['feature_id']}")
    return rows


def build_binding_rows(
    registry: dict[str, dict[str, str]], feature_rows: list[dict[str, object]]
) -> list[dict[str, object]]:
    mappings = [
        ("ENVELOPE_REF", "WIDTH", "D001", "false", "P1_G1_ENVELOPE"),
        ("ENVELOPE_REF", "LENGTH", "D002", "false", "P1_G1_ENVELOPE"),
        ("ENVELOPE_REF", "THICKNESS", "D003", "false", "P1_G1_ENVELOPE"),
        ("TOP_COVER_CAND", "THICKNESS", "C015", "false", "P1_GEOMETRY_REVIEW"),
        ("TOP_COVER_CAND", "INTAKE_GEOMETRY", "C004", "false", "P1_IMAGE_REVIEW"),
        ("VENT_DRAWN_01_I", "WIDTH_PRIOR", "P013", "false", "P1_IMAGE_REVIEW"),
        ("VENT_DRAWN_01_I", "DRAWN_OBJECT_COUNT", "C014", "false", "P1_IMAGE_REVIEW"),
        ("CELL_PARTITION_CAND_TEMPLATE", "WALL_CLEARANCE", "P014", "true", "P1_TOPOLOGY_REVIEW"),
        ("MEMBRANE_CAND_TEMPLATE", "EFFECTIVE_LENGTH", "P001", "true", "P2_ENTRY"),
        ("MEMBRANE_CAND_TEMPLATE", "EFFECTIVE_THICKNESS_R0", "P002", "true", "P2_ENTRY"),
        ("CENTRAL_ANCHOR_CAND_TEMPLATE", "ANCHOR_WIDTH", "P012", "true", "P2_ENTRY"),
        ("ORIFICE_PLATE_CAND", "PLATE_THICKNESS", "C016", "false", "P1_G4_ORIFICE_CLOSURE"),
        ("ORIFICE_PLATE_CAND", "ORIFICE_DIAMETER", "P007", "false", "P1_G4_ORIFICE_CLOSURE"),
        ("ORIFICE_PLATE_CAND", "SEPARATION_S_UNRESOLVED", "P008", "false", "P1_G4_ORIFICE_CLOSURE"),
        ("ORIFICE_PLATE_CAND", "OPEN_AREA_TARGET", "P009", "false", "P1_G4_ORIFICE_CLOSURE"),
        ("C017_SUPPORT_ALLOWANCE_REF", "THICKNESS_BOOKKEEPING", "C017", "true", "P1_G3_THICKNESS"),
        ("C019_TOP_REF", "TOTAL_RESIDUAL", "C019", "true", "P1_G3_THICKNESS"),
        ("C019_TOP_REF", "TOP_FRACTION", "C020", "true", "P1_G3_THICKNESS"),
        ("C019_BOTTOM_REF", "TOTAL_RESIDUAL", "C019", "true", "P1_G3_THICKNESS"),
        ("C019_BOTTOM_REF", "TOP_FRACTION", "C020", "true", "P1_G3_THICKNESS"),
        ("FLUID_DOMAIN_CLOSURE_DATUM_C", "SUPPORT_INTERVAL_REFERENCE", "C017", "true", "P1_G2_CONNECTIVITY"),
        ("FLUID_DOMAIN_CLOSURE_DATUM_C", "RESIDUAL_INTERVAL_REFERENCE", "C019", "true", "P1_G2_CONNECTIVITY"),
        ("HEAT_SPREADER_CAND", "THICKNESS", "C009", "false", "P1_GEOMETRY_REVIEW"),
        ("TOP_CHAMBER_FLUID_CAND_TEMPLATE", "HEIGHT", "P005", "false", "P1_G2_CONNECTIVITY"),
        ("PERIMETER_GAP_FLUID_CAND_TEMPLATE", "R0_TOTAL_BETWEEN_MEMBRANE_GAP", "P014", "false", "P1_G2_CONNECTIVITY"),
        ("BOTTOM_CHAMBER_FLUID_CAND_TEMPLATE", "HEIGHT", "C018", "false", "P1_G2_CONNECTIVITY"),
        ("ORIFICE_FLUID_SET_CAND_TEMPLATE", "DIAMETER", "P007", "false", "P1_G4_ORIFICE_CLOSURE"),
        ("ORIFICE_FLUID_SET_CAND_TEMPLATE", "OPEN_AREA_TARGET", "P009", "false", "P1_G4_ORIFICE_CLOSURE"),
        ("IMPINGEMENT_CHANNEL_FLUID_CAND", "GAP", "P010", "false", "P1_G2_CONNECTIVITY"),
        ("EXHAUST_MANIFOLD_FLUID_CAND", "GEOMETRY_BRANCH", "C005", "false", "P1_TOPOLOGY_REVIEW"),
        ("SPOUT_FLUID_CAND", "GEOMETRY_BRANCH", "C005", "false", "P1_TOPOLOGY_REVIEW"),
    ]
    feature_ids = {str(row["feature_id"]) for row in feature_rows}
    rows: list[dict[str, object]] = []
    for index, (feature_id, role, parameter_id, geometry_only, promotion_gate) in enumerate(mappings, 1):
        if feature_id not in feature_ids or parameter_id not in registry:
            raise ValueError(f"invalid feature binding {feature_id}/{parameter_id}")
        source = registry[parameter_id]
        if parameter_id == "C005":
            chosen_value = "SELECT_FROM_P1_PLANFORM_EXHAUST_CANDIDATES"
            unit = "branch_id"
            evidence_class = "C"
            source_locator = source["evidence_source"] + "; p1_planform_exhaust_candidates.csv"
            derivation = "explicit C-class R0 branch closes unresolved C005 geometry"
        else:
            chosen_value = source["initial_value"]
            unit = source["unit"]
            evidence_class = source["evidence_class"]
            source_locator = source["evidence_source"]
            derivation = source["derivation_or_parent"]
        rows.append(
            {
                "binding_id": f"B{index:03d}",
                "feature_id": feature_id,
                "parameter_role": role,
                "parameter_id": parameter_id,
                "chosen_value": chosen_value,
                "unit": unit,
                "evidence_class": evidence_class,
                "source_locator": source_locator,
                "derivation": derivation,
                "parent_parameter_ids": source["derivation_or_parent"],
                "uncertainty_or_range": source["uncertainty_or_range"],
                "adjustable": source["adjustable"],
                "geometry_only": geometry_only,
                "applicability": source["used_in"],
                "configuration_override": "SEE_P1_CAD_PARAMETER_MAP",
                "promotion_gate": promotion_gate,
                "product_fact": "false",
            }
        )
    return rows


def build_interface_rows() -> list[dict[str, object]]:
    specs = [
        ("IF001", "EXTERNAL_INLET_DOMAIN_C", "TOP_COVER_CAND", "optional external inlet domain to four vent faces", "I", "C", "NS_EXTERNAL_PLENUM_VENT_FACES_C", "NS_VENT_DRAWN_SET_I", "FLUID_CONTINUITY", "false", "P1_OPTIONAL_P4_REQUIRED", "P4_ENTRY"),
        ("IF002", "TOP_COVER_CAND", "TOP_CHAMBER_FLUID_CAND_TEMPLATE", "four vent openings to shared R0 top plenum", "I", "C", "NS_VENT_DRAWN_SET_I", "NS_TOP_PLENUM_VENT_FACES_C", "FLUID_CONTINUITY", "true", "P1_REQUIRED", "P1_G2_CONNECTIVITY"),
        ("IF003", "TOP_CHAMBER_FLUID_CAND_TEMPLATE", "PERIMETER_GAP_FLUID_CAND_TEMPLATE", "top plenum to each perimeter transfer", "P", "C", "NS_TOP_PLENUM_TO_PERIM__CELL_{NNN}", "NS_PERIM_FROM_TOP__CELL_{NNN}", "FLUID_CONTINUITY", "true", "P1_REQUIRED", "P1_G2_CONNECTIVITY"),
        ("IF004", "PERIMETER_GAP_FLUID_CAND_TEMPLATE", "BOTTOM_CHAMBER_FLUID_CAND_TEMPLATE", "each perimeter transfer to bottom chamber", "P", "C", "NS_PERIM_TO_BOTTOM__CELL_{NNN}", "NS_BOTTOM_FROM_PERIM__CELL_{NNN}", "FLUID_CONTINUITY", "true", "P1_REQUIRED", "P1_G2_CONNECTIVITY"),
        ("IF005", "BOTTOM_CHAMBER_FLUID_CAND_TEMPLATE", "ORIFICE_FLUID_SET_CAND_TEMPLATE", "bottom chamber to orifice throats", "P", "C", "NS_BOTTOM_TO_ORIFICE__CELL_{NNN}", "NS_ORIFICE_FROM_BOTTOM__CELL_{NNN}", "FLUID_CONTINUITY", "true", "P1_REQUIRED", "P1_G4_ORIFICE_CLOSURE"),
        ("IF006", "ORIFICE_FLUID_SET_CAND_TEMPLATE", "IMPINGEMENT_CHANNEL_FLUID_CAND", "orifice exits to full-product impingement channel", "P", "C", "NS_ORIFICE_EXIT__CELL_{NNN}", "NS_IMPINGEMENT_FROM_ORIFICE__CELL_{NNN}", "FLUID_CONTINUITY", "true", "P1_REQUIRED", "P1_G4_ORIFICE_CLOSURE"),
        ("IF007", "IMPINGEMENT_CHANNEL_FLUID_CAND", "EXHAUST_MANIFOLD_FLUID_CAND", "impingement channel to exhaust collection", "C", "C", "NS_IMPINGEMENT_TO_MANIFOLD_CAND", "NS_MANIFOLD_FROM_IMPINGEMENT_CAND", "FLUID_CONTINUITY", "true", "P1_REQUIRED", "P1_G2_CONNECTIVITY"),
        ("IF008", "EXHAUST_MANIFOLD_FLUID_CAND", "SPOUT_FLUID_CAND", "manifold to single-side spout", "I", "C", "NS_MANIFOLD_TO_SPOUT_CAND", "NS_SPOUT_FROM_MANIFOLD_CAND", "FLUID_CONTINUITY", "true", "P1_REQUIRED", "P1_G2_CONNECTIVITY"),
        ("IF009", "SPOUT_FLUID_CAND", "EXTERNAL_OUTLET_DOMAIN_C", "optional product outlet to external outlet domain", "I", "C", "NS_PRODUCT_OUTLET_CAND", "NS_EXTERNAL_FROM_PRODUCT_C", "FLUID_CONTINUITY_OR_OUTLET_BOUNDARY", "false", "P1_OPTIONAL_P4_REQUIRED", "P4_ENTRY"),
        ("IF010", "MEMBRANE_CAND_TEMPLATE", "TOP_CHAMBER_FLUID_CAND_TEMPLATE", "membrane top moving wall candidate", "P", "C", "NS_MEMBRANE_TOP__CELL_{NNN}", "NS_TOP_PLENUM_MEMBRANE_WALL__CELL_{NNN}", "FUTURE_MOVING_WALL_OR_FSI", "true", "P1_REQUIRED_P2_P3_CONSUMER", "P2_P3_ENTRY"),
        ("IF011", "MEMBRANE_CAND_TEMPLATE", "BOTTOM_CHAMBER_FLUID_CAND_TEMPLATE", "membrane bottom moving wall candidate", "P", "C", "NS_MEMBRANE_BOTTOM__CELL_{NNN}", "NS_BOTTOM_CHAMBER_MEMBRANE_WALL__CELL_{NNN}", "FUTURE_MOVING_WALL_OR_FSI", "true", "P1_REQUIRED_P2_P3_CONSUMER", "P2_P3_ENTRY"),
        ("IF012", "IMPINGEMENT_CHANNEL_FLUID_CAND", "HEAT_SPREADER_CAND", "impingement fluid to heat wall", "P", "C", "NS_IMPINGEMENT_HEAT_WALL_FLUID_CAND", "NS_HEAT_SPREADER_FLUID_FACE_CAND", "FUTURE_CHT_WALL", "true", "P1_REQUIRED_P5_CONSUMER", "P5_ENTRY"),
        ("IF013", "HEAT_SPREADER_CAND", "TIM_EQUIVALENT_C", "spreader to system TIM", "C", "C", "NS_SPREADER_TO_TIM_CAND", "NS_TIM_TO_SPREADER_CAND", "FUTURE_CHT_CONTACT", "false", "P5_ONLY", "P5_ENTRY"),
    ]
    forbidden = {"C017_SUPPORT_ALLOWANCE_REF", "C019_TOP_REF", "C019_BOTTOM_REF", "FLEX_KEEP_OUT_U"}
    rows: list[dict[str, object]] = []
    for spec in specs:
        interface_id, side_a, side_b, role, topology_class, geometry_class, ns_a, ns_b, behavior, required, requirement_scope, gate = spec
        if side_a in forbidden or side_b in forbidden:
            raise ValueError("geometry-only reference must not have a solver interface")
        rows.append(
            {
                "interface_id": interface_id,
                "side_a_feature_id": side_a,
                "side_b_feature_id": side_b,
                "interface_role": role,
                "topology_class": topology_class,
                "geometry_class": geometry_class,
                "source_locator": "p1_cad_features.csv parameter/source boundary",
                "named_selection_a": ns_a,
                "named_selection_b": ns_b,
                "contact_or_coupling": behavior,
                "interface_mode": "PAIRED_NONCONFORMAL_OR_MATCHED_FACE",
                "solver_behavior": "UNASSIGNED_P1_CONTRACT_ONLY",
                "connectivity_required": required,
                "requirement_scope": requirement_scope,
                "orientation_rule": "NORMALS_OPPOSE_ACROSS_INTERNAL_INTERFACE_OR_OUTWARD_AT_EXTERNAL_BOUNDARY",
                "area_rule": "MATCH_GEOMETRY_OR_RECORD_CONSERVATIVE_NONCONFORMAL_INTERFACE",
                "mass_flow_check_group": (
                    "P1_FULL_PATH"
                    if required == "true"
                    else "P5_THERMAL_ONLY"
                    if requirement_scope == "P5_ONLY"
                    else "P4_OPTIONAL_EXTERNAL"
                ),
                "branch_id": (
                    "P1_OPTIONAL_EXTERNAL_DOMAIN"
                    if requirement_scope == "P1_OPTIONAL_P4_REQUIRED"
                    else "P5_ONLY"
                    if requirement_scope == "P5_ONLY"
                    else "ALL_P1_VARIANTS"
                ),
                "nonconformal_allowed_p1": "true",
                "promotion_gate": gate,
                "status": "NOT_BUILT",
                "product_fact": "false",
            }
        )
    return rows


def build_named_selection_rows() -> list[dict[str, object]]:
    specs = [
        ("NS_EXTERNAL_INLET_C", "EXTERNAL_INLET_DOMAIN_C", "FACE", "EXTERNAL_INLET", "P4_FLUENT", "C", "NONE", "1", "OUTWARD_FROM_DOMAIN", "AREA_GT_ZERO", "true"),
        ("NS_EXTERNAL_PLENUM_VENT_FACES_C", "EXTERNAL_INLET_DOMAIN_C", "FACE_SET", "EXTERNAL_TO_FOUR_VENTS", "P4_FLUENT", "C", "NONE", "4", "TOWARD_PRODUCT", "FACE_COUNT_EQUALS_4_AND_AREA_MATCHES_VENT_SET", "true"),
        ("NS_VENT_DRAWN_SET_I", "TOP_COVER_CAND", "FACE_SET", "FOUR_DRAWN_VENT_OPENINGS", "P1_P4", "I", "DRAWN_OBJECTS_ONLY", "4", "INTO_PRODUCT_CANDIDATE", "UNION_OF_V01_TO_V04_WITHOUT_GROUP_INFERENCE", "true"),
        ("NS_VENT_DRAWN_01_I", "VENT_DRAWN_01_I", "FACE", "DRAWN_VENT_CANDIDATE", "P1_P4", "I", "DRAWN_OBJECTS_ONLY", "1", "INTO_PRODUCT_CANDIDATE", "AREA_GT_ZERO", "true"),
        ("NS_VENT_DRAWN_02_I", "VENT_DRAWN_02_I", "FACE", "DRAWN_VENT_CANDIDATE", "P1_P4", "I", "DRAWN_OBJECTS_ONLY", "1", "INTO_PRODUCT_CANDIDATE", "AREA_GT_ZERO", "true"),
        ("NS_VENT_DRAWN_03_I", "VENT_DRAWN_03_I", "FACE", "DRAWN_VENT_CANDIDATE", "P1_P4", "I", "DRAWN_OBJECTS_ONLY", "1", "INTO_PRODUCT_CANDIDATE", "AREA_GT_ZERO", "true"),
        ("NS_VENT_DRAWN_04_I", "VENT_DRAWN_04_I", "FACE", "DRAWN_VENT_CANDIDATE", "P1_P4", "I", "DRAWN_OBJECTS_ONLY", "1", "INTO_PRODUCT_CANDIDATE", "AREA_GT_ZERO", "true"),
        ("NS_TOP_PLENUM_VENT_FACES_C", "TOP_CHAMBER_FLUID_CAND_TEMPLATE", "FACE_SET", "FOUR_VENTS_TO_SHARED_PLENUM", "P1_P4", "C", "NONE", "4", "INTO_TOP_PLENUM", "FACE_COUNT_EQUALS_4_AND_AREA_MATCHES_VENT_SET", "true"),
        ("NS_TOP_PLENUM_BODY_C", "TOP_CHAMBER_FLUID_CAND_TEMPLATE", "BODY", "SHARED_TOP_PLENUM", "P1_P3_P4", "C", "NONE", "1", "NOT_APPLICABLE", "BODY_VOLUME_GT_ZERO", "true"),
        ("NS_TOP_PLENUM_TO_PERIM__CELL_{NNN}", "TOP_CHAMBER_FLUID_CAND_TEMPLATE", "FACE", "TOP_PLENUM_TO_CELL_TRANSFER", "P1_P3_P4", "C", "NONE", "N_CELL", "TOWARD_PERIMETER_GAP", "ONE_FACE_PER_CELL_AREA_GT_ZERO", "true"),
        ("NS_PERIM_FROM_TOP__CELL_{NNN}", "PERIMETER_GAP_FLUID_CAND_TEMPLATE", "FACE", "PERIMETER_FROM_TOP_PLENUM", "P1_P3_P4", "C", "NONE", "N_CELL", "FROM_TOP_PLENUM", "AREA_MATCHES_PAIRED_TOP_FACE", "true"),
        ("NS_MEMBRANE_TOP__CELL_{NNN}", "MEMBRANE_CAND_TEMPLATE", "FACE", "MOVING_WALL_TOP", "P2_P3", "P", "NONE", "N_CELL", "TOWARD_TOP_CHAMBER", "AREA_GT_ZERO", "true"),
        ("NS_TOP_PLENUM_MEMBRANE_WALL__CELL_{NNN}", "TOP_CHAMBER_FLUID_CAND_TEMPLATE", "FACE", "TOP_PLENUM_MEMBRANE_WALL", "P2_P3", "C", "NONE", "N_CELL", "TOWARD_MEMBRANE", "AREA_MATCHES_MEMBRANE_TOP", "true"),
        ("NS_MEMBRANE_BOTTOM__CELL_{NNN}", "MEMBRANE_CAND_TEMPLATE", "FACE", "MOVING_WALL_BOTTOM", "P2_P3", "P", "NONE", "N_CELL", "TOWARD_BOTTOM_CHAMBER", "AREA_GT_ZERO", "true"),
        ("NS_BOTTOM_CHAMBER_MEMBRANE_WALL__CELL_{NNN}", "BOTTOM_CHAMBER_FLUID_CAND_TEMPLATE", "FACE", "BOTTOM_CHAMBER_MEMBRANE_WALL", "P2_P3", "C", "NONE", "N_CELL", "TOWARD_MEMBRANE", "AREA_MATCHES_MEMBRANE_BOTTOM", "true"),
        ("NS_PERIM_TO_BOTTOM__CELL_{NNN}", "PERIMETER_GAP_FLUID_CAND_TEMPLATE", "FACE", "PERIM_TO_BOTTOM_TRANSFER", "P1_P3_P4", "C", "NONE", "N_CELL", "TOWARD_BOTTOM_CHAMBER", "AREA_GT_ZERO", "true"),
        ("NS_BOTTOM_FROM_PERIM__CELL_{NNN}", "BOTTOM_CHAMBER_FLUID_CAND_TEMPLATE", "FACE", "BOTTOM_FROM_PERIM_TRANSFER", "P1_P3_P4", "C", "NONE", "N_CELL", "FROM_PERIMETER_GAP", "AREA_MATCHES_PAIRED_PERIM_FACE", "true"),
        ("NS_BOTTOM_TO_ORIFICE__CELL_{NNN}", "BOTTOM_CHAMBER_FLUID_CAND_TEMPLATE", "FACE_SET", "BOTTOM_TO_ORIFICE", "P1_P3_P4", "C", "NONE", "N_CELL", "TOWARD_ORIFICE_THROATS", "FACE_COUNT_EQUALS_ACTUAL_HOLE_COUNT", "true"),
        ("NS_ORIFICE_FROM_BOTTOM__CELL_{NNN}", "ORIFICE_FLUID_SET_CAND_TEMPLATE", "FACE_SET", "ORIFICE_FROM_BOTTOM", "P1_P3_P4", "C", "NONE", "N_CELL", "FROM_BOTTOM_CHAMBER", "FACE_COUNT_EQUALS_ACTUAL_HOLE_COUNT", "true"),
        ("NS_ORIFICE_EXIT__CELL_{NNN}", "ORIFICE_FLUID_SET_CAND_TEMPLATE", "FACE_SET", "ORIFICE_EXITS", "P1_P3_P4", "C", "NONE", "N_CELL", "TOWARD_IMPINGEMENT_CHANNEL", "FACE_COUNT_EQUALS_ACTUAL_HOLE_COUNT", "true"),
        ("NS_IMPINGEMENT_FROM_ORIFICE__CELL_{NNN}", "IMPINGEMENT_CHANNEL_FLUID_CAND", "FACE_SET", "IMPINGEMENT_FROM_ORIFICES", "P1_P4", "C", "NONE", "N_CELL", "FROM_ORIFICE_THROATS", "FACE_COUNT_EQUALS_ACTUAL_HOLE_COUNT", "true"),
        ("NS_IMPINGEMENT_TO_MANIFOLD_CAND", "IMPINGEMENT_CHANNEL_FLUID_CAND", "FACE_OR_INTERFACE_SET", "IMPACT_TO_MANIFOLD", "P1_P4", "C", "QUALITATIVE_TOPOLOGY_ONLY", "1", "TOWARD_MANIFOLD", "AREA_GT_ZERO", "true"),
        ("NS_MANIFOLD_FROM_IMPINGEMENT_CAND", "EXHAUST_MANIFOLD_FLUID_CAND", "FACE_OR_INTERFACE_SET", "MANIFOLD_FROM_IMPINGEMENT", "P1_P4", "C", "QUALITATIVE_TOPOLOGY_ONLY", "1", "FROM_IMPINGEMENT_CHANNEL", "AREA_MATCHES_PAIRED_IMPINGEMENT_FACE", "true"),
        ("NS_MANIFOLD_TO_SPOUT_CAND", "EXHAUST_MANIFOLD_FLUID_CAND", "FACE", "MANIFOLD_TO_SPOUT", "P1_P4", "C", "QUALITATIVE_TOPOLOGY_ONLY", "1", "TOWARD_SPOUT", "AREA_GT_ZERO", "true"),
        ("NS_SPOUT_FROM_MANIFOLD_CAND", "SPOUT_FLUID_CAND", "FACE", "SPOUT_FROM_MANIFOLD", "P1_P4", "C", "QUALITATIVE_TOPOLOGY_ONLY", "1", "FROM_MANIFOLD", "AREA_MATCHES_PAIRED_MANIFOLD_FACE", "true"),
        ("NS_PRODUCT_OUTLET_CAND", "SPOUT_FLUID_CAND", "FACE", "PRODUCT_OUTLET", "P1_P4", "C", "QUALITATIVE_TOPOLOGY_ONLY", "1", "OUTWARD_FROM_PRODUCT", "AREA_GT_ZERO", "true"),
        ("NS_EXTERNAL_FROM_PRODUCT_C", "EXTERNAL_OUTLET_DOMAIN_C", "FACE", "EXTERNAL_FROM_PRODUCT", "P4_FLUENT", "C", "NONE", "1", "FROM_PRODUCT", "AREA_MATCHES_PRODUCT_OUTLET", "true"),
        ("NS_EXTERNAL_OUTLET_C", "EXTERNAL_OUTLET_DOMAIN_C", "FACE", "EXTERNAL_OUTLET", "P4_FLUENT", "C", "NONE", "1", "OUTWARD_FROM_DOMAIN", "AREA_GT_ZERO", "true"),
        ("NS_IMPINGEMENT_HEAT_WALL_FLUID_CAND", "IMPINGEMENT_CHANNEL_FLUID_CAND", "FACE", "IMPACT_AND_HEAT_TRANSFER_WALL_FLUID_SIDE", "P1_P4_P5", "C", "NONE", "1", "TOWARD_HEAT_SPREADER", "COVERS_ALL_ACTIVE_ORIFICES", "true"),
        ("NS_HEAT_SPREADER_FLUID_FACE_CAND", "HEAT_SPREADER_CAND", "FACE", "HEAT_SPREADER_FLUID_SIDE", "P1_P5", "C", "EXISTENCE_ONLY", "1", "TOWARD_FLUID", "AREA_MATCHES_IMPINGEMENT_HEAT_WALL", "true"),
        ("NS_SPREADER_TO_TIM_CAND", "HEAT_SPREADER_CAND", "FACE", "SPREADER_TO_TIM", "P5", "C", "EXISTENCE_ONLY", "1", "TOWARD_HOST_CHIP", "AREA_GT_ZERO", "true"),
        ("NS_TIM_TO_SPREADER_CAND", "TIM_EQUIVALENT_C", "FACE", "TIM_TO_SPREADER", "P5", "C", "NONE", "1", "TOWARD_HEAT_SPREADER", "AREA_MATCHES_SPREADER_TO_TIM", "true"),
        ("NS_SIDE_FRAME_WALL_PROXY_U", "ROOT_PRODUCT", "FACE_SET", "FLUID_WALL_PROXY_ON_DECLARED_FLUID_BODIES", "P1_P4", "C", "NONE", "BRANCH_DEFINED", "OUTWARD_FROM_FLUID", "CLOSED_WALL_EXCEPT_DECLARED_VENTS_AND_OUTLET", "true"),
        ("NS_FLEX_KEEP_OUT_REF_U", "FLEX_KEEP_OUT_U", "REFERENCE", "KEEP_OUT", "CAD_ONLY", "U", "NONE", "1", "NOT_APPLICABLE", "NO_SOLVER_EXPORT", "false"),
        ("NS_RESIDUAL_TOP_REF_U", "C019_TOP_REF", "REFERENCE", "STACK_BOOKKEEPING", "CAD_ONLY", "U", "NONE", "1", "NOT_APPLICABLE", "NO_SOLVER_EXPORT", "false"),
        ("NS_RESIDUAL_BOTTOM_REF_U", "C019_BOTTOM_REF", "REFERENCE", "STACK_BOOKKEEPING", "CAD_ONLY", "U", "NONE", "1", "NOT_APPLICABLE", "NO_SOLVER_EXPORT", "false"),
        ("NS_FLUID_CLOSURE_DATUM_C", "FLUID_DOMAIN_CLOSURE_DATUM_C", "REFERENCE_SET", "NUMERICAL_FLUID_CLOSURE", "CAD_ONLY", "C", "NONE", "THICKNESS_BUDGET_BOUNDARIES", "NOT_APPLICABLE", "NO_SOLVER_EXPORT", "false"),
    ]
    rows: list[dict[str, object]] = []
    forbidden_tokens = ("REAL_", "PRODUCTION_", "ACTUAL_SPOUT", "MATERIAL_RESIDUAL_LAYER")
    for spec in specs:
        selection_id, owner, entity_type, role, solver_target, evidence_class, scope, count, normal, check, export = spec
        if any(token in selection_id for token in forbidden_tokens):
            raise ValueError(f"named selection implies unsupported production fact: {selection_id}")
        rows.append(
            {
                "selection_id": selection_id,
                "owner_feature_id": owner,
                "entity_type": entity_type,
                "selection_role": role,
                "solver_target": solver_target,
                "evidence_class": evidence_class,
                "product_fact_scope": scope,
                "expected_cardinality": count,
                "expansion_rule": "EXPAND_NNN_001_TO_N_CELL" if "{NNN}" in selection_id else "LITERAL_SELECTION_ID",
                "normal_direction_rule": normal,
                "area_or_count_check": check,
                "boundary_condition_status": "UNASSIGNED_P1",
                "branch_id": "ALL_P1_VARIANTS",
                "export_to_solver": export,
                "stable_rebuild_rule": "REBUILD_FROM_FEATURE_ID_AND_CONFIGURATION_NOT_FACE_INDEX",
                "status": "NOT_BUILT",
                "notes": "candidate naming contract; transfer to Workbench must be verified",
            }
        )
    return rows


def build_open_question_rows(registry: dict[str, dict[str, str]]) -> list[dict[str, object]]:
    specs = [
        ("OQ001", "VENT_DRAWN_01_I", "image-inferred candidate vent positions and shapes", "I", registry["C004"]["initial_value"], "use dual-view candidate with stored uncertainty", "image candidate is exact production geometry", "P1_IMAGE_REVIEW", "new orthographic image or physical measurement"),
        ("OQ002", "VENT_DRAWN_01_I", "true intake group count and mapping to cells", "U", registry["C014"]["initial_value"], "retain drawn-object names and branch the distribution volume", "vent count equals group count or cell count", "P1_TOPOLOGY_REVIEW", "CT/teardown or explicit official architecture"),
        ("OQ003", "EXHAUST_MANIFOLD_FLUID_CAND", "exact exhaust manifold 3D geometry", "U", registry["C005"]["initial_value"], "retain at least two documented C branches", "a selected candidate is production geometry", "P1_TOPOLOGY_REVIEW", "orthographic/CT/teardown/official dimensions"),
        ("OQ004", "SPOUT_FLUID_CAND", "spout cross-section length wall thickness and exact position", "U", "TBD", "use qualitative single-side topology plus explicit C branch", "official schematic fixes spout dimensions", "P1_TOPOLOGY_REVIEW", "dimensioned official drawing or measurement"),
        ("OQ005", "SIDE_FRAME_PROXY_U", "separate side-frame identity and wall section", "U", "TBD", "use fluid-wall closure proxy only", "a proxy is an identified product part", "P1_GEOMETRY_REVIEW", "section evidence or teardown"),
        ("OQ006", "FLEX_KEEP_OUT_U", "flex keep-out polygon thickness and material", "U", "TBD", "reference keep-out only; no solver export", "flex shape or mass is known", "P1_IMAGE_REVIEW", "measured pixels with scale or teardown"),
        ("OQ007", "TOP_CHAMBER_FLUID_CAND_TEMPLATE", "shared grouped or independent top chambers", "U", "TBD", "keep topology branches", "one sharing mode is the production structure", "P1_TOPOLOGY_REVIEW", "internal imaging or stronger patent-product mapping"),
        ("OQ008", "ORIFICE_PLATE_CAND", "P008 separation s center-versus-edge definition", "U", registry["P008"]["initial_value"], "retain center-pitch and edge-gap interpretation sentinels", "P008 is silently a center pitch", "P1_G4_ORIFICE_CLOSURE", "unambiguous figure interpretation or new source"),
        ("OQ009", "ORIFICE_PLATE_CAND", "production hole shape and cone angle", "U", "TBD", "use circular cylinder R0 and retain conical deferred branch", "R0 cylinder is production shape", "P1_G4_ORIFICE_CLOSURE", "section image or direct measurement"),
        ("OQ010", "C019_TOP_REF", "physical decomposition and location of residual thickness", "U", registry["C019"]["initial_value"], "compare 0.25/0.50/0.75 placement as geometry-only", "residual reference bodies are physical layers", "P1_G3_THICKNESS", "section measurement or identified parts"),
        ("OQ011", "MEMBRANE_CAND_TEMPLATE", "size-specific actuator thickness and layer stack", "U", registry["P002"]["initial_value"], "P002 cross-size placeholder only; branch before P2", "all membrane sizes use the 8 mm patent thickness", "P2_ENTRY", "size-specific structural evidence or calibration"),
        ("OQ012", "ORIFICE_FLUID_SET_CAND_TEMPLATE", "actual active plate polygon and hole count", "C", "PROXY_ONLY", "recount after CAD Boolean and report actual porosity", "proxy hole count is production count", "P1_G4_ORIFICE_CLOSURE", "completed CAD plus geometry validation"),
        ("OQ013", "ROOT_PRODUCT", "materials densities and complete mass allocation", "U", "TBD", "export volumes and unresolved mass separately", "candidate geometry closes exactly to 11 g", "P1_MASS_BUDGET_REVIEW", "material evidence or measured component masses"),
        ("OQ014", "ROOT_PRODUCT", "external fillets chamfers and manufacturing details", "U", "TBD", "suppress in R0 unless required for topology", "marketing render edge treatment is dimensioned", "P1_GEOMETRY_REVIEW", "dimensioned image or measurement"),
        ("OQ015", "EXTERNAL_INLET_DOMAIN_C", "external plenum and test-domain extent", "C", "TBD", "defer final domain to P4 and label numerical", "external domain is a product component", "P4_ENTRY", "domain-independence study"),
    ]
    rows: list[dict[str, object]] = []
    for question_id, feature_id, question, evidence_class, current, allowed, prohibited, gate, needed in specs:
        rows.append(
            {
                "question_id": question_id,
                "feature_id": feature_id,
                "question": question,
                "evidence_class": evidence_class,
                "current_value_or_status": current,
                "allowed_p1_treatment": allowed,
                "prohibited_claim": prohibited,
                "resolution_gate": gate,
                "required_new_evidence": needed,
                "status": "OPEN",
                "product_fact": "false",
            }
        )
    return rows


def build_gate_rows(variant_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    items = [
        ("G0_INPUT_GENERATORS", "both P1 generators pass --check", "PASS text and input hashes recorded", "true"),
        ("G0_005_TOOLCHAIN", "005 authorizes P1 CAD toolchain", "P1_CAD_TOOLCHAIN_READINESS is PASS or PASS_WITH_TRANSFER_LIMITATION", "true"),
        ("G1_ENVELOPE", "external envelope equals 27.5 x 41.5 x 2.8 mm", "exact driving dimensions; measured export recorded", "true"),
        ("G1_CONFIGURATION", "Nx Ny cell count membrane size and spans match input map", "zero unexplained parameter deviations", "true"),
        ("G1_ALL_BODIES_INSIDE", "all product candidate bodies remain inside envelope", "zero out-of-envelope product bodies except declared flex reference", "true"),
        ("G1_VENT_BRANCH", "one complete four-object vent candidate set is selected and recorded", "all four cuts come from one candidate_set_id; no group-count inference", "true"),
        ("G1_INTERNAL_RULES", "all nine membrane tile anchor bottom chamber partition top plenum perimeter gap side wall residual closure and orifice grid rules are recorded", "all nine R0 rule IDs equal the generated variant manifest; no hidden CAD constants", "true"),
        ("G2_FULL_PATH", "inlet to single-side outlet path is complete", "connectivity graph reaches outlet", "true"),
        ("G2_EACH_CELL_CONNECTED", "every modeled cell reaches inlet and final outlet", "connected cell count equals configured N_CELL", "true"),
        ("G3_THICKNESS", "stack bookkeeping closes to 2.8 mm", "absolute closure error <= 0.000001 mm", "true"),
        ("G3_RESIDUAL_GUARD", "C017 C019 central-anchor and cell-partition datums have no physics", "no material mass structural CHT Boolean solver export or fluid-union membership; exact excluded feature IDs recorded", "true"),
        ("G4_INTERFERENCE", "interference count in exported physical candidate solids and required fluid bodies", "0; exclude declared CONSTRUCTION_BODY CONSTRUCTION_SURFACE REFERENCE and KEEP_OUT datums and record their feature IDs", "true"),
        ("G4_ZERO_THICKNESS", "invalid zero-thickness and sliver count in exported physical candidate solids and required fluid bodies", "0; declared zero-thickness construction datums are excluded and separately guarded", "true"),
        ("G4_DUPLICATE_FACES", "duplicate-face count in exported physical candidate solids and required fluid bodies", "0; construction/reference datums are excluded from this count", "true"),
        ("G4_ISOLATED_FLUID", "isolated required fluid-body count", "0", "true"),
        ("G4_ORIFICE_BOOLEAN", "blind or lost orifice count after Boolean", "0 and actual count recorded", "true"),
        ("G4_OPEN_AREA", "actual CAD open area fraction", "8 to 12 percent preferred; deviation requires documented branch review", "true"),
        ("G4_CLEARANCE", "maximum candidate membrane displacement clearance", "no collision at P004 amplitude plus P006 margin", "true"),
        ("G4_NAMED_SELECTIONS", "all required named selections exist", "expected cardinalities pass", "true"),
        ("G4_WB_TRANSFER", "geometry and named selections transfer to Workbench", "both transfer checks PASS", "true"),
        ("G4_NATIVE_SAVE", "native CAD and fluid volume save", "files reopen and hashes recorded", "true"),
        ("G4_STEP_TRANSFER", "STEP export reimport comparison", "record body count envelope volume and any limitation", "false"),
        ("G4_MASS_BUDGET", "mass reporting is evidence-honest", "candidate known mass plus unresolved mass reported separately; no false 11 g closure", "true"),
        ("G4_FOUR_CONFIGS", "same master model supports all four configurations", "all four configuration IDs built without envelope drift", "true"),
        ("G4_BRANCH_SENSITIVITY", "primary C020 0.25/0.50/0.75 branches compared", "thickness collision and connectivity results recorded", "true"),
        ("G4_SINGLE_FACTOR_ISOLATION", "derived vent orifice and exhaust variants differ from balanced parent in exactly one declared factor", "parameter diff and geometry-result diff manifest recorded", "true"),
        ("G4_OUTPUT_HASHES", "native STEP fluid screenshots logs and manifests are traceable", "SHA256 and Git commit recorded", "true"),
        ("P1_INDEPENDENT_REVIEW", "independent peer evidence and artifact review", "PENDING until external review; 006 cannot set PASS", "true"),
    ]
    rows: list[dict[str, object]] = []
    for variant in variant_rows:
        for item_id, requirement, acceptance, hard_gate in items:
            rows.append(
                {
                    "gate_item_id": item_id,
                    "configuration_id": variant["configuration_id"],
                    "variant_id": variant["variant_id"],
                    "variant_kind": variant["variant_kind"],
                    "comparison_parent_variant_id": variant["comparison_parent_variant_id"],
                    "changed_factor": variant["changed_factor"],
                    "selected_vent_candidate_set_id": variant["vent_candidate_set_id"],
                    "selected_orifice_pattern_id": variant["orifice_pattern_id"],
                    "selected_exhaust_branch_id": variant["exhaust_branch_id"],
                    "selected_cell_geometry_rule_id": variant["cell_geometry_rule_id"],
                    "selected_central_anchor_rule_id": variant["central_anchor_rule_id"],
                    "selected_bottom_chamber_rule_id": variant["bottom_chamber_rule_id"],
                    "selected_cell_partition_rule_id": variant["cell_partition_rule_id"],
                    "selected_top_chamber_branch_id": variant["top_chamber_branch_id"],
                    "selected_perimeter_gap_branch_id": variant["perimeter_gap_branch_id"],
                    "selected_side_frame_closure_branch_id": variant["side_frame_closure_branch_id"],
                    "selected_residual_closure_branch_id": variant["residual_closure_branch_id"],
                    "selected_orifice_grid_rule_id": variant["orifice_grid_rule_id"],
                    "requirement": requirement,
                    "status": "NOT_RUN",
                    "measured_value": "",
                    "tolerance_or_acceptance": acceptance,
                    "evidence_path": "",
                    "evidence_sha256": "",
                    "reviewer": "",
                    "date": "",
                    "git_commit": "",
                    "hard_gate": hard_gate,
                    "notes": "006 may populate evidence but may only leave P1_STAGE_GATE pending independent peer review",
                }
            )
    if any(row["status"] != "NOT_RUN" for row in rows):
        raise ValueError("generated P1 gate matrix must start entirely NOT_RUN")
    return rows


def validate_cross_contracts(
    feature_rows: list[dict[str, object]],
    internal_rule_rows: list[dict[str, object]],
    interface_rows: list[dict[str, object]],
    named_rows: list[dict[str, object]],
    open_rows: list[dict[str, object]],
) -> None:
    feature_ids = {str(row["feature_id"]) for row in feature_rows}
    named_by_id = {str(row["selection_id"]): row for row in named_rows}
    if len(named_by_id) != len(named_rows):
        raise ValueError("named-selection contract contains duplicate IDs")
    rule_ids = {str(row["rule_id"]) for row in internal_rule_rows}
    required_rules = {
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
    if rule_ids != required_rules:
        raise ValueError("internal geometry rule set changed")
    interface_forbidden_features = {
        "C017_SUPPORT_ALLOWANCE_REF",
        "C019_TOP_REF",
        "C019_BOTTOM_REF",
        "FLEX_KEEP_OUT_U",
        "CENTRAL_ANCHOR_CAND_TEMPLATE",
        "CELL_PARTITION_CAND_TEMPLATE",
    }
    for row in internal_rule_rows:
        for feature_id in str(row["feature_ids"]).split(";"):
            if feature_id not in feature_ids:
                raise ValueError(
                    f"internal rule references unknown feature: {row['rule_id']}/{feature_id}"
                )
    for row in interface_rows:
        if row["side_a_feature_id"] not in feature_ids or row["side_b_feature_id"] not in feature_ids:
            raise ValueError(f"interface references unknown feature: {row['interface_id']}")
        if (
            row["side_a_feature_id"] in interface_forbidden_features
            or row["side_b_feature_id"] in interface_forbidden_features
        ):
            raise ValueError(f"interface references a nonphysical datum: {row['interface_id']}")
        selection_a = named_by_id.get(str(row["named_selection_a"]))
        selection_b = named_by_id.get(str(row["named_selection_b"]))
        if selection_a is None or selection_b is None:
            raise ValueError(f"interface references unknown named selection: {row['interface_id']}")
        if selection_a["owner_feature_id"] != row["side_a_feature_id"]:
            raise ValueError(f"interface side A selection owner mismatch: {row['interface_id']}")
        if selection_b["owner_feature_id"] != row["side_b_feature_id"]:
            raise ValueError(f"interface side B selection owner mismatch: {row['interface_id']}")
        if row["interface_mode"] != "PAIRED_NONCONFORMAL_OR_MATCHED_FACE":
            raise ValueError(f"unsupported interface mode: {row['interface_id']}")
    for row in named_rows:
        if row["owner_feature_id"] not in feature_ids:
            raise ValueError(f"named selection references unknown feature: {row['selection_id']}")
    for row in open_rows:
        if row["feature_id"] not in feature_ids:
            raise ValueError(f"open question references unknown feature: {row['question_id']}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="verify outputs without rewriting them")
    args = parser.parse_args()

    registry = base.registry_by_id()
    layout_rows = base.build_layout_rows(registry)
    variant_rows = build_variant_rows(registry, layout_rows)
    parameter_rows = build_parameter_map_rows(registry, layout_rows, variant_rows)
    orifice_rows = build_orifice_rows(registry, layout_rows)
    vent_rows = build_vent_rows(registry)
    planform_rows = build_planform_rows(registry, layout_rows)
    internal_rule_rows = build_internal_rule_rows()
    feature_rows = build_feature_rows()
    binding_rows = build_binding_rows(registry, feature_rows)
    interface_rows = build_interface_rows()
    named_rows = build_named_selection_rows()
    open_rows = build_open_question_rows(registry)
    gate_rows = build_gate_rows(variant_rows)
    validate_cross_contracts(
        feature_rows, internal_rule_rows, interface_rows, named_rows, open_rows
    )

    outputs = [
        (VARIANT_OUTPUT, variant_rows),
        (PARAMETER_MAP_OUTPUT, parameter_rows),
        (ORIFICE_OUTPUT, orifice_rows),
        (VENT_OUTPUT, vent_rows),
        (PLANFORM_OUTPUT, planform_rows),
        (INTERNAL_RULE_OUTPUT, internal_rule_rows),
        (FEATURE_OUTPUT, feature_rows),
        (BINDING_OUTPUT, binding_rows),
        (INTERFACE_OUTPUT, interface_rows),
        (NAMED_SELECTION_OUTPUT, named_rows),
        (OPEN_QUESTION_OUTPUT, open_rows),
        (GATE_OUTPUT, gate_rows),
    ]
    for path, rows in outputs:
        if not args.check:
            path.parent.mkdir(parents=True, exist_ok=True)
        base.write_or_check(path, base.render_csv(rows), args.check)

    mode = "check" if args.check else "write"
    print(f"PASS mode={mode} variants={len(variant_rows)} parameters={len(parameter_rows)}")
    print(
        "PASS contracts="
        f"features:{len(feature_rows)},bindings:{len(binding_rows)},"
        f"interfaces:{len(interface_rows)},named:{len(named_rows)},open:{len(open_rows)}"
    )
    print(
        f"PASS orifice_candidates={len(orifice_rows)} vent_candidates={len(vent_rows)} "
        f"exhaust_candidates={len(planform_rows)} internal_rules={len(internal_rule_rows)} "
        f"gate_rows={len(gate_rows)}"
    )


if __name__ == "__main__":
    main()

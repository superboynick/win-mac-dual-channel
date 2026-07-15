#!/usr/bin/env python3
"""Positive and fail-closed tests for the V03 finite-throat contract."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import v03_finite_throat_contract_v1 as contract


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]


def route_fixture() -> dict:
    return json.loads((HERE / contract.ROUTE_NAME).read_text(encoding="utf-8"))


def body_fixture(route: dict) -> dict:
    geometry = route["geometry_contract"]
    return {
        "name": "AJM006_V03_FLUID_CONTINUOUS",
        "bbox_min_mm": list(geometry["bbox_min_mm"]),
        "bbox_max_mm": list(geometry["bbox_max_mm"]),
        "volume_mm3": geometry["analytic_volume_mm3"],
        "face_count": 1000,
        "piece_count": 1,
        "is_closed": True,
        "is_manifold": True,
    }


def producer_fixture(route: dict) -> dict:
    boundaries = route["boundary_contract"]
    groups = {"FLUID_CONTINUOUS": 1, **boundaries}
    body = body_fixture(route)
    return {
        "probe": "v03_continuous_fluid_producer",
        "status": "PASS_PARTIAL_CAD_CAPABILITY",
        "formal_006_completion": False,
        "p1_stage_gate": "NOT_RUN",
        "p1_p6_gates": "NOT_RUN",
        "mesh": "NOT_RUN",
        "physics": "NOT_RUN",
        "exact_product_geometry": "NOT_CLAIMED",
        "assertions": {
            name: True for name in contract.PRODUCER_ASSERTIONS
        },
        "geometry": {
            "cell_count": 12,
            "orifice_count": 972,
            "group_counts": groups,
            "step_boundary_counts": boundaries,
            "all_cells_have_throats": True,
            "throat_counts_by_cell": {
                str(index): 81 for index in range(1, 13)
            },
            "continuous_before_save": body,
            "native_reopen_summary": {
                "body_count": 1,
                "body_fingerprint": copy.deepcopy(body),
            },
            "step_reimport_summary": {
                "body_count": 1,
                "body_fingerprint": copy.deepcopy(body),
            },
        },
    }


def expect_contract_error(action, code_fragment: str) -> None:
    try:
        action()
    except contract.ContractError as exc:
        assert code_fragment in str(exc), (code_fragment, str(exc))
    else:
        raise AssertionError("contract mutation was accepted: " + code_fragment)


def test_route_accepts_independent_static_sources():
    result = contract.validate_route(route_fixture(), REPO)
    assert result == {
        "assignment_count": 972,
        "assignment_sha256": contract.EXPECTED_ASSIGNMENT_SHA256,
        "minimum_spacing_mm": 0.7006239999999995,
        "analytic_volume_mm3": 451.7788188426395,
    }


def test_route_rejects_identity_and_source_tamper():
    for path, value, code in (
        (("product_id",), "AIRJET_PRO", "IDENTITY"),
        (("configuration_id",), "M-2x4-8.0", "IDENTITY"),
        (("source_variant_id",), "G2", "IDENTITY"),
        (("source_contracts", 0, "sha256"), "0" * 64, "SOURCE_HASH"),
    ):
        route = route_fixture()
        target = route
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = value
        expect_contract_error(
            lambda route=route: contract.validate_route(route, REPO), code
        )


def test_route_rejects_c016_relabel_and_value_tamper():
    for key, value in (
        ("value_mm", 0.2),
        ("range_mm", [0.1, 0.2]),
        ("evidence_class", "D"),
        ("status", "product_locked"),
        ("product_fact", True),
    ):
        route = route_fixture()
        route["candidate_parameters"]["C016"][key] = value
        expect_contract_error(
            lambda route=route: contract.validate_route(route, REPO), "C016"
        )


def test_route_rejects_assignment_and_analytic_tamper():
    mutations = (
        lambda route: route["throat_contract"].__setitem__("assignment_sha256", "f" * 64),
        lambda route: route["throat_contract"].__setitem__("diameter_mm", 0.3),
        lambda route: route["throat_contract"].__setitem__("length_mm", 0.05),
        lambda route: route["throat_contract"].__setitem__("axis", [0.0, 1.0, 0.0]),
        lambda route: route["geometry_contract"].__setitem__("analytic_volume_mm3", float("nan")),
        lambda route: route["geometry_contract"]["analytic_volume_components_mm3"].__setitem__(
            "finite_throat_core", 0.0
        ),
        lambda route: route["geometry_contract"].__setitem__(
            "bbox_max_mm", [10.875, 20.75, 3.0]
        ),
    )
    for mutate in mutations:
        route = route_fixture()
        mutate(route)
        expect_contract_error(
            lambda route=route: contract.validate_route(route, REPO), "V03_ROUTE"
        )


def test_blueprint_derivation_rejects_971_and_duplicate_assignment():
    route = route_fixture()
    blueprint_path = REPO / route["source_contracts"][0]["git_path"]
    blueprint = json.loads(blueprint_path.read_text(encoding="utf-8"))
    orifice_group = next(
        item for item in blueprint["groups"]
        if item["solver_name"] == "ORIFICE_EXIT"
    )
    orifice_group["member_keys"].pop()
    assignments = contract.canonical_assignments(blueprint)
    assert len(assignments) == 971
    assignments.append(copy.deepcopy(assignments[0]))
    points = {(item["x_mm"], item["y_mm"]) for item in assignments}
    assert len(assignments) == 972
    assert len(points) == 971
    assert contract.assignment_sha256(assignments) != contract.EXPECTED_ASSIGNMENT_SHA256


def test_producer_accepts_exact_contract():
    route = route_fixture()
    contract.validate_producer_report(route, producer_fixture(route))


def test_producer_rejects_topology_body_and_claim_tamper():
    mutators = (
        lambda report: report["geometry"].__setitem__("orifice_count", 971),
        lambda report: report["geometry"]["group_counts"].__setitem__("INLET", 3),
        lambda report: report["geometry"]["continuous_before_save"].__setitem__(
            "piece_count", 2
        ),
        lambda report: report["geometry"]["continuous_before_save"].__setitem__(
            "is_closed", False
        ),
        lambda report: report["geometry"]["continuous_before_save"].__setitem__(
            "is_manifold", False
        ),
        lambda report: report["geometry"]["continuous_before_save"].__setitem__(
            "volume_mm3", float("inf")
        ),
        lambda report: report["assertions"].__setitem__("input_contract", "true"),
        lambda report: report.__setitem__("mesh", "PASS"),
        lambda report: report.__setitem__("physics", "PASS"),
        lambda report: report.__setitem__("formal_006_completion", True),
    )
    route = route_fixture()
    for mutate in mutators:
        report = producer_fixture(route)
        mutate(report)
        expect_contract_error(
            lambda report=report: contract.validate_producer_report(route, report),
            "V03_PRODUCER",
        )


def main() -> None:
    tests = [
        test_route_accepts_independent_static_sources,
        test_route_rejects_identity_and_source_tamper,
        test_route_rejects_c016_relabel_and_value_tamper,
        test_route_rejects_assignment_and_analytic_tamper,
        test_blueprint_derivation_rejects_971_and_duplicate_assignment,
        test_producer_accepts_exact_contract,
        test_producer_rejects_topology_body_and_claim_tamper,
    ]
    for test in tests:
        test()
        print("PASS " + test.__name__)
    print("AJM006_V03_FINITE_THROAT_CONTRACT=PASS_ALL")


if __name__ == "__main__":
    main()

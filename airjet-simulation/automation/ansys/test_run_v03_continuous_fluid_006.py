#!/usr/bin/env python3
"""Static and validator guards for the V03 continuous-fluid pilot."""

from __future__ import annotations

from contextlib import asynccontextmanager
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from types import ModuleType, SimpleNamespace
import sys


def setup_mcp_stub() -> None:
    if importlib.util.find_spec("mcp") is not None:
        return

    @asynccontextmanager
    async def fake_stdio_client(params, errlog=None):
        yield (SimpleNamespace(), SimpleNamespace())

    class FakeClientSession:
        pass

    class FakeStdioServerParameters:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    types_mod = ModuleType("mcp.types")
    types_mod.TextContent = type("TextContent", (), {})
    types_mod.CallToolResult = type("CallToolResult", (), {})
    types_mod.Implementation = SimpleNamespace
    mcp_mod = ModuleType("mcp")
    mcp_mod.ClientSession = FakeClientSession
    mcp_mod.StdioServerParameters = FakeStdioServerParameters
    mcp_mod.types = types_mod
    client_mod = ModuleType("mcp.client")
    stdio_mod = ModuleType("mcp.client.stdio")
    stdio_mod.stdio_client = fake_stdio_client
    sys.modules["mcp"] = mcp_mod
    sys.modules["mcp.types"] = types_mod
    sys.modules["mcp.client"] = client_mod
    sys.modules["mcp.client.stdio"] = stdio_mod


setup_mcp_stub()
sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_v03_continuous_fluid_006 as runner


HEAD = "a" * 40
PROFILE_CONTRACT = "b" * 64
DEPENDENCY_MANIFEST = "c" * 64


def throat_inventory(
    geometry_tolerance: float, xy_tolerance: float
) -> dict:
    return {
        "pass": True,
        "candidate_face_count": 972,
        "expected_radius_mm": 0.125,
        "expected_diameter_mm": 0.25,
        "expected_length_mm": 0.10,
        "expected_construction_length_mm": 0.102,
        "expected_effective_lateral_area_mm2": 0.07853981633974483,
        "expected_construction_lateral_area_mm2": 0.08011061266653972,
        "expected_center_z_mm": 1.5675,
        "expected_z_min_mm": 1.5175,
        "expected_z_max_mm": 1.6175,
        "geometry_tolerance_mm": geometry_tolerance,
        "area_tolerance_mm2": 0.001,
        "xy_inventory": {
            "expected_count": 972,
            "actual_count": 972,
            "matched_count": 972,
            "missing_count": 0,
            "unexpected_count": 0,
            "one_to_one_complete": True,
            "max_xy_delta_mm": 0.0,
            "tolerance_mm": xy_tolerance,
        },
    }


def exact_groups() -> dict:
    return {
        "FLUID_CONTINUOUS": 1,
        "INLET": 4,
        "OUTLET": 1,
        "MEMBRANE_TOP": 12,
        "MEMBRANE_BOTTOM": 12,
        "ORIFICE_THROAT_WALL": 972,
        "HEAT_WALL": 1,
    }


def valid_report_and_manifest() -> tuple[dict, dict, dict]:
    report_files = {}
    manifest_files = []
    for index, (role, filename) in enumerate(
        sorted(runner.EXPECTED_PRODUCER_ARTIFACTS.items())
    ):
        digest = ("{:x}".format(index + 1) * 64)[:64]
        size = 1000 + index
        report_files[role] = {
            "path": "D:\\AirJet_P1\\AJM-P1-CAD-006\\" + filename,
            "size": size,
            "sha256": digest,
        }
        manifest_files.append({
            "relative_path": filename,
            "size": size,
            "sha256": digest,
        })
    groups = exact_groups()
    step_groups = dict(groups)
    del step_groups["FLUID_CONTINUOUS"]
    report = {
        "schema_version": 1,
        "task": "AJM006_V03_CONTINUOUS_FLUID_FULL_PRODUCT_PILOT",
        "probe": "v03_continuous_fluid_producer",
        "status": "PASS_PARTIAL_CAD_CAPABILITY",
        "engineering_capability": "PASS_PARTIAL_CAD_CAPABILITY",
        "pilot_result": "PASS_PRELIMINARY_V03_FINITE_THROAT_GEOMETRY",
        "claim_scope": "V03_CONTINUOUS_FLUID_GEOMETRY_PILOT_ONLY",
        "formal_006_completion": False,
        "p1_stage_gate": "NOT_RUN",
        "p1_p6_gates": "NOT_RUN",
        "mesh": "NOT_RUN",
        "physics": "NOT_RUN",
        "pyfluent": "NOT_RUN",
        "workbench": "NOT_RUN",
        "visibility": "NOT_USER_OBSERVED",
        "exact_product_geometry": "NOT_CLAIMED",
        "full_variant_campaign": "NOT_RUN_1_OF_9_ONLY",
        "geometry_representation": (
            "SINGLE_CONTINUOUS_FLUID_BODY_WITH_972_EXPLICIT_FINITE_THROATS"
        ),
        "license_arguments_added": False,
        "native_parameterization": "NOT_PROVEN",
        "external_native_attach": "NOT_PROVEN",
        "native_named_selection_transfer": "NOT_PROVEN",
        "trusted_production_profile_binding": "NOT_RUN_PRELIMINARY_PROFILE",
        "formal_convex_hull_contract": "NOT_RUN",
        "identity": {
            "git_head": HEAD,
            "profile_id": runner.PROFILE_ID,
            "script_sha256": runner.PROFILE_SCRIPT_SHA256,
            "profile_contract_sha256": PROFILE_CONTRACT,
            "dependency_manifest_sha256": DEPENDENCY_MANIFEST,
            "case_id": runner.CASE_ID,
        },
        "assertions": {
            name: True for name in runner.EXPECTED_REPORT_ASSERTIONS
        },
        "c016_candidate": {
            "parameter_id": "C016",
            "value_mm": 0.10,
            "range_mm": [0.05, 0.20],
            "evidence_class": "C",
            "status": "cad_placeholder",
            "product_fact": False,
            "uncertainty_scan": "REQUIRED_LATER_NOT_RUN",
        },
        "geometry": {
            "source_variant_id": "M-3x4-7.0__R50_BALANCED",
            "configuration_id": "M-3x4-7.0",
            "cell_count": 12,
            "orifice_count": 972,
            "orifice_diameter_mm": 0.25,
            "throat_length_mm": 0.10,
            "throat_length_range_mm": [0.05, 0.20],
            "throat_length_evidence_class": "C",
            "numerical_overlap_mm": 0.001,
            "boolean_volume_delta_mm3": 0.0,
            "route_analytic_volume_mm3": 451.7788188426395,
            "native_analytic_volume_delta_mm3": 0.0,
            "native_route_volume_tolerance_mm3": 0.08,
            "step_analytic_volume_delta_mm3": 0.0,
            "step_route_volume_tolerance_mm3": 0.03,
            "continuous_route_ok": True,
            "native_route_ok": True,
            "step_route_ok": True,
            "group_counts": groups,
            "group_required": groups,
            "group_semantics_ok": True,
            "all_cells_have_throats": True,
            "throat_counts_by_cell": {
                str(index): 81 for index in range(1, 13)
            },
            "step_boundary_counts": step_groups,
            "continuous_before_save": {
                "bbox_min_mm": [-10.875, -17.75, 1.2675],
                "bbox_max_mm": [10.875, 20.75, 2.8],
                "volume_mm3": 451.7788188426395,
                "piece_count": 1,
                "is_closed": True,
                "is_manifold": True,
            },
            "expected_xy_contract": {
                "expected_count": 972,
                "unique_count_rounded_9dp": 972,
                "minimum_center_spacing_mm": 0.700624,
                "required_minimum_center_spacing_mm": 0.29,
                "step_xy_tolerance_mm": 0.02,
                "pass": True,
            },
            "throat_inventory_before_save": throat_inventory(0.002, 0.002),
            "native_throat_inventory": throat_inventory(0.002, 0.002),
            "step_throat_inventory": throat_inventory(0.005, 0.02),
            "native_reopen_summary": {
                "open_success": True,
                "body_count": 1,
                "body_fingerprint": {
                    "bbox_min_mm": [-10.875, -17.75, 1.2675],
                    "bbox_max_mm": [10.875, 20.75, 2.8],
                    "volume_mm3": 451.7788188426395,
                    "piece_count": 1,
                    "is_closed": True,
                    "is_manifold": True,
                },
                "group_counts": groups,
            },
            "step_reimport_summary": {
                "open_success": True,
                "body_count": 1,
                "body_fingerprint": {
                    "bbox_min_mm": [-10.875, -17.75, 1.2675],
                    "bbox_max_mm": [10.875, 20.75, 2.8],
                    "volume_mm3": 451.7788188426395,
                    "piece_count": 1,
                    "is_closed": True,
                    "is_manifold": True,
                },
                "boundary_counts": step_groups,
                "comparison_tolerances": {
                    "bbox_tolerance_mm": 0.02,
                    "volume_absolute_tolerance_mm3": 0.08,
                    "volume_relative_tolerance": 1.0e-5,
                    "face_count_required": False,
                    "names_required": False,
                    "throat_xy_tolerance_mm": 0.02,
                    "comparison_basis": "INDEPENDENT_ROUTE_ANALYTIC",
                    "native_to_step_volume_delta_diagnostic_only": True,
                    "route_analytic_volume_tolerance_mm3": 0.03,
                },
                "comparison_deltas": {
                    "max_bbox_delta_mm": 0.0,
                    "max_volume_delta_mm3": 0.0,
                },
            },
        },
        "files": report_files,
    }
    manifest = {
        "job_id": "v03-job-001",
        "phase": "PROCESS_EXITED_0",
        "files": [{
            "relative_path": runner.PRODUCER_REPORT,
            "size": 900,
            "sha256": "d" * 64,
            "report_json": report,
        }] + manifest_files,
    }
    state = {
        "job_id": "v03-job-001",
        "profile_contract_sha256": PROFILE_CONTRACT,
        "profile_dependency_manifest_sha256": DEPENDENCY_MANIFEST,
    }
    return report, manifest, state


def validate(report: dict, manifest: dict, state: dict) -> None:
    manifest["files"][0]["report_json"] = report
    runner.validate_producer_report(manifest, state, HEAD)


def test_validator_accepts_exact_v03_contract():
    report, manifest, state = valid_report_and_manifest()
    validate(report, manifest, state)


def test_validator_rejects_c016_product_overclaim():
    report, manifest, state = valid_report_and_manifest()
    report["c016_candidate"]["product_fact"] = True
    try:
        validate(report, manifest, state)
    except RuntimeError as exc:
        assert "C016" in str(exc)
    else:
        raise AssertionError("C016 product overclaim accepted")


def test_validator_rejects_lost_step_throat():
    report, manifest, state = valid_report_and_manifest()
    report["geometry"]["step_throat_inventory"]["candidate_face_count"] = 971
    try:
        validate(report, manifest, state)
    except RuntimeError as exc:
        assert "THROAT" in str(exc)
    else:
        raise AssertionError("lost STEP throat accepted")


def test_validator_rejects_boundary_drift():
    report, manifest, state = valid_report_and_manifest()
    report["geometry"]["step_boundary_counts"]["OUTLET"] = 2
    try:
        validate(report, manifest, state)
    except RuntimeError as exc:
        assert "GEOMETRY" in str(exc)
    else:
        raise AssertionError("STEP boundary drift accepted")


def test_validator_rejects_mesh_overclaim():
    report, manifest, state = valid_report_and_manifest()
    report["mesh"] = "PASS"
    try:
        validate(report, manifest, state)
    except RuntimeError as exc:
        assert "CLAIM_BOUNDARY" in str(exc)
    else:
        raise AssertionError("mesh overclaim accepted")


def test_validator_rejects_truthy_non_boolean_assertion():
    report, manifest, state = valid_report_and_manifest()
    report["assertions"]["input_contract"] = "true"
    try:
        validate(report, manifest, state)
    except RuntimeError as exc:
        assert "ASSERTIONS" in str(exc)
    else:
        raise AssertionError("truthy non-boolean assertion accepted")


def test_compact_report_stays_below_mcp_inline_limit():
    report, _, _ = valid_report_and_manifest()
    payload = json.dumps(report, indent=2, sort_keys=True).encode("utf-8")
    assert len(payload) < 128 * 1024
    geometry = report["geometry"]
    for key in (
        "throat_inventory_before_save",
        "native_throat_inventory",
        "step_throat_inventory",
    ):
        assert "candidate_faces" not in geometry[key]


def test_validator_rejects_nan_and_forged_xy_bounds():
    mutations = (
        lambda geometry: geometry.__setitem__(
            "boolean_volume_delta_mm3", float("nan")
        ),
        lambda geometry: geometry["expected_xy_contract"].__setitem__(
            "minimum_center_spacing_mm", float("nan")
        ),
        lambda geometry: geometry["expected_xy_contract"].__setitem__(
            "required_minimum_center_spacing_mm", -1.0
        ),
        lambda geometry: geometry["step_reimport_summary"][
            "comparison_deltas"
        ].__setitem__("max_volume_delta_mm3", float("nan")),
    )
    for mutate in mutations:
        report, manifest, state = valid_report_and_manifest()
        mutate(report["geometry"])
        try:
            validate(report, manifest, state)
        except RuntimeError:
            pass
        else:
            raise AssertionError("NaN or forged XY bound accepted")


def test_preflight_exact_profile_contract():
    policy = {
        "schema_version": 2,
        "production_contracts": {
            "execution_state": "STATIC_CONTRACT_ONLY_NOT_REGISTERED",
            "p1_p6_gates": "NOT_RUN",
        },
        "profiles": [{
            "profile_id": runner.PROFILE_ID,
            "engine": "spaceclaim",
            "script": runner.PROFILE_SCRIPT,
            "sha256": runner.PROFILE_SCRIPT_SHA256,
            "timeout_seconds": 7200,
            "output_root_id": "p1_cad_006",
            "reports": [runner.PRODUCER_REPORT],
            "predecessor": None,
        }],
    }
    original_git = runner.git_capture
    original_blob = runner.read_git_blob

    def fake_git(*args):
        outputs = {
            ("rev-parse", "--abbrev-ref", "HEAD"): "main",
            ("status", "--porcelain=v1"): "",
            ("rev-parse", "HEAD"): HEAD,
            ("rev-list", "--left-right", "--count", HEAD + "...origin/main"): "0\t0",
            ("verify-commit", "--raw", HEAD): "",
        }
        return {"exit_code": 0, "stdout": outputs[args], "stderr": ""}

    try:
        runner.git_capture = fake_git
        runner.read_git_blob = lambda head, path: json.dumps(policy).encode()
        assert runner.preflight()["preflight_ok"]
        policy["profiles"][0]["script"] = "006/wrong.py"
        result = runner.preflight()
        assert not result["preflight_ok"]
        assert "BLOCKED_PROFILE_CONTRACT_MISMATCH" in result["preflight_errors"]
    finally:
        runner.git_capture = original_git
        runner.read_git_blob = original_blob


def test_v03_script_is_isolated_and_fail_closed():
    root = Path(__file__).resolve().parent
    v02 = root / "approved" / "006" / "v02_preliminary_producer.py"
    v03 = root / "approved" / "006" / "v03_continuous_fluid_producer.py"
    assert hashlib.sha256(v02.read_bytes()).hexdigest() == (
        "e575c045ddc329175a9fad8e091adc44f299b0d86e741e098279d0fba9790a48"
    )
    source = v03.read_text(encoding="utf-8")
    assert runner.PROFILE_SCRIPT_SHA256 != "V03_SCRIPT_SHA256_PLACEHOLDER"
    assert runner.PROFILE_SCRIPT_SHA256 == hashlib.sha256(
        v03.read_bytes()
    ).hexdigest()
    compile(source, str(v03), "exec")
    for required in (
        "interface_z - numerical_overlap_mm",
        'merge_into(upstream, [downstream], "V03_FULL_CONTINUOUS_FLUID")',
        '"ORIFICE_THROAT_WALL": 972',
        '"product_fact": False',
        '"mesh": "NOT_RUN"',
        '"physics": "NOT_RUN"',
        'len(built_bodies) != 1',
        'step_throat_inventory["pass"]',
        'and continuous_route_ok',
        'set(throat_counts_by_cell.values()) == set([81])',
        'expected_xy_evidence["pass"]',
        'v03_finite_throat_route_v1.json',
        'expected_construction_lateral_area_mm2',
    ):
        assert required in source
    for forbidden in (
        "ShareTopology.FindAndFix",
        "GenerateMesh(",
        ".Solve(",
        "launch_fluent(",
        "GetTemplate(",
    ):
        assert forbidden not in source


def main():
    tests = [
        test_validator_accepts_exact_v03_contract,
        test_validator_rejects_c016_product_overclaim,
        test_validator_rejects_lost_step_throat,
        test_validator_rejects_boundary_drift,
        test_validator_rejects_mesh_overclaim,
        test_validator_rejects_truthy_non_boolean_assertion,
        test_compact_report_stays_below_mcp_inline_limit,
        test_validator_rejects_nan_and_forged_xy_bounds,
        test_preflight_exact_profile_contract,
        test_v03_script_is_isolated_and_fail_closed,
    ]
    for test in tests:
        test()
        print("PASS " + test.__name__)
    print("AJM006_V03_CONTINUOUS_FLUID_GUARDS=PASS_ALL")


if __name__ == "__main__":
    main()

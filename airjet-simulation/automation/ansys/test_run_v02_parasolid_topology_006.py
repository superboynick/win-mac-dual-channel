#!/usr/bin/env python3
"""Static guards for the AJM-006 V02 Parasolid route-discovery suite."""

from __future__ import annotations

from contextlib import asynccontextmanager
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
import run_v02_parasolid_topology_006 as runner


HEAD = "a" * 40
PROFILE_CONTRACT = "b" * 64
PRODUCER_JOB_ID = "producer-job-001"
CONVERTER_JOB_ID = "converter-job-001"


def converter_profile(sha256=None):
    return {
        "profile_id": runner.CONVERTER_PROFILE_ID,
        "engine": "spaceclaim",
        "script": "006/v02_parasolid_converter.py",
        "sha256": sha256 or runner.CONVERTER_SCRIPT_SHA256,
        "timeout_seconds": 3600,
        "output_root_id": "p1_cad_006",
        "reports": [runner.CONVERTER_REPORT],
        "predecessor": {
            "profile_id": runner.PRODUCER_PROFILE_ID,
            "report": runner.producer_runner.PRODUCER_REPORT,
            "required_probe": "v02_preliminary_producer",
            "required_status": "PASS_PARTIAL_CAD_CAPABILITY",
            "required_assertions": sorted(
                runner.producer_runner.EXPECTED_REPORT_ASSERTIONS
            ),
            "artifacts": sorted(
                runner.EXPECTED_CONVERTER_PREDECESSOR_ARTIFACTS
            ),
        },
    }


def observer_profile(sha256=None):
    return {
        "profile_id": runner.OBSERVER_PROFILE_ID,
        "engine": "workbench",
        "script": "006/v02_parasolid_topology_observer.wbjn",
        "sha256": sha256 or runner.OBSERVER_SCRIPT_SHA256,
        "timeout_seconds": 3600,
        "output_root_id": "p1_cad_006",
        "reports": [runner.OBSERVER_REPORT],
        "predecessor": {
            "profile_id": runner.CONVERTER_PROFILE_ID,
            "report": runner.CONVERTER_REPORT,
            "required_probe": "v02_parasolid_converter",
            "required_status": "PASS_PARTIAL_CAD_CAPABILITY",
            "required_assertions": sorted(
                runner.EXPECTED_CONVERTER_ASSERTIONS
            ),
            "artifacts": sorted(
                runner.EXPECTED_OBSERVER_PREDECESSOR_ARTIFACTS
            ),
        },
    }


def policy_bytes(converter=None, observer=None):
    return json.dumps({
        "schema_version": 2,
        "production_contracts": {
            "execution_state": "STATIC_CONTRACT_ONLY_NOT_REGISTERED",
            "p1_p6_gates": "NOT_RUN",
        },
        "profiles": [
            converter or converter_profile(),
            observer or observer_profile(),
        ],
    }).encode("utf-8")


def base_preflight():
    return {
        "git_head": HEAD,
        "preflight_ok": True,
        "preflight_errors": [],
        "profile_found": True,
        "profile_script_sha256_matches": True,
        "execution_state_static": True,
        "p1_p6_not_run": True,
    }


def run_preflight(blob):
    original_preflight = runner.producer_runner.preflight
    original_read = runner.producer_runner.read_git_blob
    try:
        runner.producer_runner.preflight = base_preflight
        runner.producer_runner.read_git_blob = lambda head, path: blob
        return runner.combined_preflight()
    finally:
        runner.producer_runner.preflight = original_preflight
        runner.producer_runner.read_git_blob = original_read


def test_preflight_passes():
    result = run_preflight(policy_bytes())
    assert result["preflight_ok"], result
    assert result["converter_profile_found"]
    assert result["observer_profile_found"]


def test_preflight_rejects_converter_hash_mismatch():
    result = run_preflight(policy_bytes(converter_profile("0" * 64)))
    assert not result["preflight_ok"]
    assert "BLOCKED_CONVERTER_SCRIPT_HASH_MISMATCH" in result[
        "preflight_errors"
    ]


def test_preflight_rejects_observer_artifact_contract():
    profile = observer_profile()
    profile["predecessor"]["artifacts"].append("product.step")
    result = run_preflight(policy_bytes(observer=profile))
    assert not result["preflight_ok"]
    assert "BLOCKED_OBSERVER_PROFILE_CONTRACT" in result["preflight_errors"]


def converter_report():
    artifacts = {}
    for index, (role, relative) in enumerate(
        sorted(runner.EXPECTED_CONVERTER_FILES.items())
    ):
        artifacts[role] = {
            "path": "D:\\AirJet_P1\\" + relative,
            "size": 1000 + index,
            "sha256": ("%x" % (index + 1)) * 64,
        }
    return {
        "probe": "v02_parasolid_converter",
        "status": "PASS_PARTIAL_CAD_CAPABILITY",
        "engineering_capability": "PASS_PARTIAL_CAD_CAPABILITY",
        "formal_006_completion": False,
        "p1_stage_gate": "NOT_RUN",
        "p1_p6_gates": "NOT_RUN",
        "diagnostic_only": True,
        "mesh": "NOT_RUN",
        "physics": "NOT_RUN",
        "source_native_mutated": False,
        "representation_conversion": True,
        "interface_topology": "NOT_EVALUATED_UNTIL_PARASOLID_OBSERVER",
        "license_arguments_added": False,
        "identity": {
            "git_head": HEAD,
            "profile_id": runner.CONVERTER_PROFILE_ID,
            "script_sha256": runner.CONVERTER_SCRIPT_SHA256,
            "profile_contract_sha256": PROFILE_CONTRACT,
            "case_id": runner.CASE_ID,
        },
        "predecessor": {
            "job_id": PRODUCER_JOB_ID,
            "profile_id": runner.PRODUCER_PROFILE_ID,
        },
        "assertions": dict(
            (name, True) for name in runner.EXPECTED_CONVERTER_ASSERTIONS
        ),
        "conversion": {
            "source_native_face_counts": [978, 2044],
            "native_open_face_counts": [978, 2044],
            "parasolid_reimport_face_counts": [978, 2044],
        },
        "staging_final_recheck": {
            "unchanged": True,
            "workspace_exact": True,
        },
        "files": artifacts,
    }


def converter_manifest(report):
    files = [{
        "relative_path": runner.CONVERTER_REPORT,
        "size": 1024,
        "sha256": "f" * 64,
        "report_json": report,
    }]
    for role, relative in runner.EXPECTED_CONVERTER_FILES.items():
        item = report["files"][role]
        files.append({
            "relative_path": relative,
            "size": item["size"],
            "sha256": item["sha256"],
        })
    return {
        "job_id": CONVERTER_JOB_ID,
        "phase": "PROCESS_EXITED_0",
        "files": files,
    }


def converter_job_state():
    return {
        "profile_contract_sha256": PROFILE_CONTRACT,
        "job_id": CONVERTER_JOB_ID,
        "phase": "PROCESS_EXITED_0",
    }


def test_validate_converter_accepts_exact_chain():
    report = converter_report()
    returned = runner.validate_converter_report(
        converter_manifest(report),
        converter_job_state(),
        HEAD,
        PRODUCER_JOB_ID,
    )
    assert returned["conversion"]["parasolid_reimport_face_counts"] == [
        978,
        2044,
    ]


def test_validate_converter_rejects_topology_loss():
    report = converter_report()
    report["conversion"]["parasolid_reimport_face_counts"] = [6, 2044]
    try:
        runner.validate_converter_report(
            converter_manifest(report),
            converter_job_state(),
            HEAD,
            PRODUCER_JOB_ID,
        )
    except RuntimeError as error:
        assert "CONVERTER_TOPOLOGY_OR_STAGING_INVALID" in str(error)
    else:
        raise AssertionError("Parasolid topology loss was accepted")


def test_validate_converter_rejects_wrong_manifest_job():
    report = converter_report()
    manifest = converter_manifest(report)
    manifest["job_id"] = "stale-converter-job"
    try:
        runner.validate_converter_report(
            manifest,
            converter_job_state(),
            HEAD,
            PRODUCER_JOB_ID,
        )
    except RuntimeError as error:
        assert "CONVERTER_MANIFEST_JOB_OR_PHASE_MISMATCH" in str(error)
    else:
        raise AssertionError("Wrong converter manifest job was accepted")


def observer_report(
    topology_result="972_COINCIDENT_FACE_PAIRS",
    topology_detail="COINCIDENT_PAIR_GEOMETRY_CONFIRMED",
    observed_face_counts_match=True,
    solver_shape_matches=True,
):
    artifacts = {}
    for index, (role, relative) in enumerate(
        sorted(runner.EXPECTED_OBSERVER_FILES.items())
    ):
        artifacts[role] = {
            "path": "D:\\AirJet_P1\\" + relative,
            "exists": True,
            "size": 2000 + index,
            "sha256": ("%x" % (index + 5)) * 64,
        }
    route_assessment = (
        "PASS_CANDIDATE_ROUTE_TO_MESH"
        if (
            topology_result in {
                "972_SHARED_SINGLE_FACE",
                "972_COINCIDENT_FACE_PAIRS",
            }
            and observed_face_counts_match
            and solver_shape_matches
        )
        else "REJECTED_ROUTE_TOPOLOGY"
    )
    return {
        "probe": "v02_parasolid_topology_observer",
        "status": "PASS_PRELIMINARY_PARASOLID_TOPOLOGY_OBSERVATION",
        "engineering_capability": (
            "PASS_PRELIMINARY_PARASOLID_TOPOLOGY_OBSERVATION"
        ),
        "formal_006_completion": False,
        "p1_stage_gate": "NOT_RUN",
        "p1_p6_gates": "NOT_RUN",
        "diagnostic_only": True,
        "mesh": "NOT_EVALUATED_NO_MESH",
        "license_arguments_added": False,
        "identity": {
            "git_head": HEAD,
            "profile_id": runner.OBSERVER_PROFILE_ID,
            "script_sha256": runner.OBSERVER_SCRIPT_SHA256,
            "profile_contract_sha256": PROFILE_CONTRACT,
            "case_id": runner.CASE_ID,
        },
        "predecessor_job_id": CONVERTER_JOB_ID,
        "predecessor": {
            "job_id": CONVERTER_JOB_ID,
            "profile_id": runner.CONVERTER_PROFILE_ID,
        },
        "assertions": dict(
            (name, True) for name in runner.EXPECTED_OBSERVER_ASSERTIONS
        ),
        "topology_result": topology_result,
        "topology_detail": topology_detail,
        "route_assessment": route_assessment,
        "route_assessment_basis": {
            "interface_classification_is_candidate": topology_result in {
                "972_SHARED_SINGLE_FACE",
                "972_COINCIDENT_FACE_PAIRS",
            },
            "observed_face_counts_match_parasolid_reimport": (
                observed_face_counts_match
            ),
            "solver_shape_matches_parasolid_reimport": solver_shape_matches,
            "mesh_still_required": True,
        },
        "observer_summary": {
            "topology_result": topology_result,
            "topology_detail": topology_detail,
            "body_count": 2,
            "total_body_face_references": 2050,
            "role_binding_valid": True,
            "observed_face_counts_match_parasolid_reimport": (
                observed_face_counts_match
            ),
            "solver_shape_matches_parasolid_reimport": solver_shape_matches,
            "shared_node_or_conformal_mesh": "NOT_EVALUATED_NO_MESH",
        },
        "files": artifacts,
    }


def observer_manifest(report):
    files = [{
        "relative_path": runner.OBSERVER_REPORT,
        "size": 1024,
        "sha256": "e" * 64,
        "report_json": report,
    }]
    for role, relative in runner.EXPECTED_OBSERVER_FILES.items():
        item = report["files"][role]
        files.append({
            "relative_path": relative,
            "size": item["size"],
            "sha256": item["sha256"],
        })
    return {
        "job_id": "observer-job-001",
        "phase": "PROCESS_EXITED_0",
        "files": files,
    }


def observer_job_state():
    return {
        "profile_contract_sha256": PROFILE_CONTRACT,
        "job_id": "observer-job-001",
        "phase": "PROCESS_EXITED_0",
    }


def test_validate_observer_accepts_candidate_route():
    report = observer_report()
    returned = runner.validate_observer_report(
        observer_manifest(report),
        observer_job_state(),
        HEAD,
        CONVERTER_JOB_ID,
    )
    assert returned["route_assessment"] == "PASS_CANDIDATE_ROUTE_TO_MESH"


def test_validate_observer_rejects_nonterminal_phase():
    report = observer_report()
    manifest = observer_manifest(report)
    manifest["phase"] = "RUNNING"
    try:
        runner.validate_observer_report(
            manifest, observer_job_state(), HEAD, CONVERTER_JOB_ID
        )
    except RuntimeError as error:
        assert "OBSERVER_MANIFEST_JOB_OR_PHASE_MISMATCH" in str(error)
    else:
        raise AssertionError("Nonterminal observer state was accepted")


def test_validate_observer_accepts_route_rejection_as_observation():
    report = observer_report("MIXED_OR_OTHER", "UNRESOLVED_MIXED")
    returned = runner.validate_observer_report(
        observer_manifest(report),
        observer_job_state(),
        HEAD,
        CONVERTER_JOB_ID,
    )
    assert returned["route_assessment"] == "REJECTED_ROUTE_TOPOLOGY"
    assert returned["p1_stage_gate"] == "NOT_RUN"


def test_validate_observer_rejects_candidate_route_when_face_counts_drift():
    report = observer_report(observed_face_counts_match=False)
    returned = runner.validate_observer_report(
        observer_manifest(report),
        observer_job_state(),
        HEAD,
        CONVERTER_JOB_ID,
    )
    assert returned["route_assessment"] == "REJECTED_ROUTE_TOPOLOGY"
    assert returned["route_assessment_basis"]["mesh_still_required"] is True


def test_validate_observer_rejects_candidate_route_when_body_shape_drifts():
    report = observer_report(solver_shape_matches=False)
    returned = runner.validate_observer_report(
        observer_manifest(report),
        observer_job_state(),
        HEAD,
        CONVERTER_JOB_ID,
    )
    assert returned["route_assessment"] == "REJECTED_ROUTE_TOPOLOGY"


def test_validate_observer_rejects_illegal_result_detail_pair():
    report = observer_report(
        "972_SHARED_SINGLE_FACE", "COINCIDENT_PAIR_GEOMETRY_CONFIRMED"
    )
    try:
        runner.validate_observer_report(
            observer_manifest(report),
            observer_job_state(),
            HEAD,
            CONVERTER_JOB_ID,
        )
    except RuntimeError as error:
        assert "OBSERVER_TOPOLOGY_SUMMARY_INVALID" in str(error)
    else:
        raise AssertionError("illegal result/detail pair was accepted")


def test_validate_observer_rejects_p1_overclaim():
    report = observer_report()
    report["p1_stage_gate"] = "PASS"
    try:
        runner.validate_observer_report(
            observer_manifest(report),
            observer_job_state(),
            HEAD,
            CONVERTER_JOB_ID,
        )
    except RuntimeError as error:
        assert "OBSERVER_CLAIM_BOUNDARY_VIOLATION" in str(error)
    else:
        raise AssertionError("P1 overclaim was accepted")


def test_embedded_mechanical_script_formats_and_compiles():
    observer = (
        Path(__file__).resolve().parent
        / "approved"
        / "006"
        / "v02_parasolid_topology_observer.wbjn"
    ).read_text(encoding="utf-8")
    marker = "    model_script = r'''"
    start = observer.find(marker) + len(marker)
    end = observer.find("\n''' % (", start)
    assert start >= len(marker) and end > start
    template = observer[start:end]
    rendered = template % (
        "inspection.json",
        "a" * 64,
        "inventory.json",
        "parasolid.json",
        972,
        1.5175,
        0.04908738521234052,
    )
    compile(rendered, "embedded-parasolid-mechanical-observer", "exec")


def test_embedded_classifier_requires_pair_geometry_and_adjacent_bodies():
    observer = (
        Path(__file__).resolve().parent
        / "approved"
        / "006"
        / "v02_parasolid_topology_observer.wbjn"
    ).read_text(encoding="utf-8")
    for invariant in (
        '+ relations.get("AdjacentBodies", [])',
        "coincident_geometry_pairs == expected_orifice_count",
        '"centroid_xy_max_delta_mm"',
        '"plane_gap_mm"',
        '"bbox_max_delta_mm"',
        '"area_delta_mm2"',
        '"geometry_matches"',
        '"pair_centroid_xy_tolerance_mm": 0.005',
        '"pair_plane_gap_tolerance_mm": 0.005',
        '"pair_bbox_tolerance_mm": 0.005',
    ):
        assert invariant in observer


def test_runner_uses_three_stage_isolated_chain():
    source = Path(runner.__file__).read_text(encoding="utf-8")
    assert "spec_from_file_location" in source
    assert "PRODUCER_RUNNER_PATH" in source
    assert "import run_v02_preliminary_006" not in source
    assert source.index("producer_state = await") < source.index(
        "converter_state = await"
    ) < source.index("observer_state = await")
    assert '"predecessor_job_id": producer_state["job_id"]' in source
    assert '"predecessor_job_id": converter_state["job_id"]' in source


def test_split_step_wrapper_is_converter_only_and_fail_closed():
    root = Path(__file__).resolve().parent
    wrapper = (root / "run_v02_split_step_converter_006.py").read_text(
        encoding="utf-8"
    )
    converter = (
        root / "approved" / "006" / "v02_parasolid_converter.py"
    ).read_text(encoding="utf-8")
    assert "ajm006-spaceclaim-v02-split-step-converter-v1" in wrapper
    assert "base.CONVERTER_ONLY = True" in wrapper
    assert "upstream.step" in wrapper and "downstream.step" in wrapper
    assert "SPLIT_STEP_SOURCE_BODY_NAMES_MISMATCH" in converter
    assert "Delete.Execute(Selection.Create(" in converter
    assert "NOT_EVALUATED_SEPARATE_FILES_ONLY" in converter
    assert "DocumentSave.Execute(native_path)" not in converter
    assert "GenerateMesh(" not in converter
    assert ".Solve(" not in converter


def main():
    tests = [
        test_preflight_passes,
        test_preflight_rejects_converter_hash_mismatch,
        test_preflight_rejects_observer_artifact_contract,
        test_validate_converter_accepts_exact_chain,
        test_validate_converter_rejects_topology_loss,
        test_validate_converter_rejects_wrong_manifest_job,
        test_validate_observer_accepts_candidate_route,
        test_validate_observer_rejects_nonterminal_phase,
        test_validate_observer_accepts_route_rejection_as_observation,
        test_validate_observer_rejects_candidate_route_when_face_counts_drift,
        test_validate_observer_rejects_candidate_route_when_body_shape_drifts,
        test_validate_observer_rejects_illegal_result_detail_pair,
        test_validate_observer_rejects_p1_overclaim,
        test_embedded_mechanical_script_formats_and_compiles,
        test_embedded_classifier_requires_pair_geometry_and_adjacent_bodies,
        test_runner_uses_three_stage_isolated_chain,
        test_split_step_wrapper_is_converter_only_and_fail_closed,
    ]
    for test in tests:
        test()
        print("PASS " + test.__name__)
    print("AJM006_V02_PARASOLID_TOPOLOGY_GUARDS=PASS_ALL")


if __name__ == "__main__":
    main()

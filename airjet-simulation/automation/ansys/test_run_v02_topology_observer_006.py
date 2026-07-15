#!/usr/bin/env python3
"""Static guards for the AJM-006 preliminary topology observer suite."""

from __future__ import annotations

from contextlib import asynccontextmanager, contextmanager
import ast
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
import run_v02_topology_observer_006 as runner


HEAD = "a" * 40
PROFILE_CONTRACT = "b" * 64
PREDECESSOR_JOB_ID = "producer-job-001"


def observer_profile(sha256=None):
    return {
        "profile_id": runner.OBSERVER_PROFILE_ID,
        "engine": "workbench",
        "script": "006/v02_preliminary_topology_observer.wbjn",
        "sha256": sha256 or runner.OBSERVER_SCRIPT_SHA256,
        "timeout_seconds": 3600,
        "output_root_id": "p1_cad_006",
        "reports": [runner.OBSERVER_REPORT],
        "predecessor": {
            "profile_id": runner.PRODUCER_PROFILE_ID,
            "report": "v02_preliminary_producer.json",
            "required_probe": "v02_preliminary_producer",
            "required_status": "PASS_PARTIAL_CAD_CAPABILITY",
            "required_assertions": sorted(
                runner.producer_runner.EXPECTED_REPORT_ASSERTIONS
            ),
            "artifacts": sorted(runner.EXPECTED_PREDECESSOR_ARTIFACTS),
        },
    }


def policy_bytes(profile=None):
    return json.dumps({
        "schema_version": 2,
        "production_contracts": {
            "execution_state": "STATIC_CONTRACT_ONLY_NOT_REGISTERED",
            "p1_p6_gates": "NOT_RUN",
        },
        "profiles": [profile or observer_profile()],
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
    assert result["observer_profile_found"]
    assert result["observer_script_sha256_matches"]


def test_preflight_rejects_hash_mismatch():
    result = run_preflight(policy_bytes(observer_profile("0" * 64)))
    assert not result["preflight_ok"]
    assert "BLOCKED_OBSERVER_SCRIPT_HASH_MISMATCH" in result[
        "preflight_errors"
    ]


def test_preflight_rejects_external_artifact_contract():
    profile = observer_profile()
    profile["predecessor"]["artifacts"].append("unexpected.step")
    result = run_preflight(policy_bytes(profile))
    assert not result["preflight_ok"]
    assert "BLOCKED_OBSERVER_PROFILE_CONTRACT" in result["preflight_errors"]


def test_preflight_rejects_weakened_predecessor_status():
    profile = observer_profile()
    profile["predecessor"]["required_status"] = "PASS_005_CAPABILITY"
    result = run_preflight(policy_bytes(profile))
    assert not result["preflight_ok"]
    assert "BLOCKED_OBSERVER_PROFILE_CONTRACT" in result["preflight_errors"]


def valid_report(
    topology_result="DOWNSTREAM_HEALED_SINGLE_FACE",
    topology_detail="DOWNSTREAM_HEALED_SINGLE_FACE",
):
    artifacts = {}
    for index, (role, relative) in enumerate(
        sorted(runner.EXPECTED_OBSERVER_FILES.items())
    ):
        artifacts[role] = {
            "path": "D:\\AirJet_P1\\" + relative,
            "exists": True,
            "size": 1000 + index,
            "sha256": ("%x" % (index + 1)) * 64,
        }
    report = {
        "probe": runner.OBSERVER_PROBE,
        "status": runner.OBSERVER_PASS_STATUS,
        "engineering_capability": runner.OBSERVER_PASS_STATUS,
        "formal_006_completion": False,
        "p1_stage_gate": "NOT_RUN",
        "p1_p6_gates": "NOT_RUN",
        "diagnostic_only": True,
        "license_arguments_added": False,
        "mesh": runner.EXPECTED_REPORT_MESH,
        "physics": runner.EXPECTED_REPORT_PHYSICS,
        "visibility": "NOT_USER_OBSERVED",
        "identity": {
            "git_head": HEAD,
            "profile_id": runner.OBSERVER_PROFILE_ID,
            "script_sha256": runner.OBSERVER_SCRIPT_SHA256,
            "profile_contract_sha256": PROFILE_CONTRACT,
            "case_id": runner.CASE_ID,
        },
        "predecessor_job_id": PREDECESSOR_JOB_ID,
        "predecessor": {
            "job_id": PREDECESSOR_JOB_ID,
            "profile_id": runner.PRODUCER_PROFILE_ID,
        },
        "assertions": dict(
            (name, True) for name in runner.EXPECTED_OBSERVER_ASSERTIONS
        ),
        "topology_result": topology_result,
        "topology_detail": topology_detail,
        "observer_summary": {
            "topology_result": topology_result,
            "topology_detail": topology_detail,
            "body_count": 2,
            "total_body_face_references": 2050,
            "role_binding_by_predecessor_face_counts": True,
            "shared_node_or_conformal_mesh": (
                runner.EXPECTED_MESH_CONFORMALITY
            ),
        },
        "claim_interpretation": {
            "mesh_conformality": runner.EXPECTED_MESH_CONFORMALITY,
        },
        "files": artifacts,
    }
    if runner.MESH_DIAGNOSTIC_REQUIRED:
        report["observer_summary"]["mesh_summary"] = {
            "status": "PASS_MESH_GENERATED",
            "conformality": "PASS_SHARED_INTERFACE_NODE_IDS",
            "generation_reach": "RETURNED",
            "element_size_mm": 0.5,
            "global_node_count": 10000,
            "global_element_count": 40000,
            "connection_state": "PASS_NO_CONTACT_OR_CONNECTION_OBJECTS",
            "connection_object_count": 0,
            "upstream_body_node_count": 6000,
            "upstream_body_element_count": 20000,
            "downstream_body_node_count": 6000,
            "downstream_body_element_count": 20000,
            "shared_body_node_count": 2000,
            "interface_face_count": 972,
            "interface_node_count": 2000,
            "minimum_nodes_per_interface_face": 2,
            "maximum_nodes_per_interface_face": 4,
            "empty_interface_face_ids": [],
            "nonshared_interface_face_ids": [],
            "unexpected_shared_node_count": 0,
        }
    if runner.OBSERVER_PROFILE_ID.startswith(
        "ajm006-workbench-v02-native-"
    ):
        native_sha256 = "c" * 64
        report["predecessor"]["geometry_sha256"] = native_sha256
        report["staging"] = {
            "source_sha256": native_sha256,
            "copy_sha256": native_sha256,
            "final_sha256": native_sha256,
            "hash_equal": True,
            "unchanged_after_import": True,
            "edit_called": False,
        }
    return report


@contextmanager
def native_mesh_runner_configuration():
    names = {
        "OBSERVER_PROFILE_ID": (
            "ajm006-workbench-v02-native-mesh-conformality-observer-v1"
        ),
        "OBSERVER_REPORT": "v02_native_mesh_conformality_observer.json",
        "OBSERVER_PROBE": "v02_native_mesh_conformality_observer",
        "OBSERVER_PASS_STATUS": (
            "PASS_PRELIMINARY_NATIVE_MESH_CONFORMALITY_OBSERVATION"
        ),
        "EXPECTED_OBSERVER_FILES": {
            "inspection": "v02_native_mesh_conformality_inventory.json",
            "project": "v02_native_mesh_conformality_observer.wbpj",
        },
        "EXPECTED_OBSERVER_ASSERTIONS": (
            runner.EXPECTED_OBSERVER_ASSERTIONS | {"mesh_conformality"}
        ),
        "EXPECTED_REPORT_MESH": "PASS_SHARED_INTERFACE_NODE_IDS",
        "EXPECTED_REPORT_PHYSICS": "NOT_RUN",
        "EXPECTED_MESH_CONFORMALITY": "PASS_SHARED_INTERFACE_NODE_IDS",
        "MESH_DIAGNOSTIC_REQUIRED": True,
        "OBSERVER_REPETITIONS": 2,
        "FIXED_INPUT_REPEATABILITY_REQUIRED": True,
    }
    originals = dict((name, getattr(runner, name)) for name in names)
    try:
        for name, value in names.items():
            setattr(runner, name, value)
        yield
    finally:
        for name, value in originals.items():
            setattr(runner, name, value)


def manifest_for(report):
    files = [{
        "relative_path": runner.OBSERVER_REPORT,
        "size": 1024,
        "sha256": "f" * 64,
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


def job_state():
    return {
        "profile_contract_sha256": PROFILE_CONTRACT,
        "job_id": "observer-job-001",
    }


def test_validate_observer_accepts_healed_observation():
    report = valid_report()
    returned = runner.validate_observer_report(
        manifest_for(report), job_state(), HEAD, PREDECESSOR_JOB_ID
    )
    assert returned["topology_result"] == "DOWNSTREAM_HEALED_SINGLE_FACE"


def test_validate_observer_accepts_mixed_as_diagnostic_only():
    report = valid_report("MIXED_OR_OTHER", "UNRESOLVED_MIXED")
    returned = runner.validate_observer_report(
        manifest_for(report), job_state(), HEAD, PREDECESSOR_JOB_ID
    )
    assert returned["formal_006_completion"] is False
    assert returned["p1_stage_gate"] == "NOT_RUN"


def test_validate_observer_accepts_one_sided_interface_loss():
    detail = (
        "UPSTREAM_ORIFICE_GEOMETRY_LOST_"
        "DOWNSTREAM_972_IMPRINTS_RETAINED"
    )
    report = valid_report("MIXED_OR_OTHER", detail)
    returned = runner.validate_observer_report(
        manifest_for(report), job_state(), HEAD, PREDECESSOR_JOB_ID
    )
    assert returned["topology_detail"] == detail


def test_validate_observer_rejects_p1_overclaim():
    report = valid_report()
    report["p1_stage_gate"] = "PASS"
    try:
        runner.validate_observer_report(
            manifest_for(report), job_state(), HEAD, PREDECESSOR_JOB_ID
        )
    except RuntimeError as error:
        assert "OBSERVER_CLAIM_BOUNDARY_VIOLATION" in str(error)
    else:
        raise AssertionError("P1 overclaim was accepted")


def test_validate_observer_rejects_hash_mismatch():
    report = valid_report()
    manifest = manifest_for(report)
    for item in manifest["files"]:
        if item["relative_path"] == "v02_solver_topology_inventory.json":
            item["sha256"] = "0" * 64
    try:
        runner.validate_observer_report(
            manifest, job_state(), HEAD, PREDECESSOR_JOB_ID
        )
    except RuntimeError as error:
        assert "OBSERVER_ARTIFACT_HASH_OR_SIZE_MISMATCH" in str(error)
    else:
        raise AssertionError("artifact hash mismatch was accepted")


def test_validate_native_mesh_observer_accepts_complete_evidence():
    with native_mesh_runner_configuration():
        report = valid_report(
            "972_SHARED_SINGLE_FACE", "SHARED_ID_MEMBERSHIP_CONFIRMED"
        )
        returned = runner.validate_observer_report(
            manifest_for(report), job_state(), HEAD, PREDECESSOR_JOB_ID
        )
        assert returned["mesh"] == "PASS_SHARED_INTERFACE_NODE_IDS"


def test_validate_native_mesh_observer_rejects_weakened_evidence():
    with native_mesh_runner_configuration():
        report = valid_report(
            "972_SHARED_SINGLE_FACE", "SHARED_ID_MEMBERSHIP_CONFIRMED"
        )
        report["observer_summary"]["mesh_summary"][
            "global_element_count"
        ] = 0
        try:
            runner.validate_observer_report(
                manifest_for(report), job_state(), HEAD, PREDECESSOR_JOB_ID
            )
        except RuntimeError as error:
            assert "OBSERVER_MESH_SUMMARY_INVALID" in str(error)
        else:
            raise AssertionError("zero-element mesh evidence was accepted")


def test_validate_native_mesh_observer_rejects_nonshared_topology():
    with native_mesh_runner_configuration():
        report = valid_report(
            "MIXED_OR_OTHER", "UNRESOLVED_MIXED"
        )
        try:
            runner.validate_observer_report(
                manifest_for(report), job_state(), HEAD, PREDECESSOR_JOB_ID
            )
        except RuntimeError as error:
            assert "OBSERVER_MESH_SUMMARY_INVALID" in str(error)
        else:
            raise AssertionError("nonshared topology mesh claim was accepted")


def test_validate_native_mesh_observer_rejects_physics_claim():
    with native_mesh_runner_configuration():
        report = valid_report(
            "972_SHARED_SINGLE_FACE", "SHARED_ID_MEMBERSHIP_CONFIRMED"
        )
        report["physics"] = "RUN"
        try:
            runner.validate_observer_report(
                manifest_for(report), job_state(), HEAD, PREDECESSOR_JOB_ID
            )
        except RuntimeError as error:
            assert "OBSERVER_CLAIM_BOUNDARY_VIOLATION" in str(error)
        else:
            raise AssertionError("physics claim was accepted")


def test_validate_fixed_input_repeatability_accepts_equal_reports():
    with native_mesh_runner_configuration():
        reports = [
            valid_report(
                "972_SHARED_SINGLE_FACE", "SHARED_ID_MEMBERSHIP_CONFIRMED"
            )
            for unused in range(2)
        ]
        result = runner.validate_fixed_input_repeatability(reports)
        assert result["status"] == "PASS_FIXED_INPUT_REPEATABILITY"
        assert result["repeat_count"] == 2


def test_validate_fixed_input_repeatability_rejects_hash_drift():
    with native_mesh_runner_configuration():
        reports = [
            valid_report(
                "972_SHARED_SINGLE_FACE", "SHARED_ID_MEMBERSHIP_CONFIRMED"
            )
            for unused in range(2)
        ]
        reports[1]["staging"]["source_sha256"] = "d" * 64
        try:
            runner.validate_fixed_input_repeatability(reports)
        except RuntimeError as error:
            assert "OBSERVER_REPEAT_INPUT_HASH_MISMATCH" in str(error)
        else:
            raise AssertionError("fixed-input hash drift was accepted")


def test_embedded_mechanical_script_formats_and_compiles():
    observer = (
        Path(__file__).resolve().parent
        / "approved"
        / "006"
        / "v02_preliminary_topology_observer.wbjn"
    ).read_text(encoding="utf-8")
    marker = "    model_script = r'''"
    start = observer.find(marker) + len(marker)
    end = observer.find("\n''' % (", start)
    assert start >= len(marker) and end > start
    template = observer[start:end]
    rendered = template % (
        "inspection.json",
        "a" * 64,
        "HASH_BOUND_STEP_TO_WORKBENCH_MECHANICAL_GEODATA",
        False,
        "inventory.json",
        "step.json",
        972,
        1.5175,
        0.04908738521234052,
    )
    compile(rendered, "embedded-mechanical-observer", "exec")


def test_runner_uses_isolated_mode_safe_sibling_import():
    source = Path(runner.__file__).read_text(encoding="utf-8")
    assert "spec_from_file_location" in source
    assert "PRODUCER_RUNNER_PATH" in source
    assert "import run_v02_preliminary_006" not in source


def test_native_wrapper_and_observer_are_fail_closed():
    root = Path(__file__).resolve().parent
    wrapper = (root / "run_v02_native_topology_observer_006.py").read_text(
        encoding="utf-8"
    )
    observer = (
        root / "approved" / "006" / "v02_preliminary_topology_observer.wbjn"
    ).read_text(encoding="utf-8")
    assert "ajm006-workbench-v02-native-topology-observer-v1" in wrapper
    assert "product_two_zone.scdocx" in wrapper
    assert "product.step" not in wrapper
    assert "shutil.copy2(native_path, staged_native_path)" in observer
    assert "SetFile(FilePath=native_path)" not in observer
    assert "if mesh_route:" in observer
    assert "Model.Mesh.GenerateMesh()" in observer
    assert ".Solve(" not in observer
    assert '"edit_called": False' in observer
    assert "if not native_route:" in observer


def test_native_mesh_wrapper_and_branch_are_fail_closed():
    root = Path(__file__).resolve().parent
    wrapper = (
        root / "run_v02_native_mesh_conformality_006.py"
    ).read_text(encoding="utf-8")
    observer = (
        root / "approved" / "006" / "v02_preliminary_topology_observer.wbjn"
    ).read_text(encoding="utf-8")
    assert (
        "ajm006-workbench-v02-native-mesh-conformality-observer-v1"
        in wrapper
    )
    assert 'base.EXPECTED_REPORT_PHYSICS = "NOT_RUN"' in wrapper
    assert "base.MESH_DIAGNOSTIC_REQUIRED = True" in wrapper
    assert 'NATIVE_MESH_PROFILE = (' in observer
    assert "mesh_route = profile_id == NATIVE_MESH_PROFILE" in observer
    assert "Model.Mesh.GenerateMesh()" in observer
    assert "MeshRegionById" in observer
    assert "PASS_SHARED_INTERFACE_NODE_IDS" in observer
    assert '"physics": "NOT_RUN"' in observer
    assert ".Solve(" not in observer


def test_generate_mesh_call_is_nested_under_mesh_route_guard():
    observer = (
        Path(__file__).resolve().parent
        / "approved"
        / "006"
        / "v02_preliminary_topology_observer.wbjn"
    ).read_text(encoding="utf-8")
    marker = "    model_script = r'''"
    start = observer.find(marker) + len(marker)
    end = observer.find("\n''' % (", start)
    template = observer[start:end]
    rendered = template % (
        "inspection.json",
        "a" * 64,
        "HASH_BOUND_NATIVE_STAGING_TO_WORKBENCH_MECHANICAL_GEODATA",
        True,
        "inventory.json",
        "native.json",
        972,
        1.5175,
        0.04908738521234052,
    )
    tree = ast.parse(rendered)
    parents = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent
    calls = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "GenerateMesh"
    ]
    assert len(calls) == 1
    cursor = calls[0]
    guarded = False
    while cursor in parents:
        cursor = parents[cursor]
        if (
            isinstance(cursor, ast.If)
            and isinstance(cursor.test, ast.Name)
            and cursor.test.id == "mesh_route"
        ):
            guarded = True
            break
    assert guarded


def main():
    tests = [
        test_preflight_passes,
        test_preflight_rejects_hash_mismatch,
        test_preflight_rejects_external_artifact_contract,
        test_preflight_rejects_weakened_predecessor_status,
        test_validate_observer_accepts_healed_observation,
        test_validate_observer_accepts_mixed_as_diagnostic_only,
        test_validate_observer_accepts_one_sided_interface_loss,
        test_validate_observer_rejects_p1_overclaim,
        test_validate_observer_rejects_hash_mismatch,
        test_validate_native_mesh_observer_accepts_complete_evidence,
        test_validate_native_mesh_observer_rejects_weakened_evidence,
        test_validate_native_mesh_observer_rejects_nonshared_topology,
        test_validate_native_mesh_observer_rejects_physics_claim,
        test_validate_fixed_input_repeatability_accepts_equal_reports,
        test_validate_fixed_input_repeatability_rejects_hash_drift,
        test_embedded_mechanical_script_formats_and_compiles,
        test_runner_uses_isolated_mode_safe_sibling_import,
        test_native_wrapper_and_observer_are_fail_closed,
        test_native_mesh_wrapper_and_branch_are_fail_closed,
        test_generate_mesh_call_is_nested_under_mesh_route_guard,
    ]
    for test in tests:
        test()
        print("PASS " + test.__name__)
    print("AJM006_V02_TOPOLOGY_OBSERVER_GUARDS=PASS_ALL")


if __name__ == "__main__":
    main()

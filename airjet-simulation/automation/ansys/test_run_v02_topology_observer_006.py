#!/usr/bin/env python3
"""Static guards for the AJM-006 preliminary topology observer suite."""

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


def valid_report(topology_result="DOWNSTREAM_HEALED_SINGLE_FACE"):
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
    return {
        "probe": "v02_preliminary_topology_observer",
        "status": "PASS_PRELIMINARY_TOPOLOGY_OBSERVATION",
        "engineering_capability": "PASS_PRELIMINARY_TOPOLOGY_OBSERVATION",
        "formal_006_completion": False,
        "p1_stage_gate": "NOT_RUN",
        "p1_p6_gates": "NOT_RUN",
        "diagnostic_only": True,
        "license_arguments_added": False,
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
        "observer_summary": {
            "topology_result": topology_result,
            "body_count": 2,
            "total_body_face_references": 2050,
            "role_binding_by_predecessor_face_counts": True,
            "shared_node_or_conformal_mesh": "NOT_EVALUATED_NO_MESH",
        },
        "files": artifacts,
    }


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
    report = valid_report("MIXED_OR_OTHER")
    returned = runner.validate_observer_report(
        manifest_for(report), job_state(), HEAD, PREDECESSOR_JOB_ID
    )
    assert returned["formal_006_completion"] is False
    assert returned["p1_stage_gate"] == "NOT_RUN"


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


def main():
    tests = [
        test_preflight_passes,
        test_preflight_rejects_hash_mismatch,
        test_preflight_rejects_external_artifact_contract,
        test_validate_observer_accepts_healed_observation,
        test_validate_observer_accepts_mixed_as_diagnostic_only,
        test_validate_observer_rejects_p1_overclaim,
        test_validate_observer_rejects_hash_mismatch,
        test_embedded_mechanical_script_formats_and_compiles,
        test_runner_uses_isolated_mode_safe_sibling_import,
    ]
    for test in tests:
        test()
        print("PASS " + test.__name__)
    print("AJM006_V02_TOPOLOGY_OBSERVER_GUARDS=PASS_ALL")


if __name__ == "__main__":
    main()

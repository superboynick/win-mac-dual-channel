#!/usr/bin/env python3
"""Offline validator guards for the V03 two-stage mesh runner."""

from __future__ import annotations

import copy
import math
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace


def setup_mcp_stub() -> None:
    mcp_mod = ModuleType("mcp")
    types_mod = ModuleType("mcp.types")

    class TextContent:
        def __init__(self, text: str):
            self.text = text

    class CallToolResult:
        pass

    class Implementation:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    types_mod.TextContent = TextContent
    types_mod.CallToolResult = CallToolResult
    types_mod.Implementation = Implementation
    mcp_mod.types = types_mod
    mcp_mod.ClientSession = object
    mcp_mod.StdioServerParameters = object
    client_mod = ModuleType("mcp.client")
    stdio_mod = ModuleType("mcp.client.stdio")
    stdio_mod.stdio_client = lambda *args, **kwargs: None
    sys.modules["mcp"] = mcp_mod
    sys.modules["mcp.types"] = types_mod
    sys.modules["mcp.client"] = client_mod
    sys.modules["mcp.client.stdio"] = stdio_mod


setup_mcp_stub()
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_v03_continuous_mesh_006 as runner


HEAD = "a" * 40
PROFILE_CONTRACT = "b" * 64
SCRIPT_HASH = runner.CONSUMER_SCRIPT_SHA256


def file_entry(name: str, index: int) -> dict:
    return {"relative_path": name, "size": 100 + index, "sha256": f"{index + 1:064x}"}


def valid_report_state_manifest() -> tuple[dict, dict, dict]:
    artifacts = {
        name: file_entry(name, index)
        for index, name in enumerate(sorted(runner.CONSUMER_ARTIFACTS))
    }
    report = {
        "schema_version": 1,
        "task": "AJM006_V03_PYFLUENT_WATERTIGHT_MESH_ONLY",
        "probe": "v03_pyfluent_watertight_mesh_consumer",
        "status": "PASS_PRELIMINARY_MESH_CAPABILITY",
        "engineering_capability": "PASS_PRELIMINARY_MESH_CAPABILITY",
        "mesh_result": "PASS_V03_SINGLE_REGION_972_THROAT_VOLUME_MESH",
        "claim_scope": "V03_PRELIMINARY_PYFLUENT_MESH_PILOT_ONLY",
        "formal_006_completion": False,
        "p1_stage_gate": "NOT_RUN",
        "p1_mesh_gate": "NOT_RUN",
        "p1_p6_gates": "NOT_RUN",
        "physics": "NOT_RUN",
        "boundary_conditions": "NOT_APPLIED",
        "solver_mode": "NOT_ENTERED",
        "solver_initialization": "NOT_RUN",
        "solver_iterations": 0,
        "solution": "NOT_RUN",
        "cht": "NOT_RUN",
        "fsi": "NOT_RUN",
        "exact_product_geometry": "NOT_CLAIMED",
        "visibility": "NOT_USER_OBSERVED",
        "license_arguments_added": False,
        "error": None,
        "assertions": {name: True for name in runner.CONSUMER_ASSERTIONS},
        "identity": {
            "git_head": HEAD,
            "profile_id": runner.CONSUMER_PROFILE_ID,
            "profile_contract_sha256": PROFILE_CONTRACT,
            "script_sha256": SCRIPT_HASH,
            "case_id": runner.CASE_ID,
            "predecessor_job_id": "producer-job",
        },
        "mesh_contract": {
            "product_version": "261",
            "mode": "MESHING",
            "dimension": "THREE",
            "precision": "DOUBLE",
            "processor_count": 1,
            "ui_mode": "NO_GUI_OR_GRAPHICS",
            "surface_min_size_mm": 0.05,
            "surface_max_size_mm": 0.75,
            "throat_local_size_mm": 0.075,
            "volume_max_size_mm": 0.75,
            "resolution_class": "STUDENT_COARSE_TOPOLOGY_DIAGNOSTIC_C1",
            "cad_one_zone_per": "face",
            "student_cell_limit": 1_000_000,
            "student_node_limit": 1_000_000,
        },
        "mesh_evidence": {
            "cell_count": 500_000,
            "node_count": 600_000,
            "cell_zone_count": 1,
            "throat_query_count": 972,
            "throat_zone_count": 972,
            "free_face_count": 0,
            "multi_face_count": 0,
            "min_orthogonal_quality": 0.12,
            "mesh_file": artifacts["v03_continuous_volume_mesh.msh.h5"],
        },
        "artifacts": artifacts,
    }
    report_entry = {
        "relative_path": runner.CONSUMER_REPORT,
        "size": 999,
        "sha256": "f" * 64,
        "report_json": report,
        "report_error": None,
    }
    manifest = {
        "job_id": "consumer-job",
        "phase": "PROCESS_EXITED_0",
        "files": [report_entry] + [
            copy.deepcopy(item) for item in artifacts.values()
        ],
    }
    state = {
        "job_id": "consumer-job",
        "profile_contract_sha256": PROFILE_CONTRACT,
        "predecessor_job_id": "producer-job",
    }
    return report, state, manifest


def test_consumer_report_accepts_exact_contract() -> None:
    assert runner.CONSUMER_SCRIPT_SHA256 == (
        "8e397683c7bbb534213e632f71b40e15516e94fd1abe337aae16f0a3f348db35"
    )
    report, state, manifest = valid_report_state_manifest()
    assert runner.validate_consumer_report(manifest, state, HEAD) == report


def rejects(mutator, expected: str) -> None:
    report, state, manifest = valid_report_state_manifest()
    mutator(report, state, manifest)
    try:
        runner.validate_consumer_report(manifest, state, HEAD)
    except RuntimeError as exc:
        assert expected in str(exc)
    else:
        raise AssertionError("invalid consumer report accepted")


def test_consumer_report_rejects_claim_and_truthy_assertion() -> None:
    rejects(
        lambda report, _state, _manifest: report.__setitem__("solver_iterations", 1),
        "CLAIM_BOUNDARY",
    )
    rejects(
        lambda report, _state, _manifest: report["assertions"].__setitem__(
            "volume_mesh", "true"
        ),
        "ASSERTIONS",
    )


def test_consumer_report_rejects_student_and_quality_overclaim() -> None:
    rejects(
        lambda report, _state, _manifest: report["mesh_evidence"].__setitem__(
            "node_count", 1_000_001
        ),
        "MESH_EVIDENCE",
    )
    rejects(
        lambda report, _state, _manifest: report["mesh_evidence"].__setitem__(
            "min_orthogonal_quality", math.nan
        ),
        "MESH_EVIDENCE",
    )


def test_consumer_report_rejects_missing_or_hash_drifted_artifact() -> None:
    rejects(
        lambda report, _state, _manifest: report["artifacts"].pop(
            "v03_pyfluent_transcript.txt"
        ),
        "ARTIFACT_SET",
    )
    rejects(
        lambda _report, _state, manifest: manifest["files"][1].__setitem__(
            "sha256", "0" * 64
        ),
        "ARTIFACT_INVALID",
    )


def predecessor_fixture() -> tuple[dict, dict]:
    files = [
        file_entry(name, index)
        for index, name in enumerate(runner.PREDECESSOR_ARTIFACTS)
    ]
    return {"predecessor_artifacts": copy.deepcopy(files)}, {"files": files}


def test_predecessor_state_accepts_frozen_exact_five() -> None:
    state, manifest = predecessor_fixture()
    runner.verify_predecessor_state(state, manifest)


def test_predecessor_state_rejects_missing_and_hash_drift() -> None:
    state, manifest = predecessor_fixture()
    state["predecessor_artifacts"].pop()
    try:
        runner.verify_predecessor_state(state, manifest)
    except RuntimeError as exc:
        assert "ARTIFACT_SET" in str(exc)
    else:
        raise AssertionError("missing predecessor accepted")
    state, manifest = predecessor_fixture()
    state["predecessor_artifacts"][0]["sha256"] = "0" * 64
    try:
        runner.verify_predecessor_state(state, manifest)
    except RuntimeError as exc:
        assert "FROZEN_MISMATCH" in str(exc)
    else:
        raise AssertionError("drifted predecessor accepted")


def main() -> None:
    tests = [
        value for name, value in sorted(globals().items())
        if name.startswith("test_") and callable(value)
    ]
    for test in tests:
        test()
        print("PASS", test.__name__)
    print("AJM006_V03_TWO_STAGE_RUNNER_GUARDS=PASS_ALL")


if __name__ == "__main__":
    main()

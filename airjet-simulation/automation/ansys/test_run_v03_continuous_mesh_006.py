#!/usr/bin/env python3
"""Offline validator guards for the V03 two-stage mesh runner."""

from __future__ import annotations

import asyncio
import ast
import copy
import json
import math
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
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


def valid_region_inventory() -> dict:
    return {
        "source_fields": [
            "workflow.describe_geometry.setup_type",
            "utilities.get_cell_zones",
            "utilities.get_zone_type",
            "meshing_utilities.convert_zone_ids_to_name_strings",
        ],
        "regions": [
            {
                "name": "main-flow",
                "type": "fluid",
                "classification": "MAIN_FLOW",
            }
        ],
        "main_flow_region_count": 1,
        "non_flow_region_count": 0,
        "main_flow_region_name": "main-flow",
        "approved_update_arguments": {},
    }


def valid_canonical_boundary_inventory() -> dict:
    return {
        name: {
            "role": role,
            "zone_id": 1000 + index,
            "zone_type": zone_type,
            "source_component_count": source_component_count,
            "adjacent_cell_zone_ids": [1],
        }
        for index, (name, (role, zone_type, source_component_count)) in enumerate(
            runner.CANONICAL_BOUNDARY_SPEC.items()
        )
    }


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
        "mesh_result": "PASS_V03_CONNECTED_ZONE_GRAPH_972_THROAT_VOLUME_MESH",
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
            "resolution_class": "STUDENT_COARSE_MAIN_FLOW_REGION_C5",
            "cad_import_source": "NATIVE_SCDOCX_BOUND_TO_SIGNED_PREDECESSOR",
            "cad_one_zone_per": "face",
            "wall_to_internal": False,
            "max_expected_flow_cell_zones": 1,
            "target_flow_volume_mesh_tolerance_mm3": 1.0,
            "student_cell_limit": 1_000_000,
            "student_node_limit": 1_000_000,
        },
        "mesh_evidence": {
            "cell_count": 500_000,
            "node_count": 600_000,
            "cell_zone_count": 1,
            "cell_zone_ids": [1],
            "cell_zone_types": {"1": "fluid"},
            "cell_counts_by_zone": {"1": 500_000},
            "cell_volumes_by_zone": {"1": 451.8},
            "cell_zone_graph_connected": True,
            "interior_face_zone_count": 0,
            "interior_face_records": [],
            "reached_cell_zone_ids": [1],
            "boundary_face_adjacency": {
                "100": [1], "101": [1], "102": [1], "103": [1], "104": [1]
            },
            "boundary_adjacency_ok": True,
            "post_volume_role_resolution_ok": True,
            "post_volume_inlet_zone_count": 4,
            "post_volume_outlet_zone_count": 1,
            "post_volume_throat_zone_count": 1,
            "source_boundary_face_count": 1078,
            "source_boundary_role_counts": copy.deepcopy(
                runner.BOUNDARY_ROLE_COUNTS
            ),
            "pre_canonical_role_exclusive_mapping_ok": True,
            "canonical_boundary_zone_count": 10,
            "post_volume_boundary_role_counts": copy.deepcopy(
                runner.BOUNDARY_ROLE_COUNTS
            ),
            "post_volume_boundary_coverage_count": 1078,
            "post_volume_role_exclusive_mapping_ok": True,
            "post_volume_generic_boundary_collapse": False,
            "post_volume_single_fluid_adjacency_ok": True,
            "post_volume_canonical_boundary_inventory": (
                valid_canonical_boundary_inventory()
            ),
            "throat_face_adjacency": {
                "200": {
                    "label": "THROAT_FACE_ADJACENCY",
                    "raw_none": False,
                    "values": [1],
                }
            },
            "throat_face_adjacency_ok": True,
            "anchor_zone_ids": [1],
            "anchor_occupancy_ok": True,
            "baffle_zone_count": 0,
            "embedded_baffle_zone_count": 0,
            "external_baffle_resolved": True,
            "external_baffle_count": 0,
            "unresolved_all_face_adjacency_count": 0,
            "two_fluid_non_interior_count": 0,
            "throat_occupancy_hit_count": 972,
            "throat_occupancy_miss_count": 0,
            "throat_occupancy_raw_none_count": 0,
            "throat_occupancy_zone_counts": {"1": 972},
            "throat_query_count": 972,
            "throat_occupancy_executed_query_count": 972,
            "throat_zone_count": 1,
            "expected_native_flow_volume_mm3": 451.77881884263655,
            "meshed_cell_volume_mm3": 451.8,
            "target_flow_volume_delta_mm3": 0.02118115736347259,
            "target_flow_volume_tolerance_mm3": 1.0,
            "target_flow_volume_matches_predecessor": True,
            "throat_occupancy_query_scope": "FULL_972",
            "throat_occupancy_first_miss_indices": [],
            "throat_occupancy_unique_owner_per_query": True,
            "throat_occupancy_all_hits_in_accepted_flow_zone": True,
            "actuator_gap_probe_count": 12,
            "actuator_gap_hit_count": 0,
            "actuator_gap_raw_none_count": 12,
            "actuator_gap_exclusion_evaluable": True,
            "actuator_gap_zones_excluded": True,
            "pre_update_region_inventory": valid_region_inventory(),
            "post_update_region_inventory": valid_region_inventory(),
            "region_transition": {
                "route": "REVERSED_BOUNDARY_FLUID_OBJECT",
                "main_flow_region_count": 1,
                "non_flow_region_count": 0,
                "unchanged": True,
            },
            "main_flow_region_count": 1,
            "non_flow_region_count": 0,
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
        "e4d978767bb9a37b2d66d1852b8682cd07ce7e26d7c85ee87761427f8f4cdb3e"
    )
    report, state, manifest = valid_report_state_manifest()
    assert runner.validate_consumer_report(manifest, state, HEAD) == report


def test_consumer_assertion_contract_includes_c5_hard_gates() -> None:
    expected = {
        "predecessor_identity",
        "predecessor_immutable",
        "exact_native_and_step_byte_staging",
        "fluent_v261_meshing_health",
        "watertight_native_import",
        "boundary_roles_reconstructed",
        "throat_roles_reconstructed_972",
        "boundary_semantics_preserved_1078",
        "throat_local_sizing_contract",
        "surface_mesh",
        "flow_cell_zone_inventory",
        "volume_mesh",
        "region_classification",
        "throat_occupancy_full_972",
        "actuator_gap_exclusion",
        "connected_fluid_cell_zone_graph",
        "target_flow_volume_matches_predecessor",
        "mesh_integrity",
        "student_limit_guard",
        "mesh_write_hash",
        "claim_boundaries",
    }
    assert runner.CONSUMER_ASSERTIONS == expected
    consumer = HERE / "approved" / "006" / "v03_pyfluent_watertight_mesh_consumer.py"
    tree = ast.parse(consumer.read_text(encoding="utf-8"), filename=str(consumer))
    assignments = [
        ast.literal_eval(node.value)
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "ASSERTION_NAMES" for target in node.targets)
    ]
    assert len(assignments) == 1
    assert set(assignments[0]) == expected


def test_consumer_mesh_evidence_literal_keys_match_runner_fixture() -> None:
    consumer = HERE / "approved" / "006" / "v03_pyfluent_watertight_mesh_consumer.py"
    tree = ast.parse(consumer.read_text(encoding="utf-8"), filename=str(consumer))
    observed: list[set[str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Dict):
            continue
        for target in node.targets:
            if (
                isinstance(target, ast.Subscript)
                and isinstance(target.value, ast.Name)
                and target.value.id == "result"
                and isinstance(target.slice, ast.Constant)
                and target.slice.value == "mesh_evidence"
            ):
                observed.append(
                    {
                        key.value
                        for key in node.value.keys
                        if isinstance(key, ast.Constant) and isinstance(key.value, str)
                    }
                )
    assert len(observed) == 1
    report, _state, _manifest = valid_report_state_manifest()
    assert observed[0] == set(report["mesh_evidence"])


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
    for invalid_quality in (-1.0, 0.0, 1.01):
        rejects(
            lambda report, _state, _manifest, value=invalid_quality: report[
                "mesh_evidence"
            ].__setitem__("min_orthogonal_quality", value),
            "MESH_EVIDENCE",
        )


def test_consumer_report_rejects_wrong_target_or_fake_throat_graph() -> None:
    rejects(
        lambda report, _state, _manifest: report["mesh_evidence"].__setitem__(
            "meshed_cell_volume_mm3", 13.475
        ),
        "TARGET_VOLUME_INVALID",
    )
    rejects(
        lambda report, _state, _manifest: report["mesh_evidence"][
            "throat_face_adjacency"
        ]["200"].__setitem__("values", []),
        "THROAT_GRAPH_INVALID",
    )
    rejects(
        lambda report, _state, _manifest: report["mesh_evidence"].__setitem__(
            "min_orthogonal_quality", math.nan
        ),
        "MESH_EVIDENCE",
    )


def test_consumer_report_rejects_incomplete_c7_boundary_semantics() -> None:
    rejects(
        lambda report, _state, _manifest: report["mesh_evidence"].__setitem__(
            "source_boundary_face_count", 1078.0
        ),
        "BOUNDARY_SEMANTICS_1078_INVALID",
    )
    rejects(
        lambda report, _state, _manifest: report["mesh_evidence"][
            "source_boundary_role_counts"
        ].__setitem__("HEAT_WALL", True),
        "BOUNDARY_SEMANTICS_1078_INVALID",
    )
    rejects(
        lambda report, _state, _manifest: report["mesh_evidence"].__setitem__(
            "pre_canonical_role_exclusive_mapping_ok", False
        ),
        "BOUNDARY_SEMANTICS_1078_INVALID",
    )
    rejects(
        lambda report, _state, _manifest: report["mesh_evidence"].__setitem__(
            "canonical_boundary_zone_count", 9
        ),
        "BOUNDARY_SEMANTICS_1078_INVALID",
    )
    rejects(
        lambda report, _state, _manifest: report["mesh_evidence"][
            "post_volume_boundary_role_counts"
        ].__setitem__("MEMBRANE_TOP", 11),
        "BOUNDARY_SEMANTICS_1078_INVALID",
    )
    rejects(
        lambda report, _state, _manifest: report["mesh_evidence"].__setitem__(
            "post_volume_boundary_coverage_count", 1077
        ),
        "BOUNDARY_SEMANTICS_1078_INVALID",
    )
    rejects(
        lambda report, _state, _manifest: report["mesh_evidence"].__setitem__(
            "post_volume_role_exclusive_mapping_ok", False
        ),
        "BOUNDARY_SEMANTICS_1078_INVALID",
    )
    rejects(
        lambda report, _state, _manifest: report["mesh_evidence"].__setitem__(
            "post_volume_generic_boundary_collapse", True
        ),
        "BOUNDARY_SEMANTICS_1078_INVALID",
    )
    rejects(
        lambda report, _state, _manifest: report["mesh_evidence"].__setitem__(
            "post_volume_single_fluid_adjacency_ok", False
        ),
        "BOUNDARY_SEMANTICS_1078_INVALID",
    )
    rejects(
        lambda report, _state, _manifest: report["mesh_evidence"][
            "post_volume_canonical_boundary_inventory"
        ]["ajm_heat_wall"].__setitem__(
            "zone_id",
            report["mesh_evidence"]["post_volume_canonical_boundary_inventory"][
                "ajm_outlet"
            ]["zone_id"],
        ),
        "CANONICAL_BOUNDARY_RECORD_INVALID",
    )
    rejects(
        lambda report, _state, _manifest: report["mesh_evidence"][
            "post_volume_canonical_boundary_inventory"
        ]["ajm_membrane_top"].__setitem__("zone_type", "generic"),
        "CANONICAL_BOUNDARY_RECORD_INVALID",
    )
    rejects(
        lambda report, _state, _manifest: report["mesh_evidence"][
            "post_volume_canonical_boundary_inventory"
        ]["ajm_throat_wall"].__setitem__("adjacent_cell_zone_ids", []),
        "CANONICAL_BOUNDARY_RECORD_INVALID",
    )


def test_consumer_report_rejects_c5_gate_and_region_passthrough_drift() -> None:
    rejects(
        lambda report, _state, _manifest: report["mesh_evidence"].__setitem__(
            "throat_occupancy_executed_query_count", 12
        ),
        "TOPOLOGY_INVALID",
    )
    rejects(
        lambda report, _state, _manifest: report["mesh_evidence"].__setitem__(
            "anchor_zone_ids", []
        ),
        "TOPOLOGY_INVALID",
    )
    rejects(
        lambda report, _state, _manifest: report["mesh_evidence"].__setitem__(
            "actuator_gap_exclusion_evaluable", False
        ),
        "TOPOLOGY_INVALID",
    )
    rejects(
        lambda report, _state, _manifest: report["mesh_evidence"].__setitem__(
            "throat_zone_count", 972
        ),
        "TOPOLOGY_INVALID",
    )
    rejects(
        lambda report, _state, _manifest: report["mesh_evidence"].__setitem__(
            "pre_update_region_inventory",
            {
                "source_fields": [],
                "regions": [],
                "main_flow_region_count": 1,
                "non_flow_region_count": 11,
                "main_flow_region_name": "",
                "approved_update_arguments": {},
                "passthrough": True,
            },
        ),
        "REGION_INVENTORY_SCHEMA_INVALID",
    )
    rejects(
        lambda report, _state, _manifest: report["mesh_evidence"][
            "pre_update_region_inventory"
        ].__setitem__("source_fields", ["untrusted_names/untrusted_types"]),
        "REGION_INVENTORY_INVALID",
    )
    rejects(
        lambda report, _state, _manifest: report["mesh_evidence"][
            "pre_update_region_inventory"
        ]["regions"].append(
            {"name": "second-flow", "type": "fluid", "classification": "MAIN_FLOW"}
        ),
        "REGION_INVENTORY_INVALID",
    )
    for invalid_type in ("dead", "void", "excluded"):
        rejects(
            lambda report, _state, _manifest, value=invalid_type: report[
                "mesh_evidence"
            ]["pre_update_region_inventory"]["regions"][0].__setitem__(
                "type", value
            ),
            "REGION_RECORD_INVALID",
        )
    rejects(
        lambda report, _state, _manifest: report["mesh_evidence"][
            "pre_update_region_inventory"
        ].__setitem__("non_flow_region_count", 11),
        "REGION_CLASSIFICATION_INVALID",
    )
    rejects(
        lambda report, _state, _manifest: report["mesh_evidence"][
            "region_transition"
        ].__setitem__("route", "SELF_REPORTED_PASSTHROUGH"),
        "TOPOLOGY_INVALID",
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


def test_predecessor_state_accepts_frozen_exact_seven() -> None:
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
    state, manifest = predecessor_fixture()
    state["predecessor_artifacts"].append(
        copy.deepcopy(state["predecessor_artifacts"][0])
    )
    try:
        runner.verify_predecessor_state(state, manifest)
    except RuntimeError as exc:
        assert "PREDECESSOR_ARTIFACTS" in str(exc)
    else:
        raise AssertionError("duplicate predecessor accepted")
    for native_name in (
        "product_continuous_fluid.scdocx",
        "v03_native_reopen.json",
    ):
        state, manifest = predecessor_fixture()
        native_index = runner.PREDECESSOR_ARTIFACTS.index(native_name)
        state["predecessor_artifacts"][native_index]["sha256"] = "0" * 64
        try:
            runner.verify_predecessor_state(state, manifest)
        except RuntimeError as exc:
            assert "FROZEN_MISMATCH" in str(exc)
        else:
            raise AssertionError("drifted native predecessor accepted: " + native_name)


def running_state(job_id: str, engine: str, profile_id: str, script_sha: str) -> dict:
    return {
        "job_id": job_id,
        "case_id": runner.CASE_ID,
        "profile_id": profile_id,
        "engine": engine,
        "script_sha256": script_sha,
        "profile_contract_sha256": PROFILE_CONTRACT,
        "profile_dependency_manifest_sha256": (
            "d" * 64 if engine == "spaceclaim" else None
        ),
        "profile_dependency_artifacts": [],
        "git_head": HEAD,
        "output_root_id": "p1_cad_006",
        "job_directory": "D:/AirJet_P1/{}".format(job_id),
        "license_arguments_added": False,
        "predecessor_job_id": None,
        "predecessor_artifacts": [],
        "phase": "RUNNING",
    }


def test_submit_identity_and_contract_hashes_fail_closed() -> None:
    contracts = {
        runner.stage1.PROFILE_ID: PROFILE_CONTRACT,
        runner.CONSUMER_PROFILE_ID: "c" * 64,
    }
    assert runner.validate_profile_contracts(contracts) == contracts
    inventory_contracts = dict(contracts)
    inventory_contracts.update(
        {"unrelated-profile-%02d" % index: "%x" % index * 64 for index in range(1, 19)}
    )
    assert runner.validate_profile_contracts(inventory_contracts) == contracts
    for invalid in (
        {},
        {runner.stage1.PROFILE_ID: None},
        dict(contracts, **{runner.CONSUMER_PROFILE_ID: "0" * 64}),
    ):
        try:
            runner.validate_profile_contracts(invalid)
        except RuntimeError as exc:
            assert "PROFILE_CONTRACT_HASHES_INVALID" in str(exc)
        else:
            raise AssertionError("invalid profile contract hashes accepted")

    first = running_state(
        "stage1-job", "spaceclaim", runner.stage1.PROFILE_ID,
        runner.stage1.PROFILE_SCRIPT_SHA256,
    )
    runner.validate_stage1_submit_identity(first, HEAD, PROFILE_CONTRACT)
    for name, value in (
        ("job_id", ""),
        ("case_id", "wrong-case"),
        ("profile_id", "wrong-profile"),
        ("phase", "PROCESS_EXITED_0"),
        ("engine", "pyfluent"),
        ("git_head", "0" * 40),
        ("output_root_id", "wrong-root"),
        ("job_directory", ""),
        ("script_sha256", "0" * 64),
        ("profile_contract_sha256", "0" * 64),
        ("profile_dependency_manifest_sha256", None),
        ("license_arguments_added", True),
        ("predecessor_job_id", "unexpected-job"),
        ("predecessor_artifacts", [{"relative_path": "unexpected"}]),
    ):
        changed = copy.deepcopy(first)
        changed[name] = value
        try:
            runner.validate_stage1_submit_identity(changed, HEAD, PROFILE_CONTRACT)
        except RuntimeError as exc:
            assert "STAGE1_SUBMIT_IDENTITY_MISMATCH" in str(exc)
            if name == "script_sha256":
                assert "SCRIPT_SHA256" in str(exc)
        else:
            raise AssertionError(f"stage1 identity drift accepted: {name}")

    second = running_state(
        "stage2-job", "pyfluent", runner.CONSUMER_PROFILE_ID,
        runner.CONSUMER_SCRIPT_SHA256,
    )
    second["profile_contract_sha256"] = "c" * 64
    second["predecessor_job_id"] = "stage1-job"
    runner.validate_stage2_submit_identity(second, HEAD, "c" * 64, "stage1-job")
    for name, value in (
        ("job_id", ""),
        ("case_id", "wrong-case"),
        ("profile_id", "wrong-profile"),
        ("phase", "PROCESS_EXITED_0"),
        ("engine", "spaceclaim"),
        ("git_head", "0" * 40),
        ("output_root_id", "wrong-root"),
        ("job_directory", ""),
        ("script_sha256", "0" * 64),
        ("profile_contract_sha256", "0" * 64),
        ("license_arguments_added", True),
        ("predecessor_job_id", "wrong-job"),
        ("profile_dependency_manifest_sha256", "0" * 64),
        ("profile_dependency_artifacts", [{"relative_path": "unexpected"}]),
    ):
        changed = copy.deepcopy(second)
        changed[name] = value
        try:
            runner.validate_stage2_submit_identity(
                changed, HEAD, "c" * 64, "stage1-job"
            )
        except RuntimeError as exc:
            assert "STAGE2_SUBMIT_IDENTITY_MISMATCH" in str(exc)
            if name == "script_sha256":
                assert "SCRIPT_SHA256" in str(exc)
        else:
            raise AssertionError(f"stage2 identity drift accepted: {name}")


def test_preflight_block_has_zero_stdio_submit_and_child_calls() -> None:
    counts = {"stdio": 0, "submit": 0, "child": 0}
    old_output_root = runner.stage1.OUTPUT_ROOT
    old_result_path = runner.RESULT_PATH
    old_preflight = runner.stage1.preflight
    old_stdio = runner.stdio_client
    old_parameters = runner.StdioServerParameters
    old_call_json = runner.stage1.call_json
    with TemporaryDirectory() as root:
        temp_root = Path(root)

        def blocked_preflight() -> dict:
            return {
                "preflight_ok": False,
                "preflight_errors": ["TEST_BLOCK"],
            }

        def stdio_spy(*_args, **_kwargs):
            counts["stdio"] += 1
            raise AssertionError("stdio reached after blocked preflight")

        def child_spy(*_args, **_kwargs):
            counts["child"] += 1
            raise AssertionError("child parameters built after blocked preflight")

        async def call_spy(_session, name, *_args, **_kwargs):
            if name == "submit_job":
                counts["submit"] += 1
            raise AssertionError("MCP call reached after blocked preflight")

        try:
            runner.stage1.OUTPUT_ROOT = temp_root
            runner.RESULT_PATH = temp_root / "result.json"
            runner.stage1.preflight = blocked_preflight
            runner.stdio_client = stdio_spy
            runner.StdioServerParameters = child_spy
            runner.stage1.call_json = call_spy
            assert asyncio.run(runner.run_suite()) == 2
            saved = json.loads(runner.RESULT_PATH.read_text(encoding="utf-8"))
        finally:
            runner.stage1.OUTPUT_ROOT = old_output_root
            runner.RESULT_PATH = old_result_path
            runner.stage1.preflight = old_preflight
            runner.stdio_client = old_stdio
            runner.StdioServerParameters = old_parameters
            runner.stage1.call_json = old_call_json
    assert counts == {"stdio": 0, "submit": 0, "child": 0}
    assert saved["stage1"]["capability_status"] == "NOT_RUN"
    assert saved["stage2"]["capability_status"] == "NOT_RUN"


def test_stage1_post_submit_failure_persists_partial_and_cancels() -> None:
    calls = []
    old_result_path = runner.RESULT_PATH
    old_call_json = runner.stage1.call_json
    with TemporaryDirectory() as root:
        runner.RESULT_PATH = Path(root) / "partial.json"

        async def fake_call(_session, name, arguments=None, **_kwargs):
            calls.append((name, arguments))
            if name == "submit_job":
                state = running_state(
                    "stage1-job", "wrong-engine", runner.stage1.PROFILE_ID,
                    runner.stage1.PROFILE_SCRIPT_SHA256,
                )
                return state
            if name == "cancel_job":
                partial = json.loads(runner.RESULT_PATH.read_text(encoding="utf-8"))
                assert partial["stage1"]["submitted"] is True
                assert partial["stage1"]["capability_status"] == "FAIL"
                return {"job_id": "stage1-job", "phase": "CANCELLED"}
            raise AssertionError("unexpected MCP call {}".format(name))

        try:
            runner.stage1.call_json = fake_call
            result = runner.new_result()
            try:
                asyncio.run(runner.run_submitted_stages(
                    object(), result, HEAD,
                    {runner.stage1.PROFILE_ID: PROFILE_CONTRACT},
                ))
            except RuntimeError as exc:
                assert "STAGE1_SUBMIT_IDENTITY_MISMATCH" in str(exc)
            else:
                raise AssertionError("stage1 identity failure accepted")
            saved = json.loads(runner.RESULT_PATH.read_text(encoding="utf-8"))
        finally:
            runner.RESULT_PATH = old_result_path
            runner.stage1.call_json = old_call_json
    assert [name for name, _ in calls] == ["submit_job", "cancel_job"]
    assert saved["stage1"]["submitted"] is True
    assert saved["stage1"]["capability_status"] == "FAIL"
    assert saved["stage1"]["reached_terminal"] is True
    assert saved["stage1"]["cancellation"]["confirmed_terminal"] is True
    assert saved["stage2"]["submitted"] is False
    assert saved["stage2"]["capability_status"] == "NOT_RUN"


def test_stage2_post_submit_failure_preserves_stage1_and_cancels() -> None:
    calls = []
    old_result_path = runner.RESULT_PATH
    old_call_json = runner.stage1.call_json
    old_wait = runner.wait_for_job
    old_dependency = runner.stage1.validate_dependency_artifacts
    old_report = runner.stage1.validate_producer_report
    with TemporaryDirectory() as root:
        runner.RESULT_PATH = Path(root) / "partial.json"
        first_running = running_state(
            "stage1-job", "spaceclaim", runner.stage1.PROFILE_ID,
            runner.stage1.PROFILE_SCRIPT_SHA256,
        )
        first_running["profile_contract_sha256"] = PROFILE_CONTRACT
        first_manifest = {
            "job_id": "stage1-job",
            "phase": "PROCESS_EXITED_0",
            "files": [],
        }

        async def fake_wait(_session, state, _timeout, stage_result, suite_result):
            terminal = dict(state)
            terminal["phase"] = "PROCESS_EXITED_0"
            stage_result["job_state"] = terminal
            stage_result["reached_terminal"] = True
            stage_result["cancellation_required"] = False
            runner.persist_result(suite_result)
            return terminal

        async def fake_call(_session, name, arguments=None, **_kwargs):
            calls.append((name, arguments))
            if name == "submit_job" and arguments["profile_id"] == runner.stage1.PROFILE_ID:
                return copy.deepcopy(first_running)
            if name == "artifact_manifest":
                return copy.deepcopy(first_manifest)
            if name == "submit_job":
                second = running_state(
                    "stage2-job", "wrong-engine", runner.CONSUMER_PROFILE_ID,
                    runner.CONSUMER_SCRIPT_SHA256,
                )
                second["predecessor_job_id"] = "stage1-job"
                return second
            if name == "cancel_job":
                partial = json.loads(runner.RESULT_PATH.read_text(encoding="utf-8"))
                assert partial["stage2"]["submitted"] is True
                assert partial["stage2"]["capability_status"] == "FAIL"
                return {"job_id": "stage2-job", "phase": "CANCELLED"}
            raise AssertionError("unexpected MCP call {}".format(name))

        try:
            runner.stage1.call_json = fake_call
            runner.wait_for_job = fake_wait
            runner.stage1.validate_dependency_artifacts = lambda _value: None
            runner.stage1.validate_producer_report = (
                lambda _manifest, _state, _head: {"status": "PASS"}
            )
            result = runner.new_result()
            try:
                asyncio.run(runner.run_submitted_stages(
                    object(), result, HEAD,
                    {
                        runner.stage1.PROFILE_ID: PROFILE_CONTRACT,
                        runner.CONSUMER_PROFILE_ID: PROFILE_CONTRACT,
                    },
                ))
            except RuntimeError as exc:
                assert "STAGE2_SUBMIT_IDENTITY_MISMATCH" in str(exc)
            else:
                raise AssertionError("stage2 identity failure accepted")
            saved = json.loads(runner.RESULT_PATH.read_text(encoding="utf-8"))
        finally:
            runner.RESULT_PATH = old_result_path
            runner.stage1.call_json = old_call_json
            runner.wait_for_job = old_wait
            runner.stage1.validate_dependency_artifacts = old_dependency
            runner.stage1.validate_producer_report = old_report
    assert [name for name, _ in calls] == [
        "submit_job", "artifact_manifest", "submit_job", "cancel_job"
    ]
    assert saved["stage1"]["capability_status"] == "PASS"
    assert saved["stage1"]["reached_terminal"] is True
    assert saved["stage2"]["submitted"] is True
    assert saved["stage2"]["capability_status"] == "FAIL"
    assert saved["stage2"]["reached_terminal"] is True
    assert saved["stage2"]["cancellation"]["confirmed_terminal"] is True


def test_reached_terminal_malformed_manifest_is_fail_not_not_run() -> None:
    old_result_path = runner.RESULT_PATH
    old_call_json = runner.stage1.call_json
    old_wait = runner.wait_for_job
    old_dependency = runner.stage1.validate_dependency_artifacts
    with TemporaryDirectory() as root:
        runner.RESULT_PATH = Path(root) / "partial.json"
        first_running = running_state(
            "stage1-job", "spaceclaim", runner.stage1.PROFILE_ID,
            runner.stage1.PROFILE_SCRIPT_SHA256,
        )

        async def fake_wait(_session, state, _timeout, stage_result, suite_result):
            terminal = dict(state)
            terminal["phase"] = "PROCESS_EXITED_0"
            stage_result["job_state"] = terminal
            stage_result["reached_terminal"] = True
            stage_result["cancellation_required"] = False
            runner.persist_result(suite_result)
            return terminal

        async def fake_call(_session, name, arguments=None, **_kwargs):
            if name == "submit_job":
                return copy.deepcopy(first_running)
            if name == "artifact_manifest":
                return {"job_id": "stage1-job", "phase": "MALFORMED"}
            raise AssertionError("cancel must not run after terminal state")

        try:
            runner.stage1.call_json = fake_call
            runner.wait_for_job = fake_wait
            runner.stage1.validate_dependency_artifacts = lambda _value: None
            result = runner.new_result()
            try:
                asyncio.run(runner.run_submitted_stages(
                    object(), result, HEAD,
                    {runner.stage1.PROFILE_ID: PROFILE_CONTRACT},
                ))
            except RuntimeError as exc:
                assert "STAGE1_NOT_PROCESS_EXITED_0" in str(exc)
            else:
                raise AssertionError("malformed reached manifest accepted")
            saved = json.loads(runner.RESULT_PATH.read_text(encoding="utf-8"))
        finally:
            runner.RESULT_PATH = old_result_path
            runner.stage1.call_json = old_call_json
            runner.wait_for_job = old_wait
            runner.stage1.validate_dependency_artifacts = old_dependency
    assert saved["stage1"]["submitted"] is True
    assert saved["stage1"]["reached_terminal"] is True
    assert saved["stage1"]["capability_status"] == "FAIL"
    assert saved["stage1"]["cancellation"] == {
        "attempted": False,
        "confirmed_terminal": True,
        "terminal_phase": "PROCESS_EXITED_0",
    }
    assert saved["stage2"]["capability_status"] == "NOT_RUN"


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

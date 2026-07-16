#!/usr/bin/env python3
"""Static fail-closed guards for the V03 PyFluent mesh-only consumer."""

from __future__ import annotations

import ast
import copy
from pathlib import Path
import re
from typing import Any


HERE = Path(__file__).resolve().parent
SOURCE_PATH = HERE / "approved" / "006" / "v03_pyfluent_watertight_mesh_consumer.py"
SOURCE = SOURCE_PATH.read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)


def literal_assignments() -> dict:
    result = {}
    for node in TREE.body:
        if (
            isinstance(node, (ast.Assign, ast.AnnAssign))
            and ((isinstance(node, ast.Assign) and len(node.targets) == 1)
                 or isinstance(node, ast.AnnAssign))
        ):
            target = node.targets[0] if isinstance(node, ast.Assign) else node.target
            value = node.value
            if isinstance(target, ast.Name):
                try:
                    result[target.id] = ast.literal_eval(value)
                except (ValueError, TypeError):
                    pass
    return result


def test_exact_profile_and_assertion_contract() -> None:
    values = literal_assignments()
    assert values["PROFILE_ID"] == "ajm006-pyfluent-v03-continuous-mesh-pilot-v1"
    assert values["PREDECESSOR_PROFILE_ID"] == (
        "ajm006-spaceclaim-v03-continuous-throat-pilot-v1"
    )
    assert values["PREDECESSOR_ARTIFACTS"] == {
        "v03_continuous_fluid_producer.json",
        "product_continuous_fluid.step",
        "v03_step_reimport.json",
        "v03_throat_inventory.json",
        "v03_source_chain.json",
    }
    assert len(values["PRODUCER_ASSERTIONS"]) == 17
    assertions = values["ASSERTION_NAMES"]
    assert len(assertions) == 20 and len(set(assertions)) == 20
    assert values["STUDENT_ENTITY_LIMIT"] == 1_000_000
    assert values["THROAT_COUNT"] == 972
    assert values["SURFACE_MIN_SIZE_MM"] == 0.05
    assert values["SURFACE_MAX_SIZE_MM"] == 0.75
    assert values["THROAT_LOCAL_SIZE_MM"] == 0.075
    assert values["VOLUME_MAX_SIZE_MM"] == 0.75


def test_launch_is_v261_mesh_only_and_single_process() -> None:
    for required in (
        "product_version=FluentVersion.v261",
        "mode=FluentMode.MESHING",
        "precision=Precision.DOUBLE",
        "dimension=Dimension.THREE",
        "processor_count=1",
        "start_timeout=60",
        "ui_mode=UIMode.NO_GUI_OR_GRAPHICS",
        "cleanup_on_exit=True",
        "start_watchdog=False",
        "start_transcript=True",
        "fluent_path=str(FLUENT_EXE)",
        "session.watertight()",
    ):
        assert required in SOURCE
    for forbidden in (
        "additional_arguments=",
        "license_server",
        "switch_to_solver",
        "solver_session",
        ".solution.",
        ".initialize",
        ".iterate",
    ):
        assert forbidden not in SOURCE


def test_exact_byte_predecessor_and_role_reconstruction() -> None:
    for required in (
        'PREDECESSOR_DIR / "predecessor-manifest.json"',
        "PREDECESSOR_TREE_NOT_EXACT",
        "PREDECESSOR_FILE_HASH_MISMATCH",
        "PREDECESSOR_ASSERTIONS_NOT_EXACT_PASS",
        "STAGED_STEP_NOT_BYTE_IDENTICAL",
        "get_face_zones(",
        "convert_zone_ids_to_name_strings(",
        "convert_zone_name_strings_to_ids(",
        "THROAT_CENTER_SET_NOT_972_UNIQUE",
        "RECONSTRUCTED_BOUNDARY_ZONE_ROLE_CONFLICT",
        "raw_zone_ids = meshing_utilities.get_face_zones(",
        "zone_ids = list(raw_zone_ids)",
        '"boundary_zone_queries_completed"',
    ):
        assert required in SOURCE
    assert "type(zone_ids) is not list" not in SOURCE
    assert "type(zone_ids[0]) is not int" not in SOURCE


def test_official_v261_watertight_calls_are_pinned() -> None:
    for required in (
        "workflow.import_geometry.file_name",
        'workflow.import_geometry.length_unit = "mm"',
        'workflow.import_geometry.cad_import_options.one_zone_per = "face"',
        'imported_face_zone_ids = list(utilities.get_face_zones(filter="*"))',
        '"import_face_zone_inventory_completed"',
        "local.add_child_and_update(",
        '"boi_face_zone_list": throat_zone_names',
        '"boi_size": THROAT_LOCAL_SIZE_MM',
        "workflow.create_surface_mesh",
        "surface.cfd_surface_mesh_controls.min_size = SURFACE_MIN_SIZE_MM",
        "surface.cfd_surface_mesh_controls.max_size = SURFACE_MAX_SIZE_MM",
        "workflow.describe_geometry.update_child_tasks(setup_type_changed=False)",
        "workflow.describe_geometry.update_child_tasks(setup_type_changed=True)",
        '"The geometry consists of both fluid and solid regions and/or voids"',
        "workflow.describe_geometry.capping_required = False",
        "workflow.describe_geometry.wall_to_internal = False",
        "workflow.describe_geometry.arguments()",
        '"describe_geometry_pre_execute_state"',
        "workflow.update_boundaries.boundary_zone_list",
        "workflow.update_boundaries.boundary_zone_type_list",
        "workflow.update_boundaries.old_boundary_zone_list",
        "workflow.update_boundaries.old_boundary_zone_type_list",
        '"boundary_zone_types_updated"',
        "workflow.create_regions.number_of_flow_volumes = 1",
        "workflow.create_regions.arguments()",
        '"create_regions_pre_execute_state"',
        "workflow.create_regions()",
        "workflow.update_regions.arguments()",
        '"update_regions_pre_execute_state"',
        "state=json_safe_trace_value(update_regions_pre_state)",
        "workflow.update_regions()",
        "workflow.create_volume_mesh_wtm",
        'volume_mesh.volume_fill = "poly-hexcore"',
        "volume_mesh.volume_fill_controls.hex_max_cell_length = VOLUME_MAX_SIZE_MM",
    ):
        assert required in SOURCE
    for forbidden in (
        "workflow.update_boundaries.boundary_label_list",
        "workflow.update_boundaries.boundary_label_type_list",
        "workflow.update_boundaries.old_boundary_label_list",
        "workflow.update_boundaries.old_boundary_label_type_list",
    ):
        assert forbidden not in SOURCE


def test_update_regions_is_explicit_fail_closed_and_ordered() -> None:
    boundary_guard = SOURCE.index("BOUNDARY_ZONE_TYPES_NOT_4_VELOCITY_1_PRESSURE")
    create_state = SOURCE.index("workflow.create_regions.arguments()")
    create_trace = SOURCE.index('"create_regions_pre_execute_state"')
    create_execute = SOURCE.index("workflow.create_regions()", create_state + 1)
    state_read = SOURCE.index("workflow.update_regions.arguments()")
    state_trace = SOURCE.index('"update_regions_pre_execute_state"')
    approved_trace = SOURCE.index('"update_regions_approved_arguments_frozen"')
    region_execute = SOURCE.index("workflow.update_regions()", state_read + 1)
    post_state = SOURCE.index(
        "update_regions_post_state = workflow.update_regions.arguments()"
    )
    transition = SOURCE.index("region_transition = validate_region_transition(")
    volume_mesh = SOURCE.index("workflow.create_volume_mesh_wtm")
    assert (
        boundary_guard
        < create_state
        < create_trace
        < create_execute
        < state_read
        < state_trace
        < approved_trace
        < region_execute
        < post_state
        < transition
        < volume_mesh
    )
    assert SOURCE.count("workflow.create_regions.arguments()") == 1
    assert SOURCE.count("workflow.create_regions()") == 1
    assert SOURCE.count("workflow.update_regions.arguments()") == 3
    assert SOURCE.count("workflow.update_regions()") == 1
    explicit_window = SOURCE[state_read:region_execute]
    for required in (
        "pre_update_region_inventory = parse_region_inventory(",
        "workflow.update_regions.old_region_name_list =",
        "workflow.update_regions.old_region_type_list =",
        "workflow.update_regions.region_name_list =",
        "workflow.update_regions.region_type_list =",
        "APPROVED_UPDATE_REGION_ARGUMENTS_NOT_EXACT",
    ):
        assert required in explicit_window
    for forbidden in ("workflow.update_regions.set_state(",):
        assert forbidden not in explicit_window


def load_contract_helpers() -> dict[str, Any]:
    helper_names = {
        "validate_full_throat_occupancy",
        "validate_actuator_gap_exclusion",
        "parse_region_inventory",
        "validate_region_transition",
        "parse_mesh_size",
    }
    nodes = [
        node
        for node in TREE.body
        if isinstance(node, ast.FunctionDef) and node.name in helper_names
    ]
    assert {node.name for node in nodes} == helper_names
    namespace = {
        "Any": Any,
        "THROAT_COUNT": 972,
        "ACTUATOR_GAP_PROBE_COUNT": 12,
        "REGION_INVENTORY_FIELD_PAIRS": (
            ("region_current_list", "region_current_type_list"),
            ("region_name_list", "region_type_list"),
            ("old_region_name_list", "old_region_type_list"),
            ("region_internals", "region_internal_types"),
        ),
        "NON_FLOW_REGION_TYPES": {"dead", "void", "excluded"},
        "re": re,
    }
    module = ast.Module(body=nodes, type_ignores=[])
    exec(
        compile(ast.fix_missing_locations(module), str(SOURCE_PATH), "exec"),
        namespace,
    )
    return namespace


def expect_runtime_error(function, *args, marker: str) -> None:
    try:
        function(*args)
    except RuntimeError as exc:
        assert marker in str(exc)
    else:
        raise AssertionError(f"expected rejection: {marker}")


def test_mesh_size_parser_accepts_frozen_v261_summary() -> None:
    parse = load_contract_helpers()["parse_mesh_size"]
    frozen = """number of interior nodes = 174926
number of interior edges = 8475
number of interior faces = 224572
number of interior cells = 35108
number of boundary nodes = 67213
number of boundary edges = 30196
number of boundary faces = 14501
"""
    assert parse(frozen) == (35108, 239073, 242139, 1)
    expect_runtime_error(
        parse,
        frozen.replace("number of boundary faces = 14501\n", ""),
        marker="MESH_STATS_V261_SUMMARY_INCOMPLETE_OR_DUPLICATE",
    )
    expect_runtime_error(
        parse,
        frozen + "number of interior cells = 35108\n",
        marker="MESH_STATS_V261_SUMMARY_INCOMPLETE_OR_DUPLICATE",
    )


def test_full_972_occupancy_pure_contract() -> None:
    validate = load_contract_helpers()["validate_full_throat_occupancy"]
    records = [
        {"query_index": index, "raw_none": False, "zone_ids": [41]}
        for index in range(972)
    ]
    observed = validate(records, [41])
    assert observed == {
        "occupancy_mode": "FULL_972",
        "executed_queries": 972,
        "hit_count": 972,
        "miss_count": 0,
        "raw_none_count": 0,
        "first_miss_indices": [],
        "accepted_flow_cell_zone_id": 41,
        "owner_counts": {"41": 972},
        "unique_owner_per_query": True,
        "all_hits_belong_to_the_single_accepted_flow_cell_zone": True,
    }
    expect_runtime_error(
        validate, records[:12], [41], marker="QUERY_COUNT_NOT_972"
    )
    duplicate = copy.deepcopy(records)
    duplicate[1]["query_index"] = 0
    expect_runtime_error(
        validate, duplicate, [41], marker="QUERY_INDICES_NOT_EXACT"
    )
    wrong_owner = copy.deepcopy(records)
    wrong_owner[300]["zone_ids"] = [42]
    expect_runtime_error(
        validate, wrong_owner, [41], marker="NOT_FULL_SINGLE_OWNER"
    )
    multi_owner = copy.deepcopy(records)
    multi_owner[300]["zone_ids"] = [41, 42]
    expect_runtime_error(
        validate, multi_owner, [41], marker="NOT_FULL_SINGLE_OWNER"
    )
    raw_none = copy.deepcopy(records)
    raw_none[300] = {"query_index": 300, "raw_none": True, "zone_ids": []}
    expect_runtime_error(
        validate, raw_none, [41], marker="NOT_FULL_SINGLE_OWNER"
    )
    truthy = copy.deepcopy(records)
    truthy[0]["raw_none"] = 1
    expect_runtime_error(
        validate, truthy, [41], marker="RAW_NONE_NOT_BOOLEAN"
    )
    expect_runtime_error(
        validate, records, [41, 42], marker="ACCEPTED_FLOW_ZONE_NOT_UNIQUE"
    )


def test_actuator_gap_exclusion_pure_contract() -> None:
    validate = load_contract_helpers()["validate_actuator_gap_exclusion"]
    records = [
        {"query_index": index, "raw_none": True, "zone_ids": []}
        for index in range(12)
    ]
    assert validate(records) == {
        "actuator_gap_probe_count": 12,
        "actuator_gap_hit_count": 0,
        "actuator_gap_raw_none_count": 12,
        "actuator_gap_zones_excluded": True,
    }
    hit = copy.deepcopy(records)
    hit[3] = {"query_index": 3, "raw_none": False, "zone_ids": [41]}
    expect_runtime_error(validate, hit, marker="ZONES_NOT_EXCLUDED")
    empty_not_none = copy.deepcopy(records)
    empty_not_none[3]["raw_none"] = False
    expect_runtime_error(validate, empty_not_none, marker="ZONES_NOT_EXCLUDED")
    duplicate = copy.deepcopy(records)
    duplicate[3]["query_index"] = 2
    expect_runtime_error(validate, duplicate, marker="PROBE_INDICES_NOT_EXACT")


def test_actuator_gap_failure_stays_truthful_and_does_not_block_mesh_write() -> None:
    for required in (
        'actuator_gap_exclusion_evaluable = "error" not in actuator_gap_exclusion',
        'actuator_gap_exclusion.get("actuator_gap_zones_excluded") is True',
        'result["assertions"]["actuator_gap_exclusion"] = (',
    ):
        assert required in SOURCE
    for forbidden in (
        "actuator_gap_exclusion_evaluable = True",
        "actuator_gap_zones_excluded = True",
        'and result["assertions"]["actuator_gap_exclusion"]',
        'and actuator_gap_exclusion["actuator_gap_zones_excluded"]',
    ):
        assert forbidden not in SOURCE
    assert SOURCE.index("session.tui.file.write_mesh(str(MESH_PATH))") < SOURCE.index(
        'if not all(result["assertions"].values()):'
    )


def test_throat_occupancy_failure_stays_truthful_and_does_not_block_mesh_write() -> None:
    for required in (
        'throat_occupancy_evaluable = "error" not in occupancy_contract',
        'occupancy_contract.get("executed_queries") == THROAT_COUNT',
        'occupancy_contract.get("hit_count") == THROAT_COUNT',
        'result["assertions"]["throat_occupancy_full_972"] = (',
    ):
        assert required in SOURCE
    for forbidden in (
        'result["assertions"]["throat_occupancy_full_972"] = True',
        'and result["assertions"]["throat_occupancy_full_972"]',
        'and occupancy_contract[\n            "all_hits_belong_to_the_single_accepted_flow_cell_zone"\n        ]',
    ):
        assert forbidden not in SOURCE
    assert SOURCE.index("session.tui.file.write_mesh(str(MESH_PATH))") < SOURCE.index(
        'if not all(result["assertions"].values()):'
    )


def test_region_inventory_and_transition_pure_contract() -> None:
    helpers = load_contract_helpers()
    parse = helpers["parse_region_inventory"]
    transition = helpers["validate_region_transition"]
    names = ["main-flow"] + [f"actuator-pocket-{index:02d}" for index in range(11)]
    types = ["fluid"] + ["dead"] * 11
    state = {
        "region_current_list": names,
        "region_current_type_list": types,
        "region_name_list": list(names),
        "region_type_list": list(types),
    }
    pre = parse(state, "PRE_UPDATE")
    post = parse(copy.deepcopy(state), "POST_UPDATE")
    assert pre["main_flow_region_count"] == 1
    assert pre["non_flow_region_count"] == 11
    assert transition(pre, post) == {
        "main_flow_region_count": 1,
        "non_flow_region_count": 11,
        "region_names_types_preserved": True,
        "void_to_fluid_conversion": False,
        "region_merge_or_omission": False,
    }
    expect_runtime_error(
        parse, {}, "PRE_UPDATE", marker="INVENTORY_UNRESOLVED"
    )
    all_fluid = copy.deepcopy(state)
    all_fluid["region_current_type_list"] = ["fluid"] * 12
    all_fluid["region_type_list"] = ["fluid"] * 12
    expect_runtime_error(
        parse, all_fluid, "PRE_UPDATE", marker="NOT_1_FLOW_11_NON_FLOW"
    )
    conflicting = copy.deepcopy(state)
    conflicting["region_type_list"][1] = "fluid"
    expect_runtime_error(
        parse, conflicting, "PRE_UPDATE", marker="INVENTORY_CONFLICT"
    )
    renamed_state = copy.deepcopy(state)
    renamed_state["region_current_list"][1] = "silently-renamed"
    renamed_state["region_name_list"][1] = "silently-renamed"
    renamed = parse(renamed_state, "POST_UPDATE")
    expect_runtime_error(
        transition,
        pre,
        renamed,
        marker="RENAMED_RECLASSIFIED_OR_MERGED",
    )
def test_json_safe_trace_helper_preserves_nested_input() -> None:
    helper_node = next(
        node for node in TREE.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "json_safe_trace_value"
    )
    helper_module = ast.Module(body=[helper_node], type_ignores=[])
    namespace = {"Any": object}
    exec(compile(ast.fix_missing_locations(helper_module), str(SOURCE_PATH), "exec"), namespace)
    helper = namespace["json_safe_trace_value"]
    original = {"regions": [("live", None), [1, True]], "unknown": object()}
    before = copy.deepcopy(original)
    observed = helper(original)
    assert original["regions"] == before["regions"]
    assert observed["regions"] == [["live", None], [1, True]]
    assert observed["unknown"]["python_type"] == "object"
    assert isinstance(observed["unknown"]["repr"], str)


def test_prelaunch_trace_and_predecessor_identity_are_pinned() -> None:
    for required in (
        'PRELAUNCH_TRACE_PATH = JOB_DIR / "v03_pyfluent_prelaunch_trace.jsonl"',
        'LAUNCH_STACK_PATH = JOB_DIR / "v03_pyfluent_launch_stack.txt"',
        'r"D:\\ansys\\ANSYS Inc\\ANSYS Student\\v261\\fluent\\ntbin\\win64\\fluent.exe"',
        '"PINNED_FLUENT_EXECUTABLE_NOT_FOUND"',
        '"pinned_fluent_executable_verified"',
        "session.exit(wait=False)",
        "faulthandler.dump_traceback_later(",
        "45, repeat=True, file=launch_stack, exit=False",
        "faulthandler.cancel_dump_traceback_later()",
        'os.name != "nt"',
        'os.environ.get("PROCESSOR_ARCHITECTURE") != "AMD64"',
        "module.is_windows = lambda: True",
        '"PYFLUENT_WINDOWS_PLATFORM_IDENTITY_NOT_VERIFIED"',
        '"PYFLUENT_WINDOWS_PLATFORM_PIN_FAILED"',
        "pin_verified_windows_platform_for_pyfluent()",
        '"pyfluent_windows_platform_pinned"',
        'trace_checkpoint("predecessor_validation_started")',
        '"predecessor_validation_completed"',
        'trace_checkpoint("step_copy_started"',
        'trace_checkpoint("step_copy_completed"',
        'trace_checkpoint("source_step_hash_started")',
        'trace_checkpoint("source_step_hash_completed"',
        'trace_checkpoint("staged_step_hash_started")',
        'trace_checkpoint("staged_step_hash_completed"',
        '"boundary_role_points_completed"',
        'trace_checkpoint("fluent_launch_started", start_timeout_seconds=60)',
        'trace_checkpoint("fluent_launch_completed")',
        'result["identity"]["predecessor_job_id"] = manifest.get(',
    ):
        assert required in SOURCE


def test_volume_mesh_and_student_guards_precede_write() -> None:
    for required in (
        "utilities.mesh_exists() is not True",
        'utilities.get_cell_zones(filter="*")',
        "utilities.get_cell_zone_count(",
        "utilities.get_cell_zone_volume(",
        "utilities.get_free_faces_count(",
        "utilities.get_multi_faces_count(",
        "utilities.mesh_check(",
        "utilities.get_cell_quality_limits(",
        "session.tui.report.mesh_size()",
        "MESH_STATS_LEVEL_ZERO_ROW_NOT_UNIQUE",
        "STUDENT_LIMIT_UNPROVEN_OR_EXCEEDED",
        "session.tui.file.write_mesh(str(MESH_PATH))",
        'cell_zone_raw = list(utilities.get_cell_zones(filter="*"))',
        "cell_zone_query(utilities, throat_axis_points[index])",
        '"throat_center_occupancy_observed"',
        '"TARGET_FLOW_VOLUME_NOT_MESHED:"',
        "get_interior_face_zones_for_given_cell_zones(",
        "get_adjacent_cell_zones_for_given_face_zones(",
        "get_baffles_for_face_zones(",
        "get_embedded_baffles()",
        '"CONNECTED_FLUID_CELL_ZONE_GRAPH_NOT_PROVEN:"',
        "quality_limits = list(",
    ):
        assert required in SOURCE
    assert "type(cell_zone_raw) is not list" not in SOURCE
    assert "type(quality_limits) is not list" not in SOURCE
    assert SOURCE.index("STUDENT_LIMIT_UNPROVEN_OR_EXCEEDED") < SOURCE.index(
        "session.tui.file.write_mesh(str(MESH_PATH))"
    )


def test_cell_zone_point_query_preserves_no_hit() -> None:
    for required in (
        "if raw_zone_ids is None:",
        'return {"raw_none": True, "zone_ids": []}',
        '"CELL_ZONE_QUERY_RETURN_NOT_ITERABLE"',
        '"CELL_ZONE_QUERY_RETURN_NOT_INTEGER_IDS"',
        '"first_miss_indices": []',
    ):
        assert required in SOURCE
    assert SOURCE.index('"throat_center_occupancy_observed"') < SOURCE.index(
        '"TARGET_FLOW_VOLUME_NOT_MESHED:'
    )


def test_cell_zone_graph_uses_per_face_dual_adjacency() -> None:
    nodes = [
        node for node in TREE.body
        if isinstance(node, ast.FunctionDef)
        and node.name in {"adjacent_cell_zone_ids", "build_cell_zone_graph"}
    ]
    namespace = {"Any": object}
    module = ast.Module(body=nodes, type_ignores=[])
    exec(
        compile(ast.fix_missing_locations(module), str(SOURCE_PATH), "exec"),
        namespace,
    )

    class Utilities:
        adjacent = {10: [1, 2], 11: [2, 3]}

        def get_adjacent_cell_zones_for_given_face_zones(self, face_zone_id_list):
            return self.adjacent[face_zone_id_list[0]]

        def get_face_zone_count(self, face_zone_id_list):
            return 7

        def get_zone_type(self, zone_id):
            return "interior"

    records, reached = namespace["build_cell_zone_graph"](
        Utilities(), [1, 2, 3], [10, 11]
    )
    assert reached == [1, 2, 3]
    assert [record["adjacent_cell_zone_ids"] for record in records] == [
        [1, 2], [2, 3]
    ]
    bad = Utilities()
    bad.adjacent = {10: [1, 4]}
    try:
        namespace["build_cell_zone_graph"](bad, [1, 2, 3], [10])
    except RuntimeError as exc:
        assert "UNKNOWN_CELL_ZONE" in str(exc)
    else:
        raise AssertionError("unknown graph node accepted")


def test_claim_ceiling_is_explicit() -> None:
    for required in (
        '"formal_006_completion": False',
        '"p1_stage_gate": "NOT_RUN"',
        '"p1_mesh_gate": "NOT_RUN"',
        '"p1_p6_gates": "NOT_RUN"',
        '"physics": "NOT_RUN"',
        '"boundary_conditions": "NOT_APPLIED"',
        '"solver_mode": "NOT_ENTERED"',
        '"solver_initialization": "NOT_RUN"',
        '"solver_iterations": 0',
        '"solution": "NOT_RUN"',
        '"cht": "NOT_RUN"',
        '"fsi": "NOT_RUN"',
        '"license_arguments_added": False',
    ):
        assert required in SOURCE


def main() -> None:
    tests = [
        value for name, value in sorted(globals().items())
        if name.startswith("test_") and callable(value)
    ]
    for test in tests:
        test()
        print("PASS", test.__name__)
    print("AJM006_V03_PYFLUENT_CONSUMER_GUARDS=PASS_ALL")


if __name__ == "__main__":
    main()

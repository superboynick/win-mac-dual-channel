#!/usr/bin/env python3
"""Static fail-closed guards for the V03 PyFluent mesh-only consumer."""

from __future__ import annotations

import ast
import copy
from pathlib import Path


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
    assert len(assertions) == 17 and len(set(assertions)) == 17
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
        "workflow.update_boundaries.boundary_zone_list",
        "workflow.update_boundaries.boundary_zone_type_list",
        "workflow.update_boundaries.old_boundary_zone_list",
        "workflow.update_boundaries.old_boundary_zone_type_list",
        '"boundary_zone_types_updated"',
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


def test_update_regions_probe_is_observation_only_and_ordered() -> None:
    boundary_guard = SOURCE.index("BOUNDARY_ZONE_TYPES_NOT_4_VELOCITY_1_PRESSURE")
    state_read = SOURCE.index("workflow.update_regions.arguments()")
    state_trace = SOURCE.index('"update_regions_pre_execute_state"')
    region_execute = SOURCE.index("workflow.update_regions()", state_read + 1)
    volume_mesh = SOURCE.index("workflow.create_volume_mesh_wtm")
    assert boundary_guard < state_read < state_trace < region_execute < volume_mesh
    assert SOURCE.count("workflow.update_regions.arguments()") == 1
    assert SOURCE.count("workflow.update_regions()") == 1
    observation_window = SOURCE[state_read:region_execute]
    for forbidden in (
        "workflow.update_regions.region_name_list =",
        "workflow.update_regions.region_type_list =",
        "workflow.update_regions.set_state(",
        "workflow.update_regions.arguments({",
    ):
        assert forbidden not in observation_window


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
        "list(utilities.get_cell_zones(xyz_coordinates=point))",
        "quality_limits = list(",
    ):
        assert required in SOURCE
    assert "type(cell_zone_raw) is not list" not in SOURCE
    assert "type(quality_limits) is not list" not in SOURCE
    assert SOURCE.index("STUDENT_LIMIT_UNPROVEN_OR_EXCEEDED") < SOURCE.index(
        "session.tui.file.write_mesh(str(MESH_PATH))"
    )


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

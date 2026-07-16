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
        "product_continuous_fluid.scdocx",
        "product_continuous_fluid.step",
        "v03_native_reopen.json",
        "v03_step_reimport.json",
        "v03_throat_inventory.json",
        "v03_source_chain.json",
    }
    assert len(values["PRODUCER_ASSERTIONS"]) == 17
    assertions = values["ASSERTION_NAMES"]
    assert len(assertions) == 21 and len(set(assertions)) == 21
    assert "boundary_semantics_preserved_1078" in assertions
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
        "STAGED_NATIVE_NOT_BYTE_IDENTICAL",
        "PREDECESSOR_NATIVE_EVIDENCE_INVALID",
        "PREDECESSOR_STEP_EVIDENCE_INVALID",
        "staged_native_immutable",
        '"exact_native_and_step_byte_staging"',
        "get_face_zones(",
        "convert_zone_ids_to_name_strings(",
        "convert_zone_name_strings_to_ids(",
        "THROAT_CENTER_SET_NOT_972_UNIQUE",
        "RECONSTRUCTED_BOUNDARY_ZONE_ROLE_CONFLICT",
        "raw_zone_ids = meshing_utilities.get_face_zones(",
        "zone_ids = list(raw_zone_ids)",
        '"boundary_zone_queries_completed"',
        "session.tui.boundary.manage.flip(imported_face_zone_names)",
        '"imported_boundary_normals_reversed"',
    ):
        assert required in SOURCE
    assert "type(zone_ids) is not list" not in SOURCE
    assert "type(zone_ids[0]) is not int" not in SOURCE


def test_official_v261_watertight_calls_are_pinned() -> None:
    for required in (
        "workflow.import_geometry.file_name",
        "workflow.import_geometry.file_name = str(STAGED_NATIVE_PATH)",
        '"NATIVE_SCDOCX_BOUND_TO_SIGNED_PREDECESSOR"',
        '"NATIVE_IMPORT_FACE_ZONE_COUNT_NOT_1078:{}"',
        "rebind_post_surface_canonical_records(",
        "session.tui.boundary.separate.sep_face_zone_by_region([inlet_name])",
        '"POST_SURFACE_NATIVE_BOUNDARY_ZONE_COUNT_LT_7:{}"',
        '"POST_SURFACE_INLET_SPLIT_COUNT_NOT_4"',
        '"POST_SURFACE_ROLE_ZONE_IDS_NOT_EXACT_10"',
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
        '"The geometry consists of only fluid regions with no voids"',
        "workflow.describe_geometry.setup_type = FLUID_ONLY_SETUP_TYPE",
        "workflow.describe_geometry.wall_to_internal = False",
        "workflow.describe_geometry.arguments()",
        '"describe_geometry_pre_execute_state"',
        "workflow.update_boundaries.boundary_zone_list",
        "workflow.update_boundaries.boundary_zone_type_list",
        "workflow.update_boundaries.old_boundary_zone_list",
        "workflow.update_boundaries.old_boundary_zone_type_list",
        '"boundary_zone_types_updated"',
        "utilities.set_object_cell_zone_type(",
        'cell_zone_type="fluid"',
        '"fluid_only_object_cell_zone_type_route_selected"',
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
        "workflow.create_regions",
        "workflow.update_regions",
        "number_of_flow_volumes",
        '"The geometry consists of both fluid and solid regions and/or voids"',
    ):
        assert forbidden not in SOURCE


def test_fluid_only_region_route_is_explicit_and_ordered() -> None:
    boundary_guard = SOURCE.index("BOUNDARY_SEMANTIC_ZONE_TYPES_NOT_EXACT")
    describe = SOURCE.index(
        '"The geometry consists of only fluid regions with no voids"'
    )
    select_fluid_object = SOURCE.index(
        "utilities.set_object_cell_zone_type("
    )
    route_trace = SOURCE.index(
        '"fluid_only_object_cell_zone_type_route_selected"'
    )
    volume_mesh = SOURCE.index("workflow.create_volume_mesh_wtm")
    inventory = SOURCE.index("fluid_only_inventory = {")
    assert (
        describe
        < boundary_guard
        < select_fluid_object
        < route_trace
        < volume_mesh
        < inventory
    )
    for required in (
        '"workflow.describe_geometry.setup_type"',
        '"utilities.get_cell_zones"',
        '"utilities.get_zone_type"',
        '"meshing_utilities.convert_zone_ids_to_name_strings"',
        '"non_flow_region_count": 0',
        '"route": "REVERSED_BOUNDARY_FLUID_OBJECT"',
        'utilities.get_objects(filter="*")',
        'not name.startswith("origin-")',
        'f"origin-{mesh_object_candidates[0]}" not in mesh_objects',
        "len(mesh_objects) != 2",
        "utilities.set_object_cell_zone_type(",
        'object_name=mesh_object_name, cell_zone_type="fluid"',
        '"fluid_object_cell_zone_type_selected"',
        "setup_type=FLUID_ONLY_SETUP_TYPE",
        "create_regions_executed=False",
        "update_regions_executed=False",
    ):
        assert required in SOURCE
    for forbidden in (
        "workflow.create_regions",
        "workflow.update_regions",
        "number_of_flow_volumes",
        '"The geometry consists of both fluid and solid regions and/or voids"',
        "session.tui.material_point",
        "session.tui.objects.volumetric_regions",
    ):
        assert forbidden not in SOURCE


def load_contract_helpers() -> dict[str, Any]:
    helper_names = {
        "validate_full_throat_occupancy",
        "validate_actuator_gap_exclusion",
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
        "re": re,
    }
    module = ast.Module(body=nodes, type_ignores=[])
    exec(
        compile(ast.fix_missing_locations(module), str(SOURCE_PATH), "exec"),
        namespace,
    )
    return namespace


def load_semantic_helpers() -> dict[str, Any]:
    helper_names = {
        "build_boundary_role_blueprint",
        "validate_semantic_zone_mapping",
        "validate_canonical_semantic_mapping",
        "semantic_zone_type",
        "validate_final_boundary_semantics",
    }
    nodes = [
        node
        for node in TREE.body
        if isinstance(node, ast.FunctionDef) and node.name in helper_names
    ]
    assert {node.name for node in nodes} == helper_names
    role_counts = {
        "INLET": 4,
        "OUTLET": 1,
        "HEAT_WALL": 1,
        "MEMBRANE_TOP": 12,
        "MEMBRANE_BOTTOM": 12,
        "ORIFICE_THROAT_WALL": 972,
        "WALL_CONTINUOUS_UNCLASSIFIED": 76,
    }
    namespace = {
        "Any": Any,
        "math": __import__("math"),
        "THROAT_RADIUS_MM": 0.125,
        "BOUNDARY_ROLE_ORDER": tuple(role_counts),
        "EXPECTED_BOUNDARY_ROLE_COUNTS": role_counts,
        "SOURCE_BOUNDARY_FACE_COUNT": 1078,
        "CANONICAL_BOUNDARY_ZONE_NAMES": {
            "INLET": ["ajm_inlet_001", "ajm_inlet_002", "ajm_inlet_003", "ajm_inlet_004"],
            "OUTLET": ["ajm_outlet"],
            "HEAT_WALL": ["ajm_heat_wall"],
            "MEMBRANE_TOP": ["ajm_membrane_top"],
            "MEMBRANE_BOTTOM": ["ajm_membrane_bottom"],
            "ORIFICE_THROAT_WALL": ["ajm_throat_wall"],
            "WALL_CONTINUOUS_UNCLASSIFIED": ["ajm_remaining_wall"],
        },
        "CANONICAL_BOUNDARY_ZONE_COUNT": 10,
    }
    module = ast.Module(body=nodes, type_ignores=[])
    exec(
        compile(ast.fix_missing_locations(module), str(SOURCE_PATH), "exec"),
        namespace,
    )
    return namespace


def semantic_source_fixture() -> dict[str, Any]:
    role_counts = {
        "INLET": 4,
        "OUTLET": 1,
        "HEAT_WALL": 1,
        "MEMBRANE_TOP": 12,
        "MEMBRANE_BOTTOM": 12,
        "ORIFICE_THROAT_WALL": 972,
        "WALL_CONTINUOUS_UNCLASSIFIED": 76,
    }
    faces = []
    index = 0
    for role, count in role_counts.items():
        for _ in range(count):
            x = float(index + 1)
            faces.append(
                {
                    "area_mm2": x,
                    "bbox_max_mm": [x + 0.25, 1.0, 1.0],
                    "bbox_min_mm": [x - 0.25, 0.0, 0.0],
                    "body_name": "AJM006_V03_FLUID_CONTINUOUS",
                    "center_mm": [x, 0.5, 0.5],
                    "classification": role,
                    "edge_count": 4,
                }
            )
            index += 1
    return {"continuous_faces": faces}


def semantic_mapping_fixture(blueprint: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "source_face_index": record["source_face_index"],
            "role": record["role"],
            "zone_id": record["source_face_index"] + 1,
            "zone_name": "ajm_semantic_{:04d}".format(record["source_face_index"]),
        }
        for record in blueprint
    ]


def canonical_mapping_fixture(
    blueprint: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    role_names = {
        "INLET": ["ajm_inlet_001", "ajm_inlet_002", "ajm_inlet_003", "ajm_inlet_004"],
        "OUTLET": ["ajm_outlet"],
        "HEAT_WALL": ["ajm_heat_wall"],
        "MEMBRANE_TOP": ["ajm_membrane_top"],
        "MEMBRANE_BOTTOM": ["ajm_membrane_bottom"],
        "ORIFICE_THROAT_WALL": ["ajm_throat_wall"],
        "WALL_CONTINUOUS_UNCLASSIFIED": ["ajm_remaining_wall"],
    }
    name_to_id = {
        name: index + 1
        for index, name in enumerate(
            name for names in role_names.values() for name in names
        )
    }
    role_offsets = {role: 0 for role in role_names}
    records = []
    for record in blueprint:
        role = record["role"]
        names = role_names[role]
        name = names[role_offsets[role] % len(names)]
        role_offsets[role] += 1
        records.append(
            {
                "source_face_index": record["source_face_index"],
                "role": role,
                "zone_id": name_to_id[name],
                "zone_name": name,
            }
        )
    return records


def test_c7_source_blueprint_and_unique_mapping_contract() -> None:
    helpers = load_semantic_helpers()
    source = semantic_source_fixture()
    blueprint = helpers["build_boundary_role_blueprint"](source)
    assert len(blueprint) == 1078
    assert blueprint[30]["role"] == "ORIFICE_THROAT_WALL"
    assert blueprint[30]["probe_point_mm"][0] == 31.125
    mapping = semantic_mapping_fixture(blueprint)
    summary = helpers["validate_semantic_zone_mapping"](mapping, "TEST")
    assert summary["semantic_zone_count"] == 1078
    assert summary["role_exclusive_mapping_ok"] is True
    assert summary["role_counts"]["ORIFICE_THROAT_WALL"] == 972

    missing = copy.deepcopy(source)
    missing["continuous_faces"].pop()
    expect_runtime_error(
        helpers["build_boundary_role_blueprint"],
        missing,
        marker="SOURCE_BOUNDARY_FACE_COUNT_NOT_1078",
    )
    wrong_role = copy.deepcopy(source)
    wrong_role["continuous_faces"][0]["classification"] = "GENERIC_WALL"
    expect_runtime_error(
        helpers["build_boundary_role_blueprint"],
        wrong_role,
        marker="SOURCE_BOUNDARY_ROLE_INVALID",
    )
    duplicate = copy.deepcopy(source)
    duplicate["continuous_faces"][1] = copy.deepcopy(
        duplicate["continuous_faces"][0]
    )
    expect_runtime_error(
        helpers["build_boundary_role_blueprint"],
        duplicate,
        marker="SOURCE_BOUNDARY_FINGERPRINT_DUPLICATE",
    )

    same_role_merged = copy.deepcopy(mapping)
    same_role_merged[-1]["zone_id"] = same_role_merged[-2]["zone_id"]
    same_role_merged[-1]["zone_name"] = same_role_merged[-2]["zone_name"]
    merged_summary = helpers["validate_semantic_zone_mapping"](
        same_role_merged, "TEST"
    )
    assert merged_summary["semantic_zone_count"] == 1077
    collapsed = copy.deepcopy(mapping)
    collapsed[-1]["zone_id"] = collapsed[0]["zone_id"]
    collapsed[-1]["zone_name"] = collapsed[0]["zone_name"]
    expect_runtime_error(
        helpers["validate_semantic_zone_mapping"],
        collapsed,
        "TEST",
        marker="TEST_SEMANTIC_ZONE_CROSSES_ROLES",
    )
    duplicate_name = copy.deepcopy(mapping)
    duplicate_name[-1]["zone_name"] = duplicate_name[0]["zone_name"]
    expect_runtime_error(
        helpers["validate_semantic_zone_mapping"],
        duplicate_name,
        "TEST",
        marker="TEST_SEMANTIC_ZONE_NAME_CROSSES_IDS",
    )


def test_c7_final_boundary_coverage_and_single_fluid_adjacency() -> None:
    helpers = load_semantic_helpers()
    blueprint = helpers["build_boundary_role_blueprint"](
        semantic_source_fixture()
    )
    mapping = canonical_mapping_fixture(blueprint)
    boundary_ids = list(range(1, 11))
    zone_types = {
        record["zone_id"]: helpers["semantic_zone_type"](record["role"])
        for record in mapping
    }
    adjacency = {zone_id: [2001] for zone_id in boundary_ids}
    summary = helpers["validate_final_boundary_semantics"](
        mapping, boundary_ids, zone_types, adjacency, [2001]
    )
    assert summary == {
        "role_counts": {
            "INLET": 4,
            "OUTLET": 1,
            "HEAT_WALL": 1,
            "MEMBRANE_TOP": 12,
            "MEMBRANE_BOTTOM": 12,
            "ORIFICE_THROAT_WALL": 972,
            "WALL_CONTINUOUS_UNCLASSIFIED": 76,
        },
        "canonical_zone_count": 10,
        "boundary_coverage_count": 1078,
        "role_exclusive_mapping_ok": True,
        "generic_boundary_collapse": False,
        "single_fluid_adjacency_ok": True,
        "canonical_inventory": {
            record["zone_name"]: {
                "role": record["role"],
                "zone_id": record["zone_id"],
                "zone_type": zone_types[record["zone_id"]],
                "source_component_count": (
                    1 if record["role"] == "INLET" else {
                        "OUTLET": 1,
                        "HEAT_WALL": 1,
                        "MEMBRANE_TOP": 12,
                        "MEMBRANE_BOTTOM": 12,
                        "ORIFICE_THROAT_WALL": 972,
                        "WALL_CONTINUOUS_UNCLASSIFIED": 76,
                    }[record["role"]]
                ),
                "adjacent_cell_zone_ids": [2001],
            }
            for record in mapping
        },
    }
    expect_runtime_error(
        helpers["validate_final_boundary_semantics"],
        mapping,
        boundary_ids[:-1],
        zone_types,
        adjacency,
        [2001],
        marker="POST_VOLUME_SEMANTIC_BOUNDARY_COVERAGE_INVALID",
    )
    wrong_adjacency = copy.deepcopy(adjacency)
    wrong_adjacency[1] = [2001, 2002]
    expect_runtime_error(
        helpers["validate_final_boundary_semantics"],
        mapping,
        boundary_ids,
        zone_types,
        wrong_adjacency,
        [2001],
        marker="POST_VOLUME_SEMANTIC_SINGLE_FLUID_ADJACENCY_INVALID",
    )


def test_c7_runtime_integration_and_compact_evidence_fields_are_pinned() -> None:
    for required in (
        "build_boundary_role_blueprint(inventory)",
        "session.tui.boundary.manage.merge(current_names)",
        "session.tui.boundary.manage.name(current_name, target_name)",
        "session.tui.boundary.manage.name(current_names[0], target_names[0])",
        'observe_semantic_zone_mapping(\n            utilities, boundary_blueprint, "PRE_SURFACE"',
        "rebind_post_surface_canonical_records(",
        'observe_semantic_zone_mapping(\n            utilities, boundary_blueprint, "POST_VOLUME"',
        'result["assertions"]["boundary_semantics_preserved_1078"] = True',
        '"source_boundary_face_count": SOURCE_BOUNDARY_FACE_COUNT',
        '"source_boundary_role_counts": source_boundary_role_counts',
        '"pre_canonical_role_exclusive_mapping_ok"',
        '"canonical_boundary_zone_count"',
        '"post_volume_boundary_role_counts"',
        '"post_volume_boundary_coverage_count"',
        '"post_volume_role_exclusive_mapping_ok"',
        '"post_volume_generic_boundary_collapse"',
        '"post_volume_single_fluid_adjacency_ok"',
        '"post_volume_canonical_boundary_inventory"',
    ):
        assert required in SOURCE


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


def test_fluid_only_inventory_is_observed_from_actual_cell_zone() -> None:
    for required in (
        "if len(cell_zone_ids) != 1:",
        "cell_zone_names = zone_names_one_way(utilities, cell_zone_ids)",
        '"name": cell_zone_names[0]',
        '"type": "fluid"',
        '"classification": "MAIN_FLOW"',
        'post_update_region_inventory = copy.deepcopy(fluid_only_inventory)',
    ):
        assert required in SOURCE
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

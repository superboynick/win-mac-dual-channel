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
        "session.tui.boundary.separate.sep_face_zone_by_region(",
        '"POST_SURFACE_NATIVE_BOUNDARY_ZONE_COUNT_LT_7:{}"',
        '"POST_SURFACE_INLET_REPRESENTATIVE_BINDING_INVALID"',
        "validate_post_surface_role_partition(",
        "canonical_boundary_update_contract(",
        'workflow.import_geometry.length_unit = "mm"',
        'workflow.import_geometry.cad_import_options.one_zone_per = "face"',
        'imported_face_zone_ids = list(utilities.get_face_zones(filter="*"))',
        '"import_face_zone_inventory_completed"',
        'local.add_child = "yes"',
        'local.boi_execution = "Face Size"',
        "local.boi_face_zone_list = throat_zone_names",
        "local.boi_size = THROAT_LOCAL_SIZE_MM",
        "local.add_child_and_update(defer_update=False)",
        "validate_local_sizing_child(",
        "workflow.create_surface_mesh",
        "surface.cfd_surface_mesh_controls.min_size = SURFACE_MIN_SIZE_MM",
        "surface.cfd_surface_mesh_controls.max_size = SURFACE_MAX_SIZE_MM",
        "workflow.describe_geometry.update_child_tasks(setup_type_changed=False)",
        "workflow.describe_geometry.update_child_tasks(setup_type_changed=True)",
        '"The geometry consists of both fluid and solid regions and/or voids"',
        "workflow.describe_geometry.setup_type = MIXED_REGION_SETUP_TYPE",
        "workflow.describe_geometry.wall_to_internal = False",
        "workflow.describe_geometry.arguments()",
        '"describe_geometry_pre_execute_state"',
        "workflow.update_boundaries.boundary_zone_list",
        "workflow.update_boundaries.boundary_zone_type_list",
        "workflow.update_boundaries.old_boundary_zone_list",
        "workflow.update_boundaries.old_boundary_zone_type_list",
        '"boundary_zone_types_updated"',
        "workflow.create_regions()",
        "workflow.update_regions()",
        '"MIXED_1_MAIN_12_VOID_UPDATE_REGIONS"',
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
        "number_of_flow_volumes",
        '"The geometry consists of only fluid regions with no voids"',
    ):
        assert forbidden not in SOURCE


def test_mixed_region_route_is_explicit_and_ordered() -> None:
    boundary_guard = SOURCE.index("BOUNDARY_SEMANTIC_ZONE_TYPES_NOT_EXACT")
    describe = SOURCE.index(
        '"The geometry consists of both fluid and solid regions and/or voids"'
    )
    create_regions = SOURCE.index("workflow.create_regions()")
    update_regions = SOURCE.index("workflow.update_regions()")
    volume_mesh = SOURCE.index("workflow.create_volume_mesh_wtm")
    assert (
        describe
        < boundary_guard
        < create_regions
        < update_regions
        < volume_mesh
    )
    for required in (
        '"workflow.update_regions.region_current_list"',
        '"workflow.update_regions.region_current_type_list"',
        '"workflow.update_regions.number_of_listed_regions"',
        '"non_flow_region_count": 12',
        '"route": "MIXED_1_MAIN_12_VOID_UPDATE_REGIONS"',
        '"voids_excluded": True',
    ):
        assert required in SOURCE
    for forbidden in (
        "number_of_flow_volumes",
        '"The geometry consists of only fluid regions with no voids"',
        "session.tui.material_point",
        "session.tui.objects.volumetric_regions",
    ):
        assert forbidden not in SOURCE


def load_contract_helpers() -> dict[str, Any]:
    helper_names = {
        "validate_full_throat_occupancy",
        "validate_actuator_gap_exclusion",
        "parse_mesh_size",
        "json_safe_trace_value",
        "observe_parameter",
        "observe_update_regions_argument_menu",
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
        "validate_post_surface_role_partition",
        "canonical_boundary_update_contract",
        "validate_mixed_region_state",
        "validate_local_sizing_child",
        "workflow_task_identity",
        "semantic_zone_type",
        "validate_final_boundary_semantics",
        "json_safe_trace_value",
        "zone_names_one_way",
        "safe_diagnostic_observation",
        "build_post_surface_coverage_diagnostic",
        "validate_post_surface_product_suffix_structure",
        "resolve_post_surface_dual_object_boundaries",
        "enforce_post_surface_native_role_coverage",
        "classify_post_surface_product_roles",
        "rebuild_post_surface_canonical_records",
        "one_face_zone",
        "bind_post_surface_inlet_representatives",
        "validate_post_surface_product_only_state",
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
        "re": re,
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
        "THROAT_LOCAL_SIZE_MM": 0.075,
        "PRELAUNCH_TRACE_PATH": Path("v03_pyfluent_prelaunch_trace.jsonl"),
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


def post_surface_dual_object_fixture(suffix_start=1124):
    origin_ids = {
        "INLET": [1051, 1056, 1065, 1071],
        "OUTLET": [2],
        "HEAT_WALL": [1078],
        "MEMBRANE_TOP": [7],
        "MEMBRANE_BOTTOM": [9],
        "ORIFICE_THROAT_WALL": [78],
        "WALL_CONTINUOUS_UNCLASSIFIED": [3],
    }
    origin_names = {
        "INLET": ["ajm_inlet_001", "ajm_inlet_002", "ajm_inlet_003", "ajm_inlet_004"],
        "OUTLET": ["ajm_outlet"],
        "HEAT_WALL": ["ajm_heat_wall"],
        "MEMBRANE_TOP": ["ajm_membrane_top"],
        "MEMBRANE_BOTTOM": ["ajm_membrane_bottom"],
        "ORIFICE_THROAT_WALL": ["ajm_throat_wall"],
        "WALL_CONTINUOUS_UNCLASSIFIED": ["ajm_remaining_wall"],
    }
    name_by_id = {}
    for role in origin_ids:
        name_by_id.update(zip(origin_ids[role], origin_names[role]))
    product_ids = {
        "INLET": [1105],
        "OUTLET": [4],
        "HEAT_WALL": [8],
        "MEMBRANE_TOP": [5] + list(range(suffix_start + 12, suffix_start + 23)),
        "MEMBRANE_BOTTOM": [6] + list(range(suffix_start + 23, suffix_start + 34)),
        "ORIFICE_THROAT_WALL": [1106],
        "WALL_CONTINUOUS_UNCLASSIFIED": [1104] + list(range(suffix_start, suffix_start + 12)),
    }
    name_by_id.update(
        {
            1105: "inlet",
            4: "outlet",
            8: "heat_wall",
            5: "membrane_top",
            6: "membrane_bottom",
            1106: "orifice_throat_wall",
            1104: "fluid_continuous:1",
        }
    )
    name_by_id.update({zone_id: f"membrane_top:{zone_id}" for zone_id in range(suffix_start + 12, suffix_start + 23)})
    name_by_id.update({zone_id: f"membrane_bottom:{zone_id}" for zone_id in range(suffix_start + 23, suffix_start + 34)})
    name_by_id.update({zone_id: f"fluid_continuous:{zone_id}" for zone_id in range(suffix_start, suffix_start + 12)})
    origin_flat = sorted(zone_id for ids in origin_ids.values() for zone_id in ids)
    product_flat = sorted(zone_id for ids in product_ids.values() for zone_id in ids)
    return {
        "origin_ids": origin_ids,
        "origin_names": origin_names,
        "product_ids": product_ids,
        "objects": ["mesh-object-with-no-trusted-name", "origin-object-also-untrusted"],
        "type_objects": {
            "geom": ["origin-object-also-untrusted"],
            "mesh": ["mesh-object-with-no-trusted-name"],
        },
        "object_ids": {
            "mesh-object-with-no-trusted-name": product_flat,
            "origin-object-also-untrusted": origin_flat,
        },
        "global_ids": sorted(origin_flat + product_flat),
        "name_by_id": name_by_id,
        "type_by_id": {
            zone_id: ("geometry" if zone_id in origin_flat else "wall")
            for zone_id in origin_flat + product_flat
        },
    }


class PostSurfaceDualObjectUtilities:
    def __init__(self, fixture):
        self.fixture = fixture

    def get_objects(self, filter=None, type_name=None):
        if type_name is not None:
            return list(self.fixture["type_objects"][type_name])
        assert filter == "*"
        return list(self.fixture["objects"])

    def get_face_zones(self, filter):
        assert filter == "*"
        return list(reversed(self.fixture["global_ids"]))

    def get_face_zones_of_object(self, object_name):
        return list(reversed(self.fixture["object_ids"][object_name]))

    def convert_zone_ids_to_name_strings(self, zone_id_list):
        return [self.fixture["name_by_id"][zone_id] for zone_id in zone_id_list]

    def get_zone_type(self, zone_id):
        return self.fixture["type_by_id"][zone_id]

    def get_face_zone_count(self, face_zone_id_list):
        return 1

    def get_adjacent_cell_zones_for_given_face_zones(self, face_zone_id_list):
        return []

    def get_labels_on_face_zones(self, face_zone_id_list):
        return []

    def get_regions_of_face_zones(self, face_zone_id_list):
        return []

    def get_all_objects(self):
        return list(self.fixture["objects"])

    def get_average_bounding_box_center(self, face_zone_id_list):
        return [0.0, 0.0, 0.0]


def test_post_surface_dual_object_41_wall_partition_is_exact() -> None:
    resolve = load_semantic_helpers()[
        "resolve_post_surface_dual_object_boundaries"
    ]
    fixture = post_surface_dual_object_fixture()
    observed = resolve(
        PostSurfaceDualObjectUtilities(fixture),
        fixture["origin_ids"],
        fixture["origin_names"],
    )
    assert observed["global_zone_ids"] == fixture["global_ids"]
    assert observed["origin_object"] == "origin-object-also-untrusted"
    assert observed["product_object"] == "mesh-object-with-no-trusted-name"
    assert observed["geometry_objects"] == ["origin-object-also-untrusted"]
    assert observed["mesh_objects"] == ["mesh-object-with-no-trusted-name"]
    assert observed["origin_zone_ids"] == sorted(
        zone_id for ids in fixture["origin_ids"].values() for zone_id in ids
    )
    assert observed["product_zone_ids"] == sorted(
        zone_id for ids in fixture["product_ids"].values() for zone_id in ids
    )
    assert {
        role: sorted(ids)
        for role, ids in observed["product_role_zone_ids"].items()
    } == {
        role: sorted(ids) for role, ids in fixture["product_ids"].items()
    }
    assert observed["product_role_counts"] == {
        "INLET": 1,
        "OUTLET": 1,
        "HEAT_WALL": 1,
        "MEMBRANE_TOP": 12,
        "MEMBRANE_BOTTOM": 12,
        "ORIFICE_THROAT_WALL": 1,
        "WALL_CONTINUOUS_UNCLASSIFIED": 13,
    }
    assert set(observed["origin_zone_ids"]).isdisjoint(
        observed["product_zone_ids"]
    )
    assert observed["product_suffix_structure"]["suffix_start_zone_id"] == 1124
    new_fixture = post_surface_dual_object_fixture(suffix_start=1123)
    new_observed = resolve(
        PostSurfaceDualObjectUtilities(new_fixture),
        new_fixture["origin_ids"],
        new_fixture["origin_names"],
    )
    assert new_observed["product_suffix_structure"] == {
        "suffix_start_zone_id": 1123,
        "suffix_end_zone_id": 1156,
        "suffix_zone_count": 34,
        "suffix_blocks": {
            "WALL_CONTINUOUS_UNCLASSIFIED": list(range(1123, 1135)),
            "MEMBRANE_TOP": list(range(1135, 1146)),
            "MEMBRANE_BOTTOM": list(range(1146, 1157)),
        },
    }


def test_post_surface_dual_object_partition_rejects_every_trust_break() -> None:
    resolve = load_semantic_helpers()[
        "resolve_post_surface_dual_object_boundaries"
    ]
    base = post_surface_dual_object_fixture()

    def reject(fixture, marker, origin_ids=None, origin_names=None):
        expect_runtime_error(
            resolve,
            PostSurfaceDualObjectUtilities(fixture),
            origin_ids if origin_ids is not None else fixture["origin_ids"],
            origin_names if origin_names is not None else fixture["origin_names"],
            marker=marker,
        )

    broken = copy.deepcopy(base)
    broken["objects"] = broken["objects"][:1]
    reject(broken, "POST_SURFACE_OBJECT_COUNT_NOT_EXACT_2")

    broken = copy.deepcopy(base)
    product_object, origin_object = broken["objects"]
    broken["object_ids"][product_object][0] = broken["object_ids"][origin_object][0]
    reject(broken, "POST_SURFACE_OBJECT_ZONE_IDS_OVERLAP")

    broken = copy.deepcopy(base)
    broken["global_ids"] = broken["global_ids"][:-1]
    reject(broken, "POST_SURFACE_GLOBAL_ZONE_COUNT_NOT_EXACT_51")

    broken = copy.deepcopy(base)
    broken["type_by_id"][broken["origin_ids"]["OUTLET"][0]] = "wall"
    reject(broken, "POST_SURFACE_ORIGIN_ZONE_TYPE_NOT_GEOMETRY")

    broken = copy.deepcopy(base)
    broken["type_objects"]["geom"] = []
    reject(broken, "POST_SURFACE_OBJECT_KIND_PARTITION_INVALID")

    broken = copy.deepcopy(base)
    broken["name_by_id"][broken["origin_ids"]["OUTLET"][0]] = "not-ajm-outlet"
    reject(broken, "POST_SURFACE_ORIGIN_CANONICAL_NAMES_INVALID")

    wrong_expected_ids = copy.deepcopy(base["origin_ids"])
    wrong_expected_ids["OUTLET"] = [999]
    reject(
        copy.deepcopy(base),
        "POST_SURFACE_ORIGIN_IDS_NOT_BOUND_TO_CANONICAL_SOURCE",
        origin_ids=wrong_expected_ids,
    )

    broken = copy.deepcopy(base)
    broken["type_by_id"][broken["product_ids"]["OUTLET"][0]] = "geometry"
    reject(broken, "POST_SURFACE_PRODUCT_ZONE_TYPE_NOT_WALL")

    broken = copy.deepcopy(base)
    broken["name_by_id"][broken["product_ids"]["OUTLET"][0]] = "mystery_wall"
    reject(broken, "POST_SURFACE_PRODUCT_ZONE_NAME_UNKNOWN")

    broken = copy.deepcopy(base)
    broken["name_by_id"][broken["product_ids"]["MEMBRANE_TOP"][1]] = "membrane_bottom:9999"
    reject(broken, "POST_SURFACE_PRODUCT_ROLE_COUNTS_INVALID")

    broken = copy.deepcopy(base)
    broken["name_by_id"][broken["product_ids"]["MEMBRANE_TOP"][1]] = "membrane_top:9999"
    reject(broken, "POST_SURFACE_PRODUCT_SUFFIX_NOT_ZONE_ID")

    broken = copy.deepcopy(base)
    old_zone_id = broken["product_ids"]["WALL_CONTINUOUS_UNCLASSIFIED"][1]
    new_zone_id = 9999
    broken["product_ids"]["WALL_CONTINUOUS_UNCLASSIFIED"][1] = new_zone_id
    for object_name, ids in broken["object_ids"].items():
        broken["object_ids"][object_name] = [
            new_zone_id if zone_id == old_zone_id else zone_id for zone_id in ids
        ]
    broken["global_ids"] = [
        new_zone_id if zone_id == old_zone_id else zone_id
        for zone_id in broken["global_ids"]
    ]
    broken["name_by_id"][new_zone_id] = "fluid_continuous:9999"
    broken["type_by_id"][new_zone_id] = broken["type_by_id"][old_zone_id]
    del broken["name_by_id"][old_zone_id]
    del broken["type_by_id"][old_zone_id]
    reject(broken, "POST_SURFACE_PRODUCT_SUFFIX_BLOCKS_NOT_CONTIGUOUS_ORDERED")


def test_post_surface_coverage_diagnostic_is_complete_and_fail_safe() -> None:
    build = load_semantic_helpers()["build_post_surface_coverage_diagnostic"]

    class Utilities:
        def convert_zone_ids_to_name_strings(self, zone_id_list):
            return ["zone-{}".format(zone_id) for zone_id in zone_id_list]

        def get_zone_type(self, zone_id):
            return "wall" if zone_id != 99 else "interior"

        def get_face_zone_count(self, face_zone_id_list):
            return 17 + face_zone_id_list[0]

        def get_adjacent_cell_zones_for_given_face_zones(self, face_zone_id_list):
            return [2001, 2002] if face_zone_id_list == [99] else [2001]

        def get_labels_on_face_zones(self, face_zone_id_list):
            return ["orphan-label"] if face_zone_id_list == [99] else []

        def get_regions_of_face_zones(self, face_zone_id_list):
            return ["dead11"] if face_zone_id_list == [99] else ["fluid"]

        def get_all_objects(self):
            return ["fluid-object", "orphan-object"]

        def get_face_zones_of_object(self, object_name):
            return [1, 2] if object_name == "fluid-object" else [99]

        def get_average_bounding_box_center(self, face_zone_id_list):
            return [float(face_zone_id_list[0]), 2.0, 3.0]

    role_ids = {
        role: ([1] if role == "INLET" else [2])
        for role in (
            "INLET",
            "OUTLET",
            "HEAT_WALL",
            "MEMBRANE_TOP",
            "MEMBRANE_BOTTOM",
            "ORIFICE_THROAT_WALL",
            "WALL_CONTINUOUS_UNCLASSIFIED",
        )
    }
    role_names = {
        role: ["mapped-{}".format(role.lower())] for role in role_ids
    }
    observed = build(Utilities(), [1, 2, 99], role_ids, role_names)
    assert set(observed) == {
        "global_zone_ids",
        "global_zone_count",
        "global_zone_names",
        "global_zone_types",
        "global_zone_face_counts",
        "role_mapped_ids",
        "role_mapped_names",
        "role_mapped_count",
        "missing_global_ids",
        "unexpected_mapped_ids",
        "missing_zone_diagnostics",
    }
    assert observed["global_zone_ids"] == [1, 2, 99]
    assert observed["global_zone_count"] == 3
    assert observed["global_zone_names"] == {
        "status": "OK",
        "value": ["zone-1", "zone-2", "zone-99"],
    }
    assert observed["missing_global_ids"] == [99]
    assert observed["unexpected_mapped_ids"] == []
    assert observed["role_mapped_count"] == 2
    assert observed["missing_zone_diagnostics"]["99"] == {
        "face_count": {"status": "OK", "value": 116},
        "zone_type": {"status": "OK", "value": "interior"},
        "one_way_name": {"status": "OK", "value": "zone-99"},
        "adjacent_cell_zone_ids": {"status": "OK", "value": [2001, 2002]},
        "labels": {"status": "OK", "value": ["orphan-label"]},
        "region_origins": {"status": "OK", "value": ["dead11"]},
        "object_origin_names": {"status": "OK", "value": ["orphan-object"]},
        "average_bounding_box_center": {
            "status": "OK",
            "value": [99.0, 2.0, 3.0],
        },
    }

    class OptionalQueriesFail(Utilities):
        def get_adjacent_cell_zones_for_given_face_zones(self, face_zone_id_list):
            raise RuntimeError("adjacency unavailable")

        def get_labels_on_face_zones(self, face_zone_id_list):
            raise RuntimeError("labels unavailable")

        def get_regions_of_face_zones(self, face_zone_id_list):
            raise RuntimeError("regions unavailable")

        def get_all_objects(self):
            raise RuntimeError("objects unavailable")

        def get_average_bounding_box_center(self, face_zone_id_list):
            raise RuntimeError("origin unavailable")

    failed = build(OptionalQueriesFail(), [1, 2, 99], role_ids, role_names)
    missing = failed["missing_zone_diagnostics"]["99"]
    for field in (
        "adjacent_cell_zone_ids",
        "labels",
        "region_origins",
        "object_origin_names",
        "average_bounding_box_center",
    ):
        assert missing[field]["status"] == "ERROR"
        assert missing[field]["error_type"] == "RuntimeError"
        assert missing[field]["error"]

    class OptionalQueriesReturnNone(Utilities):
        def get_adjacent_cell_zones_for_given_face_zones(self, face_zone_id_list):
            return None

        def get_labels_on_face_zones(self, face_zone_id_list):
            return None

        def get_regions_of_face_zones(self, face_zone_id_list):
            return None

        def get_all_objects(self):
            return None

        def get_average_bounding_box_center(self, face_zone_id_list):
            return None

    returned_none = build(
        OptionalQueriesReturnNone(), [1, 2, 99], role_ids, role_names
    )["missing_zone_diagnostics"]["99"]
    for field in (
        "adjacent_cell_zone_ids",
        "labels",
        "region_origins",
        "object_origin_names",
        "average_bounding_box_center",
    ):
        assert returned_none[field] == {
            "status": "ERROR",
            "error_type": "RuntimeError",
            "error": "POST_SURFACE_DIAGNOSTIC_QUERY_RETURNED_NONE",
        }


def test_native_coverage_mismatch_traces_then_raises_original_error() -> None:
    helpers = load_semantic_helpers()
    events = []
    helpers["trace_checkpoint"] = (
        lambda name, **details: events.append((name, details))
    )

    fixture = post_surface_dual_object_fixture()
    role_ids = copy.deepcopy(fixture["origin_ids"])
    role_ids["OUTLET"] = list(fixture["product_ids"]["OUTLET"])
    role_names = copy.deepcopy(fixture["origin_names"])
    diagnostics = {}
    expect_runtime_error(
        helpers["enforce_post_surface_native_role_coverage"],
        PostSurfaceDualObjectUtilities(fixture),
        fixture["global_ids"],
        role_ids,
        role_names,
        fixture["origin_ids"],
        fixture["origin_names"],
        diagnostics,
        marker="POST_SURFACE_NATIVE_ROLE_ZONE_COVERAGE_INVALID",
    )
    assert events and events[0][0] == "post_surface_native_role_coverage_observed"
    assert events[0][1]["global_zone_count"] == 51
    assert diagnostics["post_surface_native_role_coverage"] == {
        "trace_relative_path": "v03_pyfluent_prelaunch_trace.jsonl",
        "observation": events[0][1],
    }


def test_post_surface_native_trace_precedes_unchanged_gate_error() -> None:
    function = next(
        node
        for node in TREE.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "enforce_post_surface_native_role_coverage"
    )
    guarded = next(node for node in function.body if isinstance(node, ast.Try))
    try_source = "\n".join(
        ast.get_source_segment(SOURCE, node) or "" for node in guarded.body
    )
    handler_source = "\n".join(
        ast.get_source_segment(SOURCE, node) or ""
        for handler in guarded.handlers
        for node in handler.body
    )
    assert "resolve_post_surface_dual_object_boundaries(" in try_source
    assert "POST_SURFACE_NATIVE_ROLE_ZONE_COVERAGE_INVALID" in try_source
    assert "build_post_surface_coverage_diagnostic(" not in try_source
    assert "build_post_surface_coverage_diagnostic(" in handler_source
    assert "post_surface_native_role_coverage_observed" in handler_source


def test_product_only_state_guards_41_and_10_zone_transitions() -> None:
    validate = load_semantic_helpers()[
        "validate_post_surface_product_only_state"
    ]
    fixture = post_surface_dual_object_fixture()
    product_object = fixture["objects"][0]
    product_ids = list(fixture["object_ids"][product_object])
    product_only = copy.deepcopy(fixture)
    product_only["objects"] = [product_object]
    product_only["global_ids"] = list(product_ids)
    product_only["object_ids"] = {product_object: list(product_ids)}
    observed = validate(
        PostSurfaceDualObjectUtilities(product_only),
        product_object,
        product_ids,
        41,
        "POST_SURFACE_GEOMETRY_DELETE",
    )
    assert observed["objects"] == [product_object]
    assert len(observed["global_zone_ids"]) == 41

    canonical_ids = sorted(product_ids)[:10]
    canonical = copy.deepcopy(product_only)
    canonical["global_ids"] = list(canonical_ids)
    canonical["object_ids"][product_object] = list(canonical_ids)
    observed = validate(
        PostSurfaceDualObjectUtilities(canonical),
        product_object,
        canonical_ids,
        10,
        "POST_SURFACE_CANONICAL",
    )
    assert len(observed["global_zone_ids"]) == 10

    broken = copy.deepcopy(product_only)
    broken["objects"].append("unexpected-object")
    broken["object_ids"]["unexpected-object"] = []
    expect_runtime_error(
        validate,
        PostSurfaceDualObjectUtilities(broken),
        product_object,
        product_ids,
        41,
        "POST_SURFACE_GEOMETRY_DELETE",
        marker="POST_SURFACE_GEOMETRY_DELETE_PRODUCT_ONLY_STATE_INVALID",
    )


def test_destructive_post_surface_sequence_is_fully_gated() -> None:
    function = next(
        node
        for node in TREE.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "rebind_post_surface_canonical_records"
    )
    source = ast.get_source_segment(SOURCE, function)
    assert source is not None
    dual = source.index("enforce_post_surface_native_role_coverage(")
    partition_trace = source.index(
        '"post_surface_dual_object_partition_validated"'
    )
    delete = source.index("session.tui.objects.delete_all_geom()")
    delete_gate = source.index(
        '"POST_SURFACE_GEOMETRY_DELETE"', delete
    )
    merge = source.index("session.tui.boundary.manage.merge(")
    merge_gate = source.index('"POST_SURFACE_ROLE_MERGE"', merge)
    split = source.index(
        "session.tui.boundary.separate.sep_face_zone_by_region(", merge_gate
    )
    split_gate = source.index('"POST_SURFACE_INLET_SPLIT"', split)
    canonicalize = source.index("canonicalize_boundary_zones(", split_gate)
    canonical_gate = source.index('"POST_SURFACE_CANONICAL"', canonicalize)
    assert (
        dual
        < partition_trace
        < delete
        < delete_gate
        < merge
        < merge_gate
        < split
        < split_gate
        < canonicalize
        < canonical_gate
    )


def test_rebind_has_zero_exhaustive_post_surface_mapping_calls() -> None:
    function = next(
        node
        for node in TREE.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "rebind_post_surface_canonical_records"
    )
    calls = [
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "observe_semantic_zone_mapping"
    ]
    assert calls == []
    assert sum(
        1
        for node in ast.walk(function)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "bind_post_surface_inlet_representatives"
    ) == 1


def test_inlet_binding_executes_exactly_four_point_queries() -> None:
    bind = load_semantic_helpers()[
        "bind_post_surface_inlet_representatives"
    ]

    class Utilities:
        def __init__(self):
            self.query_count = 0

        def get_face_zones(self, xyz_coordinates):
            self.query_count += 1
            return [int(xyz_coordinates[0])]

        def convert_zone_ids_to_name_strings(self, zone_id_list):
            return ["inlet:{}".format(zone_id) for zone_id in zone_id_list]

    blueprint = [
        {
            "source_face_index": index,
            "role": "INLET",
            "probe_point_mm": [float(zone_id), 0.0, 0.0],
        }
        for index, zone_id in enumerate((1105, 29316, 29317, 29318))
    ]
    utilities = Utilities()
    ids, names = bind(
        utilities,
        blueprint,
        [29318, 1105, 29317, 29316],
    )
    assert utilities.query_count == 4
    assert ids == [1105, 29316, 29317, 29318]
    assert names == [
        "inlet:1105",
        "inlet:29316",
        "inlet:29317",
        "inlet:29318",
    ]


def test_post_surface_partition_region_and_local_sizing_negative_contracts() -> None:
    helpers = load_semantic_helpers()
    roles = {
        "INLET": [1, 1, 1, 1],
        "OUTLET": [2],
        "HEAT_WALL": [3],
        "MEMBRANE_TOP": [4],
        "MEMBRANE_BOTTOM": [5],
        "ORIFICE_THROAT_WALL": [6],
        "WALL_CONTINUOUS_UNCLASSIFIED": [7, 8, 9],
    }
    normalized = helpers["validate_post_surface_role_partition"](roles)
    assert normalized["INLET"] == [1]
    assert normalized["WALL_CONTINUOUS_UNCLASSIFIED"] == [7, 8, 9]
    crossing = copy.deepcopy(roles)
    crossing["OUTLET"] = [1]
    expect_runtime_error(
        helpers["validate_post_surface_role_partition"],
        crossing,
        marker="POST_SURFACE_ZONE_CROSSES_ROLES",
    )
    bad_inlets = copy.deepcopy(roles)
    bad_inlets["INLET"] = [1, 10]
    expect_runtime_error(
        helpers["validate_post_surface_role_partition"],
        bad_inlets,
        marker="POST_SURFACE_INLET_ZONE_CARDINALITY_INVALID",
    )

    blueprint = helpers["build_boundary_role_blueprint"](
        semantic_source_fixture()
    )
    canonical = canonical_mapping_fixture(blueprint)
    names, types, zone_ids = helpers["canonical_boundary_update_contract"](
        canonical
    )
    assert len(names) == len(types) == len(zone_ids) == 10
    assert len(set(zone_ids)) == 10

    region_names = ["fluid_continuous"] + [
        f"dead{index}-membrane_bottom" for index in range(12)
    ]
    region_types = ["fluid"] + ["dead"] * 12
    inventory = helpers["validate_mixed_region_state"](
        region_names, region_types, 13
    )
    assert inventory["main_flow_region_count"] == 1
    assert inventory["non_flow_region_count"] == 12
    expect_runtime_error(
        helpers["validate_mixed_region_state"],
        region_names[:-1],
        region_types[:-1],
        12,
        marker="MIXED_REGION_STATE_NOT_EXACT_13",
    )
    expect_runtime_error(
        helpers["validate_mixed_region_state"],
        region_names + ["dead12-membrane_bottom"],
        region_types + ["dead"],
        14,
        marker="MIXED_REGION_STATE_NOT_EXACT_13",
    )

    child_args = {
        "boi_control_name": "throat-face-size-0p075mm",
        "boi_execution": "Face Size",
        "boi_zoneor_label": "zone",
        "boi_face_zone_list": ["ajm_throat_wall"],
        "boi_size": 0.075,
    }
    helpers["validate_local_sizing_child"](
        True, ["existing"], ["existing", "new"], "new", child_args,
        ["ajm_throat_wall"],
    )
    expect_runtime_error(
        helpers["validate_local_sizing_child"],
        object(), ["existing"], ["existing", "new"], "new", child_args,
        ["ajm_throat_wall"],
        marker="LOCAL_SIZING_ADD_CHILD_NOT_TRUE",
    )

    class IntegerIdTask:
        def get_id(self):
            return 17

    class NameFallbackTask:
        def get_id(self):
            return None

        def name(self):
            return "local-sizing-child"

    assert helpers["workflow_task_identity"](IntegerIdTask()) == "id:17"
    assert (
        helpers["workflow_task_identity"](NameFallbackTask())
        == "name:local-sizing-child"
    )


def test_c7_runtime_integration_and_compact_evidence_fields_are_pinned() -> None:
    for required in (
        "build_boundary_role_blueprint(inventory)",
        "session.tui.boundary.manage.merge(current_names)",
        "session.tui.boundary.manage.name(current_name, target_name)",
        "session.tui.boundary.manage.name(current_names[0], target_names[0])",
        'observe_semantic_zone_mapping(\n            utilities, boundary_blueprint, "PRE_SURFACE"',
        "rebind_post_surface_canonical_records(",
        'result["diagnostics"]',
        'result["diagnostic_trace"] = file_record(PRELAUNCH_TRACE_PATH)',
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


def test_mixed_region_inventory_is_observed_before_volume() -> None:
    for required in (
        "if len(cell_zone_ids) != 1:",
        "cell_zone_names = zone_names_one_way(utilities, cell_zone_ids)",
        "validate_mixed_region_state(",
        '"MIXED_REGION_TYPES_NOT_1_FLUID_12_VOID"',
        '"POST_VOLUME_MAIN_REGION_NAME_MISMATCH',
        "observe_update_regions_argument_menu(",
        "workflow.update_regions.arguments",
        '"update_regions_argument_menu_state"',
    ):
        assert required in SOURCE
    assert "getattr(workflow.update_regions, name)" not in SOURCE


def test_update_regions_reads_generated_argument_menu_only() -> None:
    observe = load_contract_helpers()[
        "observe_update_regions_argument_menu"
    ]

    class Parameter:
        def __init__(self, value):
            self.value = value

        def __call__(self):
            return self.value

    class ArgumentMenu:
        region_current_list = Parameter(["fluid", "dead0"])
        region_current_type_list = Parameter(["fluid", "dead"])
        number_of_listed_regions = Parameter(2)

    assert observe(ArgumentMenu()) == {
        "region_current_list": {
            "read_ok": True,
            "python_type": "list",
            "value": ["fluid", "dead0"],
        },
        "region_current_type_list": {
            "read_ok": True,
            "python_type": "list",
            "value": ["fluid", "dead"],
        },
        "number_of_listed_regions": {
            "read_ok": True,
            "python_type": "int",
            "value": 2,
        },
    }

    class BrokenParameter:
        def __call__(self):
            raise RuntimeError("menu read failed")

    class BrokenMenu:
        region_current_list = BrokenParameter()

    broken = observe(BrokenMenu())
    assert broken["region_current_list"] == {
        "read_ok": False,
        "error_type": "RuntimeError",
        "error": "menu read failed",
    }
    assert broken["region_current_type_list"]["read_ok"] is False
    assert broken["region_current_type_list"]["error_type"] == "AttributeError"
    assert broken["number_of_listed_regions"]["read_ok"] is False


def test_update_regions_argument_menu_calls_are_attributes_not_calls() -> None:
    calls = [
        node
        for node in ast.walk(TREE)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "observe_update_regions_argument_menu"
    ]
    assert len(calls) == 2
    for call in calls:
        assert len(call.args) == 1
        argument = call.args[0]
        assert isinstance(argument, ast.Attribute)
        assert argument.attr == "arguments"
        assert not isinstance(argument.value, ast.Call)
    assert "workflow.update_regions.arguments()" not in SOURCE
    assert "getattr(workflow.update_regions, name)" not in SOURCE


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

#!/usr/bin/env python3
"""Static fail-closed checks for the AirJet ANSYS MCP and approved profiles."""

from __future__ import annotations

import ast
import copy
import hashlib
import json
from pathlib import Path
import os
import stat
import subprocess
import sys
import tempfile
from unittest import mock


SKILL_ROOT = Path(__file__).resolve().parents[1]


def resolve_repo_root() -> Path:
    for candidate in (SKILL_ROOT.parents[1], Path.cwd().resolve()):
        if (
            (candidate / "airjet-simulation" / "automation" / "ansys" / "profiles.json").is_file()
            and (candidate / "codex-skills" / "airjet-ansys-automation").is_dir()
        ):
            return candidate
    raise RuntimeError("AIRJET_REPO_ROOT_NOT_VALIDATED")


REPO = resolve_repo_root()
SERVER = SKILL_ROOT / "scripts" / "airjet_ansys_mcp.py"
POLICY = REPO / "airjet-simulation" / "automation" / "ansys" / "profiles.json"
APPROVED = REPO / "airjet-simulation" / "automation" / "ansys" / "approved"
T0_RUNNER = SKILL_ROOT / "scripts" / "run_t0_suite.py"
T1_CAD_RUNNER = SKILL_ROOT / "scripts" / "run_t1_cad_suite.py"
T1_SEMANTIC_RUNNER = (
    SKILL_ROOT / "scripts" / "run_t1_semantic_reconstruction_suite.py"
)
T1_CONNECTED_RUNNER = (
    SKILL_ROOT / "scripts" / "run_t1_connected_spaceclaim_suite.py"
)
T1_ALTERNATE_RUNNER = (
    SKILL_ROOT / "scripts" / "run_t1_alternate_route_confirmation_suite.py"
)
AJM005_CLOSEOUT_HELPER = SKILL_ROOT / "scripts" / "ajm005_closeout_v2.py"
AJM005_CLOSEOUT_TEST = SKILL_ROOT / "scripts" / "test_ajm005_closeout_v2.py"
AJM005_RUNNER_GUARD = SKILL_ROOT / "scripts" / "test_ajm005_runner_guards.py"
MCP_POLICY_TEST = Path(__file__).resolve()
V2_CONTRACT_ROOT = REPO / "airjet-simulation" / "automation" / "ansys" / "contracts"
V2_ROUTE = V2_CONTRACT_ROOT / "ajm005_alternate_route_v2.json"
V2_JUDGMENT = V2_CONTRACT_ROOT / "ajm005_semantic_judgment_v2.json"
V2_SCHEMA = V2_CONTRACT_ROOT / "semantic_sidecar_v2.schema.json"
V2_VALIDATOR = V2_CONTRACT_ROOT / "semantic_sidecar_v2_contract.py"
V2_CONTRACT_TEST = V2_CONTRACT_ROOT / "test_semantic_sidecar_v2_contract.py"
FULL_PRODUCT_ENGINE = V2_CONTRACT_ROOT / "full_product_semantic_contract_v1.py"
FULL_PRODUCT_SCHEMA = V2_CONTRACT_ROOT / "full_product_semantic_sidecar_v1.schema.json"
FULL_PRODUCT_CORE_TEST = V2_CONTRACT_ROOT / "test_full_product_semantic_contract_v1.py"
FULL_PRODUCT_VARIANT_GENERATOR = V2_CONTRACT_ROOT / "build_full_product_trusted_variants.py"
FULL_PRODUCT_VARIANT_TEST = V2_CONTRACT_ROOT / "test_full_product_trusted_variants.py"
FULL_PRODUCT_CAMPAIGN = V2_CONTRACT_ROOT / "trusted_full_product_gen1" / "campaign.json"
FULL_PRODUCT_REVIEWER = REPO / "airjet-simulation" / "checklists" / "prepare_p1_cad_review.py"
FULL_PRODUCT_REVIEWER_TEST = REPO / "airjet-simulation" / "checklists" / "test_prepare_p1_cad_review_static.py"
V02_TOPOLOGY_RUNNER = REPO / "airjet-simulation" / "automation" / "ansys" / "run_v02_topology_observer_006.py"
V02_TOPOLOGY_RUNNER_TEST = REPO / "airjet-simulation" / "automation" / "ansys" / "test_run_v02_topology_observer_006.py"
V02_NATIVE_TOPOLOGY_RUNNER = REPO / "airjet-simulation" / "automation" / "ansys" / "run_v02_native_topology_observer_006.py"
V02_NATIVE_MESH_RUNNER = REPO / "airjet-simulation" / "automation" / "ansys" / "run_v02_native_mesh_conformality_006.py"
V02_PARASOLID_RUNNER = REPO / "airjet-simulation" / "automation" / "ansys" / "run_v02_parasolid_topology_006.py"
V02_PARASOLID_RUNNER_TEST = REPO / "airjet-simulation" / "automation" / "ansys" / "test_run_v02_parasolid_topology_006.py"
V02_SPLIT_STEP_RUNNER = REPO / "airjet-simulation" / "automation" / "ansys" / "run_v02_split_step_converter_006.py"
V03_CONTINUOUS_RUNNER = REPO / "airjet-simulation" / "automation" / "ansys" / "run_v03_continuous_fluid_006.py"
V03_CONTINUOUS_RUNNER_TEST = REPO / "airjet-simulation" / "automation" / "ansys" / "test_run_v03_continuous_fluid_006.py"
V03_MESH_RUNNER = REPO / "airjet-simulation" / "automation" / "ansys" / "run_v03_continuous_mesh_006.py"
V03_MESH_RUNNER_TEST = REPO / "airjet-simulation" / "automation" / "ansys" / "test_run_v03_continuous_mesh_006.py"
V03_MESH_CONSUMER_TEST = REPO / "airjet-simulation" / "automation" / "ansys" / "test_v03_pyfluent_watertight_mesh_consumer.py"
P2_S0_CONTRACT_TEST = V2_CONTRACT_ROOT / "test_p2_s0_equivalent_plate_v1.py"
P2_S0_PRODUCER_TEST = REPO / "airjet-simulation" / "automation" / "ansys" / "test_p2_s0_equivalent_plate_producer.py"
P2_S0_RUNNER = REPO / "airjet-simulation" / "automation" / "ansys" / "run_p2_s0_equivalent_plate_008.py"
P2_S0_RUNNER_TEST = REPO / "airjet-simulation" / "automation" / "ansys" / "test_run_p2_s0_equivalent_plate_008.py"
T1_PREDECESSOR_NEGATIVE = (
    SKILL_ROOT / "scripts" / "test_t1_predecessor_negative.py"
)


def fail(message: str) -> None:
    print(f"FAIL {message}")
    raise SystemExit(1)


source = SERVER.read_text(encoding="utf-8")
tree = ast.parse(source)
functions = {
    node.name: node
    for node in tree.body
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
}


def module_literal(name: str):
    matches = [
        node.value
        for node in tree.body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == name
    ]
    if len(matches) != 1:
        fail(f"server assignment is not unique: {name}")
    try:
        return ast.literal_eval(matches[0])
    except (TypeError, ValueError) as exc:
        fail(f"server assignment is not literal: {name}: {exc}")


def keyed_dict_values(root: ast.AST, key: str) -> list[ast.AST]:
    values: list[ast.AST] = []
    for candidate in ast.walk(root):
        if not isinstance(candidate, ast.Dict):
            continue
        if len(candidate.keys) != len(candidate.values):
            fail("AST dictionary key/value cardinality mismatch")
        for candidate_key, candidate_value in zip(candidate.keys, candidate.values):
            if isinstance(candidate_key, ast.Constant) and candidate_key.value == key:
                values.append(candidate_value)
    return values


def assert_python39_static_compatibility(path: Path) -> None:
    compatibility_source = path.read_text(encoding="utf-8")
    try:
        compatibility_tree = ast.parse(
            compatibility_source,
            filename=str(path),
            feature_version=9,
        )
    except SyntaxError as exc:
        fail(f"Python 3.9 grammar regression: {path}: {exc}")
    for call in (
        node for node in ast.walk(compatibility_tree) if isinstance(node, ast.Call)
    ):
        if (
            isinstance(call.func, ast.Attribute)
            and call.func.attr == "write_text"
            and any(keyword.arg == "newline" for keyword in call.keywords)
        ):
            fail(f"Python 3.9 Path.write_text newline regression: {path}")
        if (
            isinstance(call.func, ast.Name)
            and call.func.id == "zip"
            and any(keyword.arg == "strict" for keyword in call.keywords)
        ):
            fail(f"Python 3.9 zip strict regression: {path}")
        if (
            isinstance(call.func, ast.Attribute)
            and call.func.attr == "stat"
            and any(keyword.arg == "follow_symlinks" for keyword in call.keywords)
            and not (
                isinstance(call.func.value, ast.Name)
                and call.func.value.id == "os"
            )
        ):
            fail(f"Python 3.9 Path.stat follow_symlinks regression: {path}")


for python39_static_path in (
    SERVER,
    AJM005_CLOSEOUT_TEST,
    AJM005_RUNNER_GUARD,
    MCP_POLICY_TEST,
):
    assert_python39_static_compatibility(python39_static_path)


def parsed_expression(expression: str) -> ast.AST:
    return ast.parse(expression, mode="eval").body


def same_expression(actual: ast.AST, expected: str) -> bool:
    return ast.dump(actual, include_attributes=False) == ast.dump(
        parsed_expression(expected), include_attributes=False
    )


def assert_hash_file_python39_runtime() -> None:
    """Exercise the Python 3.9-safe hash and fail-closed symlink walk paths."""

    namespace = {
        "os": os,
        "stat": stat,
        "hashlib": hashlib,
        "Path": Path,
        "MAX_ARTIFACT_BYTES": 1024 * 1024,
        "MAX_ARTIFACTS": 100,
        "reject_existing_reparse_ancestors": lambda path: None,
        "is_reparse_point": lambda path: False,
    }
    runtime_module = ast.Module(
        body=[copy.deepcopy(functions["hash_file"]), copy.deepcopy(functions["walk_artifacts"])],
        type_ignores=[],
    )
    ast.fix_missing_locations(runtime_module)
    exec(compile(runtime_module, "<python39-hash-file-regression>", "exec"), namespace)
    hash_file_runtime = namespace["hash_file"]
    walk_artifacts_runtime = namespace["walk_artifacts"]
    payload = b"airjet-python39-hash-file\n"
    with tempfile.TemporaryDirectory(prefix="airjet-hash-file-py39-") as temporary:
        root = Path(temporary)
        regular = root / "regular.bin"
        regular.write_bytes(payload)
        size, digest = hash_file_runtime(regular)
        if size != len(payload) or digest != hashlib.sha256(payload).hexdigest():
            fail("Python 3.9 hash_file runtime regression")
        link = root / "link.bin"
        try:
            os.symlink(str(regular), str(link))
            used_real_symlink = True
        except OSError:
            link.write_bytes(payload)
            used_real_symlink = False
        try:
            if used_real_symlink:
                walk_artifacts_runtime(root)
            else:
                original_is_symlink = Path.is_symlink

                def synthetic_is_symlink(path):
                    return path.name == "link.bin" or original_is_symlink(path)

                with mock.patch.object(Path, "is_symlink", synthetic_is_symlink):
                    walk_artifacts_runtime(root)
        except ValueError as exc:
            if str(exc) != "BLOCKED_ARTIFACT_REPARSE_POINT":
                fail("Python 3.9 symlink rejection code changed: " + str(exc))
        else:
            fail("Python 3.9 artifact walk followed a symlink path")


assert_hash_file_python39_runtime()


def subscript_assignments(
    root: ast.AST, container: str, key: str
) -> list[ast.Assign]:
    matches: list[ast.Assign] = []
    for candidate in ast.walk(root):
        if not isinstance(candidate, ast.Assign) or len(candidate.targets) != 1:
            continue
        target = candidate.targets[0]
        if (
            isinstance(target, ast.Subscript)
            and isinstance(target.value, ast.Name)
            and target.value.id == container
            and isinstance(target.slice, ast.Constant)
            and target.slice.value == key
        ):
            matches.append(candidate)
    return matches


tools = {
    node.name
    for node in functions.values()
    if any(
        isinstance(decorator, ast.Call)
        and isinstance(decorator.func, ast.Attribute)
        and decorator.func.attr == "tool"
        for decorator in node.decorator_list
    )
}
expected_tools = {"inventory", "submit_job", "poll_job", "cancel_job", "artifact_manifest"}
if tools != expected_tools:
    fail(f"unexpected MCP tools: {sorted(tools)}")

expected_arguments = {
    "inventory": [],
    "submit_job": ["profile_id", "case_id", "predecessor_job_id"],
    "poll_job": ["job_id"],
    "cancel_job": ["job_id"],
    "artifact_manifest": ["job_id"],
}
for name, arguments in expected_arguments.items():
    actual = [argument.arg for argument in functions[name].args.args]
    if actual != arguments:
        fail(f"unsafe tool arguments for {name}: {actual}")

expected_dependency_git_paths = {
    "ajm005-spaceclaim-cad-t1-v2": (
        "airjet-simulation/automation/ansys/approved/005/spaceclaim_cad_t1.py",
        "airjet-simulation/automation/ansys/contracts/semantic_sidecar_v2_contract.py",
        "airjet-simulation/automation/ansys/contracts/semantic_sidecar_v2.schema.json",
        "airjet-simulation/automation/ansys/contracts/ajm005_semantic_judgment_v2.json",
        "airjet-simulation/automation/ansys/contracts/ajm005_alternate_route_v2.json",
    ),
    "ajm005-workbench-semantic-reconstruction-t1-v2": (
        "airjet-simulation/automation/ansys/approved/005/workbench_semantic_reconstruction_t1.wbjn",
        "airjet-simulation/automation/ansys/contracts/semantic_sidecar_v2_contract.py",
        "airjet-simulation/automation/ansys/contracts/semantic_sidecar_v2.schema.json",
        "airjet-simulation/automation/ansys/contracts/ajm005_semantic_judgment_v2.json",
        "airjet-simulation/automation/ansys/contracts/ajm005_alternate_route_v2.json",
    ),
    "ajm006-spaceclaim-v02-preliminary-v1": (
        "airjet-simulation/automation/ansys/contracts/full_product_semantic_contract_v1.py",
        "airjet-simulation/automation/ansys/contracts/full_product_semantic_sidecar_v1.schema.json",
        "airjet-simulation/automation/ansys/contracts/test_full_product_semantic_contract_v1.py",
        "airjet-simulation/automation/ansys/contracts/build_full_product_trusted_variants.py",
        "airjet-simulation/automation/ansys/contracts/test_full_product_trusted_variants.py",
        "airjet-simulation/parameters/p1_model_form_variants.csv",
        "airjet-simulation/parameters/p1_layout_configuration_matrix.csv",
        "airjet-simulation/parameters/p1_internal_geometry_rules.csv",
        "airjet-simulation/parameters/p1_cad_parameter_map.csv",
        "airjet-simulation/parameters/p1_orifice_pattern_candidates.csv",
        "airjet-simulation/parameters/p1_vent_geometry_candidates.csv",
        "airjet-simulation/parameters/p1_planform_exhaust_candidates.csv",
        "airjet-simulation/parameters/p1_thickness_budget.csv",
        "airjet-simulation/automation/ansys/contracts/trusted_full_product_gen1/campaign.json",
        "airjet-simulation/automation/ansys/contracts/trusted_full_product_gen1/variant_02_m_3x4_7_0_r50_balanced.json",
    ),
    "ajm006-spaceclaim-v03-continuous-throat-pilot-v1": (
        "airjet-simulation/automation/ansys/contracts/full_product_semantic_contract_v1.py",
        "airjet-simulation/automation/ansys/contracts/full_product_semantic_sidecar_v1.schema.json",
        "airjet-simulation/automation/ansys/contracts/test_full_product_semantic_contract_v1.py",
        "airjet-simulation/automation/ansys/contracts/build_full_product_trusted_variants.py",
        "airjet-simulation/automation/ansys/contracts/test_full_product_trusted_variants.py",
        "airjet-simulation/parameters/p1_model_form_variants.csv",
        "airjet-simulation/parameters/p1_layout_configuration_matrix.csv",
        "airjet-simulation/parameters/p1_internal_geometry_rules.csv",
        "airjet-simulation/parameters/p1_cad_parameter_map.csv",
        "airjet-simulation/parameters/p1_orifice_pattern_candidates.csv",
        "airjet-simulation/parameters/p1_vent_geometry_candidates.csv",
        "airjet-simulation/parameters/p1_planform_exhaust_candidates.csv",
        "airjet-simulation/parameters/p1_thickness_budget.csv",
        "airjet-simulation/parameters/full_product_parameter_registry.csv",
        "airjet-simulation/automation/ansys/contracts/v03_finite_throat_route_v1.json",
        "airjet-simulation/automation/ansys/contracts/trusted_full_product_gen1/campaign.json",
        "airjet-simulation/automation/ansys/contracts/trusted_full_product_gen1/variant_02_m_3x4_7_0_r50_balanced.json",
    ),
    "ajm008-spaceclaim-p2-s0-equivalent-plate-v1": (
        "airjet-simulation/automation/ansys/contracts/p2_s0_equivalent_plate_v1.json",
        "airjet-simulation/parameters/p2_s0_equivalent_material_candidates.csv",
        "airjet-simulation/automation/ansys/contracts/trusted_full_product_gen1/variant_02_m_3x4_7_0_r50_balanced.json",
    ),
}
actual_dependency_git_paths = module_literal("PROFILE_DEPENDENCY_GIT_PATHS")
if actual_dependency_git_paths != expected_dependency_git_paths:
    fail("profile dependency Git allowlist changed")
if module_literal("PROFILE_DEPENDENCY_MANIFEST") != "dependency-manifest.json":
    fail("profile dependency manifest name changed")
if module_literal("PROFILE_DEPENDENCY_GIT_PREFIXES") != (
    "airjet-simulation/automation/ansys/",
    "airjet-simulation/parameters/",
):
    fail("profile dependency Git prefixes changed")
if module_literal("MAX_PROFILE_DEPENDENCY_BYTES") != 4 * 1024 * 1024:
    fail("profile dependency file-size limit changed")

sanitized_arguments = [
    argument.arg for argument in functions["sanitized_environment"].args.args
]
expected_sanitized_arguments = [
    "job_dir",
    "profile_id",
    "case_id",
    "predecessor_dir",
    "profile_dependency_dir",
    "git_head",
    "script_sha256",
    "profile_contract_sha256",
]
if sanitized_arguments != expected_sanitized_arguments:
    fail(f"unsafe sanitized_environment arguments: {sanitized_arguments}")

profile_contract_values = keyed_dict_values(
    functions["load_profiles"], "profile_contract_sha256"
)
expected_profile_contract_expression = (
    'sha256_bytes(json.dumps(raw, ensure_ascii=True, sort_keys=True, '
    'separators=(",", ":")).encode("utf-8"))'
)
if len(profile_contract_values) != 1 or not same_expression(
    profile_contract_values[0], expected_profile_contract_expression
):
    fail("profile contract hash is not canonical and commit-bound")

for environment_key, expected_value in {
    "AIRJET_GIT_HEAD": "git_head",
    "AIRJET_SCRIPT_SHA256": "script_sha256",
    "AIRJET_PROFILE_CONTRACT_SHA256": "profile_contract_sha256",
    "PROCESSOR_ARCHITECTURE": '"AMD64"',
    "REMOTING_SERVER_ADDRESS": '"127.0.0.1"',
    "USERNAME": '"admin"',
}.items():
    values = keyed_dict_values(functions["sanitized_environment"], environment_key)
    if len(values) != 1 or not same_expression(values[0], expected_value):
        fail(f"sanitized environment binding changed: {environment_key}")

sanitized_parent_by_node: dict[ast.AST, ast.AST] = {}
for parent in ast.walk(functions["sanitized_environment"]):
    for child in ast.iter_child_nodes(parent):
        sanitized_parent_by_node[child] = parent
dependency_environment_assignments = subscript_assignments(
    functions["sanitized_environment"],
    "environment",
    "AIRJET_PROFILE_DEPENDENCY_DIR",
)
dependency_environment_mentions = [
    node
    for node in ast.walk(functions["sanitized_environment"])
    if isinstance(node, ast.Constant)
    and node.value == "AIRJET_PROFILE_DEPENDENCY_DIR"
]
if (
    len(dependency_environment_assignments) != 1
    or len(dependency_environment_mentions) != 1
    or not same_expression(
        dependency_environment_assignments[0].value,
        "str(profile_dependency_dir)",
    )
):
    fail("profile dependency environment must name only the frozen directory")
dependency_environment_guard = sanitized_parent_by_node.get(
    dependency_environment_assignments[0]
)
if not (
    isinstance(dependency_environment_guard, ast.If)
    and same_expression(
        dependency_environment_guard.test,
        "profile_dependency_dir is not None",
    )
    and dependency_environment_guard.body == dependency_environment_assignments
    and not dependency_environment_guard.orelse
):
    fail("profile dependency environment assignment is not fail-closed")

for function_name, key, expected_value in (
    (
        "inventory",
        "profile_contract_sha256",
        '{profile_id: profile["profile_contract_sha256"] '
        "for profile_id, profile in sorted(profiles.items())}",
    ),
    (
        "submit_job",
        "profile_contract_sha256",
        'profile["profile_contract_sha256"]',
    ),
    ("submit_job", "profile_dependency_artifacts", "[]"),
    ("submit_job", "profile_dependency_manifest_sha256", "None"),
    (
        "prepare_predecessor_input",
        "predecessor_script_sha256",
        'state["script_sha256"]',
    ),
    (
        "prepare_predecessor_input",
        "predecessor_profile_contract_sha256",
        'state["profile_contract_sha256"]',
    ),
):
    values = keyed_dict_values(functions[function_name], key)
    if len(values) != 1 or not same_expression(values[0], expected_value):
        fail(f"commit provenance state binding changed: {function_name}.{key}")

dependency_function = functions.get("prepare_profile_dependencies")
if dependency_function is None:
    fail("profile dependency freezer is missing")
dependency_arguments = [argument.arg for argument in dependency_function.args.args]
if dependency_arguments != ["profile_id", "git_head", "input_dir"]:
    fail(f"unsafe profile dependency freezer arguments: {dependency_arguments}")
dependency_calls = [
    node
    for node in ast.walk(dependency_function)
    if isinstance(node, ast.Call)
]
git_blob_calls = [
    node
    for node in dependency_calls
    if isinstance(node.func, ast.Name) and node.func.id == "read_git_blob"
]
if (
    len(git_blob_calls) != 1
    or len(git_blob_calls[0].args) != 2
    or not same_expression(git_blob_calls[0].args[0], "git_head")
    or not same_expression(git_blob_calls[0].args[1], "git_path")
    or git_blob_calls[0].keywords
):
    fail("profile dependencies must come from the saved verified Git commit")
reparse_calls = [
    node
    for node in dependency_calls
    if isinstance(node.func, ast.Name)
    and node.func.id == "reject_existing_reparse_ancestors"
]
hash_calls = [
    node
    for node in dependency_calls
    if isinstance(node.func, ast.Name) and node.func.id == "hash_file"
]
if len(reparse_calls) < 7 or len(hash_calls) < 3:
    fail("profile dependency freeze lacks reparse or hash revalidation")
dependency_source = ast.get_source_segment(source, dependency_function) or ""
for dependency_invariant in (
    "BLOCKED_PROFILE_DEPENDENCY_CONFIGURATION",
    "BLOCKED_PROFILE_DEPENDENCY_MISSING",
    "BLOCKED_PROFILE_DEPENDENCY_TOO_LARGE",
    "BLOCKED_PROFILE_DEPENDENCY_EXTRA",
    "BLOCKED_PROFILE_DEPENDENCY_COPY_HASH_MISMATCH",
    "BLOCKED_PROFILE_DEPENDENCY_MANIFEST_HASH_MISMATCH",
    "dependency_dir = input_dir / \"dependencies\"",
    "target.chmod(stat.S_IREAD)",
    "manifest_path.chmod(stat.S_IREAD)",
    "if observed_before_manifest != expected_files",
    "if observed_after_manifest != expected_files | {PROFILE_DEPENDENCY_MANIFEST}",
    "return dependency_dir, copied, manifest_sha256",
):
    if dependency_invariant not in dependency_source:
        fail(f"profile dependency freezer lacks invariant: {dependency_invariant}")
for manifest_key, expected_value in {
    "schema_version": "1",
    "profile_id": "profile_id",
    "git_head": "git_head",
    "artifacts": "copied",
}.items():
    values = keyed_dict_values(dependency_function, manifest_key)
    if len(values) != 1 or not same_expression(values[0], expected_value):
        fail(f"profile dependency manifest binding changed: {manifest_key}")

submit_parent_by_node: dict[ast.AST, ast.AST] = {}
for parent in ast.walk(functions["submit_job"]):
    for child in ast.iter_child_nodes(parent):
        submit_parent_by_node[child] = parent
prepare_dependency_calls = [
    node
    for node in ast.walk(functions["submit_job"])
    if isinstance(node, ast.Call)
    and isinstance(node.func, ast.Name)
    and node.func.id == "prepare_profile_dependencies"
]
if (
    len(prepare_dependency_calls) != 1
    or [ast.dump(argument, include_attributes=False) for argument in prepare_dependency_calls[0].args]
    != [
        ast.dump(parsed_expression(expression), include_attributes=False)
        for expression in ("profile_id", "git_head", "input_dir")
    ]
    or prepare_dependency_calls[0].keywords
):
    fail("submit_job does not freeze dependencies from its saved Git head")
prepare_dependency_assignment = submit_parent_by_node.get(
    prepare_dependency_calls[0]
)
expected_dependency_targets = [
    "profile_dependency_dir",
    "profile_dependency_artifacts",
    "profile_dependency_manifest_sha256",
]
if not (
    isinstance(prepare_dependency_assignment, ast.Assign)
    and len(prepare_dependency_assignment.targets) == 1
    and isinstance(prepare_dependency_assignment.targets[0], ast.Tuple)
    and [
        element.id
        for element in prepare_dependency_assignment.targets[0].elts
        if isinstance(element, ast.Name)
    ]
    == expected_dependency_targets
    and len(prepare_dependency_assignment.targets[0].elts)
    == len(expected_dependency_targets)
):
    fail("submit_job does not retain the frozen dependency provenance")
for state_key, expected_value in (
    ("profile_dependency_artifacts", "profile_dependency_artifacts"),
    (
        "profile_dependency_manifest_sha256",
        "profile_dependency_manifest_sha256",
    ),
):
    assignments = subscript_assignments(functions["submit_job"], "state", state_key)
    if len(assignments) != 1 or not same_expression(
        assignments[0].value, expected_value
    ):
        fail(f"submit_job does not persist dependency provenance: {state_key}")

sanitized_calls = [
    node
    for node in ast.walk(functions["submit_job"])
    if isinstance(node, ast.Call)
    and isinstance(node.func, ast.Name)
    and node.func.id == "sanitized_environment"
]
expected_sanitized_call_arguments = (
    "job_dir",
    "profile_id",
    "case_id",
    "predecessor_dir",
    "profile_dependency_dir",
    "git_head",
    'profile["sha256"]',
    'profile["profile_contract_sha256"]',
)
if len(sanitized_calls) != 1:
    fail("submit_job environment is not bound to frozen commit provenance")
sanitized_call = sanitized_calls[0]
if len(sanitized_call.args) != len(expected_sanitized_call_arguments):
    fail("submit_job environment is not bound to frozen commit provenance")
if (
    any(
        not same_expression(actual, expected)
        for actual, expected in zip(
            sanitized_call.args,
            expected_sanitized_call_arguments,
        )
    )
    or sanitized_call.keywords
):
    fail("submit_job environment is not bound to frozen commit provenance")

for node in ast.walk(tree):
    if isinstance(node, ast.Call):
        function_name = ""
        if isinstance(node.func, ast.Name):
            function_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            function_name = node.func.attr
        if function_name in {"system", "popen", "eval", "exec"}:
            fail(f"forbidden dynamic execution API: {function_name}")
        for keyword in node.keywords:
            if keyword.arg == "shell" and not (
                isinstance(keyword.value, ast.Constant) and keyword.value.value is False
            ):
                fail("subprocess shell must be literal false")

if 'return [str(executable), "-I", "-B", str(script)]' not in source:
    fail("Python profiles must use isolated mode")
if "read_git_blob(head" not in source or "verify-commit" not in source:
    fail("approved scripts must come from a verified Git commit blob")
if "BLOCKED_MCP_SERVER_COPY_MISMATCH" not in source or "SERVER_GIT_PATH" not in source:
    fail("installed MCP server must match the verified Git server blob")
if "CREATE_SUSPENDED" not in source or "TerminateJobObject" not in source:
    fail("Windows process-tree containment is missing")
if (
    "CreateEventW" not in source
    or 'MACHINE_JOB_LOCK_NAME = r"Global\\AirJetAnsysAutomation-OneJob"' not in source
    or "BLOCKED_ONE_JOB_AT_A_TIME_CROSS_PROCESS" not in source
):
    fail("cross-process one-job lock is missing")
submit_calls = {
    node.func.id
    for node in ast.walk(functions["submit_job"])
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
}
if "require_runtime_readiness" not in submit_calls:
    fail("submit_job must enforce runtime readiness independently of inventory")
if "prepare_predecessor_input" not in submit_calls:
    fail("submit_job must bind and copy policy-declared predecessor artifacts")
for invariant in (
    "BLOCKED_UNKNOWN_OR_SERVER_RESTARTED_PREDECESSOR",
    "BLOCKED_PREDECESSOR_IDENTITY_MISMATCH",
    "BLOCKED_PREDECESSOR_REPORT_NOT_CAPABILITY_PASS",
    "BLOCKED_PREDECESSOR_MANIFEST_NOT_FROZEN",
    "BLOCKED_PREDECESSOR_FROZEN_HASH_MISMATCH",
    "BLOCKED_PREDECESSOR_COPY_HASH_MISMATCH",
    'environment["AIRJET_PREDECESSOR_DIR"]',
):
    if invariant not in source:
        fail(f"predecessor linkage lacks invariant: {invariant}")

runner_source = T0_RUNNER.read_text(encoding="utf-8")
for invariant in (
    "BLOCKED_T0_RUNNER_COPY_MISMATCH",
    "PASS_CONTROL_SET",
    "NOT_EVALUATED_T0_ONLY",
    "artifact_manifest",
):
    if invariant not in runner_source:
        fail(f"T0 suite runner lacks invariant: {invariant}")

t1_cad_runner_source = T1_CAD_RUNNER.read_text(encoding="utf-8")
for invariant in (
    "BLOCKED_T1_CAD_RUNNER_COPY_MISMATCH",
    "PASS_CAD_TRANSFER_SET",
    "PARTIAL_CAD_TRANSFER_ONLY",
    'WB_PROFILE = "ajm005-workbench-transfer-t1-v1"',
    'case_id = "a5n-" + uuid4().hex[:12]',
    '"input/stagingcopy/spaceclaim_cad_t1.scdocx": "working_native"',
    'declared_path.endswith(',
    '"/" + artifact_path',
    "NATIVE_PARAMETERIZATION_NOT_RUN",
    "predecessor_job_id",
    "artifact_manifest",
    "P1_STAGE_GATE",
):
    if invariant.upper() not in t1_cad_runner_source.upper():
        fail(f"T1 CAD suite runner lacks invariant: {invariant}")
for forbidden in (
    "ajm005-workbench-semantic-reconstruction-t1-v1",
    "PASS_STEP_SEMANTIC_RECONSTRUCTION_DIAGNOSTIC",
):
    if forbidden in t1_cad_runner_source:
        fail(f"native T1 CAD runner must not use semantic route: {forbidden}")

t1_semantic_runner_source = T1_SEMANTIC_RUNNER.read_text(encoding="utf-8")
for invariant in (
    "BLOCKED_T1_SEMANTIC_RUNNER_COPY_MISMATCH",
    "PASS_STEP_SEMANTIC_RECONSTRUCTION_DIAGNOSTIC",
    "NATIVE_PARAMETERIZATION_AND_NATIVE_TRANSFER_NOT_PROVEN",
    "native_named_selection_transfer_claim",
    "spaceclaim_semantic_sidecar.json",
    "p1_p6_gates",
):
    if invariant not in t1_semantic_runner_source:
        fail(f"T1 semantic suite runner lacks invariant: {invariant}")
if "PASS_CAD_TRANSFER_SET" in t1_semantic_runner_source:
    fail("T1 semantic suite must not claim native CAD transfer pass")

t1_connected_runner_source = T1_CONNECTED_RUNNER.read_text(encoding="utf-8")
for invariant in (
    "BLOCKED_T1_CONNECTED_RUNNER_COPY_MISMATCH",
    "PASS_CONNECTED_SPACECLAIM_TRANSFER_DIAGNOSTIC",
    "DIAGNOSTIC_ONLY_NOT_EXTERNAL_NATIVE_TRANSFER",
    'WB_PROFILE = "ajm005-workbench-connected-spaceclaim-t1-v1"',
    'case_id = "a5c-" + uuid4().hex[:12]',
    "EXTERNAL_NATIVE_ATTACH_AND_NATIVE_PARAMETERIZATION_NOT_PROVEN",
    "canonical_claim_boundaries",
    "connected_spaceclaim_entry.sentinel",
    "script_channel_classification",
    "file_runscript_diagnostic_contract_ok",
    "INVALID_DIAGNOSTIC_CONTRACT",
    "artifact_manifest",
    "p1_p6_gates",
):
    if invariant not in t1_connected_runner_source:
        fail(f"T1 connected suite runner lacks invariant: {invariant}")
for forbidden in (
    "PASS_CAD_TRANSFER_SET",
    "PASS_STEP_SEMANTIC_RECONSTRUCTION_DIAGNOSTIC",
):
    if forbidden in t1_connected_runner_source:
        fail(f"T1 connected diagnostic overclaims another route: {forbidden}")

t1_connected_runner_tree = ast.parse(t1_connected_runner_source)
diagnostic_validator_nodes = []
for node in t1_connected_runner_tree.body:
    if isinstance(node, ast.Assign) and any(
        isinstance(target, ast.Name)
        and target.id
        in {
            "FILE_DIAGNOSTIC_FIELDS",
            "FILE_CHECKPOINTS",
            "BUILD_PROBE_CHECKPOINTS",
            "BUILD_CAPTURE_STATES",
            "FILE_CLASSIFICATIONS",
            "FILE_BUILD_STATES",
        }
        for target in node.targets
    ):
        diagnostic_validator_nodes.append(node)
    if isinstance(node, ast.FunctionDef) and node.name == "file_runscript_diagnostic_contract_ok":
        diagnostic_validator_nodes.append(node)
if len(diagnostic_validator_nodes) != 7:
    fail("T1 connected runner file diagnostic validator is not uniquely extractable")
validator_namespace = {}
exec(
    compile(
        ast.fix_missing_locations(
            ast.Module(body=diagnostic_validator_nodes, type_ignores=[])
        ),
        "t1_connected_file_diagnostic_validator",
        "exec",
    ),
    validator_namespace,
)
diagnostic_validator = validator_namespace["file_runscript_diagnostic_contract_ok"]
valid_file_diagnostic_report = {
    "execution_reach": {
        "connected_editor_send_command_control": "SKIPPED_BY_EXPERIMENT",
        "connected_editor_post_send_command_probe": "SKIPPED_BY_EXPERIMENT",
        "connected_editor_run_script": "RETURNED",
        "connected_build_contract": "RETURNED",
    },
    "script_channel_diagnostic": {
        "schema_version": 2,
        "mode": "INTERACTIVE_TRUE_RUNSCRIPT_ONLY",
        "send_command_control": "SKIPPED_BY_EXPERIMENT",
        "entry_expected_size": 34,
        "entry_expected_sha256": (
            "3ee230fb69349453cf2f7f5275879c40423a3462e6d78baadb97237f415cecd7"
        ),
        "runscript_call_outcome": "RETURNED",
        "entry_exact_at_call_checkpoint": True,
        "entry_exact_post_exit": True,
        "entry_exact_failure_pre_cleanup": None,
        "entry_exact_failure_post_cleanup": None,
        "entry_exact_at_freeze": True,
        "entry_first_observed_at": "POST_RUNSCRIPT",
        "entry_invalid_or_partial_at": [],
        "entry_probe_errors_at": [],
        "build_report_probe_errors_at": [],
        "entry_delayed_or_later_observed": False,
        "entry_lost_after_checkpoint": False,
        "build_report_exists_at_freeze": True,
        "build_report_exists_at_capture": None,
        "build_report_capture_state": "NOT_ATTEMPTED",
        "build_report_capture_context": None,
        "build_report_state": "CONTRACT_PASS",
        "classification": "BUILD_CONTRACT_PASS",
        "freeze_probe": "POST_EXIT",
    },
}
if not diagnostic_validator(valid_file_diagnostic_report):
    fail("T1 connected runner rejects valid file-only PASS diagnostic")
valid_call_exception_report = copy.deepcopy(valid_file_diagnostic_report)
valid_call_exception_report["execution_reach"].update(
    {
        "connected_editor_run_script": "CALLED",
        "connected_build_contract": "NOT_REACHED",
    }
)
valid_call_exception_report["script_channel_diagnostic"].update(
    {
        "runscript_call_outcome": "EXCEPTION",
        "entry_exact_at_call_checkpoint": None,
        "entry_exact_post_exit": None,
        "entry_exact_failure_pre_cleanup": False,
        "entry_exact_failure_post_cleanup": False,
        "entry_exact_at_freeze": False,
        "entry_first_observed_at": None,
        "build_report_exists_at_freeze": False,
        "build_report_exists_at_capture": False,
        "build_report_capture_state": "ABSENT",
        "build_report_capture_context": "FAILURE_POST_CLEANUP",
        "build_report_state": "ABSENT",
        "classification": "RUNSCRIPT_CALL_EXCEPTION_ENTRY_ABSENT",
        "freeze_probe": "FAILURE_POST_CLEANUP",
    }
)
if not diagnostic_validator(valid_call_exception_report):
    fail("T1 connected runner rejects valid file-only call exception diagnostic")


def diagnostic_case(diagnostic_updates, reach_updates):
    candidate = copy.deepcopy(valid_file_diagnostic_report)
    candidate["script_channel_diagnostic"].update(diagnostic_updates)
    candidate["execution_reach"].update(reach_updates)
    return candidate


valid_diagnostic_cases = {
    "not reached": diagnostic_case(
        {
            "runscript_call_outcome": "NOT_REACHED",
            "entry_exact_at_call_checkpoint": None,
            "entry_exact_post_exit": None,
            "entry_exact_failure_pre_cleanup": False,
            "entry_exact_failure_post_cleanup": False,
            "entry_exact_at_freeze": False,
            "entry_first_observed_at": None,
            "build_report_exists_at_freeze": False,
            "build_report_state": "ABSENT",
            "classification": "RUNSCRIPT_NOT_REACHED",
            "freeze_probe": "FAILURE_POST_CLEANUP",
        },
        {
            "connected_editor_run_script": "NOT_REACHED",
            "connected_build_contract": "NOT_REACHED",
        },
    ),
    "exception exact": diagnostic_case(
        {
            "runscript_call_outcome": "EXCEPTION",
            "entry_exact_at_call_checkpoint": None,
            "entry_exact_post_exit": None,
            "entry_exact_failure_pre_cleanup": True,
            "entry_exact_failure_post_cleanup": True,
            "entry_exact_at_freeze": True,
            "entry_first_observed_at": "FAILURE_PRE_CLEANUP",
            "build_report_exists_at_freeze": False,
            "build_report_state": "ENTRY_EXACT_BUILD_REPORT_ABSENT",
            "classification": "RUNSCRIPT_CALL_EXCEPTION_ENTRY_EXACT",
            "freeze_probe": "FAILURE_POST_CLEANUP",
        },
        {
            "connected_editor_run_script": "CALLED",
            "connected_build_contract": "NOT_REACHED",
        },
    ),
    "exception delayed": diagnostic_case(
        {
            "runscript_call_outcome": "EXCEPTION",
            "entry_exact_at_call_checkpoint": None,
            "entry_exact_post_exit": None,
            "entry_exact_failure_pre_cleanup": False,
            "entry_exact_failure_post_cleanup": True,
            "entry_exact_at_freeze": True,
            "entry_first_observed_at": "FAILURE_POST_CLEANUP",
            "entry_delayed_or_later_observed": True,
            "build_report_exists_at_freeze": False,
            "build_report_state": "ENTRY_EXACT_BUILD_REPORT_ABSENT",
            "classification": (
                "RUNSCRIPT_CALL_EXCEPTION_ENTRY_DELAYED_OR_CLEANUP_OBSERVED"
            ),
            "freeze_probe": "FAILURE_POST_CLEANUP",
        },
        {
            "connected_editor_run_script": "CALLED",
            "connected_build_contract": "NOT_REACHED",
        },
    ),
    "returned absent": diagnostic_case(
        {
            "entry_exact_at_call_checkpoint": False,
            "entry_exact_post_exit": False,
            "entry_exact_failure_pre_cleanup": False,
            "entry_exact_failure_post_cleanup": False,
            "entry_exact_at_freeze": False,
            "entry_first_observed_at": None,
            "build_report_exists_at_freeze": False,
            "build_report_state": "ABSENT",
            "classification": "RUNSCRIPT_RETURNED_ENTRY_ABSENT",
            "freeze_probe": "FAILURE_POST_CLEANUP",
        },
        {"connected_build_contract": "CALLED"},
    ),
    "returned exact before later failure": diagnostic_case(
        {
            "entry_exact_post_exit": None,
            "entry_exact_failure_pre_cleanup": True,
            "entry_exact_failure_post_cleanup": True,
            "build_report_state": "PRESENT_NOT_VALIDATED",
            "classification": "RUNSCRIPT_RETURNED_ENTRY_EXACT",
            "freeze_probe": "FAILURE_POST_CLEANUP",
        },
        {"connected_build_contract": "NOT_REACHED"},
    ),
    "delayed entry": diagnostic_case(
        {
            "entry_exact_at_call_checkpoint": False,
            "entry_exact_post_exit": True,
            "entry_exact_at_freeze": True,
            "entry_first_observed_at": "POST_EXIT",
            "entry_delayed_or_later_observed": True,
            "build_report_state": "PRESENT_ENTRY_CONTRACT_FAIL",
            "classification": "ENTRY_DELAYED_OR_POST_EXIT_OBSERVED",
        },
        {"connected_build_contract": "CALLED"},
    ),
    "entry lost": diagnostic_case(
        {
            "entry_exact_post_exit": False,
            "entry_exact_failure_pre_cleanup": False,
            "entry_exact_failure_post_cleanup": False,
            "entry_exact_at_freeze": False,
            "entry_lost_after_checkpoint": True,
            "build_report_exists_at_freeze": False,
            "build_report_state": "ABSENT",
            "classification": "ENTRY_LOST_AFTER_CHECKPOINT",
            "freeze_probe": "FAILURE_POST_CLEANUP",
        },
        {"connected_build_contract": "CALLED"},
    ),
    "exact entry report absent": diagnostic_case(
        {
            "entry_exact_failure_pre_cleanup": True,
            "entry_exact_failure_post_cleanup": True,
            "build_report_exists_at_freeze": False,
            "build_report_state": "ENTRY_EXACT_BUILD_REPORT_ABSENT",
            "classification": "ENTRY_EXACT_BUILD_REPORT_ABSENT",
            "freeze_probe": "FAILURE_POST_CLEANUP",
        },
        {"connected_build_contract": "CALLED"},
    ),
    "build report invalid": diagnostic_case(
        {
            "build_report_state": "INVALID_OR_UNREADABLE",
            "classification": "BUILD_REPORT_INVALID",
        },
        {"connected_build_contract": "CALLED"},
    ),
    "build contract fail": diagnostic_case(
        {
            "build_report_state": "CONTRACT_FAIL",
            "classification": "BUILD_CONTRACT_FAIL",
        },
        {"connected_build_contract": "CALLED"},
    ),
    "build probe indeterminate": diagnostic_case(
        {
            "build_report_probe_errors_at": ["POST_EXIT"],
            "entry_exact_failure_pre_cleanup": True,
            "entry_exact_failure_post_cleanup": True,
            "build_report_exists_at_freeze": True,
            "build_report_exists_at_capture": None,
            "build_report_capture_state": "SKIPPED_PRIOR_PROBE_ERROR",
            "build_report_capture_context": "FAILURE_POST_CLEANUP",
            "build_report_state": "PROBE_INDETERMINATE",
            "classification": "PROBE_INDETERMINATE",
            "freeze_probe": "FAILURE_POST_CLEANUP",
        },
        {"connected_build_contract": "CALLED"},
    ),
    "capture exists probe error": diagnostic_case(
        {
            "runscript_call_outcome": "EXCEPTION",
            "entry_exact_at_call_checkpoint": None,
            "entry_exact_post_exit": None,
            "entry_exact_failure_pre_cleanup": False,
            "entry_exact_failure_post_cleanup": False,
            "entry_exact_at_freeze": False,
            "entry_first_observed_at": None,
            "build_report_probe_errors_at": ["BUILD_CAPTURE"],
            "build_report_exists_at_freeze": False,
            "build_report_exists_at_capture": None,
            "build_report_capture_state": "EXISTS_PROBE_ERROR",
            "build_report_capture_context": "FAILURE_POST_CLEANUP",
            "build_report_state": "PROBE_INDETERMINATE",
            "classification": "PROBE_INDETERMINATE",
            "freeze_probe": "FAILURE_POST_CLEANUP",
        },
        {
            "connected_editor_run_script": "CALLED",
            "connected_build_contract": "NOT_REACHED",
        },
    ),
    "late captured build fail after exception": diagnostic_case(
        {
            "runscript_call_outcome": "EXCEPTION",
            "entry_exact_at_call_checkpoint": None,
            "entry_exact_post_exit": None,
            "entry_exact_failure_pre_cleanup": True,
            "entry_exact_failure_post_cleanup": True,
            "entry_exact_at_freeze": True,
            "entry_first_observed_at": "FAILURE_PRE_CLEANUP",
            "build_report_exists_at_freeze": False,
            "build_report_exists_at_capture": True,
            "build_report_capture_state": "PRESENT_VALID_OBJECT",
            "build_report_capture_context": "FAILURE_POST_CLEANUP",
            "build_report_state": "REPORTED_BUILD_FAIL",
            "classification": "RUNSCRIPT_CALL_EXCEPTION_ENTRY_EXACT",
            "freeze_probe": "FAILURE_POST_CLEANUP",
        },
        {
            "connected_editor_run_script": "CALLED",
            "connected_build_contract": "NOT_REACHED",
        },
    ),
}
valid_diagnostic_cases["returned exact late nonfail build"] = diagnostic_case(
    {
        "entry_exact_failure_pre_cleanup": True,
        "entry_exact_failure_post_cleanup": True,
        "build_report_exists_at_freeze": False,
        "build_report_exists_at_capture": True,
        "build_report_capture_state": "PRESENT_VALID_OBJECT",
        "build_report_capture_context": "FAILURE_POST_CLEANUP",
        "build_report_state": "PRESENT_NOT_VALIDATED",
        "classification": "ENTRY_EXACT_BUILD_REPORT_ABSENT",
        "freeze_probe": "FAILURE_POST_CLEANUP",
    },
    {"connected_build_contract": "CALLED"},
)
valid_diagnostic_cases["returned exact late failed build"] = copy.deepcopy(
    valid_diagnostic_cases["returned exact late nonfail build"]
)
valid_diagnostic_cases["returned exact late failed build"][
    "script_channel_diagnostic"
]["build_report_state"] = "REPORTED_BUILD_FAIL"
valid_diagnostic_cases["returned exact late invalid build"] = copy.deepcopy(
    valid_diagnostic_cases["returned exact late nonfail build"]
)
valid_diagnostic_cases["returned exact late invalid build"][
    "script_channel_diagnostic"
].update(
    {
        "build_report_capture_state": "PRESENT_INVALID_OR_UNREADABLE",
        "build_report_state": "INVALID_OR_UNREADABLE",
    }
)
valid_diagnostic_cases["returned absent late failed build"] = diagnostic_case(
    {
        "entry_exact_at_call_checkpoint": False,
        "entry_exact_post_exit": False,
        "entry_exact_failure_pre_cleanup": False,
        "entry_exact_failure_post_cleanup": False,
        "entry_exact_at_freeze": False,
        "entry_first_observed_at": None,
        "build_report_exists_at_freeze": False,
        "build_report_exists_at_capture": True,
        "build_report_capture_state": "PRESENT_VALID_OBJECT",
        "build_report_capture_context": "FAILURE_POST_CLEANUP",
        "build_report_state": "REPORTED_BUILD_FAIL",
        "classification": "RUNSCRIPT_RETURNED_ENTRY_ABSENT",
        "freeze_probe": "FAILURE_POST_CLEANUP",
    },
    {"connected_build_contract": "CALLED"},
)
valid_diagnostic_cases["freeze present capture gone"] = diagnostic_case(
    {
        "entry_exact_failure_pre_cleanup": True,
        "entry_exact_failure_post_cleanup": True,
        "build_report_exists_at_freeze": True,
        "build_report_exists_at_capture": False,
        "build_report_capture_state": "ABSENT",
        "build_report_capture_context": "FAILURE_POST_CLEANUP",
        "build_report_state": "PRESENT_NOT_VALIDATED",
        "classification": "RUNSCRIPT_RETURNED_ENTRY_EXACT",
        "freeze_probe": "FAILURE_POST_CLEANUP",
    },
    {"connected_build_contract": "NOT_REACHED"},
)
valid_diagnostic_cases["historical build probe error recovered absent"] = (
    copy.deepcopy(valid_diagnostic_cases["build probe indeterminate"])
)
valid_diagnostic_cases["historical build probe error recovered absent"][
    "script_channel_diagnostic"
]["build_report_exists_at_freeze"] = False
for captured_absent_case in (
    "not reached",
    "exception exact",
    "exception delayed",
    "returned absent",
    "entry lost",
    "exact entry report absent",
):
    valid_diagnostic_cases[captured_absent_case]["script_channel_diagnostic"].update(
        {
            "build_report_exists_at_capture": False,
            "build_report_capture_state": "ABSENT",
            "build_report_capture_context": "FAILURE_POST_CLEANUP",
        }
    )
valid_diagnostic_cases["returned exact before later failure"][
    "script_channel_diagnostic"
].update(
    {
        "build_report_exists_at_capture": True,
        "build_report_capture_state": "PRESENT_VALID_OBJECT",
        "build_report_capture_context": "FAILURE_POST_CLEANUP",
    }
)
valid_diagnostic_cases["returned exact before later failure"].update(
    {
        "connected_build": {"status": "PASS_CONNECTED_EDITOR_BUILD"},
        "connected_build_capture_context": "FAILURE_POST_CLEANUP",
    }
)
valid_diagnostic_cases["late captured build fail after exception"].update(
    {
        "connected_build": {"status": "FAIL_CONNECTED_EDITOR_BUILD"},
        "connected_build_capture_context": "FAILURE_POST_CLEANUP",
    }
)
valid_diagnostic_cases["capture exists probe error"][
    "connected_build_capture_error"
] = {"context": "FAILURE_POST_CLEANUP"}
valid_diagnostic_cases["returned exact late nonfail build"].update(
    {
        "connected_build": {"status": "PASS_CONNECTED_EDITOR_BUILD"},
        "connected_build_capture_context": "FAILURE_POST_CLEANUP",
    }
)
for late_failed_case in (
    "returned exact late failed build",
    "returned absent late failed build",
):
    valid_diagnostic_cases[late_failed_case].update(
        {
            "connected_build": {"status": "FAIL_CONNECTED_EDITOR_BUILD"},
            "connected_build_capture_context": "FAILURE_POST_CLEANUP",
        }
    )
valid_diagnostic_cases["returned exact late invalid build"][
    "connected_build_parse_error"
] = {"context": "FAILURE_POST_CLEANUP"}
for case_name, candidate in valid_diagnostic_cases.items():
    if not diagnostic_validator(candidate):
        fail("T1 connected runner rejects valid diagnostic case: " + case_name)
for mutation_name, diagnostic_key, mutation_value in (
    ("wrong mode", "mode", "INLINE_AND_FILE"),
    ("wrong skipped state", "send_command_control", "NOT_REACHED"),
    ("PASS without exact entry", "entry_exact_at_call_checkpoint", False),
    ("PASS without build", "build_report_exists_at_freeze", False),
    ("returned with exception class", "classification", "RUNSCRIPT_CALL_EXCEPTION_ENTRY_EXACT"),
):
    mutated = copy.deepcopy(valid_file_diagnostic_report)
    mutated["script_channel_diagnostic"][diagnostic_key] = mutation_value
    if diagnostic_validator(mutated):
        fail("T1 connected runner accepted contradictory diagnostic: " + mutation_name)
mutated = copy.deepcopy(valid_file_diagnostic_report)
mutated["script_channel_diagnostic"]["inline_control_pass_at_checkpoint"] = True
if diagnostic_validator(mutated):
    fail("T1 connected runner accepted removed inline diagnostic field")
contradictory_diagnostics = {}
candidate = copy.deepcopy(valid_diagnostic_cases["not reached"])
candidate["execution_reach"]["connected_editor_run_script"] = "RETURNED"
contradictory_diagnostics["NOT_REACHED with returned reach"] = candidate
candidate = copy.deepcopy(valid_diagnostic_cases["returned absent"])
candidate["script_channel_diagnostic"]["build_report_exists_at_freeze"] = True
contradictory_diagnostics["ABSENT state with existing report"] = candidate
candidate = copy.deepcopy(valid_file_diagnostic_report)
candidate["script_channel_diagnostic"]["entry_invalid_or_partial_at"] = [
    "POST_RUNSCRIPT"
]
contradictory_diagnostics["exact and invalid at one checkpoint"] = candidate
candidate = copy.deepcopy(valid_call_exception_report)
candidate["script_channel_diagnostic"].update(
    {
        "entry_exact_failure_pre_cleanup": True,
        "entry_first_observed_at": "FAILURE_PRE_CLEANUP",
    }
)
contradictory_diagnostics["exception absent with exact pre-cleanup"] = candidate
candidate = copy.deepcopy(valid_file_diagnostic_report)
candidate["script_channel_diagnostic"].update(
    {
        "freeze_probe": "FAILURE_POST_CLEANUP",
        "entry_exact_failure_post_cleanup": True,
    }
)
contradictory_diagnostics["PASS frozen in failure cleanup"] = candidate
candidate = copy.deepcopy(valid_file_diagnostic_report)
candidate["script_channel_diagnostic"].update(
    {
        "build_report_state": "CONTRACT_FAIL",
        "classification": "RUNSCRIPT_RETURNED_ENTRY_EXACT",
    }
)
contradictory_diagnostics["exact classification with failed contract"] = candidate
candidate = copy.deepcopy(valid_call_exception_report)
candidate["script_channel_diagnostic"].update(
    {
        "build_report_exists_at_capture": None,
        "build_report_capture_state": "NOT_ATTEMPTED",
        "build_report_capture_context": None,
    }
)
contradictory_diagnostics["failure freeze without capture attempt"] = candidate
candidate = copy.deepcopy(valid_diagnostic_cases["build probe indeterminate"])
candidate["script_channel_diagnostic"].update(
    {
        "build_report_exists_at_capture": False,
        "build_report_capture_state": "ABSENT",
    }
)
contradictory_diagnostics["prior freeze error with non-skipped capture"] = candidate
candidate = copy.deepcopy(valid_file_diagnostic_report)
candidate["script_channel_diagnostic"].update(
    {
        "build_report_exists_at_capture": True,
        "build_report_capture_state": "PRESENT_VALID_OBJECT",
        "build_report_capture_context": "FAILURE_POST_CLEANUP",
    }
)
contradictory_diagnostics["post-exit freeze with failure capture"] = candidate
candidate = copy.deepcopy(valid_diagnostic_cases["build report invalid"])
candidate["script_channel_diagnostic"].update(
    {
        "entry_exact_at_call_checkpoint": False,
        "entry_first_observed_at": "POST_EXIT",
        "entry_delayed_or_later_observed": True,
    }
)
contradictory_diagnostics["parsed invalid build without immediate entry"] = candidate
candidate = copy.deepcopy(valid_call_exception_report)
candidate["execution_reach"]["connected_build_contract"] = "RETURNED"
contradictory_diagnostics["RunScript exception with returned build contract"] = candidate
candidate = copy.deepcopy(
    valid_diagnostic_cases["returned exact before later failure"]
)
candidate["execution_reach"]["connected_build_contract"] = "RETURNED"
contradictory_diagnostics["capture attempted after returned build contract"] = candidate
candidate = copy.deepcopy(valid_diagnostic_cases["build probe indeterminate"])
candidate["script_channel_diagnostic"].update(
    {
        "build_report_probe_errors_at": ["FAILURE_POST_CLEANUP"],
        "build_report_exists_at_freeze": False,
    }
)
contradictory_diagnostics["current freeze probe error with definite absence"] = candidate
candidate = copy.deepcopy(valid_diagnostic_cases["build probe indeterminate"])
candidate["script_channel_diagnostic"]["build_report_exists_at_freeze"] = None
contradictory_diagnostics["recovered final freeze without existence"] = candidate
candidate = copy.deepcopy(
    valid_diagnostic_cases["returned exact late nonfail build"]
)
del candidate["connected_build"]
contradictory_diagnostics["valid capture without captured object"] = candidate
candidate = copy.deepcopy(
    valid_diagnostic_cases["returned exact late failed build"]
)
candidate["connected_build"]["status"] = "PASS_CONNECTED_EDITOR_BUILD"
contradictory_diagnostics["reported failure with non-fail child status"] = candidate
candidate = copy.deepcopy(
    valid_diagnostic_cases["returned exact late invalid build"]
)
del candidate["connected_build_parse_error"]
contradictory_diagnostics["invalid capture without parse error"] = candidate
for contradiction_name, candidate in contradictory_diagnostics.items():
    if diagnostic_validator(candidate):
        fail(
            "T1 connected runner accepted contradictory diagnostic: "
            + contradiction_name
        )

t1_negative_source = T1_PREDECESSOR_NEGATIVE.read_text(encoding="utf-8")
for invariant in (
    "BLOCKED_REQUIRED_PREDECESSOR_ID",
    "BLOCKED_UNEXPECTED_PREDECESSOR",
    "BLOCKED_UNKNOWN_OR_SERVER_RESTARTED_PREDECESSOR",
    'state.get("phase") != "FAILED_START"',
    'state.get("pid") is not None',
):
    if invariant not in t1_negative_source:
        fail(f"T1 predecessor negative test lacks invariant: {invariant}")

policy = json.loads(POLICY.read_text(encoding="utf-8"))
if set(policy) != {"schema_version", "production_contracts", "profiles"} or policy["schema_version"] != 2:
    fail("invalid profiles root")
production = policy["production_contracts"]
if not isinstance(production, dict) or set(production) != {
    "schema_version", "contract_id", "scope", "product_id",
    "expected_variant_count", "producer_profile_id", "observer_profile_id",
    "execution_state", "p1_p6_gates", "components",
}:
    fail("invalid production contract fields")
if (
    production["schema_version"] != 1
    or production["contract_id"] != "AJM006_GEN1_FULL_PRODUCT_SEMANTIC_PRODUCTION_V1"
    or production["scope"] != "FULL_PRODUCT"
    or production["product_id"] != "AIRJET_MINI_GEN1"
    or production["expected_variant_count"] != 9
    or production["producer_profile_id"] != "ajm006-spaceclaim-full-product-producer-v1"
    or production["observer_profile_id"] != "ajm006-workbench-full-product-observer-v1"
    or production["execution_state"] != "STATIC_CONTRACT_ONLY_NOT_REGISTERED"
    or production["p1_p6_gates"] != "NOT_RUN"
):
    fail("production contract identity changed")
expected_production_components = {
    "full_product_validator": "airjet-simulation/automation/ansys/contracts/full_product_semantic_contract_v1.py",
    "full_product_schema": "airjet-simulation/automation/ansys/contracts/full_product_semantic_sidecar_v1.schema.json",
    "full_product_core_test": "airjet-simulation/automation/ansys/contracts/test_full_product_semantic_contract_v1.py",
    "trusted_variant_generator": "airjet-simulation/automation/ansys/contracts/build_full_product_trusted_variants.py",
    "trusted_variant_test": "airjet-simulation/automation/ansys/contracts/test_full_product_trusted_variants.py",
    "trusted_campaign": "airjet-simulation/automation/ansys/contracts/trusted_full_product_gen1/campaign.json",
}
components = production["components"]
if not isinstance(components, list) or len(components) != len(expected_production_components):
    fail("production component count changed")
production_by_key = {}
for item in components:
    if not isinstance(item, dict) or set(item) != {"contract_key", "git_path", "sha256"}:
        fail("production component fields changed")
    key = item["contract_key"]
    if key in production_by_key:
        fail("duplicate production component key")
    production_by_key[key] = item
if set(production_by_key) != set(expected_production_components):
    fail("production component set changed")
for key, git_path in expected_production_components.items():
    item = production_by_key[key]
    path = REPO / git_path
    if (
        item["git_path"] != git_path
        or not path.is_file()
        or item["sha256"] != hashlib.sha256(path.read_bytes()).hexdigest()
    ):
        fail("production component hash/path differs: " + key)
campaign = json.loads((REPO / expected_production_components["trusted_campaign"]).read_text(encoding="ascii"))
if (
    campaign.get("product_id") != "AIRJET_MINI_GEN1"
    or campaign.get("expected_variant_count") != 9
    or len(campaign.get("variant_contracts", [])) != 9
):
    fail("Gen1 trusted campaign identity changed")
for record in campaign["variant_contracts"]:
    blueprint_path = REPO / record["blueprint_path"]
    if (
        not blueprint_path.is_file()
        or hashlib.sha256(blueprint_path.read_bytes()).hexdigest()
        != record["blueprint_sha256"]
    ):
        fail("trusted blueprint hash differs: " + str(record.get("source_variant_id")))
    blueprint = json.loads(blueprint_path.read_text(encoding="ascii"))
    if (
        blueprint.get("product_id") != "AIRJET_MINI_GEN1"
        or blueprint.get("configuration", {}).get("product_id")
        != "AIRJET_MINI_GEN1"
        or "G2" in json.dumps(blueprint, ensure_ascii=True).upper()
    ):
        fail("non-Gen1 value entered trusted blueprint")
profile_ids: set[str] = set()
for profile in policy["profiles"]:
    required = {
        "profile_id",
        "engine",
        "script",
        "sha256",
        "timeout_seconds",
        "output_root_id",
        "reports",
        "predecessor",
    }
    if set(profile) != required:
        fail(f"invalid fields for profile {profile.get('profile_id')}")
    profile_id = profile["profile_id"]
    if profile_id in profile_ids:
        fail(f"duplicate profile {profile_id}")
    profile_ids.add(profile_id)
    relative = Path(profile["script"])
    if relative.is_absolute() or ".." in relative.parts:
        fail(f"unsafe script path {relative}")
    script = APPROVED / relative
    if not script.is_file():
        fail(f"missing script {relative}")
    digest = hashlib.sha256(script.read_bytes()).hexdigest()
    if digest != profile["sha256"]:
        fail(f"hash mismatch {relative}: expected={profile['sha256']} actual={digest}")
    if not profile["reports"] or any(not item.endswith(".json") for item in profile["reports"]):
        fail(f"invalid declared reports for {profile_id}")

future_dependency_profiles = set(expected_dependency_git_paths)
present_dependency_profiles = future_dependency_profiles & profile_ids
if present_dependency_profiles != future_dependency_profiles:
    fail("all dependency-bearing profiles are mandatory")

expected_profile_ids = {
    "ajm005-spaceclaim-t0-v1",
    "ajm005-workbench-t0-v1",
    "ajm005-pymechanical-t0-v1",
    "ajm005-pyfluent-t0-v1",
    "ajm005-spaceclaim-cad-t1-v1",
    "ajm005-workbench-transfer-t1-v1",
    "ajm005-workbench-semantic-reconstruction-t1-v1",
    "ajm005-workbench-connected-spaceclaim-t1-v1",
    "ajm005-spaceclaim-cad-t1-v2",
    "ajm005-workbench-semantic-reconstruction-t1-v2",
    "ajm006-spaceclaim-v02-preliminary-v1",
    "ajm006-workbench-v02-topology-observer-v1",
    "ajm006-workbench-v02-native-topology-observer-v1",
    "ajm006-workbench-v02-native-mesh-conformality-observer-v1",
    "ajm006-spaceclaim-v02-parasolid-converter-v1",
    "ajm006-spaceclaim-v02-split-step-converter-v1",
    "ajm006-workbench-v02-parasolid-topology-observer-v1",
    "ajm006-spaceclaim-v03-continuous-throat-pilot-v1",
    "ajm006-pyfluent-v03-continuous-mesh-pilot-v1",
    "ajm008-spaceclaim-p2-s0-equivalent-plate-v1",
}
if profile_ids != expected_profile_ids:
    fail(f"approved profile set is not exact: {sorted(profile_ids)}")

for required_path in (
    T1_ALTERNATE_RUNNER,
    V2_ROUTE,
    V2_JUDGMENT,
    V2_SCHEMA,
    V2_VALIDATOR,
    V2_CONTRACT_TEST,
    AJM005_CLOSEOUT_HELPER,
    AJM005_CLOSEOUT_TEST,
    AJM005_RUNNER_GUARD,
    FULL_PRODUCT_ENGINE,
    FULL_PRODUCT_SCHEMA,
    FULL_PRODUCT_CORE_TEST,
    FULL_PRODUCT_VARIANT_GENERATOR,
    FULL_PRODUCT_VARIANT_TEST,
    FULL_PRODUCT_CAMPAIGN,
    FULL_PRODUCT_REVIEWER,
    FULL_PRODUCT_REVIEWER_TEST,
    V02_TOPOLOGY_RUNNER,
    V02_TOPOLOGY_RUNNER_TEST,
    V02_NATIVE_TOPOLOGY_RUNNER,
    V02_NATIVE_MESH_RUNNER,
    V02_PARASOLID_RUNNER,
    V02_PARASOLID_RUNNER_TEST,
    V02_SPLIT_STEP_RUNNER,
    V03_CONTINUOUS_RUNNER,
    V03_CONTINUOUS_RUNNER_TEST,
    V03_MESH_RUNNER,
    V03_MESH_RUNNER_TEST,
    V03_MESH_CONSUMER_TEST,
):
    if not required_path.is_file():
        fail(f"missing mandatory v2 route file: {required_path}")

route = json.loads(V2_ROUTE.read_text(encoding="utf-8"))
judgment = json.loads(V2_JUDGMENT.read_text(encoding="utf-8"))
if route.get("contract_id") != "AJM005_ALTERNATE_ROUTE_V2":
    fail("invalid v2 route contract identity")
if route.get("scope") != "DISPOSABLE_CAPABILITY_FIXTURE_ONLY":
    fail("005 v2 route must remain fixture-only")
if route.get("route") != {
    "cad_authoring": "SPACECLAIM_SIGNED_SCRIPT_PARAMETRIC",
    "solver_handoff": "HASH_BOUND_STEP_SEMANTIC_SIDECAR",
    "connected_route": "DEFERRED_CURRENT_HOST_ROUTE",
    "step_is_route_hard_requirement": True,
}:
    fail("v2 route execution boundary changed")
if route.get("claim_boundaries") != {
    "p1_cad_toolchain_scope": "ALTERNATE_ROUTE_ONLY",
    "external_native_attach": "NOT_PROVEN",
    "native_parameterization": "NOT_PROVEN",
    "native_named_selection_transfer": "NOT_PROVEN",
    "p1_stage_gate": "NOT_RUN",
    "p1_p6_gates": "NOT_RUN",
}:
    fail("v2 route claim boundaries changed")
if route.get("producer", {}).get("required_assertions") != judgment.get(
    "producer_required_assertions"
):
    fail("v2 producer judgment/route assertion sets differ")
if route.get("consumer", {}).get("required_assertions") != judgment.get(
    "consumer_required_assertions"
):
    fail("v2 consumer judgment/route assertion sets differ")
if judgment.get("suite_pass_status") != "PASS_ALTERNATE_ROUTE_SEMANTIC_CONFIRMATION":
    fail("v2 judgment suite status changed")
if route.get("confirmation") != {
    "old_v1_evidence_reusable_for_v2_closeout": False,
    "post_freeze_combined_run_required": True,
    "connected_route_rerun_required": False,
}:
    fail("v2 confirmation policy changed")

by_profile_id = {profile["profile_id"]: profile for profile in policy["profiles"]}
for role, profile_id in (
    ("producer", "ajm005-spaceclaim-cad-t1-v2"),
    ("consumer", "ajm005-workbench-semantic-reconstruction-t1-v2"),
):
    raw_profile = by_profile_id[profile_id]
    profile_contract_sha256 = hashlib.sha256(
        json.dumps(
            raw_profile,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    route_role = route[role]
    if route_role.get("profile_id") != profile_id:
        fail(f"v2 route {role} profile id differs")
    if route_role.get("profile_contract_sha256") != profile_contract_sha256:
        fail(f"v2 route {role} profile contract hash differs")
    if route_role.get("script_sha256") != raw_profile["sha256"]:
        fail(f"v2 route {role} script hash differs")

expected_contract_hashes = {
    "schema_sha256": hashlib.sha256(V2_SCHEMA.read_bytes()).hexdigest(),
    "judgment_sha256": hashlib.sha256(V2_JUDGMENT.read_bytes()).hexdigest(),
    "validator_sha256": hashlib.sha256(V2_VALIDATOR.read_bytes()).hexdigest(),
}
if route.get("contract_hashes") != expected_contract_hashes:
    fail("v2 route contract dependency hashes differ")
if route.get("runner") != {
    "path": "codex-skills/airjet-ansys-automation/scripts/run_t1_alternate_route_confirmation_suite.py",
    "sha256": hashlib.sha256(T1_ALTERNATE_RUNNER.read_bytes()).hexdigest(),
    "guard_test_path": "codex-skills/airjet-ansys-automation/scripts/test_ajm005_runner_guards.py",
    "guard_test_sha256": hashlib.sha256(AJM005_RUNNER_GUARD.read_bytes()).hexdigest(),
}:
    fail("v2 route runner identity differs")
if route.get("closeout") != {
    "helper": {
        "git_path": "codex-skills/airjet-ansys-automation/scripts/ajm005_closeout_v2.py",
        "sha256": hashlib.sha256(AJM005_CLOSEOUT_HELPER.read_bytes()).hexdigest(),
    },
    "test": {
        "git_path": "codex-skills/airjet-ansys-automation/scripts/test_ajm005_closeout_v2.py",
        "sha256": hashlib.sha256(AJM005_CLOSEOUT_TEST.read_bytes()).hexdigest(),
    },
}:
    fail("v2 route closeout supply chain differs")
if route.get("mcp_server") != {
    "path": "codex-skills/airjet-ansys-automation/scripts/airjet_ansys_mcp.py",
    "sha256": hashlib.sha256(SERVER.read_bytes()).hexdigest(),
}:
    fail("v2 route MCP server identity differs")

alternate_source = T1_ALTERNATE_RUNNER.read_text(encoding="utf-8")
for invariant in (
    "PASS_ALTERNATE_ROUTE_SEMANTIC_CONFIRMATION",
    'SC_PROFILE = "ajm005-spaceclaim-cad-t1-v2"',
    'WB_PROFILE = "ajm005-workbench-semantic-reconstruction-t1-v2"',
    "AIRJET_ANSYS_STUDENT_CAPABILITY_SMOKE_005.txt",
    "ALTERNATE_ROUTE_ONLY",
    "DEFERRED_CURRENT_HOST_ROUTE",
    '"native_parameterization"',
    "NOT_PROVEN",
    '"p1_stage_gate"',
    "NOT_RUN",
    "profile_dependency_manifest_sha256",
):
    if invariant not in alternate_source:
        fail(f"alternate route runner lacks invariant: {invariant}")
for forbidden in (
    "PASS_WITH_TRANSFER_LIMITATION",
    "PASS_START_P1_WITH_LIMITATIONS",
    "PASS_CAD_TRANSFER_SET",
    "P1_STAGE_GATE=PASS",
):
    if forbidden in alternate_source:
        fail(f"alternate route runner contains forbidden claim: {forbidden}")
try:
    compile(alternate_source, str(T1_ALTERNATE_RUNNER), "exec")
except SyntaxError as exc:
    fail(f"alternate route runner is invalid: {exc}")

test_environment = dict(os.environ)
test_environment["PYTHONDONTWRITEBYTECODE"] = "1"
contract_test = subprocess.run(
    [sys.executable, "-B", str(V2_CONTRACT_TEST)],
    capture_output=True,
    text=True,
    timeout=30,
    check=False,
    env=test_environment,
)
if (
    contract_test.returncode != 0
    or "AJM005_SEMANTIC_SIDECAR_V2_NEGATIVE_TESTS=PASS" not in contract_test.stdout
    or "real_artifacts=2" not in contract_test.stdout
):
    fail(
        "v2 semantic contract regression failed: "
        + contract_test.stdout
        + contract_test.stderr
    )

for static_test_path, marker in (
    (AJM005_CLOSEOUT_TEST, "AJM005_CLOSEOUT_V2_TESTS=PASS cases=9 fields=99"),
    (AJM005_RUNNER_GUARD, "AJM005_RUNNER_GUARDS=PASS"),
):
    test_python = sys.executable
    if static_test_path == AJM005_RUNNER_GUARD and sys.platform == "win32":
        local_app_data = os.environ.get("LOCALAPPDATA")
        if not local_app_data:
            fail("approved AirJet audit venv root is unavailable")
        approved_python = (
            Path(local_app_data)
            / "AirJetAnsysAutomation" / ".venv" / "Scripts" / "python.exe"
        )
        if not approved_python.is_file():
            fail("approved AirJet audit venv interpreter is missing")
        venv_probe = subprocess.run(
            [
                str(approved_python), "-B", "-c",
                "from importlib.metadata import version; import mcp; "
                "print('MCP=' + version('mcp'))",
            ],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
            env=test_environment,
        )
        if venv_probe.returncode != 0 or venv_probe.stdout.strip() != "MCP=1.28.1":
            fail(
                "approved AirJet audit venv dependency check failed: "
                + venv_probe.stdout
                + venv_probe.stderr
            )
        test_python = str(approved_python)
    static_test = subprocess.run(
        [test_python, "-B", str(static_test_path)],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
        env=test_environment,
    )
    if static_test.returncode != 0 or marker not in static_test.stdout:
        fail(
            "005 closeout supply-chain regression failed: "
            + static_test.stdout
            + static_test.stderr
        )

for command, marker in (
    ([sys.executable, "-B", str(FULL_PRODUCT_CORE_TEST)], "FULL_PRODUCT_SEMANTIC_CONTRACT_V1_TESTS=PASS positive=1 negative=31"),
    ([sys.executable, "-B", str(FULL_PRODUCT_VARIANT_GENERATOR), "--check"], "FULL_PRODUCT_TRUSTED_VARIANTS=PASS product=AIRJET_MINI_GEN1 variants=9 mode=check"),
    ([sys.executable, "-B", str(FULL_PRODUCT_VARIANT_TEST)], "FULL_PRODUCT_TRUSTED_VARIANT_TESTS=PASS product=AIRJET_MINI_GEN1 variants=9"),
    ([sys.executable, "-B", str(FULL_PRODUCT_REVIEWER_TEST)], "P1_REVIEWER_STATIC_TESTS=PASS product=AIRJET_MINI_GEN1 variants=9"),
):
    production_test = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
        env=test_environment,
    )
    if production_test.returncode != 0 or marker not in production_test.stdout:
        fail(
            "full-product production contract regression failed: "
            + production_test.stdout
            + production_test.stderr
        )
if sys.platform == "win32":
    ironpython = Path(r"D:\ansys\ANSYS Inc\ANSYS Student\v261\commonfiles\IronPython\ipy64.exe")
    if not ironpython.is_file():
        fail("approved ANSYS IronPython compatibility interpreter is missing")
    ironpython_test = subprocess.run(
        [str(ironpython), "-X:Frames", str(FULL_PRODUCT_CORE_TEST)],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
        env=test_environment,
    )
    if (
        ironpython_test.returncode != 0
        or "FULL_PRODUCT_SEMANTIC_CONTRACT_V1_TESTS=PASS positive=1 negative=31"
        not in ironpython_test.stdout
    ):
        fail(
            "full-product IronPython compatibility regression failed: "
            + ironpython_test.stdout
            + ironpython_test.stderr
        )

v2_producer_profile = by_profile_id["ajm005-spaceclaim-cad-t1-v2"]
v2_consumer_profile = by_profile_id[
    "ajm005-workbench-semantic-reconstruction-t1-v2"
]
if v2_producer_profile.get("reports") != [
    "spaceclaim_cad_t1.json",
    "spaceclaim_cad_t1_v2.json",
]:
    fail("v2 producer report policy differs")
v2_predecessor = v2_consumer_profile.get("predecessor") or {}
if (
    v2_predecessor.get("profile_id") != "ajm005-spaceclaim-cad-t1-v2"
    or v2_predecessor.get("report") != "spaceclaim_cad_t1_v2.json"
    or v2_predecessor.get("required_probe") != "spaceclaim_cad_t1_v2"
    or v2_predecessor.get("required_status") != "PASS_PARTIAL_CAD_CAPABILITY"
    or v2_predecessor.get("required_assertions")
    != judgment["producer_required_assertions"]
):
    fail("v2 consumer predecessor judgment policy differs")
required_v2_predecessor_artifacts = {
    "spaceclaim_cad_t1.json",
    "spaceclaim_cad_t1_v2.json",
    "spaceclaim_cad_t1.scdocx",
    "spaceclaim_cad_t1.step",
    "spaceclaim_semantic_sidecar.json",
    "spaceclaim_semantic_sidecar_v2.json",
    "spaceclaim_semantic_binding_v2.json",
}
if set(v2_predecessor.get("artifacts", [])) != required_v2_predecessor_artifacts:
    fail("v2 consumer predecessor artifact set differs")

v2_producer_source = (
    APPROVED / v2_producer_profile["script"]
).read_text(encoding="utf-8")
v2_consumer_source = (
    APPROVED / v2_consumer_profile["script"]
).read_text(encoding="utf-8")
for name, wrapper_source in (
    ("producer", v2_producer_source),
    ("consumer", v2_consumer_source),
):
    if 'os.environ["AIRJET_PROFILE_DEPENDENCY_DIR"]' not in wrapper_source:
        fail(f"v2 {name} does not consume frozen dependencies")
    if 'os.environ["AIRJET_REPO_ROOT"]' in wrapper_source:
        fail(f"v2 {name} reads mutable repository dependencies")
    if "verify_dependency_bundle" not in wrapper_source:
        fail(f"v2 {name} lacks dependency manifest revalidation")
    try:
        compile(wrapper_source, f"v2_{name}_wrapper", "exec")
    except SyntaxError as exc:
        fail(f"v2 {name} wrapper is invalid: {exc}")
for invariant in (
    "actual_sources",
    "sha256_file(actual_sources",
    "artifact_hash_checks",
    "detached_sidecar_raw_hash",
    "actual_source_files_hashed",
):
    if invariant not in v2_producer_source:
        fail(f"v2 producer lacks actual artifact invariant: {invariant}")
for invariant in (
    "actual_step_sha256",
    "actual_native_sha256",
    "actual_sidecar_sha256",
    "actual_binding_sha256",
    "normal_at_centroid",
    "direction_matches",
    "observed_owner_by_key",
    "body_surface_coverage_ok",
    "assignment_solution_count",
    "required_negative_codes",
    "artifact_hash_checks",
    "AJM005_V2_COMPUTED_SEMANTIC_OBSERVATION_FAILED",
):
    if invariant not in v2_consumer_source:
        fail(f"v2 consumer lacks computed semantic invariant: {invariant}")
if '"artifact_hash_chain": True' in v2_consumer_source:
    fail("v2 consumer hardcodes artifact hash-chain success")

v02_profile = by_profile_id["ajm006-spaceclaim-v02-preliminary-v1"]
v02_source = (APPROVED / v02_profile["script"]).read_text(encoding="utf-8")
for invariant in (
    'os.environ["AIRJET_PROFILE_DEPENDENCY_DIR"]',
    "verify_dependency_bundle",
    "dependency_manifest_sha256",
    "AJM006_DEPENDENCY_MANIFEST_IDENTITY",
):
    if invariant not in v02_source:
        fail(f"V02 producer lacks frozen dependency invariant: {invariant}")
if 'os.environ["AIRJET_REPO_ROOT"]' in v02_source:
    fail("V02 producer reads mutable repository dependencies")

v03_profile = by_profile_id[
    "ajm006-spaceclaim-v03-continuous-throat-pilot-v1"
]
if (
    v03_profile.get("engine") != "spaceclaim"
    or v03_profile.get("script") != "006/v03_continuous_fluid_producer.py"
    or v03_profile.get("timeout_seconds") != 7200
    or v03_profile.get("output_root_id") != "p1_cad_006"
    or v03_profile.get("reports")
    != ["v03_continuous_fluid_producer.json"]
    or v03_profile.get("predecessor") is not None
):
    fail("V03 continuous-fluid profile contract changed")
v03_source_path = APPROVED / v03_profile["script"]
v03_source = v03_source_path.read_text(encoding="utf-8")
v03_tree = ast.parse(v03_source)
v03_assignments = {
    node.targets[0].id: ast.literal_eval(node.value)
    for node in v03_tree.body
    if isinstance(node, ast.Assign)
    and len(node.targets) == 1
    and isinstance(node.targets[0], ast.Name)
    and node.targets[0].id in {"assertion_names", "DEPENDENCY_NAMES"}
}
if len(v03_assignments.get("assertion_names", ())) != 17:
    fail("V03 assertion contract count changed")
if len(v03_assignments.get("DEPENDENCY_NAMES", ())) != 17:
    fail("V03 dependency contract count changed")
for invariant in (
    'os.environ["AIRJET_PROFILE_DEPENDENCY_DIR"]',
    "verify_dependency_bundle",
    '"value_mm": 0.10',
    '"evidence_class": "C"',
    '"product_fact": False',
    '"ORIFICE_THROAT_WALL": 972',
    'len(built_bodies) != 1',
    '"volume_tolerance_native_mm3"',
    'continuous_route_ok = fingerprint_matches_route(',
    'native_analytic_volume_delta_mm3',
    'set(throat_counts_by_cell.values()) == set([81])',
    '"mesh": "NOT_RUN"',
    '"physics": "NOT_RUN"',
    '"p1_p6_gates": "NOT_RUN"',
    '"formal_006_completion": False',
    "compact_throat_inventory",
    "expected_xy_contract",
):
    if invariant not in v03_source:
        fail("V03 continuous-fluid producer lacks invariant: " + invariant)
for forbidden in (
    'os.environ["AIRJET_REPO_ROOT"]',
    "GenerateMesh(",
    ".Solve(",
    "launch_fluent(",
):
    if forbidden in v03_source:
        fail("V03 continuous-fluid producer contains forbidden action: " + forbidden)
v03_runner_source = V03_CONTINUOUS_RUNNER.read_text(encoding="utf-8")
v03_runner_tree = ast.parse(v03_runner_source)
v03_runner_literals = {
    node.targets[0].id: ast.literal_eval(node.value)
    for node in v03_runner_tree.body
    if isinstance(node, ast.Assign)
    and len(node.targets) == 1
    and isinstance(node.targets[0], ast.Name)
    and node.targets[0].id in {
        "PROFILE_ID",
        "PROFILE_SCRIPT_SHA256",
        "PROFILE_SCRIPT",
        "EXPECTED_REPORT_ASSERTIONS",
        "EXPECTED_PRODUCER_ARTIFACTS",
        "EXPECTED_DEPENDENCY_COUNT",
    }
}
if (
    v03_runner_literals.get("PROFILE_ID") != v03_profile["profile_id"]
    or v03_runner_literals.get("PROFILE_SCRIPT") != v03_profile["script"]
    or v03_runner_literals.get("PROFILE_SCRIPT_SHA256")
    != v03_profile["sha256"]
    or "PLACEHOLDER" in str(v03_runner_literals.get("PROFILE_SCRIPT_SHA256"))
    or len(v03_runner_literals.get("EXPECTED_REPORT_ASSERTIONS", ())) != 17
    or len(v03_runner_literals.get("EXPECTED_PRODUCER_ARTIFACTS", {})) != 7
    or v03_runner_literals.get("EXPECTED_DEPENDENCY_COUNT") != 17
):
    fail("V03 runner/profile binding changed")
for path in (V03_CONTINUOUS_RUNNER, V03_CONTINUOUS_RUNNER_TEST):
    assert_python39_static_compatibility(path)

v03_mesh_profile = by_profile_id[
    "ajm006-pyfluent-v03-continuous-mesh-pilot-v1"
]
v03_mesh_source_path = APPROVED / v03_mesh_profile["script"]
if (
    v03_mesh_profile.get("engine") != "pyfluent"
    or v03_mesh_profile.get("script")
    != "006/v03_pyfluent_watertight_mesh_consumer.py"
    or v03_mesh_profile.get("timeout_seconds") != 7200
    or v03_mesh_profile.get("output_root_id") != "p1_cad_006"
    or v03_mesh_profile.get("reports")
    != ["v03_pyfluent_watertight_mesh_consumer.json"]
    or not isinstance(v03_mesh_profile.get("predecessor"), dict)
    or v03_mesh_profile["predecessor"].get("profile_id")
    != "ajm006-spaceclaim-v03-continuous-throat-pilot-v1"
    or v03_mesh_profile["predecessor"].get("report")
    != "v03_continuous_fluid_producer.json"
    or v03_mesh_profile["predecessor"].get("required_probe")
    != "v03_continuous_fluid_producer"
    or v03_mesh_profile["predecessor"].get("required_status")
    != "PASS_PARTIAL_CAD_CAPABILITY"
    or len(v03_mesh_profile["predecessor"].get("required_assertions") or [])
    != 17
    or v03_mesh_profile["predecessor"].get("artifacts")
    != [
        "v03_continuous_fluid_producer.json",
        "product_continuous_fluid.scdocx",
        "product_continuous_fluid.step",
        "v03_native_reopen.json",
        "v03_step_reimport.json",
        "v03_throat_inventory.json",
        "v03_source_chain.json",
    ]
):
    fail("V03 PyFluent mesh profile contract changed")
if hashlib.sha256(v03_mesh_source_path.read_bytes()).hexdigest() != v03_mesh_profile.get("sha256"):
    fail("V03 PyFluent mesh script hash differs")
if actual_dependency_git_paths.get(v03_mesh_profile["profile_id"]) is not None:
    fail("V03 PyFluent consumer must not receive repository dependencies")
v03_mesh_source = v03_mesh_source_path.read_text(encoding="utf-8")
for invariant in (
    "FluentVersion.v261",
    "FluentMode.MESHING",
    "processor_count=1",
    "THROAT_COUNT = 972",
    "STUDENT_ENTITY_LIMIT = 1_000_000",
    "session.tui.report.mesh_size()",
    "session.tui.file.write_mesh(str(MESH_PATH))",
    "workflow.import_geometry.file_name = str(STAGED_NATIVE_PATH)",
    '"NATIVE_IMPORT_FACE_ZONE_COUNT_NOT_1078:{}"',
    "session.tui.boundary.separate.sep_face_zone_by_region([inlet_name])",
    '"POST_SURFACE_INLET_SPLIT_COUNT_NOT_4"',
    '"PREDECESSOR_NATIVE_EVIDENCE_INVALID"',
    '"exact_native_and_step_byte_staging"',
    '"ROUND_TRIP_CORROBORATION_NOT_MESH_SOURCE"',
    '"physics": "NOT_RUN"',
    '"solver_iterations": 0',
):
    if invariant not in v03_mesh_source:
        fail("V03 PyFluent consumer lacks invariant: " + invariant)
for forbidden in ("switch_to_solver", "additional_arguments=", ".iterate("):
    if forbidden in v03_mesh_source:
        fail("V03 PyFluent consumer contains forbidden action: " + forbidden)

# C5 is a full-observation contract.  The earlier diagnostic admitted either
# twelve anchor queries or all 972 throat queries; that fallback is no longer
# evidence for the connected-volume mesh claim.  Reject the semantic shape of
# that fallback rather than relying on its current whitespace or spelling.
v03_mesh_runner_tree = ast.parse(
    V03_MESH_RUNNER.read_text(encoding="utf-8"),
    filename=str(V03_MESH_RUNNER),
)
for comparison in (
    node for node in ast.walk(v03_mesh_runner_tree)
    if isinstance(node, ast.Compare)
):
    comparison_names = {
        node.id for node in ast.walk(comparison) if isinstance(node, ast.Name)
    }
    comparison_sets = []
    for candidate in ast.walk(comparison):
        if not isinstance(candidate, ast.Set):
            continue
        try:
            comparison_sets.append({ast.literal_eval(item) for item in candidate.elts})
        except (TypeError, ValueError):
            continue
    if (
        "executed_queries" in comparison_names
        and {12, 972} in comparison_sets
    ):
        fail("V03 C5 runner still admits the obsolete 12-or-972 query fallback")

v03_mesh_runner_source = V03_MESH_RUNNER.read_text(encoding="utf-8")
for invariant in (
    '"throat_occupancy_query_scope"',
    '"throat_occupancy_executed_query_count"',
    '"throat_occupancy_hit_count"',
    '"throat_occupancy_miss_count"',
    '"throat_occupancy_raw_none_count"',
    '"throat_occupancy_first_miss_indices"',
    '"throat_occupancy_zone_counts"',
    '"throat_occupancy_unique_owner_per_query"',
    '"throat_occupancy_all_hits_in_accepted_flow_zone"',
    '"anchor_zone_ids"',
    '"anchor_occupancy_ok"',
    '"actuator_gap_probe_count"',
    '"actuator_gap_hit_count"',
    '"actuator_gap_raw_none_count"',
    '"actuator_gap_exclusion_evaluable"',
    '"actuator_gap_zones_excluded"',
    '"pre_update_region_inventory"',
    '"post_update_region_inventory"',
    '"main_flow_region_count"',
    '"non_flow_region_count"',
    '"FULL_972"',
):
    if invariant not in v03_mesh_runner_source:
        fail("V03 C5 runner lacks fail-closed evidence invariant: " + invariant)

# Require the producer-side observation to be computed from all queries and
# from the actual post-mesh Fluent cell-zone APIs.  The route must describe
# fluid-only geometry and must never invoke Create/Update Regions, whose void
# semantics previously selected an actuator pocket instead of the main flow.
for invariant in (
    "validate_full_throat_occupancy(",
    '"occupancy_mode": "FULL_972"',
    '"executed_queries": THROAT_COUNT',
    '"miss_count": 0',
    '"raw_none_count": 0',
    '"unique_owner_per_query": True',
    '"all_hits_belong_to_the_single_accepted_flow_cell_zone": True',
    "validate_actuator_gap_exclusion(",
    '"actuator_gap_probe_count": ACTUATOR_GAP_PROBE_COUNT',
    '"actuator_gap_hit_count": 0',
    '"actuator_gap_raw_none_count": ACTUATOR_GAP_PROBE_COUNT',
    '"actuator_gap_zones_excluded": True',
    '"actuator_gap_exclusion_evaluable": actuator_gap_exclusion_evaluable',
    '"throat_occupancy_first_miss_indices"',
    '"The geometry consists of only fluid regions with no voids"',
    "workflow.describe_geometry.setup_type = FLUID_ONLY_SETUP_TYPE",
    "setup_type=FLUID_ONLY_SETUP_TYPE",
    'cell_zone_raw = list(utilities.get_cell_zones(filter="*"))',
    'cell_zone_types = {',
    'utilities.get_zone_type(zone_id=zone_id)',
    'if any(value != "fluid" for value in cell_zone_types.values()):',
    'if len(cell_zone_ids) != 1:',
    'cell_zone_names = zone_names_one_way(utilities, cell_zone_ids)',
    '"workflow.describe_geometry.setup_type"',
    '"utilities.get_cell_zones"',
    '"utilities.get_zone_type"',
    '"meshing_utilities.convert_zone_ids_to_name_strings"',
    '"route": "REVERSED_BOUNDARY_FLUID_OBJECT"',
    "session.tui.boundary.manage.flip(imported_face_zone_names)",
    '"imported_boundary_normals_reversed"',
    "utilities.set_object_cell_zone_type(",
    'object_name=mesh_object_name, cell_zone_type="fluid"',
    'not name.startswith("origin-")',
    'f"origin-{mesh_object_candidates[0]}" not in mesh_objects',
    "len(mesh_objects) != 2",
    '"fluid_object_cell_zone_type_selected"',
    '"main_flow_region_count": 1',
    '"non_flow_region_count": 0',
    'actuator_gap_exclusion_evaluable = "error" not in actuator_gap_exclusion',
    'actuator_gap_exclusion.get("actuator_gap_zones_excluded") is True',
    'throat_occupancy_evaluable = "error" not in occupancy_contract',
    'occupancy_contract.get("executed_queries") == THROAT_COUNT',
    'occupancy_contract.get("hit_count") == THROAT_COUNT',
):
    if invariant not in v03_mesh_source:
        fail("V03 C5 consumer lacks computed occupancy/region invariant: " + invariant)
if "passthrough" in v03_mesh_source or "passthrough" in v03_mesh_runner_source:
    fail("V03 C5 runtime reintroduced forbidden region passthrough")
for forbidden in (
    "workflow.create_regions",
    "workflow.update_regions",
    "number_of_flow_volumes",
    '"The geometry consists of both fluid and solid regions and/or voids"',
    "REGION_INVENTORY_FIELD_PAIRS",
    "NON_FLOW_REGION_TYPES",
    "parse_region_inventory(",
    "validate_region_transition(",
    "NOT_1_FLOW_11_NON_FLOW",
    "session.tui.material_point",
    "session.tui.objects.volumetric_regions",
):
    if forbidden in v03_mesh_source:
        fail("V03 C5 consumer reintroduced obsolete mixed/void route: " + forbidden)
for forbidden in (
    "actuator_gap_exclusion_evaluable = True",
    "actuator_gap_zones_excluded = True",
    'and result["assertions"]["actuator_gap_exclusion"]',
    'and actuator_gap_exclusion["actuator_gap_zones_excluded"]',
    'result["assertions"]["throat_occupancy_full_972"] = True',
    'and result["assertions"]["throat_occupancy_full_972"]',
):
    if forbidden in v03_mesh_source:
        fail("V03 C5 consumer contains false actuator-gap evidence: " + forbidden)

v03_mesh_consumer_test_source = V03_MESH_CONSUMER_TEST.read_text(
    encoding="utf-8"
)
v03_mesh_consumer_test_tree = ast.parse(
    v03_mesh_consumer_test_source,
    filename=str(V03_MESH_CONSUMER_TEST),
)
consumer_guard_names = {
    node.name
    for node in v03_mesh_consumer_test_tree.body
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
}
for guard_name in (
    "test_full_972_occupancy_pure_contract",
    "test_actuator_gap_exclusion_pure_contract",
    "test_actuator_gap_failure_stays_truthful_and_does_not_block_mesh_write",
    "test_throat_occupancy_failure_stays_truthful_and_does_not_block_mesh_write",
    "test_mesh_size_parser_accepts_frozen_v261_summary",
    "test_fluid_only_region_route_is_explicit_and_ordered",
    "test_fluid_only_inventory_is_observed_from_actual_cell_zone",
):
    if guard_name not in consumer_guard_names:
        fail("V03 C5 consumer regression guard missing: " + guard_name)
for invariant in (
    '"occupancy_mode": "FULL_972"',
    '"executed_queries": 972',
    '"hit_count": 972',
    '"miss_count": 0',
    '"raw_none_count": 0',
    '"unique_owner_per_query": True',
    '"all_hits_belong_to_the_single_accepted_flow_cell_zone": True',
    "records[:12]",
    'marker="QUERY_COUNT_NOT_972"',
    'marker="NOT_FULL_SINGLE_OWNER"',
    'marker="RAW_NONE_NOT_BOOLEAN"',
    'marker="ACCEPTED_FLOW_ZONE_NOT_UNIQUE"',
    '"actuator_gap_probe_count": 12',
    '"actuator_gap_hit_count": 0',
    '"actuator_gap_raw_none_count": 12',
    '"actuator_gap_zones_excluded": True',
    '"The geometry consists of only fluid regions with no voids"',
    '"workflow.describe_geometry.setup_type"',
    '"utilities.get_cell_zones"',
    '"utilities.get_zone_type"',
    '"meshing_utilities.convert_zone_ids_to_name_strings"',
    '"non_flow_region_count": 0',
    '"workflow.create_regions"',
    '"workflow.update_regions"',
    "MESH_STATS_V261_SUMMARY_INCOMPLETE_OR_DUPLICATE",
    "assert parse(frozen) == (35108, 239073, 242139, 1)",
):
    if invariant not in v03_mesh_consumer_test_source:
        fail("V03 C5 consumer negative/positive coverage missing: " + invariant)

# Once submit_job returns, evidence must be persisted before validation and
# every stage must be protected by cancellation.  The pure spies are mandatory
# so this policy does not mistake source markers alone for exercised guards.
v03_mesh_runner_test_source = V03_MESH_RUNNER_TEST.read_text(encoding="utf-8")
v03_mesh_runner_test_tree = ast.parse(
    v03_mesh_runner_test_source,
    filename=str(V03_MESH_RUNNER_TEST),
)
runner_guard_names = {
    node.name
    for node in v03_mesh_runner_test_tree.body
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
}
for guard_name in (
    "test_preflight_block_has_zero_stdio_submit_and_child_calls",
    "test_stage1_post_submit_failure_persists_partial_and_cancels",
    "test_stage2_post_submit_failure_preserves_stage1_and_cancels",
    "test_reached_terminal_malformed_manifest_is_fail_not_not_run",
    "test_consumer_assertion_contract_includes_c5_hard_gates",
    "test_consumer_mesh_evidence_literal_keys_match_runner_fixture",
    "test_submit_identity_and_contract_hashes_fail_closed",
):
    if guard_name not in runner_guard_names:
        fail("V03 C5 runner cancellation regression guard missing: " + guard_name)
for invariant in (
    "def persist_result(",
    "async def cancel_submitted_job(",
    "async def run_submitted_stages(",
    '"submitted": True',
    '"capability_status": "FAIL"',
    "stage1_complete = False",
    "stage2_complete = False",
    "finally:",
    "await cancel_submitted_job(session, result[\"stage1\"])",
    "await cancel_submitted_job(session, result[\"stage2\"])",
    "validate_profile_contracts(",
    "validate_stage1_submit_identity(",
    "validate_stage2_submit_identity(",
    'state.get("script_sha256") == stage1.PROFILE_SCRIPT_SHA256',
    'state.get("script_sha256") == CONSUMER_SCRIPT_SHA256',
    "CONSUMER_PREDECESSOR_ARTIFACTS_DUPLICATE_OR_INVALID",
    "BLOCKED_PROFILE_CONTRACT_HASHES_INVALID",
    'if set(profile) != set(expected):',
    'not 0.0 < float(evidence["min_orthogonal_quality"]) <= 1.0',
    'evidence.get("post_volume_throat_zone_count") != 1',
    'evidence.get("throat_zone_count") != 1',
):
    if invariant not in v03_mesh_runner_source:
        fail("V03 C5 runner lacks partial/cancel invariant: " + invariant)
if 'contracts[profile_id] == "0" * 64' not in v03_mesh_runner_source:
    fail("V03 C5 runner does not reject zero profile-contract hashes")
for forbidden in (
    'result[pid] = "0" * 64',
    'stage1.PROFILE_ID: "0" * 64',
    "PROFILE_COUNT_WARNING",
    "PROFILE_WARNING",
    "BLOB_HASH_WARNING",
    "INVENTORY_WARNING",
):
    if forbidden in v03_mesh_runner_source:
        fail("V03 C5 runner contains forbidden profile-contract zero-hash fallback")
for invariant in (
    'counts == {"stdio": 0, "submit": 0, "child": 0}',
    '["submit_job", "cancel_job"]',
    '"submit_job", "artifact_manifest", "submit_job", "cancel_job"',
    'saved["stage1"]["capability_status"] == "FAIL"',
    'saved["stage2"]["capability_status"] == "FAIL"',
    'saved["stage2"]["capability_status"] == "NOT_RUN"',
    '["cancellation"]["confirmed_terminal"] is True',
    "for invalid_quality in (-1.0, 0.0, 1.01):",
    '("script_sha256", "0" * 64)',
):
    if invariant not in v03_mesh_runner_test_source:
        fail("V03 C5 runner spy coverage missing: " + invariant)
for path in (
    V03_MESH_RUNNER,
    V03_MESH_RUNNER_TEST,
    V03_MESH_CONSUMER_TEST,
    v03_mesh_source_path,
):
    assert_python39_static_compatibility(path)

p2_s0_profile = by_profile_id[
    "ajm008-spaceclaim-p2-s0-equivalent-plate-v1"
]
p2_s0_source_path = APPROVED / p2_s0_profile["script"]
if (
    p2_s0_profile.get("engine") != "spaceclaim"
    or p2_s0_profile.get("script")
    != "008/p2_s0_equivalent_plate_producer.py"
    or p2_s0_profile.get("timeout_seconds") != 900
    or p2_s0_profile.get("output_root_id") != "p2_structural_008"
    or p2_s0_profile.get("reports")
    != ["p2_s0_equivalent_plate_producer.json"]
    or p2_s0_profile.get("predecessor") is not None
):
    fail("P2 S0 equivalent-plate producer profile contract changed")
if (
    hashlib.sha256(p2_s0_source_path.read_bytes()).hexdigest()
    != p2_s0_profile.get("sha256")
):
    fail("P2 S0 equivalent-plate producer script hash differs")
p2_s0_source = p2_s0_source_path.read_text(encoding="utf-8")
for invariant in (
    'os.environ["AIRJET_PROFILE_DEPENDENCY_DIR"]',
    "verify_dependency_bundle",
    '"p2_s0_equivalent_plate_v1.json"',
    '"p2_s0_equivalent_material_candidates.csv"',
    '"variant_02_m_3x4_7_0_r50_balanced.json"',
    "Combine.Merge(",
    '"NS_ANCHOR_FIXED": 1',
    '"step_named_selection_transfer": "NOT_ASSUMED"',
    '"formal_p2_completion": False',
    '"p2_stage_gate": "NOT_RUN"',
    '"mechanical": "NOT_RUN"',
    '"modal": "NOT_RUN"',
    '"harmonic": "NOT_RUN"',
    '"status"] = "PASS_PARTIAL_CAD_CAPABILITY"',
):
    if invariant not in p2_s0_source:
        fail("P2 S0 equivalent-plate producer lacks invariant: " + invariant)
for forbidden in (
    'os.environ["AIRJET_REPO_ROOT"]',
    "PASS_P2_GATE",
    "launch_fluent(",
    "pymechanical",
):
    if forbidden in p2_s0_source:
        fail("P2 S0 equivalent-plate producer contains forbidden action: " + forbidden)
for path in (
    p2_s0_source_path,
    P2_S0_CONTRACT_TEST,
    P2_S0_PRODUCER_TEST,
    P2_S0_RUNNER,
    P2_S0_RUNNER_TEST,
):
    assert_python39_static_compatibility(path)
for test_path, success_token in (
    (P2_S0_CONTRACT_TEST, "AJM_P2_S0_EQUIVALENT_PLATE_CONTRACT=PASS_ALL"),
    (P2_S0_PRODUCER_TEST, "AJM_P2_S0_EQUIVALENT_PLATE_PRODUCER_GUARDS=PASS_ALL"),
    (P2_S0_RUNNER_TEST, "AJM_P2_S0_EQUIVALENT_PLATE_RUNNER_GUARDS=PASS_ALL"),
):
    completed = subprocess.run(
        [sys.executable, "-B", str(test_path)],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
        env=test_environment,
    )
    if completed.returncode != 0 or success_token not in completed.stdout:
        fail("P2 S0 static regression failed: " + str(test_path))

v02_observer_profile = by_profile_id[
    "ajm006-workbench-v02-topology-observer-v1"
]
v02_observer_source = (
    APPROVED / v02_observer_profile["script"]
).read_text(encoding="utf-8")
v02_observer_predecessor = v02_observer_profile.get("predecessor")
if (
    not isinstance(v02_observer_predecessor, dict)
    or v02_observer_predecessor.get("profile_id")
    != "ajm006-spaceclaim-v02-preliminary-v1"
    or set(v02_observer_predecessor.get("artifacts") or [])
    != {
        "v02_preliminary_producer.json",
        "product.step",
        "v02_face_inventory.json",
        "native_reopen.json",
        "step_reimport.json",
    }
):
    fail("V02 topology observer predecessor contract changed")
for invariant in (
    'os.environ["AIRJET_PREDECESSOR_DIR"]',
    "predecessor-manifest.json",
    "predecessor_final_recheck",
    "GetGeometryFileAndSaveData",
    "model_container.Refresh()",
    'model_container.SendCommand(Language="Python", Command=model_script)',
    "ExtAPI.DataModel.GeoData",
    "GetBoundingBox",
    '"Body", "Bodies", "Parent", "AdjacentBodies"',
    "expected_orifice_xy_keys",
    "972_SHARED_SINGLE_FACE",
    "972_COINCIDENT_FACE_PAIRS",
    "DOWNSTREAM_HEALED_SINGLE_FACE",
    "MIXED_OR_OTHER",
    "UPSTREAM_ORIFICE_GEOMETRY_LOST_DOWNSTREAM_972_IMPRINTS_RETAINED",
    "PERSISTED_BODY_NAME",
    '"formal_006_completion": False',
    '"p1_stage_gate": "NOT_RUN"',
    '"p1_p6_gates": "NOT_RUN"',
    "NOT_EVALUATED_NO_MESH",
):
    if invariant not in v02_observer_source:
        fail("V02 topology observer lacks invariant: " + invariant)

v02_native_observer_profile = by_profile_id[
    "ajm006-workbench-v02-native-topology-observer-v1"
]
v02_native_predecessor = v02_native_observer_profile.get("predecessor")
if (
    v02_native_observer_profile.get("script")
    != "006/v02_preliminary_topology_observer.wbjn"
    or v02_native_observer_profile.get("reports")
    != ["v02_native_topology_observer.json"]
    or not isinstance(v02_native_predecessor, dict)
    or v02_native_predecessor.get("profile_id")
    != "ajm006-spaceclaim-v02-preliminary-v1"
    or set(v02_native_predecessor.get("artifacts") or [])
    != {
        "v02_preliminary_producer.json",
        "product_two_zone.scdocx",
        "v02_face_inventory.json",
        "native_reopen.json",
    }
):
    fail("V02 native topology observer predecessor contract changed")
for invariant in (
    'NATIVE_PROFILE = "ajm006-workbench-v02-native-topology-observer-v1"',
    "shutil.copy2(native_path, staged_native_path)",
    "NATIVE_STAGING_COPY_HASH_MISMATCH",
    "if not native_route:",
    "source_geometry.SetFile(FilePath=geometry_path)",
    "model_container.Refresh()",
    'model_container.SendCommand(Language="Python", Command=model_script)',
    '"edit_called": False',
    '"PASS_PRELIMINARY_NATIVE_TOPOLOGY_OBSERVATION"',
):
    if invariant not in v02_observer_source:
        fail("V02 native topology observer lacks invariant: " + invariant)
for forbidden in (".Solve(", "SetFile(FilePath=native_path)"):
    if forbidden in v02_observer_source:
        fail("V02 native topology observer contains forbidden action: " + forbidden)

v02_native_mesh_profile = by_profile_id[
    "ajm006-workbench-v02-native-mesh-conformality-observer-v1"
]
v02_native_mesh_predecessor = v02_native_mesh_profile.get("predecessor")
if (
    v02_native_mesh_profile.get("engine") != "workbench"
    or v02_native_mesh_profile.get("script")
    != "006/v02_preliminary_topology_observer.wbjn"
    or v02_native_mesh_profile.get("reports")
    != ["v02_native_mesh_conformality_observer.json"]
    or not isinstance(v02_native_mesh_predecessor, dict)
    or v02_native_mesh_predecessor.get("profile_id")
    != "ajm006-spaceclaim-v02-preliminary-v1"
    or v02_native_mesh_predecessor.get("report")
    != "v02_preliminary_producer.json"
    or v02_native_mesh_predecessor.get("required_probe")
    != "v02_preliminary_producer"
    or v02_native_mesh_predecessor.get("required_status")
    != "PASS_PARTIAL_CAD_CAPABILITY"
    or set(v02_native_mesh_predecessor.get("required_assertions") or [])
    != {
        "input_contract",
        "gen1_target",
        "full_product_scope",
        "complete_flow_path",
        "two_fluid_zone",
        "native_save",
        "native_reopen",
        "step_export_reimport",
        "artifact_hashes",
        "physics_guards",
    }
    or set(v02_native_mesh_predecessor.get("artifacts") or [])
    != {
        "v02_preliminary_producer.json",
        "product_two_zone.scdocx",
        "v02_face_inventory.json",
        "native_reopen.json",
    }
):
    fail("V02 native mesh conformality profile contract changed")
for invariant in (
    'NATIVE_MESH_PROFILE = (',
    'mesh_route = profile_id == NATIVE_MESH_PROFILE',
    'Model.Mesh.ElementSize = Quantity("0.5 [mm]")',
    "Model.Mesh.GenerateMesh()",
    "MeshRegionById",
    "Model.Connections.Children",
    "PASS_NO_CONTACT_OR_CONNECTION_OBJECTS",
    "PASS_SHARED_INTERFACE_NODE_IDS",
    '"physics": "NOT_RUN"',
    '"p1_stage_gate": "NOT_RUN"',
):
    if invariant not in v02_observer_source:
        fail("V02 native mesh observer lacks invariant: " + invariant)
for invariant in (
    "ajm006-workbench-v02-native-mesh-conformality-observer-v1",
    'base.EXPECTED_REPORT_PHYSICS = "NOT_RUN"',
    "base.MESH_DIAGNOSTIC_REQUIRED = True",
    "base.OBSERVER_REPETITIONS = 2",
    "base.FIXED_INPUT_REPEATABILITY_REQUIRED = True",
    "PASS_PRELIMINARY_NATIVE_MESH_CONFORMALITY_OBSERVATION",
):
    if invariant not in V02_NATIVE_MESH_RUNNER.read_text(encoding="utf-8"):
        fail("V02 native mesh runner lacks invariant: " + invariant)
if ".Solve(" in v02_observer_source:
    fail("V02 native mesh observer contains physics solve")
for path in (
    V02_TOPOLOGY_RUNNER,
    V02_TOPOLOGY_RUNNER_TEST,
    V02_NATIVE_TOPOLOGY_RUNNER,
    V02_NATIVE_MESH_RUNNER,
):
    assert_python39_static_compatibility(path)

v02_parasolid_converter_profile = by_profile_id[
    "ajm006-spaceclaim-v02-parasolid-converter-v1"
]
v02_parasolid_converter_predecessor = (
    v02_parasolid_converter_profile.get("predecessor")
)
expected_v02_producer_assertions = {
    "input_contract",
    "gen1_target",
    "full_product_scope",
    "complete_flow_path",
    "two_fluid_zone",
    "native_save",
    "native_reopen",
    "step_export_reimport",
    "artifact_hashes",
    "physics_guards",
}
if (
    v02_parasolid_converter_profile.get("engine") != "spaceclaim"
    or v02_parasolid_converter_profile.get("script")
    != "006/v02_parasolid_converter.py"
    or v02_parasolid_converter_profile.get("reports")
    != ["v02_parasolid_converter.json"]
    or v02_parasolid_converter_profile.get("output_root_id") != "p1_cad_006"
    or not isinstance(v02_parasolid_converter_predecessor, dict)
    or v02_parasolid_converter_predecessor.get("profile_id")
    != "ajm006-spaceclaim-v02-preliminary-v1"
    or v02_parasolid_converter_predecessor.get("report")
    != "v02_preliminary_producer.json"
    or v02_parasolid_converter_predecessor.get("required_probe")
    != "v02_preliminary_producer"
    or v02_parasolid_converter_predecessor.get("required_status")
    != "PASS_PARTIAL_CAD_CAPABILITY"
    or set(
        v02_parasolid_converter_predecessor.get("required_assertions") or []
    )
    != expected_v02_producer_assertions
    or set(v02_parasolid_converter_predecessor.get("artifacts") or [])
    != {
        "v02_preliminary_producer.json",
        "product_two_zone.scdocx",
        "v02_face_inventory.json",
        "native_reopen.json",
    }
):
    fail("V02 Parasolid converter profile contract changed")
v02_parasolid_converter_source = (
    APPROVED / v02_parasolid_converter_profile["script"]
).read_text(encoding="utf-8")
for invariant in (
    'os.environ["AIRJET_PREDECESSOR_DIR"]',
    "snapshot_tree",
    "predecessor-manifest.json",
    "expected_predecessor_tree_names",
    "staging_workspace_exact",
    "ExportOptions.Create()",
    "ParasolidVersion.V23",
    "DocumentSave.Execute(parasolid_path, export_options)",
    "DocumentOpen.Execute(parasolid_path)",
    "parasolid_body_envelope_and_face_count_preserved",
    '"source_native_mutated": False',
    '"representation_conversion": True',
    '"NOT_EVALUATED_UNTIL_PARASOLID_OBSERVER"',
    '"formal_006_completion": False',
    '"p1_stage_gate": "NOT_RUN"',
    '"p1_p6_gates": "NOT_RUN"',
):
    if invariant not in v02_parasolid_converter_source:
        fail("V02 Parasolid converter lacks invariant: " + invariant)
if "DocumentSave.Execute(parasolid_path)" in v02_parasolid_converter_source:
    fail("V02 Parasolid converter restored deprecated implicit export options")
if 'os.environ["AIRJET_REPO_ROOT"]' in v02_parasolid_converter_source:
    fail("V02 Parasolid converter reads mutable repository dependencies")

v02_split_profile = by_profile_id[
    "ajm006-spaceclaim-v02-split-step-converter-v1"
]
v02_split_predecessor = v02_split_profile.get("predecessor")
if (
    v02_split_profile.get("engine") != "spaceclaim"
    or v02_split_profile.get("script") != "006/v02_parasolid_converter.py"
    or v02_split_profile.get("reports") != ["v02_split_step_converter.json"]
    or not isinstance(v02_split_predecessor, dict)
    or v02_split_predecessor.get("profile_id")
    != "ajm006-spaceclaim-v02-preliminary-v1"
    or set(v02_split_predecessor.get("artifacts") or [])
    != {
        "v02_preliminary_producer.json",
        "product_two_zone.scdocx",
        "v02_face_inventory.json",
        "native_reopen.json",
    }
):
    fail("V02 split STEP converter profile contract changed")
for invariant in (
    'SPLIT_STEP_PROFILE = "ajm006-spaceclaim-v02-split-step-converter-v1"',
    'upstream_step_path = os.path.join(job_dir, "upstream.step")',
    'downstream_step_path = os.path.join(job_dir, "downstream.step")',
    "Delete.Execute(Selection.Create(",
    "SPLIT_STEP_SOURCE_BODY_NAMES_MISMATCH",
    "SPLIT_STEP_BODY_SHAPE_OR_FACE_COUNT_NOT_PRESERVED",
    "NOT_EVALUATED_SEPARATE_FILES_ONLY",
    '"formal_006_completion": False',
    '"p1_stage_gate": "NOT_RUN"',
    '"p1_p6_gates": "NOT_RUN"',
):
    if invariant not in v02_parasolid_converter_source:
        fail("V02 split STEP converter lacks invariant: " + invariant)
for forbidden in ("DocumentSave.Execute(native_path)", "GenerateMesh(", ".Solve("):
    if forbidden in v02_parasolid_converter_source:
        fail("V02 split STEP converter contains forbidden action: " + forbidden)

v02_parasolid_observer_profile = by_profile_id[
    "ajm006-workbench-v02-parasolid-topology-observer-v1"
]
v02_parasolid_observer_predecessor = (
    v02_parasolid_observer_profile.get("predecessor")
)
expected_v02_converter_assertions = {
    "predecessor_identity",
    "predecessor_immutable",
    "staging_copy_hash_equal",
    "staging_workspace_exact",
    "source_native_open",
    "source_native_exact",
    "parasolid_export",
    "parasolid_reimport",
    "parasolid_body_envelope_and_face_count_preserved",
    "evidence_copy_hash_equal",
    "artifact_hashes",
    "claim_boundaries",
}
if (
    v02_parasolid_observer_profile.get("engine") != "workbench"
    or v02_parasolid_observer_profile.get("script")
    != "006/v02_parasolid_topology_observer.wbjn"
    or v02_parasolid_observer_profile.get("reports")
    != ["v02_parasolid_topology_observer.json"]
    or v02_parasolid_observer_profile.get("output_root_id") != "p1_cad_006"
    or not isinstance(v02_parasolid_observer_predecessor, dict)
    or v02_parasolid_observer_predecessor.get("profile_id")
    != "ajm006-spaceclaim-v02-parasolid-converter-v1"
    or v02_parasolid_observer_predecessor.get("report")
    != "v02_parasolid_converter.json"
    or v02_parasolid_observer_predecessor.get("required_probe")
    != "v02_parasolid_converter"
    or v02_parasolid_observer_predecessor.get("required_status")
    != "PASS_PARTIAL_CAD_CAPABILITY"
    or set(
        v02_parasolid_observer_predecessor.get("required_assertions") or []
    )
    != expected_v02_converter_assertions
    or set(v02_parasolid_observer_predecessor.get("artifacts") or [])
    != {
        "v02_parasolid_converter.json",
        "product.x_t",
        "parasolid_reimport.json",
        "v02_face_inventory.json",
        "source_chain.json",
    }
):
    fail("V02 Parasolid topology observer profile contract changed")
v02_parasolid_observer_source = (
    APPROVED / v02_parasolid_observer_profile["script"]
).read_text(encoding="utf-8")
for invariant in (
    'os.environ["AIRJET_PREDECESSOR_DIR"]',
    "predecessor-manifest.json",
    "predecessor_snapshot_before",
    "predecessor_snapshot_after",
    "GetGeometryFileAndSaveData",
    'model_container.SendCommand(Language="Python", Command=model_script)',
    "ExtAPI.DataModel.GeoData",
    '+ relations.get("AdjacentBodies", [])',
    "PERSISTED_BODY_NAME",
    "role_binding_valid",
    "observed_face_counts_match_parasolid_reimport",
    "solver_shape_matches_parasolid_reimport",
    "coincident_geometry_pairs == expected_orifice_count",
    "route_assessment_basis",
    "PASS_CANDIDATE_ROUTE_TO_MESH",
    "NOT_EVALUATED_NO_MESH",
    '"formal_006_completion": False',
    '"p1_stage_gate": "NOT_RUN"',
    '"p1_p6_gates": "NOT_RUN"',
):
    if invariant not in v02_parasolid_observer_source:
        fail("V02 Parasolid topology observer lacks invariant: " + invariant)
try:
    compile(
        v02_parasolid_converter_source,
        "v02_parasolid_converter.py",
        "exec",
    )
    compile(
        v02_parasolid_observer_source,
        "v02_parasolid_topology_observer.wbjn",
        "exec",
    )
except SyntaxError as exc:
    fail(f"V02 Parasolid approved script is invalid: {exc}")
for path in (V02_PARASOLID_RUNNER, V02_PARASOLID_RUNNER_TEST):
    assert_python39_static_compatibility(path)

native_profile = by_profile_id.get("ajm005-workbench-transfer-t1-v1")
if not isinstance(native_profile, dict):
    fail("missing native T1 Workbench transfer profile")
native_script = (APPROVED / native_profile["script"]).read_text(encoding="utf-8")
for invariant in (
    'staging_dir = os.path.join(job_dir, "input", "stagingcopy")',
    "shutil.copyfile(native_path, working_native_path)",
    "os.chmod(working_native_path, stat.S_IREAD | stat.S_IWRITE)",
    "len(native_path) == len(working_native_path)",
    "source_geometry.SetFile(FilePath=working_native_path)",
    '"working_copy_mutated_by_editor"',
    '"working_copy_exists_after_run"',
    '"working_copy_changed_or_missing_after_run"',
    '"immutable_source_bytes_unchanged_after"',
    '"immutable_source_read_only_after"',
    '"immutable_source_unchanged_after"',
    '"working_native"',
    '"IMMUTABLE_PREDECESSOR_CHANGED"',
    '"WORKING_COPY_MISSING_AFTER_RUN"',
    '"WRITABLE_STAGING_EXPLICIT_SPACECLAIM_EDIT_COMPONENTS_TO_SHARE"',
):
    if invariant not in native_script:
        fail(f"native Workbench staging route lacks invariant: {invariant}")
if "source_geometry.SetFile(FilePath=native_path)" in native_script:
    fail("native Workbench route must not edit the frozen predecessor directly")
if native_script.index("working_copy_exists_after_run = os.path.isfile") > native_script.index(
    "with open(report_path, \"w\") as report_handle:"
):
    fail("native Workbench finalizer must run before report write")
try:
    compile(native_script, "workbench_transfer_t1.wbjn", "exec")
except SyntaxError as exc:
    fail(f"native Workbench staging journal is invalid: {exc}")

connected_profile = by_profile_id.get(
    "ajm005-workbench-connected-spaceclaim-t1-v1"
)
if not isinstance(connected_profile, dict):
    fail("missing connected SpaceClaim diagnostic profile")
connected_predecessor = connected_profile.get("predecessor") or {}
if connected_predecessor.get("artifacts") != ["spaceclaim_cad_t1.json"]:
    fail("connected diagnostic must consume only the producer control report")
connected_script = (
    APPROVED / connected_profile["script"]
).read_text(encoding="utf-8")
for invariant in (
    '"WORKBENCH_MANAGED_CONNECTED_SPACECLAIM_DOCUMENT"',
    "source_properties.GeometryFilePath",
    "source_geometry.Edit(Interactive=True, IsSpaceClaimGeometry=True)",
    "source_geometry.RunScript(ScriptFile=build_script_path)",
    "source_geometry.Exit()",
    '"connected_editor_cleanup"',
    "ComponentsToShare=[source_component]",
    "source_geometry.GetGeometryFileAndSaveData()",
    "model_container.Refresh()",
    'master_shape = getattr(master, "Shape", None)',
    '"topology_shape_source"',
    '"connected_editor_post_runscript_probe"',
    '"connected_editor_post_exit_probe"',
    '"connected_editor_send_command_control"',
    '"connected_editor_post_send_command_probe"',
    '"post_runscript_artifact_probe"',
    '"post_exit_artifact_probe"',
    '"failure_pre_cleanup_artifact_probe"',
    '"failure_post_cleanup_artifact_probe"',
    'item["probe_error"] = str(item_probe_error)',
    '"connected_spaceclaim_entry.sentinel"',
    '"script_channel_diagnostic"',
    '"schema_version": 2',
    '"mode": "INTERACTIVE_TRUE_RUNSCRIPT_ONLY"',
    '"send_command_control": "SKIPPED_BY_EXPERIMENT"',
    '"runscript_call_outcome"',
    '"entry_exact_at_call_checkpoint"',
    '"entry_exact_post_exit"',
    '"entry_exact_failure_pre_cleanup"',
    '"entry_exact_failure_post_cleanup"',
    '"entry_exact_at_freeze"',
    '"entry_first_observed_at"',
    '"entry_invalid_or_partial_at"',
    '"entry_probe_errors_at"',
    '"build_report_probe_errors_at"',
    '"entry_delayed_or_later_observed"',
    '"entry_lost_after_checkpoint"',
    '"build_report_state"',
    '"RUNSCRIPT_CALL_EXCEPTION_ENTRY_ABSENT"',
    '"RUNSCRIPT_RETURNED_ENTRY_ABSENT"',
    '"ENTRY_DELAYED_OR_POST_EXIT_OBSERVED"',
    '"ENTRY_LOST_AFTER_CHECKPOINT"',
    '"ENTRY_EXACT_BUILD_REPORT_ABSENT"',
    '"BUILD_REPORT_INVALID"',
    '"BUILD_CONTRACT_FAIL"',
    '"BUILD_CONTRACT_PASS"',
    '"FAIL_CONNECTED_EDITOR_STARTED_REPORT_MISSING"',
    '"FAIL_FILE_ENTRY_SENTINEL_INVALID_OR_PARTIAL"',
    '"FAIL_RUNSCRIPT_RETURNED_ENTRY_AND_BUILD_ABSENT"',
    "capture_build_report_for_diagnostics(",
    "workbench_message_snapshot()",
    '"__AJM005_JOB_DIR_LITERAL__"',
    '"__AJM005_BUILD_REPORT_LITERAL__"',
    '"__AJM005_ENTRY_SENTINEL_LITERAL__"',
    '"PASS_CONNECTED_SPACECLAIM_TRANSFER_DIAGNOSTIC"',
    '"external_scdocx_attach": "NOT_RUN"',
    '"native_parameterization": "NOT_RUN"',
    '"p1_stage_gate": "NOT_RUN"',
):
    if invariant not in connected_script:
        fail(f"connected SpaceClaim journal lacks invariant: {invariant}")
for removed_inline_symbol in (
    "inline_sentinel_path",
    "inline_sentinel_payload",
    "inline_command",
    "connected_spaceclaim_inline.sentinel",
    "AJM005_CONNECTED_INLINE",
    "post_send_command_artifact_probe",
    "INLINE_PASS_",
    "INLINE_FAIL_",
):
    if removed_inline_symbol in connected_script:
        fail(
            "connected RunScript-only journal retains inline experiment symbol: "
            + removed_inline_symbol
        )
for forbidden in (
    "source_geometry.SetFile(",
    "DocumentHelper.CreateNewDocument()",
    "DocumentOpen.Execute(",
    "DocumentSave.Execute(",
):
    if forbidden in connected_script:
        fail(f"connected SpaceClaim route uses forbidden external route: {forbidden}")
try:
    connected_tree = ast.parse(connected_script)

    def dotted_call_name(function):
        parts = []
        current = function
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
            return ".".join(reversed(parts))
        return ""

    def has_forbidden_dynamic_dispatch(candidate_tree):
        parent_by_node = {}
        for parent in ast.walk(candidate_tree):
            for child in ast.iter_child_nodes(parent):
                parent_by_node[child] = parent
        safe_getattr_names = {
            "DateTimeStamp",
            "MessageType",
            "Summary",
            "Master",
            "Shape",
            "PieceCount",
            "IsClosed",
            "IsManifold",
        }
        dangerous_dynamic_names = {
            "eval",
            "exec",
            "globals",
            "locals",
            "vars",
            "attrgetter",
            "__builtins__",
            "builtins",
        }
        dangerous_dynamic_attributes = dangerous_dynamic_names | {
            "getattr",
            "__getattribute__",
            "__dict__",
            "GetType",
            "GetMethod",
            "Invoke",
        }
        reviewed_source_methods = {
            "GetGeometryProperties",
            "Edit",
            "RunScript",
            "Exit",
            "GetGeometryFileAndSaveData",
        }
        for candidate in ast.walk(candidate_tree):
            if isinstance(candidate, (ast.Import, ast.ImportFrom)):
                imported = {
                    alias.name.rsplit(".", 1)[-1] for alias in candidate.names
                }
                if imported & (dangerous_dynamic_names | {"getattr"}):
                    return True
            if (
                isinstance(candidate, ast.Attribute)
                and candidate.attr in dangerous_dynamic_attributes
            ):
                return True
            if (
                isinstance(candidate, ast.Name)
                and isinstance(candidate.ctx, ast.Load)
                and candidate.id in dangerous_dynamic_names | {"getattr"}
            ):
                parent = parent_by_node.get(candidate)
                if candidate.id != "getattr" or not (
                    isinstance(parent, ast.Call)
                    and parent.func is candidate
                    and len(parent.args) == 3
                    and not parent.keywords
                    and isinstance(parent.args[1], ast.Constant)
                    and parent.args[1].value in safe_getattr_names
                ):
                    return True
            if (
                isinstance(candidate, ast.Name)
                and isinstance(candidate.ctx, ast.Load)
                and candidate.id == "source_geometry"
            ):
                parent = parent_by_node.get(candidate)
                if isinstance(parent, ast.Compare) and (
                    parent.left is candidate
                    and len(parent.ops) == 1
                    and isinstance(parent.ops[0], ast.IsNot)
                    and len(parent.comparators) == 1
                    and isinstance(parent.comparators[0], ast.Constant)
                    and parent.comparators[0].value is None
                ):
                    continue
                if isinstance(parent, ast.Attribute) and (
                    parent.value is candidate
                    and parent.attr in reviewed_source_methods
                    and isinstance(parent_by_node.get(parent), ast.Call)
                    and parent_by_node[parent].func is parent
                ):
                    continue
                return True
            if isinstance(candidate, ast.Call):
                if isinstance(candidate.func, (ast.Call, ast.Subscript, ast.Lambda)):
                    return True
        return False

    if has_forbidden_dynamic_dispatch(connected_tree):
        fail("connected SpaceClaim route uses forbidden dynamic dispatch")
    for dynamic_mutation in (
        'getattr(source_geometry, "Send" + "Command")(Command="x")',
        'getattr(source_geometry, "Run" + "Script")(ScriptFile="x.py")',
        'source_geometry.__getattribute__("Run" + "Script")("x.py")',
        '{"run": source_geometry.RunScript}["run"](ScriptFile="x.py")',
        'sg = source_geometry\ngetattr(sg, "Run" + "Script")("x.py")',
        'ga = getattr\nga(source_geometry, "Run" + "Script")("x.py")',
        'getter = source_geometry.__getattribute__\ngetter("Run" + "Script")("x.py")',
        'import operator\noperator.attrgetter("Run" + "Script")(source_geometry)("x.py")',
        'runner = source_geometry.RunScript\nrunner(ScriptFile="x.py")',
        'sg = source_system.GetContainer(ComponentName="Geometry")\n'
        'ga = __builtins__["get" + "attr"]\n'
        'method = ga(sg, "Run" + "Script")\nmethod(ScriptFile="x.py")',
        'sg = source_system.GetContainer(ComponentName="Geometry")\n'
        'method = sg.GetType().GetMethod("Run" + "Script")\n'
        'method.Invoke(sg, ("x.py",))',
    ):
        if not has_forbidden_dynamic_dispatch(ast.parse(dynamic_mutation)):
            fail("computed geometry scripting dispatch escaped policy mutation test")

    outer_call_names = {
        dotted_call_name(node.func)
        for node in ast.walk(connected_tree)
        if isinstance(node, ast.Call)
    }
    outer_attribute_names = {
        dotted_call_name(node)
        for node in ast.walk(connected_tree)
        if isinstance(node, ast.Attribute)
    }
    outer_name_references = {
        node.id for node in ast.walk(connected_tree) if isinstance(node, ast.Name)
    }
    if any(
        isinstance(node, ast.Attribute) and node.attr == "SetFile"
        for node in ast.walk(connected_tree)
    ) or any(
        isinstance(node, ast.Constant) and node.value == "SetFile"
        for node in ast.walk(connected_tree)
    ):
        fail("connected SpaceClaim route references forbidden SetFile API")
    for forbidden_call in (
        "source_geometry.SetFile",
        "DocumentHelper.CreateNewDocument",
        "DocumentOpen.Execute",
        "DocumentSave.Execute",
    ):
        if forbidden_call in outer_call_names:
            fail(
                "connected SpaceClaim route uses forbidden AST call: "
                + forbidden_call
            )
        if forbidden_call in outer_attribute_names:
            fail(
                "connected SpaceClaim route references forbidden attribute: "
                + forbidden_call
            )
    for forbidden_root in ("DocumentHelper", "DocumentOpen", "DocumentSave"):
        if forbidden_root in outer_name_references:
            fail(
                "connected SpaceClaim route references forbidden API root: "
                + forbidden_root
            )
    outer_parent_by_node = {}
    for parent in ast.walk(connected_tree):
        for child in ast.iter_child_nodes(parent):
            outer_parent_by_node[child] = parent
    source_container_calls = [
        node
        for node in ast.walk(connected_tree)
        if isinstance(node, ast.Call)
        and dotted_call_name(node.func) == "source_system.GetContainer"
    ]
    if len(source_container_calls) != 1:
        fail("connected source Geometry container retrieval is not unique")
    source_container_call = source_container_calls[0]
    source_container_assignment = outer_parent_by_node.get(source_container_call)
    if not (
        isinstance(source_container_assignment, ast.Assign)
        and len(source_container_assignment.targets) == 1
        and isinstance(source_container_assignment.targets[0], ast.Name)
        and source_container_assignment.targets[0].id == "source_geometry"
        and not source_container_call.args
        and len(source_container_call.keywords) == 1
        and source_container_call.keywords[0].arg == "ComponentName"
        and isinstance(source_container_call.keywords[0].value, ast.Constant)
        and source_container_call.keywords[0].value.value == "Geometry"
    ):
        fail("connected source Geometry container binding changed")
    source_send_command_calls = [
        node
        for node in ast.walk(connected_tree)
        if isinstance(node, ast.Call)
        and dotted_call_name(node.func) == "source_geometry.SendCommand"
    ]
    run_script_calls = [
        node
        for node in ast.walk(connected_tree)
        if isinstance(node, ast.Call)
        and dotted_call_name(node.func) == "source_geometry.RunScript"
    ]
    edit_calls = [
        node
        for node in ast.walk(connected_tree)
        if isinstance(node, ast.Call)
        and dotted_call_name(node.func) == "source_geometry.Edit"
    ]
    exit_calls = [
        node
        for node in ast.walk(connected_tree)
        if isinstance(node, ast.Call)
        and dotted_call_name(node.func) == "source_geometry.Exit"
    ]
    edit_attribute_references = [
        node
        for node in ast.walk(connected_tree)
        if isinstance(node, ast.Attribute)
        and node.attr == "Edit"
    ]
    exit_attribute_references = [
        node
        for node in ast.walk(connected_tree)
        if isinstance(node, ast.Attribute)
        and node.attr == "Exit"
    ]
    run_script_attribute_references = [
        node
        for node in ast.walk(connected_tree)
        if isinstance(node, ast.Attribute)
        and node.attr == "RunScript"
    ]
    send_command_calls = [
        node
        for node in ast.walk(connected_tree)
        if isinstance(node, ast.Call)
        and dotted_call_name(node.func).endswith(".SendCommand")
    ]
    send_command_attribute_references = [
        node
        for node in ast.walk(connected_tree)
        if isinstance(node, ast.Attribute)
        and node.attr == "SendCommand"
    ]
    if (
        len(edit_calls) != 1
        or len(edit_attribute_references) != 1
        or len(exit_calls) != 2
        or len(exit_attribute_references) != 2
        or len(run_script_calls) != 1
        or len(run_script_attribute_references) != 1
        or source_send_command_calls
        or len(send_command_calls) != 1
        or len(send_command_attribute_references) != 1
        or dotted_call_name(send_command_calls[0].func)
        != "model_container.SendCommand"
    ):
        fail("connected RunScript-only call cardinality or owner changed")
    if edit_attribute_references[0] is not edit_calls[0].func:
        fail("connected editor Edit attribute escaped the reviewed direct call")
    if any(
        isinstance(node, ast.Constant)
        and node.value in {"Edit", "RunScript", "SendCommand", "Exit"}
        for node in ast.walk(connected_tree)
    ):
        fail("connected editor methods must not use reflective string dispatch")
    if "Interactive=False" in connected_script:
        fail("connected interactive diagnostic retains batch Edit mode")
    edit_call = edit_calls[0]
    if edit_call.args or any(keyword.arg is None for keyword in edit_call.keywords):
        fail("connected editor Edit must use only explicit reviewed keywords")
    edit_keywords = {keyword.arg: keyword.value for keyword in edit_call.keywords}
    if set(edit_keywords) != {"Interactive", "IsSpaceClaimGeometry"} or any(
        not isinstance(edit_keywords[name], ast.Constant)
        or edit_keywords[name].value is not True
        for name in ("Interactive", "IsSpaceClaimGeometry")
    ):
        fail("connected editor Edit must be exact interactive SpaceClaim mode")
    run_call = run_script_calls[0]
    if run_call.args or any(keyword.arg is None for keyword in run_call.keywords):
        fail("connected RunScript must use only the reviewed keyword")
    if (
        len(run_call.keywords) != 1
        or run_call.keywords[0].arg != "ScriptFile"
        or not isinstance(run_call.keywords[0].value, ast.Name)
        or run_call.keywords[0].value.id != "build_script_path"
    ):
        fail("connected RunScript must use exact ScriptFile=build_script_path")
    edit_statement = outer_parent_by_node.get(edit_call)
    run_statement = outer_parent_by_node.get(run_call)
    model_send_statement = outer_parent_by_node.get(send_command_calls[0])
    edit_body = outer_parent_by_node.get(edit_statement)
    run_body = outer_parent_by_node.get(run_statement)
    model_send_body = outer_parent_by_node.get(model_send_statement)
    exit_statements = [outer_parent_by_node.get(call) for call in exit_calls]
    normal_exit_statements = [
        statement
        for statement in exit_statements
        if outer_parent_by_node.get(statement) is edit_body
    ]
    cleanup_exit_statements = [
        statement
        for statement in exit_statements
        if statement not in normal_exit_statements
    ]
    if not (
        isinstance(edit_statement, ast.Expr)
        and isinstance(run_statement, ast.Expr)
        and isinstance(model_send_statement, ast.Expr)
        and isinstance(edit_body, ast.Try)
        and edit_body is run_body
        and edit_statement in edit_body.body
        and run_statement in edit_body.body
        and edit_body.body.index(edit_statement)
        < edit_body.body.index(run_statement)
        and model_send_body is edit_body
        and model_send_statement in edit_body.body
        and edit_body.body.index(run_statement)
        < edit_body.body.index(model_send_statement)
        and len(normal_exit_statements) == 1
        and isinstance(normal_exit_statements[0], ast.Expr)
        and edit_body.body.index(run_statement)
        < edit_body.body.index(normal_exit_statements[0])
        < edit_body.body.index(model_send_statement)
    ):
        fail("connected Edit RunScript and Mechanical command ordering changed")
    if any(call.args or call.keywords for call in exit_calls):
        fail("connected editor Exit calls must not take arguments")
    if len(cleanup_exit_statements) != 1 or not isinstance(
        cleanup_exit_statements[0], ast.Expr
    ):
        fail("connected editor cleanup Exit is not unique and direct")
    cleanup_try = outer_parent_by_node.get(cleanup_exit_statements[0])
    cleanup_if = outer_parent_by_node.get(cleanup_try)
    cleanup_handler = outer_parent_by_node.get(cleanup_if)
    cleanup_outer_try = outer_parent_by_node.get(cleanup_handler)
    expected_cleanup_guard = ast.parse(
        "connected_editor_open and source_geometry is not None", mode="eval"
    ).body
    if not (
        isinstance(cleanup_try, ast.Try)
        and cleanup_exit_statements[0] in cleanup_try.body
        and isinstance(cleanup_if, ast.If)
        and cleanup_try in cleanup_if.body
        and ast.dump(cleanup_if.test, include_attributes=False)
        == ast.dump(expected_cleanup_guard, include_attributes=False)
        and isinstance(cleanup_handler, ast.ExceptHandler)
        and cleanup_if in cleanup_handler.body
        and cleanup_outer_try is edit_body
    ):
        fail("connected editor cleanup Exit escaped the reviewed exception guard")
    embedded_assignments = [
        node
        for node in connected_tree.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name)
            and target.id == "connected_spaceclaim_script"
            for target in node.targets
        )
    ]
    if len(embedded_assignments) != 1:
        fail("connected SpaceClaim embedded build script is not unique")
    embedded_source = ast.literal_eval(embedded_assignments[0].value)
    compile(embedded_source, "connected_spaceclaim_fixture.py", "exec")
    embedded_tree = ast.parse(embedded_source)
    parent_by_node = {}
    for parent in ast.walk(embedded_tree):
        for child in ast.iter_child_nodes(parent):
            parent_by_node[child] = parent

    literal_assignments = {
        "job_dir": "__AJM005_JOB_DIR_LITERAL__",
        "report_path": "__AJM005_BUILD_REPORT_LITERAL__",
        "entry_sentinel_path": "__AJM005_ENTRY_SENTINEL_LITERAL__",
    }
    for variable, expected_literal in literal_assignments.items():
        stores = [
            node
            for node in ast.walk(embedded_tree)
            if isinstance(node, ast.Name)
            and node.id == variable
            and isinstance(node.ctx, ast.Store)
        ]
        assignments = [
            node
            for node in embedded_tree.body
            if isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == variable
        ]
        if len(stores) != 1 or len(assignments) != 1:
            fail(f"connected child path variable can be reassigned: {variable}")
        value = assignments[0].value
        if not isinstance(value, ast.Constant) or value.value != expected_literal:
            fail(f"connected child path is not literal-bound: {variable}")

    environment_key_nodes = [
        node
        for node in ast.walk(embedded_tree)
        if isinstance(node, ast.Constant) and node.value == "AIRJET_JOB_DIR"
    ]
    if len(environment_key_nodes) != 1:
        fail("connected child must observe AIRJET_JOB_DIR exactly once")
    environment_get_calls = [
        node
        for node in ast.walk(embedded_tree)
        if isinstance(node, ast.Call)
        and dotted_call_name(node.func) == "os.environ.get"
    ]
    if len(environment_get_calls) != 1:
        fail("connected child must have one diagnostic os.environ.get call")
    environment_assignment = parent_by_node.get(environment_get_calls[0])
    if not (
        isinstance(environment_assignment, ast.Assign)
        and len(environment_assignment.targets) == 1
        and isinstance(environment_assignment.targets[0], ast.Name)
        and environment_assignment.targets[0].id == "observed_job_dir"
    ):
        fail("connected child environment observation has an unsafe target")
    observed_stores = [
        node
        for node in ast.walk(embedded_tree)
        if isinstance(node, ast.Name)
        and node.id == "observed_job_dir"
        and isinstance(node.ctx, ast.Store)
    ]
    if len(observed_stores) != 1:
        fail("connected child observed_job_dir can be reassigned")
    environment_assignments = [
        node
        for node in ast.walk(embedded_tree)
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Subscript)
        and isinstance(node.targets[0].value, ast.Name)
        and node.targets[0].value.id == "result"
        and isinstance(node.targets[0].slice, ast.Constant)
        and node.targets[0].slice.value == "environment"
    ]
    if len(environment_assignments) != 1 or not isinstance(
        environment_assignments[0].value, ast.Dict
    ):
        fail("connected child environment diagnostic object is not unique")
    environment_keys = [
        key.value if isinstance(key, ast.Constant) else None
        for key in environment_assignments[0].value.keys
    ]
    if environment_keys != [
        "airjet_job_dir_present",
        "airjet_job_dir_value",
        "matches_literal_job_dir",
    ]:
        fail("connected child environment diagnostic keys changed")
    expected_environment_value = ast.parse(
        """{
            "airjet_job_dir_present": observed_job_dir is not None,
            "airjet_job_dir_value": observed_job_dir,
            "matches_literal_job_dir": (
                observed_job_dir is not None
                and os.path.normcase(os.path.abspath(observed_job_dir))
                == os.path.normcase(os.path.abspath(job_dir))
            ),
        }""",
        mode="eval",
    ).body
    if ast.dump(
        environment_assignments[0].value, include_attributes=False
    ) != ast.dump(expected_environment_value, include_attributes=False):
        fail("connected child environment diagnostic values changed")
    environment_subscripts = [
        node
        for node in ast.walk(embedded_tree)
        if isinstance(node, ast.Subscript)
        and isinstance(node.value, ast.Name)
        and node.value.id == "result"
        and isinstance(node.slice, ast.Constant)
        and node.slice.value == "environment"
    ]
    if len(environment_subscripts) != 1 or not isinstance(
        environment_subscripts[0].ctx, ast.Store
    ):
        fail("connected child environment diagnostic can be read or rewritten")
    for observed_load in (
        node
        for node in ast.walk(embedded_tree)
        if isinstance(node, ast.Name)
        and node.id == "observed_job_dir"
        and isinstance(node.ctx, ast.Load)
    ):
        ancestor = parent_by_node.get(observed_load)
        while ancestor is not None and not isinstance(ancestor, ast.Assign):
            ancestor = parent_by_node.get(ancestor)
        target = (
            ancestor.targets[0]
            if isinstance(ancestor, ast.Assign) and len(ancestor.targets) == 1
            else None
        )
        safe_diagnostic_assignment = (
            isinstance(target, ast.Subscript)
            and isinstance(target.value, ast.Name)
            and target.value.id == "result"
            and isinstance(target.slice, ast.Constant)
            and target.slice.value == "environment"
        )
        if not safe_diagnostic_assignment:
            fail("connected child environment observation escaped diagnostics")
        call_ancestor = parent_by_node.get(observed_load)
        while call_ancestor is not None and not isinstance(
            call_ancestor, ast.Assign
        ):
            if isinstance(call_ancestor, ast.Call) and dotted_call_name(
                call_ancestor.func
            ) not in {"os.path.abspath", "os.path.normcase"}:
                fail(
                    "connected child environment observation entered an unsafe call"
                )
            call_ancestor = parent_by_node.get(call_ancestor)
    for node in ast.walk(embedded_tree):
        if isinstance(node, ast.Subscript) and dotted_call_name(node.value) == "os.environ":
            fail("connected child must not subscript os.environ")
        if isinstance(node, ast.Call) and dotted_call_name(node.func) == "os.getenv":
            fail("connected child must not call os.getenv")

    embedded_call_names = {
        dotted_call_name(node.func)
        for node in ast.walk(embedded_tree)
        if isinstance(node, ast.Call)
    }
    embedded_attribute_names = {
        dotted_call_name(node)
        for node in ast.walk(embedded_tree)
        if isinstance(node, ast.Attribute)
    }
    embedded_name_references = {
        node.id for node in ast.walk(embedded_tree) if isinstance(node, ast.Name)
    }
    if any(
        isinstance(node, ast.Attribute) and node.attr == "SetFile"
        for node in ast.walk(embedded_tree)
    ) or any(
        isinstance(node, ast.Constant) and node.value == "SetFile"
        for node in ast.walk(embedded_tree)
    ):
        fail("connected child references forbidden SetFile API")
    for forbidden_call in (
        "DocumentHelper.CreateNewDocument",
        "DocumentOpen.Execute",
        "DocumentSave.Execute",
    ):
        if forbidden_call in embedded_call_names:
            fail(
                "connected child uses forbidden external-document call: "
                + forbidden_call
            )
        if forbidden_call in embedded_attribute_names:
            fail(
                "connected child references forbidden external-document attribute: "
                + forbidden_call
            )
    for forbidden_root in ("DocumentHelper", "DocumentOpen", "DocumentSave"):
        if forbidden_root in embedded_name_references:
            fail(
                "connected child references forbidden external-document API root: "
                + forbidden_root
            )
    for embedded_invariant in (
        'entry_sentinel_path = r"__AJM005_ENTRY_SENTINEL_LITERAL__"',
        'entry_handle = open(entry_sentinel_path, "wb")',
        'entry_handle.write(b"AJM005_CONNECTED_CHILD_ENTERED_V2\\n")',
        "finally:",
        "entry_handle.close()",
        'observed_job_dir = os.environ.get("AIRJET_JOB_DIR")',
        '"matches_literal_job_dir"',
        '"literal_paths_injected"',
        'result["final_stage"] = stage',
    ):
        if embedded_invariant not in embedded_source:
            fail(
                "connected child lacks observability invariant: "
                + embedded_invariant
            )
    if embedded_source.index('entry_handle = open(entry_sentinel_path, "wb")') > embedded_source.index(
        "import json"
    ):
        fail("connected child entry sentinel must precede imports")
except (SyntaxError, ValueError) as exc:
    fail(f"connected SpaceClaim journal or embedded script is invalid: {exc}")

semantic_profile = by_profile_id.get(
    "ajm005-workbench-semantic-reconstruction-t1-v1"
)
if not isinstance(semantic_profile, dict):
    fail("missing independent T1 semantic reconstruction profile")
semantic_predecessor = semantic_profile.get("predecessor") or {}
if "spaceclaim_cad_t1.scdocx" in semantic_predecessor.get("artifacts", []):
    fail("semantic reconstruction profile must not consume native CAD")
for required in (
    "spaceclaim_cad_t1.step",
    "spaceclaim_semantic_sidecar.json",
):
    if required not in semantic_predecessor.get("artifacts", []):
        fail(f"semantic reconstruction predecessor lacks {required}")
semantic_script = (
    APPROVED / semantic_profile["script"]
).read_text(encoding="utf-8")
for invariant in (
    '"native_named_selection_transfer_claim": False',
    '"native_attach": False',
    '"native_parameterization": False',
    '"p1_cad_toolchain_readiness": False',
    "PASS_STEP_SEMANTIC_RECONSTRUCTION_DIAGNOSTIC",
):
    if invariant not in semantic_script:
        fail(f"semantic reconstruction script lacks claim boundary: {invariant}")
semantic_tree = ast.parse(semantic_script)
model_script_assignments = [
    node
    for node in ast.walk(semantic_tree)
    if isinstance(node, ast.Assign)
    and any(
        isinstance(target, ast.Name) and target.id == "model_script"
        for target in node.targets
    )
]
if len(model_script_assignments) != 1:
    fail("semantic reconstruction must define exactly one embedded model_script")
model_script_value = model_script_assignments[0].value
if not (
    isinstance(model_script_value, ast.BinOp)
    and isinstance(model_script_value.op, ast.Mod)
    and isinstance(model_script_value.left, ast.Constant)
    and isinstance(model_script_value.left.value, str)
):
    fail("semantic reconstruction model_script must use audited literal formatting")
try:
    rendered_model_script = model_script_value.left.value % (
        r"C:\AirJetAudit\inspection.json",
        r"C:\AirJetAudit\semantic-sidecar.json",
    )
    compile(rendered_model_script, "embedded_mechanical_model_script.py", "exec")
except (SyntaxError, TypeError, ValueError) as exc:
    fail(f"semantic reconstruction embedded model_script is invalid: {exc}")
face_observation_marker = (
    '"classification_stage": (\n'
    '                "FACE_CANDIDATES_OBSERVED_BEFORE_COUNT_VALIDATION"'
)
negative_observation_marker = (
    '"classification_stage": (\n'
    '                "NEGATIVE_CONTROLS_OBSERVED_BEFORE_PARTITION_VALIDATION"'
)
face_count_guard = (
    "    if len(face_details) != expected_face_count:\n"
    "        raise Exception("
)
negative_control_guard = (
    "    if not all(negative_controls.values()):\n"
    '        raise Exception("SEMANTIC_RECONSTRUCTION_NEGATIVE_CONTROL_FAILED")'
)
real_partition_validation = (
    "    validate_partition(\n"
    "        expected_face_count,\n"
    "        expected_counts,"
)
for diagnostic_field in (
    '"face_details": face_details',
    '"candidate_face_ids": {',
    '"candidate_face_counts": {',
    '"negative_controls": negative_controls',
    '"surface_type": surface_type',
    '"surface_type_error": surface_type_error',
    'surface_type_error = str(surface_type_exception)',
    '"edge_count": edge_count',
    '"edge_count_error": edge_count_error',
    'edge_count_error = str(edge_count_exception)',
    '"normal_at_centroid": normal_at_centroid',
    '"normal_error": normal_error',
    '"inlet_solver_match_contract": inlet_solver_topology',
    '"area_role": "DIAGNOSTIC_ONLY"',
    '"calibration_evidence_ids": ["REAL-20260714-034", "REAL-20260714-035"]',
    'surface_type == inlet_solver_topology["surface_type"]',
    'edge_count == inlet_solver_topology["edge_count"]',
    "normal_abs_axis_match(",
    face_observation_marker,
    negative_observation_marker,
):
    if diagnostic_field not in rendered_model_script:
        fail(
            "semantic reconstruction must preserve prevalidation field: "
            + diagnostic_field
        )
if rendered_model_script.index(face_observation_marker) > rendered_model_script.index(
    face_count_guard
):
    fail("semantic reconstruction face observations occur after face-count guard")
if rendered_model_script.index(negative_observation_marker) > rendered_model_script.index(
    negative_control_guard
):
    fail("semantic reconstruction negative observations occur after control guard")
if rendered_model_script.index(negative_observation_marker) > rendered_model_script.index(
    real_partition_validation
):
    fail("semantic reconstruction negative observations occur after partition guard")
inlet_predicate = rendered_model_script.split("        if (\n", 1)[1].split(
    "        elif (\n", 1
)[0]
if 'inlet_signature["area_mm2"]' in inlet_predicate:
    fail("semantic reconstruction inlet predicate must not use unstable STEP area")
for inlet_anchor in (
    'inlet_signature["center_mm"]',
    'surface_type == inlet_solver_topology["surface_type"]',
    'edge_count == inlet_solver_topology["edge_count"]',
    "normal_abs_axis_match(",
):
    if inlet_anchor not in inlet_predicate:
        fail("semantic reconstruction inlet predicate lost anchor: " + inlet_anchor)
outlet_predicate = rendered_model_script.split("        elif (\n", 1)[1].split(
    "        else:\n", 1
)[0]
if 'outlet_signature["area_mm2"]' not in outlet_predicate:
    fail("semantic reconstruction outlet predicate lost its validated area anchor")
for profile in policy["profiles"]:
    predecessor = profile["predecessor"]
    if predecessor is None:
        continue
    if set(predecessor) != {
        "profile_id",
        "report",
        "required_probe",
        "required_status",
        "required_assertions",
        "artifacts",
    }:
        fail(f"invalid predecessor fields for {profile['profile_id']}")
    upstream = by_profile_id.get(predecessor["profile_id"])
    if upstream is None:
        fail(f"unknown predecessor for {profile['profile_id']}")
    if predecessor["required_status"] not in {
        "PASS_005_CAPABILITY",
        "PASS_PARTIAL_CAD_CAPABILITY",
    }:
        fail(f"unsafe predecessor status for {profile['profile_id']}")
    if not predecessor["required_probe"] or not predecessor["required_assertions"]:
        fail(f"incomplete predecessor report contract for {profile['profile_id']}")
    if predecessor["report"] not in upstream["reports"]:
        fail(f"undeclared predecessor report for {profile['profile_id']}")
    if predecessor["report"] not in predecessor["artifacts"]:
        fail(f"predecessor report not copied for {profile['profile_id']}")
    if upstream["output_root_id"] != profile["output_root_id"]:
        fail(f"predecessor output root mismatch for {profile['profile_id']}")

print(f"AIRJET_ANSYS_MCP_STATIC_POLICY=PASS profiles={len(profile_ids)} tools={len(tools)}")

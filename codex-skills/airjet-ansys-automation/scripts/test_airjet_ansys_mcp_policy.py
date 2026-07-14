#!/usr/bin/env python3
"""Static fail-closed checks for the AirJet ANSYS MCP and approved profiles."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import sys


SKILL_ROOT = Path(__file__).resolve().parents[1]
REPO = Path(r"C:\Users\admin\win-mac-dual-channel") if sys.platform == "win32" else SKILL_ROOT.parents[1]
SERVER = SKILL_ROOT / "scripts" / "airjet_ansys_mcp.py"
POLICY = REPO / "airjet-simulation" / "automation" / "ansys" / "profiles.json"
APPROVED = REPO / "airjet-simulation" / "automation" / "ansys" / "approved"
T0_RUNNER = SKILL_ROOT / "scripts" / "run_t0_suite.py"
T1_CAD_RUNNER = SKILL_ROOT / "scripts" / "run_t1_cad_suite.py"
T1_SEMANTIC_RUNNER = (
    SKILL_ROOT / "scripts" / "run_t1_semantic_reconstruction_suite.py"
)
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
    "predecessor_job_id",
    "artifact_manifest",
    "P1_STAGE_GATE",
):
    if invariant.upper() not in t1_cad_runner_source.upper():
        fail(f"T1 CAD suite runner lacks invariant: {invariant}")

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
if set(policy) != {"schema_version", "profiles"} or policy["schema_version"] != 2:
    fail("invalid profiles root")
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

by_profile_id = {profile["profile_id"]: profile for profile in policy["profiles"]}
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

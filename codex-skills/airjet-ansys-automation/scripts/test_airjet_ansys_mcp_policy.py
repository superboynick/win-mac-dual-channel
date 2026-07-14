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
T1_CONNECTED_RUNNER = (
    SKILL_ROOT / "scripts" / "run_t1_connected_spaceclaim_suite.py"
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
    "source_geometry.Edit(Interactive=False, IsSpaceClaimGeometry=True)",
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
    '"post_runscript_artifact_probe"',
    '"post_exit_artifact_probe"',
    '"failure_artifact_probe"',
    'item["probe_error"] = str(item_probe_error)',
    '"connected_spaceclaim_entry.sentinel"',
    '"FAIL_CONNECTED_EDITOR_ENTRY_SENTINEL_MISSING"',
    '"FAIL_CONNECTED_EDITOR_STARTED_REPORT_MISSING"',
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
        'entry_handle.write("AJM005_CONNECTED_CHILD_ENTERED_V2\\n")',
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
    if embedded_source.index("with open(entry_sentinel_path") > embedded_source.index(
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

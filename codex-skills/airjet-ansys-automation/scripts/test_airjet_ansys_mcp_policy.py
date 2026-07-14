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
    "submit_job": ["profile_id", "case_id"],
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
if "CREATE_SUSPENDED" not in source or "TerminateJobObject" not in source:
    fail("Windows process-tree containment is missing")
submit_calls = {
    node.func.id
    for node in ast.walk(functions["submit_job"])
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
}
if "require_runtime_readiness" not in submit_calls:
    fail("submit_job must enforce runtime readiness independently of inventory")

policy = json.loads(POLICY.read_text(encoding="utf-8"))
if set(policy) != {"schema_version", "profiles"} or policy["schema_version"] != 1:
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

print(f"AIRJET_ANSYS_MCP_STATIC_POLICY=PASS profiles={len(profile_ids)} tools={len(tools)}")

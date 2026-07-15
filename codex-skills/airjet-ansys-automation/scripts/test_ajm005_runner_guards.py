#!/usr/bin/env python3
"""Pure spies for AJM-005 runner preflight and post-submit cancellation guards."""

from __future__ import annotations

import asyncio
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import ModuleType, SimpleNamespace


def _install_mcp_import_stub_if_missing() -> None:
    """Permit pure guard tests without weakening real MCP environment checks."""
    if importlib.util.find_spec("mcp") is not None:
        return

    def unexpected_mcp_use(*args, **kwargs):
        raise AssertionError("pure runner guard unexpectedly used MCP")

    mcp_module = ModuleType("mcp")
    mcp_module.__path__ = []
    mcp_module.ClientSession = unexpected_mcp_use
    mcp_module.StdioServerParameters = unexpected_mcp_use
    mcp_module.types = SimpleNamespace(TextContent=object)

    client_module = ModuleType("mcp.client")
    client_module.__path__ = []
    stdio_module = ModuleType("mcp.client.stdio")
    stdio_module.stdio_client = unexpected_mcp_use

    sys.modules["mcp"] = mcp_module
    sys.modules["mcp.client"] = client_module
    sys.modules["mcp.client.stdio"] = stdio_module


_install_mcp_import_stub_if_missing()

import run_t1_alternate_route_confirmation_suite as runner


HEAD = "1" * 40
SHA = "a" * 64


def blocked_preflight() -> dict:
    return {
        "git_fetch": True,
        "branch": "main",
        "git_clean": False,
        "ahead_behind": "0\t0",
        "git_head": HEAD,
        "project_audit": True,
        "project_audit_stdout": "",
        "project_audit_stderr": "",
        "preflight_errors": [],
        "signed_composite_sources": {},
        "preflight_ok": False,
    }


async def assert_preflight_starts_nothing(root: Path) -> None:
    calls = {"stdio": 0, "submit": 0, "child": 0, "closeout": 0}
    originals = {
        name: getattr(runner, name)
        for name in (
            "EXPECTED_PYTHON", "OUTPUT_ROOT", "CLOSEOUT_PATH", "preflight",
            "git_blob", "sha256_file", "load_frozen_closeout_helper", "version",
            "stdio_client", "call_json", "write_closeout",
        )
    }
    original_popen = runner.subprocess.Popen
    runner_bytes = b"runner"
    server_bytes = b"server"
    guard_bytes = b"guard"
    runner_sha = hashlib.sha256(runner_bytes).hexdigest()
    server_sha = hashlib.sha256(server_bytes).hexdigest()
    guard_sha = hashlib.sha256(guard_bytes).hexdigest()
    route = {
        "route": {
            "cad_authoring": runner.CAD_AUTHORING_ROUTE,
            "solver_handoff": runner.SOLVER_HANDOFF_ROUTE,
            "connected_route": runner.CONNECTED_ROUTE,
            "step_is_route_hard_requirement": True,
        },
        "runner": {
            "path": runner.RUNNER_GIT_PATH,
            "sha256": runner_sha,
            "guard_test_path": runner.RUNNER_GUARD_TEST_GIT_PATH,
            "guard_test_sha256": guard_sha,
        },
        "mcp_server": {"sha256": server_sha},
        "closeout": {
            "helper": {"git_path": runner.CLOSEOUT_HELPER_GIT_PATH, "sha256": SHA},
            "test": {"git_path": runner.CLOSEOUT_TEST_GIT_PATH, "sha256": SHA},
        },
    }

    def fake_git_blob(head: str, path: str) -> bytes:
        assert head == HEAD
        if path == runner.RUNNER_GIT_PATH:
            return runner_bytes
        if path == runner.ROUTE_GIT_PATH:
            return json.dumps(route).encode("ascii")
        if path == runner.JUDGMENT_GIT_PATH:
            return json.dumps(
                {"suite_pass_status": runner.SUITE_PASS_STATUS}
            ).encode("ascii")
        if path == runner.SERVER_GIT_PATH:
            return server_bytes
        if path == runner.RUNNER_GUARD_TEST_GIT_PATH:
            return guard_bytes
        raise AssertionError("unexpected blob " + path)

    def forbidden_stdio(*args, **kwargs):
        calls["stdio"] += 1
        raise AssertionError("stdio_client reached after blocked preflight")

    async def forbidden_call_json(session, name, arguments=None, timeout_seconds=120):
        if name == "submit_job":
            calls["submit"] += 1
        raise AssertionError("MCP call reached after blocked preflight")

    def forbidden_popen(*args, **kwargs):
        calls["child"] += 1
        raise AssertionError("child start reached after blocked preflight")

    def fake_write_closeout(result, result_path, helper):
        calls["closeout"] += 1
        raise ValueError("closeout=serialization-failure")

    try:
        runner.EXPECTED_PYTHON = Path(sys.executable)
        runner.OUTPUT_ROOT = root / "output"
        runner.CLOSEOUT_PATH = root / "closeout.txt"
        runner.preflight = blocked_preflight
        runner.git_blob = fake_git_blob
        runner.sha256_file = lambda path: runner_sha
        runner.load_frozen_closeout_helper = lambda head, contract: SimpleNamespace()
        runner.version = lambda package: "1.28.1"
        runner.stdio_client = forbidden_stdio
        runner.call_json = forbidden_call_json
        runner.write_closeout = fake_write_closeout
        runner.subprocess.Popen = forbidden_popen
        exit_code = await runner.run_suite()
        assert exit_code == 2
        assert calls == {"stdio": 0, "submit": 0, "child": 0, "closeout": 1}
        result_files = list(runner.OUTPUT_ROOT.glob("AJM005_T1_ALTERNATE_ROUTE_SUITE_*.json"))
        assert len(result_files) == 1
        persisted = json.loads(result_files[0].read_text(encoding="utf-8"))
        assert persisted["error"]["message"].startswith("BLOCKED_PREFLIGHT:")
        assert persisted["closeout_write_error"]["message"] == "closeout=serialization-failure"
    finally:
        for name, value in originals.items():
            setattr(runner, name, value)
        runner.subprocess.Popen = original_popen


async def assert_post_submit_failure_cancels(
    profile_id: str, predecessor_job_id: str = ""
) -> None:
    calls: list[str] = []
    original_call_json = runner.call_json

    async def fake_call_json(session, name, arguments=None, timeout_seconds=120):
        calls.append(name)
        if name == "submit_job":
            return {
                "job_id": "job-cancel-spy",
                "case_id": "case-cancel-spy",
                "profile_id": profile_id,
                "engine": "spaceclaim" if profile_id == runner.SC_PROFILE else "workbench",
                "script_sha256": SHA,
                "profile_contract_sha256": SHA,
                "git_head": "0" * 40,
                "output_root_id": "root-spy",
                "predecessor_job_id": predecessor_job_id or None,
                "profile_dependency_manifest_sha256": SHA,
                "profile_dependency_artifacts": [{} for _ in range(5)],
                "license_arguments_added": False,
                "phase": "RUNNING",
            }
        if name == "cancel_job":
            return {
                "job_id": "job-cancel-spy",
                "case_id": "case-cancel-spy",
                "profile_id": profile_id,
                "phase": "CANCELLED",
            }
        raise AssertionError("unexpected call " + name)

    judgment = {
        "producer_required_status": "PASS_PARTIAL_CAD_CAPABILITY",
        "consumer_required_status": "PASS_ALTERNATE_ROUTE_SEMANTIC_RECONSTRUCTION",
        "producer_required_assertions": [],
        "consumer_required_assertions": [],
    }
    record = runner.new_run_record(profile_id, "case-cancel-spy", predecessor_job_id)
    runner.call_json = fake_call_json
    try:
        try:
            await runner.run_profile(
                object(), profile_id, "case-cancel-spy", HEAD, SHA,
                judgment, predecessor_job_id, run_record=record,
            )
        except RuntimeError as error:
            assert str(error).startswith("SUBMIT_IDENTITY_INVALID")
        else:
            raise AssertionError("identity failure did not propagate")
    finally:
        runner.call_json = original_call_json
    assert calls == ["submit_job", "cancel_job"]
    assert record["submitted"] is True
    assert record["capability_status"] == "FAIL"
    assert record["cancel_attempted"] is True
    assert record["cancel_succeeded"] is True
    assert record["reached_terminal"] is True
    assert record["final_state"]["phase"] == "CANCELLED"
    assert record["p1_stage_gate"] == "NOT_RUN"


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="ajm005-runner-guards-") as temporary:
        asyncio.run(assert_preflight_starts_nothing(Path(temporary)))
    asyncio.run(assert_post_submit_failure_cancels(runner.SC_PROFILE))
    asyncio.run(assert_post_submit_failure_cancels(runner.WB_PROFILE, "producer-job-spy"))
    print(
        "AJM005_RUNNER_GUARDS=PASS preflight_stdio=0 preflight_submit=0 "
        "preflight_child_start=0 closeout=1 producer_cancel=PASS consumer_cancel=PASS "
        "post_submit_gate=FAIL p1_p6=NOT_RUN"
    )


if __name__ == "__main__":
    main()

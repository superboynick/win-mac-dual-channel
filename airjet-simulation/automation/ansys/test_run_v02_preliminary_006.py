#!/usr/bin/env python3
"""Pure static tests for run_v02_preliminary_006 runner. No ANSYS, no network."""

from __future__ import annotations

import asyncio
import hashlib
import importlib.util
import json
import os
import sys
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any


def _setup_mcp_stub() -> None:
    if importlib.util.find_spec("mcp") is not None:
        return

    @asynccontextmanager
    async def fake_stdio_client(params, errlog=None):
        yield (SimpleNamespace(), SimpleNamespace())

    class FakeClientSession:
        def __init__(self, *args, **kwargs):
            pass
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass
        async def initialize(self):
            return SimpleNamespace(
                protocolVersion="2024-11-05",
                serverInfo=SimpleNamespace(name="test-server"),
            )
        async def list_tools(self):
            names = sorted([
                "artifact_manifest", "cancel_job", "inventory",
                "poll_job", "submit_job",
            ])
            return SimpleNamespace(
                tools=[SimpleNamespace(name=n) for n in names]
            )

    class FakeStdioServerParameters:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    types_mod = ModuleType("mcp.types")
    types_mod.TextContent = type("TextContent", (), {})
    types_mod.CallToolResult = type(
        "CallToolResult", (), {"isError": False, "content": [], "structuredContent": {}}
    )
    types_mod.Implementation = SimpleNamespace

    mcp_mod = ModuleType("mcp")
    mcp_mod.ClientSession = FakeClientSession
    mcp_mod.StdioServerParameters = FakeStdioServerParameters
    mcp_mod.types = types_mod

    client_mod = ModuleType("mcp.client")
    stdio_mod = ModuleType("mcp.client.stdio")
    stdio_mod.stdio_client = fake_stdio_client

    sys.modules["mcp"] = mcp_mod
    sys.modules["mcp.types"] = types_mod
    sys.modules["mcp.client"] = client_mod
    sys.modules["mcp.client.stdio"] = stdio_mod


_setup_mcp_stub()

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_v02_preliminary_006 as runner


HEAD = "a" * 40
VALID_SHA256 = runner.PROFILE_SCRIPT_SHA256
PROFILE_CONTRACT_SHA256 = "b" * 64
DEPENDENCY_MANIFEST_SHA256 = "c" * 64

VALID_POLICY = {
    "schema_version": 2,
    "production_contracts": {
        "schema_version": 1,
        "contract_id": "AJM006_GEN1_FULL_PRODUCT_SEMANTIC_PRODUCTION_V1",
        "execution_state": "STATIC_CONTRACT_ONLY_NOT_REGISTERED",
        "p1_p6_gates": "NOT_RUN",
        "components": [],
    },
    "profiles": [
        {
            "profile_id": runner.PROFILE_ID,
            "engine": "spaceclaim",
            "script": "006/v02_preliminary_producer.py",
            "sha256": VALID_SHA256,
            "timeout_seconds": 7200,
            "output_root_id": "p1_cad_006",
            "reports": ["v02_preliminary_producer.json"],
            "predecessor": None,
        }
    ],
}

VALID_POLICY_BYTES = json.dumps(VALID_POLICY, indent=2, sort_keys=True).encode("utf-8")


class FakeGitCapture:
    def __init__(self, overrides=None):
        self._overrides = overrides or {}
        self._calls = []

    def __call__(self, *args):
        self._calls.append(args)
        if args in self._overrides:
            return dict(self._overrides[args])
        return {"exit_code": 0, "stdout": "", "stderr": ""}


class FakeReadGitBlob:
    def __init__(self, blob_map=None):
        self._blob_map = blob_map or {}

    def __call__(self, head, relative):
        key = "{}:{}".format(head, relative)
        if key in self._blob_map:
            return self._blob_map[key]
        raise RuntimeError("BLOCKED_MISSING_GIT_BLOB")


def default_git():
    overrides = {
        ("rev-parse", "--abbrev-ref", "HEAD"): {
            "exit_code": 0, "stdout": "main", "stderr": ""
        },
        ("rev-parse", "HEAD"): {
            "exit_code": 0, "stdout": HEAD, "stderr": ""
        },
        ("status", "--porcelain=v1"): {
            "exit_code": 0, "stdout": "", "stderr": ""
        },
        ("rev-list", "--left-right", "--count",
         "{}...origin/main".format(HEAD)): {
            "exit_code": 0, "stdout": "0\t0", "stderr": ""
        },
        ("verify-commit", "--raw", HEAD): {
            "exit_code": 0, "stdout": "", "stderr": ""
        },
    }
    return FakeGitCapture(overrides)


def default_blob():
    return FakeReadGitBlob({
        "{}:{}".format(HEAD, runner.POLICY_GIT_PATH): VALID_POLICY_BYTES,
    })


def assert_preflight_blocked(expected_error, git=None, blob=None):
    orig_git = runner.git_capture
    orig_blob = runner.read_git_blob
    try:
        runner.git_capture = git or default_git()
        runner.read_git_blob = blob or default_blob()
        result = runner.preflight()
        assert not result["preflight_ok"], "expected preflight to block"
        found = any(expected_error in e for e in result["preflight_errors"])
        assert found, "error {!r} not in {!r}".format(
            expected_error, result["preflight_errors"]
        )
    finally:
        runner.git_capture = orig_git
        runner.read_git_blob = orig_blob


def assert_preflight_passes(git=None, blob=None):
    orig_git = runner.git_capture
    orig_blob = runner.read_git_blob
    try:
        runner.git_capture = git or default_git()
        runner.read_git_blob = blob or default_blob()
        result = runner.preflight()
        assert result["preflight_ok"], "preflight errors: {}".format(
            result["preflight_errors"]
        )
        assert result["git_head"] == HEAD
        return result
    finally:
        runner.git_capture = orig_git
        runner.read_git_blob = orig_blob


# ---------------------------------------------------------------------------
# Preflight tests
# ---------------------------------------------------------------------------

def test_preflight_not_main():
    git = default_git()
    git._overrides[("rev-parse", "--abbrev-ref", "HEAD")] = {
        "exit_code": 0, "stdout": "develop", "stderr": ""
    }
    assert_preflight_blocked("BLOCKED_NOT_MAIN", git=git)


def test_preflight_dirty():
    git = default_git()
    git._overrides[("status", "--porcelain=v1")] = {
        "exit_code": 0, "stdout": " M modified.py", "stderr": ""
    }
    assert_preflight_blocked("BLOCKED_DIRTY_WORKTREE", git=git)


def test_preflight_ahead_behind():
    git = default_git()
    git._overrides[("rev-list", "--left-right", "--count",
                     "{}...origin/main".format(HEAD))] = {
        "exit_code": 0, "stdout": "1\t0", "stderr": ""
    }
    assert_preflight_blocked("BLOCKED_AHEAD_BEHIND", git=git)


def test_preflight_unsigned():
    git = default_git()
    git._overrides[("verify-commit", "--raw", HEAD)] = {
        "exit_code": 1, "stdout": "", "stderr": "no signature"
    }
    assert_preflight_blocked("BLOCKED_UNSIGNED", git=git)


def test_preflight_hash_mismatch():
    bad_policy = dict(VALID_POLICY)
    bad_policy["profiles"] = [
        dict(VALID_POLICY["profiles"][0], sha256="0" * 64)
    ]
    blob = FakeReadGitBlob({
        "{}:{}".format(HEAD, runner.POLICY_GIT_PATH): json.dumps(
            bad_policy, indent=2, sort_keys=True
        ).encode("utf-8"),
    })
    assert_preflight_blocked("BLOCKED_PROFILE_SCRIPT_HASH_MISMATCH", blob=blob)


def test_preflight_registered_state():
    bad_policy = dict(VALID_POLICY)
    bad_policy["production_contracts"] = dict(
        VALID_POLICY["production_contracts"], execution_state="REGISTERED"
    )
    blob = FakeReadGitBlob({
        "{}:{}".format(HEAD, runner.POLICY_GIT_PATH): json.dumps(
            bad_policy, indent=2, sort_keys=True
        ).encode("utf-8"),
    })
    assert_preflight_blocked("BLOCKED_PRODUCTION_STATE", blob=blob)


def test_preflight_profile_not_found():
    bad_policy = dict(VALID_POLICY)
    bad_policy["profiles"] = [
        {"profile_id": "other-profile", "sha256": VALID_SHA256}
    ]
    blob = FakeReadGitBlob({
        "{}:{}".format(HEAD, runner.POLICY_GIT_PATH): json.dumps(
            bad_policy, indent=2, sort_keys=True
        ).encode("utf-8"),
    })
    assert_preflight_blocked("BLOCKED_PROFILE_NOT_FOUND", blob=blob)


def test_preflight_p1_p6_not_run():
    bad_policy = dict(VALID_POLICY)
    bad_policy["production_contracts"] = dict(
        VALID_POLICY["production_contracts"], p1_p6_gates="PASS"
    )
    blob = FakeReadGitBlob({
        "{}:{}".format(HEAD, runner.POLICY_GIT_PATH): json.dumps(
            bad_policy, indent=2, sort_keys=True
        ).encode("utf-8"),
    })
    assert_preflight_blocked("BLOCKED_P1_P6_STATE", blob=blob)


def test_preflight_success():
    result = assert_preflight_passes()
    assert result["profile_found"]
    assert result["profile_script_sha256_matches"]
    assert result["execution_state_static"]
    assert result["p1_p6_not_run"]


# ---------------------------------------------------------------------------
# Suite-level tests (mock preflight + MCP)
# ---------------------------------------------------------------------------

def mock_preflight(ok=True):
    return {
        "git_head": HEAD if ok else None,
        "preflight_ok": ok,
        "preflight_errors": [] if ok else ["BLOCKED_MOCKED"],
        "profile_found": ok,
        "profile_script_sha256_matches": ok,
        "execution_state_static": ok,
        "p1_p6_not_run": ok,
    }


class FakeMCP:
    """Replaces runner's MCP imports so run_suite can proceed."""

    def __init__(self):
        self.call_log = []
        self.submit_returned = False
        self.cancel_called = False
        self.poll_phase = "PROCESS_EXITED_0"
        self.poll_attempts = 0
        self.report_status = "PASS_PARTIAL_CAD_CAPABILITY"

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    # Fake session methods
    async def initialize(self):
        return SimpleNamespace(
            protocolVersion="2024-11-05",
            serverInfo=SimpleNamespace(name="test-mcp"),
        )

    async def list_tools(self):
        names = sorted([
            "artifact_manifest", "cancel_job", "inventory",
            "poll_job", "submit_job",
        ])
        return SimpleNamespace(
            tools=[SimpleNamespace(name=n) for n in names]
        )

    async def call_tool(self, name, arguments=None, **kwargs):
        self.call_log.append((name, arguments))
        if name == "inventory":
            return SimpleNamespace(
                isError=False,
                content=[],
                structuredContent={
                    "ready": True,
                    "git_head": HEAD,
                    "approved_profiles": [runner.PROFILE_ID],
                    "profile_contract_sha256": {
                        runner.PROFILE_ID: PROFILE_CONTRACT_SHA256,
                    },
                    "errors": [],
                    "license_data_read": False,
                },
            )
        if name == "submit_job":
            self.submit_returned = True
            return SimpleNamespace(
                isError=False,
                content=[],
                structuredContent={
                    "job_id": "test-job-001",
                    "case_id": runner.CASE_ID,
                    "profile_id": runner.PROFILE_ID,
                    "engine": "spaceclaim",
                    "script_sha256": VALID_SHA256,
                    "profile_contract_sha256": PROFILE_CONTRACT_SHA256,
                    "profile_dependency_manifest_sha256": DEPENDENCY_MANIFEST_SHA256,
                    "profile_dependency_artifacts": [
                        {"relative_path": "dependency-%02d" % index}
                        for index in range(runner.EXPECTED_DEPENDENCY_COUNT)
                    ],
                    "git_head": HEAD,
                    "output_root_id": "p1_cad_006",
                    "license_arguments_added": False,
                    "phase": "RUNNING",
                },
            )
        if name == "poll_job":
            self.poll_attempts += 1
            if self.poll_attempts >= 10:
                return SimpleNamespace(
                    isError=False,
                    content=[],
                    structuredContent={
                        "job_id": "test-job-001",
                        "case_id": runner.CASE_ID,
                        "profile_id": runner.PROFILE_ID,
                        "engine": "spaceclaim",
                        "script_sha256": VALID_SHA256,
                        "profile_contract_sha256": PROFILE_CONTRACT_SHA256,
                        "profile_dependency_manifest_sha256": DEPENDENCY_MANIFEST_SHA256,
                        "git_head": HEAD,
                        "output_root_id": "p1_cad_006",
                        "license_arguments_added": False,
                        "phase": self.poll_phase,
                    },
                )
            return SimpleNamespace(
                isError=False,
                content=[],
                structuredContent={
                    "job_id": "test-job-001",
                    "case_id": runner.CASE_ID,
                    "profile_id": runner.PROFILE_ID,
                    "engine": "spaceclaim",
                    "script_sha256": VALID_SHA256,
                    "profile_contract_sha256": PROFILE_CONTRACT_SHA256,
                    "profile_dependency_manifest_sha256": DEPENDENCY_MANIFEST_SHA256,
                    "git_head": HEAD,
                    "output_root_id": "p1_cad_006",
                    "license_arguments_added": False,
                    "phase": "RUNNING",
                },
            )
        if name == "cancel_job":
            self.cancel_called = True
            return SimpleNamespace(
                isError=False,
                content=[],
                structuredContent={
                    "job_id": "test-job-001",
                    "case_id": runner.CASE_ID,
                    "profile_id": runner.PROFILE_ID,
                    "phase": "CANCELLED",
                },
            )
        if name == "artifact_manifest":
            artifact_entries = []
            producer_files = {}
            for index, (role, filename) in enumerate(
                sorted(runner.EXPECTED_PRODUCER_ARTIFACTS.items())
            ):
                size = 1000 + index
                digest = ("%x" % (index + 1)) * 64
                producer_files[role] = {
                    "path": "D:\\AirJet_P1\\AJM-P1-CAD-006\\" + filename,
                    "size": size,
                    "sha256": digest,
                }
                artifact_entries.append({
                    "relative_path": filename,
                    "size": size,
                    "sha256": digest,
                })
            producer_report = {
                "probe": "v02_preliminary_producer",
                "status": self.report_status,
                "engineering_capability": self.report_status,
                "formal_006_completion": False,
                "p1_stage_gate": "NOT_RUN",
                "p1_p6_gates": "NOT_RUN",
                "identity": {
                    "profile_id": runner.PROFILE_ID,
                    "script_sha256": runner.PROFILE_SCRIPT_SHA256,
                    "profile_contract_sha256": PROFILE_CONTRACT_SHA256,
                    "dependency_manifest_sha256": DEPENDENCY_MANIFEST_SHA256,
                    "git_head": HEAD,
                    "case_id": runner.CASE_ID,
                },
                "assertions": dict(
                    (name, True) for name in runner.EXPECTED_REPORT_ASSERTIONS
                ),
                "files": producer_files,
            }
            return SimpleNamespace(
                isError=False,
                content=[],
                structuredContent={
                    "job_id": "test-job-001",
                    "phase": self.poll_phase,
                    "file_count": 5,
                    "total_size": 12345,
                    "files": [{
                        "relative_path": runner.PRODUCER_REPORT,
                        "size": 512,
                        "sha256": "d" * 64,
                        "report_json": producer_report,
                    }] + artifact_entries,
                },
            )
        raise AssertionError("unexpected tool call: {}".format(name))


def run_suite_with_mocks(
    fake_mcp,
    preflight_ok=True,
    override_poll_phase=None,
):
    """Install mocks on runner, run suite, return (exit_code, result_dict)."""

    if override_poll_phase:
        fake_mcp.poll_phase = override_poll_phase

    originals = {}
    for attr in (
        "preflight", "version", "SERVER", "EXPECTED_PYTHON",
        "OUTPUT_ROOT", "RESULT_PATH", "ClientSession", "StdioServerParameters",
        "stdio_client", "POLL_SECONDS",
    ):
        originals[attr] = getattr(runner, attr, None)

    try:
        runner.preflight = lambda: mock_preflight(preflight_ok)
        runner.version = lambda pkg: "1.28.1"
        runner.SERVER = Path(sys.executable)
        runner.EXPECTED_PYTHON = Path(sys.executable)
        runner.ClientSession = lambda *a, **kw: fake_mcp
        runner.StdioServerParameters = lambda **kw: SimpleNamespace(**kw)
        runner.POLL_SECONDS = 0.001

        @asynccontextmanager
        async def fake_stdio_client(params, errlog=None):
            yield (SimpleNamespace(), SimpleNamespace())

        runner.stdio_client = fake_stdio_client

        with tempfile.TemporaryDirectory(prefix="ajm006-suite-") as tmp:
            root = Path(tmp)
            runner.OUTPUT_ROOT = root
            runner.RESULT_PATH = root / "V02_PRELIMINARY_RUN_SUMMARY.json"
            exit_code = asyncio.run(runner.run_suite())
            result = json.loads(runner.RESULT_PATH.read_text(encoding="utf-8"))
            return exit_code, result, fake_mcp
    finally:
        for attr, val in originals.items():
            if val is not None:
                setattr(runner, attr, val)


def test_suite_blocked_preflight():
    exit_code, result, _ = run_suite_with_mocks(FakeMCP(), preflight_ok=False)
    assert exit_code == 2, "exit_code={}".format(exit_code)
    assert result["final_status"] == "FAIL_PRELIMINARY"
    assert result["error"] is not None
    assert "BLOCKED_PREFLIGHT" in result["error"]["message"]


def test_suite_unknown_poll_state():
    exit_code, result, _ = run_suite_with_mocks(
        FakeMCP(), preflight_ok=True, override_poll_phase="BOGUS_STATE"
    )
    assert exit_code == 2, "exit_code={}".format(exit_code)
    assert result["final_status"] == "FAIL_PRELIMINARY"
    assert result["error"] is not None, "expected error, got success"
    assert "UNKNOWN_TERMINAL_PHASE" in result["error"]["message"], (
        "unexpected error: {}".format(result["error"]["message"])
    )


def test_suite_timeout_cancel():
    """Force immediate timeout by setting wait=0, verify cancel is called."""
    orig_wait = runner.HARD_PROFILE_WAIT_SECONDS
    orig_poll = runner.POLL_SECONDS
    try:
        runner.HARD_PROFILE_WAIT_SECONDS = 0
        runner.POLL_SECONDS = 0.005
        mcp = FakeMCP()
        mcp.poll_phase = "RUNNING"
        exit_code, result, fake = run_suite_with_mocks(
            mcp, preflight_ok=True
        )
        assert exit_code == 2
        assert result["final_status"] == "FAIL_PRELIMINARY"
        assert fake.cancel_called, "cancel was not called on timeout"
    finally:
        runner.HARD_PROFILE_WAIT_SECONDS = orig_wait
        runner.POLL_SECONDS = orig_poll


def test_suite_success():
    exit_code, result, _ = run_suite_with_mocks(
        FakeMCP(), preflight_ok=True, override_poll_phase="PROCESS_EXITED_0"
    )
    assert exit_code == 0, "exit_code={}".format(exit_code)
    assert result["final_status"] == "PASS_PRELIMINARY_PRODUCER"
    assert result["job_id"] == "test-job-001"
    assert result["manifest"] is not None
    assert result["manifest"]["phase"] == "PROCESS_EXITED_0"
    assert result["error"] is None


def test_suite_exit0_invalid_report():
    mcp = FakeMCP()
    mcp.report_status = "FAIL_PRELIMINARY_GEOMETRY"
    exit_code, result, _ = run_suite_with_mocks(
        mcp, preflight_ok=True, override_poll_phase="PROCESS_EXITED_0"
    )
    assert exit_code == 2
    assert result["final_status"] == "FAIL_PRELIMINARY"
    assert "PRODUCER_REPORT_STATUS_OR_PROBE_MISMATCH" in result["error"]["message"]


# ---------------------------------------------------------------------------
#  Main
# ---------------------------------------------------------------------------

def main():
    test_preflight_not_main()
    print("PASS preflight_not_main")

    test_preflight_dirty()
    print("PASS preflight_dirty")

    test_preflight_ahead_behind()
    print("PASS preflight_ahead_behind")

    test_preflight_unsigned()
    print("PASS preflight_unsigned")

    test_preflight_hash_mismatch()
    print("PASS preflight_hash_mismatch")

    test_preflight_registered_state()
    print("PASS preflight_registered_state")

    test_preflight_profile_not_found()
    print("PASS preflight_profile_not_found")

    test_preflight_p1_p6_not_run()
    print("PASS preflight_p1_p6_not_run")

    test_preflight_success()
    print("PASS preflight_success")

    test_suite_blocked_preflight()
    print("PASS suite_blocked_preflight")

    test_suite_unknown_poll_state()
    print("PASS suite_unknown_poll_state")

    test_suite_timeout_cancel()
    print("PASS suite_timeout_cancel")

    test_suite_success()
    print("PASS suite_success")

    test_suite_exit0_invalid_report()
    print("PASS suite_exit0_invalid_report")

    print("\nAJM006_V02_PRELIMINARY_RUNNER_GUARDS=PASS_ALL")


if __name__ == "__main__":
    main()

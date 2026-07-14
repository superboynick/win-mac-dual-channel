#!/usr/bin/env python3
"""Fail-closed local MCP adapter for approved AirJet ANSYS automation profiles."""

from __future__ import annotations

import ctypes
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import IO, Any
from uuid import uuid4

from mcp.server.fastmcp import FastMCP


MCP = FastMCP(
    "AirJet ANSYS Automation",
    instructions=(
        "Run only Git-tracked, hash-pinned AirJet profiles through official ANSYS "
        "interfaces. Never inspect or change licensing and never expose a shell."
    ),
)

REPO = Path(r"C:\Users\admin\win-mac-dual-channel")
SCRIPT_ROOT = REPO / "airjet-simulation" / "automation" / "ansys" / "approved"
POLICY_GIT_PATH = "airjet-simulation/automation/ansys/profiles.json"
SCRIPT_GIT_ROOT = "airjet-simulation/automation/ansys/approved"
ANSYS_ROOT = Path(r"D:\ansys\ANSYS Inc\ANSYS Student\v261")
SPACECLAIM = ANSYS_ROOT / "scdm" / "SpaceClaim.exe"
RUNWB2 = ANSYS_ROOT / "Framework" / "bin" / "Win64" / "RunWB2.exe"
MECHANICAL = ANSYS_ROOT / "aisol" / "bin" / "winx64" / "AnsysWBU.exe"
VENV_PYTHON = Path(
    r"C:\Users\admin\AppData\Local\AirJetAnsysAutomation\.venv\Scripts\python.exe"
)
OUTPUT_ROOTS = {
    "student_smoke_005": Path(
        r"C:\Users\admin\Downloads\AIRJET_ANSYS_STUDENT_SMOKE_005"
    ),
    "p1_cad_006": Path(r"D:\AirJet_P1\AJM-P1-CAD-006"),
}
ENGINE_EXECUTABLES = {
    "spaceclaim": SPACECLAIM,
    "workbench": RUNWB2,
    "pymechanical": VENV_PYTHON,
    "pyfluent": VENV_PYTHON,
}
ENGINE_EXTENSIONS = {
    "spaceclaim": ".py",
    "workbench": ".wbjn",
    "pymechanical": ".py",
    "pyfluent": ".py",
}
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
MAX_ARTIFACTS = 500
MAX_INLINE_REPORT_BYTES = 128 * 1024
MAX_SCRIPT_BYTES = 1024 * 1024
MAX_ARTIFACT_BYTES = 16 * 1024 * 1024 * 1024
MAX_TOTAL_ARTIFACT_BYTES = 64 * 1024 * 1024 * 1024
FILE_ATTRIBUTE_REPARSE_POINT = 0x400
ALLOWED_SIGNER_FINGERPRINTS = {
    "SHA256:jdxP5xJrt8J7PKjeCrJmrEeoAH44u9NxBICo41HwMuc",
    "SHA256:oI3/MIlKz1mgLV3+5n1coQxynaqQOzxqi0GHxreGEdc",
}
EXPECTED_PACKAGES = {
    "mcp": "1.28.1",
    "ansys-fluent-core": "0.40.2",
    "ansys-mechanical-core": "0.12.11",
}


@dataclass
class Job:
    process: subprocess.Popen[bytes]
    stdout: IO[bytes]
    stderr: IO[bytes]
    state_path: Path
    state: dict[str, Any]
    timeout_seconds: int
    job_handle: int | None
    reports: tuple[str, ...]


JOBS: dict[str, Job] = {}
JOBS_LOCK = threading.RLock()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def lexical(path: Path) -> Path:
    return Path(os.path.abspath(os.path.expanduser(str(path))))


def contained(path: Path, root: Path) -> bool:
    try:
        candidate = os.path.normcase(str(lexical(path)))
        boundary = os.path.normcase(str(lexical(root)))
        return os.path.commonpath((candidate, boundary)) == boundary
    except ValueError:
        return False


def is_reparse_point(path: Path) -> bool:
    try:
        details = path.lstat()
    except FileNotFoundError:
        return False
    return bool(getattr(details, "st_file_attributes", 0) & FILE_ATTRIBUTE_REPARSE_POINT)


def reject_existing_reparse_ancestors(path: Path) -> None:
    current = lexical(path)
    chain = [current, *current.parents]
    for item in reversed(chain):
        if item.exists() and (item.is_symlink() or is_reparse_point(item)):
            raise ValueError("BLOCKED_REPARSE_POINT")


def run_capture(args: list[str], timeout: int = 20) -> dict[str, Any]:
    completed = subprocess.run(
        args,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
        stdin=subprocess.DEVNULL,
    )
    return {
        "exit_code": completed.returncode,
        "stdout": completed.stdout[-8000:],
        "stderr": completed.stderr[-8000:],
    }


def run_bytes(args: list[str], timeout: int = 20) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        args,
        capture_output=True,
        timeout=timeout,
        check=False,
        stdin=subprocess.DEVNULL,
    )


def git_text(*args: str) -> str:
    result = run_capture(["git", "-C", str(REPO), *args])
    if result["exit_code"] != 0:
        raise ValueError(f"BLOCKED_GIT_{args[0].upper().replace('-', '_')}")
    return result["stdout"].strip()


def require_git_invariants() -> str:
    head = git_text("rev-parse", "HEAD")
    if not re.fullmatch(r"[0-9a-f]{40}", head):
        raise ValueError("BLOCKED_INVALID_GIT_HEAD")
    if git_text("rev-parse", "--abbrev-ref", "HEAD") != "main":
        raise ValueError("BLOCKED_WRONG_BRANCH")
    if git_text("rev-parse", "refs/heads/main") != head:
        raise ValueError("BLOCKED_HEAD_NOT_MAIN")
    if git_text("rev-parse", "refs/remotes/origin/main") != head:
        raise ValueError("BLOCKED_GIT_NOT_SYNCHRONIZED")
    if git_text("status", "--porcelain=v1"):
        raise ValueError("BLOCKED_DIRTY_WORKTREE")
    verify = run_capture(["git", "-C", str(REPO), "verify-commit", "--raw", head])
    if verify["exit_code"] != 0:
        raise ValueError("BLOCKED_UNVERIFIED_HEAD_SIGNATURE")
    signature_text = verify["stdout"] + verify["stderr"]
    fingerprints = {
        fingerprint
        for fingerprint in ALLOWED_SIGNER_FINGERPRINTS
        if fingerprint in signature_text
    }
    if len(fingerprints) != 1:
        raise ValueError("BLOCKED_UNAPPROVED_HEAD_SIGNER")
    if git_text("rev-parse", "HEAD") != head:
        raise ValueError("BLOCKED_GIT_HEAD_CHANGED_DURING_VALIDATION")
    return head


def read_git_blob(head: str, relative: str) -> bytes:
    if (
        not re.fullmatch(r"[0-9a-f]{40}", head)
        or not relative
        or relative.startswith(("/", "\\"))
        or ".." in Path(relative).parts
        or ":" in relative
    ):
        raise ValueError("BLOCKED_UNSAFE_GIT_BLOB_PATH")
    result = run_bytes(["git", "-C", str(REPO), "show", f"{head}:{relative}"])
    if result.returncode != 0:
        raise ValueError("BLOCKED_MISSING_GIT_BLOB")
    return result.stdout


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_approved_file(head: str, relative: str, expected_sha256: str) -> bytes:
    git_path = f"{SCRIPT_GIT_ROOT}/{relative}"
    data = read_git_blob(head, git_path)
    if len(data) > MAX_SCRIPT_BYTES:
        raise ValueError("BLOCKED_APPROVED_SCRIPT_TOO_LARGE")
    if sha256_bytes(data) != expected_sha256:
        raise ValueError("BLOCKED_APPROVED_SCRIPT_HASH_MISMATCH")
    return data


def load_profiles(head: str) -> dict[str, dict[str, Any]]:
    try:
        policy = json.loads(read_git_blob(head, POLICY_GIT_PATH).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("BLOCKED_PROFILE_POLICY_INVALID_JSON") from exc
    if not isinstance(policy, dict) or set(policy) != {"schema_version", "profiles"}:
        raise ValueError("BLOCKED_PROFILE_POLICY_ROOT")
    if policy.get("schema_version") != 1 or not isinstance(policy.get("profiles"), list):
        raise ValueError("BLOCKED_PROFILE_POLICY_SCHEMA")
    profiles: dict[str, dict[str, Any]] = {}
    for raw in policy.get("profiles", []):
        if not isinstance(raw, dict):
            raise ValueError("BLOCKED_PROFILE_POLICY_ENTRY")
        if set(raw) != {
            "profile_id",
            "engine",
            "script",
            "sha256",
            "timeout_seconds",
            "output_root_id",
            "reports",
        }:
            raise ValueError("BLOCKED_PROFILE_POLICY_FIELDS")
        profile_id = raw.get("profile_id")
        engine = raw.get("engine")
        relative = raw.get("script")
        digest = raw.get("sha256")
        output_root_id = raw.get("output_root_id")
        timeout = raw.get("timeout_seconds")
        reports = raw.get("reports", [])
        if not isinstance(profile_id, str) or not SAFE_ID.fullmatch(profile_id):
            raise ValueError("BLOCKED_PROFILE_ID")
        if profile_id in profiles:
            raise ValueError("BLOCKED_DUPLICATE_PROFILE_ID")
        if engine not in ENGINE_EXTENSIONS:
            raise ValueError("BLOCKED_PROFILE_ENGINE")
        if (
            not isinstance(relative, str)
            or not relative
            or Path(relative).is_absolute()
            or ":" in relative
            or "\\" in relative
        ):
            raise ValueError("BLOCKED_PROFILE_SCRIPT_PATH")
        relative_path = Path(relative)
        if ".." in relative_path.parts or relative_path.suffix.lower() != ENGINE_EXTENSIONS[engine]:
            raise ValueError("BLOCKED_PROFILE_SCRIPT_PATH")
        if not isinstance(digest, str) or not SHA256.fullmatch(digest):
            raise ValueError("BLOCKED_PROFILE_SCRIPT_HASH")
        if output_root_id not in OUTPUT_ROOTS:
            raise ValueError("BLOCKED_PROFILE_OUTPUT_ROOT")
        if not isinstance(timeout, int) or timeout < 30 or timeout > 7200:
            raise ValueError("BLOCKED_PROFILE_TIMEOUT")
        if not isinstance(reports, list) or len(reports) > 20:
            raise ValueError("BLOCKED_PROFILE_REPORTS")
        for report in reports:
            if (
                not isinstance(report, str)
                or not report
                or Path(report).is_absolute()
                or ".." in Path(report).parts
                or ":" in report
                or "\\" in report
                or not report.endswith(".json")
                or report in {"job.json", "stdout.json", "stderr.json"}
            ):
                raise ValueError("BLOCKED_PROFILE_REPORT_PATH")
        profiles[profile_id] = {
            **raw,
            "script_relative": relative_path.as_posix(),
            "reports": reports,
        }
    if not profiles:
        raise ValueError("BLOCKED_PROFILE_POLICY_EMPTY")
    return profiles


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "MISSING"


def authenticode_inventory() -> dict[str, dict[str, Any]]:
    paths = {
        "spaceclaim": SPACECLAIM,
        "workbench": RUNWB2,
        "mechanical": MECHANICAL,
        "fluent": ANSYS_ROOT / "fluent" / "ntbin" / "win64" / "fluent.exe",
    }
    quoted = ",".join("'" + str(path).replace("'", "''") + "'" for path in paths.values())
    script = (
        "[Console]::OutputEncoding=[Text.UTF8Encoding]::new();"
        f"$paths=@({quoted});"
        "$rows=@($paths|ForEach-Object{$s=Get-AuthenticodeSignature -LiteralPath $_;"
        "[pscustomobject]@{Path=$_;Status=[string]$s.Status;"
        "Subject=$(if($s.SignerCertificate){[string]$s.SignerCertificate.Subject}else{''});"
        "Version=$([Diagnostics.FileVersionInfo]::GetVersionInfo($_).FileVersion)}});"
        "$rows|ConvertTo-Json -Compress"
    )
    powershell = r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
    result = run_capture(
        [powershell, "-NoProfile", "-NonInteractive", "-Command", script], timeout=30
    )
    if result["exit_code"] != 0:
        raise ValueError("BLOCKED_AUTHENTICODE_QUERY_FAILED")
    try:
        rows = json.loads(result["stdout"])
    except json.JSONDecodeError as exc:
        raise ValueError("BLOCKED_AUTHENTICODE_QUERY_INVALID") from exc
    if isinstance(rows, dict):
        rows = [rows]
    if not isinstance(rows, list) or len(rows) != len(paths):
        raise ValueError("BLOCKED_AUTHENTICODE_QUERY_INCOMPLETE")
    by_path = {os.path.normcase(row.get("Path", "")): row for row in rows if isinstance(row, dict)}
    inventory: dict[str, dict[str, Any]] = {}
    for name, path in paths.items():
        row = by_path.get(os.path.normcase(str(path)), {})
        inventory[name] = {
            "path": str(path),
            "exists": path.is_file(),
            "status": row.get("Status", "MISSING"),
            "publisher_is_ansys": "ANSYS Inc." in row.get("Subject", ""),
            "file_version": row.get("Version", ""),
        }
    return inventory


def require_runtime_readiness() -> dict[str, dict[str, Any]]:
    if os.path.normcase(str(lexical(Path(sys.executable)))) != os.path.normcase(
        str(lexical(VENV_PYTHON))
    ):
        raise ValueError("BLOCKED_WRONG_AUTOMATION_INTERPRETER")
    reject_existing_reparse_ancestors(VENV_PYTHON)
    if not VENV_PYTHON.is_file():
        raise ValueError("BLOCKED_AUTOMATION_PYTHON_MISSING")
    for name, expected in EXPECTED_PACKAGES.items():
        actual = package_version(name)
        if actual != expected:
            raise ValueError(f"BLOCKED_PACKAGE_VERSION:{name}:{actual}:{expected}")
    for executable in (
        SPACECLAIM,
        RUNWB2,
        MECHANICAL,
        ANSYS_ROOT / "fluent" / "ntbin" / "win64" / "fluent.exe",
    ):
        reject_existing_reparse_ancestors(executable)
    signatures = authenticode_inventory()
    for name, item in signatures.items():
        if not item["exists"] or item["status"] != "Valid" or not item["publisher_is_ansys"]:
            raise ValueError(f"BLOCKED_INVALID_ANSYS_EXECUTABLE:{name}")
    return signatures


def write_state(job: Job) -> None:
    write_state_data(job.state_path, job.state)


def write_state_data(state_path: Path, state: dict[str, Any]) -> None:
    temporary = state_path.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(state, indent=2, sort_keys=True), encoding="utf-8"
    )
    temporary.replace(state_path)


def build_command(engine: str, script: Path, job_dir: Path) -> list[str]:
    executable = ENGINE_EXECUTABLES[engine]
    reject_existing_reparse_ancestors(executable)
    if not executable.is_file():
        raise ValueError("BLOCKED_ENGINE_EXECUTABLE_MISSING")
    if engine == "spaceclaim":
        return [
            str(executable),
            f"/RunScript={script}",
            "/ScriptAPI=V261",
            f"/ScriptOutput={job_dir / 'spaceclaim-script-output.log'}",
            "/Headless=True",
            "/ExitAfterScript=True",
        ]
    if engine == "workbench":
        return [str(executable), "-B", "-R", str(script)]
    return [str(executable), "-I", "-B", str(script)]


def sanitized_environment(job_dir: Path, profile_id: str, case_id: str) -> dict[str, str]:
    temporary = job_dir / "temp"
    temporary.mkdir()
    return {
        "SystemRoot": r"C:\Windows",
        "WINDIR": r"C:\Windows",
        "COMSPEC": r"C:\Windows\System32\cmd.exe",
        "PATH": ";".join(
            (
                str(VENV_PYTHON.parent),
                str(ANSYS_ROOT / "Framework" / "bin" / "Win64"),
                str(ANSYS_ROOT / "fluent" / "ntbin" / "win64"),
                r"C:\Windows\System32",
                r"C:\Windows",
            )
        ),
        "PATHEXT": ".COM;.EXE;.BAT;.CMD",
        "USERPROFILE": r"C:\Users\admin",
        "HOMEDRIVE": "C:",
        "HOMEPATH": r"\Users\admin",
        "APPDATA": r"C:\Users\admin\AppData\Roaming",
        "LOCALAPPDATA": r"C:\Users\admin\AppData\Local",
        "AWP_ROOT261": str(ANSYS_ROOT),
        "AIRJET_JOB_DIR": str(job_dir),
        "AIRJET_PROFILE_ID": profile_id,
        "AIRJET_CASE_ID": case_id,
        "AIRJET_REPO_ROOT": str(REPO),
        "TEMP": str(temporary),
        "TMP": str(temporary),
    }


def create_windows_job_object(process: subprocess.Popen[bytes]) -> int | None:
    if os.name != "nt":
        return None

    class BasicLimitInformation(ctypes.Structure):
        _fields_ = [
            ("PerProcessUserTimeLimit", ctypes.c_longlong),
            ("PerJobUserTimeLimit", ctypes.c_longlong),
            ("LimitFlags", ctypes.c_uint32),
            ("MinimumWorkingSetSize", ctypes.c_size_t),
            ("MaximumWorkingSetSize", ctypes.c_size_t),
            ("ActiveProcessLimit", ctypes.c_uint32),
            ("Affinity", ctypes.c_size_t),
            ("PriorityClass", ctypes.c_uint32),
            ("SchedulingClass", ctypes.c_uint32),
        ]

    class IoCounters(ctypes.Structure):
        _fields_ = [
            ("ReadOperationCount", ctypes.c_uint64),
            ("WriteOperationCount", ctypes.c_uint64),
            ("OtherOperationCount", ctypes.c_uint64),
            ("ReadTransferCount", ctypes.c_uint64),
            ("WriteTransferCount", ctypes.c_uint64),
            ("OtherTransferCount", ctypes.c_uint64),
        ]

    class ExtendedLimitInformation(ctypes.Structure):
        _fields_ = [
            ("BasicLimitInformation", BasicLimitInformation),
            ("IoInfo", IoCounters),
            ("ProcessMemoryLimit", ctypes.c_size_t),
            ("JobMemoryLimit", ctypes.c_size_t),
            ("PeakProcessMemoryUsed", ctypes.c_size_t),
            ("PeakJobMemoryUsed", ctypes.c_size_t),
        ]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateJobObjectW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p]
    kernel32.CreateJobObjectW.restype = ctypes.c_void_p
    kernel32.SetInformationJobObject.argtypes = [
        ctypes.c_void_p,
        ctypes.c_int,
        ctypes.c_void_p,
        ctypes.c_uint32,
    ]
    kernel32.AssignProcessToJobObject.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    kernel32.AssignProcessToJobObject.restype = ctypes.c_int
    kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
    kernel32.CloseHandle.restype = ctypes.c_int
    handle = kernel32.CreateJobObjectW(None, None)
    if not handle:
        raise OSError(ctypes.get_last_error(), "CreateJobObjectW failed")
    information = ExtendedLimitInformation()
    information.BasicLimitInformation.LimitFlags = 0x00002000
    if not kernel32.SetInformationJobObject(
        handle, 9, ctypes.byref(information), ctypes.sizeof(information)
    ):
        error = ctypes.get_last_error()
        kernel32.CloseHandle(handle)
        raise OSError(error, "SetInformationJobObject failed")
    if not kernel32.AssignProcessToJobObject(handle, ctypes.c_void_p(process._handle)):
        error = ctypes.get_last_error()
        kernel32.CloseHandle(handle)
        raise OSError(error, "AssignProcessToJobObject failed")
    return int(handle)


def resume_windows_process(process: subprocess.Popen[bytes]) -> None:
    if os.name != "nt":
        return
    ntdll = ctypes.WinDLL("ntdll", use_last_error=True)
    ntdll.NtResumeProcess.argtypes = [ctypes.c_void_p]
    ntdll.NtResumeProcess.restype = ctypes.c_long
    status = ntdll.NtResumeProcess(ctypes.c_void_p(process._handle))
    if status != 0:
        raise OSError(status, "NtResumeProcess failed")


def active_job_processes(handle: int | None) -> int:
    if not handle or os.name != "nt":
        return 0

    class BasicAccountingInformation(ctypes.Structure):
        _fields_ = [
            ("TotalUserTime", ctypes.c_longlong),
            ("TotalKernelTime", ctypes.c_longlong),
            ("ThisPeriodTotalUserTime", ctypes.c_longlong),
            ("ThisPeriodTotalKernelTime", ctypes.c_longlong),
            ("TotalPageFaultCount", ctypes.c_uint32),
            ("TotalProcesses", ctypes.c_uint32),
            ("ActiveProcesses", ctypes.c_uint32),
            ("TotalTerminatedProcesses", ctypes.c_uint32),
        ]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.QueryInformationJobObject.argtypes = [
        ctypes.c_void_p,
        ctypes.c_int,
        ctypes.c_void_p,
        ctypes.c_uint32,
        ctypes.c_void_p,
    ]
    kernel32.QueryInformationJobObject.restype = ctypes.c_int
    information = BasicAccountingInformation()
    if not kernel32.QueryInformationJobObject(
        ctypes.c_void_p(handle),
        1,
        ctypes.byref(information),
        ctypes.sizeof(information),
        None,
    ):
        raise OSError(ctypes.get_last_error(), "QueryInformationJobObject failed")
    return int(information.ActiveProcesses)


def terminate_windows_job(handle: int | None) -> None:
    if not handle or os.name != "nt":
        return
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.TerminateJobObject.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
    kernel32.TerminateJobObject.restype = ctypes.c_int
    if not kernel32.TerminateJobObject(ctypes.c_void_p(handle), 1):
        raise OSError(ctypes.get_last_error(), "TerminateJobObject failed")


def close_windows_handle(handle: int | None) -> None:
    if not handle or os.name != "nt":
        return
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
    kernel32.CloseHandle.restype = ctypes.c_int
    if not kernel32.CloseHandle(ctypes.c_void_p(handle)):
        raise OSError(ctypes.get_last_error(), "CloseHandle failed")


def finish_job_locked(
    job: Job, phase: str, exit_code: int | None, reason: str | None = None
) -> None:
    if job.state["phase"] != "RUNNING":
        return
    job.stdout.close()
    job.stderr.close()
    try:
        close_windows_handle(job.job_handle)
    except OSError as exc:
        reason = f"{reason or ''};JOB_HANDLE_CLOSE_FAILED:{exc.winerror or exc.errno}".strip(";")
    job.job_handle = None
    job.state["phase"] = phase
    job.state["exit_code"] = exit_code
    job.state["ended_at"] = utc_now()
    job.state["reason"] = reason
    write_state(job)


def terminate_job_locked(job: Job, phase: str, reason: str) -> None:
    if job.state["phase"] != "RUNNING":
        return
    termination_error = None
    try:
        if job.job_handle:
            terminate_windows_job(job.job_handle)
        else:
            job.process.kill()
    except OSError as exc:
        termination_error = f"TERMINATE_FAILED:{exc.winerror or exc.errno}"
    deadline = time.monotonic() + 15.0
    while time.monotonic() < deadline:
        try:
            active = active_job_processes(job.job_handle)
        except OSError:
            active = 1
        if active == 0:
            break
        time.sleep(0.1)
    try:
        exit_code = job.process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        try:
            job.process.kill()
            exit_code = job.process.wait(timeout=2)
        except (OSError, subprocess.TimeoutExpired):
            exit_code = None
            termination_error = termination_error or "PROCESS_TREE_STILL_ACTIVE"
    final_reason = ";".join(part for part in (reason, termination_error) if part)
    final_phase = phase if not termination_error else "FAILED_TERMINATION"
    finish_job_locked(job, final_phase, exit_code, final_reason)


def poll_internal_locked(job: Job) -> None:
    if job.state["phase"] != "RUNNING":
        return
    exit_code = job.process.poll()
    try:
        active = active_job_processes(job.job_handle)
    except OSError as exc:
        terminate_job_locked(job, "FAILED_MONITOR", f"JOB_QUERY_FAILED:{exc.winerror or exc.errno}")
        return
    if exit_code is not None and active == 0:
        finish_job_locked(
            job,
            "PROCESS_EXITED_0" if exit_code == 0 else "FAILED_PROCESS",
            exit_code,
        )


def watch_job(job_id: str) -> None:
    deadline = None
    while True:
        with JOBS_LOCK:
            job = JOBS.get(job_id)
            if job is None or job.state["phase"] != "RUNNING":
                return
            if deadline is None:
                deadline = time.monotonic() + job.timeout_seconds
            poll_internal_locked(job)
            if job.state["phase"] != "RUNNING":
                return
            if time.monotonic() >= deadline:
                terminate_job_locked(job, "TIMED_OUT", "PROFILE_TIMEOUT")
                return
        time.sleep(0.25)


@MCP.tool()
def inventory() -> dict[str, Any]:
    """Return ANSYS, profile, package, and Git readiness without querying licenses."""
    errors: list[str] = []
    head = None
    signatures: dict[str, dict[str, Any]] = {}
    packages = {name: package_version(name) for name in EXPECTED_PACKAGES}
    try:
        reject_existing_reparse_ancestors(REPO)
        head = require_git_invariants()
        profiles = load_profiles(head)
        for profile in profiles.values():
            read_approved_file(head, profile["script_relative"], profile["sha256"])
            executable = ENGINE_EXECUTABLES[profile["engine"]]
            reject_existing_reparse_ancestors(executable)
            if not executable.is_file():
                errors.append(f"BLOCKED_ENGINE_EXECUTABLE_MISSING:{profile['engine']}")
        signatures = require_runtime_readiness()
    except (OSError, ValueError) as exc:
        errors.append(str(exc))
        profiles = {}
    for name, expected in EXPECTED_PACKAGES.items():
        if packages[name] != expected:
            errors.append(f"BLOCKED_PACKAGE_VERSION:{name}:{packages[name]}:{expected}")
    return {
        "schema_version": 2,
        "ready": not errors,
        "errors": errors,
        "repo": str(REPO),
        "git_head": head,
        "ansys_root": str(ANSYS_ROOT),
        "executables": signatures,
        "automation_python": {"path": str(VENV_PYTHON), "exists": VENV_PYTHON.is_file()},
        "packages": packages,
        "approved_profiles": sorted(profiles),
        "license_data_read": False,
    }


@MCP.tool()
def submit_job(profile_id: str, case_id: str) -> dict[str, Any]:
    """Start one hash-pinned profile; callers cannot supply paths, commands, or environment."""
    if not SAFE_ID.fullmatch(profile_id) or not SAFE_ID.fullmatch(case_id):
        raise ValueError("BLOCKED_INVALID_ID")
    with JOBS_LOCK:
        for active in JOBS.values():
            poll_internal_locked(active)
            if active.state["phase"] == "RUNNING":
                raise ValueError("BLOCKED_ONE_JOB_AT_A_TIME")

        git_head = require_git_invariants()
        profiles = load_profiles(git_head)
        if profile_id not in profiles:
            raise ValueError("BLOCKED_UNKNOWN_PROFILE")
        profile = profiles[profile_id]
        require_runtime_readiness()
        source_data = read_approved_file(
            git_head, profile["script_relative"], profile["sha256"]
        )

        output_root = lexical(OUTPUT_ROOTS[profile["output_root_id"]])
        reject_existing_reparse_ancestors(output_root)
        output_root.mkdir(parents=True, exist_ok=True)
        reject_existing_reparse_ancestors(output_root)
        job_id = f"{case_id}-{uuid4().hex[:12]}"
        job_dir = output_root / case_id / job_id
        if not contained(job_dir, output_root):
            raise ValueError("BLOCKED_OUTPUT_OUTSIDE_APPROVED_ROOT")
        job_dir.mkdir(parents=True, exist_ok=False)
        reject_existing_reparse_ancestors(job_dir)
        input_dir = job_dir / "input"
        input_dir.mkdir()
        execution_script = input_dir / Path(profile["script_relative"]).name
        execution_script.write_bytes(source_data)
        if sha256_bytes(execution_script.read_bytes()) != profile["sha256"]:
            raise ValueError("BLOCKED_EXECUTION_COPY_HASH_MISMATCH")
        execution_script.chmod(stat.S_IREAD)
        reject_existing_reparse_ancestors(execution_script)

        state_path = job_dir / "job.json"
        state: dict[str, Any] = {
            "schema_version": 3,
            "job_id": job_id,
            "case_id": case_id,
            "profile_id": profile_id,
            "engine": profile["engine"],
            "script_sha256": profile["sha256"],
            "git_head": git_head,
            "output_root_id": profile["output_root_id"],
            "job_directory": str(job_dir),
            "pid": None,
            "phase": "PREPARING",
            "exit_code": None,
            "started_at": utc_now(),
            "ended_at": None,
            "reason": None,
            "license_arguments_added": False,
        }
        write_state_data(state_path, state)

        command = build_command(profile["engine"], execution_script, job_dir)
        stdout_path = job_dir / "stdout.log"
        stderr_path = job_dir / "stderr.log"
        stdout = stdout_path.open("wb")
        stderr = stderr_path.open("wb")
        creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        if os.name == "nt":
            creationflags |= 0x00000004  # CREATE_SUSPENDED
        process: subprocess.Popen[bytes] | None = None
        job_handle: int | None = None
        try:
            process = subprocess.Popen(
                command,
                cwd=job_dir,
                env=sanitized_environment(job_dir, profile_id, case_id),
                stdin=subprocess.DEVNULL,
                stdout=stdout,
                stderr=stderr,
                creationflags=creationflags,
                shell=False,
            )
            job_handle = create_windows_job_object(process)
            resume_windows_process(process)
        except Exception:
            if job_handle:
                try:
                    terminate_windows_job(job_handle)
                except OSError:
                    pass
                try:
                    close_windows_handle(job_handle)
                except OSError:
                    pass
            if process is not None:
                try:
                    process.kill()
                    process.wait(timeout=5)
                except (OSError, subprocess.TimeoutExpired):
                    pass
            stdout.close()
            stderr.close()
            state["phase"] = "FAILED_START"
            state["ended_at"] = utc_now()
            state["reason"] = "PROCESS_START_OR_JOB_ASSIGN_FAILED"
            write_state_data(state_path, state)
            raise

        state["pid"] = process.pid
        state["phase"] = "RUNNING"
        job = Job(
            process=process,
            stdout=stdout,
            stderr=stderr,
            state_path=state_path,
            state=state,
            timeout_seconds=profile["timeout_seconds"],
            job_handle=job_handle,
            reports=tuple(profile["reports"]),
        )
        JOBS[job_id] = job
        try:
            write_state(job)
            watcher = threading.Thread(
                target=watch_job,
                args=(job_id,),
                name=f"airjet-ansys-{job_id}",
                daemon=True,
            )
            watcher.start()
        except Exception:
            terminate_job_locked(job, "FAILED_START", "STATE_OR_WATCHDOG_START_FAILED")
            raise
        return dict(state)


@MCP.tool()
def poll_job(job_id: str) -> dict[str, Any]:
    """Poll a job created by this server and enforce its profile timeout."""
    with JOBS_LOCK:
        if job_id not in JOBS:
            raise ValueError("BLOCKED_UNKNOWN_OR_SERVER_RESTARTED_JOB")
        job = JOBS[job_id]
        poll_internal_locked(job)
        return dict(job.state)


@MCP.tool()
def cancel_job(job_id: str) -> dict[str, Any]:
    """Cancel only a running job created by this MCP server."""
    with JOBS_LOCK:
        if job_id not in JOBS:
            raise ValueError("BLOCKED_UNKNOWN_OR_SERVER_RESTARTED_JOB")
        job = JOBS[job_id]
        poll_internal_locked(job)
        if job.state["phase"] == "RUNNING":
            terminate_job_locked(job, "CANCELLED", "REQUESTED_CANCEL")
        return dict(job.state)


def hash_file(path: Path) -> tuple[int, str]:
    size = path.stat(follow_symlinks=False).st_size
    if size > MAX_ARTIFACT_BYTES:
        raise ValueError("BLOCKED_ARTIFACT_FILE_TOO_LARGE")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return size, digest.hexdigest()


def walk_artifacts(root: Path) -> list[Path]:
    files: list[Path] = []
    for current_text, directories, names in os.walk(root, topdown=True, followlinks=False):
        current = Path(current_text)
        reject_existing_reparse_ancestors(current)
        directories.sort()
        names.sort()
        for directory in directories:
            candidate = current / directory
            if candidate.is_symlink() or is_reparse_point(candidate):
                raise ValueError("BLOCKED_ARTIFACT_REPARSE_POINT")
        for name in names:
            candidate = current / name
            if candidate.is_symlink() or is_reparse_point(candidate):
                raise ValueError("BLOCKED_ARTIFACT_REPARSE_POINT")
            details = os.stat(candidate, follow_symlinks=False)
            if not stat.S_ISREG(details.st_mode):
                raise ValueError("BLOCKED_NONREGULAR_ARTIFACT")
            files.append(candidate)
            if len(files) > MAX_ARTIFACTS:
                raise ValueError("BLOCKED_MANIFEST_TOO_MANY_FILES")
    return files


@MCP.tool()
def artifact_manifest(job_id: str) -> dict[str, Any]:
    """Hash one known job directory and inline only profile-declared small reports."""
    with JOBS_LOCK:
        if job_id not in JOBS:
            raise ValueError("BLOCKED_UNKNOWN_OR_SERVER_RESTARTED_JOB")
        job = JOBS[job_id]
        poll_internal_locked(job)
        if job.state["phase"] == "RUNNING":
            raise ValueError("BLOCKED_JOB_STILL_RUNNING")
        job_dir = job.state_path.parent
        reject_existing_reparse_ancestors(job_dir)
        declared_reports = set(job.reports)
        entries: list[dict[str, Any]] = []
        total_size = 0
        for path in walk_artifacts(job_dir):
            if not contained(path, job_dir):
                raise ValueError("BLOCKED_ARTIFACT_OUTSIDE_JOB")
            size, digest = hash_file(path)
            total_size += size
            if total_size > MAX_TOTAL_ARTIFACT_BYTES:
                raise ValueError("BLOCKED_ARTIFACT_TOTAL_TOO_LARGE")
            relative = path.relative_to(job_dir).as_posix()
            entry: dict[str, Any] = {
                "relative_path": relative,
                "size": size,
                "sha256": digest,
            }
            if relative in declared_reports:
                if size > MAX_INLINE_REPORT_BYTES:
                    entry["report_error"] = "DECLARED_REPORT_TOO_LARGE"
                else:
                    try:
                        report = json.loads(path.read_text(encoding="utf-8"))
                        if not isinstance(report, dict):
                            raise ValueError
                        entry["report_json"] = report
                    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
                        entry["report_error"] = "DECLARED_REPORT_INVALID_JSON"
            entries.append(entry)
        return {
            "job_id": job_id,
            "phase": job.state["phase"],
            "file_count": len(entries),
            "total_size": total_size,
            "files": entries,
        }


if __name__ == "__main__":
    MCP.run(transport="stdio")

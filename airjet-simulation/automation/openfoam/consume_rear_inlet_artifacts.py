#!/usr/bin/env python3
"""Read-only, fail-closed host consumer for the accepted rear-inlet artifacts.

This module verifies artifact bytes only.  It does not create an OpenFOAM case,
launch a solver, or advance any AirJet stage gate.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import re
import stat
import sys
import unicodedata
from dataclasses import asdict, dataclass
from decimal import Decimal
from pathlib import Path, PureWindowsPath
from typing import Any, BinaryIO, Iterator

from validate_rear_inlet_handoff import validate_manifest


ALLOWED_ARTIFACT_ROOT = Path(
    r"D:\AirJet_P1\AJM-P1-CAD-006\ajm-rear-inlet-009-mcp"
    r"\ajm-rear-inlet-009-mcp-fbff57daa893"
)
EXPECTED_HANDOFF_PATH = Path(__file__).absolute().with_name(
    "rear_inlet_handoff_accepted_20260720.json"
)
EXPECTED_HANDOFF_SHA256 = (
    "e3a571534208feeccdaaa7e1d09f8b16162f509a23753c026f0d7894517c00da"
)
EXPECTED_ARTIFACT_ATTESTATIONS = {
    "native": (
        "D:/AirJet_P1/AJM-P1-CAD-006/ajm-rear-inlet-009-mcp/"
        "ajm-rear-inlet-009-mcp-fbff57daa893/product_continuous_fluid.scdocx",
        6_957_892,
        "50223b0fd0d70b80ce7d4abd4e267e44fb2c66c1a4ae77f117629953b08cae9e",
    ),
    "step": (
        "D:/AirJet_P1/AJM-P1-CAD-006/ajm-rear-inlet-009-mcp/"
        "ajm-rear-inlet-009-mcp-fbff57daa893/product_continuous_fluid.step",
        1_806_621,
        "b1ce3b9016f74663a7fdb686b122f491f9df391a668d86b43c33a5132e477fa4",
    ),
    "runtime_report": (
        "D:/AirJet_P1/AJM-P1-CAD-006/ajm-rear-inlet-009-mcp/"
        "ajm-rear-inlet-009-mcp-fbff57daa893/v03_continuous_fluid_producer.json",
        16_056,
        "6bd4604baa6b9c7631e99ff8a517ce782d3c006de13301c31f9955a12def0c4b",
    ),
}
EXPECTED_ROLES = frozenset({"native", "step", "runtime_report"})
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SAFE_FINDING_PATH_RE = re.compile(r"^\$(?:(?:\.[A-Za-z_][A-Za-z0-9_]*)|(?:\[[0-9]+\]))*$")
MAX_MANIFEST_BYTES = 1_048_576
MAX_JSON_DEPTH = 16
MAX_JSON_NODES = 4_096
READ_CHUNK_BYTES = 1_048_576
FILE_ATTRIBUTE_REPARSE_POINT = 0x400


@dataclass(frozen=True)
class ConsumerFinding:
    code: str
    path: str
    message: str


@dataclass(frozen=True)
class VerifiedArtifact:
    role: str
    size_bytes: int
    sha256: str


@dataclass(frozen=True)
class ConsumptionResult:
    accepted: bool
    findings: tuple[ConsumerFinding, ...]
    artifacts: tuple[VerifiedArtifact, ...]

    def as_json_object(self) -> dict[str, Any]:
        return {
            "accepted": self.accepted,
            "scope": "READ_ONLY_ARTIFACT_VERIFICATION_ONLY",
            "stage_gate_advanced": False,
            "solver_authorized": False,
            "findings": [asdict(item) for item in self.findings],
            "artifacts": [asdict(item) for item in self.artifacts],
        }


class DuplicateKeyError(ValueError):
    pass


class NonFiniteNumberError(ValueError):
    pass


class ArtifactRejected(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(code)
        self.code = code
        self.safe_message = message


def _duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError
        result[key] = value
    return result


def _reject_nonfinite(_value: str) -> Any:
    raise NonFiniteNumberError


def _finding(code: str, path: str, message: str) -> ConsumerFinding:
    return ConsumerFinding(code=code, path=path, message=message)


def _rejected_result(*findings: ConsumerFinding) -> ConsumptionResult:
    return ConsumptionResult(False, tuple(findings), ())


def _redact_manifest_finding(item: Any) -> ConsumerFinding:
    safe_path = item.path if isinstance(item.path, str) and SAFE_FINDING_PATH_RE.fullmatch(item.path) else "$"
    return _finding(item.code, safe_path, item.message)


def _validate_json_complexity(value: Any) -> None:
    """Bound container depth and node count without recursive traversal."""
    nodes = 0
    stack: list[tuple[Any, int]] = [(value, 1)]
    while stack:
        item, depth = stack.pop()
        nodes += 1
        if nodes > MAX_JSON_NODES or depth > MAX_JSON_DEPTH:
            raise ValueError
        if isinstance(item, dict):
            stack.extend((child, depth + 1) for child in item.values())
        elif isinstance(item, list):
            stack.extend((child, depth + 1) for child in item)


def _manifest_style_path(path: Path) -> str:
    return str(path.absolute()).replace("\\", "/")


def _has_reparse_attribute(file_stat: os.stat_result) -> bool:
    attributes = int(getattr(file_stat, "st_file_attributes", 0))
    return bool(attributes & FILE_ATTRIBUTE_REPARSE_POINT)


def _stable_identity(file_stat: os.stat_result) -> tuple[int, int] | None:
    device = int(file_stat.st_dev)
    inode = int(file_stat.st_ino)
    if inode == 0:
        return None
    return device, inode


def _same_windows_path(left: Path, right: Path) -> bool:
    return os.path.normcase(os.path.normpath(str(left.absolute()))) == os.path.normcase(
        os.path.normpath(str(right.absolute()))
    )


def _opened_final_path(stream: BinaryIO, fallback_path: Path) -> Path:
    """Return the kernel-resolved name for the already-open file handle."""
    if os.name == "nt":
        import ctypes
        import msvcrt
        from ctypes import wintypes

        get_final_path = ctypes.WinDLL("kernel32", use_last_error=True).GetFinalPathNameByHandleW
        get_final_path.argtypes = (
            wintypes.HANDLE,
            wintypes.LPWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
        )
        get_final_path.restype = wintypes.DWORD
        handle = msvcrt.get_osfhandle(stream.fileno())
        required = get_final_path(handle, None, 0, 0)
        if required == 0:
            raise OSError(ctypes.get_last_error(), "final path lookup failed")
        buffer = ctypes.create_unicode_buffer(required + 1)
        written = get_final_path(handle, buffer, len(buffer), 0)
        if written == 0 or written >= len(buffer):
            raise OSError(ctypes.get_last_error(), "final path lookup failed")
        value = buffer.value
        if value.startswith("\\\\?\\UNC\\"):
            value = "\\\\" + value[8:]
        elif value.startswith("\\\\?\\"):
            value = value[4:]
        return Path(value)

    descriptor_link = Path(f"/proc/self/fd/{stream.fileno()}")
    if descriptor_link.exists():
        return Path(os.path.realpath(descriptor_link))
    return Path(os.path.realpath(fallback_path))


def _validate_lexical_path(value: Any, allowed_root: Path) -> Path:
    if not isinstance(value, str) or not value:
        raise ArtifactRejected("B.CONSUME.PATH.FORMAT", "artifact path is not canonical")
    if "\\" in value or "\x00" in value or unicodedata.normalize("NFC", value) != value:
        raise ArtifactRejected("B.CONSUME.PATH.ALIAS", "artifact path alias is rejected")
    if value.startswith("//") or not re.match(r"^[A-Z]:/", value):
        raise ArtifactRejected("B.CONSUME.PATH.ABSOLUTE", "artifact path must be a canonical drive path")

    raw_parts = value.split("/")
    if len(raw_parts) < 2 or any(part == "" for part in raw_parts[1:]):
        raise ArtifactRejected("B.CONSUME.PATH.ALIAS", "artifact path alias is rejected")
    for part in raw_parts[1:]:
        if part in {".", ".."}:
            raise ArtifactRejected("B.CONSUME.PATH.TRAVERSAL", "path traversal is rejected")
        if part.endswith((" ", ".")) or ":" in part:
            raise ArtifactRejected("B.CONSUME.PATH.ALIAS", "artifact path alias is rejected")
        if any(ord(character) < 32 for character in part):
            raise ArtifactRejected("B.CONSUME.PATH.FORMAT", "artifact path contains a control character")
        if PureWindowsPath(part).is_reserved():
            raise ArtifactRejected("B.CONSUME.PATH.RESERVED", "reserved path component is rejected")

    root_text = _manifest_style_path(allowed_root)
    if not re.match(r"^[A-Z]:/", root_text):
        raise ArtifactRejected("B.CONSUME.CONFIG.ROOT", "configured artifact root is not an absolute drive path")
    prefix = root_text + "/"
    if not value.startswith(prefix):
        if value.casefold().startswith(prefix.casefold()):
            raise ArtifactRejected("B.CONSUME.PATH.CASE_ALIAS", "artifact path case alias is rejected")
        raise ArtifactRejected("B.CONSUME.PATH.OUTSIDE_ROOT", "artifact path is outside the allowed root")

    relative_parts = value[len(prefix) :].split("/")
    if not relative_parts or any(not part for part in relative_parts):
        raise ArtifactRejected("B.CONSUME.PATH.ALIAS", "artifact path alias is rejected")
    return allowed_root.joinpath(*relative_parts)


def _walk_exact_case(target: Path) -> os.stat_result:
    """Inspect every component without following a symlink or reparse point."""
    absolute = target.absolute()
    parts = absolute.parts
    if not parts or not absolute.is_absolute():
        raise ArtifactRejected("B.CONSUME.PATH.ABSOLUTE", "artifact path is not absolute")

    current = Path(parts[0])
    for index, wanted in enumerate(parts[1:], start=1):
        try:
            with os.scandir(current) as entries:
                matches = [entry for entry in entries if entry.name.casefold() == wanted.casefold()]
        except FileNotFoundError:
            raise ArtifactRejected("B.CONSUME.FILE.MISSING", "artifact or parent directory is missing") from None
        except OSError:
            raise ArtifactRejected("B.CONSUME.FILE.ACCESS", "artifact path cannot be inspected") from None
        if not matches:
            raise ArtifactRejected("B.CONSUME.FILE.MISSING", "artifact or parent directory is missing")
        if len(matches) != 1:
            raise ArtifactRejected("B.CONSUME.PATH.CASE_COLLISION", "case-colliding directory entries are rejected")
        entry = matches[0]
        if entry.name != wanted:
            raise ArtifactRejected("B.CONSUME.PATH.CASE_ALIAS", "artifact path case alias is rejected")
        try:
            entry_stat = entry.stat(follow_symlinks=False)
        except OSError:
            raise ArtifactRejected("B.CONSUME.FILE.ACCESS", "artifact path cannot be inspected") from None
        if stat.S_ISLNK(entry_stat.st_mode) or _has_reparse_attribute(entry_stat):
            raise ArtifactRejected("B.CONSUME.PATH.REPARSE", "symlink or reparse point is rejected")
        is_last = index == len(parts) - 1
        if not is_last and not stat.S_ISDIR(entry_stat.st_mode):
            raise ArtifactRejected("B.CONSUME.PATH.PARENT_TYPE", "artifact parent is not a directory")
        current = Path(entry.path)

    try:
        final_stat = os.lstat(current)
    except FileNotFoundError:
        raise ArtifactRejected("B.CONSUME.FILE.MISSING", "artifact is missing") from None
    except OSError:
        raise ArtifactRejected("B.CONSUME.FILE.ACCESS", "artifact cannot be inspected") from None
    if stat.S_ISLNK(final_stat.st_mode) or _has_reparse_attribute(final_stat):
        raise ArtifactRejected("B.CONSUME.PATH.REPARSE", "symlink or reparse point is rejected")
    if not stat.S_ISREG(final_stat.st_mode):
        raise ArtifactRejected("B.CONSUME.FILE.NOT_REGULAR", "artifact is not a regular file")
    if int(final_stat.st_nlink) != 1:
        raise ArtifactRejected("B.CONSUME.PATH.HARDLINK", "multiply linked artifact is rejected")
    return final_stat


@contextlib.contextmanager
def _open_read_only(path: Path) -> Iterator[BinaryIO]:
    """Open without following the final reparse point; deny Windows writes/deletes."""
    if os.name == "nt":
        import ctypes
        import msvcrt
        from ctypes import wintypes

        create_file = ctypes.WinDLL("kernel32", use_last_error=True).CreateFileW
        create_file.argtypes = (
            wintypes.LPCWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.LPVOID,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.HANDLE,
        )
        create_file.restype = wintypes.HANDLE
        handle = create_file(
            str(path),
            0x80000000,  # GENERIC_READ
            0x00000001,  # FILE_SHARE_READ only: deny writes and deletes while hashing
            None,
            3,  # OPEN_EXISTING
            0x00200000 | 0x08000000,  # OPEN_REPARSE_POINT | SEQUENTIAL_SCAN
            None,
        )
        invalid_handle = wintypes.HANDLE(-1).value
        if handle == invalid_handle:
            raise OSError(ctypes.get_last_error(), "secure read-only open failed")
        try:
            descriptor = msvcrt.open_osfhandle(handle, os.O_RDONLY | os.O_BINARY)
        except BaseException:
            ctypes.WinDLL("kernel32", use_last_error=True).CloseHandle(handle)
            raise
        with os.fdopen(descriptor, "rb", closefd=True) as stream:
            yield stream
        return

    flags = os.O_RDONLY
    flags |= getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    with os.fdopen(descriptor, "rb", closefd=True) as stream:
        yield stream


def _verify_one(path: Path, expected_size: int, expected_hash: str) -> tuple[int, str]:
    pre_stat = _walk_exact_case(path)
    pre_identity = _stable_identity(pre_stat)
    if pre_identity is None:
        raise ArtifactRejected("B.CONSUME.IDENTITY.UNAVAILABLE", "stable artifact identity is unavailable")
    if pre_stat.st_size == 0:
        raise ArtifactRejected("B.CONSUME.FILE.ZERO_LENGTH", "zero-length artifact is rejected")
    if pre_stat.st_size != expected_size:
        raise ArtifactRejected("B.CONSUME.FILE.SIZE_MISMATCH", "artifact size differs from the manifest")

    try:
        with _open_read_only(path) as stream:
            opened_stat = os.fstat(stream.fileno())
            if stat.S_ISLNK(opened_stat.st_mode) or _has_reparse_attribute(opened_stat):
                raise ArtifactRejected("B.CONSUME.PATH.REPARSE", "symlink or reparse point is rejected")
            if not stat.S_ISREG(opened_stat.st_mode):
                raise ArtifactRejected("B.CONSUME.FILE.NOT_REGULAR", "artifact is not a regular file")
            opened_identity = _stable_identity(opened_stat)
            if opened_identity is None or opened_identity != pre_identity:
                raise ArtifactRejected("B.CONSUME.IDENTITY.DRIFT", "artifact identity changed before hashing")
            if opened_stat.st_size != expected_size:
                raise ArtifactRejected("B.CONSUME.FILE.SIZE_DRIFT", "artifact size changed before hashing")
            opened_final_path = _opened_final_path(stream, path)
            if not _same_windows_path(opened_final_path, path):
                raise ArtifactRejected("B.CONSUME.PATH.HANDLE_REDIRECT", "opened artifact resolved to a different path")

            digest = hashlib.sha256()
            while True:
                chunk = stream.read(READ_CHUNK_BYTES)
                if not chunk:
                    break
                digest.update(chunk)
            observed_hash = digest.hexdigest()

            post_fd_stat = os.fstat(stream.fileno())
            post_path_stat = _walk_exact_case(path)
            post_final_path = _opened_final_path(stream, path)
            post_identity = _stable_identity(post_path_stat)
            if (
                _stable_identity(post_fd_stat) != opened_identity
                or post_identity != opened_identity
            ):
                raise ArtifactRejected("B.CONSUME.IDENTITY.DRIFT", "artifact identity changed while hashing")
            if not _same_windows_path(post_final_path, path):
                raise ArtifactRejected("B.CONSUME.PATH.HANDLE_REDIRECT", "opened artifact path changed while hashing")
            if post_fd_stat.st_size != expected_size or post_path_stat.st_size != expected_size:
                raise ArtifactRejected("B.CONSUME.FILE.SIZE_DRIFT", "artifact size changed while hashing")
            if (
                post_fd_stat.st_mtime_ns != opened_stat.st_mtime_ns
                or post_path_stat.st_mtime_ns != opened_stat.st_mtime_ns
            ):
                raise ArtifactRejected("B.CONSUME.CONTENT.DRIFT", "artifact metadata changed while hashing")
    except ArtifactRejected:
        raise
    except FileNotFoundError:
        raise ArtifactRejected("B.CONSUME.FILE.MISSING", "artifact disappeared before verification") from None
    except OSError:
        raise ArtifactRejected("B.CONSUME.FILE.ACCESS", "artifact cannot be opened read-only") from None

    if SHA256_RE.fullmatch(observed_hash) is None:
        raise ArtifactRejected("B.CONSUME.HASH.FORMAT", "computed SHA-256 is not canonical lowercase hex")
    if observed_hash != expected_hash:
        raise ArtifactRejected("B.CONSUME.HASH.MISMATCH", "artifact SHA-256 differs from the manifest")
    return expected_size, observed_hash


def consume_manifest(manifest: Any) -> ConsumptionResult:
    """Validate the descriptor first, then verify every artifact without mutation."""
    manifest_findings = validate_manifest(manifest)
    if manifest_findings:
        return _rejected_result(
            *(_redact_manifest_finding(item) for item in manifest_findings)
        )
    if set(EXPECTED_ARTIFACT_ATTESTATIONS) != EXPECTED_ROLES:
        return _rejected_result(
            _finding(
                "B.CONSUME.CONFIG.ATTESTATION_SET",
                "$.artifacts",
                "configured artifact attestations are incomplete",
            )
        )

    artifacts = manifest["artifacts"]
    findings: list[ConsumerFinding] = []
    candidates: list[tuple[int, str, Path, int, str]] = []
    seen_roles: set[str] = set()
    seen_paths: set[str] = set()

    for index, artifact in enumerate(artifacts):
        item_path = f"$.artifacts[{index}]"
        role = artifact["role"]
        if role in seen_roles:
            findings.append(_finding("B.CONSUME.ROLE.DUPLICATE", f"{item_path}.role", "duplicate artifact role is rejected"))
        seen_roles.add(role)
        expected_attestation = EXPECTED_ARTIFACT_ATTESTATIONS.get(role)
        if expected_attestation is not None:
            expected_path, pinned_size, pinned_hash = expected_attestation
            if artifact["path"] != expected_path:
                findings.append(_finding("B.CONSUME.ATTESTATION.PATH", f"{item_path}.path", "artifact path differs from the accepted handoff"))
            if artifact["size_bytes"] != pinned_size:
                findings.append(_finding("B.CONSUME.ATTESTATION.SIZE", f"{item_path}.size_bytes", "artifact size differs from the accepted handoff"))
            if artifact["sha256_observed"] != pinned_hash:
                findings.append(_finding("B.CONSUME.ATTESTATION.HASH", f"{item_path}.sha256_observed", "artifact SHA-256 differs from the accepted handoff"))
        try:
            candidate = _validate_lexical_path(artifact["path"], ALLOWED_ARTIFACT_ROOT)
        except ArtifactRejected as exc:
            findings.append(_finding(exc.code, f"{item_path}.path", exc.safe_message))
            continue
        path_key = _manifest_style_path(candidate).casefold()
        if path_key in seen_paths:
            findings.append(_finding("B.CONSUME.PATH.DUPLICATE", f"{item_path}.path", "duplicate artifact path is rejected"))
        seen_paths.add(path_key)
        expected_hash = artifact["sha256_observed"]
        if SHA256_RE.fullmatch(expected_hash) is None:
            findings.append(_finding("B.CONSUME.HASH.FORMAT", f"{item_path}.sha256_observed", "expected canonical lowercase SHA-256"))
            continue
        candidates.append((index, role, candidate, artifact["size_bytes"], expected_hash))

    if seen_roles != EXPECTED_ROLES:
        findings.append(_finding("B.CONSUME.ROLE.SET", "$.artifacts", "exactly native, step, and runtime_report are required"))
    if findings:
        return ConsumptionResult(False, tuple(findings), ())

    verified: list[VerifiedArtifact] = []
    for index, role, candidate, expected_size, expected_hash in candidates:
        try:
            size, observed_hash = _verify_one(candidate, expected_size, expected_hash)
        except ArtifactRejected as exc:
            findings.append(_finding(exc.code, f"$.artifacts[{index}].path", exc.safe_message))
            continue
        verified.append(VerifiedArtifact(role=role, size_bytes=size, sha256=observed_hash))

    if findings or len(verified) != len(EXPECTED_ROLES):
        return ConsumptionResult(False, tuple(findings), ())
    return ConsumptionResult(True, (), tuple(verified))


def _load_source_manifest(path: Path) -> tuple[Any, str]:
    with _open_read_only(path) as handle:
        before = os.fstat(handle.fileno())
        if stat.S_ISLNK(before.st_mode) or _has_reparse_attribute(before):
            raise ValueError
        if not stat.S_ISREG(before.st_mode) or before.st_size < 1 or before.st_size > MAX_MANIFEST_BYTES:
            raise ValueError
        if not _same_windows_path(_opened_final_path(handle, path), path):
            raise ValueError
        identity = _stable_identity(before)
        if identity is None:
            raise ValueError
        data = handle.read(MAX_MANIFEST_BYTES + 1)
        after = os.fstat(handle.fileno())
        if len(data) > MAX_MANIFEST_BYTES or len(data) != before.st_size:
            raise ValueError
        if (
            _stable_identity(after) != identity
            or after.st_size != before.st_size
            or after.st_mtime_ns != before.st_mtime_ns
        ):
            raise ValueError
    manifest = json.loads(
        data.decode("utf-8"),
        parse_float=Decimal,
        parse_constant=_reject_nonfinite,
        object_pairs_hook=_duplicate_keys,
    )
    _validate_json_complexity(manifest)
    return manifest, hashlib.sha256(data).hexdigest()


def _print_result(result: ConsumptionResult) -> None:
    print(json.dumps(result.as_json_object(), indent=2, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", help="absolute path to the accepted JSON handoff manifest")
    args = parser.parse_args(argv)
    source = Path(args.manifest)
    if not source.is_absolute():
        _print_result(_rejected_result(_finding("B.CONSUME.INPUT.ABSOLUTE", "$.source_manifest", "source manifest path must be absolute")))
        return 3
    if not _same_windows_path(source, EXPECTED_HANDOFF_PATH):
        _print_result(_rejected_result(_finding("B.CONSUME.INPUT.IDENTITY", "$.source_manifest", "source manifest is not the accepted handoff")))
        return 3
    try:
        manifest, source_hash = _load_source_manifest(source)
    except DuplicateKeyError:
        _print_result(_rejected_result(_finding("B.CONSUME.INPUT.JSON_DUPLICATE_KEY", "$.source_manifest", "duplicate JSON object key is rejected")))
        return 3
    except NonFiniteNumberError:
        _print_result(_rejected_result(_finding("B.CONSUME.INPUT.JSON_NONFINITE", "$.source_manifest", "non-finite JSON number is rejected")))
        return 3
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError, RecursionError, MemoryError, OverflowError):
        _print_result(_rejected_result(_finding("B.CONSUME.INPUT.JSON", "$.source_manifest", "source manifest cannot be read as bounded UTF-8 JSON")))
        return 3
    if source_hash != EXPECTED_HANDOFF_SHA256:
        _print_result(_rejected_result(_finding("B.CONSUME.INPUT.IDENTITY", "$.source_manifest", "source manifest is not the accepted handoff")))
        return 3

    result = consume_manifest(manifest)
    _print_result(result)
    return 0 if result.accepted else 2


if __name__ == "__main__":
    sys.exit(main())

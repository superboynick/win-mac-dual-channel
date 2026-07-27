#!/usr/bin/env python3
"""Handle-anchored, read-only verification of coupling artifact bytes.

Artifact directories are opened from the bound root and retained.  Every
artifact handle is opened before hashing begins and retained until both hash
passes and final directory-entry checks complete.  Windows handles deny write
and delete sharing; POSIX traversal uses ``dir_fd`` plus ``O_NOFOLLOW``.
"""

from __future__ import annotations

import hashlib
import os
import re
import stat
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any, Iterable


MAX_CONTRACT_BYTES = 1_048_576
MAX_ARTIFACT_BYTES = 512 * 1024 * 1024
MAX_TOTAL_ARTIFACT_BYTES = 1024 * 1024 * 1024
READ_CHUNK_BYTES = 1024 * 1024
MAX_DIRECTORY_ENTRIES = 100_000
REPARSE_POINT_ATTRIBUTE = 0x400
WINDOWS_DEVICE = re.compile(
    r"^(?:con|prn|aux|nul|clock\$|com[1-9]|lpt[1-9])(?:\..*)?$",
    re.IGNORECASE,
)


class SafeArtifactError(ValueError):
    """A rejection with a fixed, caller-safe code."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class VerifiedArtifact:
    role: str
    size_bytes: int
    sha256: str


@dataclass
class _HeldDirectory:
    path: str
    identity: tuple[int, ...]
    fd: int | None = None
    win_handle: int | None = None


@dataclass
class _HeldArtifact:
    role: str
    expected_size: int
    expected_hash: str
    parent: _HeldDirectory
    name: str
    path: str
    fd: int
    identity: tuple[int, ...]


def _identity(value: os.stat_result) -> tuple[int, ...]:
    device = getattr(value, "st_dev", None)
    inode = getattr(value, "st_ino", None)
    if (
        isinstance(device, bool)
        or not isinstance(device, int)
        or device <= 0
        or isinstance(inode, bool)
        or not isinstance(inode, int)
        or inode <= 0
    ):
        raise SafeArtifactError("IDENTITY_UNAVAILABLE")
    common = (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_nlink,
        value.st_size,
        value.st_mtime_ns,
    )
    # Windows creation/change time is not a reliable mutation clock.  POSIX
    # ctime is required so same-size writes followed by mtime restoration fail.
    return common if os.name == "nt" else common + (value.st_ctime_ns,)


def _is_reparse(value: os.stat_result) -> bool:
    return bool(getattr(value, "st_file_attributes", 0) & REPARSE_POINT_ATTRIBUTE)


def _safe_lstat(path: str, code: str) -> os.stat_result:
    try:
        return os.lstat(path)
    except (OSError, ValueError, TypeError) as exc:
        raise SafeArtifactError(code) from exc


def _regular_single_link(value: os.stat_result, code: str) -> None:
    if (
        not stat.S_ISREG(value.st_mode)
        or stat.S_ISLNK(value.st_mode)
        or _is_reparse(value)
        or value.st_nlink != 1
    ):
        raise SafeArtifactError(code)


def _handle_final_path(fd: int) -> str | None:
    if os.name == "nt":
        try:
            import ctypes
            import msvcrt
            from ctypes import wintypes

            handle = msvcrt.get_osfhandle(fd)
            get_final_path = ctypes.WinDLL(
                "kernel32", use_last_error=True
            ).GetFinalPathNameByHandleW
            get_final_path.argtypes = (
                wintypes.HANDLE,
                wintypes.LPWSTR,
                wintypes.DWORD,
                wintypes.DWORD,
            )
            get_final_path.restype = wintypes.DWORD
            needed = get_final_path(handle, None, 0, 0)
            if not needed:
                return None
            buffer = ctypes.create_unicode_buffer(needed + 1)
            written = get_final_path(handle, buffer, len(buffer), 0)
            if not written or written >= len(buffer):
                return None
            value = buffer.value
            if value.startswith("\\\\?\\UNC\\"):
                value = "\\\\" + value[8:]
            elif value.startswith("\\\\?\\"):
                value = value[4:]
            return os.path.normpath(value)
        except (AttributeError, OSError, TypeError, ValueError):
            return None
    if sys.platform == "darwin":
        try:
            import fcntl

            # Python caps fcntl bytes-like arguments at 1024 bytes; Darwin's
            # MAXPATHLEN is also 1024.
            value = fcntl.fcntl(fd, 50, b"\0" * 1024)
            return os.path.normpath(os.fsdecode(value.split(b"\0", 1)[0]))
        except (OSError, TypeError, ValueError):
            return None
    try:
        return os.path.normpath(os.readlink(f"/proc/self/fd/{fd}"))
    except (OSError, ValueError):
        return None


def _win_final_directory_path(handle: int) -> str | None:
    try:
        import ctypes
        from ctypes import wintypes

        get_final_path = ctypes.WinDLL(
            "kernel32", use_last_error=True
        ).GetFinalPathNameByHandleW
        get_final_path.argtypes = (
            wintypes.HANDLE,
            wintypes.LPWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
        )
        get_final_path.restype = wintypes.DWORD
        needed = get_final_path(handle, None, 0, 0)
        if not needed:
            return None
        buffer = ctypes.create_unicode_buffer(needed + 1)
        written = get_final_path(handle, buffer, len(buffer), 0)
        if not written or written >= len(buffer):
            return None
        value = buffer.value
        if value.startswith("\\\\?\\UNC\\"):
            value = "\\\\" + value[8:]
        elif value.startswith("\\\\?\\"):
            value = value[4:]
        return os.path.normpath(value)
    except (AttributeError, OSError, TypeError, ValueError):
        return None


def _win_directory_identity(handle: int) -> tuple[int, ...]:
    import ctypes
    from ctypes import wintypes

    class FILETIME(ctypes.Structure):
        _fields_ = [("low", wintypes.DWORD), ("high", wintypes.DWORD)]

    class FILE_INFO(ctypes.Structure):
        _fields_ = [
            ("attributes", wintypes.DWORD),
            ("creation", FILETIME),
            ("access", FILETIME),
            ("write", FILETIME),
            ("volume", wintypes.DWORD),
            ("size_high", wintypes.DWORD),
            ("size_low", wintypes.DWORD),
            ("links", wintypes.DWORD),
            ("index_high", wintypes.DWORD),
            ("index_low", wintypes.DWORD),
        ]

    info = FILE_INFO()
    get_info = ctypes.WinDLL(
        "kernel32", use_last_error=True
    ).GetFileInformationByHandle
    get_info.argtypes = (wintypes.HANDLE, wintypes.LPVOID)
    get_info.restype = wintypes.BOOL
    if not get_info(handle, ctypes.byref(info)):
        raise SafeArtifactError("ARTIFACT_IDENTITY_DRIFT")
    identity = (
        int(info.volume),
        (int(info.index_high) << 32) | int(info.index_low),
        int(info.attributes),
        int(info.links),
        (int(info.size_high) << 32) | int(info.size_low),
        (int(info.write.high) << 32) | int(info.write.low),
    )
    if identity[0] == 0 or identity[1] == 0:
        raise SafeArtifactError("IDENTITY_UNAVAILABLE")
    return identity


def _win_open_directory(path: str, code: str) -> int:
    import ctypes
    from ctypes import wintypes

    create_file = ctypes.windll.kernel32.CreateFileW
    create_file.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    create_file.restype = wintypes.HANDLE
    handle = create_file(
        path,
        0x80000000,  # GENERIC_READ
        0x00000001,  # FILE_SHARE_READ only: deny write and delete sharing
        None,
        3,  # OPEN_EXISTING
        0x02000000 | 0x00200000,  # BACKUP_SEMANTICS | OPEN_REPARSE_POINT
        None,
    )
    invalid = ctypes.c_void_p(-1).value
    if handle in (None, invalid):
        raise SafeArtifactError(code)
    return int(handle)


def _win_open_file(path: str, code: str) -> int:
    import ctypes
    import msvcrt
    from ctypes import wintypes

    create_file = ctypes.windll.kernel32.CreateFileW
    create_file.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    create_file.restype = wintypes.HANDLE
    handle = create_file(
        path,
        0x80000000,
        0x00000001,  # read sharing only
        None,
        3,
        0x00200000 | 0x08000000,  # OPEN_REPARSE_POINT | SEQUENTIAL_SCAN
        None,
    )
    invalid = ctypes.c_void_p(-1).value
    if handle in (None, invalid):
        raise SafeArtifactError(code)
    try:
        return msvcrt.open_osfhandle(
            int(handle), os.O_RDONLY | getattr(os, "O_BINARY", 0)
        )
    except (OSError, ValueError) as exc:
        _win_close_handle(int(handle))
        raise SafeArtifactError(code) from exc


def _win_close_handle(handle: int) -> bool:
    try:
        import ctypes
        from ctypes import wintypes

        close_handle = ctypes.WinDLL(
            "kernel32", use_last_error=True
        ).CloseHandle
        close_handle.argtypes = (wintypes.HANDLE,)
        close_handle.restype = wintypes.BOOL
        return bool(close_handle(handle))
    except (AttributeError, OSError, TypeError, ValueError):
        return False


def _close_directory(directory: _HeldDirectory) -> None:
    if directory.fd is not None:
        try:
            os.close(directory.fd)
        except OSError:
            pass
    elif directory.win_handle is not None:
        _win_close_handle(directory.win_handle)


def _hash_fd(fd: int, maximum: int, code: str) -> tuple[int, str]:
    try:
        os.lseek(fd, 0, os.SEEK_SET)
        digest = hashlib.sha256()
        total = 0
        while True:
            chunk = os.read(fd, min(READ_CHUNK_BYTES, maximum + 1 - total))
            if not chunk:
                break
            total += len(chunk)
            if total > maximum:
                raise SafeArtifactError(code)
            digest.update(chunk)
        return total, digest.hexdigest()
    except SafeArtifactError:
        raise
    except (OSError, MemoryError, OverflowError) as exc:
        raise SafeArtifactError(code) from exc


def _read_fd_bytes(fd: int, maximum: int, code: str) -> bytes:
    try:
        os.lseek(fd, 0, os.SEEK_SET)
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(fd, min(READ_CHUNK_BYTES, maximum + 1 - total))
            if not chunk:
                break
            total += len(chunk)
            if total > maximum:
                raise SafeArtifactError(code)
            chunks.append(chunk)
        return b"".join(chunks)
    except SafeArtifactError:
        raise
    except (OSError, MemoryError, OverflowError) as exc:
        raise SafeArtifactError(code) from exc


def _open_absolute_file(path: str, code: str) -> int:
    if os.name == "nt":
        return _win_open_file(path, code)
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        return os.open(path, flags)
    except (OSError, ValueError, TypeError) as exc:
        raise SafeArtifactError(code) from exc


def read_bounded_regular_file(path: str, maximum: int, code: str) -> tuple[bytes, str]:
    """Read a stable small file twice through one retained handle."""
    before_path = _safe_lstat(path, code)
    _regular_single_link(before_path, code)
    if before_path.st_size < 1 or before_path.st_size > maximum:
        raise SafeArtifactError(code)
    fd = _open_absolute_file(path, code)
    try:
        before = os.fstat(fd)
        _regular_single_link(before, code)
        if _identity(before) != _identity(before_path):
            raise SafeArtifactError(code)
        final = _handle_final_path(fd)
        if final is None or os.path.normcase(os.path.abspath(final)) != os.path.normcase(
            os.path.abspath(path)
        ):
            raise SafeArtifactError(code)
        first = _read_fd_bytes(fd, maximum, code)
        after_first = os.fstat(fd)
        second = _read_fd_bytes(fd, maximum, code)
        after_second = os.fstat(fd)
        after_path = _safe_lstat(path, code)
        if (
            len(first) != before.st_size
            or first != second
            or _identity(after_first) != _identity(before)
            or _identity(after_second) != _identity(before)
            or _identity(after_path) != _identity(before)
            or _handle_final_path(fd) != final
        ):
            raise SafeArtifactError(code)
        return first, hashlib.sha256(first).hexdigest()
    finally:
        os.close(fd)


def hash_bounded_regular_file(path: str, maximum: int, code: str) -> tuple[int, str]:
    """Compatibility helper: stable double-hash without retaining content."""
    fd = _open_absolute_file(path, code)
    try:
        before = os.fstat(fd)
        _regular_single_link(before, code)
        first = _hash_fd(fd, maximum, code)
        if _identity(os.fstat(fd)) != _identity(before):
            raise SafeArtifactError(code)
        second = _hash_fd(fd, maximum, code)
        if first != second or _identity(os.fstat(fd)) != _identity(before):
            raise SafeArtifactError(code)
        return first
    finally:
        os.close(fd)


def validate_relative_posix_path(value: Any) -> tuple[str, ...]:
    if not isinstance(value, str) or not value or len(value) > 1024:
        raise SafeArtifactError("ARTIFACT_PATH_REJECTED")
    if value != unicodedata.normalize("NFC", value):
        raise SafeArtifactError("ARTIFACT_PATH_REJECTED")
    if (
        value.startswith("/")
        or "\\" in value
        or ":" in value
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        raise SafeArtifactError("ARTIFACT_PATH_REJECTED")
    parts = value.split("/")
    if any(
        not part
        or part in {".", ".."}
        or part.endswith((".", " "))
        or WINDOWS_DEVICE.fullmatch(part)
        for part in parts
    ):
        raise SafeArtifactError("ARTIFACT_PATH_REJECTED")
    if PurePosixPath(*parts).as_posix() != value:
        raise SafeArtifactError("ARTIFACT_PATH_REJECTED")
    return tuple(parts)


def _exact_name(names: Iterable[str], requested: str) -> None:
    exact = False
    aliases = 0
    requested_key = unicodedata.normalize("NFC", requested).casefold()
    for count, name in enumerate(names, start=1):
        if count > MAX_DIRECTORY_ENTRIES:
            raise SafeArtifactError("ARTIFACT_PATH_REJECTED")
        if unicodedata.normalize("NFC", name).casefold() == requested_key:
            aliases += 1
            exact = exact or name == requested
    if not exact or aliases != 1:
        raise SafeArtifactError("ARTIFACT_PATH_REJECTED")


def _scan_exact_path(parent: str, segment: str) -> str:
    try:
        with os.scandir(parent) as entries:
            _exact_name((entry.name for entry in entries), segment)
    except SafeArtifactError:
        raise
    except (OSError, ValueError, TypeError) as exc:
        raise SafeArtifactError("ARTIFACT_PATH_REJECTED") from exc
    return os.path.join(parent, segment)


def _scan_exact_fd(parent_fd: int, segment: str) -> None:
    try:
        with os.scandir(parent_fd) as entries:
            _exact_name((entry.name for entry in entries), segment)
    except SafeArtifactError:
        raise
    except (OSError, ValueError, TypeError) as exc:
        raise SafeArtifactError("ARTIFACT_PATH_REJECTED") from exc


def _bind_root(root: str) -> _HeldDirectory:
    if not isinstance(root, str) or not os.path.isabs(root):
        raise SafeArtifactError("ROOT_CONFIG_REJECTED")
    canonical = os.path.normpath(root)
    if os.name == "nt":
        drive, tail = os.path.splitdrive(canonical)
        if drive.startswith("\\\\") or drive != drive.upper():
            raise SafeArtifactError("ROOT_REJECTED")
        parent = drive + os.sep
        for segment in [part for part in re.split(r"[\\/]+", tail) if part]:
            parent = _scan_exact_path(parent, segment)
            value = _safe_lstat(parent, "ROOT_REJECTED")
            if (
                not stat.S_ISDIR(value.st_mode)
                or stat.S_ISLNK(value.st_mode)
                or _is_reparse(value)
            ):
                raise SafeArtifactError("ROOT_REJECTED")
        handle = _win_open_directory(canonical, "ROOT_REJECTED")
        try:
            final = _win_final_directory_path(handle)
            if final is None or os.path.normpath(final) != canonical:
                raise SafeArtifactError("ROOT_REJECTED")
            identity = _win_directory_identity(handle)
            if identity[2] & REPARSE_POINT_ATTRIBUTE:
                raise SafeArtifactError("ROOT_REJECTED")
            return _HeldDirectory(canonical, identity, win_handle=handle)
        except BaseException:
            _win_close_handle(handle)
            raise
    flags = (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    current_fd: int | None = None
    try:
        current_fd = os.open(os.sep, flags)
        for segment in [part for part in canonical.split(os.sep) if part]:
            _scan_exact_fd(current_fd, segment)
            next_fd = os.open(segment, flags, dir_fd=current_fd)
            try:
                value = os.fstat(next_fd)
                if not stat.S_ISDIR(value.st_mode):
                    raise SafeArtifactError("ROOT_REJECTED")
                _identity(value)
            except BaseException:
                os.close(next_fd)
                raise
            os.close(current_fd)
            current_fd = next_fd
    except SafeArtifactError:
        if current_fd is not None:
            os.close(current_fd)
        raise
    except (OSError, ValueError, TypeError) as exc:
        if current_fd is not None:
            os.close(current_fd)
        raise SafeArtifactError("ROOT_REJECTED") from exc
    try:
        if current_fd is None:
            raise SafeArtifactError("ROOT_REJECTED")
        value = os.fstat(current_fd)
        if not stat.S_ISDIR(value.st_mode):
            raise SafeArtifactError("ROOT_REJECTED")
        final = _handle_final_path(current_fd)
        if final is None or os.path.normpath(final) != canonical:
            raise SafeArtifactError("ROOT_REJECTED")
        return _HeldDirectory(canonical, _identity(value), fd=current_fd)
    except BaseException:
        if current_fd is not None:
            os.close(current_fd)
        raise


def _open_child_directory(parent: _HeldDirectory, segment: str) -> _HeldDirectory:
    path = os.path.join(parent.path, segment)
    if os.name == "nt":
        path = _scan_exact_path(parent.path, segment)
        handle = _win_open_directory(path, "ARTIFACT_PATH_REJECTED")
        try:
            identity = _win_directory_identity(handle)
            if identity[2] & REPARSE_POINT_ATTRIBUTE:
                raise SafeArtifactError("ARTIFACT_PATH_REJECTED")
            final = _win_final_directory_path(handle)
            if final is None or final != os.path.normpath(path):
                raise SafeArtifactError("ARTIFACT_PATH_REJECTED")
            return _HeldDirectory(path, identity, win_handle=handle)
        except BaseException:
            _win_close_handle(handle)
            raise
    if parent.fd is None:
        raise SafeArtifactError("ARTIFACT_PATH_REJECTED")
    _scan_exact_fd(parent.fd, segment)
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    fd: int | None = None
    try:
        fd = os.open(segment, flags, dir_fd=parent.fd)
        value = os.fstat(fd)
    except (OSError, ValueError, TypeError) as exc:
        if fd is not None:
            os.close(fd)
        raise SafeArtifactError("ARTIFACT_PATH_REJECTED") from exc
    try:
        if fd is None:
            raise SafeArtifactError("ARTIFACT_PATH_REJECTED")
        if not stat.S_ISDIR(value.st_mode):
            raise SafeArtifactError("ARTIFACT_PATH_REJECTED")
        return _HeldDirectory(path, _identity(value), fd=fd)
    except BaseException:
        os.close(fd)
        raise


def _open_artifact(
    parent: _HeldDirectory,
    name: str,
    role: str,
    expected_size: int,
    expected_hash: str,
) -> _HeldArtifact:
    path = os.path.join(parent.path, name)
    if os.name == "nt":
        path = _scan_exact_path(parent.path, name)
        fd = _win_open_file(path, "ARTIFACT_PATH_REJECTED")
    else:
        if parent.fd is None:
            raise SafeArtifactError("ARTIFACT_PATH_REJECTED")
        _scan_exact_fd(parent.fd, name)
        flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
        try:
            fd = os.open(name, flags, dir_fd=parent.fd)
        except (OSError, ValueError, TypeError) as exc:
            raise SafeArtifactError("ARTIFACT_PATH_REJECTED") from exc
    try:
        value = os.fstat(fd)
        _regular_single_link(value, "ARTIFACT_PATH_REJECTED")
        if value.st_size != expected_size or value.st_size > MAX_ARTIFACT_BYTES:
            raise SafeArtifactError("ARTIFACT_BYTES_MISMATCH")
        final = _handle_final_path(fd)
        if final is None or os.path.normcase(final) != os.path.normcase(os.path.normpath(path)):
            raise SafeArtifactError("ARTIFACT_PATH_REJECTED")
        return _HeldArtifact(
            role, expected_size, expected_hash, parent, name, path, fd, _identity(value)
        )
    except BaseException:
        os.close(fd)
        raise


def _directory_identity(directory: _HeldDirectory) -> tuple[int, ...]:
    if os.name == "nt":
        if directory.win_handle is None:
            raise SafeArtifactError("ARTIFACT_IDENTITY_DRIFT")
        return _win_directory_identity(directory.win_handle)
    if directory.fd is None:
        raise SafeArtifactError("ARTIFACT_IDENTITY_DRIFT")
    return _identity(os.fstat(directory.fd))


def _reopen_final_identity(artifact: _HeldArtifact) -> tuple[int, ...]:
    if os.name == "nt":
        fd = _win_open_file(artifact.path, "ARTIFACT_IDENTITY_DRIFT")
    else:
        if artifact.parent.fd is None:
            raise SafeArtifactError("ARTIFACT_IDENTITY_DRIFT")
        try:
            fd = os.open(
                artifact.name,
                os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
                dir_fd=artifact.parent.fd,
            )
        except (OSError, ValueError, TypeError) as exc:
            raise SafeArtifactError("ARTIFACT_IDENTITY_DRIFT") from exc
    try:
        value = os.fstat(fd)
        _regular_single_link(value, "ARTIFACT_IDENTITY_DRIFT")
        return _identity(value)
    finally:
        os.close(fd)


def verify_artifacts(root: str, declarations: Iterable[dict[str, Any]]) -> tuple[VerifiedArtifact, ...]:
    """Verify an all-or-nothing set using retained directory and file handles."""
    prepared: list[tuple[str, tuple[str, ...], int, str]] = []
    declared_total = 0
    seen_paths: set[tuple[str, ...]] = set()
    for item in list(declarations):
        try:
            role = item["role"]
            size = item["size_bytes"]
            digest = item["sha256"]
            parts = validate_relative_posix_path(item["path"])
        except (KeyError, TypeError) as exc:
            raise SafeArtifactError("ARTIFACT_DECLARATION_REJECTED") from exc
        if (
            not isinstance(role, str)
            or isinstance(size, bool)
            or not isinstance(size, int)
            or size < 1
            or size > MAX_ARTIFACT_BYTES
            or not isinstance(digest, str)
            or re.fullmatch(r"[0-9a-f]{64}", digest) is None
            or parts in seen_paths
        ):
            raise SafeArtifactError("ARTIFACT_DECLARATION_REJECTED")
        seen_paths.add(parts)
        declared_total += size
        if declared_total > MAX_TOTAL_ARTIFACT_BYTES:
            raise SafeArtifactError("ARTIFACT_TOTAL_LIMIT")
        prepared.append((role, parts, size, digest))

    directories: list[_HeldDirectory] = []
    directory_cache: dict[tuple[str, ...], _HeldDirectory] = {}
    artifacts: list[_HeldArtifact] = []
    try:
        root_handle = _bind_root(root)
        directories.append(root_handle)
        directory_cache[()] = root_handle
        for role, parts, size, digest in prepared:
            prefix: tuple[str, ...] = ()
            parent = root_handle
            for segment in parts[:-1]:
                prefix += (segment,)
                child = directory_cache.get(prefix)
                if child is None:
                    child = _open_child_directory(parent, segment)
                    directories.append(child)
                    directory_cache[prefix] = child
                parent = child
            artifacts.append(
                _open_artifact(parent, parts[-1], role, size, digest)
            )

        first_pass: list[tuple[int, str]] = []
        for artifact in artifacts:
            observed = _hash_fd(
                artifact.fd, artifact.expected_size, "ARTIFACT_READ_REJECTED"
            )
            if (
                observed != (artifact.expected_size, artifact.expected_hash)
                or _identity(os.fstat(artifact.fd)) != artifact.identity
            ):
                raise SafeArtifactError("ARTIFACT_BYTES_MISMATCH")
            first_pass.append(observed)

        second_pass: list[tuple[int, str]] = []
        for artifact, first in zip(artifacts, first_pass):
            observed = _hash_fd(
                artifact.fd, artifact.expected_size, "ARTIFACT_READ_REJECTED"
            )
            if (
                observed != first
                or _identity(os.fstat(artifact.fd)) != artifact.identity
            ):
                raise SafeArtifactError("ARTIFACT_IDENTITY_DRIFT")
            second_pass.append(observed)

        for directory in directories:
            if _directory_identity(directory) != directory.identity:
                raise SafeArtifactError("ARTIFACT_IDENTITY_DRIFT")
        for artifact in artifacts:
            if (
                _identity(os.fstat(artifact.fd)) != artifact.identity
                or _reopen_final_identity(artifact) != artifact.identity
                or _handle_final_path(artifact.fd) != os.path.normpath(artifact.path)
            ):
                raise SafeArtifactError("ARTIFACT_IDENTITY_DRIFT")
        return tuple(
            VerifiedArtifact(artifact.role, observed[0], observed[1])
            for artifact, observed in zip(artifacts, second_pass)
        )
    except SafeArtifactError:
        raise
    except (OSError, ValueError, TypeError, MemoryError, OverflowError) as exc:
        raise SafeArtifactError("ARTIFACT_READ_REJECTED") from exc
    finally:
        for artifact in reversed(artifacts):
            try:
                os.close(artifact.fd)
            except OSError:
                pass
        for directory in reversed(directories):
            _close_directory(directory)

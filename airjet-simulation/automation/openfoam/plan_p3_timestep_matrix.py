#!/usr/bin/env python3
"""Create a deterministic, planning-only P3 steps-per-cycle matrix."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import sys
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path
from typing import Any, NoReturn, Sequence


SCHEMA = "AJM_PLAN_B_P3_TIMESTEP_PLAN_V1"
MAX_BYTES = 1_048_576
MAX_DEPTH = 12
MAX_NODES = 1024
MAX_STRING = 128
DECIMAL_RE = re.compile(r"^(0|[1-9][0-9]*)(\.[0-9]+)?([eE][+-]?[0-9]+)?$")
HEX40_RE = re.compile(r"^[0-9a-f]{40}$")
EXPECTED_KEYS = frozenset(
    {
        "schema_version",
        "source_commit",
        "case_scope",
        "frequency_hz",
        "frequency_status",
        "steps_per_cycle",
        "ramp_cycles",
        "monitored_cycles",
        "sample_every_steps",
        "p2_displacement_authorized",
        "solver_authorized",
        "formal_gate_effect",
    }
)


class PlanError(ValueError):
    pass


def fail(code: str) -> NoReturn:
    raise PlanError(code)


def is_link_or_reparse(value: os.stat_result) -> bool:
    return stat.S_ISLNK(value.st_mode) or bool(
        getattr(value, "st_file_attributes", 0)
        & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    )


def safe_lstat(path: Path, phase: str) -> os.stat_result:
    try:
        return os.lstat(path)
    except OSError as exc:
        raise PlanError(f"INPUT_{phase}_LSTAT_FAILED_{exc.__class__.__name__}") from exc


def read_stable(path: Path) -> tuple[bytes, str]:
    pre = safe_lstat(path, "PREOPEN")
    if is_link_or_reparse(pre):
        fail("INPUT_LINK_OR_REPARSE_REJECTED")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise PlanError(f"INPUT_OPEN_FAILED_{exc.__class__.__name__}") from exc
    try:
        before = os.fstat(fd)
        opened = safe_lstat(path, "POSTOPEN")
        if is_link_or_reparse(opened):
            fail("INPUT_LINK_OR_REPARSE_REJECTED")
        if (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
            fail("INPUT_PATH_IDENTITY_MISMATCH")
        if not stat.S_ISREG(before.st_mode):
            fail("INPUT_NOT_REGULAR")
        if before.st_size <= 0:
            fail("INPUT_EMPTY")
        if before.st_size > MAX_BYTES:
            fail("INPUT_SIZE_LIMIT_EXCEEDED")
        chunks: list[bytes] = []
        remaining = MAX_BYTES + 1
        while remaining:
            chunk = os.read(fd, min(65_536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        data = b"".join(chunks)
        after = os.fstat(fd)
        final = safe_lstat(path, "FINAL")
        if is_link_or_reparse(final):
            fail("INPUT_LINK_OR_REPARSE_REJECTED")
        if (
            final.st_dev,
            final.st_ino,
            final.st_size,
            final.st_mtime_ns,
        ) != (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
        ):
            fail("INPUT_FINAL_PATH_METADATA_MISMATCH")
    finally:
        os.close(fd)
    if len(data) > MAX_BYTES:
        fail("INPUT_SIZE_LIMIT_EXCEEDED")
    if (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
    ) != (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
    ) or len(data) != before.st_size:
        fail("INPUT_CHANGED_DURING_READ")
    if b"\x00" in data:
        fail("INPUT_NUL_REJECTED")
    return data, hashlib.sha256(data).hexdigest()


def duplicate_guard(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            fail("DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def preflight_depth(data: bytes) -> None:
    depth = 0
    quoted = False
    escaped = False
    for byte in data:
        if quoted:
            if escaped:
                escaped = False
            elif byte == 0x5C:
                escaped = True
            elif byte == 0x22:
                quoted = False
        elif byte == 0x22:
            quoted = True
        elif byte in (0x7B, 0x5B):
            depth += 1
            if depth > MAX_DEPTH:
                fail("JSON_DEPTH_LIMIT_EXCEEDED")
        elif byte in (0x7D, 0x5D):
            depth -= 1


def count_nodes(value: Any, depth: int = 0) -> int:
    if depth > MAX_DEPTH:
        fail("JSON_DEPTH_LIMIT_EXCEEDED")
    if isinstance(value, str):
        if len(value) > MAX_STRING:
            fail("JSON_STRING_LIMIT_EXCEEDED")
        return 1
    if isinstance(value, dict):
        total = 1
        for key, child in value.items():
            if not isinstance(key, str) or len(key) > MAX_STRING:
                fail("JSON_KEY_INVALID")
            total += 1 + count_nodes(child, depth + 1)
            if total > MAX_NODES:
                fail("JSON_NODE_LIMIT_EXCEEDED")
        return total
    if isinstance(value, list):
        total = 1
        for child in value:
            total += count_nodes(child, depth + 1)
            if total > MAX_NODES:
                fail("JSON_NODE_LIMIT_EXCEEDED")
        return total
    return 1


def load_contract(path: Path) -> tuple[dict[str, Any], str]:
    data, digest = read_stable(path)
    if data.startswith(b"\xef\xbb\xbf"):
        fail("INPUT_UTF8_BOM_REJECTED")
    preflight_depth(data)
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PlanError("INPUT_NOT_UTF8") from exc
    try:
        value = json.loads(
            text,
            object_pairs_hook=duplicate_guard,
            parse_int=lambda token: int(token)
            if len(token) <= 12
            else fail("JSON_INTEGER_LIMIT_EXCEEDED"),
            parse_float=lambda _token: fail("JSON_NUMBER_MUST_BE_STRING"),
            parse_constant=lambda _token: fail("JSON_NONFINITE_REJECTED"),
        )
    except PlanError:
        raise
    except (json.JSONDecodeError, RecursionError) as exc:
        raise PlanError("INPUT_INVALID_JSON") from exc
    count_nodes(value)
    if not isinstance(value, dict) or set(value) != EXPECTED_KEYS:
        fail("CONTRACT_KEYS_MISMATCH")
    return value, digest


def require_int(value: Any, low: int, high: int, code: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
        fail(code)
    return value


def validate(value: dict[str, Any]) -> tuple[Decimal, int, int]:
    if value["schema_version"] != SCHEMA:
        fail("SCHEMA_MISMATCH")
    if not isinstance(value["source_commit"], str) or not HEX40_RE.fullmatch(
        value["source_commit"]
    ):
        fail("SOURCE_COMMIT_INVALID")
    if value["case_scope"] != "P3_CELL_CALIBRATION_REFERENCE":
        fail("CASE_SCOPE_INVALID")
    if value["frequency_status"] != "PLANNING_INPUT_NOT_P2_AUTHORIZED":
        fail("FREQUENCY_STATUS_INVALID")
    raw_frequency = value["frequency_hz"]
    if (
        not isinstance(raw_frequency, str)
        or len(raw_frequency) > 64
        or not DECIMAL_RE.fullmatch(raw_frequency)
    ):
        fail("FREQUENCY_DECIMAL_STRING_INVALID")
    try:
        frequency = Decimal(raw_frequency)
    except InvalidOperation as exc:
        raise PlanError("FREQUENCY_DECIMAL_STRING_INVALID") from exc
    if not frequency.is_finite() or frequency <= 0 or not -3 <= frequency.adjusted() <= 6:
        fail("FREQUENCY_RANGE_INVALID")
    if value["steps_per_cycle"] != [100, 200, 400] or any(
        isinstance(item, bool) for item in value["steps_per_cycle"]
    ):
        fail("STEPS_PER_CYCLE_MISMATCH")
    ramp = require_int(value["ramp_cycles"], 2, 5, "RAMP_CYCLES_INVALID")
    monitored = require_int(
        value["monitored_cycles"], 10, 20, "MONITORED_CYCLES_INVALID"
    )
    if value["sample_every_steps"] != 1 or isinstance(
        value["sample_every_steps"], bool
    ):
        fail("SAMPLE_EVERY_STEPS_INVALID")
    if value["p2_displacement_authorized"] is not False:
        fail("P2_AUTHORIZATION_MUST_BE_FALSE")
    if value["solver_authorized"] is not False:
        fail("SOLVER_AUTHORIZATION_MUST_BE_FALSE")
    if value["formal_gate_effect"] != "NONE":
        fail("FORMAL_GATE_EFFECT_MUST_BE_NONE")
    return frequency, ramp, monitored


def fixed(value: Decimal) -> str:
    rendered = format(value, "f")
    if "." in rendered:
        rendered = rendered.rstrip("0").rstrip(".")
    return rendered or "0"


def build_result(
    value: dict[str, Any], digest: str, frequency: Decimal, ramp: int, monitored: int
) -> dict[str, Any]:
    with localcontext() as context:
        context.prec = 60
        period = Decimal(1) / frequency
        total_cycles = ramp + monitored
        plans = []
        for steps in (100, 200, 400):
            delta_t = period / Decimal(steps)
            previous_index = total_cycles - 2
            final_index = total_cycles - 1
            plans.append(
                {
                    "steps_per_cycle": steps,
                    "period_s": fixed(period),
                    "delta_t_s": fixed(delta_t),
                    "sample_every_steps": 1,
                    "scheduled_step_samples_per_cycle": steps,
                    "endpoint_row_count_asserted": False,
                    "ramp_cycles": ramp,
                    "ramp_end_s": fixed(period * ramp),
                    "monitored_cycles": monitored,
                    "monitor_start_s": fixed(period * ramp),
                    "monitor_end_s": fixed(period * total_cycles),
                    "total_cycles": total_cycles,
                    "total_steps": total_cycles * steps,
                    "adjacent_comparison_windows": [
                        {
                            "cycle_index": previous_index,
                            "start_s": fixed(period * previous_index),
                            "end_s": fixed(period * (previous_index + 1)),
                        },
                        {
                            "cycle_index": final_index,
                            "start_s": fixed(period * final_index),
                            "end_s": fixed(period * (final_index + 1)),
                        },
                    ],
                }
            )
    return {
        "status": "P3_TIMESTEP_MATRIX_PLANNED_NOT_AUTHORIZED",
        "schema_version": SCHEMA,
        "source_commit": value["source_commit"],
        "contract_sha256": digest,
        "frequency_hz": fixed(frequency),
        "frequency_status": value["frequency_status"],
        "decimal_context_precision_digits": 60,
        "decimal_values_are_planning_approximations": True,
        "plans": plans,
        "control_dict_written": False,
        "case_written": False,
        "p2_frequency_verified": False,
        "p2_displacement_verified": False,
        "cfl_verified": False,
        "dynamic_mesh_verified": False,
        "periodic_stability_verified": False,
        "time_step_independence_verified": False,
        "solver_verified": False,
        "solver_authorized": False,
        "formal_gate_effect": "NONE",
    }


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("contract", type=Path)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = parse_args(sys.argv[1:] if argv is None else argv)
        value, digest = load_contract(args.contract)
        frequency, ramp, monitored = validate(value)
        print(
            json.dumps(
                build_result(value, digest, frequency, ramp, monitored),
                ensure_ascii=True,
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    except PlanError as exc:
        print(f"REJECTED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

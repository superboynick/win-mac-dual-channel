#!/usr/bin/env python3
"""Bounded offline conservation checks for OpenFOAM-derived time series.

The input CSV uses explicit engineering sign conventions:

* ``mass_in_kg_s`` is positive into the modeled domain.
* ``mass_out_kg_s`` is positive out of the modeled domain.
* ``domain_mass_rate_kg_s`` is positive for accumulation in the domain.
* optional total-energy columns use the analogous input/output/accumulation
  signs. The input/output totals must already include every applicable
  advective enthalpy, kinetic, pressure-work, conductive, source, and work term.

The pointwise residual is therefore ``input - output - accumulation``.  This
tool evaluates the final two cycles using fixed planning-manual thresholds.  It
uses a shared-boundary convention: cycle N phase 1 and cycle N+1 phase 0 must
have the same timestamp, while time is strictly increasing within each cycle.
This prevents separated windows from masquerading as adjacent cycles.  It
does not run OpenFOAM, verify data provenance, authorize a solver, or advance a
formal AirJet Gate.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import stat
import sys
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path
from typing import Sequence


MAX_FILE_BYTES = 8 * 1024 * 1024
MAX_ROWS = 50_000
MAX_FIELD_CHARS = 256
MAX_DECIMAL_ADJUSTED_EXPONENT = 100
MASS_BALANCE_LIMIT_PERCENT = Decimal("0.5")
ADJACENT_CYCLE_LIMIT_PERCENT = Decimal("1")
ENERGY_BALANCE_LIMIT_PERCENT = Decimal("1")

EXIT_ACCEPTED = 0
EXIT_INVALID_INPUT = 2
EXIT_NUMERIC_REJECTED = 3

BASE_HEADERS = (
    "time_s",
    "cycle_index",
    "cycle_phase",
    "mass_in_kg_s",
    "mass_out_kg_s",
    "domain_mass_rate_kg_s",
    "chamber_pressure_pa",
    "jet_velocity_m_s",
)
ENERGY_HEADERS = (
    "total_energy_in_w",
    "total_energy_out_w",
    "domain_total_energy_rate_w",
    "energy_flux_contract",
)
ENERGY_FLUX_CONTRACT = "TOTAL_ENERGY_ALL_BOUNDARY_AND_SOURCE_TERMS_V1"


class InputError(Exception):
    """Stable, redacted input rejection."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class StableBytes:
    data: bytes
    size_bytes: int
    sha256: str
    basename: str


@dataclass(frozen=True)
class Sample:
    time_s: Decimal
    cycle_index: int
    cycle_phase: Decimal
    mass_in_kg_s: Decimal
    mass_out_kg_s: Decimal
    domain_mass_rate_kg_s: Decimal
    chamber_pressure_pa: Decimal
    jet_velocity_m_s: Decimal
    total_energy_in_w: Decimal | None = None
    total_energy_out_w: Decimal | None = None
    domain_total_energy_rate_w: Decimal | None = None


def _is_reparse_point(file_stat: os.stat_result) -> bool:
    attributes = getattr(file_stat, "st_file_attributes", 0)
    reparse_attribute = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return bool(attributes & reparse_attribute)


def _identity(file_stat: os.stat_result) -> tuple[int, int, int, int]:
    return (
        int(file_stat.st_dev),
        int(file_stat.st_ino),
        int(file_stat.st_size),
        int(file_stat.st_mtime_ns),
    )


def _safe_basename(path: Path) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]", "_", path.name)
    return (cleaned or "input.csv")[:128]


def read_stable_bytes(path: Path) -> StableBytes:
    """Read a regular non-reparse file through one bounded open handle."""

    try:
        before = os.lstat(path)
    except OSError as exc:
        raise InputError("INPUT_OPEN_FAILED") from exc
    if stat.S_ISLNK(before.st_mode) or _is_reparse_point(before):
        raise InputError("INPUT_REPARSE_OR_SYMLINK_REJECTED")
    if not stat.S_ISREG(before.st_mode):
        raise InputError("INPUT_NOT_REGULAR_FILE")
    if before.st_size > MAX_FILE_BYTES:
        raise InputError("INPUT_FILE_TOO_LARGE")

    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise InputError("INPUT_OPEN_FAILED") from exc

    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode):
            raise InputError("OPENED_INPUT_NOT_REGULAR_FILE")
        if _identity(before) != _identity(opened):
            raise InputError("INPUT_IDENTITY_CHANGED_BEFORE_READ")

        chunks: list[bytes] = []
        total = 0
        digest = hashlib.sha256()
        while True:
            chunk = os.read(descriptor, min(1024 * 1024, MAX_FILE_BYTES + 1 - total))
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_FILE_BYTES:
                raise InputError("INPUT_FILE_TOO_LARGE")
            chunks.append(chunk)
            digest.update(chunk)

        after_handle = os.fstat(descriptor)
        try:
            after_path = os.lstat(path)
        except OSError as exc:
            raise InputError("INPUT_PATH_DISAPPEARED") from exc
        if stat.S_ISLNK(after_path.st_mode) or _is_reparse_point(after_path):
            raise InputError("INPUT_REPARSE_OR_SYMLINK_REJECTED")
        if _identity(opened) != _identity(after_handle):
            raise InputError("INPUT_CHANGED_DURING_READ")
        if _identity(opened) != _identity(after_path):
            raise InputError("INPUT_PATH_IDENTITY_CHANGED")
    finally:
        os.close(descriptor)

    return StableBytes(
        data=b"".join(chunks),
        size_bytes=total,
        sha256=digest.hexdigest(),
        basename=_safe_basename(path),
    )


def _parse_decimal(token: str, field: str, row_number: int) -> Decimal:
    if token == "" or token != token.strip():
        raise InputError(f"INVALID_{field.upper()}_ROW_{row_number}")
    try:
        value = Decimal(token)
    except InvalidOperation as exc:
        raise InputError(f"INVALID_{field.upper()}_ROW_{row_number}") from exc
    if not value.is_finite():
        raise InputError(f"NONFINITE_{field.upper()}_ROW_{row_number}")
    if (
        value != 0
        and abs(value.adjusted()) > MAX_DECIMAL_ADJUSTED_EXPONENT
    ):
        raise InputError(f"MAGNITUDE_{field.upper()}_ROW_{row_number}")
    return value


def _parse_cycle_index(token: str, row_number: int) -> int:
    if not re.fullmatch(r"0|[1-9][0-9]{0,8}", token):
        raise InputError(f"INVALID_CYCLE_INDEX_ROW_{row_number}")
    return int(token)


def parse_csv(stable: StableBytes, require_energy: bool = False) -> tuple[list[Sample], bool]:
    try:
        text = stable.data.decode("utf-8-sig", errors="strict")
    except UnicodeDecodeError as exc:
        raise InputError("INPUT_NOT_UTF8") from exc
    if "\x00" in text:
        raise InputError("INPUT_CONTAINS_NUL")

    previous_field_limit = csv.field_size_limit()
    csv.field_size_limit(MAX_FIELD_CHARS)
    try:
        reader = csv.reader(io.StringIO(text, newline=""), strict=True)
        try:
            header = next(reader)
        except StopIteration as exc:
            raise InputError("CSV_EMPTY") from exc
        except csv.Error as exc:
            raise InputError("CSV_HEADER_PARSE_FAILED") from exc

        if len(header) != len(set(header)):
            raise InputError("CSV_DUPLICATE_HEADER")
        if tuple(header) == BASE_HEADERS:
            energy_present = False
        elif tuple(header) == BASE_HEADERS + ENERGY_HEADERS:
            energy_present = True
        else:
            raise InputError("CSV_HEADER_CONTRACT_MISMATCH")
        if require_energy and not energy_present:
            raise InputError("ENERGY_COLUMNS_REQUIRED")

        samples: list[Sample] = []
        previous_time: Decimal | None = None
        previous_cycle: int | None = None
        previous_phase: Decimal | None = None
        previous_sample: Sample | None = None
        for row_number, row in enumerate(reader, start=2):
            if row_number - 1 > MAX_ROWS:
                raise InputError("CSV_ROW_LIMIT_EXCEEDED")
            if len(row) != len(header):
                raise InputError(f"CSV_COLUMN_COUNT_ROW_{row_number}")
            values = dict(zip(header, row))
            time_s = _parse_decimal(values["time_s"], "time_s", row_number)
            if time_s < 0:
                raise InputError(f"NEGATIVE_TIME_ROW_{row_number}")
            cycle_index = _parse_cycle_index(values["cycle_index"], row_number)
            cycle_phase = _parse_decimal(
                values["cycle_phase"], "cycle_phase", row_number
            )
            if cycle_phase < 0 or cycle_phase > 1:
                raise InputError(f"CYCLE_PHASE_OUT_OF_RANGE_ROW_{row_number}")
            if previous_cycle is not None:
                if cycle_index < previous_cycle:
                    raise InputError(f"CYCLE_INDEX_REGRESSION_ROW_{row_number}")
                if cycle_index > previous_cycle + 1:
                    raise InputError(f"CYCLE_INDEX_GAP_ROW_{row_number}")
                if cycle_index == previous_cycle:
                    if previous_time is not None and time_s <= previous_time:
                        raise InputError(
                            f"TIME_NOT_STRICTLY_INCREASING_ROW_{row_number}"
                        )
                else:
                    if previous_phase != 1 or cycle_phase != 0:
                        raise InputError(
                            f"CYCLE_BOUNDARY_PHASE_INVALID_ROW_{row_number}"
                        )
                    if previous_time is None or time_s != previous_time:
                        raise InputError(
                            f"CYCLE_BOUNDARY_TIME_DISCONTINUITY_ROW_{row_number}"
                        )

            sample = Sample(
                time_s=time_s,
                cycle_index=cycle_index,
                cycle_phase=cycle_phase,
                mass_in_kg_s=_parse_decimal(
                    values["mass_in_kg_s"], "mass_in_kg_s", row_number
                ),
                mass_out_kg_s=_parse_decimal(
                    values["mass_out_kg_s"], "mass_out_kg_s", row_number
                ),
                domain_mass_rate_kg_s=_parse_decimal(
                    values["domain_mass_rate_kg_s"],
                    "domain_mass_rate_kg_s",
                    row_number,
                ),
                chamber_pressure_pa=_parse_decimal(
                    values["chamber_pressure_pa"], "chamber_pressure_pa", row_number
                ),
                jet_velocity_m_s=_parse_decimal(
                    values["jet_velocity_m_s"], "jet_velocity_m_s", row_number
                ),
                total_energy_in_w=(
                    _parse_decimal(
                        values["total_energy_in_w"],
                        "total_energy_in_w",
                        row_number,
                    )
                    if energy_present
                    else None
                ),
                total_energy_out_w=(
                    _parse_decimal(
                        values["total_energy_out_w"],
                        "total_energy_out_w",
                        row_number,
                    )
                    if energy_present
                    else None
                ),
                domain_total_energy_rate_w=(
                    _parse_decimal(
                        values["domain_total_energy_rate_w"],
                        "domain_total_energy_rate_w",
                        row_number,
                    )
                    if energy_present
                    else None
                ),
            )
            if (
                energy_present
                and values["energy_flux_contract"] != ENERGY_FLUX_CONTRACT
            ):
                raise InputError(f"ENERGY_FLUX_CONTRACT_ROW_{row_number}")
            if (
                previous_sample is not None
                and previous_cycle is not None
                and cycle_index == previous_cycle + 1
            ):
                boundary_fields = (
                    "mass_in_kg_s",
                    "mass_out_kg_s",
                    "domain_mass_rate_kg_s",
                    "chamber_pressure_pa",
                    "jet_velocity_m_s",
                    "total_energy_in_w",
                    "total_energy_out_w",
                    "domain_total_energy_rate_w",
                )
                for field in boundary_fields:
                    if getattr(previous_sample, field) != getattr(sample, field):
                        raise InputError(
                            "CYCLE_BOUNDARY_VALUE_DISCONTINUITY_"
                            f"{field.upper()}_ROW_{row_number}"
                        )
            samples.append(sample)
            previous_time = time_s
            previous_cycle = cycle_index
            previous_phase = cycle_phase
            previous_sample = sample
    except csv.Error as exc:
        raise InputError("CSV_PARSE_FAILED") from exc
    finally:
        csv.field_size_limit(previous_field_limit)

    if not samples:
        raise InputError("CSV_NO_DATA_ROWS")
    return samples, energy_present


def _trapezoid(times: Sequence[Decimal], values: Sequence[Decimal]) -> Decimal:
    total = Decimal(0)
    for index in range(1, len(times)):
        total += (
            (times[index] - times[index - 1])
            * (values[index] + values[index - 1])
            / Decimal(2)
        )
    return total


def _symmetric_difference_percent(first: Decimal, second: Decimal) -> Decimal:
    denominator = abs(first) + abs(second)
    if denominator == 0:
        return Decimal(0)
    return Decimal(200) * abs(second - first) / denominator


def _decimal_text(value: Decimal | None) -> str | None:
    if value is None:
        return None
    if value == 0:
        return "0"
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def _group_cycles(samples: Sequence[Sample]) -> list[list[Sample]]:
    cycles: list[list[Sample]] = []
    current: list[Sample] = []
    current_index: int | None = None
    for sample in samples:
        if current_index is None or sample.cycle_index == current_index:
            current.append(sample)
            current_index = sample.cycle_index
            continue
        cycles.append(current)
        current = [sample]
        current_index = sample.cycle_index
    cycles.append(current)
    if len(cycles) < 2:
        raise InputError("AT_LEAST_TWO_CYCLES_REQUIRED")
    for cycle in cycles:
        if len(cycle) < 3:
            raise InputError(f"CYCLE_{cycle[0].cycle_index}_HAS_FEWER_THAN_THREE_ROWS")
        if cycle[0].cycle_phase != 0 or cycle[-1].cycle_phase != 1:
            raise InputError(f"CYCLE_{cycle[0].cycle_index}_PHASE_INCOMPLETE")
        for index in range(1, len(cycle)):
            if cycle[index].cycle_phase <= cycle[index - 1].cycle_phase:
                raise InputError(
                    f"CYCLE_{cycle[0].cycle_index}_PHASE_NOT_STRICTLY_INCREASING"
                )
    return cycles


def _cycle_metrics(cycle: Sequence[Sample], energy_present: bool) -> dict[str, object]:
    times = [sample.time_s for sample in cycle]
    duration = times[-1] - times[0]
    if duration <= 0:
        raise InputError(f"CYCLE_{cycle[0].cycle_index}_NONPOSITIVE_DURATION")

    mass_in = [sample.mass_in_kg_s for sample in cycle]
    mass_out = [sample.mass_out_kg_s for sample in cycle]
    mass_rate = [sample.domain_mass_rate_kg_s for sample in cycle]
    mass_residual = [
        incoming - outgoing - accumulation
        for incoming, outgoing, accumulation in zip(mass_in, mass_out, mass_rate)
    ]
    mass_throughput_rate = [
        (abs(incoming) + abs(outgoing) + abs(accumulation)) / Decimal(2)
        for incoming, outgoing, accumulation in zip(mass_in, mass_out, mass_rate)
    ]
    integrated_mass_residual = _trapezoid(times, mass_residual)
    integrated_absolute_mass_residual = _trapezoid(
        times, [abs(value) for value in mass_residual]
    )
    integrated_mass_throughput = _trapezoid(times, mass_throughput_rate)
    mass_error = (
        Decimal(100)
        * integrated_absolute_mass_residual
        / integrated_mass_throughput
        if integrated_mass_throughput > 0
        else None
    )
    net_mass_imbalance = (
        Decimal(100) * abs(integrated_mass_residual) / integrated_mass_throughput
        if integrated_mass_throughput > 0
        else None
    )

    pressure_values = [sample.chamber_pressure_pa for sample in cycle]
    velocity_values = [sample.jet_velocity_m_s for sample in cycle]
    metrics: dict[str, object] = {
        "cycle_index": cycle[0].cycle_index,
        "row_count": len(cycle),
        "start_time_s": _decimal_text(times[0]),
        "end_time_s": _decimal_text(times[-1]),
        "duration_s": duration,
        "integrated_mass_residual_kg": integrated_mass_residual,
        "integrated_absolute_mass_residual_kg": integrated_absolute_mass_residual,
        "integrated_mass_throughput_kg": integrated_mass_throughput,
        "absolute_mass_balance_error_percent": mass_error,
        "net_mass_imbalance_percent": net_mass_imbalance,
        "net_outlet_mass_kg": _trapezoid(times, mass_out),
        "chamber_pressure_peak_to_peak_pa": (
            max(pressure_values) - min(pressure_values)
        ),
        "absolute_jet_velocity_peak_m_s": max(abs(value) for value in velocity_values),
    }

    if energy_present:
        energy_input = [sample.total_energy_in_w for sample in cycle]
        energy_output = [sample.total_energy_out_w for sample in cycle]
        energy_rate = [sample.domain_total_energy_rate_w for sample in cycle]
        if any(value is None for value in energy_input + energy_output + energy_rate):
            raise InputError("ENERGY_COLUMNS_INTERNALLY_INCOMPLETE")
        typed_input = [value for value in energy_input if value is not None]
        typed_output = [value for value in energy_output if value is not None]
        typed_rate = [value for value in energy_rate if value is not None]
        energy_residual = [
            incoming - outgoing - accumulation
            for incoming, outgoing, accumulation in zip(
                typed_input, typed_output, typed_rate
            )
        ]
        energy_throughput_rate = [
            (abs(incoming) + abs(outgoing) + abs(accumulation)) / Decimal(2)
            for incoming, outgoing, accumulation in zip(
                typed_input, typed_output, typed_rate
            )
        ]
        integrated_energy_residual = _trapezoid(times, energy_residual)
        integrated_absolute_energy_residual = _trapezoid(
            times, [abs(value) for value in energy_residual]
        )
        integrated_energy_throughput = _trapezoid(times, energy_throughput_rate)
        energy_error = (
            Decimal(100)
            * integrated_absolute_energy_residual
            / integrated_energy_throughput
            if integrated_energy_throughput > 0
            else None
        )
        net_energy_imbalance = (
            Decimal(100)
            * abs(integrated_energy_residual)
            / integrated_energy_throughput
            if integrated_energy_throughput > 0
            else None
        )
        metrics.update(
            {
                "integrated_total_energy_residual_j": integrated_energy_residual,
                "integrated_absolute_total_energy_residual_j": (
                    integrated_absolute_energy_residual
                ),
                "integrated_total_energy_throughput_j": (
                    integrated_energy_throughput
                ),
                "absolute_total_energy_balance_error_percent": energy_error,
                "net_total_energy_imbalance_percent": net_energy_imbalance,
            }
        )
    return metrics


def _serialize_metrics(metrics: dict[str, object]) -> dict[str, object]:
    return {
        key: _decimal_text(value) if isinstance(value, Decimal) else value
        for key, value in metrics.items()
    }


def analyze_path(path: Path, require_energy: bool = False) -> dict[str, object]:
    stable = read_stable_bytes(path)
    samples, energy_present = parse_csv(stable, require_energy=require_energy)
    cycles = _group_cycles(samples)
    selected = cycles[-2:]

    with localcontext() as context:
        context.prec = 50
        metrics = [_cycle_metrics(cycle, energy_present) for cycle in selected]
        first, second = metrics
        comparisons = {
            "cycle_duration_difference_percent": _symmetric_difference_percent(
                first["duration_s"], second["duration_s"]  # type: ignore[arg-type]
            ),
            "net_outlet_mass_difference_percent": _symmetric_difference_percent(
                first["net_outlet_mass_kg"],  # type: ignore[arg-type]
                second["net_outlet_mass_kg"],  # type: ignore[arg-type]
            ),
            "chamber_pressure_peak_to_peak_difference_percent": (
                _symmetric_difference_percent(
                    first["chamber_pressure_peak_to_peak_pa"],  # type: ignore[arg-type]
                    second["chamber_pressure_peak_to_peak_pa"],  # type: ignore[arg-type]
                )
            ),
            "absolute_jet_velocity_peak_difference_percent": (
                _symmetric_difference_percent(
                    first["absolute_jet_velocity_peak_m_s"],  # type: ignore[arg-type]
                    second["absolute_jet_velocity_peak_m_s"],  # type: ignore[arg-type]
                )
            ),
        }

    findings: list[str] = []
    for cycle_metric in metrics:
        cycle_index = cycle_metric["cycle_index"]
        mass_error = cycle_metric["absolute_mass_balance_error_percent"]
        if mass_error is None:
            findings.append(f"CYCLE_{cycle_index}_ZERO_MASS_THROUGHPUT")
        elif mass_error >= MASS_BALANCE_LIMIT_PERCENT:  # type: ignore[operator]
            findings.append(f"CYCLE_{cycle_index}_MASS_BALANCE_LIMIT_EXCEEDED")
        if cycle_metric["net_outlet_mass_kg"] <= 0:  # type: ignore[operator]
            findings.append(f"CYCLE_{cycle_index}_NONPOSITIVE_NET_OUTLET_MASS")
        if cycle_metric["chamber_pressure_peak_to_peak_pa"] <= 0:  # type: ignore[operator]
            findings.append(f"CYCLE_{cycle_index}_ZERO_CHAMBER_PRESSURE_AMPLITUDE")
        if cycle_metric["absolute_jet_velocity_peak_m_s"] <= 0:  # type: ignore[operator]
            findings.append(f"CYCLE_{cycle_index}_ZERO_JET_VELOCITY_PEAK")
        if energy_present:
            energy_error = cycle_metric[
                "absolute_total_energy_balance_error_percent"
            ]
            if energy_error is None:
                findings.append(f"CYCLE_{cycle_index}_ZERO_ENERGY_THROUGHPUT")
            elif energy_error >= ENERGY_BALANCE_LIMIT_PERCENT:  # type: ignore[operator]
                findings.append(f"CYCLE_{cycle_index}_ENERGY_BALANCE_LIMIT_EXCEEDED")

    comparison_names = {
        "cycle_duration_difference_percent": "CYCLE_DURATION_STABILITY_LIMIT_EXCEEDED",
        "net_outlet_mass_difference_percent": "NET_OUTLET_MASS_STABILITY_LIMIT_EXCEEDED",
        "chamber_pressure_peak_to_peak_difference_percent": (
            "CHAMBER_PRESSURE_STABILITY_LIMIT_EXCEEDED"
        ),
        "absolute_jet_velocity_peak_difference_percent": (
            "JET_VELOCITY_STABILITY_LIMIT_EXCEEDED"
        ),
    }
    for metric_name, finding in comparison_names.items():
        if comparisons[metric_name] >= ADJACENT_CYCLE_LIMIT_PERCENT:
            findings.append(finding)

    numeric_pass = not findings
    return {
        "schema_version": 1,
        "analysis_kind": "OFFLINE_CONSERVATION_AND_ADJACENT_CYCLE_CONTRACT",
        "input_limits": {
            "max_file_bytes": MAX_FILE_BYTES,
            "max_rows": MAX_ROWS,
            "max_field_characters": MAX_FIELD_CHARS,
            "max_absolute_decimal_adjusted_exponent": (
                MAX_DECIMAL_ADJUSTED_EXPONENT
            ),
        },
        "source": {
            "basename": stable.basename,
            "size_bytes": stable.size_bytes,
            "sha256": stable.sha256,
            "row_count": len(samples),
            "cycle_count": len(cycles),
            "energy_columns_present": energy_present,
            "data_origin_verified": False,
        },
        "sign_convention": {
            "mass_residual": "mass_in_kg_s - mass_out_kg_s - domain_mass_rate_kg_s",
            "energy_residual": (
                "total_energy_in_w - total_energy_out_w - "
                "domain_total_energy_rate_w"
                if energy_present
                else "NOT_ANALYZED"
            ),
            "energy_flux_contract": (
                ENERGY_FLUX_CONTRACT if energy_present else "NOT_ANALYZED"
            ),
        },
        "normalization": {
            "acceptance_error": (
                "integral(abs(residual),dt) / "
                "integral(0.5*(abs(input)+abs(output)+abs(accumulation)),dt)"
            ),
            "net_imbalance_diagnostic": (
                "abs(integral(residual,dt)) / "
                "integral(0.5*(abs(input)+abs(output)+abs(accumulation)),dt)"
            ),
        },
        "thresholds_percent": {
            "mass_balance_strictly_less_than": _decimal_text(
                MASS_BALANCE_LIMIT_PERCENT
            ),
            "adjacent_cycle_metrics_strictly_less_than": _decimal_text(
                ADJACENT_CYCLE_LIMIT_PERCENT
            ),
            "energy_balance_strictly_less_than": (
                _decimal_text(ENERGY_BALANCE_LIMIT_PERCENT)
                if energy_present
                else None
            ),
        },
        "selected_cycle_indices": [cycle[0].cycle_index for cycle in selected],
        "cycle_metrics": [_serialize_metrics(metric) for metric in metrics],
        "adjacent_cycle_comparisons_percent": _serialize_metrics(comparisons),
        "findings": findings,
        "truth": {
            "input_valid": True,
            "complete_cycle_phase_contract_verified": True,
            "temporal_cycle_adjacency_verified": True,
            "numeric_contract_result": "PASS" if numeric_pass else "REJECT",
            "time_step_independence_verified": False,
            "mesh_independence_verified": False,
            "boundary_semantics_verified": False,
            "openfoam_solver_run_verified": False,
            "airjet_solver_authorized": False,
            "stage_gate_advanced": False,
            "formal_gate_effect": "NONE",
            "zero_flow_can_pass": False,
        },
    }


def _invalid_result(code: str) -> dict[str, object]:
    return {
        "schema_version": 1,
        "error_code": code,
        "truth": {
            "input_valid": False,
            "complete_cycle_phase_contract_verified": False,
            "temporal_cycle_adjacency_verified": False,
            "numeric_contract_result": "REJECT",
            "time_step_independence_verified": False,
            "mesh_independence_verified": False,
            "boundary_semantics_verified": False,
            "openfoam_solver_run_verified": False,
            "airjet_solver_authorized": False,
            "stage_gate_advanced": False,
            "formal_gate_effect": "NONE",
            "zero_flow_can_pass": False,
        },
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Analyze a bounded OpenFOAM-derived conservation CSV offline."
    )
    parser.add_argument("csv_path", type=Path)
    parser.add_argument(
        "--require-energy",
        action="store_true",
        help="reject input unless the complete optional energy column set is present",
    )
    parser.add_argument("--pretty", action="store_true")
    arguments = parser.parse_args(argv)

    try:
        result = analyze_path(arguments.csv_path, require_energy=arguments.require_energy)
    except InputError as exc:
        print(
            json.dumps(
                _invalid_result(exc.code),
                ensure_ascii=True,
                sort_keys=True,
                indent=2 if arguments.pretty else None,
            ),
            file=sys.stderr,
        )
        return EXIT_INVALID_INPUT
    except (OSError, ValueError, ArithmeticError, csv.Error, MemoryError):
        print(
            json.dumps(
                _invalid_result("UNEXPECTED_BOUNDED_ANALYSIS_FAILURE"),
                ensure_ascii=True,
                sort_keys=True,
                indent=2 if arguments.pretty else None,
            ),
            file=sys.stderr,
        )
        return EXIT_INVALID_INPUT

    print(
        json.dumps(
            result,
            ensure_ascii=True,
            sort_keys=True,
            indent=2 if arguments.pretty else None,
        )
    )
    return (
        EXIT_ACCEPTED
        if result["truth"]["numeric_contract_result"] == "PASS"  # type: ignore[index]
        else EXIT_NUMERIC_REJECTED
    )


if __name__ == "__main__":
    raise SystemExit(main())

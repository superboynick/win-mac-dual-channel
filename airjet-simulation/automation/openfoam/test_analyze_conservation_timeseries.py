#!/usr/bin/env python3
"""Contract tests for the offline OpenFOAM conservation analyzer."""

from __future__ import annotations

import csv
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "analyze_conservation_timeseries.py"
SPEC = importlib.util.spec_from_file_location("conservation", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def base_rows(
    *,
    mass_in_cycle_0: str = "1",
    mass_out_cycle_0: str = "1",
    mass_in_cycle_1: str = "1",
    mass_out_cycle_1: str = "1",
    zero_flow: bool = False,
    energy: bool = False,
    energy_input: str = "5.25",
    energy_output: str = "5.25",
) -> list[list[str]]:
    rows: list[list[str]] = []
    pressure = ("0", "1", "0", "-1", "0")
    velocity = ("0", "2", "0", "-2", "0")
    for cycle in (0, 1):
        incoming = mass_in_cycle_0 if cycle == 0 else mass_in_cycle_1
        outgoing = mass_out_cycle_0 if cycle == 0 else mass_out_cycle_1
        if zero_flow:
            incoming = "0"
            outgoing = "0"
        for offset, phase in enumerate(("0", "0.25", "0.5", "0.75", "1")):
            time_value = str(cycle + float(phase))
            row = [
                time_value,
                str(cycle),
                phase,
                incoming,
                outgoing,
                "0",
                pressure[offset],
                velocity[offset],
            ]
            if energy:
                row.extend(
                    (
                        energy_input,
                        energy_output,
                        "0",
                        MODULE.ENERGY_FLUX_CONTRACT,
                    )
                )
            rows.append(row)
    return rows


class ConservationAnalyzerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_csv(
        self,
        name: str,
        rows: list[list[str]],
        *,
        header: tuple[str, ...] = MODULE.BASE_HEADERS,
    ) -> Path:
        path = self.root / name
        with path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream, lineterminator="\n")
            writer.writerow(header)
            writer.writerows(rows)
        return path

    def assert_rejected(self, path: Path, expected_code: str) -> None:
        with self.assertRaises(MODULE.InputError) as captured:
            MODULE.analyze_path(path)
        self.assertEqual(captured.exception.code, expected_code)

    def test_balanced_two_cycle_mass_contract_passes(self) -> None:
        path = self.write_csv("balanced.csv", base_rows())
        result = MODULE.analyze_path(path)
        self.assertEqual(result["truth"]["numeric_contract_result"], "PASS")
        self.assertFalse(result["truth"]["openfoam_solver_run_verified"])
        self.assertFalse(result["truth"]["airjet_solver_authorized"])
        self.assertFalse(result["truth"]["stage_gate_advanced"])
        self.assertFalse(result["truth"]["time_step_independence_verified"])
        self.assertFalse(result["truth"]["mesh_independence_verified"])
        self.assertFalse(result["truth"]["boundary_semantics_verified"])
        self.assertEqual(result["truth"]["formal_gate_effect"], "NONE")
        self.assertEqual(result["findings"], [])
        self.assertEqual(result["selected_cycle_indices"], [0, 1])

    def test_small_mass_error_below_strict_limit_passes(self) -> None:
        path = self.write_csv(
            "small-error.csv",
            base_rows(mass_out_cycle_0="0.999", mass_out_cycle_1="0.999"),
        )
        result = MODULE.analyze_path(path)
        self.assertEqual(result["truth"]["numeric_contract_result"], "PASS")

    def test_mass_error_at_or_above_limit_rejects(self) -> None:
        path = self.write_csv(
            "mass-fail.csv",
            base_rows(mass_out_cycle_0="0.98", mass_out_cycle_1="0.98"),
        )
        result = MODULE.analyze_path(path)
        self.assertEqual(result["truth"]["numeric_contract_result"], "REJECT")
        self.assertIn("CYCLE_0_MASS_BALANCE_LIMIT_EXCEEDED", result["findings"])
        self.assertIn("CYCLE_1_MASS_BALANCE_LIMIT_EXCEEDED", result["findings"])

    def test_alternating_residuals_cannot_cancel_to_pass(self) -> None:
        rows = base_rows()
        for cycle_start in (0, 5):
            for offset, incoming in enumerate(("3", "-1", "3", "-1", "3")):
                rows[cycle_start + offset][3] = incoming
                rows[cycle_start + offset][4] = "1"
        path = self.write_csv("alternating-residual.csv", rows)
        result = MODULE.analyze_path(path)
        first = result["cycle_metrics"][0]
        self.assertEqual(first["integrated_mass_residual_kg"], "0")
        self.assertEqual(first["net_mass_imbalance_percent"], "0")
        self.assertNotEqual(first["absolute_mass_balance_error_percent"], "0")
        self.assertIn("CYCLE_0_MASS_BALANCE_LIMIT_EXCEEDED", result["findings"])
        self.assertEqual(result["truth"]["numeric_contract_result"], "REJECT")

        energy_rows = base_rows(energy=True)
        for cycle_start in (0, 5):
            for offset, incoming in enumerate(
                ("7.25", "3.25", "7.25", "3.25", "7.25")
            ):
                energy_rows[cycle_start + offset][8] = incoming
                energy_rows[cycle_start + offset][9] = "5.25"
        energy_path = self.write_csv(
            "alternating-energy-residual.csv",
            energy_rows,
            header=MODULE.BASE_HEADERS + MODULE.ENERGY_HEADERS,
        )
        energy_result = MODULE.analyze_path(energy_path, require_energy=True)
        first_energy = energy_result["cycle_metrics"][0]
        self.assertEqual(first_energy["integrated_total_energy_residual_j"], "0")
        self.assertEqual(first_energy["net_total_energy_imbalance_percent"], "0")
        self.assertNotEqual(
            first_energy["absolute_total_energy_balance_error_percent"], "0"
        )
        self.assertIn(
            "CYCLE_0_ENERGY_BALANCE_LIMIT_EXCEEDED", energy_result["findings"]
        )

    def test_exact_mass_threshold_and_over_limit_stability_reject(self) -> None:
        mass_path = self.write_csv(
            "mass-exact-limit.csv",
            base_rows(
                mass_in_cycle_0="1.0025",
                mass_out_cycle_0="0.9975",
                mass_in_cycle_1="1.0025",
                mass_out_cycle_1="0.9975",
            ),
        )
        mass_result = MODULE.analyze_path(mass_path)
        self.assertEqual(
            mass_result["cycle_metrics"][0][
                "absolute_mass_balance_error_percent"
            ],
            "0.5",
        )
        self.assertIn(
            "CYCLE_0_MASS_BALANCE_LIMIT_EXCEEDED", mass_result["findings"]
        )

        stability_rows = base_rows()
        for row in stability_rows[6:]:
            row[3] = "0.98"
            row[4] = "0.98"
        stability_path = self.write_csv(
            "stability-over-limit.csv", stability_rows
        )
        stability_result = MODULE.analyze_path(stability_path)
        self.assertGreater(
            float(
                stability_result["adjacent_cycle_comparisons_percent"][
                    "net_outlet_mass_difference_percent"
                ]
            ),
            1,
        )
        self.assertIn(
            "NET_OUTLET_MASS_STABILITY_LIMIT_EXCEEDED",
            stability_result["findings"],
        )

    def test_adjacent_cycle_flow_change_rejects_stability(self) -> None:
        rows = base_rows()
        for row in rows[6:]:
            row[3] = "1.2"
            row[4] = "1.2"
        path = self.write_csv("periodic-fail.csv", rows)
        result = MODULE.analyze_path(path)
        self.assertEqual(result["truth"]["numeric_contract_result"], "REJECT")
        self.assertIn(
            "NET_OUTLET_MASS_STABILITY_LIMIT_EXCEEDED", result["findings"]
        )
        self.assertNotIn(
            "CYCLE_1_MASS_BALANCE_LIMIT_EXCEEDED", result["findings"]
        )

    def test_zero_flow_cannot_pass(self) -> None:
        path = self.write_csv("zero.csv", base_rows(zero_flow=True))
        result = MODULE.analyze_path(path)
        self.assertEqual(result["truth"]["numeric_contract_result"], "REJECT")
        self.assertFalse(result["truth"]["zero_flow_can_pass"])
        self.assertIn("CYCLE_0_ZERO_MASS_THROUGHPUT", result["findings"])
        self.assertIn("CYCLE_1_ZERO_MASS_THROUGHPUT", result["findings"])

    def test_degenerate_or_reverse_signals_cannot_pass(self) -> None:
        degenerate_rows = base_rows()
        for row in degenerate_rows:
            row[6] = "10"
            row[7] = "0"
        degenerate_path = self.write_csv("degenerate.csv", degenerate_rows)
        degenerate_result = MODULE.analyze_path(degenerate_path)
        self.assertIn(
            "CYCLE_0_ZERO_CHAMBER_PRESSURE_AMPLITUDE",
            degenerate_result["findings"],
        )
        self.assertIn(
            "CYCLE_1_ZERO_JET_VELOCITY_PEAK", degenerate_result["findings"]
        )

        reverse_path = self.write_csv(
            "reverse.csv",
            base_rows(
                mass_in_cycle_0="-1",
                mass_out_cycle_0="-1",
                mass_in_cycle_1="-1",
                mass_out_cycle_1="-1",
            ),
        )
        reverse_result = MODULE.analyze_path(reverse_path)
        self.assertIn(
            "CYCLE_0_NONPOSITIVE_NET_OUTLET_MASS", reverse_result["findings"]
        )

    def test_complete_energy_contract_passes_when_required(self) -> None:
        path = self.write_csv(
            "energy.csv",
            base_rows(energy=True),
            header=MODULE.BASE_HEADERS + MODULE.ENERGY_HEADERS,
        )
        result = MODULE.analyze_path(path, require_energy=True)
        self.assertEqual(result["truth"]["numeric_contract_result"], "PASS")
        self.assertTrue(result["source"]["energy_columns_present"])
        self.assertEqual(
            result["cycle_metrics"][0][
                "absolute_total_energy_balance_error_percent"
            ],
            "0",
        )

    def test_energy_imbalance_rejects(self) -> None:
        path = self.write_csv(
            "energy-fail.csv",
            base_rows(energy=True, energy_output="5"),
            header=MODULE.BASE_HEADERS + MODULE.ENERGY_HEADERS,
        )
        result = MODULE.analyze_path(path, require_energy=True)
        self.assertEqual(result["truth"]["numeric_contract_result"], "REJECT")
        self.assertIn("CYCLE_0_ENERGY_BALANCE_LIMIT_EXCEEDED", result["findings"])

    def test_exact_energy_threshold_rejects(self) -> None:
        path = self.write_csv(
            "energy-exact-limit.csv",
            base_rows(
                energy=True,
                energy_input="5.025",
                energy_output="4.975",
            ),
            header=MODULE.BASE_HEADERS + MODULE.ENERGY_HEADERS,
        )
        result = MODULE.analyze_path(path, require_energy=True)
        self.assertEqual(
            result["cycle_metrics"][0][
                "absolute_total_energy_balance_error_percent"
            ],
            "1",
        )
        self.assertIn(
            "CYCLE_0_ENERGY_BALANCE_LIMIT_EXCEEDED", result["findings"]
        )

    def test_missing_required_energy_columns_rejects(self) -> None:
        path = self.write_csv("no-energy.csv", base_rows())
        stable = MODULE.read_stable_bytes(path)
        with self.assertRaises(MODULE.InputError) as captured:
            MODULE.parse_csv(stable, require_energy=True)
        self.assertEqual(captured.exception.code, "ENERGY_COLUMNS_REQUIRED")

    def test_energy_flux_contract_must_be_exact(self) -> None:
        rows = base_rows(energy=True)
        rows[0][-1] = "HEAT_ONLY"
        path = self.write_csv(
            "wrong-energy-contract.csv",
            rows,
            header=MODULE.BASE_HEADERS + MODULE.ENERGY_HEADERS,
        )
        self.assert_rejected(path, "ENERGY_FLUX_CONTRACT_ROW_2")

    def test_partial_energy_header_rejects(self) -> None:
        partial = MODULE.BASE_HEADERS + ("total_energy_in_w",)
        rows = [row + ["5.25"] for row in base_rows()]
        path = self.write_csv("partial-energy.csv", rows, header=partial)
        self.assert_rejected(path, "CSV_HEADER_CONTRACT_MISMATCH")

    def test_duplicate_and_extra_headers_reject(self) -> None:
        duplicate = list(MODULE.BASE_HEADERS)
        duplicate[-1] = duplicate[-2]
        duplicate_path = self.write_csv(
            "duplicate.csv", base_rows(), header=tuple(duplicate)
        )
        self.assert_rejected(duplicate_path, "CSV_DUPLICATE_HEADER")

        extra_path = self.write_csv(
            "extra.csv",
            [row + ["x"] for row in base_rows()],
            header=MODULE.BASE_HEADERS + ("unexpected",),
        )
        self.assert_rejected(extra_path, "CSV_HEADER_CONTRACT_MISMATCH")

    def test_nonfinite_and_oversized_magnitude_reject(self) -> None:
        nonfinite_rows = base_rows()
        nonfinite_rows[0][3] = "NaN"
        nonfinite_path = self.write_csv("nan.csv", nonfinite_rows)
        self.assert_rejected(
            nonfinite_path, "NONFINITE_MASS_IN_KG_S_ROW_2"
        )

        huge_rows = base_rows()
        huge_rows[0][3] = "1e101"
        huge_path = self.write_csv("huge-number.csv", huge_rows)
        self.assert_rejected(
            huge_path, "MAGNITUDE_MASS_IN_KG_S_ROW_2"
        )

        tiny_rows = base_rows()
        tiny_rows[0][3] = "1e-101"
        tiny_path = self.write_csv("tiny-number.csv", tiny_rows)
        self.assert_rejected(
            tiny_path, "MAGNITUDE_MASS_IN_KG_S_ROW_2"
        )

    def test_time_and_cycle_sequence_reject(self) -> None:
        time_rows = base_rows()
        time_rows[3][0] = time_rows[2][0]
        time_path = self.write_csv("time.csv", time_rows)
        self.assert_rejected(time_path, "TIME_NOT_STRICTLY_INCREASING_ROW_5")

        cycle_rows = base_rows()
        for row in cycle_rows[5:]:
            row[1] = "2"
        cycle_path = self.write_csv("cycle-gap.csv", cycle_rows)
        self.assert_rejected(cycle_path, "CYCLE_INDEX_GAP_ROW_7")

    def test_incomplete_or_nonmonotonic_cycle_phase_rejects(self) -> None:
        incomplete_rows = base_rows()
        incomplete_rows[4][2] = "0.9"
        incomplete_path = self.write_csv("incomplete-phase.csv", incomplete_rows)
        self.assert_rejected(
            incomplete_path, "CYCLE_BOUNDARY_PHASE_INVALID_ROW_7"
        )

        repeated_rows = base_rows()
        repeated_rows[3][2] = repeated_rows[2][2]
        repeated_path = self.write_csv("repeated-phase.csv", repeated_rows)
        self.assert_rejected(
            repeated_path, "CYCLE_0_PHASE_NOT_STRICTLY_INCREASING"
        )

        range_rows = base_rows()
        range_rows[2][2] = "1.1"
        range_path = self.write_csv("phase-range.csv", range_rows)
        self.assert_rejected(range_path, "CYCLE_PHASE_OUT_OF_RANGE_ROW_4")

    def test_nonadjacent_cycle_windows_reject(self) -> None:
        rows = base_rows()
        for row in rows[5:]:
            row[0] = str(float(row[0]) + 99)
        path = self.write_csv("nonadjacent.csv", rows)
        self.assert_rejected(
            path, "CYCLE_BOUNDARY_TIME_DISCONTINUITY_ROW_7"
        )

    def test_shared_boundary_physical_discontinuity_rejects(self) -> None:
        pressure_rows = base_rows()
        pressure_rows[4][6] = "100"
        pressure_rows[4][7] = "100"
        pressure_rows[5][6] = "-100"
        pressure_rows[5][7] = "-100"
        pressure_path = self.write_csv(
            "boundary-pressure-jump.csv", pressure_rows
        )
        self.assert_rejected(
            pressure_path,
            "CYCLE_BOUNDARY_VALUE_DISCONTINUITY_CHAMBER_PRESSURE_PA_ROW_7",
        )

        mass_rows = base_rows()
        mass_rows[5][3] = "2"
        mass_path = self.write_csv("boundary-mass-jump.csv", mass_rows)
        self.assert_rejected(
            mass_path,
            "CYCLE_BOUNDARY_VALUE_DISCONTINUITY_MASS_IN_KG_S_ROW_7",
        )

    def test_cycle_count_and_minimum_rows_reject(self) -> None:
        one_cycle = base_rows()[:5]
        one_cycle_path = self.write_csv("one-cycle.csv", one_cycle)
        self.assert_rejected(one_cycle_path, "AT_LEAST_TWO_CYCLES_REQUIRED")

        short_cycle = base_rows()
        del short_cycle[1:4]
        short_path = self.write_csv("short-cycle.csv", short_cycle)
        self.assert_rejected(short_path, "CYCLE_0_HAS_FEWER_THAN_THREE_ROWS")

    def test_oversized_file_is_rejected_before_parse(self) -> None:
        path = self.root / "oversized.csv"
        with path.open("wb") as stream:
            stream.seek(MODULE.MAX_FILE_BYTES)
            stream.write(b"x")
        self.assert_rejected(path, "INPUT_FILE_TOO_LARGE")

    def test_row_and_field_limits_reject(self) -> None:
        row_path = self.write_csv("row-limit.csv", base_rows())
        previous_max_rows = MODULE.MAX_ROWS
        MODULE.MAX_ROWS = 5
        try:
            self.assert_rejected(row_path, "CSV_ROW_LIMIT_EXCEEDED")
        finally:
            MODULE.MAX_ROWS = previous_max_rows

        field_rows = base_rows()
        field_rows[0][6] = "1" * (MODULE.MAX_FIELD_CHARS + 1)
        field_path = self.write_csv("field-limit.csv", field_rows)
        self.assert_rejected(field_path, "CSV_PARSE_FAILED")

    @unittest.skipUnless(hasattr(os, "symlink"), "symlink API unavailable")
    def test_symlink_is_rejected_when_platform_allows_creation(self) -> None:
        target = self.write_csv("target.csv", base_rows())
        link = self.root / "link.csv"
        try:
            link.symlink_to(target)
        except OSError:
            self.skipTest("symlink creation not permitted")
        self.assert_rejected(link, "INPUT_REPARSE_OR_SYMLINK_REJECTED")

    def test_cli_exit_codes_json_and_path_redaction(self) -> None:
        accepted = self.write_csv("accepted.csv", base_rows())
        passed = subprocess.run(
            [sys.executable, str(SCRIPT), str(accepted)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(passed.returncode, MODULE.EXIT_ACCEPTED)
        passed_json = json.loads(passed.stdout)
        self.assertEqual(passed_json["truth"]["numeric_contract_result"], "PASS")
        self.assertNotIn(str(self.root), passed.stdout)

        numeric_reject = self.write_csv(
            "numeric-reject.csv",
            base_rows(mass_out_cycle_0="0.9", mass_out_cycle_1="0.9"),
        )
        rejected = subprocess.run(
            [sys.executable, str(SCRIPT), str(numeric_reject)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(rejected.returncode, MODULE.EXIT_NUMERIC_REJECTED)
        rejected_json = json.loads(rejected.stdout)
        self.assertEqual(
            rejected_json["truth"]["numeric_contract_result"], "REJECT"
        )

        invalid = self.root / "missing.csv"
        failed = subprocess.run(
            [sys.executable, str(SCRIPT), str(invalid)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(failed.returncode, MODULE.EXIT_INVALID_INPUT)
        failed_json = json.loads(failed.stderr)
        self.assertFalse(failed_json["truth"]["input_valid"])
        self.assertEqual(failed_json["error_code"], "INPUT_OPEN_FAILED")
        self.assertNotIn(str(self.root), failed.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)

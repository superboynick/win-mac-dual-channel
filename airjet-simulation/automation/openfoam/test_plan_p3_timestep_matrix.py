#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock


HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "plan_p3_timestep_matrix.py"
SPEC = importlib.util.spec_from_file_location("timestep_plan", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def valid() -> dict[str, object]:
    return {
        "schema_version": "AJM_PLAN_B_P3_TIMESTEP_PLAN_V1",
        "source_commit": "1" * 40,
        "case_scope": "P3_CELL_CALIBRATION_REFERENCE",
        "frequency_hz": "20000",
        "frequency_status": "PLANNING_INPUT_NOT_P2_AUTHORIZED",
        "steps_per_cycle": [100, 200, 400],
        "ramp_cycles": 3,
        "monitored_cycles": 10,
        "sample_every_steps": 1,
        "p2_displacement_authorized": False,
        "solver_authorized": False,
        "formal_gate_effect": "NONE",
    }


class TimestepPlanTests(unittest.TestCase):
    def write(self, root: Path, value: object) -> Path:
        path = root / "contract.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def run_cli(self, path: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(path)],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )

    def test_exact_matrix_and_conservative_truth(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = self.write(Path(raw), valid())
            first = self.run_cli(path)
            second = self.run_cli(path)
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(first.stdout, second.stdout)
        result = json.loads(first.stdout)
        self.assertEqual(result["frequency_hz"], "20000")
        self.assertEqual(result["source_commit"], "1" * 40)
        self.assertFalse(result["source_commit_verified"])
        self.assertTrue(result["source_commit_is_caller_supplied_unverified_claim"])
        self.assertEqual(
            [item["delta_t_s"] for item in result["plans"]],
            ["0.0000005", "0.00000025", "0.000000125"],
        )
        self.assertEqual(
            [item["total_steps"] for item in result["plans"]],
            [1300, 2600, 5200],
        )
        self.assertTrue(result["decimal_values_are_planning_approximations"])
        self.assertEqual(result["decimal_context_precision_digits"], 60)
        self.assertFalse(result["plans"][0]["endpoint_row_count_asserted"])
        self.assertEqual(
            result["plans"][0]["adjacent_comparison_windows"],
            [
                {
                    "cycle_index": 11,
                    "start_s": "0.00055",
                    "end_s": "0.0006",
                },
                {
                    "cycle_index": 12,
                    "start_s": "0.0006",
                    "end_s": "0.00065",
                },
            ],
        )
        for key in (
            "control_dict_written",
            "case_written",
            "p2_frequency_verified",
            "p2_displacement_verified",
            "cfl_verified",
            "dynamic_mesh_verified",
            "periodic_stability_verified",
            "time_step_independence_verified",
            "solver_verified",
            "solver_authorized",
        ):
            self.assertFalse(result[key])
        self.assertEqual(result["formal_gate_effect"], "NONE")

    def test_frequency_range_boundaries(self) -> None:
        for frequency in ("0.001", "9999999"):
            with self.subTest(frequency=frequency), tempfile.TemporaryDirectory() as raw:
                value = valid()
                value["frequency_hz"] = frequency
                result = self.run_cli(self.write(Path(raw), value))
            self.assertEqual(result.returncode, 0, result.stderr)
        for frequency in (
            "0",
            "0.0009",
            "9999999.00000000000000000000000000000000000000000000000001",
            "9999999.99999999999999999999999999999999999999999999999999",
            "10000000",
            "-1",
            "NaN",
            "1.0.0",
            20000,
        ):
            with self.subTest(frequency=frequency), tempfile.TemporaryDirectory() as raw:
                value = valid()
                value["frequency_hz"] = frequency
                result = self.run_cli(self.write(Path(raw), value))
            self.assertEqual(result.returncode, 2)
            self.assertIn("FREQUENCY_", result.stderr)

    def test_fixed_matrix_and_cycle_ranges(self) -> None:
        cases = (
            ("steps_per_cycle", [100, 400], "STEPS_PER_CYCLE"),
            ("steps_per_cycle", [100, 200, True], "STEPS_PER_CYCLE"),
            ("ramp_cycles", 1, "RAMP_CYCLES"),
            ("ramp_cycles", True, "RAMP_CYCLES"),
            ("monitored_cycles", 9, "MONITORED_CYCLES"),
            ("sample_every_steps", 2, "SAMPLE_EVERY_STEPS"),
        )
        for key, replacement, code in cases:
            with self.subTest(key=key), tempfile.TemporaryDirectory() as raw:
                value = valid()
                value[key] = replacement
                result = self.run_cli(self.write(Path(raw), value))
            self.assertEqual(result.returncode, 2)
            self.assertIn(code, result.stderr)

    def test_authorization_and_identity_are_fail_closed(self) -> None:
        cases = (
            ("p2_displacement_authorized", True, "P2_AUTHORIZATION"),
            ("solver_authorized", True, "SOLVER_AUTHORIZATION"),
            ("formal_gate_effect", "PASS", "FORMAL_GATE_EFFECT"),
            ("frequency_status", "P2_VERIFIED", "FREQUENCY_STATUS"),
            ("case_scope", "P3_GATE_PASS", "CASE_SCOPE"),
            ("source_commit", "A" * 40, "SOURCE_COMMIT"),
        )
        for key, replacement, code in cases:
            with self.subTest(key=key), tempfile.TemporaryDirectory() as raw:
                value = valid()
                value[key] = replacement
                result = self.run_cli(self.write(Path(raw), value))
            self.assertEqual(result.returncode, 2)
            self.assertIn(code, result.stderr)

    def test_duplicate_extra_deep_float_and_nonfinite_reject(self) -> None:
        cases = (
            ('{"schema_version":"a","schema_version":"b"}', "DUPLICATE_JSON_KEY"),
            (json.dumps({**valid(), "extra": 1}), "CONTRACT_KEYS_MISMATCH"),
            ("[" * 100 + "0" + "]" * 100, "JSON_DEPTH_LIMIT"),
            ('{"value":1.2}', "JSON_NUMBER_MUST_BE_STRING"),
            ('{"value":NaN}', "JSON_NONFINITE"),
        )
        for text, code in cases:
            with self.subTest(code=code), tempfile.TemporaryDirectory() as raw:
                path = Path(raw) / "contract.json"
                path.write_text(text, encoding="utf-8")
                result = self.run_cli(path)
            self.assertEqual(result.returncode, 2)
            self.assertIn(code, result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_missing_nul_bom_invalid_utf8_and_oversize_reject(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            result = self.run_cli(Path(raw) / "missing.json")
        self.assertEqual(result.returncode, 2)
        self.assertNotIn("Traceback", result.stderr)
        for data, code in (
            (b"\x00", "INPUT_NUL"),
            (b"\xef\xbb\xbf{}", "INPUT_UTF8_BOM"),
            (b"\xff", "INPUT_NOT_UTF8"),
            (b"x" * (MODULE.MAX_BYTES + 1), "INPUT_SIZE_LIMIT"),
        ):
            with self.subTest(code=code), tempfile.TemporaryDirectory() as raw:
                path = Path(raw) / "contract.json"
                path.write_bytes(data)
                result = self.run_cli(path)
            self.assertEqual(result.returncode, 2)
            self.assertIn(code, result.stderr)

    @unittest.skipUnless(hasattr(os, "symlink"), "symlink unavailable")
    def test_symlink_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            target = self.write(root, valid())
            link = root / "link.json"
            try:
                link.symlink_to(target)
            except OSError as exc:
                self.skipTest(f"symlink privilege unavailable: {exc}")
            result = self.run_cli(link)
        self.assertEqual(result.returncode, 2)
        self.assertIn("INPUT_LINK_OR_REPARSE_REJECTED", result.stderr)

    def test_handle_and_final_path_drift_reject(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = self.write(Path(raw), valid())
            real_read = os.read

            def short_read(fd: int, count: int) -> bytes:
                return real_read(fd, min(count, 7))

            with mock.patch.object(MODULE.os, "read", side_effect=short_read):
                data, _digest = MODULE.read_stable(path)
            self.assertEqual(json.loads(data), valid())

            real_fstat = os.fstat
            calls = 0

            def drifting(fd: int):
                nonlocal calls
                calls += 1
                result = real_fstat(fd)
                if calls == 2:
                    values = list(result)
                    values[8] = result.st_mtime + 1
                    return os.stat_result(values)
                return result

            with mock.patch.object(MODULE.os, "fstat", side_effect=drifting):
                with self.assertRaisesRegex(
                    MODULE.PlanError, "INPUT_CHANGED_DURING_READ"
                ):
                    MODULE.read_stable(path)

            actual = os.lstat(path)
            swapped_preopen = types.SimpleNamespace(
                st_mode=actual.st_mode,
                st_dev=actual.st_dev,
                st_ino=actual.st_ino + 1,
                st_size=actual.st_size,
                st_mtime_ns=actual.st_mtime_ns,
                st_file_attributes=getattr(actual, "st_file_attributes", 0),
            )
            real_lstat = MODULE.safe_lstat

            def preopen_identity_swap(candidate: Path, phase: str):
                if phase == "PREOPEN":
                    return swapped_preopen
                return real_lstat(candidate, phase)

            with mock.patch.object(
                MODULE, "safe_lstat", side_effect=preopen_identity_swap
            ):
                with self.assertRaisesRegex(
                    MODULE.PlanError, "INPUT_PREOPEN_METADATA_MISMATCH"
                ):
                    MODULE.read_stable(path)

            real_lstat = os.lstat

            def final_metadata_drift(candidate: os.PathLike[str] | str, phase: str):
                result = real_lstat(candidate)
                if phase != "FINAL":
                    return result
                return types.SimpleNamespace(
                    st_mode=result.st_mode,
                    st_dev=result.st_dev,
                    st_ino=result.st_ino,
                    st_size=result.st_size + 1,
                    st_mtime_ns=result.st_mtime_ns + 1,
                    st_file_attributes=getattr(result, "st_file_attributes", 0),
                )

            with mock.patch.object(
                MODULE, "safe_lstat", side_effect=final_metadata_drift
            ):
                with self.assertRaisesRegex(
                    MODULE.PlanError, "INPUT_FINAL_PATH_METADATA_MISMATCH"
                ):
                    MODULE.read_stable(path)

    def test_source_has_no_process_network_or_write_api(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        for token in (
            "import subprocess",
            "from subprocess",
            "import socket",
            "requests",
            "urllib",
            "os.system",
            "Popen(",
            "write_text(",
            "write_bytes(",
        ):
            with self.subTest(token=token):
                self.assertNotIn(token, source)


if __name__ == "__main__":
    unittest.main()

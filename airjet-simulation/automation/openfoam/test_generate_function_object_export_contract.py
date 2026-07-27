#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "generate_function_object_export_contract.py"
SPEC = importlib.util.spec_from_file_location("export_contract", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def valid_descriptor() -> dict[str, object]:
    return {
        "schema_version": "AJM_PLAN_B_OPENFOAM_EXPORT_CONTRACT_V1",
        "openfoam_distribution": "OpenFOAM Foundation",
        "openfoam_major": 14,
        "case_scope": "P3_CELL_CALIBRATION_REFERENCE",
        "source_commit": "1" * 40,
        "geometry_manifest_sha256": "2" * 64,
        "write_control": "writeTime",
        "phi_dimensions": [1, 0, -1, 0, 0, 0, 0],
        "field_names": {
            "density": "rho",
            "flux": "phi",
            "pressure": "p",
            "velocity": "U",
        },
        "chamber_cell_zone": "chamberCells",
        "inlet_patches": ["rearInletB", "rearInletA"],
        "outlet_patches": ["exhaust"],
        "jet_patches": ["jetOrifices"],
    }


class ExportContractTests(unittest.TestCase):
    def write_descriptor(self, directory: Path, value: object) -> Path:
        path = directory / "descriptor.json"
        path.write_text(
            json.dumps(value, ensure_ascii=True, separators=(",", ":")),
            encoding="utf-8",
        )
        return path

    def run_cli(self, path: Path, *extra: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(path), *extra],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )

    def test_valid_descriptor_generates_deterministic_truth_envelope(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = self.write_descriptor(Path(raw), valid_descriptor())
            first = self.run_cli(path)
            second = self.run_cli(path)
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(first.stdout, second.stdout)
        envelope = json.loads(first.stdout)
        self.assertEqual(envelope["formal_gate_effect"], "NONE")
        self.assertFalse(envelope["solver_authorized"])
        self.assertFalse(envelope["runtime_field_dimensions_verified"])
        self.assertFalse(envelope["analyzer_csv_ready"])
        self.assertFalse(envelope["write_schedule_sampling_density_verified"])
        self.assertFalse(envelope["mass_source_sink_terms_included"])
        self.assertEqual(
            envelope["region_scope"],
            "DEFAULT_OBJECT_REGISTRY_SINGLE_FLUID_REGION_ONLY",
        )
        self.assertIn("OUTWARD_POSITIVE", envelope["raw_sign_semantics"])
        self.assertIn("PRESERVE_REVERSE_FLOW", envelope["raw_sign_semantics"])
        self.assertEqual(
            envelope["energy_export"],
            "NOT_IMPLEMENTED_REQUIRES_SOLVER_SPECIFIC_REVIEW",
        )
        snippet = envelope["function_objects"]
        self.assertIn("cellZone        all;", snippet)
        self.assertIn("operation       volIntegrate;", snippet)
        self.assertIn("fields          (rho);", snippet)
        self.assertIn("operation       volAverage;", snippet)
        self.assertIn("fields          (p);", snippet)
        self.assertEqual(snippet.count("operation       orientedSum;"), 2)
        self.assertIn("patches         (rearInletA rearInletB);", snippet)
        self.assertIn("operation       maxMag;", snippet)
        self.assertIn("fields          (U);", snippet)

    def test_foam_output_has_inert_truth_header(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = self.write_descriptor(Path(raw), valid_descriptor())
            result = self.run_cli(path, "--output-format", "foam")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(result.stdout.startswith("// SOURCE_ONLY=true\n"))
        self.assertIn("// SOLVER_AUTHORIZED=false", result.stdout)
        self.assertIn("// FORMAL_GATE_EFFECT=NONE", result.stdout)
        self.assertIn("// RUNTIME_FIELD_DIMENSIONS_VERIFIED=false", result.stdout)
        self.assertIn("// ANALYZER_CSV_READY=false", result.stdout)

    def test_patch_input_order_is_canonicalized(self) -> None:
        left = valid_descriptor()
        right = valid_descriptor()
        right["inlet_patches"] = ["rearInletA", "rearInletB"]
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            left_path = directory / "left.json"
            right_path = directory / "right.json"
            left_path.write_text(json.dumps(left), encoding="utf-8")
            right_path.write_text(json.dumps(right), encoding="utf-8")
            left_result = self.run_cli(left_path)
            right_result = self.run_cli(right_path)
        self.assertEqual(left_result.returncode, 0, left_result.stderr)
        self.assertEqual(right_result.returncode, 0, right_result.stderr)
        self.assertEqual(
            json.loads(left_result.stdout)["contract_sha256"],
            json.loads(right_result.stdout)["contract_sha256"],
        )

    def test_duplicate_json_key_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "duplicate.json"
            path.write_text(
                '{"schema_version":"x","schema_version":"y"}', encoding="utf-8"
            )
            result = self.run_cli(path)
        self.assertEqual(result.returncode, 2)
        self.assertIn("DUPLICATE_JSON_KEY", result.stderr)

    def test_missing_and_extra_keys_rejected(self) -> None:
        for mutate, code in (
            (lambda value: value.pop("jet_patches"), "DESCRIPTOR_MISSING_KEYS"),
            (lambda value: value.update({"unexpected": 1}), "DESCRIPTOR_EXTRA_KEYS"),
        ):
            with self.subTest(code=code), tempfile.TemporaryDirectory() as raw:
                descriptor = valid_descriptor()
                mutate(descriptor)
                result = self.run_cli(self.write_descriptor(Path(raw), descriptor))
            self.assertEqual(result.returncode, 2)
            self.assertIn(code, result.stderr)

    def test_distribution_and_version_are_pinned(self) -> None:
        cases = (
            ("openfoam_distribution", "OpenCFD", "OPENFOAM_DISTRIBUTION_MISMATCH"),
            ("openfoam_major", 13, "OPENFOAM_MAJOR_MISMATCH"),
            ("openfoam_major", True, "OPENFOAM_MAJOR_MISMATCH"),
        )
        for key, replacement, code in cases:
            with self.subTest(key=key, replacement=replacement):
                descriptor = valid_descriptor()
                descriptor[key] = replacement
                with tempfile.TemporaryDirectory() as raw:
                    result = self.run_cli(
                        self.write_descriptor(Path(raw), descriptor)
                    )
                self.assertEqual(result.returncode, 2)
                self.assertIn(code, result.stderr)

    def test_only_reference_scopes_allowed(self) -> None:
        for replacement in ("P3_GATE_PASS", [], None, True):
            with self.subTest(replacement=replacement):
                descriptor = valid_descriptor()
                descriptor["case_scope"] = replacement
                with tempfile.TemporaryDirectory() as raw:
                    result = self.run_cli(
                        self.write_descriptor(Path(raw), descriptor)
                    )
                self.assertEqual(result.returncode, 2)
                self.assertIn("CASE_SCOPE_NOT_ALLOWED", result.stderr)

    def test_field_names_dimensions_and_write_control_are_locked(self) -> None:
        cases = (
            ("write_control", "timeStep", "WRITE_CONTROL_MUST_BE_WRITETIME"),
            (
                "phi_dimensions",
                [0, 3, -1, 0, 0, 0, 0],
                "PHI_DIMENSIONS_MUST_BE_MASS_FLUX",
            ),
            (
                "field_names",
                {
                    "density": "rho",
                    "flux": "rhoPhi",
                    "pressure": "p",
                    "velocity": "U",
                },
                "FIELD_NAMES_MISMATCH",
            ),
        )
        for key, replacement, code in cases:
            with self.subTest(key=key):
                descriptor = valid_descriptor()
                descriptor[key] = replacement
                with tempfile.TemporaryDirectory() as raw:
                    result = self.run_cli(
                        self.write_descriptor(Path(raw), descriptor)
                    )
                self.assertEqual(result.returncode, 2)
                self.assertIn(code, result.stderr)

    def test_openfoam_word_injection_rejected(self) -> None:
        attacks = (
            "rearInlet; system(\"calc\")",
            "../rearInlet",
            "rear-inlet",
            "rear inlet",
            "9rearInlet",
            "a" * 64,
            "inlet\noperation sum",
        )
        for attack in attacks:
            with self.subTest(attack=attack):
                descriptor = valid_descriptor()
                descriptor["inlet_patches"] = [attack]
                with tempfile.TemporaryDirectory() as raw:
                    result = self.run_cli(
                        self.write_descriptor(Path(raw), descriptor)
                    )
                self.assertEqual(result.returncode, 2)
                self.assertIn("INVALID_FOAM_WORD_INLET_PATCHES", result.stderr)

    def test_empty_duplicate_and_excessive_patch_lists_rejected(self) -> None:
        cases = (
            ([], "INLET_PATCHES_COUNT_OUT_OF_RANGE"),
            (["inlet", "inlet"], "INLET_PATCHES_DUPLICATE"),
            (
                [f"inlet{index}" for index in range(33)],
                "INLET_PATCHES_COUNT_OUT_OF_RANGE",
            ),
        )
        for patches, code in cases:
            with self.subTest(code=code):
                descriptor = valid_descriptor()
                descriptor["inlet_patches"] = patches
                with tempfile.TemporaryDirectory() as raw:
                    result = self.run_cli(
                        self.write_descriptor(Path(raw), descriptor)
                    )
                self.assertEqual(result.returncode, 2)
                self.assertIn(code, result.stderr)

    def test_patch_roles_must_be_pairwise_disjoint(self) -> None:
        cases = (
            ("outlet_patches", ["rearInletA"], "PATCH_ROLE_OVERLAP_INLET_OUTLET"),
            ("jet_patches", ["rearInletA"], "PATCH_ROLE_OVERLAP_INLET_JET"),
            ("jet_patches", ["exhaust"], "PATCH_ROLE_OVERLAP_OUTLET_JET"),
        )
        for key, patches, code in cases:
            with self.subTest(key=key):
                descriptor = valid_descriptor()
                descriptor[key] = patches
                with tempfile.TemporaryDirectory() as raw:
                    result = self.run_cli(
                        self.write_descriptor(Path(raw), descriptor)
                    )
                self.assertEqual(result.returncode, 2)
                self.assertIn(code, result.stderr)

    def test_invalid_hashes_rejected(self) -> None:
        cases = (
            ("source_commit", "A" * 40, "SOURCE_COMMIT_INVALID"),
            (
                "geometry_manifest_sha256",
                "2" * 63,
                "GEOMETRY_MANIFEST_SHA256_INVALID",
            ),
        )
        for key, replacement, code in cases:
            with self.subTest(key=key):
                descriptor = valid_descriptor()
                descriptor[key] = replacement
                with tempfile.TemporaryDirectory() as raw:
                    result = self.run_cli(
                        self.write_descriptor(Path(raw), descriptor)
                    )
                self.assertEqual(result.returncode, 2)
                self.assertIn(code, result.stderr)

    def test_nonfinite_nul_bom_and_invalid_utf8_rejected(self) -> None:
        cases = (
            (b'{"x":NaN}', "JSON_NONFINITE_NaN"),
            (b'{"x":"a\\u0000"}\x00', "DESCRIPTOR_NUL_BYTE_REJECTED"),
            (b"\xef\xbb\xbf{}", "DESCRIPTOR_UTF8_BOM_REJECTED"),
            (b"\xff", "DESCRIPTOR_NOT_UTF8"),
        )
        for raw_bytes, code in cases:
            with self.subTest(code=code), tempfile.TemporaryDirectory() as raw:
                path = Path(raw) / "descriptor.json"
                path.write_bytes(raw_bytes)
                result = self.run_cli(path)
            self.assertEqual(result.returncode, 2)
            self.assertIn(code, result.stderr)

    def test_float_and_oversized_integer_tokens_rejected(self) -> None:
        for token, code in (
            ("1.0", "JSON_FLOAT_REJECTED"),
            ("1e2", "JSON_FLOAT_REJECTED"),
            ("9" * 21, "JSON_INTEGER_TOKEN_LIMIT_EXCEEDED"),
        ):
            with self.subTest(token=token), tempfile.TemporaryDirectory() as raw:
                path = Path(raw) / "descriptor.json"
                path.write_text(f'{{"value":{token}}}', encoding="utf-8")
                result = self.run_cli(path)
            self.assertEqual(result.returncode, 2)
            self.assertIn(code, result.stderr)

    def test_missing_descriptor_is_stable_rejection_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            missing = Path(raw) / "missing.json"
            result = self.run_cli(missing)
        self.assertEqual(result.returncode, 2)
        self.assertIn("DESCRIPTOR_PREOPEN_LSTAT_FAILED_FileNotFoundError", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_unlinked_after_open_is_stable_rejection(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = self.write_descriptor(Path(raw), valid_descriptor())
            real_lstat = os.lstat
            calls = 0

            def disappearing_lstat(candidate: os.PathLike[str] | str):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise FileNotFoundError
                return real_lstat(candidate)

            with mock.patch.object(
                MODULE.os, "lstat", side_effect=disappearing_lstat
            ):
                with self.assertRaisesRegex(
                    MODULE.ContractError,
                    "DESCRIPTOR_POSTOPEN_LSTAT_FAILED_FileNotFoundError",
                ):
                    MODULE.read_stable_descriptor(path)

    def test_extreme_raw_nesting_is_rejected_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "nested.json"
            path.write_bytes(b"[" * 100_000 + b"0" + b"]" * 100_000)
            result = self.run_cli(path)
        self.assertEqual(result.returncode, 2)
        self.assertIn("JSON_DEPTH_LIMIT_EXCEEDED", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_hostile_json_keys_never_reach_diagnostics(self) -> None:
        hostile_keys = (
            "line\\nbreak",
            "\\u001b[31mred",
            "nul\\u0000key",
            "surrogate\\ud800key",
        )
        for escaped_key in hostile_keys:
            with self.subTest(escaped_key=escaped_key), tempfile.TemporaryDirectory() as raw:
                path = Path(raw) / "hostile.json"
                path.write_text(
                    f'{{"{escaped_key}":1,"{escaped_key}":2}}',
                    encoding="ascii",
                )
                result = self.run_cli(path)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stderr, "REJECTED: DUPLICATE_JSON_KEY\n")
            self.assertTrue(result.stderr.isascii())

        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "extra.json"
            descriptor = valid_descriptor()
            descriptor["line\n\u001b[31m"] = 1
            path.write_text(json.dumps(descriptor), encoding="utf-8")
            result = self.run_cli(path)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stderr, "REJECTED: DESCRIPTOR_EXTRA_KEYS\n")
        self.assertTrue(result.stderr.isascii())

    def test_size_depth_and_string_limits_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "large.json"
            path.write_bytes(b" " * (MODULE.MAX_DESCRIPTOR_BYTES + 1))
            result = self.run_cli(path)
        self.assertEqual(result.returncode, 2)
        self.assertIn("DESCRIPTOR_SIZE_LIMIT_EXCEEDED", result.stderr)

        nested: object = 0
        for _ in range(MODULE.MAX_JSON_DEPTH + 2):
            nested = [nested]
        with tempfile.TemporaryDirectory() as raw:
            result = self.run_cli(self.write_descriptor(Path(raw), nested))
        self.assertEqual(result.returncode, 2)
        self.assertIn("JSON_DEPTH_LIMIT_EXCEEDED", result.stderr)

        descriptor = valid_descriptor()
        descriptor["case_scope"] = "x" * (MODULE.MAX_STRING_CHARS + 1)
        with tempfile.TemporaryDirectory() as raw:
            result = self.run_cli(self.write_descriptor(Path(raw), descriptor))
        self.assertEqual(result.returncode, 2)
        self.assertIn("JSON_STRING_LIMIT_EXCEEDED", result.stderr)

    def test_empty_and_directory_descriptors_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            empty = directory / "empty.json"
            empty.write_bytes(b"")
            empty_result = self.run_cli(empty)
            directory_result = self.run_cli(directory)
        self.assertEqual(empty_result.returncode, 2)
        self.assertIn("DESCRIPTOR_EMPTY", empty_result.stderr)
        self.assertEqual(directory_result.returncode, 2)
        self.assertTrue(
            "DESCRIPTOR_OPEN_FAILED" in directory_result.stderr
            or "DESCRIPTOR_NOT_REGULAR_FILE" in directory_result.stderr
        )

    @unittest.skipUnless(hasattr(os, "symlink"), "symlink unavailable")
    def test_symlink_descriptor_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            target = self.write_descriptor(directory, valid_descriptor())
            link = directory / "link.json"
            try:
                link.symlink_to(target)
            except OSError as exc:
                self.skipTest(f"symlink privilege unavailable: {exc}")
            result = self.run_cli(link)
        self.assertEqual(result.returncode, 2)
        self.assertIn("DESCRIPTOR_LINK_OR_REPARSE_POINT_REJECTED", result.stderr)

    def test_changed_during_read_is_rejected(self) -> None:
        descriptor = valid_descriptor()
        with tempfile.TemporaryDirectory() as raw:
            path = self.write_descriptor(Path(raw), descriptor)
            real_fstat = os.fstat
            calls = 0

            def drifting_fstat(fd: int):
                nonlocal calls
                calls += 1
                result = real_fstat(fd)
                if calls == 2:
                    values = list(result)
                    values[8] = result.st_mtime + 1
                    return os.stat_result(values)
                return result

            with mock.patch.object(MODULE.os, "fstat", side_effect=drifting_fstat):
                with self.assertRaisesRegex(
                    MODULE.ContractError, "DESCRIPTOR_CHANGED_DURING_READ"
                ):
                    MODULE.read_stable_descriptor(path)

    def test_generator_has_no_process_or_network_api(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        forbidden = (
            "import subprocess",
            "from subprocess",
            "import socket",
            "from socket",
            "urllib",
            "requests",
            "os.system",
            "Popen(",
            "subprocess.",
        )
        for token in forbidden:
            with self.subTest(token=token):
                self.assertNotIn(token, source)


if __name__ == "__main__":
    unittest.main()

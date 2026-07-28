#!/usr/bin/env python3
"""Adversarial tests for the OpenFOAM Foundation v14 motion contract."""

from __future__ import annotations

import contextlib
import copy
import hashlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import generate_openfoam_v14_motion_contract as module  # noqa: E402


def valid_descriptor() -> dict[str, object]:
    return {
        "schema_version": module.SCHEMA_VERSION,
        "openfoam_distribution": "OpenFOAM Foundation",
        "openfoam_major": 14,
        "case_scope": "P3_CELL_CALIBRATION_REFERENCE",
        "source_commit": "1" * 40,
        "geometry_manifest_sha256": "2" * 64,
        "motion_patch": "activeMembrane",
        "motion_field_status": "REAL_P2_SPATIAL_FIELD_NOT_AVAILABLE",
        "point_displacement_file_generation": "REJECT",
        "p2_artifact_authorized": False,
        "p3_case_write_authorized": False,
        "solver_authorized": False,
        "formal_gate_effect": "NONE",
    }


def write_descriptor(directory: Path, value: object) -> tuple[Path, str]:
    path = directory / "motion.json"
    data = json.dumps(value, ensure_ascii=True, separators=(",", ":")).encode("ascii")
    path.write_bytes(data)
    return path, hashlib.sha256(data).hexdigest()


class MotionContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.directory = Path(self.temporary.name)
        self.path, self.pin = write_descriptor(self.directory, valid_descriptor())

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_deterministic_envelope_and_exact_v14_fragments(self) -> None:
        first = module.generate(str(self.path), self.pin)
        second = module.generate(str(self.path), self.pin)
        self.assertEqual(first, second)
        self.assertEqual(
            first["dynamic_mesh_dict_mover_fragment"],
            """mover
{
    type            displacementLaplacian;
    libs            ("libfvMotionSolvers.so");
    diffusivity     inverseDistance 1(activeMembrane);
}
""",
        )
        self.assertEqual(
            first["point_displacement_motion_patch_fragment"],
            """activeMembrane
{
    type                uniformInterpolatedDisplacement;
    value               uniform (0 0 0);
    field               p2PrescribedPointDisplacement;
    interpolationScheme linear;
}
""",
        )
        rendered = json.dumps(first, sort_keys=True)
        for forbidden in module.FORBIDDEN_DIALECT:
            self.assertNotIn(forbidden, first["dynamic_mesh_dict_mover_fragment"])
            if forbidden != "oscillatingDisplacement":
                self.assertNotIn(forbidden, rendered)

    def test_truth_boundary_and_required_future_checks_are_explicit(self) -> None:
        result = module.generate(str(self.path), self.pin)
        self.assertTrue(result["descriptor_sha256_is_caller_supplied_pin"])
        for key in (
            "descriptor_authority_verified",
            "descriptor_pin_authority_verified",
            "source_commit_verified",
            "source_commit_authority_verified",
            "geometry_manifest_verified",
            "geometry_verified",
            "motion_patch_verified_against_mesh",
            "motion_patch_exists_verified",
            "patch_inventory_verified",
            "complete_point_displacement_file_generated",
            "point_displacement_header_generated",
            "non_motion_patch_entries_generated",
            "real_p2_artifact_bytes_consumed",
            "real_p2_spatial_field_available",
            "p2_artifact_authority_verified",
            "mesh_identity_verified",
            "motion_field_point_order_verified",
            "p2_node_to_openfoam_point_bijection_verified",
            "p2_mapping_verified",
            "p2_component_order_verified",
            "p2_spatial_units_verified",
            "p2_coordinate_transform_verified",
            "p2_phase_time_origin_verified",
            "p2_time_sampling_verified",
            "control_dict_user_time_verified",
            "period_closure_verified",
            "uniform_amplitude_vector_used_as_p2_mode",
            "case_file_written",
            "openfoam_runtime_syntax_verified",
            "diffusivity_suitability_verified",
            "mesh_motion_verified",
            "negative_volume_verified",
            "mesh_quality_verified",
            "p2_displacement_verified",
            "p2_displacement_authorized",
            "p3_authorized",
            "p3_case_write_authorized",
            "p3_solver_run_authorized",
            "solver_verified",
            "solver_authorized",
            "stage_gate_advanced",
        ):
            self.assertIs(result[key], False, key)
        required = result["required_before_case_write"]
        self.assertEqual(required["point_displacement_class"], "pointVectorField")
        self.assertEqual(required["point_displacement_dimensions"], "[length]")
        self.assertEqual(
            required["point_displacement_internal_field"], "uniform (0 0 0)"
        )
        for key, status in required.items():
            if key not in {
                "point_displacement_class",
                "point_displacement_dimensions",
                "point_displacement_internal_field",
            }:
                self.assertEqual(status, "REQUIRED_NOT_VERIFIED", key)
        self.assertTrue(result["descriptor_bytes_match_caller_pin"])
        self.assertTrue(result["descriptor_schema_accepted"])
        self.assertTrue(result["foundation_v14_template_emitted"])
        self.assertTrue(result["legacy_dialect_rejected"])
        self.assertTrue(result["oscillating_displacement_rejected"])
        self.assertEqual(result["formal_gate_effect"], "NONE")

    def test_pin_is_checked_before_json_parse(self) -> None:
        with mock.patch.object(module.json, "loads") as parser:
            with self.assertRaisesRegex(module.MotionContractError, "PIN_MISMATCH"):
                module.generate(str(self.path), "0" * 64)
            parser.assert_not_called()

    def test_safe_reader_is_reused(self) -> None:
        original = module.read_bounded_regular_file
        with mock.patch.object(
            module, "read_bounded_regular_file", wraps=original
        ) as reader:
            module.generate(str(self.path), self.pin)
        reader.assert_called_once_with(
            str(self.path), module.MAX_CONTRACT_BYTES, "DESCRIPTOR_READ_REJECTED"
        )

    def test_argument_configuration_requires_absolute_path_and_lowercase_pin(self) -> None:
        cases = (
            [],
            [str(self.path)],
            ["relative.json", self.pin],
            [str(self.path), "A" * 64],
            [str(self.path), "0" * 63],
            [str(self.path), self.pin, "extra"],
        )
        for args in cases:
            with self.subTest(args=args), contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(module.main(args), 3)
            result = json.loads(out.getvalue())
            self.assertEqual(result["status"], "REJECTED")
            self.assertFalse(result["solver_authorized"])
        with self.assertRaisesRegex(module.MotionContractError, "ARGUMENT_CONFIG"):
            module.generate("relative.json", self.pin)
        for descriptor, pin in ((None, self.pin), (str(self.path), None)):
            with self.subTest(descriptor=descriptor, pin=pin):
                with self.assertRaisesRegex(
                    module.MotionContractError, "ARGUMENT_CONFIG"
                ):
                    module.generate(descriptor, pin)  # type: ignore[arg-type]

    def test_exact_keys_schema_types_and_frozen_values(self) -> None:
        cases = (
            ("missing", lambda value: value.pop("motion_patch")),
            ("extra", lambda value: value.update({"motionSolver": "legacy"})),
            ("schema", lambda value: value.update({"schema_version": "wrong"})),
            ("distribution", lambda value: value.update({"openfoam_distribution": "other"})),
            ("major_bool", lambda value: value.update({"openfoam_major": True})),
            ("major", lambda value: value.update({"openfoam_major": 13})),
            ("scope", lambda value: value.update({"case_scope": "P4"})),
            ("commit", lambda value: value.update({"source_commit": "A" * 40})),
            ("geometry", lambda value: value.update({"geometry_manifest_sha256": "A" * 64})),
            ("field_status", lambda value: value.update({"motion_field_status": "AVAILABLE"})),
            ("write", lambda value: value.update({"point_displacement_file_generation": "ALLOW"})),
            ("p2_true", lambda value: value.update({"p2_artifact_authorized": True})),
            ("p2_zero", lambda value: value.update({"p2_artifact_authorized": 0})),
            ("p3_true", lambda value: value.update({"p3_case_write_authorized": True})),
            ("solver_true", lambda value: value.update({"solver_authorized": True})),
            ("gate", lambda value: value.update({"formal_gate_effect": "P3_PASS"})),
        )
        for name, mutate in cases:
            with self.subTest(name=name):
                value = valid_descriptor()
                mutate(value)
                path, pin = write_descriptor(self.directory, value)
                with self.assertRaises(module.MotionContractError):
                    module.generate(str(path), pin)

    def test_foam_word_injection_and_aliases_are_rejected(self) -> None:
        for patch in (
            "",
            "1patch",
            "patch-name",
            "../patch",
            "patch/name",
            "patch;solver",
            "patch name",
            "x" * 64,
            "oscillatingDisplacement",
            "motionSolver",
        ):
            with self.subTest(patch=patch):
                value = valid_descriptor()
                value["motion_patch"] = patch
                path, pin = write_descriptor(self.directory, value)
                with self.assertRaises(module.MotionContractError):
                    module.generate(str(path), pin)

    def test_all_legacy_and_uniform_mode_dialect_tokens_are_rejected(self) -> None:
        for token in module.FORBIDDEN_DIALECT:
            with self.subTest(token=token):
                value = valid_descriptor()
                value["motion_patch"] = token
                path, pin = write_descriptor(self.directory, value)
                with self.assertRaisesRegex(
                    module.MotionContractError,
                    "LEGACY_OR_UNIFORM_MODE_DIALECT_REJECTED",
                ):
                    module.generate(str(path), pin)

    def test_duplicate_deep_large_string_float_and_nonfinite_are_rejected(self) -> None:
        raw_cases = (
            b'{"schema_version":"a","schema_version":"b"}',
            b"[" * (module.MAX_JSON_DEPTH + 1) + b"0" + b"]" * (module.MAX_JSON_DEPTH + 1),
            b'{"x":1.25}',
            b'{"x":NaN}',
            b'{"x":99999999999999999}',
        )
        for index, data in enumerate(raw_cases):
            with self.subTest(index=index):
                path = self.directory / f"raw-{index}.json"
                path.write_bytes(data)
                pin = hashlib.sha256(data).hexdigest()
                with self.assertRaises(module.MotionContractError):
                    module.generate(str(path), pin)
        value = valid_descriptor()
        value["motion_patch"] = "x" * (module.MAX_STRING_CHARS + 1)
        path, pin = write_descriptor(self.directory, value)
        with self.assertRaisesRegex(module.MotionContractError, "STRING_LIMIT"):
            module.generate(str(path), pin)

    def test_bom_nul_invalid_utf8_and_malformed_json_rejected(self) -> None:
        cases = (
            b"\xef\xbb\xbf{}",
            b'{"x":"a\x00b"}',
            b"\xff",
            b"{",
        )
        for index, data in enumerate(cases):
            with self.subTest(index=index):
                path = self.directory / f"encoding-{index}.json"
                path.write_bytes(data)
                pin = hashlib.sha256(data).hexdigest()
                with self.assertRaises(module.MotionContractError):
                    module.generate(str(path), pin)

    def test_node_bound_and_oversize_empty_directory_are_rejected(self) -> None:
        nodes = {"x": [0] * (module.MAX_JSON_NODES + 1)}
        path, pin = write_descriptor(self.directory, nodes)
        with self.assertRaisesRegex(module.MotionContractError, "NODE_LIMIT"):
            module.generate(str(path), pin)

        oversized = self.directory / "oversized.json"
        oversized.write_bytes(b" " * (module.MAX_CONTRACT_BYTES + 1))
        pin = hashlib.sha256(oversized.read_bytes()).hexdigest()
        with self.assertRaises(module.MotionContractError):
            module.generate(str(oversized), pin)

        empty = self.directory / "empty.json"
        empty.write_bytes(b"")
        with self.assertRaises(module.MotionContractError):
            module.generate(str(empty), hashlib.sha256(b"").hexdigest())

        with self.assertRaises(module.MotionContractError):
            module.generate(str(self.directory), "0" * 64)

    def test_symlink_descriptor_is_rejected_when_available(self) -> None:
        link = self.directory / "link.json"
        try:
            link.symlink_to(self.path)
        except (OSError, NotImplementedError):
            self.skipTest("symlink privilege unavailable")
        with self.assertRaises(module.MotionContractError):
            module.generate(str(link), self.pin)

    def test_cli_success_is_deterministic_path_free_and_failure_is_redacted(self) -> None:
        outputs = []
        for _ in range(2):
            with contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(module.main([str(self.path), self.pin]), 0)
            outputs.append(out.getvalue())
        self.assertEqual(outputs[0], outputs[1])
        self.assertNotIn(str(self.path), outputs[0])

        secret = self.directory / "SECRET_DESCRIPTOR.json"
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(module.main([str(secret), "0" * 64]), 2)
        self.assertNotIn("SECRET_DESCRIPTOR", out.getvalue())
        self.assertNotIn("Traceback", out.getvalue())

    def test_cli_failure_truth_preserves_completed_pin_phase(self) -> None:
        wrong_schema = valid_descriptor()
        wrong_schema["schema_version"] = "wrong"
        path, pin = write_descriptor(self.directory, wrong_schema)
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(module.main([str(path), pin]), 2)
        result = json.loads(out.getvalue())
        self.assertTrue(result["descriptor_bytes_match_caller_pin"])
        self.assertFalse(result["descriptor_schema_accepted"])
        self.assertEqual(
            result["error"]["code"], "SCHEMA_VERSION_MISMATCH"
        )

        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(module.main([str(path), "0" * 64]), 2)
        result = json.loads(out.getvalue())
        self.assertFalse(result["descriptor_bytes_match_caller_pin"])
        self.assertFalse(result["descriptor_schema_accepted"])

    def test_generator_has_no_write_process_network_or_solver_api(self) -> None:
        source = Path(module.__file__).read_text(encoding="utf-8")
        for token in (
            "subprocess",
            "socket",
            ".write_text(",
            ".write_bytes(",
            "os.system(",
            "Popen(",
            "urlopen(",
            "requests",
            "foamRun",
            "blockMesh",
        ):
            self.assertNotIn(token, source)


if __name__ == "__main__":
    unittest.main(verbosity=2)

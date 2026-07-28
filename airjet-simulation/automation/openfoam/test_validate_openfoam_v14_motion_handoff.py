#!/usr/bin/env python3
"""Adversarial tests for the source-only P3 motion negative interlock."""

from __future__ import annotations

import contextlib
import copy
import ast
import hashlib
import io
import json
import os
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from unittest import mock


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import validate_openfoam_v14_motion_handoff as module  # noqa: E402
import generate_openfoam_v14_motion_contract as motion_source  # noqa: E402
import plan_p3_timestep_matrix as timestep_source  # noqa: E402


def p2_receipt() -> dict:
    return {
        "status": module.EXPECTED_STATUSES["p2_artifact_receipt"],
        "contract_sha256": "a" * 64,
        "snapshot_root_identity_bound": True,
        "artifacts": [
            {"role": role, "size_bytes": index + 1, "sha256": str(index + 1) * 64}
            for index, role in enumerate(
                ("nodes", "connectivity", "displacement_vector_field")
            )
        ],
        **module.P2_TRUTH,
        "formal_gate_effect": "NONE",
    }


def motion_contract() -> dict:
    return motion_source._envelope(
        {
            "source_commit": "1" * 40,
            "geometry_manifest_sha256": "2" * 64,
        },
        "a" * 64,
        "activeMembrane",
    )


def timestep_plan() -> dict:
    return timestep_source.build_result(
        {
            "source_commit": "1" * 40,
            "frequency_status": "PLANNING_INPUT_NOT_P2_AUTHORIZED",
        },
        "b" * 64,
        Decimal("22000"),
        3,
        10,
    )


def write_json(directory: Path, name: str, value: object) -> tuple[str, str]:
    path = directory / name
    data = json.dumps(value, ensure_ascii=True, separators=(",", ":")).encode("ascii")
    path.write_bytes(data)
    return str(path), hashlib.sha256(data).hexdigest()


class MotionHandoffInterlockTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.directory = Path(self.temporary.name)
        self.values = [p2_receipt(), motion_contract(), timestep_plan()]
        self.args: list[str] = []
        for name, value in zip(("p2.json", "motion.json", "time.json"), self.values):
            self.args.extend(write_json(self.directory, name, value))

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_valid_source_only_trio_is_deterministically_blocked_nonzero(self) -> None:
        first = module.validate(self.args)
        second = module.validate(self.args)
        self.assertEqual(first, second)
        self.assertEqual(first["status"], "P3_MOTION_HANDOFF_BLOCKED_REQUIRED_AUTHORITY")
        self.assertEqual(first["blockers"], list(module.BLOCKERS))
        self.assertNotIn("PASS", json.dumps(first))
        for phase in first["input_phases"].values():
            self.assertEqual(
                phase,
                {
                    "bytes_pinned": True,
                    "bytes_pin_phase": "COMPLETE",
                    "json_parsed": True,
                    "json_parse_phase": "COMPLETE",
                    "contract_recognized": True,
                    "contract_recognition_phase": "COMPLETE",
                },
            )
        with contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(module.main(self.args), module.BLOCKED_EXIT)
        self.assertEqual(json.loads(output.getvalue()), first)

    def test_blocker_list_is_exact_and_all_authority_remains_false(self) -> None:
        result = module.validate(self.args)
        self.assertEqual(
            tuple(result["blockers"]),
            (
                "TRUSTED_P2_AUTHORITY",
                "REAL_P2_SPATIAL_FIELD",
                "MESH_BOUND_POINT_BIJECTION",
                "COORDINATE_UNIT_PHASE_TIME_VERIFICATION",
                "COMPLETE_POINT_DISPLACEMENT",
                "OPENFOAM_V14_RUNTIME_SYNTAX_VERIFICATION",
                "MESH_MOTION_QUALITY_VERIFICATION",
                "CFL_VERIFICATION",
                "PERIODIC_STABILITY_VERIFICATION",
                "TIMESTEP_INDEPENDENCE_VERIFICATION",
                "INDEPENDENT_GATE_ACCEPTANCE",
            ),
        )
        for key, value in module._base_truth().items():
            if key != "formal_gate_effect":
                self.assertIs(result[key], False)
        self.assertEqual(result["formal_gate_effect"], "NONE")
        self.assertEqual(
            {key: result[key] for key in module.TASK_CLASSIFICATION},
            module.TASK_CLASSIFICATION,
        )
        self.assertEqual(
            {
                key: result[key]
                for key in module._source_processing_truth(True, True, True)
            },
            module._source_processing_truth(True, True, True),
        )

    def test_all_three_pins_complete_before_any_json_parse(self) -> None:
        bad = list(self.args)
        bad[5] = "0" * 64
        with mock.patch.object(module.json, "loads") as parser:
            with self.assertRaises(module.InterlockError) as caught:
                module.validate(bad)
            parser.assert_not_called()
        self.assertEqual(caught.exception.pinned, (True, True, False))
        self.assertEqual(caught.exception.parsed, (False, False, False))
        self.assertEqual(
            caught.exception.pin_states, ("COMPLETE", "COMPLETE", "REJECTED")
        )
        self.assertEqual(
            caught.exception.parse_states,
            ("NOT_EVALUATED", "NOT_EVALUATED", "NOT_EVALUATED"),
        )

    def test_all_three_reads_complete_before_parse(self) -> None:
        calls: list[str] = []
        original_read = module.read_bounded_regular_file
        original_parse = module._parse

        def read(path, maximum, code):
            calls.append("read")
            return original_read(path, maximum, code)

        def parse(data):
            calls.append("parse")
            return original_parse(data)

        with mock.patch.object(module, "read_bounded_regular_file", side_effect=read), mock.patch.object(
            module, "_parse", side_effect=parse
        ):
            module.validate(self.args)
        self.assertEqual(calls[:3], ["read", "read", "read"])
        self.assertEqual(calls[3:], ["parse", "parse", "parse"])

    def test_exact_source_statuses_only(self) -> None:
        for index in range(3):
            with self.subTest(index=index):
                values = copy.deepcopy(self.values)
                values[index]["status"] += "_PASS"
                args: list[str] = []
                for name, value in zip(("a.json", "b.json", "c.json"), values):
                    args.extend(write_json(self.directory, name, value))
                with self.assertRaises(module.InterlockError):
                    module.validate(args)

    def test_current_full_source_envelopes_are_recognized_only_as_blocked(self) -> None:
        motion = motion_source._envelope(
            {
                "source_commit": "1" * 40,
                "geometry_manifest_sha256": "2" * 64,
            },
            "a" * 64,
            "activeMembrane",
        )
        timestep = timestep_source.build_result(
            {
                "source_commit": "1" * 40,
                "frequency_status": "PLANNING_INPUT_NOT_P2_AUTHORIZED",
            },
            "b" * 64,
            Decimal("22000"),
            3,
            10,
        )
        args: list[str] = []
        for name, value in (
            ("full-p2.json", p2_receipt()),
            ("full-motion.json", motion),
            ("full-time.json", timestep),
        ):
            args.extend(write_json(self.directory, name, value))
        result = module.validate(args)
        self.assertEqual(
            result["status"], "P3_MOTION_HANDOFF_BLOCKED_REQUIRED_AUTHORITY"
        )
        self.assertFalse(result["cross_output_identity_bound"])

    def test_every_required_false_truth_rejects_true_null_string_or_missing(self) -> None:
        groups = (
            (0, module.P2_TRUTH),
            (1, module.MOTION_TRUTH),
            (2, module.TIMESTEP_TRUTH),
        )
        for index, expected in groups:
            for key, wanted in expected.items():
                if wanted is not False:
                    continue
                for replacement in (True, None, "unknown"):
                    with self.subTest(source=index, key=key, replacement=replacement):
                        values = copy.deepcopy(self.values)
                        values[index][key] = replacement
                        args: list[str] = []
                        for name, value in zip(("x.json", "y.json", "z.json"), values):
                            args.extend(write_json(self.directory, name, value))
                        with self.assertRaisesRegex(
                            module.InterlockError, "SOURCE_TRUTH_CONTRADICTION"
                        ):
                            module.validate(args)

    def test_unknown_authorization_and_verification_claims_reject_even_false(self) -> None:
        for index, key in (
            (0, "invented_authorized"),
            (1, "new_engineering_verified"),
            (2, "mystery_gate_accepted"),
        ):
            with self.subTest(index=index, key=key):
                values = copy.deepcopy(self.values)
                values[index][key] = False
                args: list[str] = []
                for name, value in zip(("u.json", "v.json", "w.json"), values):
                    args.extend(write_json(self.directory, name, value))
                with self.assertRaisesRegex(
                    module.InterlockError, "UNKNOWN_AUTHORIZATION"
                ):
                    module.validate(args)

    def test_required_not_verified_motion_checks_are_exact(self) -> None:
        for key in module.MOTION_REQUIRED:
            for replacement in (True, False, None, "unknown", "VERIFIED"):
                with self.subTest(key=key, replacement=replacement):
                    values = copy.deepcopy(self.values)
                    values[1]["required_before_case_write"][key] = replacement
                    args: list[str] = []
                    for name, value in zip(("r.json", "s.json", "t.json"), values):
                        args.extend(write_json(self.directory, name, value))
                    with self.assertRaises(module.InterlockError):
                        module.validate(args)

    def test_failure_phase_truth_is_precise_and_has_no_partial_authority(self) -> None:
        values = copy.deepcopy(self.values)
        values[1]["solver_authorized"] = True
        args: list[str] = []
        for name, value in zip(("p2x.json", "mx.json", "tx.json"), values):
            args.extend(write_json(self.directory, name, value))
        with contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(module.main(args), 2)
        result = json.loads(output.getvalue())
        self.assertEqual(result["status"], "REJECTED")
        self.assertTrue(result["input_phases"]["p2_artifact_receipt"]["contract_recognized"])
        self.assertFalse(result["input_phases"]["motion_contract"]["contract_recognized"])
        self.assertTrue(result["input_phases"]["timestep_plan"]["json_parsed"])
        self.assertTrue(result["all_output_bytes_match_caller_pins"])
        self.assertFalse(result["all_output_schemas_accepted"])
        self.assertFalse(
            result["all_upstream_non_authorization_constraints_accepted"]
        )
        self.assertFalse(result["blocker_evaluation_completed"])
        self.assertFalse(result["p3_motion_handoff_authorized"])
        self.assertNotIn("PASS", output.getvalue())

    def test_duplicate_nonfinite_bom_nul_utf8_depth_string_and_root_reject(self) -> None:
        raw_cases = (
            b'{"status":"a","status":"b"}',
            b'{"x":NaN}',
            b"\xef\xbb\xbf{}",
            b'{"x":"a\x00b"}',
            b"\xff",
            b"[" * (module.MAX_DEPTH + 1) + b"0" + b"]" * (module.MAX_DEPTH + 1),
            json.dumps({"x": "z" * (module.MAX_STRING + 1)}).encode(),
            b"[]",
            b"}",
            b'{"x":"unterminated}',
            b'{"x":[1,2}',
        )
        for index, data in enumerate(raw_cases):
            with self.subTest(index=index):
                path = self.directory / f"bad-{index}.json"
                path.write_bytes(data)
                args = list(self.args)
                args[0] = str(path)
                args[1] = hashlib.sha256(data).hexdigest()
                with self.assertRaises(module.InterlockError):
                    module.validate(args)

    def test_p2_artifact_shape_and_timestep_plan_shape_reject(self) -> None:
        mutations = (
            (0, lambda value: value["artifacts"].pop()),
            (0, lambda value: value["artifacts"][0].update({"size_bytes": True})),
            (0, lambda value: value["artifacts"][0].update({"sha256": "A" * 64})),
            (0, lambda value: value["artifacts"].reverse()),
            (
                0,
                lambda value: value["artifacts"][0].update(
                    {"size_bytes": module.MAX_ARTIFACT_BYTES + 1}
                ),
            ),
            (
                0,
                lambda value: [
                    item.update({"size_bytes": 400 * 1024 * 1024})
                    for item in value["artifacts"]
                ],
            ),
            (2, lambda value: value["plans"].reverse()),
            (2, lambda value: value["plans"][0].update({"endpoint_row_count_asserted": True})),
            (2, lambda value: value["plans"][0].update({"endpoint_row_count_asserted": 0})),
            (2, lambda value: value["plans"][0].update({"sample_every_steps": True})),
            (2, lambda value: value.pop("schema_version")),
            (2, lambda value: value.update({"frequency_hz": "22000.0"})),
            (2, lambda value: value.update({"decimal_context_precision_digits": 59})),
            (2, lambda value: value["plans"][0].update({"delta_t_s": "0.1"})),
        )
        for index, mutate in mutations:
            with self.subTest(index=index):
                values = copy.deepcopy(self.values)
                mutate(values[index])
                args: list[str] = []
                for name, value in zip(("shape-a.json", "shape-b.json", "shape-c.json"), values):
                    args.extend(write_json(self.directory, name, value))
                with self.assertRaises(module.InterlockError):
                    module.validate(args)

    def test_motion_envelope_requires_exact_v14_patch_and_fragments(self) -> None:
        mutations = (
            lambda value: value.pop("schema_version"),
            lambda value: value.pop("descriptor_sha256"),
            lambda value: value.update({"openfoam_distribution": "OpenFOAM"}),
            lambda value: value.update({"openfoam_major": 13}),
            lambda value: value.update({"motion_patch": "bad-patch"}),
            lambda value: value.update({"point_vector_field_name": "pointDisplacement"}),
            lambda value: value.update({"dynamic_mesh_dict_mover_fragment": "mover{}"}),
            lambda value: value.update(
                {"point_displacement_motion_patch_fragment": "activeMembrane{}"}
            ),
            lambda value: value.update(
                {"uniform_interpolated_displacement_semantics": "UNIFORM_AMPLITUDE"}
            ),
            lambda value: value["required_before_case_write"].pop(
                "motion_field_count_at_least_two"
            ),
        )
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                values = copy.deepcopy(self.values)
                mutate(values[1])
                args: list[str] = []
                for name, value in zip(("ma.json", "mb.json", "mc.json"), values):
                    args.extend(write_json(self.directory, name, value))
                with self.assertRaisesRegex(
                    module.InterlockError, "MOTION_SOURCE_SHAPE_REJECTED"
                ):
                    module.validate(args)

    def test_exact_top_level_producer_surfaces_reject_missing_or_extra_fields(self) -> None:
        for index in range(3):
            for mode in ("missing", "extra"):
                with self.subTest(index=index, mode=mode):
                    values = copy.deepcopy(self.values)
                    if mode == "missing":
                        values[index].pop(next(iter(values[index])))
                    else:
                        values[index]["benign_note"] = "source only"
                    args: list[str] = []
                    for name, value in zip(("ea.json", "eb.json", "ec.json"), values):
                        args.extend(write_json(self.directory, name, value))
                    with self.assertRaises(module.InterlockError):
                        module.validate(args)

    def test_argument_config_requires_six_alternating_absolute_path_pin_args(self) -> None:
        cases = (
            [],
            self.args[:-1],
            ["relative.json", *self.args[1:]],
            [self.args[0], "A" * 64, *self.args[2:]],
            [*self.args, "extra"],
        )
        for args in cases:
            with self.subTest(length=len(args)), contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(module.main(args), 3)
            result = json.loads(output.getvalue())
            self.assertEqual(result["status"], "REJECTED")
            self.assertFalse(result["solver_run_authorized"])

    def test_same_canonical_source_path_is_configuration_rejection(self) -> None:
        args = list(self.args)
        args[2] = args[0]
        args[3] = args[1]
        with contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(module.main(args), 3)
        self.assertEqual(
            json.loads(output.getvalue())["error"]["code"],
            "DUPLICATE_CANONICAL_SOURCE_PATH",
        )

    def test_unknown_truth_case_unicode_boolean_and_pass_string_reject(self) -> None:
        attacks = (
            ("Solver_Authorized", False),
            ("caseWrite", "PASS"),
            ("invented_boolean", True),
            ("solver_authoriz\uff45d", False),
        )
        for key, value in attacks:
            with self.subTest(key=key):
                values = copy.deepcopy(self.values)
                values[1][key] = value
                args: list[str] = []
                for name, item in zip(("ua.json", "ub.json", "uc.json"), values):
                    args.extend(write_json(self.directory, name, item))
                with self.assertRaises(module.InterlockError):
                    module.validate(args)

    def test_safe_reader_errors_redact_paths_and_no_traceback(self) -> None:
        secret = str(self.directory / "SECRET_SOURCE.json")
        args = list(self.args)
        args[0] = secret
        args[1] = "0" * 64
        with contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(module.main(args), 2)
        self.assertNotIn("SECRET_SOURCE", output.getvalue())
        self.assertNotIn("Traceback", output.getvalue())

    def test_symlink_and_hardlink_inputs_reject_when_available(self) -> None:
        target = Path(self.args[0])
        symlink = self.directory / "source-link.json"
        try:
            symlink.symlink_to(target)
        except (OSError, NotImplementedError):
            symlink = None
        if symlink is not None:
            args = list(self.args)
            args[0] = str(symlink)
            with self.assertRaises(module.InterlockError):
                module.validate(args)

        hardlink = self.directory / "source-hard.json"
        try:
            os.link(target, hardlink)
        except OSError:
            self.skipTest("hardlink unavailable")
        args = list(self.args)
        args[0] = str(hardlink)
        with self.assertRaises(module.InterlockError):
            module.validate(args)

    def test_no_write_process_network_solver_or_pass_path(self) -> None:
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

        tree = ast.parse(source)
        allowed_imports = {
            "__future__",
            "dataclasses",
            "decimal",
            "hmac",
            "json",
            "os",
            "re",
            "safe_artifact_io",
            "sys",
            "typing",
        }
        forbidden_calls = {
            "__import__",
            "eval",
            "exec",
            "makedirs",
            "mkdir",
            "open",
            "popen",
            "remove",
            "rename",
            "replace",
            "rmdir",
            "run",
            "spawn",
            "startfile",
            "system",
            "unlink",
            "write",
            "write_bytes",
            "write_text",
        }
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = {name.name.split(".")[0] for name in node.names}
                self.assertLessEqual(names, allowed_imports)
            elif isinstance(node, ast.ImportFrom):
                self.assertIn((node.module or "").split(".")[0], allowed_imports)
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    called = node.func.id.lower()
                    self.assertNotIn(called, {"__import__", "compile", "eval", "exec"})
                elif isinstance(node.func, ast.Attribute):
                    called = node.func.attr.lower()
                else:
                    continue
                self.assertNotIn(called, forbidden_calls)


if __name__ == "__main__":
    unittest.main(verbosity=2)

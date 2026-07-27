#!/usr/bin/env python3
"""Adversarial tests for the P2-to-P3 byte-only artifact consumer."""

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
REFERENCE_SRC = HERE / "coupling_contract_reference_v2" / "src"
sys.path.insert(0, str(REFERENCE_SRC))

import safe_artifact_io  # noqa: E402
import consume_p2_to_p3_artifact_bytes as consumer_module  # noqa: E402
from airjet_coupling.validator import _schema_for, P2_TYPE  # noqa: E402
from consume_p2_to_p3_artifact_bytes import consume, main  # noqa: E402
from safe_artifact_io import SafeArtifactError  # noqa: E402


ROLES = ("nodes", "connectivity", "displacement_vector_field")


def valid_contract(root: Path) -> dict:
    schema_hash = _schema_for(P2_TYPE)[2]
    contents = {
        "nodes": b"node-bytes",
        "connectivity": b"connectivity-bytes",
        "displacement_vector_field": b"displacement-bytes",
    }
    artifacts = []
    for role in ROLES:
        relative = f"fields/{role}.bin"
        path = root / Path(*relative.split("/"))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(contents[role])
        item = {
            "role": role,
            "path": relative,
            "size_bytes": len(contents[role]),
            "sha256": hashlib.sha256(contents[role]).hexdigest(),
            "media_type": "application/octet-stream",
        }
        if role == "displacement_vector_field":
            item.update({"components": ["ux", "uy", "uz"], "value_unit": "mm"})
        artifacts.append(item)
    return {
        "contract_type": P2_TYPE,
        "contract_version": "2.0.0",
        "identity": {
            "task_id": "AJM-P2-TEST",
            "session_id": "session-test",
            "snapshot_id": "snap_0123456789abcdef",
            "receipt_id": "rcpt_0123456789abcdef",
            "schema_sha256": schema_hash,
        },
        "coordinate_system": {
            "frame_id": "AJM_CELL_LOCAL",
            "origin": [0, 0, 0],
            "axes": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
            "handedness": "right",
            "length_unit": "mm",
        },
        "temporal_sampling": {
            "frequency": 22000,
            "frequency_unit": "Hz",
            "phase_reference_deg": 0,
            "samples_per_cycle": 400,
            "period_count": 3,
            "time_origin_s": 0,
        },
        "artifacts": artifacts,
        "mapping": {
            "method": "barycentric",
            "tolerance": 0.001,
            "tolerance_unit": "mm",
            "coverage_scope": "ALL_DISPLACEMENT_FIELD_NODES",
            "unmapped_policy": "FAIL_IF_ACTIVE_MEMBRANE_NODE_UNMAPPED",
            "maximum_unmapped_fraction": 0.0001,
        },
        "mechanical_metrics": {
            "minimum_gap": {"value": 0.02, "unit": "mm", "provenance_ref": "gap-d"},
            "maximum_stress": {"value": 1, "unit": "Pa", "provenance_ref": "stress-p"},
            "electrical_power": {"value": 1, "unit": "W", "provenance_ref": "power-c"},
        },
        "provenance": {
            "claims": [
                {
                    "id": "gap-d", "classification": "D", "assertion_kind": "measured_fact",
                    "source_ref": "producer:test", "derivation": "",
                    "uncertainty": {"kind": "absolute", "lower": -0.1, "upper": 0.1, "unit": "mm"},
                },
                {
                    "id": "stress-p", "classification": "P", "assertion_kind": "patent_bound",
                    "source_ref": "producer:test", "derivation": "bounded",
                    "uncertainty": {"kind": "relative", "lower": -0.1, "upper": 0.1, "unit": "1"},
                },
                {
                    "id": "power-c", "classification": "C", "assertion_kind": "calibration",
                    "source_ref": "producer:test", "derivation": "calibrated",
                    "uncertainty": {"kind": "relative", "lower": -0.1, "upper": 0.1, "unit": "1"},
                },
            ]
        },
    }


def write_contract(directory: Path, document: dict) -> tuple[Path, str]:
    path = directory / "contract.json"
    data = json.dumps(document, separators=(",", ":")).encode()
    path.write_bytes(data)
    return path, hashlib.sha256(data).hexdigest()


class ConsumerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name)
        self.root = self.base / "Snapshot"
        self.root.mkdir()
        self.document = valid_contract(self.root)
        self.contract, self.pin = write_contract(self.base, self.document)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_success_returns_only_byte_receipts_and_conservative_truth(self) -> None:
        result = consume(str(self.contract), str(self.root), self.pin)
        self.assertEqual(
            result["status"], "P2_ARTIFACT_BYTES_MATCH_CALLER_PIN_NOT_AUTHORIZED"
        )
        self.assertEqual(result["contract_sha256"], self.pin)
        self.assertTrue(result["snapshot_root_identity_bound"])
        self.assertEqual([item["role"] for item in result["artifacts"]], list(ROLES))
        self.assertEqual(set(result["artifacts"][0]), {"role", "size_bytes", "sha256"})
        self.assertTrue(result["byte_contract_accepted"])
        self.assertTrue(result["schema_contract_accepted"])
        self.assertTrue(result["artifact_bytes_match_descriptor"])
        self.assertTrue(result["expected_contract_sha256_is_caller_supplied_pin"])
        for key in (
            "contract_authority_verified", "artifact_physical_content_parsed",
            "receipt_is_persistent_snapshot_authority",
            "verified_bytes_reopen_authorized",
            "verification_handles_retained_after_return",
            "artifact_mapping_verified", "artifact_units_verified",
            "artifact_phase_verified", "artifact_cross_file_semantics_verified",
            "p2_displacement_verified", "p2_displacement_authorized",
            "p3_authorized", "solver_authorized", "stage_gate_advanced",
        ):
            self.assertIs(result[key], False)
        self.assertEqual(result["formal_gate_effect"], "NONE")

    def test_self_consistent_truth_labels_do_not_authorize_physics(self) -> None:
        document = copy.deepcopy(self.document)
        document["provenance"]["claims"][0]["source_ref"] = "producer:self-asserted-pass"
        contract, pin = write_contract(self.base, document)
        self.assertFalse(
            consume(str(contract), str(self.root), pin)["p2_displacement_authorized"]
        )

    def test_invalid_contract_is_rejected_before_artifact_access(self) -> None:
        document = copy.deepcopy(self.document)
        document["contract_type"] = "AIRJET_P4_TO_P5_WALL_CHT"
        contract, pin = write_contract(self.base, document)
        with mock.patch.object(consumer_module, "verify_artifacts") as forbidden:
            with self.assertRaises(SafeArtifactError):
                consume(str(contract), str(self.root), pin)
            forbidden.assert_not_called()

    def test_wrong_pin_rejects_before_validation_or_artifact_access(self) -> None:
        with mock.patch("consume_p2_to_p3_artifact_bytes.load_json_bytes") as parser:
            with self.assertRaisesRegex(SafeArtifactError, "CONTRACT_PIN_MISMATCH"):
                consume(str(self.contract), str(self.root), "0" * 64)
            parser.assert_not_called()

    def test_path_attacks_are_rejected(self) -> None:
        attacks = (
            "../escape.bin", "/absolute.bin", "fields\\nodes.bin", "fields//nodes.bin",
            "fields/./nodes.bin", "fields/x:ads", "fields/con", "fields/a\x01b",
            "fields/e\u0301.bin",
        )
        for attack in attacks:
            with self.subTest(attack=repr(attack)):
                document = copy.deepcopy(self.document)
                document["artifacts"][0]["path"] = attack
                contract, pin = write_contract(self.base, document)
                with self.assertRaises(SafeArtifactError):
                    consume(str(contract), str(self.root), pin)

    def test_wrong_case_and_directory_target_are_rejected(self) -> None:
        document = copy.deepcopy(self.document)
        document["artifacts"][0]["path"] = "Fields/nodes.bin"
        contract, pin = write_contract(self.base, document)
        with self.assertRaises(SafeArtifactError):
            consume(str(contract), str(self.root), pin)

        target = self.root / "fields" / "nodes.bin"
        target.unlink()
        target.mkdir()
        with self.assertRaises(SafeArtifactError):
            consume(str(self.contract), str(self.root), self.pin)

    def test_wrong_case_root_is_rejected(self) -> None:
        wrong = str(self.root).replace("Snapshot", "snapshot")
        self.assertNotEqual(wrong, str(self.root))
        with self.assertRaises(SafeArtifactError):
            consume(str(self.contract), wrong, self.pin)

    def test_symlink_is_rejected_when_supported(self) -> None:
        target = self.root / "fields" / "nodes.bin"
        other = self.base / "other.bin"
        other.write_bytes(b"node-bytes")
        target.unlink()
        try:
            target.symlink_to(other)
        except (OSError, NotImplementedError):
            self.skipTest("symlink creation is unavailable")
        with self.assertRaises(SafeArtifactError):
            consume(str(self.contract), str(self.root), self.pin)

    def test_hardlink_is_rejected(self) -> None:
        target = self.root / "fields" / "nodes.bin"
        alias = self.base / "alias.bin"
        try:
            os.link(target, alias)
        except OSError:
            self.skipTest("hardlink creation is unavailable")
        with self.assertRaises(SafeArtifactError):
            consume(str(self.contract), str(self.root), self.pin)

    def test_intermediate_symlink_or_reparse_is_rejected(self) -> None:
        fields = self.root / "fields"
        actual = self.root / "actual-fields"
        fields.rename(actual)
        try:
            fields.symlink_to(actual, target_is_directory=True)
        except (OSError, NotImplementedError):
            actual.rename(fields)
            self.skipTest("directory symlink/reparse creation is unavailable")
        with self.assertRaises(SafeArtifactError):
            consume(str(self.contract), str(self.root), self.pin)

    def test_reparse_attribute_is_rejected_without_symlink_privilege(self) -> None:
        value = os.stat(self.root / "fields" / "nodes.bin")
        marked = mock.Mock(
            st_mode=value.st_mode,
            st_nlink=value.st_nlink,
            st_file_attributes=safe_artifact_io.REPARSE_POINT_ATTRIBUTE,
        )
        with self.assertRaises(SafeArtifactError):
            safe_artifact_io._regular_single_link(marked, "TEST_REPARSE")

    def test_unavailable_stable_identity_is_rejected(self) -> None:
        value = os.lstat(self.root)
        for device, inode in ((0, value.st_ino), (value.st_dev, 0)):
            unavailable = mock.Mock(
                st_dev=device,
                st_ino=inode,
                st_mode=value.st_mode,
                st_size=value.st_size,
                st_mtime_ns=value.st_mtime_ns,
                st_ctime_ns=value.st_ctime_ns,
                st_nlink=value.st_nlink,
            )
            with self.subTest(device=device, inode=inode):
                with self.assertRaisesRegex(
                    SafeArtifactError, "IDENTITY_UNAVAILABLE"
                ):
                    safe_artifact_io._identity(unavailable)

    def test_size_hash_and_total_bounds_reject(self) -> None:
        for field, value in (("size_bytes", 1), ("sha256", "0" * 64)):
            with self.subTest(field=field):
                document = copy.deepcopy(self.document)
                document["artifacts"][0][field] = value
                contract, pin = write_contract(self.base, document)
                with self.assertRaisesRegex(SafeArtifactError, "ARTIFACT_BYTES_MISMATCH"):
                    consume(str(contract), str(self.root), pin)
        declarations = copy.deepcopy(self.document["artifacts"])
        for item in declarations:
            item["size_bytes"] = safe_artifact_io.MAX_ARTIFACT_BYTES
        with self.assertRaisesRegex(SafeArtifactError, "ARTIFACT_TOTAL_LIMIT"):
            safe_artifact_io.verify_artifacts(str(self.root), declarations)

        declarations = copy.deepcopy(self.document["artifacts"])
        declarations[0]["size_bytes"] = safe_artifact_io.MAX_ARTIFACT_BYTES + 1
        with self.assertRaisesRegex(SafeArtifactError, "ARTIFACT_DECLARATION_REJECTED"):
            safe_artifact_io.verify_artifacts(str(self.root), declarations)

    def test_contract_oversize_is_rejected_without_artifact_access(self) -> None:
        oversized = self.base / "oversized.json"
        data = b"{" + b" " * safe_artifact_io.MAX_CONTRACT_BYTES + b"}"
        oversized.write_bytes(data)
        pin = hashlib.sha256(data).hexdigest()
        with mock.patch.object(consumer_module, "verify_artifacts") as forbidden:
            with self.assertRaisesRegex(SafeArtifactError, "CONTRACT_READ_REJECTED"):
                consume(str(oversized), str(self.root), pin)
            forbidden.assert_not_called()

    def test_open_handle_final_path_redirect_is_rejected(self) -> None:
        redirected = str(self.base / "redirected.bin")
        with mock.patch.object(
            safe_artifact_io, "_handle_final_path", return_value=redirected
        ):
            with self.assertRaises(SafeArtifactError):
                consume(str(self.contract), str(self.root), self.pin)

    def test_darwin_final_path_uses_supported_fcntl_buffer(self) -> None:
        expected = "/private/tmp/artifact.bin"
        fake_fcntl = mock.Mock()

        def get_path(fd, command, buffer):
            self.assertEqual(fd, 17)
            self.assertEqual(command, 50)
            self.assertEqual(len(buffer), 1024)
            return expected.encode() + b"\0" * (1024 - len(expected))

        fake_fcntl.fcntl.side_effect = get_path
        with mock.patch.object(
            safe_artifact_io.sys, "platform", "darwin"
        ), mock.patch.object(
            safe_artifact_io.os, "name", "posix"
        ), mock.patch.dict(sys.modules, {"fcntl": fake_fcntl}):
            self.assertEqual(
                safe_artifact_io._handle_final_path(17),
                os.path.normpath(expected),
            )

    def test_posix_child_fstat_failure_closes_open_fd(self) -> None:
        parent = safe_artifact_io._HeldDirectory(
            "/snapshot", (1,), fd=11
        )
        with mock.patch.object(
            safe_artifact_io.os, "name", "posix"
        ), mock.patch.object(
            safe_artifact_io, "_scan_exact_fd"
        ), mock.patch.object(
            safe_artifact_io.os, "open", return_value=19
        ), mock.patch.object(
            safe_artifact_io.os, "fstat", side_effect=OSError
        ), mock.patch.object(
            safe_artifact_io.os, "close"
        ) as close:
            with self.assertRaises(SafeArtifactError):
                safe_artifact_io._open_child_directory(parent, "fields")
        close.assert_called_once_with(19)

    def test_first_artifact_same_size_overwrite_with_restored_mtime_is_not_accepted(self) -> None:
        original = safe_artifact_io._hash_fd
        calls = 0
        attack_succeeded = False
        attack_blocked = False

        def mutate(fd, maximum, code):
            nonlocal calls, attack_succeeded, attack_blocked
            calls += 1
            # All three artifact handles are retained before hashing.  Schedule
            # the attack while the second artifact is about to be hashed.
            if calls == 2:
                target = self.root / "fields" / "nodes.bin"
                before = target.stat()
                replacement = b"X" * before.st_size
                try:
                    with target.open("r+b") as handle:
                        handle.seek(0)
                        handle.write(replacement)
                        handle.flush()
                        os.fsync(handle.fileno())
                    os.utime(
                        target,
                        ns=(before.st_atime_ns, before.st_mtime_ns),
                    )
                    attack_succeeded = True
                except OSError:
                    # Windows retained handles deny write/delete sharing.
                    attack_blocked = True
            return original(fd, maximum, code)

        rejected = False
        with mock.patch.object(safe_artifact_io, "_hash_fd", side_effect=mutate):
            try:
                consume(str(self.contract), str(self.root), self.pin)
            except SafeArtifactError:
                rejected = True
        self.assertTrue(attack_succeeded or attack_blocked)
        self.assertTrue(attack_blocked or rejected)
        if attack_succeeded:
            self.assertTrue(rejected)

    def test_each_hash_pass_is_bounded_by_declared_size(self) -> None:
        original = safe_artifact_io._hash_fd
        limits = []

        def record(fd, maximum, code):
            limits.append(maximum)
            return original(fd, maximum, code)

        with mock.patch.object(
            safe_artifact_io, "_hash_fd", side_effect=record
        ):
            consume(str(self.contract), str(self.root), self.pin)
        expected = [
            item["size_bytes"] for item in self.document["artifacts"]
        ]
        self.assertEqual(limits, expected + expected)

    @unittest.skipUnless(os.name == "nt", "Windows handle test")
    def test_windows_directory_handle_uses_typed_close(self) -> None:
        handle = safe_artifact_io._win_open_directory(
            str(self.root), "TEST_OPEN"
        )
        self.assertTrue(safe_artifact_io._win_close_handle(handle))

    def test_intermediate_directory_swap_and_recover_is_not_accepted(self) -> None:
        original = safe_artifact_io._hash_fd
        attempted = False
        attack_succeeded = False
        attack_blocked = False

        def swap(fd, maximum, code):
            nonlocal attempted, attack_succeeded, attack_blocked
            if not attempted:
                attempted = True
                fields = self.root / "fields"
                held = self.root / "held-fields"
                replacement = self.root / "replacement-fields"
                try:
                    fields.rename(held)
                    fields.mkdir()
                    fields.rename(replacement)
                    held.rename(fields)
                    attack_succeeded = True
                except OSError:
                    attack_blocked = True
                    # Recover any partially completed test mutation.
                    if held.exists() and not fields.exists():
                        held.rename(fields)
            return original(fd, maximum, code)

        rejected = False
        with mock.patch.object(safe_artifact_io, "_hash_fd", side_effect=swap):
            try:
                consume(str(self.contract), str(self.root), self.pin)
            except SafeArtifactError:
                rejected = True
        self.assertTrue(attack_succeeded or attack_blocked)
        self.assertTrue(attack_blocked or rejected)
        if attack_succeeded:
            self.assertTrue(rejected)

    def test_cli_redacts_paths_and_returns_no_partial_artifacts(self) -> None:
        secret = "SECRET_PATH_MARKER"
        missing = self.base / secret
        with contextlib.redirect_stdout(io.StringIO()) as output:
            code = main([str(self.contract), str(missing), self.pin])
        result = json.loads(output.getvalue())
        self.assertEqual(code, 2)
        self.assertEqual(result["artifacts"], [])
        self.assertEqual(result["status"], "REJECTED")
        self.assertFalse(result["artifact_bytes_match_descriptor"])
        self.assertFalse(result["contract_authority_verified"])
        self.assertNotIn(secret, output.getvalue())
        self.assertNotIn("Traceback", output.getvalue())

    def test_cli_success_is_deterministic_and_path_free(self) -> None:
        outputs: list[str] = []
        for _index in range(2):
            with contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(
                    main([str(self.contract), str(self.root), self.pin]), 0
                )
            outputs.append(output.getvalue())
        self.assertEqual(outputs[0], outputs[1])
        result = json.loads(outputs[0])
        self.assertEqual(
            result["status"],
            "P2_ARTIFACT_BYTES_MATCH_CALLER_PIN_NOT_AUTHORIZED",
        )
        self.assertNotIn(str(self.contract), outputs[0])
        self.assertNotIn(str(self.root), outputs[0])

    def test_cli_failure_truth_reports_only_completed_phases(self) -> None:
        document = copy.deepcopy(self.document)
        document["artifacts"][0]["sha256"] = "0" * 64
        contract, pin = write_contract(self.base, document)
        with contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main([str(contract), str(self.root), pin]), 2)
        result = json.loads(output.getvalue())
        self.assertTrue(result["byte_contract_accepted"])
        self.assertTrue(result["schema_contract_accepted"])
        self.assertFalse(result["artifact_bytes_match_descriptor"])
        self.assertEqual(result["artifacts"], [])

    def test_late_third_artifact_failure_returns_no_partial_receipt(self) -> None:
        document = copy.deepcopy(self.document)
        document["artifacts"][2]["sha256"] = "0" * 64
        contract, pin = write_contract(self.base, document)
        with contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main([str(contract), str(self.root), pin]), 2)
        result = json.loads(output.getvalue())
        self.assertTrue(result["byte_contract_accepted"])
        self.assertTrue(result["schema_contract_accepted"])
        self.assertFalse(result["artifact_bytes_match_descriptor"])
        self.assertEqual(result["artifacts"], [])

    def test_invalid_role_sets_reject_before_artifact_access(self) -> None:
        documents = []
        missing = copy.deepcopy(self.document)
        missing["artifacts"].pop()
        documents.append(missing)
        duplicate = copy.deepcopy(self.document)
        duplicate["artifacts"][2]["role"] = duplicate["artifacts"][1]["role"]
        documents.append(duplicate)
        extra = copy.deepcopy(self.document)
        extra["artifacts"].append(copy.deepcopy(extra["artifacts"][0]))
        extra["artifacts"][-1]["role"] = "unexpected"
        documents.append(extra)
        for document in documents:
            with self.subTest(roles=[item["role"] for item in document["artifacts"]]):
                contract, pin = write_contract(self.base, document)
                with mock.patch.object(
                    consumer_module, "verify_artifacts"
                ) as forbidden:
                    with self.assertRaises(SafeArtifactError):
                        consume(str(contract), str(self.root), pin)
                    forbidden.assert_not_called()

    def test_argument_configuration_exit_three(self) -> None:
        for args, pin_supplied in (
            ([], False),
            ([str(self.contract), str(self.root)], False),
            ([str(self.contract), "relative", self.pin], True),
            (["relative.json", str(self.root), self.pin], True),
            ([str(self.contract), str(self.root), "not-a-sha256"], False),
        ):
            with self.subTest(args=args), contextlib.redirect_stdout(
                io.StringIO()
            ) as output:
                self.assertEqual(main(args), 3)
            result = json.loads(output.getvalue())
            self.assertIs(
                result["expected_contract_sha256_is_caller_supplied_pin"],
                pin_supplied,
            )

    def test_implementation_has_no_write_process_or_network_apis(self) -> None:
        source = (
            (HERE / "safe_artifact_io.py").read_text(encoding="utf-8")
            + (HERE / "consume_p2_to_p3_artifact_bytes.py").read_text(encoding="utf-8")
        )
        for token in (
            "subprocess", "socket", ".write_bytes(", ".write_text(", "os.system(",
            "Popen(", "run(", "urlopen(", "requests",
        ):
            self.assertNotIn(token, source)


if __name__ == "__main__":
    unittest.main(verbosity=2)

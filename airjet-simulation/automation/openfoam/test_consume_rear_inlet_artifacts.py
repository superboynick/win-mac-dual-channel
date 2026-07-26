#!/usr/bin/env python3
"""Adversarial tests for the read-only rear-inlet artifact consumer."""

from __future__ import annotations

import contextlib
import copy
import hashlib
import io
import json
import os
import stat
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import consume_rear_inlet_artifacts as consumer  # noqa: E402
from test_validate_rear_inlet_handoff import valid_manifest  # noqa: E402


ROLE_NAMES = {
    "native": "product_continuous_fluid.scdocx",
    "step": "product_continuous_fluid.step",
    "runtime_report": "v03_continuous_fluid_producer.json",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class ArtifactConsumerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve() / "AcceptedEvidence"
        self.root.mkdir()
        self.contents = {
            "native": b"small-native-evidence\n",
            "step": b"small-step-evidence\n",
            "runtime_report": b'{"runtime":"evidence"}\n',
        }
        self.files: dict[str, Path] = {}
        for role, name in ROLE_NAMES.items():
            path = self.root / name
            path.write_bytes(self.contents[role])
            self.files[role] = path
        self.manifest = self._make_manifest()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _make_manifest(self) -> dict:
        manifest = valid_manifest()
        for artifact in manifest["artifacts"]:
            role = artifact["role"]
            data = self.contents[role]
            digest = sha256(data)
            artifact.update(
                path=self.files[role].as_posix(),
                size_bytes=len(data),
                sha256_declared=digest,
                sha256_observed=digest,
            )
        manifest["mac_review"]["runtime_report_sha256"] = sha256(self.contents["runtime_report"])
        return manifest

    @staticmethod
    def _attestations(manifest: dict) -> dict[str, tuple[str, int, str]]:
        return {
            item["role"]: (item["path"], item["size_bytes"], item["sha256_observed"])
            for item in manifest["artifacts"]
        }

    def consume(self, manifest: dict | None = None) -> consumer.ConsumptionResult:
        candidate = self.manifest if manifest is None else manifest
        with (
            mock.patch.object(consumer, "ALLOWED_ARTIFACT_ROOT", self.root),
            mock.patch.object(
                consumer,
                "EXPECTED_ARTIFACT_ATTESTATIONS",
                self._attestations(candidate),
            ),
        ):
            return consumer.consume_manifest(candidate)

    def assert_code(self, result: consumer.ConsumptionResult, expected: str) -> None:
        self.assertFalse(result.accepted)
        self.assertIn(expected, {item.code for item in result.findings})
        self.assertEqual(result.artifacts, ())

    def test_valid_small_artifacts_are_verified_without_stage_or_solver_claim(self) -> None:
        result = self.consume()
        self.assertTrue(result.accepted, result.findings)
        self.assertEqual({item.role for item in result.artifacts}, set(ROLE_NAMES))
        self.assertTrue(all(consumer.SHA256_RE.fullmatch(item.sha256) for item in result.artifacts))
        output = result.as_json_object()
        self.assertEqual(output["scope"], "READ_ONLY_ARTIFACT_VERIFICATION_ONLY")
        self.assertFalse(output["stage_gate_advanced"])
        self.assertFalse(output["solver_authorized"])

    def test_self_consistent_alternate_artifact_set_is_rejected_by_pin(self) -> None:
        accepted = copy.deepcopy(self.manifest)
        alternate = copy.deepcopy(self.manifest)
        replacement = self.root / "alternate-native.scdocx"
        replacement_bytes = b"self-consistent-but-not-accepted\n"
        replacement.write_bytes(replacement_bytes)
        alternate_native = alternate["artifacts"][0]
        alternate_native.update(
            path=replacement.as_posix(),
            size_bytes=len(replacement_bytes),
            sha256_declared=sha256(replacement_bytes),
            sha256_observed=sha256(replacement_bytes),
        )
        with (
            mock.patch.object(consumer, "ALLOWED_ARTIFACT_ROOT", self.root),
            mock.patch.object(
                consumer,
                "EXPECTED_ARTIFACT_ATTESTATIONS",
                self._attestations(accepted),
            ),
            mock.patch.object(consumer, "_walk_exact_case") as walk,
        ):
            result = consumer.consume_manifest(alternate)
        walk.assert_not_called()
        self.assert_code(result, "B.CONSUME.ATTESTATION.PATH")
        self.assert_code(result, "B.CONSUME.ATTESTATION.SIZE")
        self.assert_code(result, "B.CONSUME.ATTESTATION.HASH")

    def test_incomplete_attestation_configuration_fails_before_file_access(self) -> None:
        incomplete = self._attestations(self.manifest)
        incomplete.pop("native")
        with (
            mock.patch.object(
                consumer,
                "EXPECTED_ARTIFACT_ATTESTATIONS",
                incomplete,
            ),
            mock.patch.object(consumer, "_walk_exact_case") as walk,
        ):
            result = consumer.consume_manifest(self.manifest)
        walk.assert_not_called()
        self.assert_code(result, "B.CONSUME.CONFIG.ATTESTATION_SET")

    def test_existing_manifest_validator_runs_first_and_blocks_file_access(self) -> None:
        sentinel = consumer.ConsumerFinding("MANIFEST.REJECTED", "$.x", "rejected")
        with (
            mock.patch.object(consumer, "validate_manifest", return_value=[sentinel]) as validate,
            mock.patch.object(consumer, "_validate_lexical_path") as lexical,
        ):
            result = consumer.consume_manifest({"artifacts": "must not be read"})
        validate.assert_called_once()
        lexical.assert_not_called()
        self.assert_code(result, "MANIFEST.REJECTED")

    def test_untrusted_manifest_finding_path_is_redacted(self) -> None:
        sentinel = consumer.ConsumerFinding("MANIFEST.REJECTED", "$.C:/private/secret", "rejected")
        with mock.patch.object(consumer, "validate_manifest", return_value=[sentinel]):
            result = consumer.consume_manifest({})
        self.assertEqual(result.findings[0].path, "$")
        self.assertNotIn("private", json.dumps(result.as_json_object()))

    def test_manifest_input_and_artifact_bytes_are_not_mutated(self) -> None:
        before_manifest = copy.deepcopy(self.manifest)
        before_bytes = {role: path.read_bytes() for role, path in self.files.items()}
        result = self.consume()
        self.assertTrue(result.accepted, result.findings)
        self.assertEqual(self.manifest, before_manifest)
        self.assertEqual({role: path.read_bytes() for role, path in self.files.items()}, before_bytes)

    def test_missing_artifact_is_rejected(self) -> None:
        self.files["native"].unlink()
        self.assert_code(self.consume(), "B.CONSUME.FILE.MISSING")

    def test_zero_length_artifact_is_rejected(self) -> None:
        self.files["native"].write_bytes(b"")
        artifact = self.manifest["artifacts"][0]
        artifact["size_bytes"] = 1
        artifact["sha256_declared"] = artifact["sha256_observed"] = sha256(b"")
        self.assert_code(self.consume(), "B.CONSUME.FILE.ZERO_LENGTH")

    def test_size_mismatch_is_rejected(self) -> None:
        self.manifest["artifacts"][0]["size_bytes"] += 1
        self.assert_code(self.consume(), "B.CONSUME.FILE.SIZE_MISMATCH")

    def test_hash_mismatch_is_rejected(self) -> None:
        artifact = self.manifest["artifacts"][0]
        artifact["sha256_declared"] = artifact["sha256_observed"] = "a" * 64
        self.assert_code(self.consume(), "B.CONSUME.HASH.MISMATCH")

    def test_uppercase_manifest_hash_is_rejected_before_file_access(self) -> None:
        artifact = self.manifest["artifacts"][0]
        artifact["sha256_declared"] = artifact["sha256_observed"] = "A" * 64
        with mock.patch.object(consumer, "_walk_exact_case") as walk:
            result = self.consume()
        walk.assert_not_called()
        self.assert_code(result, "GATE.INTEG.HASH_FORMAT")

    def test_directory_is_rejected_as_non_regular(self) -> None:
        directory = self.root / "directory-artifact"
        directory.mkdir()
        artifact = self.manifest["artifacts"][0]
        artifact.update(path=directory.as_posix(), size_bytes=1)
        self.assert_code(self.consume(), "B.CONSUME.FILE.NOT_REGULAR")

    def test_hard_link_alias_is_rejected_when_supported(self) -> None:
        alias = self.root / "native-hardlink.scdocx"
        try:
            os.link(self.files["native"], alias)
        except OSError as exc:
            self.skipTest(f"hard links unavailable: {type(exc).__name__}")
        self.assert_code(self.consume(), "B.CONSUME.PATH.HARDLINK")

    def test_symlink_or_reparse_artifact_is_rejected_when_supported(self) -> None:
        original = self.files["native"]
        target = self.root / "native-target.bin"
        original.replace(target)
        try:
            original.symlink_to(target)
        except OSError as exc:
            target.replace(original)
            self.skipTest(f"symlinks unavailable: {type(exc).__name__}")
        self.assert_code(self.consume(), "B.CONSUME.PATH.REPARSE")

    def test_reparse_attribute_detection_is_explicit(self) -> None:
        fake = types.SimpleNamespace(st_file_attributes=consumer.FILE_ATTRIBUTE_REPARSE_POINT)
        self.assertTrue(consumer._has_reparse_attribute(fake))

    def test_intermediate_reparse_point_is_rejected(self) -> None:
        real_scandir = os.scandir
        redirected = self.root / "redirected"

        def reparse_scandir(path: os.PathLike[str] | str):
            if Path(path) == self.root:
                entry = types.SimpleNamespace(
                    name="redirected",
                    path=str(redirected),
                    stat=lambda *, follow_symlinks: types.SimpleNamespace(
                        st_mode=stat.S_IFDIR,
                        st_file_attributes=consumer.FILE_ATTRIBUTE_REPARSE_POINT,
                    ),
                )
                return contextlib.nullcontext([entry])
            return real_scandir(path)

        with mock.patch.object(consumer.os, "scandir", side_effect=reparse_scandir):
            with self.assertRaises(consumer.ArtifactRejected) as caught:
                consumer._walk_exact_case(redirected / "artifact.bin")
        self.assertEqual(caught.exception.code, "B.CONSUME.PATH.REPARSE")

    def test_traversal_is_rejected_before_filesystem_access(self) -> None:
        artifact = self.manifest["artifacts"][0]
        artifact["path"] = self.root.as_posix() + "/../outside.bin"
        with mock.patch.object(consumer, "_walk_exact_case") as walk:
            result = self.consume()
        walk.assert_not_called()
        self.assert_code(result, "B.CONSUME.PATH.TRAVERSAL")

    def test_current_directory_alias_is_rejected(self) -> None:
        artifact = self.manifest["artifacts"][0]
        artifact["path"] = self.root.as_posix() + "/./" + ROLE_NAMES["native"]
        self.assert_code(self.consume(), "B.CONSUME.PATH.TRAVERSAL")

    def test_outside_root_is_rejected_and_caller_path_is_redacted(self) -> None:
        arbitrary = "C:/private/user-secret/artifact.bin"
        self.manifest["artifacts"][0]["path"] = arbitrary
        result = self.consume()
        self.assert_code(result, "B.CONSUME.PATH.OUTSIDE_ROOT")
        self.assertNotIn(arbitrary, json.dumps(result.as_json_object()))
        self.assertTrue(all(item.path.startswith("$.") for item in result.findings))

    def test_lexical_aliases_and_ads_are_rejected(self) -> None:
        original = self.manifest["artifacts"][0]["path"]
        cases = {
            original.replace("/", "\\"): "B.CONSUME.PATH.ALIAS",
            original.replace("/product_", "//product_"): "B.CONSUME.PATH.ALIAS",
            original + ".": "B.CONSUME.PATH.ALIAS",
            original + ":hidden": "B.CONSUME.PATH.ALIAS",
        }
        for value, code in cases.items():
            with self.subTest(value=value):
                manifest = copy.deepcopy(self.manifest)
                manifest["artifacts"][0]["path"] = value
                self.assert_code(self.consume(manifest), code)

    def test_reserved_name_and_control_character_are_rejected(self) -> None:
        cases = (
            (self.root.as_posix() + "/CON", "B.CONSUME.PATH.RESERVED"),
            (self.root.as_posix() + "/bad\x01name.bin", "B.CONSUME.PATH.FORMAT"),
        )
        for value, code in cases:
            with self.subTest(value=repr(value)):
                manifest = copy.deepcopy(self.manifest)
                manifest["artifacts"][0]["path"] = value
                self.assert_code(self.consume(manifest), code)

    def test_root_case_alias_is_rejected(self) -> None:
        original = self.manifest["artifacts"][0]["path"]
        self.manifest["artifacts"][0]["path"] = original[0].lower() + original[1:]
        self.assert_code(self.consume(), "B.CONSUME.PATH.ABSOLUTE")

    def test_filename_case_alias_is_rejected(self) -> None:
        artifact = self.manifest["artifacts"][0]
        artifact["path"] = artifact["path"].replace("product_continuous", "Product_continuous")
        self.assert_code(self.consume(), "B.CONSUME.PATH.CASE_ALIAS")

    def test_casefold_duplicate_artifact_paths_are_rejected(self) -> None:
        native = self.manifest["artifacts"][0]
        step = self.manifest["artifacts"][1]
        step.update(
            path=native["path"].upper(),
            size_bytes=native["size_bytes"],
            sha256_declared=native["sha256_declared"],
            sha256_observed=native["sha256_observed"],
        )
        self.assertFalse(self.consume().accepted)

    def test_filesystem_case_collision_is_rejected(self) -> None:
        real_scandir = os.scandir
        wanted = ROLE_NAMES["native"]

        def collision_scandir(path: os.PathLike[str] | str):
            if Path(path) == self.root:
                entries = [
                    types.SimpleNamespace(name=wanted, path=str(self.root / wanted)),
                    types.SimpleNamespace(name=wanted.upper(), path=str(self.root / wanted.upper())),
                ]
                return contextlib.nullcontext(entries)
            return real_scandir(path)

        with mock.patch.object(consumer.os, "scandir", side_effect=collision_scandir):
            self.assert_code(self.consume(), "B.CONSUME.PATH.CASE_COLLISION")

    def test_duplicate_exact_path_is_rejected(self) -> None:
        native = self.manifest["artifacts"][0]
        step = self.manifest["artifacts"][1]
        step.update(
            path=native["path"],
            size_bytes=native["size_bytes"],
            sha256_declared=native["sha256_declared"],
            sha256_observed=native["sha256_observed"],
        )
        self.assert_code(self.consume(), "B.CONSUME.PATH.DUPLICATE")

    def test_duplicate_role_is_rejected_by_first_stage(self) -> None:
        self.manifest["artifacts"][1]["role"] = "native"
        self.assert_code(self.consume(), "GATE.INTEG.ARTIFACT_ROLE_DUPLICATE")

    def test_post_hash_identity_drift_is_rejected(self) -> None:
        path = self.files["native"]
        pre = os.lstat(path)
        drift = types.SimpleNamespace(
            st_dev=pre.st_dev,
            st_ino=pre.st_ino + 1,
            st_size=pre.st_size,
            st_mode=pre.st_mode,
            st_nlink=pre.st_nlink,
            st_mtime_ns=pre.st_mtime_ns,
        )
        with mock.patch.object(consumer, "_walk_exact_case", side_effect=[pre, drift]):
            with self.assertRaises(consumer.ArtifactRejected) as caught:
                consumer._verify_one(path, pre.st_size, sha256(path.read_bytes()))
        self.assertEqual(caught.exception.code, "B.CONSUME.IDENTITY.DRIFT")

    def test_post_hash_size_drift_is_rejected(self) -> None:
        path = self.files["native"]
        pre = os.lstat(path)
        drift = types.SimpleNamespace(
            st_dev=pre.st_dev,
            st_ino=pre.st_ino,
            st_size=pre.st_size + 1,
            st_mode=pre.st_mode,
            st_nlink=pre.st_nlink,
            st_mtime_ns=pre.st_mtime_ns,
        )
        with mock.patch.object(consumer, "_walk_exact_case", side_effect=[pre, drift]):
            with self.assertRaises(consumer.ArtifactRejected) as caught:
                consumer._verify_one(path, pre.st_size, sha256(path.read_bytes()))
        self.assertEqual(caught.exception.code, "B.CONSUME.FILE.SIZE_DRIFT")

    def test_open_handle_final_path_redirect_is_rejected(self) -> None:
        path = self.files["native"]
        with mock.patch.object(consumer, "_opened_final_path", return_value=self.root.parent / "outside.bin"):
            with self.assertRaises(consumer.ArtifactRejected) as caught:
                consumer._verify_one(path, path.stat().st_size, sha256(path.read_bytes()))
        self.assertEqual(caught.exception.code, "B.CONSUME.PATH.HANDLE_REDIRECT")

    def test_unavailable_file_identity_fails_closed(self) -> None:
        path = self.files["native"]
        with mock.patch.object(consumer, "_stable_identity", return_value=None):
            with self.assertRaises(consumer.ArtifactRejected) as caught:
                consumer._verify_one(path, path.stat().st_size, sha256(path.read_bytes()))
        self.assertEqual(caught.exception.code, "B.CONSUME.IDENTITY.UNAVAILABLE")

    def test_cli_requires_absolute_source_manifest_path(self) -> None:
        with contextlib.redirect_stdout(io.StringIO()) as output:
            status = consumer.main(["relative.json"])
        self.assertEqual(status, 3)
        result = json.loads(output.getvalue())
        self.assertEqual(result["findings"][0]["code"], "B.CONSUME.INPUT.ABSOLUTE")
        self.assertNotIn("relative.json", output.getvalue())

    def test_cli_rejects_duplicate_keys_without_echoing_them(self) -> None:
        source = self.root / "duplicate.json"
        source.write_text('{"secret-key":1,"secret-key":2}', encoding="utf-8")
        with (
            mock.patch.object(consumer, "EXPECTED_HANDOFF_PATH", source),
            contextlib.redirect_stdout(io.StringIO()) as output,
        ):
            status = consumer.main([str(source)])
        self.assertEqual(status, 3)
        self.assertIn("B.CONSUME.INPUT.JSON_DUPLICATE_KEY", output.getvalue())
        self.assertNotIn("secret-key", output.getvalue())

    def test_cli_rejects_every_nonfinite_json_constant(self) -> None:
        for value in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(value=value):
                source = self.root / "nonfinite.json"
                source.write_text('{"value":' + value + "}", encoding="utf-8")
                with (
                    mock.patch.object(consumer, "EXPECTED_HANDOFF_PATH", source),
                    contextlib.redirect_stdout(io.StringIO()) as output,
                ):
                    status = consumer.main([str(source)])
                self.assertEqual(status, 3)
                self.assertIn("B.CONSUME.INPUT.JSON_NONFINITE", output.getvalue())

    def test_source_manifest_read_is_bounded_on_the_open_handle(self) -> None:
        source = self.root / "oversized.json"
        source.write_bytes(b" " * (consumer.MAX_MANIFEST_BYTES + 1))
        with (
            mock.patch.object(consumer, "EXPECTED_HANDOFF_PATH", source),
            contextlib.redirect_stdout(io.StringIO()) as output,
        ):
            status = consumer.main([str(source)])
        self.assertEqual(status, 3)
        self.assertIn("B.CONSUME.INPUT.JSON", output.getvalue())

    def test_source_manifest_loader_does_not_use_preopen_path_stat(self) -> None:
        source = self.root / "small.json"
        source.write_text("{}", encoding="utf-8")
        with mock.patch.object(Path, "stat", side_effect=AssertionError("pre-open stat used")):
            manifest, digest = consumer._load_source_manifest(source)
        self.assertEqual(manifest, {})
        self.assertEqual(digest, sha256(b"{}"))

    def test_cli_rejects_unexpected_manifest_digest_before_artifact_access(self) -> None:
        source = self.root / "accepted-manifest.json"
        source.write_text(json.dumps(self.manifest), encoding="utf-8")
        with (
            mock.patch.object(consumer, "EXPECTED_HANDOFF_PATH", source),
            mock.patch.object(consumer, "EXPECTED_HANDOFF_SHA256", "0" * 64),
            mock.patch.object(consumer, "_walk_exact_case") as walk,
            contextlib.redirect_stdout(io.StringIO()) as output,
        ):
            status = consumer.main([str(source)])
        walk.assert_not_called()
        self.assertEqual(status, 3)
        self.assertIn("B.CONSUME.INPUT.IDENTITY", output.getvalue())

    def test_cli_rejects_excessive_json_depth(self) -> None:
        source = self.root / "accepted-manifest.json"
        source.write_text(
            "[" * (consumer.MAX_JSON_DEPTH + 1)
            + "0"
            + "]" * (consumer.MAX_JSON_DEPTH + 1),
            encoding="utf-8",
        )
        with (
            mock.patch.object(consumer, "EXPECTED_HANDOFF_PATH", source),
            contextlib.redirect_stdout(io.StringIO()) as output,
        ):
            status = consumer.main([str(source)])
        self.assertEqual(status, 3)
        self.assertIn("B.CONSUME.INPUT.JSON", output.getvalue())

    def test_cli_accepts_valid_temp_manifest_and_returns_no_artifact_paths(self) -> None:
        source = self.root / "accepted-manifest.json"
        source.write_text(json.dumps(self.manifest), encoding="utf-8")
        with (
            mock.patch.object(consumer, "ALLOWED_ARTIFACT_ROOT", self.root),
            mock.patch.object(consumer, "EXPECTED_HANDOFF_PATH", source),
            mock.patch.object(
                consumer,
                "EXPECTED_HANDOFF_SHA256",
                sha256(source.read_bytes()),
            ),
            mock.patch.object(
                consumer,
                "EXPECTED_ARTIFACT_ATTESTATIONS",
                self._attestations(self.manifest),
            ),
            contextlib.redirect_stdout(io.StringIO()) as output,
        ):
            status = consumer.main([str(source)])
        self.assertEqual(status, 0, output.getvalue())
        parsed = json.loads(output.getvalue())
        self.assertTrue(parsed["accepted"])
        self.assertFalse(parsed["stage_gate_advanced"])
        self.assertFalse(parsed["solver_authorized"])
        self.assertNotIn(self.root.as_posix(), output.getvalue())


if __name__ == "__main__":
    unittest.main(verbosity=2)

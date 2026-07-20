#!/usr/bin/env python3
"""Negative tests for the Task 006 OpenFOAM consumer rejection gate."""

from __future__ import annotations

import copy
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from validate_rear_inlet_handoff import (  # noqa: E402
    EXPECTED_PRODUCER_SHA256,
    FORBIDDEN_PRODUCER_MARKERS,
    GEOMETRY_CONTRACT_TASK_ID,
    POLICY_CONTRACT_TASK_ID,
    TASK_ID,
    main,
    validate_manifest,
)


HASH_A = "a" * 64
HASH_B = "b" * 64


def valid_manifest() -> dict:
    return {
        "schema_version": "1.0",
        "task_id": TASK_ID,
        "policy_contract_task_id": POLICY_CONTRACT_TASK_ID,
        "geometry_contract_task_id": GEOMETRY_CONTRACT_TASK_ID,
        "producer": {
            "acceptance_state": "PASS",
            "source_commit": "1" * 40,
            "script": {
                "path": "automation/ansys/producer.py",
                "sha256_declared": EXPECTED_PRODUCER_SHA256,
                "sha256_observed": EXPECTED_PRODUCER_SHA256,
            },
            "profile": {
                "path": "profiles/reviewed.json",
                "sha256_declared": HASH_B,
                "sha256_observed": HASH_B,
            },
            "source_policy": {
                "forbidden_markers_checked": sorted(FORBIDDEN_PRODUCER_MARKERS),
                "forbidden_markers_detected": [],
            },
        },
        "geometry": {
            "inlets": [{"id": "V01"}, {"id": "V02"}, {"id": "V03"}, {"id": "V04"}],
            "outlets": [{"id": "O01"}],
            "cell_footprint_y_min_mm": -14.5,
            "supported_plenum_y_min_mm": -17.75,
            "rear_support_extension_mm": 3.25,
            "rear_inlet_ids": ["V01", "V02"],
            "body_count": 1,
            "piece_count": 1,
            "closed": True,
            "manifold": True,
            "bbox_min_mm": [-10.875, -17.75, 1.2675],
            "bbox_max_mm": [10.875, 20.75, 2.8],
            "analytic_volume_mm3": 469.4396438426395,
            "native_reopen_pass": True,
            "step_reopen_pass": True,
            "connectivity_pass": True,
        },
        "artifacts": [
            {
                "role": role,
                "path": f"evidence/{role}.dat",
                "size_bytes": 100,
                "sha256_declared": HASH_A,
                "sha256_observed": HASH_A,
            }
            for role in ("native", "step", "runtime_report")
        ],
        "mac_review": {
            "acceptance_state": "ACCEPTED_PASS",
            "review_commit": "2" * 40,
            "producer_source_commit": "1" * 40,
            "runtime_report_sha256": HASH_A,
        },
    }


def codes(manifest: dict) -> set[str]:
    return {finding.code for finding in validate_manifest(manifest)}


class RearInletHandoffGateTests(unittest.TestCase):
    def assert_rejected(self, manifest: dict, expected_code: str) -> None:
        actual = codes(manifest)
        self.assertIn(expected_code, actual, f"findings were: {sorted(actual)}")

    def test_valid_manifest_is_accepted(self) -> None:
        self.assertEqual(validate_manifest(valid_manifest()), [])

    def test_schema_is_valid_json_and_freezes_task(self) -> None:
        schema = json.loads((HERE / "rear_inlet_handoff_schema_v1.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(schema["properties"]["task_id"]["const"], TASK_ID)
        self.assertEqual(
            schema["properties"]["policy_contract_task_id"]["const"],
            POLICY_CONTRACT_TASK_ID,
        )
        self.assertEqual(
            schema["properties"]["geometry_contract_task_id"]["const"],
            GEOMETRY_CONTRACT_TASK_ID,
        )
        self.assertFalse(schema["additionalProperties"])

    def test_missing_inlet_identity_is_rejected(self) -> None:
        manifest = valid_manifest()
        del manifest["geometry"]["inlets"][0]["id"]
        self.assert_rejected(manifest, "GATE.STRUCT.ID_MISSING")

    def test_duplicate_inlet_identity_is_rejected(self) -> None:
        manifest = valid_manifest()
        manifest["geometry"]["inlets"][3]["id"] = "V01"
        self.assert_rejected(manifest, "GATE.STRUCT.ID_DUPLICATE")

    def test_inlet_count_other_than_four_is_rejected(self) -> None:
        for count in (3, 5):
            with self.subTest(count=count):
                manifest = valid_manifest()
                if count == 3:
                    manifest["geometry"]["inlets"].pop()
                else:
                    manifest["geometry"]["inlets"].append({"id": "V05"})
                self.assert_rejected(manifest, "GATE.STRUCT.INLET_COUNT")

    def test_outlet_count_other_than_one_is_rejected(self) -> None:
        for count in (0, 2):
            with self.subTest(count=count):
                manifest = valid_manifest()
                manifest["geometry"]["outlets"] = [] if count == 0 else [{"id": "O01"}, {"id": "O02"}]
                self.assert_rejected(manifest, "GATE.STRUCT.OUTLET_COUNT")

    def test_frozen_rear_geometry_scalars_are_required_and_exact(self) -> None:
        cases = (
            ("cell_footprint_y_min_mm", -14.4, "GATE.GEOM.FOOTPRINT_Y"),
            ("supported_plenum_y_min_mm", -17.5, "GATE.GEOM.PLENUM_Y"),
            ("rear_support_extension_mm", 3.0, "GATE.GEOM.EXTENSION"),
        )
        for key, wrong_value, expected_code in cases:
            with self.subTest(key=key, mode="wrong"):
                manifest = valid_manifest()
                manifest["geometry"][key] = wrong_value
                self.assert_rejected(manifest, expected_code)
            with self.subTest(key=key, mode="missing"):
                manifest = valid_manifest()
                del manifest["geometry"][key]
                self.assert_rejected(manifest, expected_code)

    def test_rear_ids_must_be_exact_set_and_reference_inlets(self) -> None:
        for value in (["V01"], ["V01", "V03"], ["V01", "V01"], [{"id": "V01"}, "V02"]):
            with self.subTest(value=value):
                manifest = valid_manifest()
                manifest["geometry"]["rear_inlet_ids"] = value
                self.assert_rejected(manifest, "GATE.STRUCT.REAR_ID")
        reordered = valid_manifest()
        reordered["geometry"]["rear_inlet_ids"] = ["V02", "V01"]
        self.assertEqual(validate_manifest(reordered), [])

    def test_acceptance_must_be_literal_pass(self) -> None:
        for value in ("FAIL", "pass", "PASS ", True, None):
            with self.subTest(value=value):
                manifest = valid_manifest()
                manifest["producer"]["acceptance_state"] = value
                self.assert_rejected(manifest, "GATE.SEM.ACCEPTANCE")

    def test_mac_acceptance_is_required_and_bound_to_runtime_evidence(self) -> None:
        manifest = valid_manifest()
        del manifest["mac_review"]
        self.assert_rejected(manifest, "GATE.SEM.MAC_ACCEPTANCE")

        manifest = valid_manifest()
        manifest["mac_review"]["acceptance_state"] = "PENDING"
        self.assert_rejected(manifest, "GATE.SEM.MAC_ACCEPTANCE")

        manifest = valid_manifest()
        manifest["mac_review"]["producer_source_commit"] = "3" * 40
        self.assert_rejected(manifest, "GATE.INTEG.MAC_PRODUCER_COMMIT")

        manifest = valid_manifest()
        manifest["mac_review"]["runtime_report_sha256"] = HASH_B
        self.assert_rejected(manifest, "GATE.INTEG.MAC_RUNTIME_REPORT_HASH")

    def test_producer_and_profile_hash_mismatch_are_rejected(self) -> None:
        for component, expected_code in (
            ("script", "GATE.INTEG.HASH_PRODUCER"),
            ("profile", "GATE.INTEG.HASH_PROFILE"),
        ):
            with self.subTest(component=component):
                manifest = valid_manifest()
                manifest["producer"][component]["sha256_observed"] = HASH_A
                self.assert_rejected(manifest, expected_code)

    def test_producer_hash_must_match_reviewed_pin_even_when_self_consistent(self) -> None:
        manifest = valid_manifest()
        manifest["producer"]["script"]["sha256_declared"] = HASH_A
        manifest["producer"]["script"]["sha256_observed"] = HASH_A
        self.assert_rejected(manifest, "GATE.INTEG.PRODUCER_PIN")

    def test_forbidden_clip_marker_or_incomplete_scan_is_rejected(self) -> None:
        manifest = valid_manifest()
        manifest["producer"]["source_policy"]["forbidden_markers_detected"] = [
            "vent_rear_containment_clip"
        ]
        self.assert_rejected(manifest, "GATE.SEM.CLIP_MARKER")

        manifest = valid_manifest()
        manifest["producer"]["source_policy"]["forbidden_markers_checked"] = [
            "vent_rear_containment_clip"
        ]
        self.assert_rejected(manifest, "GATE.SEM.CLIP_MARKER_POLICY")

        manifest = valid_manifest()
        del manifest["producer"]["source_policy"]
        self.assert_rejected(manifest, "GATE.SEM.CLIP_MARKER_POLICY")

    def test_each_artifact_hash_mismatch_is_rejected(self) -> None:
        expected = {
            "native": "GATE.INTEG.HASH_NATIVE",
            "step": "GATE.INTEG.HASH_STEP",
            "runtime_report": "GATE.INTEG.HASH_RUNTIME_REPORT",
        }
        for index, role in enumerate(("native", "step", "runtime_report")):
            with self.subTest(role=role):
                manifest = valid_manifest()
                manifest["artifacts"][index]["sha256_observed"] = HASH_B
                self.assert_rejected(manifest, expected[role])

    def test_artifact_roles_are_complete_and_unique(self) -> None:
        manifest = valid_manifest()
        manifest["artifacts"][2]["role"] = "native"
        actual = codes(manifest)
        self.assertIn("GATE.INTEG.ARTIFACT_ROLE_DUPLICATE", actual)
        self.assertIn("GATE.INTEG.ARTIFACT_ROLE_SET", actual)

    def test_non_string_artifact_role_is_rejected_without_crashing(self) -> None:
        manifest = valid_manifest()
        manifest["artifacts"][0]["role"] = ["native"]
        self.assert_rejected(manifest, "GATE.INTEG.ARTIFACT_ROLE")

    def test_geometry_acceptance_evidence_is_fail_closed(self) -> None:
        cases = (
            ("body_count", 2, "GATE.STRUCT.BODY_COUNT"),
            ("piece_count", 2, "GATE.STRUCT.PIECE_COUNT"),
            ("closed", False, "GATE.GEOM.CLOSED"),
            ("manifold", False, "GATE.GEOM.MANIFOLD"),
            ("bbox_min_mm", [-10.875, -17.5, 1.2675], "GATE.GEOM.BBOX"),
            ("bbox_max_mm", [10.875, 20.75, 3.0], "GATE.GEOM.BBOX"),
            ("analytic_volume_mm3", 469.44, "GATE.GEOM.VOLUME"),
            ("native_reopen_pass", False, "GATE.INTEG.REOPEN_NATIVE"),
            ("step_reopen_pass", False, "GATE.INTEG.REOPEN_STEP"),
            ("connectivity_pass", False, "GATE.GEOM.CONNECTIVITY"),
        )
        for key, value, expected_code in cases:
            with self.subTest(key=key):
                manifest = valid_manifest()
                manifest["geometry"][key] = value
                self.assert_rejected(manifest, expected_code)

    def test_unknown_fields_are_rejected(self) -> None:
        manifest = valid_manifest()
        manifest["geometry"]["invented_pass"] = True
        self.assert_rejected(manifest, "GATE.SCHEMA.UNKNOWN_FIELD")

    def test_hashes_and_commit_require_lowercase_full_length_hex(self) -> None:
        manifest = valid_manifest()
        manifest["producer"]["source_commit"] = "A" * 40
        manifest["producer"]["script"]["sha256_declared"] = "A" * 64
        actual = codes(manifest)
        self.assertIn("GATE.INTEG.COMMIT_FORMAT", actual)
        self.assertIn("GATE.INTEG.HASH_FORMAT", actual)

    def test_inlet_outlet_identity_overlap_is_rejected(self) -> None:
        manifest = valid_manifest()
        manifest["geometry"]["outlets"][0]["id"] = "V01"
        self.assert_rejected(manifest, "GATE.STRUCT.ID_DUPLICATE")

    def test_whitespace_and_path_like_identities_are_rejected(self) -> None:
        for value in ("", "   ", "../V01", "V01/other", "V01\x00hidden"):
            with self.subTest(value=value):
                manifest = valid_manifest()
                manifest["geometry"]["inlets"][0]["id"] = value
                self.assert_rejected(manifest, "GATE.STRUCT.ID_FORMAT")

    def test_artifact_size_must_be_positive_integer(self) -> None:
        for value in (0, -1, 1.5, True):
            with self.subTest(value=value):
                manifest = valid_manifest()
                manifest["artifacts"][0]["size_bytes"] = value
                self.assert_rejected(manifest, "GATE.INTEG.ARTIFACT_SIZE")

    def test_numeric_strings_are_not_coerced(self) -> None:
        manifest = valid_manifest()
        manifest["geometry"]["rear_support_extension_mm"] = "3.25"
        self.assert_rejected(manifest, "GATE.GEOM.EXTENSION")

    def test_input_is_not_mutated(self) -> None:
        manifest = valid_manifest()
        before = copy.deepcopy(manifest)
        validate_manifest(manifest)
        self.assertEqual(manifest, before)

    def test_cli_accepts_valid_json_and_rejects_invalid_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "handoff.json"
            path.write_text(json.dumps(valid_manifest()), encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(main([str(path)]), 0)
            self.assertTrue(json.loads(output.getvalue())["accepted"])

            manifest = valid_manifest()
            manifest["producer"]["acceptance_state"] = "FAIL"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(main([str(path)]), 2)
            result = json.loads(output.getvalue())
            self.assertFalse(result["accepted"])
            self.assertIn("GATE.SEM.ACCEPTANCE", {item["code"] for item in result["findings"]})

    def test_cli_rejects_duplicate_json_keys(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicate.json"
            path.write_text('{"schema_version":"1.0","schema_version":"evil"}', encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(main([str(path)]), 3)
            result = json.loads(output.getvalue())
            self.assertFalse(result["accepted"])
            self.assertEqual(result["findings"][0]["code"], "GATE.INPUT.JSON_DUPLICATE_KEY")

    def test_malformed_root_types_are_rejected_without_crashing(self) -> None:
        for value in (None, [], "manifest", 1, True):
            with self.subTest(value=value):
                self.assertIn("GATE.SCHEMA.TYPE", {item.code for item in validate_manifest(value)})


if __name__ == "__main__":
    unittest.main(verbosity=2)

from __future__ import annotations

import copy
import contextlib
import hashlib
import io
import json
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from airjet_coupling import validator  # noqa: E402
from airjet_coupling.validator import (  # noqa: E402
    ContractValidationError,
    _schema_errors,
    load_json_bytes,
    validate_document,
    validate_file,
)
from airjet_coupling.cli import main as cli_main  # noqa: E402


def fixture(relative: str):
    return load_json_bytes((ROOT / "fixtures" / relative).read_bytes())


def p2():
    return fixture("valid/p2_to_p3.json")


def p4():
    return fixture("valid/p4_to_p5_temperature.json")


def set_path(path, value):
    def mutate(document):
        node = document
        for key in path[:-1]:
            node = node[key]
        node[path[-1]] = value
    return mutate


def delete_path(path):
    def mutate(document):
        node = document
        for key in path[:-1]:
            node = node[key]
        del node[path[-1]]
    return mutate


class TestAcceptedContracts(unittest.TestCase):
    def test_p2_fixture(self):
        validate_file(ROOT / "fixtures" / "valid" / "p2_to_p3.json")

    def test_p4_temperature_fixture(self):
        validate_file(ROOT / "fixtures" / "valid" / "p4_to_p5_temperature.json")

    def test_p4_heat_flux_variant(self):
        document = p4()
        document["wall_field"]["representation"] = "H_AND_WALL_HEAT_FLUX"
        artifact = document["wall_field"]["artifacts"][1]
        artifact["role"] = "wall_heat_flux"
        artifact["path"] = "wall/heat_flux_field.h5"
        artifact["value_unit"] = "W/m^2"
        validate_document(document)

    def test_other_declared_energy_point(self):
        document = p4()
        energy = document["energy_sources"]
        energy["operating_point"] = "OTHER_DECLARED_POINT"
        energy["q_chip"]["value"] = 2
        energy["q_airjet_self"]["value"] = 0.5
        energy["q_total"]["value"] = 2.5
        validate_document(document)

    def test_p4_instantaneous_temporal_form(self):
        document = p4()
        document["temporal_sampling"] = {
            "time_basis": "instantaneous", "time_unit": "s", "start": 0,
            "step": 0.000001, "sample_count": 5, "periodic": False,
        }
        validate_document(document)

    def test_p4_cycle_mean_temporal_form(self):
        document = p4()
        document["temporal_sampling"] = {
            "time_basis": "cycle_mean", "time_unit": "s", "start": 0,
            "averaging_window_s": 0.001, "sample_count": 1, "periodic": False,
        }
        validate_document(document)

    def test_schema_files_are_draft_2020_12_json(self):
        for path in (ROOT / "schemas").glob("*.schema.json"):
            schema = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
            self.assertIn("$defs", schema)
            self.assertFalse(schema["additionalProperties"])

    def test_fixture_schema_hashes_bind_exact_bytes(self):
        mapping = {
            "valid/p2_to_p3.json": "p2_to_p3_structural_displacement_handoff.schema.json",
            "valid/p4_to_p5_temperature.json": "p4_to_p5_wall_cht_handoff.schema.json",
        }
        for fixture_name, schema_name in mapping.items():
            document = fixture(fixture_name)
            digest = hashlib.sha256((ROOT / "schemas" / schema_name).read_bytes()).hexdigest()
            self.assertEqual(document["identity"]["schema_sha256"], digest)

    def test_cli_acceptance_never_claims_artifact_contents_verified(self):
        output = io.StringIO()
        path = ROOT / "fixtures" / "valid" / "p2_to_p3.json"
        with contextlib.redirect_stdout(output):
            result = cli_main(["validate", str(path)])
        payload = json.loads(output.getvalue())
        self.assertEqual(result, 0)
        self.assertTrue(payload["metadata_contract_accepted"])
        self.assertFalse(payload["artifact_contents_verified"])
        self.assertFalse(payload["solver_authorized"])
        self.assertFalse(payload["stage_gate_advanced"])
        self.assertEqual(payload["scope"], "REFERENCE_METADATA_CONTRACT_ONLY")
        self.assertNotIn("document", payload)
        self.assertIn("revalidate size and SHA-256", payload["consumer_action_required"])

    def test_nonfinite_decimal_direct_input_is_controlled_rejection(self):
        for value in (Decimal("NaN"), Decimal("Infinity"), Decimal("-Infinity")):
            with self.subTest(value=str(value)):
                document = p2()
                document["mapping"]["tolerance"] = value
                with self.assertRaises(ContractValidationError):
                    validate_document(document)

    def test_deep_json_is_rejected_before_recursive_validation(self):
        value = "0"
        for _ in range(validator.MAX_JSON_DEPTH + 1):
            value = "[" + value + "]"
        with self.assertRaises(ContractValidationError):
            load_json_bytes(value.encode("utf-8"))

    def test_oversized_document_is_rejected_before_parse(self):
        with self.assertRaises(ContractValidationError):
            load_json_bytes(b" " * (validator.MAX_DOCUMENT_BYTES + 1))

    def test_excessive_json_node_count_is_rejected(self):
        raw = ("[" + ",".join("0" for _ in range(validator.MAX_JSON_NODES)) + "]").encode("utf-8")
        self.assertLess(len(raw), validator.MAX_DOCUMENT_BYTES)
        with self.assertRaises(ContractValidationError):
            load_json_bytes(raw)

    def test_validate_file_uses_bounded_open_handle_read(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "oversized.json"
            path.write_bytes(b" " * (validator.MAX_DOCUMENT_BYTES + 1))
            with self.assertRaises(ContractValidationError):
                validator.validate_file(path)

    def test_cli_read_error_does_not_disclose_source_path(self):
        secret_path = "C:/private/secret-contract.json"
        with contextlib.redirect_stderr(io.StringIO()) as output:
            result = cli_main(["validate", secret_path])
        self.assertEqual(result, 2)
        self.assertNotIn(secret_path, output.getvalue())


P2_REJECTIONS = {
    "missing_task": delete_path(("identity", "task_id")),
    "missing_session": delete_path(("identity", "session_id")),
    "missing_snapshot": delete_path(("identity", "snapshot_id")),
    "missing_receipt": delete_path(("identity", "receipt_id")),
    "wrong_schema_hash": set_path(("identity", "schema_sha256"), "0" * 64),
    "absolute_artifact_path": set_path(("artifacts", 0, "path"), "C:/escape/nodes.arrow"),
    "parent_artifact_path": set_path(("artifacts", 0, "path"), "../nodes.arrow"),
    "zero_artifact_size": set_path(("artifacts", 0, "size_bytes"), 0),
    "bad_artifact_hash": set_path(("artifacts", 0, "sha256"), "xyz"),
    "scalar_role": set_path(("artifacts", 2, "role"), "displacement_scalar_field"),
    "missing_components": delete_path(("artifacts", 2, "components")),
    "wrong_component_order": set_path(("artifacts", 2, "components"), ["uz", "uy", "ux"]),
    "wrong_displacement_unit": set_path(("artifacts", 2, "value_unit"), "um"),
    "missing_phase": delete_path(("temporal_sampling", "phase_reference_deg")),
    "phase_360": set_path(("temporal_sampling", "phase_reference_deg"), 360),
    "frequency_zero": set_path(("temporal_sampling", "frequency"), 0),
    "one_sample_per_cycle": set_path(("temporal_sampling", "samples_per_cycle"), 1),
    "missing_coordinate_unit": delete_path(("coordinate_system", "length_unit")),
    "missing_handedness": delete_path(("coordinate_system", "handedness")),
    "contradict_handedness": set_path(("coordinate_system", "handedness"), "left"),
    "non_unit_axis": set_path(("coordinate_system", "axes", 0), [2, 0, 0]),
    "non_orthogonal_axes": set_path(("coordinate_system", "axes", 1), [1, 0, 0]),
    "zero_mapping_tolerance": set_path(("mapping", "tolerance"), 0),
    "mapping_unit_mismatch": set_path(("mapping", "tolerance_unit"), "um"),
    "unmapped_over_one": set_path(("mapping", "maximum_unmapped_fraction"), 1.1),
    "unmapped_equal_one": set_path(("mapping", "maximum_unmapped_fraction"), 1),
    "unmapped_above_conservative_cap": set_path(("mapping", "maximum_unmapped_fraction"), 0.0001001),
    "wrong_coverage_scope": set_path(("mapping", "coverage_scope"), "ACTIVE_NODES_ONLY"),
    "wrong_unmapped_policy": set_path(("mapping", "unmapped_policy"), "ALLOW_ACTIVE_NODE_GAPS"),
    "missing_gap": delete_path(("mechanical_metrics", "minimum_gap")),
    "missing_stress": delete_path(("mechanical_metrics", "maximum_stress")),
    "missing_power": delete_path(("mechanical_metrics", "electrical_power")),
    "wrong_gap_unit": set_path(("mechanical_metrics", "minimum_gap", "unit"), "um"),
    "wrong_stress_unit": set_path(("mechanical_metrics", "maximum_stress", "unit"), "MPa"),
    "wrong_power_unit": set_path(("mechanical_metrics", "electrical_power", "unit"), "mW"),
    "zero_minimum_gap": set_path(("mechanical_metrics", "minimum_gap", "value"), 0),
    "negative_minimum_gap": set_path(("mechanical_metrics", "minimum_gap", "value"), -0.001),
    "negative_maximum_stress": set_path(("mechanical_metrics", "maximum_stress", "value"), -1),
    "negative_electrical_power": set_path(("mechanical_metrics", "electrical_power", "value"), -0.001),
    "ads_artifact_path": set_path(("artifacts", 0, "path"), "fields/nodes.arrow:evil"),
    "reserved_con_path": set_path(("artifacts", 0, "path"), "fields/CON"),
    "reserved_prn_extension_path": set_path(("artifacts", 0, "path"), "fields/prn.arrow"),
    "reserved_com_path": set_path(("artifacts", 0, "path"), "fields/COM1.bin"),
    "reserved_lpt_path": set_path(("artifacts", 0, "path"), "Lpt9"),
    "trailing_dot_path": set_path(("artifacts", 0, "path"), "fields/nodes."),
    "trailing_space_path": set_path(("artifacts", 0, "path"), "fields/nodes "),
    "unknown_source": set_path(("provenance", "claims", 0, "source_ref"), "UNKNOWN"),
    "null_source": set_path(("provenance", "claims", 0, "source_ref"), None),
    "active_unresolved": set_path(("provenance", "claims", 0, "classification"), "U"),
    "class_kind_masquerade": set_path(("provenance", "claims", 0, "classification"), "I"),
    "inference_empty_derivation": lambda d: (
        d["provenance"]["claims"][0].update({"classification": "I", "assertion_kind": "inference", "derivation": ""})
    ),
    "inference_zero_uncertainty": lambda d: (
        d["provenance"]["claims"][0].update({"classification": "I", "assertion_kind": "inference", "derivation": "equation"}),
        d["provenance"]["claims"][0]["uncertainty"].update({"lower": 0, "upper": 0}),
    ),
    "extra_top_property": set_path(("unexpected",), 1),
}


def duplicate_p2_role(document):
    document["artifacts"][1]["role"] = "nodes"


def duplicate_p2_path(document):
    document["artifacts"][1]["path"] = "FIELDS/NODES.ARROW"


def duplicate_claim_id(document):
    document["provenance"]["claims"][1]["id"] = document["provenance"]["claims"][0]["id"]


def separator_normalized_duplicate_path(document):
    document["artifacts"][1]["path"] = "fields\\nodes.arrow"


def unicode_normalized_duplicate_path(document):
    document["artifacts"][0]["path"] = "fields/caf\u00e9.arrow"
    document["artifacts"][1]["path"] = "fields/cafe\u0301.arrow"


P2_REJECTIONS.update({
    "duplicate_artifact_role": duplicate_p2_role,
    "duplicate_artifact_path": duplicate_p2_path,
    "duplicate_claim_id": duplicate_claim_id,
    "separator_normalized_duplicate_path": separator_normalized_duplicate_path,
    "unicode_normalized_duplicate_path": unicode_normalized_duplicate_path,
})


P4_REJECTIONS = {
    "missing_h_field": lambda d: d["wall_field"]["artifacts"].pop(0),
    "representation_mismatch": set_path(("wall_field", "representation"), "H_AND_WALL_HEAT_FLUX"),
    "wrong_h_unit": set_path(("wall_field", "artifacts", 0, "value_unit"), "W/m^2"),
    "wrong_temperature_unit": set_path(("wall_field", "artifacts", 1, "value_unit"), "degC"),
    "bad_map_role": set_path(("region_interface_map", "artifact", "role"), "wall_temperature"),
    "bad_map_unit": set_path(("region_interface_map", "artifact", "value_unit"), "kg"),
    "missing_material": lambda d: d["solid_material_refs"].clear(),
    "unresolved_material": set_path(("provenance", "claims", 0, "classification"), "U"),
    "energy_sum_mismatch": set_path(("energy_sources", "q_total", "value"), 5.2),
    "reference_wrong_chip": set_path(("energy_sources", "q_chip", "value"), 4.0),
    "wrong_accounting_basis": set_path(("energy_sources", "accounting_basis"), "TOTAL_PLUS_SELF"),
    "wrong_power_unit": set_path(("energy_sources", "q_chip", "unit"), "mW"),
    "zero_time_step": set_path(("temporal_sampling", "step"), 0),
    "phase_nonperiodic": set_path(("temporal_sampling", "periodic"), False),
    "phase_one_sample": set_path(("temporal_sampling", "sample_count"), 1),
    "phase_missing_cycle_period": delete_path(("temporal_sampling", "cycle_period_s")),
    "phase_inconsistent_cycle_period": set_path(("temporal_sampling", "cycle_period_s"), 0.001),
    "wrong_schema_hash": set_path(("identity", "schema_sha256"), "f" * 64),
    "unknown_material": set_path(("solid_material_refs", 0, "material_id"), "TBD"),
    "absolute_wall_path": set_path(("wall_field", "artifacts", 0, "path"), "/tmp/h.h5"),
}


def double_count(document):
    energy = document["energy_sources"]
    energy["operating_point"] = "OTHER_DECLARED_POINT"
    energy["q_chip"]["value"] = 5.25
    energy["q_airjet_self"]["value"] = 1
    energy["q_total"]["value"] = 6.25


def duplicate_wall_path(document):
    document["wall_field"]["artifacts"][1]["path"] = "WALL/H_FIELD.H5"


def duplicate_interface_id(document):
    document["region_interface_map"]["interfaces"].append(copy.deepcopy(document["region_interface_map"]["interfaces"][0]))


def duplicate_material_region(document):
    document["solid_material_refs"].append(copy.deepcopy(document["solid_material_refs"][0]))


def extra_unreferenced_material_region(document):
    item = copy.deepcopy(document["solid_material_refs"][0])
    item["solid_region"] = "unreferenced-solid"
    item["material_id"] = "candidate-extra-001"
    item["material_record_sha256"] = "8" * 64
    document["solid_material_refs"].append(item)


def instantaneous_periodic(document):
    document["temporal_sampling"] = {
        "time_basis": "instantaneous", "time_unit": "s", "start": 0,
        "step": 0.001, "sample_count": 2, "periodic": True,
    }


def instantaneous_zero_samples(document):
    document["temporal_sampling"] = {
        "time_basis": "instantaneous", "time_unit": "s", "start": 0,
        "step": 0.001, "sample_count": 0, "periodic": False,
    }


def instantaneous_with_cycle_period(document):
    document["temporal_sampling"] = {
        "time_basis": "instantaneous", "time_unit": "s", "start": 0,
        "step": 0.001, "sample_count": 2, "periodic": False, "cycle_period_s": 0.002,
    }


def cycle_mean_two_samples(document):
    document["temporal_sampling"] = {
        "time_basis": "cycle_mean", "time_unit": "s", "start": 0,
        "averaging_window_s": 0.001, "sample_count": 2, "periodic": False,
    }


def cycle_mean_periodic(document):
    document["temporal_sampling"] = {
        "time_basis": "cycle_mean", "time_unit": "s", "start": 0,
        "averaging_window_s": 0.001, "sample_count": 1, "periodic": True,
    }


def cycle_mean_with_step(document):
    document["temporal_sampling"] = {
        "time_basis": "cycle_mean", "time_unit": "s", "start": 0,
        "step": 0.001, "sample_count": 1, "periodic": False,
    }


P4_REJECTIONS.update({
    "forbidden_double_count": double_count,
    "duplicate_artifact_path": duplicate_wall_path,
    "duplicate_interface_id": duplicate_interface_id,
    "duplicate_material_region": duplicate_material_region,
    "extra_unreferenced_material_region": extra_unreferenced_material_region,
    "instantaneous_periodic": instantaneous_periodic,
    "instantaneous_zero_samples": instantaneous_zero_samples,
    "instantaneous_with_cycle_period": instantaneous_with_cycle_period,
    "cycle_mean_two_samples": cycle_mean_two_samples,
    "cycle_mean_periodic": cycle_mean_periodic,
    "cycle_mean_with_step": cycle_mean_with_step,
})


class TestSchemaSemanticAlignment(unittest.TestCase):
    def _assert_schema_rejects(self, contract, mutation, schema_name):
        mutation(contract)
        schema = json.loads((ROOT / "schemas" / schema_name).read_text(encoding="utf-8"))
        self.assertTrue(_schema_errors(contract, schema, schema))

    def test_schema_rejects_unmapped_fraction_one(self):
        self._assert_schema_rejects(p2(), P2_REJECTIONS["unmapped_equal_one"], "p2_to_p3_structural_displacement_handoff.schema.json")

    def test_schema_rejects_negative_stress(self):
        self._assert_schema_rejects(p2(), P2_REJECTIONS["negative_maximum_stress"], "p2_to_p3_structural_displacement_handoff.schema.json")

    def test_schema_rejects_negative_power(self):
        self._assert_schema_rejects(p2(), P2_REJECTIONS["negative_electrical_power"], "p2_to_p3_structural_displacement_handoff.schema.json")

    def test_schema_rejects_ads_path(self):
        self._assert_schema_rejects(p2(), P2_REJECTIONS["ads_artifact_path"], "p2_to_p3_structural_displacement_handoff.schema.json")

    def test_schema_rejects_reserved_device_path(self):
        self._assert_schema_rejects(p2(), P2_REJECTIONS["reserved_con_path"], "p2_to_p3_structural_displacement_handoff.schema.json")

    def test_schema_rejects_map_unit(self):
        self._assert_schema_rejects(p4(), P4_REJECTIONS["bad_map_unit"], "p4_to_p5_wall_cht_handoff.schema.json")

    def test_schema_rejects_temporal_relation(self):
        self._assert_schema_rejects(p4(), P4_REJECTIONS["phase_nonperiodic"], "p4_to_p5_wall_cht_handoff.schema.json")


class TestRejectedRawDocuments(unittest.TestCase):
    def test_duplicate_json_key(self):
        with self.assertRaises(ContractValidationError):
            validate_file(ROOT / "fixtures" / "invalid" / "duplicate_keys.json")

    def test_nonfinite_nan(self):
        with self.assertRaises(ContractValidationError):
            load_json_bytes(b'{"value":NaN}')

    def test_top_level_array(self):
        with self.assertRaises(ContractValidationError):
            validate_document([])

    def test_unknown_contract(self):
        with self.assertRaises(ContractValidationError):
            validate_document({"contract_type": "OTHER"})

    def test_unhashable_contract_type_is_controlled_rejection(self):
        with self.assertRaises(ContractValidationError):
            validate_document({"contract_type": []})

    def test_malformed_sections_never_escape_type_errors(self):
        section_names = [
            "identity", "coordinate_system", "temporal_sampling", "artifacts",
            "mapping", "mechanical_metrics", "provenance",
        ]
        hostile_values = [None, "bad", 0, [], True]
        for section in section_names:
            for value in hostile_values:
                with self.subTest(section=section, value=value):
                    document = p2()
                    document[section] = value
                    with self.assertRaises(ContractValidationError):
                        validate_document(document)


def make_rejection_test(base_factory, mutator):
    def test(self):
        document = base_factory()
        mutator(document)
        with self.assertRaises(ContractValidationError):
            validate_document(document)
    return test


for name, mutation in P2_REJECTIONS.items():
    setattr(TestRejectedRawDocuments, f"test_p2_reject_{name}", make_rejection_test(p2, mutation))

for name, mutation in P4_REJECTIONS.items():
    setattr(TestRejectedRawDocuments, f"test_p4_reject_{name}", make_rejection_test(p4, mutation))


if __name__ == "__main__":
    unittest.main()

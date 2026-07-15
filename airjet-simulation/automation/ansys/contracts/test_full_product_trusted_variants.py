#!/usr/bin/env python3
"""Static negative tests for the nine AirJet Mini Gen1 trusted blueprints."""

from __future__ import print_function

import copy
import csv
import hashlib
import json
import os
from pathlib import Path
import tempfile

import build_full_product_trusted_variants as generator
import full_product_semantic_contract_v1 as contract


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
CAMPAIGN = HERE / "trusted_full_product_gen1" / "campaign.json"
PRODUCT_ID = "AIRJET_MINI_GEN1"
SHA = "a" * 64


def raw_json(value):
    return (json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("ascii")


def expect_code(function, code):
    try:
        function()
    except ValueError as error:
        assert str(error) == code, (str(error), code)
        return
    raise AssertionError("expected rejection " + code)


def csv_expected_records():
    layouts_path = REPO / "airjet-simulation/parameters/p1_layout_configuration_matrix.csv"
    variants_path = REPO / "airjet-simulation/parameters/p1_model_form_variants.csv"
    with layouts_path.open("r", encoding="utf-8", newline="") as handle:
        layouts = dict((row["configuration_id"], row) for row in csv.DictReader(handle))
    with variants_path.open("r", encoding="utf-8", newline="") as handle:
        variants = list(csv.DictReader(handle))
    assert len(variants) == 9
    expected = {}
    for index, row in enumerate(variants, 1):
        expected[row["variant_id"]] = {
            "configuration_id": generator.safe_id(row["configuration_id"], "AJM006_GEN1_CFG_"),
            "cell_count": int(layouts[row["configuration_id"]]["cell_count"]),
            "variant_id": generator.safe_id(row["variant_id"], "AJM006_GEN1_V%02d_" % index),
        }
    return expected


def load_inputs():
    campaign_bytes = CAMPAIGN.read_bytes()
    campaign = json.loads(campaign_bytes.decode("ascii"))
    blueprint_bytes = dict(
        (record["blueprint_path"], (REPO / record["blueprint_path"]).read_bytes())
        for record in campaign["variant_contracts"]
    )
    source_bytes = dict(
        (record["git_path"], (REPO / record["git_path"]).read_bytes())
        for record in campaign["source_contracts"]
    )
    return campaign_bytes, campaign, blueprint_bytes, source_bytes


def campaign_call(campaign_bytes, blueprint_bytes, source_bytes, expected=None):
    return contract.load_trusted_campaign_bytes(
        campaign_bytes,
        hashlib.sha256(campaign_bytes).hexdigest(),
        blueprint_bytes,
        expected,
        source_bytes,
    )


def main():
    campaign_bytes, campaign, blueprint_bytes, source_bytes = load_inputs()
    expected = csv_expected_records()
    result = campaign_call(campaign_bytes, blueprint_bytes, source_bytes, expected)
    assert result["status"] == "PASS_TRUSTED_FULL_PRODUCT_CAMPAIGN"
    assert result["variant_count"] == 9
    assert campaign["product_id"] == PRODUCT_ID
    cell_counts = []
    entity_counts = []
    raw_hash_by_path = {}
    blueprints = []
    for record in campaign["variant_contracts"]:
        payload = blueprint_bytes[record["blueprint_path"]]
        raw_hash = hashlib.sha256(payload).hexdigest()
        raw_hash_by_path[record["blueprint_path"]] = raw_hash
        blueprint = contract.load_trusted_blueprint_bytes(payload, raw_hash)
        blueprints.append(blueprint)
        summary = contract.validate_trusted_blueprint(blueprint)
        assert blueprint["product_id"] == PRODUCT_ID
        assert blueprint["configuration"]["product_id"] == PRODUCT_ID
        assert blueprint["artifact_root_id"] == "p1_cad_006"
        assert "full_product_core_test" in blueprint["required_contract_hash_keys"]
        assert {
            "PRODUCER_JOB_RECORD",
            "PRODUCER_ARTIFACT_MANIFEST",
            "SEMANTIC_OBSERVATION",
            "OBSERVER_JOB_RECORD",
            "OBSERVER_ARTIFACT_MANIFEST",
        } <= {item["role"] for item in blueprint["artifact_contracts"]}
        assert "G2" not in json.dumps(blueprint, ensure_ascii=True).upper()
        assert len(blueprint["frames"]) == summary["cell_count"] + 1
        assert all(frame["cell_index"] is not None for frame in blueprint["frames"][1:])
        assert len(set(frame["frame_id"] for frame in blueprint["frames"])) == len(blueprint["frames"])
        cell_counts.append(summary["cell_count"])
        entity_counts.append(summary["semantic_entity_count"])
        source_hashes = dict((item["contract_key"], item["sha256"]) for item in campaign["source_contracts"])
        hashes = []
        for name in blueprint["required_contract_hash_keys"]:
            if name == "full_product_blueprint":
                value = summary["blueprint_payload_sha256"]
            elif name == "trusted_blueprint_file":
                value = raw_hash
            elif name == "trusted_campaign":
                value = hashlib.sha256(campaign_bytes).hexdigest()
            else:
                value = source_hashes[name]
            hashes.append({"contract_key": name, "sha256": value})
        with tempfile.TemporaryDirectory(prefix="ajm-gen1-contract-") as temporary:
            root = os.path.realpath(temporary)
            trusted = contract.materialize_trusted_contract(
                blueprint,
                raw_hash,
                {"profile_id": generator.PRODUCER_PROFILE_ID, "profile_contract_sha256": SHA, "script_sha256": SHA},
                {"profile_id": generator.OBSERVER_PROFILE_ID, "profile_contract_sha256": SHA, "script_sha256": SHA},
                root,
                hashes,
            )
            assert trusted["configuration"]["product_id"] == PRODUCT_ID
    assert sorted(set(cell_counts)) == [8, 12, 15]
    assert min(entity_counts) > 700
    generator.validate_gen1_target(campaign, blueprints)

    negative = 0
    expect_code(
        lambda: contract.load_trusted_campaign_bytes(
            campaign_bytes, "0" * 64, blueprint_bytes, expected, source_bytes
        ),
        "FPSEM_CAMPAIGN_RAW_SHA256",
    ); negative += 1
    missing_sources = dict(source_bytes); missing_sources.pop(next(iter(missing_sources)))
    expect_code(lambda: campaign_call(campaign_bytes, blueprint_bytes, missing_sources, expected), "FPSEM_CAMPAIGN_SOURCE_FILE_SET"); negative += 1
    tampered_sources = dict(source_bytes); first_source = next(iter(tampered_sources)); tampered_sources[first_source] += b"x"
    expect_code(lambda: campaign_call(campaign_bytes, blueprint_bytes, tampered_sources, expected), "FPSEM_CAMPAIGN_SOURCE_FILE_SHA256"); negative += 1
    missing_blueprints = dict(blueprint_bytes); missing_blueprints.pop(next(iter(missing_blueprints)))
    expect_code(lambda: campaign_call(campaign_bytes, missing_blueprints, source_bytes, expected), "FPSEM_CAMPAIGN_BLUEPRINT_FILE_SET"); negative += 1
    tampered_blueprints = dict(blueprint_bytes); first_blueprint = next(iter(tampered_blueprints)); tampered_blueprints[first_blueprint] += b"x"
    expect_code(lambda: campaign_call(campaign_bytes, tampered_blueprints, source_bytes, expected), "FPSEM_BLUEPRINT_RAW_SHA256"); negative += 1
    missing_expected = dict(expected); missing_expected.pop(next(iter(missing_expected)))
    expect_code(lambda: campaign_call(campaign_bytes, blueprint_bytes, source_bytes, missing_expected), "FPSEM_CAMPAIGN_EXPECTED_VARIANT_SET"); negative += 1

    duplicate_campaign = copy.deepcopy(campaign)
    duplicate_campaign["variant_contracts"][1]["source_variant_id"] = duplicate_campaign["variant_contracts"][0]["source_variant_id"]
    duplicate_bytes = raw_json(duplicate_campaign)
    expect_code(lambda: campaign_call(duplicate_bytes, blueprint_bytes, source_bytes, expected), "FPSEM_CAMPAIGN_VARIANT_IDENTITY"); negative += 1
    record_mismatch = copy.deepcopy(campaign)
    record_mismatch["variant_contracts"][0]["cell_count"] += 1
    mismatch_bytes = raw_json(record_mismatch)
    expect_code(lambda: campaign_call(mismatch_bytes, blueprint_bytes, source_bytes, expected), "FPSEM_CAMPAIGN_BLUEPRINT_RECORD_MISMATCH"); negative += 1
    bad_source_id = copy.deepcopy(blueprints[0]); bad_source_id["source_variant_id"] = "bad source"
    expect_code(lambda: contract.validate_trusted_blueprint(bad_source_id), "FPSEM_BLUEPRINT_SOURCE_VARIANT_ID"); negative += 1
    g2_campaign = copy.deepcopy(campaign); g2_campaign["product_id"] = "AIRJET_MINI_G2"
    expect_code(lambda: generator.validate_gen1_target(g2_campaign, blueprints), "GEN1_CAMPAIGN_TARGET"); negative += 1
    g2_blueprint = copy.deepcopy(blueprints[0]); g2_blueprint["product_id"] = "AIRJET_MINI_G2"; g2_blueprint["configuration"]["product_id"] = "AIRJET_MINI_G2"
    expect_code(lambda: generator.validate_gen1_target(campaign, [g2_blueprint] + blueprints[1:]), "GEN1_BLUEPRINT_TARGET"); negative += 1
    wrong_root = copy.deepcopy(blueprints[0]); wrong_root["artifact_root_id"] = "untrusted_root"
    expect_code(lambda: generator.validate_gen1_target(campaign, [wrong_root] + blueprints[1:]), "GEN1_BLUEPRINT_TARGET"); negative += 1
    missing_core_test = copy.deepcopy(blueprints[0]); missing_core_test["required_contract_hash_keys"].remove("full_product_core_test")
    expect_code(lambda: generator.validate_gen1_target(campaign, [missing_core_test] + blueprints[1:]), "GEN1_BLUEPRINT_TARGET"); negative += 1
    missing_observer_manifest = copy.deepcopy(blueprints[0]); missing_observer_manifest["artifact_contracts"] = [item for item in missing_observer_manifest["artifact_contracts"] if item["role"] != "OBSERVER_ARTIFACT_MANIFEST"]
    expect_code(lambda: generator.validate_gen1_target(campaign, [missing_observer_manifest] + blueprints[1:]), "GEN1_BLUEPRINT_TARGET"); negative += 1

    print(
        "FULL_PRODUCT_TRUSTED_VARIANT_TESTS=PASS product=AIRJET_MINI_GEN1 "
        "variants=9 cells=8,12,15 negative=%d g2_rejected=PASS" % negative
    )


if __name__ == "__main__":
    main()

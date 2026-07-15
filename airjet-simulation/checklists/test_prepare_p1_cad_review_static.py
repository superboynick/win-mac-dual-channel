#!/usr/bin/env python3
"""Pure static tests for the Gen1 006/007 production-contract bridge."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
REVIEWER_PATH = HERE / "prepare_p1_cad_review.py"
spec = importlib.util.spec_from_file_location("prepare_p1_cad_review", REVIEWER_PATH)
reviewer = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(reviewer)


def expectations() -> dict[str, tuple[str, int]]:
    with (REPO / "airjet-simulation/parameters/p1_model_form_variants.csv").open(
        encoding="utf-8", newline=""
    ) as handle:
        variants = list(csv.DictReader(handle))
    with (REPO / "airjet-simulation/parameters/p1_cad_parameter_map.csv").open(
        encoding="utf-8", newline=""
    ) as handle:
        parameters = list(csv.DictReader(handle))
    counts = {
        row["variant_id"]: int(float(row["value"]))
        for row in parameters
        if row["parameter_id"] == "C001"
    }
    return {
        row["variant_id"]: (row["configuration_id"], counts[row["variant_id"]])
        for row in variants
    }


def profile(
    profile_id: str,
    engine: str,
    script: str,
    script_bytes: bytes,
    reports: list[str],
    predecessor: dict[str, object] | None,
) -> dict[str, object]:
    return {
        "profile_id": profile_id,
        "engine": engine,
        "script": script,
        "sha256": hashlib.sha256(script_bytes).hexdigest(),
        "timeout_seconds": 1800,
        "output_root_id": "p1_cad_006",
        "reports": reports,
        "predecessor": predecessor,
    }


def main() -> int:
    original_git_blob = reviewer.git_blob
    original_expected_variants = reviewer.EXPECTED_VARIANTS
    fake_scripts = {
        "airjet-simulation/automation/ansys/approved/006/gen1_producer.py": b"# signed producer\n",
        "airjet-simulation/automation/ansys/approved/006/gen1_observer.wbjn": b"# signed observer\n",
    }
    profiles_path = REPO / reviewer.PROFILES_PATH
    static_doc = json.loads(profiles_path.read_text(encoding="utf-8"))

    def working_blob(_repo: Path, _commit: str, relative_path: str) -> bytes:
        if relative_path in fake_scripts:
            return fake_scripts[relative_path]
        return (REPO / relative_path).read_bytes().replace(b"\r\n", b"\n")

    reviewer.git_blob = working_blob
    negative = 0
    try:
        try:
            reviewer.load_production_contract_at_commit(REPO, "0" * 40, expectations())
        except ValueError as exc:
            assert "static-only" in str(exc)
            negative += 1
        else:
            raise AssertionError("static production state did not block execution")

        registered = json.loads(json.dumps(static_doc))
        registered["production_contracts"]["execution_state"] = reviewer.PRODUCTION_REGISTERED_STATE
        producer = profile(
            reviewer.PRODUCTION_PRODUCER_PROFILE_ID,
            "spaceclaim",
            "006/gen1_producer.py",
            fake_scripts[
                "airjet-simulation/automation/ansys/approved/006/gen1_producer.py"
            ],
            ["producer_report.json"],
            None,
        )
        observer = profile(
            reviewer.PRODUCTION_OBSERVER_PROFILE_ID,
            "workbench",
            "006/gen1_observer.wbjn",
            fake_scripts[
                "airjet-simulation/automation/ansys/approved/006/gen1_observer.wbjn"
            ],
            ["observer_report.json"],
            {
                "profile_id": reviewer.PRODUCTION_PRODUCER_PROFILE_ID,
                "report": "producer_report.json",
                "required_probe": "ajm006_gen1_producer",
                "required_status": "PASS_PARTIAL_CAD_CAPABILITY",
                "required_assertions": ["full_product_semantic_bundle"],
                "artifacts": ["producer_report.json", "product.step"],
            },
        )
        registered["profiles"].extend([producer, observer])
        registered_blob = (
            json.dumps(registered, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
        ).encode("ascii")

        def registered_blob_reader(_repo: Path, _commit: str, relative_path: str) -> bytes:
            if relative_path == reviewer.PROFILES_PATH:
                return registered_blob
            return working_blob(_repo, _commit, relative_path)

        reviewer.git_blob = registered_blob_reader
        context = reviewer.load_production_contract_at_commit(
            REPO, "0" * 40, expectations()
        )
        assert context["production"]["product_id"] == "AIRJET_MINI_GEN1"
        assert len(context["campaign"]["variant_contracts"]) == 9
        assert set(context["runtime_contracts"]) == {"producer", "observer"}
        for record in context["campaign"]["variant_contracts"]:
            blueprint = json.loads(context["blueprint_blobs"][record["blueprint_path"]])
            roles = {item["role"] for item in blueprint["artifact_contracts"]}
            assert {
                "PRODUCER_JOB_RECORD",
                "PRODUCER_ARTIFACT_MANIFEST",
                "SEMANTIC_OBSERVATION",
                "OBSERVER_JOB_RECORD",
                "OBSERVER_ARTIFACT_MANIFEST",
            } <= roles
            assert "full_product_core_test" in blueprint["required_contract_hash_keys"]
            assert blueprint["artifact_root_id"] == "p1_cad_006"
            assert "G2" not in json.dumps(blueprint, ensure_ascii=True).upper()

        tampered = json.loads(registered_blob.decode("ascii"))
        tampered["production_contracts"]["product_id"] = "AIRJET_MINI_G2"
        tampered_blob = json.dumps(tampered, ensure_ascii=True).encode("ascii")
        reviewer.git_blob = lambda repo, commit, path: (
            tampered_blob if path == reviewer.PROFILES_PATH else working_blob(repo, commit, path)
        )
        try:
            reviewer.load_production_contract_at_commit(REPO, "0" * 40, expectations())
        except ValueError as exc:
            assert "identity changed" in str(exc)
            negative += 1
        else:
            raise AssertionError("G2 target tamper was accepted")

        class FakeEngine:
            @staticmethod
            def load_trusted_blueprint_bytes(data: bytes, expected_sha: str) -> dict[str, object]:
                assert hashlib.sha256(data).hexdigest() == expected_sha
                return json.loads(data)

            @staticmethod
            def validate_trusted_blueprint(_blueprint: dict[str, object]) -> dict[str, object]:
                return {"blueprint_payload_sha256": "1" * 64}

            @staticmethod
            def materialize_trusted_contract(*_args: object) -> dict[str, object]:
                return {"ok": True}

            @staticmethod
            def load_json_bytes_strict(data: bytes) -> dict[str, object]:
                return json.loads(data.decode("utf-8"))

            @staticmethod
            def validate_full_product_bundle(
                _sidecar: dict[str, object],
                _binding: dict[str, object],
                _observation: dict[str, object],
                actual_files: dict[str, object],
                _trusted_bytes: bytes,
                trusted_sha: str,
            ) -> dict[str, object]:
                return {
                    "missing_keys": [],
                    "unexpected_keys": [],
                    "dangling_adjacency": [],
                    "orphan_critical_surfaces": [],
                    "body_surface_coverage_ok": True,
                    "assignment_solution_count": 1,
                    "topology_observed": True,
                    "cardinality_observed": True,
                    "observed_semantic_key_count": 1,
                    "observed_actual_entity_count": 1,
                    "observed_group_count": 1,
                    "actual_artifact_count": len(actual_files["files"]),
                    "detached_binding_valid": True,
                    "trusted_contract_sha256": trusted_sha,
                    "status": "PASS_FULL_PRODUCT_SEMANTIC_BUNDLE",
                }

        with tempfile.TemporaryDirectory(prefix="ajm006-reviewer-wrapper-") as temporary:
            root = Path(temporary).resolve()
            source_id = "STATIC_TEST_VARIANT"
            runtime_id = "AJM006_GEN1_STATIC_TEST_VARIANT"
            roles = [
                ("native_cad", "NATIVE_CAD", "product.scdocx"),
                ("producer_job_record", "PRODUCER_JOB_RECORD", "checks/producer_job.json"),
                ("producer_artifact_manifest", "PRODUCER_ARTIFACT_MANIFEST", "checks/producer_manifest.json"),
                ("step_geometry", "STEP_GEOMETRY", "product.step"),
                ("step_reimport_log", "STEP_REIMPORT_LOG", "checks/step_reimport.json"),
                ("semantic_sidecar", "SEMANTIC_SIDECAR", "checks/sidecar.json"),
                ("semantic_binding", "SEMANTIC_BINDING", "checks/binding.json"),
                ("semantic_observation", "SEMANTIC_OBSERVATION", "checks/observation.json"),
                ("semantic_key_report", "SEMANTIC_KEY_CARDINALITY_REPORT", "checks/key_report.json"),
                ("workbench_project", "WORKBENCH_PROJECT", "checks/project.wbpj"),
                ("observer_job_record", "OBSERVER_JOB_RECORD", "checks/observer_job.json"),
                ("observer_artifact_manifest", "OBSERVER_ARTIFACT_MANIFEST", "checks/observer_manifest.json"),
                ("workbench_semantic_log", "WORKBENCH_STEP_SEMANTIC_LOG", "checks/semantic.log"),
            ]
            artifact_contracts = [
                {
                    "artifact_id": artifact_id,
                    "role": role,
                    "relative_path": "variant_static/%s" % relative,
                    "required": True,
                }
                for artifact_id, role, relative in roles
            ]
            blueprint = {
                "artifact_contracts": artifact_contracts,
                "artifact_root_id": "p1_cad_006",
                "required_contract_hash_keys": [
                    "full_product_blueprint",
                    "trusted_blueprint_file",
                    "trusted_campaign",
                ],
                "groups": [{}],
            }
            blueprint_bytes = json.dumps(blueprint, sort_keys=True).encode("utf-8")
            blueprint_sha = hashlib.sha256(blueprint_bytes).hexdigest()
            campaign = {
                "source_contracts": [],
                "variant_contracts": [
                    {
                        "source_variant_id": source_id,
                        "variant_id": runtime_id,
                        "configuration_id": "AJM006_GEN1_CFG_STATIC",
                        "semantic_entity_count": 1,
                        "blueprint_path": "blueprint.json",
                        "blueprint_sha256": blueprint_sha,
                    }
                ],
            }
            campaign_blob = json.dumps(campaign, sort_keys=True).encode("utf-8")
            trusted_bytes = json.dumps(
                {"ok": True}, ensure_ascii=True, sort_keys=True, separators=(",", ":")
            ).encode("ascii")
            trusted_sha = hashlib.sha256(trusted_bytes).hexdigest()
            computed = FakeEngine.validate_full_product_bundle(
                {}, {}, {}, {"files": artifact_contracts}, trusted_bytes, trusted_sha
            )
            key_report = {
                "schema_version": 1,
                "contract_id": "AIRJET_FULL_PRODUCT_SEMANTIC_KEY_REPORT_V1",
                "source_variant_id": source_id,
                "configuration_id": "AJM006_GEN1_CFG_STATIC",
                **computed,
            }
            payload_by_role: dict[str, bytes] = {role: b"x" for _, role, _ in roles}
            for role in (
                "PRODUCER_ARTIFACT_MANIFEST",
                "OBSERVER_ARTIFACT_MANIFEST",
                "STEP_REIMPORT_LOG",
                "SEMANTIC_SIDECAR",
                "SEMANTIC_BINDING",
                "SEMANTIC_OBSERVATION",
            ):
                payload_by_role[role] = b"{}"
            producer_manifest_sha = hashlib.sha256(
                payload_by_role["PRODUCER_ARTIFACT_MANIFEST"]
            ).hexdigest()
            observer_manifest_sha = hashlib.sha256(
                payload_by_role["OBSERVER_ARTIFACT_MANIFEST"]
            ).hexdigest()
            base_identity = {
                "git_head": "0" * 40,
                "case_id": runtime_id,
                "artifact_manifest_sha256": producer_manifest_sha,
            }
            payload_by_role["PRODUCER_JOB_RECORD"] = json.dumps(base_identity).encode("utf-8")
            observer_identity = dict(base_identity)
            observer_identity["artifact_manifest_sha256"] = observer_manifest_sha
            payload_by_role["OBSERVER_JOB_RECORD"] = json.dumps(observer_identity).encode("utf-8")
            payload_by_role["SEMANTIC_KEY_CARDINALITY_REPORT"] = json.dumps(
                key_report, sort_keys=True
            ).encode("utf-8")
            manifest_rows = []
            for item in artifact_contracts:
                path = root.joinpath(*item["relative_path"].split("/"))
                path.parent.mkdir(parents=True, exist_ok=True)
                data = payload_by_role[item["role"]]
                path.write_bytes(data)
                manifest_rows.append(
                    {
                        "case_id": source_id,
                        "file_role": item["role"],
                        "absolute_path": str(path),
                        "size_bytes": str(len(data)),
                        "sha256": hashlib.sha256(data).hexdigest(),
                    }
                )
            context = {
                "engine": FakeEngine(),
                "campaign": campaign,
                "campaign_blob": campaign_blob,
                "blueprint_blobs": {"blueprint.json": blueprint_bytes},
                "runtime_contracts": {"producer": {}, "observer": {}},
            }
            reviewer.EXPECTED_VARIANTS = {source_id}
            result = reviewer.validate_production_bundles(
                context, manifest_rows, root, str(root), "0" * 40, {source_id}
            )
            assert set(result) == {source_id}

            for mutation, marker in (
                (
                    lambda rows: [
                        row for row in rows if row["file_role"] != "SEMANTIC_OBSERVATION"
                    ],
                    "exactly one",
                ),
                (
                    lambda rows: [
                        ({**row, "sha256": "0" * 64}
                         if row["file_role"] == "PRODUCER_ARTIFACT_MANIFEST" else row)
                        for row in rows
                    ],
                    "artifact-manifest binding",
                ),
                (
                    lambda rows: [
                        ({**row, "absolute_path": next(
                            item["absolute_path"]
                            for item in rows
                            if item["file_role"] == "SEMANTIC_BINDING"
                        )} if row["file_role"] == "SEMANTIC_OBSERVATION" else row)
                        for row in rows
                    ],
                    "trusted blueprint",
                ),
            ):
                try:
                    reviewer.validate_production_bundles(
                        context, mutation([dict(row) for row in manifest_rows]), root, str(root), "0" * 40, {source_id}
                    )
                except ValueError as exc:
                    assert marker in str(exc)
                    negative += 1
                else:
                    raise AssertionError("reviewer wrapper tamper was accepted")
            key_row = next(
                row for row in manifest_rows
                if row["file_role"] == "SEMANTIC_KEY_CARDINALITY_REPORT"
            )
            key_path = Path(key_row["absolute_path"])
            original_key_bytes = key_path.read_bytes()
            corrupted_key_report = json.loads(original_key_bytes)
            corrupted_key_report["missing_keys"] = ["self_reported_fake_key"]
            corrupted_bytes = json.dumps(corrupted_key_report, sort_keys=True).encode("utf-8")
            key_path.write_bytes(corrupted_bytes)
            corrupted_rows = [dict(row) for row in manifest_rows]
            corrupted_row = next(
                row for row in corrupted_rows
                if row["file_role"] == "SEMANTIC_KEY_CARDINALITY_REPORT"
            )
            corrupted_row["size_bytes"] = str(len(corrupted_bytes))
            corrupted_row["sha256"] = hashlib.sha256(corrupted_bytes).hexdigest()
            try:
                reviewer.validate_production_bundles(
                    context, corrupted_rows, root, str(root), "0" * 40, {source_id}
                )
            except ValueError as exc:
                assert "differs from computed observation" in str(exc)
                negative += 1
            else:
                raise AssertionError("self-reported semantic key result was accepted")
            finally:
                key_path.write_bytes(original_key_bytes)
    finally:
        reviewer.git_blob = original_git_blob
        reviewer.EXPECTED_VARIANTS = original_expected_variants

    print(
        "P1_REVIEWER_STATIC_TESTS=PASS product=AIRJET_MINI_GEN1 "
        "variants=9 registered_bridge=PASS static_block=PASS negative=%d" % negative
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

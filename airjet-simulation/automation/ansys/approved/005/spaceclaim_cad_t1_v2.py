# AJM-005 v2 producer wrapper. Preserves and executes the frozen v1 geometry script.
from __future__ import print_function

import copy
import hashlib
import json
import os


job_dir = os.environ["AIRJET_JOB_DIR"]
dependency_dir = os.environ["AIRJET_PROFILE_DEPENDENCY_DIR"]
base_path = os.path.join(dependency_dir, "spaceclaim_cad_t1.py")
contract_dir = dependency_dir
validator_path = os.path.join(contract_dir, "semantic_sidecar_v2_contract.py")
schema_path = os.path.join(contract_dir, "semantic_sidecar_v2.schema.json")
judgment_path = os.path.join(contract_dir, "ajm005_semantic_judgment_v2.json")
route_contract_path = os.path.join(contract_dir, "ajm005_alternate_route_v2.json")
base_report_path = os.path.join(job_dir, "spaceclaim_cad_t1.json")
v2_report_path = os.path.join(job_dir, "spaceclaim_cad_t1_v2.json")
v2_sidecar_path = os.path.join(job_dir, "spaceclaim_semantic_sidecar_v2.json")
v2_binding_path = os.path.join(job_dir, "spaceclaim_semantic_binding_v2.json")


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path):
    with open(path, "r") as handle:
        return json.load(handle)


def write_json_bytes(path, value):
    rendered = json.dumps(value, indent=2, sort_keys=True)
    if not isinstance(rendered, bytes):
        rendered = rendered.encode("utf-8")
    with open(path, "wb") as handle:
        handle.write(rendered)
    return rendered


def verify_dependency_bundle(expected_names):
    manifest_path = os.path.join(dependency_dir, "dependency-manifest.json")
    manifest = read_json(manifest_path)
    if (
        manifest.get("schema_version") != 1
        or manifest.get("profile_id") != os.environ["AIRJET_PROFILE_ID"]
        or manifest.get("git_head") != os.environ["AIRJET_GIT_HEAD"]
    ):
        raise Exception("AJM005_V2_DEPENDENCY_MANIFEST_IDENTITY")
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list):
        raise Exception("AJM005_V2_DEPENDENCY_MANIFEST_ARTIFACTS")
    by_name = dict((item.get("relative_path"), item) for item in artifacts)
    if set(by_name) != set(expected_names) or len(by_name) != len(artifacts):
        raise Exception("AJM005_V2_DEPENDENCY_MANIFEST_SET")
    if set(os.listdir(dependency_dir)) != set(expected_names) | {
        "dependency-manifest.json"
    }:
        raise Exception("AJM005_V2_DEPENDENCY_DIRECTORY_SET")
    for name in expected_names:
        path = os.path.join(dependency_dir, name)
        item = by_name[name]
        if (
            not os.path.isfile(path)
            or int(item.get("size", -1)) != int(os.path.getsize(path))
            or item.get("sha256") != sha256_file(path)
        ):
            raise Exception("AJM005_V2_DEPENDENCY_HASH:%s" % name)
    return manifest_path


dependency_manifest_path = verify_dependency_bundle(
    [
        "spaceclaim_cad_t1.py",
        "semantic_sidecar_v2_contract.py",
        "semantic_sidecar_v2.schema.json",
        "ajm005_semantic_judgment_v2.json",
        "ajm005_alternate_route_v2.json",
    ]
)


base_sha256 = sha256_file(base_path)
if base_sha256 != "4fdaf2f1f5ae2063f79b99adc8ac6ae91a147032c1386fc4119b5abd4ceff17e":
    raise Exception("AJM005_V2_BASE_PRODUCER_HASH_MISMATCH")

base_globals = globals().copy()
base_globals["__file__"] = base_path
execfile(base_path, base_globals)

base_report = read_json(base_report_path)
if base_report.get("status") != "PASS_PARTIAL_CAD_CAPABILITY":
    raise Exception("AJM005_V2_BASE_PRODUCER_NOT_PASS")

actual_sources = {
    "full_native": os.path.join(job_dir, "spaceclaim_cad_t1_full.scdocx"),
    "handoff_native": os.path.join(job_dir, "spaceclaim_cad_t1.scdocx"),
    "step": os.path.join(job_dir, "spaceclaim_cad_t1.step"),
}
declared_source_keys = {
    "full_native": "full_native",
    "handoff_native": "transfer_native",
    "step": "step",
}
for source_name, source_path in actual_sources.items():
    declared = base_report.get("files", {}).get(
        declared_source_keys[source_name], {}
    )
    if (
        not os.path.isfile(source_path)
        or int(declared.get("size", -1)) != int(os.path.getsize(source_path))
        or declared.get("sha256") != sha256_file(source_path)
    ):
        raise Exception("AJM005_V2_ACTUAL_SOURCE_HASH:%s" % source_name)

route_contract = read_json(route_contract_path)
judgment = read_json(judgment_path)
schema_sha256 = sha256_file(schema_path)
judgment_sha256 = sha256_file(judgment_path)
validator_sha256 = sha256_file(validator_path)
route_contract_sha256 = sha256_file(route_contract_path)
script_sha256 = os.environ["AIRJET_SCRIPT_SHA256"]
profile_contract_sha256 = os.environ["AIRJET_PROFILE_CONTRACT_SHA256"]
profile_id = os.environ["AIRJET_PROFILE_ID"]

if route_contract.get("contract_id") != "AJM005_ALTERNATE_ROUTE_V2":
    raise Exception("AJM005_V2_ROUTE_CONTRACT_ID")
if (
    judgment.get("contract_id") != "AJM005_ALTERNATE_ROUTE_JUDGMENT_V2"
    or judgment.get("producer_profile_id") != profile_id
    or judgment.get("producer_required_status")
    != base_report.get("status")
    or judgment.get("route", {}).get("cad_authoring")
    != "SPACECLAIM_SIGNED_SCRIPT_PARAMETRIC"
    or judgment.get("route", {}).get("solver_handoff")
    != "HASH_BOUND_STEP_SEMANTIC_SIDECAR"
    or judgment.get("claim_boundaries", {}).get("p1_stage_gate")
    != "NOT_RUN"
):
    raise Exception("AJM005_V2_JUDGMENT_PRODUCER_CONTRACT")
if route_contract.get("producer", {}).get("profile_id") != profile_id:
    raise Exception("AJM005_V2_ROUTE_PRODUCER_PROFILE")
if route_contract.get("producer", {}).get("script_sha256") != script_sha256:
    raise Exception("AJM005_V2_ROUTE_PRODUCER_SCRIPT")
if route_contract.get("producer", {}).get("profile_contract_sha256") != profile_contract_sha256:
    raise Exception("AJM005_V2_ROUTE_PRODUCER_PROFILE_HASH")
if route_contract.get("producer", {}).get("base_script_sha256") != base_sha256:
    raise Exception("AJM005_V2_ROUTE_BASE_SCRIPT")
for key, actual in (
    ("schema_sha256", schema_sha256),
    ("judgment_sha256", judgment_sha256),
    ("validator_sha256", validator_sha256),
):
    if route_contract.get("contract_hashes", {}).get(key) != actual:
        raise Exception("AJM005_V2_ROUTE_HASH_%s" % key.upper())

validator_globals = {"__file__": validator_path, "__name__": "semantic_sidecar_v2_contract"}
execfile(validator_path, validator_globals)

identity = {
    "git_head": os.environ["AIRJET_GIT_HEAD"],
    "profile_id": profile_id,
    "profile_contract_sha256": profile_contract_sha256,
    "script_sha256": script_sha256,
    "base_script_sha256": base_sha256,
}
contract_hashes = {
    "route_contract_sha256": route_contract_sha256,
    "schema_sha256": schema_sha256,
    "judgment_sha256": judgment_sha256,
    "validator_sha256": validator_sha256,
}
source_files = {
    "full_native": {
        "relative_path": "spaceclaim_cad_t1_full.scdocx",
        "size": int(base_report["files"]["full_native"]["size"]),
        "sha256": base_report["files"]["full_native"]["sha256"],
    },
    "handoff_native": {
        "relative_path": "spaceclaim_cad_t1.scdocx",
        "size": int(base_report["files"]["transfer_native"]["size"]),
        "sha256": base_report["files"]["transfer_native"]["sha256"],
    },
    "step": {
        "relative_path": "spaceclaim_cad_t1.step",
        "size": int(base_report["files"]["step"]["size"]),
        "sha256": base_report["files"]["step"]["sha256"],
    },
}
sidecar = validator_globals["build_fixture_sidecar"](
    base_report["construction"]["face_details"],
    source_files,
    identity,
    contract_hashes,
)
expected_hashes = {
    "step_sha256": source_files["step"]["sha256"],
    "handoff_native_sha256": source_files["handoff_native"]["sha256"],
    "profile_contract_sha256": profile_contract_sha256,
    "script_sha256": script_sha256,
    "route_contract_sha256": route_contract_sha256,
    "schema_sha256": schema_sha256,
    "judgment_sha256": judgment_sha256,
    "validator_sha256": validator_sha256,
}
validation = validator_globals["validate_sidecar"](sidecar, expected_hashes)
sidecar_bytes = write_json_bytes(v2_sidecar_path, sidecar)
binding = validator_globals["build_binding"](
    sidecar_bytes, sidecar, identity, contract_hashes
)
validator_globals["validate_binding"](
    binding,
    sidecar_bytes,
    sidecar,
    {
        "step_sha256": source_files["step"]["sha256"],
        "handoff_native_sha256": source_files["handoff_native"]["sha256"],
        "profile_contract_sha256": profile_contract_sha256,
        "script_sha256": script_sha256,
        "route_contract_sha256": route_contract_sha256,
    },
)
write_json_bytes(v2_binding_path, binding)

artifact_hash_checks = {
    "actual_sidecar_matches_binding": binding["sidecar_sha256"]
    == sha256_file(v2_sidecar_path),
    "actual_step_matches_binding": binding["step_sha256"]
    == sha256_file(actual_sources["step"]),
    "actual_native_matches_binding": binding["handoff_native_sha256"]
    == sha256_file(actual_sources["handoff_native"]),
    "actual_step_matches_sidecar": sidecar["source_artifacts"]["step"][
        "sha256"
    ]
    == sha256_file(actual_sources["step"]),
    "actual_native_matches_sidecar": sidecar["source_artifacts"][
        "handoff_native"
    ]["sha256"]
    == sha256_file(actual_sources["handoff_native"]),
    "route_contract_matches_sidecar": sidecar["contract_hashes"][
        "route_contract_sha256"
    ]
    == route_contract_sha256,
    "schema_matches_sidecar": sidecar["contract_hashes"]["schema_sha256"]
    == schema_sha256,
    "judgment_matches_sidecar": sidecar["contract_hashes"]["judgment_sha256"]
    == judgment_sha256,
    "validator_matches_sidecar": sidecar["contract_hashes"][
        "validator_sha256"
    ]
    == validator_sha256,
}
artifact_hash_chain_ok = all(artifact_hash_checks.values())
if not artifact_hash_chain_ok:
    raise Exception("AJM005_V2_PRODUCER_ARTIFACT_HASH_CHAIN")

v2_report = copy.deepcopy(base_report)
v2_report["schema_version"] = 2
v2_report["probe"] = "spaceclaim_cad_t1_v2"
v2_report["native_parameterization"] = "NOT_PROVEN"
v2_report["p1_cad_hard_gate"] = "ALTERNATE_ROUTE_PRODUCER_PENDING_CONSUMER"
v2_report["p1_cad_toolchain_scope"] = "ALTERNATE_ROUTE_ONLY"
v2_report["cad_authoring_route"] = "SPACECLAIM_SIGNED_SCRIPT_PARAMETRIC"
v2_report["solver_handoff_route"] = "HASH_BOUND_STEP_SEMANTIC_SIDECAR"
v2_report["external_native_attach"] = "NOT_PROVEN"
v2_report["native_named_selection_transfer"] = "NOT_PROVEN"
v2_report["route_contract"] = {
    "path": route_contract_path,
    "sha256": route_contract_sha256,
}
v2_report["semantic_v2_validation"] = validation
v2_report["semantic_v2_artifact_hash_checks"] = artifact_hash_checks
v2_report["semantic_v2_identity"] = {
    "profile_contract_sha256": profile_contract_sha256,
    "script_sha256": script_sha256,
    "schema_sha256": schema_sha256,
    "judgment_sha256": judgment_sha256,
    "validator_sha256": validator_sha256,
    "dependency_manifest_sha256": sha256_file(dependency_manifest_path),
}
v2_report["assertions"].update(
    {
        "semantic_schema_identity": True,
        "semantic_keys_exact": validation["required_key_count"] == 14,
        "semantic_cardinality_declared": validation["surface_key_count"] == 13,
        "semantic_topology_nonorphan": True,
        "detached_sidecar_raw_hash": (
            binding["sidecar_sha256"] == sha256_file(v2_sidecar_path)
            and "sidecar_sha256" not in sidecar
        ),
        "artifact_hash_chain": artifact_hash_chain_ok,
        "actual_source_files_hashed": True,
    }
)
v2_report["files"]["semantic_sidecar_v2"] = {
    "path": v2_sidecar_path,
    "size": os.path.getsize(v2_sidecar_path),
    "sha256": sha256_file(v2_sidecar_path),
}
v2_report["files"]["semantic_binding_v2"] = {
    "path": v2_binding_path,
    "size": os.path.getsize(v2_binding_path),
    "sha256": sha256_file(v2_binding_path),
}

required = route_contract["producer"]["required_assertions"]
if required != judgment["producer_required_assertions"]:
    raise Exception("AJM005_V2_JUDGMENT_PRODUCER_ASSERTION_SET")
if not all(v2_report["assertions"].get(name) is True for name in required):
    raise Exception("AJM005_V2_PRODUCER_ASSERTION_FAILED")
write_json_bytes(v2_report_path, v2_report)

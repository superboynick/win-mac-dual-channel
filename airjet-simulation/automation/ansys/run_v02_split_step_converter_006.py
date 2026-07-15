#!/usr/bin/env python3
"""Run the V02 producer -> independent upstream/downstream STEP converter."""

from __future__ import annotations

import asyncio
import importlib.util
from pathlib import Path


BASE_PATH = Path(__file__).resolve().with_name(
    "run_v02_parasolid_topology_006.py"
)
SPEC = importlib.util.spec_from_file_location(
    "airjet_v02_parasolid_runner_base", BASE_PATH
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("BLOCKED_BASE_RUNNER_IMPORT_SPEC")
base = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(base)

base.RESULT_PATH = base.OUTPUT_ROOT / "V02_SPLIT_STEP_CONVERTER_RUN_SUMMARY.json"
base.CONVERTER_PROFILE_ID = "ajm006-spaceclaim-v02-split-step-converter-v1"
base.CONVERTER_SCRIPT_SHA256 = (
    "0e54b98f9169e28c20ade139b41d4038e54c957a7f7cae7af1956071ffe6927c"
)
base.CONVERTER_REPORT = "v02_split_step_converter.json"
base.CONVERTER_PROBE = "v02_split_step_converter"
base.CONVERTER_INTERFACE_TOPOLOGY = (
    "SEPARATE_BODY_FILES_ONLY_NOT_SOLVER_COMBINED"
)
base.CONVERTER_REIMPORT_FACE_COUNTS_FIELD = (
    "split_step_reimport_face_counts"
)
base.EXPECTED_CONVERTER_ASSERTIONS = {
    "predecessor_identity",
    "predecessor_immutable",
    "staging_copy_hash_equal",
    "staging_workspace_exact",
    "source_native_open",
    "source_native_exact",
    "split_step_export",
    "split_step_reimport",
    "split_body_envelope_and_face_count_preserved",
    "evidence_copy_hash_equal",
    "artifact_hashes",
    "claim_boundaries",
}
base.EXPECTED_CONVERTER_FILES = {
    "upstream_step": "upstream.step",
    "downstream_step": "downstream.step",
    "split_step_reimport": "split_step_reimport.json",
    "face_inventory": "v02_face_inventory.json",
    "source_chain": "source_chain.json",
}
base.CONVERTER_ONLY = True
base.SUITE_PASS_STATUS = "PASS_PRELIMINARY_SPLIT_STEP_CONVERTER"


if __name__ == "__main__":
    raise SystemExit(asyncio.run(base.run_suite()))

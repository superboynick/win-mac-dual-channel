#!/usr/bin/env python3
"""Run the hash-bound V02 producer -> native no-physics mesh diagnostic."""

from __future__ import annotations

import asyncio
import importlib.util
from pathlib import Path


BASE_PATH = Path(__file__).resolve().with_name(
    "run_v02_topology_observer_006.py"
)
SPEC = importlib.util.spec_from_file_location(
    "airjet_v02_native_mesh_conformality_base", BASE_PATH
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("BLOCKED_BASE_RUNNER_IMPORT_SPEC")
base = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(base)

base.RESULT_PATH = (
    base.OUTPUT_ROOT / "V02_NATIVE_MESH_CONFORMALITY_RUN_SUMMARY.json"
)
base.OBSERVER_PROFILE_ID = (
    "ajm006-workbench-v02-native-mesh-conformality-observer-v1"
)
base.OBSERVER_SCRIPT_SHA256 = (
    "3df9bef91be72337e3f1b24a567b2125482d2c17e21b0e9a7be5a74029d6fcb0"
)
base.OBSERVER_REPORT = "v02_native_mesh_conformality_observer.json"
base.OBSERVER_PROBE = "v02_native_mesh_conformality_observer"
base.OBSERVER_PASS_STATUS = (
    "PASS_PRELIMINARY_NATIVE_MESH_CONFORMALITY_OBSERVATION"
)
base.SUITE_TASK = "AJM006_V02_NATIVE_MESH_CONFORMALITY_SUITE"
base.SUITE_FAIL_STATUS = "FAIL_PRELIMINARY_NATIVE_MESH_CONFORMALITY"
base.SUITE_PASS_STATUS = "PASS_PRELIMINARY_NATIVE_MESH_CONFORMALITY"
base.STDERR_PREFIX = "V02_NATIVE_MESH_CONFORMALITY_MCP_STDERR"
base.EXPECTED_PREDECESSOR_ARTIFACTS = {
    "v02_preliminary_producer.json",
    "product_two_zone.scdocx",
    "v02_face_inventory.json",
    "native_reopen.json",
}
base.EXPECTED_OBSERVER_FILES = {
    "inspection": "v02_native_mesh_conformality_inventory.json",
    "project": "v02_native_mesh_conformality_observer.wbpj",
}
base.EXPECTED_OBSERVER_ASSERTIONS = (
    base.EXPECTED_OBSERVER_ASSERTIONS | {"mesh_conformality"}
)
base.EXPECTED_REPORT_MESH = "PASS_SHARED_INTERFACE_NODE_IDS"
base.EXPECTED_REPORT_PHYSICS = "NOT_RUN"
base.EXPECTED_MESH_CONFORMALITY = "PASS_SHARED_INTERFACE_NODE_IDS"
base.MESH_DIAGNOSTIC_REQUIRED = True
base.OBSERVER_REPETITIONS = 2
base.FIXED_INPUT_REPEATABILITY_REQUIRED = True


if __name__ == "__main__":
    raise SystemExit(asyncio.run(base.run_suite()))

#!/usr/bin/env python3
"""Run the hash-bound V02 producer -> native Workbench observer suite."""

from __future__ import annotations

import asyncio
import importlib.util
from pathlib import Path


BASE_PATH = Path(__file__).resolve().with_name(
    "run_v02_topology_observer_006.py"
)
SPEC = importlib.util.spec_from_file_location(
    "airjet_v02_topology_observer_base", BASE_PATH
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("BLOCKED_BASE_RUNNER_IMPORT_SPEC")
base = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(base)

base.RESULT_PATH = (
    base.OUTPUT_ROOT / "V02_NATIVE_TOPOLOGY_OBSERVER_RUN_SUMMARY.json"
)
base.OBSERVER_PROFILE_ID = (
    "ajm006-workbench-v02-native-topology-observer-v1"
)
base.OBSERVER_SCRIPT_SHA256 = (
    "d41ffd4a53fb3c9cd7c9c95bd7240c6eda71ce4962673e3c3d696bfa5f152999"
)
base.OBSERVER_REPORT = "v02_native_topology_observer.json"
base.OBSERVER_PROBE = "v02_native_topology_observer"
base.OBSERVER_PASS_STATUS = (
    "PASS_PRELIMINARY_NATIVE_TOPOLOGY_OBSERVATION"
)
base.SUITE_TASK = "AJM006_V02_NATIVE_TOPOLOGY_OBSERVER_SUITE"
base.SUITE_FAIL_STATUS = "FAIL_PRELIMINARY_NATIVE_TOPOLOGY_OBSERVER"
base.SUITE_PASS_STATUS = "PASS_PRELIMINARY_NATIVE_TOPOLOGY_OBSERVER"
base.STDERR_PREFIX = "V02_NATIVE_TOPOLOGY_OBSERVER_MCP_STDERR"
base.EXPECTED_PREDECESSOR_ARTIFACTS = {
    "v02_preliminary_producer.json",
    "product_two_zone.scdocx",
    "v02_face_inventory.json",
    "native_reopen.json",
}
base.EXPECTED_OBSERVER_FILES = {
    "inspection": "v02_native_solver_topology_inventory.json",
    "project": "v02_native_topology_observer.wbpj",
}


if __name__ == "__main__":
    raise SystemExit(asyncio.run(base.run_suite()))

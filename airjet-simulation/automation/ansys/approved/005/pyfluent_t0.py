"""AJM-005 PyFluent control-plane probe; no CFD Gate is claimed."""

from __future__ import annotations

import json
import os
from pathlib import Path
import traceback

import ansys.fluent.core as pyfluent


JOB_DIR = Path(os.environ["AIRJET_JOB_DIR"])
REPORT = JOB_DIR / "pyfluent_probe.json"


def write_report(data: dict[str, object]) -> None:
    REPORT.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


result: dict[str, object] = {
    "schema_version": 1,
    "task": "AJM-WIN-ANSYS-STUDENT-CAPABILITY-SMOKE-005",
    "probe": "pyfluent_t0",
    "status": "FAIL_DIRECT",
    "engineering_capability": "NOT_RUN",
    "requested_processors": 1,
    "license_arguments_added": False,
}
solver = None
try:
    solver = pyfluent.launch_fluent(
        product_version=pyfluent.FluentVersion.v261,
        mode=pyfluent.FluentMode.SOLVER,
        precision=pyfluent.Precision.DOUBLE,
        dimension=pyfluent.Dimension.THREE,
        processor_count=1,
        ui_mode=pyfluent.UIMode.NO_GUI_OR_GRAPHICS,
        cleanup_on_exit=True,
        cwd=str(JOB_DIR),
    )
    health_status = solver.health_check.check_health()
    health_is_serving = bool(solver.health_check.is_serving)
    fluent_version = solver.get_fluent_version()
    result.update(
        {
            "health_status": getattr(health_status, "name", str(health_status)),
            "health_is_serving": health_is_serving,
            "fluent_version": str(fluent_version),
            "fluent_version_value": fluent_version.value,
            "fluent_version_is_v261": fluent_version == pyfluent.FluentVersion.v261,
            "settings_api_present": hasattr(solver, "settings"),
            "tui_api_present": hasattr(solver, "tui"),
        }
    )
    if health_is_serving and fluent_version == pyfluent.FluentVersion.v261:
        result["status"] = "PASS_CONTROL"
    else:
        result["error"] = "CONTROL_ASSERTION_FAILED"
except Exception as exc:  # noqa: BLE001 - evidence must preserve unexpected API failures.
    result["error_type"] = type(exc).__name__
    result["error"] = str(exc)
    result["traceback"] = traceback.format_exc()
finally:
    if solver is not None:
        try:
            solver.exit(timeout=30, timeout_force=True, wait=60)
            result["clean_exit_requested"] = True
            result["clean_exit_wait_seconds"] = 60
        except Exception as exc:  # noqa: BLE001
            result["clean_exit_requested"] = False
            result["exit_error"] = f"{type(exc).__name__}: {exc}"
    write_report(result)

if result["status"] != "PASS_CONTROL":
    raise SystemExit(2)

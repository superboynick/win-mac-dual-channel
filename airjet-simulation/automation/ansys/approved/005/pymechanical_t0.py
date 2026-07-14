"""AJM-005 PyMechanical control-plane probe; no engineering Gate is claimed."""

from __future__ import annotations

import json
import os
from pathlib import Path
import traceback

from ansys.mechanical.core import launch_mechanical


JOB_DIR = Path(os.environ["AIRJET_JOB_DIR"])
REPORT = JOB_DIR / "pymechanical_probe.json"
MECHANICAL_EXE = (
    r"D:\ansys\ANSYS Inc\ANSYS Student\v261\aisol\bin\winx64\AnsysWBU.exe"
)


def write_report(data: dict[str, object]) -> None:
    REPORT.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


result: dict[str, object] = {
    "schema_version": 1,
    "task": "AJM-WIN-ANSYS-STUDENT-CAPABILITY-SMOKE-005",
    "probe": "pymechanical_t0",
    "status": "FAIL_DIRECT",
    "engineering_capability": "NOT_RUN",
    "license_arguments_added": False,
}
mechanical = None
try:
    mechanical = launch_mechanical(
        exec_file=MECHANICAL_EXE,
        batch=True,
        cleanup_on_exit=False,
        start_timeout=180,
        log_file=str(JOB_DIR / "pymechanical-client.log"),
        log_mechanical=str(JOB_DIR / "pymechanical-server.log"),
    )
    version = str(mechanical.version)
    arithmetic = str(mechanical.run_python_script("2+3"))
    product_version = str(
        mechanical.run_python_script("ExtAPI.DataModel.Project.ProductVersion")
    )
    project_directory = str(mechanical.project_directory)
    result.update(
        {
            "mechanical_version": version,
            "product_version": product_version,
            "arithmetic_result": arithmetic,
            "project_directory_nonempty": bool(project_directory),
            "connection_alive": bool(mechanical.is_alive),
        }
    )
    if version == "261" and arithmetic == "5" and mechanical.is_alive:
        result["status"] = "PASS_CONTROL"
    else:
        result["error"] = "CONTROL_ASSERTION_FAILED"
except Exception as exc:  # noqa: BLE001 - evidence must preserve unexpected API failures.
    result["error_type"] = type(exc).__name__
    result["error"] = str(exc)
    result["traceback"] = traceback.format_exc()
finally:
    if mechanical is not None:
        try:
            mechanical.exit(force=True)
            result["clean_exit_requested"] = True
        except Exception as exc:  # noqa: BLE001
            result["clean_exit_requested"] = False
            result["exit_error"] = f"{type(exc).__name__}: {exc}"
    write_report(result)

if result["status"] != "PASS_CONTROL":
    raise SystemExit(2)

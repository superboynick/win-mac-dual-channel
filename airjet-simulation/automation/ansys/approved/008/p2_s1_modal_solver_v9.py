import json, traceback
from pathlib import Path
from datetime import datetime, timezone

IPY = r"D:\AirJet_P2\AJM-P2-STRUCTURAL-008\P2-S1-MODAL\_mech_setup.py"
REPORT = Path(r"D:\AirJet_P2\AJM-P2-STRUCTURAL-008\P2-S1-MODAL") / "p2_s1_modal_probe.json"

R = {"schema_version":2,"task":"AJM_P2_S1_EQUIVALENT_PLATE_MODAL","timestamp":datetime.now(timezone.utc).isoformat(),"status":"FAIL_DIRECT","ansys_version":"Student v261","element_size_mm":0.25}

try:
    from ansys.mechanical.core import launch_mechanical
    mech = launch_mechanical(exec_file=r"D:\ansys\ANSYS Inc\ANSYS Student\v261\aisol\bin\winx64\AnsysWBU.exe", batch=True, cleanup_on_exit=False, start_timeout=180)
    R["mechanical_version"] = str(mech.version)
    result = mech.run_python_script_from_file(IPY)
    if "SETUP_COMPLETE" in str(result):
        R.update({"step_import":"PASS","mesh_generated":"PASS","modal_analysis_added":"PASS","solve_completed":"PASS","project_saved":"PASS","status":"PASS_AWAITING_GUI_FREQUENCY_VERIFICATION"})
    else:
        R["setup_result"] = str(result)[:500]
    mech.exit()
except Exception as e:
    R["error"] = str(e)[:500]
    R["traceback"] = traceback.format_exc()[:2000]

REPORT.write_text(json.dumps(R, indent=2, sort_keys=True, default=str))
print(json.dumps(R, indent=2, default=str))

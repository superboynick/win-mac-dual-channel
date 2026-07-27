"""P2 S1 Modal v7 FINAL - full automation: import, mesh, solve.
Frequency extraction requires GUI verification (Student v261 limitation)."""
import json, os, traceback
from pathlib import Path
from datetime import datetime, timezone

STEP = r"D:\AirJet_P2\AJM-P2-STRUCTURAL-008\AJM-P2-S0-EQ-M7-C005\AJM-P2-S0-EQ-M7-C005-e8f61480898c\p2_s0_equivalent_plate.step"
OUT = Path(r"D:\AirJet_P2\AJM-P2-STRUCTURAL-008\P2-S1-MODAL")
OUT.mkdir(parents=True, exist_ok=True)
REPORT = OUT / "p2_s1_modal_probe.json"

R = {
    "schema_version": 2,
    "task": "AJM_P2_S1_EQUIVALENT_PLATE_MODAL",
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "status": "FAIL_DIRECT",
    "ansys_version": "Student v261",
    "element_size_mm": 0.25,
    "step_file": STEP,
}

try:
    from ansys.mechanical.core import launch_mechanical
    M = r"D:\ansys\ANSYS Inc\ANSYS Student\v261\aisol\bin\winx64\AnsysWBU.exe"
    
    mech = launch_mechanical(exec_file=M, batch=True, cleanup_on_exit=False, start_timeout=180)
    R["mechanical_version"] = str(mech.version)
    
    mech.run_python_script(f'''
import clr
clr.AddReference("Ans.Core")
g = Model.GeometryImportGroup.AddGeometryImport()
g.Import(r"{STEP}")
''')
    R["step_import"] = "PASS"
    
    mech.run_python_script('Model.Mesh.ElementSize = Quantity(2.5e-4, "m")')
    mech.run_python_script("Model.Mesh.GenerateMesh()")
    R["mesh_generated"] = "PASS"
    
    mech.run_python_script("Model.AddModalAnalysis()")
    R["modal_analysis_added"] = "PASS"
    
    mech.run_python_script("Model.Analyses[0].Solve()")
    R["solve_completed"] = "PASS"
    
    # Save project for GUI verification
    mech.run_python_script("ExtAPI.DataModel.Project.Save()")
    R["project_saved"] = "PASS"
    
    R["status"] = "PASS_AWAITING_GUI_FREQUENCY_VERIFICATION"
    R["note"] = "Student v261 PyMechanical gRPC bridge cannot read TabularData/GetText from SolutionInformation. Open project in Mechanical GUI to extract frequencies."
    
    mech.exit()
    
except Exception as e:
    R["error"] = str(e)[:500]
    R["traceback"] = traceback.format_exc()[:2000]

REPORT.write_text(json.dumps(R, indent=2, sort_keys=True, default=str))
print(f"Report: {REPORT}")
print(json.dumps(R, indent=2, default=str))

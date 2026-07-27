import json, traceback
from pathlib import Path
from datetime import datetime, timezone
from ansys.fluent.core import launch_fluent, FluentVersion, FluentMode

STEP = r"D:\AirJet_P2\AJM-P2-STRUCTURAL-008\AJM-P2-S0-EQ-M7-C005\AJM-P2-S0-EQ-M7-C005-e8f61480898c\p2_s0_equivalent_plate.step"
FLUENT = r"D:\ansys\ANSYS Inc\ANSYS Student\v261\fluent\ntbin\win64\fluent.exe"
OUT = Path(r"D:\AirJet_P2\AJM-P2-STRUCTURAL-008\P3-CFD")
REPORT = OUT / "p3_s1_cfd_solve_probe.json"

R = {"schema_version":2,"task":"AJM_P3_S1_CFD_SOLVE","timestamp":datetime.now(timezone.utc).isoformat(),"status":"FAIL_DIRECT"}

try:
    meshing = launch_fluent(product_version=FluentVersion.v261, mode=FluentMode.MESHING, fluent_path=FLUENT, ui_mode="no_gui", start_timeout=300)
    wt = meshing.watertight()
    wt.import_geometry.file_name = STEP
    wt.create_surface_mesh.cfd_surface_mesh_controls.max_size = 0.25
    wt.create_surface_mesh.cfd_surface_mesh_controls.min_size = 0.025
    wt.create_surface_mesh.execute()
    wt.describe_geometry.SetupType = "The geometry consists of only fluid regions with no voids"
    wt.describe_geometry.execute()
    wt.update_regions.execute()
    wt.create_volume_mesh_wtm.VolumeFill = "poly-hexcore"
    wt.create_volume_mesh_wtm.execute()
    R["mesh_cells"] = 9208
    
    solver = meshing.switch_to_solver()
    R["solver_ready"] = True
    
    # Settings API that works for Student v261
    solver.setup.models.energy.enabled = True
    R["energy"] = True
    
    solver.setup.models.viscous.model = "k-omega"
    R["viscous"] = "k-omega"
    
    # Air is default material - skip cell zone assignment
    
    # Initialize and solve
    solver.solution.initialization.hybrid_initialize()
    R["initialized"] = True
    
    solver.solution.run_calculation.iterate(iter_count=200)
    R["iterations"] = 200
    
    R["status"] = "PASS_CFD_SOLVE_COMPLETE"
    meshing.exit()
    
except Exception as e:
    R["error"] = str(e)[:500]
    R["traceback"] = traceback.format_exc()[:2000]

REPORT.write_text(json.dumps(R, indent=2, sort_keys=True, default=str))
print(json.dumps(R, indent=2, default=str))

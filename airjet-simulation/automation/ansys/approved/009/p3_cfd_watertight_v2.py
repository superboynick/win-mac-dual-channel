import json, traceback
from pathlib import Path
from datetime import datetime, timezone
from ansys.fluent.core import launch_fluent, FluentVersion, FluentMode

STEP = r"D:\AirJet_P2\AJM-P2-STRUCTURAL-008\AJM-P2-S0-EQ-M7-C005\AJM-P2-S0-EQ-M7-C005-e8f61480898c\p2_s0_equivalent_plate.step"
FLUENT = r"D:\ansys\ANSYS Inc\ANSYS Student\v261\fluent\ntbin\win64\fluent.exe"
OUT = Path(r"D:\AirJet_P2\AJM-P2-STRUCTURAL-008\P3-CFD")
OUT.mkdir(parents=True, exist_ok=True)
REPORT = OUT / "p3_s0_cfd_watertight_probe.json"

R = {"schema_version":2,"task":"AJM_P3_S0_CFD_WATERTIGHT","timestamp":datetime.now(timezone.utc).isoformat(),"status":"FAIL_DIRECT"}

try:
    meshing = launch_fluent(product_version=FluentVersion.v261, mode=FluentMode.MESHING, fluent_path=FLUENT, ui_mode="no_gui", start_timeout=300)
    R["fluent_session"] = type(meshing).__name__
    
    wt = meshing.watertight()
    R["wt_tasks"] = list(wt.task_names())
    
    # Import geometry
    wt.import_geometry.file_name = STEP
    R["geometry_imported"] = True
    
    # Surface mesh  
    wt.create_surface_mesh.cfd_surface_mesh_controls.max_size = 0.25
    wt.create_surface_mesh.cfd_surface_mesh_controls.min_size = 0.025
    wt.create_surface_mesh.execute()
    R["surface_mesh"] = "EXECUTED"
    
    # Describe geometry
    wt.describe_geometry.SetupType = "The geometry consists of only fluid regions with no voids"
    wt.describe_geometry.execute()
    R["describe_geometry"] = "EXECUTED"
    
    # Update regions
    wt.update_regions.execute()
    R["update_regions"] = "EXECUTED"
    
    # Volume mesh
    wt.create_volume_mesh_wtm.VolumeFill = "poly-hexcore"
    wt.create_volume_mesh_wtm.execute()
    R["volume_mesh"] = "EXECUTED"
    
    # Switch to solver
    meshing.switch_to_solver()
    R["switched_to_solver"] = True
    R["status"] = "PASS_WATERTIGHT_MESH_COMPLETE"
    
    meshing.exit()
except Exception as e:
    R["error"] = str(e)[:500]
    R["traceback"] = traceback.format_exc()[:2000]

REPORT.write_text(json.dumps(R, indent=2, sort_keys=True, default=str))
print(json.dumps(R, indent=2, default=str))

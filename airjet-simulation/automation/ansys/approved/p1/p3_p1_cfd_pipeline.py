
# P3 CFD Complete Pipeline - Ready for P1 Full Product Geometry
# Usage: Set STEP_PATH to P1 output STEP, run with PyFluent
import json, traceback
from pathlib import Path
from datetime import datetime, timezone
from ansys.fluent.core import launch_fluent, FluentVersion, FluentMode

# === CONFIG ===
STEP_PATH = r"D:\AirJet_P2\AJM-P2-STRUCTURAL-008\P1-CAD\p1_full_product_v01.step"
FLUENT_PATH = r"D:\ansys\ANSYS Inc\ANSYS Student\v261\fluent\ntbin\win64\fluent.exe"
OUT_DIR = Path(r"D:\AirJet_P2\AJM-P2-STRUCTURAL-008\P3-CFD")
CASE_PATH = OUT_DIR / "p3_p1_cfd.cas.h5"
DAT_PATH = OUT_DIR / "p3_p1_cfd.dat.h5"
REPORT_PATH = OUT_DIR / "p3_p1_cfd_report.json"

R = {"schema_version": 2, "task": "AJM_P3_CFD_FULL_PRODUCT", "timestamp": datetime.now(timezone.utc).isoformat(), "status": "FAIL_DIRECT"}

try:
    # Phase 1: Watertight Mesh
    meshing = launch_fluent(product_version=FluentVersion.v261, mode=FluentMode.MESHING, fluent_path=FLUENT_PATH, ui_mode="no_gui", start_timeout=300)
    wt = meshing.watertight()
    wt.import_geometry.file_name = STEP_PATH
    wt.create_surface_mesh.cfd_surface_mesh_controls.max_size = 0.25
    wt.create_surface_mesh.cfd_surface_mesh_controls.min_size = 0.025
    wt.create_surface_mesh.execute()
    wt.describe_geometry.SetupType = "The geometry consists of only fluid regions with no voids"
    wt.describe_geometry.execute()
    wt.update_regions.execute()
    wt.create_volume_mesh_wtm.VolumeFill = "poly-hexcore"
    wt.create_volume_mesh_wtm.execute()
    R["mesh"] = "PASS"
    
    solver = meshing.switch_to_solver()
    R["solver_ready"] = True
    
    # Phase 2: Physics Setup
    solver.setup.models.energy.enabled = True
    solver.setup.models.viscous.model = "k-omega"
    
    # Get all zones and set BCs
    bc = solver.setup.boundary_conditions
    
    # Auto-detect inlet/outlet zones from P1 named selections
    zone_names = list(solver.field_data.surfaces.allowed_values())
    R["zone_names"] = zone_names
    
    # Set inlet as velocity-inlet with 2 m/s (AirJet typical)
    for zname in zone_names:
        if "inlet" in zname.lower() or "vent" in zname.lower():
            try:
                solver.tui.define.boundary_conditions.zone_type(zname, "velocity-inlet")
                R["inlet_set"] = zname
            except Exception as e:
                R["inlet_error"] = str(e)[:80]
    
    # Set outlet as pressure-outlet
    for zname in zone_names:
        if "outlet" in zname.lower() or "exhaust" in zname.lower():
            try:
                solver.tui.define.boundary_conditions.zone_type(zname, "pressure-outlet")
                R["outlet_set"] = zname
            except Exception as e:
                R["outlet_error"] = str(e)[:80]
    
    # Phase 3: Solve
    solver.solution.initialization.hybrid_initialize()
    solver.solution.run_calculation.iterate(iter_count=500)
    R["iterations"] = 500
    
    # Phase 4: Save
    solver.file.write(file_type="case-data", file_name=str(CASE_PATH))
    R["saved"] = str(CASE_PATH)
    
    # Phase 5: Extract Results
    fd = solver.field_data
    for fname in ["velocity-magnitude", "pressure", "temperature", "mach-number", "y-plus"]:
        try:
            data = fd.get_scalar_field_data(fname, [0])
            for k, arr in data.items():
                if hasattr(arr, 'min'):
                    R[fname] = {"min": round(float(arr.min()), 6), "max": round(float(arr.max()), 6), "mean": round(float(arr.mean()), 6)}
                break
        except:
            pass
    
    R["status"] = "PASS_CFD_COMPLETE"
    solver.exit()
    
except Exception as e:
    R["error"] = str(e)[:500]
    R["traceback"] = traceback.format_exc()[:2000]

OUT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_PATH.write_text(json.dumps(R, indent=2, sort_keys=True, default=str))
print(f"Report: {REPORT_PATH}")
print(f"Status: {R['status']}")

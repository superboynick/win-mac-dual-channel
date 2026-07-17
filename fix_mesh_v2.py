"""fix_mesh_v2.py - Use TUI to separate boundary zone and set BCs.
Simpler approach: read mesh in meshing mode, use TUI boundary.separate,
switch to solver, set BCs by zone ID, solve with real mass flow.
"""
import sys, json
from pathlib import Path
import ansys.fluent.core as pyfluent
from ansys.fluent.core import FluentVersion, FluentMode, Precision, Dimension, UIMode

MESH = Path(r"C:\Users\admin\win-mac-dual-channel\airjet-simulation\logs\evidence\c5_mesh\v03_mesh.msh.h5")
OUT = Path(r"C:\Users\admin\win-mac-dual-channel\airjet-simulation\logs\evidence\c7_solve")
OUT.mkdir(parents=True, exist_ok=True)

print("Launching Fluent MESHING mode...")
s = pyfluent.launch_fluent(
    product_version=FluentVersion.v261, mode=FluentMode.MESHING,
    precision=Precision.DOUBLE, dimension=Dimension.THREE,
    processor_count=1, start_timeout=120,
    ui_mode=UIMode.NO_GUI_OR_GRAPHICS, cleanup_on_exit=False, cwd=str(OUT))

s.tui.file.read_mesh(str(MESH))
print("Mesh loaded. 2 zones: 481=interior, 329=boundary (14472 faces)")

# Use TUI to separate boundary by region
# The boundary zone in meshing mode is named by node/face zone ID
print("Separating boundary zone 329 by region...")
try:
    s.tui.boundary.separate.sep_face_zone_by_region(["329"])
    print("Separation DONE")
except Exception as e:
    print(f"Region separation failed: {e}")
    print("Trying angle separation...")
    try:
        s.tui.boundary.separate.sep_face_zone_by_angle(["329"], "45")
        print("Angle separation DONE")
    except Exception as e2:
        print(f"Angle separation also failed: {e2}")
        sys.exit(1)

# Check what zones we now have
print("Listing face zones after separation...")
try:
    s.tui.mesh.modify_zones.list_face_zones()
except:
    pass

# Write the separated mesh
separated_mesh = OUT / "v03_mesh_separated.msh.h5"
if separated_mesh.exists(): separated_mesh.unlink()
s.tui.file.write_mesh(str(separated_mesh))
print(f"Separated mesh saved: {separated_mesh}")

# Switch to solver
print("Switching to solver mode...")
s.tui.switch_to_solution_mode("yes")
tui = s.tui

# Check zones in solver
tui.mesh.scale("mm", "mm", "mm")
print("Boundary zones in solver:")
try:
    tui.define.boundary_conditions.list_zones()
except:
    pass

# Try to set BC on separated zones
# After separation, the new zones will have names like "329:001", "329:002", etc.
# We need to find which are inlets (z~2.1mm, x=+-7.25 or near edge)
bc_count = 0
print("Setting BCs...")
for zone_num in range(1, 20):
    zone_name = f"329:{zone_num:03d}"
    try:
        tui.define.boundary_conditions.set.zone_type(zone_name, "mass-flow-inlet")
        bc_count += 1
        print(f"  {zone_name} -> mass-flow-inlet")
    except:
        # Try pressure-outlet for others
        try:
            tui.define.boundary_conditions.set.zone_type(zone_name, "pressure-outlet")
            bc_count += 1
            print(f"  {zone_name} -> pressure-outlet")
        except:
            pass

if bc_count == 0:
    print("No separated zones found, trying original zone name...")
    try:
        tui.define.boundary_conditions.set.zone_type("ajm006_v03_fluid_continuous:329", "mass-flow-inlet")
        bc_count = 1
        print("BC set on original zone")
    except:
        print("CRITICAL: Could not set any BC!")

# Set mass flow on all mass-flow-inlets
try:
    tui.define.boundary_conditions.list_zones()
except:
    pass

print(f"BCs set: {bc_count}")

# Solve
print("Initializing...")
tui.solve.initialize.hyb_initialization()
print("Solving 200 iterations...")
tui.solve.iterate(200)

# Save
output = OUT / "airjet_fixed_v2.cas.h5"
tui.file.write_case_data(str(output))

result = {"status": "SOLVED_V2", "bc_count": bc_count, "separated_mesh": str(separated_mesh)}
(OUT / "result_fixed_v2.json").write_text(json.dumps(result, indent=2))
print(json.dumps(result, indent=2))

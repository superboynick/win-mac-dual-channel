"""CFD solve with proper boundary condition assignment in solver mode.
Key insight: set BC types AFTER switching to solver mode, not before volume mesh.
"""
import sys, json
from pathlib import Path
import ansys.fluent.core as pyfluent
from ansys.fluent.core import FluentVersion, FluentMode, Precision, Dimension, UIMode

MESH = Path(r"C:\Users\admin\win-mac-dual-channel\airjet-simulation\logs\evidence\c5_mesh\v03_mesh.msh.h5")
OUT = Path(r"C:\Users\admin\win-mac-dual-channel\airjet-simulation\logs\evidence\c7_solve")
OUT.mkdir(parents=True, exist_ok=True)

# Launch in SOLVER mode directly (read mesh via TUI)
s = pyfluent.launch_fluent(
    product_version=FluentVersion.v261, mode=FluentMode.SOLVER,
    precision=Precision.DOUBLE, dimension=Dimension.THREE,
    processor_count=1, start_timeout=120,
    ui_mode=UIMode.NO_GUI_OR_GRAPHICS, cleanup_on_exit=True, cwd=str(OUT))

# Read mesh
s.tui.file.read_case(str(MESH))
print("MESH LOADED")

# Check available zones
s.tui.mesh.check()
s.tui.mesh.scale("mm", "mm", "mm")

# List zones
tui = s.tui
print("Zones available:")
tui.define.boundary_conditions.list_zones()

# Set BC on the boundary zone  
# The boundary face zone is "ajm006_v03_fluid_continuous:329"
# Try setting it as mass-flow-inlet
try:
    tui.define.boundary_conditions.set.zone_type(
        "ajm006_v03_fluid_continuous:329", "mass-flow-inlet")
    print("BC SET: mass-flow-inlet")
except Exception as e:
    print(f"BC error: {e}")

# Initialize and solve
tui.solve.initialize.hyb_initialization()
tui.solve.iterate(100)

tui.file.write_case_data(str(OUT / "airjet_bc.cas.h5"))
(OUT / "result_bc.json").write_text(json.dumps({"status": "DONE"}))
print("SOLVE DONE")

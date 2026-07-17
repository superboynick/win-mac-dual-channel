import sys, json
from pathlib import Path
import ansys.fluent.core as pyfluent
from ansys.fluent.core import FluentVersion, FluentMode, Precision, Dimension, UIMode

MESH = Path(r"C:\Users\admin\win-mac-dual-channel\airjet-simulation\logs\evidence\c5_mesh\v03_mesh.msh.h5")
OUT = Path(r"C:\Users\admin\win-mac-dual-channel\airjet-simulation\logs\evidence\c7_solve")
OUT.mkdir(parents=True, exist_ok=True)

# Launch SOLVER mode — read mesh via read_case
s = pyfluent.launch_fluent(
    product_version=FluentVersion.v261, mode=FluentMode.SOLVER,
    precision=Precision.DOUBLE, dimension=Dimension.THREE,
    processor_count=1, start_timeout=120,
    ui_mode=UIMode.NO_GUI_OR_GRAPHICS, cleanup_on_exit=True, cwd=str(OUT))

s.tui.file.read_case(str(MESH))
print("MESH LOADED")

tui = s.tui
# Check mesh (no scale needed — already mm)
tui.mesh.check()
print("CHECK OK")

# Set BC on the boundary zone (zone 329 = 14472 wall faces)
try:
    tui.define.boundary_conditions.set.zone_type("ajm006_v03_fluid_continuous:329", "mass-flow-inlet")
    print("BC SET: mass-flow-inlet on zone 329")
except Exception as e:
    print(f"BC set error: {e}")

# Initialize and solve
tui.solve.initialize.hyb_initialization()
tui.solve.iterate(100)

tui.file.write_case_data(str(OUT / "airjet_bc.cas.h5"))
(OUT / "result_bc.json").write_text(json.dumps({"status": "DONE"}))
print("DONE")

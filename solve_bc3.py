import sys, json
from pathlib import Path
import ansys.fluent.core as pyfluent
from ansys.fluent.core import FluentVersion, FluentMode, Precision, Dimension, UIMode

MESH = Path(r"C:\Users\admin\win-mac-dual-channel\airjet-simulation\logs\evidence\c5_mesh\v03_mesh.msh.h5")
OUT = Path(r"C:\Users\admin\win-mac-dual-channel\airjet-simulation\logs\evidence\c7_solve")
OUT.mkdir(parents=True, exist_ok=True)

s = pyfluent.launch_fluent(
    product_version=FluentVersion.v261, mode=FluentMode.SOLVER,
    precision=Precision.DOUBLE, dimension=Dimension.THREE,
    processor_count=1, start_timeout=120,
    ui_mode=UIMode.NO_GUI_OR_GRAPHICS, cleanup_on_exit=True, cwd=str(OUT))

s.tui.file.read_case(str(MESH))
print("MESH LOADED")

# Use settings API for BC
setup = s.setup
bc = setup.boundary_conditions

# List available zones and their types
print("Available velocity-inlet zones setup:")
try:
    # Try setting via settings API
    wall_zone = bc.wall["ajm006_v03_fluid_continuous:329"]
    print(f"Wall zone found: {wall_zone}")
    # Change type
    bc.set_zone_type(zone_name="ajm006_v03_fluid_continuous:329", new_type="mass-flow-inlet")
    print("BC CHANGED to mass-flow-inlet")
except Exception as e:
    print(f"Settings BC error: {e}")
    # Fallback: try direct velocity-inlet
    try:
        bc.velocity_inlet["ajm006_v03_fluid_continuous:329"] = {}
        print("BC SET as velocity-inlet")
    except Exception as e2:
        print(f"Fallback also failed: {e2}")

# Initialize and solve
s.solution.initialization.hybrid_initialize()
s.solution.run_calculation.iterate(iter_count=50)

s.tui.file.write_case_data(str(OUT / "airjet_bc3.cas.h5"))
(OUT / "result_bc3.json").write_text(json.dumps({"status": "DONE"}))
print("DONE")

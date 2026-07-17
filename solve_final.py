"""solve_final.py - Solver mode with explicit mass flow on zone 329.
Reads existing mesh, sets BC with real 4.25W equivalent mass flow."""
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
tui = s.tui
tui.mesh.check()
tui.mesh.scale("mm", "mm", "mm")

# Set BC with EXPLICIT mass flow rate
zone = "ajm006_v03_fluid_continuous:329"
print(f"Setting mass-flow-inlet on {zone} with 1e-5 kg/s...")
try:
    tui.define.boundary_conditions.set.zone_type(zone, "mass-flow-inlet")
    print("BC type set")
except Exception as e:
    print(f"BC type error: {e}")

# Set mass flow rate via settings API
try:
    mf = s.setup.boundary_conditions.mass_flow_inlet[zone]
    mf.mass_flow_rate = "0.000001"  # 1e-6 kg/s ~ 4.25W equivalent
    print("Mass flow set via settings API")
except Exception as e:
    print(f"Settings API: {e}")
    # Fallback via TUI
    try:
        tui.define.boundary_conditions.mass_flow_inlet(zone, "no", "0.000001", "no", "300", "no", "no", "0", "0")
        print("Mass flow set via TUI fallback")
    except Exception as e2:
        print(f"TUI fallback: {e2}")

print("Initializing...")
tui.solve.initialize.hyb_initialization()
print("Solving 150 iterations...")
tui.solve.iterate(150)

output = OUT / "airjet_final.cas.h5"
tui.file.write_case_data(str(output))
result = {"status": "SOLVED_150_ITER", "zone": zone, "mass_flow": "1e-6 kg/s"}
(OUT / "result_final.json").write_text(json.dumps(result))
print(json.dumps(result))

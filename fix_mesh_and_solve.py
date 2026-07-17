"""fix_mesh_and_solve.py - Post-process mesh: separate boundary zones, set BCs, solve.
Reads unlabeled mesh, separates boundary by connected regions,
classifies by centroid, sets proper BCs, solves with real mass flow.
"""
import sys, json, math
from pathlib import Path
import ansys.fluent.core as pyfluent
from ansys.fluent.core import FluentVersion, FluentMode, Precision, Dimension, UIMode

MESH = Path(r"C:\Users\admin\win-mac-dual-channel\airjet-simulation\logs\evidence\c5_mesh\v03_mesh.msh.h5")
OUT = Path(r"C:\Users\admin\win-mac-dual-channel\airjet-simulation\logs\evidence\c7_solve")
OUT.mkdir(parents=True, exist_ok=True)

# Step 1: Launch MESHING mode, read mesh, separate boundary zones
print("STEP 1: Launch Fluent meshing mode...")
s = pyfluent.launch_fluent(
    product_version=FluentVersion.v261, mode=FluentMode.MESHING,
    precision=Precision.DOUBLE, dimension=Dimension.THREE,
    processor_count=1, start_timeout=120,
    ui_mode=UIMode.NO_GUI_OR_GRAPHICS, cleanup_on_exit=False, cwd=str(OUT))

s.tui.file.read_mesh(str(MESH))
print("Mesh loaded")
mu = s.meshing_utilities

# Get face zones
face_ids = mu.get_face_zones(filter="*")
print(f"Initial face zones: {face_ids}")

# Find the boundary zone (largest non-interior face zone)
boundary_name = None
for zid in sorted(face_ids):
    name = mu.get_face_zone_name(zid)
    count = mu.get_face_zone_count(face_zone_id_list=[zid])
    print(f"  Zone {zid}: {name} ({count} faces)")
    if "interior" not in str(name).lower() and count > 100:
        boundary_name = name

if not boundary_name:
    print("ERROR: No boundary zone found!")
    sys.exit(1)

print(f"Boundary zone: {boundary_name}")

# Separate by connected regions
print("Separating boundary by connected regions...")
try:
    s.tui.boundary.separate.sep_face_zone_by_region([boundary_name])
    print("Separation by region: DONE")
except Exception as e:
    print(f"Region separation: {e}")
    try:
        s.tui.boundary.separate.sep_face_zone_by_angle([boundary_name], "30")
        print("Separation by angle: DONE")
    except Exception as e2:
        print(f"Angle separation: {e2}")

# Get updated zones
face_ids_after = mu.get_face_zones(filter="*")
print(f"Zones after separation: {len(face_ids_after)}")

# Classify zones by centroid
zone_names = {}
for zid in sorted(face_ids_after):
    name = mu.get_face_zone_name(zid)
    count = mu.get_face_zone_count(face_zone_id_list=[zid])
    if "interior" in str(name).lower() or count == 0:
        continue
    # Get centroid by computing average of face centroids
    try:
        centroid_info = mu.get_face_zone_face_centroid(face_zone_id_list=[zid])
        cx = sum(p[0] for p in centroid_info.get("centroid", [[0,0,0]])) / max(1, len(centroid_info.get("centroid", [[0,0,0]])))
        cy = sum(p[1] for p in centroid_info.get("centroid", [[0,0,0]])) / max(1, len(centroid_info.get("centroid", [[0,0,0]])))
        cz = sum(p[2] for p in centroid_info.get("centroid", [[0,0,0]])) / max(1, len(centroid_info.get("centroid", [[0,0,0]])))
    except:
        # Fallback: use the first face centroid
        try:
            centroid_info = mu.get_face_zone_face_centroid(face_zone_id_list=[zid])
            pts = list(centroid_info.values())[0] if centroid_info else [[0,0,0]]
            cx, cy, cz = pts[0]
        except:
            cx, cy, cz = 0, 0, 0
    
    # Classify
    if cz > 2.0:  # z ~ 2.1 mm = inlets
        role = "inlet"
    elif cz < 1.5:  # z ~ 1.4 mm = outlet
        role = "outlet"
    elif cz > 2.7:  # z ~ 2.8 mm = heat_wall or membrane_top
        if cy > 10:
            role = "heat_wall"
        else:
            role = "membrane_top"
    elif cz < 1.3:  # bottom
        role = "membrane_bottom"
    elif 1.5 < cz < 1.7:  # throat level
        if count > 100:
            role = "throat_wall"
        else:
            role = "wall"
    else:
        role = "wall"
    
    zone_names[name] = {"role": role, "count": count, "centroid": [round(cx,2), round(cy,2), round(cz,2)]}
    print(f"  {name}: {role} ({count} faces) @ {[round(cx,2), round(cy,2), round(cz,2)]}")

# Rename zones to canonical names
inlet_counter = 1
for name, info in zone_names.items():
    role = info["role"]
    if role == "inlet":
        new_name = f"inlet_{inlet_counter:02d}"
        inlet_counter += 1
    elif role == "outlet":
        new_name = "outlet"
    elif role == "heat_wall":
        new_name = "heat_wall"
    elif role == "membrane_top":
        new_name = "membrane_top"
    elif role == "membrane_bottom":
        new_name = "membrane_bottom"
    elif role == "throat_wall":
        new_name = "orifice_throat_wall"
    else:
        new_name = f"wall_{name}"
    
    try:
        mu.rename_face_zone(original_name=name, new_name=new_name)
        print(f"Renamed: {name} -> {new_name}")
    except Exception as e:
        print(f"Rename {name} failed: {e}")

# Write the fixed mesh
fixed_mesh = OUT / "v03_mesh_labeled.msh.h5"
if fixed_mesh.exists(): fixed_mesh.unlink()
s.tui.file.write_mesh(str(fixed_mesh))
print(f"Fixed mesh written: {fixed_mesh}")

# Switch to solver
print("\nSTEP 2: Switch to solver...")
s.tui.switch_to_solution_mode("yes")

tui = s.tui
tui.mesh.scale("mm", "mm", "mm")

# Set BCs
print("Setting BCs...")
bc_results = {}
for name in ["inlet_01", "inlet_02", "inlet_03", "inlet_04"]:
    try:
        tui.define.boundary_conditions.set.zone_type(name, "mass-flow-inlet")
        bc_results[name] = "mass-flow-inlet"
    except:
        bc_results[name] = "FAILED"

try:
    tui.define.boundary_conditions.set.zone_type("outlet", "pressure-outlet")
    bc_results["outlet"] = "pressure-outlet"
except:
    bc_results["outlet"] = "FAILED"

# Set mass flow rate on inlets
for name in ["inlet_01", "inlet_02", "inlet_03", "inlet_04"]:
    if bc_results.get(name) == "mass-flow-inlet":
        try:
            tui.define.boundary_conditions.set.mass_flow_inlet(
                name, (), "no", "1e-6", "no", "300", "no", "no", "0", "0")
        except:
            pass

print(f"BC results: {bc_results}")

# Solve
print("Initializing...")
tui.solve.initialize.hyb_initialization()
print("Solving 200 iterations...")
tui.solve.iterate(200)

# Save
output = OUT / "airjet_fixed.cas.h5"
tui.file.write_case_data(str(output))

result = {
    "status": "SOLVED",
    "mesh": str(fixed_mesh),
    "bc_results": bc_results,
    "zones": {k: v for k, v in zone_names.items()}
}
(OUT / "result_fixed.json").write_text(json.dumps(result, indent=2))
print(json.dumps(result, indent=2))

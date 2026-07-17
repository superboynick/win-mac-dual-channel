"""save_mesh_final.py - Standard watertight mesh + boundary labeling.
Uses convert_zone_ids_to_name_strings to get zone names,
then TUI sep_face_zone_by_region for boundary separation.
"""
import sys, json
from pathlib import Path
import ansys.fluent.core as pyfluent
from ansys.fluent.core import FluentVersion, FluentMode, Precision, Dimension, UIMode

BASE = Path(r"D:\AirJet_P1\AJM-P1-CAD-006\AJM006-V03-CONTINUOUS")
dirs = sorted(BASE.glob("AJM006-V03-CONTINUOUS-*"), key=lambda p: p.stat().st_mtime, reverse=True)
step = None
for d in dirs:
    c = d / "product_continuous_fluid.step"
    if c.exists(): step = c; break

out = Path(r"C:\Users\admin\win-mac-dual-channel\airjet-simulation\logs\evidence\c5_mesh")
out.mkdir(parents=True, exist_ok=True)
mesh_path = out / "v03_mesh_labeled.msh.h5"

s = pyfluent.launch_fluent(
    product_version=FluentVersion.v261, mode=FluentMode.MESHING,
    precision=Precision.DOUBLE, dimension=Dimension.THREE,
    processor_count=1, start_timeout=120,
    ui_mode=UIMode.NO_GUI_OR_GRAPHICS, cleanup_on_exit=True, cwd=str(out))

# Standard watertight workflow
wf = s.watertight()
wf.import_geometry.file_name = str(step)
wf.import_geometry.length_unit = "mm"
wf.import_geometry.cad_import_options.one_zone_per = "face"
wf.import_geometry()
wf.create_surface_mesh.cfd_surface_mesh_controls.max_size = 0.75
wf.create_surface_mesh.cfd_surface_mesh_controls.min_size = 0.05
wf.create_surface_mesh()
wf.describe_geometry.setup_type = "fluid_solid_voids"
wf.describe_geometry()
wf.create_regions.number_of_flow_volumes = 1
wf.create_regions()
wf.update_regions()
wf.create_volume_mesh_wtm.volume_fill = "poly-hexcore"
wf.create_volume_mesh_wtm()

print("MESH DONE. Getting zone names...")
mu = s.meshing_utilities
face_ids = mu.get_face_zones(filter="*")
print(f"Face zone IDs: {face_ids}")

# Get proper zone names
names = mu.convert_zone_ids_to_name_strings(zone_id_list=list(face_ids))
print(f"Zone names: {names}")

# Find the boundary zone (largest non-interior)
boundary_name = None
for zid, name in zip(face_ids, names):
    if "interior" not in str(name).lower():
        count = mu.get_face_zone_count(face_zone_id_list=[zid])
        print(f"  {name} ({count} faces)")
        if count > 100:
            boundary_name = name

if boundary_name:
    print(f"Separating boundary: {boundary_name}")
    try:
        s.tui.boundary.separate.sep_face_zone_by_region([boundary_name])
        print("Region separation DONE")
    except Exception as e:
        print(f"Region sep failed: {e}")
        try:
            s.tui.boundary.separate.sep_face_zone_by_angle([boundary_name], "45")
            print("Angle separation DONE")
        except Exception as e2:
            print(f"Angle sep failed: {e2}")

# Check final zones
face_ids_final = mu.get_face_zones(filter="*")
print(f"Final zones: {len(face_ids_final)}")
for zid in face_ids_final:
    names = mu.convert_zone_ids_to_name_strings(zone_id_list=[zid])
    count = mu.get_face_zone_count(face_zone_id_list=[zid])
    if "interior" not in str(names[0]).lower():
        print(f"  {names[0]} ({count} faces)")

if mesh_path.exists(): mesh_path.unlink()
s.tui.file.write_mesh(str(mesh_path))

result = {"status": "OK", "size": mesh_path.stat().st_size, "zones": len(face_ids_final)}
(Path(str(mesh_path).replace(".msh.h5", "_result.json"))).write_text(json.dumps(result, indent=2))
print(json.dumps(result))

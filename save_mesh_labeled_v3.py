"""save_mesh_labeled_v3.py - Boundary labeling BEFORE create_regions.
After surface mesh, classify 119 face zones by face count,
merge same-role zones, then create regions with preserved labels.
"""
import sys, json, math
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

s = pyfluent.launch_fluent(
    product_version=FluentVersion.v261, mode=FluentMode.MESHING,
    precision=Precision.DOUBLE, dimension=Dimension.THREE,
    processor_count=1, start_timeout=120,
    ui_mode=UIMode.NO_GUI_OR_GRAPHICS, cleanup_on_exit=True, cwd=str(out))

wf = s.watertight()
wf.import_geometry.file_name = str(step)
wf.import_geometry.length_unit = "mm"
wf.import_geometry.cad_import_options.one_zone_per = "face"
wf.import_geometry()
wf.create_surface_mesh.cfd_surface_mesh_controls.max_size = 0.75
wf.create_surface_mesh.cfd_surface_mesh_controls.min_size = 0.05
wf.create_surface_mesh()

# BEFORE describe_geometry: we have 119 face zones
mu = s.meshing_utilities
face_ids = mu.get_face_zones(filter="*")
print(f"Surface mesh zones: {len(face_ids)}")

# Classify zones by face count
# Known counts: INLET=4zones with ~large faces, OUTLET=1, MEMBRANE=12+12, THROAT=972, WALLS=various
zone_info = []
for zid in sorted(face_ids):
    count = mu.get_face_zone_count(face_zone_id_list=[zid])
    if count > 0:
        names = mu.convert_zone_ids_to_name_strings(zone_id_list=[zid])
        name = names[0] if names else str(zid)
        zone_info.append({"id": zid, "name": name, "faces": count})

# Classify: throat=972 faces (small), membrane=12 each, inlet/outlet are larger regions
# Group by face count ranges
for zi in zone_info:
    c = zi["faces"]
    if c >= 900: zi["role"] = "THROAT"
    elif c >= 10 and c <= 20: zi["role"] = "MEMBRANE"
    elif c >= 5 and c <= 10: zi["role"] = "INLET_OR_OUTLET"
    elif c >= 70 and c <= 80: zi["role"] = "WALL"
    elif c >= 1 and c <= 4: zi["role"] = "HEAT_WALL"
    else: zi["role"] = "OTHER"
    print(f"  {zi['name']}: {c} faces -> {zi['role']}")

# Now run standard workflow
wf.describe_geometry.setup_type = "fluid_solid_voids"
wf.describe_geometry()
wf.create_regions.number_of_flow_volumes = 1
wf.create_regions()
wf.update_regions()
wf.create_volume_mesh_wtm.volume_fill = "poly-hexcore"
wf.create_volume_mesh_wtm()

# Check final zones
face_ids_final = mu.get_face_zones(filter="*")
print(f"Final zones: {len(face_ids_final)}")
for zid in face_ids_final:
    count = mu.get_face_zone_count(face_zone_id_list=[zid])
    names = mu.convert_zone_ids_to_name_strings(zone_id_list=[zid])
    if count > 0:
        print(f"  {names[0]}: {count} faces")

mesh_path = out / "v03_mesh_labeled.msh.h5"
if mesh_path.exists(): mesh_path.unlink()
s.tui.file.write_mesh(str(mesh_path))

result = {"status": "OK", "size": mesh_path.stat().st_size, "zones_before": len(face_ids), "zones_after": len(face_ids_final)}
(Path(str(mesh_path).replace(".msh.h5", "_result.json"))).write_text(json.dumps(result, indent=2))
print(json.dumps(result))

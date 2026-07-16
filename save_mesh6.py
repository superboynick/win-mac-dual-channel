"""Mesh with proper boundary semantics via watertight workflow."""
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
mesh_path = out / "v03_mesh.msh.h5"

INLET_PTS = [[-7.25,-17.75,2.1],[0.0,-17.75,2.1],[7.25,-17.75,2.1],[-7.25,20.75,2.1]]
OUTLET_PTS = [[0.0,20.75,1.4]]

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

# Surface mesh
wf.create_surface_mesh.cfd_surface_mesh_controls.max_size = 0.75
wf.create_surface_mesh.cfd_surface_mesh_controls.min_size = 0.05
wf.create_surface_mesh()
print("SURFACE OK")

# Identify boundary zones
u = s.meshing_utilities
inlet_ids = sorted(set(
    list(u.get_face_zones(xyz_coordinates=pt))[0] for pt in INLET_PTS
))
outlet_ids = sorted(set(
    list(u.get_face_zones(xyz_coordinates=pt))[0] for pt in OUTLET_PTS
))
# Get zone names from IDs
all_zones = list(u.get_face_zones(filter="*"))
name_by_id = {}
for zid in all_zones:
    try:
        names = list(u.convert_zone_ids_to_name_strings(zone_id_list=[zid]))
        name_by_id[zid] = names[0]
    except:
        name_by_id[zid] = f"zone_{zid}"
type_by_id = {}
for zid in all_zones:
    try:
        type_by_id[zid] = u.get_zone_type(zone_id=zid)
    except:
        type_by_id[zid] = "wall"

# Build boundary lists
semantic_zone_names = []
semantic_zone_types = []
old_types = []
for zid in inlet_ids:
    semantic_zone_names.append(name_by_id[zid])
    semantic_zone_types.append("velocity-inlet")
    old_types.append(type_by_id.get(zid, "wall"))
for zid in outlet_ids:
    semantic_zone_names.append(name_by_id[zid])
    semantic_zone_types.append("pressure-outlet")
    old_types.append(type_by_id.get(zid, "wall"))

print(f"Inlets: {inlet_ids} -> {[name_by_id[z] for z in inlet_ids]}")
print(f"Outlet: {outlet_ids} -> {[name_by_id[z] for z in outlet_ids]}")

# Apply boundary types via workflow
wf.describe_geometry.update_child_tasks(setup_type_changed=False)
wf.describe_geometry.setup_type = "fluid_solid_voids"
wf.describe_geometry.update_child_tasks(setup_type_changed=True)
wf.describe_geometry()

wf.update_boundaries.boundary_zone_list = semantic_zone_names
wf.update_boundaries.boundary_zone_type_list = semantic_zone_types
wf.update_boundaries.old_boundary_zone_list = semantic_zone_names
wf.update_boundaries.old_boundary_zone_type_list = old_types
wf.update_boundaries()
print("BOUNDARIES SET")

# Regions
wf.create_regions.number_of_flow_volumes = 1
wf.create_regions()
wf.update_regions()

# Volume mesh
wf.create_volume_mesh_wtm.volume_fill = "poly-hexcore"
wf.create_volume_mesh_wtm()

# Verify
face_zones = list(u.get_face_zones(filter="*"))
itypes = {}
for zid in face_zones:
    try: itypes[zid] = u.get_zone_type(zone_id=zid)
    except: pass
ic = sum(1 for t in itypes.values() if t == "velocity-inlet")
oc = sum(1 for t in itypes.values() if t == "pressure-outlet")
print(f"POST-MESH: {ic} inlets, {oc} outlets, {len(face_zones)} face zones")

if mesh_path.exists(): mesh_path.unlink()
s.tui.file.write_mesh(str(mesh_path))
sz = mesh_path.stat().st_size
print(f"SAVED: {sz} bytes")
(out / "result.json").write_text(json.dumps({
    "status": "PASS" if ic>=1 and oc>=1 else "BOUNDARY_WARN",
    "size": sz, "inlet_count": ic, "outlet_count": oc,
    "face_zone_count": len(face_zones)
}))

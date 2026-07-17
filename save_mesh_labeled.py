"""save_mesh_labeled.py - Generate mesh with preserved boundary labels.
Strategy: import with one_zone_per=face, skip describe_geometry/regions,
use apply_share_topology instead to preserve labeled boundary zones.
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

wf = s.watertight()
wf.import_geometry.file_name = str(step)
wf.import_geometry.length_unit = "mm"
# KEY: import with one zone per face to preserve labeled boundaries
wf.import_geometry.cad_import_options.one_zone_per = "face"
wf.import_geometry()

# Get face zones BEFORE describe_geometry
mu = s.meshing_utilities
face_ids_before = mu.get_face_zones(filter="*")
print(f"Face zones after import: {len(face_ids_before)}")

# Surface mesh
wf.create_surface_mesh.cfd_surface_mesh_controls.max_size = 0.75
wf.create_surface_mesh.cfd_surface_mesh_controls.min_size = 0.05
wf.create_surface_mesh()

# Try: skip describe_geometry entirely, use apply_share_topology instead
print("Applying share topology to preserve boundaries...")
try:
    wf.apply_share_topology.tolerance = 0.01
    wf.apply_share_topology()
except Exception as e:
    print(f"Share topology: {e}")
    # Fallback: describe_geometry but try to preserve zones
    try:
        wf.describe_geometry.setup_type = "fluid_solid_voids"
        wf.describe_geometry()
        wf.create_regions.number_of_flow_volumes = 1
        wf.create_regions()
        wf.update_regions()
    except Exception as e2:
        print(f"Regions fallback: {e2}")

# Check zones after region setup
face_ids_mid = mu.get_face_zones(filter="*")
print(f"Face zones after region setup: {len(face_ids_mid)}")

# Volume mesh
wf.create_volume_mesh_wtm.volume_fill = "poly-hexcore"
wf.create_volume_mesh_wtm()

face_ids_final = mu.get_face_zones(filter="*")
print(f"Face zones after volume mesh: {len(face_ids_final)}")

# Count boundary zones
zone_info = []
for zid in sorted(face_ids_final):
    count = mu.get_face_zone_count(face_zone_id_list=[zid])
    if count > 0 and "interior" not in str(zid).lower():
        zone_info.append({"id": zid, "faces": count})
        print(f"  Zone {zid}: {count} faces")

if mesh_path.exists(): mesh_path.unlink()
s.tui.file.write_mesh(str(mesh_path))

result = {
    "status": "OK" if len(zone_info) > 2 else "BOUNDARY_WARN",
    "size": mesh_path.stat().st_size if mesh_path.exists() else 0,
    "face_zone_count": len(zone_info),
    "zones": zone_info
}
(Path(str(mesh_path).replace(".msh.h5", "_result.json"))).write_text(json.dumps(result, indent=2))
print(json.dumps(result, indent=2))

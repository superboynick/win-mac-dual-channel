"""Generate meshes at 3 refinement levels for mesh independence study."""
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

# 3 refinement levels
SIZINGS = {
    "coarse": {"surf_min": 0.10, "surf_max": 1.0, "vol": 1.0},
    "medium": {"surf_min": 0.05, "surf_max": 0.75, "vol": 0.75},
    "fine": {"surf_min": 0.03, "surf_max": 0.5, "vol": 0.5},
}

for level, sizes in SIZINGS.items():
    out = Path(rf"C:\Users\admin\win-mac-dual-channel\airjet-simulation\logs\evidence\mesh_study\{level}")
    out.mkdir(parents=True, exist_ok=True)
    mesh_path = out / "v03_mesh.msh.h5"
    
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
    
    wf.create_surface_mesh.cfd_surface_mesh_controls.max_size = sizes["surf_max"]
    wf.create_surface_mesh.cfd_surface_mesh_controls.min_size = sizes["surf_min"]
    wf.create_surface_mesh()
    
    wf.describe_geometry.setup_type = "fluid_solid_voids"
    wf.describe_geometry()
    wf.create_regions.number_of_flow_volumes = 1
    wf.create_regions()
    wf.update_regions()
    
    wf.create_volume_mesh_wtm.volume_fill = "poly-hexcore"
    wf.create_volume_mesh_wtm()
    
    if mesh_path.exists(): mesh_path.unlink()
    s.tui.file.write_mesh(str(mesh_path))
    sz = mesh_path.stat().st_size
    print(f"{level}: {sz} bytes - {sizes}")
    (out / "result.json").write_text(json.dumps({"level": level, "size": sz, "sizes": sizes}))

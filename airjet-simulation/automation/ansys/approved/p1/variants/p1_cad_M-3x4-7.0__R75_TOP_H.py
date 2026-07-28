# P1 CAD SpaceClaim Script - Variant M-3x4-7.0__R75_TOP_HEAVY
import clr, math, json, os
from System import Array

MM = 0.001
D001, D002, D003 = 27.5, 41.5, 2.8
P001 = 7.0
P014 = 0.25
n_col, n_row = 3, 4
pitch = P001 + P014

# Z-stack (mm)
Z_BC_BOT = 1.6175
Z_BC_TOP = 1.6575
Z_TC_BOT = 1.9325
Z_TC_TOP = 2.1825

job_dir = os.environ.get("AIRJET_JOB_DIR", r"D:\AirJet_P2\AJM-P2-STRUCTURAL-008\P1-CAD\variants")
report = {"status": "FAIL_DIRECT", "variant": "M-3x4-7.0__R75_TOP_HEAVY"}

try:
    from SpaceClaim.Api.V261.Scripting import BlockBody, Point, Union, Intersect, DocumentSave, Export, ExportFormat
    
    half = (P001 * MM) / 2.0
    half_tile = (pitch * MM) / 2.0
    
    # Cell grid
    cells = []
    for row in range(n_row):
        for col in range(n_col):
            cx = (col - (n_col-1)/2.0) * pitch * MM
            cy = (row - (n_row-1)/2.0) * pitch * MM
            cells.append((cx, cy))
    
    # Build bottom chambers
    bcs = []
    for cx, cy in cells:
        bc = BlockBody.Create(
            Point.Create(cx - half, cy - half, Z_BC_BOT * MM),
            Point.Create(cx + half, cy + half, Z_BC_TOP * MM))
        bcs.append(bc)
    
    # Build perimeter gaps (tile minus membrane)
    gaps = []
    from SpaceClaim.Api.V261.Scripting import Subtract
    for cx, cy in cells:
        tile = BlockBody.Create(
            Point.Create(cx - half_tile, cy - half_tile, Z_BC_BOT * MM),
            Point.Create(cx + half_tile, cy + half_tile, Z_TC_TOP * MM))
        memb = BlockBody.Create(
            Point.Create(cx - half, cy - half, Z_BC_BOT * MM + 0.001),
            Point.Create(cx + half, cy + half, Z_TC_TOP * MM - 0.001))
        try:
            gap = Subtract(tile, memb)
            gaps.append(gap)
        except:
            pass
    
    # Top plenum
    span_x = (n_col - 1) * pitch * MM / 2.0 + half_tile
    span_y = (n_row - 1) * pitch * MM / 2.0 + half_tile
    plenum = BlockBody.Create(
        Point.Create(-span_x, -span_y, Z_TC_BOT * MM),
        Point.Create(span_x, span_y, Z_TC_TOP * MM))
    
    # Union and clip
    all_bodies = bcs + gaps + [plenum]
    fluid = Union(all_bodies) if len(all_bodies) > 1 else all_bodies[0]
    env = BlockBody.Create(
        Point.Create(-D001*MM/2, -D002*MM/2, 0.0),
        Point.Create(D001*MM/2, D002*MM/2, D003*MM))
    domain = Intersect(fluid, env)
    
    # Save
    native = os.path.join(job_dir, "M-3x4-7.0__R75_TOP_HEAVY.scdocx")
    step = os.path.join(job_dir, "M-3x4-7.0__R75_TOP_HEAVY.step")
    DocumentSave.Execute(native)
    Export.Execute(step, ExportFormat.STEP)
    
    report["native"] = os.path.getsize(native)
    report["step"] = os.path.getsize(step)
    report["cells"] = len(bcs)
    report["status"] = "PASS_VARIANT_CAD"
    
except Exception as e:
    report["error"] = str(e)[:200]

with open(os.path.join(job_dir, "M-3x4-7.0__R75_TOP_HEAVY_report.json"), "w") as f:
    json.dump(report, f, indent=2, default=str)

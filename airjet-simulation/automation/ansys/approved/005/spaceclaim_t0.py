# AJM-005 SpaceClaim V261 control-plane probe; no engineering Gate is claimed.
import json
import os
import traceback


job_dir = os.environ["AIRJET_JOB_DIR"]
report_path = os.path.join(job_dir, "spaceclaim_probe.json")
native_scdocx_path = os.path.join(job_dir, "spaceclaim_probe.scdocx")
native_scdoc_path = os.path.join(job_dir, "spaceclaim_probe.scdoc")
result_data = {
    "schema_version": 1,
    "task": "AJM-WIN-ANSYS-STUDENT-CAPABILITY-SMOKE-005",
    "probe": "spaceclaim_t0",
    "status": "FAIL_DIRECT",
    "engineering_capability": "NOT_RUN",
    "script_api": "V261",
    "license_arguments_added": False,
}

try:
    document = DocumentHelper.CreateNewDocument()
    corner_1 = Point.Create(MM(0), MM(0), MM(0))
    corner_2 = Point.Create(MM(20), MM(10), MM(4))
    block_result = BlockBody.Create(corner_1, corner_2, ExtrudeType.ForceAdd)
    body = block_result.CreatedBody
    body.Name = "AJM005_T0_BLOCK"
    scdocx_save_result = DocumentSave.Execute(native_scdocx_path)
    scdoc_save_result = DocumentSave.Execute(native_scdoc_path)
    body_count = GetRootPart().Bodies.Count
    result_data.update({
        "block_command_success": bool(block_result.Success),
        "document_created": document is not None,
        "scdocx_save_command_success": bool(scdocx_save_result.Success),
        "scdoc_save_command_success": bool(scdoc_save_result.Success),
        "body_count": int(body_count),
        "body_name": str(body.Name),
        "scdocx_path": native_scdocx_path,
        "scdoc_path": native_scdoc_path,
        "scdocx_exists": os.path.isfile(native_scdocx_path),
        "scdoc_exists": os.path.isfile(native_scdoc_path),
        "construction_mm": [20.0, 10.0, 4.0],
    })
    if (block_result.Success and (scdocx_save_result.Success or scdoc_save_result.Success) and
            body_count == 1 and body.Name == "AJM005_T0_BLOCK" and
            (os.path.isfile(native_scdocx_path) or os.path.isfile(native_scdoc_path))):
        result_data["status"] = "PASS_CONTROL"
    else:
        result_data["error"] = "CONTROL_ASSERTION_FAILED"
except Exception as error:
    result_data["error_type"] = type(error).__name__
    result_data["error"] = str(error)
    result_data["traceback"] = traceback.format_exc()

with open(report_path, "w") as report_handle:
    json.dump(result_data, report_handle, indent=2, sort_keys=True)

if result_data["status"] != "PASS_CONTROL":
    raise Exception("AJM005_SPACECLAIM_T0_FAILED")

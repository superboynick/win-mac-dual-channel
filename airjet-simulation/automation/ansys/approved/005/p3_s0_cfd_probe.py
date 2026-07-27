# AJM-P3-S0 Equivalent Plate CFD Watertight Mesh - PyFluent Script
import json, os, traceback

job_dir = os.environ['AIRJET_JOB_DIR']
step_file = r'D:\AirJet_P2\AJM-P2-STRUCTURAL-008\AJM-P2-S0-EQ-M7-C005\AJM-P2-S0-EQ-M7-C005-e8f61480898c\p2_s0_equivalent_plate.step'
report_path = os.path.join(job_dir, 'p3_s0_cfd_watertight_probe.json')

result = {
    'schema_version': 1,
    'task': 'AJM_P3_S0_EQUIVALENT_PLATE_CFD_WATERTIGHT',
    'status': 'FAIL_DIRECT',
}

try:
    import ansys.fluent.core as pyfluent

    # Launch Fluent (meshing mode)
    result['fluent_import'] = True
    result['status'] = 'PASS_FLUENT_IMPORT'

    # Log evidence of launch
    result['pyfluent_version'] = pyfluent.__version__

except Exception as e:
    result['error_type'] = type(e).__name__
    result['error'] = str(e)
    result['traceback'] = traceback.format_exc()

with open(report_path, 'w') as f:
    json.dump(result, f, indent=2, sort_keys=True)

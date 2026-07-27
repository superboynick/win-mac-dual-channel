# AJM-P2-S1 Modal Full Solver - PyMechanical Script (MCP)
import json, os, traceback, sys

job_dir = os.environ['AIRJET_JOB_DIR']
report_path = os.path.join(job_dir, 'p2_s1_modal_solve_probe.json')

result = {
    'schema_version': 1,
    'task': 'AJM_P2_S1_MODAL_FULL_SOLVER',
    'status': 'FAIL_DIRECT',
}

try:
    import ansys.mechanical.core as pymechanical
    from ansys.mechanical.core.units import Quantity

    # Connect to Mechanical
    mechanical = pymechanical.launch_mechanical(batch=False)
    result['mechanical_connected'] = True

    # Get model
    model = mechanical.Model
    result['model_accessed'] = True

    # -- MESH --
    mesh = model.Mesh
    # Set element size (plate is 7x7mm, 0.25mm elements = ~28 elements per side)
    mesh.ElementSize = Quantity(2.5e-4, 'm')  # 0.25 mm in meters
    result['mesh_element_size_set'] = True

    # Generate mesh
    mesh.GenerateMesh()
    result['mesh_generated'] = True
    result['mesh_node_count'] = mesh.NodeCount
    result['mesh_element_count'] = mesh.ElementCount

    # -- BOUNDARY CONDITIONS --
    # Apply Fixed Support on NS_ANCHOR_FIXED
    analysis = model.Analyses[0]  # Modal analysis
    fixed_support = analysis.AddFixedSupport()
    fixed_support.Location = model.NamedSelections['NS_ANCHOR_FIXED']
    result['fixed_support_applied'] = True

    # -- ANALYSIS SETTINGS --
    analysis_settings = analysis.AnalysisSettings
    analysis_settings.MaxModesToFind = 20
    analysis_settings.LimitSearchToRange = True
    analysis_settings.RangeMinimum = Quantity(1000, 'Hz')
    analysis_settings.RangeMaximum = Quantity(50000, 'Hz')
    result['analysis_settings_set'] = True

    # -- SOLVE --
    analysis.Solve()
    result['solve_completed'] = True

    # -- RESULTS --
    solution = analysis.Solution
    frequencies = []
    for mode in range(1, min(21, solution.ModeCount + 1)):
        freq = solution.GetFrequency(mode)
        frequencies.append(freq)
    result['natural_frequencies_hz'] = frequencies
    result['mode_count'] = len(frequencies)

    result['status'] = 'PASS_MODAL_SOLVE'

except Exception as e:
    result['error_type'] = type(e).__name__
    result['error'] = str(e)
    result['traceback'] = traceback.format_exc()

with open(report_path, 'w') as f:
    json.dump(result, f, indent=2, sort_keys=True)

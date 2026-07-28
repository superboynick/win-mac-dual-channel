import clr, json, traceback
clr.AddReference("Ans.Core")

R = {"schema_version":2,"task":"AJM_P2_S2_HARMONIC_FULL","status":"FAIL_DIRECT"}

try:
    g = Model.GeometryImportGroup.AddGeometryImport()
    g.Import("D:\\AirJet_P2\\AJM-P2-STRUCTURAL-008\\AJM-P2-S0-EQ-M7-C005\\AJM-P2-S0-EQ-M7-C005-e8f61480898c\\p2_s0_equivalent_plate.step")
    Model.Mesh.ElementSize = Quantity(2.5e-4, "m")
    Model.Mesh.GenerateMesh()
    R["mesh"] = "PASS"
    
    ns_group = Model.NamedSelections
    ns_list = list(ns_group.Children)
    R["ns_count"] = len(ns_list)
    R["ns_names"] = [str(ns.Name) for ns in ns_list]
    
    for ns in ns_list:
        name = str(ns.Name).upper()
        if "FIXED" in name:
            fs = Model.AddFixedSupport()
            fs.Location = ns
            R["fixed_support"] = "OK"
        elif "PRESSURE" in name:
            p = Model.AddPressure()
            p.Location = ns
            p.Magnitude = Quantity(1000, "Pa")
            R["pressure"] = "OK"
    
    Model.AddModalAnalysis()
    Model.Analyses[0].Solve()
    children = [c for c in Model.Analyses[0].Solution.Children if hasattr(c, "Frequency")]
    R["modal_modes"] = len(children)
    
    Model.AddHarmonicResponseAnalysis()
    ha = Model.Analyses[1]
    ha.AnalysisSettings.RangeMinimum = Quantity(1000, "Hz")
    ha.AnalysisSettings.RangeMaximum = Quantity(50000, "Hz")
    ha.AnalysisSettings.SolutionIntervals = 20
    ha.Solve()
    R["harmonic_solved"] = True
    
    soln = ha.Solution
    td = soln.AddTotalDeformation()
    td.EvaluateAllResults()
    R["total_def_max_m"] = str(td.Maximum)
    R["total_def_min_m"] = str(td.Minimum)
    
    ExtAPI.DataModel.Project.SaveAs("D:\\AirJet_P2\\AJM-P2-STRUCTURAL-008\\P2-S2-HARMONIC\\p2_s2_harmonic_full.mechdb")
    R["saved"] = True
    R["status"] = "PASS_HARMONIC_FULL"
    
except Exception as e:
    R["error"] = str(e)[:300]
    R["traceback"] = traceback.format_exc()[:1000]

with open("D:\\AirJet_P2\\AJM-P2-STRUCTURAL-008\\P2-S2-HARMONIC\\_p2_s2_full_output.json", "w") as f:
    f.write(json.dumps(R, indent=2, default=str))

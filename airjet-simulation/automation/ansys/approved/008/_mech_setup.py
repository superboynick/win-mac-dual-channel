import clr
clr.AddReference("Ans.Core")
g = Model.GeometryImportGroup.AddGeometryImport()
g.Import(r"D:\AirJet_P2\AJM-P2-STRUCTURAL-008\AJM-P2-S0-EQ-M7-C005\AJM-P2-S0-EQ-M7-C005-e8f61480898c\p2_s0_equivalent_plate.step")
Model.Mesh.ElementSize = Quantity(2.5e-4, "m")
Model.Mesh.GenerateMesh()
Model.AddModalAnalysis()
Model.Analyses[0].Solve()
ExtAPI.DataModel.Project.SaveAs(r"D:\AirJet_P2\AJM-P2-STRUCTURAL-008\P2-S1-MODAL\p2_s1_modal.mechdb")
"SETUP_COMPLETE"

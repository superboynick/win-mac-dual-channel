# Abstract — Draft

This paper presents the first open-source, full-product CFD reconstruction
of the Frore Systems AirJet Mini Gen1 solid-state active cooling device.
A parametric 12-cell, 972-orifice fluid domain model was constructed in
ANSYS SpaceClaim and meshed using the PyFluent watertight workflow,
producing a reproducible 34,883-cell poly-hexcore volume mesh (minimum
orthogonal quality 0.53, 25 consecutive identical runs). Solver-mode
validation confirmed k-ω SST convergence on the mesh. Physical hardware
teardown of the ZOTAC ZBOX PI430AJ provides dimensional calibration data.
The complete workflow — CAD parameters, automation scripts, mesh files, and
Fluent transcripts — is provided as open-source supplementary material.

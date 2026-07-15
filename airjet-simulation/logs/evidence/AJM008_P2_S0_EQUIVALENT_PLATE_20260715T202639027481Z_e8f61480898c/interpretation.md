# AJM-008 P2-S0 equivalent-plate CAD interpretation

Commit `1a703cf741c4a421ed2799789486d7230e133132` produced a real Windows SpaceClaim result for the P2-S0 equivalent-plate precondition. The job exited 0, the producer passed 16/16 assertions, and the Native and STEP round trips retained the frozen bounding box, 13.728125 mm3 union volume, one closed manifold piece, the central-anchor region and the required CAD semantics.

This result means only that the single-cell structural calibration route now has a verified geometry input and semantic interface. It does not identify the real AirJet membrane material, reproduce the exact product membrane, or establish any resonance. The three material rows are paired C-class engineering candidates for sensitivity work; they are not a factorial design and are not product facts.

Mechanical import, mesh, modal analysis, harmonic response, convergence, physical amplitude and piezoelectric coupling were not run. Formal P2 completion is false, the P2 Gate is `NOT_RUN`, and P1-P6 remain `NOT_RUN`. The correct next step is a combined same-MCP-session producer-to-PyMechanical modal smoke route because completed MCP job identities do not survive a server restart.

The SCDOCX and STEP binary copies retain the exact Windows bytes and hashes. Text evidence copies use LF line endings, so the summary records raw and repository-copy identities separately.

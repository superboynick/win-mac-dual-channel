# Introduction — Draft

Solid-state active cooling represents a paradigm shift in thermal management
for compact electronics. Unlike conventional fan-based solutions, the Frore
Systems AirJet Mini Gen1 employs piezoelectric membrane actuation to generate
high-frequency synthetic jets through a dense array of micro-orifices (972
passages across 12 cells). With a form factor of 27.75 × 41.5 × 1.53 mm and
a power consumption below 5 W, the AirJet Mini targets applications where
traditional cooling solutions are infeasible due to space, noise, or
reliability constraints.

Despite the commercial availability of AirJet-equipped products such as the
ZOTAC ZBOX PI430AJ, no complete public-domain simulation of the full-product
fluid domain currently exists. Existing literature focuses on single-orifice
or single-cell models, which cannot capture the multi-cell interaction
effects, manifold pressure distribution, or system-level thermal performance
characteristic of the integrated 12-cell architecture.

This paper presents the first full-product CFD reconstruction of the AirJet
Mini Gen1 fluid domain, validated against physical hardware teardown
measurements. The workflow combines parametric CAD generation in ANSYS
SpaceClaim, automated watertight meshing via PyFluent, and solver validation
using the k-ω SST turbulence model. All parameters, scripts, and mesh files
are provided as open-source supplementary material to enable community
reproduction and extension.

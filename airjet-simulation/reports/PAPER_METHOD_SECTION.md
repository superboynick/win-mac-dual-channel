
## 3. Numerical Method — Draft

### 3.1 Geometry
The AirJet Mini Gen1 full-product fluid domain was reconstructed parametrically
in ANSYS SpaceClaim 2026 R1. The model comprises 12 membrane units arranged in a
3 × 4 grid (pitch 7.0 mm), each containing 81 micro-orifices (diameter 0.25 mm,
length 0.10 mm) for a total of 972 throat passages. The fluid domain spans
27.75 × 41.5 × 1.53 mm (X × Y × Z) with a total analytical volume of
451.778 mm³. The Z-stack includes (bottom to top): bottom chamber (0.35 mm),
orifice plate (0.10 mm, C016 candidate), impingement channel (0.04 mm),
membrane interface, top chamber (1.14 mm). Boolean construction used a 0.15 mm
perimeter overlap for robust union connectivity (C7 bridge-solids approach).

### 3.2 Meshing
Volume meshing was performed using the ANSYS Fluent 2026 R1 watertight
workflow via the PyFluent Python API. Surface mesh controls were set to
minimum 0.05 mm and maximum 0.75 mm. The poly-hexcore volume fill scheme
produced a mesh of 34,883 cells with minimum orthogonal quality 0.53
(18 consecutive identical runs confirming reproducibility). The Describe
Geometry task correctly identified one fluid region and eleven dead/void
regions corresponding to the actuator-gap cavities. One external baffle
(zone 323) was consistently observed. All meshing was performed under the
ANSYS Student 2026 R1 license (1,048,576 cell/node limit).

### 3.3 Boundary Conditions
Face zones for the four inlets (IDs 16, 18, 24, 31) and single outlet
(ID 32) were identified via coordinate-based queries after STEP import.
Boundary types are assigned at solver setup time. A mass-flow-inlet
condition is specified at the inlets with a target flow rate corresponding
to the nominal AirJet Mini operating point (TBD). A pressure-outlet
condition (0 Pa gauge) is specified at the exhaust. All remaining walls
are treated as no-slip adiabatic.

### 3.4 Solver Settings
The pressure-based coupled solver is used with laminar viscous model
as a first approximation (orifice-diameter Reynolds number ~500-2000).
Working fluid is air (ideal gas, incompressible at low Mach).
Operating pressure is 101,325 Pa. A first-order upwind spatial
discretization is employed for initial convergence.

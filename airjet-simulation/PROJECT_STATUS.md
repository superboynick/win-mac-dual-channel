# AirJet project status — 2026-07-18

## Literal stage state

- P0 public-evidence freeze: `PASS AJM-P0-v001`.
- P1-P6 formal Gates: `NOT_PASSED`.
- Full-product target: AirJet Mini Gen1; single-cell work is calibration-only.
- Execution strategy: complete ANSYS line plus independent OpenFOAM reproduction line. Neither replaces the other.

## Valid progress

- Evidence, parameter registry, layout candidates, stage manuals and audited ANSYS automation framework exist.
- V03/C7 preliminary SpaceClaim geometry preserved a single closed/manifold product candidate with 972 finite throats.
- ANSYS Student tooling diagnostics and several partial CAD/transfer routes produced auditable capability evidence.
- OpenFOAM Track B received a Mac read-only readiness audit and source-only smoke launcher; actual tooling smoke and AirJet solves remain `NOT_RUN`.

## Rear-inlet correction state

The user-observed rear-inlet defect is closed for the hash-bound V03 CAD route. V01 and V02
remain image-derived rear inlets reaching `Y=-17.750 mm`; the actual cell footprint remains
`Y=-14.500 mm`; and the C-class shared plenum now supplies the required `3.250 mm` rearward
support without clipping any of the four inlet boxes or projecting the geometry downward.

Official SpaceClaim job `ajm-rear-inlet-009-mcp-fbff57daa893` exited zero using producer SHA
`8f23d7d7dd66efcf06909341a45a76caccd6732cbf11fa1f54157699d55228b0`.
Mac independently accepted the native/STEP reopen evidence in
`AJM_MAC_REAR_INLET_RUNTIME_ACCEPTANCE_2026-07-20.md`; the machine-readable OpenFOAM handoff
passes the fail-closed consumer validator with zero findings. This is a geometry-runtime
acceptance only: formal P1 and P2--P6 remain `NOT_PASSED`.

The committed 34,883-cell Fluent mesh selects one actuator-gap tile, not the complete main-flow domain. It collapses all boundaries into one generic wall face zone. Fluent transcripts state `This case has no inlets & no outlets`; zero-velocity iterations are diagnostic failures, not converged AirJet CFD.

The first formal C7 retry reached the complete pre-region boundary evidence but failed at Watertight `Create Regions` with `Topology region with name dead0 already exists`. The reviewed consumer now replaces the preceding region-based inlet split with a face-angle split while retaining exact-four, conservation and probe-binding gates.

The 2026-09-01 hash-pinned rear-support retry independently reconfirmed the corrected SpaceClaim
geometry, but the consumer stopped before Fluent launch because its predecessor fingerprint still
required the old 1078-face body. The corrected rear-support body has 1076 faces: the two-face
difference is confined to the remaining continuous-wall inventory (74 rather than 76), while the
4/1 inlet/outlet, heat wall, 12+12 membrane and 972 throat contracts remain unchanged. This is a
contract synchronization failure, not mesh evidence; formal 006 and P1--P6 remain `NOT_PASSED`.

Next ANSYS action: commit the reviewed 1076-face consumer/runner/profile lock, require clean
inventory, and run exactly one official-MCP two-stage C7 retry. Stop before solver mode on the
first failed assertion. Only after C7 closes may Windows Codex A continue the remaining complete
P1 stage prerequisites. Do not use root-level ad-hoc mesh/solve scripts.

Next OpenFOAM action: Windows Codex B consumes only
`rear_inlet_handoff_accepted_20260720.json`, revalidates the artifact hashes available on its
host and continues source/tooling readiness. It must still reject AirJet solver execution
until the remaining formal P1/P2 interface requirements are satisfied.

## Coordination

Windows Codex A owns the complete ANSYS chain. A separate Windows Codex B owns the complete OpenFOAM reproduction chain. Mac owns Git watcher coordination, ETA/checkpoint tracking,催交, independent evidence review and integration. See `DUAL_WINDOWS_EXECUTION_CONTRACT.md`.

Large CAD, mesh, case/data, transcript, field, container and solver-native artifacts stay outside Git and are referenced by size/SHA256. Git contains reviewed source, compact reports and manifests only.

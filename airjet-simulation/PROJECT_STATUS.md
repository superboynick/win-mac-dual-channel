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

## Current engineering blocker

User visual inspection and source reconstruction confirm that rear inlet risers V01 and
V02 reach `Y=-17.750 mm`, while the generated shared plenum stops at the actual cell
footprint boundary `Y=-14.500 mm`, leaving `3.250 mm` of each rear inlet unsupported.
The array boundary `Y=-14.375 mm` is not the plenum boundary. The reviewed correction
preserves all four image-derived inlet lengths and extends the C-class shared plenum
support rather than silently clipping visible inlet geometry. A owns runtime validation;
B must reject and not consume the unvalidated geometry.

The committed 34,883-cell Fluent mesh selects one actuator-gap tile, not the complete main-flow domain. It collapses all boundaries into one generic wall face zone. Fluent transcripts state `This case has no inlets & no outlets`; zero-velocity iterations are diagnostic failures, not converged AirJet CFD.

The first formal C7 retry reached the complete pre-region boundary evidence but failed at Watertight `Create Regions` with `Topology region with name dead0 already exists`. The reviewed consumer now replaces the preceding region-based inlet split with a face-angle split while retaining exact-four, conservation and probe-binding gates.

Next ANSYS action: Windows Codex A pulls the signed hash-pinned fix and performs exactly one official-MCP two-stage retry, requiring the full boundary/region contract before entering solver mode. Do not run root-level ad-hoc mesh or solve scripts.

Next OpenFOAM action: Windows Codex B performs read-only tooling inventory and a separately authorized pinned tooling smoke, then waits for valid P1/P2 interfaces before AirJet P3.

## Coordination

Windows Codex A owns the complete ANSYS chain. A separate Windows Codex B owns the complete OpenFOAM reproduction chain. Mac owns Git watcher coordination, ETA/checkpoint tracking,催交, independent evidence review and integration. See `DUAL_WINDOWS_EXECUTION_CONTRACT.md`.

Large CAD, mesh, case/data, transcript, field, container and solver-native artifacts stay outside Git and are referenced by size/SHA256. Git contains reviewed source, compact reports and manifests only.

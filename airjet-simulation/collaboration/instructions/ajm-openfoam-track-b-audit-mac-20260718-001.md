# Mac root task: recover and audit Track B (OpenFOAM)

## Ownership and objective

Mac owns Codex B for this task. Windows continues Codex A (ANSYS/Mechanical and local
artifact recovery). Do not edit Windows runtime, watcher, ANSYS automation, current C7
runtime artifacts, or Codex A coupling outputs.

Establish a truthful, reproducible starting point for the OpenFOAM CFD/CHT track without
upgrading any diagnostic result to P3, P4, P5, or P6. The full AirJet Mini Gen1 product
remains the formal target; a single-cell model is calibration-only.

## Required preflight

1. Verify this exact signed task commit, clean `main`, trusted GitHub remote, and
   `0 ahead / 0 behind`.
2. Read `AGENTS.md`, the complete `airjet-product-reconstruction` skill,
   `airjet-simulation/PROJECT_STATUS.md`, `checklists/full_product_stage_gates.md`,
   `DUAL_TRACK_PLAN.md`, `coupling/COUPLING_PROTOCOL.md`, `coupling/COUPLING_STATUS.md`,
   `manuals/03_CELL_TRANSIENT_CFD.md`, `manuals/04_FULL_PRODUCT_AIRFLOW.md`,
   `manuals/05_FULL_PRODUCT_CHT.md`, and `manuals/07_RUN_LOG_AND_GIT.md`.
3. Run the project audit before edits.

## Authorized work

- Perform a read-only inventory of locally available Docker, Colima, OrbStack,
  OpenFOAM, CPU, memory, and free disk space. Do not install, upgrade, sign in, or
  change system configuration.
- Audit the current Track B plan against the formal P3-P5 stage gates and the actual
  repository evidence. Explicitly identify stale or unsupported claims.
- Design the narrowest deterministic OpenFOAM smoke route that could test tooling
  readiness without claiming AirJet physics. Separate tooling readiness, single-cell
  calibration, full-product airflow, and CHT.
- Add one small report at
  `airjet-simulation/reports/AJM_MAC_OPENFOAM_TRACK_B_AUDIT_2026-07-18.md`.
- If useful, add small, source-only smoke scripts under
  `airjet-simulation/automation/openfoam/`; do not execute a production solve and do
  not commit generated meshes, fields, logs, images, containers, archives, or binaries.
- Correct only Track B text in `airjet-simulation/DUAL_TRACK_PLAN.md` and
  `airjet-simulation/coupling/COUPLING_STATUS.md` when the report provides direct
  evidence. Do not edit `PROJECT_STATUS.md` or formal Gate checkboxes.

## Evidence and stop rules

- Classify AirJet inputs as D/P/I/C/U and preserve the full-product objective.
- Treat the existing 34,883-cell Fluent mesh, v4/v5 case/data, and C7/V8 attempts as
  diagnostic failures or unresolved evidence, not validated boundary conditions or
  converged product physics.
- No software installation, credential access, external messages, paid API calls,
  destructive Git action, force push, or large artifact commit is authorized.
- If OpenFOAM is unavailable, report `TOOLING_NOT_INSTALLED` with a concrete safe
  installation proposal; absence is not a blocker to completing this audit task.

## Completion

Run the project audit, relevant source-only checks, `git diff --check`, and inspect the
final diff. Commit with the Mac peer signing key and push normally to `origin/main`.
Report the signed result commit and literal statuses. Do not create or modify another
task envelope or receipt; automatic relay is disabled.

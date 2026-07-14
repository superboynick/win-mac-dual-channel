---
name: airjet-ansys-automation
description: Drive the AirJet full-product CAD and simulation workflow through audited ANSYS 2026 R1 automation interfaces. Use for Windows ANSYS inventory, SpaceClaim or Discovery scripted geometry, Workbench journals, PyMechanical structural work, PyFluent CFD or CHT, Student capability smoke tests, solver job monitoring, artifact hashing, and P1-P5 gate evidence. Keep the complete product as the main model and use single-cell work only for calibration.
---

# AirJet ANSYS automation

Use official ANSYS scripting interfaces instead of generic GUI clicking. Use this skill together
with `airjet-product-reconstruction`; that skill owns evidence classification and the P0-P6 model
scope, while this skill owns deterministic Windows execution.

## Required sequence

1. Read `AGENTS.md`, `airjet-simulation/PROJECT_STATUS.md`, the active numbered Windows task,
   and the relevant P1-P5 manual.
2. Require clean `main`, successful fetch, `0 ahead / 0 behind`, project audit PASS, and the exact
   official Student installation root before starting ANSYS.
3. Call the `airjet-ansys` MCP `inventory` tool. Do not proceed when an executable, Python package,
   approved profile, or Git invariant is missing.
4. Select the narrowest official engine:
   - SpaceClaim: `SpaceClaim.exe /RunScript` for CAD and fluid-volume construction.
   - Workbench: `RunWB2.exe -B -R` for project integration and transfer checks.
   - PyMechanical: structural, modal, harmonic, mesh, solve, and result export.
   - PyFluent: meshing, solver setup, transient CFD, CHT, transcript, and result export.
5. Start only a repository-reviewed, hash-pinned `profile_id` through MCP. Poll the job until
   terminal, then obtain its artifact manifest and declared report. The caller must never supply
   an executable, script path, command line, working directory, environment variable, or script
   text.
6. Record literal results. A process exit of zero is not a stage PASS; verify the required native
   file, log, report fields, connectivity, Named Selections, convergence, and conservation checks.
7. Close every run in `airjet-simulation/logs/run-index.csv`. Commit only the small, redacted
   `job.json`, artifact manifest, declared report, and interpretation below `logs/evidence/`; keep
   native CAD, projects, meshes, case/data, transcripts, and fields outside Git and register them
   in `logs/external-files.csv`. Add real failures to `logs/REALITY_AND_FAILURE_LOG.md`.
8. Stop at the active Gate. The 005 smoke test may unlock 006, but cannot pass P1. The 006 build
   may only reach `PENDING_PEER_REVIEW`; 007 performs the independent P1 review.

## Safety boundary

- Never inspect, enumerate, modify, or print license contents, license-pool data, activation data,
  registry license settings, or unrelated authorization environment variables.
- Never expose an arbitrary shell through MCP. Profiles are fixed in
  `airjet-simulation/automation/ansys/profiles.json`; their scripts are Git-tracked below the
  `approved/` subdirectory and pinned by SHA-256. Outputs use fixed server-side root identifiers.
- Never add license-selection flags to ANSYS commands. Preserve observed Student limitations.
- Never modify Git from an ANSYS automation script. Store native CAD, mesh, case/data, projects,
  screenshots, transcripts, and large fields outside Git.
- Treat GUI visibility separately from technical execution. When the user did not observe it,
  record `VISIBILITY=NOT_USER_OBSERVED`; do not downgrade verified batch/API results for that reason.
- Do not reduce cells, holes, or full-product flow paths to evade a Student limit.
- Treat the administrator account as a residual security limitation. Before unattended production
  runs, prefer a dedicated non-administrator runner even though the MCP fails closed against
  ordinary prompt injection and accidental path/command expansion.

## Resources

- Read `references/official-automation-routes.md` when selecting or troubleshooting an engine.
- Read `references/gate-evidence.md` before translating automation output into 005-007 status.
- Use `scripts/bootstrap_windows.ps1` only after reviewing the pinned dependencies and Git state.
- The installed MCP entry point is `scripts/airjet_ansys_mcp.py` and requires the local
  `airjet-ansys` Codex MCP registration.

If the MCP is unavailable, report that tooling blocker. Do not fall back to repeated generic Codex
prompts or coordinate-based GUI automation.

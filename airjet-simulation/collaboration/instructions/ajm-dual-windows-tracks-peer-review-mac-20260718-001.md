# Mac peer task: review two Windows tracks and preserve role boundaries

## Correction and authority

This task supersedes the incorrect Mac assignment in commit
`52dc8e9cc3b6305368f00425b7b37e4cd0c4c26f`. Mac is not Codex B and must not
perform or own the OpenFOAM/Fluid+Thermal track.

The signed role definition in commit `e29dcdaff5086811c27b7ab676dfb2e57385f578`
is authoritative:

- Windows Codex A: ANSYS structural track, CAD/Mechanical, modal and harmonic
  response, and `coupling/membrane_params.json`.
- A separate Windows Codex CLI B: Fluid+Thermal/OpenFOAM track and
  `coupling/cell_results.json`.
- Mac: equal peer reviewer, evidence auditor, Git coordinator, and cross-machine
  handoff endpoint. Mac owns neither Windows solver track.

If work from the superseded task already started, stop it without installing or
changing software. Preserve any small notes as explicitly superseded diagnostics;
do not claim them as Track B execution.

## Required review

1. Verify this exact signed target-tip task, clean `main`, trusted GitHub remote,
   and `0 ahead / 0 behind`.
2. Read `AGENTS.md`, the complete `airjet-product-reconstruction` skill,
   `airjet-simulation/PEER_COLLABORATION_PROTOCOL.md`,
   `airjet-simulation/coupling/COUPLING_PROTOCOL.md`,
   `airjet-simulation/coupling/COUPLING_STATUS.md`,
   `airjet-simulation/windows-prompts/AJM_WIN_CODEX_A_ANSYS_TRACK_009.md`,
   `airjet-simulation/windows-prompts/AJM_WIN_CODEX_B_OPENFOAM_TRACK_010.md`, and
   `airjet-simulation/checklists/full_product_stage_gates.md`.
3. Review commits `52dc8e9` and `0634485` against the signed watcher protocol.
   Record that `0634485` changed `WINDOWS_TASK.env` into a non-schema status with
   a BOM and mislabeled the B CLI as A. Do not treat that status as engineering
   evidence or valid task authorization.
4. Audit only; do not run ANSYS, Fluent, OpenFOAM, Docker, or production models.

## Deliverable and edit scope

Create only:

`airjet-simulation/reports/AJM_MAC_DUAL_WINDOWS_TRACKS_PEER_REVIEW_2026-07-18.md`

The report must provide the literal role map, current Git/task-envelope defects,
the fact that P1-P6 remain unpassed, and a safe recommendation for separate A/B
worktrees with the clean integration checkout reserved for watcher operation.

Do not modify `MAC_TASK.env`, `WINDOWS_TASK.env`, coupling outputs, formal Gate
checkboxes, project status, watcher source/state, or solver files as a completion
side effect. Do not install software, access credentials, or commit generated or
large artifacts.

## Completion

Run the project audit and `git diff --check`, inspect the final one-file diff,
commit with the Mac peer signing key, and push normally to `origin/main`. Report
the signed result commit and literal findings. Automatic relay remains disabled.

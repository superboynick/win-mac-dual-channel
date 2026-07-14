---
name: airjet-product-reconstruction
description: Evidence-led planning, auditing, and execution support for reconstructing a complete Frore AirJet Mini-class product from public product sheets, patents, tutorials, and simulation literature. Use when Codex works on the AirJet repository for product selection, source provenance, parameter derivation, full-product CAD, piezo/structural modeling, transient compressible CFD, complete airflow, CHT, calibration, uncertainty, run logs, or Windows handoff. Preserve the full-product target and treat single-cell models only as calibration submodels.
---

# AirJet Product Reconstruction

Advance a complete, public-evidence-constrained AirJet product reconstruction without turning patent embodiments or marketing drawings into unsupported product facts.

## Start every task

1. Locate the repository. Prefer the current Git root; known paths are:
   - macOS: `/Users/zhangjianxiao/win-mac-dual-channel`
   - Windows: `C:\Users\admin\win-mac-dual-channel`
2. Read `AGENTS.md` and `airjet-simulation/README.md`.
3. Read the task-specific files from the routing table below.
4. Run `python scripts/audit_project.py --repo <repo>` before broad edits and again before handoff. On Windows without a working Python launcher, run repository-root `audit-airjet-project.ps1` instead.
5. Inspect `git status`; stop on unknown changes or divergence.

## Coordinate long-running work

- For a genuinely long or multi-part task, use 1-2 bounded subagents when independent research, audit, or testing can run in parallel.
- The primary agent must read required skills and task files itself, retain ownership, integrate the findings, verify the result, and stop all subagents before handoff.
- Do not use subagents merely for idle persistence, or to bypass approvals, stage gates, evidence rules, Git safety, or visible-GUI requirements.
- Keep machine-specific watcher state, credentials, caches, PIDs, logs, and pending events outside Git. Synchronize only reviewed instructions and portable source files through the repository.

## Preserve the objective

- Treat AirJet Mini Gen1 as the primary full-product reconstruction target unless the user changes it.
- Require the final CAD and at least one CFD/CHT model to cover the whole product, all modeled cells, intake distribution, orifice plate, impingement channel, exhaust, and thermal stack.
- Use a high-fidelity cell model only to identify actuator displacement and pressure-flow transfer behavior for the full product.
- Do not resume geometry/material optimization until the reconstruction and multi-metric calibration gates pass.
- Do not call the result an exact digital twin without teardown, CT, or direct measurements.

## Route by task

| Task | Read first |
|---|---|
| Product choice or master planning | `AIRJET_MINI_FULL_PRODUCT_MASTER_PLAN.md`, `DECISION_AND_REASONING_ARCHIVE.md` |
| Parameter/source question | `evidence/SOURCE_PROVENANCE.md`, `parameters/full_product_parameter_registry.csv`, then `references/evidence-rules.md` |
| Full CAD | `manuals/01_FULL_PRODUCT_CAD.md`, `evidence/layout_candidate_constraints.md` |
| Piezo/structure | `manuals/02_ACTUATOR_STRUCTURAL.md` |
| Cell dynamic CFD | `manuals/03_CELL_TRANSIENT_CFD.md` |
| Full-product airflow | `manuals/04_FULL_PRODUCT_AIRFLOW.md` |
| Complete CHT | `manuals/05_FULL_PRODUCT_CHT.md` |
| Calibration/uncertainty | `manuals/06_CALIBRATION_AND_UNCERTAINTY.md` |
| Run/handoff/Git | `manuals/07_RUN_LOG_AND_GIT.md`, `WINDOWS_HANDOFF.md` |

All paths above are relative to `airjet-simulation/`. Read `references/stage-routing.md` when deciding whether a model may advance to the next stage.

## Apply evidence rules

Classify every input before using it:

- `D`: direct, model-specific product data; lock unless a corrected primary source appears.
- `P`: patent embodiment/range; constrain candidates but never label as exact product geometry.
- `I`: inference from images or cross-source geometry; preserve the derivation and uncertainty.
- `C`: calibration parameter; identify with multiple independent metrics.
- `U`: unresolved; retain alternatives and do not silently choose one.

Use `references/evidence-rules.md` for conflicts, derived values, and source hierarchy. Update the parameter registry, source provenance, decision archive, and model annotations together when a fact changes.

## Maintain engineering logic

- Separate product evidence, patent evidence, numerical-method literature, and assumptions.
- Record an equation or geometric constraint for every derived parameter.
- Keep rejected alternatives and rejection reasons.
- Calibrate dimensions, dynamics, airflow/backpressure, power, and heat jointly; do not fit only temperature.
- Distinguish `Q_chip`, `P_airjet`, and `Q_total` to avoid double-counting heat.
- Treat the Mini performance chart right axis as system noise at 50 cm, not airflow.
- State when a desired observable has no public direct measurement.

## Editing and artifacts

- Use `apply_patch` for repository text edits.
- Keep PDFs outside Git; link them through source provenance.
- Commit scripts, parameter tables, journals, summaries, and small plots. Exclude credentials, licenses, raw large cases, meshes, and transient fields.
- Put reproducible analysis notebooks under `airjet-simulation/notebooks/` and use the `jupyter-notebook` skill.
- Put rendered reports under an ignored/output area unless the user explicitly wants them versioned.

## Validate before handoff

1. Run the audit script and require `PASS`.
2. Run `git diff --check` and relevant script/notebook tests.
3. Confirm Mac, GitHub, and Windows commit hashes when cross-machine handoff is requested.
4. Confirm Windows research ZIP checksum and extraction state.
5. Add a dated entry to `MODEL_ANNOTATIONS.md` for any material modeling decision.
6. For a visible Windows handoff, launch from the logged-in desktop with repository-root `launch-airjet-codex-visible.ps1`; do not treat an SSH-session process as proof of a visible window.

## Resources

- `scripts/audit_project.py`: deterministic project integrity and evidence-language audit.
- `references/evidence-rules.md`: source hierarchy, derivation, uncertainty, and conflict rules.
- `references/stage-routing.md`: stage inputs, gates, outputs, and fallback behavior.
- `references/windows-operation.md`: Windows skill installation and visible Codex launch rules.

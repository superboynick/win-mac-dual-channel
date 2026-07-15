# P1-P3 48-hour sprint 002 teaching log

This log teaches the reproducible engineering path and its evidence limits. It does not write the
user's paper and does not upgrade a missing run to a result.

## START — signed task reception and baseline boundary

### Input

- Mac-signed root task `ajm-p1-p3-48h-sprint-20260715-002` at commit
  `31436c8d395cafe35a1eeab5e460062e48247da6`.
- P0 public-evidence freeze v1 and the current project status.
- Reviewed ANSYS automation profiles, installed watcher runtime, and Git-external trust roots.
- Measured start memory: 31.435 GiB physical, 9.268 GiB currently available.

### Model or equation

No geometry or physics model was executed at START. The intended dependency is deliberately ordered:

```text
complete-product P1 pilot
  -> P2 S0 displacement/frequency baseline
  -> P3 single-cell transient calibration baseline
```

The order prevents an isolated cell model from silently becoming the product model. The alternate
handoff route is signed-script SpaceClaim authoring followed by STEP plus a hash-bound semantic
sidecar; it does not claim native Named Selection transfer.

### Numerical and software checks

- Git main/clean/0-ahead/0-behind and exact task tip: PASS.
- Mac task signature and Windows trust-root hashes: PASS.
- Installed watcher bytes: 4/4 PASS.
- Project AirJet skills: 6/6 and 12/12 PASS.
- ANSYS static policy: 8 profiles / 5 tools PASS.
- Project audit: 106 required files / 7 manuals / 28 CSV files PASS.
- No ANSYS numerical solve was run; convergence and conservation are therefore `NOT_RUN`.

### Output

- A signed START evidence report.
- This teaching log.
- A first-draft evidence manifest that separates available claims from placeholders.

### Uncertainty and limitations

- Watcher/Codex startup evidence is execution-control evidence, not geometry or physics evidence.
- Available memory was below the signed task's 24 GiB threshold for a medium or larger P3
  dynamic-mesh baseline. Memory must be remeasured immediately before such a run.
- Native `.scdocx` attach, native parameterization, and native Named Selection transfer remain
  unproven. The STEP semantic route is reconstruction, not native transfer.

### Available for writing

The methods record may state that a signed, hash-pinned, fail-closed Windows execution path was
verified before the sprint and that formal engineering Gates remained unchanged.

### Prohibited wording

Do not state that ANSYS capability, full-product CAD, structural response, transient CFD, or any
P1-P6 Gate passed at START. Do not describe a future P2/P3 baseline as measured product behavior.

## Evidence-class reminder

- `D`: direct model-specific or direct run evidence.
- `P`: patent embodiment or range; a constraint, not an exact product fact.
- `I`: image/cross-source inference with derivation and uncertainty.
- `C`: calibration parameter to be identified with multiple metrics.
- `U`: unresolved; alternatives remain explicit.

Later entries must retain these classes and use the fixed sequence: input → model/equation →
numerical checks → output → uncertainty → available/prohibited wording.

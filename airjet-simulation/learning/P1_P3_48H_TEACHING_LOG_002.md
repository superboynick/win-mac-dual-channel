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

## Phase A — archive run #22 and defer the connected route

### Input

- Signed-run commit `1a9696c3930a42cd8a30aafe7093b8acafd6dd59`.
- Suite `AJM005_T1_CONNECTED_SC_SUITE_20260715T021529059815Z_aa1180f6`, case
  `a5c-eedabacc1fc6`.
- SpaceClaim producer `a5c-eedabacc1fc6-f70b77c399ca` and connected Workbench consumer
  `a5c-eedabacc1fc6-027f5de8b724`.
- Fixed 34-byte child-entry sentinel and fail-closed file-channel state machine.

### Model or equation

This phase did not solve a product equation. It tested an observable software state machine:

```text
Workbench Edit
  -> direct RunScript call
  -> entry/build probe
  -> Exit
  -> second probe
  -> failure-pre/failure-post probes when the build contract is not terminal
```

`RunScript=RETURNED` and `entry=ABSENT` are separate observations. Their conjunction does not imply
that the child geometry build ran and failed. Likewise, a suite-level diagnostic failure does not
mean the downstream transfer was executed.

### Numerical and software checks

- Producer: 21.451068 s, exit 0, 8/8 assertions true, `PASS_PARTIAL_CAD_CAPABILITY`.
- Consumer: 136.554323 s, exit 2, root error
  `FAIL_RUNSCRIPT_RETURNED_ENTRY_AND_BUILD_ABSENT`.
- Exact classification: `RUNSCRIPT_RETURNED_ENTRY_ABSENT`.
- Entry and build were absent at post-RunScript, post-Exit, failure-pre, and failure-post; both probe
  error lists were empty.
- Share, save-data, Refresh, Mechanical, mesh, and project save were `NOT_REACHED`.
- All producer 20/20 and consumer 19/19 artifact-manifest entries were rehashed and matched.
- The Git-external ZIP contains 22 selected payloads plus `SHA256SUMS.csv`; its SHA-256 is
  `62b058ef4125704ef4d74624d23b5cc0093315ab29bc613cd0e55cf5d92b7a96`.
- After the final evidence edits, the staged `suite-summary.json` SHA-256 was recomputed as
  `fe1abf7c7bce798ba43ba581ecf9e1d5289475a6f1b9863abb8f99cf45f6f3db` and matched the
  evidence-manifest row exactly.

### Output

- Condensed Git evidence in
  `logs/evidence/AJM005_T1_CONNECTED_SC_SUITE_20260715T021529059815Z_aa1180f6/`.
- Two run-index rows and reality item `REAL-20260715-050`.
- Route state `DEFERRED_CURRENT_HOST_ROUTE`; no further connected marker probes in this sprint.
- Next-route requirement: signed SpaceClaim authoring followed by hash-bound STEP and semantic
  sidecar reconstruction.

### Uncertainty and limitations

- No immediate outer-process observation was captured when the suite ended. A delayed archive-time
  check found zero related processes, but it cannot prove immediate cleanup.
- A same-host/session runtime positive control that deliberately writes both entry and build files was
  `NOT_RUN`. Synthetic validator-state tests do not replace that runtime control, so absence is not a
  loader or session root-cause result.
- The absent entry is bounded to this run and these checkpoints. It does not prove that `.py` is
  unsupported or that the child can never run.
- External native attach, native parameterization, and native Named Selection transfer remain
  `NOT_PROVEN`.
- The fixture is disposable toolchain evidence, not a full-product model.

### Available for writing

The methods record may state that the direct RunScript call returned but the fixed child entry and
build report were not observed in this run, with exact classification
`RUNSCRIPT_RETURNED_ENTRY_ABSENT`. It may state that this evidence motivated deferring the current
connected route and adopting a hash-bound STEP plus semantic-sidecar route for further testing.

### Prohibited wording

Do not state that the child build executed and failed, that Python script files are unsupported,
that connected transfer failed or passed, or that Mechanical/mesh/project work was reached. Do not
upgrade P1 readiness or any P1-P6 engineering Gate from this diagnostic.

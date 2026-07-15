# AJM P1-P3 48-hour sprint 002: Windows START evidence

## Literal task state

```text
TASK_ID=ajm-p1-p3-48h-sprint-20260715-002
WORKFLOW_ID=ajm-p1-p3-48h-sprint-20260715-r2
TASK_COMMIT=31436c8d395cafe35a1eeab5e460062e48247da6
INSTRUCTION_PATH=airjet-simulation/collaboration/instructions/ajm-p1-p3-48h-sprint-20260715-002.md
INSTRUCTION_BLOB=4f11075b6e0659da78c3f6395c67f6212e6bec04
INSTRUCTION_SHA256=9e3136c2fa89cdbfc25add3d956f8827d16fcff9ca18808aef5a3fa9f07a25e3
TASK_SIGNER_FINGERPRINT=SHA256:jdxP5xJrt8J7PKjeCrJmrEeoAH44u9NxBICo41HwMuc
EXPECTED_START_COMMIT_SIGNER_FINGERPRINT=SHA256:oI3/MIlKz1mgLV3+5n1coQxynaqQOzxqi0GHxreGEdc
SPRINT_STARTED_AT_UTC=2026-07-15T05:00:14.339Z
SPRINT_DEADLINE_UTC=2026-07-17T05:00:14.339Z
PREFLIGHT_AT_UTC=2026-07-15T05:00:14.339Z
PREFLIGHT_HEAD=31436c8d395cafe35a1eeab5e460062e48247da6
PREFLIGHT_ORIGIN_MAIN=31436c8d395cafe35a1eeab5e460062e48247da6
PREFLIGHT_WORKTREE=CLEAN
PREFLIGHT_AHEAD_BEHIND=0_AHEAD_0_BEHIND
RUNNER_READ_SIGNED_INSTRUCTION=PASS
WATCHER_CLAIM_PHASE=CODEX_EXITED_0
CONTINUATION_MODE=MANUAL_CONTINUATION_AFTER_VERIFIED_WATCHER_EXIT
CODEX_VERSION=codex-cli 0.144.4
GUI_VISIBILITY=NOT_USER_OBSERVED
RECEPTION_GATE=PASS
```

This START record proves only that the Windows execution session accepted and entered the signed
task after the required trust and repository checks. It is not an ANSYS result and does not pass an
engineering Gate.

## Trust, runtime, skills, and audit

The task commit is a good Mac SSH-signed linear tip. Its only changed paths are the strict 11-field
`WINDOWS_TASK.env` and the corresponding `100644` instruction blob. The frozen 001 instruction was
also checked at blob `fff0d07a093bc0bf44299109f975b3e45f003fba` and SHA-256
`f72348f2b87ac06bc3d7097ef812ab08f390149d45939a1625677e3b84eae664`.

```text
WATCHER_RUNTIME_HASHES=PASS_4_OF_4
WATCHER_TRUST_HASHES=PASS_3_OF_3
AIRJET_PRODUCT_RECONSTRUCTION_SKILL=PASS_6_OF_6
AIRJET_ANSYS_AUTOMATION_SKILL=PASS_12_OF_12
ANSYS_STATIC_POLICY=PASS_PROFILES_8_TOOLS_5
PROJECT_AUDIT=PASS_REQUIRED_FILES_106_MANUALS_7_CSV_FILES_28
EVIDENCE_MANIFEST_SCHEMA_CHECK=PASS_ROWS_6_FIELDS_12
CLAUDE_STAGED_REVIEW=APPROVED_NO_BLOCKERS
CLAUDE_REVIEW_MODEL=deepseek-v4-flash
```

The two signer fingerprints intentionally differ: the peer task authorization is signed by the
Mac task key, while this START result commit must be signed by the independent Windows result key.
The Windows fingerprint is verified again against the completed commit before push.

Raw-byte watcher hashes matched both the repository checkout and the installed runtime:

| Runtime file | SHA-256 |
|---|---|
| `AirJetWatcher.Common.ps1` | `C1597D7760CDA60ADA452305EE20E749812A73B5EF48F0A600E37986B6F3CCD4` |
| `Watch-AirJetGit.ps1` | `295ECFEEF182C11EDF51B21B3273594FBB08DE9F1BE0CEC106804330970557C4` |
| `Manage-AirJetWatcher.ps1` | `EB1E53088F8FFF59708B6EA11896BD1D047E81665851FE08DE65BEC42538DC1D` |
| `Run-AwakenedCodex.ps1` | `6D0667D7B60BB04B7BC549EE380C22F042C818A1990A69A6B96041BD59B2BBDB` |

Task 001 stopped before model execution because the npm `codex.cmd` path carried the long prompt in
argv. Task 002 used the reviewed no-BOM UTF-8 stdin transport. The watcher created a verified 002
claim and launched Codex; the first child exited zero without leaving START or engineering output,
so the current manually resumed Codex session is the authorized continuation described by the
signed instruction. GUI visibility remains `NOT_USER_OBSERVED`; exit zero is not treated as sprint
completion.

## Initial engineering state and dependency route

```text
INITIAL_STATUS=P0=PASS / P1-P6=NOT_RUN
P0_STAGE_GATE=PASS_V1
P1_STAGE_GATE=NOT_RUN
P2_STAGE_GATE=NOT_RUN
P3_STAGE_GATE=NOT_RUN
P4_STAGE_GATE=NOT_RUN
P5_STAGE_GATE=NOT_RUN
P6_STAGE_GATE=NOT_RUN
CAD_AUTHORING_ROUTE=SPACECLAIM_SIGNED_SCRIPT_PARAMETRIC
SOLVER_HANDOFF_ROUTE=HASH_BOUND_STEP_SEMANTIC_SIDECAR
EXTERNAL_NATIVE_ATTACH=NOT_PROVEN
NATIVE_PARAMETERIZATION=NOT_PROVEN
NATIVE_NAMED_SELECTION_TRANSFER=NOT_PROVEN
```

The bounded execution dependency is:

```text
P1 full-product primary-balanced pilot
  -> P2 S0 displacement / frequency response
  -> P3 single-cell calibration baseline
```

The P1 pilot remains a complete 12-cell product candidate. P2 and P3 are pre-Gate submodels; the
single-cell CFD model cannot replace the full-product reconstruction target.

## Memory snapshot at START

```text
PHYSICAL_MEMORY_BYTES=33752997888
PHYSICAL_MEMORY_GIB=31.435
AVAILABLE_MEMORY_BYTES=9951375360
AVAILABLE_MEMORY_GIB=9.268
RAM_PRESSURE_AT_START=BELOW_24_GIB_THRESHOLD
P3_MEDIUM_OR_LARGER_DYNAMIC_MESH=BLOCKED_UNTIL_MEMORY_RECHECK_GE_24_GIB
```

Only process name, PID, and working-set size were observed; no private process contents were read and
no user process was terminated.

| Rank | Process | PID | Working set MiB |
|---:|---|---:|---:|
| 1 | `steamwebhelper` | 1844 | 913.3 |
| 2 | `msedge` | 41608 | 908.9 |
| 3 | `explorer` | 13664 | 691.5 |
| 4 | `steamwebhelper` | 7532 | 480.3 |
| 5 | `claude` | 33396 | 426.4 |
| 6 | `msedgewebview2` | 39768 | 407.5 |
| 7 | `QQ` | 4440 | 403.7 |
| 8 | `codex` | 14772 | 397.5 |
| 9 | `5EClient` | 25888 | 365.5 |
| 10 | `5EClient` | 22112 | 338.3 |

Memory pressure does not block evidence archival, route-contract work, P1/P2 preparation, or an
appropriately small disposable smoke. It does block starting a medium or larger P3 dynamic-mesh
baseline until memory is measured again and at least 24 GiB is available.

## START claim boundary

Allowed claim: the signed task, trust roots, runtime bytes, project skills, static policy, audit, and
Git preflight were verified, and the Windows session entered sprint 002.

Prohibited claim: no CAD, Mechanical solve, Fluent solve, mesh independence, time-step independence,
or P1-P6 engineering Gate has passed because of this START record.

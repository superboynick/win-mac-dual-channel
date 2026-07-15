# URGENT Mac task: freeze the V02 native `.scdocx` topology observer

Act now and deliver the smallest safe static package. Do not stop at planning and do not
repeat the closed Parasolid route.

## Fixed facts and scope

- Product target: AirJet Mini Gen1 only.
- STEP observer is executable, but the upstream 972-interface geometry is lost while the
  downstream 972 imprints remain.
- Parasolid export is closed as `CLOSED_DIAGNOSTIC_ROUTE_BLOCKED`; do not modify or run it
  as a retry or fallback.
- The preceding signed Windows commit fixes the stale Parasolid policy invariant so the
  current implementation and project audits agree. Preserve that fix.
- Mac performs code, profile, runner, tests, documentation, and static review only. Do not
  run ANSYS on Mac.
- Formal 006, mesh, physics, and P1-P6 remain `NOT_RUN`.

## Required implementation

Create and freeze one audited native route:

```text
ajm006-spaceclaim-v02-preliminary-v1
  -> hash-bound product_two_zone.scdocx
  -> ajm006-workbench-v02-native-topology-observer-v1
```

Add these fixed artifacts, using equivalent final names only if existing repository naming
rules require them:

```text
airjet-simulation/automation/ansys/approved/006/v02_native_topology_observer.wbjn
airjet-simulation/automation/ansys/run_v02_native_topology_006.py
airjet-simulation/automation/ansys/test_run_v02_native_topology_006.py
airjet-simulation/windows-prompts/AJM_WIN_V02_NATIVE_TOPOLOGY_OBSERVER_006.md
```

Register exactly one new diagnostic profile:

```text
PROFILE_ID=ajm006-workbench-v02-native-topology-observer-v1
```

It must be hash-pinned in `profiles.json`, repeated as exact script/profile constants in the
runner, and bind only the terminal predecessor
`ajm006-spaceclaim-v02-preliminary-v1`, its report, required status/assertions, and the
minimum reviewed artifacts needed for the native inspection. The native input is
`product_two_zone.scdocx`. Do not consume `.x_t`, STEP, a semantic sidecar, or mutable
repository/runtime paths. MCP must bind the predecessor source commit, job/profile/report
identity and artifact-manifest SHA256; the observer must not trust a hash reported by the
producer without recomputing the copied artifact bytes.

The fixed runner must use one MCP server process and execute only:

```text
producer -> native observer
```

No direct ANSYS executable, arbitrary command/path, connected-route fallback, automatic
retry, mesh, solve, CFD, CHT, or nine-variant execution is allowed.

## Native observer contract

- Keep the MCP-frozen predecessor read-only and recheck its size/SHA256 after observation.
- If the editor needs a writable document, use only a job-local hash-equal staging copy and
  prove the frozen source remained unchanged.
- Use one fixed attach/update/Mechanical inspection sequence. Preserve the first literal
  error and fail closed; never fall back to STEP, Parasolid, or connected routes.
- Do not set `native_attach=true` or `observer_reached=true` until Mechanical actually
  attaches the geometry and enumerates the bodies/faces.
- Record actual body IDs, deterministic role binding, face count, bbox, volume, upstream
  and downstream 972-interface candidates, membership, and shared/coincident/adjacency
  observations.
- The only observer success is `PASS_PRELIMINARY_NATIVE_TOPOLOGY_OBSERVATION`.
- `route_assessment=PASS_CANDIDATE_ROUTE_TO_MESH` is allowed only when both sides of the
  972-interface, role geometry, and the complete identity/hash chain close. It still does
  not pass mesh, formal 006, P1, or any physics Gate.
- Always retain `formal_006_completion=false`, `P1-P6=NOT_RUN`,
  `mesh=NOT_EVALUATED_NO_MESH`, `physics=NOT_RUN`, and
  `visibility=NOT_USER_OBSERVED`.

## Windows prompt and static gates

The Windows prompt must require literal `GIT_READY=<40hex>`, good signature, clean `main`,
`0/0`, project audit PASS, the single guard command, and the single runner command. It must
report the job IDs, raw errors, summary/artifact paths and hashes, topology classification,
route assessment, and unchanged Gate boundaries. Mac must not execute this prompt.

Hard-wire the new script/profile/runner/test/prompt into the MCP policy and these exact two
project audits:

```text
codex-skills/airjet-product-reconstruction/scripts/audit_project.py
audit-airjet-project.ps1
```

Add fail-closed guards for the exact predecessor, artifact allowlist, SHA binding,
single-process ordering, forbidden routes, predecessor immutability, actual observer
reachability, and Gate enums. Negative tests must mutate each of those identities and prove
rejection; they must also prove that a submitted/reached job with missing or malformed
report evidence becomes `FAIL`, never `NOT_RUN`.

Journal static checks must require the one reviewed native attach/update/Mechanical
enumeration sequence and reject `DocumentOpen`, STEP/Parasolid import, connected-editor
commands, mesh/solve calls, arbitrary executable launch, fallback branches, and mutable
repository reads. They do not substitute for the later Windows execution.

Run and require:

```text
runner guards=PASS
Python compile/tests=PASS
journal static checks=PASS
MCP policy=PASS
Python project audit=PASS
PowerShell project audit semantics=PASS or independently reproduced equivalent on Mac
git diff --check=PASS
ANSYS_RUN=NO
```

Use `deepseek-v4-pro` and `deepseek-v4-flash` in parallel through the repository
`tools/claude-cli/review-staged.sh` read-only wrapper. The reviewers do not edit; Codex
independently verifies findings, applies justified fixes, re-stages, and repeats both reviews
if functional bytes changed. If either configured model is unavailable, report the literal
CLI error as a task blocker rather than inventing a verdict. Do not send secrets, license
data, commercial PDFs, or solver output to either model.

Update status/log text only to `STATIC_READY_WINDOWS_NOT_RUN`. Do not claim native attach,
topology preservation, mesh readiness, formal 006, or P1-P6 PASS before the Windows run.

## Git delivery

Start only from clean, signed, synchronized `main`. Preserve linear history; no amend,
rebase, reset, merge, clean, or force push. Commit only the coherent static package, sign
with the Mac key, fetch-check, and push normally.

After push, report exactly:

```text
GIT_READY=<full 40-hex result commit>
FIXED_WINDOWS_PROMPT=<repository-relative path>
RUNNER=<repository-relative path>
PROFILE_ID=ajm006-workbench-v02-native-topology-observer-v1
DEEPSEEK_PRO_VERDICT=<PASS or precise blockers>
DEEPSEEK_FLASH_VERDICT=<PASS or precise blockers>
STATIC_TESTS=<literal results>
PROJECT_AUDIT=<literal result>
SIGNATURE=GOOD
CLEAN=true
AHEAD_BEHIND=0/0
ANSYS_RUN=NO
P1-P6=NOT_RUN
```

Do not create or modify `WINDOWS_TASK.env`; reciprocal relay is disabled. Stop after the
signed Mac result commit and wait for the coordinating session to create the next Windows
root task.

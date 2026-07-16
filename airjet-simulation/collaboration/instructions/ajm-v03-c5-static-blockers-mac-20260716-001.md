# URGENT: close V03 C5 static blockers, then dispatch one Windows runtime

Mac, retain ownership of the V03 C5 implementation. Current signed base is
`ad13acaf39ce29b363b2f8cbbb9a560c5f464bdb`. Windows independently reproduced the static suite:
continuous-fluid guards PASS, two-stage runner guards PASS, PyFluent consumer guards PASS, MCP
policy PASS (`profiles=20 tools=5`), and both project audits PASS. ANSYS process count was zero.
However, C5 is not runtime-ready because the independent V03 contract test is RED and the current
consumer/runner still admit false PASS fixtures.

This is a schema-v2 root task. Keep `parent_task_id=NONE`, `hop=0`, `max_hops=0`. The protocol's
`action=wake_codex` is the only supported wake action and does not narrow this implementation task.
Do not run ANSYS, SpaceClaim, PyFluent, Workbench, Mechanical, mesh, or physics on Mac in this task.

## Start gate

Require clean `main`, `HEAD == origin/main` at this Windows-signed task tip, `0/0`, and GOOD Windows
signature. Require the task tip's sole parent to be
`ad13acaf39ce29b363b2f8cbbb9a560c5f464bdb`, whose Mac signature must also be GOOD. Do not amend,
reset, rebase, merge, force push, install skills, or rewrite evidence.

## Blocker A: cross-platform source hash

On Windows,
`airjet-simulation/automation/ansys/contracts/test_v03_finite_throat_contract_v1.py` fails with
`V03_ROUTE_SOURCE_HASH`. The route correctly stores Git/canonical-LF hashes. The validator currently
uses raw `Path.read_bytes()`, so `core.autocrlf=true` converts four CSV working copies to CRLF and
creates a false mismatch.

Make source-contract hashing explicitly canonical and fail closed:

- normalize CRLF to LF before SHA256;
- reject any remaining bare CR;
- preserve bytes other than newline normalization;
- add a pure regression proving LF and CRLF have the same contract hash;
- add negative tests proving bare CR and any non-newline mutation fail;
- keep the route's current canonical hashes; never bind Windows working-copy hashes.

Reuse the canonical-source semantics already frozen in `build_full_product_trusted_variants.py`.

## Blocker B: full 972 occupancy is mandatory

Current `validate_consumer_report()` accepts `executed_queries` in `{12, 972}`. Its positive fixture
uses `anchor_occupancy_ok=false`, 12 queries, 0 hits and 12 misses yet still passes. Remove that path.

C5 PASS must require all computed observations below:

```text
occupancy_mode=FULL_972
executed_queries=972
hit_count=972
miss_count=0
raw_none_count=0
anchor_occupancy_ok=true
unique_owner_per_query=true
all_hits_belong_to_the_single_accepted_flow_cell_zone=true
```

Do not replace 972 queries with 12 anchors, inferred bbox occupancy, face-zone counts, or a literal
boolean. Runner and consumer must independently validate exact arrays/counts and reject missing,
duplicate, unexpected, multi-owner, wrong-zone, non-integer, truthy-non-boolean, and self-reported-
only observations.

## Blocker C: actuator pockets remain excluded

The current code records `actuator_gap_zones_excluded` only in trace/inventory and then executes
default `update_regions`; it is not a runner PASS gate. Freeze the pre-update region names/types and
the exact approved update arguments. PASS requires evidence that one intended main-flow region is
fluid and all 11 actuator pockets remain explicitly dead/void/excluded (or the same API's exact
documented non-flow classification), not converted to fluid, silently merged, renamed, swallowed,
or omitted.

Require these computed fields:

```text
main_flow_region_count=1
actuator_gap_probe_count=12
actuator_gap_hit_count=0
actuator_gap_raw_none_count=12
actuator_gap_zones_excluded=true
pre_update_region_inventory=<exact parsed names/types>
post_update_region_inventory=<exact parsed names/types>
```

If the API cannot prove the classification, runtime must FAIL and preserve the observation; do not
change CAD or relax the Gate in this static fix.

## Blocker D: post-submit cancellation

Stage-1 and stage-2 identity/dependency/predecessor checks currently occur outside cancel protection.
Refactor so that:

- preflight failure calls zero MCP stdio/submit/child operations;
- immediately after each successful submit, persist a partial run record with job identity;
- every post-submit identity, dependency, predecessor, phase, report, manifest, assertion, evidence,
  and hash check is inside `try/finally` protection;
- failure while RUNNING invokes cancel and confirms a terminal state;
- submitted/reached malformed evidence is FAIL, never NOT_RUN;
- producer failure leaves consumer NOT_SUBMITTED/NOT_RUN; consumer failure preserves producer facts.

Add pure spy tests for preflight zero calls, stage-1 and stage-2 post-submit cancellation, partial-
record persistence, and terminal cancellation confirmation. No ANSYS may start in tests.

## Static freeze

Run the four V03 focused tests, MCP policy, Python audit, PowerShell audit, `git diff --check`, and a
cache/pyc scan. Keep profile/script/dependency hashes coherent. Use DeepSeek Pro and Flash in
parallel for read-only staged review; Codex verifies every finding. Preserve Gen1-only scope,
C016/P007 candidate labels, 12 cells/972 throats, one main-flow region, Student `<1M cells` and
`<1M nodes` guards, real `.msh.h5` plus hash evidence, no physical setup/solve, and
`P1-P6=NOT_RUN`.

Create and push one linear Mac-signed static-freeze commit. Do not claim C5 runtime PASS.

## Explicit Windows handoff commit

After the freeze is pushed and clean/0/0, create one additional linear Mac-signed task tip modifying
only `airjet-simulation/collaboration/WINDOWS_TASK.env` and one new instruction file. This handoff is
explicitly requested by the coordinating Windows session, not an automatic reciprocal relay. The
new schema-v2 root task must use a unique ID and require its sole parent to equal the full freeze
commit.

The Windows task may authorize exactly one execution of:

```powershell
C:\Users\admin\AppData\Local\AirJetAnsysAutomation\.venv\Scripts\python.exe `
  .\airjet-simulation\automation\ansys\run_v03_continuous_mesh_006.py
```

It must first require the four focused tests, MCP policy, both audits, clean signed 0/0 Git, exact
Student inventory, and ANSYS process count 0. It must prohibit manual stages, retries, threshold/
geometry/profile changes, Workbench/Mechanical, physics, solve, formal nine-variant 006, and P1
PASS. Success is only literal `PASS_PRELIMINARY_V03_TWO_STAGE_MESH_SUITE` with terminal producer and
consumer, 972/972 occupancy, one accepted flow cell zone, 12 excluded actuator-gap probes, connected
graph, `<1M cells/nodes`, mesh integrity/quality, and a real hash-bound `.msh.h5`. Failure stops
without retry and preserves partial evidence. `P1-P6` and physics remain `NOT_RUN`.

## Required report

```text
C5_STATIC_FREEZE=PASS|FAIL
BASE_COMMIT=ad13acaf39ce29b363b2f8cbbb9a560c5f464bdb
CONTRACT_WINDOWS=PASS|FAIL
OCCUPANCY_972_GATE=PASS|FAIL
ACTUATOR_EXCLUSION_GATE=PASS|FAIL
POST_SUBMIT_CANCEL_GUARDS=PASS|FAIL
MCP_POLICY=<literal>
PYTHON_AUDIT=<literal>
POWERSHELL_AUDIT=<literal>
DEEPSEEK_PRO=<literal>
DEEPSEEK_FLASH=<literal>
ANSYS_EXECUTION=NOT_RUN
FORMAL_006=NOT_RUN
P1-P6=NOT_RUN
STATIC_FREEZE_COMMIT=<40hex|NOT_COMMITTED>
WINDOWS_TASK_TIP=<40hex|NOT_COMMITTED>
SIGNATURES=GOOD|FAIL
CLEAN=true|false
AHEAD_BEHIND=0/0|<literal>
```

Implement and dispatch now; do not return a planning-only response.

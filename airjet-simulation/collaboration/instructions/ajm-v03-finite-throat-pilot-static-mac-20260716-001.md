# URGENT: freeze the Gen1 V03 finite-throat pilot route

Mac, take ownership of this static-only task immediately. The V02 split-STEP runtime result is
frozen in signed commit `cfbffdc6a63563fd22fe422bce943708c2a622cd`: upstream reimport retained
2044 faces, while downstream reimport remained one closed/manifold body with unchanged envelope and
volume but healed 978 faces to 6. This proves that 972 zero-thickness interface imprints are not
stable in that STEP representation. It does not prove full-product geometry, ANSYS, or solver
failure.

This is a schema-v2 root task. Keep `parent_task_id=NONE`, `hop=0`, and `max_hops=0`. Do not run
ANSYS, SpaceClaim, Fluent, Workbench, Mechanical, mesh generation, or any solver in this task.
The envelope's protocol-defined `action=wake_codex` is the only supported wake action and does not
limit the implementation scope described here. This Windows dispatch commit intentionally contains
only the task envelope and this instruction; Mac creates the implementation artifacts in its result
commit. Historical instruction files remain immutable audit records and are not active unless their
exact path is selected by the current envelope.

## Start gate

Require clean `main`, `HEAD == origin/main` at this Windows-signed task-delivery tip, `0/0`, and a
GOOD Windows signature for the tip. Require its sole parent to be
`cfbffdc6a63563fd22fe422bce943708c2a622cd`, then verify GOOD Mac trust for that base commit.
Recheck the committed LF evidence-summary hash
`32c061f34f89196c850fdbabc54dd7cc474bbf49504878227307753d85a766d7`; do not replace it with
the Windows CRLF working-copy hash. The exact evidence path is
`airjet-simulation/logs/evidence/AJM006_V02_SPLIT_STEP_CONVERTER_20260715T165856334518Z_9687be3d4dce/evidence-summary.json`.
Verify MCP policy and both project audits PASS before edits.

## Sole target and evidence boundary

The sole product target is AirJet Mini Gen1. G2 remains comparison evidence only. Freeze one pilot:

```text
PRODUCT=AIRJET_MINI_GEN1
CONFIGURATION=M-3x4-7.0
VARIANT=M-3x4-7.0__R50_BALANCED
CELLS=12
ORIFICE_CANDIDATES=972
ROUTE=UPSTREAM_TO_972_FINITE_THROATS_TO_DOWNSTREAM_SINGLE_CONTINUOUS_FLUID_BODY
```

Lock every input to existing rows in
`airjet-simulation/parameters/full_product_parameter_registry.csv`,
`airjet-simulation/parameters/p1_cad_parameter_map.csv`, and the applicable
`airjet-simulation/geometry/contracts/` tables. In particular:

- `D001/D002/D003` envelope is direct product evidence.
- 3x4, 12 cells, 972 throats, and the single-body transfer representation are pilot candidates,
  not product facts.
- `P007=0.25 mm` is a patent candidate diameter, not a measured Mini value.
- throat length uses `C016=0.10 mm`, `C / cad_placeholder`, allowed exploratory range
  `0.05-0.20 mm`, `product_fact=false`.
- the four drawn vent objects remain `I` class and do not prove intake-group or cell count.

Do not edit the nine production blueprints under
`airjet-simulation/automation/ansys/contracts/trusted_full_product_gen1/variant_*.json` or their
`campaign.json` to make this pilot appear formal.

## Required static package

Implement the smallest coherent package with exact naming chosen once and then hash-bound across all
consumers:

1. A trusted V03 route/blueprint JSON that independently locks product/configuration/variant, source
   rows and hashes, 972 unique XY assignments (81 per cell), +Z axes, P007 diameter, C016 length,
   exact expected topology/connectivity, roles, native/reopen/STEP bbox, analytic volume, tolerances,
   and claim enums. Expected values must not be copied from producer observations.
2. A generic-enough V03 validator plus positive and fail-closed negative tests. It must verify one
   BODY, closed/manifold/single-piece, independent expected bbox/analytic-volume closure for native,
   native reopen, and STEP reopen, 972 unique finite cylindrical throats with exact XY/cell/axis/
   radius/z-span ownership, 4 inlet and 1 outlet roles, all 12 cells connected to the outlet, and
   empty missing/unexpected/duplicate/orphan/dangling sets with assignment solution count exactly 1.
3. One reviewed SpaceClaim producer script below `automation/ansys/approved/006/`. It must construct
   the single continuous pilot fluid body, save native and STEP, reopen both, and emit inventory,
   sidecar, detached binding, source chain, and actual size/SHA evidence. Do not use global face count
   978 as a substitute for reconstructing the 972 finite-throat semantics.
4. One reviewed PyFluent watertight-meshing consumer script below `approved/006/`. It may only import
   the exact-byte predecessor STEP and reconstruct roles. The future runtime is limited to one fluid
   region, 4 inlets, 1 outlet, nonempty surface/volume mesh, no unassigned/orphan regions, and basic
   mesh-validity observations. It must not set materials or physics, initialize, iterate, solve, or
   add license-selection flags.
5. Exactly two new pilot profiles in
   `airjet-simulation/automation/ansys/profiles.json`: producer and consumer. Use only the existing
   profile schema to pin engine, scripts, SHA256, timeout, output root, reports, and exact predecessor
   contract. Lock v261/watertight mode in the frozen consumer script plus policy, and lock the
   dependency bundle through the MCP dependency allowlist/manifest plus policy. Do not add invented
   profile fields or register formal nine-variant 006 profiles.
6. A deterministic two-stage runner and pure guard test. Preflight must require signed clean 0/0 Git,
   trusted route/profile/script hashes, and fixed case/output identities before MCP use. Producer
   failure keeps consumer NOT_RUN. Once any job is submitted, missing or invalid identity, terminal
   state, manifest, report, assertion, or hash is FAIL, never NOT_RUN; cancel any still-running job in
   `finally` and preserve partial evidence.
7. A fixed Windows runtime prompt. It must permit only the new runner after static checks and must
   keep ANSYS execution outside this Mac task.
8. Wire exact route/validator/test/scripts/runner/guard/profile dependencies into MCP static policy,
   Python audit, PowerShell audit, and the skill manifest/install/bootstrap integrity consumers where
   applicable. Preserve all existing native, split-STEP, semantic, evidence, and Gate invariants.

## Mandatory negative coverage

Reject at least: G2 or wrong product/configuration/variant; C016 relabeled D or product fact; changed
0.10/range; 971/973/duplicate/wrong-XY/wrong-cell throats; wrong diameter/length/axis/z-span; two
bodies, open/nonmanifold/multiple-piece geometry; native/reopen/STEP bbox or analytic-volume tamper;
broken 4/1 roles or cell-to-outlet path; stale, tautological, raw-file, predecessor, job, case, Git,
profile, script, or artifact hashes; substituted
STEP; wrong Fluent version/mode/process count; any license argument; region count not 1; empty or bad
mesh; and any PASS report claiming P1, formal 006, physics, pressure, flow, thermal, or product truth.

## Claim ceiling

The strongest future statuses are:

```text
PRODUCER=PASS_PRELIMINARY_V03_FINITE_THROAT_GEOMETRY
CONSUMER=PASS_PRELIMINARY_V03_WATERTIGHT_MESH_SMOKE
SUITE=PASS_PRELIMINARY_V03_ROUTE
```

Even those would prove only that this C/P/I candidate representation survived this native-to-STEP-
to-PyFluent meshing route in one pilot. They do not prove product internal dimensions/count/layout,
native attach or Named Selection transfer, formal 006, P1, mesh independence, CFD, pressure/flow,
thermal performance, or physics. Keep `P1-P6=NOT_RUN`.

## Freeze checks and handoff

Run focused validator/runner tests, all existing native/split/semantic guards, MCP policy, generator
checks, both project audits, and `git diff --check`. Use DeepSeek Pro and Flash in parallel for
read-only staged-diff review; Codex must independently verify every finding. Remove cache artifacts.
Commit one linear Mac-signed result and push normally. No amend, reset, rebase, force push, skill
installation, ANSYS, or modification of `WINDOWS_TASK.env`.

Report exactly:

```text
V03_STATIC_PACKAGE=PASS|FAIL
BASE_COMMIT=cfbffdc6a63563fd22fe422bce943708c2a622cd
PRODUCT=AIRJET_MINI_GEN1
C016=0.10_MM_C_CAD_PLACEHOLDER_PRODUCT_FACT_FALSE
PROFILES_ADDED=2|FAIL
STATIC_TESTS=<literal>
MCP_POLICY=<literal>
PYTHON_AUDIT=<literal>
POWERSHELL_AUDIT=<literal>
DEEPSEEK_PRO=<literal>
DEEPSEEK_FLASH=<literal>
ANSYS_EXECUTION=NOT_RUN
FORMAL_006=NOT_RUN
P1-P6=NOT_RUN
GIT_READY=<full signed Mac commit|NOT_COMMITTED>
SIGNATURE=GOOD|FAIL
CLEAN=true|false
AHEAD_BEHIND=0/0|<literal>
```

Do the implementation now; do not return another planning-only response.

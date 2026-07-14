# Automation evidence for AirJet gates

## 005 Student capability smoke

Require independently terminal jobs and artifacts for:

- SpaceClaim parameterized solid/cavity, inlet/outlet, Named Selections, connected fluid volume,
  native save, STEP round trip, and transfer input;
- Workbench geometry and Named Selection transfer;
- Mechanical minimal static solve, result-table export, modal/harmonic route, and at least one
  usable piezoelectric or coupled-field route;
- Fluent one-core launch, model availability, minimal flow solution, mass balance, case/data save,
  and explicit four/eight-core attempts.

The MCP job result is execution evidence only. Parse the required 005 report literally. Keep
`P1_STAGE_GATE=NOT_RUN` regardless of the smoke result.

Use these automation result states consistently:

- `PASS_CONTROL`: the official API launched, answered deterministic assertions, and exited; no
  engineering capability or stage Gate is implied.
- `PASS_PARTIAL_CAD_CAPABILITY`: the fixed script-rebuild, geometry, save/reopen or transfer
  assertions for the declared partial CAD profile passed; native driving parameters and the full
  005 CAD readiness contract remain blocked unless separately proven.
- `PASS_005_CAPABILITY`: the corresponding 005 geometry, transfer, solve, or conservation
  assertions and required artifacts passed.
- `FAIL_DIRECT`: the tested route itself failed.
- `BLOCKED_UPSTREAM`: the route was not testable because a required earlier artifact failed.
- `NOT_RUN`: no attempt was made.

Batch/API evidence is technically valid even when no user watches a GUI. Record
`VISIBILITY=NOT_USER_OBSERVED`. Do not translate that to `GUI_VISIBLE=PASS`, and do not infer a
model's availability merely from a menu name or API node; the stated 005 assertion must run.

## 006 full-product CAD

Use the same master to generate all nine rows in `p1_model_form_variants.csv`. Every output must
cover the complete external envelope, all modeled cells, four candidate intake vents, top plenum,
perimeter transfer gaps, bottom chambers, actual orifice throats, full impingement channel,
manifold, and one product outlet. Preserve all evidence classes and R0 branch identifiers.

Require native CAD, STEP, fluid volume, Workbench project, scripts, logs, screenshots, parameter
diffs, connectivity checks, Named Selection cardinalities, and SHA256 manifests. The 006 result is
at most `PENDING_PEER_REVIEW`.

## 007 independent review

Recompute contract hashes and all 252 evidence rows without trusting 006 summaries. Verify six
native files in the official application when technically possible. Only the independent finalize
workflow may recommend a P1 Gate result.

## P2-P5

- P2: require material-stack candidates, mesh/modal convergence, harmonic displacement field, and
  electrical/mechanical power accounting.
- P3: require time-step/mesh independence, periodic stability, mass conservation, and a calibrated
  single-cell transfer relation. This is a calibration submodel, not the product main model.
- P4: require all cells and full intake-to-outlet flow, phase cases, flow/pressure curves, and
  pressure-capability scans.
- P5: require spreader/TIM/heat source/self-heating, full CHT conservation, and the 5.25/4.25 W
  thermal account.

Never promote `NOT_RUN`, missing native output, unconverged results, or a process-only observation
to PASS.

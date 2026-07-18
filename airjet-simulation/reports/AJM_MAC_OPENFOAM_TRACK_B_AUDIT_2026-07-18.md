# AJM Mac OpenFOAM Track B readiness audit — 2026-07-18

> Role correction: this was a one-time read-only Mac readiness audit created under a superseded task assignment. Windows Codex B owns and executes the OpenFOAM track; Mac does not own either solver track.

## Result

`TRACK_B_AUDIT=COMPLETE`

`MAC_TRACK_B_TOOLING=TOOLING_NOT_INSTALLED`

`OPENFOAM_TOOLING_SMOKE=NOT_RUN`

`P3_STAGE_GATE=NOT_RUN`

`P4_STAGE_GATE=NOT_RUN`

`P5_STAGE_GATE=NOT_RUN`

`MEMBRANE_PARAMS_JSON=NOT_CREATED`

`CELL_RESULTS_JSON=NOT_CREATED`

`AIRJET_PRODUCTION_SOLVE=NOT_RUN`

This audit establishes a reproducible starting boundary only. It does not validate
AirJet geometry, boundary conditions, flow, heat transfer, or any P3-P6 physics.
The full AirJet Mini Gen1 product remains the formal target; a single-cell model is
calibration-only.

## Task and preflight boundary

- Signed task commit: `52dc8e9cc3b6305368f00425b7b37e4cd0c4c26f`.
- Local `HEAD` and `origin/main` tracking ref matched that exact commit; branch was
  clean `main`, index and worktree were clean, and the local comparison was `0/0`.
- `git verify-commit` reported a good signature from the trusted Windows peer key.
- Remote is the trusted private repository through
  `ssh://git@ssh.github.com:443/superboynick/win-mac-dual-channel.git`.
- The signed watcher launch stated that the remote/task was revalidated immediately
  before launch. A second in-session `git fetch` could not write `.git/FETCH_HEAD`
  under the read-only Git sandbox, and `git ls-remote` could not resolve the network
  host. Therefore no second live-remote check is claimed.
- The repository-tracked project audit returned `PASS` before edits:
  `required_files=163`, `manuals=7`, `csv_files=30`. The older installed skill copy
  returned `FAIL` against newer P1/ANSYS contracts and is not treated as current.

## Read-only Mac inventory

Observed on 2026-07-18 without installation, sign-in, service startup, or system
configuration changes:

| Item | Observed state |
|---|---|
| Host | macOS 27.0 build 26A5368g, Darwin 27.0.0, arm64 |
| CPU | 10 physical / 10 logical cores |
| Memory | 16 GiB installed; `memory_pressure -Q` reported 64% free |
| Free disk | about 57 GiB on the macOS data volume |
| Docker CLI / Docker.app | not found |
| Colima | not found |
| OrbStack | not found |
| Podman / Lima | not found |
| Canonical Multipass | not found |
| Native OpenFOAM commands | not found (`foamVersion`, `blockMesh`, `checkMesh`, `foamRun`, common solvers) |

Literal conclusion: `TOOLING_NOT_INSTALLED`. Its absence does not block this audit,
but it prevents an OpenFOAM smoke or any OpenFOAM engineering run.

## Repository evidence audit

Formal truth is set by `checklists/full_product_stage_gates.md`: every P3, P4, and
P5 checkbox remains unchecked.

The current 34,883-cell Fluent artifact is a diagnostic failure, not an AirJet
product-flow mesh. Its own interpretation records a single actuator-gap tile with
used-node bounds `X=[-10.75,-3.75]`, `Y=[-14.375,-7.375]`,
`Z=[1.6575,1.9325] mm`, only one interior and one generic wall face zone, and the
literal classifications `REGION_SELECTION_FAIL_ACTUATOR_GAP` and
`BOUNDARY_SEMANTICS_COLLAPSED`. It does not contain the complete product inlet,
distribution, orifice, impingement, exhaust, and thermal path.

The committed Fluent transcripts for the v4/v5 case/data attempts state
`This case has no inlets & no outlets`; their zero-velocity residual histories and
50/100 iterations therefore do not show driven-flow convergence. Boundary reassignment
attempts failed or left the same closed wall-only topology. The accompanying
`result*.json` value `DONE` is process completion, not an engineering pass. The
repository does not provide a sufficient identity manifest to promote the task's
v4/v5 labels into validated case versions.

The C7/V8 work remains failed or unresolved diagnostic evidence. Repetition of the
same region-selection failure can show deterministic tooling behavior, but cannot
validate its geometry or physics. The current mesh study also is not grid independent:
the coarse artifact records only a file-size `PASS`, while medium and fine launches
failed. There are not three accepted grids or any compared P3/P4 physical observables.

Consequently these claims elsewhere are stale or unsupported:

- `PROJECT_STATUS.md` labels the page as live P3 and calls the 50 iterations
  converged even though the boundary condition and domain are invalid. This file is
  outside the authorized edit set and was not changed.
- `DUAL_TRACK_PLAN.md` previously collapsed installation, single-cell calibration,
  full-product airflow, and CHT into undifferentiated pending tasks, and described
  OpenFOAM as effectively unconstrained before any local tooling test.
- `coupling/COUPLING_PROTOCOL.md` says both agents run on Windows and suggests a
  placeholder AirJet cell can feed direct product validation. It is historical and
  outside the authorized edit set; the correct dependency chain is below.
- Only `membrane_params_schema.json` and `cell_results_schema.json` exist. Neither
  `membrane_params.json` nor `cell_results.json` exists, and no tracked OpenFOAM case
  or prior OpenFOAM run evidence existed at this audit's input commit.

## Evidence-class boundary for Track B

- `D` (locked direct product evidence): 27.5 x 41.5 x 2.8 mm envelope; 1 W maximum
  electrical power; 4.25 W net heat removal and 5.25 W total heat at 85 C die / 25 C
  ambient; 1750 Pa is pressure capability with no public flow at that point.
- `P` (patent candidates, not exact Mini facts): actuator length/thickness/frequency/
  amplitude, chamber heights, orifice width/separation/open area, impingement gap,
  vent and anchor dimensions, and jet-speed embodiments.
- `I` (explicit inference): digitized intermediate performance-curve points, official
  image proportions, active-area fraction, and drawn vent-object observations.
- `C` (calibration/placeholder): cell count/layout, damping, unresolved layer
  thickness allocations, spreader conductivity, TIM resistance, and self-heat map.
- `U` (unresolved): actuator material stack, exact internal topology, and any other
  solver input not yet supported or calibrated. A tooling tutorial contains no AirJet
  input; any future placeholder AirJet geometry or boundary remains diagnostic `U`.

## Narrow deterministic smoke route

### T0 — tooling readiness only

After separate user authorization, use the current official macOS route: Canonical
Multipass with an Ubuntu arm64 guest and the signed OpenFOAM Foundation v14 Ubuntu
package. OpenFOAM v14 was released on 2026-07-14 and its official macOS page directs
Apple Silicon users to Multipass, which automatically selects arm64 packages:
[OpenFOAM v14 macOS](https://openfoam.org/download/14-macos/) and
[OpenFOAM macOS route](https://openfoam.org/download/macos/).

Do not install during this task. Before a later install, free additional disk or
approve an external-volume strategy. For a tooling-only VM on this 10-core/16-GiB
host, a conservative proposal is 6 cores, 8 GiB RAM, and 30 GiB disk, leaving host
headroom; this is not a production sizing claim. Record the Multipass version, Ubuntu
image release, architecture, `openfoam14` package version, repository signature
verification, and installed file hashes. Do not use an unpinned mutable container tag.

Then run `automation/openfoam/smoke_openfoam14_tooling.sh` inside a configured
OpenFOAM v14 shell. It copies the installed official `pitzDailySteady` tutorial to a
temporary directory, runs `blockMesh`, `checkMesh`, and `foamRun`, requires a clean
solver end marker, and deletes the temporary case. It writes no AirJet case and
cannot advance any stage gate. Until executed: `OPENFOAM_TOOLING_SMOKE=NOT_RUN`.

### T1 — P3 single-cell calibration

Only after P1 provides selected-layout chambers/orifices and P2 provides an audited
displacement field, create the compressible transient dynamic-mesh cell model. Run
three grids, three time steps, periodic-stability and mass-balance checks, and produce
the pressure-flow-displacement map, backflow ratio, jet velocity, and reduced
interface. This is calibration-only and may advance P3 only after every P3 gate passes.

### T2 — P4 full-product airflow

Only after P3, use the complete P1 fluid volume and all cells, intake distribution,
orifice plate, impingement channel, exhaust path, phase cases, and at least one
no-symmetry full-product case. Demonstrate <0.5% mass error and explain cell
starvation. Keep 1750 Pa as a pressure-capability check, not a fabricated flow point.

### T3 — P5 full-product CHT

Only after P4, add chip/TIM/spreader/product solids and keep `Q_chip=4.25 W` separate
from up to `P_airjet=1 W`, with `Q_total=5.25 W`. Require <1% energy error and both
fixed-temperature and fixed-power checks. No CHT case or result exists yet.

## Final audit boundary

This task ran no production solve, installed no software, changed no system settings,
and created no mesh, field, container, archive, binary, or coupling output. P3-P6
remain unchanged. The source-only smoke launcher passed `bash -n`, then exited before
case creation with `TOOLING_NOT_INSTALLED missing=foamVersion` and code 20; therefore
the actual OpenFOAM tooling smoke remains `NOT_RUN`.

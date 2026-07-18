# AJM Windows Codex B OpenFOAM task card — 2026-07-18

```text
TASK_ID=AJM-B-OPENFOAM-T0-20260718-001
OWNER=B
SCOPE=Close duplicate-work archive; prepare and execute the independent Windows OpenFOAM T0 line without modifying ANSYS assets
INPUT_COMMIT=bda8341bc9b9a188d2a39dcf5ae4cbd850e13f73
ESTIMATED_EFFORT=3 hours for archive plus source-only T0 preparation; tooling installation/runtime ETA requires authorization
STARTED_AT_UTC=2026-07-18T13:17:00Z
ETA_UTC=2026-07-18T16:30:00Z for source-only preparation
CHECKPOINTS=2026-07-18T13:30:00Z=archive index;2026-07-18T14:00:00Z=Windows tooling inventory;2026-07-18T16:30:00Z=T0 source and fallback preparation
DELIVERABLES=unified archive index;Windows T0 inventory;validated smoke source;B execution and fallback plan;external-artifact root
ACCEPTANCE=clean isolated B worktree;project audit PASS;archive hashes reproducible;no ANSYS files edited;T0 truth recorded without overstating P3-P6
BLOCKERS=Windows has no configured WSL distribution, Docker/Podman or native OpenFOAM; installation/reboot/service mutation needs separate authorization;AirJet P3 also waits for valid P1 chamber/orifice geometry and A/P2 displacement
SAFE_BACKLOG_NEXT=schema validators;case-source lints;conservation and periodicity post-processing;run-manifest templates;official tutorial smoke wrapper
FILES_OWNED=airjet-simulation/automation/openfoam/;airjet-simulation/reports/AJM_WIN_*OPENFOAM*;this task card;B-only external artifacts
EXTERNAL_ARTIFACT_ROOT=D:\AirJet_P1\openfoam\codex-b-openfoam-20260718
```

## Execution boundary

B owns only the independent OpenFOAM reproduction line:

`T0 tooling smoke -> P3 cell CFD -> P4 full-product airflow -> P5 full-product CHT -> P6 cross-validation`

A remains the only ANSYS owner. Mac remains coordinator/reviewer/Git integrator. B
does not edit `automation/ansys/`, approved profiles, A evidence, A worktree or the
dirty integration checkout.

Formal project state remains P0 PASS and P1-P6 NOT_PASSED. The complete AirJet Mini
Gen1 product is the target; single-cell work is calibration-only.

## Primary route

1. Keep the clean B worktree and external artifact root isolated.
2. Inventory Windows tooling without installation or service changes.
3. After explicit installation authorization, pin one official OpenFOAM Foundation
   v14 Windows environment: WSL2, Ubuntu 22.04 LTS and the signed `openfoam14`
   package. Record distribution, package, signature and version identities.
4. Run the repository's official-tutorial-only T0 smoke. T0 proves tooling only.
5. While P1/P2 inputs are absent, prepare validators, generators and post-processing
   without inventing AirJet physics.
6. Accept A inputs only after schema, units, source commit and artifact hashes pass.
7. Execute P3-P6 in Gate order; never use a placeholder solve to skip an upstream Gate.

## Plan B / fallback route

The fallback is chosen before installation so failure does not trigger ad-hoc tool
changes. Official references are
<https://openfoam.org/download/windows/>,
<https://openfoam.org/download/14-ubuntu/> and
<https://learn.microsoft.com/windows/wsl/install>.

- Primary: enable the official WSL2 route and install `Ubuntu-22.04`, then add the
  Foundation package repository and install `openfoam14`.
- Plan B: when Store/network installation is unavailable, use Microsoft's official
  offline WSL package and Ubuntu `.wsl` distribution route, then install the same
  signed `openfoam14` package from an approved local package cache/mirror.
- A container or native Windows port is not an automatic fallback. It needs a new
  source/provenance review and explicit authorization; mutable tags are forbidden.
- If neither official WSL route is authorized or hardware virtualization is unavailable, stop
  runtime work at `TOOLING_NOT_INSTALLED` and continue the source-only backlog. Do not
  install unofficial Windows ports or call static checks a tooling smoke.
- If T0 fails twice without a discriminating change, stop retries, preserve logs and
  perform root-cause analysis before changing route.
- If P1/P2 inputs remain unavailable, do not create a placeholder AirJet P3 case.
  Continue schema, conservation, periodic-stability and evidence-template work.

No route may silently change OpenFOAM distribution, major version, package source,
geometry, boundary conditions or evidence classification.

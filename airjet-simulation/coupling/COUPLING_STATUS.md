# Coupling Status Board

Last updated: 2026-07-18
Read by BOTH Codex instances before starting any coupled work.

---

## Codex A — ANSYS Track

| Item | Status |
|---|---|
| P0 evidence freeze | DONE |
| P1 CAD geometry | NOT RUN |
| Mechanical modal analysis | NOT RUN |
| Mechanical harmonic response | NOT RUN |
| Wrote membrane_params.json | NOT YET |
| Validated cell_results.json | NOT YET |

Currently doing: _waiting for Codex A to start_

---

## Codex B — OpenFOAM Track (Mac audit owner for this task)

| Item | Status |
|---|---|
| Mac OpenFOAM tooling | TOOLING_NOT_INSTALLED |
| Deterministic non-AirJet tooling smoke | NOT_RUN |
| OpenFOAM AirJet source/case | NOT_CREATED |
| P3 single-cell calibration run | NOT_RUN |
| Wrote cell_results.json | NOT_CREATED — schema only |
| P4 full-product airflow | NOT_RUN |
| P5 full-product CHT | NOT_RUN |

Currently doing: _audit complete; installation and AirJet solve were not authorized_

---

## Messages

_(Write short messages here. Sign with `A:` or `B:` and timestamp.)_

---

## Shared Files

| File | Owner | Status |
|---|---|---|
| `coupling/membrane_params.json` | A | NOT_CREATED — schema only |
| `coupling/cell_results.json` | B | NOT_CREATED — schema only |

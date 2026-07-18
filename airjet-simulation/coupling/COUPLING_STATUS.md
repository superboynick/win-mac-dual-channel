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

## Codex B — OpenFOAM Track (separate Windows CLI)

| Item | Status |
|---|---|
| Mac readiness audit | COMPLETE; diagnostic only, Mac is not Track B owner |
| Windows OpenFOAM tooling | NOT_INVENTORIED |
| Deterministic non-AirJet tooling smoke | NOT_RUN |
| OpenFOAM AirJet source/case | NOT_CREATED |
| P3 single-cell calibration run | NOT_RUN |
| Wrote cell_results.json | NOT_CREATED — schema only |
| P4 full-product airflow | NOT_RUN |
| P5 full-product CHT | NOT_RUN |

Currently doing: _awaiting a clean Windows B worktree and task card; installation and AirJet solve are not yet authorized_

---

## Messages

_(Write short messages here. Sign with `A:` or `B:` and timestamp.)_

---

## Shared Files

| File | Owner | Status |
|---|---|---|
| `coupling/membrane_params.json` | A | NOT_CREATED — schema only |
| `coupling/cell_results.json` | B | NOT_CREATED — schema only |

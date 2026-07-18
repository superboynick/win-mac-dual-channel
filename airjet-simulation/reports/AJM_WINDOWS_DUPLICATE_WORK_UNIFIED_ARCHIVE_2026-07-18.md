# AJM Windows duplicate-work unified archive — 2026-07-18

## Result

`DUPLICATE_WORK_ARCHIVE=INDEXED`

`ANSYS_OWNER=A_ONLY`

`OPENFOAM_OWNER=B_ONLY`

`INTEGRATION_MAIN=RESERVED_FOR_HANDOFF`

`A_ACTIVE_PROCESS_INTERRUPTED=NO`

`P1_P6_GATE_EFFECT=NONE`

This record unifies the recoverable Windows artifacts created while two Codex
sessions overlapped on ANSYS/Fluent. It is an archive and ownership correction,
not engineering acceptance. Process completion, solver iterations and archived
case/data files do not advance P1-P6.

## Git line reconciliation

| Line | Worktree / branch | Frozen tip | Owner and allowed scope |
|---|---|---|---|
| Integration | `C:\Users\admin\win-mac-dual-channel` / `main` | `bda8341bc9b9a188d2a39dcf5ae4cbd850e13f73` | Mac/Git integration and watcher handoff only |
| A | `C:\Users\admin\win-mac-dual-channel-a` / `codex-a-ansys-20260718` | `c4195a63dda054296ef5c2fb4af7caee6777f406` | ANSYS CAD, Mechanical, Fluent and A evidence only |
| B | `C:\Users\admin\win-mac-dual-channel-b` / `codex-b-openfoam-20260718` | input `bda8341bc9b9a188d2a39dcf5ae4cbd850e13f73` | OpenFOAM tooling and P3-P6 reproduction only |

Both frozen commits have good repository-trusted SSH signatures. At reconciliation,
local `main` and `origin/main` were `0/0`; the B worktree was clean and also `0/0`.

The integration checkout still reported the A-owned consumer as modified while an
A Fluent/PyFluent process was active. `git diff` contained no semantic hunk, while
the working-copy SHA256 was
`a03cb6e7bc3b0bfc212cc1063b71056059876c5a81fdae02ce4b13d5fce385d3`.
The observed warning indicates line-ending normalization state. The file was copied
to the external archive and was not restored, staged or overwritten during the
active A run. Until A releases it and the integration checkout is clean, watcher
state must remain fail-closed; no one may report it as running.

The byte-level Git diagnosis is conclusive rather than inferential:

- `.gitattributes` resolves to `text eol=lf` for the consumer;
- `git ls-files --eol` reports `i/lf w/crlf`;
- both `git diff --binary` and `git diff --ignore-cr-at-eol` are empty;
- the HEAD blob and normalized working-tree Git object are both
  `f06a92c6b9ea62d28f22ff54bc2dbfefe930987b`;
- `main` and `origin/main` both resolve to
  `bda8341bc9b9a188d2a39dcf5ae4cbd850e13f73`.

Therefore the reported modification is an EOL/stat state, not a semantic Python
change. That still does not authorize B to mutate A's file or the integration index.
The closure procedure is in
`AJM_GIT_DIRTY_MAIN_RECONCILIATION_RUNBOOK_2026-07-18.md`.

## External archive identity

Canonical root:

`D:\AirJet_P1\external-evidence\workspace-recovery-20260718T075804Z`

The root contains 223 files totaling 200,163,841 bytes. For each directory below,
`tree_sha256` is SHA256 over UTF-8 lines
`relative/path|size_bytes|file_sha256`, sorted by full path and joined with LF.
This makes the compact Git index independently checkable without committing solver
artifacts.

| Directory | Files | Bytes | tree_sha256 |
|---|---:|---:|---|
| `files` | 40 | 75,381,628 | `8db44479c46bb0704fb137774c0594c37436b325503fcef2a5189e10d5bacdc4` |
| `increment-20260718T080524Z` | 6 | 44,127 | `b61e47e5fad8a89dc6fba28c35a0d96e3a1ce2a938ba2e152d7b7bc05a2d2913` |
| `increment-20260718T093100Z` | 8 | 210,847 | `89f504f78abb3fea4de128189b043fe03cbd9dbc11dc01a61e6a13f3a9e2da42` |
| `increment-20260718T094800Z` | 14 | 174,744 | `879d5e6070fc64b0ee8eba1262f9395e2f05c770510e52d7c2321e90a3424b7d` |
| `increment-20260718T095600Z` | 19 | 38,311,580 | `48999739e714135e851ddc41323260495ffa20dab52dfd786d703f3956676e21` |
| `increment-20260718T095900Z` | 10 | 43,237,389 | `7df5c34a54cda41d1c0f1251342e46f00c03f983abf017296f0c2cd64e23d5c7` |
| `increment-20260718T101000Z` | 115 | 42,285,308 | `fa1214459234b59130262b5d5b2b8b85118612c92b699d01e1166eac04631f1c` |
| `increment-20260718T101600Z` | 6 | 208,137 | `3fc9dcb91026341cc3999025a1fbcaa324c4fcff70af246f750f446c6fb2ebcf` |
| `increment-20260718T102000Z` | 3 | 156,411 | `f3d3a9a2fa6e2d179d06d3d48cb0bcc8382059cc2c5422c25bef012c3d1ca044` |
| `increment-20260718T132155Z` | 2 | 153,670 | `2c8d9b9d9529deab4d922f7818cda692d1c8fefedca3fed932061bc46057844b` |

The last increment adds the two live-reconciliation snapshots:

- `a_diagnostic_cfd_200iter.py`, 2,128 bytes, SHA256
  `497497ae7abce87707299b2a10cae39d90c79d1d88a78583a6b3125edf278bdb`;
- `a_main_worktree_consumer_snapshot.py`, 151,542 bytes, SHA256
  `a03cb6e7bc3b0bfc212cc1063b71056059876c5a81fdae02ce4b13d5fce385d3`.

## Interpretation and de-duplication

- `increment-20260718T101000Z` is the formal A C7 two-stage evidence package. Its
  producer completed; its consumer stopped at `workflow.create_regions()` because
  region `dead0` already existed. This is the canonical formal blocker evidence.
- Earlier root-level mesh/solve scripts, transcripts and v4/v5 case/data are retained
  as diagnostics. They must not be rerun unchanged or promoted into P3/P4 results.
- The active `cfd_200iter.py` applies a fixed 12 m/s velocity inlet and steady
  200-iteration setup. It may be an A-side solver diagnostic, but it is not the P3
  compressible transient membrane-driven calibration required by the project.
- B will read only schema-valid, hash-bound A handoffs. B will not repair, replace or
  reinterpret A artifacts in place.

## Closure rules

1. A finishes or deliberately stops its current run, archives final outputs, and
   performs all future ANSYS work only in the A worktree.
2. The owner of the integration checkout verifies the consumer snapshot, returns
   `main` to a clean state without discarding unarchived bytes, then explicitly
   restarts the manual watcher. B does not mutate this checkout.
3. B performs all OpenFOAM work in the B worktree and external root
   `D:\AirJet_P1\openfoam\codex-b-openfoam-20260718`.
4. Git stores source, reports and compact manifests only. CAD, meshes, case/data,
   fields, transcripts, containers and native projects stay outside Git.
5. Any future run needs one task ID, owner, case ID, hypothesis and acceptance
   condition. A second implementation is permitted only as explicit cross-validation.

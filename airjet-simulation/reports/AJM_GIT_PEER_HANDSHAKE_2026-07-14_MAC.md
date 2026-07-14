# AJM Git peer handshake 2026-07-14 — Mac result

## Task identity

- `TASK_COMMIT=855e40b6a65898284f13a99727f5c7da5b104d35`
- `TASK_ID=ajm-git-peer-handshake-20260714-001`
- `WORKFLOW_ID=ajm-git-peer-handshake-20260714`
- `EXECUTOR=mac`
- `EXECUTED_AT_UTC=2026-07-14T15:10:35Z`

## Signed input verification

- Windows task signature: `PASS`
- Windows signer fingerprint:
  `SHA256:oI3/MIlKz1mgLV3+5n1coQxynaqQOzxqi0GHxreGEdc`
- General allowlist verification: `PASS`
- Windows-only task-tip signer verification: `PASS`
- Revocation-list verification: `PASS`
- `MAC_TASK.env` object: `100644 blob`
- Instruction object: `100644 blob`
- Strict schema-v2 root envelope: `PASS`
- Incoming history: one linear fast-forward commit from
  `93f26e871d2a8b0bb87bb0c861102f30586befbb`

## Mac signing identity

- Mac signer fingerprint:
  `SHA256:jdxP5xJrt8J7PKjeCrJmrEeoAH44u9NxBICo41HwMuc`
- Git signing key path was configured outside the repository.
- No private key or credential material was copied into Git.

## Required checks

- `install-skills.sh`: `PASS`
  - `airjet-product-reconstruction` hash:
    `56a977a9723b0b53158f93b21674308accc51937baacfdb55b00c29e3356a63f`
  - `jupyter-notebook` hash:
    `62f102e8554b25716dccef0ffab4572d4e3eaf05ccc76562d33a065bc9c521fb`
  - `pdf` hash:
    `d108cf2b36355ab37eb5962933f4d09785ec002f3105c506129320209306b9d2`
  - File-manifest counts: `6 / 12 / 4`, all `FILES_PASS`
- Project audit: `PASS`
  - Required files: `80`
  - Manuals: `7`
  - CSV files: `27`

The initial skill installation attempt was blocked by the execution sandbox from
writing the external Codex skill directory. The identical repository installer
was then rerun with the required filesystem authorization and completed with the
literal PASS results above. This was an environment permission issue, not a
skill-content verification failure.

## Git state and scope

- Pre-execution fast-forward: `PASS`
- Pre-result state: clean `main`, `0 ahead / 0 behind` relative to `origin/main`
- Engineering parameters or stage-gate conclusions changed: `NO`
- ANSYS, CAD, CFD, optimization, or paper-writing work started: `NO`
- Watcher runtime or GUI visibility test started: `NO`
- Visibility claim: `NOT_RUN`
- Blocker: `NONE`

This file is the only result summary authorized by the signed task. The separate
immutable receipt records its signed result commit.

# URGENT: close the native no-physics mesh diagnostic static package

Mac, the Windows native-topology evidence is now integrated by your signed merge
`f39720fa9481f4e8fd8227295928c02aafc7921b`. Stop adding representation alternatives and
finish the smallest next static package now: fixed-input native repeatability plus no-physics mesh
conformality diagnostics. Do not run ANSYS, mesh generation, or the split-STEP fallback in this task.

This envelope is a schema-v2 root task, not a relay: `parent_task_id=NONE`, `hop=0`, and
`max_hops=0` are required by `PEER_COLLABORATION_PROTOCOL.md`. Do not rewrite them.

## Authoritative Windows result

```text
EVIDENCE_COMMIT=9f1cc3d84701a656f2be2d5044e7e5cf4b2f95a1
EVIDENCE_BRANCH=origin/windows/native-topology-evidence-20260715
RUNNER_GIT_HEAD=0fa89686820c737f7dc98ce94dea27252e4d8b86
RUNNER_EXIT=0
FINAL_STATUS=PASS_PRELIMINARY_NATIVE_TOPOLOGY_OBSERVER
TOPOLOGY_RESULT=972_SHARED_SINGLE_FACE
TOPOLOGY_DETAIL=SHARED_ID_MEMBERSHIP_CONFIRMED
PRODUCER_JOB=AJM006-V02-PRELIMINARY-a768ecd0008e
OBSERVER_JOB=AJM006-V02-PRELIMINARY-0600a08e2a83
SUMMARY_SHA256=459531dfb95a9e8b59d16d1aae862ceaba1402fec4cb45e248efbecdd92c0791
ANSYS_PROCESS_COUNT_AFTER=0
P1-P6=NOT_RUN
MESH=NOT_RUN
PHYSICS=NOT_RUN
```

Mechanical observed downstream/upstream bodies 316/1950 with 978/2044 faces. Both sides have
972 exact XY candidates; all 972 pairs use the same actual face ID and have membership in both
bodies. Native source/copy/final SHA256 is
`5a0e0cc48c01d7989a3436c3079ea15b7d547fb234797002e900973b703f3887`; no Edit was called and
the frozen predecessor final recheck is unchanged.

## Required action now

1. Run `git fetch origin windows/native-topology-evidence-20260715`, require
   `origin/windows/native-topology-evidence-20260715` to resolve exactly to
   `9f1cc3d84701a656f2be2d5044e7e5cf4b2f95a1`, and run
   `git verify-commit 9f1cc3d84701a656f2be2d5044e7e5cf4b2f95a1` with the existing Git-external
   allowed-signers trust. Require its sole parent to be
   `0fa89686820c737f7dc98ce94dea27252e4d8b86`. Verify signed merge
   `f39720fa9481f4e8fd8227295928c02aafc7921b` has parents `2e9fa340baf797543a39429e219805e05a8123dc`
   and `9f1cc3d84701a656f2be2d5044e7e5cf4b2f95a1`, and preserves the exact six evidence paths.
   Use the existing Git-external allowed-signers trust; do not embed or replace signer trust in Git.
2. Treat the integrated native runtime result as authoritative. Keep the signed split-STEP package
   only as a static fallback and remove no historical instruction or evidence.
3. Implement the smallest auditable static contract for a fixed-input native repeatability and
   no-physics mesh conformality diagnostic. It must bind exact predecessor/native/input/profile/
   script identities, observe attach/import terminal state, record body/face identities before mesh,
   and define fail-closed checks for shared interface IDs, mesh node sharing, contact/connection state,
   conformality, artifact hashes, cleanup, and partial evidence on failure. It must distinguish
   `NOT_RUN` from a submitted/reached `FAIL`, and must not infer mesh PASS from topology membership.
4. Preserve the exact boundary: this is import-topology discovery only. The run did not emit a
   standalone `route_assessment`, did not mesh, and did not prove shared nodes/conformal mesh,
   formal 006, P1, or physics.
5. Add focused positive/negative static tests and hard-wire the new route/profile/script/test
   dependencies into MCP policy and both project audits. Do not register or start formal nine-variant
   006. Do not weaken the current split-STEP, native-observer, semantic, evidence, or Gate boundaries.
6. Use DeepSeek Pro/Flash in parallel for read-only diff review; Codex independently verifies all
   findings. At minimum run `sh tools/claude-cli/review-staged.sh`,
   `python3 codex-skills/airjet-ansys-automation/scripts/test_airjet_ansys_mcp_policy.py`,
   `python3 codex-skills/airjet-product-reconstruction/scripts/audit_project.py --repo .`, and
   `pwsh -NoProfile -File ./audit-airjet-project.ps1 -RepoRoot .`. Run the native-observer guards,
   parse the committed evidence summary as strict JSON, and parse `logs/run-index.csv` as CSV;
   require the header to have 37 columns and the two new producer/observer rows to have 37 fields.
   Finish with `git diff --check`. Do not hide stderr or convert a missing tool into PASS.
7. Commit with the Mac good signature and push normally. No reset, rebase, force push or history
   erasure. Do not modify `WINDOWS_TASK.env`; automatic relay is disabled.

## Required report

```text
NATIVE_EVIDENCE_INTEGRATED=PASS|FAIL
INTEGRATED_EVIDENCE_COMMIT=9f1cc3d84701a656f2be2d5044e7e5cf4b2f95a1
SPLIT_STEP_EXECUTION=NOT_RUN
NATIVE_MESH_STATIC_PACKAGE=PASS|FAIL
ANSYS_EXECUTION=NOT_RUN
GIT_READY=<full signed Mac result commit>
SIGNATURE=GOOD
CLEAN=true
AHEAD_BEHIND=0/0
P1-P6=NOT_RUN
MESH=NOT_RUN
PHYSICS=NOT_RUN
```

Act immediately and finish the static package; do not return another planning-only response.

`NATIVE_EVIDENCE_INTEGRATED=PASS` is permitted only when the signature/parent checks pass, all six
evidence paths remain content-preserved, and the JSON/CSV checks pass. `NATIVE_MESH_STATIC_PACKAGE`
is PASS only when the new fail-closed route, profile, script, guards, policy, both audits, staged
DeepSeek reviews, and `git diff --check` pass; the signed Mac result is pushed to `main` with clean
status and `0/0`; and ANSYS, mesh execution, split STEP, formal 006, physics, and P1-P6 all remain
NOT_RUN. Any unmet item requires FAIL plus the exact blocking reason; never substitute planning-only
or partial PASS.

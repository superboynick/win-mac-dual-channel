# Execute the recovered dual Windows harness

TASK_ID=`ajm-dual-windows-harness-execute-20260720-008`

This is the post-watcher-start execution task. Read and apply the complete ownership,
acceptance and 15/45/90-minute checkpoint contract in
`airjet-simulation/collaboration/instructions/ajm-dual-windows-harness-recovery-20260720-007.md`.

Before engineering work:

1. Confirm clean synchronized `main` at this signed task commit and official Windows watcher
   state/PID. Do not push `main`.
2. Stop the custom Git heartbeat loop. Do not create any new `windows-heartbeat-*.txt`
   receipt or heartbeat-only commit; process state belongs outside Git.
3. Publish separate A and B task cards and file leases on separate signed branches.
4. A runs official-MCP inventory/preflight against producer SHA `8f23d7d7...`, then the
   reviewed producer/native/STEP acceptance. B builds only the OpenFOAM rejection harness.
5. Report the first 15-minute checkpoint with expected versus actual time, evidence,
   blocker, next action and revised ETA.

The `a6a1e910...` producer hash and all vent-clipping variants are rejected. Do not update
the profile to match them and do not cherry-pick incident `d42630d`. Old-mesh CFD is invalid
for acceptance. P1--P6 remain `NOT_RUN/NOT_PASSED`.

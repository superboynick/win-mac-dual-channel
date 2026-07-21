# Install Windows-local A/B self-driver

TASK_ID=`ajm-install-ab-self-driver-20260720-014`

Install the reviewed Windows-local self-driver so Plan A and Plan B no longer depend on Mac
SSH or a new Git task to consume safe backlog work.

1. Verify clean signed main at this task tip and run watcher tests plus project audit.
2. Verify both external runners exist under `Downloads\AirJetGitWatcherReports` and contain no
   credentials. Do not print their full prompts into logs.
3. Run `tools\airjet-self-driver\windows\Install-AirJetABSelfDriver.ps1 -Minutes 5` from the
   interactive Limited Windows session.
4. Verify scheduled task `AirJetABSelfDriver` is Interactive, Limited, IgnoreNew, every five
   minutes, and invokes only the signed repository driver.
5. Verify one tick produces `AIRJET_AB_SELF_DRIVER.log`, never duplicates an active A/B
   runner, and starts a missing line from its independent external runner.
6. Report task definition, next run time, A/B runner PIDs, evidence ages and exact blockers.

The driver may fill idle time only with each line's safe external backlog. It must not modify
Git, task envelopes, CAD, profiles, keys, licenses or formal P1--P6 state, and must never
submit ANSYS/Mechanical/Fluent without a separate signed runtime authorization.

# Windows dual-track incident recovery and live report

You are the Windows incident coordinator. The user reports a major incident and has
explicitly requested Mac/Windows watcher coordination until it is resolved.

## Immediate safety boundary

Do not run `git reset`, `git clean`, `git stash`, `git rebase`, force push, checkout
overwrites, bulk deletion, process termination, reboot, package installation, ANSYS
solver execution, or OpenFOAM execution. Do not print, commit, or copy credentials,
licenses, API keys, or tokens. Preserve all unknown and native artifacts in place.

ANSYS remains A-only. OpenFOAM remains B-only. The integration checkout is for
coordination and handoff only. Do not edit A-owned engineering files from B or B-owned
engineering files from A.

## Read-only incident inventory

Inspect all three Windows worktrees if present:

- `C:\Users\admin\win-mac-dual-channel` (integration)
- `C:\Users\admin\win-mac-dual-channel-a` (A / ANSYS)
- `C:\Users\admin\win-mac-dual-channel-b` (B / OpenFOAM)

For each, record exact path, branch, HEAD, upstream, `git status --porcelain=v2
--branch`, ahead/behind, last signed commit, and changed/untracked paths. Record the
Windows watcher manager status, PID, state/detail, pending event, processed claim,
and last 50 watcher log lines. Record active Codex, Git, ANSYS/Fluent, OpenFOAM, WSL,
Docker and PowerShell processes without stopping them.

Determine what the user meant by the major incident from observable local state and
the current visible Codex sessions. Preserve exact error text and UTC timestamps.
If unknown bytes are at risk, copy only those bytes to a new timestamped directory
under `D:\AirJet_P1\external-evidence\incident-20260718`, then record file count,
size and SHA256. Never copy secrets or licenses.

## Allowed recovery

Only perform a recovery when all of the following are proven first: target owner is
known, no process is writing the target, bytes are externally preserved with hashes,
the recovery is non-destructive and reversible, and it does not cross A/B ownership.
Watcher restart is allowed only through the reviewed Windows manager and only when
the integration worktree is clean, synchronized, signed and has no pending conflict.
Otherwise stop and report the blocker; do not improvise.

Do not repeat the old C7 `dead0` run. A may resume ANSYS only after its worktree is
clean, it has fast-forwarded to signed `90b645a648204e64a8da11c1ce13ed9626421634`,
the approved profile hash passes, and the incident is closed. B must remain on its
OpenFOAM scope and must not install tooling without separate authorization.

## Git delivery and cadence

Create a new branch named `incident/windows-recovery-20260718-001` from the current
signed `origin/main` only if that can be done without overwriting a dirty checkout;
otherwise use a new clean worktree. Write one compact report at
`airjet-simulation/reports/AJM_WINDOWS_INCIDENT_RECOVERY_2026-07-18.md` containing:

- `INCIDENT_STATE=OPEN|RESOLVED|BLOCKED`
- exact observed failure and impact radius
- A, B, integration and watcher states
- preserved evidence paths and hashes
- actions taken, explicitly including destructive actions as `NONE`
- owner, next action, checkpoint and revised ETA
- P1-P6 Gate effect, which remains unchanged unless formal evidence proves otherwise

Commit with the trusted Windows signing key and push the incident branch. Push an
initial evidence report within 15 minutes. If unresolved, update the same report with
a new signed commit at each discriminating checkpoint no more than 30 minutes apart.
Never push directly to `main`; Mac performs review and integration.

Completion means the incident cause is evidenced, at-risk bytes are safe, A/B
ownership is restored, integration and watcher state are truthful, and a signed Git
report is available. Merely starting a process or obtaining exit code 0 is not
completion.

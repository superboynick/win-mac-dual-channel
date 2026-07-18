# AJM dirty integration-main reconciliation runbook — 2026-07-18

Use this only when the shared integration checkout is dirty in an A/B-owned path and
the watcher has failed closed. It does not authorize one owner to overwrite another.

## Diagnose without mutation

1. Record `git status --porcelain=v2`, `git rev-parse main`,
   `git rev-parse origin/main` and `git rev-list --left-right --count`.
2. For every dirty path, record `git check-attr -a`, `git ls-files --eol`,
   `git diff --binary`, `git diff --ignore-cr-at-eol`, the filesystem SHA256,
   `git hash-object` and the HEAD blob ID.
3. Snapshot every non-reproducible byte outside Git with size/SHA256 before any
   normalization action. Do not copy credentials, licenses or secrets.
4. Identify the task owner and any process using or generating the path. Do not stop
   the process or alter the file without that owner's release/sign-off.

## Current incident

Path:
`airjet-simulation/automation/ansys/approved/006/v03_pyfluent_watertight_mesh_consumer.py`

Observed state:

```text
main=origin/main=bda8341bc9b9a188d2a39dcf5ae4cbd850e13f73
attribute=text eol=lf
index_eol=lf
working_eol=crlf
HEAD_BLOB=f06a92c6b9ea62d28f22ff54bc2dbfefe930987b
NORMALIZED_WORKTREE_BLOB=f06a92c6b9ea62d28f22ff54bc2dbfefe930987b
git_diff_binary=EMPTY
git_diff_ignore_cr_at_eol=EMPTY
filesystem_sha256=a03cb6e7bc3b0bfc212cc1063b71056059876c5a81fdae02ce4b13d5fce385d3
archive_snapshot=increment-20260718T132155Z/a_main_worktree_consumer_snapshot.py
owner=A
```

This is an EOL/stat-only dirty indication. No semantic Python delta exists.

## Close after owner release

1. A finishes/stops its current run safely, copies final native outputs to a new
   external increment, records hashes, and confirms that no process will write the
   integration checkout.
2. The integration owner re-runs the diagnosis. If the normalized blob still equals
   HEAD and both diffs remain empty, refresh/normalize only through an explicitly
   reviewed non-destructive Git operation. Do not use reset, clean, stash, rebase or
   checkout-overwrite shortcuts.
3. Require an empty `git status --porcelain`, empty `git diff HEAD`, and `0/0`
   comparison with `origin/main`.
4. Re-run `audit-airjet-project.ps1` and require `PASS`.
5. Only then restart the manual watcher using its documented manager entry point.
   Record UTC restart time, PID and state. Never bypass the manager.
6. A and B continue only in their dedicated worktrees. The integration checkout is
   reserved for reviewed handoff/integration.

If any semantic diff, hash mismatch, divergence or unknown writer appears, stop and
return the incident to its owner. Do not infer that a visually empty diff is harmless
without the normalized blob proof above.

# Windows-Mac dual-channel Git safety tool

AirJet project skills are versioned under `codex-skills/`. After pulling, run `install-skills.ps1` on Windows or `install-skills.sh` on macOS. Use `audit-airjet-project.ps1` for a Python-independent Windows handoff check and `launch-airjet-codex-visible.ps1` from the logged-in Windows desktop for a visible project session. Do not Git-sync the entire `.codex` directory.

GitHub is the authoritative remote (`origin`). The generic toolkit retains optional NAS support, but NAS is out of scope for the current AirJet workflow unless the user explicitly reintroduces it. The tool compares commit relationships and stops on divergent history. It never stashes, merges, rebases, resets, cleans, force-pushes, or stores credentials.

## Setup per repository

```powershell
git remote add origin <github-url>
git remote add nas <nas-bare-repo-url>
Copy-Item .dual-channel.example.json <repo>\.dual-channel.json
```

Use SSH keys or the system credential manager. Never place passwords or tokens in the JSON file or repository.

## Commands

```powershell
.\dual-channel.ps1 status -Repo C:\path\to\repo
.\dual-channel.ps1 sync-check -Repo C:\path\to\repo
.\dual-channel.ps1 push-main -Repo C:\path\to\repo
.\dual-channel.ps1 backup-nas -Repo C:\path\to\repo
```

`push-main` requires a clean worktree, equal GitHub/NAS starting points, and a local branch that is only ahead. `backup-nas` additionally requires the local commit to already exist on GitHub. Any behind/diverged/remote-mismatch state exits with an error for manual review.

## Recommended workflow

1. Commit work locally with a meaningful message.
2. Run `sync-check`.
3. Run `push-main`.
4. Run `sync-check` again, then `backup-nas`.
5. On the other computer, fetch and compare before changing anything.

## Troubleshooting

- `remote is not configured`: add the exact repository URLs; do not guess them.
- `Working tree is not clean`: commit or manually stash after reviewing files.
- `Divergence detected`: inspect `git log --graph --oneline --all`; explicitly choose merge or rebase.
- NAS authentication fails: install the public SSH key in the NAS account; never embed its password.
- GitHub CLI is optional when SSH remotes are already configured; install/login only when repository creation or account operations are required.

# Windows operation

## Known paths

- Repository: `C:\Users\admin\win-mac-dual-channel`
- User skills: `C:\Users\admin\.codex\skills`
- Research bundle: `C:\Users\admin\Downloads\AirJet_simulation_bundle_2026-07-12_v2`

Revalidate these paths and the host before use.

## Install the project skill

Copy the repository source folder:

`codex-skills\airjet-product-reconstruction`

to:

`C:\Users\admin\.codex\skills\airjet-product-reconstruction`

Do not edit `.system` skills.

## Visible Codex launch

Use an interactive desktop process, not an SSH-attached hidden process. From an existing interactive Windows session, prefer the repository script:

```powershell
.\launch-airjet-codex-visible.ps1
```

The underlying launch is:

```powershell
Start-Process powershell.exe -ArgumentList '-NoExit','-Command','Set-Location C:\Users\admin\win-mac-dual-channel; codex'
```

Do not claim visibility merely because a process exists. The repository script rejects non-interactive sessions and requires a newly observed Codex process in the current Explorer session, but even that does not prove the user can see an unlocked desktop or that Codex read the project. Final proof requires the user to see the window and the new Codex to write `C:\Users\admin\Downloads\AIRJET_CODEX_HANDSHAKE.txt` after answering the project-understanding checklist. If only SSH is available, prepare and verify the repository/skills through SSH, then ask the logged-in user to run the visible-launch command.

## Verify

```powershell
codex --version
Get-ChildItem $HOME\.codex\skills -Filter SKILL.md -Recurse
git status --short --branch
powershell -ExecutionPolicy Bypass -File .\audit-airjet-project.ps1
```

Start a fresh Codex session after installing skills; newly installed skills are available on the next turn/session.

The handoff is complete only after the visible Codex report records the current commit, clean Git state, audit result, all three skills, project target, heat accounting, evidence classes, 1750 Pa limitation, P0 status, and Windows hardware/software limits.

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

Do not claim visibility merely because a process exists. The repository script rejects non-interactive sessions. If only SSH is available, prepare and verify the repository/skills through SSH, then ask the logged-in user to run the one visible-launch command or use an explicitly verified `InteractiveToken` scheduled task.

## Verify

```powershell
codex --version
Get-ChildItem $HOME\.codex\skills -Filter SKILL.md -Recurse
git status --short --branch
powershell -ExecutionPolicy Bypass -File .\audit-airjet-project.ps1
```

Start a fresh Codex session after installing skills; newly installed skills are available on the next turn/session.

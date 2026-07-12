# Cross-machine Git collaboration context

This repository is the user's safe GitHub-primary collaboration toolkit for Mac and Windows. Read this file before making changes.

## Current verified state

- GitHub remote: `https://github.com/superboynick/win-mac-dual-channel.git` (private).
- Default branch: `main`.
- Initial shared commit: `0ebc4c6 feat: add safe dual-channel Git collaboration toolkit`.
- Windows host: `192.168.1.50` (`LAPTOP-LCCLM2HI`).
- Windows SSH user: `admin`; connect with `ssh admin@192.168.1.50`.
- The Windows SSH service is enabled and starts automatically.
- Do not use the older SSH username `superboynick`; it was verified to fail on 2026-07-12.

## Collaboration rules

1. GitHub is the primary shared remote. NAS is out of scope unless the user explicitly reintroduces it.
2. First inspect only: check status, branch, remotes, latest commit, and divergence before changing configuration or files.
3. Before work: run `git pull`. After work: `git add .`, `git commit -m "..."`, then `git push`.
4. Stop on divergence, dirty worktrees, missing authentication, or ambiguous ownership. Do not auto-merge, rebase, force-push, reset, clean, or overwrite changes.
5. Preserve user files and existing changes. Never store passwords, tokens, or private keys in repository files.

## Toolkit scope

`dual-channel.ps1` exposes safe operations including status, fetch, compare, sync-check, push-main, and backup-nas. It is designed to fetch before comparison/push and block unsafe states.

## Current task direction

The GitHub setup is complete and both Mac and Windows were verified at the same initial commit. Future work should use this repository as the handoff point for cross-machine tasks.

The active research handoff is `airjet-simulation/`. Its main file is `airjet-simulation/AIRJET_SIMULATION_PROJECT.md`; read it before changing the AirJet model, parameters, scripts, or result summaries. `PROJECT_ASSESSMENT_AND_PLAN.md` defines scope, stage gates and risks; its mandated first technical task is one single-nozzle steady laminar CHT case, not FSI. The local evidence library is deliberately outside Git at `Downloads/AirJet_research/` (or the matching directory extracted from the Windows research bundle). Do not add commercial PDFs, raw CFD case/data files, meshes, licenses, credentials, or large transient fields to Git.

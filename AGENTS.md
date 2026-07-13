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
3. Before work: run `git status`, `git fetch origin`, inspect ahead/behind, then use `git pull --ff-only` only when clean and non-divergent. After work: review, commit, and push without force.
4. Stop on divergence, dirty worktrees, missing authentication, or ambiguous ownership. Do not auto-merge, rebase, force-push, reset, clean, or overwrite changes.
5. Preserve user files and existing changes. Never store passwords, tokens, or private keys in repository files.

## Toolkit scope

`dual-channel.ps1` exposes safe operations including status, fetch, compare, sync-check, push-main, and backup-nas. It is designed to fetch before comparison/push and block unsafe states.

## Current task direction

The GitHub setup is complete and both Mac and Windows were verified at the same initial commit. Future work should use this repository as the handoff point for cross-machine tasks.

The active research handoff is `airjet-simulation/`. Its primary file is `airjet-simulation/AIRJET_MINI_FULL_PRODUCT_MASTER_PLAN.md`, not the older optimization plan or the single-cell reconstruction subplan. Read `airjet-simulation/PROJECT_STATUS.md` for the current completion boundary: `AJM-P0-v001` public-evidence freeze has passed, but P1–P6 CAD/physical gates have not. The user’s current aim is public-evidence-constrained reconstruction of a complete AirJet product without an actual module. The selected first target is AirJet Mini Gen1 because its local official sheet provides the strongest combined envelope, cross-section, power, heat-removal and performance-curve evidence. The final CAD and at least one CFD/CHT model must cover the full product, all modeled cells, intake distribution, orifice plate, impingement channel, exhaust path and thermal stack. A high-fidelity single-cell model is only a calibration submodel for actuator displacement and reduced full-product boundaries. Read `evidence/P0_EVIDENCE_FREEZE_RECORD.md`, `evidence/airjet_reconstruction_ledger.csv`, `evidence/patent_product_component_map.csv`, `evidence/layout_candidate_scores.csv`, and `MODEL_ANNOTATIONS.md` before changing model parameters. The local evidence library is deliberately outside Git at `Downloads/AirJet_research/` (or the matching directory extracted from the Windows research bundle). Do not add commercial PDFs, raw CFD case/data files, meshes, licenses, credentials, or large transient fields to Git.

For a new Windows Codex session, also read `airjet-simulation/WINDOWS_HANDOFF.md`, `airjet-simulation/DECISION_AND_REASONING_ARCHIVE.md`, and `airjet-simulation/evidence/SOURCE_PROVENANCE.md`. These files preserve the engineering rationale and source boundaries. Do not claim access to private chain-of-thought; use the documented evidence, assumptions, alternatives, equations and decision records.

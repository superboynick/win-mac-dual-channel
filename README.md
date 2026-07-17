# AirJet Mini Gen1 — Full Product CFD Reconstruction

[![GitHub](https://img.shields.io/badge/public-OK-green)](https://github.com/superboynick/win-mac-dual-channel)

Open-source full-product simulation reconstruction of Frore Systems AirJet Mini Gen1 solid-state active cooling device.

## 📄 Paper
- **Main:** `airjet-paper/main.tex` (287 lines, 13 references)
- **Reproduction Guide:** `airjet-simulation/AIRJET_SIMULATION_REPRODUCTION_GUIDE.md`

## 📊 Results
- 34,883 poly-hexcore cells, min OQ 0.53
- 25 consecutive identical mesh runs
- CFD solver validation: k-ω SST convergence
- Mesh independence: coarse (2.8MB) + medium (8.2MB)

## 🚀 Quick Start
1. `git clone git@ssh.github.com:superboynick/win-mac-dual-channel.git`
2. Read `airjet-simulation/AIRJET_SIMULATION_REPRODUCTION_GUIDE.md`
3. Run `save_mesh6.py` on Windows with ANSYS Student 2026 R1

## 🤝 Dual Codex Collaboration
- `tools/airjet-daemon/` — Git monitor + task dispatch
- `airjet-simulation/coupling/` — ANSYS↔OpenFOAM protocol

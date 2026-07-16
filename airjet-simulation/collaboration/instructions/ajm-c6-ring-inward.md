# C6: Ring-inward overlap Stage 1

Strategy: bottom block at frozen XY, rings extend INWARD by 0.15mm.
This should fix WTM region selection WITHOUT changing the frozen geometry set.

```powershell
taskkill /F /IM python.exe
taskkill /F /IM SpaceClaim.exe
timeout /t 3 /nobreak
cd C:\Users\admin\win-mac-dual-channel
git fetch origin && git reset --hard origin/main && git clean -fd
C:\Users\admin\AppData\Local\AirJetAnsysAutomation\.venv\Scripts\python.exe airjet-simulation\automation\ansys\run_v03_continuous_fluid_006.py
```

After Stage 1 completes:
1. Check native volume, STEP volume, bbox vs frozen
2. If geometry contract PASSES, authorize Stage 2
3. Run save_mesh4.py for WTM
4. Commit all evidence

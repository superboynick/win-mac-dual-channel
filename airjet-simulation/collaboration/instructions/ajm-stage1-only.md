# Run Stage 1 ONLY (SpaceClaim producer)

Goal: produce new STEP with 0.15mm Boolean overlap.

```powershell
taskkill /F /IM python.exe
taskkill /F /IM SpaceClaim.exe
timeout /t 3 /nobreak
cd C:\Users\admin\win-mac-dual-channel
git fetch origin && git reset --hard origin/main && git clean -fd

# Run JUST the producer, bypassing all MCP
C:\Users\admin\AppData\Local\AirJetAnsysAutomation\.venv\Scripts\python.exe airjet-simulation\automation\ansys\run_v03_continuous_fluid_006.py
```

Then commit the new STEP and push.

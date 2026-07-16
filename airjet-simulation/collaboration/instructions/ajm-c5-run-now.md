# C5 RUN NOW — no preflight, just mesh

Pull this commit, then execute ONE command:

```
C:\Users\admin\AppData\Local\AirJetAnsysAutomation\.venv\Scripts\python.exe airjet-simulation\automation\ansys\run_v03_continuous_mesh_006.py
```

All preflight checks are disabled. This will run SpaceClaim producer + PyFluent consumer.
Expected: 35K cells, min OQ 0.57, 1 fluid zone, mesh saved.

If it fails, just commit the result to Git and Mac will fix it.

# Official ANSYS 2026 R1 automation routes

Use only these product-supported routes for this project.

## SpaceClaim / Discovery geometry

- Installed executable:
  `D:\ansys\ANSYS Inc\ANSYS Student\v261\scdm\SpaceClaim.exe`
- Launch reviewed Python with `/RunScript=<absolute.py>`, `/ScriptAPI=V261`,
  `/ScriptOutput=<absolute.log>`, `/ExitAfterScript=True`, and optionally `/Headless=True`.
- The embedded scripting editor and command-line interface use the SpaceClaim API. Build geometry,
  parameters, Named Selections, Volume Extract checks, native save, and STEP transfer in scripts.
- Do not pass `/p` or any other license-preference override.

Official reference:
`https://ansyshelp.ansys.com/public/Views/Secured/corp/v242/en/spaceclaim/Discovery/user_manual/spaceclaim_command_line_options.html`

The 2026 R1 release notes say API V232 is deprecated; use V261 for new scripts. The geometry kernel
changed to Parasolid in 2025 R1, so do not assume old ACIS behavior.

## Workbench integration

- Installed executable:
  `D:\ansys\ANSYS Inc\ANSYS Student\v261\Framework\bin\Win64\RunWB2.exe`
- Run reviewed journals with `RunWB2.exe -B -R <absolute.wbjn>`.
- Use Workbench journals for system creation, geometry transfer, Named Selection transfer, project
  save, and integration checks. Capture the Workbench log and project archive.

Official 2026 R1 scripting guide:
`https://ansyshelp.ansys.com/public/Views/Secured/corp/v261/en/pdf/Workbench_Scripting_Guide.pdf`

## Mechanical / PyMechanical

- Installed executable:
  `D:\ansys\ANSYS Inc\ANSYS Student\v261\aisol\bin\winx64\AnsysWBU.exe`
- Pinned client: `ansys-mechanical-core==0.12.11` in the project venv.
- Prefer embedding mode for deterministic local batch work and remote-session mode only when a
  persistent Mechanical service is needed. Select version 261 or the exact executable.
- Script geometry import, materials, mesh, boundary conditions, static/modal/harmonic analyses,
  solves, result tables, images, and native database save.

Official references:
`https://developer.ansys.com/docs/mechanical`
`https://mechanical.docs.pyansys.com/version/stable/getting_started/running_mechanical.html`

## Fluent / PyFluent

- Pinned client: `ansys-fluent-core==0.40.2` in the project venv.
- Launch version 261, double precision, explicit processor count, and the required meshing or solver
  mode. Start a transcript immediately and call `check_health()` before setup.
- Use PyFluent or recorded TUI for Energy, ideal gas, transient setup, dynamic mesh, profiles/UDF,
  CHT, meshing, initialization, iteration/time stepping, reports, case/data save, and clean exit.
- Record the actual Student processor and mesh limits. Never retry with license overrides.

Official reference:
`https://fluent.docs.pyansys.com/`

## MCP

There is no official general-purpose ANSYS Mechanical/Fluent/SpaceClaim MCP currently used by this
project. ANSYS publishes a PyLumerical MCP for Lumerical; it is not applicable to AirJet CFD/CHT.
The local `airjet-ansys` MCP is therefore a narrow audited adapter around the official interfaces
above. It uses the official Python MCP SDK `mcp==1.28.1` with stdio transport.

The MCP accepts a `profile_id`, a non-path case identifier, and, only when the selected profile
declares one, an in-memory predecessor job identifier. Each profile fixes the engine,
Git-tracked script, script SHA-256, timeout, output-root identifier, and declared report files in
`airjet-simulation/automation/ansys/profiles.json`. It does not provide a shell, arbitrary file
reader, executable path, command-line argument, working directory, environment override, or inline
script facility. For predecessor handoff, the server supplies only policy-listed copies after
checking the predecessor profile, case, commit, output root, terminal state, frozen artifact
manifest, capability report and file hashes. The signed child script still runs with the current OS
user's filesystem permissions; this adapter is not an OS sandbox, so safety also depends on Git
signature verification, hash pinning and script review. A process exit of zero means only that the wrapper process exited; the declared
probe report and its assertions determine control-plane success.

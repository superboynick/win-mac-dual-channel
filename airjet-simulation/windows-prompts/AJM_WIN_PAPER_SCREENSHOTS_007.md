# AJM_WIN_PAPER_SCREENSHOTS_007

Date: 2026-07-16
Trigger: Mac Codex via Git
Role: Read-only screenshot collection for paper first draft
Hard deadline: 2026-07-17 morning (Pacific)

## Task

Take screenshots of existing modeling artifacts for the paper. Do NOT run any solvers. Read-only.

## Step 1: Check what exists

Check under `C:\Users\admin\win-mac-dual-channel\airjet-simulation\`:

1. Any CAD files (SpaceClaim .scdoc, .stp, .igs)?
2. Any ANSYS Workbench project (.wbpj)?
3. Any Fluent case (.cas) or Mechanical results?
4. Run `git log --oneline -10`

## Step 2: Take screenshots (priority order)

### If CAD geometry exists:
Open SpaceClaim, take these:
- Full assembly isometric view
- Internal cell array (hide outer shell)
- Orifice plate detail (zoom on one cell)
- Section cut showing intake → membrane → orifice → impingement → exhaust
- Thickness side view

### If only Workbench project exists:
- Workbench project overview
- Geometry module preview
- Mesh preview if already generated

### If nothing exists:
- Windows Explorer screenshot of `airjet-simulation` folder structure
- `git log --oneline -10` output

## Step 3: Save

Save all PNGs to: `C:\Users\admin\Desktop\airjet_screenshots\`
Use English filenames, e.g. `cad_full_assembly.png`, `cad_cell_array.png`

## Rules
- READ ONLY — no solver runs
- Do not modify any files
- Do not commit or push
- Report what was found and what was captured

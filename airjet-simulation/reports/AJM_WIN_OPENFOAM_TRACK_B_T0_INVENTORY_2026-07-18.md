# AJM Windows OpenFOAM Track B T0 inventory — 2026-07-18

## Result

`WINDOWS_T0_INVENTORY=COMPLETE`

`OPENFOAM_TOOLING=NOT_INSTALLED`

`OPENFOAM_TOOLING_SMOKE=NOT_RUN`

`SOURCE_SCRIPT_SYNTAX=PASS`

`SOURCE_ONLY_RUNTIME=EXPECTED_FAIL_20_MISSING_FOAMVERSION`

`P3_P6_GATE_EFFECT=NONE`

This is a read-only inventory plus source-only check. No feature, distribution,
package, service or container was installed or started.

## Observed host and tooling

| Item | Observation |
|---|---|
| Host | Windows 11 Home, build 26200, `LAPTOP-LCCLM2HI` |
| Capacity | 24 logical processors, 33,752,997,888 bytes RAM |
| Free storage | C: 132,350,418,944 bytes; D: 99,294,175,232 bytes |
| WSL executable | present at the Windows system path |
| WSL commands | `--status` exit 50; `--version` exit 1; `--list --quiet` exit 1 |
| WSL distributions | no current-user `Lxss` distribution registry |
| Feature query | requires elevation; state not claimed |
| Virtualization telemetry | `HypervisorPresent=True`; processor firmware flag reported `False`; needs privileged/firmware verification before installation |
| Docker/Podman | commands, installed-app records and standard directories not found |
| Native OpenFOAM | `foamVersion`, `blockMesh`, `checkMesh`, `foamRun` not found |
| Git Bash | present outside PATH; usable only for source syntax/static execution |

The repository smoke launcher passed `bash -n`. Running it in Git Bash stopped before
creating a case with exit 20 and `TOOLING_NOT_INSTALLED missing=foamVersion`, exactly
as designed. This does not constitute T0 smoke execution because no configured
OpenFOAM shell existed.

The repeatable read-only inventory entry point is
`automation/openfoam/inventory_windows_openfoam_t0.ps1`, SHA256
`d671cd466b181aebd678cc03a63d0a9695541484fdc0fb07ef6670b973ff4c13`.
PowerShell 5.1 execution returned exit 0, one parseable JSON object, the four truth
labels above, and WSL exit codes `50/1/1` for status/version/list respectively.
The script explicitly limits its OpenFOAM probe to the Windows PATH plus WSL registry;
if a distribution exists it reports `UNKNOWN_WSL_NOT_LAUNCHED` rather than a false
negative. The no-write contract test
`automation/openfoam/test_inventory_windows_openfoam_t0.ps1`, SHA256
`dd7ad4d59ba7503f3e30d4ecd8cbac3d6b5995beb6abbe0471191c7d6234e37c`,
returned `WINDOWS_OPENFOAM_T0_INVENTORY_TEST=PASS`.

## Frozen primary and Plan B routes

The OpenFOAM Foundation's current Windows instructions specify WSL2 with Ubuntu
22.04 LTS. Its v14 Ubuntu instructions identify the signed package as `openfoam14`
and the environment entry point as `/opt/openfoam14/etc/bashrc`:

- <https://openfoam.org/download/windows/>
- <https://openfoam.org/download/14-ubuntu/>
- <https://learn.microsoft.com/windows/wsl/install>

Primary route, only after explicit authorization:

1. use an elevated terminal to install WSL2 with `Ubuntu-22.04`;
2. reboot only if Windows requires it;
3. record WSL, distribution, architecture and Ubuntu release identities;
4. add the Foundation repository/key exactly as documented and install
   `openfoam14`;
5. source `/opt/openfoam14/etc/bashrc`, record package/version identities, then run
   the repository T0 smoke against the installed official `pitzDailySteady` case.

Plan B if Store/network delivery is unavailable:

1. follow Microsoft's official offline WSL MSI/feature process and Ubuntu `.wsl`
   distribution route;
2. use an approved local mirror/cache for the same signed Foundation `openfoam14`
   package;
3. run the identical identity checks and T0 smoke.

A container, unofficial native Windows port, different OpenFOAM distribution or
different major version is not an automatic fallback. It requires a new provenance
review and user authorization.

## Stop conditions and safe backlog

Stop runtime work if elevation/reboot is not authorized, virtualization is unavailable,
distribution/package identity cannot be pinned, repository signatures fail, or the
same T0 failure repeats twice without a discriminating change.

Even after T0 passes, AirJet P3 remains blocked until A supplies valid, hash-bound P1
chamber/orifice geometry and P2 displacement. While blocked, B may prepare:

- schema/template validators and unit/hash checks;
- OpenFOAM v14 source/dictionary lints;
- periodic stability, mass conservation and mesh-quality post-processing;
- case/run manifests and external-artifact indexing;
- P3-P5 Gate evidence templates.

No placeholder AirJet solve may be labeled P3, and T0 never changes the existing P0
evidence Gate.

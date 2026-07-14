[CmdletBinding()]
param(
    [string]$RepositoryRoot = 'C:\Users\admin\win-mac-dual-channel',
    [switch]$ReplaceMcp
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$RepositoryRoot = [IO.Path]::GetFullPath((Resolve-Path -LiteralPath $RepositoryRoot).ProviderPath).TrimEnd('\')
if ($RepositoryRoot -cne 'C:\Users\admin\win-mac-dual-channel') { throw 'BLOCKED_UNEXPECTED_REPOSITORY_ROOT' }
Set-Location $RepositoryRoot

if ((git rev-parse --abbrev-ref HEAD) -cne 'main') { throw 'BLOCKED_WRONG_BRANCH' }
if ((git status --porcelain=v1 | Out-String).Trim()) { throw 'BLOCKED_DIRTY_WORKTREE' }
git fetch origin
if ($LASTEXITCODE -ne 0) { throw 'BLOCKED_GIT_FETCH' }
if ((git rev-list --left-right --count HEAD...origin/main | Out-String).Trim() -notmatch '^0\s+0$') {
    throw 'BLOCKED_GIT_NOT_SYNCHRONIZED'
}

$InstallSkills = Join-Path $RepositoryRoot 'install-skills.ps1'
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $InstallSkills
if ($LASTEXITCODE -ne 0) { throw 'BLOCKED_SKILL_INSTALL' }

$Root = Join-Path $env:LOCALAPPDATA 'AirJetAnsysAutomation'
$Venv = Join-Path $Root '.venv'
$Python = Join-Path $Venv 'Scripts\python.exe'
$BasePython = 'C:\Users\admin\AppData\Local\Programs\Python\Python312\python.exe'
$Server = Join-Path $HOME '.codex\skills\airjet-ansys-automation\scripts\airjet_ansys_mcp.py'
$PolicyTest = Join-Path $HOME '.codex\skills\airjet-ansys-automation\scripts\test_airjet_ansys_mcp_policy.py'
[void](New-Item -ItemType Directory -Path $Root -Force)

if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
    if (-not (Test-Path -LiteralPath $BasePython -PathType Leaf)) { throw 'BLOCKED_BASE_PYTHON_MISSING' }
    & $BasePython -m venv $Venv
    if ($LASTEXITCODE -ne 0) { throw 'BLOCKED_VENV_CREATE' }
}
& $Python -m pip install --disable-pip-version-check --upgrade 'pip<27'
if ($LASTEXITCODE -ne 0) { throw 'BLOCKED_PIP_BOOTSTRAP' }
& $Python -m pip install --disable-pip-version-check 'mcp==1.28.1' 'ansys-fluent-core==0.40.2' 'ansys-mechanical-core==0.12.11'
if ($LASTEXITCODE -ne 0) { throw 'BLOCKED_AUTOMATION_DEPENDENCY_INSTALL' }
& $Python -c "import mcp, ansys.fluent.core, ansys.mechanical.core; print('AUTOMATION_IMPORTS=PASS')"
if ($LASTEXITCODE -ne 0) { throw 'BLOCKED_AUTOMATION_IMPORT' }
if (-not (Test-Path -LiteralPath $Server -PathType Leaf)) { throw 'BLOCKED_MCP_SERVER_MISSING' }
if (-not (Test-Path -LiteralPath $PolicyTest -PathType Leaf)) { throw 'BLOCKED_MCP_POLICY_TEST_MISSING' }
& $Python -m py_compile $Server $PolicyTest
if ($LASTEXITCODE -ne 0) { throw 'BLOCKED_MCP_PYTHON_SYNTAX' }
& $Python -I -B $PolicyTest
if ($LASTEXITCODE -ne 0) { throw 'BLOCKED_MCP_STATIC_POLICY' }

$Codex = (Get-Command codex.cmd -ErrorAction SilentlyContinue)
if (-not $Codex) { $Codex = Get-Command codex -ErrorAction Stop }
$PreviousErrorActionPreference = $ErrorActionPreference
$ErrorActionPreference = 'Continue'
$null = & $Codex.Source mcp get airjet-ansys 2>&1
$Exists = ($LASTEXITCODE -eq 0)
$ErrorActionPreference = $PreviousErrorActionPreference
if ($Exists -and (-not $ReplaceMcp)) { throw 'BLOCKED_EXISTING_MCP_USE_REPLACE' }
if ($Exists) {
    & $Codex.Source mcp remove airjet-ansys
    if ($LASTEXITCODE -ne 0) { throw 'BLOCKED_EXISTING_MCP_REMOVE' }
}
& $Codex.Source mcp add airjet-ansys -- $Python -I -B $Server
if ($LASTEXITCODE -ne 0) { throw 'BLOCKED_MCP_ADD' }
& $Codex.Source mcp get airjet-ansys
if ($LASTEXITCODE -ne 0) { throw 'BLOCKED_MCP_VERIFY' }

$State = @(
    'schema_version=1',
    "installed_at=$([DateTime]::UtcNow.ToString('o'))",
    "repository=$RepositoryRoot",
    "python=$Python",
    'mcp=mcp==1.28.1',
    'pyfluent=ansys-fluent-core==0.40.2',
    'pymechanical=ansys-mechanical-core==0.12.11',
    'codex_mcp=airjet-ansys'
)
[IO.File]::WriteAllLines((Join-Path $Root 'bootstrap.state'), $State, (New-Object Text.UTF8Encoding($false)))
Write-Output 'AIRJET_ANSYS_AUTOMATION_BOOTSTRAP=PASS'

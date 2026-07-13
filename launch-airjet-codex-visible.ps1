[CmdletBinding()]
param([switch]$SkipAudit)

$ErrorActionPreference = 'Stop'
$RepoRoot = $PSScriptRoot
$CurrentSession = (Get-Process -Id $PID).SessionId
$InteractiveShell = @(Get-Process -Name explorer -ErrorAction SilentlyContinue | Where-Object { $_.SessionId -eq $CurrentSession })

if ($CurrentSession -eq 0 -or $InteractiveShell.Count -eq 0) {
    throw 'No logged-in interactive desktop was detected in this session. Run this script from the visible Windows desktop, not through SSH.'
}

$GitPath = Join-Path $RepoRoot '.git'
$ProjectSkill = Join-Path $HOME '.codex\skills\airjet-product-reconstruction\SKILL.md'
if (-not (Test-Path -LiteralPath $GitPath)) { throw "Not a Git worktree: $RepoRoot" }
if (-not (Test-Path -LiteralPath $ProjectSkill -PathType Leaf)) {
    throw 'The AirJet project skill is not installed. Run install-skills.ps1 first.'
}

if (-not $SkipAudit) {
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $RepoRoot 'audit-airjet-project.ps1')
    if ($LASTEXITCODE -ne 0) { throw 'AirJet project audit failed; visible Codex was not started.' }
}

$Codex = Get-Command codex.cmd -ErrorAction SilentlyContinue
if (-not $Codex) { $Codex = Get-Command codex -ErrorAction SilentlyContinue }
if (-not $Codex) { throw 'codex was not found on PATH.' }

$EscapedRepo = $RepoRoot.Replace("'", "''")
$EscapedCodex = $Codex.Source.Replace("'", "''")
$BeforeCodexIds = @(Get-Process -Name codex -ErrorAction SilentlyContinue |
    Where-Object { $_.SessionId -eq $CurrentSession } |
    Select-Object -ExpandProperty Id)
$ChildCommand = @"
`$Host.UI.RawUI.WindowTitle = 'AirJet Codex'
Set-Location -LiteralPath '$EscapedRepo'
Write-Host 'AirJet repository and project skill audit: PASS' -ForegroundColor Green
Write-Host 'Paste the Windows collaboration prompt into this Codex window.' -ForegroundColor Cyan
& '$EscapedCodex'
"@
$Encoded = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($ChildCommand))
$Process = Start-Process powershell.exe -ArgumentList @(
    '-NoExit',
    '-ExecutionPolicy', 'Bypass',
    '-EncodedCommand', $Encoded
) -WorkingDirectory $RepoRoot -PassThru

$NewCodex = $null
for ($Attempt = 0; $Attempt -lt 40 -and $null -eq $NewCodex; $Attempt += 1) {
    Start-Sleep -Milliseconds 250
    $Process.Refresh()
    if ($Process.HasExited) { break }
    $NewCodex = Get-Process -Name codex -ErrorAction SilentlyContinue |
        Where-Object { $_.SessionId -eq $CurrentSession -and $BeforeCodexIds -notcontains $_.Id } |
        Select-Object -First 1
}

if ($null -eq $NewCodex) {
    throw "An interactive shell was requested (pid=$($Process.Id)), but no new Codex process was observed in session $CurrentSession. Inspect the desktop window."
}

Write-Host "INTERACTIVE_CODEX_PROCESS_STARTED codex_pid=$($NewCodex.Id) shell_pid=$($Process.Id) session=$CurrentSession repo=$RepoRoot"
Write-Host 'Visual confirmation and the AIRJET_CODEX_HANDSHAKE.txt project-reading report are still required.'

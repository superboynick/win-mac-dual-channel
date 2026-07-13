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

Start-Sleep -Milliseconds 800
$Process.Refresh()
Write-Host "VISIBLE_CODEX_LAUNCHED pid=$($Process.Id) session=$CurrentSession repo=$RepoRoot"

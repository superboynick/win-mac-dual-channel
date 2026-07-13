[CmdletBinding()]
param([switch]$RefreshOfficial)

$ErrorActionPreference = 'Stop'
$RepoRoot = $PSScriptRoot
$ManifestPath = Join-Path $RepoRoot 'codex-skills\skills-manifest.json'
$Manifest = Get-Content -Raw -LiteralPath $ManifestPath | ConvertFrom-Json
$TargetRoot = Join-Path $HOME '.codex\skills'
New-Item -ItemType Directory -Force -Path $TargetRoot | Out-Null

function Get-SkillHash {
    param([string]$SkillPath)
    $Entry = Join-Path $SkillPath 'SKILL.md'
    if (-not (Test-Path -LiteralPath $Entry)) { return $null }
    $Text = [System.IO.File]::ReadAllText($Entry, [System.Text.Encoding]::UTF8)
    $Canonical = $Text.Replace("`r`n", "`n").Replace("`r", "`n")
    $Bytes = [System.Text.Encoding]::UTF8.GetBytes($Canonical)
    $Sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        return ([System.BitConverter]::ToString($Sha.ComputeHash($Bytes))).Replace('-', '').ToLowerInvariant()
    } finally {
        $Sha.Dispose()
    }
}

function Sync-SkillDirectory {
    param([string]$Source, [string]$Target)
    New-Item -ItemType Directory -Force -Path $Target | Out-Null
    & robocopy $Source $Target /MIR /NFL /NDL /NJH /NJS /NP | Out-Null
    if ($LASTEXITCODE -gt 7) {
        throw "robocopy failed for $Source -> $Target with exit code $LASTEXITCODE"
    }
}

$OfficialNeeded = @()
foreach ($Skill in $Manifest.skills) {
    if ($Skill.kind -ne 'official') { continue }
    $Target = Join-Path $TargetRoot $Skill.name
    $Hash = Get-SkillHash -SkillPath $Target
    if ($RefreshOfficial -or $Hash -ne $Skill.skill_md_sha256) {
        $OfficialNeeded += $Skill
    }
}

$TempRoot = $null
$ZipPath = $null
if ($OfficialNeeded.Count -gt 0) {
    $Commit = $Manifest.official_source.commit
    $TempRoot = Join-Path ([System.IO.Path]::GetTempPath()) "openai-skills-$Commit"
    $ZipPath = "$TempRoot.zip"
    if (Test-Path -LiteralPath $TempRoot) { Remove-Item -Recurse -Force -LiteralPath $TempRoot }
    if (Test-Path -LiteralPath $ZipPath) { Remove-Item -Force -LiteralPath $ZipPath }
    Invoke-WebRequest -UseBasicParsing -Uri "https://github.com/openai/skills/archive/$Commit.zip" -OutFile $ZipPath
    Expand-Archive -LiteralPath $ZipPath -DestinationPath $TempRoot
}

foreach ($Skill in $Manifest.skills) {
    $Target = Join-Path $TargetRoot $Skill.name
    if ($Skill.kind -eq 'project') {
        $Source = Join-Path $RepoRoot $Skill.source
        Sync-SkillDirectory -Source $Source -Target $Target
    } elseif ($OfficialNeeded.name -contains $Skill.name) {
        $ExtractedRepo = Join-Path $TempRoot "skills-$($Manifest.official_source.commit)"
        $Source = Join-Path $ExtractedRepo ($Skill.source -replace '/', '\')
        Sync-SkillDirectory -Source $Source -Target $Target
    }

    $Actual = Get-SkillHash -SkillPath $Target
    if ($Actual -ne $Skill.skill_md_sha256) {
        throw "Hash mismatch for $($Skill.name): expected $($Skill.skill_md_sha256), got $Actual"
    }
    Write-Host "PASS $($Skill.name) $Actual"
}

if ($TempRoot -and (Test-Path -LiteralPath $TempRoot)) { Remove-Item -Recurse -Force -LiteralPath $TempRoot }
if ($ZipPath -and (Test-Path -LiteralPath $ZipPath)) { Remove-Item -Force -LiteralPath $ZipPath }

Write-Host "Installed skills to $TargetRoot"
Write-Host 'Start a fresh Codex session to load newly installed skills.'

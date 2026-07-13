[CmdletBinding()]
param([switch]$RefreshOfficial)

$ErrorActionPreference = 'Stop'
$RepoRoot = $PSScriptRoot
$ManifestPath = Join-Path $RepoRoot 'codex-skills\skills-manifest.json'
$Manifest = Get-Content -Raw -LiteralPath $ManifestPath | ConvertFrom-Json

$ExpectedSkills = @{
    'airjet-product-reconstruction' = [pscustomobject]@{
        kind = 'project'
        source = 'codex-skills/airjet-product-reconstruction'
        required = @('SKILL.md', 'agents/openai.yaml', 'references/evidence-rules.md', 'references/stage-routing.md', 'references/windows-operation.md', 'scripts/audit_project.py')
    }
    'jupyter-notebook' = [pscustomobject]@{
        kind = 'official'
        source = 'skills/.curated/jupyter-notebook'
        required = @('LICENSE.txt', 'SKILL.md', 'agents/openai.yaml', 'assets/experiment-template.ipynb', 'assets/jupyter-small.svg', 'assets/jupyter.png', 'assets/tutorial-template.ipynb', 'references/experiment-patterns.md', 'references/notebook-structure.md', 'references/quality-checklist.md', 'references/tutorial-patterns.md', 'scripts/new_notebook.py')
    }
    'pdf' = [pscustomobject]@{
        kind = 'official'
        source = 'skills/.curated/pdf'
        required = @('LICENSE.txt', 'SKILL.md', 'agents/openai.yaml', 'assets/pdf.png')
    }
}

if ($Manifest.schema_version -ne 1) { throw 'Unsupported skills manifest schema.' }
if ($Manifest.hash_canonicalization -ne 'UTF-8 text with CRLF and CR normalized to LF') {
    throw 'Unexpected skills manifest hash canonicalization.'
}
if ($Manifest.official_source.repository -ne 'https://github.com/openai/skills.git') {
    throw 'Unexpected official skill repository.'
}
$Commit = [string]$Manifest.official_source.commit
if ($Commit -notmatch '^[0-9a-f]{40}$') { throw 'Official skill commit must be 40 lowercase hexadecimal characters.' }
if ($Commit -ne '49f948faa9258a0c61caceaf225e179651397431') {
    throw 'Official skill commit differs from the project-reviewed lock.'
}

$Skills = @($Manifest.skills)
$Names = @($Skills | ForEach-Object { [string]$_.name })
if ($Names.Count -ne $ExpectedSkills.Count -or @($Names | Select-Object -Unique).Count -ne $ExpectedSkills.Count) {
    throw 'Skills manifest must contain exactly three unique skills.'
}
foreach ($Skill in $Skills) {
    $Name = [string]$Skill.name
    if (-not $ExpectedSkills.ContainsKey($Name)) { throw "Unexpected skill name: $Name" }
    $Expected = $ExpectedSkills[$Name]
    if ($Skill.kind -ne $Expected.kind -or $Skill.source -ne $Expected.source) {
        throw "Unexpected kind/source for skill $Name"
    }
    if ([string]$Skill.skill_md_sha256 -notmatch '^[0-9a-f]{64}$') {
        throw "Invalid SHA256 for skill $Name"
    }
    $Required = @($Skill.required_files | ForEach-Object { [string]$_ })
    if ($Required.Count -ne $Expected.required.Count -or @($Required | Select-Object -Unique).Count -ne $Expected.required.Count) {
        throw "Required-file list is incomplete or duplicated for skill $Name"
    }
    $RequiredDiff = @(Compare-Object ($Expected.required | Sort-Object) ($Required | Sort-Object))
    if ($RequiredDiff.Count -gt 0) { throw "Unexpected required-file list for skill $Name" }
    foreach ($Relative in $Required) {
        if ([IO.Path]::IsPathRooted($Relative) -or $Relative -match '(^|[\\/])\.\.([\\/]|$)') {
            throw "Unsafe required path for skill $Name`: $Relative"
        }
    }
}

$TargetRoot = Join-Path $HOME '.codex\skills'
New-Item -ItemType Directory -Force -Path $TargetRoot | Out-Null
$TargetRootFull = [IO.Path]::GetFullPath($TargetRoot).TrimEnd([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar)

function Get-DirectSkillTarget {
    param([string]$Name)
    $Candidate = [IO.Path]::GetFullPath((Join-Path $TargetRootFull $Name))
    $Parent = [IO.Path]::GetDirectoryName($Candidate).TrimEnd([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar)
    if (-not $Parent.Equals($TargetRootFull, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Skill target escapes target root: $Name"
    }
    return $Candidate
}

function Get-ContainedPath {
    param([string]$Base, [string]$Relative)
    if ([IO.Path]::IsPathRooted($Relative) -or $Relative -match '(^|[\\/])\.\.([\\/]|$)') {
        throw "Unsafe relative path: $Relative"
    }
    $BaseFull = [IO.Path]::GetFullPath($Base).TrimEnd([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar)
    $Candidate = [IO.Path]::GetFullPath((Join-Path $BaseFull $Relative))
    $Prefix = $BaseFull + [IO.Path]::DirectorySeparatorChar
    if (-not $Candidate.StartsWith($Prefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Path escapes base directory: $Relative"
    }
    return $Candidate
}

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
    if (-not (Test-Path -LiteralPath $Source -PathType Container)) { throw "Missing skill source: $Source" }
    New-Item -ItemType Directory -Force -Path $Target | Out-Null
    & robocopy $Source $Target /MIR /NFL /NDL /NJH /NJS /NP | Out-Null
    if ($LASTEXITCODE -gt 7) {
        throw "robocopy failed for $Source -> $Target with exit code $LASTEXITCODE"
    }
}

function Test-SkillRequiredFiles {
    param([object]$Skill, [string]$Target)
    foreach ($Relative in @($Skill.required_files)) {
        $Path = Get-ContainedPath -Base $Target -Relative ([string]$Relative)
        if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $false }
    }
    return $true
}

$OfficialNeeded = @()
foreach ($Skill in $Manifest.skills) {
    if ($Skill.kind -ne 'official') { continue }
    $Target = Get-DirectSkillTarget -Name $Skill.name
    $Hash = Get-SkillHash -SkillPath $Target
    if ($RefreshOfficial -or $Hash -ne $Skill.skill_md_sha256 -or -not (Test-SkillRequiredFiles -Skill $Skill -Target $Target)) {
        $OfficialNeeded += $Skill
    }
}

$TempRoot = $null
$ZipPath = $null
if ($OfficialNeeded.Count -gt 0) {
    $TempRoot = Join-Path ([System.IO.Path]::GetTempPath()) "openai-skills-$Commit"
    $ZipPath = "$TempRoot.zip"
    if (Test-Path -LiteralPath $TempRoot) { Remove-Item -Recurse -Force -LiteralPath $TempRoot }
    if (Test-Path -LiteralPath $ZipPath) { Remove-Item -Force -LiteralPath $ZipPath }
    Invoke-WebRequest -UseBasicParsing -Uri "https://github.com/openai/skills/archive/$Commit.zip" -OutFile $ZipPath
    Expand-Archive -LiteralPath $ZipPath -DestinationPath $TempRoot
}

foreach ($Skill in $Manifest.skills) {
    $Target = Get-DirectSkillTarget -Name $Skill.name
    if ($Skill.kind -eq 'project') {
        $Source = Get-ContainedPath -Base $RepoRoot -Relative $Skill.source
        Sync-SkillDirectory -Source $Source -Target $Target
    } elseif ($OfficialNeeded.name -contains $Skill.name) {
        $ExtractedRepo = Join-Path $TempRoot "skills-$($Manifest.official_source.commit)"
        $Source = Get-ContainedPath -Base $ExtractedRepo -Relative $Skill.source
        Sync-SkillDirectory -Source $Source -Target $Target
    }

    $Actual = Get-SkillHash -SkillPath $Target
    if ($Actual -ne $Skill.skill_md_sha256) {
        throw "Hash mismatch for $($Skill.name): expected $($Skill.skill_md_sha256), got $Actual"
    }
    if (-not (Test-SkillRequiredFiles -Skill $Skill -Target $Target)) {
        throw "Required file missing after install for $($Skill.name)"
    }
    Write-Host "PASS $($Skill.name) $Actual files=$(@($Skill.required_files).Count)"
}

if ($TempRoot -and (Test-Path -LiteralPath $TempRoot)) { Remove-Item -Recurse -Force -LiteralPath $TempRoot }
if ($ZipPath -and (Test-Path -LiteralPath $ZipPath)) { Remove-Item -Force -LiteralPath $ZipPath }

Write-Host "Installed skills to $TargetRoot"
Write-Host 'Start a fresh Codex session to load newly installed skills.'

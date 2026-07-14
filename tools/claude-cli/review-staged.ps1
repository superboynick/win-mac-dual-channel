[CmdletBinding()]
param(
    [ValidateSet('deepseek-v4-pro','deepseek-v4-flash')]
    [string]$Model = 'deepseek-v4-pro',
    [ValidateSet('low','medium','high')]
    [string]$Effort = 'low',
    [ValidateRange(1000, 200000)]
    [int]$MaxDiffChars = 100000,
    [string]$SettingsPath = (Join-Path $HOME '.claude\settings.json'),
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Path
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$claude = Get-Command claude -ErrorAction Stop
if (-not (Test-Path -LiteralPath $SettingsPath -PathType Leaf)) {
    throw 'CLAUDE_REVIEW_BLOCKED_LOCAL_SETTINGS_MISSING'
}

$repoRoot = (& git rev-parse --show-toplevel 2>$null).Trim()
if ($LASTEXITCODE -ne 0 -or -not $repoRoot) {
    throw 'CLAUDE_REVIEW_BLOCKED_NOT_GIT_REPOSITORY'
}
Set-Location -LiteralPath $repoRoot

$diffArgs = @('diff','--cached','--no-ext-diff','--unified=5')
if ($Path -and $Path.Count -gt 0) {
    $diffArgs += '--'
    $diffArgs += $Path
}
$diff = (& git @diffArgs | Out-String)
if ($LASTEXITCODE -ne 0) { throw 'CLAUDE_REVIEW_BLOCKED_GIT_DIFF_FAILED' }
if ([string]::IsNullOrWhiteSpace($diff)) { throw 'CLAUDE_REVIEW_BLOCKED_EMPTY_STAGED_DIFF' }
if ($diff.Length -gt $MaxDiffChars) {
    throw "CLAUDE_REVIEW_BLOCKED_DIFF_TOO_LARGE chars=$($diff.Length) max=$MaxDiffChars"
}

$prompt = @"
Act as a read-only second-model code reviewer. Review only the staged diff below. Identify
concrete correctness, consistency, regression, and missing-test issues. Do not use tools,
edit files, weaken repository controls, or expand scope. Return concise sections BLOCKERS,
NON_BLOCKING, and VERDICT. Codex will independently verify every finding.

STAGED DIFF:
$diff
"@

$prompt | & $claude.Source -p --bare --settings $SettingsPath --model $Model --tools '' `
    --permission-mode plan --effort $Effort --no-session-persistence --output-format text
exit $LASTEXITCODE

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$PromptPath,
    [Parameter(Mandatory = $true)][string]$OldCommit,
    [Parameter(Mandatory = $true)][string]$NewCommit
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'AirJetWatcher.Common.ps1')

$runnerLock = $null
$claimedTask = $null
try {
    Initialize-AirJetWatcherContext
    if ($script:TestMode) { throw 'BLOCKED_TEST_MODE_CODEX_FORBIDDEN' }
    if ($script:RuntimeStatus -ne 'ENABLED_AFTER_END_TO_END') { throw "BLOCKED_RUNTIME_$script:RuntimeStatus" }
    Assert-AirJetOid -Oid $OldCommit -Label old
    Assert-AirJetOid -Oid $NewCommit -Label new
    if (-not [Environment]::UserInteractive) { throw 'BLOCKED_NOT_INTERACTIVE_USER' }
    if ($env:SSH_CONNECTION -or $env:SSH_CLIENT -or $env:SSH_TTY) { throw 'BLOCKED_SSH_SESSION' }

    if (-not (Test-Path -LiteralPath $PromptPath -PathType Leaf)) { throw 'BLOCKED_PROMPT_MISSING' }
    if (Test-AirJetReparsePoint -Path $PromptPath) { throw 'BLOCKED_PROMPT_REPARSE_POINT' }
    $promptCanonical = Get-AirJetCanonicalExistingPath -Path $PromptPath
    if (-not (Test-AirJetChildPath -Parent $script:EventRoot -Child $promptCanonical)) { throw 'BLOCKED_PROMPT_OUTSIDE_EVENT_ROOT' }

    $pending = Read-AirJetPending
    if ($pending.phase -cne 'WAKE_REQUESTED') { throw 'BLOCKED_PENDING_PHASE' }
    if (($pending.old_commit -cne $OldCommit) -or ($pending.new_commit -cne $NewCommit)) { throw 'BLOCKED_PENDING_COMMIT_MISMATCH' }
    $task = Assert-AirJetRetryState -Old $OldCommit -New $NewCommit
    if (Test-AirJetCriticalChange -Old $OldCommit -Target $NewCommit) { throw 'BLOCKED_CRITICAL_WATCHER_UPDATE' }
    if (Test-AirJetProcessedTask -TaskId $task.Fields.task_id) { throw 'BLOCKED_TASK_ALREADY_PROCESSED' }

    $downloads = Join-Path $env:USERPROFILE 'Downloads'
    if (-not (Test-Path -LiteralPath $downloads -PathType Container)) { throw 'BLOCKED_DOWNLOADS_MISSING' }
    $downloads = Get-AirJetCanonicalExistingPath -Path $downloads
    $reports = Join-Path $downloads 'AirJetGitWatcherReports'
    if (Test-Path -LiteralPath $reports) {
        if (-not (Test-Path -LiteralPath $reports -PathType Container)) { throw 'BLOCKED_REPORT_ROOT_NOT_DIRECTORY' }
        if (Test-AirJetReparsePoint -Path $reports) { throw 'BLOCKED_REPORT_ROOT_REPARSE_POINT' }
    } else {
        [void](New-Item -ItemType Directory -Path $reports)
    }
    $reports = Get-AirJetCanonicalExistingPath -Path $reports
    if (($reports -eq $script:RepoRoot) -or (Test-AirJetChildPath -Parent $script:RepoRoot -Child $reports)) { throw 'BLOCKED_REPORT_ROOT_INSIDE_REPOSITORY' }

    $runnerLockPath = Join-Path $script:StateRoot 'runner.lock'
    try { $runnerLock = New-Item -ItemType Directory -Path $runnerLockPath -ErrorAction Stop }
    catch { throw 'BLOCKED_RUNNER_LOCK_HELD' }

    $codexCommand = Get-Command codex.cmd -ErrorAction SilentlyContinue
    if (-not $codexCommand) { $codexCommand = Get-Command codex -ErrorAction Stop }
    $codex = [IO.Path]::GetFullPath($codexCommand.Source)
    if (-not [IO.Path]::IsPathRooted($codex)) { throw 'BLOCKED_CODEX_PATH_NOT_ABSOLUTE' }

    Add-AirJetProcessedTask -Task $task.Fields -Commit $NewCommit
    $claimedTask = $task.Fields

    # Revalidate after the atomic claim and immediately before constructing the
    # execution prompt. A second runner cannot pass CreateNew for this task.
    $task = Assert-AirJetRetryState -Old $OldCommit -New $NewCommit
    if (Test-AirJetCriticalChange -Old $OldCommit -Target $NewCommit) { throw 'BLOCKED_CRITICAL_WATCHER_UPDATE' }
    Assert-AirJetClean
    if ((Get-AirJetHead) -ne $NewCommit) { throw 'BLOCKED_FINAL_HEAD_CHANGED' }
    if ((Get-AirJetRemoteOid) -ne $NewCommit) { throw 'BLOCKED_FINAL_REMOTE_MOVED' }

    $instruction = $task.Fields.instruction_path
    $instructionText = (Invoke-AirJetGit -Arguments @('show',"$NewCommit`:$instruction")).Text
    $prompt = @"
A signed, fail-closed AirJet task was delivered from the Mac peer.

OLD_COMMIT=$OldCommit
NEW_COMMIT=$NewCommit
TASK_ID=$($task.Fields.task_id)
WORKFLOW_ID=$($task.Fields.workflow_id)
PARENT_TASK_ID=$($task.Fields.parent_task_id)
HOP=$($task.Fields.hop)
MAX_HOPS=$($task.Fields.max_hops)
INSTRUCTION_PATH=$instruction

The runner independently verified HEAD, origin/main, the full linear incoming commit chain, the general signer allowlist, the KRL, the Mac-only task-tip signer, and rebuilt the task from the signed commit. Preserve peer Git safety and stage gates. Do not create a reciprocal task envelope; automatic relay is disabled.

The signed committed instruction follows:

$instructionText
"@

    Update-AirJetProcessedTaskPhase -Task $task.Fields -Commit $NewCommit -Phase CODEX_STARTED
    Write-AirJetPending -Phase CODEX_STARTED -Old $OldCommit -New $NewCommit -TaskId $task.Fields.task_id
    Write-AirJetStatus -State 'CODEX_STARTED' -Detail "task_id=$($task.Fields.task_id) sandbox=workspace-write approvals=never mode=exec" -Commit $NewCommit
    Write-Output 'Starting visible Codex exec with sandbox=workspace-write approvals=never.'
    $reportFile = Join-Path $reports 'AIRJET_GIT_WATCHER_LAST_REPORT.txt'
    $code = 1
    Invoke-AirJetCodexUtf8Stdin -Codex $codex -RepoRoot $script:RepoRoot -Reports $reports -ReportFile $reportFile -Prompt $prompt -ApprovalPolicyConfig 'approval_policy="never"' -ExitCode ([ref]$code)
    if ($code -eq 0) {
        Update-AirJetProcessedTaskPhase -Task $task.Fields -Commit $NewCommit -Phase CODEX_EXITED_0
        Write-AirJetPending -Phase CODEX_EXITED_0 -Old $OldCommit -New $NewCommit -TaskId $task.Fields.task_id
        Write-AirJetStatus -State 'CODEX_EXITED_0' -Detail "task_id=$($task.Fields.task_id)" -Commit $NewCommit
    } else {
        Update-AirJetProcessedTaskPhase -Task $task.Fields -Commit $NewCommit -Phase CODEX_FAILED
        Write-AirJetPending -Phase CODEX_FAILED -Old $OldCommit -New $NewCommit -TaskId $task.Fields.task_id
        Write-AirJetStatus -State 'CODEX_FAILED' -Detail "task_id=$($task.Fields.task_id) exit=$code" -Commit $NewCommit
    }
    Write-Output "CODEX_EXIT=$code"
    exit $code
} catch {
    if ($claimedTask) {
        try {
            Update-AirJetProcessedTaskPhase -Task $claimedTask -Commit $NewCommit -Phase CODEX_FAILED
            Write-AirJetPending -Phase CODEX_FAILED -Old $OldCommit -New $NewCommit -TaskId $claimedTask.task_id
            Write-AirJetStatus -State 'CODEX_FAILED' -Detail "task_id=$($claimedTask.task_id) runner_error=$($_.Exception.Message)" -Commit $NewCommit
        } catch { }
    }
    [Console]::Error.WriteLine($_.Exception.Message)
    exit 1
} finally {
    if ($runnerLock) { Remove-Item -LiteralPath $runnerLock.FullName -Force -ErrorAction SilentlyContinue }
}

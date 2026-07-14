[CmdletBinding()]
param(
    [ValidateRange(10, 3600)][int]$PollSeconds = 10,
    [switch]$Once,
    [switch]$NoWake,
    [switch]$RetryPending
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'AirJetWatcher.Common.ps1')

function Stop-AirJetWatcherBlocked {
    param([Parameter(Mandatory = $true)][string]$Message, [string]$Commit = '')
    $state = if ($Message -match '^(BLOCKED_[A-Z0-9_]+)') { $Matches[1] } else { 'BLOCKED_INTERNAL_ERROR' }
    try { Write-AirJetStatus -State $state -Detail $Message -Commit $Commit } catch { }
    [Console]::Error.WriteLine("WATCHER_BLOCKED=$state detail=$($Message -replace '[\r\n\t]+',' ') commit=$Commit")
    exit 1
}

function Invoke-AirJetFastForward {
    param([Parameter(Mandatory = $true)][string]$Old, [Parameter(Mandatory = $true)][string]$Target)
    if (Test-AirJetCriticalChange -Old $Old -Target $Target) { throw 'BLOCKED_CRITICAL_WATCHER_UPDATE' }
    $task = Get-AirJetTaskClassification -Old $Old -Target $Target
    Assert-AirJetIncomingChain -Old $Old -Target $Target -TaskTip:($task.State -eq 'VALID')
    if ((Get-AirJetRemoteOid) -ne $Target) { throw 'BLOCKED_REMOTE_MOVED_DURING_VALIDATION' }
    Assert-AirJetRepositoryIdentity
    Assert-AirJetClean
    if ((Get-AirJetHead) -ne $Old) { throw 'BLOCKED_HEAD_CHANGED_BEFORE_PULL' }

    if ($task.State -eq 'VALID') { Write-AirJetPending -Phase PULL_PENDING -Old $Old -New $Target -TaskId $task.Fields.task_id }
    try {
        [void](Invoke-AirJetGit -Arguments @('-c','core.hooksPath=NUL','-c','submodule.recurse=false','merge','--ff-only','--no-edit',$Target))
    } catch {
        if (Test-Path -LiteralPath $script:PendingPath -PathType Leaf) { Remove-Item -LiteralPath $script:PendingPath -Force }
        throw
    }
    Assert-AirJetClean
    if ((Get-AirJetHead) -ne $Target) { throw 'BLOCKED_POST_PULL_HEAD' }
    if ((Get-AirJetRemoteOid) -ne $Target) { throw 'BLOCKED_POST_PULL_REMOTE_MOVED' }

    if ($task.State -eq 'NONE') {
        Write-AirJetStatus -State 'SYNCED_NO_WINDOWS_TASK' -Detail $task.Detail -Commit $Target
        Write-Output "SYNCED_NO_WINDOWS_TASK=$Target"
        return
    }

    $task = Get-AirJetTaskClassification -Old $Old -Target $Target -WriteEvent
    if (Test-AirJetProcessedTask -TaskId $task.Fields.task_id) {
        if (Test-Path -LiteralPath $script:PendingPath -PathType Leaf) { Remove-Item -LiteralPath $script:PendingPath -Force }
        Write-AirJetStatus -State 'SYNCED_TASK_ALREADY_PROCESSED' -Detail $task.Detail -Commit $Target
        Write-Output "SYNCED_TASK_ALREADY_PROCESSED=$($task.Fields.task_id)"
        return
    }
    Invoke-AirJetWake -Old $Old -Target $Target -Task $task
}

function ConvertTo-AirJetCommandLineArgument {
    param([Parameter(Mandatory = $true)][string]$Value)
    return '"' + ($Value -replace '(\\*)"', '$1$1\"' -replace '(\\+)$', '$1$1') + '"'
}

function Invoke-AirJetWake {
    param([Parameter(Mandatory = $true)][string]$Old, [Parameter(Mandatory = $true)][string]$Target, [Parameter(Mandatory = $true)]$Task)
    if ($script:TestMode -and (-not $NoWake)) { throw 'BLOCKED_TEST_MODE_WAKE_FORBIDDEN' }
    if ($NoWake) {
        Write-AirJetPending -Phase PENDING_NO_WAKE -Old $Old -New $Target -TaskId $Task.Fields.task_id
        Write-AirJetStatus -State 'PENDING_NO_WAKE' -Detail $Task.Detail -Commit $Target
        Write-Output "PENDING_NO_WAKE=$Target"
        return
    }
    if ($script:RuntimeStatus -ne 'ENABLED_AFTER_END_TO_END') { throw "BLOCKED_RUNTIME_$script:RuntimeStatus" }
    if (-not [Environment]::UserInteractive) { throw 'BLOCKED_NOT_INTERACTIVE_USER' }
    if ($env:SSH_CONNECTION -or $env:SSH_CLIENT -or $env:SSH_TTY) { throw 'BLOCKED_SSH_SESSION' }
    $sessionId = [Diagnostics.Process]::GetCurrentProcess().SessionId
    $explorer = @(Get-Process explorer -ErrorAction SilentlyContinue | Where-Object { $_.SessionId -eq $sessionId })
    if ($explorer.Count -lt 1) { throw 'BLOCKED_NO_EXPLORER_IN_CURRENT_SESSION' }
    $runner = Join-Path $PSScriptRoot 'Run-AwakenedCodex.ps1'
    if (-not (Test-Path -LiteralPath $runner -PathType Leaf)) { throw 'BLOCKED_RUNNER_MISSING' }
    if (Test-AirJetReparsePoint -Path $runner) { throw 'BLOCKED_RUNNER_REPARSE_POINT' }
    $promptPath = Join-Path $script:EventRoot "wake-$Target.txt"
    Write-AirJetAtomicLines -Path $promptPath -Lines @(
        'The Windows AirJet Git watcher received a verified task.',
        "OLD_COMMIT=$Old", "NEW_COMMIT=$Target", "TASK_ID=$($Task.Fields.task_id)",
        "WORKFLOW_ID=$($Task.Fields.workflow_id)", "INSTRUCTION_PATH=$($Task.Fields.instruction_path)",
        'The runner will independently revalidate signed Git state before starting Codex.'
    )
    Write-AirJetPending -Phase WAKE_REQUESTED -Old $Old -New $Target -TaskId $Task.Fields.task_id
    Write-AirJetStatus -State 'SHELL_REQUESTED_NOT_USER_OBSERVED' -Detail $Task.Detail -Commit $Target
    $powerShell = (Get-Command powershell.exe -ErrorAction Stop).Source
    $arguments = @('-NoProfile','-ExecutionPolicy','RemoteSigned','-File',$runner,$promptPath,$Old,$Target)
    $commandLine = ($arguments | ForEach-Object { ConvertTo-AirJetCommandLineArgument -Value $_ }) -join ' '
    $process = Start-Process -FilePath $powerShell -ArgumentList $commandLine -PassThru
    Write-Output "SHELL_REQUESTED_PID=$($process.Id)"
    Wait-AirJetTaskCompletion -Process $process -Task $Task -Target $Target
}

function Wait-AirJetTaskCompletion {
    param(
        [Parameter(Mandatory = $true)][Diagnostics.Process]$Process,
        [Parameter(Mandatory = $true)]$Task,
        [Parameter(Mandatory = $true)][string]$Target
    )
    $notStarted = 0
    while ($true) {
        $pending = Read-AirJetPending
        switch ($pending.phase) {
            'WAKE_REQUESTED' {
                $notStarted++
                if ($Process.HasExited) { throw "BLOCKED_RUNNER_EXITED_BEFORE_CODEX exit=$($Process.ExitCode)" }
                if ($notStarted -gt 60) { throw 'BLOCKED_RUNNER_START_TIMEOUT' }
            }
            'CODEX_STARTED' {
                $notStarted = 0
                Write-AirJetStatus -State 'CODEX_RUNNING_NOT_USER_OBSERVED' -Detail "task_id=$($Task.Fields.task_id)" -Commit $Target
            }
            'CODEX_EXITED_0' {
                $claim = Join-Path $script:ProcessedRoot "$($Task.Fields.task_id).claim"
                $claimFields = Get-AirJetStateFields -Path $claim
                if (($claimFields.task_id -cne $Task.Fields.task_id) -or ($claimFields.commit -cne $Target) -or ($claimFields.phase -cne 'CODEX_EXITED_0')) {
                    throw 'BLOCKED_PROCESSED_CLAIM_TERMINAL_MISMATCH'
                }
                $destination = Join-Path $script:EventRoot "completed-$($Task.Fields.task_id)-$Target.state"
                if (Test-Path -LiteralPath $destination) { throw 'BLOCKED_COMPLETED_STATE_EXISTS' }
                Move-Item -LiteralPath $script:PendingPath -Destination $destination
                Write-AirJetStatus -State 'TASK_COMPLETED' -Detail "task_id=$($Task.Fields.task_id) state=$destination" -Commit $Target
                return
            }
            'CODEX_FAILED' { throw "BLOCKED_CODEX_TASK_FAILED task_id=$($Task.Fields.task_id)" }
            default { throw "BLOCKED_RUNNER_STATE phase=$($pending.phase)" }
        }
        Start-Sleep -Seconds 5
    }
}

function Invoke-AirJetPollOnce {
    Assert-AirJetRepositoryIdentity
    Assert-AirJetClean
    if (Test-Path -LiteralPath $script:PendingPath -PathType Leaf) { throw 'BLOCKED_PENDING_EVENT' }
    $head = Get-AirJetHead
    $remote = Get-AirJetRemoteOid
    if ($remote -eq $head) {
        Write-AirJetStatus -State 'WATCHING' -Detail 'clean; remote main unchanged; no model invoked' -Commit $head
        return
    }
    Invoke-AirJetFetch
    Assert-AirJetRepositoryIdentity
    Assert-AirJetClean
    if ((Get-AirJetHead) -ne $head) { throw 'BLOCKED_HEAD_CHANGED_AFTER_FETCH' }
    $counts = Get-AirJetCounts
    if ($counts.Ahead -ne 0) { throw "BLOCKED_LOCAL_AHEAD_OR_DIVERGED ahead=$($counts.Ahead) behind=$($counts.Behind)" }
    if ($counts.Behind -eq 0) {
        Write-AirJetStatus -State 'WATCHING' -Detail 'fetch completed; no fast-forward update required' -Commit $head
        return
    }
    $target = (Invoke-AirJetGit -Arguments @('rev-parse','origin/main')).Text.ToLowerInvariant()
    Assert-AirJetOid -Oid $target -Label origin_main
    Invoke-AirJetFastForward -Old $head -Target $target
}

function Invoke-AirJetRetry {
    $pending = Read-AirJetPending
    if (@('PULL_PENDING','READY_TO_WAKE','PENDING_NO_WAKE') -cnotcontains $pending.phase) { throw "BLOCKED_PENDING_RETRY_PHASE phase=$($pending.phase)" }
    if ($pending.phase -eq 'PULL_PENDING') {
        Assert-AirJetRepositoryIdentity
        Assert-AirJetClean
        $head = Get-AirJetHead
        if ($head -eq $pending.old_commit) {
            if ((Get-AirJetRemoteOid) -ne $pending.new_commit) { throw 'BLOCKED_PENDING_REMOTE_MOVED' }
            Invoke-AirJetFetch
            if ((Invoke-AirJetGit -Arguments @('rev-parse','origin/main')).Text.ToLowerInvariant() -ne $pending.new_commit) { throw 'BLOCKED_PENDING_REMOTE_MOVED' }
            Remove-Item -LiteralPath $script:PendingPath -Force
            Invoke-AirJetFastForward -Old $pending.old_commit -Target $pending.new_commit
            return
        }
        if ($head -ne $pending.new_commit) { throw 'BLOCKED_PENDING_HEAD_CHANGED' }
    }
    $task = Assert-AirJetRetryState -Old $pending.old_commit -New $pending.new_commit
    if (Test-AirJetProcessedTask -TaskId $task.Fields.task_id) { throw 'BLOCKED_TASK_ALREADY_PROCESSED' }
    Invoke-AirJetWake -Old $pending.old_commit -Target $pending.new_commit -Task $task
}

$lockHeld = $false
try {
    Initialize-AirJetWatcherContext
    if ((-not $script:TestMode) -and ($script:RuntimeStatus -ne 'ENABLED_AFTER_END_TO_END') -and ((-not $Once) -or $RetryPending -or (-not $NoWake))) {
        throw "BLOCKED_RUNTIME_$script:RuntimeStatus"
    }
    if (Test-Path -LiteralPath $script:LockPath -PathType Container) {
        $stale = $true
        if (Test-Path -LiteralPath $script:PidPath -PathType Leaf) {
            $oldPid = ([IO.File]::ReadAllText($script:PidPath)).Trim()
            if ($oldPid -match '^\d+$') {
                $oldProcess = Get-Process -Id ([int]$oldPid) -ErrorAction SilentlyContinue
                if ($oldProcess) {
                    $oldCommand = (Get-CimInstance Win32_Process -Filter "ProcessId=$oldPid" -ErrorAction SilentlyContinue).CommandLine
                    if ($oldCommand -and ($oldCommand.IndexOf($PSCommandPath,[StringComparison]::OrdinalIgnoreCase) -ge 0)) { $stale = $false }
                }
            }
        }
        if (-not $stale) { throw 'BLOCKED_WATCHER_LOCK_HELD' }
        Remove-Item -LiteralPath $script:PidPath -Force -ErrorAction SilentlyContinue
        Remove-Item -LiteralPath $script:LockPath -Force -ErrorAction Stop
    }
    try {
        [void](New-Item -ItemType Directory -Path $script:LockPath -ErrorAction Stop)
        $lockHeld = $true
    } catch {
        throw 'BLOCKED_WATCHER_LOCK_HELD'
    }
    Write-AirJetAtomicLines -Path $script:PidPath -Lines @([string]$PID)
    Remove-Item -LiteralPath $script:StopPath -Force -ErrorAction SilentlyContinue
    if ($RetryPending) {
        Invoke-AirJetRetry
    } elseif ($Once) {
        Invoke-AirJetPollOnce
    } else {
        while ($true) {
            if (Test-Path -LiteralPath $script:StopPath -PathType Leaf) {
                Remove-Item -LiteralPath $script:StopPath -Force
                Write-AirJetStatus -State 'STOPPED' -Detail 'stop requested' -Commit (Get-AirJetHead)
                break
            }
            Invoke-AirJetPollOnce
            Start-Sleep -Seconds $PollSeconds
        }
    }
} catch {
    Stop-AirJetWatcherBlocked -Message $_.Exception.Message
} finally {
    if ($lockHeld) {
        Remove-Item -LiteralPath $script:PidPath -Force -ErrorAction SilentlyContinue
        Remove-Item -LiteralPath $script:LockPath -Force -ErrorAction SilentlyContinue
    }
}

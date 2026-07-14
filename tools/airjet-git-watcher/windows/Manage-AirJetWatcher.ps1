[CmdletBinding()]
param(
    [ValidateSet('status','once','start','stop','retry','acknowledge')][string]$Action = 'status',
    [ValidateRange(30, 3600)][int]$PollSeconds = 180
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$RuntimeStatus = 'ENABLED_AFTER_END_TO_END'
$watcher = Join-Path $PSScriptRoot 'Watch-AirJetGit.ps1'
. (Join-Path $PSScriptRoot 'AirJetWatcher.Common.ps1')

if ((($Action -eq 'start') -or ($Action -eq 'retry')) -and ($RuntimeStatus -ne 'ENABLED_AFTER_END_TO_END')) {
    [Console]::Error.WriteLine("$($Action.ToUpperInvariant())_RESULT=REFUSED_$RuntimeStatus")
    exit 1
}

function Assert-AirJetVisibleSession {
    if (-not [Environment]::UserInteractive) { throw 'BLOCKED_NOT_INTERACTIVE_USER' }
    if ($env:SSH_CONNECTION -or $env:SSH_CLIENT -or $env:SSH_TTY) { throw 'BLOCKED_SSH_SESSION' }
    $sessionId = [Diagnostics.Process]::GetCurrentProcess().SessionId
    if (@(Get-Process explorer -ErrorAction SilentlyContinue | Where-Object { $_.SessionId -eq $sessionId }).Count -lt 1) {
        throw 'BLOCKED_NO_EXPLORER_IN_CURRENT_SESSION'
    }
}

function Get-AirJetWatcherProcess {
    if (-not (Test-Path -LiteralPath $script:PidPath -PathType Leaf)) { return $null }
    $text = ([IO.File]::ReadAllText($script:PidPath)).Trim()
    if ($text -notmatch '^\d+$') { return $null }
    $process = Get-Process -Id ([int]$text) -ErrorAction SilentlyContinue
    if (-not $process) { return $null }
    $commandLine = (Get-CimInstance Win32_Process -Filter "ProcessId=$text" -ErrorAction Stop).CommandLine
    if (-not $commandLine -or ($commandLine.IndexOf($watcher, [StringComparison]::OrdinalIgnoreCase) -lt 0)) {
        throw 'BLOCKED_PID_NOT_AIRJET_WATCHER'
    }
    return $process
}

function Show-AirJetWatcherStatus {
    $process = Get-AirJetWatcherProcess
    $status = Get-AirJetStateFields -Path $script:StatusPath
    $pending = Get-AirJetStateFields -Path $script:PendingPath
    $state = if ($status.ContainsKey('state')) { $status.state } else { 'UNKNOWN' }
    $detail = if ($status.ContainsKey('detail')) { $status.detail } else { 'NONE' }
    $commit = if ($status.ContainsKey('commit')) { $status.commit } else { 'UNKNOWN' }
    $phase = if ($pending.ContainsKey('phase')) { $pending.phase } else { 'NONE' }
    $newCommit = if ($pending.ContainsKey('new_commit')) { $pending.new_commit } else { 'NONE' }
    Write-Output "WATCHER_RUNNING=$([bool]$process)"
    Write-Output "WATCHER_PID=$(if ($process) { $process.Id } else { 'NONE' })"
    Write-Output "WATCHER_STATE=$state"
    Write-Output "WATCHER_DETAIL=$detail"
    Write-Output "WATCHER_COMMIT=$commit"
    Write-Output "PENDING_EVENT=$(Test-Path -LiteralPath $script:PendingPath -PathType Leaf)"
    Write-Output "PENDING_PHASE=$phase"
    Write-Output "PENDING_COMMIT=$newCommit"
    Write-Output 'AUTO_START=DISABLED'
    Write-Output "RUNTIME_STATUS=$RuntimeStatus"
}

try {
    Initialize-AirJetWatcherContext
    if ($script:TestMode -and (($Action -eq 'start') -or ($Action -eq 'retry'))) {
        [Console]::Error.WriteLine("$($Action.ToUpperInvariant())_RESULT=REFUSED_TEST_MODE")
        exit 1
    }
    switch ($Action) {
        'status' { Show-AirJetWatcherStatus }
        'once' {
            if (Get-AirJetWatcherProcess) { throw 'BLOCKED_WATCHER_ALREADY_RUNNING' }
            & powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File $watcher -Once -NoWake -PollSeconds $PollSeconds
            $code = $LASTEXITCODE
            Show-AirJetWatcherStatus
            exit $code
        }
        'start' {
            Assert-AirJetVisibleSession
            if (Get-AirJetWatcherProcess) { throw 'BLOCKED_WATCHER_ALREADY_RUNNING' }
            if (Test-Path -LiteralPath $script:PendingPath -PathType Leaf) { throw 'BLOCKED_PENDING_EVENT' }
            foreach ($name in @('AIRJET_WATCHER_TEST_MODE','AIRJET_REPO_ROOT','AIRJET_WATCHER_STATE_ROOT')) { Remove-Item "Env:$name" -ErrorAction SilentlyContinue }
            $powerShell = (Get-Command powershell.exe -ErrorAction Stop).Source
            $arguments = "-NoProfile -ExecutionPolicy RemoteSigned -File `"$watcher`" -PollSeconds $PollSeconds"
            $process = Start-Process -FilePath $powerShell -ArgumentList $arguments -WindowStyle Hidden -PassThru
            Start-Sleep -Seconds 2
            if ($process.HasExited) { throw "BLOCKED_WATCHER_START_FAILED exit=$($process.ExitCode)" }
            Write-Output "STARTED_PID=$($process.Id)"
            Show-AirJetWatcherStatus
        }
        'retry' {
            Assert-AirJetVisibleSession
            if (Get-AirJetWatcherProcess) { throw 'BLOCKED_WATCHER_ALREADY_RUNNING' }
            foreach ($name in @('AIRJET_WATCHER_TEST_MODE','AIRJET_REPO_ROOT','AIRJET_WATCHER_STATE_ROOT')) { Remove-Item "Env:$name" -ErrorAction SilentlyContinue }
            & powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File $watcher -Once -RetryPending -PollSeconds $PollSeconds
            $code = $LASTEXITCODE
            Show-AirJetWatcherStatus
            exit $code
        }
        'stop' {
            $process = Get-AirJetWatcherProcess
            if (-not $process) { Write-Output 'STOP_RESULT=NOT_RUNNING'; Show-AirJetWatcherStatus; break }
            Write-AirJetAtomicLines -Path $script:StopPath -Lines @("requested_at=$([DateTime]::UtcNow.ToString('o'))")
            if (-not $process.WaitForExit(($PollSeconds + 15) * 1000)) { throw 'BLOCKED_STOP_TIMEOUT' }
            Write-Output 'STOP_RESULT=STOPPED'
            Show-AirJetWatcherStatus
        }
        'acknowledge' {
            if (Get-AirJetWatcherProcess) { throw 'BLOCKED_WATCHER_RUNNING' }
            $pending = Read-AirJetPending
            if (@('CODEX_EXITED_0','CODEX_FAILED') -cnotcontains $pending.phase) { throw 'BLOCKED_ACKNOWLEDGE_NONTERMINAL' }
            if (-not $pending.ContainsKey('task_id')) { throw 'BLOCKED_ACKNOWLEDGE_TASK_ID_MISSING' }
            $claim = Join-Path $script:ProcessedRoot "$($pending.task_id).claim"
            $claimFields = Get-AirJetStateFields -Path $claim
            if (($claimFields.task_id -cne $pending.task_id) -or ($claimFields.commit -cne $pending.new_commit) -or ($claimFields.phase -cne $pending.phase)) {
                throw 'BLOCKED_ACKNOWLEDGE_CLAIM_MISMATCH'
            }
            $destination = Join-Path $script:EventRoot "acknowledged-$($pending.new_commit)-$([DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ')).state"
            Move-Item -LiteralPath $script:PendingPath -Destination $destination
            Write-Output 'ACKNOWLEDGE_RESULT=ARCHIVED'
            Write-Output "ACKNOWLEDGED_PATH=$destination"
        }
    }
} catch {
    [Console]::Error.WriteLine($_.Exception.Message)
    exit 1
}
exit 0

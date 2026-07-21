[CmdletBinding()]
param([ValidateRange(1,12)][int]$Hours = 10)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$reports = Join-Path $env:USERPROFILE 'Downloads\AirJetGitWatcherReports'
$statePath = Join-Path $reports 'AIRJET_10H_AWAKE.env'
$logPath = Join-Path $reports 'AIRJET_10H_AWAKE.log'
$lockPath = Join-Path $reports 'AIRJET_10H_AWAKE.lock'
$deadline = [DateTime]::UtcNow.AddHours($Hours)

if (-not (Test-Path -LiteralPath $reports -PathType Container)) {
    [void](New-Item -ItemType Directory -Path $reports)
}

$lock = $null
try {
    $lock = [IO.File]::Open($lockPath, [IO.FileMode]::OpenOrCreate, [IO.FileAccess]::ReadWrite, [IO.FileShare]::None)
} catch [IO.IOException] {
    Add-Content -LiteralPath $logPath -Encoding UTF8 -Value "$([DateTime]::UtcNow.ToString('o')) ALREADY_ACTIVE"
    exit 0
}

if (-not ('AirJet.PowerRequest' -as [type])) {
    Add-Type @'
using System;
using System.Runtime.InteropServices;
namespace AirJet {
    public static class PowerRequest {
        [DllImport("kernel32.dll", SetLastError = true)]
        public static extern uint SetThreadExecutionState(uint flags);
    }
}
'@
}

$continuous = [uint32]2147483648
$systemRequired = [uint32]0x00000001
$activeFlags = [uint32]($continuous -bor $systemRequired)

function Write-AwakeState([string]$Status) {
    $temporary = "$statePath.$PID.tmp"
    @(
        'schema_version=1'
        "status=$Status"
        "pid=$PID"
        "started_at_utc=$($script:startedAt.ToString('o'))"
        "deadline_utc=$($deadline.ToString('o'))"
        "updated_at_utc=$([DateTime]::UtcNow.ToString('o'))"
        "hours=$Hours"
        'power_plan_modified=false'
        'display_required=false'
    ) | Set-Content -LiteralPath $temporary -Encoding ASCII
    Move-Item -LiteralPath $temporary -Destination $statePath -Force
}

$startedAt = [DateTime]::UtcNow
try {
    while ([DateTime]::UtcNow -lt $deadline) {
        $result = [AirJet.PowerRequest]::SetThreadExecutionState($activeFlags)
        if ($result -eq 0) { throw 'SET_THREAD_EXECUTION_STATE_FAILED' }
        Write-AwakeState 'ACTIVE'
        Add-Content -LiteralPath $logPath -Encoding UTF8 -Value "$([DateTime]::UtcNow.ToString('o')) ACTIVE pid=$PID deadline=$($deadline.ToString('o'))"
        Start-Sleep -Seconds 300
    }
    Write-AwakeState 'COMPLETED'
} catch {
    Write-AwakeState 'FAILED'
    Add-Content -LiteralPath $logPath -Encoding UTF8 -Value "$([DateTime]::UtcNow.ToString('o')) FAILED error=$($_.Exception.Message)"
    exit 1
} finally {
    [void][AirJet.PowerRequest]::SetThreadExecutionState($continuous)
    if ($lock) { $lock.Dispose() }
}

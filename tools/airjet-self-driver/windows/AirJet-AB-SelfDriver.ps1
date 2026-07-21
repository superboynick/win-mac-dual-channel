[CmdletBinding()]
param()

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$reports = Join-Path $env:USERPROFILE 'Downloads\AirJetGitWatcherReports'
$repo = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..\..')).Path
$lockPath = Join-Path $reports 'self-driver.lock'
$logPath = Join-Path $reports 'AIRJET_AB_SELF_DRIVER.log'

function Write-DriverLog([string]$Message) {
    Add-Content -LiteralPath $logPath -Encoding UTF8 -Value "$([DateTime]::UtcNow.ToString('o')) $Message"
}

function Get-Runner([string]$ScriptName) {
    Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
        $_.Name -eq 'powershell.exe' -and $_.CommandLine -like "*$ScriptName*"
    } | Select-Object -First 1
}

function Move-UntrackedReceiptsOutsideGit {
    $receiptRoot = Join-Path $repo 'airjet-simulation\collaboration\receipts'
    if (-not (Test-Path -LiteralPath $receiptRoot -PathType Container)) { return }
    $receiptRootItem = Get-Item -LiteralPath $receiptRoot
    if (($receiptRootItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
        Write-DriverLog "BLOCKED_RECEIPT_ROOT_REPARSE path=$receiptRoot"
        throw 'BLOCKED_RECEIPT_ROOT_REPARSE'
    }
    $git = (Get-Command git.exe -ErrorAction SilentlyContinue)
    if (-not $git) { $git = Get-Command git -ErrorAction Stop }
    foreach ($item in Get-ChildItem -LiteralPath $receiptRoot -Filter 'windows-receipt-*.txt' -File -ErrorAction SilentlyContinue) {
        if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
            Write-DriverLog "BLOCKED_RECEIPT_REPARSE path=$($item.FullName)"
            throw 'BLOCKED_RECEIPT_REPARSE'
        }
        $relative = 'airjet-simulation/collaboration/receipts/' + $item.Name
        & $git.Source -C $repo ls-files --error-unmatch -- $relative *> $null
        $trackedExit = $LASTEXITCODE
        if ($trackedExit -eq 0) {
            Write-DriverLog "TRACKED_RECEIPT_PRESERVED path=$relative"
            continue
        }
        if ($trackedExit -ne 1) {
            Write-DriverLog "BLOCKED_GIT_TRACKING_QUERY path=$relative exit=$trackedExit"
            throw 'BLOCKED_GIT_TRACKING_QUERY'
        }
        $untracked = @(& $git.Source -C $repo ls-files --others --exclude-standard -- $relative 2>$null)
        $untrackedExit = $LASTEXITCODE
        if ($untrackedExit -ne 0 -or $untracked.Count -ne 1 -or $untracked[0] -ne $relative) {
            Write-DriverLog "BLOCKED_RECEIPT_NOT_CONFIRMED_UNTRACKED path=$relative exit=$untrackedExit matches=$($untracked.Count)"
            throw 'BLOCKED_RECEIPT_NOT_CONFIRMED_UNTRACKED'
        }
        $probe = $null
        try {
            $probe = [IO.File]::Open($item.FullName, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::None)
        } catch [IO.IOException] {
            Write-DriverLog "RECEIPT_BUSY_DEFERRED path=$relative"
            throw 'BLOCKED_RECEIPT_BUSY'
        } finally {
            if ($probe) { $probe.Dispose() }
        }
        $destination = Join-Path $reports $item.Name
        if (Test-Path -LiteralPath $destination) {
            $destination = Join-Path $reports ("{0}-{1}{2}" -f $item.BaseName, [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ'), $item.Extension)
        }
        Move-Item -LiteralPath $item.FullName -Destination $destination
        Write-DriverLog "UNTRACKED_RECEIPT_QUARANTINED source=$relative destination=$destination"
    }
}

function Start-Line([string]$Line, [string]$ScriptName) {
    $runner = Join-Path $reports $ScriptName
    if (-not (Test-Path -LiteralPath $runner -PathType Leaf)) {
        Write-DriverLog "$Line BLOCKED_RUNNER_MISSING path=$runner"
        return
    }
    if (Get-Runner $ScriptName) {
        Write-DriverLog "$Line RUNNING_NO_DUPLICATE"
        return
    }
    $process = Start-Process powershell.exe -ArgumentList @(
        '-NoProfile','-ExecutionPolicy','RemoteSigned','-File',$runner
    ) -WindowStyle Hidden -PassThru
    Write-DriverLog "$Line STARTED pid=$($process.Id) runner=$ScriptName"
}

$lock = $null
try {
    if (-not (Test-Path -LiteralPath $reports -PathType Container)) {
        [void](New-Item -ItemType Directory -Path $reports)
    }
    $lock = [IO.File]::Open($lockPath, [IO.FileMode]::OpenOrCreate, [IO.FileAccess]::ReadWrite, [IO.FileShare]::None)
} catch [IO.IOException] {
    Write-DriverLog 'SKIP_LOCK_HELD'
    exit 0
}

try {
    Write-DriverLog 'TICK'
    Move-UntrackedReceiptsOutsideGit
    Start-Line 'A' 'Run-AirJetPlanA.ps1'
    Start-Line 'B' 'Run-AirJetPlanB.ps1'
} catch {
    Write-DriverLog "FAILED error=$($_.Exception.Message)"
    exit 1
} finally {
    if ($lock) { $lock.Dispose() }
}
exit 0

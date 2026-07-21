[CmdletBinding()]
param()

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$reports = Join-Path $env:USERPROFILE 'Downloads\AirJetGitWatcherReports'
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
    Write-DriverLog 'TICK'
    Start-Line 'A' 'Run-AirJetPlanA.ps1'
    Start-Line 'B' 'Run-AirJetPlanB.ps1'
} catch [IO.IOException] {
    Write-DriverLog 'SKIP_LOCK_HELD'
} catch {
    Write-DriverLog "FAILED error=$($_.Exception.Message)"
    exit 1
} finally {
    if ($lock) { $lock.Dispose() }
}
exit 0

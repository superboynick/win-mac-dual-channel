[CmdletBinding()]
param(
    [string]$RepositoryRoot = 'C:\Users\admin\win-mac-dual-channel',
    [string]$InstallRoot = (Join-Path $env:LOCALAPPDATA 'Programs\AirJetGitWatcher'),
    [string]$StateRoot = (Join-Path $env:LOCALAPPDATA 'AirJetGitWatcher'),
    [switch]$RegisterAtLogOn
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$ExpectedRemote = 'ssh://git@ssh.github.com:443/superboynick/win-mac-dual-channel.git'
$RuntimeFiles = @(
    'AirJetWatcher.Common.ps1',
    'Watch-AirJetGit.ps1',
    'Manage-AirJetWatcher.ps1',
    'Run-AwakenedCodex.ps1'
)

function Canonical-Existing([string]$Path) {
    return [IO.Path]::GetFullPath((Resolve-Path -LiteralPath $Path -ErrorAction Stop).ProviderPath).TrimEnd('\')
}

function Is-Child([string]$Parent, [string]$Child) {
    return $Child.StartsWith($Parent.TrimEnd('\') + '\', [StringComparison]::OrdinalIgnoreCase)
}

try {
    $sourceRoot = Canonical-Existing -Path $PSScriptRoot
    $RepositoryRoot = Canonical-Existing -Path $RepositoryRoot
    if ($RepositoryRoot -cne 'C:\Users\admin\win-mac-dual-channel') { throw 'BLOCKED_INSTALL_REPOSITORY_NOT_PRODUCTION_PATH' }
    if (-not (Is-Child -Parent $RepositoryRoot -Child $sourceRoot)) { throw 'BLOCKED_INSTALL_SOURCE_OUTSIDE_REPOSITORY' }
    $git = (Get-Command git.exe -ErrorAction SilentlyContinue)
    if (-not $git) { $git = Get-Command git -ErrorAction Stop }
    $remote = (& $git.Source -C $RepositoryRoot remote get-url origin 2>&1 | Out-String).Trim()
    if (($LASTEXITCODE -ne 0) -or ($remote -cne $ExpectedRemote)) { throw 'BLOCKED_INSTALL_WRONG_REMOTE' }
    $dirty = (& $git.Source -C $RepositoryRoot status --porcelain=v1 --untracked-files=all 2>&1 | Out-String).Trim()
    if (($LASTEXITCODE -ne 0) -or $dirty) { throw 'BLOCKED_INSTALL_DIRTY_REPOSITORY' }
    $branch = (& $git.Source -C $RepositoryRoot symbolic-ref --quiet --short HEAD 2>&1 | Out-String).Trim()
    $upstream = (& $git.Source -C $RepositoryRoot rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>&1 | Out-String).Trim()
    $counts = (& $git.Source -C $RepositoryRoot rev-list --left-right --count HEAD...origin/main 2>&1 | Out-String).Trim()
    $shallow = (& $git.Source -C $RepositoryRoot rev-parse --is-shallow-repository 2>&1 | Out-String).Trim()
    if (($branch -cne 'main') -or ($upstream -cne 'origin/main') -or ($counts -notmatch '^0\s+0$') -or ($shallow -cne 'false')) { throw 'BLOCKED_INSTALL_GIT_IDENTITY' }

    foreach ($name in $RuntimeFiles) {
        $source = Join-Path $sourceRoot $name
        if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { throw "BLOCKED_INSTALL_SOURCE_MISSING name=$name" }
        $item = Get-Item -LiteralPath $source -Force
        if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw "BLOCKED_INSTALL_SOURCE_REPARSE_POINT name=$name" }
    }

    [void](New-Item -ItemType Directory -Path $InstallRoot -Force)
    [void](New-Item -ItemType Directory -Path $StateRoot -Force)
    $InstallRoot = Canonical-Existing -Path $InstallRoot
    $StateRoot = Canonical-Existing -Path $StateRoot
    if (($InstallRoot -eq $RepositoryRoot) -or (Is-Child -Parent $RepositoryRoot -Child $InstallRoot)) { throw 'BLOCKED_INSTALL_ROOT_INSIDE_REPOSITORY' }
    if (($StateRoot -eq $RepositoryRoot) -or (Is-Child -Parent $RepositoryRoot -Child $StateRoot)) { throw 'BLOCKED_STATE_ROOT_INSIDE_REPOSITORY' }
    if (($InstallRoot -eq $StateRoot) -or (Is-Child -Parent $InstallRoot -Child $StateRoot) -or (Is-Child -Parent $StateRoot -Child $InstallRoot)) { throw 'BLOCKED_CODE_AND_STATE_NOT_SEPARATE' }
    $pidPath = Join-Path $StateRoot 'watcher.pid'
    if (Test-Path -LiteralPath $pidPath -PathType Leaf) {
        $pidText = ([IO.File]::ReadAllText($pidPath)).Trim()
        if (($pidText -match '^\d+$') -and (Get-Process -Id ([int]$pidText) -ErrorAction SilentlyContinue)) { throw 'BLOCKED_INSTALL_WATCHER_RUNNING' }
    }
    foreach ($trust in @(
        @{ Name='allowed_signers'; Hash='DB1ADA7DBB7472C43CF32405A3C02F755AE5D291F4348E01C35C60C8EB2A79A6' },
        @{ Name='mac_task_signers'; Hash='0DCA6F17DECAF03EF17C97EFA69EEDD0A54C173D01AC63D3C8B29821709661A6' },
        @{ Name='revoked_keys.krl'; Hash='39462E5A1E80CC2065599E74BFDBCB903B54DC088AC1D69E1D612EE65B8C8EB7' }
    )) {
        $trustPath = Join-Path (Join-Path $StateRoot 'trust') $trust.Name
        if (-not (Test-Path -LiteralPath $trustPath -PathType Leaf)) { throw "BLOCKED_INSTALL_TRUST_MISSING name=$($trust.Name)" }
        if ((Get-FileHash -LiteralPath $trustPath -Algorithm SHA256).Hash -cne $trust.Hash) { throw "BLOCKED_INSTALL_TRUST_HASH name=$($trust.Name)" }
    }

    $manifest = @('schema_version=1', "installed_at=$([DateTime]::UtcNow.ToString('o'))", "repo=$RepositoryRoot")
    foreach ($name in $RuntimeFiles) {
        $source = Join-Path $sourceRoot $name
        $destination = Join-Path $InstallRoot $name
        $temporary = "$destination.$PID.tmp"
        Copy-Item -LiteralPath $source -Destination $temporary -Force
        $sourceHash = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
        $destinationHash = (Get-FileHash -LiteralPath $temporary -Algorithm SHA256).Hash
        if ($sourceHash -ne $destinationHash) { throw "BLOCKED_INSTALL_COPY_HASH name=$name" }
        Move-Item -LiteralPath $temporary -Destination $destination -Force
        $manifest += "file=$name|sha256=$destinationHash"
    }
    [IO.File]::WriteAllLines((Join-Path $InstallRoot 'install-manifest.state'), $manifest, (New-Object Text.UTF8Encoding($false)))

    if ($RegisterAtLogOn) {
        $manager = Join-Path $InstallRoot 'Manage-AirJetWatcher.ps1'
        $common = Join-Path $InstallRoot 'AirJetWatcher.Common.ps1'
        $watcher = Join-Path $InstallRoot 'Watch-AirJetGit.ps1'
        $runner = Join-Path $InstallRoot 'Run-AwakenedCodex.ps1'
        $managerText = [IO.File]::ReadAllText($manager)
        $commonText = [IO.File]::ReadAllText($common)
        $watcherText = [IO.File]::ReadAllText($watcher)
        $runnerText = [IO.File]::ReadAllText($runner)
        if (($managerText -notmatch "RuntimeStatus\s*=\s*'ENABLED_AFTER_END_TO_END'") -or ($commonText -notmatch "RuntimeStatus\s*=\s*'ENABLED_AFTER_END_TO_END'") -or ($watcherText -notmatch 'BLOCKED_RUNTIME_') -or ($runnerText -notmatch 'ENABLED_AFTER_END_TO_END')) { throw 'BLOCKED_REGISTER_RUNTIME_NOT_ENABLED' }
        Import-Module ScheduledTasks -ErrorAction Stop
        $powerShell = (Get-Command powershell.exe -ErrorAction Stop).Source
        $arguments = "-NoProfile -ExecutionPolicy RemoteSigned -File `"$watcher`" -PollSeconds 10"
        $existing = Get-ScheduledTask -TaskName 'AirJetGitWatcher' -ErrorAction SilentlyContinue
        if ($existing) {
            $owned = @($existing.Actions | Where-Object { ($_.Execute -eq $powerShell) -and ($_.Arguments -eq $arguments) })
            if ($owned.Count -ne 1) { throw 'BLOCKED_UNKNOWN_EXISTING_SCHEDULED_TASK' }
        }
        $action = New-ScheduledTaskAction -Execute $powerShell -Argument $arguments
        $trigger = New-ScheduledTaskTrigger -AtLogOn -User ([Security.Principal.WindowsIdentity]::GetCurrent().Name)
        $principal = New-ScheduledTaskPrincipal -UserId ([Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
        $settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -ExecutionTimeLimit ([TimeSpan]::Zero) -StartWhenAvailable -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 5)
        Register-ScheduledTask -TaskName 'AirJetGitWatcher' -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force | Out-Null
        Write-Output 'AT_LOGON_REGISTERED=true'
    } else {
        Write-Output 'AT_LOGON_REGISTERED=false'
    }
    Write-Output "INSTALL_RESULT=PASS"
    Write-Output "INSTALL_ROOT=$InstallRoot"
    Write-Output "STATE_ROOT=$StateRoot"
    Write-Output 'TRUST_FILES_COPIED=false'
    Write-Output 'TRUST_FILES_PREEXISTING_HASH_VERIFIED=true'
} catch {
    [Console]::Error.WriteLine($_.Exception.Message)
    exit 1
}

#Requires -Version 5.1

<#
.SYNOPSIS
    Performs a read-only Windows inventory for the OpenFOAM Track B T0 route.

.DESCRIPTION
    This script does not install software, start a WSL distribution, launch an
    OpenFOAM executable, or authorize an AirJet solve. Command names and
    registry entries are discovery evidence only and remain unverified until a
    separately authorized, pinned OpenFOAM Foundation v14 tooling smoke passes.
#>

[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$probeErrors = New-Object System.Collections.Generic.List[string]

function ConvertTo-RedactedPath {
    param([AllowNull()][string]$Path)

    if ([string]::IsNullOrWhiteSpace($Path)) {
        return $null
    }

    $result = $Path
    $prefixes = @(
        [ordered]@{ Value = $env:USERPROFILE; Token = '<USERPROFILE>' },
        [ordered]@{ Value = $env:ProgramFiles; Token = '<PROGRAMFILES>' },
        [ordered]@{ Value = ${env:ProgramFiles(x86)}; Token = '<PROGRAMFILES_X86>' },
        [ordered]@{ Value = $env:SystemRoot; Token = '<SYSTEMROOT>' }
    ) | Sort-Object { if ($null -eq $_.Value) { 0 } else { $_.Value.Length } } -Descending

    foreach ($prefix in $prefixes) {
        if (-not [string]::IsNullOrWhiteSpace($prefix.Value) -and
            $result.StartsWith($prefix.Value, [StringComparison]::OrdinalIgnoreCase)) {
            $result = $prefix.Token + $result.Substring($prefix.Value.Length)
            break
        }
    }
    return $result
}

$hostInventory = [ordered]@{}
try {
    $computer = Get-CimInstance -ClassName Win32_ComputerSystem
    $operatingSystem = Get-CimInstance -ClassName Win32_OperatingSystem
    $processors = @(Get-CimInstance -ClassName Win32_Processor)
    if ($processors.Count -eq 0) {
        throw 'NO_PROCESSORS_RETURNED'
    }

    $firmwareStates = @($processors | ForEach-Object {
        [bool]$_.VirtualizationFirmwareEnabled
    })
    $hostInventory = [ordered]@{
        os_caption = [string]$operatingSystem.Caption
        os_version = [string]$operatingSystem.Version
        os_build = [string]$operatingSystem.BuildNumber
        logical_processors = [int]$computer.NumberOfLogicalProcessors
        physical_memory_bytes = [uint64]$computer.TotalPhysicalMemory
        hypervisor_present = [bool]$computer.HypervisorPresent
        virtualization_firmware_telemetry_all = -not ($firmwareStates -contains $false)
        virtualization_telemetry_is_authorization = $false
    }
}
catch {
    $hostInventory = [ordered]@{ inventory_available = $false }
    $probeErrors.Add('HOST_CIM_FAILED')
}

$volumes = [ordered]@{}
foreach ($driveLetter in @('C', 'D')) {
    try {
        $drive = Get-PSDrive -Name $driveLetter -PSProvider FileSystem -ErrorAction SilentlyContinue
        if ($null -ne $drive) {
            if ($drive.Free -lt 0) {
                $probeErrors.Add("VOLUME_${driveLetter}_NEGATIVE_FREE_BYTES")
            }
            else {
                $volumes[$driveLetter] = [ordered]@{
                    free_bytes = [uint64]$drive.Free
                }
            }
        }
    }
    catch {
        $probeErrors.Add("VOLUME_${driveLetter}_PROBE_FAILED")
    }
}

$commandNames = @(
    'wsl.exe',
    'docker',
    'podman',
    'foamVersion',
    'blockMesh',
    'checkMesh',
    'foamRun'
)
$commands = [ordered]@{}
foreach ($commandName in $commandNames) {
    try {
        $command = Get-Command -Name $commandName -ErrorAction SilentlyContinue |
            Select-Object -First 1
        $commands[$commandName] = [ordered]@{
            found = ($null -ne $command)
            command_type = if ($null -ne $command) { [string]$command.CommandType } else { $null }
            source = if ($null -ne $command) {
                ConvertTo-RedactedPath -Path ([string]$command.Source)
            }
            else {
                $null
            }
            identity_verified = $false
        }
    }
    catch {
        $commands[$commandName] = [ordered]@{
            found = $false
            command_type = $null
            source = $null
            identity_verified = $false
        }
        $probeErrors.Add("COMMAND_${commandName}_PROBE_FAILED")
    }
}

$wslRegistry = [ordered]@{
    present = $false
    distributions = @()
}
$lxssPath = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Lxss'
try {
    if (Test-Path -LiteralPath $lxssPath) {
        $wslRegistry.present = $true
        $distributionRecords = @(
            foreach ($item in Get-ChildItem -LiteralPath $lxssPath) {
                $properties = Get-ItemProperty -LiteralPath $item.PSPath
                if (-not [string]::IsNullOrWhiteSpace([string]$properties.DistributionName)) {
                    [ordered]@{
                        name = [string]$properties.DistributionName
                        version = if ($null -ne $properties.Version) {
                            [int]$properties.Version
                        }
                        else {
                            $null
                        }
                        identity_verified = $false
                    }
                }
            }
        )
        $wslRegistry.distributions = @(
            $distributionRecords | Sort-Object { $_.name }
        )
    }
}
catch {
    $probeErrors.Add('WSL_REGISTRY_PROBE_FAILED')
}

$wslExitCodes = [ordered]@{
    status = $null
    version = $null
    list_quiet = $null
}
$systemWsl = Join-Path $env:SystemRoot 'System32\wsl.exe'
if (Test-Path -LiteralPath $systemWsl -PathType Leaf) {
    foreach ($probe in @(
        [ordered]@{ Name = 'status'; Arguments = @('--status') },
        [ordered]@{ Name = 'version'; Arguments = @('--version') },
        [ordered]@{ Name = 'list_quiet'; Arguments = @('--list', '--quiet') }
    )) {
        try {
            $previousErrorActionPreference = $ErrorActionPreference
            try {
                # Windows PowerShell 5.1 promotes native stderr to an error
                # record under Stop. A missing WSL distribution is an expected
                # non-zero exit state, so preserve the native exit code.
                $ErrorActionPreference = 'SilentlyContinue'
                & $systemWsl @($probe.Arguments) *> $null
                $wslExitCodes[$probe.Name] = [int]$LASTEXITCODE
            }
            finally {
                $ErrorActionPreference = $previousErrorActionPreference
            }
        }
        catch {
            $wslExitCodes[$probe.Name] = -1
            $probeErrors.Add("WSL_$($probe.Name.ToUpperInvariant())_PROBE_FAILED")
        }
    }
}

$installedAppMatches = @()
$uninstallRoots = @(
    'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*',
    'HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*',
    'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*'
)
try {
    $installedAppMatches = @(
        Get-ItemProperty -Path $uninstallRoots -ErrorAction SilentlyContinue |
            Where-Object {
                $_.DisplayName -match 'OpenFOAM|Docker|Podman|Ubuntu|Windows Subsystem for Linux|WSL'
            } |
            Sort-Object DisplayName, DisplayVersion, Publisher |
            ForEach-Object {
                [ordered]@{
                    display_name = [string]$_.DisplayName
                    display_version = [string]$_.DisplayVersion
                    publisher = [string]$_.Publisher
                    identity_verified = $false
                }
            }
    )
}
catch {
    $probeErrors.Add('INSTALLED_APPS_REGISTRY_PROBE_FAILED')
}

$standardPaths = [ordered]@{}
foreach ($path in @(
    'C:\Program Files\OpenFOAM',
    'C:\Program Files\Docker',
    'C:\ProgramData\DockerDesktop',
    'C:\Program Files\RedHat\Podman'
)) {
    try {
        $standardPaths[(ConvertTo-RedactedPath -Path $path)] =
            [bool](Test-Path -LiteralPath $path)
    }
    catch {
        $standardPaths[(ConvertTo-RedactedPath -Path $path)] = $false
        $probeErrors.Add('STANDARD_PATH_PROBE_FAILED')
    }
}

$requiredOpenFoamCommands = @('foamVersion', 'blockMesh', 'checkMesh', 'foamRun')
$allOpenFoamCommandsFound = @($requiredOpenFoamCommands | Where-Object {
    -not $commands[$_].found
}).Count -eq 0
$wslDistributionCount = @($wslRegistry.distributions).Count
$runtimeCandidateFound = ($installedAppMatches.Count -gt 0) -or
    (@($standardPaths.Values | Where-Object { $_ }).Count -gt 0)

$toolingEvidence = if ($allOpenFoamCommandsFound) {
    'WINDOWS_PATH_COMMANDS_PRESENT_UNVERIFIED'
}
elseif ($wslDistributionCount -gt 0) {
    'WSL_DISTRIBUTION_PRESENT_UNVERIFIED'
}
elseif ($runtimeCandidateFound) {
    'RUNTIME_CANDIDATE_PRESENT_UNVERIFIED'
}
else {
    'NO_RUNTIME_DETECTED_IN_DECLARED_SCOPE'
}

$result = [ordered]@{
    schema_version = 1
    observed_at_utc = [DateTime]::UtcNow.ToString('o')
    declared_probe_scope = @(
        'WINDOWS_PATH_COMMAND_DISCOVERY',
        'CURRENT_USER_WSL_REGISTRY',
        'READ_ONLY_WSL_STATUS_EXIT_CODES',
        'WINDOWS_UNINSTALL_REGISTRY',
        'STANDARD_INSTALL_PATH_EXISTENCE',
        'HOST_CAPACITY_TELEMETRY'
    )
    truth = [ordered]@{
        windows_t0_inventory = if ($probeErrors.Count -eq 0) { 'COMPLETE' } else { 'PARTIAL' }
        openfoam_tooling_evidence = $toolingEvidence
        openfoam_tooling_ready_for_smoke = $false
        openfoam_tooling_smoke = 'NOT_RUN'
        airjet_solver_authorized = $false
        stage_gate_advanced = $false
        p1_stage_gate = 'NOT_PASSED'
        p2_stage_gate = 'NOT_RUN'
        p3_p6_gate_effect = 'NONE'
    }
    probe_errors = @($probeErrors)
    exit_semantics = 'Exit 0 means the JSON inventory completed; it never means tooling readiness, solver authorization, or Gate advancement.'
    inventory = [ordered]@{
        host = $hostInventory
        volumes = $volumes
        commands = $commands
        wsl_registry = $wslRegistry
        wsl_exit_codes = $wslExitCodes
        installed_app_matches = $installedAppMatches
        standard_paths = $standardPaths
    }
}

$result | ConvertTo-Json -Depth 12 -Compress
exit 0

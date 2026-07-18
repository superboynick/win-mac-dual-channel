#Requires -Version 5.1

[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$inventory = [ordered]@{}
$probeErrors = @()

try {
    $computer = Get-CimInstance -ClassName Win32_ComputerSystem
    $operatingSystem = Get-CimInstance -ClassName Win32_OperatingSystem
    $processors = @(Get-CimInstance -ClassName Win32_Processor)
    if ($processors.Count -eq 0) {
        throw 'NO_PROCESSORS_RETURNED_BY_CIM'
    }
    $virtualizationFirmwareStates = @($processors | ForEach-Object {
        [bool]$_.VirtualizationFirmwareEnabled
    })
    $inventory.host = [ordered]@{
        name = $computer.Name
        os_caption = $operatingSystem.Caption
        os_version = $operatingSystem.Version
        os_build = $operatingSystem.BuildNumber
        logical_processors = [int]$computer.NumberOfLogicalProcessors
        physical_memory_bytes = [uint64]$computer.TotalPhysicalMemory
        hypervisor_present = [bool]$computer.HypervisorPresent
        virtualization_firmware_enabled_all = -not ($virtualizationFirmwareStates -contains $false)
    }
}
catch {
    $inventory.host = [ordered]@{ inventory_error = $_.Exception.Message }
    $probeErrors += 'host_cim'
}

$inventory.volumes = [ordered]@{}
foreach ($driveLetter in @('C', 'D')) {
    $drive = Get-PSDrive -Name $driveLetter -PSProvider FileSystem -ErrorAction SilentlyContinue
    if ($null -ne $drive) {
        if ($drive.Free -lt 0) {
            $probeErrors += "volume_${driveLetter}_negative_free_bytes"
            continue
        }
        $inventory.volumes[$driveLetter] = [ordered]@{
            free_bytes = [uint64]$drive.Free
        }
    }
}

$inventory.commands = [ordered]@{}
$commandNames = @(
    'wsl', 'docker', 'podman', 'foamVersion', 'blockMesh', 'checkMesh', 'foamRun'
)
foreach ($commandName in $commandNames) {
    $command = Get-Command -Name $commandName -ErrorAction SilentlyContinue
    $inventory.commands[$commandName] = [ordered]@{
        found = ($null -ne $command)
        source = if ($null -ne $command) { $command.Source } else { $null }
    }
}

$inventory.wsl_registry = [ordered]@{
    present = $false
    distributions = @()
}
$lxssPath = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Lxss'
try {
    if (Test-Path -LiteralPath $lxssPath) {
        $inventory.wsl_registry.present = $true
        $distributions = foreach ($item in Get-ChildItem -LiteralPath $lxssPath) {
            $properties = Get-ItemProperty -LiteralPath $item.PSPath
            if ($properties.DistributionName) {
                [ordered]@{
                    name = $properties.DistributionName
                    version = $properties.Version
                    state = $properties.State
                }
            }
        }
        $inventory.wsl_registry.distributions = @(
            $distributions | Where-Object { $null -ne $_ }
        )
    }
}
catch {
    $inventory.wsl_registry.error = $_.Exception.Message
    $probeErrors += 'wsl_registry'
}

$inventory.wsl_exit_codes = [ordered]@{}
$wslCommand = Get-Command -Name wsl.exe -ErrorAction SilentlyContinue
foreach ($probe in @(
    [ordered]@{ name = 'status'; command = 'wsl.exe --status >nul 2>nul' },
    [ordered]@{ name = 'version'; command = 'wsl.exe --version >nul 2>nul' },
    [ordered]@{ name = 'list_quiet'; command = 'wsl.exe --list --quiet >nul 2>nul' }
)) {
    if ($null -eq $wslCommand) {
        $inventory.wsl_exit_codes[$probe.name] = $null
        continue
    }
    try {
        & $env:ComSpec /d /c $probe.command
        $inventory.wsl_exit_codes[$probe.name] = [int]$LASTEXITCODE
    }
    catch {
        $inventory.wsl_exit_codes[$probe.name] = -1
        $probeErrors += "wsl_$($probe.name)"
    }
}

$inventory.installed_app_matches = @()
$uninstallRoots = @(
    'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*',
    'HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*',
    'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*'
)
try {
    $inventory.installed_app_matches = @(
        Get-ItemProperty -Path $uninstallRoots -ErrorAction SilentlyContinue |
            Where-Object {
                $_.DisplayName -match 'OpenFOAM|Docker|Podman|Ubuntu|Windows Subsystem for Linux|WSL'
            } |
            Sort-Object DisplayName, DisplayVersion, Publisher |
            ForEach-Object {
                [ordered]@{
                    display_name = $_.DisplayName
                    display_version = $_.DisplayVersion
                    publisher = $_.Publisher
                }
            }
    )
}
catch {
    $inventory.installed_apps_error = $_.Exception.Message
    $probeErrors += 'installed_apps_registry'
}

$inventory.standard_paths = [ordered]@{}
foreach ($path in @(
    'C:\Program Files\OpenFOAM',
    'C:\Program Files\Docker',
    'C:\ProgramData\DockerDesktop',
    'C:\Program Files\RedHat\Podman'
)) {
    $inventory.standard_paths[$path] = Test-Path -LiteralPath $path
}

$requiredOpenFoamCommands = @('foamVersion', 'blockMesh', 'checkMesh', 'foamRun')
$allOpenFoamCommandsFound = -not ($requiredOpenFoamCommands | Where-Object {
    -not $inventory.commands[$_].found
})
$wslDistributionCount = @($inventory.wsl_registry.distributions).Count
$openFoamToolingTruth = if ($allOpenFoamCommandsFound) {
    'DETECTED_NATIVE_WINDOWS'
}
elseif ($wslDistributionCount -gt 0) {
    'UNKNOWN_WSL_NOT_LAUNCHED'
}
else {
    'NOT_INSTALLED'
}

$output = [ordered]@{
    observed_at_utc = [DateTime]::UtcNow.ToString('o')
    truth = [ordered]@{
        WINDOWS_T0_INVENTORY = if ($probeErrors.Count -eq 0) { 'COMPLETE' } else { 'PARTIAL' }
        OPENFOAM_TOOLING = $openFoamToolingTruth
        OPENFOAM_TOOLING_PROBE_SCOPE = 'WINDOWS_PATH_AND_WSL_REGISTRY_ONLY'
        OPENFOAM_TOOLING_SMOKE = 'NOT_RUN'
        P3_P6_GATE_EFFECT = 'NONE'
    }
    probe_errors = @($probeErrors)
    exit_semantics = 'Exit 0 means inventory completed; parse truth and probe_errors for environment state.'
    inventory = $inventory
}

$output | ConvertTo-Json -Depth 8
exit 0

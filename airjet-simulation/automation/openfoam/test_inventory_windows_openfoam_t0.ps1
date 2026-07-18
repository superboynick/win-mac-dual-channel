#Requires -Version 5.1

[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$inventoryScript = Join-Path $PSScriptRoot 'inventory_windows_openfoam_t0.ps1'
if (-not (Test-Path -LiteralPath $inventoryScript -PathType Leaf)) {
    throw 'INVENTORY_SCRIPT_MISSING'
}

$json = & powershell -NoProfile -ExecutionPolicy Bypass -File $inventoryScript
if ($LASTEXITCODE -ne 0) {
    throw "INVENTORY_PROCESS_FAILED exit=$LASTEXITCODE"
}

try {
    $result = $json | ConvertFrom-Json
}
catch {
    throw "INVENTORY_JSON_INVALID $($_.Exception.Message)"
}

foreach ($requiredProperty in @(
    'observed_at_utc', 'truth', 'probe_errors', 'exit_semantics', 'inventory'
)) {
    if ($null -eq $result.PSObject.Properties[$requiredProperty]) {
        throw "TOP_LEVEL_PROPERTY_MISSING property=$requiredProperty"
    }
}

$allowedInventoryStates = @('COMPLETE', 'PARTIAL')
$allowedToolingStates = @(
    'DETECTED_NATIVE_WINDOWS',
    'UNKNOWN_WSL_NOT_LAUNCHED',
    'NOT_INSTALLED'
)

if ($result.truth.WINDOWS_T0_INVENTORY -notin $allowedInventoryStates) {
    throw 'INVENTORY_TRUTH_INVALID'
}
if ($result.truth.OPENFOAM_TOOLING -notin $allowedToolingStates) {
    throw 'TOOLING_TRUTH_INVALID'
}
if ($result.truth.OPENFOAM_TOOLING_PROBE_SCOPE -ne 'WINDOWS_PATH_AND_WSL_REGISTRY_ONLY') {
    throw 'TOOLING_SCOPE_INVALID'
}
if ($result.truth.OPENFOAM_TOOLING_SMOKE -ne 'NOT_RUN') {
    throw 'SMOKE_TRUTH_INVALID'
}
if ($result.truth.P3_P6_GATE_EFFECT -ne 'NONE') {
    throw 'GATE_EFFECT_INVALID'
}
if ([string]::IsNullOrWhiteSpace($result.observed_at_utc)) {
    throw 'OBSERVED_AT_MISSING'
}
if ($null -eq $result.probe_errors) {
    throw 'PROBE_ERRORS_MISSING'
}
$probeErrorCount = @($result.probe_errors).Count
if ($result.truth.WINDOWS_T0_INVENTORY -eq 'COMPLETE' -and $probeErrorCount -ne 0) {
    throw 'COMPLETE_WITH_PROBE_ERRORS'
}
if ($result.truth.WINDOWS_T0_INVENTORY -eq 'PARTIAL' -and $probeErrorCount -eq 0) {
    throw 'PARTIAL_WITHOUT_PROBE_ERRORS'
}
if ($null -eq $result.inventory.wsl_registry.distributions) {
    throw 'WSL_DISTRIBUTIONS_MISSING'
}
$openFoamCommandNames = @('foamVersion', 'blockMesh', 'checkMesh', 'foamRun')
$nativeOpenFoamMissing = @($openFoamCommandNames | Where-Object {
    $commandName = $_
    -not $result.inventory.commands.$commandName.found
}).Count -gt 0
$wslDistributionCount = @($result.inventory.wsl_registry.distributions).Count
if ($nativeOpenFoamMissing -and $wslDistributionCount -eq 0 -and
    $result.truth.OPENFOAM_TOOLING -ne 'NOT_INSTALLED') {
    throw 'EMPTY_WSL_FALSE_TOOLING_STATE'
}

Write-Output 'WINDOWS_OPENFOAM_T0_INVENTORY_TEST=PASS'

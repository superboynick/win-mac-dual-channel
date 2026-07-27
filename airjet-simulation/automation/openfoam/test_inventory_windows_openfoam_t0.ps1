#Requires -Version 5.1

[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$inventoryScript = Join-Path $PSScriptRoot 'inventory_windows_openfoam_t0.ps1'
if (-not (Test-Path -LiteralPath $inventoryScript -PathType Leaf)) {
    throw 'INVENTORY_SCRIPT_MISSING'
}

$source = Get-Content -Raw -LiteralPath $inventoryScript
foreach ($forbiddenPattern in @(
    '(?i)\bwsl(?:\.exe)?\s+--install\b',
    '(?i)\bEnable-WindowsOptionalFeature\b',
    '(?i)\bStart-Process\b',
    '(?i)\bInstall-Package\b',
    '(?i)\bwinget\s+install\b',
    '(?i)\bfoamRun\s+(?![''"])',
    '(?i)\bblockMesh\s+(?![''"])',
    '(?i)\bcheckMesh\s+(?![''"])',
    '(?i)\$env:ComSpec'
)) {
    if ($source -match $forbiddenPattern) {
        throw "FORBIDDEN_MUTATING_OR_EXECUTION_PATTERN pattern=$forbiddenPattern"
    }
}

$json = & powershell -NoProfile -ExecutionPolicy Bypass -File $inventoryScript
if ($LASTEXITCODE -ne 0) {
    throw "INVENTORY_PROCESS_FAILED exit=$LASTEXITCODE"
}

$serialized = [string]::Join([Environment]::NewLine, @($json))
if ([Text.Encoding]::UTF8.GetByteCount($serialized) -gt 1048576) {
    throw 'INVENTORY_JSON_EXCEEDS_1_MIB'
}

try {
    $result = $serialized | ConvertFrom-Json
}
catch {
    throw 'INVENTORY_JSON_INVALID'
}

$requiredTopLevel = @(
    'schema_version',
    'observed_at_utc',
    'declared_probe_scope',
    'truth',
    'probe_errors',
    'exit_semantics',
    'inventory'
)
foreach ($requiredProperty in $requiredTopLevel) {
    if ($null -eq $result.PSObject.Properties[$requiredProperty]) {
        throw "TOP_LEVEL_PROPERTY_MISSING property=$requiredProperty"
    }
}

if ([int]$result.schema_version -ne 1) {
    throw 'SCHEMA_VERSION_INVALID'
}

$observedAt = [DateTimeOffset]::MinValue
if (-not [DateTimeOffset]::TryParse(
    [string]$result.observed_at_utc,
    [Globalization.CultureInfo]::InvariantCulture,
    [Globalization.DateTimeStyles]::RoundtripKind,
    [ref]$observedAt
)) {
    throw 'OBSERVED_AT_INVALID'
}
if ($observedAt.Offset -ne [TimeSpan]::Zero) {
    throw 'OBSERVED_AT_NOT_UTC'
}

$requiredScopes = @(
    'WINDOWS_PATH_COMMAND_DISCOVERY',
    'CURRENT_USER_WSL_REGISTRY',
    'READ_ONLY_WSL_STATUS_EXIT_CODES',
    'WINDOWS_UNINSTALL_REGISTRY',
    'STANDARD_INSTALL_PATH_EXISTENCE',
    'HOST_CAPACITY_TELEMETRY'
)
if (@($result.declared_probe_scope).Count -ne $requiredScopes.Count) {
    throw 'DECLARED_SCOPE_COUNT_INVALID'
}
foreach ($scope in $requiredScopes) {
    if ($scope -notin @($result.declared_probe_scope)) {
        throw "DECLARED_SCOPE_MISSING scope=$scope"
    }
}

$allowedInventoryStates = @('COMPLETE', 'PARTIAL')
$allowedToolingEvidence = @(
    'WINDOWS_PATH_COMMANDS_PRESENT_UNVERIFIED',
    'WSL_DISTRIBUTION_PRESENT_UNVERIFIED',
    'RUNTIME_CANDIDATE_PRESENT_UNVERIFIED',
    'NO_RUNTIME_DETECTED_IN_DECLARED_SCOPE'
)
if ($result.truth.windows_t0_inventory -notin $allowedInventoryStates) {
    throw 'INVENTORY_TRUTH_INVALID'
}
if ($result.truth.openfoam_tooling_evidence -notin $allowedToolingEvidence) {
    throw 'TOOLING_EVIDENCE_INVALID'
}
if ($result.truth.openfoam_tooling_ready_for_smoke -ne $false) {
    throw 'TOOLING_READY_MUST_REMAIN_FALSE'
}
if ($result.truth.openfoam_tooling_smoke -ne 'NOT_RUN') {
    throw 'SMOKE_TRUTH_INVALID'
}
if ($result.truth.airjet_solver_authorized -ne $false) {
    throw 'SOLVER_AUTHORIZATION_MUST_REMAIN_FALSE'
}
if ($result.truth.stage_gate_advanced -ne $false) {
    throw 'STAGE_GATE_ADVANCEMENT_MUST_REMAIN_FALSE'
}
if ($result.truth.p1_stage_gate -ne 'NOT_PASSED') {
    throw 'P1_GATE_TRUTH_INVALID'
}
if ($result.truth.p2_stage_gate -ne 'NOT_RUN') {
    throw 'P2_GATE_TRUTH_INVALID'
}
if ($result.truth.p3_p6_gate_effect -ne 'NONE') {
    throw 'P3_P6_GATE_EFFECT_INVALID'
}

$probeErrorCount = @($result.probe_errors).Count
if ($result.truth.windows_t0_inventory -eq 'COMPLETE' -and $probeErrorCount -ne 0) {
    throw 'COMPLETE_WITH_PROBE_ERRORS'
}
if ($result.truth.windows_t0_inventory -eq 'PARTIAL' -and $probeErrorCount -eq 0) {
    throw 'PARTIAL_WITHOUT_PROBE_ERRORS'
}

$requiredCommandNames = @(
    'wsl.exe',
    'docker',
    'podman',
    'foamVersion',
    'blockMesh',
    'checkMesh',
    'foamRun'
)
foreach ($commandName in $requiredCommandNames) {
    $property = $result.inventory.commands.PSObject.Properties[$commandName]
    if ($null -eq $property) {
        throw "COMMAND_RESULT_MISSING command=$commandName"
    }
    if ($property.Value.identity_verified -ne $false) {
        throw "COMMAND_IDENTITY_MUST_REMAIN_UNVERIFIED command=$commandName"
    }
}

if ($null -eq $result.inventory.wsl_registry.distributions) {
    throw 'WSL_DISTRIBUTIONS_MISSING'
}
foreach ($distribution in @($result.inventory.wsl_registry.distributions)) {
    if ($distribution.identity_verified -ne $false) {
        throw 'WSL_DISTRIBUTION_IDENTITY_MUST_REMAIN_UNVERIFIED'
    }
}
foreach ($app in @($result.inventory.installed_app_matches)) {
    if ($app.identity_verified -ne $false) {
        throw 'INSTALLED_APP_IDENTITY_MUST_REMAIN_UNVERIFIED'
    }
}

$openFoamCommandNames = @('foamVersion', 'blockMesh', 'checkMesh', 'foamRun')
$allOpenFoamCommandsFound = @($openFoamCommandNames | Where-Object {
    $commandName = $_
    -not $result.inventory.commands.$commandName.found
}).Count -eq 0
$wslDistributionCount = @($result.inventory.wsl_registry.distributions).Count
$runtimeCandidateFound = (@($result.inventory.installed_app_matches).Count -gt 0) -or
    (@($result.inventory.standard_paths.PSObject.Properties |
        Where-Object { $_.Value -eq $true }).Count -gt 0)

$expectedToolingEvidence = if ($allOpenFoamCommandsFound) {
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
if ($result.truth.openfoam_tooling_evidence -ne $expectedToolingEvidence) {
    throw "TOOLING_EVIDENCE_CLASSIFICATION_INVALID expected=$expectedToolingEvidence"
}

if ($result.inventory.host.PSObject.Properties['name']) {
    throw 'HOST_NAME_MUST_NOT_BE_EMITTED'
}
if ($serialized -match [regex]::Escape([string]$env:USERPROFILE)) {
    throw 'USERPROFILE_PATH_NOT_REDACTED'
}

Write-Output 'WINDOWS_OPENFOAM_T0_INVENTORY_TEST=PASS'

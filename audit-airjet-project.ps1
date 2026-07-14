[CmdletBinding()]
param([string]$RepoRoot)

$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($RepoRoot)) { $RepoRoot = $PSScriptRoot }
$RepoRoot = (Resolve-Path -LiteralPath $RepoRoot).Path
$Failures = New-Object System.Collections.Generic.List[string]

function Add-Failure {
    param([string]$Message)
    $Failures.Add($Message)
}

function Read-Utf8 {
    param([string]$Path)
    return [System.IO.File]::ReadAllText($Path, [System.Text.Encoding]::UTF8)
}

function ConvertFrom-Utf8Base64 {
    param([string]$Value)
    return [System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($Value))
}

function Convert-InvariantDouble {
    param([object]$Value)
    return [double]::Parse(
        [string]$Value,
        [System.Globalization.NumberStyles]::Float,
        [System.Globalization.CultureInfo]::InvariantCulture
    )
}

function Test-Close {
    param([object]$Actual, [double]$Expected, [double]$Tolerance = 1e-9)
    try {
        return [math]::Abs((Convert-InvariantDouble $Actual) - $Expected) -le $Tolerance
    } catch {
        return $false
    }
}

function Get-CanonicalTextSha256 {
    param([string]$Path)
    $Text = Read-Utf8 $Path
    $Canonical = $Text.Replace("`r`n", "`n").Replace("`r", "`n")
    $Bytes = [System.Text.Encoding]::UTF8.GetBytes($Canonical)
    $Sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        return ([System.BitConverter]::ToString($Sha.ComputeHash($Bytes))).Replace('-', '').ToLowerInvariant()
    } finally {
        $Sha.Dispose()
    }
}

$Required = @(
    'AGENTS.md',
    'airjet-simulation\README.md',
    'airjet-simulation\AIRJET_MINI_FULL_PRODUCT_MASTER_PLAN.md',
    'airjet-simulation\PROJECT_STATUS.md',
    'airjet-simulation\DECISION_AND_REASONING_ARCHIVE.md',
    'airjet-simulation\MODEL_ANNOTATIONS.md',
    'airjet-simulation\WINDOWS_HANDOFF.md',
    'airjet-simulation\WINDOWS_ENVIRONMENT_REPORT.md',
    'airjet-simulation\PEER_COLLABORATION_PROTOCOL.md',
    'airjet-simulation\collaboration\README.md',
    'airjet-simulation\SKILLS_AND_GIT_WORKFLOW.md',
    'airjet-simulation\evidence\SOURCE_PROVENANCE.md',
    'airjet-simulation\evidence\product_selection_matrix.csv',
    'airjet-simulation\evidence\airjet_mini_performance_curve_digitized.csv',
    'airjet-simulation\evidence\airjet_mini_curve_pixels.csv',
    'airjet-simulation\evidence\CURVE_DIGITIZATION_METHOD.md',
    'airjet-simulation\evidence\digitize_airjet_mini_curve.py',
    'airjet-simulation\evidence\P0_EVIDENCE_FREEZE_RECORD.md',
    'airjet-simulation\evidence\OFFICIAL_IMAGE_COORDINATE_METHOD.md',
    'airjet-simulation\evidence\patent_product_component_map.csv',
    'airjet-simulation\evidence\layout_candidate_scores.csv',
    'airjet-simulation\windows-prompts\AJM_WIN_P1_READINESS_001.md',
    'airjet-simulation\windows-prompts\AJM_WIN_ANSYS_OFFICIAL_TRIAL_INSTALL_AND_SMOKE_004.md',
    'airjet-simulation\windows-prompts\AJM_WIN_ANSYS_STUDENT_CAPABILITY_SMOKE_005.md',
    'airjet-simulation\windows-prompts\AJM_WIN_P1_FULL_PRODUCT_CAD_BUILD_006.md',
    'airjet-simulation\reports\AJM_WIN_ANSYS_CAPABILITY_SMOKE_003_SUMMARY.md',
    'airjet-simulation\reports\AJM_WIN_ANSYS_STUDENT_CLEANUP_2026-07-14.md',
    'airjet-simulation\reports\AIRJET_DUAL_ENDPOINT_WATCHER_IMPLEMENTATION_2026-07-14.md',
    'airjet-simulation\evidence\build_layout_candidate_scores.py',
    'airjet-simulation\evidence\extract_official_image_geometry.py',
    'airjet-simulation\evidence\analyze_official_vent_views.py',
    'airjet-simulation\evidence\official_image_measurements.csv',
    'airjet-simulation\evidence\annotated_figures\gen1_vent_homography_results.csv',
    'airjet-simulation\evidence\annotated_figures\gen1_vent_cross_view_comparison.csv',
    'airjet-simulation\evidence\annotated_figures\gen1_top_render_quad_annotated.png',
    'airjet-simulation\evidence\annotated_figures\gen1_cross_section_annotated.png',
    'airjet-simulation\parameters\full_product_parameter_registry.csv',
    'airjet-simulation\parameters\build_p1_cad_inputs.py',
    'airjet-simulation\parameters\p1_layout_configuration_matrix.csv',
    'airjet-simulation\parameters\p1_thickness_budget.csv',
    'airjet-simulation\parameters\build_p1_cad_contracts.py',
    'airjet-simulation\parameters\P1_CAD_CONTRACT_METHOD.md',
    'airjet-simulation\parameters\p1_model_form_variants.csv',
    'airjet-simulation\parameters\p1_cad_parameter_map.csv',
    'airjet-simulation\parameters\p1_orifice_pattern_candidates.csv',
    'airjet-simulation\parameters\p1_vent_geometry_candidates.csv',
    'airjet-simulation\parameters\p1_planform_exhaust_candidates.csv',
    'airjet-simulation\parameters\p1_internal_geometry_rules.csv',
    'airjet-simulation\geometry\contracts\README.md',
    'airjet-simulation\geometry\contracts\p1_cad_features.csv',
    'airjet-simulation\geometry\contracts\p1_cad_feature_parameter_bindings.csv',
    'airjet-simulation\geometry\contracts\p1_cad_interfaces.csv',
    'airjet-simulation\geometry\contracts\p1_cad_named_selections.csv',
    'airjet-simulation\geometry\contracts\p1_cad_open_questions.csv',
    'airjet-simulation\checklists\full_product_stage_gates.md',
    'airjet-simulation\checklists\p1_cad_gate_matrix.csv',
    'airjet-simulation\checklists\P1_CAD_INDEPENDENT_REVIEW_METHOD.md',
    'airjet-simulation\checklists\prepare_p1_cad_review.py',
    'airjet-simulation\logs\p1_cad_run_template.md',
    'airjet-simulation\logs\external-files.csv',
    'airjet-simulation\notebooks\airjet-mini-layout-baseline.ipynb',
    'airjet-simulation\notebooks\build_layout_baseline.py',
    'codex-skills\airjet-product-reconstruction\SKILL.md',
    'codex-skills\skills-manifest.json',
    'install-skills.ps1',
    'install-skills.sh',
    'launch-airjet-codex-visible.ps1',
    'tools\airjet-git-watcher\README.md',
    'tools\airjet-git-watcher\wake-policy.md',
    'tools\airjet-git-watcher\mac\manage-airjet-watcher.sh',
    'tools\airjet-git-watcher\mac\install-mac-watcher.sh',
    'tools\airjet-git-watcher\mac\run-awakened-codex.sh',
    'tools\airjet-git-watcher\mac\watch-airjet-git.sh',
    'tools\airjet-git-watcher\tests\test-watch-airjet-git.sh',
    'tools\airjet-git-watcher\windows\AirJetWatcher.Common.ps1',
    'tools\airjet-git-watcher\windows\Watch-AirJetGit.ps1',
    'tools\airjet-git-watcher\windows\Manage-AirJetWatcher.ps1',
    'tools\airjet-git-watcher\windows\Run-AwakenedCodex.ps1',
    'tools\airjet-git-watcher\windows\Install-AirJetWatcher.ps1',
    'tools\airjet-git-watcher\tests\test-watch-airjet-git-windows.ps1'
)

foreach ($Relative in $Required) {
    if (-not (Test-Path -LiteralPath (Join-Path $RepoRoot $Relative) -PathType Leaf)) {
        Add-Failure "missing required file: $Relative"
    }
}

$MacWatcherPath = Join-Path $RepoRoot 'tools\airjet-git-watcher\mac\watch-airjet-git.sh'
$MacWatcherManagerPath = Join-Path $RepoRoot 'tools\airjet-git-watcher\mac\manage-airjet-watcher.sh'
$MacWatcherRunnerPath = Join-Path $RepoRoot 'tools\airjet-git-watcher\mac\run-awakened-codex.sh'
$MacWatcherTestPath = Join-Path $RepoRoot 'tools\airjet-git-watcher\tests\test-watch-airjet-git.sh'
if (Test-Path -LiteralPath $MacWatcherPath -PathType Leaf) {
    $MacWatcherText = Read-Utf8 $MacWatcherPath
    foreach ($Marker in @(
        'TASK_ENVELOPE_REL=airjet-simulation/collaboration/MAC_TASK.env',
        'BLOCKED_STATE_ROOT_INSIDE_REPOSITORY',
        'BLOCKED_CRITICAL_WATCHER_UPDATE',
        'BLOCKED_INVALID_MAC_TASK_ENVELOPE',
        'BLOCKED_EVENT_ROOT_NOT_DIRECT_STATE_CHILD',
        'BLOCKED_LOG_ROOT_NOT_DIRECT_STATE_CHILD',
        'BLOCKED_PENDING_REMOTE_MOVED',
        'BLOCKED_UNTRUSTED_COMMIT',
        'task_tip_not_signed_by_windows_peer',
        'automatic_relay_not_enabled',
        'RUNTIME_STATUS=ENABLED_AFTER_REVIEW',
        'unsafe_instruction_object_type',
        'SYNCED_NO_MAC_TASK'
    )) {
        if (-not $MacWatcherText.Contains($Marker)) { Add-Failure "Mac watcher lacks safety marker: $Marker" }
    }
}
if (Test-Path -LiteralPath $MacWatcherManagerPath -PathType Leaf) {
    $MacWatcherManagerText = Read-Utf8 $MacWatcherManagerPath
    if (-not $MacWatcherManagerText.Contains('RUNTIME_STATUS=ENABLED_AFTER_REVIEW')) {
        Add-Failure 'Mac watcher manager is not enabled for reviewed manual runtime'
    }
}
if (Test-Path -LiteralPath $MacWatcherRunnerPath -PathType Leaf) {
    $MacWatcherRunnerText = Read-Utf8 $MacWatcherRunnerPath
    foreach ($Marker in @(
        'BLOCKED_REPORT_ROOT_SYMLINK',
        'BLOCKED_REPORT_ROOT_INSIDE_REPOSITORY',
        'BLOCKED_PROMPT_HANDLE_MISSING_OR_SYMLINKED',
        'RUNNER_RESULT=REFUSED_',
        'BLOCKED_TEST_MODE_CODEX_START',
        'approval_policy="never"'
    )) {
        if (-not $MacWatcherRunnerText.Contains($Marker)) { Add-Failure "Mac watcher runner lacks safety marker: $Marker" }
    }
}
if (Test-Path -LiteralPath $MacWatcherTestPath -PathType Leaf) {
    $MacWatcherTestText = Read-Utf8 $MacWatcherTestPath
    foreach ($Marker in @(
        'critical_update_no_pending',
        'ordinary_update_no_pending',
        'dirty_pending_retry_block',
        'symlink_instruction_block',
        'state_root_boundary_output',
        'state_child_symlink_block',
        'report_root_symlink_block',
        'manager_start_test_mode_guard',
        'unsigned_commit_block',
        'self_signed_task_block',
        'revoked_signer_block',
        'automatic_relay_block',
        'EXPECTED_PASS_COUNT=80',
        'RUNTIME_TEST_MODE_GUARD=BEHAVIOR_TESTED',
        'OVERALL=PASS_CORE_RUNTIME_ENABLED_MANUAL',
        'VISIBLE_WAKE_TEST=SKIPPED_BY_DESIGN'
    )) {
        if (-not $MacWatcherTestText.Contains($Marker)) { Add-Failure "Mac watcher test lacks case marker: $Marker" }
    }
}

$WindowsWatcherFiles = @{
    'AirJetWatcher.Common.ps1' = @('ENABLED_AFTER_END_TO_END','WINDOWS_TASK.env','MAC_TASK.env','gpg.minTrustLevel=fully','--no-replace-objects','BLOCKED_RELAY_NOT_ENABLED','[IO.FileMode]::CreateNew')
    'Watch-AirJetGit.ps1' = @('BLOCKED_RUNTIME_','BLOCKED_TEST_MODE_WAKE_FORBIDDEN','BLOCKED_CRITICAL_WATCHER_UPDATE','SHELL_REQUESTED_NOT_USER_OBSERVED')
    'Manage-AirJetWatcher.ps1' = @('ENABLED_AFTER_END_TO_END','REFUSED_TEST_MODE',"'start'", "'retry'")
    'Run-AwakenedCodex.ps1' = @('BLOCKED_TEST_MODE_CODEX_FORBIDDEN','ENABLED_AFTER_END_TO_END','approval_policy="never"')
    'Install-AirJetWatcher.ps1' = @('InteractiveToken','RegisterAtLogOn','BLOCKED_REGISTER_RUNTIME_NOT_ENABLED')
}
foreach ($Name in $WindowsWatcherFiles.Keys) {
    $Path = Join-Path $RepoRoot (Join-Path 'tools\airjet-git-watcher\windows' $Name)
    if (Test-Path -LiteralPath $Path -PathType Leaf) {
        $Text = Read-Utf8 $Path
        foreach ($Marker in $WindowsWatcherFiles[$Name]) {
            if (-not $Text.Contains($Marker)) { Add-Failure "Windows watcher file lacks safety marker: ${Name}: $Marker" }
        }
    }
}
$WindowsWatcherTestPath = Join-Path $RepoRoot 'tools\airjet-git-watcher\tests\test-watch-airjet-git-windows.ps1'
if (Test-Path -LiteralPath $WindowsWatcherTestPath -PathType Leaf) {
    $Text = Read-Utf8 $WindowsWatcherTestPath
    foreach ($Marker in @('EXPECTED_PASS_COUNT=$ExpectedPassCount','RUNTIME_TEST_MODE_GUARD=BEHAVIOR_TESTED','OVERALL=PASS_CORE_RUNTIME_ENABLED_MANUAL')) {
        if (-not $Text.Contains($Marker)) { Add-Failure "Windows watcher test lacks marker: $Marker" }
    }
}

$ManualNames = @(
    '01_FULL_PRODUCT_CAD.md',
    '02_ACTUATOR_STRUCTURAL.md',
    '03_CELL_TRANSIENT_CFD.md',
    '04_FULL_PRODUCT_AIRFLOW.md',
    '05_FULL_PRODUCT_CHT.md',
    '06_CALIBRATION_AND_UNCERTAINTY.md',
    '07_RUN_LOG_AND_GIT.md'
)
$ManualRoot = Join-Path $RepoRoot 'airjet-simulation\manuals'
foreach ($Name in $ManualNames) {
    if (-not (Test-Path -LiteralPath (Join-Path $ManualRoot $Name) -PathType Leaf)) {
        Add-Failure "missing manual: $Name"
    }
}

$Archived = @(
    'airjet-simulation\AIRJET_SIMULATION_PROJECT.md',
    'airjet-simulation\PROJECT_ASSESSMENT_AND_PLAN.md',
    'airjet-simulation\checklists\stage-gates.md'
)
foreach ($Relative in $Archived) {
    $Path = Join-Path $RepoRoot $Relative
    if (Test-Path -LiteralPath $Path -PathType Leaf) {
        $Text = Read-Utf8 $Path
        if (($Text -notmatch [regex]::Escape([Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('5bey5b2S5qGj')))) -and
            ($Text -notmatch [regex]::Escape([Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('5YGc55So'))))) {
            Add-Failure "legacy route lacks archive banner: $Relative"
        }
    }
}

$CsvFiles = @(Get-ChildItem -LiteralPath (Join-Path $RepoRoot 'airjet-simulation') -Filter '*.csv' -File -Recurse)
Add-Type -AssemblyName Microsoft.VisualBasic
foreach ($CsvFile in $CsvFiles) {
    $Parser = $null
    try {
        $Parser = [Microsoft.VisualBasic.FileIO.TextFieldParser]::new(
            $CsvFile.FullName,
            [System.Text.Encoding]::UTF8,
            $true
        )
        $Parser.TextFieldType = [Microsoft.VisualBasic.FileIO.FieldType]::Delimited
        $Parser.SetDelimiters(',')
        $Parser.HasFieldsEnclosedInQuotes = $true
        $ExpectedWidth = $null
        $RowNumber = 0
        while (-not $Parser.EndOfData) {
            $Fields = $Parser.ReadFields()
            $RowNumber += 1
            if ($null -eq $ExpectedWidth) {
                $ExpectedWidth = $Fields.Count
                if ($ExpectedWidth -eq 0) { Add-Failure "empty CSV: $($CsvFile.FullName)" }
            } elseif ($Fields.Count -ne $ExpectedWidth) {
                Add-Failure "CSV width mismatch: $($CsvFile.FullName):$RowNumber expected $ExpectedWidth got $($Fields.Count)"
            }
        }
        if ($RowNumber -eq 0) { Add-Failure "empty CSV: $($CsvFile.FullName)" }
    } catch {
        Add-Failure "CSV parse failed: $($CsvFile.FullName): $($_.Exception.Message)"
    } finally {
        if ($null -ne $Parser) { $Parser.Close() }
    }
}

$ArchivedFullPaths = @{}
foreach ($Relative in $Archived) {
    $ArchivedFullPaths[(Join-Path $RepoRoot $Relative).ToLowerInvariant()] = $true
}
$ObsoleteChinese = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('5Yqf6ICX4oCU5rWB6YeP5puy57q/'))
$ObsoletePressureClaim = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('5ZyoIDE3NTAgUGEg55uu5qCH6IOM5Y6L5LiL57u05oyB5YeA5rWB'))
$DrawnVentMarker = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('5Zub5LiqIGVsb25nYXRlZCB0b3AgdmVudCBvYmplY3Rz'))
$ActiveFiles = Get-ChildItem -LiteralPath (Join-Path $RepoRoot 'airjet-simulation') -File -Recurse |
    Where-Object { $_.Extension -in @('.md', '.csv') -and -not $ArchivedFullPaths.ContainsKey($_.FullName.ToLowerInvariant()) }
foreach ($File in $ActiveFiles) {
    $Text = Read-Utf8 $File.FullName
    if ($Text.Contains('delivered_airflow_chart_units') -or $Text.Contains($ObsoleteChinese) -or
        $Text.Contains('30-60,m/s') -or $Text.Contains($ObsoletePressureClaim)) {
        Add-Failure "obsolete evidence interpretation in $($File.FullName)"
    }
}
$PeerLanguageFiles = Get-ChildItem -LiteralPath (Join-Path $RepoRoot 'airjet-simulation') -File -Recurse |
    Where-Object { $_.Extension -in @('.md', '.csv', '.py') -and -not $ArchivedFullPaths.ContainsKey($_.FullName.ToLowerInvariant()) }
foreach ($File in $PeerLanguageFiles) {
    $Text = Read-Utf8 $File.FullName
    if ($Text.Contains('pending Mac review') -or $Text.Contains('Mac evidence and artifact review') -or
        $Text.Contains('independent Mac review')) {
        Add-Failure "obsolete machine hierarchy phrase in $($File.FullName)"
    }
}

$PerfPath = Join-Path $RepoRoot 'airjet-simulation\evidence\airjet_mini_performance_curve_digitized.csv'
if (Test-Path -LiteralPath $PerfPath) {
    $PerfRows = @(Import-Csv -LiteralPath $PerfPath -Encoding UTF8)
    if ($PerfRows.Count -ne 4) { Add-Failure "performance curve must contain four rows, got $($PerfRows.Count)" }
    if ($PerfRows.Count -gt 0 -and -not ($PerfRows[0].PSObject.Properties.Name -contains 'system_noise_at_50cm_dBA')) {
        Add-Failure 'performance curve right axis is not identified as 50 cm system noise'
    }
    $Endpoint = @($PerfRows | Where-Object { $_.power_W -eq '1.00' })
    if ($Endpoint.Count -ne 1 -or
        -not (Test-Close $Endpoint[0].net_heat_dissipation_W 4.25) -or
        -not (Test-Close $Endpoint[0].system_noise_at_50cm_dBA 21.0) -or
        $Endpoint[0].status -notlike '*direct_endpoint*') {
        Add-Failure '1 W endpoint must preserve 4.25 W net heat, 21 dBA, and direct endpoint status'
    }
}

$RegistryPath = Join-Path $RepoRoot 'airjet-simulation\parameters\full_product_parameter_registry.csv'
if (Test-Path -LiteralPath $RegistryPath) {
    $RegistryRows = @(Import-Csv -LiteralPath $RegistryPath -Encoding UTF8)
    $RequiredRegistryColumns = @('evidence_class', 'uncertainty_or_range', 'derivation_or_parent', 'adjustable')
    foreach ($Column in $RequiredRegistryColumns) {
        if ($RegistryRows.Count -eq 0 -or -not ($RegistryRows[0].PSObject.Properties.Name -contains $Column)) {
            Add-Failure "parameter registry lacks column: $Column"
        }
    }
    $ById = @{}
    foreach ($Row in $RegistryRows) {
        if ([string]::IsNullOrWhiteSpace($Row.id) -or $ById.ContainsKey($Row.id)) {
            Add-Failure 'parameter registry contains a blank or duplicate id'
        } else {
            $ById[$Row.id] = $Row
        }
        if ($Row.evidence_class -notin @('D', 'P', 'I', 'C', 'U')) {
            Add-Failure "invalid evidence class for $($Row.id): $($Row.evidence_class)"
        }
        if ($Row.adjustable -notin @('true', 'false')) {
            Add-Failure "invalid adjustable flag for $($Row.id): $($Row.adjustable)"
        }
    }
    $DirectExpected = @{
        D001 = 27.5; D002 = 41.5; D003 = 2.8; D004 = 1.0; D005 = 5.25;
        D006 = 4.25; D011 = 1750.0; D012 = 21.0; D013 = 11.0
    }
    foreach ($Id in $DirectExpected.Keys) {
        if (-not $ById.ContainsKey($Id)) {
            Add-Failure "parameter registry missing $Id"
        } elseif (-not (Test-Close $ById[$Id].initial_value $DirectExpected[$Id]) -or
            $ById[$Id].status -ne 'direct_product' -or
            $ById[$Id].evidence_class -ne 'D' -or
            $ById[$Id].adjustable -ne 'false') {
            Add-Failure "locked product target changed: $Id"
        }
    }
    if ($ById.ContainsKey('D004') -and $ById.ContainsKey('D005') -and $ById.ContainsKey('D006')) {
        $HeatError = (Convert-InvariantDouble $ById['D006'].initial_value) +
            (Convert-InvariantDouble $ById['D004'].initial_value) -
            (Convert-InvariantDouble $ById['D005'].initial_value)
        if ([math]::Abs($HeatError) -gt 1e-9) {
            Add-Failure 'heat accounting failed: Q_net + P_airjet != Q_total'
        }
    }
    foreach ($Id in @('D007', 'D008', 'D009')) {
        if (-not $ById.ContainsKey($Id) -or $ById[$Id].evidence_class -ne 'I') {
            Add-Failure "$Id must remain an image-digitized I-class target"
        }
    }
    foreach ($Row in $RegistryRows | Where-Object { $_.id -like 'P*' }) {
        if ($Row.evidence_class -ne 'P') { Add-Failure "patent row is not P-class: $($Row.id)" }
        if ($Row.evidence_source -notlike '*printed col.*') { Add-Failure "patent row lacks local printed-column locator: $($Row.id)" }
    }
    if (-not $ById.ContainsKey('P011') -or $ById['P011'].status -ne 'patent_lower_bound' -or
        $ById['P011'].uncertainty_or_range -notlike '*no 60 m/s upper bound*') {
        Add-Failure 'P011 must preserve a >=30 m/s lower bound and no 60 m/s upper bound'
    }
    if ($ById.ContainsKey('D011') -and $ById['D011'].calibration_target -notlike '*not a known flow operating point*') {
        Add-Failure '1750 Pa must be recorded as pressure capability with unknown corresponding flow'
    }
    if (-not $ById.ContainsKey('C004') -or $ById['C004'].initial_value -ne 'candidate_v1_dual_view_homography') {
        Add-Failure 'C004 must preserve the dual-view P0 intake candidate'
    }
    if (-not $ById.ContainsKey('C014') -or $ById['C014'].initial_value -ne '4_drawn_vent_objects_not_confirmed_groups') {
        Add-Failure 'C014 must distinguish drawn vents from confirmed intake groups'
    }
    $ExpectedP1Parameters = @{
        C015 = @('C', 'true')
        C016 = @('C', 'true')
        C017 = @('C', 'true')
        C018 = @('C', 'false')
        C019 = @('U', 'false')
        C020 = @('C', 'true')
    }
    foreach ($Id in $ExpectedP1Parameters.Keys) {
        if (-not $ById.ContainsKey($Id)) {
            Add-Failure "parameter registry missing P1 input $Id"
            continue
        }
        $Expected = $ExpectedP1Parameters[$Id]
        if ($ById[$Id].evidence_class -ne $Expected[0] -or $ById[$Id].adjustable -ne $Expected[1]) {
            Add-Failure "P1 parameter evidence/adjustability changed: $Id"
        }
    }
    try {
        $BottomExpected = (Convert-InvariantDouble $ById['P004'].initial_value) / 1000.0 +
            (Convert-InvariantDouble $ById['P006'].initial_value)
        if (-not (Test-Close $ById['C018'].initial_value $BottomExpected)) {
            Add-Failure 'C018 must equal P004/1000 + P006'
        }
        $AllocatedIds = @('C015', 'P005', 'P002', 'C018', 'C016', 'P010', 'C009', 'C017')
        $Allocated = 0.0
        foreach ($Id in $AllocatedIds) { $Allocated += Convert-InvariantDouble $ById[$Id].initial_value }
        $ResidualExpected = (Convert-InvariantDouble $ById['D003'].initial_value) - $Allocated
        if (-not (Test-Close $ById['C019'].initial_value $ResidualExpected)) {
            Add-Failure 'C019 must equal D003 minus the allocated TB0 stack'
        }
        $Split = Convert-InvariantDouble $ById['C020'].initial_value
        if ($Split -lt 0.0 -or $Split -gt 1.0) {
            Add-Failure 'C020 residual top fraction must remain within [0, 1]'
        }
    } catch {
        Add-Failure 'P1 thickness derivations could not be evaluated'
    }
    if (-not $ById.ContainsKey('C009') -or
        $ById['C009'].uncertainty_or_range -notlike '*no mass constraint claimed*') {
        Add-Failure 'C009 exploratory spreader range must not claim an uncomputed 11 g constraint'
    }
}

$LedgerPath = Join-Path $RepoRoot 'airjet-simulation\evidence\airjet_reconstruction_ledger.csv'
if (Test-Path -LiteralPath $LedgerPath) {
    $LedgerRows = @(Import-Csv -LiteralPath $LedgerPath -Encoding UTF8)
    foreach ($Row in $LedgerRows) {
        if ($Row.evidence_class -notin @('D', 'P', 'I', 'C', 'U')) {
            Add-Failure "legacy ledger has invalid evidence class: $($Row.id)"
        }
        if ($Row.evidence_class -eq 'P' -and $Row.model_status -like '*locked*') {
            Add-Failure "patent ledger row is incorrectly locked: $($Row.id)"
        }
        if ($Row.evidence_class -eq 'P' -and $Row.source -like '*paragraph *') {
            Add-Failure "patent ledger row uses a webpage line as a patent paragraph: $($Row.id)"
        }
    }
}

$SelectionPath = Join-Path $RepoRoot 'airjet-simulation\evidence\product_selection_matrix.csv'
if (Test-Path -LiteralPath $SelectionPath) {
    $SelectionRows = @(Import-Csv -LiteralPath $SelectionPath -Encoding UTF8)
    $G2 = @($SelectionRows | Where-Object { $_.product -eq 'AirJet Mini G2' })
    if ($G2.Count -ne 1 -or $G2[0].external_dimensions_mm -ne '27.1x41.5x2.65' -or
        -not (Test-Close $G2[0].heat_dissipation_W 7.5) -or
        -not (Test-Close $G2[0].max_power_W 1.2) -or
        -not (Test-Close $G2[0].backpressure_Pa 1750) -or
        -not (Test-Close $G2[0].noise_dBA 21) -or
        -not (Test-Close $G2[0].weight_g 7)) {
        Add-Failure 'G2 product row does not preserve page-2 direct specifications'
    }
}

$PatentMapPath = Join-Path $RepoRoot 'airjet-simulation\evidence\patent_product_component_map.csv'
if (Test-Path -LiteralPath $PatentMapPath) {
    $PatentRows = @(Import-Csv -LiteralPath $PatentMapPath -Encoding UTF8)
    if ($PatentRows.Count -ne 10) { Add-Failure "patent-product map must contain 10 rows, got $($PatentRows.Count)" }
    foreach ($Row in $PatentRows) {
        if ($Row.evidence_class -ne 'P' -or $Row.exact_locator -notlike '*FIG*' -or $Row.exact_locator -notlike '*col.*') {
            Add-Failure "patent-product map row lacks P/FIG/column evidence: $($Row.product_component_id)"
        }
    }
}

$LayoutScorePath = Join-Path $RepoRoot 'airjet-simulation\evidence\layout_candidate_scores.csv'
if (Test-Path -LiteralPath $LayoutScorePath) {
    $LayoutRows = @(Import-Csv -LiteralPath $LayoutScorePath -Encoding UTF8)
    $UniqueGeometry = @($LayoutRows | ForEach-Object { $_.geometry_key } | Select-Object -Unique)
    $FitRows = @($LayoutRows | Where-Object { $_.hard_envelope -eq 'PASS_CONFIG_A0' })
    $Primary = @($LayoutRows | Where-Object { $_.rank_tier -eq 'PRIMARY-P0' })
    $Alternate = @($LayoutRows | Where-Object { $_.rank_tier -eq 'ALTERNATE-P0' })
    if ($LayoutRows.Count -ne 32 -or $UniqueGeometry.Count -ne 32) { Add-Failure 'layout score table must contain 32 unique geometries' }
    if ($FitRows.Count -ne 23) { Add-Failure "layout score table must preserve 23 A0-fit geometries, got $($FitRows.Count)" }
    if ($Primary.Count -ne 1 -or $Primary[0].candidate_id -ne 'M-3x4-7.0') { Add-Failure 'layout score table changed the P0 working primary' }
    if ($Alternate.Count -ne 1 -or $Alternate[0].candidate_id -ne 'M+S-3x5-6.0') { Add-Failure 'layout score table changed the P0 working alternate' }
    foreach ($Row in $FitRows) {
        if ($Row.score_coverage_pct -ne '20') { Add-Failure "layout score coverage changed: $($Row.candidate_id)" }
        foreach ($Pending in @('S_image','S_modal','S_power','S_flow','S_thermal')) {
            if (-not [string]::IsNullOrWhiteSpace($Row.$Pending)) { Add-Failure "layout pending score was populated: $($Row.candidate_id) $Pending" }
        }
    }
}

$P1LayoutPath = Join-Path $RepoRoot 'airjet-simulation\parameters\p1_layout_configuration_matrix.csv'
if (Test-Path -LiteralPath $P1LayoutPath) {
    $P1LayoutRows = @(Import-Csv -LiteralPath $P1LayoutPath -Encoding UTF8)
    $ExpectedRoles = @{
        'M-3x4-7.0' = 'PRIMARY-P0'
        'M+S-3x5-6.0' = 'ALTERNATE-P0'
        'L-2x4-8.0' = 'LOW-CELL-SENTINEL'
        'S-3x5-5.5' = 'SMALL-CELL-SENTINEL'
    }
    $Ids = @($P1LayoutRows | ForEach-Object { $_.configuration_id })
    $UniqueIds = @($Ids | Select-Object -Unique)
    $ExpectedIds = @($ExpectedRoles.Keys)
    if ($P1LayoutRows.Count -ne 4 -or $UniqueIds.Count -ne 4 -or
        @(Compare-Object ($ExpectedIds | Sort-Object) ($UniqueIds | Sort-Object)).Count -gt 0) {
        Add-Failure 'P1 layout matrix must contain the four unique frozen work configurations'
    }
    foreach ($Row in $P1LayoutRows) {
        $Id = $Row.configuration_id
        if (-not $ExpectedRoles.ContainsKey($Id) -or $Row.p1_role -ne $ExpectedRoles[$Id]) {
            Add-Failure "P1 layout role changed: $Id"
        }
        if ($Row.evidence_class -ne 'C' -or $Row.source_evidence_classes -ne 'D;P;I') {
            Add-Failure "P1 layout must use C with D/P/I source classes: $Id"
        }
        if ($Row.product_fact -ne 'false' -or $Row.hole_count_status -ne 'PROXY_NOT_CAD_LOCKED') {
            Add-Failure "P1 layout was promoted beyond candidate/proxy status: $Id"
        }
        if ($Row.source_refs -notlike '*single-side integrated spout qualitative topology*') {
            Add-Failure "P1 topology lacks official cross-section/spout source boundary: $Id"
        }
        try {
            $Diameter = Convert-InvariantDouble $Row.orifice_diameter_candidate_mm
            $Porosity = (Convert-InvariantDouble $Row.open_area_candidate_pct) / 100.0
            $Area = Convert-InvariantDouble $Row.active_membrane_area_proxy_mm2
            $ExpectedHoles = [Math]::Round(
                $Porosity * $Area / ([Math]::PI * [Math]::Pow($Diameter / 2.0, 2)),
                0,
                [MidpointRounding]::ToEven
            )
            if ((Convert-InvariantDouble $Row.porosity_hole_count_proxy) -ne $ExpectedHoles) {
                Add-Failure "P1 porosity hole-count proxy is stale: $Id"
            }
        } catch {
            Add-Failure "P1 porosity proxy could not be evaluated: $Id"
        }
    }
}

$P1ThicknessPath = Join-Path $RepoRoot 'airjet-simulation\parameters\p1_thickness_budget.csv'
if (Test-Path -LiteralPath $P1ThicknessPath) {
    $P1ThicknessRows = @(Import-Csv -LiteralPath $P1ThicknessPath -Encoding UTF8)
    if ($P1ThicknessRows.Count -ne 10) {
        Add-Failure "P1 thickness budget must contain 10 rows, got $($P1ThicknessRows.Count)"
    }
    $RunningZ = 0.0
    foreach ($Row in $P1ThicknessRows) {
        if ($Row.evidence_class -notin @('D', 'P', 'I', 'C', 'U')) {
            Add-Failure "P1 thickness row has invalid evidence class: $($Row.parameter_id)"
        }
        if ($Row.product_fact -ne 'false') {
            Add-Failure "P1 thickness placeholder was promoted to product fact: $($Row.parameter_id)"
        }
        try {
            $ZMin = Convert-InvariantDouble $Row.z_min_mm
            $ZMax = Convert-InvariantDouble $Row.z_max_mm
            $Thickness = Convert-InvariantDouble $Row.thickness_mm
            if ([Math]::Abs($ZMin - $RunningZ) -gt 1e-9) {
                Add-Failure "P1 thickness z continuity failed at $($Row.parameter_id)"
            }
            if ([Math]::Abs(($ZMax - $ZMin) - $Thickness) -gt 1e-9) {
                Add-Failure "P1 thickness interval failed at $($Row.parameter_id)"
            }
            $RunningZ = $ZMax
        } catch {
            Add-Failure "P1 thickness row is non-numeric: $($Row.parameter_id)"
        }
    }
    if ([Math]::Abs($RunningZ - 2.8) -gt 1e-9) {
        Add-Failure 'P1 thickness budget must close exactly to 2.8 mm'
    }
    $P002Rows = @($P1ThicknessRows | Where-Object { $_.parameter_id -eq 'P002' })
    if ($P002Rows.Count -ne 1 -or $P002Rows[0].applicability_note -notlike '*cross-size CAD placeholder*') {
        Add-Failure 'P002 thickness must remain an explicit 8 mm cross-size P1 placeholder'
    }
    $GeometryOnly = @($P1ThicknessRows | Where-Object {
        $_.parameter_id -in @('C017', 'C019_TOP', 'C019_BOTTOM')
    })
    if ($GeometryOnly.Count -ne 3 -or @($GeometryOnly | Where-Object {
        $_.solver_use -ne 'GEOMETRY_ONLY_NO_MATERIAL_NO_MASS_NO_STRUCTURAL_NO_CHT'
    }).Count -gt 0) {
        Add-Failure 'unresolved P1 residual/support placeholders must be excluded from physics'
    }
}

$P1BuilderPath = Join-Path $RepoRoot 'airjet-simulation\parameters\build_p1_cad_inputs.py'
if (Test-Path -LiteralPath $P1BuilderPath) {
    $PythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($null -eq $PythonCommand) { $PythonCommand = Get-Command python3 -ErrorAction SilentlyContinue }
    if ($null -eq $PythonCommand) {
        Add-Failure 'Python is required to verify generated P1 CAD inputs'
    } else {
        $BuilderOutput = @(& $PythonCommand.Source $P1BuilderPath --check 2>&1)
        if ($LASTEXITCODE -ne 0 -or ($BuilderOutput -join "`n") -notlike '*PASS mode=check*') {
            Add-Failure "P1 generated inputs are stale or invalid: $($BuilderOutput -join ' | ')"
        }
    }
}

$P1ContractBuilderPath = Join-Path $RepoRoot 'airjet-simulation\parameters\build_p1_cad_contracts.py'
if (Test-Path -LiteralPath $P1ContractBuilderPath) {
    $PythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($null -eq $PythonCommand) { $PythonCommand = Get-Command python3 -ErrorAction SilentlyContinue }
    if ($null -eq $PythonCommand) {
        Add-Failure 'Python is required to verify generated P1 CAD contracts'
    } else {
        $ContractBuilderOutput = @(& $PythonCommand.Source $P1ContractBuilderPath --check 2>&1)
        if ($LASTEXITCODE -ne 0 -or ($ContractBuilderOutput -join "`n") -notlike '*PASS mode=check*') {
            Add-Failure "P1 CAD contracts are stale or invalid: $($ContractBuilderOutput -join ' | ')"
        }
    }
}

$VariantPath = Join-Path $RepoRoot 'airjet-simulation\parameters\p1_model_form_variants.csv'
if (Test-Path -LiteralPath $VariantPath) {
    $VariantRows = @(Import-Csv -LiteralPath $VariantPath -Encoding UTF8)
    $ExpectedVariantIds = @(
        'M-3x4-7.0__R25_BOTTOM_HEAVY',
        'M-3x4-7.0__R50_BALANCED',
        'M-3x4-7.0__R75_TOP_HEAVY',
        'M+S-3x5-6.0__R50_BALANCED',
        'L-2x4-8.0__R50_BALANCED',
        'S-3x5-5.5__R50_BALANCED',
        'M-3x4-7.0__R50_VENT_UPPER',
        'M-3x4-7.0__R50_ORIFICE_EDGE_GAP',
        'M-3x4-7.0__R50_EXHAUST_HALF_TAPER'
    )
    $ActualVariantIds = @($VariantRows | ForEach-Object { $_.variant_id } | Sort-Object -Unique)
    if ($VariantRows.Count -ne 9 -or @(Compare-Object ($ExpectedVariantIds | Sort-Object) $ActualVariantIds).Count -gt 0) {
        Add-Failure 'P1 model-form table must contain six base/residual and three derived variants'
    }
    $PrimaryFractions = @($VariantRows | Where-Object { $_.configuration_id -eq 'M-3x4-7.0' } |
        ForEach-Object { $_.C020_residual_top_fraction } | Sort-Object -Unique)
    if (@(Compare-Object @('0.25', '0.50', '0.75') $PrimaryFractions).Count -gt 0) {
        Add-Failure 'P1 primary residual branches must remain 0.25/0.50/0.75'
    }
    foreach ($Row in $VariantRows) {
        if ($Row.product_fact -ne 'false' -or $Row.status -ne 'CANDIDATE_NOT_RUN') {
            Add-Failure "P1 variant was promoted beyond candidate input: $($Row.variant_id)"
        }
        $ExpectedInternalBranches = @{
            cell_geometry_rule_id = 'CELL_CENTER_AND_TILE_R0'
            central_anchor_rule_id = 'CENTRAL_ANCHOR_SQUARE_DATUM_R0'
            bottom_chamber_rule_id = 'BOTTOM_CHAMBER_PER_CELL_SQUARE_R0'
            cell_partition_rule_id = 'CELL_PARTITION_DATUM_R0'
            top_chamber_branch_id = 'TOP_SHARED_PLENUM_R0'
            perimeter_gap_branch_id = 'PERIM_SPLIT_GAP_R0'
            side_frame_closure_branch_id = 'SIDE_WALL_BOUNDARY_R0'
            residual_closure_branch_id = 'RESIDUAL_NUMERICAL_CLOSURE_R0'
            orifice_grid_rule_id = 'ORIFICE_PER_CELL_CENTERED_CLIP_R0'
        }
        foreach ($Field in $ExpectedInternalBranches.Keys) {
            if ($Row.$Field -ne $ExpectedInternalBranches[$Field]) {
                Add-Failure "P1 variant internal R0 branch set changed: $($Row.variant_id)"
                break
            }
        }
        try {
            $Residual = Convert-InvariantDouble $Row.C019_residual_total_mm
            $Split = (Convert-InvariantDouble $Row.residual_top_mm) + (Convert-InvariantDouble $Row.residual_bottom_mm)
            if ([Math]::Abs($Split - $Residual) -gt 1e-9) { Add-Failure "P1 residual split does not close: $($Row.variant_id)" }
        } catch {
            Add-Failure "P1 residual split is non-numeric: $($Row.variant_id)"
        }
    }
    $DerivedRows = @($VariantRows | Where-Object { $_.variant_kind -eq 'DERIVED_SINGLE_FACTOR' })
    $BaselineRows = @($VariantRows | Where-Object { $_.variant_id -eq 'M-3x4-7.0__R50_BALANCED' })
    if ($DerivedRows.Count -ne 3 -or $BaselineRows.Count -ne 1) {
        Add-Failure 'P1 variant table lacks baseline or three derived single-factor rows'
    } else {
        $Baseline = $BaselineRows[0]
        foreach ($Row in $DerivedRows) {
            $Changes = 0
            foreach ($Field in @('vent_candidate_set_id', 'orifice_pattern_id', 'exhaust_branch_id')) {
                if ($Row.$Field -ne $Baseline.$Field) { $Changes++ }
            }
            if ($Row.comparison_parent_variant_id -ne $Baseline.variant_id -or $Changes -ne 1) {
                Add-Failure "P1 derived variant is not single-factor: $($Row.variant_id)"
            }
        }
    }
}

$ParameterMapPath = Join-Path $RepoRoot 'airjet-simulation\parameters\p1_cad_parameter_map.csv'
if (Test-Path -LiteralPath $ParameterMapPath) {
    $ParameterMapRows = @(Import-Csv -LiteralPath $ParameterMapPath -Encoding UTF8)
    if ($ParameterMapRows.Count -ne 342) { Add-Failure "P1 CAD parameter map must contain 342 rows, got $($ParameterMapRows.Count)" }
    if (@($ParameterMapRows | Where-Object { $_.evidence_class -notin @('D', 'P', 'I', 'C', 'U') }).Count -gt 0) {
        Add-Failure 'P1 CAD parameter map contains an invalid evidence class'
    }
    $ProductFactRows = @($ParameterMapRows | Where-Object { $_.product_fact -eq 'true' })
    if ($ProductFactRows.Count -ne 27 -or @($ProductFactRows | Where-Object { $_.parameter_id -notin @('D001', 'D002', 'D003') }).Count -gt 0) {
        Add-Failure 'only D001/D002/D003 may be product facts in the P1 CAD parameter map'
    }
    $GuardedRows = @($ParameterMapRows | Where-Object { $_.parameter_id -in @('C017', 'C019', 'C019_TOP', 'C019_BOTTOM') })
    if ($GuardedRows.Count -ne 36 -or @($GuardedRows | Where-Object {
        $_.geometry_only -ne 'true' -or $_.solver_use -ne 'GEOMETRY_ONLY_NO_MATERIAL_NO_MASS_NO_STRUCTURAL_NO_CHT'
    }).Count -gt 0) {
        Add-Failure 'P1 CAD parameter-map geometry-only guards changed'
    }
}

$OrificePath = Join-Path $RepoRoot 'airjet-simulation\parameters\p1_orifice_pattern_candidates.csv'
if (Test-Path -LiteralPath $OrificePath) {
    $OrificeRows = @(Import-Csv -LiteralPath $OrificePath -Encoding UTF8)
    $OrificeConfigurations = @($OrificeRows | ForEach-Object { $_.configuration_id } | Select-Object -Unique)
    if ($OrificeRows.Count -ne 12 -or $OrificeConfigurations.Count -ne 4) {
        Add-Failure 'P1 orifice table must contain three branches for each of four configurations'
    }
    if (@($OrificeRows | Where-Object { $_.product_fact -ne 'false' }).Count -gt 0) {
        Add-Failure 'P1 orifice branch was promoted to product fact'
    }
    $CenterRows = @($OrificeRows | Where-Object { $_.pattern_id -like '*CENTER_PITCH_SENTINEL*' })
    if ($CenterRows.Count -ne 4 -or @($CenterRows | Where-Object {
        (Convert-InvariantDouble $_.infinite_square_grid_open_area_pct) -le 15.0 -or $_.cad_ready_candidate -ne 'false'
    }).Count -gt 0) {
        Add-Failure 'P008 center-pitch porosity conflict sentinel was lost'
    }
    $EdgeRows = @($OrificeRows | Where-Object { $_.pattern_id -like '*P008_AS_EDGE_GAP*' })
    if ($EdgeRows.Count -ne 4 -or @($EdgeRows | Where-Object { -not (Test-Close $_.pitch_x_mm 0.75 1e-6) }).Count -gt 0) {
        Add-Failure 'P008 edge-gap candidate pitch must remain 0.75 mm'
    }
}

$VentCandidatePath = Join-Path $RepoRoot 'airjet-simulation\parameters\p1_vent_geometry_candidates.csv'
if (Test-Path -LiteralPath $VentCandidatePath) {
    $VentCandidateRows = @(Import-Csv -LiteralPath $VentCandidatePath -Encoding UTF8)
    $FlowCandidateRows = @($VentCandidateRows | Where-Object { $_.candidate_set_id -eq 'VENT_FLOW_BBOX_R0' })
    $UpperCandidateRows = @($VentCandidateRows | Where-Object { $_.candidate_set_id -eq 'VENT_UPPER_CENTERLINE_P013_R0' })
    if ($VentCandidateRows.Count -ne 8 -or $FlowCandidateRows.Count -ne 4 -or $UpperCandidateRows.Count -ne 4 -or
        @($FlowCandidateRows.vent_id | Select-Object -Unique).Count -ne 4 -or
        @($UpperCandidateRows.vent_id | Select-Object -Unique).Count -ne 4) {
        Add-Failure 'P1 vent candidates must contain two complete four-object sets'
    }
    if (@($VentCandidateRows | Where-Object {
        $_.product_fact -ne 'false' -or $_.drawn_object_count_scope -ne 'FOUR_DRAWN_OBJECTS_NOT_GROUP_COUNT'
    }).Count -gt 0) {
        Add-Failure 'P1 vent candidate evidence boundary changed'
    }
}

$PlanformPath = Join-Path $RepoRoot 'airjet-simulation\parameters\p1_planform_exhaust_candidates.csv'
if (Test-Path -LiteralPath $PlanformPath) {
    $PlanformRows = @(Import-Csv -LiteralPath $PlanformPath -Encoding UTF8)
    $PlanformConfigurations = @($PlanformRows | ForEach-Object { $_.configuration_id } | Select-Object -Unique)
    $PlanformCountFailure = $false
    foreach ($Configuration in $PlanformConfigurations) {
        if (@($PlanformRows | Where-Object { $_.configuration_id -eq $Configuration }).Count -ne 2) {
            $PlanformCountFailure = $true
        }
    }
    if ($PlanformRows.Count -ne 8 -or $PlanformConfigurations.Count -ne 4 -or $PlanformCountFailure) {
        Add-Failure 'P1 exhaust table must contain two branches for each configuration'
    }
    if (@($PlanformRows | Where-Object {
        $_.product_fact -ne 'false' -or $_.single_side_rule -ne 'OUTLET_ON_Y_PLUS_ENVELOPE_FACE_ONLY' -or
        -not (Test-Close $_.manifold_y_max_mm 20.75 1e-9) -or (Convert-InvariantDouble $_.manifold_length_mm) -le 0.0
    }).Count -gt 0) {
        Add-Failure 'P1 exhaust branch evidence or geometry closure changed'
    }
}

$InternalRulePath = Join-Path $RepoRoot 'airjet-simulation\parameters\p1_internal_geometry_rules.csv'
if (Test-Path -LiteralPath $InternalRulePath) {
    $InternalRuleRows = @(Import-Csv -LiteralPath $InternalRulePath -Encoding UTF8)
    $ExpectedRuleIds = @(
        'CELL_CENTER_AND_TILE_R0',
        'BOTTOM_CHAMBER_PER_CELL_SQUARE_R0',
        'CENTRAL_ANCHOR_SQUARE_DATUM_R0',
        'CELL_PARTITION_DATUM_R0',
        'TOP_SHARED_PLENUM_R0',
        'PERIM_SPLIT_GAP_R0',
        'SIDE_WALL_BOUNDARY_R0',
        'RESIDUAL_NUMERICAL_CLOSURE_R0',
        'ORIFICE_PER_CELL_CENTERED_CLIP_R0'
    )
    $ActualRuleIds = @($InternalRuleRows | ForEach-Object { $_.rule_id } | Sort-Object -Unique)
    if ($InternalRuleRows.Count -ne 9 -or @(Compare-Object ($ExpectedRuleIds | Sort-Object) $ActualRuleIds).Count -gt 0) {
        Add-Failure 'P1 internal geometry table must retain the nine explicit R0 rules'
    }
    if (@($InternalRuleRows | Where-Object {
        $_.product_fact -ne 'false' -or $_.evidence_class -ne 'C' -or
        $_.selection_status -ne 'SELECTED_R0_ENGINEERING_CLOSURE'
    }).Count -gt 0) {
        Add-Failure 'P1 internal geometry rule was promoted beyond C-class engineering closure'
    }
    $ExpectedRuleSources = @{
        CELL_CENTER_AND_TILE_R0 = 'P;C'
        BOTTOM_CHAMBER_PER_CELL_SQUARE_R0 = 'P;C'
        CENTRAL_ANCHOR_SQUARE_DATUM_R0 = 'P;C'
        CELL_PARTITION_DATUM_R0 = 'P;C'
        TOP_SHARED_PLENUM_R0 = 'P;I;C'
        PERIM_SPLIT_GAP_R0 = 'P;C'
        SIDE_WALL_BOUNDARY_R0 = 'D;I;C;U'
        RESIDUAL_NUMERICAL_CLOSURE_R0 = 'C;U'
        ORIFICE_PER_CELL_CENTERED_CLIP_R0 = 'P;C'
    }
    if (@($InternalRuleRows | Where-Object {
        $_.source_evidence_classes -ne $ExpectedRuleSources[$_.rule_id]
    }).Count -gt 0) {
        Add-Failure 'P1 internal geometry rule provenance classes changed'
    }
    $ResidualRule = @($InternalRuleRows | Where-Object { $_.rule_id -eq 'RESIDUAL_NUMERICAL_CLOSURE_R0' })
    if ($ResidualRule.Count -ne 1 -or $ResidualRule[0].planform_or_construction_rule -notlike '*NEVER_EXTRACT_OUTER_ENVELOPE_MINUS_ALL_SOLIDS*') {
        Add-Failure 'P1 residual closure no longer prevents false fluid extraction'
    }
}

$FeatureContractPath = Join-Path $RepoRoot 'airjet-simulation\geometry\contracts\p1_cad_features.csv'
if (Test-Path -LiteralPath $FeatureContractPath) {
    $FeatureRows = @(Import-Csv -LiteralPath $FeatureContractPath -Encoding UTF8)
    $FeatureIds = @($FeatureRows | ForEach-Object { $_.feature_id } | Select-Object -Unique)
    if ($FeatureRows.Count -ne 30 -or $FeatureIds.Count -ne 30) { Add-Failure 'P1 feature contract must contain 30 unique features' }
    $TrueFeatures = @($FeatureRows | Where-Object { $_.product_fact -eq 'true' })
    if ($TrueFeatures.Count -ne 1 -or $TrueFeatures[0].feature_id -ne 'ENVELOPE_REF') {
        Add-Failure 'only ENVELOPE_REF may be a product fact in the P1 feature contract'
    }
    $ResidualFeatures = @($FeatureRows | Where-Object { $_.feature_id -in @('C017_SUPPORT_ALLOWANCE_REF', 'C019_TOP_REF', 'C019_BOTTOM_REF') })
    if ($ResidualFeatures.Count -ne 3 -or @($ResidualFeatures | Where-Object {
        $_.material_policy -ne 'PROHIBITED' -or $_.mass_policy -ne 'EXCLUDE' -or
        $_.boolean_policy -ne 'NO_BOOLEAN' -or $_.export_policy -ne 'DO_NOT_EXPORT' -or
        $_.solver_use -ne 'GEOMETRY_ONLY_NO_PHYSICS'
    }).Count -gt 0) {
        Add-Failure 'P1 feature residual/support guards changed'
    }
    $ConstructionDatums = @($FeatureRows | Where-Object {
        $_.feature_id -in @('CENTRAL_ANCHOR_CAND_TEMPLATE', 'CELL_PARTITION_CAND_TEMPLATE')
    })
    if ($ConstructionDatums.Count -ne 2 -or @($ConstructionDatums | Where-Object {
        $_.material_policy -ne 'PROHIBITED' -or $_.mass_policy -ne 'EXCLUDE' -or
        $_.boolean_policy -notlike 'NO_BOOLEAN*' -or $_.export_policy -notlike 'DO_NOT_EXPORT*' -or
        $_.solver_use -ne 'GEOMETRY_ONLY_NO_PHYSICS'
    }).Count -gt 0) {
        Add-Failure 'P1 central-anchor or cell-partition datum gained physical behavior'
    }
    if (@($ConstructionDatums | Where-Object { $_.geometry_class -ne 'C' }).Count -gt 0) {
        Add-Failure 'P1 central-anchor or cell-partition exact geometry was promoted beyond C'
    }
}

$BindingContractPath = Join-Path $RepoRoot 'airjet-simulation\geometry\contracts\p1_cad_feature_parameter_bindings.csv'
if (Test-Path -LiteralPath $BindingContractPath) {
    $BindingRows = @(Import-Csv -LiteralPath $BindingContractPath -Encoding UTF8)
    $BindingIds = @($BindingRows | ForEach-Object { $_.binding_id } | Select-Object -Unique)
    if ($BindingRows.Count -ne 31 -or $BindingIds.Count -ne 31 -or @($BindingRows | Where-Object {
        [string]::IsNullOrWhiteSpace($_.parameter_id) -or [string]::IsNullOrWhiteSpace($_.source_locator)
    }).Count -gt 0) {
        Add-Failure 'P1 parameter-binding contract count or provenance changed'
    }
    $PartitionBindings = @($BindingRows | Where-Object {
        $_.feature_id -eq 'CELL_PARTITION_CAND_TEMPLATE' -and $_.parameter_id -eq 'P014'
    })
    if ($PartitionBindings.Count -ne 1 -or $PartitionBindings[0].geometry_only -ne 'true') {
        Add-Failure 'P1 cell-partition datum binding must remain geometry-only'
    }
}

$InterfaceContractPath = Join-Path $RepoRoot 'airjet-simulation\geometry\contracts\p1_cad_interfaces.csv'
if (Test-Path -LiteralPath $InterfaceContractPath) {
    $InterfaceRows = @(Import-Csv -LiteralPath $InterfaceContractPath -Encoding UTF8)
    $ForbiddenInterfaceFeatures = @(
        'C017_SUPPORT_ALLOWANCE_REF', 'C019_TOP_REF', 'C019_BOTTOM_REF', 'FLEX_KEEP_OUT_U',
        'CENTRAL_ANCHOR_CAND_TEMPLATE', 'CELL_PARTITION_CAND_TEMPLATE'
    )
    if ($InterfaceRows.Count -ne 13 -or @($InterfaceRows | Where-Object {
        $_.side_a_feature_id -in $ForbiddenInterfaceFeatures -or $_.side_b_feature_id -in $ForbiddenInterfaceFeatures
    }).Count -gt 0) {
        Add-Failure 'P1 interface contract count or geometry-only exclusion changed'
    }
    foreach ($Interface in $InterfaceRows) {
        $ExpectedBranch = 'ALL_P1_VARIANTS'
        if ($Interface.interface_id -in @('IF001', 'IF009')) { $ExpectedBranch = 'P1_OPTIONAL_EXTERNAL_DOMAIN' }
        if ($Interface.interface_id -eq 'IF013') { $ExpectedBranch = 'P5_ONLY' }
        if ($Interface.branch_id -ne $ExpectedBranch) {
            Add-Failure "P1 interface branch scope changed: $($Interface.interface_id)"
        }
    }
}

$NamedContractPath = Join-Path $RepoRoot 'airjet-simulation\geometry\contracts\p1_cad_named_selections.csv'
if (Test-Path -LiteralPath $NamedContractPath) {
    $NamedRows = @(Import-Csv -LiteralPath $NamedContractPath -Encoding UTF8)
    $NamedIds = @($NamedRows | ForEach-Object { $_.selection_id } | Select-Object -Unique)
    if ($NamedRows.Count -ne 37 -or $NamedIds.Count -ne 37 -or @($NamedRows | Where-Object {
        $_.selection_id -match 'REAL_|PRODUCTION_|ACTUAL_SPOUT|MATERIAL_RESIDUAL_LAYER'
    }).Count -gt 0) {
        Add-Failure 'P1 named-selection contract count or evidence-safe naming changed'
    }
    $NamedById = @{}
    foreach ($Row in $NamedRows) { $NamedById[$Row.selection_id] = $Row }
    if (Test-Path -LiteralPath $InterfaceContractPath) {
        foreach ($Interface in $InterfaceRows) {
            $SideA = $NamedById[$Interface.named_selection_a]
            $SideB = $NamedById[$Interface.named_selection_b]
            if ($null -eq $SideA -or $null -eq $SideB) {
                Add-Failure "P1 interface lacks an exact named-selection pair: $($Interface.interface_id)"
            } elseif ($SideA.owner_feature_id -ne $Interface.side_a_feature_id -or
                $SideB.owner_feature_id -ne $Interface.side_b_feature_id -or
                $Interface.interface_mode -ne 'PAIRED_NONCONFORMAL_OR_MATCHED_FACE') {
                Add-Failure "P1 interface named-selection ownership mismatch: $($Interface.interface_id)"
            }
        }
    }
}

$OpenQuestionPath = Join-Path $RepoRoot 'airjet-simulation\geometry\contracts\p1_cad_open_questions.csv'
if (Test-Path -LiteralPath $OpenQuestionPath) {
    $OpenRows = @(Import-Csv -LiteralPath $OpenQuestionPath -Encoding UTF8)
    if ($OpenRows.Count -ne 15 -or @($OpenRows | Where-Object { $_.status -ne 'OPEN' -or $_.product_fact -ne 'false' }).Count -gt 0) {
        Add-Failure 'P1 open-question contract must retain 15 open non-product-fact rows'
    }
    $IntakeMapping = @($OpenRows | Where-Object { $_.question_id -eq 'OQ002' })
    if ($IntakeMapping.Count -ne 1 -or $IntakeMapping[0].evidence_class -ne 'U') {
        Add-Failure 'true intake-group count and cell mapping must remain U-class'
    }
}

$GateMatrixPath = Join-Path $RepoRoot 'airjet-simulation\checklists\p1_cad_gate_matrix.csv'
if (Test-Path -LiteralPath $GateMatrixPath) {
    $GateRows = @(Import-Csv -LiteralPath $GateMatrixPath -Encoding UTF8)
    $GateVariantIds = @($GateRows | ForEach-Object { $_.variant_id } | Select-Object -Unique)
    if ($GateRows.Count -ne 252 -or $GateVariantIds.Count -ne 9 -or
        @($GateRows | Where-Object { $_.status -ne 'NOT_RUN' }).Count -gt 0) {
        Add-Failure 'P1 CAD gate matrix must contain 252 NOT_RUN rows across nine variants'
    }
    if ($GateRows.Count -gt 0) {
        $GateProperties = @($GateRows[0].PSObject.Properties.Name)
        foreach ($RequiredProperty in @(
            'selected_vent_candidate_set_id',
            'selected_orifice_pattern_id',
            'selected_exhaust_branch_id',
            'selected_cell_geometry_rule_id',
            'selected_central_anchor_rule_id',
            'selected_bottom_chamber_rule_id',
            'selected_cell_partition_rule_id',
            'selected_top_chamber_branch_id',
            'selected_perimeter_gap_branch_id',
            'selected_side_frame_closure_branch_id',
            'selected_residual_closure_branch_id',
            'selected_orifice_grid_rule_id',
            'comparison_parent_variant_id',
            'changed_factor'
        )) {
            if ($RequiredProperty -notin $GateProperties) { Add-Failure "P1 CAD gate matrix lacks branch field: $RequiredProperty" }
        }
    }
    foreach ($GateId in @('G4_INTERFERENCE', 'G4_ZERO_THICKNESS', 'G4_DUPLICATE_FACES')) {
        $ScopedRows = @($GateRows | Where-Object { $_.gate_item_id -eq $GateId })
        if ($ScopedRows.Count -ne 9 -or @($ScopedRows | Where-Object {
            $_.requirement -notlike '*exported physical candidate solids and required fluid bodies*'
        }).Count -gt 0) {
            Add-Failure "P1 geometry-health Gate scope changed: $GateId"
        }
    }
}

$ExternalFilesPath = Join-Path $RepoRoot 'airjet-simulation\logs\external-files.csv'
if (Test-Path -LiteralPath $ExternalFilesPath) {
    $ExternalText = (Read-Utf8 $ExternalFilesPath).Trim()
    $ExpectedExternalHeader = 'case_id,file_role,absolute_path,size_bytes,sha256,created_at_utc,software_version,git_commit,notes'
    if ($ExternalText -ne $ExpectedExternalHeader) {
        Add-Failure 'external-files.csv must remain an empty canonical P1 artifact manifest'
    }
}

$ReviewScriptPath = Join-Path $RepoRoot 'airjet-simulation\checklists\prepare_p1_cad_review.py'
if (Test-Path -LiteralPath $ReviewScriptPath) {
    $ReviewScriptText = Read-Utf8 $ReviewScriptPath
    foreach ($Marker in @(
        'AJM-WIN-P1-FULL-PRODUCT-CAD-BUILD-006',
        'duplicate report key',
        '"merge-base"',
        'P1 gate input must contain 252 unique gate/variant rows',
        'review packet output must remain outside the Git repository',
        'P1_STAGE_GATE=PENDING_INDEPENDENT_REVIEW',
        'REVIEW_PACKET_PREPARATION=PASS',
        'PureWindowsPath',
        'GATE_EVIDENCE_006_CSV',
        'P1_CONTRACT_BUNDLE_SHA256',
        'load_gate_rows_at_commit',
        'copied run root contains unindexed files',
        '"REPORT_005_COPY"',
        '"PARENT_GEOMETRY_RESULT_DIFF"',
        '"secondary_evidence_original_path"',
        '"secondary_evidence_sha256"',
        '"--finalize-worksheet"',
        '"--spot-check-record"',
        'validate_step_limitation_consistency',
        'P1_REVIEW_RECOMMENDATION=PASS',
        'P1_STAGE_GATE=PENDING_REVIEW_RECORD_COMMIT',
        'Preparation PASS does not mean P1 PASS'
    )) {
        if (-not $ReviewScriptText.Contains($Marker)) { Add-Failure "P1 independent-review script lacks invariant: $Marker" }
    }
}

$ReviewMethodPath = Join-Path $RepoRoot 'airjet-simulation\checklists\P1_CAD_INDEPENDENT_REVIEW_METHOD.md'
if (Test-Path -LiteralPath $ReviewMethodPath) {
    $ReviewMethodText = Read-Utf8 $ReviewMethodPath
    foreach ($Marker in @(
        'P1_REVIEW_RECOMMENDATION=PASS',
        '252',
        'LIMITATION_ACCEPTED',
        'NOT_REVIEWED',
        'PureWindowsPath',
        '006 commit',
        'prepare_p1_cad_review.py',
        'INCOMPLETE'
    )) {
        if (-not $ReviewMethodText.Contains($Marker)) { Add-Failure "P1 independent-review method lacks invariant: $Marker" }
    }
}

$VentResultsPath = Join-Path $RepoRoot 'airjet-simulation\evidence\annotated_figures\gen1_vent_homography_results.csv'
if (Test-Path -LiteralPath $VentResultsPath) {
    $VentRows = @(Import-Csv -LiteralPath $VentResultsPath -Encoding UTF8)
    $FlowRows = @($VentRows | Where-Object { $_.view_id -eq 'flow_636' })
    $UpperRows = @($VentRows | Where-Object { $_.view_id -eq 'upper_547' })
    $FlowFeatures = @($FlowRows | ForEach-Object { $_.feature_id } | Select-Object -Unique)
    $UpperFeatures = @($UpperRows | ForEach-Object { $_.feature_id } | Select-Object -Unique)
    if ($VentRows.Count -ne 8 -or $FlowRows.Count -ne 4 -or $UpperRows.Count -ne 4 -or
        $FlowFeatures.Count -ne 4 -or $UpperFeatures.Count -ne 4) {
        Add-Failure 'vent homography table must contain four features in each of two views'
    }
    if (@($VentRows | Where-Object { $_.evidence_class -ne 'I' }).Count -gt 0) { Add-Failure 'vent homography results must remain I-class' }
}

$CrossViewPath = Join-Path $RepoRoot 'airjet-simulation\evidence\annotated_figures\gen1_vent_cross_view_comparison.csv'
if (Test-Path -LiteralPath $CrossViewPath) {
    $CrossRows = @(Import-Csv -LiteralPath $CrossViewPath -Encoding UTF8)
    $CrossFeatures = @($CrossRows | ForEach-Object { $_.feature_id } | Select-Object -Unique)
    $CrossDifferences = New-Object System.Collections.Generic.List[double]
    foreach ($Row in $CrossRows) {
        try {
            $Value = Convert-InvariantDouble $Row.abs_center_x_difference_mm
            if ([double]::IsNaN($Value) -or [double]::IsInfinity($Value)) { throw 'non-finite value' }
            $CrossDifferences.Add($Value)
        } catch {
            Add-Failure "vent cross-view difference is not finite: $($Row.feature_id)"
        }
    }
    if ($CrossRows.Count -ne 4 -or $CrossFeatures.Count -ne 4) {
        Add-Failure 'vent cross-view comparison must contain four matched features'
    } elseif ($CrossDifferences.Count -eq 4) {
        $MaxDifference = ($CrossDifferences | Measure-Object -Maximum).Maximum
        if ($MaxDifference -lt 2.5) { Add-Failure 'vent cross-view model-form discrepancy was lost or understated' }
    }
}

$P0RecordPath = Join-Path $RepoRoot 'airjet-simulation\evidence\P0_EVIDENCE_FREEZE_RECORD.md'
if (Test-Path -LiteralPath $P0RecordPath) {
    $P0Text = Read-Utf8 $P0RecordPath
    if (-not $P0Text.Contains('PASS - P0 evidence freeze v1') -or
        -not $P0Text.Contains('P1 CAD') -or -not $P0Text.Contains('P6') -or
        -not $P0Text.Contains($DrawnVentMarker)) {
        Add-Failure 'P0 evidence-freeze record lacks the PASS/boundary markers'
    }
}

$WindowsPromptPath = Join-Path $RepoRoot 'airjet-simulation\windows-prompts\AJM_WIN_P1_READINESS_001.md'
if (Test-Path -LiteralPath $WindowsPromptPath) {
    $WindowsPromptText = Read-Utf8 $WindowsPromptPath
    foreach ($Marker in @(
        'HANDSHAKE_STATUS=P1_HANDOFF_READY',
        'HANDSHAKE_STATUS=P1_BLOCKED',
        'P1_CAD_STATUS=READY',
        'P1_CAD_STATUS=BLOCKED',
        'ACTION_BOUNDARY=DO_NOT_CREATE_CAD',
        'MODEL_BOUNDARY=WORKING_CANDIDATES_NOT_PRODUCT_FACT',
        'P0_GATE_BOUNDARY=P0_EVIDENCE_ONLY_P1_P6_NOT_PASSED',
        'PRESSURE_BOUNDARY=1750_PA_CAPABILITY_FLOW_UNKNOWN',
        'AIRJET_P1_READINESS_REPORT.txt',
        'git status --porcelain',
        'git remote get-url origin',
        'git rev-list --left-right --count HEAD...origin/main',
        'https://github.com/superboynick/win-mac-dual-channel.git',
        'M-3x4-7.0',
        'M+S-3x5-6.0',
        'model_reasoning_effort = "high"',
        '96f65ca6e5c8b8d4bc2b4acdeeb78d9917cf3c5ec2c159055daf88fa3ea261a4',
        '822fbb7e9735a5505734a291083fed7901c1fdfa01cb7de369679e4d41fd19bd'
    )) {
        if (-not $WindowsPromptText.Contains($Marker)) { Add-Failure "Windows P1 prompt lacks invariant: $Marker" }
    }
    if ($WindowsPromptText.Contains('HANDSHAKE_STATUS=P1_READY')) {
        Add-Failure 'Windows P1 prompt uses an ambiguous P1_READY status'
    }
}

$TrialPromptPath = Join-Path $RepoRoot 'airjet-simulation\windows-prompts\AJM_WIN_ANSYS_OFFICIAL_TRIAL_INSTALL_AND_SMOKE_004.md'
if (Test-Path -LiteralPath $TrialPromptPath) {
    $TrialPromptText = Read-Utf8 $TrialPromptPath
    foreach ($Marker in @(
        'AnsysInstaller.exe',
        'OFFICIAL_TRIAL_STATUS=NOT_YET_ENTITLED',
        'OFFICIAL_TRIAL_STATUS=PASS_START_P1_WITH_LIMITATIONS',
        (ConvertFrom-Utf8Base64 'U1RFUCDkuI3mmK8gUDEg5ZSv5LiA56Gs6Zeo5qeb'),
        (ConvertFrom-Utf8Base64 '56aB5q2i5oiq5Y+W5ZCr6L+Z5Lqb5L+h5oGv55qE6aG16Z2i5YaF5a65'),
        (ConvertFrom-Utf8Base64 '5b2T5YmNIGNoZWNrb3V0IOadpeiHquWumOaWuSBTdHVkZW50IOaIluW3suW8gOmAmiB0cmlhbA==')
    )) {
        if (-not $TrialPromptText.Contains($Marker)) {
            Add-Failure "Windows official-trial prompt lacks invariant: $Marker"
        }
    }
}

$StudentPromptPath = Join-Path $RepoRoot 'airjet-simulation\windows-prompts\AJM_WIN_ANSYS_STUDENT_CAPABILITY_SMOKE_005.md'
if (Test-Path -LiteralPath $StudentPromptPath) {
    $StudentPromptText = Read-Utf8 $StudentPromptPath
    foreach ($Marker in @(
        'D:\ansys\ANSYS Inc\ANSYS Student\v261',
        'git fetch origin',
        'GIT_FETCH=PASS/FAIL',
        'STUDENT_TOOLCHAIN_STATUS=PASS_START_P1',
        'STUDENT_TOOLCHAIN_STATUS=PASS_START_P1_WITH_LIMITATIONS',
        'STUDENT_TOOLCHAIN_STATUS=BLOCKED_CONTAMINATED_BASELINE',
        'P1_CAD_TOOLCHAIN_READINESS=PASS/PASS_WITH_TRANSFER_LIMITATION/BLOCKED',
        'P1_STAGE_GATE=NOT_RUN',
        'NAMED_SELECTION_TRANSFER=PASS/FAIL',
        (ConvertFrom-Utf8Base64 'U1RFUCDmmK/ph43opoHkuqTmjqXog73lipvvvIzkvYbkuI3mmK/llK/kuIDnoazpl6jmp5s='),
        'SYSTEM_COUPLING_STATUS=UNVERIFIED_WARNING',
        'CUDSS_STATUS=UNVERIFIED_WARNING',
        'AIRJET_ANSYS_STUDENT_CAPABILITY_SMOKE_005.txt',
        (ConvertFrom-Utf8Base64 '5LiN5Yib5bu65q2j5byPIEFpckpldCBDQUQ=')
    )) {
        if (-not $StudentPromptText.Contains($Marker)) {
            Add-Failure "Windows Student smoke prompt lacks invariant: $Marker"
        }
    }
    if ($StudentPromptText.Contains('P1_FULL_PRODUCT_CAD=')) {
        Add-Failure 'Windows Student smoke prompt conflates toolchain readiness with the P1 stage Gate'
    }
}

$CadPromptPath = Join-Path $RepoRoot 'airjet-simulation\windows-prompts\AJM_WIN_P1_FULL_PRODUCT_CAD_BUILD_006.md'
if (Test-Path -LiteralPath $CadPromptPath) {
    $CadPromptText = Read-Utf8 $CadPromptPath
    foreach ($Marker in @(
        'AJM-WIN-P1-FULL-PRODUCT-CAD-BUILD-006',
        'TASK=AJM-WIN-ANSYS-STUDENT-CAPABILITY-SMOKE-005',
        'OLD_PLE_BASELINE=CLEAN',
        'GIT_FETCH=PASS',
        'git merge-base --is-ancestor $Report005Commit HEAD',
        'git remote get-url origin',
        "git rev-parse --abbrev-ref --symbolic-full-name '@{u}'",
        'https://github.com/superboynick/win-mac-dual-channel.git',
        'AIRJET_ANSYS_STUDENT_CAPABILITY_SMOKE_005.txt',
        'build_p1_cad_contracts.py --check',
        'D:\AirJet_P1\AJM-P1-CAD-006\<UTC-run-id>',
        '$RunId = (Get-Date).ToUniversalTime().ToString(''yyyyMMddTHHmmssZ'')',
        'git status --porcelain',
        'ANSYSLMD_LICENSE_FILE=1055@localhost',
        'REPORT_005_GIT_COMMIT=',
        'GIT_ORIGIN=https://github.com/superboynick/win-mac-dual-channel.git',
        'GIT_BRANCH=main',
        'GIT_UPSTREAM=origin/main',
        'FINAL_GIT_CLEAN=PASS/FAIL',
        'C_FREE_GIB=',
        'D_FREE_GIB=',
        'AVAILABLE_RAM_GIB=',
        'LICENSE_SAFETY_CHECK=PASS/FAIL',
        'P1_CONTRACT_BUNDLE_SHA256=',
        'GATE_TEMPLATE_SHA256=',
        'VARIANT_TABLE_SHA256=',
        'INTERNAL_RULES_SHA256=',
        'GATE_EVIDENCE_006_CSV',
        'AUTOMATED_CHECKS_CSV',
        'REPORT_005_COPY',
        'PARENT_GEOMETRY_RESULT_DIFF',
        'secondary_evidence_original_path,secondary_evidence_sha256',
        'excluded_datum_feature_ids',
        'anchor_partition_nonphysical_guard',
        'selected_central_anchor_rule_id=CENTRAL_ANCHOR_SQUARE_DATUM_R0',
        'selected_bottom_chamber_rule_id=BOTTOM_CHAMBER_PER_CELL_SQUARE_R0',
        'selected_cell_partition_rule_id=CELL_PARTITION_DATUM_R0',
        'CONFIGURATIONS_REQUESTED=4',
        'BASE_OR_RESIDUAL_VARIANTS_REQUESTED=6',
        'DERIVED_SINGLE_FACTOR_VARIANTS_REQUESTED=3',
        'TOTAL_VARIANTS_REQUESTED=9',
        'BLOCKED_005_GATE',
        'BLOCKED_GIT_OR_ENVIRONMENT',
        'PARTIAL_CAD_OUTPUT',
        'COMPLETE_WITH_TRANSFER_LIMITATION_AWAITING_REVIEW',
        'COMPLETE_AWAITING_REVIEW',
        'P1_STAGE_GATE=NOT_STARTED/INCOMPLETE/PENDING_PEER_REVIEW',
        'C017_C019_PHYSICS_GUARD=',
        'PARAMETER_DIFF_CHECK=PASS_ALL_3_DERIVED/FAIL',
        'GEOMETRY_RESULT_DIFF_CHECK=PASS_ALL_3_DERIVED/FAIL',
        'STEP_EXPORT_REIMPORT=PASS_ALL_9/LIMITATION_RECORDED/FAIL',
        'ANCHOR_PARTITION_NONPHYSICAL_GUARD=PASS_ALL_9/FAIL',
        'TRANSFER_LIMITATION_SCOPE=NONE/STEP_ONLY',
        'REPORT_005_PARSE=UNIQUE_KEYS_REJECT_DUPLICATES_AND_CONFLICTS',
        'REPORT_005_IDENTITY=TASK_COMPUTER_ANSYS_VERSION_INSTALL_ROOT_COMMIT',
        'LICENSE_POLICY=NO_LICENSE_FILE_POOL_SERVICE_REGISTRY_ENV_PRIORITY_CHECKOUT_MUTATION',
        'RESOURCE_THRESHOLDS_GIB=C_FREE_GE_10_D_FREE_GE_20_AVAILABLE_RAM_GE_8',
        'GIT_RECHECK=BEFORE_BUILD_AFTER_EACH_VARIANT_AFTER_FINAL_MANIFEST',
        'STATUS_MAP_BLOCKED_005_GATE=NOT_STARTED',
        'STATUS_MAP_BLOCKED_GIT_OR_ENVIRONMENT=NOT_STARTED',
        'STATUS_MAP_PARTIAL_CAD_OUTPUT=INCOMPLETE',
        'STATUS_MAP_COMPLETE_WITH_TRANSFER_LIMITATION_AWAITING_REVIEW=PENDING_PEER_REVIEW',
        'STATUS_MAP_COMPLETE_AWAITING_REVIEW=PENDING_PEER_REVIEW',
        'P1_PASS_PROHIBITED=006_CAN_ONLY_REACH_PENDING_PEER_REVIEW',
        '005_TRANSFER_LIMITATION_INHERITANCE=REQUIRED'
    )) {
        if (-not $CadPromptText.Contains($Marker)) { Add-Failure "Windows P1 CAD prompt lacks invariant: $Marker" }
    }
    if ($CadPromptText -match '(?mi)^\s*(?:[-*+]\s*)?`?P1_STAGE_GATE\s*=\s*PASS(?:\s|`|$)') {
        Add-Failure 'Windows P1 CAD prompt is allowed to report P1 PASS'
    }
}

$StudentCleanupPath = Join-Path $RepoRoot 'airjet-simulation\reports\AJM_WIN_ANSYS_STUDENT_CLEANUP_2026-07-14.md'
if (Test-Path -LiteralPath $StudentCleanupPath) {
    $StudentCleanupText = Read-Utf8 $StudentCleanupPath
    foreach ($Marker in @(
        'WINDOWS_ANSYS_STUDENT_CLEANUP_STATUS=PASS',
        (ConvertFrom-Utf8Base64 'TWFjIFNTSCDlho3pqozor4E='),
        'python_site_syscplg',
        'cuDSS',
        (ConvertFrom-Utf8Base64 '5LiN6KGo56S6IFAxLS1QNSDlt6XnqIvog73lipvlt7Llhajpg6jpgJrov4c=')
    )) {
        if (-not $StudentCleanupText.Contains($Marker)) {
            Add-Failure "Student cleanup report lacks boundary marker: $Marker"
        }
    }
}

$NotebookPath = Join-Path $RepoRoot 'airjet-simulation\notebooks\airjet-mini-layout-baseline.ipynb'
if (Test-Path -LiteralPath $NotebookPath) {
    try {
        $NotebookText = Read-Utf8 $NotebookPath
        $Notebook = $NotebookText | ConvertFrom-Json
        if ($Notebook.nbformat -ne 4 -or @($Notebook.cells).Count -eq 0) {
            Add-Failure 'layout notebook must be a non-empty nbformat 4 document'
        }
        foreach ($Invariant in @('system_noise_at_50cm_dBA', 'geometry_fit', '1750')) {
            if (-not $NotebookText.Contains($Invariant)) { Add-Failure "layout notebook lacks invariant: $Invariant" }
        }
    } catch {
        Add-Failure "layout notebook JSON failed: $($_.Exception.Message)"
    }
}

$ManifestPath = Join-Path $RepoRoot 'codex-skills\skills-manifest.json'
if (Test-Path -LiteralPath $ManifestPath) {
    try {
        $Manifest = (Read-Utf8 $ManifestPath) | ConvertFrom-Json
        $Skills = @($Manifest.skills)
        $ExpectedManifest = @{
            'airjet-product-reconstruction' = [pscustomobject]@{ kind='project'; source='codex-skills/airjet-product-reconstruction'; required=@('SKILL.md','agents/openai.yaml','references/evidence-rules.md','references/stage-routing.md','references/windows-operation.md','scripts/audit_project.py') }
            'jupyter-notebook' = [pscustomobject]@{ kind='official'; source='skills/.curated/jupyter-notebook'; required=@('LICENSE.txt','SKILL.md','agents/openai.yaml','assets/experiment-template.ipynb','assets/jupyter-small.svg','assets/jupyter.png','assets/tutorial-template.ipynb','references/experiment-patterns.md','references/notebook-structure.md','references/quality-checklist.md','references/tutorial-patterns.md','scripts/new_notebook.py') }
            'pdf' = [pscustomobject]@{ kind='official'; source='skills/.curated/pdf'; required=@('LICENSE.txt','SKILL.md','agents/openai.yaml','assets/pdf.png') }
        }
        $Names = @($Skills | ForEach-Object { [string]$_.name })
        if ($Manifest.schema_version -ne 1 -or
            $Manifest.official_source.repository -ne 'https://github.com/openai/skills.git' -or
            $Manifest.official_source.commit -ne '49f948faa9258a0c61caceaf225e179651397431' -or
            $Manifest.hash_canonicalization -ne 'UTF-8 text with CRLF and CR normalized to LF' -or
            $Names.Count -ne 3 -or @($Names | Select-Object -Unique).Count -ne 3) {
            Add-Failure 'skills manifest identity/schema/unique-name lock failed'
        }
        foreach ($Skill in $Skills) {
            $Name = [string]$Skill.name
            if (-not $ExpectedManifest.ContainsKey($Name)) {
                Add-Failure "unexpected skill in manifest: $Name"
                continue
            }
            $Expected = $ExpectedManifest[$Name]
            $ActualRequired = @($Skill.required_files | ForEach-Object { [string]$_ })
            if ($Skill.kind -ne $Expected.kind -or $Skill.source -ne $Expected.source -or
                $ActualRequired.Count -ne $Expected.required.Count -or
                @($ActualRequired | Select-Object -Unique).Count -ne $Expected.required.Count -or
                @(Compare-Object ($Expected.required | Sort-Object) ($ActualRequired | Sort-Object)).Count -gt 0) {
                Add-Failure "manifest kind/source/required files changed for $Name"
            }
        }
        $ProjectSkill = @($Skills | Where-Object { $_.name -eq 'airjet-product-reconstruction' })
        if ($ProjectSkill.Count -eq 1) {
            $Entry = Join-Path (Join-Path $RepoRoot $ProjectSkill[0].source) 'SKILL.md'
            $ActualHash = Get-CanonicalTextSha256 $Entry
            if ($ActualHash -ne $ProjectSkill[0].skill_md_sha256) {
                Add-Failure 'project skill hash does not match manifest'
            }
        }
        $MacInstaller = Read-Utf8 (Join-Path $RepoRoot 'install-skills.sh')
        foreach ($Skill in $Skills) {
            if (-not $MacInstaller.Contains([string]$Skill.skill_md_sha256)) {
                Add-Failure "Mac installer lacks locked hash for $($Skill.name)"
            }
            foreach ($Relative in @($Skill.required_files)) {
                if (-not $MacInstaller.Contains([string]$Relative)) {
                    Add-Failure "Mac installer lacks required-file check for $($Skill.name): $Relative"
                }
            }
        }
    } catch {
        Add-Failure "skills manifest audit failed: $($_.Exception.Message)"
    }
}

$ProvenancePath = Join-Path $RepoRoot 'airjet-simulation\evidence\SOURCE_PROVENANCE.md'
if (Test-Path -LiteralPath $ProvenancePath) {
    $ProvenanceText = Read-Utf8 $ProvenancePath
    foreach ($Marker in @(
        '822fbb7e9735a5505734a291083fed7901c1fdfa01cb7de369679e4d41fd19bd',
        '5f7042dfb2af4a9f37f5a26f792d305d0382b59175d1dfb545a21b96135107b1',
        'page 1',
        'Acoustics of AirJet Mini in system measured at 50 cm (dBA)'
    )) {
        if (-not $ProvenanceText.Contains($Marker)) {
            Add-Failure "source provenance lacks marker: $Marker"
        }
    }
}

if ($Failures.Count -gt 0) {
    Write-Host 'FAIL'
    foreach ($Failure in $Failures) { Write-Host "- $Failure" }
    exit 1
}

Write-Host 'PASS'
Write-Host "repo=$RepoRoot"
Write-Host "required_files=$($Required.Count)"
Write-Host "manuals=$($ManualNames.Count)"
Write-Host "csv_files=$($CsvFiles.Count)"
exit 0

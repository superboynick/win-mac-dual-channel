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
    'airjet-simulation\reports\AJM_WIN_ANSYS_CAPABILITY_SMOKE_003_SUMMARY.md',
    'airjet-simulation\reports\AJM_WIN_ANSYS_STUDENT_CLEANUP_2026-07-14.md',
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
    'airjet-simulation\checklists\full_product_stage_gates.md',
    'airjet-simulation\notebooks\airjet-mini-layout-baseline.ipynb',
    'airjet-simulation\notebooks\build_layout_baseline.py',
    'codex-skills\airjet-product-reconstruction\SKILL.md',
    'codex-skills\skills-manifest.json',
    'install-skills.ps1',
    'install-skills.sh',
    'launch-airjet-codex-visible.ps1'
)

foreach ($Relative in $Required) {
    if (-not (Test-Path -LiteralPath (Join-Path $RepoRoot $Relative) -PathType Leaf)) {
        Add-Failure "missing required file: $Relative"
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

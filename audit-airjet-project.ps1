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
    'airjet-simulation\parameters\full_product_parameter_registry.csv',
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
$ActiveFiles = Get-ChildItem -LiteralPath (Join-Path $RepoRoot 'airjet-simulation') -File -Recurse |
    Where-Object { $_.Extension -in @('.md', '.csv') -and -not $ArchivedFullPaths.ContainsKey($_.FullName.ToLowerInvariant()) }
foreach ($File in $ActiveFiles) {
    $Text = Read-Utf8 $File.FullName
    if ($Text.Contains('delivered_airflow_chart_units') -or $Text.Contains($ObsoleteChinese)) {
        Add-Failure "obsolete airflow interpretation in $($File.FullName)"
    }
}

$PerfPath = Join-Path $RepoRoot 'airjet-simulation\evidence\airjet_mini_performance_curve_digitized.csv'
if (Test-Path -LiteralPath $PerfPath) {
    $PerfRows = @(Import-Csv -LiteralPath $PerfPath)
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
    $RegistryRows = @(Import-Csv -LiteralPath $RegistryPath)
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
        if ($ById.ContainsKey($Id) -and $ById[$Id].evidence_class -ne 'I') {
            Add-Failure "$Id must remain an image-digitized I-class target"
        }
    }
    foreach ($Row in $RegistryRows | Where-Object { $_.id -like 'P*' }) {
        if ($Row.evidence_class -ne 'P') { Add-Failure "patent row is not P-class: $($Row.id)" }
    }
    if ($ById.ContainsKey('P011') -and
        ($ById['P011'].status -ne 'patent_lower_bound' -or $ById['P011'].uncertainty_or_range -notlike '*no 60 m/s upper bound*')) {
        Add-Failure 'P011 must preserve a >=30 m/s lower bound and no 60 m/s upper bound'
    }
    if ($ById.ContainsKey('D011') -and $ById['D011'].calibration_target -notlike '*not a known flow operating point*') {
        Add-Failure '1750 Pa must be recorded as pressure capability with unknown corresponding flow'
    }
}

$LedgerPath = Join-Path $RepoRoot 'airjet-simulation\evidence\airjet_reconstruction_ledger.csv'
if (Test-Path -LiteralPath $LedgerPath) {
    $LedgerRows = @(Import-Csv -LiteralPath $LedgerPath)
    foreach ($Row in $LedgerRows) {
        if ($Row.evidence_class -notin @('D', 'P', 'I', 'C', 'U')) {
            Add-Failure "legacy ledger has invalid evidence class: $($Row.id)"
        }
        if ($Row.evidence_class -eq 'P' -and $Row.model_status -like '*locked*') {
            Add-Failure "patent ledger row is incorrectly locked: $($Row.id)"
        }
    }
}

$SelectionPath = Join-Path $RepoRoot 'airjet-simulation\evidence\product_selection_matrix.csv'
if (Test-Path -LiteralPath $SelectionPath) {
    $SelectionRows = @(Import-Csv -LiteralPath $SelectionPath)
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

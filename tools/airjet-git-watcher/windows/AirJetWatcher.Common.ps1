Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$script:ExpectedRemote = 'ssh://git@ssh.github.com:443/superboynick/win-mac-dual-channel.git'
$script:RuntimeStatus = 'ENABLED_AFTER_END_TO_END'
$script:TaskEnvelopeRel = 'airjet-simulation/collaboration/WINDOWS_TASK.env'
$script:OtherTaskEnvelopeRel = 'airjet-simulation/collaboration/MAC_TASK.env'
$script:CriticalPaths = @('.gitattributes', '.gitmodules', 'tools/airjet-git-watcher')
$script:ProductionTrustHashes = @{
    allowed = 'DB1ADA7DBB7472C43CF32405A3C02F755AE5D291F4348E01C35C60C8EB2A79A6'
    mac = '0DCA6F17DECAF03EF17C97EFA69EEDD0A54C173D01AC63D3C8B29821709661A6'
    krl = '39462E5A1E80CC2065599E74BFDBCB903B54DC088AC1D69E1D612EE65B8C8EB7'
}

function Test-AirJetChildPath {
    param([Parameter(Mandatory = $true)][string]$Parent, [Parameter(Mandatory = $true)][string]$Child)
    $prefix = $Parent.TrimEnd('\') + '\'
    return $Child.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)
}

function Get-AirJetCanonicalExistingPath {
    param([Parameter(Mandatory = $true)][string]$Path)
    return [IO.Path]::GetFullPath((Resolve-Path -LiteralPath $Path -ErrorAction Stop).ProviderPath).TrimEnd('\')
}

function Test-AirJetReparsePoint {
    param([Parameter(Mandatory = $true)][string]$Path)
    $item = Get-Item -LiteralPath $Path -Force -ErrorAction Stop
    return (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0)
}

function Write-AirJetAtomicLines {
    param([Parameter(Mandatory = $true)][string]$Path, [Parameter(Mandatory = $true)][string[]]$Lines)
    $directory = Split-Path -Parent $Path
    if (-not (Test-Path -LiteralPath $directory -PathType Container)) {
        [void](New-Item -ItemType Directory -Path $directory -Force)
    }
    $temporary = "$Path.$PID.$([Guid]::NewGuid().ToString('N')).tmp"
    [IO.File]::WriteAllLines($temporary, $Lines, (New-Object Text.UTF8Encoding($false)))
    Move-Item -LiteralPath $temporary -Destination $Path -Force
}

function Get-AirJetStateFields {
    param([Parameter(Mandatory = $true)][string]$Path)
    $result = @{}
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $result }
    if (Test-AirJetReparsePoint -Path $Path) { throw "BLOCKED_STATE_FILE_REPARSE_POINT path=$Path" }
    foreach ($line in [IO.File]::ReadAllLines($Path)) {
        $separator = $line.IndexOf('=')
        if ($separator -lt 1) { throw "BLOCKED_STATE_FILE_MALFORMED path=$Path" }
        $key = $line.Substring(0, $separator)
        if ($result.ContainsKey($key)) { throw "BLOCKED_STATE_FILE_DUPLICATE_FIELD field=$key" }
        $result[$key] = $line.Substring($separator + 1)
    }
    return $result
}

function Assert-AirJetOid {
    param([Parameter(Mandatory = $true)][string]$Oid, [string]$Label = 'commit')
    if ($Oid -notmatch '^[0-9a-f]{40}([0-9a-f]{24})?$') { throw "BLOCKED_INVALID_OID label=$Label" }
}

function Invoke-AirJetGit {
    param(
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [switch]$AllowFailure
    )
    $savedPrompt = $env:GIT_TERMINAL_PROMPT
    $savedAskPass = $env:GIT_ASKPASS
    $savedLfs = $env:GIT_LFS_SKIP_SMUDGE
    $savedPreference = $ErrorActionPreference
    $savedGitEnvironment = @{}
    try {
        $env:GIT_TERMINAL_PROMPT = '0'
        $env:GIT_ASKPASS = 'NUL'
        $env:GIT_LFS_SKIP_SMUDGE = '1'
        # Windows PowerShell promotes a native stderr record to a terminating
        # NativeCommandError when the caller uses Stop. Git writes ordinary
        # fetch progress to stderr, so capture it and decide only by exit code.
        $ErrorActionPreference = 'Continue'
        foreach ($entry in Get-ChildItem Env:) {
            if (($entry.Name -like 'GIT_CONFIG_*') -or ($entry.Name -in @(
                'GIT_EXEC_PATH','GIT_OBJECT_DIRECTORY','GIT_ALTERNATE_OBJECT_DIRECTORIES',
                'GIT_REPLACE_REF_BASE','GIT_COMMON_DIR','GIT_DIR','GIT_WORK_TREE','GIT_INDEX_FILE',
                'GIT_SHALLOW_FILE','GIT_NAMESPACE','GIT_CEILING_DIRECTORIES',
                'GIT_SSH','GIT_SSH_COMMAND','GIT_SSH_VARIANT','SSH_ASKPASS'
            ))) {
                $savedGitEnvironment[$entry.Name] = $entry.Value
                Remove-Item -LiteralPath "Env:$($entry.Name)"
            }
        }
        $env:GIT_SSH_COMMAND = 'C:\Windows\System32\OpenSSH\ssh.exe -o BatchMode=yes -o StrictHostKeyChecking=yes -o ConnectTimeout=15 -p 443'
        $env:GIT_SSH_VARIANT = 'ssh'
        $all = @('--no-replace-objects','-C', $script:RepoRoot) + $Arguments
        $output = @(& $script:GitExe @all 2>&1 | ForEach-Object { $_.ToString() })
        $code = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $savedPreference
        $env:GIT_TERMINAL_PROMPT = $savedPrompt
        $env:GIT_ASKPASS = $savedAskPass
        $env:GIT_LFS_SKIP_SMUDGE = $savedLfs
        Remove-Item -LiteralPath 'Env:GIT_SSH_COMMAND' -ErrorAction SilentlyContinue
        Remove-Item -LiteralPath 'Env:GIT_SSH_VARIANT' -ErrorAction SilentlyContinue
        foreach ($entry in $savedGitEnvironment.GetEnumerator()) { Set-Item -LiteralPath "Env:$($entry.Key)" -Value $entry.Value }
    }
    $text = ($output -join "`n").TrimEnd()
    if (($code -ne 0) -and (-not $AllowFailure)) {
        throw "BLOCKED_GIT_COMMAND exit=$code args=$($Arguments[0]) output=$($text -replace '[\r\n\t]+',' ')"
    }
    return [pscustomobject]@{ ExitCode = $code; Text = $text; Lines = $output }
}

function Assert-AirJetTrustFiles {
    foreach ($entry in @(
        @{ Name = 'allowed'; Path = $script:AllowedSignersFile; Hash = $script:TrustHashes.allowed },
        @{ Name = 'mac'; Path = $script:MacSignersFile; Hash = $script:TrustHashes.mac },
        @{ Name = 'krl'; Path = $script:RevocationKrl; Hash = $script:TrustHashes.krl }
    )) {
        if (-not (Test-Path -LiteralPath $entry.Path -PathType Leaf)) { throw "BLOCKED_TRUST_FILE_MISSING name=$($entry.Name)" }
        if (Test-AirJetReparsePoint -Path $entry.Path) { throw "BLOCKED_TRUST_FILE_REPARSE_POINT name=$($entry.Name)" }
        $actual = (Get-FileHash -LiteralPath $entry.Path -Algorithm SHA256).Hash.ToUpperInvariant()
        if ($actual -ne $entry.Hash) { throw "BLOCKED_TRUST_FILE_HASH name=$($entry.Name) actual=$actual" }
    }
    if (-not (Test-Path -LiteralPath $script:SshKeygenExe -PathType Leaf)) { throw 'BLOCKED_GIT_SSH_KEYGEN_MISSING' }
    if (-not [IO.Path]::IsPathRooted($script:SshKeygenExe)) { throw 'BLOCKED_GIT_SSH_KEYGEN_NOT_ABSOLUTE' }
    if (Test-AirJetReparsePoint -Path $script:SshKeygenExe) { throw 'BLOCKED_GIT_SSH_KEYGEN_REPARSE_POINT' }
}

function Initialize-AirJetWatcherContext {
    param([string]$RepoRoot, [string]$StateRoot)
    $script:TestMode = ($env:AIRJET_WATCHER_TEST_MODE -eq '1')
    if ($script:TestMode) {
        if ([string]::IsNullOrWhiteSpace($StateRoot)) { $StateRoot = $env:AIRJET_WATCHER_STATE_ROOT }
        if ([string]::IsNullOrWhiteSpace($RepoRoot)) { $RepoRoot = $env:AIRJET_REPO_ROOT }
        if ([string]::IsNullOrWhiteSpace($StateRoot) -or [string]::IsNullOrWhiteSpace($RepoRoot)) { throw 'BLOCKED_TEST_ROOT_MISSING' }
    } else {
        $StateRoot = Join-Path $env:LOCALAPPDATA 'AirJetGitWatcher'
        $RepoRoot = 'C:\Users\admin\win-mac-dual-channel'
    }
    if (-not (Test-Path -LiteralPath $RepoRoot -PathType Container)) { throw 'BLOCKED_REPOSITORY_MISSING' }
    [void](New-Item -ItemType Directory -Path $StateRoot -Force)
    $script:RepoRoot = Get-AirJetCanonicalExistingPath -Path $RepoRoot
    $script:StateRoot = Get-AirJetCanonicalExistingPath -Path $StateRoot
    if (($script:RepoRoot -eq $script:StateRoot) -or (Test-AirJetChildPath -Parent $script:RepoRoot -Child $script:StateRoot)) {
        throw 'BLOCKED_STATE_ROOT_INSIDE_REPOSITORY'
    }
    if (Test-AirJetReparsePoint -Path $script:StateRoot) { throw 'BLOCKED_STATE_ROOT_REPARSE_POINT' }

    $script:EventRoot = Join-Path $script:StateRoot 'events'
    $script:LogRoot = Join-Path $script:StateRoot 'logs'
    $script:TrustRoot = Join-Path $script:StateRoot 'trust'
    $script:ProcessedRoot = Join-Path $script:StateRoot 'processed'
    foreach ($directory in @($script:EventRoot, $script:LogRoot, $script:TrustRoot, $script:ProcessedRoot)) {
        [void](New-Item -ItemType Directory -Path $directory -Force)
        $canonical = Get-AirJetCanonicalExistingPath -Path $directory
        if (-not (Test-AirJetChildPath -Parent $script:StateRoot -Child $canonical)) { throw 'BLOCKED_STATE_CHILD_REDIRECTED' }
        if (Test-AirJetReparsePoint -Path $directory) { throw 'BLOCKED_STATE_CHILD_REPARSE_POINT' }
    }
    $script:StatusPath = Join-Path $script:StateRoot 'status.state'
    $script:PendingPath = Join-Path $script:StateRoot 'pending-event.state'
    $script:LockPath = Join-Path $script:StateRoot 'watcher.lock'
    $script:StopPath = Join-Path $script:StateRoot 'stop.request'
    $script:PidPath = Join-Path $script:StateRoot 'watcher.pid'

    if ($script:TestMode) {
        $gitCommand = Get-Command git.exe -ErrorAction SilentlyContinue
        if (-not $gitCommand) { $gitCommand = Get-Command git -ErrorAction Stop }
        $script:GitExe = [IO.Path]::GetFullPath($gitCommand.Source)
    } else {
        $script:GitExe = 'C:\Program Files\Git\cmd\git.exe'
    }
    if (-not (Test-Path -LiteralPath $script:GitExe -PathType Leaf)) { throw 'BLOCKED_GIT_EXE_MISSING' }
    if (-not [IO.Path]::IsPathRooted($script:GitExe)) { throw 'BLOCKED_GIT_EXE_NOT_ABSOLUTE' }
    if (Test-AirJetReparsePoint -Path $script:GitExe) { throw 'BLOCKED_GIT_EXE_REPARSE_POINT' }
    $script:AllowedSignersFile = Join-Path $script:TrustRoot 'allowed_signers'
    $script:MacSignersFile = Join-Path $script:TrustRoot 'mac_task_signers'
    $script:RevocationKrl = Join-Path $script:TrustRoot 'revoked_keys.krl'
    $script:SshKeygenExe = 'C:\Program Files\Git\usr\bin\ssh-keygen.exe'
    $script:TrustHashes = $script:ProductionTrustHashes.Clone()

    if ($script:TestMode) {
        $tempRoot = Get-AirJetCanonicalExistingPath -Path $env:TEMP
        if (-not (Test-AirJetChildPath -Parent $tempRoot -Child $script:RepoRoot)) { throw 'BLOCKED_TEST_REPOSITORY_OUTSIDE_TEMP' }
        if (-not (Test-AirJetChildPath -Parent $tempRoot -Child $script:StateRoot)) { throw 'BLOCKED_TEST_STATE_OUTSIDE_TEMP' }
        if (-not $env:AIRJET_TEST_EXPECTED_REMOTE) { throw 'BLOCKED_TEST_REMOTE_MISSING' }
        $script:ExpectedRemote = $env:AIRJET_TEST_EXPECTED_REMOTE
        foreach ($name in @('AIRJET_TEST_ALLOWED_SIGNERS_FILE','AIRJET_TEST_MAC_SIGNERS_FILE','AIRJET_TEST_KRL_FILE','AIRJET_TEST_SSH_KEYGEN','AIRJET_TEST_ALLOWED_HASH','AIRJET_TEST_MAC_HASH','AIRJET_TEST_KRL_HASH')) {
            if (-not (Get-Item -LiteralPath "Env:$name" -ErrorAction SilentlyContinue)) { throw "BLOCKED_TEST_SETTING_MISSING name=$name" }
        }
        $script:AllowedSignersFile = $env:AIRJET_TEST_ALLOWED_SIGNERS_FILE
        $script:MacSignersFile = $env:AIRJET_TEST_MAC_SIGNERS_FILE
        $script:RevocationKrl = $env:AIRJET_TEST_KRL_FILE
        $script:SshKeygenExe = $env:AIRJET_TEST_SSH_KEYGEN
        $script:TrustHashes = @{
            allowed = $env:AIRJET_TEST_ALLOWED_HASH.ToUpperInvariant()
            mac = $env:AIRJET_TEST_MAC_HASH.ToUpperInvariant()
            krl = $env:AIRJET_TEST_KRL_HASH.ToUpperInvariant()
        }
        foreach ($hash in $script:TrustHashes.Values) {
            if ($hash -notmatch '^[0-9A-F]{64}$') { throw 'BLOCKED_TEST_TRUST_HASH_INVALID' }
        }
    }
    Assert-AirJetTrustFiles
}

function Assert-AirJetRepositoryIdentity {
    $unsafeConfig = Invoke-AirJetGit -Arguments @('config','--name-only','--get-regexp','^(core\.fsmonitor|core\.sshcommand|diff\.external|filter\..*\.(clean|smudge|process)|url\..*\.insteadof)$') -AllowFailure
    $unsafeKeys = @($unsafeConfig.Lines | Where-Object { $_ -and ($_ -notmatch '^filter\.lfs\.(clean|smudge|process)$') })
    if ($unsafeConfig.ExitCode -eq 0 -and $unsafeKeys.Count -gt 0) { throw "BLOCKED_UNSAFE_LOCAL_GIT_CONFIG keys=$(($unsafeKeys -join ',') -replace '[\r\n\t]+',',')" }
    if ($unsafeConfig.ExitCode -notin @(0,1)) { throw 'BLOCKED_LOCAL_GIT_CONFIG_QUERY' }
    $root = (Invoke-AirJetGit -Arguments @('rev-parse','--show-toplevel')).Text
    if ((Get-AirJetCanonicalExistingPath -Path $root) -ne $script:RepoRoot) { throw 'BLOCKED_WRONG_REPOSITORY' }
    if ((Invoke-AirJetGit -Arguments @('symbolic-ref','--quiet','--short','HEAD')).Text -ne 'main') { throw 'BLOCKED_WRONG_BRANCH' }
    if ((Invoke-AirJetGit -Arguments @('rev-parse','--abbrev-ref','--symbolic-full-name','@{u}')).Text -ne 'origin/main') { throw 'BLOCKED_WRONG_UPSTREAM' }
    if ((Invoke-AirJetGit -Arguments @('remote','get-url','origin')).Text -cne $script:ExpectedRemote) { throw 'BLOCKED_WRONG_REMOTE' }
    if ((Invoke-AirJetGit -Arguments @('rev-parse','--is-shallow-repository')).Text -cne 'false') { throw 'BLOCKED_SHALLOW_REPOSITORY' }
}

function Get-AirJetHead {
    $head = (Invoke-AirJetGit -Arguments @('rev-parse','HEAD')).Text.ToLowerInvariant()
    Assert-AirJetOid -Oid $head
    return $head
}

function Assert-AirJetClean {
    $status = (Invoke-AirJetGit -Arguments @('status','--porcelain=v1','--untracked-files=all')).Text
    if ($status) { throw "BLOCKED_DIRTY_WORKTREE output=$($status -replace '[\r\n\t]+',' ')" }
}

function Get-AirJetCounts {
    $text = (Invoke-AirJetGit -Arguments @('rev-list','--left-right','--count','HEAD...origin/main')).Text
    if ($text -notmatch '^(\d+)\s+(\d+)$') { throw 'BLOCKED_COMPARE_INVALID' }
    return [pscustomobject]@{ Ahead = [int]$Matches[1]; Behind = [int]$Matches[2] }
}

function Invoke-AirJetFetch {
    [void](Invoke-AirJetGit -Arguments @('-c','core.hooksPath=NUL','-c','submodule.recurse=false','fetch','--no-tags','--no-recurse-submodules','origin','+refs/heads/main:refs/remotes/origin/main'))
}

function Get-AirJetRemoteOid {
    $result = Invoke-AirJetGit -Arguments @('ls-remote','--exit-code','origin','refs/heads/main')
    if ($result.Text -notmatch '^([0-9a-fA-F]{40}([0-9a-fA-F]{24})?)\s+refs/heads/main$') { throw 'BLOCKED_REMOTE_OID_INVALID' }
    return $Matches[1].ToLowerInvariant()
}

function Test-AirJetCommitSignature {
    param([Parameter(Mandatory = $true)][string]$Commit, [Parameter(Mandatory = $true)][string]$SignersFile, [Parameter(Mandatory = $true)][string]$Label)
    $arguments = @(
        '-c','gpg.format=ssh',
        '-c','gpg.minTrustLevel=fully',
        '-c',"gpg.ssh.program=$script:SshKeygenExe",
        '-c',"gpg.ssh.allowedSignersFile=$SignersFile",
        '-c',"gpg.ssh.revocationFile=$script:RevocationKrl",
        'verify-commit','--raw',$Commit
    )
    $result = Invoke-AirJetGit -Arguments $arguments -AllowFailure
    if ($result.ExitCode -ne 0) {
        throw "BLOCKED_COMMIT_SIGNATURE label=$Label commit=$Commit"
    }
}

function Assert-AirJetIncomingChain {
    param([Parameter(Mandatory = $true)][string]$Old, [Parameter(Mandatory = $true)][string]$Target, [switch]$TaskTip)
    Assert-AirJetOid -Oid $Old -Label old
    Assert-AirJetOid -Oid $Target -Label target
    Assert-AirJetNoCaseCollisions -Commit $Target
    $ancestor = Invoke-AirJetGit -Arguments @('merge-base','--is-ancestor',$Old,$Target) -AllowFailure
    if ($ancestor.ExitCode -ne 0) { throw 'BLOCKED_TARGET_NOT_DESCENDANT' }
    $commits = @((Invoke-AirJetGit -Arguments @('rev-list','--reverse',"$Old..$Target")).Lines | Where-Object { $_ })
    if (($commits.Count -lt 1) -or ($commits.Count -gt 100)) { throw "BLOCKED_INCOMING_COMMIT_COUNT count=$($commits.Count)" }
    $previous = $Old
    foreach ($commit in $commits) {
        $commit = $commit.ToLowerInvariant()
        Assert-AirJetOid -Oid $commit
        $parents = @((Invoke-AirJetGit -Arguments @('rev-list','--parents','-n','1',$commit)).Text -split '\s+')
        if (($parents.Count -ne 2) -or ($parents[1].ToLowerInvariant() -ne $previous)) { throw "BLOCKED_NON_LINEAR_OR_MERGE_COMMIT commit=$commit" }
        Test-AirJetCommitSignature -Commit $commit -SignersFile $script:AllowedSignersFile -Label allowed
        $previous = $commit
    }
    if ($previous -ne $Target) { throw 'BLOCKED_INCOMING_CHAIN_TARGET' }
    if ($TaskTip) { Test-AirJetCommitSignature -Commit $Target -SignersFile $script:MacSignersFile -Label mac_task_tip }
}

function Assert-AirJetNoCaseCollisions {
    param([Parameter(Mandatory = $true)][string]$Commit)
    $seen = @{}
    foreach ($path in (Invoke-AirJetGit -Arguments @('-c','core.quotePath=false','ls-tree','-r','--name-only',$Commit)).Lines) {
        if (-not $path) { continue }
        $folded = $path.ToLowerInvariant()
        if ($seen.ContainsKey($folded) -and ($seen[$folded] -cne $path)) { throw "BLOCKED_CASE_COLLISION first=$($seen[$folded]) second=$path" }
        $seen[$folded] = $path
    }
}

function Assert-AirJetRegularBlob {
    param([Parameter(Mandatory = $true)][string]$Commit, [Parameter(Mandatory = $true)][string]$Path, [Parameter(Mandatory = $true)][string]$Label)
    $tree = (Invoke-AirJetGit -Arguments @('ls-tree',$Commit,'--',$Path)).Text
    if ($tree -notmatch '^100644 blob [0-9a-f]{40}([0-9a-f]{24})?\t(.+)$') { throw "BLOCKED_UNSAFE_OBJECT_TYPE label=$Label" }
    if ($Matches[2] -cne $Path) { throw "BLOCKED_PATH_CASE_MISMATCH label=$Label" }
}

function Test-AirJetSafeRepoPath {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (($Path -cnotmatch '^airjet-simulation/collaboration/instructions/[A-Za-z0-9._/-]+$') -or $Path.Contains('\') -or $Path.Contains('//')) { return $false }
    foreach ($segment in $Path.Split('/')) {
        if (($segment -eq '.') -or ($segment -eq '..') -or (-not $segment) -or $segment.EndsWith('.')) { return $false }
        $base = ($segment -split '\.',2)[0].ToUpperInvariant()
        if (($base -in @('CON','PRN','AUX','NUL')) -or ($base -match '^(COM|LPT)[1-9]$')) { return $false }
    }
    return $true
}

function Get-AirJetTipParent {
    param([Parameter(Mandatory = $true)][string]$Commit)
    $parts = @((Invoke-AirJetGit -Arguments @('rev-list','--parents','-n','1',$Commit)).Text -split '\s+')
    if ($parts.Count -ne 2) { throw 'BLOCKED_TASK_TIP_NOT_LINEAR' }
    return $parts[1].ToLowerInvariant()
}

function Get-AirJetTaskClassification {
    param([Parameter(Mandatory = $true)][string]$Old, [Parameter(Mandatory = $true)][string]$Target, [switch]$WriteEvent)
    $tipParent = Get-AirJetTipParent -Commit $Target
    $otherTaskTouches = @((Invoke-AirJetGit -Arguments @('log','--format=%H',"$Old..$Target",'--',$script:OtherTaskEnvelopeRel)).Lines | Where-Object { $_ })
    if ($otherTaskTouches.Count -gt 0) { throw 'BLOCKED_OTHER_ENDPOINT_TASK_CHANGED path=MAC_TASK.env' }
    $tipChanged = (Invoke-AirJetGit -Arguments @('diff','--no-ext-diff','--name-only',$tipParent,$Target,'--',$script:TaskEnvelopeRel)).Text
    $rangeTouches = @((Invoke-AirJetGit -Arguments @('log','--format=%H',"$Old..$Target",'--',$script:TaskEnvelopeRel)).Lines | Where-Object { $_ })
    if (-not $tipChanged) {
        if ($rangeTouches.Count -gt 0) { throw 'BLOCKED_WINDOWS_TASK_NOT_AT_TARGET_TIP' }
        return [pscustomobject]@{ State='NONE'; Detail='no_windows_task_at_target_tip'; Fields=@{}; EventPath=$null }
    }
    if (($rangeTouches.Count -ne 1) -or ($rangeTouches[0].ToLowerInvariant() -ne $Target)) { throw 'BLOCKED_WINDOWS_TASK_NOT_ONLY_AT_TARGET_TIP' }
    Assert-AirJetNoCaseCollisions -Commit $Target
    Assert-AirJetRegularBlob -Commit $Target -Path $script:TaskEnvelopeRel -Label envelope
    $envelopeSize = [int64](Invoke-AirJetGit -Arguments @('cat-file','-s',"$Target`:$script:TaskEnvelopeRel")).Text
    if (($envelopeSize -lt 1) -or ($envelopeSize -gt 8192)) { throw 'BLOCKED_TASK_ENVELOPE_SIZE' }
    $raw = (Invoke-AirJetGit -Arguments @('show',"$Target`:$script:TaskEnvelopeRel")).Text
    if ($raw.IndexOf([char]0) -ge 0) { throw 'BLOCKED_TASK_ENVELOPE_NUL' }
    $required = @('schema_version','type','source','target','action','task_id','workflow_id','parent_task_id','hop','max_hops','instruction_path')
    $fields = @{}
    foreach ($line in ($raw -split "`n")) {
        $line = $line.TrimEnd("`r")
        if ($line -notmatch '^([a-z_]+)=(.*)$') { throw 'BLOCKED_TASK_ENVELOPE_MALFORMED' }
        $key = $Matches[1]; $value = $Matches[2]
        if ($required -cnotcontains $key) { throw "BLOCKED_TASK_ENVELOPE_UNKNOWN_FIELD field=$key" }
        if ($fields.ContainsKey($key)) { throw "BLOCKED_TASK_ENVELOPE_DUPLICATE_FIELD field=$key" }
        $fields[$key] = $value
    }
    foreach ($key in $required) { if (-not $fields.ContainsKey($key)) { throw "BLOCKED_TASK_ENVELOPE_MISSING_FIELD field=$key" } }
    if ($fields.Count -ne $required.Count) { throw 'BLOCKED_TASK_ENVELOPE_FIELD_COUNT' }
    if ($fields.schema_version -cne '2') { throw 'BLOCKED_TASK_SCHEMA_VERSION' }
    if ($fields.type -cne 'task') { throw 'BLOCKED_TASK_TYPE' }
    if ($fields.source -cne 'mac') { throw 'BLOCKED_TASK_SOURCE' }
    if ($fields.target -cne 'windows') { throw 'BLOCKED_TASK_TARGET' }
    if ($fields.action -cne 'wake_codex') { throw 'BLOCKED_TASK_ACTION' }
    foreach ($key in @('task_id','workflow_id')) { if ($fields[$key] -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$') { throw "BLOCKED_TASK_ID field=$key" } }
    if ($fields.parent_task_id -cne 'NONE') { throw 'BLOCKED_RELAY_NOT_ENABLED parent_task_id' }
    if (($fields.hop -cne '0') -or ($fields.max_hops -cne '0')) { throw 'BLOCKED_RELAY_NOT_ENABLED hop' }
    if (-not (Test-AirJetSafeRepoPath -Path $fields.instruction_path)) { throw 'BLOCKED_TASK_INSTRUCTION_PATH' }
    Assert-AirJetRegularBlob -Commit $Target -Path $fields.instruction_path -Label instruction
    $instructionSize = [int64](Invoke-AirJetGit -Arguments @('cat-file','-s',"$Target`:$($fields.instruction_path)")).Text
    if (($instructionSize -lt 1) -or ($instructionSize -gt 65536)) { throw 'BLOCKED_TASK_INSTRUCTION_SIZE' }
    $instructionText = (Invoke-AirJetGit -Arguments @('show',"$Target`:$($fields.instruction_path)")).Text
    if ($instructionText.IndexOf([char]0) -ge 0) { throw 'BLOCKED_TASK_INSTRUCTION_NUL' }

    $eventPath = Join-Path $script:EventRoot "windows-task-$Target.env"
    if ($WriteEvent) {
        $lines = foreach ($key in $required) { "$key=$($fields[$key])" }
        Write-AirJetAtomicLines -Path $eventPath -Lines $lines
    }
    return [pscustomobject]@{ State='VALID'; Detail="task_id=$($fields.task_id) workflow_id=$($fields.workflow_id)"; Fields=$fields; EventPath=$eventPath }
}

function Test-AirJetProcessedTask {
    param([Parameter(Mandatory = $true)][string]$TaskId)
    if ($TaskId -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$') { throw 'BLOCKED_PROCESSED_TASK_ID' }
    $claim = Join-Path $script:ProcessedRoot "$TaskId.claim"
    if (-not (Test-Path -LiteralPath $claim)) { return $false }
    if (-not (Test-Path -LiteralPath $claim -PathType Leaf)) { throw 'BLOCKED_PROCESSED_CLAIM_NOT_FILE' }
    if (Test-AirJetReparsePoint -Path $claim) { throw 'BLOCKED_PROCESSED_CLAIM_REPARSE_POINT' }
    return $true
}

function Add-AirJetProcessedTask {
    param([Parameter(Mandatory = $true)]$Task, [Parameter(Mandatory = $true)][string]$Commit)
    if ($Task.task_id -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$') { throw 'BLOCKED_PROCESSED_TASK_ID' }
    $claim = Join-Path $script:ProcessedRoot "$($Task.task_id).claim"
    $line = "workflow_id=$($Task.workflow_id)`ntask_id=$($Task.task_id)`ncommit=$Commit`nhop=$($Task.hop)`nphase=CLAIMED`nclaimed_at=$([DateTime]::UtcNow.ToString('o'))`n"
    try {
        $stream = [IO.File]::Open($claim, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
        try {
            $bytes = (New-Object Text.UTF8Encoding($false)).GetBytes($line)
            $stream.Write($bytes, 0, $bytes.Length)
            $stream.Flush($true)
        } finally { $stream.Dispose() }
    } catch [IO.IOException] {
        throw 'BLOCKED_TASK_ALREADY_PROCESSED'
    }
}

function Update-AirJetProcessedTaskPhase {
    param(
        [Parameter(Mandatory = $true)]$Task,
        [Parameter(Mandatory = $true)][string]$Commit,
        [Parameter(Mandatory = $true)][string]$Phase
    )
    $claim = Join-Path $script:ProcessedRoot "$($Task.task_id).claim"
    if (-not (Test-Path -LiteralPath $claim -PathType Leaf)) { throw 'BLOCKED_PROCESSED_CLAIM_MISSING' }
    if (Test-AirJetReparsePoint -Path $claim) { throw 'BLOCKED_PROCESSED_CLAIM_REPARSE_POINT' }
    Write-AirJetAtomicLines -Path $claim -Lines @(
        "workflow_id=$($Task.workflow_id)", "task_id=$($Task.task_id)", "commit=$Commit",
        "hop=$($Task.hop)", "phase=$Phase", "updated_at=$([DateTime]::UtcNow.ToString('o'))"
    )
}

function Test-AirJetCriticalChange {
    param([Parameter(Mandatory = $true)][string]$Old, [Parameter(Mandatory = $true)][string]$Target)
    $changed = (Invoke-AirJetGit -Arguments (@('diff','--no-ext-diff','--name-only',$Old,$Target,'--') + $script:CriticalPaths)).Text
    return [bool]$changed
}

function Write-AirJetPending {
    param(
        [Parameter(Mandatory = $true)][string]$Phase,
        [Parameter(Mandatory = $true)][string]$Old,
        [Parameter(Mandatory = $true)][string]$New,
        [string]$TaskId = ''
    )
    Assert-AirJetOid -Oid $Old -Label old
    Assert-AirJetOid -Oid $New -Label new
    $lines = @(
        'schema_version=2', "phase=$Phase", "created_at=$([DateTime]::UtcNow.ToString('o'))",
        "repo=$script:RepoRoot", "old_commit=$Old", "new_commit=$New"
    )
    if ($TaskId) { $lines += "task_id=$TaskId" }
    Write-AirJetAtomicLines -Path $script:PendingPath -Lines $lines
}

function Read-AirJetPending {
    if (-not (Test-Path -LiteralPath $script:PendingPath -PathType Leaf)) { throw 'BLOCKED_PENDING_MISSING' }
    $pending = Get-AirJetStateFields -Path $script:PendingPath
    foreach ($key in @('schema_version','phase','repo','old_commit','new_commit')) { if (-not $pending.ContainsKey($key)) { throw "BLOCKED_PENDING_FIELD field=$key" } }
    if (($pending.schema_version -cne '2') -or ($pending.repo -cne $script:RepoRoot)) { throw 'BLOCKED_PENDING_IDENTITY' }
    Assert-AirJetOid -Oid $pending.old_commit -Label pending_old
    Assert-AirJetOid -Oid $pending.new_commit -Label pending_new
    if (@('PULL_PENDING','READY_TO_WAKE','PENDING_NO_WAKE','WAKE_REQUESTED','CODEX_STARTED','CODEX_EXITED_0','CODEX_FAILED') -cnotcontains $pending.phase) { throw 'BLOCKED_PENDING_PHASE' }
    return $pending
}

function Write-AirJetStatus {
    param([Parameter(Mandatory = $true)][string]$State, [Parameter(Mandatory = $true)][string]$Detail, [string]$Commit = '')
    $safeDetail = $Detail -replace '[\r\n\t]+',' '
    Write-AirJetAtomicLines -Path $script:StatusPath -Lines @(
        "timestamp=$([DateTime]::UtcNow.ToString('o'))", "state=$State", "detail=$safeDetail",
        "commit=$Commit", "watcher_pid=$PID", "repo=$script:RepoRoot", 'auto_start=false'
    )
}

function Assert-AirJetRetryState {
    param([Parameter(Mandatory = $true)][string]$Old, [Parameter(Mandatory = $true)][string]$New)
    Assert-AirJetRepositoryIdentity
    Assert-AirJetClean
    if ((Get-AirJetHead) -ne $New) { throw 'BLOCKED_PENDING_HEAD_CHANGED' }
    if ((Get-AirJetRemoteOid) -ne $New) { throw 'BLOCKED_PENDING_REMOTE_MOVED' }
    Invoke-AirJetFetch
    Assert-AirJetRepositoryIdentity
    Assert-AirJetClean
    if ((Get-AirJetHead) -ne $New) { throw 'BLOCKED_PENDING_HEAD_CHANGED' }
    if ((Invoke-AirJetGit -Arguments @('rev-parse','origin/main')).Text.ToLowerInvariant() -ne $New) { throw 'BLOCKED_PENDING_REMOTE_MOVED' }
    $taskProbe = Get-AirJetTaskClassification -Old $Old -Target $New
    if ($taskProbe.State -ne 'VALID') { throw 'BLOCKED_PENDING_TASK_REVALIDATION' }
    Assert-AirJetIncomingChain -Old $Old -Target $New -TaskTip
    return Get-AirJetTaskClassification -Old $Old -Target $New -WriteEvent
}

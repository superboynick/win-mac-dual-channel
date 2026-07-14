[CmdletBinding()]
param()

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$WindowsRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\windows'))
$Watcher = Join-Path $WindowsRoot 'Watch-AirJetGit.ps1'
$Manager = Join-Path $WindowsRoot 'Manage-AirJetWatcher.ps1'
$Runner = Join-Path $WindowsRoot 'Run-AwakenedCodex.ps1'
$Installer = Join-Path $WindowsRoot 'Install-AirJetWatcher.ps1'
$Common = Join-Path $WindowsRoot 'AirJetWatcher.Common.ps1'
$PowerShell = (Get-Command powershell.exe -ErrorAction Stop).Source
$Git = (Get-Command git.exe -ErrorAction Stop).Source
$SshKeygen = 'C:\Program Files\Git\usr\bin\ssh-keygen.exe'
if (-not (Test-Path -LiteralPath $SshKeygen -PathType Leaf)) { throw 'Git bundled ssh-keygen is missing' }
$Root = Join-Path $env:TEMP "airjet-windows-watcher-test-$([Guid]::NewGuid().ToString('N'))"
$Trust = Join-Path $Root 'trust'
$PassCount = 0

function Pass([string]$Name) { $script:PassCount++; Write-Output "PASS=$Name" }
function Fail([string]$Name) { throw "FAIL=$Name" }
function Assert-Contains([string]$Name, [string]$Text, [string]$Needle) {
    if ($Text.IndexOf($Needle, [StringComparison]::Ordinal) -lt 0) { Fail "$Name missing=$Needle output=$Text" }
    Pass $Name
}
function Assert-Equal([string]$Name, $Actual, $Expected) {
    if ([string]$Actual -cne [string]$Expected) { Fail "$Name actual=$Actual expected=$Expected" }
    Pass $Name
}
function Git([string]$Repo, [string[]]$Arguments, [switch]$AllowFailure) {
    $savedPreference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        $output = @(& $script:Git -C $Repo @Arguments 2>&1 | ForEach-Object { $_.ToString() })
        $code = $LASTEXITCODE
    } finally { $ErrorActionPreference = $savedPreference }
    if (($code -ne 0) -and (-not $AllowFailure)) { throw "git failed code=$code args=$($Arguments -join ' ') output=$($output -join ' ')" }
    return [pscustomobject]@{ Code=$code; Text=($output -join "`n").Trim(); Lines=$output }
}
function Configure-Identity([string]$Repo) {
    [void](Git $Repo @('config','user.name','AirJet Watcher Test'))
    [void](Git $Repo @('config','user.email','airjet-watcher-test@example.invalid'))
    [void](Git $Repo @('config','gpg.format','ssh'))
    [void](Git $Repo @('config','gpg.ssh.program',$script:SshKeygen))
}
function Set-Signer([string]$Repo, [string]$Key, [bool]$Enabled = $true) {
    [void](Git $Repo @('config','user.signingkey',$Key))
    [void](Git $Repo @('config','commit.gpgsign',$(if ($Enabled) { 'true' } else { 'false' })))
}
function Commit-All([string]$Repo, [string]$Message, [string]$Signer, [bool]$Signed = $true) {
    Set-Signer $Repo $Signer $Signed
    [void](Git $Repo @('add','-A'))
    [void](Git $Repo @('commit','-m',$Message))
    [void](Git $Repo @('push','origin','main'))
    return (Git $Repo @('rev-parse','HEAD')).Text.ToLowerInvariant()
}
function Public-KeyBody([string]$Path) {
    $parts = ([IO.File]::ReadAllText($Path)).Trim() -split '\s+'
    return "$($parts[0]) $($parts[1])"
}
function New-Fixture([string]$Name) {
    $base = Join-Path $script:Root $Name
    $origin = Join-Path $base 'origin.git'
    $seed = Join-Path $base 'seed'
    $writer = Join-Path $base 'writer'
    [void](New-Item -ItemType Directory -Path $base -Force)
    [void](Git $base @('init','--bare',$origin))
    [void](Git $base @('init',$seed))
    Configure-Identity $seed
    [void](Git $seed @('checkout','-b','main'))
    [IO.File]::WriteAllText((Join-Path $seed 'README.fixture'), "baseline`n")
    [void](New-Item -ItemType Directory -Path (Join-Path $seed 'tools\airjet-git-watcher') -Force)
    [IO.File]::WriteAllText((Join-Path $seed 'tools\airjet-git-watcher\fixture.txt'), "baseline`n")
    Set-Signer $seed $script:WindowsKey $true
    [void](Git $seed @('add','-A'))
    [void](Git $seed @('commit','-m','baseline'))
    [void](Git $seed @('remote','add','origin',$origin))
    [void](Git $seed @('push','-u','origin','main'))
    [void](Git $origin @('symbolic-ref','HEAD','refs/heads/main'))
    [void](Git $base @('clone',$origin,$writer))
    Configure-Identity $writer
    return [pscustomobject]@{ Base=$base; Origin=$origin; Seed=$seed; Writer=$writer }
}
function Clone-Case($Fixture, [string]$Name) {
    $path = Join-Path $Fixture.Base $Name
    [void](Git $Fixture.Base @('clone',$Fixture.Origin,$path))
    Configure-Identity $path
    return $path
}
function Write-Task([string]$Repo, [string]$Instruction = 'airjet-simulation/collaboration/instructions/windows-test.md', [string]$TaskId = 'windows-test-task') {
    $taskDir = Join-Path $Repo 'airjet-simulation\collaboration'
    $instructionFull = Join-Path $Repo ($Instruction -replace '/', '\')
    [void](New-Item -ItemType Directory -Path $taskDir -Force)
    if ($Instruction -notmatch '\.\.') {
        [void](New-Item -ItemType Directory -Path (Split-Path -Parent $instructionFull) -Force)
        [IO.File]::WriteAllText($instructionFull, "# signed Windows test instruction`n")
    }
    $lines = @(
        'schema_version=2','type=task','source=mac','target=windows','action=wake_codex',
        "task_id=$TaskId",'workflow_id=windows-test-workflow','parent_task_id=NONE',
        'hop=0','max_hops=0',"instruction_path=$Instruction"
    )
    [IO.File]::WriteAllLines((Join-Path $taskDir 'WINDOWS_TASK.env'), $lines, (New-Object Text.UTF8Encoding($false)))
}
function Set-TestEnvironment($Fixture, [string]$Repo, [string]$State) {
    [void](New-Item -ItemType Directory -Path $State -Force)
    $env:AIRJET_WATCHER_TEST_MODE='1'
    $env:AIRJET_REPO_ROOT=$Repo
    $env:AIRJET_WATCHER_STATE_ROOT=$State
    $env:AIRJET_TEST_EXPECTED_REMOTE=$Fixture.Origin
    $env:AIRJET_TEST_ALLOWED_SIGNERS_FILE=$script:Allowed
    $env:AIRJET_TEST_MAC_SIGNERS_FILE=$script:MacAllowed
    $env:AIRJET_TEST_KRL_FILE=$script:Krl
    $env:AIRJET_TEST_SSH_KEYGEN=$script:SshKeygen
    $env:AIRJET_TEST_ALLOWED_HASH=(Get-FileHash $script:Allowed -Algorithm SHA256).Hash
    $env:AIRJET_TEST_MAC_HASH=(Get-FileHash $script:MacAllowed -Algorithm SHA256).Hash
    $env:AIRJET_TEST_KRL_HASH=(Get-FileHash $script:Krl -Algorithm SHA256).Hash
}
function Run-Watcher($Fixture, [string]$Repo, [string]$State, [string[]]$Extra = @('-Once','-NoWake')) {
    Set-TestEnvironment $Fixture $Repo $State
    $savedPreference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        $output = @(& $script:PowerShell -NoProfile -ExecutionPolicy Bypass -File $script:Watcher @Extra 2>&1 | ForEach-Object { $_.ToString() })
        $code = $LASTEXITCODE
    } finally { $ErrorActionPreference = $savedPreference }
    return [pscustomobject]@{ Code=$code; Text=($output -join "`n") }
}
function Add-IndexSymlink([string]$Repo, [string]$Path, [string]$Target) {
    $temporary = Join-Path $Repo 'symlink-target.fixture'
    [IO.File]::WriteAllText($temporary, $Target)
    $blob = @((Git $Repo @('hash-object','-w',$temporary)).Lines | Where-Object { $_ -match '^[0-9a-f]{40}([0-9a-f]{24})?$' })[-1]
    Remove-Item $temporary
    [void](Git $Repo @('update-index','--add','--cacheinfo',"120000,$blob,$Path"))
}

try {
    [void](New-Item -ItemType Directory -Path $Trust -Force)
    $script:MacKey = Join-Path $Trust 'mac_signing'
    $script:WindowsKey = Join-Path $Trust 'windows_signing'
    $script:WrongKey = Join-Path $Trust 'wrong_signing'
    $script:RevokedKey = Join-Path $Trust 'revoked_fixture'
    foreach ($key in @($script:MacKey,$script:WindowsKey,$script:WrongKey,$script:RevokedKey)) {
        # Windows PowerShell 5 drops a native empty-string argument.  The
        # quoted empty value is decoded by the Git-for-Windows CRT as -N "".
        & $SshKeygen -q -t ed25519 -N '""' -f $key
        if ($LASTEXITCODE -ne 0) { throw "ssh-keygen failed key=$key" }
    }
    $script:Allowed = Join-Path $Trust 'allowed_signers'
    $script:MacAllowed = Join-Path $Trust 'mac_task_signers'
    $script:Krl = Join-Path $Trust 'revoked_keys.krl'
    [IO.File]::WriteAllLines($script:Allowed, @(
        "mac namespaces=`"git`" $(Public-KeyBody "$script:MacKey.pub")",
        "windows namespaces=`"git`" $(Public-KeyBody "$script:WindowsKey.pub")",
        "revoked namespaces=`"git`" $(Public-KeyBody "$script:RevokedKey.pub")"
    ), (New-Object Text.UTF8Encoding($false)))
    [IO.File]::WriteAllText($script:MacAllowed, "mac namespaces=`"git`" $(Public-KeyBody "$script:MacKey.pub")`n", (New-Object Text.UTF8Encoding($false)))
    & $SshKeygen -q -k -f $script:Krl "$script:RevokedKey.pub"
    if ($LASTEXITCODE -ne 0) { throw 'KRL generation failed' }

    foreach ($file in @($Watcher,$Manager,$Runner,$Installer,$Common)) {
        if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { Fail "missing_runtime_file_$file" }
        $tokens=$null; $errors=$null
        [void][Management.Automation.Language.Parser]::ParseFile($file,[ref]$tokens,[ref]$errors)
        if ($errors.Count -ne 0) { Fail "parse_$([IO.Path]::GetFileName($file))_$($errors[0].Message)" }
        Pass "parse_$([IO.Path]::GetFileName($file))"
    }

    $fixture = New-Fixture 'unchanged'
    $case = Clone-Case $fixture 'case'
    $head = (Git $case @('rev-parse','HEAD')).Text
    $result = Run-Watcher $fixture $case (Join-Path $fixture.Base 'state')
    if ($result.Code -ne 0) { Fail "unchanged_output_$($result.Text)" }
    Assert-Equal 'unchanged_exit' $result.Code 0
    Assert-Equal 'unchanged_head' (Git $case @('rev-parse','HEAD')).Text $head

    $fixture = New-Fixture 'shallow'
    $case = Join-Path $fixture.Base 'case'
    $originUrl = 'file:///' + (($fixture.Origin -replace '\\','/').TrimStart('/'))
    [void](Git $fixture.Base @('clone','--depth','1',$originUrl,$case))
    Configure-Identity $case
    [void](Git $case @('remote','set-url','origin',$fixture.Origin))
    $result = Run-Watcher $fixture $case (Join-Path $fixture.Base 'state')
    if ($result.Code -eq 0) { Fail 'shallow_repository_was_accepted' }
    Assert-Contains 'shallow_repository_block' $result.Text 'BLOCKED_SHALLOW_REPOSITORY'

    $fixture = New-Fixture 'ordinary'
    $case = Clone-Case $fixture 'case'
    [IO.File]::WriteAllText((Join-Path $fixture.Writer 'ordinary.txt'), "ordinary`n")
    $target = Commit-All $fixture.Writer 'ordinary signed update' $script:WindowsKey
    $result = Run-Watcher $fixture $case (Join-Path $fixture.Base 'state')
    if ($result.Code -ne 0) { Fail "ordinary_output_$($result.Text)" }
    Assert-Equal 'ordinary_exit' $result.Code 0
    Assert-Equal 'ordinary_fast_forward' (Git $case @('rev-parse','HEAD')).Text.ToLowerInvariant() $target
    Assert-Contains 'ordinary_no_wake' $result.Text 'SYNCED_NO_WINDOWS_TASK='

    $fixture = New-Fixture 'unsigned'
    $case = Clone-Case $fixture 'case'; $old=(Git $case @('rev-parse','HEAD')).Text
    [IO.File]::WriteAllText((Join-Path $fixture.Writer 'unsigned.txt'), "unsigned`n")
    [void](Commit-All $fixture.Writer 'unsigned update' $script:WindowsKey $false)
    $result = Run-Watcher $fixture $case (Join-Path $fixture.Base 'state')
    if ($result.Code -eq 0) { Fail 'unsigned_was_accepted' }
    Assert-Contains 'unsigned_block' $result.Text 'BLOCKED_COMMIT_SIGNATURE'
    Assert-Equal 'unsigned_head_unchanged' (Git $case @('rev-parse','HEAD')).Text $old

    $fixture = New-Fixture 'wrong-signer'
    $case = Clone-Case $fixture 'case'
    [IO.File]::WriteAllText((Join-Path $fixture.Writer 'wrong.txt'), "wrong`n")
    [void](Commit-All $fixture.Writer 'wrong signer update' $script:WrongKey)
    $result = Run-Watcher $fixture $case (Join-Path $fixture.Base 'state')
    if ($result.Code -eq 0) { Fail 'wrong_signer_was_accepted' }
    Assert-Contains 'wrong_signer_block' $result.Text 'BLOCKED_COMMIT_SIGNATURE'

    $fixture = New-Fixture 'revoked-signer'
    $case = Clone-Case $fixture 'case'
    [IO.File]::WriteAllText((Join-Path $fixture.Writer 'revoked.txt'), "revoked`n")
    [void](Commit-All $fixture.Writer 'revoked signer update' $script:RevokedKey)
    $result = Run-Watcher $fixture $case (Join-Path $fixture.Base 'state')
    if ($result.Code -eq 0) { Fail 'revoked_signer_was_accepted' }
    Assert-Contains 'revoked_signer_block' $result.Text 'BLOCKED_COMMIT_SIGNATURE'

    $fixture = New-Fixture 'valid-task'
    $case = Clone-Case $fixture 'case'; Write-Task $fixture.Writer
    $target = Commit-All $fixture.Writer 'valid mac task tip' $script:MacKey
    $state = Join-Path $fixture.Base 'state'
    $env:GIT_CONFIG_COUNT='1'
    $env:GIT_CONFIG_KEY_0='gpg.ssh.allowedSignersFile'
    $env:GIT_CONFIG_VALUE_0=(Join-Path $Trust 'does-not-exist')
    $result = Run-Watcher $fixture $case $state
    Remove-Item Env:GIT_CONFIG_COUNT,Env:GIT_CONFIG_KEY_0,Env:GIT_CONFIG_VALUE_0 -ErrorAction SilentlyContinue
    if ($result.Code -ne 0) { Fail "valid_task_output_$($result.Text)" }
    Assert-Equal 'valid_task_exit' $result.Code 0
    Assert-Contains 'valid_task_pending' ([IO.File]::ReadAllText((Join-Path $state 'pending-event.state'))) 'phase=PENDING_NO_WAKE'
    Assert-Equal 'valid_task_head' (Git $case @('rev-parse','HEAD')).Text.ToLowerInvariant() $target

    $fixture = New-Fixture 'wrong-task-tip'
    $case = Clone-Case $fixture 'case'; Write-Task $fixture.Writer
    [void](Commit-All $fixture.Writer 'task signed by windows' $script:WindowsKey)
    $result = Run-Watcher $fixture $case (Join-Path $fixture.Base 'state')
    if ($result.Code -eq 0) { Fail 'windows_task_tip_signer_was_accepted' }
    Assert-Contains 'mac_only_tip_block' $result.Text 'label=mac_task_tip'

    $fixture = New-Fixture 'relay-disabled'
    $case = Clone-Case $fixture 'case'; Write-Task $fixture.Writer
    $relayPath=Join-Path $fixture.Writer 'airjet-simulation\collaboration\WINDOWS_TASK.env'
    $relayText=[IO.File]::ReadAllText($relayPath).Replace('parent_task_id=NONE','parent_task_id=upstream-task').Replace('hop=0','hop=1').Replace('max_hops=0','max_hops=4')
    [IO.File]::WriteAllText($relayPath,$relayText,(New-Object Text.UTF8Encoding($false)))
    [void](Commit-All $fixture.Writer 'relay is reserved' $script:MacKey)
    $result = Run-Watcher $fixture $case (Join-Path $fixture.Base 'state')
    if ($result.Code -eq 0) { Fail 'relay_task_was_accepted' }
    Assert-Contains 'relay_disabled_block' $result.Text 'BLOCKED_RELAY_NOT_ENABLED'

    $fixture = New-Fixture 'other-endpoint-task'
    $case = Clone-Case $fixture 'case'; $old=(Git $case @('rev-parse','HEAD')).Text
    $otherDir=Join-Path $fixture.Writer 'airjet-simulation\collaboration'; [void](New-Item -ItemType Directory -Path $otherDir -Force)
    [IO.File]::WriteAllText((Join-Path $otherDir 'MAC_TASK.env'), "schema_version=2`ntype=task`nsource=windows`ntarget=mac`n")
    [void](Commit-All $fixture.Writer 'other endpoint task' $script:MacKey)
    $result = Run-Watcher $fixture $case (Join-Path $fixture.Base 'state')
    if ($result.Code -eq 0) { Fail 'other_endpoint_task_was_accepted' }
    Assert-Contains 'other_endpoint_task_block' $result.Text 'BLOCKED_OTHER_ENDPOINT_TASK_CHANGED'
    Assert-Equal 'other_endpoint_before_merge' (Git $case @('rev-parse','HEAD')).Text $old

    $fixture = New-Fixture 'symlink'
    $case = Clone-Case $fixture 'case'; Write-Task $fixture.Writer 'airjet-simulation/collaboration/instructions/symlink.md' 'symlink-task'
    Remove-Item (Join-Path $fixture.Writer 'airjet-simulation\collaboration\instructions\symlink.md')
    Add-IndexSymlink $fixture.Writer 'airjet-simulation/collaboration/instructions/symlink.md' '../../../outside.md'
    Set-Signer $fixture.Writer $script:MacKey $true
    [void](Git $fixture.Writer @('add','airjet-simulation/collaboration/WINDOWS_TASK.env'))
    [void](Git $fixture.Writer @('commit','-m','symlink task'))
    [void](Git $fixture.Writer @('push','origin','main'))
    $result = Run-Watcher $fixture $case (Join-Path $fixture.Base 'state')
    if ($result.Code -eq 0) { Fail 'symlink_instruction_was_accepted' }
    Assert-Contains 'symlink_block' $result.Text 'BLOCKED_UNSAFE_OBJECT_TYPE label=instruction'

    $fixture = New-Fixture 'traversal'
    $case = Clone-Case $fixture 'case'; Write-Task $fixture.Writer 'airjet-simulation/collaboration/instructions/../WINDOWS_TASK.env' 'traversal-task'
    [void](Commit-All $fixture.Writer 'traversal task' $script:MacKey)
    $result = Run-Watcher $fixture $case (Join-Path $fixture.Base 'state')
    if ($result.Code -eq 0) { Fail 'traversal_was_accepted' }
    Assert-Contains 'traversal_block' $result.Text 'BLOCKED_TASK_INSTRUCTION_PATH'

    $fixture = New-Fixture 'dirty'
    $case = Clone-Case $fixture 'case'; [IO.File]::AppendAllText((Join-Path $case 'README.fixture'), "dirty`n")
    $result = Run-Watcher $fixture $case (Join-Path $fixture.Base 'state')
    if ($result.Code -eq 0) { Fail 'dirty_was_accepted' }
    Assert-Contains 'dirty_block' $result.Text 'BLOCKED_DIRTY_WORKTREE'

    $fixture = New-Fixture 'ahead'
    $case = Clone-Case $fixture 'case'; [IO.File]::WriteAllText((Join-Path $case 'ahead.txt'), "ahead`n")
    Set-Signer $case $script:WindowsKey $true; [void](Git $case @('add','ahead.txt')); [void](Git $case @('commit','-m','local ahead'))
    $result = Run-Watcher $fixture $case (Join-Path $fixture.Base 'state')
    if ($result.Code -eq 0) { Fail 'ahead_was_accepted' }
    Assert-Contains 'ahead_block' $result.Text 'BLOCKED_LOCAL_AHEAD_OR_DIVERGED'

    $fixture = New-Fixture 'critical'
    $case = Clone-Case $fixture 'case'; $old=(Git $case @('rev-parse','HEAD')).Text
    [IO.File]::WriteAllText((Join-Path $fixture.Writer 'tools\airjet-git-watcher\fixture.txt'), "changed`n")
    [void](Commit-All $fixture.Writer 'critical update' $script:WindowsKey)
    $result = Run-Watcher $fixture $case (Join-Path $fixture.Base 'state')
    if ($result.Code -eq 0) { Fail 'critical_was_accepted' }
    Assert-Contains 'critical_block' $result.Text 'BLOCKED_CRITICAL_WATCHER_UPDATE'
    Assert-Equal 'critical_before_merge' (Git $case @('rev-parse','HEAD')).Text $old

    $fixture = New-Fixture 'retry'
    $case = Clone-Case $fixture 'case'; Write-Task $fixture.Writer 'airjet-simulation/collaboration/instructions/retry.md' 'retry-task'
    $target = Commit-All $fixture.Writer 'retry task' $script:MacKey; $state=Join-Path $fixture.Base 'state'
    $result = Run-Watcher $fixture $case $state
    Assert-Equal 'retry_setup' $result.Code 0
    $event=Join-Path $state "events\windows-task-$target.env"
    [IO.File]::WriteAllText($event, "type=tampered`n")
    $result = Run-Watcher $fixture $case $state @('-RetryPending','-NoWake')
    Assert-Equal 'retry_exit' $result.Code 0
    Assert-Contains 'retry_rebuilt_event' ([IO.File]::ReadAllText($event)) 'task_id=retry-task'

    $fixture = New-Fixture 'pull-pending-retry'
    $case = Clone-Case $fixture 'case'; $old=(Git $case @('rev-parse','HEAD')).Text.ToLowerInvariant()
    Write-Task $fixture.Writer 'airjet-simulation/collaboration/instructions/pull-retry.md' 'pull-retry-task'
    $target = Commit-All $fixture.Writer 'pull pending retry task' $script:MacKey
    $state=Join-Path $fixture.Base 'state'; [void](New-Item -ItemType Directory -Path $state -Force)
    [IO.File]::WriteAllLines((Join-Path $state 'pending-event.state'), @(
        'schema_version=2','phase=PULL_PENDING',"created_at=$([DateTime]::UtcNow.ToString('o'))",
        "repo=$case","old_commit=$old","new_commit=$target"
    ), (New-Object Text.UTF8Encoding($false)))
    $result = Run-Watcher $fixture $case $state @('-RetryPending','-NoWake')
    Assert-Equal 'pull_pending_retry_exit' $result.Code 0
    Assert-Equal 'pull_pending_retry_head' (Git $case @('rev-parse','HEAD')).Text.ToLowerInvariant() $target
    Assert-Contains 'pull_pending_retry_phase' ([IO.File]::ReadAllText((Join-Path $state 'pending-event.state'))) 'phase=PENDING_NO_WAKE'

    $fixture = New-Fixture 'dedupe'
    $case = Clone-Case $fixture 'case'; Write-Task $fixture.Writer 'airjet-simulation/collaboration/instructions/dedupe.md' 'dedupe-task'
    [void](Commit-All $fixture.Writer 'dedupe task' $script:MacKey); $state=Join-Path $fixture.Base 'state'
    [void](New-Item -ItemType Directory -Path $state -Force)
    [void](New-Item -ItemType Directory -Path (Join-Path $state 'processed') -Force)
    [IO.File]::WriteAllText((Join-Path $state 'processed\dedupe-task.claim'), "task_id=dedupe-task`n")
    $result = Run-Watcher $fixture $case $state
    Assert-Equal 'dedupe_exit' $result.Code 0
    Assert-Contains 'dedupe_no_wake' $result.Text 'SYNCED_TASK_ALREADY_PROCESSED=dedupe-task'
    if (Test-Path (Join-Path $state 'pending-event.state')) { Fail 'dedupe_left_pending' } else { Pass 'dedupe_no_pending' }

    $fixture = New-Fixture 'case-collision'
    $case = Clone-Case $fixture 'case'; Write-Task $fixture.Writer 'airjet-simulation/collaboration/instructions/Foo.md' 'collision-task'
    [void](Git $fixture.Writer @('config','core.ignorecase','false'))
    [void](Git $fixture.Writer @('add','airjet-simulation/collaboration/WINDOWS_TASK.env','airjet-simulation/collaboration/instructions/Foo.md'))
    $blobFile=Join-Path $fixture.Writer 'collision.fixture'; [IO.File]::WriteAllText($blobFile,"other`n")
    $blob=@((Git $fixture.Writer @('hash-object','-w',$blobFile)).Lines | Where-Object { $_ -match '^[0-9a-f]{40}([0-9a-f]{24})?$' })[-1]; Remove-Item $blobFile
    [void](Git $fixture.Writer @('update-index','--add','--cacheinfo',"100644,$blob,airjet-simulation/collaboration/instructions/foo.md"))
    Set-Signer $fixture.Writer $script:MacKey $true
    [void](Git $fixture.Writer @('commit','-m','case collision task')); [void](Git $fixture.Writer @('push','origin','main'))
    $result = Run-Watcher $fixture $case (Join-Path $fixture.Base 'state')
    if ($result.Code -eq 0) { Fail 'case_collision_was_accepted' }
    Assert-Contains 'case_collision_block' $result.Text 'BLOCKED_CASE_COLLISION'

    $savedPreference=$ErrorActionPreference; $ErrorActionPreference='Continue'
    try { $output=@(& $PowerShell -NoProfile -ExecutionPolicy Bypass -File $Manager -Action status 2>&1 | ForEach-Object { $_.ToString() }); $code=$LASTEXITCODE }
    finally { $ErrorActionPreference=$savedPreference }
    if ($code -ne 0) { Fail "manager_status_exit_$code" }
    Assert-Contains 'manager_status_exit' ($output -join "`n") 'RUNTIME_STATUS=ENABLED_AFTER_END_TO_END'

    $savedPreference=$ErrorActionPreference; $ErrorActionPreference='Continue'
    try { $output=@(& $PowerShell -NoProfile -ExecutionPolicy Bypass -File $Manager -Action start 2>&1 | ForEach-Object { $_.ToString() }); $code=$LASTEXITCODE }
    finally { $ErrorActionPreference=$savedPreference }
    if ($code -eq 0) { Fail 'manager_start_guard' }
    Assert-Contains 'manager_start_guard' ($output -join "`n") 'START_RESULT=REFUSED_TEST_MODE'
    $savedPreference=$ErrorActionPreference; $ErrorActionPreference='Continue'
    try { $output=@(& $PowerShell -NoProfile -ExecutionPolicy Bypass -File $Manager -Action retry 2>&1 | ForEach-Object { $_.ToString() }); $code=$LASTEXITCODE }
    finally { $ErrorActionPreference=$savedPreference }
    if ($code -eq 0) { Fail 'manager_retry_guard' }
    Assert-Contains 'manager_retry_guard' ($output -join "`n") 'RETRY_RESULT=REFUSED_TEST_MODE'

    Assert-Contains 'fixed_remote' ([IO.File]::ReadAllText($Common)) 'ssh://git@ssh.github.com:443/superboynick/win-mac-dual-channel.git'
    Assert-Contains 'fixed_allowed_hash' ([IO.File]::ReadAllText($Common)) 'DB1ADA7DBB7472C43CF32405A3C02F755AE5D291F4348E01C35C60C8EB2A79A6'
    Assert-Contains 'fixed_mac_hash' ([IO.File]::ReadAllText($Common)) '0DCA6F17DECAF03EF17C97EFA69EEDD0A54C173D01AC63D3C8B29821709661A6'
    Assert-Contains 'fixed_krl_hash' ([IO.File]::ReadAllText($Common)) '39462E5A1E80CC2065599E74BFDBCB903B54DC088AC1D69E1D612EE65B8C8EB7'
    Assert-Contains 'fixed_git_ssh_keygen' ([IO.File]::ReadAllText($Common)) 'C:\Program Files\Git\usr\bin\ssh-keygen.exe'
    Assert-Contains 'fixed_ssh_variant' ([IO.File]::ReadAllText($Common)) '$env:GIT_SSH_VARIANT = ''ssh'''
    Assert-Contains 'fixed_ssh_command_shell_path' ([IO.File]::ReadAllText($Common)) 'C:/Windows/System32/OpenSSH/ssh.exe'
    Assert-Contains 'fixed_poll_default_10' ([IO.File]::ReadAllText($Watcher)) '[ValidateRange(10, 3600)][int]$PollSeconds = 10'
    Assert-Contains 'runner_sandbox' ([IO.File]::ReadAllText($Runner)) 'exec -C $script:RepoRoot -s workspace-write -c ''approval_policy="never"'''
    Assert-Contains 'runner_test_mode_guard' ([IO.File]::ReadAllText($Runner)) 'BLOCKED_TEST_MODE_CODEX_FORBIDDEN'
    Assert-Contains 'atomic_processed_claim' ([IO.File]::ReadAllText($Common)) '[IO.FileMode]::CreateNew'
    Assert-Contains 'watcher_runtime_guard' ([IO.File]::ReadAllText($Watcher)) 'BLOCKED_RUNTIME_'
    Assert-Contains 'installer_default_no_register' ([IO.File]::ReadAllText($Installer)) 'if ($RegisterAtLogOn)'

    $ExpectedPassCount = 54
    if ($PassCount -ne $ExpectedPassCount) { Fail "pass_count_expected_$ExpectedPassCount`_actual_$PassCount" }
    Write-Output "WINDOWS_CORE_CASES_PASS=$PassCount"
    Write-Output "EXPECTED_PASS_COUNT=$ExpectedPassCount"
    Write-Output 'SIGNED_CHAIN=BEHAVIOR_TESTED'
    Write-Output 'MAC_ONLY_TASK_TIP=BEHAVIOR_TESTED'
    Write-Output 'RETRY_REBUILD=BEHAVIOR_TESTED'
    Write-Output 'RUNTIME_TEST_MODE_GUARD=BEHAVIOR_TESTED'
    Write-Output 'VISIBLE_WAKE=SKIPPED_BY_DESIGN'
    Write-Output 'OVERALL=PASS_CORE_RUNTIME_ENABLED_MANUAL'
} finally {
    foreach ($name in @('AIRJET_WATCHER_TEST_MODE','AIRJET_REPO_ROOT','AIRJET_WATCHER_STATE_ROOT','AIRJET_TEST_EXPECTED_REMOTE','AIRJET_TEST_ALLOWED_SIGNERS_FILE','AIRJET_TEST_MAC_SIGNERS_FILE','AIRJET_TEST_KRL_FILE','AIRJET_TEST_SSH_KEYGEN','AIRJET_TEST_ALLOWED_HASH','AIRJET_TEST_MAC_HASH','AIRJET_TEST_KRL_HASH','GIT_CONFIG_COUNT','GIT_CONFIG_KEY_0','GIT_CONFIG_VALUE_0')) {
        Remove-Item "Env:$name" -ErrorAction SilentlyContinue
    }
    if (Test-Path -LiteralPath $Root) { Remove-Item -LiteralPath $Root -Recurse -Force -ErrorAction SilentlyContinue }
}
exit 0

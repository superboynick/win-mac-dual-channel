$ErrorActionPreference='Stop';$root=Join-Path $env:TEMP ('dual-channel-test-'+[guid]::NewGuid());New-Item $root -ItemType Directory|Out-Null
function ExpectFail([scriptblock]$Test,[string]$Name){$failed=$false;try{& $Test}catch{$failed=$true};if(!$failed){throw "Expected failure: $Name"};Write-Output "PASS: blocked $Name"}
try {
  $main=Join-Path $root main.git;$nas=Join-Path $root nas.git;$work=Join-Path $root work
  git init --bare $main|Out-Null;git init --bare $nas|Out-Null;git init -b main $work|Out-Null
  git -C $work config user.name Test;git -C $work config user.email test@example.invalid
  Set-Content (Join-Path $work seed.txt) seed;git -C $work add .;git -C $work commit -m seed|Out-Null
  git -C $work remote add origin $main;git -C $work remote add nas $nas;git -C $work push origin main|Out-Null;git -C $work push nas main|Out-Null
  & (Join-Path $PSScriptRoot dual-channel.ps1) sync-check -Repo $work
  Add-Content (Join-Path $work seed.txt) next;git -C $work add .;git -C $work commit -m next|Out-Null
  & (Join-Path $PSScriptRoot dual-channel.ps1) push-main -Repo $work
  & (Join-Path $PSScriptRoot dual-channel.ps1) backup-nas -Repo $work
  & (Join-Path $PSScriptRoot dual-channel.ps1) sync-check -Repo $work
  Write-Output 'PASS: equal, local-ahead, main-push, NAS-backup'
  Add-Content (Join-Path $work seed.txt) dirty
  ExpectFail { & (Join-Path $PSScriptRoot dual-channel.ps1) push-main -Repo $work } 'dirty worktree push'
  git -C $work restore seed.txt
  $other=Join-Path $root other;git clone -b main $nas $other|Out-Null;git -C $other config user.name Test;git -C $other config user.email test@example.invalid
  Add-Content (Join-Path $other seed.txt) nas-only;git -C $other add .;git -C $other commit -m nas-only|Out-Null;git -C $other push origin main|Out-Null
  Add-Content (Join-Path $work seed.txt) local-only;git -C $work add .;git -C $work commit -m local-only|Out-Null
  ExpectFail { & (Join-Path $PSScriptRoot dual-channel.ps1) sync-check -Repo $work } 'diverged NAS history'
} finally { Remove-Item $root -Recurse -Force -ErrorAction SilentlyContinue }

[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)][ValidateSet('status','fetch','compare','sync-check','push-main','backup-nas')] [string]$Action,
  [string]$Repo='.', [string]$Config='.dual-channel.json'
)
$ErrorActionPreference='Stop'
function RunGit([string[]]$GitArgs) { & git -C $Repo @GitArgs; if($LASTEXITCODE -ne 0){ throw "git failed: git $($GitArgs -join ' ')" } }
function GitText([string[]]$GitArgs) { $v=& git -C $Repo @GitArgs 2>$null; if($LASTEXITCODE -ne 0){ return $null }; return ($v -join "`n").Trim() }
function RemoteExists([string]$Name) { return [bool](GitText @('remote','get-url',$Name)) }
function RequireClean { if(GitText @('status','--porcelain')){ throw 'Working tree is not clean. Commit or stash manually; no files were changed.' } }
function Ref([string]$Name) { $v=GitText @('rev-parse','--verify',$Name); if(!$v){ throw "Missing ref: $Name" }; return $v }
function Relation([string]$A,[string]$B) {
  $raw=GitText @('rev-list','--left-right','--count',"$A...$B"); if(!$raw){ throw "Cannot compare $A and $B" }
  $n=$raw -split '\s+'; $left=[int]$n[0]; $right=[int]$n[1]
  $state=if($left -eq 0 -and $right -eq 0){'equal'}elseif($left -gt 0 -and $right -eq 0){'ahead'}elseif($left -eq 0 -and $right -gt 0){'behind'}else{'diverged'}
  [pscustomobject]@{A=$A;B=$B;Ahead=$left;Behind=$right;State=$state}
}
if(!(Test-Path $Repo)){ throw "Repository path not found: $Repo" }
RunGit @('rev-parse','--git-dir') | Out-Null
$cfgPath=Join-Path (Resolve-Path $Repo) $Config
$cfg=@{mainRemote='origin';backupRemote='nas';branch=(GitText @('branch','--show-current'))}
if(Test-Path $cfgPath){ $u=Get-Content $cfgPath -Raw|ConvertFrom-Json; if($u.mainRemote){$cfg.mainRemote=$u.mainRemote};if($u.backupRemote){$cfg.backupRemote=$u.backupRemote};if($u.branch){$cfg.branch=$u.branch} }
$main=$cfg.mainRemote;$backup=$cfg.backupRemote;$branch=$cfg.branch
if(!$branch){throw 'Detached HEAD is not supported.'}
if($Action -eq 'status'){ RunGit @('status','--short','--branch'); RunGit @('remote','-v'); exit 0 }
if(!(RemoteExists $main)){throw "Main remote '$main' is not configured."}
if(!(RemoteExists $backup)){throw "Backup remote '$backup' is not configured."}
function FetchBoth { RunGit @('fetch','--prune',$main); RunGit @('fetch','--prune',$backup) }
if($Action -eq 'fetch'){ FetchBoth; exit 0 }
FetchBoth
$local=Ref 'HEAD';$mainRef="$main/$branch";$backupRef="$backup/$branch";Ref $mainRef|Out-Null;Ref $backupRef|Out-Null
$lm=Relation 'HEAD' $mainRef;$lb=Relation 'HEAD' $backupRef;$mb=Relation $mainRef $backupRef
[pscustomobject]@{Branch=$branch;Local=$local;Main=(Ref $mainRef);Backup=(Ref $backupRef);LocalVsMain=$lm.State;LocalVsBackup=$lb.State;MainVsBackup=$mb.State}|Format-List
if($lm.State -eq 'diverged' -or $lb.State -eq 'diverged' -or $mb.State -eq 'diverged'){throw 'Divergence detected. Stopped; choose merge or rebase manually.'}
if($Action -in @('compare','sync-check')){ if($mb.State -ne 'equal'){throw 'Main and backup remotes differ. Stopped for review.'}; exit 0 }
RequireClean
if($Action -eq 'push-main'){
  if($mb.State -ne 'equal'){throw 'Remote channels differ. Refusing main push.'}
  if($lm.State -eq 'behind'){throw 'Local branch is behind main. Pull/reconcile manually.'}
  if($lm.State -eq 'equal'){Write-Output 'Main is already current.';exit 0}
  RunGit @('push',$main,"HEAD:refs/heads/$branch");exit 0
}
if($Action -eq 'backup-nas'){
  if($lm.State -ne 'equal'){throw 'Local HEAD must already be safely present on main before NAS backup.'}
  if($lb.State -eq 'behind'){throw 'Local branch is behind NAS. Reconcile manually.'}
  if($lb.State -eq 'equal'){Write-Output 'NAS is already current.';exit 0}
  RunGit @('push',$backup,"HEAD:refs/heads/$branch");exit 0
}

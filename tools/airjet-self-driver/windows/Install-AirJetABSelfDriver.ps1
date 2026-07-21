[CmdletBinding()]
param([ValidateRange(1,60)][int]$Minutes = 5)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$taskName = 'AirJetABSelfDriver'
$driver = Join-Path $PSScriptRoot 'AirJet-AB-SelfDriver.ps1'
if (-not [Environment]::UserInteractive) { throw 'BLOCKED_NOT_INTERACTIVE_USER' }
if (-not (Test-Path -LiteralPath $driver -PathType Leaf)) { throw 'BLOCKED_DRIVER_MISSING' }

$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-NoProfile -ExecutionPolicy RemoteSigned -File `"$driver`""
$trigger = New-ScheduledTaskTrigger -Once -At ((Get-Date).AddMinutes(1)) -RepetitionInterval (New-TimeSpan -Minutes $Minutes)
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 4)
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force | Out-Null
Start-ScheduledTask -TaskName $taskName
$task = Get-ScheduledTask -TaskName $taskName
Write-Output "SELF_DRIVER_INSTALLED=$($task.TaskName)"
Write-Output "SELF_DRIVER_STATE=$($task.State)"
Write-Output "SELF_DRIVER_INTERVAL_MINUTES=$Minutes"

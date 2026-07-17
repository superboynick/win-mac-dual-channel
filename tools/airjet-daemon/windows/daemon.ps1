# AirJet Windows Daemon — keep alive, monitor git, relay prompts
# Run: powershell -NoProfile -File tools\airjet-daemon\windows\daemon.ps1

$Repo = "C:\Users\admin\win-mac-dual-channel"
$WatcherState = "$Repo\tools\airjet-daemon\watcher-state.json"
$CollabDir = "$Repo\airjet-simulation\collaboration"
$PromptFile = "$env:USERPROFILE\.codex\airjet_prompt.txt"
$PollSec = 10
$WinIP = "192.168.1.50"
$MacIP = "192.168.1.66"

Write-Host "[DAEMON] Starting AirJet Windows daemon (PID $PID)"
Write-Host "[DAEMON] Win IP: $WinIP | Mac IP: $MacIP | Poll: ${PollSec}s"

# Prevent sleep
powercfg /change standby-timeout-ac 0
powercfg /change monitor-timeout-ac 0
$executionState = Add-Type -MemberDefinition '[DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint esFlags);' -Name SystemSleep -Namespace Win32 -PassThru
$executionState::SetThreadExecutionState(0x80000003)  # ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED

$LastCommit = ""
Set-Location $Repo

while ($true) {
    # Fetch latest
    git fetch origin 2>$null
    
    # Check for new commits
    $Current = (git rev-parse origin/main 2>$null)
    
    if ($Current -and $Current -ne $LastCommit) {
        Write-Host "[DAEMON] NEW COMMIT: $Current"
        git pull --ff-only 2>$null
        
        # Check for WINDOWS_TASK
        $WinTask = "$CollabDir\WINDOWS_TASK.env"
        if (Test-Path $WinTask) {
            $instrPath = (Select-String -Path $WinTask -Pattern '^instruction_path=' | Select-Object -First 1).Line -replace 'instruction_path=',''
            if ($instrPath) {
                $instrFile = "$Repo\$instrPath"
                if (Test-Path $instrFile) {
                    Write-Host "[DAEMON] Dispatching WINDOWS_TASK: $instrPath"
                    Copy-Item $instrFile $PromptFile -Force
                    Add-Content $PromptFile ""
                    Add-Content $PromptFile "---"
                    Add-Content $PromptFile "This is an automated task from Mac AirJet peer."
                    Add-Content $PromptFile "Read and execute the instruction above."
                }
            }
        }
        
        $LastCommit = $Current
        
        # Update watcher state
        @{
            win_daemon = $true
            pid = $PID
            last_commit = $Current
            win_ip = $WinIP
            mac_ip = $MacIP
            updated = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
        } | ConvertTo-Json | Set-Content $WatcherState
    }

    # Check for pending prompts from Mac
    if (Test-Path $WatcherState) {
        try {
            $state = Get-Content $WatcherState | ConvertFrom-Json
            if ($state.pending_prompt -eq $true) {
                Write-Host "[DAEMON] Mac has pending prompt"
            }
        } catch {}
    }
    
    Start-Sleep -Seconds $PollSec
}

# AirJet Windows Daemon v2 — tray notifications + git monitoring
$Repo = "C:\Users\admin\win-mac-dual-channel"
$Collab = "$Repo\airjet-simulation\collaboration"
$PromptDir = "$env:USERPROFILE\.codex"
$PromptFile = "$PromptDir\airjet_task.md"
$PollSec = 10

$Host.UI.RawUI.WindowTitle = "🟢 AirJet Daemon"
Write-Host "🟢 AirJet Daemon v2 (PID $PID)"

if (!(Test-Path $PromptDir)) { New-Item -ItemType Directory -Path $PromptDir -Force | Out-Null }

$Last = ""
Set-Location $Repo

while ($true) {
    git fetch origin 2>$null
    $Cur = (git rev-parse origin/main 2>$null)
    
    if ($Cur -and $Cur -ne $Last -and $Last) {
        $Short = $Cur.Substring(0, 10)
        git pull --ff-only 2>$null
        
        # Check WINDOWS_TASK
        $TaskFile = "$Collab\WINDOWS_TASK.env"
        if (Test-Path $TaskFile) {
            $instrLine = Select-String -Path $TaskFile -Pattern '^instruction_path=' | Select-Object -First 1
            if ($instrLine) {
                $instr = $instrLine.Line -replace 'instruction_path=', ''
                $instFile = "$Repo\$instr"
                if (Test-Path $instFile) {
                    "# New task from Mac AirJet peer — read and execute" | Set-Content $PromptFile
                    Get-Content $instFile | Add-Content $PromptFile
                    Write-Host "[$(Get-Date -Format HH:mm)] 📨 TASK: $instr"
                }
            }
        }
        
        $Last = $Cur
    } elseif ($Cur -and !$Last) {
        $Last = $Cur
    }
    
    $Host.UI.RawUI.WindowTitle = "🟢 AirJet — $($Cur.Substring(0,10))"
    
    # Update state
    @{
        win_daemon = $true
        pid = $PID
        last_commit = $Cur
        pending = (Test-Path $PromptFile)
        updated = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    } | ConvertTo-Json | Set-Content "$Repo\tools\airjet-daemon\watcher-state.json"
    
    Start-Sleep -Seconds $PollSec
}

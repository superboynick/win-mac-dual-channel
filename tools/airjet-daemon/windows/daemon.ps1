# AirJet Windows Daemon v3 — git monitor + coupling relay + task dispatch
$Repo = "C:\Users\admin\win-mac-dual-channel"
$Collab = "$Repo\airjet-simulation\collaboration"
$Coupling = "$Repo\airjet-simulation\coupling"
$PromptDir = "$env:USERPROFILE\.codex"
$PromptFile = "$PromptDir\airjet_task.md"
$CoupSignal = "$PromptDir\coupling_signal.txt"
$PollSec = 10
$Host.UI.RawUI.WindowTitle = "🟢 AirJet Daemon v3"

if (!(Test-Path $PromptDir)) { New-Item -ItemType Directory -Path $PromptDir -Force | Out-Null }
$Last = ""
Set-Location $Repo

while ($true) {
    git fetch origin 2>$null
    $Cur = (git rev-parse origin/main 2>$null)
    
    if ($Cur -and $Cur -ne $Last -and $Last) {
        $Short = $Cur.Substring(0, 10)
        $Host.UI.RawUI.WindowTitle = "📨 AirJet — $Short"
        git pull --ff-only 2>$null
        
        # Check WINDOWS_TASK
        $TaskFile = "$Collab\WINDOWS_TASK.env"
        if (Test-Path $TaskFile) {
            $instrLine = Select-String -Path $TaskFile -Pattern '^instruction_path=' | Select-Object -First 1
            if ($instrLine) {
                $instr = $instrLine.Line -replace 'instruction_path=', ''
                $instFile = "$Repo\$instr"
                if (Test-Path $instFile) {
                    "# New task from Mac AirJet peer" | Set-Content $PromptFile
                    Get-Content $instFile | Add-Content $PromptFile
                    Write-Host "[$(Get-Date -Format HH:mm)] 📨 TASK: $instr"
                }
            }
        }
        
        # Check Coupling Status
        $CS = "$Coupling\COUPLING_STATUS.md"
        if (Test-Path $CS) {
            $content = Get-Content $CS -Raw
            if ($content -match "membrane_params\.json.*WRITTEN.*YES") {
                Write-Host "[$(Get-Date -Format HH:mm)] 📡 Coupling: membrane_params ready"
                "# Coupling: membrane_params.json ready for OpenFOAM" | Set-Content $CoupSignal
            }
            if ($content -match "cell_results\.json.*WRITTEN.*YES") {
                Write-Host "[$(Get-Date -Format HH:mm)] 📡 Coupling: cell_results ready"
                "# Coupling: cell_results.json ready for ANSYS validation" | Set-Content $CoupSignal
            }
        }
        
        $Last = $Cur
        $Host.UI.RawUI.WindowTitle = "🟢 AirJet — $Short"
    } elseif ($Cur -and !$Last) {
        $Last = $Cur
        $Host.UI.RawUI.WindowTitle = "🟢 AirJet — $($Cur.Substring(0,10))"
    }
    
    @{win_daemon=$true; pid=$PID; commit=$Cur; pending=(Test-Path $PromptFile); time=(Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")} | ConvertTo-Json | Set-Content "$Repo\tools\airjet-daemon\watcher-state.json"
    Start-Sleep -Seconds $PollSec
}

# coupling-watch.ps1
# Background polling script for Windows.
# Run in a separate PowerShell window:
#   powershell -NoProfile -File coupling-watch.ps1
#
# Polls git every 30 seconds. When coupling data changes,
# writes a signal file that both Codex instances can check.

param(
    [int]$IntervalSeconds = 30
)

$repo = "C:\Users\admin\win-mac-dual-channel"
$signalDir = "$repo\airjet-simulation\coupling"
$statusFile = "$signalDir\COUPLING_STATUS.md"
$signalA = "$signalDir\.signal_codex_a"
$signalB = "$signalDir\.signal_codex_b"
$lastCommit = ""

Write-Host "[coupling-watch] Started. Polling every $IntervalSeconds seconds."
Write-Host "[coupling-watch] Repo: $repo"

while ($true) {
    Set-Location $repo
    
    # Pull silently
    git fetch origin 2>&1 | Out-Null
    $current = git rev-parse origin/main
    
    if ($current -ne $lastCommit -and $lastCommit -ne "") {
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        Write-Host "[$timestamp] New commit detected: $($current.Substring(0,7))"
        
        # Check what changed
        $diff = git diff --name-only $lastCommit $current
        
        if ($diff -match "membrane_params\.json") {
            "CHANGED" | Out-File -FilePath $signalB -NoNewline
            Write-Host "  -> Codex B signal: membrane_params.json updated"
        }
        if ($diff -match "cell_results\.json") {
            "CHANGED" | Out-File -FilePath $signalA -NoNewline
            Write-Host "  -> Codex A signal: cell_results.json updated"
        }
        if ($diff -match "COUPLING_STATUS\.md") {
            "CHANGED" | Out-File -FilePath $signalA -NoNewline
            "CHANGED" | Out-File -FilePath $signalB -NoNewline
            Write-Host "  -> Both signals: COUPLING_STATUS.md updated"
        }
    }
    
    $lastCommit = $current
    Start-Sleep -Seconds $IntervalSeconds
}

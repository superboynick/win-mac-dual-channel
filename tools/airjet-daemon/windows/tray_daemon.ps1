# AirJet Windows System Tray Daemon
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$Repo = "C:\Users\admin\win-mac-dual-channel"
$Collab = "$Repo\airjet-simulation\collaboration"
$PromptFile = "$env:USERPROFILE\.codex\airjet_prompt.txt"
$PollSec = 10
$IconSize = 16

# Create tray icon
$icon = [System.Drawing.Icon]::ExtractAssociatedIcon("$env:SystemRoot\System32\shell32.dll")
$notifyIcon = New-Object System.Windows.Forms.NotifyIcon
$notifyIcon.Icon = $icon
$notifyIcon.Text = "AirJet Daemon — 🟢 Watching"
$notifyIcon.Visible = $true

# Context menu
$contextMenu = New-Object System.Windows.Forms.ContextMenuStrip

$statusItem = New-Object System.Windows.Forms.ToolStripMenuItem
$statusItem.Text = "Status: Watching Git..."
$contextMenu.Items.Add($statusItem) | Out-Null

$separator = New-Object System.Windows.Forms.ToolStripSeparator
$contextMenu.Items.Add($separator) | Out-Null

$openLogItem = New-Object System.Windows.Forms.ToolStripMenuItem
$openLogItem.Text = "Open Git Repo"
$openLogItem.Add_Click({ Start-Process $Repo })
$contextMenu.Items.Add($openLogItem) | Out-Null

$quitItem = New-Object System.Windows.Forms.ToolStripMenuItem
$quitItem.Text = "Quit Daemon"
$quitItem.Add_Click({
    $script:running = $false
    $notifyIcon.Visible = $false
    [System.Windows.Forms.Application]::Exit()
})
$contextMenu.Items.Add($quitItem) | Out-Null

$notifyIcon.ContextMenuStrip = $contextMenu

# Git polling thread
$running = $true
$lastCommit = ""
$pollJob = Start-Job -ScriptBlock {
    param($Repo, $Collab, $PromptFile, $PollSec)
    $last = ""
    while ($true) {
        Set-Location $Repo
        git fetch origin 2>$null
        $current = (git rev-parse origin/main 2>$null)
        if ($current -and $current -ne $last -and $last) {
            git pull --ff-only 2>$null
            $WinTask = "$Collab\WINDOWS_TASK.env"
            if (Test-Path $WinTask) {
                $instr = (Select-String -Path $WinTask -Pattern '^instruction_path=').Line -replace 'instruction_path=',''
                $instFile = "$Repo\$instr"
                if (Test-Path $instFile) {
                    $parent = Split-Path $PromptFile -Parent
                    if (!(Test-Path $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
                    $content = Get-Content $instFile -Raw
                    "# AirJet Task from Mac`n`n$content`n`n---`nRead and execute." | Set-Content $PromptFile
                }
            }
            $last = $current
        } elseif ($current) {
            $last = $current
        }
        Start-Sleep -Seconds $PollSec
    }
} -ArgumentList $Repo, $Collab, $PromptFile, $PollSec

# Update status periodically
$timer = New-Object System.Windows.Forms.Timer
$timer.Interval = 5000
$timer.Add_Tick({
    $jobs = Get-Job -State Running | Where-Object { $_.Name -eq $pollJob.Name }
    if ($jobs) {
        $notifyIcon.Text = "AirJet Daemon — 🟢 Active"
    }
})
$timer.Start()

# Run message loop
[System.Windows.Forms.Application]::Run()
$running = $false
Stop-Job -Job $pollJob
Remove-Job -Job $pollJob

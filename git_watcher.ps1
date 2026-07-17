# Git watcher for Windows-Mac collaboration
# Polls git every 10s, reads new collaboration instructions
$repo = "C:\Users\admin\win-mac-dual-channel"
$collab = "$repo\airjet-simulation\collaboration"
$lastHead = ""

while ($true) {
    try {
        Set-Location $repo
        git fetch origin 2>$null
        $head = git rev-parse HEAD
        $origin = git rev-parse origin/main
        $ahead = (git rev-list --left-right --count HEAD...origin/main 2>$null) -replace '\s+','_'
        
        if ($lastHead -ne $head -or $head -ne $origin) {
            $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            "WATCHER $ts | HEAD=$($head.Substring(0,8)) ORIGIN=$($origin.Substring(0,8)) AHEAD_BEHIND=$ahead"
            
            if ($ahead -match '_0$' -and $head -ne $origin) {
                # Local ahead, push
                git push origin main 2>$null
                "WATCHER: pushed to origin"
            } elseif ($ahead -match '^0_' -and $head -ne $origin) {
                # Remote ahead, pull
                git pull --ff-only 2>$null
                $newHead = git rev-parse HEAD
                "WATCHER: pulled origin/main -> $($newHead.Substring(0,8))"
                
                # Check for new collaboration instructions
                if (Test-Path $collab) {
                    $newFiles = Get-ChildItem $collab -Recurse -File | Where-Object { $_.LastWriteTime -gt (Get-Date).AddMinutes(-5) }
                    foreach ($f in $newFiles) {
                        "WATCHER: new collab file: $($f.Name) ($($f.Length) bytes)"
                    }
                }
            }
            
            $lastHead = $head
        }
    } catch {}
    
    Start-Sleep -Seconds 10
}

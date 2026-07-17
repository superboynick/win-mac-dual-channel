#!/bin/bash
# Install AirJet daemon as launchd service (auto-start on login)
PLIST="$HOME/Library/LaunchAgents/com.airjet.daemon.plist"
cat > "$PLIST" << PLISTXML
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key><string>com.airjet.daemon</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/sh</string>
        <string>$HOME/win-mac-dual-channel/tools/airjet-daemon/mac/daemon.sh</string>
    </array>
    <key>RunAtLoad</key><true/>
    <key>KeepAlive</key><true/>
    <key>WorkingDirectory</key><string>$HOME/win-mac-dual-channel</string>
    <key>StandardOutPath</key><string>$HOME/Library/Logs/airjet-daemon.log</string>
    <key>StandardErrorPath</key><string>$HOME/Library/Logs/airjet-daemon.err</string>
</dict>
</plist>
PLISTXML
launchctl load "$PLIST" 2>/dev/null
echo "AirJet daemon installed. To start: launchctl start com.airjet.daemon"
echo "To stop: launchctl unload $PLIST"
echo "Logs: ~/Library/Logs/airjet-daemon.log"

#!/bin/bash
# AirJet daemon: install for auto-start on boot/login

SCRIPT="$HOME/win-mac-dual-channel/tools/airjet-daemon/mac/daemon.sh"

# Method 1: launchd agent (runs on login)
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
        <string>$SCRIPT</string>
    </array>
    <key>RunAtLoad</key><true/>
    <key>KeepAlive</key><true/>
    <key>WorkingDirectory</key><string>$HOME/win-mac-dual-channel</string>
    <key>StandardOutPath</key><string>$HOME/Library/Logs/airjet-daemon.log</string>
    <key>StandardErrorPath</key><string>$HOME/Library/Logs/airjet-daemon.err</string>
</dict>
</plist>
PLISTXML

# Method 2: Login Item (System Preferences > Users > Login Items)
osascript -e "tell application \"System Events\" to make login item at end with properties {path:\"$SCRIPT\", hidden:true}" 2>/dev/null

launchctl unload "$PLIST" 2>/dev/null
launchctl load "$PLIST" 2>/dev/null
echo "✅ AirJet daemon installed. Will auto-start on boot/login."
echo "   Logs: ~/Library/Logs/airjet-daemon.log"
echo "   Manual start: sh $SCRIPT &"

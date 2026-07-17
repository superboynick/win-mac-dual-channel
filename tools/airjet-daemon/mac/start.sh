#!/bin/bash
# Start AirJet daemon alongside Codex CLI
DIR="$(cd "$(dirname "$0")" && pwd)"
python3 "$DIR/menubar_daemon.py" &
echo "AirJet daemon started (PID $!) — 🟢 in menu bar"
echo "Install menu bar dependency: pip3 install rumps"
echo "Without rumps: daemon runs in terminal"

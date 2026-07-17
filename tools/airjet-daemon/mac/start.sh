#!/bin/bash
nohup sh "$(dirname "$0")/daemon.sh" > /dev/null 2>&1 &
echo "Daemon started (PID $!) — auto-starts on next boot if installed via install.sh"

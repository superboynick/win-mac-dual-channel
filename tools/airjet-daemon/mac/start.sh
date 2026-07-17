#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"
echo "Starting AirJet Daemon in new terminal..."
osascript -e "tell app \"Terminal\" to do script \"sh '$DIR/daemon.sh'\"" 2>/dev/null || sh "$DIR/daemon.sh"

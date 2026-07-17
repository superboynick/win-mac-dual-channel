#!/bin/bash
# AirJet Mac Daemon v2 — status in Terminal title + OS notifications
REPO="$HOME/win-mac-dual-channel"
COLLAB="$REPO/airjet-simulation/collaboration"
PROMPT_DIR="$HOME/.codex"
PROMPT_FILE="$PROMPT_DIR/airjet_task.md"
POLL=10

echo "🟢 AirJet Daemon v2 (PID $$)"
printf "\033]0;🟢 AirJet Daemon\007"  # Set terminal title

mkdir -p "$PROMPT_DIR"
LAST=""

while true; do
  cd "$REPO"
  git fetch origin 2>/dev/null
  CUR=$(git rev-parse origin/main 2>/dev/null)
  
  if [ -n "$CUR" ] && [ "$CUR" != "$LAST" ] && [ -n "$LAST" ]; then
    SHORT="${CUR:0:10}"
    printf "\033]0;📨 AirJet — $SHORT\007"
    git pull --ff-only 2>/dev/null
    
    # Check MAC_TASK
    TASK="$COLLAB/MAC_TASK.env"
    if [ -f "$TASK" ]; then
      INSTR=$(grep "^instruction_path=" "$TASK" 2>/dev/null | cut -d= -f2)
      if [ -n "$INSTR" ] && [ -f "$REPO/$INSTR" ]; then
        cp "$REPO/$INSTR" "$PROMPT_FILE"
        echo "# New task from Windows AirJet peer — read and execute" > "$PROMPT_FILE.tmp"
        cat "$REPO/$INSTR" >> "$PROMPT_FILE.tmp"
        mv "$PROMPT_FILE.tmp" "$PROMPT_FILE"
        echo "[$(date +%H:%M)] 📨 TASK: $INSTR"
        osascript -e "display notification \"New AirJet task from Windows\" with title \"AirJet Daemon\" subtitle \"$SHORT\"" 2>/dev/null
        afplay /System/Library/Sounds/Glass.aiff 2>/dev/null &
      fi
    fi
    
    # Check coupling status
    COUP="$REPO/airjet-simulation/coupling/COUPLING_STATUS.md"
    if [ -f "$COUP" ]; then
      echo "[$(date +%H:%M)] 📡 Coupling status updated"
    fi
    
    LAST="$CUR"
    printf "\033]0;🟢 AirJet — $SHORT\007"
  elif [ -n "$CUR" ] && [ -z "$LAST" ]; then
    LAST="$CUR"
    printf "\033]0;🟢 AirJet — ${CUR:0:10}\007"
  fi
  
  # Update watcher state
  cat > "$REPO/tools/airjet-daemon/watcher-state.json" << STATE
{"mac_daemon":true,"pid":$$,"last_commit":"$CUR","pending":"$([ -f "$PROMPT_FILE" ] && echo true || echo false)","updated":"$(date -u +%Y-%m-%dT%H:%M:%SZ)"}
STATE
  
  sleep $POLL
done

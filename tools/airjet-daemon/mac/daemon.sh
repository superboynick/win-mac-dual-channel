#!/bin/bash
# AirJet Mac Daemon — keep alive, monitor git, relay prompts
# Run: sh tools/airjet-daemon/mac/daemon.sh

REPO="/Users/zhangjianxiao/win-mac-dual-channel"
WATCHER_STATE="$REPO/tools/airjet-daemon/watcher-state.json"
COLLAB_DIR="$REPO/airjet-simulation/collaboration"
PROMPT_FILE="/Users/zhangjianxiao/.codex/airjet_prompt.txt"
POLL_SEC=10
MAC_IP=$(ipconfig getifaddr en0 2>/dev/null || echo "127.0.0.1")
WIN_IP="192.168.1.50"

echo "[DAEMON] Starting AirJet Mac daemon (PID $$)"
echo "[DAEMON] Mac IP: $MAC_IP | Win IP: $WIN_IP | Poll: ${POLL_SEC}s"

# Prevent sleep
caffeinate -i -d -m -s $$ 2>/dev/null &
echo "[DAEMON] Caffeinate PID: $!"

LAST_COMMIT=""
cd "$REPO"

while true; do
  # Fetch latest
  git fetch origin 2>/dev/null
  CURRENT=$(git rev-parse origin/main 2>/dev/null)
  
  # Check for new commits
  if [ -n "$CURRENT" ] && [ "$CURRENT" != "$LAST_COMMIT" ]; then
    echo "[DAEMON] NEW COMMIT: ${CURRENT:0:12}"
    
    # Check for MAC_TASK
    MAC_TASK="$COLLAB_DIR/MAC_TASK.env"
    if [ -f "$MAC_TASK" ]; then
      git checkout origin/main -- "$MAC_TASK" 2>/dev/null
      INSTR=$(grep "^instruction_path=" "$MAC_TASK" 2>/dev/null | cut -d= -f2)
      if [ -n "$INSTR" ]; then
        INSTR_FILE="$REPO/$INSTR"
        git checkout origin/main -- "$INSTR_FILE" 2>/dev/null
        if [ -f "$INSTR_FILE" ]; then
          # Write prompt for Codex to pick up
          echo "[DAEMON] Dispatching MAC_TASK: $INSTR"
          cp "$INSTR_FILE" "$PROMPT_FILE"
          echo "" >> "$PROMPT_FILE"
          echo "---" >> "$PROMPT_FILE"
          echo "This is an automated task from Windows AirJet peer." >> "$PROMPT_FILE"
          echo "Read and execute the instruction above." >> "$PROMPT_FILE"
        fi
      fi
    fi
    
    LAST_COMMIT="$CURRENT"
    
    # Update watcher state
    cat > "$WATCHER_STATE" << STATE
{"mac_daemon":true,"pid":$$,"last_commit":"$CURRENT","mac_ip":"$MAC_IP","win_ip":"$WIN_IP","updated":"$(date -u +%Y-%m-%dT%H:%M:%SZ)"}
STATE
  fi
  
  # Check for incoming prompts from Windows (via shared state file)
  WIN_STATE=$(git show origin/main:tools/airjet-daemon/watcher-state.json 2>/dev/null)
  if [ -n "$WIN_STATE" ]; then
    WIN_PENDING=$(echo "$WIN_STATE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('pending_prompt','false'))" 2>/dev/null)
    if [ "$WIN_PENDING" = "true" ]; then
      echo "[DAEMON] Windows has pending prompt — checking"
      WIN_PROMPT="$COLLAB_DIR/instructions/latest-win-prompt.md"
      git checkout origin/main -- "$WIN_PROMPT" 2>/dev/null
      if [ -f "$WIN_PROMPT" ]; then
        cp "$WIN_PROMPT" "$PROMPT_FILE"
      fi
    fi
  fi
  
  sleep $POLL_SEC
done

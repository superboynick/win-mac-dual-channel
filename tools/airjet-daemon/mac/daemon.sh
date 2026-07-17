#!/bin/bash
# AirJet Mac Daemon v3 — git monitor + coupling relay + task dispatch
REPO="$HOME/win-mac-dual-channel"
COLLAB="$REPO/airjet-simulation/collaboration"
COUPLING="$REPO/airjet-simulation/coupling"
PROMPT_DIR="$HOME/.codex"
PROMPT_FILE="$PROMPT_DIR/airjet_task.md"
COUP_SIGNAL="$PROMPT_DIR/coupling_signal.txt"
POLL=10

echo "🟢 AirJet Daemon v3 (PID $$)"
printf "\033]0;🟢 AirJet Daemon\007"
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
    
    # 1. Check MAC_TASK
    TASK="$COLLAB/MAC_TASK.env"
    if [ -f "$TASK" ]; then
      INSTR=$(grep "^instruction_path=" "$TASK" 2>/dev/null | cut -d= -f2)
      if [ -n "$INSTR" ] && [ -f "$REPO/$INSTR" ]; then
        echo "# New task from Windows AirJet peer" > "$PROMPT_FILE"
        cat "$REPO/$INSTR" >> "$PROMPT_FILE"
        echo "[$(date +%H:%M)] 📨 TASK: $INSTR"
        osascript -e "display notification \"New AirJet task\" with title \"AirJet\" subtitle \"$SHORT\"" 2>/dev/null
      fi
    fi
    
    # 2. Check Coupling Status
    CS="$COUPLING/COUPLING_STATUS.md"
    if [ -f "$CS" ]; then
      A_DONE=$(grep "Codex A.*ANSYS_DONE" "$CS" 2>/dev/null | grep -c "YES")
      B_DONE=$(grep "Codex B.*OPENFOAM_DONE" "$CS" 2>/dev/null | grep -c "YES")
      MEMBRANE=$(grep "membrane_params.json.*WRITTEN" "$CS" 2>/dev/null | grep -c "YES")
      CELL=$(grep "cell_results.json.*WRITTEN" "$CS" 2>/dev/null | grep -c "YES")
      
      if [ "$MEMBRANE" -gt 0 ]; then
        echo "[$(date +%H:%M)] 📡 Coupling: membrane_params ready → OpenFOAM can start"
        echo "# Coupling signal: membrane_params.json is ready" > "$COUP_SIGNAL"
        echo "Read $COUPLING/membrane_params_schema.json for the interface." >> "$COUP_SIGNAL"
      fi
      if [ "$CELL" -gt 0 ]; then
        echo "[$(date +%H:%M)] 📡 Coupling: cell_results ready → ANSYS can validate"
        echo "# Coupling signal: cell_results.json is ready" > "$COUP_SIGNAL"
        echo "Read $COUPLING/cell_results_schema.json for the interface." >> "$COUP_SIGNAL"
      fi
    fi
    
    LAST="$CUR"
    printf "\033]0;🟢 AirJet — $SHORT\007"
  elif [ -n "$CUR" ] && [ -z "$LAST" ]; then
    LAST="$CUR"
    printf "\033]0;🟢 AirJet — ${CUR:0:10}\007"
  fi
  
  # Update watcher state
  PENDING=$([ -f "$PROMPT_FILE" ] && echo true || echo false)
  cat > "$REPO/tools/airjet-daemon/watcher-state.json" << STATE
{"mac_daemon":true,"pid":$$,"commit":"$CUR","pending":$PENDING,"time":"$(date -u +%Y-%m-%dT%H:%M:%SZ)"}
STATE
  
  sleep $POLL
done

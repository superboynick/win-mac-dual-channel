#!/bin/bash
# Continuous work loop for AirJet project
# Polls git every 15s, responds to Windows commits

REPO="/Users/zhangjianxiao/win-mac-dual-channel"
LAST_COMMIT=$(git -C "$REPO" rev-parse HEAD 2>/dev/null)
echo "AIRJET_CONTINUOUS_START commit=$LAST_COMMIT"

while true; do
  sleep 15
  git -C "$REPO" fetch origin 2>/dev/null
  NEW_COMMIT=$(git -C "$REPO" rev-parse origin/main 2>/dev/null)
  
  if [ "$NEW_COMMIT" != "$LAST_COMMIT" ] && [ -n "$NEW_COMMIT" ]; then
    echo "=== NEW WINDOWS COMMIT: $NEW_COMMIT ==="
    git -C "$REPO" pull --ff-only origin main 2>&1 || git -C "$REPO" merge --no-ff origin/main 2>&1
    
    # Check for task receipts
    RECEIPT_DIR="$REPO/airjet-simulation/collaboration/receipts"
    if [ -d "$RECEIPT_DIR" ]; then
      for f in $(ls -t "$RECEIPT_DIR"/*.env 2>/dev/null); do
        if [ "$f" -nt "/tmp/airjet_last_check" ]; then
          echo "NEW_RECEIPT: $f"
          cat "$f"
        fi
      done
    fi
    
    # Check for WINDOWS_TASK.env (if Windows has a task for Mac)
    TASK_FILE="$REPO/airjet-simulation/collaboration/MAC_TASK.env"
    if [ -f "$TASK_FILE" ] && [ "$TASK_FILE" -nt "/tmp/airjet_last_check" ]; then
      echo "NEW_MAC_TASK:"
      cat "$TASK_FILE"
    fi
    
    touch /tmp/airjet_last_check
    LAST_COMMIT="$NEW_COMMIT"
  fi
done

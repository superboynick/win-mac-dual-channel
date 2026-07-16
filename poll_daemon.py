#!/usr/bin/env python3
"""Continuous Git poller for AirJet Mac-Windows collaboration."""
import subprocess, time, os, sys
from datetime import datetime

REPO = "/Users/zhangjianxiao/win-mac-dual-channel"
LOG = "/tmp/airjet_poll_daemon.log"

def log(msg):
    with open(LOG, "a") as f:
        f.write(f"[{datetime.now().isoformat()}] {msg}\n")

def git(*args):
    return subprocess.check_output(["git", "-C", REPO] + list(args), text=True).strip()

log("DAEMON_STARTED")
last = git("rev-parse", "HEAD")
log(f"INITIAL_COMMIT={last[:12]}")

iteration = 0
while True:
    iteration += 1
    time.sleep(15)
    try:
        git("fetch", "origin")
        new = git("rev-parse", "origin/main")
        if new != last:
            log(f"NEW_COMMIT_DETECTED: {new[:12]} (was {last[:12]})")
            # Pull
            try:
                git("pull", "--ff-only", "origin", "main")
            except:
                git("merge", "--no-ff", "origin/main", "-m", "auto-merge from daemon")
            # Check for task files
            task = f"{REPO}/airjet-simulation/collaboration/MAC_TASK.env"
            if os.path.exists(task):
                with open(task) as f:
                    log(f"MAC_TASK: {f.read()[:200]}")
            receipt_dir = f"{REPO}/airjet-simulation/collaboration/receipts"
            if os.path.exists(receipt_dir):
                for fn in sorted(os.listdir(receipt_dir)):
                    if fn.endswith(".env"):
                        log(f"RECEIPT: {fn}")
            last = new
        if iteration % 60 == 0:  # Every 15 minutes
            log(f"HEARTBEAT iteration={iteration} commit={last[:12]}")
    except Exception as e:
        log(f"ERROR: {e}")

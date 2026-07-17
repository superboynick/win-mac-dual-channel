#!/usr/bin/env python3
"""AirJet Mac Menu Bar Daemon — runs alongside Codex CLI, sits in menu bar."""
import subprocess, sys, json, time, threading, os
from pathlib import Path

REPO = Path.home() / "win-mac-dual-channel"
COLLAB = REPO / "airjet-simulation/collaboration"
PROMPT_FILE = Path.home() / ".codex" / "airjet_prompt.txt"
POLL_SEC = 10

class AirJetDaemon:
    def __init__(self):
        self.running = True
        self.last_commit = ""
        self.pending = False
        self.icon_state = "🟢"
        
    def git_poll(self):
        while self.running:
            try:
                subprocess.run(["git", "-C", str(REPO), "fetch", "origin"], 
                             capture_output=True, timeout=15)
                current = subprocess.run(["git", "-C", str(REPO), "rev-parse", "origin/main"],
                              capture_output=True, text=True, timeout=5).stdout.strip()
                
                if current and current != self.last_commit and self.last_commit:
                    self.last_commit = current
                    self.pending = True
                    self.dispatch_task()
                    subprocess.run(["git", "-C", str(REPO), "pull", "--ff-only"],
                                 capture_output=True, timeout=10)
                elif current:
                    self.last_commit = current
                    self.pending = False
            except:
                pass
            time.sleep(POLL_SEC)
    
    def dispatch_task(self):
        """Check for MAC_TASK and write to Codex prompt file."""
        mac_task = COLLAB / "MAC_TASK.env"
        if mac_task.exists():
            instr = {}
            for line in mac_task.read_text().splitlines():
                if "=" in line:
                    k, v = line.split("=", 1)
                    instr[k.strip()] = v.strip()
            path = instr.get("instruction_path", "")
            inst_file = REPO / path
            if inst_file.exists():
                PROMPT_FILE.parent.mkdir(parents=True, exist_ok=True)
                prompt = f"# AirJet Task from Windows\n\n{inst_file.read_text()}\n\n---\nRead and execute."
                PROMPT_FILE.write_text(prompt)

def run():
    daemon = AirJetDaemon()
    
    # Try menu bar icon first
    try:
        import rumps
        class AirJetApp(rumps.App):
            def __init__(self):
                super().__init__("AirJet", title="🔄")
                self.daemon = daemon
                self.timer = rumps.Timer(self.update_status, 5)
                self.timer.start()
                
            def update_status(self, _):
                if self.daemon.pending:
                    self.title = "📨"
                else:
                    self.title = "🟢"
                    
            @rumps.clicked("Status")
            def show_status(self, _):
                commit = self.daemon.last_commit[:12] if self.daemon.last_commit else "unknown"
                pending = "YES" if self.daemon.pending else "no"
                rumps.alert(f"AirJet Daemon\nCommit: {commit}\nPending: {pending}")
                
            @rumps.clicked("Quit")
            def quit_app(self, _):
                self.daemon.running = False
                rumps.quit_application()
        
        threading.Thread(target=daemon.git_poll, daemon=True).start()
        AirJetApp().run()
    except ImportError:
        # Fallback: terminal mode
        print("🟢 AirJet Daemon — Watching Git (menu bar requires: pip3 install rumps)")
        print("   Press Ctrl+C to stop")
        threading.Thread(target=daemon.git_poll, daemon=True).start()
        try:
            while daemon.running:
                time.sleep(5)
                if daemon.pending:
                    print(f"📨 Task pending — commit {daemon.last_commit[:12]}")
        except KeyboardInterrupt:
            daemon.running = False
            print("👋 Daemon stopped")

if __name__ == "__main__":
    run()

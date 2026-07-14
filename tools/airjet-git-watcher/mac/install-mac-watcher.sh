#!/bin/sh
set -eu

ACTION=${1:-status}
[ "$#" -eq 0 ] || shift
POLL_SECONDS=180
while [ "$#" -gt 0 ]; do
  case "$1" in
    --poll-seconds)
      [ "$#" -ge 2 ] || { printf '%s\n' 'missing value for --poll-seconds' >&2; exit 2; }
      POLL_SECONDS=$2
      shift 2
      ;;
    *) printf 'unknown argument: %s\n' "$1" >&2; exit 2 ;;
  esac
done
case "$POLL_SECONDS" in ''|*[!0-9]*) printf '%s\n' 'poll seconds must be an integer' >&2; exit 2 ;; esac
[ "$POLL_SECONDS" -ge 30 ] && [ "$POLL_SECONDS" -le 3600 ] || {
  printf '%s\n' 'poll seconds must be between 30 and 3600' >&2
  exit 2
}

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
WATCHER=$SCRIPT_DIR/watch-airjet-git.sh
MANAGER=$SCRIPT_DIR/manage-airjet-watcher.sh
LABEL=com.airjet.git-watcher
DOMAIN=gui/$(id -u)
PLIST=$HOME/Library/LaunchAgents/$LABEL.plist
LOG_DIR=$HOME/Library/Logs/AirJetGitWatcher
STDOUT_LOG=$LOG_DIR/launchd.stdout.log
STDERR_LOG=$LOG_DIR/launchd.stderr.log

assert_visible_gui() {
  [ "$(uname -s)" = Darwin ] || { printf '%s\n' 'macOS is required' >&2; exit 1; }
  [ -z "${SSH_CONNECTION:-}${SSH_CLIENT:-}${SSH_TTY:-}" ] || { printf '%s\n' 'registration is refused from SSH' >&2; exit 1; }
  console_user=$(stat -f '%Su' /dev/console 2>/dev/null || true)
  [ "$console_user" = "$(id -un)" ] || { printf '%s\n' 'current user does not own the visible console' >&2; exit 1; }
  launchctl print "$DOMAIN" >/dev/null 2>&1 || { printf '%s\n' 'visible GUI launchd domain is unavailable' >&2; exit 1; }
}

runtime_enabled() {
  grep -q '^RUNTIME_STATUS=ENABLED_AFTER_REVIEW$' "$WATCHER" &&
    grep -q '^RUNTIME_STATUS=ENABLED_AFTER_REVIEW$' "$MANAGER" &&
    grep -q '^RUNTIME_STATUS=ENABLED_AFTER_REVIEW$' "$SCRIPT_DIR/run-awakened-codex.sh"
}

show_status() {
  [ -f "$PLIST" ] && installed=true || installed=false
  if launchctl print "$DOMAIN/$LABEL" >/dev/null 2>&1; then loaded=true; else loaded=false; fi
  printf 'MAC_WATCHER_PLIST=%s\nMAC_WATCHER_INSTALLED=%s\nMAC_WATCHER_LOADED=%s\n' "$PLIST" "$installed" "$loaded"
  if runtime_enabled; then printf '%s\n' 'RUNTIME_STATUS=ENABLED_AFTER_REVIEW'; else printf '%s\n' 'RUNTIME_STATUS=DISABLED_PENDING_END_TO_END'; fi
  /bin/sh "$MANAGER" status
}

install_agent() {
  assert_visible_gui
  [ -f "$WATCHER" ] && [ ! -L "$WATCHER" ] || { printf '%s\n' 'watcher is missing or symlinked' >&2; exit 1; }
  [ -f "$MANAGER" ] && [ ! -L "$MANAGER" ] || { printf '%s\n' 'manager is missing or symlinked' >&2; exit 1; }
  runtime_enabled || { printf '%s\n' 'INSTALL_RESULT=REFUSED_DISABLED_PENDING_END_TO_END' >&2; exit 1; }
  mkdir -p "$HOME/Library/LaunchAgents" "$LOG_DIR"
  chmod 700 "$LOG_DIR" 2>/dev/null || true
  temporary=$PLIST.$$.tmp
  {
    printf '%s\n' '<?xml version="1.0" encoding="UTF-8"?>'
    printf '%s\n' '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">'
    printf '%s\n' '<plist version="1.0"><dict>'
    printf '%s\n' '<key>Label</key><string>com.airjet.git-watcher</string>'
    printf '%s\n' '<key>ProgramArguments</key><array>'
    printf '%s\n' '<string>/bin/sh</string>'
    printf '<string>%s</string>\n' "$WATCHER"
    printf '%s\n' '<string>--poll-seconds</string>'
    printf '<string>%s</string>\n' "$POLL_SECONDS"
    printf '%s\n' '</array>'
    printf '%s\n' '<key>RunAtLoad</key><true/>'
    printf '%s\n' '<key>KeepAlive</key><false/>'
    printf '%s\n' '<key>ProcessType</key><string>Background</string>'
    printf '<key>StandardOutPath</key><string>%s</string>\n' "$STDOUT_LOG"
    printf '<key>StandardErrorPath</key><string>%s</string>\n' "$STDERR_LOG"
    printf '%s\n' '</dict></plist>'
  } > "$temporary"
  plutil -lint "$temporary" >/dev/null
  chmod 600 "$temporary"
  mv -f "$temporary" "$PLIST"
  launchctl bootout "$DOMAIN/$LABEL" >/dev/null 2>&1 || true
  launchctl bootstrap "$DOMAIN" "$PLIST"
  launchctl enable "$DOMAIN/$LABEL"
  printf '%s\n' 'INSTALL_RESULT=REGISTERED_AT_VISIBLE_USER_LOGIN'
  show_status
}

uninstall_agent() {
  assert_visible_gui
  launchctl bootout "$DOMAIN/$LABEL" >/dev/null 2>&1 || true
  if [ -f "$PLIST" ] && [ ! -L "$PLIST" ]; then rm -f "$PLIST"; fi
  printf '%s\n' 'UNINSTALL_RESULT=REMOVED'
  show_status
}

case "$ACTION" in
  status) show_status ;;
  install) install_agent ;;
  uninstall) uninstall_agent ;;
  *) printf 'unknown action: %s\n' "$ACTION" >&2; exit 2 ;;
esac

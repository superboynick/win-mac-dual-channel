#!/bin/sh
set -eu

MODEL=${CLAUDE_REVIEW_MODEL:-deepseek-v4-pro}
EFFORT=${CLAUDE_REVIEW_EFFORT:-low}
MAX_DIFF_CHARS=${CLAUDE_REVIEW_MAX_DIFF_CHARS:-100000}
SETTINGS=${CLAUDE_SETTINGS_FILE:-$HOME/.claude/settings.json}

case "$MODEL" in deepseek-v4-pro|deepseek-v4-flash) ;; *) printf '%s\n' 'CLAUDE_REVIEW_BLOCKED_MODEL' >&2; exit 1 ;; esac
case "$EFFORT" in low|medium|high) ;; *) printf '%s\n' 'CLAUDE_REVIEW_BLOCKED_EFFORT' >&2; exit 1 ;; esac
case "$MAX_DIFF_CHARS" in ''|*[!0-9]*) printf '%s\n' 'CLAUDE_REVIEW_BLOCKED_MAX_DIFF' >&2; exit 1 ;; esac

command -v claude >/dev/null 2>&1 || { printf '%s\n' 'CLAUDE_REVIEW_BLOCKED_CLI_MISSING' >&2; exit 1; }
[ -f "$SETTINGS" ] || { printf '%s\n' 'CLAUDE_REVIEW_BLOCKED_LOCAL_SETTINGS_MISSING' >&2; exit 1; }
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null) || { printf '%s\n' 'CLAUDE_REVIEW_BLOCKED_NOT_GIT_REPOSITORY' >&2; exit 1; }
cd "$REPO_ROOT"

if [ "$#" -gt 0 ]; then
  DIFF=$(git diff --cached --no-ext-diff --unified=5 -- "$@")
else
  DIFF=$(git diff --cached --no-ext-diff --unified=5)
fi
[ -n "$DIFF" ] || { printf '%s\n' 'CLAUDE_REVIEW_BLOCKED_EMPTY_STAGED_DIFF' >&2; exit 1; }
DIFF_CHARS=$(printf '%s' "$DIFF" | wc -c | tr -d ' ')
[ "$DIFF_CHARS" -le "$MAX_DIFF_CHARS" ] || {
  printf 'CLAUDE_REVIEW_BLOCKED_DIFF_TOO_LARGE chars=%s max=%s\n' "$DIFF_CHARS" "$MAX_DIFF_CHARS" >&2
  exit 1
}

{
  printf '%s\n' 'Act as a read-only second-model code reviewer. Review only the staged diff below.'
  printf '%s\n' 'Identify concrete correctness, consistency, regression, and missing-test issues.'
  printf '%s\n' 'Do not use tools, edit files, weaken repository controls, or expand scope.'
  printf '%s\n' 'Return concise sections BLOCKERS, NON_BLOCKING, and VERDICT.'
  printf '%s\n\n' 'Codex will independently verify every finding. STAGED DIFF:'
  printf '%s\n' "$DIFF"
} | claude -p --bare --settings "$SETTINGS" --model "$MODEL" --tools "" \
  --permission-mode plan --effort "$EFFORT" --no-session-persistence --output-format text

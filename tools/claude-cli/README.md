# Claude CLI second-model workflow

This directory provides portable, read-only review entry points for Windows and macOS.
Claude CLI is a supporting reviewer; Codex remains the task owner, runs the tests, decides
which findings are valid, and owns every Git commit and push.

## Model routing

- `deepseek-v4-pro`: critical release review, cross-file reasoning, test-gap review.
- `deepseek-v4-flash`: broad low-risk scans, summaries, and first-pass triage.
- `dsv4pro` is only an informal name. The configured API rejects it as a CLI model ID.

Windows validation on 2026-07-14 used Claude Code `2.1.209`. A no-tools smoke request to
`deepseek-v4-pro` returned `PASS`, and a focused watcher diff review returned no blockers.
The local configuration also exposes `deepseek-v4-flash` for the fast tier.

## Local configuration boundary

Each endpoint configures its own `~/.claude/settings.json` outside Git. Never copy or commit
the settings file, authentication token, API key helper, gateway/base URL, sessions, cache,
debug logs, or machine-specific paths. The wrappers read the local settings file but never
print it.

Mac readiness check:

```sh
claude --version
claude -p --bare --settings "$HOME/.claude/settings.json" \
  --model deepseek-v4-pro --tools "" --permission-mode plan \
  --effort low --no-session-persistence \
  'Return only: CLAUDE_DSV4PRO=PASS'
```

Windows readiness check:

```powershell
claude --version
claude -p --bare --settings "$HOME\.claude\settings.json" `
  --model deepseek-v4-pro --tools "" --permission-mode plan `
  --effort low --no-session-persistence `
  'Return only: CLAUDE_DSV4PRO=PASS'
```

## Review a staged change

Windows:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File `
  .\tools\claude-cli\review-staged.ps1
```

Mac:

```sh
sh tools/claude-cli/review-staged.sh
```

Pass repository-relative paths to narrow the review. Select the fast tier with
`-Model deepseek-v4-flash` on Windows or `CLAUDE_REVIEW_MODEL=deepseek-v4-flash` on Mac.
The wrappers reject an empty or oversized diff, disable tools, use plan mode, and disable
session persistence. They do not edit files or run Git mutations.

Use a narrow diff and a clear review question. Do not send credentials, license material,
commercial PDFs, private research bundles, or generated solver data to the configured model
gateway. A provider response is evidence for review, not an automatic engineering decision.

Current CLI behavior is based on the installed `claude --help` plus Anthropic's
[CLI reference](https://docs.anthropic.com/en/docs/claude-code/cli-usage) and
[LLM gateway guidance](https://docs.anthropic.com/en/docs/claude-code/llm-gateway).
